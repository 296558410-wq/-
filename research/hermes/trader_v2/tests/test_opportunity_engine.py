# -*- coding: utf-8 -*-
"""Hermes V2 Opportunity Discovery 测试（验收 §C 的 8 个场景）+ 决策上下文冻结测试。

在合成 Agent1/Agent2 快照上跑 Hermes 参照器, 检查它能 TRADE / WAIT / REJECT 而非机械交易。
日志: logs/test_opportunity_engine.log
"""
import sys, json
from datetime import datetime, timezone, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "hermes"))
import hermes as H  # noqa: E402
import context as CTX  # noqa: E402

TMP = HERE / "_tmp"; TMP.mkdir(exist_ok=True)
LOGS = ROOT / "logs"; LOGS.mkdir(exist_ok=True)
LOG = LOGS / "test_opportunity_engine.log"
_res = []


def log(s):
    line = f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] {s}"
    print(line)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def check(name, cond, detail=""):
    _res.append(bool(cond)); log(f"{'PASS' if cond else 'FAIL'} | {name} {detail}")


def a1(regime="mixed", bo="inside", pos=50, rm=5.0, atr=0.18, bias="neutral",
       exp="neutral", age_min=0, gaps=None, price=4350.0):
    gen = (datetime.now(timezone.utc) - timedelta(minutes=age_min)).isoformat()
    eb = int((datetime.now(timezone.utc) - timedelta(minutes=age_min)).timestamp())
    tf = lambda: {"trend_range": {"cat": "mixed"}, "structure": {"swing_bias": bias},
                  "exp_cont": {"state": exp}, "breakout": {"state": bo, "range_hi": 4360.0, "range_lo": 4340.0},
                  "range60": {"high": 4360.0, "low": 4340.0, "pos_pct": pos},
                  "atr_pct": atr, "recent_move_bps": rm}
    return {"agent": "agent1-technical", "agent_version": "agent1/test", "cycle": "TEST",
            "generated_utc": gen, "market_regime": {"regime": regime},
            "timeframes": {"15m": tf(), "60m": tf(), "4h": tf(), "1d": tf(), "5m": tf()},
            "price_basis": {"primary_last": price}, "quotes": {"gold_spot": {"spread": 0.35}},
            "data_quality": {"gaps": gaps or [], "by_tf": {"15m": {"last_bar_ts": eb}}}}


def a2(macro="NEUTRAL", diverg=False, geo=0, usd=0.1, tnx=0.2, age_min=0):
    ts = (datetime.now(timezone.utc) - timedelta(minutes=age_min)).isoformat()
    eb = int((datetime.now(timezone.utc) - timedelta(minutes=age_min)).timestamp())
    return {"agent": "agent2-macro-global", "agent_version": "agent2/test", "cycle": "TEST",
            "snapshot_ts": ts, "gold_macro_state": macro, "macro_status": "OK",
            "macro": {"usd": {"change_pct_1d": usd, "data_ts": eb}, "rates": {"change_pct_1d": tnx, "data_ts": eb}, "economic_data": []},
            "geopolitics": {"events": [{"evidence_id": f"ev_geo_{i}"} for i in range(geo)]},
            "narrative_vs_flow": {"narrative_flow_divergence": diverg},
            "gold_flows": {"etf": {"cn_gold_etf_net_inflow_sum_cny": -1e8 if diverg else 1e6}},
            "evidence": {"refs": [f"ev_x_{i}" for i in range(3)]}}


def run_case(name, snap1, snap2, expect):
    p1 = TMP / f"{name}_a1.json"; p2 = TMP / f"{name}_a2.json"
    p1.write_text(json.dumps(snap1, ensure_ascii=False), encoding="utf-8")
    p2.write_text(json.dumps(snap2, ensure_ascii=False), encoding="utf-8")
    d, ctx, cands, tags = H.run(cycle=f"TEST_{name}", source="reference_rules",
                                agent1_path=p1, agent2_path=p2)
    ok = d["decision"] == expect
    check(f"{name}: expect {expect}", ok, f"got {d['decision']} | {d.get('reason')}")
    return d


def main():
    open(LOG, "a", encoding="utf-8").write("\n" + "=" * 60 + "\n")
    log("=== Hermes V2 Opportunity Discovery 测试 ===")

    # 1 技术多头 + 宏观多头 → TRADE
    run_case("S1_techUp_macroUp", a1(regime="trend", bias="up", pos=50, rm=5.0), a2(macro="BULLISH"), "TRADE")
    # 2 技术多头 + 宏观空头 → WAIT(冲突)
    run_case("S2_techUp_macroDown", a1(regime="trend", bias="up", pos=50, rm=5.0), a2(macro="BEARISH"), "WAIT")
    # 3 突破 + 已严重定价 → WAIT
    run_case("S3_breakout_pricedIn", a1(regime="range", bo="breakout_up", pos=60, rm=70.0), a2(macro="NEUTRAL"), "WAIT")
    # 4 地缘 headline 无 follow-through → WAIT(需确认)
    run_case("S4_geo_noFollow", a1(regime="range", bo="inside", pos=50, rm=2.0), a2(macro="NEUTRAL", geo=3), "WAIT")
    # 5 ETF 流出 + 避险叙事(背离) → WAIT(方向未定)
    run_case("S5_divergence", a1(regime="range", bo="inside", pos=50, rm=2.0), a2(macro="NEUTRAL", diverg=True), "WAIT")
    # 6 数据过期 → WAIT
    run_case("S6_staleData", a1(regime="trend", bias="up", pos=50, age_min=180), a2(macro="BULLISH", age_min=300), "WAIT")
    # 7 证据冲突(技术多 vs 宏观空) → WAIT
    run_case("S7_conflict", a1(regime="trend", bias="up", pos=50, rm=5.0), a2(macro="BEARISH", diverg=True, geo=2), "WAIT")
    # 8 风险回报不足(突破但处区间高位=追高) → REJECT
    run_case("S8_badRR", a1(regime="range", bo="breakout_up", pos=93, rm=5.0), a2(macro="NEUTRAL"), "REJECT")

    # 上下文冻结: 相同输入 → 相同 context_hash; 且已写文件不被覆盖
    c1, p1 = CTX.build_context("FREEZE1")
    h1 = c1["context_hash"]
    c2, _ = CTX.build_context("FREEZE1")
    check("context freeze: same input -> same hash", h1 == c2["context_hash"], h1[:12])
    before = p1.read_bytes()
    snap_mod = a2(macro="BEARISH")
    p2 = TMP / "z_a2.json"; p2.write_text(json.dumps(snap_mod), encoding="utf-8")
    CTX.build_context("FREEZE1", agent2_path=p2)
    check("context file immutable", p1.read_bytes() == before, "unchanged")

    ok = all(_res)
    log(f"=== RESULT: {sum(_res)}/{len(_res)} PASS ===")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
