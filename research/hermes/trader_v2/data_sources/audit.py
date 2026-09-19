# -*- coding: utf-8 -*-
"""V2 Data Source Router — 审计日志（可回答：Hermes 在某时刻做决定时，实际看到了哪一份数据？）。

FIX(2026-09-16) — 审计限速/聚合：
  一个坏 source 绝不能无限高速刷日志（事故：DX-Y.NYB 连续 2 天刷出 39MB / 97k 行）。
  规则：同一 (data_type, status, error-kind) 在一个窗口内最多直写 `_MAX_DIRECT` 条；
       超出部分只计数（写入时聚合为 1 条 AGGREGATED 汇总行，并在窗口滚动时归档 suppressed 计数）。
  不删除历史；只是限制新增速率。`log()` 签名与返回保持不变。
"""
from __future__ import annotations
import json
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "data_cache" / "router_audit.jsonl"

WINDOW_S = 60.0        # 聚合窗口（秒）
MAX_DIRECT = 3         # 每窗口每 key 直写上限
_LIMIT: dict = {}      # key -> {"t0": ts, "n": int, "suppressed": int}


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _err_kind(err):
    """错误分类键：同 kind 的重复失败才聚合（不把不同故障混为一谈）。"""
    if not err:
        return None
    s = str(err)
    return s.split(":", 1)[0][:40]


def _raw_write(obj: dict) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def _flush_summary(prev_key, new_ts) -> None:
    dt, status, kind = prev_key
    _raw_write({"data_type": dt, "status": "AGGREGATED", "freshness": None, "source_id": None,
                "fallback_level": "rate_limited", "data_timestamp": None, "latency_ms": None,
                "error": f"suppressed {_LIMIT[prev_key].get('suppressed', 0)} repeated "
                         f"(status={status}, kind={kind}) rows within {WINDOW_S:.0f}s",
                "logged_at": _now_iso()})


def log(**kw):
    """写一条审计行（带限速/聚合）。返回 True=已写入，False=被限速聚合。"""
    kw.setdefault("logged_at", _now_iso())
    key = (kw.get("data_type"), kw.get("status"), _err_kind(kw.get("error")))
    now = time.time()
    st = _LIMIT.get(key)
    if st is not None and (now - st["t0"]) >= WINDOW_S:
        if st.get("suppressed"):
            try:
                _flush_summary(key, now)
            except Exception:  # noqa: BLE001
                pass
        st = None
    if st is None:
        st = {"t0": now, "n": 0, "suppressed": 0}
        _LIMIT[key] = st
    st["n"] += 1
    if st["n"] <= MAX_DIRECT:
        _raw_write(kw)
        return True
    st["suppressed"] += 1
    return False


def tail(n: int = 50) -> list:
    if not LOG.exists():
        return []
    lines = LOG.read_text(encoding="utf-8", errors="replace").splitlines()[-n:]
    out = []
    for ln in lines:
        try:
            out.append(json.loads(ln))
        except Exception:  # noqa: BLE001
            pass
    return out


def limiter_state() -> dict:
    """可观测：当前窗口各 key 的直写/压制计数。"""
    return {f"{k[0]}|{k[1]}|{k[2]}": dict(v) for k, v in _LIMIT.items()}


def reset_limiter() -> None:
    _LIMIT.clear()
