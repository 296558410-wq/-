# -*- coding: utf-8 -*-
"""V2 回归 — 价格空间转换层（GC=F signal → XAUUSD execution）。

覆盖任务书 §九 Case A-F + §十五 单元/回归:
  A SHORT + 转换后 SL 正确 → order valid
  B SHORT + 转换后 SL 错误侧 → local reject
  C LONG  + 转换后 SL 错误侧 → local reject
  D basis 缺失 → fail-closed
  E basis stale → fail-closed
  F basis 异常跳变 → fail-closed
另: 换算数学 / 精度(tick) / R:R / risk / sizing(execution space) / 集成(process 写 execution_* 且保留 signal_*)。
日志: logs/test_price_space_conversion.log
"""
from __future__ import annotations
import json
import sys
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "execution"))
sys.path.insert(0, str(ROOT / "ledger"))
import price_space as PS  # noqa: E402
import hermes_paper_adapter as ADP  # noqa: E402
import paper_executor as PE  # noqa: E402
import ledger as L  # noqa: E402
import replay as R  # noqa: E402

LOGS = ROOT / "logs"; LOGS.mkdir(exist_ok=True)
LOG = LOGS / "test_price_space_conversion.log"
_RES = []
TMP = Path(tempfile.mkdtemp(prefix="ps_test_"))


def log(s):
    line = f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] {s}"
    print(line)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def check(n, c, d=""):
    _RES.append(bool(c))
    log(f"{'PASS' if c else 'FAIL'} | {n} {d}")


def _iso(dt=None):
    return (dt or datetime.now(timezone.utc)).isoformat()


CFG = {**PS.DEFAULT_CFG, "enabled": True, "max_basis_age_seconds": 300,
       "max_abs_basis_usd": 60.0, "max_basis_jump_usd": 25.0}
NOW = datetime.now(timezone.utc).timestamp()
SHORT = {"direction": "SHORT", "entry": 4351.82, "stop_loss": 4369.23, "take_profit": 4323.96}
LONG = {"direction": "LONG", "entry": 4300.0, "stop_loss": 4282.61, "take_profit": 4327.5}


def prep(plan, *, basis=13.0, age=5, recent=None, live_bid=None, live_ask=None, cfg=CFG):
    gc = plan["entry"]
    spot = gc + basis
    return PS.prepare(plan, gc_price=gc, gc_ts=_iso(datetime.now(timezone.utc) - timedelta(seconds=age)),
                      spot_price=spot, spot_ts=_iso(datetime.now(timezone.utc) - timedelta(seconds=age)),
                      spot_source="test_pair", now_ts=NOW, cfg=cfg, recent_basis=recent,
                      live_bid=live_bid, live_ask=live_ask)


