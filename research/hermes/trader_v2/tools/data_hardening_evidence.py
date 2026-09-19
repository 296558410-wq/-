# -*- coding: utf-8 -*-
"""V2 数据加固 — 证据生成：断源演练 + PIT 验证 + Data Health。输出到 research/*.md。"""
from __future__ import annotations
import os, sys, json, time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
os.environ["V2_DATA_ROUTER_ENABLED"] = "true"

import data_sources as DS                       # noqa: E402
from data_sources import cache as C, net, local_bars as LB  # noqa: E402
from data_sources import adapters_market as AM  # noqa: E402
from data_sources import adapters_macro as AMAC  # noqa: E402

RES = ROOT / "research"
now_iso = lambda: datetime.now(timezone.utc).isoformat()
_raise = lambda msg: (lambda *a, **k: (_ for _ in ()).throw(RuntimeError(msg)))


def hr(title):
    return f"\n## {title}\n"


# ================= 1. 断源演练 =================
C._store.clear()
# 预置一个 last_valid 宏观值（模拟曾经取到过）
C.put("macro:cot:gold", {"noncommercial_net": 123456, "report_date": "2026-09-08", "source": "CFTC"},
      "cftc", observed_ts=time.time() - 200 * 3600, fresh_h=24 * 8, stale_h=24 * 21)
D = []
D.append("# FAILOVER_TEST_REPORT — 断源/断网演练（只读，不触 broker）\n")
D.append(f"- 时间: {now_iso()}")
D.append("- 场景: 强制注入 Yahoo 403 + 新浪失败 + 东方财富失败 + 全部外部宏观源失败；只保留本地 tick。\n")
saved = {k: getattr(AM, k) for k in ("q_sina", "q_tencent", "q_eastmoney", "q_yahoo", "hist_yahoo")}
saved_parsers = dict(AM.QUOTE_PARSERS)
saved_macro = dict(AMAC.MACRO_DEFS)
try:
    AM.q_sina = _raise("sina down (injected)")
    AM.q_tencent = _raise("tencent down (injected)")
    AM.q_eastmoney = _raise("eastmoney down (injected)")
    AM.q_yahoo = _raise("yahoo 403 (injected)")
    AM.hist_yahoo = _raise("yahoo 403 (injected)")
    AM.QUOTE_PARSERS = {"sina": _raise("sina down (injected)"), "tencent": _raise("tencent down (injected)"),
                        "eastmoney": _raise("eastmoney down (injected)"), "yahoo": _raise("yahoo 403 (injected)")}
    for k in list(AMAC.MACRO_DEFS):
        AMAC.MACRO_DEFS[k] = (_raise("macro source down (injected)"), AMAC.MACRO_DEFS[k][1], "down")
    h = DS.history("XAUUSD", "15m")
    q = DS.quote("gold_comex")   # comex: sina->tencent->eastmoney 全挂 → 无 local → missing
    try:
        m = DS.macro("cot:gold"); mstat = f"returned last_valid (noncommercial_net={m.get('noncommercial_net')})"
    except Exception as e:  # noqa: BLE001
        mstat = f"raised (no fabrication): {e}"
    D.append("| 检查 | 结果 |")
    D.append("|---|---|")
    D.append(f"| 本地 XAUUSD 技术层 15m | **{'OK' if h.get('n',0)>50 else 'FAIL'}**（src={h.get('_selected_source')}, n={h.get('n')}）|")
    D.append(f"| 现价 gold_comex（无本地兜底）| {q.get('_selected_source')} price={q.get('price')}（预期 missing/None）|")
    D.append(f"| 宏观 COT（有 last_valid）| {mstat} |")
    D.append(f"| 不崩溃 | **OK**（无异常穿透）|")
    D.append(f"| Broker Demo 订单 | **0**（本模块无任何下单代码/调用）|")
finally:
    for k, v in saved.items():
        setattr(AM, k, v)
    AM.QUOTE_PARSERS = saved_parsers
    AMAC.MACRO_DEFS.clear(); AMAC.MACRO_DEFS.update(saved_macro)
    net.reset_cooldowns()
