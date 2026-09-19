# -*- coding: utf-8 -*-
"""V2 Data Source Router — 核心解析器：确定性 fallback（Primary→Secondary→Tertiary→Cache→Missing）。"""
from __future__ import annotations
import threading
import time
from datetime import datetime, timezone
from . import net, cache, audit, validate, registry, local_bars, pit_cache
from . import mt5_market as MT
from . import adapters_market as AM
from . import adapters_macro as AMAC

_TF_SECONDS = {"5m": 300, "15m": 900, "60m": 3600, "4h": 14400, "1d": 86400}
_HIST_FRESH = {"5m": 0.5, "15m": 0.5, "60m": 2.0, "4h": 8.0, "1d": 48.0}
_HIST_STALE = {"5m": 48, "15m": 48, "60m": 72, "4h": 168, "1d": 240}

# FIX(2026-09-16) — macro 取数的硬边界（事故：DX-Y.NYB 重入递归 + 无冷却刷爆审计）
MAX_RETRIES = 3                 # retry 硬上限（调用方传再大也截断）
MAX_BACKOFF_S = 2.0             # 单次退避上限
MACRO_COOLDOWN_S = 300.0        # 源失败后的 per-host 冷却
_INFLIGHT = threading.local()   # 结构性禁止 reentrant 递归（per-thread, 按 name）


def _inflight_enter(name):
    s = getattr(_INFLIGHT, "names", None)
    if s is None:
        s = set()
        _INFLIGHT.names = s
    if name in s:
        return False
    s.add(name)
    return True


def _inflight_exit(name):
    s = getattr(_INFLIGHT, "names", None)
    if s is not None:
        s.discard(name)


def _iso():
    return datetime.now(timezone.utc).isoformat()


