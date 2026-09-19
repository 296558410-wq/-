# -*- coding: utf-8 -*-
"""Module 3 测试 —— Ledger 完整性 + Replay 确定性 + 环境隔离 + 迁移兼容 (Test 1–10)。

日志: logs/test_ledger_replay.log
"""
import sys, json, hashlib
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "ledger"))
import ledger as L  # noqa: E402
import replay as R  # noqa: E402
import migrate_demo_calibration as M  # noqa: E402

TMP = HERE / "_tmp"; TMP.mkdir(exist_ok=True)
LOGS = ROOT / "logs"; LOGS.mkdir(exist_ok=True)
LOG = LOGS / "test_ledger_replay.log"
_res = []


def log(s):
    line = f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] {s}"
    print(line)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def check(n, c, d=""):
    _res.append(bool(c)); log(f"{'PASS' if c else 'FAIL'} | {n} {d}")


def fresh(name):
    p = TMP / name
    if p.exists():
        p.unlink()
    return p


def build(led, init=10000.0, include_wait=True, include_reject=True):
    L.append_event(L.new_event("ACCOUNT_INIT", environment="PAPER", execution_mode="PAPER",
                               account_balance=init, currency="USD"), led)
    if include_wait:
        L.append_event(L.new_event("DECISION", environment="PAPER", execution_mode="PAPER",
                                   decision_id="D-WAIT", status="WAIT", message="no setup"), led)
    L.append_event(L.new_event("DECISION", environment="PAPER", execution_mode="PAPER",
                               decision_id="D-1", status="TRADE"), led)
    L.append_event(L.new_event("POSITION_OPEN", environment="PAPER", execution_mode="PAPER",
                               decision_id="D-1", position_id="P-1", symbol="XAUUSD", side="LONG",
                               volume=0.02, fill_price=4350.0), led)
    L.append_event(L.new_event("POSITION_CLOSED", environment="PAPER", execution_mode="PAPER",
                               position_id="P-1", symbol="XAUUSD", side="LONG", volume=0.02,
                               fill_price=4360.0, gross_pnl=10.0, commission=-0.22, swap=0.0, net_pnl=9.78), led)
    if include_reject:
        L.append_event(L.new_event("DECISION", environment="PAPER", execution_mode="PAPER",
                                   decision_id="D-2", status="TRADE"), led)
        L.append_event(L.new_event("EXECUTION_REQUEST", environment="PAPER", execution_mode="PAPER",
                                   decision_id="D-2", symbol="XAUUSD", side="BUY", volume=0.01), led)
        L.append_event(L.new_event("ORDER_REJECTED", environment="PAPER", execution_mode="PAPER",
                                   decision_id="D-2", retcode=10027, message="AutoTrading disabled"), led)


