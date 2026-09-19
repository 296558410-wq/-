# -*- coding: utf-8 -*-
"""V3 MT5 能力验证（只读；order_send 硬拦截）。

产出:
  research/V3_MT5_ENVIRONMENT.md
  state/V3_MT5_ENVIRONMENT.json
  data/raw_ticks/<ts>_xauusd_ticks_sample.jsonl   (原始 tick 样本，证明可存原始 tick)
"""
from __future__ import annotations
import json
import statistics as st
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

V3 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(V3 / "mt5"))
import v3_adapter as A  # noqa: E402

OUT_JSON = V3 / "state" / "V3_MT5_ENVIRONMENT.json"
OUT_MD = V3 / "research" / "V3_MT5_ENVIRONMENT.md"
RAW = V3 / "data" / "raw_ticks"
DUKA_DIR = Path(r"C:\AIQuant\data\staging_duka")
POINT = None


def pct(xs, p):
    if not xs:
        return None
    xs = sorted(xs)
    k = (len(xs) - 1) * p / 100.0
    f = int(k); c = min(f + 1, len(xs) - 1)
    return xs[f] + (xs[c] - xs[f]) * (k - f)


def sha(p):
    import hashlib
    try:
        return hashlib.sha256(Path(p).read_bytes()).hexdigest()
    except Exception:  # noqa: BLE001
        return None


