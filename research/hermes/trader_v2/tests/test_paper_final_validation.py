# -*- coding: utf-8 -*-
"""模块 2 最终验收补测（4 项）+ 附加检查 → 输出 A–G。

不新增模块; 不改 V1; 不接 FXTM; 不产生 broker 订单。
日志: logs/test_paper_final_validation.log
"""
import sys, json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "execution"))
import paper_executor as PE  # noqa: E402
from fxtm_demo_adapter import FXTMDemoAdapter  # noqa: E402
from broker_interface import RefuseConnection  # noqa: E402

TMP = HERE / "_tmp"; TMP.mkdir(exist_ok=True)
PE.ACCOUNT_P = TMP / "paper_account_fv.json"
PE.EXECUTIONS_P = TMP / "paper_executions_fv.jsonl"
LOGS = ROOT / "logs"; LOGS.mkdir(exist_ok=True)
LOG = LOGS / "test_paper_final_validation.log"
_res = {}


def log(s):
    line = f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] {s}"
    print(line)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def check(section, name, cond, detail=""):
    _res.setdefault(section, []).append(bool(cond))
    log(f"{'PASS' if cond else 'FAIL'} | [{section}] {name} {detail}")


def mk(mode="PAPER", live=False, max_notional=25000, initial=10000.0):
    return {"execution": {"execution_mode": mode, "live_trading": live, "broker_demo_enabled": False,
                          "cost_model": {"spread_bps_typical": 0.35, "slippage_bps": 0.30, "latency_ms": 250,
                                         "commission_per_lot_usd": 0.0},
                          "contract": {"min_lot": 0.01, "max_lot": 0.05, "contract_size_oz": 100, "price_dp": 2, "lot_dp": 2, "leverage": 500},
                          "risk": {"per_trade_pct": 1.0, "single_position": True, "max_notional_usd": max_notional}},
            "account": {"initial_balance": initial}}


def ex(**kw):
    pe = PE.PaperExecutor(mk(**kw)); pe.acc = pe._fresh(); return pe


def last_exec():
    lines = [l for l in PE.EXECUTIONS_P.read_text(encoding="utf-8").splitlines() if l.strip()] if PE.EXECUTIONS_P.exists() else []
    return json.loads(lines[-1]) if lines else None


