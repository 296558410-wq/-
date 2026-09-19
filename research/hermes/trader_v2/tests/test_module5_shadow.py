# -*- coding: utf-8 -*-
"""Module 5 测试 —— 实时 Paper Shadow Run 基础设施 (T1–T14, fixture 注入, 不依赖网络)。

日志: logs/test_module5_shadow.log
"""
import os, sys, json, shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
for sub in ("runtime", "execution", "ledger"):
    sys.path.insert(0, str(ROOT / sub))
import shadow_run as SR  # noqa: E402
# P1-G: 未认证禁止开新正式 run；本测试在隔离 TMP 沙盒内显式授权（非生产）。
os.environ["V2_FORWARD_VALIDATION_ALLOWED"] = "true"
import hermes_paper_adapter as ADP  # noqa: E402
import ledger as L  # noqa: E402
import replay as R  # noqa: E402

TMP = HERE / "_tmp" / "m5"; LOGS = ROOT / "logs"; LOGS.mkdir(exist_ok=True)
LOG = LOGS / "test_module5_shadow.log"
_res = []

# 固定 PAPER 配置（测试与仓库实时 config 解耦；Module 6 后仓库 config 可为 BROKER_DEMO）
PAPER_CFG = {"symbol": "XAUUSD",
             "execution": {"execution_mode": "PAPER", "live_trading": False, "broker_demo_enabled": False,
                           "cost_model": {"spread_bps_typical": 0.35, "slippage_bps": 0.30, "latency_ms": 250, "commission_per_lot_usd": 0.0},
                           "contract": {"min_lot": 0.01, "max_lot": 0.05, "contract_size_oz": 100, "price_dp": 2, "lot_dp": 2, "leverage": 500},
                           "risk": {"per_trade_pct": 1.0, "single_position": True, "max_notional_usd": 25000}},
             "broker": {"enabled": False}, "account": {"initial_balance": 10000.0}}


def log(s):
    print(s if s.startswith(("[", "=")) else "  " + s)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(s + "\n")


def check(n, c, d=""):
    _res.append(bool(c)); log(f"{'PASS' if c else 'FAIL'} | {n} {d}")


def setup():
    if TMP.exists():
        shutil.rmtree(TMP, ignore_errors=True)
    TMP.mkdir(parents=True)
    SR.RUNS = TMP / "runs"; SR.ACTIVE = TMP / "ACTIVE.json"
    ADP.load_config = lambda: PAPER_CFG   # 固定 PAPER 路径（与实时 config 解耦）


def ctx(cid="ctx-t", ch="ch-t", px=4350.0):
    return {"context_id": cid, "context_hash": ch, "market": {"primary_last": px, "retrieval_ts": "2026-09-11T00:00:00Z"}}


def dec(kind, entry=4350.0, sl=4310.0, tp=4400.0, qty=0.02, cid="ctx-t", ch="ch-t"):
    plan = ({"direction": "LONG", "entry": entry, "stop_loss": sl, "take_profit": tp, "qty_lots": qty,
             "confidence": 0.55} if kind == "TRADE" else None)
    return {"decision": kind, "reason": f"fixture-{kind}", "no_trade_reason": f"fixture-{kind}", "plan": plan,
            "context_id": cid, "context_hash": ch, "ts": "2026-09-11T00:00:00Z"}


def patch(d, c=None, px=4350.0):
    SR.A1.build = lambda cycle=None: ({"generated_utc": "2026-09-11T00:00:00Z",
                                       "quotes": {"gold_spot": {"data_ts": "00:00:00", "retrieval_ts": "t"}},
                                       "market_regime": {"regime": "trend"}}, TMP / "a1.json")
    SR.A2.build = lambda cycle=None: ({"snapshot_ts": "2026-09-11T00:00:00Z", "data_gaps": []}, TMP / "a2.json")
    SR.HERMES.run = lambda cycle=None: (d, c or ctx(), [], [])