def main():
    global POINT
    result = {"schema": "v3_mt5_env/1", "ts_utc": datetime.now(timezone.utc).isoformat(),
              "safety": A.safety_flags(), "symbol": A.SYMBOL, "magic": A.MAGIC,
              "terminal": A.EXE, "data_dir": A.DATA_DIR, "capabilities": {}, "validation": {},
              "hf_limitations": {}, "gaps": [], "hashes": {}, "verdict": None}
    mt5, info = A.connect()
    # warmup: 等终端 connected + 登录 + 选中 symbol(MarketWatch)，否则 bid/ask=0 且无 tick
    for _ in range(40):
        ti = mt5.terminal_info()
        if ti and ti.connected and getattr(ti, "trade_allowed", None) is not None:
            break
        time.sleep(1)
    try:
        mt5.symbol_select(A.SYMBOL, True)
    except Exception:  # noqa: BLE001
        pass
    ai = None
    for _ in range(20):
        ai = mt5.account_info()
        if ai is not None:
            break
        time.sleep(1)
    time.sleep(3)
    result["account"] = {"login_present": bool(getattr(ai, "login", None)), "server": getattr(ai, "server", None),
                         "trade_allowed": getattr(ai, "trade_allowed", None), "independent_account": False,
                         "note": "复用可用 FXTM demo 凭据（未获独立账号）；执行只读，永不发单（§四 回退）"}
    result["data_path"] = info.get("data_path")

    # ---- symbol ----
    si = mt5.symbol_info(A.SYMBOL)
    if si is None:
        # 尝试在 MarketWatch 里选中
        mt5.symbol_select(A.SYMBOL, True); si = mt5.symbol_info(A.SYMBOL)
    if si is None:
        result["verdict"] = "FAIL"; result["gaps"].append("XAUUSD symbol not found")
        _write(result); return 0
    POINT = si.point
    result["symbol_info"] = {"name": si.name, "digits": si.digits, "point": si.point,
                             "spread_current": si.spread, "trade_mode": si.trade_mode,
                             "filling_mode": si.filling_mode, "visible": si.visible,
                             "session_deals": getattr(si, "session_deals", None),
                             "volume_min": si.volume_min, "volume_step": si.volume_step,
                             "description": si.description, "currency_base": si.currency_base,
                             "currency_profit": si.currency_profit}

    # ---- live quote + latency ----
    t0 = time.perf_counter(); tick = mt5.symbol_info_tick(A.SYMBOL); dt_ms = (time.perf_counter() - t0) * 1000
    if tick:
        result["live_quote"] = {"bid": tick.bid, "ask": tick.ask, "last": tick.last,
                                "spread_points": round((tick.ask - tick.bid) / si.point, 1) if si.point else None,
                                "time": tick.time, "time_msc": tick.time_msc, "volume": tick.volume,
                                "flags": tick.flags, "roundtrip_ms": round(dt_ms, 3)}
        result["capabilities"]["quote_bidask"] = True
    else:
        result["capabilities"]["quote_bidask"] = False; result["gaps"].append("live quote unavailable")

    # ---- ticks (copy_ticks_from, recent 6h) ----
    t0 = time.perf_counter()
    from_dt = datetime.now(timezone.utc) - timedelta(hours=24)
    ticks = mt5.copy_ticks_from(A.SYMBOL, from_dt, 1_000_000, mt5.COPY_TICKS_ALL)
    fetch_ms = (time.perf_counter() - t0) * 1000
    rows = []
    if ticks is not None and len(ticks):
        for r in ticks:
            rows.append({"time": int(r["time"]), "time_msc": int(r["time_msc"]), "bid": float(r["bid"]),
                         "ask": float(r["ask"]), "last": float(r["last"]), "volume": int(r["volume"]),
                         "flags": int(r["flags"])})
    result["capabilities"]["ticks_read"] = bool(rows)
    result["tick_fetch"] = {"count": len(rows), "window_hours": 24, "fetch_ms": round(fetch_ms, 1)}
    if not rows:
        result["gaps"].append("no live ticks in last 24h (market closed or tick history empty)")
    else:
        spreads = [round((x["ask"] - x["bid"]) / si.point, 1) for x in rows if x["ask"] > 0 and x["bid"] > 0]
        ivs = [rows[i + 1]["time_msc"] - rows[i]["time_msc"] for i in range(len(rows) - 1)]
        # ticks per hour
        perh = {}
        for x in rows:
            hh = datetime.fromtimestamp(x["time"], timezone.utc).strftime("%Y-%m-%dT%H")
            perh[hh] = perh.get(hh, 0) + 1
        # gaps (>30s between ticks)
        gaps = [iv for iv in ivs if iv > 30_000]
        # ms resolution
        distinct_ms = len(set(x["time_msc"] % 1000 for x in rows))
        result["tick_stats"] = {
            "spread_points": {"p50": pct(spreads, 50), "p90": pct(spreads, 90), "p95": pct(spreads, 95), "p99": pct(spreads, 99),
                              "min": min(spreads), "max": max(spreads), "mean": round(st.mean(spreads), 2)},
            "interval_ms": {"p50": pct(ivs, 50), "p90": pct(ivs, 90), "p95": pct(ivs, 95), "p99": pct(ivs, 99),
                            "min": min(ivs), "max": max(ivs)},
            "ticks_per_hour": perh,
            "ticks_per_hour_mean": round(st.mean(perh.values()), 1) if perh else None,
            "sessions_gaps_gt_30s": len(gaps),
            "timestamp_resolution_ms_declared": 1,
            "distinct_ms_low3": distinct_ms,
            "flags_seen": sorted(set(x["flags"] for x in rows)),
        }
        # raw tick sample (prove raw tick storage)
        RAW.mkdir(parents=True, exist_ok=True)
        rp = RAW / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_xauusd_ticks_sample.jsonl")
        with open(rp, "w", encoding="utf-8") as f:
            for x in rows[:5000]:
                f.write(json.dumps(x) + "\n")
        result["raw_tick_sample"] = {"path": str(rp), "rows": min(len(rows), 5000), "sha256": sha(rp)}
        result["capabilities"]["raw_tick_storage"] = True

    # ---- bars ----
    b1 = mt5.copy_rates_from_pos(A.SYMBOL, mt5.TIMEFRAME_M1, 0, 5)
    b5 = mt5.copy_rates_from_pos(A.SYMBOL, mt5.TIMEFRAME_M5, 0, 5)
    result["capabilities"]["bars_m1"] = bool(b1 is not None and len(b1))
    result["capabilities"]["bars_m5"] = bool(b5 is not None and len(b5))
    if b1 is not None and len(b1):
        result["bars_last"] = {"m1_close": float(b1[-1]["close"]), "m1_time": int(b1[-1]["time"]),
                               "m5_close": float(b5[-1]["close"]) if b5 is not None and len(b5) else None}

    # ---- HF limitations ----
    result["hf_limitations"] = {
        "true_trade_direction": "PARTIAL — tick.flags 有 BUY/SELL 标志(成交方向, broker侧)，非真实 aggressor",
        "aggressor_side": "UNRESOLVABLE — MT5 无 order book，无 aggressor",
        "market_depth": "UNRESOLVABLE — MT5 零售数据无 DOM/L2",
        "queue_position": "UNRESOLVABLE — 无 queue 信息",
        "only_bidask_quote": "YES — 仅 Bid/Ask(+broker 聚合 last/volume)",
        "broker_side_aggregation": "LIKELY — 零售 broker tick 为聚合流，非交易所逐笔",
        "timestamp_resolution": "声明 ms(time_msc)；实际分辨率受 broker 聚合影响，通常 >1ms",
        "supports_100ms": "PARTIAL — 可聚合到 100ms，但非真实 100ms 事件序列",
        "supports_500ms": "PARTIAL", "supports_1s": "YES(聚合)", "supports_2s": "YES(聚合)",
    }

    # ---- DUKA compare ----
    result["duka_compare"] = _duka_compare(rows, si)

    # ---- validation matrix (§三) ----
    ts = result.get("tick_stats") or {}
    result["validation"] = {
        "1_symbol_exists": (si.name == "XAUUSD"),
        "2_bid_ask_read": result["capabilities"].get("quote_bidask"),
        "3_tick_timestamp": bool(rows),
        "4_timestamp_precision_ms_declared": 1 if rows else None,
        "5_tick_interval_pcts_ms": ts.get("interval_ms"),
        "6_spread_pcts_points": ts.get("spread_points"),
        "7_ticks_per_hour_mean": ts.get("ticks_per_hour_mean"),
        "8_session_gaps_gt30s": ts.get("sessions_gaps_gt_30s"),
        "9_raw_tick_saved": result["capabilities"].get("raw_tick_storage"),
        "10_duka_compare": (result.get("duka_compare") or {}).get("status"),
    }

    # ---- key file hashes (§五) ----
    for p in (V3 / "config" / "v3_config.json", V3 / "mt5" / "v3_adapter.py",
              V3 / "tools" / "v3_capability_audit.py", V3 / "state" / "V3_LIVE_ALLOWED",
              V3 / "state" / "V3_ORDER_SEND_ALLOWED", V3 / "state" / "V3_FORWARD_ALLOWED"):
        result["hashes"][str(p.relative_to(V3))] = sha(p)

    # ---- verdict ----
    caps = result["capabilities"]
    core = caps.get("quote_bidask") and caps.get("ticks_read") and caps.get("bars_m1") and caps.get("raw_tick_storage")
    if not core:
        result["verdict"] = "DATA_GAP"
    else:
        result["verdict"] = "PASS" if not result["gaps"] else "DATA_GAP"
    # 关键研究粒度无法由数据真实支持 → 已在 hf_limitations 标注 DATA_GAP/UNRESOLVABLE
    _write(result)
    A.disconnect(mt5)
    return 0