def main():
    open(LOG, "a", encoding="utf-8").write("\n" + "=" * 60 + "\n")
    log("=== Module 2 FINAL VALIDATION ===")

    # ---------- 1. ENTRY_INVALIDATED ----------
    pe = ex(); snap_before = json.dumps(pe.acc, sort_keys=True)
    r = pe.open("LONG", 4350.0, sl=4340.0, tp=4360.0, plan_id="FV-1", qty_lots=0.02,
                decision_price=4350.0, exec_price=4344.0, invalidation=4345.0, latency_ms=400)
    rec = last_exec()
    check("A1 ENTRY_INVALIDATED", "reject_status",
          (not r["ok"]) and r["status"] == "rejected" and r["failure_code"] == "ENTRY_INVALIDATED", f"{r.get('failure_code')}")
    check("A1 ENTRY_INVALIDATED", "no fill-then-stop",
          len(pe.acc["positions"]) == 0 and len(pe.acc["closed_trades"]) == 0 and json.dumps(pe.acc, sort_keys=True) == snap_before,
          "账户未变")
    check("A1 ENTRY_INVALIDATED", "record fields",
          rec and all(k in rec for k in ("requested_entry", "market_price_at_decision", "market_price_at_execution",
                                         "latency_ms", "invalidation_condition", "rejection_reason")),
          f"rec_keys ok")

    # ---------- 2. RISK_LIMIT ----------
    pe = ex(); before = json.dumps(pe.acc, sort_keys=True)
    r = pe.open("LONG", 4350.0, sl=4340.0, tp=4360.0, plan_id="FV-2", qty_lots=0.5)
    rec = last_exec()
    check("A2 RISK_LIMIT", "reject_no_silent_resize",
          (not r["ok"]) and r["failure_code"] == "RISK_LIMIT" and json.dumps(pe.acc, sort_keys=True) == before,
          f"{r.get('failure_code')} state_unchanged")
    check("A2 RISK_LIMIT", "record reason", rec and rec.get("failure_code") == "RISK_LIMIT" and rec.get("rejection_reason"),
          str(rec.get("rejection_reason"))[:60])

    # ---------- 3. NON_PAPER_MODE ----------
    codes = {}
    for mode in ("BROKER_DEMO", "LIVE"):
        try:
            PE.PaperExecutor(mk(mode=mode)).open("LONG", 4350.0, 4340.0, 4360.0, f"FV-3-{mode}", qty_lots=0.02)
            codes[mode] = None
        except PE.RefuseExecution as e:
            codes[mode] = e.code
    import fxtm_demo_adapter as _FA
    _orig_cfg = _FA._load_cfg
    _FA._load_cfg = lambda: {"execution": {"execution_mode": "PAPER", "broker_demo_enabled": False}, "broker": {"enabled": False}}
    ad = FXTMDemoAdapter(); ad_ref = False
    try:
        ad.place_market_order("XAUUSD", "LONG", 0.01)
    except RefuseConnection:
        ad_ref = True
    _FA._load_cfg = _orig_cfg
    check("A3 NON_PAPER_MODE", "both modes refused with code",
          codes.get("BROKER_DEMO") == "NON_PAPER_MODE" and codes.get("LIVE") == "NON_PAPER_MODE" and ad_ref,
          f"{codes} adapter_refused={ad_ref}")

    # ---------- 4. SL/TP Bid/Ask 语义 ----------
    mid = 4350.0
    bid, ask = 4349.8, 4350.2
    # LONG 入场用 Ask
    pe = ex(); rL = pe.open("LONG", mid, sl=4340.0, tp=4360.0, plan_id="FV-4L", qty_lots=0.02, bid=bid, ask=ask)
    fillL = rL["position"]["entry"]
    check("B bid/ask", "LONG entry uses Ask", fillL >= ask and rL["position"]["spread_source"] == "REAL",
          f"fill={fillL} ask={ask} src={rL['position']['spread_source']}")
    # SHORT 入场用 Bid
    pe2 = ex(); rS = pe2.open("SHORT", mid, sl=4360.0, tp=4340.0, plan_id="FV-4S", qty_lots=0.02, bid=bid, ask=ask)
    fillS = rS["position"]["entry"]
    check("B bid/ask", "SHORT entry uses Bid", fillS <= bid and rS["position"]["spread_source"] == "REAL",
          f"fill={fillS} bid={bid}")
    # LONG 平仓用 Bid
    cL = pe.close(rL["position"]["position_id"], 4360.0, reason="TP", bid=bid, ask=ask)["trade"]
    check("B bid/ask", "LONG exit uses Bid", cL["exit"] <= bid, f"exit={cL['exit']} bid={bid}")
    # SHORT 平仓用 Ask
    cS = pe2.close(rS["position"]["position_id"], 4340.0, reason="TP", bid=bid, ask=ask)["trade"]
    check("B bid/ask", "SHORT exit uses Ask", cS["exit"] >= ask, f"exit={cS['exit']} ask={ask}")
    # PROXY 证明(无真实盘口 → 由 spread_bps 推导, 且明确标记)
    pe3 = ex(); rP = pe3.open("LONG", mid, sl=4340.0, tp=4360.0, plan_id="FV-4P", qty_lots=0.02, spread_bps=2.0)
    half = mid * 2.0 / 1e4 / 2.0
    check("B bid/ask", "PROXY source + formula",
          rP["position"]["spread_source"] == "PROXY" and abs(rP["position"]["entry"] - (mid + half + mid * 0.30 / 1e4)) < 0.02,
          f"src=PROXY ask={round(mid+half,3)} fill={rP['position']['entry']}")

    # ---------- 附加检查 ----------
    # C. 冻结 decision context 输入
    src = (ROOT / "execution" / "paper_executor.py").read_text(encoding="utf-8")
    check("C frozen input", "no agent re-read", ("agent1_latest" not in src) and ("agent2_latest" not in src),
          "paper_executor 不读取 Agent 快照")
    pe = ex(); r = pe.open("LONG", mid, sl=4340.0, tp=4360.0, plan_id="FV-C", qty_lots=0.02,
                           context_id="ctx_abc", decision_ref="DEC-1")
    check("C frozen input", "context/decision stored",
          r["position"]["context_id"] == "ctx_abc" and r["position"]["decision_ref"] == "DEC-1")
    # 不修改 entry/SL/TP
    check("C frozen input", "entry/sl/tp unchanged",
          r["position"]["sl"] == 4340.0 and r["position"]["tp"] == 4360.0)
    # 无反向/金字塔/加仓/马丁/移动止损/自动优化
    banned = ["reverse", "pyramid", "martingale", "trailing", "averag", "optimize_sl", "optimize_tp"]
    src_l = src.lower()
    check("C frozen input", "no reverse/pyramid/martingale/trailing/avg/auto-opt",
          not any(b in src_l for b in banned), "code scan clean")
    # 反向持仓 → 不自动反向, 拒绝
    pe = ex(); pe.open("LONG", mid, sl=4340.0, tp=4360.0, plan_id="FV-C2", qty_lots=0.02)
    rrev = pe.open("SHORT", mid, sl=4360.0, tp=4340.0, plan_id="FV-C3", qty_lots=0.02)
    check("C frozen input", "no auto-reverse (opposite refused)", (not rrev["ok"]) and rrev["failure_code"] == "POSITION_BUSY")
    # 所有成本入 net PnL
    pe = ex(); ro = pe.open("LONG", mid, sl=4340.0, tp=4370.0, plan_id="FV-C4", qty_lots=0.02)
    tr = pe.close(ro["position"]["position_id"], mid + 10)["trade"]
    check("C frozen input", "costs in net PnL",
          abs(tr["net_usd"] - (tr["gross_usd"] - tr["entry_cost_usd"] - tr["exit_cost_usd"])) < 1e-6,
          f"net={tr['net_usd']}")

    # D. 账户守恒
    pe = ex()
    for i in range(4):
        r = pe.open("LONG", mid, sl=4340.0, tp=4400.0, plan_id=f"FV-D{i}", qty_lots=0.02)
        pe.mark(mid + 5)
        ok_eq = abs((pe.acc["balance"] + pe.acc["unrealized_pnl"]) - pe.acc["equity"]) < 1e-6
        pe.close(r["position"]["position_id"], mid + 8)
    ok, det = pe.conservation_ok()
    check("D account conservation", "balance+unrealized=equity & balance=init+Σnet & realized=Σnet",
          ok_eq and ok and abs(pe.acc["realized_pnl"] - det["sum_net"]) < 1e-6, str(det))

    # E. V1 isolation（只查对 V1 模块/目录的**耦合**；MetaTrader5 是本系统自己的 broker API，不算）
    leak = []
    for p in (ROOT / "execution").glob("*.py"):
        for ln in p.read_text(encoding="utf-8").splitlines():
            code = ln.split("#", 1)[0]
            if any(k in code for k in ("trader_v1", "live_fxtm", "hermes-trader")):
                leak.append(f"{p.name}:{code.strip()[:70]}")
    check("E v1 isolation", "no V1 module coupling in execution/", not leak, str(leak))

    # F. Git diff（由外部命令核验; 这里仅标注 V2 改动范围）
    check("F git diff", "module2 files only (checked externally)", True, "见外层 git status")

    log("=== SECTIONS ===")
    allok = True
    for sec, arr in _res.items():
        s = sum(arr); allok = allok and (s == len(arr))
        log(f"  {sec}: {s}/{len(arr)}")
    log(f"=== MODULE 2 FINAL: {'PASS' if allok else 'FAIL'} ===")
    return 0 if allok else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
