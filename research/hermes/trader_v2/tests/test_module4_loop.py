# -*- coding: utf-8 -*-
"""Module 4 测试 —— Hermes→Paper→Ledger 闭环 (T1–T12)。日志: logs/test_module4_loop.log"""
import sys, json, copy
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "execution"))
sys.path.insert(0, str(ROOT / "ledger"))
import paper_executor as PE  # noqa: E402
import hermes_paper_adapter as ADP  # noqa: E402
import ledger as L  # noqa: E402
import replay as R  # noqa: E402

TMP = HERE / "_tmp"; TMP.mkdir(exist_ok=True)
LOGS = ROOT / "logs"; LOGS.mkdir(exist_ok=True)
LOG = LOGS / "test_module4_loop.log"
PE.ACCOUNT_P = TMP / "m4_paper_account.json"
PE.EXECUTIONS_P = TMP / "m4_paper_execs.jsonl"
_res = []


def log(s):
    line = f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] {s}"
    print(line)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def check(n, c, d=""):
    _res.append(bool(c)); log(f"{'PASS' if c else 'FAIL'} | {n} {d}")


PAPER_CFG = {"symbol": "XAUUSD",
            "execution": {"execution_mode": "PAPER", "live_trading": False, "broker_demo_enabled": False,
                          "cost_model": {"spread_bps_typical": 0.35, "slippage_bps": 0.30, "latency_ms": 250, "commission_per_lot_usd": 0.0},
                          "contract": {"min_lot": 0.01, "max_lot": 0.05, "contract_size_oz": 100, "price_dp": 2, "lot_dp": 2, "leverage": 500},
                          "risk": {"per_trade_pct": 1.0, "single_position": True, "max_notional_usd": 25000}},
            "broker": {"enabled": False}, "account": {"initial_balance": 10000.0}}


def fresh_ex():
    pe = PE.PaperExecutor(PAPER_CFG); pe.acc = pe._fresh(); return pe


def fresh_ledger(name):
    p = TMP / name
    if p.exists():
        p.unlink()
    return p


def trade(qty=None, entry=4350.0, sl=4310.0, tp=4400.0, ctx="ctx-m4", did=None):
    return {"decision": "TRADE", "reason": "unit fixture", "chosen_opportunity": "opp_x", "regime_tags": ["TREND"],
            "decision_id": did, "context_id": ctx, "context_hash": "ch_" + ctx, "ts": "2026-09-11T00:00:00Z",
            "plan": {"direction": "LONG", "entry": entry, "stop_loss": sl, "take_profit": tp,
                     "qty_lots": qty, "confidence": 0.55, "expected_R": 2.0,
                     "thesis": "t", "counter_thesis": "c", "evidence_ids": []}}


def wait(): return {"decision": "WAIT", "reason": "no setup", "no_trade_reason": "no setup",
                    "context_id": "ctx-wait", "context_hash": "ch-wait", "ts": "2026-09-11T00:00:00Z", "plan": None}
def reject(): return {"decision": "REJECT", "reason": "bad RR", "no_trade_reason": "bad RR",
                      "context_id": "ctx-reject", "context_hash": "ch-reject", "ts": "2026-09-11T00:00:00Z", "plan": None}


def compare_account_replay(pe, led):
    st = R.replay(led, execution_mode="PAPER")
    acc = pe.account()
    closed = acc["closed_trades"]
    sum_gross = round(sum(t["gross_usd"] for t in closed), 6)
    sum_cost = round(sum(t["entry_cost_usd"] + t["exit_cost_usd"] for t in closed), 6)
    checks = {
        "balance": abs((st["account"]["balance"] or 0) - acc["balance"]) < 1e-6,
        "equity": abs((st["account"]["equity"] or 0) - acc["equity"]) < 1e-6,
        "realized==net": abs(st["net_pnl"] - acc["realized_pnl"]) < 1e-6,
        "trade_count": st["trade_count"] == len(closed),
        "gross": abs(st["gross_pnl"] - sum_gross) < 1e-6,
        "costs==commission": abs(st["commission"] - (-sum_cost)) < 1e-6,
        "open_positions": len(st["open_positions"]) == len(acc["positions"]),
    }
    return all(checks.values()), checks, st, acc