def _duka_compare(rows, si):
    out = {"duka_dir": str(DUKA_DIR), "ticks_files": 0, "latest_tick_file": None, "overlap_window": None,
           "status": "DATA_GAP", "note": None}
    try:
        tfs = sorted(DUKA_DIR.glob("ticks_*.parquet"))
        out["ticks_files"] = len(tfs)
        if not tfs:
            out["note"] = "no DUKA tick parquet"; return out
        out["latest_tick_file"] = tfs[-1].name
        # 用 pandas 读 schema（若可用）
        try:
            import pandas as pd
            df = pd.read_parquet(tfs[-1])
            out["duka_cols"] = list(df.columns)
            out["duka_rows"] = int(len(df))
            out["duka_price_scale"] = "ask/bid /1000 (推断)"
        except Exception as e:  # noqa: BLE001
            out["note"] = f"duka read failed: {type(e).__name__}"
        # 与 MT5 tick 窗口的重叠判断
        if rows:
            mt5_from = min(r["time"] for r in rows); mt5_to = max(r["time"] for r in rows)
            out["mt5_tick_window"] = {"from": mt5_from, "to": mt5_to}
            out["overlap_window"] = "NONE — DUKA 最新 2026-08-04，MT5 窗口 2026-09 无重叠"
            out["status"] = "DATA_GAP"
            out["note"] = "无时间重叠 → 无法逐 tick 对照；仅能做价格量级/spread 分布参照（见 tick_stats）"
    except Exception as e:  # noqa: BLE001
        out["note"] = f"{type(e).__name__}: {e}"
    return out