class Router:
    def __init__(self):
        self.last = {}
        self._last_req = 0.0

    # ---------------- 历史 K 线 ----------------
    def history(self, tf, symbol="XAUUSD"):
        key = f"hist:{symbol}:{tf}"
        attempts = []
        for level, (src, prio) in enumerate(registry.history_sources(tf)):
            req = time.time()
            try:
                if src == "mt5":
                    res = MT.history(tf, symbol)
                elif src == "local_fxtm":
                    res = AM.hist_local(tf)
                elif src == "yahoo":
                    # P0-01: fallback 必须同 instrument（XAUUSD 现货→Yahoo XAUUSD=X），禁止 fallback 换成 GC=F 期货
                    res = AM.hist_yahoo("XAUUSD=X" if symbol == "XAUUSD" else symbol, tf)
                else:
                    continue
                ok, reasons, clean = validate.validate_bars(res.get("bars"), tf, _TF_SECONDS[tf])
                attempts.append({"source": src, "level": level, "n": len(clean), "ok": ok, "reasons": reasons[:3]})
                if ok and len(clean) >= 5:
                    res["bars"] = clean; res["n"] = len(clean)
                    res["last_bar_ts"] = clean[-1]["t"]
                    res["_selected_source"] = src; res["_fallback_level"] = level
                    res["_freshness"] = cache.FRESH
                    cache.put(key, res, src, observed_ts=clean[-1]["t"],
                              fresh_h=_HIST_FRESH[tf], stale_h=_HIST_STALE[tf])
                    audit.log(data_type=f"history:{tf}", source_id=src, requested_at=req,
                              received_at=time.time(), selected_source=src, fallback_level=level,
                              data_timestamp=clean[-1]["t"], freshness=cache.FRESH, status="OK",
                              latency_ms=res.get("latency_ms"), error=None,
                              field=key, requested_symbol=symbol,
                              candidate_sources=[s for s, _ in registry.history_sources(tf)],
                              selection_reason=("primary" if level == 0 else f"fallback_level_{level}"),
                              pit="PASS", quality="OK")
                    self.last[key] = {"source": src, "level": level, "freshness": cache.FRESH}
                    try:  # P0-05: 写入不可变 PIT 记录（供 as-of / replay 输入快照）
                        pit_cache.put_record(key, symbol, clean[-1]["c"], data_ts=clean[-1]["t"], source=src)
                    except Exception:  # noqa: BLE001
                        pass
                    return res
                if res.get("error"):
                    attempts.append({"source": src, "level": level, "error": res.get("error")})
            except Exception as e:  # noqa: BLE001
                attempts.append({"source": src, "level": level, "error": f"{type(e).__name__}:{str(e)[:100]}"})
        # 全源失败 → cache
        rec = cache.get(key)
        if rec and rec.get("usable"):
            _v = rec.get("value")
            if _v is None:
                _v = rec.get("last_valid")
            if _v is None:
                val = {"tf": tf, "symbol": symbol, "source": None, "bars": [], "n": 0,
                       "retrieval_ts": _iso(), "last_bar_ts": None, "error": "CACHE_EMPTY"}
                return val
            val = dict(_v); val["_selected_source"] = f"cache({rec.get('source')})"
            val["_fallback_level"] = "cache"; val["_freshness"] = rec["freshness"]
            audit.log(data_type=f"history:{tf}", source_id="cache", requested_at=time.time(),
                      received_at=time.time(), selected_source=f"cache({rec.get('source')})",
                      fallback_level="cache", data_timestamp=val.get("last_bar_ts"),
                      freshness=rec["freshness"], status=rec["freshness"], error=None)
            self.last[key] = {"source": "cache", "freshness": rec["freshness"]}
            return val
        # Missing
        audit.log(data_type=f"history:{tf}", source_id=None, requested_at=time.time(), received_at=time.time(),
                  selected_source=None, fallback_level="missing", data_timestamp=None,
                  freshness=cache.MISSING, status=cache.SOURCE_DOWN, error=str(attempts[-3:])[:200])
        self.last[key] = {"source": None, "freshness": cache.MISSING}
        return {"tf": tf, "symbol": symbol, "source": None, "bars": [], "n": 0,
                "retrieval_ts": _iso(), "last_bar_ts": None,
                "error": "ALL_SOURCES_FAILED", "attempts": attempts,
                "_selected_source": None, "_fallback_level": "missing", "_freshness": cache.MISSING}

    # ---------------- 现价 ----------------
    def quote(self, key):
        ckey = f"quote:{key}"
        errs = []
        for level, (src, code) in enumerate(registry.quote_sources(key)):
            req = time.time()
            try:
                if src == "mt5":
                    q = MT.quote(code)
                elif src == "local_fxtm":
                    q = local_bars.local_quote()
                else:
                    parser = AM.QUOTE_PARSERS.get(src)
                    if parser is None:
                        continue
                    q = parser(code)
                ok, reasons = validate.validate_quote(q)
                if ok:
                    q["key"] = key; q["retrieval_ts"] = _iso(); q["code"] = code
                    q["_selected_source"] = src; q["_fallback_level"] = level; q["_freshness"] = cache.FRESH
                    cache.put(ckey, q, src, fresh_h=0.05, stale_h=24)
                    audit.log(data_type=f"quote:{key}", source_id=src, requested_at=req, received_at=time.time(),
                              selected_source=src, fallback_level=level, data_timestamp=q.get("data_ts"),
                              freshness=cache.FRESH, status="OK", latency_ms=None, error=None)
                    try:  # P0-05: 不可变 PIT 记录
                        pit_cache.put_record(ckey, key, q.get("price"),
                                             data_ts=q.get("data_ts") or time.time(), source=src)
                    except Exception:  # noqa: BLE001
                        pass
                    return q
                errs.append(f"{src}:invalid({reasons})")
            except Exception as e:  # noqa: BLE001
                errs.append(f"{src}:{type(e).__name__}")
        rec = cache.get(ckey)
        if rec and rec.get("usable"):
            _v = rec.get("value")
            if _v is None:
                _v = rec.get("last_valid")
            if _v is None:
                return {"key": key, "price": None, "retrieval_ts": _iso(), "source": None, "errors": errs,
                        "_selected_source": None, "_fallback_level": "missing", "_freshness": cache.MISSING}
            q = dict(_v); q["_selected_source"] = f"cache({rec.get('source')})"
            q["_fallback_level"] = "cache"; q["_freshness"] = rec["freshness"]; q["errors"] = errs
            audit.log(data_type=f"quote:{key}", source_id="cache", requested_at=time.time(), received_at=time.time(),
                      selected_source=f"cache({rec.get('source')})", fallback_level="cache",
                      data_timestamp=q.get("data_ts"), freshness=rec["freshness"], status=rec["freshness"], error=None)
            return q
        return {"key": key, "price": None, "retrieval_ts": _iso(), "source": None, "errors": errs,
                "_selected_source": None, "_fallback_level": "missing", "_freshness": cache.MISSING}

    def _macro_fallback(self, name, ckey, fresh_h, stale_h, last_err, attempts, status):
        """统一失败出口：有可用缓存 → 返回 last_valid 并标 STALE；否则抛干净的 SOURCE_DOWN。"""
        rec = cache.get(ckey)
        audit.log(data_type=f"macro:{name}", source_id=name, requested_at=self._last_req,
                  received_at=time.time(),
                  selected_source=(f"cache({name})" if rec and rec.get("usable") else None),
                  fallback_level=("cache" if rec and rec.get("usable") else "missing"),
                  data_timestamp=(rec or {}).get("observed_at"),
                  freshness=(rec or {}).get("freshness", cache.MISSING),
                  status=status, latency_ms=None, error=last_err, attempts=attempts)
        if rec and rec.get("usable"):
            val = rec.get("value")
            if val is None:
                val = rec.get("last_valid")
            if val is None:
                raise RuntimeError(f"macro source down (no usable value): {name} ({last_err})")
            cache.put(ckey, None, name, state_override=cache.STALE,
                      observed_at=rec.get("observed_at"), observed_ts=rec.get("observed_ts"),
                      fresh_h=fresh_h, stale_h=stale_h)
            return val
        raise RuntimeError(f"macro source down: {name} ({last_err})")

    # ---------------- 宏观（带 cache + freshness + cooldown；失败→last_valid） ----------------
    def macro(self, name, retries=2, backoff=0.6):
        """宏观取数（有界、无递归、带 per-source cooldown）。

        硬边界（FIX 2026-09-16）：
        - **重入保护**：router→adapter→sources→router 回流结构上被禁止（线程内按 name 判定），
          重入时绝不递归，直接走 cache/last_valid 或抛 SOURCE_DOWN。
        - **retry 硬上限**：min(retries, MAX_RETRIES)，退避封顶 MAX_BACKOFF_S。
        - **cooldown**：失败后按 host 进入冷却，冷却期内直接 SOURCE_DOWN（不再打网络/不再重试）。
        """
        d = AMAC.MACRO_DEFS.get(name)
        if not d:
            raise KeyError(f"unknown macro source: {name}")
        fn, (fresh_h, stale_h), host = d
        ckey = f"macro:{name}"
        self._last_req = time.time()
        if not _inflight_enter(name):
            # 重入（同一 name 在调用栈里再次进入）→ 结构性阻断递归
            return self._macro_fallback(name, ckey, fresh_h, stale_h,
                                        "REENTRANT_SOURCE_LOOP(prevented)", 0, cache.SOURCE_DOWN)
        try:
            retries = max(0, min(int(retries) if retries is not None else 0, MAX_RETRIES))
            cooling, rem = net.is_cooling(host) if host else (False, 0.0)
            if cooling:
                return self._macro_fallback(name, ckey, fresh_h, stale_h,
                                            f"SOURCE_DOWN(cooldown {rem}s)", 0, cache.SOURCE_DOWN)
            last_err = None
            attempts = 0
            for attempt in range(retries + 1):
                attempts = attempt + 1
                try:
                    v = fn()
                    cache.put(ckey, v, name, fresh_h=fresh_h, stale_h=stale_h)
                    audit.log(data_type=f"macro:{name}", source_id=name, requested_at=self._last_req,
                              received_at=time.time(), selected_source=name, fallback_level=attempt,
                              data_timestamp=None, freshness=cache.FRESH, status="OK",
                              latency_ms=None, error=None, attempts=attempts)
                    return v
                except Exception as e:  # noqa: BLE001
                    last_err = f"{type(e).__name__}:{str(e)[:120]}"
                    if attempt < retries:
                        time.sleep(min(backoff * (2 ** attempt), MAX_BACKOFF_S))
            net.mark_down(host, MACRO_COOLDOWN_S)   # 失败 → 进冷却，阻断后续高频重试
            return self._macro_fallback(name, ckey, fresh_h, stale_h, last_err, attempts, cache.SOURCE_DOWN)
        finally:
            _inflight_exit(name)

    # ---------------- 健康 ----------------
    def health_report(self):
        from . import health
        return health.build_report(self)