def main():
    open(LOG, "a", encoding="utf-8").write("\n" + "=" * 60 + "\n")
    log(f"[{'-'*8}] === Module 5 shadow tests (T1–T14) ===")
    setup()

    # T1 run_id 唯一
    r1 = SR.start_run(minutes=60); r2 = SR.start_run(minutes=60)
    check("T1 run_id unique", r1 != r2 and r1.startswith("V2-PAPER-"), f"{r1} / {r2}")

    # T2 manifest 冻结字段
    man = json.loads((SR.run_dir(r1) / "run_manifest.json").read_text(encoding="utf-8"))
    req = ["run_id", "start_time_utc", "end_time_utc", "execution_mode", "strategy_version", "agent1_version",
           "agent2_version", "hermes_version", "paper_engine_version", "ledger_version", "config_hash",
           "code_commit", "market_data_source", "symbol", "timezone"]
    check("T2 run_manifest complete+frozen", all(k in man for k in req) and man["execution_mode"] == "PAPER" and man["frozen"])

    # T3 TRADE fixture 全链
    setup(); patch(dec("TRADE"), ctx("ctx-t3", "ch-t3")); rid = SR.start_run(60)
    out = SR.run_cycle(rid, window="2026-09-11T03:00Z")
    evs = L.load_events(SR.run_ledger(rid)); rst = R.replay(SR.run_ledger(rid), "PAPER")
    check("T3 TRADE→Paper→Ledger", out["execution_result"] == "EXECUTED" and out["paper_orders"] == 1
          and rst["trade_count"] == 0 and out["replay_match"] and L.verify_ledger(SR.run_ledger(rid))[0],
          f"exec={out['execution_result']} match={out['replay_match']}")

    # T4 WAIT: 无纸面订单
    setup(); patch(dec("WAIT"), ctx("ctx-t4", "ch-t4")); rid = SR.start_run(60)
    out = SR.run_cycle(rid, window="2026-09-11T03:15Z"); rst = R.replay(SR.run_ledger(rid), "PAPER")
    check("T4 WAIT no paper order", out["paper_orders"] == 0 and out["replay_match"]
          and rst["decisions"]["WAIT"] == 1 and rst["trade_count"] == 0)

    # T5 REJECT: 无纸面订单
    setup(); patch(dec("REJECT"), ctx("ctx-t5", "ch-t5")); rid = SR.start_run(60)
    out = SR.run_cycle(rid, window="2026-09-11T03:30Z"); rst = R.replay(SR.run_ledger(rid), "PAPER")
    check("T5 REJECT no paper order", out["paper_orders"] == 0 and rst["decisions"]["REJECT"] == 1)

    # T6 去重: 同 window 二次调用 → skip
    setup(); patch(dec("TRADE"), ctx("ctx-t6", "ch-t6")); rid = SR.start_run(60)
    o1 = SR.run_cycle(rid, window="2026-09-11T04:00Z")
    o2 = SR.run_cycle(rid, window="2026-09-11T04:00Z")
    evs = L.load_events(SR.run_ledger(rid))
    ndec = sum(1 for e in evs if e["event_type"] == "DECISION"); nf = sum(1 for e in evs if e["event_type"] == "FILL")
    check("T6 duplicate decision window skipped", o1.get("execution_result") == "EXECUTED" and o2.get("skipped_duplicate")
          and ndec == 1 and nf == 1, f"decisions={ndec} fills={nf}")

    # T7 Crash recovery (状态落盘=进程重启语义): 重入不再决策/执行
    st = SR.load_state(rid)
    o3 = SR.run_cycle(rid, window="2026-09-11T04:00Z")  # 模拟 restart 后重放同 window
    evs = L.load_events(SR.run_ledger(rid)); ok = L.verify_ledger(SR.run_ledger(rid))[0]
    rst = R.replay(SR.run_ledger(rid), "PAPER")
    acc = json.loads((SR.run_dir(rid) / "paper_account.json").read_text(encoding="utf-8"))
    check("T7 crash recovery: no dup, ledger ok, account recovered",
          o3.get("skipped_duplicate") and sum(1 for e in evs if e["event_type"] == "DECISION") == 1
          and ok and abs(rst["account"]["balance"] - acc["balance"]) < 1e-6)

    # T8a Ledger 不可用 → 不执行
    setup(); patch(dec("TRADE"), ctx("ctx-t8", "ch-t8")); rid = SR.start_run(60)
    orig_writable = SR._ledger_writable
    SR._ledger_writable = lambda p: False
    o = SR.run_cycle(rid, window="2026-09-11T05:00Z")
    led_exists = SR.run_ledger(rid).exists()
    ndec = sum(1 for e in L.load_events(SR.run_ledger(rid)) if e["event_type"] == "DECISION") if led_exists else 0
    check("T8a ledger unavailable → NO EXECUTION", o.get("blocked") == "LEDGER_UNAVAILABLE" and ndec == 0)
    SR._ledger_writable = orig_writable  # 恢复

    # T8b Ledger 被篡改 → 阻塞不执行
    setup(); patch(dec("TRADE"), ctx("ctx-t8b", "ch-t8b")); rid = SR.start_run(60)
    SR.run_cycle(rid, window="2026-09-11T05:15Z")
    led = SR.run_ledger(rid); lines = led.read_text(encoding="utf-8").splitlines()
    obj = json.loads(lines[0]); obj["account_balance"] = 1.0; lines[0] = json.dumps(obj)
    led.write_text("\n".join(lines) + "\n", encoding="utf-8")   # 篡改首条
    o = SR.run_cycle(rid, window="2026-09-11T05:30Z")
    check("T8b tampered ledger → blocked", str(o.get("blocked")).startswith("LEDGER_UNVERIFIABLE"), str(o.get("blocked"))[:60])

    # T9 确定性 replay
    led = SR.run_ledger(rid)
    check("T9 deterministic replay", R.replay(led, "PAPER")["state_hash"] == R.replay(led, "PAPER")["state_hash"])

    # T10 verify_ledger
    setup(); patch(dec("TRADE"), ctx("ctx-t10", "ch-t10")); rid = SR.start_run(60)
    SR.run_cycle(rid, window="2026-09-11T06:00Z")
    check("T10 verify_ledger PASS", L.verify_ledger(SR.run_ledger(rid))[0])

    # T11 环境隔离 PAPER only
    modes = {e.get("execution_mode") for e in L.load_events(SR.run_ledger(rid))}
    runs = {e.get("run_id") for e in L.load_events(SR.run_ledger(rid))}
    check("T11 env isolation + run_id stamped", modes == {"PAPER"} and runs == {rid}, f"modes={modes} runs={runs}")

    # T12 paper-only gate: 非 PAPER 拒绝
    bad = False
    try:
        ADP.assert_paper_only({"execution": {"execution_mode": "LIVE", "live_trading": True, "broker_demo_enabled": True},
                               "broker": {"enabled": True}})
    except ADP.RefuseToStart:
        bad = True
    check("T12 paper-only gate refuses non-paper", bad)

    # T13 RAW + FROZEN 均存在且 frozen 未改意图
    setup(); patch(dec("TRADE", entry=4350.0, sl=4310.0), ctx("ctx-t13", "ch-t13")); rid = SR.start_run(60)
    SR.run_cycle(rid, window="2026-09-11T07:00Z")
    decdir = SR.run_dir(rid) / "decisions"; raws = list(decdir.glob("*.raw.json")); fros = list(decdir.glob("*.frozen.json"))
    raw = json.loads(raws[0].read_text(encoding="utf-8"))
    fro = json.loads(fros[0].read_text(encoding="utf-8"))
    check("T13 RAW+FROZEN preserved, intent unchanged",
          len(raws) == 1 and len(fros) == 1 and raw["plan"]["entry"] == fro["entry_reference"]
          and raw["plan"]["direction"] == fro["side"], f"entry={fro['entry_reference']} side={fro['side']}")

    # T14 策略纪律: config_hash 不变 (无阈值/成本/风控改动)
    man = json.loads((SR.run_dir(rid) / "run_manifest.json").read_text(encoding="utf-8"))
    cur = SR.sha_file(ROOT / "config" / "v2_config.json")
    check("T14 config frozen (no strategy/cost/risk change)", man["config_hash"] == cur)

    log(f"[{'='*8}] RESULT: {sum(_res)}/{len(_res)} PASS")
    return 0 if all(_res) else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