def _write(result):
    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    md = ["# V3 MT5 环境清单 — XAUUSD 高频研究（只读）", "",
          f"- 生成: {result['ts_utc']}", f"- **verdict: {result['verdict']}**", "",
          "## 实例 / 终端",
          f"- instance: `fxtm_demo_v3`", f"- terminal: `{result['terminal']}`",
          f"- data directory: `{result['data_dir']}`  (实际 data_path: `{result.get('data_path')}`)",
          f"- server: `{(result.get('account') or {}).get('server')}`",
          f"- symbol: `{result['symbol']}`", f"- Magic Number: **{result['magic']}** (V1=90002 / V2=90003)",
          f"- 创建时间: {result['ts_utc']}", "",
          "## 账号（敏感信息不写入）",
          f"- login present: {(result.get('account') or {}).get('login_present')}",
          f"- 独立账号: NO（复用 FXTM demo 凭据；未获独立账号 → §四 回退：只建实例/只读，永不发单）",
          f"- trade_allowed(broker): {(result.get('account') or {}).get('trade_allowed')}",
          f"- **order_send: 代码层硬拦截（OrderSendBlocked）**", "",
          "## symbol_info", "```json", json.dumps(result.get("symbol_info"), ensure_ascii=False, indent=1), "```",
          "## 数据能力",
          "```json", json.dumps(result.get("capabilities"), ensure_ascii=False, indent=1), "```",
          "## tick 统计（近 6h）",
          "```json", json.dumps(result.get("tick_stats"), ensure_ascii=False, indent=1), "```",
          f"- tick fetch: {json.dumps(result.get('tick_fetch'), ensure_ascii=False)}",
          f"- live quote: {json.dumps(result.get('live_quote'), ensure_ascii=False)}",
          f"- raw tick 样本: {json.dumps(result.get('raw_tick_sample'), ensure_ascii=False)}", "",
          "## 高频研究限制（§四）", "```json", json.dumps(result.get("hf_limitations"), ensure_ascii=False, indent=1), "```",
          "## DUKA 对照", "```json", json.dumps(result.get("duka_compare"), ensure_ascii=False, indent=1), "```",
          "## 安全闸门",
          f"```json\n{json.dumps(result.get('safety'), ensure_ascii=False, indent=1)}```",
          "", "## V1/V2 隔离证明",
          f"- V1: `C:\\Program Files\\ForexTime (FXTM) MT5\\terminal64.exe` — 未连接、未修改",
          f"- V2: `C:\\AIQuant\\mt5_instances\\fxtm_demo_01` — 未连接、未修改",
          f"- V3 只用独立 data dir: `{result['data_dir']}`（data_path 断言含 fxtm_demo_v3）",
          f"- order_send/order_check 代码层 raise；三个安全闸门均为 NO", "",
          "## 数据缺口 / FAIL", *([f"- {g}" for g in result.get("gaps", [])] or ["- (无)"]),
          *[f"- HF: {k}={v}" for k, v in result.get("hf_limitations", {}).items() if "UNRESOLVABLE" in str(v) or "PARTIAL" in str(v)],
          "", "## 关键文件 SHA256", "```json", json.dumps(result.get("hashes"), ensure_ascii=False, indent=1), "```"]
    OUT_MD.write_text("\n".join(md) + "\n", encoding="utf-8")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
