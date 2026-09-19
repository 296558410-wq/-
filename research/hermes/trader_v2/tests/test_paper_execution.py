# -*- coding: utf-8 -*-
"""模块 2 验收测试（LOCAL PAPER, 12 项）—— 更新至"不静默缩仓"语义。

日志: logs/test_paper_execution.log
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
PE.ACCOUNT_P = TMP / "paper_account_test.json"
PE.EXECUTIONS_P = TMP / "paper_executions_test.jsonl"
LOGS = ROOT / "logs"; LOGS.mkdir(exist_ok=True)
LOG = LOGS / "test_paper_execution.log"
_res = []


def log(s):
    line = f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] {s}"
    print(line)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def check(name, cond, detail=""):
    _res.append(bool(cond)); log(f"{'PASS' if cond else 'FAIL'} | {name} {detail}")


def mk(commission=0.0, mode="PAPER", live=False, initial=10000.0, max_notional=25000):
    return {"execution": {"execution_mode": mode, "live_trading": live, "broker_demo_enabled": False,
                          "cost_model": {"spread_bps_typical": 0.35, "slippage_bps": 0.30, "latency_ms": 250,
                                         "commission_per_lot_usd": commission},
                          "contract": {"min_lot": 0.01, "max_lot": 0.05, "contract_size_oz": 100, "price_dp": 2, "lot_dp": 2, "leverage": 500},
                          "risk": {"per_trade_pct": 1.0, "single_position": True, "max_notional_usd": max_notional}},
            "account": {"initial_balance": initial}}


def ex(**kw):
    pe = PE.PaperExecutor(mk(**kw)); pe.acc = pe._fresh(); return pe


def main():
    open(LOG, "a", encoding="utf-8").write("\n" + "=" * 60 + "\n")
    log("=== Module 2 LOCAL PAPER execution tests (v2) ===")
    mid = 4350.0

    # 1 LONG open: 不利成交(>=mid) + 成本>0
    pe = ex(); r = pe.open("LONG", mid, sl=4340.0, tp=4360.0, plan_id="TP-1", qty_lots=0.02)
    p = r["position"]
    check("1 LONG open adverse fill + cost", r["ok"] and p["entry"] > mid and p["entry_cost_usd"] > 0,
          f"fill={p['entry']} cost={p['entry_cost_usd']:.3f} qty={p['qty_lots']}")

    # 2 SHORT open: 不利成交(<=mid)
    pe = ex(); r = pe.open("SHORT", mid, sl=4360.0, tp=4340.0, plan_id="TP-2", qty_lots=0.02)
    check("2 SHORT open adverse fill", r["ok"] and r["position"]["entry"] < mid, f"fill={r['fill']}")

    # 3 mark 浮盈符号
    pe = ex(); pe.open("LONG", mid, sl=4340.0, tp=4360.0, plan_id="TP-3", qty_lots=0.02); pe.mark(mid + 5)
    check("3 mark unrealized PnL sign", pe.acc["unrealized_pnl"] > 0 and pe.acc["equity"] > pe.acc["balance"],
          f"un={pe.acc['unrealized_pnl']}")

    # 4 close LONG 净盈亏
    pe = ex(); r = pe.open("LONG", mid, sl=4340.0, tp=4370.0, plan_id="TP-4", qty_lots=0.02)
    t = pe.close(r["position"]["position_id"], mid + 20)["trade"]
    check("4 close LONG net PnL", t["net_usd"] > 0 and t["net_usd"] < t["gross_usd"] and t["exit_cost_usd"] > 0,
          f"net={t['net_usd']} gross={t['gross_usd']}")

    # 5 close SHORT 净盈亏
    pe = ex(); r = pe.open("SHORT", mid, sl=4360.0, tp=4300.0, plan_id="TP-5", qty_lots=0.02)
    t = pe.close(r["position"]["position_id"], mid - 20)["trade"]
    check("5 close SHORT net PnL", t["net_usd"] > 0, f"net={t['net_usd']}")

    # 6 SL 触发 → 平仓, 亏损
    pe = ex(); pe.open("LONG", mid, sl=4345.0, tp=4360.0, plan_id="TP-6", qty_lots=0.02)
    pe.check_exits(4344.0)
    cl = pe.acc["closed_trades"][-1]
    check("6 SL trigger close", cl["reason"] == "SL" and cl["net_usd"] < 0, f"net={cl['net_usd']}")

    # 7 TP 触发 → 平仓, 盈利
    pe = ex(); pe.open("LONG", mid, sl=4340.0, tp=4360.0, plan_id="TP-7", qty_lots=0.02)
    pe.check_exits(4361.0)
    cl = pe.acc["closed_trades"][-1]
    check("7 TP trigger close", cl["reason"] == "TP" and cl["net_usd"] > 0, f"net={cl['net_usd']}")

    # 8 latency 记录 + commission 计入
    pe = ex(commission=3.5); r = pe.open("LONG", mid, sl=4340.0, tp=4360.0, plan_id="TP-8", qty_lots=0.02)
    p = r["position"]
    check("8 latency recorded + commission applied", p["latency_ms"] == 250 and p["entry_cost_usd"] >= 3.5 * 0.02,
          f"lat={p['latency_ms']} cost={p['entry_cost_usd']:.3f}")

    # 9 RISK_LIMIT: 拒绝而非静默缩仓（各用独立账户, 避免单仓干扰）
    pe_a = ex()
    ok_normal = pe_a.open("LONG", mid, sl=4340.0, tp=4360.0, plan_id="TP-9a", qty_lots=0.02)["ok"]
    pe_b = ex()
    r_big = pe_b.open("LONG", mid, sl=4340.0, tp=4360.0, plan_id="TP-9b", qty_lots=0.5)
    pe_c = ex(max_notional=5000)
    r_not = pe_c.open("LONG", mid, sl=4300.0, tp=4400.0, plan_id="TP-9c", qty_lots=0.05)
    check("9 RISK_LIMIT rejects (no silent resize)",
          ok_normal and (not r_big["ok"]) and r_big["failure_code"] == "RISK_LIMIT"
          and (not r_not["ok"]) and r_not["failure_code"] == "RISK_LIMIT",
          f"big={r_big.get('failure_code')} notional={r_not.get('failure_code')}")

    # 10 单仓约束(每 symbol)
    pe = ex(); pe.open("LONG", mid, sl=4340.0, tp=4360.0, plan_id="TP-10a", qty_lots=0.02)
    r2 = pe.open("LONG", mid, sl=4340.0, tp=4360.0, plan_id="TP-10b", qty_lots=0.02)
    check("10 single-position enforced", (not r2["ok"]) and r2["failure_code"] == "POSITION_BUSY", f"{r2.get('failure_code')}")

    # 11 账户守恒
    pe = ex()
    for i in range(3):
        r = pe.open("LONG", mid, sl=4340.0, tp=4400.0, plan_id=f"TP-11-{i}", qty_lots=0.02)
        pe.close(r["position"]["position_id"], mid + 10)
    ok, det = pe.conservation_ok()
    check("11 account conservation", ok, str(det))

    # 12 安全门 + V1隔离 + 凭据不入配置
    refused = False
    try:
        PE.PaperExecutor(mk(mode="BROKER_DEMO")).open("LONG", mid, 4340.0, 4360.0, "TP-12")
    except PE.RefuseExecution as e:
        refused = (e.code == "NON_PAPER_MODE")
    import fxtm_demo_adapter as _FA
    _orig_cfg = _FA._load_cfg
    _FA._load_cfg = lambda: {"execution": {"execution_mode": "PAPER", "broker_demo_enabled": False}, "broker": {"enabled": False}}
    ad = FXTMDemoAdapter(); refused_adapter = False
    try:
        ad.place_market_order("XAUUSD", "LONG", 0.01)
    except RefuseConnection:
        refused_adapter = True
    _FA._load_cfg = _orig_cfg
    cfg = json.loads((ROOT / "config" / "v2_config.json").read_text(encoding="utf-8"))
    leak = False
    def _scan(o):
        global leak
        if isinstance(o, dict):
            for k, v in o.items():
                if str(k).lower() in ("password", "login", "investor_password", "demo_password"): leak = True
                _scan(v)
        elif isinstance(o, list):
            for v in o: _scan(v)
    _scan(cfg)
    check("12 safety gate + isolation", refused and refused_adapter and not leak,
          f"paper={refused} adapter={refused_adapter} no_cred_keys={not leak}")

    ok = all(_res)
    log(f"=== RESULT: {sum(_res)}/{len(_res)} PASS ===")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
