# -*- coding: utf-8 -*-
"""V2 回归 — P1-F Failure Injection（真实注入，断言 fail-closed）。

覆盖: 数据缺失/降级、健康、freshness、price_space、broker 预校验、PIT cache、replay snapshot、ledger、forward gate。
要求: 每种情况 NO FALSE FRESH / NO FALSE NEUTRAL / NO TRADE（fail-closed）。
日志: logs/test_failure_injection.log
"""
from __future__ import annotations
import copy
import importlib
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
for sub in ("hermes", "execution", "data_sources", "agents/technical", "agents/macro_global", "runtime", "ledger"):
    sys.path.insert(0, str(ROOT / sub))
import agent2 as A2  # noqa: E402
import hermes as H  # noqa: E402
import price_space as PS  # noqa: E402
import broker_validate as BV  # noqa: E402
import pit_cache as PC  # noqa: E402
import replay_inputs as RI  # noqa: E402
import ledger as L  # noqa: E402

LOGS = ROOT / "logs"; LOGS.mkdir(exist_ok=True)
LOG = LOGS / "test_failure_injection.log"
_RES = []


def log(s):
    line = f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] {s}"
    print(line)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def check(n, c, d=""):
    _RES.append(bool(c))
    log(f"{'PASS' if c else 'FAIL'} | {n} {d}")


def main():
    ctx_ok = {"agent1": {"freshness": "fresh"}, "agent2": {"freshness": "fresh"}, "health": {"overall_status": "PASS"}}

    # 1 DXY/UST10Y/VIX 缺失 -> DEGRADED (not NEUTRAL)
    check("DATA: core macro missing -> DEGRADED", A2.macro_state(True, 0.0, [])[1] == "DEGRADED")
    # 2 health FAIL -> REJECT
    check("HEALTH: FAIL -> REJECT", H.gate(None, {**ctx_ok, "health": {"overall_status": "FAIL"}}, {})[0] == "REJECT")
    # 3 health DEGRADED -> WAIT
    check("HEALTH: DEGRADED -> WAIT", H.gate(None, {**ctx_ok, "health": {"overall_status": "DEGRADED"}}, {})[0] == "WAIT")
    # 4 macro_status DEGRADED -> WAIT
    check("MACRO: DEGRADED -> WAIT", H.gate(None, ctx_ok, {"macro_status": "DEGRADED"})[0] == "WAIT")
    # 5 freshness unknown -> WAIT
    check("FRESH: unknown -> WAIT", H.gate(None, {"agent1": {"freshness": "unknown"}, "agent2": {"freshness": "fresh"}}, {})[0] == "WAIT")

    # 6 price_space missing basis -> fail-closed
    r = PS.prepare({"direction": "SHORT", "entry": 4300.0, "stop_loss": 4317.0, "take_profit": 4273.0},
                   gc_price=4300.0, gc_ts=None, spot_price=None, spot_ts=None, now_ts=None, cfg={**PS.DEFAULT_CFG, "enabled": True})
    check("PRICE_SPACE: missing basis -> reject", (not r["valid"]) and r["reject_code"] == "BASIS_UNAVAILABLE", r["reject_code"])
    # 7 price_space stale -> reject
    old = (datetime.now(timezone.utc).timestamp() - 100000)
    r = PS.prepare({"direction": "SHORT", "entry": 4300.0, "stop_loss": 4317.0, "take_profit": 4273.0},
                   gc_price=4300.0, gc_ts=old, spot_price=4290.0, spot_ts=old,
                   now_ts=datetime.now(timezone.utc).timestamp(), cfg={**PS.DEFAULT_CFG, "enabled": True})
    check("PRICE_SPACE: stale -> reject", (not r["valid"]) and r["reject_code"] == "BASIS_STALE", r["reject_code"])

    # 8 broker precheck invalid stops -> reject
    check("BROKER: invalid stops -> precheck reject",
          BV.precheck_order("SHORT", 4300.0, 4283.0, 4327.0, market_bid=4299.8, market_ask=4300.0)[0] is False)

    # 9 pit_cache future excluded
    tmp = Path(tempfile.mkdtemp()) / "p.jsonl"
    PC.put_record("f", "XAUUSD", 1.0, data_ts=9000, received_ts=9001, path=tmp)
    check("PIT: future not visible", PC.get_asof("f", 5000, "XAUUSD", path=tmp) is None)

    # 10 replay snapshot missing -> fail-closed
    try:
        RI.offline_replay(None); check("REPLAY: missing -> fail-closed", False)
    except RI.ReplayError as e:
        check("REPLAY: missing -> fail-closed", e.code == "SNAPSHOT_MISSING", e.code)

    # 11 ledger truncated -> LedgerMalformed (fail-closed, not silent)
    led = Path(tempfile.mkdtemp()) / "l.jsonl"
    led.write_text('{"event_type":"DECISION","seq":1,"previous_event_hash":"GENESIS"}\n{"event_type":"DEC', encoding="utf-8")
    try:
        L.load_events(led); check("LEDGER: truncated -> fail-closed", False)
    except L.LedgerMalformed:
        check("LEDGER: truncated -> fail-closed", True)

    # 12 forward gate locked -> refuse
    import shadow_run as SR
    prev = os.environ.pop("V2_FORWARD_VALIDATION_ALLOWED", None)
    try:
        ok = False
        try:
            SR.start_run(1)
        except RuntimeError:
            ok = True
        check("GATE: locked -> refuse start_run", ok and SR.forward_allowed() is False)
    finally:
        if prev is not None:
            os.environ["V2_FORWARD_VALIDATION_ALLOWED"] = prev

    # 13 router disabled via env -> router_enabled False
    import data_sources as DS
    p2 = os.environ.get("V2_DATA_ROUTER_ENABLED")
    try:
        os.environ["V2_DATA_ROUTER_ENABLED"] = "false"
        check("ROUTER: explicit disable honored", DS.router_enabled() is False)
    finally:
        if p2 is None:
            os.environ.pop("V2_DATA_ROUTER_ENABLED", None)
        else:
            os.environ["V2_DATA_ROUTER_ENABLED"] = p2

    log(f"=== RESULT: {sum(_RES)}/{len(_RES)} PASS ===")
    return 0 if all(_RES) else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