def main():
    open(LOG, "a", encoding="utf-8").write("\n" + "=" * 60 + "\n")
    log("=== Module 3 ledger/replay tests ===")
    led = fresh("ledger_test.jsonl")
    build(led)

    # Test1 Append
    ok, det = L.verify_ledger(led)
    check("T1 append/verify PASS", ok, str(det))

    # Test5 Determinism
    s1 = R.replay(led); s2 = R.replay(led)
    check("T5 replay determinism", s1["state_hash"] == s2["state_hash"], s1["state_hash"][:12])

    # Test7 WAIT preserved & trade_count
    check("T7 WAIT preserved + no trade", s1["decisions"]["WAIT"] == 1 and s1["trade_count"] == 1,
          f"WAIT={s1['decisions']['WAIT']} trades={s1['trade_count']}")

    # Test8 REJECT not a trade
    check("T8 REJECT not counted as trade", s1["orders_rejected"] == 1 and s1["trade_count"] == 1,
          f"rejected={s1['orders_rejected']} trades={s1['trade_count']}")

    # Test10 Cost conservation
    g, c, sw, n = s1["gross_pnl"], s1["commission"], s1["swap"], s1["net_pnl"]
    okc, detc = R.conservation(s1)
    check("T10 cost conservation", abs(n - (g + c + sw)) < 1e-9 and okc, f"net={n} g+c+s={round(g+c+sw,6)} cons={detc['ok']}")

    # Test2 Tamper
    lines = led.read_text(encoding="utf-8").splitlines()
    obj = json.loads(lines[2]); obj["volume"] = 999
    lines[2] = json.dumps(obj, ensure_ascii=False)
    tam = fresh("ledger_tamper.jsonl"); tam.write_text("\n".join(lines) + "\n", encoding="utf-8")
    ok2, d2 = L.verify_ledger(tam)
    check("T2 tamper detected", (not ok2) and "hash_mismatch" in d2.get("reason", ""), str(d2.get("reason")))

    # Test3 Delete
    lines = led.read_text(encoding="utf-8").splitlines()
    dl = fresh("ledger_delete.jsonl"); dl.write_text("\n".join(lines[:3] + lines[4:]) + "\n", encoding="utf-8")
    ok3, d3 = L.verify_ledger(dl)
    check("T3 delete detected", not ok3, str(d3.get("reason")))

    # Test4 Reorder
    lines = led.read_text(encoding="utf-8").splitlines()
    rl = fresh("ledger_reorder.jsonl"); rr = lines[:]; rr[3], rr[4] = rr[4], rr[3]
    rl.write_text("\n".join(rr) + "\n", encoding="utf-8")
    ok4, d4 = L.verify_ledger(rl)
    check("T4 reorder detected", not ok4, str(d4.get("reason")))

    # Test6 Empty ledger
    el = fresh("ledger_empty.jsonl"); el.write_text("", encoding="utf-8")
    ok6, d6 = L.verify_ledger(el)
    s6 = R.replay(el)
    check("T6 empty ledger legal initial state", ok6 and s6["trade_count"] == 0 and s6["events_consumed"] == 0,
          str(d6))

    # Test9 Partial/Zero fill (schema + replay): zero-fill order must not create a trade
    zf = fresh("ledger_zerofill.jsonl")
    L.append_event(L.new_event("ACCOUNT_INIT", environment="PAPER", execution_mode="PAPER", account_balance=5000.0), zf)
    L.append_event(L.new_event("EXECUTION_REQUEST", environment="PAPER", execution_mode="PAPER", decision_id="DZ", side="BUY", volume=0.01), zf)
    L.append_event(L.new_event("EXECUTION_RESPONSE", environment="PAPER", execution_mode="PAPER", decision_id="DZ",
                               retcode=10009, fill_price=None, fill_volume=0.0, status="EXECUTED"), zf)
    sz = R.replay(zf)
    check("T9 zero-fill no position/trade", sz["trade_count"] == 0 and len(sz["open_positions"]) == 0, f"trades={sz['trade_count']}")

    # Environment separation: PAPER vs BROKER_DEMO
    mixed = fresh("ledger_mixed.jsonl")
    build(mixed, init=10000.0)
    M.migrate(phase_dir=ROOT / "state" / "demo_calibration" / "phase2", out_path=mixed)
    sp = R.replay(mixed, execution_mode="PAPER")
    sb = R.replay(mixed, execution_mode="BROKER_DEMO")
    check("Env separation PAPER/BROKER_DEMO", sp["trade_count"] == 1 and sb["trade_count"] == 1
          and sp["account"]["initial_balance"] == 10000.0 and sb["account"]["initial_balance"] is None,
          f"paper_trades={sp['trade_count']} demo_trades={sb['trade_count']}")

    # Migration compatibility (original files unchanged + source_record_hash present)
    before = {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in (ROOT / "state" / "demo_calibration" / "phase2").glob("*.json")}
    mig = M.migrate(phase_dir=ROOT / "state" / "demo_calibration" / "phase2", out_path=fresh("ledger_mig.jsonl"))
    after = {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in (ROOT / "state" / "demo_calibration" / "phase2").glob("*.json")}
    has_src = all(e.get("source_record_hash") for e in mig)
    check("MIG compat + originals immutable", len(mig) >= 8 and has_src and before == after,
          f"events={len(mig)} src_hash_all={has_src} originals_unchanged={before == after}")

    log(f"=== RESULT: {sum(_res)}/{len(_res)} PASS ===")
    return 0 if all(_res) else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