def main():
    open(LOG, "a", encoding="utf-8").write("\n" + "=" * 60 + "\n")
    log("=== Module 4 loop tests (T1–T12) ===")

    # T1 TRADE 全链
    pe = fresh_ex(); led = fresh_ledger("m4_t1.jsonl")
    out = ADP.process(trade(qty=0.02), pe, led, market_mid=4350.0, close_after=True, close_price=4360.0)
    ok1 = out["paper_orders"] == 1 and L.verify_ledger(led)[0] and R.replay(led, "PAPER")["trade_count"] == 1
    check("T1 Hermes TRADE full chain", ok1, f"orders={out['paper_orders']} exec={out['execution_result']}")

    # T2 WAIT
    pe = fresh_ex(); led = fresh_ledger("m4_t2.jsonl")
    out = ADP.process(wait(), pe, led)
    st = R.replay(led, "PAPER")
    check("T2 WAIT preserved, no trade", out["paper_orders"] == 0 and st["decisions"]["WAIT"] == 1
          and st["trade_count"] == 0, f"WAIT={st['decisions']['WAIT']}")

    # T3 REJECT (Hermes)
    pe = fresh_ex(); led = fresh_ledger("m4_t3.jsonl")
    out = ADP.process(reject(), pe, led)
    st = R.replay(led, "PAPER")
    check("T3 Hermes REJECT preserved", out["paper_orders"] == 0 and st["decisions"]["REJECT"] == 1,
          f"REJECT={st['decisions']['REJECT']}")

    # T4 execution reject (HERMES TRADE but executor rejects)
    pe = fresh_ex(); led = fresh_ledger("m4_t4.jsonl")
    out = ADP.process(trade(qty=0.5), pe, led)   # qty>max_lot → RISK_LIMIT
    evs = L.load_events(led)
    has_dec_trade = any(e["event_type"] == "DECISION" and e.get("status") == "TRADE" for e in evs)
    has_exec_rej = any(e["event_type"] == "EXECUTION_RESPONSE" and e.get("status") == "REJECTED" for e in evs)
    check("T4 Hermes TRADE vs Execution REJECT distinguished",
          out["paper_orders"] == 0 and has_dec_trade and has_exec_rej and str(out["execution_result"]).startswith("REJECTED"),
          f"exec={out['execution_result']}")

    # T5 decision immutability
    d = trade(qty=0.02)
    snap = ADP.freeze_decision(d)
    before = snap["entry_reference"]
    d["plan"]["entry"] = 9999.0; d["plan"]["stop_loss"] = 1.0; d["plan"]["direction"] = "SHORT"
    check("T5 frozen snapshot immutable", snap["entry_reference"] == before == 4350.0 and snap["side"] == "LONG",
          f"snap_entry={snap['entry_reference']} side={snap['side']}")

    # T6 causal chain
    pe = fresh_ex(); led = fresh_ledger("m4_t6.jsonl")
    ADP.process(trade(qty=0.02, ctx="ctx-chain"), pe, led, market_mid=4350.0, close_after=True, close_price=4360.0)
    evs = {e["event_id"]: e for e in L.load_events(led)}
    by_type = {}
    for e in evs.values():
        by_type.setdefault(e["event_type"], []).append(e)
    chain_ok = True
    dec = by_type["DECISION"][0]
    req = by_type["EXECUTION_REQUEST"][0]
    fill = by_type["FILL"][0]
    opn = by_type["POSITION_OPEN"][0]
    cls = by_type["POSITION_CLOSED"][0]
    chain_ok &= (req["parent_event_id"] == dec["event_id"])
    chain_ok &= (fill["parent_event_id"] == req["event_id"])
    chain_ok &= (opn["parent_event_id"] == fill["event_id"])
    chain_ok &= (cls["parent_event_id"] == opn["event_id"])
    chain_ok &= len({dec["decision_id"], req["decision_id"], fill["decision_id"], opn["decision_id"], cls["decision_id"]}) == 1
    check("T6 causal chain (decision_id + parent_event_id)", chain_ok)

    # T7 account conservation
    pe = fresh_ex(); led = fresh_ledger("m4_t7.jsonl")
    ADP.process(trade(qty=0.02), pe, led, market_mid=4350.0, close_after=True, close_price=4360.0)
    st = R.replay(led, "PAPER")
    okc, detc = R.conservation(st)
    check("T7 account conservation", okc, str(detc))

    # T8 replay equality
    eq_ok, checks, st, acc = compare_account_replay(pe, led)
    check("T8 paper account == replay", eq_ok, str(checks))

    # T9 deterministic replay
    check("T9 deterministic replay", R.replay(led, "PAPER")["state_hash"] == R.replay(led, "PAPER")["state_hash"])

    # T10 ledger integrity
    check("T10 verify_ledger PASS", L.verify_ledger(led)[0])

    # T11 environment isolation (PAPER only; no BROKER_DEMO/LIVE)
    modes = {e.get("execution_mode") for e in L.load_events(led)}
    check("T11 env isolation PAPER only", modes == {"PAPER"}, str(modes))

    # T12 V1 isolation (code scan + paper-only gate)
    refs = []
    for p in list((ROOT / "execution").glob("*.py")) + list((ROOT / "hermes").glob("*.py")):
        t = p.read_text(encoding="utf-8")
        if any(k in t for k in ("trader_v1", "live_fxtm", "hermes-trader")):
            refs.append(p.name)
    gate_ok = False
    try:
        ADP.assert_paper_only(PAPER_CFG); gate_ok = True   # 显式 PAPER 配置（与实时 config 解耦）
    except Exception:  # noqa: BLE001
        gate_ok = False
    bad_gate = False
    try:
        ADP.assert_paper_only({"execution": {"execution_mode": "BROKER_DEMO", "live_trading": False,
                                             "broker_demo_enabled": False}, "broker": {"enabled": False}})
    except ADP.RefuseToStart:
        bad_gate = True
    check("T12 V1 isolation + paper-only gate", (not refs) and gate_ok and bad_gate,
          f"v1_refs={refs} gate_ok={gate_ok} refuses_nonpaper={bad_gate}")

    log(f"=== RESULT: {sum(_res)}/{len(_res)} PASS ===")
    return 0 if all(_res) else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