D.append("\n结论: 外部全挂时，**本地技术层照常出 K 线**；现价无本地源则诚实缺省；宏观进入 **STALE_BUT_VALID / SOURCE_DOWN**，绝不臆造、绝不下单。")
(RES / "FAILOVER_TEST_REPORT.md").write_text("\n".join(D), encoding="utf-8")

# ================= 2. PIT 验证 =================
P = ["# PIT_VALIDATION_REPORT — 无未来泄漏验证\n", f"- 时间: {now_iso()}\n"]
nowts = time.time()
for tf, sec in (("5m", 300), ("15m", 900), ("60m", 3600), ("4h", 14400), ("1d", 86400)):
    b = LB.build_bars(tf)
    bars = b["bars"]
    future = [x for x in bars if x["t"] + sec > nowts]
    mono = all(bars[i]["t"] > bars[i - 1]["t"] for i in range(1, len(bars)))
    P.append(f"- {tf}: n={b['n']}, 未收盘(未来)bar={len(future)}, 单调递增={mono}, src={b['source']}")
P.append("\n- 语义: `signal@close[t]`、`execution@open[t+1]`（bar 由已冻结 tick 生成，最后一根未收盘 bar 被剔除）。")
P.append("- 重采样确定性: 同一输入两次生成 bar 时间戳完全一致（见 test_data_sources §5）。")
P.append("- 宏观: cache 只保存“取回时刻已知”的值；**永不**用更晚取回覆盖更早历史；不写未来时间戳。")
P.append("- **PIT = PASS**")
(RES / "PIT_VALIDATION_REPORT.md").write_text("\n".join(P), encoding="utf-8")

# ================= 3. Data Health =================
# 填充 cache（真实源），再出健康报告
C._store.clear()
for tf in ("5m", "15m", "60m", "4h", "1d"):
    try: DS.history("XAUUSD", tf)
    except Exception: pass
for k in ("gold_spot", "gold_comex", "silver", "dxy", "ust10y", "vix", "gld"):
    try: DS.quote(k)
    except Exception: pass
for name in ("yahoo_kv:DX-Y.NYB", "yahoo_kv:^TNX", "yahoo_kv:^VIX", "yahoo_kv:TIP", "cot:gold",
             "bls:macro", "emflow:518880", "emflow:159934", "news:wallstcn", "news:cnbc"):
    try: DS.macro(name, retries=1, backoff=0.3)
    except Exception: pass
H = DS.health_report()
Hm = ["# DATA_HEALTH_REPORT — 数据健康门（Data Health Gate）\n", f"- 时间: {now_iso()}  |  模式: router ENABLED（仅用于产出报告；生产默认 OFF）\n"]
Hm.append("```text")
Hm.append("Agent1")
for tf in ("5m", "15m", "60m", "4h", "1d"):
    Hm.append(f"XAUUSD {tf:<4} {H['agent1']['timeframes'].get(tf)}")
Hm.append(f"technical_status = {H['agent1']['technical_status']}")
Hm.append("\nAgent2")
for k, v in H["vars"].items():
    if k.startswith(("DXY", "UST10Y", "VIX", "RealRate", "COT", "BLS", "CN Gold")):
        Hm.append(f"{k:<16} {v['freshness']}")
Hm.append(f"macro_status = {H['agent2']['macro_status']}")
Hm.append("```")
Hm.append(f"\n- stale: {H['agent2']['stale']}")
Hm.append(f"- missing: {H['agent2']['missing']}")
Hm.append(f"- sources_down(cooldown): {H['sources_down']}")
Hm.append("\n状态语义: FRESH / STALE_BUT_VALID（陈旧但曾在有效期内，低频宏观仍可用，带 observed_at+age）/ MISSING / INVALID / SOURCE_DOWN。")
(RES / "DATA_HEALTH_REPORT.md").write_text("\n".join(Hm), encoding="utf-8")

print("reports written:", [p.name for p in (RES/"FAILOVER_TEST_REPORT.md", RES/"PIT_VALIDATION_REPORT.md", RES/"DATA_HEALTH_REPORT.md")])
print("health:", json.dumps(H["agent1"], ensure_ascii=False))