def main():
    # ---------- 单元: 换算数学 ----------
    c = PS.convert("SHORT", 4351.82, 4369.23, 4323.96, 13.0)
    check("convert SHORT +basis", c == {"execution_entry": 4364.82, "execution_stop_loss": 4382.23,
                                        "execution_take_profit": 4336.96}, str(c))
    c2 = PS.convert("LONG", 4300.0, 4282.61, 4327.5, -4.5)
    check("convert LONG -basis", c2 == {"execution_entry": 4295.5, "execution_stop_loss": 4278.11,
                                        "execution_take_profit": 4323.0}, str(c2))
    b = PS.convert("SHORT", 4351.82, 4362.5, 4335.0, 12.926)
    check("precision dp=2", b["execution_entry"] == 4364.75 and b["execution_stop_loss"] == 4375.43, str(b))

    # ---------- 单元: basis 解析 fail-closed ----------
    def _rb(gc, spot, age=5, basis_ts_age=None, recent=None):
        return PS.resolve_basis(gc_price=gc, spot_price=spot,
                                gc_ts=_iso(datetime.now(timezone.utc) - timedelta(seconds=age)),
                                spot_ts=_iso(datetime.now(timezone.utc) - timedelta(seconds=age)),
                                now_ts=NOW, max_age_s=300, max_abs_usd=60.0,
                                recent_basis=recent, max_jump_usd=25.0)
    gc = SHORT["entry"]
    for code, fn in [
            ("BASIS_UNAVAILABLE", lambda: _rb(gc, None)),
            ("BASIS_STALE", lambda: _rb(gc, gc + 13.0, age=999)),
            ("BASIS_ABS_SANITY", lambda: _rb(gc, gc + 82.52)),
            ("BASIS_JUMP", lambda: _rb(gc, gc + 45.0, recent=[13.0, 13.4, 6.2, 21.4, 5.7]))]:
        try:
            fn()
            check(f"basis {code} raises", False, "no raise")
        except PS.PriceSpaceError as e:
            check(f"basis {code} raises", e.code == code, e.code)

    # ---------- Case A: SHORT + 转换后 SL 正确 ----------
    rec = prep(SHORT, basis=13.0)
    check("A SHORT valid (SL correct side)", rec["valid"] and rec["execution_stop_loss"] > rec["execution_entry"]
          and rec["execution_take_profit"] < rec["execution_entry"], json.dumps({k: rec.get(k) for k in
          ("valid", "execution_entry", "execution_stop_loss", "execution_take_profit", "basis")}))
    check("A rr/risk recomputed (execution space)", rec.get("rr") is not None and rec.get("risk_usd_per_lot") is not None,
          f"rr={rec.get('rr')} risk/lot={rec.get('risk_usd_per_lot')}")

    # ---------- Case B: SHORT + 转换后 SL 错误侧(相对市价) ----------
    # 市价已升过转换后 SL → 送 broker 必 10016；本层必须 local reject
    rB = prep(SHORT, basis=13.0, live_bid=4390.0, live_ask=4390.2)
    check("B SHORT SL at/below market -> local reject", (not rB["valid"]) and
          rB["reject_code"] == "INVALID_EXECUTION_PRICE_SPACE" and
          "short_sl" in str(rB["reject_detail"].get("reason")), f"code={rB['reject_code']} det={rB['reject_detail']}")

    # ---------- Case C: LONG + 转换后 SL 错误侧 ----------
    rC = prep(LONG, basis=-3.0, live_bid=4270.0, live_ask=4270.2)  # exec SL ~4279.6 > market 4270 → wrong side
    check("C LONG SL at/above market -> local reject", (not rC["valid"]) and
          rC["reject_code"] == "INVALID_EXECUTION_PRICE_SPACE", f"code={rC['reject_code']} det={rC['reject_detail']}")

    # ---------- Case D: basis 缺失 ----------
    rD = PS.prepare(SHORT, gc_price=SHORT["entry"], gc_ts=_iso(), spot_price=None, spot_ts=_iso(),
                    now_ts=NOW, cfg=CFG)
    check("D missing basis -> fail-closed", (not rD["valid"]) and rD["reject_code"] == "BASIS_UNAVAILABLE",
          rD["reject_code"])

    # ---------- Case E: basis stale ----------
    rE = prep(SHORT, basis=13.0, age=9999)
    check("E stale basis -> fail-closed", (not rE["valid"]) and rE["reject_code"] == "BASIS_STALE", rE["reject_code"])

    # ---------- Case F: basis 异常跳变 ----------
    rF = prep(SHORT, basis=45.0, recent=[13.0, 13.4, 6.2, 21.4, 5.7])
    check("F abnormal jump -> fail-closed", (not rF["valid"]) and rF["reject_code"] == "BASIS_JUMP", rF["reject_code"])

    # ---------- 精度/tick ----------
    okp, codep, _ = PS.validate_execution("SHORT", 4364.82, 4382.23, 4336.96, tick=0.01)
    check("validate on-tick OK", okp, str(codep))
    okq, codeq, detq = PS.validate_execution("SHORT", 4364.825, 4382.23, 4336.96, tick=0.01)
    check("validate off-tick reject", (not okq) and codeq == "INVALID_EXECUTION_PRICE_SPACE", str(detq))

    # ---------- sizing 在 execution space ----------
    pe = PE.PaperExecutor({"execution": {"execution_mode": "PAPER", "live_trading": False,
                                         "contract": {"min_lot": 0.01, "max_lot": 0.05,
                                                      "contract_size_oz": 100, "price_dp": 2, "lot_dp": 2},
                                         "risk": {"per_trade_pct": 2.0, "max_notional_usd": 25000}}})
    q = pe.size_position_raw(rec["execution_entry"], rec["execution_stop_loss"], equity=1000.0)
    q_sig = pe.size_position_raw(SHORT["entry"], SHORT["stop_loss"], equity=1000.0)
    check("sizing(exec dist) == sizing(signal dist) : 平移不变", q == q_sig == 0.01, f"{q}/{q_sig}")

    # ---------- 集成: process 写 execution_* 且保留 signal_* ----------
    PE.ACCOUNT_P = TMP / "acc1.json"; PE.EXECUTIONS_P = TMP / "exec1.jsonl"
    pe1 = PE.PaperExecutor({"account": {"initial_balance": 1000.0},
                            "execution": {"execution_mode": "PAPER", "live_trading": False,
                                          "contract": {"min_lot": 0.01, "max_lot": 0.05,
                                                       "contract_size_oz": 100, "price_dp": 2, "lot_dp": 2},
                                          "risk": {"per_trade_pct": 2.0, "max_notional_usd": 25000}}})
    led1 = TMP / "ledger1.jsonl"
    dec = {"decision": "TRADE", "ts": _iso(), "context_id": "ctx_t1", "context_hash": "h1",
           "reason": "test", "plan": {"direction": "SHORT", "entry": 4351.82, "stop_loss": 4369.23,
                                      "take_profit": 4323.96, "confidence": 0.55}}
    out1 = ADP.process(dec, pe1, led1, market_mid=SHORT["entry"], input_hash="h1", execution_plan=rec)
    evs1 = L.load_events(led1)
    d_ev = next(e for e in evs1 if e["event_type"] == "DECISION")
    req_ev = next(e for e in evs1 if e["event_type"] == "EXECUTION_REQUEST")
    check("integration executed", out1["execution_result"] == "EXECUTED", out1["execution_result"])
    check("DECISION keeps signal_*", d_ev.get("signal_entry") == 4351.82 and d_ev.get("signal_stop_loss") == 4369.23,
          f"sig={d_ev.get('signal_entry')}")
    check("DECISION adds execution_*", d_ev.get("execution_entry") == rec["execution_entry"]
          and d_ev.get("execution_stop_loss") == rec["execution_stop_loss"], f"exec={d_ev.get('execution_entry')}")
    check("DECISION records basis/provenance", d_ev.get("basis") == rec["basis"]
          and d_ev.get("source_hash") and d_ev.get("conversion_version") == PS.CONVERSION_VERSION,
          f"basis={d_ev.get('basis')}")
    check("EXECUTION_REQUEST uses execution price", req_ev.get("requested_price") == rec["execution_entry"]
          and req_ev.get("stop_loss") == rec["execution_stop_loss"], f"req={req_ev.get('requested_price')}")
    pos = pe1.acc["positions"][0]
    check("opened in execution space (not GC)", abs(pos["entry"] - rec["execution_entry"]) < 1.0
          and abs(pos["entry"] - 4351.82) > 5, f"entry={pos['entry']}")
    check("ledger verify OK", L.verify_ledger(led1)[0])

    # ---------- 集成: fail-closed reject ----------
    PE.ACCOUNT_P = TMP / "acc2.json"; PE.EXECUTIONS_P = TMP / "exec2.jsonl"
    pe2 = PE.PaperExecutor({"account": {"initial_balance": 1000.0},
                            "execution": {"execution_mode": "PAPER", "live_trading": False,
                                          "contract": {"min_lot": 0.01, "max_lot": 0.05,
                                                       "contract_size_oz": 100, "price_dp": 2, "lot_dp": 2},
                                          "risk": {"per_trade_pct": 2.0, "max_notional_usd": 25000}}})
    led2 = TMP / "ledger2.jsonl"
    out2 = ADP.process(dec, pe2, led2, market_mid=SHORT["entry"], input_hash="h1", execution_reject=rF)
    evs2 = L.load_events(led2)
    check("fail-closed -> REJECTED:BASIS_JUMP", out2["execution_result"] == "REJECTED:BASIS_JUMP", out2["execution_result"])
    check("fail-closed did NOT open position", len(pe2.acc["positions"]) == 0)
    check("fail-closed emits ORDER_REJECTED", any(e["event_type"] == "ORDER_REJECTED" for e in evs2))

    # ---------- 回归: 不传 execution_plan 时字段不写(逐字节兼容) ----------
    PE.ACCOUNT_P = TMP / "acc3.json"; PE.EXECUTIONS_P = TMP / "exec3.jsonl"
    pe3 = PE.PaperExecutor({"account": {"initial_balance": 1000.0},
                            "execution": {"execution_mode": "PAPER", "live_trading": False,
                                          "contract": {"min_lot": 0.01, "max_lot": 0.05,
                                                       "contract_size_oz": 100, "price_dp": 2, "lot_dp": 2},
                                          "risk": {"per_trade_pct": 2.0, "max_notional_usd": 25000}}})
    led3 = TMP / "ledger3.jsonl"
    ADP.process(dec, pe3, led3, market_mid=SHORT["entry"], input_hash="h1")
    d3 = next(e for e in L.load_events(led3) if e["event_type"] == "DECISION")
    check("disabled: no price-space fields", ("execution_entry" not in d3) and ("signal_entry" not in d3)
          and d3.get("requested_price") == 4351.82, f"entry={d3.get('requested_price')}")

    log(f"=== RESULT: {sum(_RES)}/{len(_RES)} PASS ===")
    return 0 if all(_RES) else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
