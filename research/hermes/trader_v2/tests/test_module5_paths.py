# -*- coding: utf-8 -*-
"""Module 5 路径专项测试 —— PATH-01..PATH-10（路径/透传/隔离；不依赖网络）。"""
import sys, json, hashlib
from datetime import datetime, timezone, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
for sub in ("hermes", "execution", "runtime", "agents/technical", "agents/macro_global"):
    sys.path.insert(0, str(ROOT / sub))
import context as CTX  # noqa: E402
import hermes as HERMES  # noqa: E402
import hermes_paper_adapter as ADP  # noqa: E402

TMP = HERE / "_tmp" / "m5paths"; TMP.mkdir(parents=True, exist_ok=True)
LOGS = ROOT / "logs"; LOGS.mkdir(exist_ok=True)
LOG = LOGS / "test_module5_paths.log"
_res = []


def log(s):
    print(s)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(s + "\n")


def check(n, c, d=""):
    _res.append(bool(c)); log(f"{'PASS' if c else 'FAIL'} | {n} {d}")


def main():
    open(LOG, "a", encoding="utf-8").write("\n" + "=" * 60 + "\n")
    tv2 = str(ROOT).lower()
    now = datetime.now(timezone.utc).isoformat()

    # PATH-01 Agent1 path resolution
    a1p = CTX.STATE / "agent1_latest.json"
    check("PATH-01 Agent1 path resolution", tv2 in str(CTX.STATE).lower() and a1p == ROOT / "state" / "agent1_latest.json"
          and a1p.exists(), str(a1p))

    # PATH-02 Agent2 path resolution
    a2p = CTX.STATE / "agent2_latest.json"
    check("PATH-02 Agent2 path resolution", a2p == ROOT / "state" / "agent2_latest.json" and a2p.exists(), str(a2p))

    # PATH-03 freshness propagation (fixture fresh ts → not unknown)
    fa1 = TMP / "a1.json"; fa2 = TMP / "a2.json"
    _now_ep = int(datetime.now(timezone.utc).timestamp())
    fa1.write_text(json.dumps({"generated_utc": now, "cycle": "cf", "agent_version": "agent1/x",
                               "price_basis": {"primary_last": 4350.0}, "quotes": {"gold_spot": {"spread": 0.3}},
                               "data_quality": {"gaps": [], "by_tf": {"15m": {"last_bar_ts": _now_ep}}}}), encoding="utf-8")
    fa2.write_text(json.dumps({"snapshot_ts": now, "cycle": "cf", "agent_version": "agent2/x",
                               "macro": {"usd": {"data_ts": _now_ep}}}), encoding="utf-8")
    ctx, _ = CTX.build_context(agent1_path=fa1, agent2_path=fa2)
    check("PATH-03 freshness propagation (not unknown)",
          ctx["agent1"]["freshness"] == "fresh" and ctx["agent2"]["freshness"] == "fresh",
          f"a1={ctx['agent1']['freshness']} a2={ctx['agent2']['freshness']}")
    # 反向证明: 缺 ts → unknown
    (TMP / "a1_empty.json").write_text(json.dumps({"cycle": "x"}), encoding="utf-8")
    c2, _ = CTX.build_context(agent1_path=TMP / "a1_empty.json", agent2_path=fa2)
    check("PATH-03b missing ts → unknown (honest)", c2["agent1"]["freshness"] == "unknown")

    # PATH-04 config path
    check("PATH-04 config path", CTX.CONFIG == ROOT / "config" / "v2_config.json" and CTX.CONFIG.exists(), str(CTX.CONFIG))

    # PATH-05 config hash consistency
    want = hashlib.sha256((ROOT / "config" / "v2_config.json").read_bytes()).hexdigest()
    ch = CTX.build_context(agent1_path=fa1, agent2_path=fa2)[0]["config_hash"]
    check("PATH-05 config hash consistency", ch == want and ch != hashlib.sha256(b"").hexdigest(), ch[:16])

    # PATH-06 decision context path
    c3, p3 = CTX.build_context(agent1_path=fa1, agent2_path=fa2)
    check("PATH-06 decision context path", str(p3).lower().startswith(tv2) and "state" in str(p3).lower()
          and "decision_contexts" in str(p3), str(p3))

    # PATH-07 Hermes gate receives real freshness (not WAIT-due-to-freshness)
    g2 = {"gold_macro_state": "UNCERTAIN"}
    verdict, reason = HERMES.gate(None, c3, g2, {})
    check("PATH-07 gate receives real freshness", "数据不新鲜" not in reason and verdict == "WAIT", f"{verdict}:{reason}")
    # 反向: unknown 时 gate 必须 WAIT(数据不新鲜)
    verdict2, reason2 = HERMES.gate(None, c2, g2, {})
    check("PATH-07b gate WAIT on unknown (safety intact)", "数据不新鲜" in reason2, reason2)

    # PATH-08 old wrong-root dir cannot be active input
    bad_root = Path("C:/AIQuant/research/hermes/state").resolve()
    check("PATH-08 wrong-root not active", CTX.STATE.resolve() != bad_root and tv2 in str(CTX.STATE).lower(),
          f"STATE={CTX.STATE}")
    # hermes.py 自身 state 也应在 trader_v2
    check("PATH-08b hermes.py ROOT fixed", str(HERMES.STATE).lower().startswith(tv2), str(HERMES.STATE))

    # PATH-09 V1 isolation
    refs = []
    for p in list((ROOT / "hermes").glob("*.py")) + list((ROOT / "execution").glob("*.py")) + list((ROOT / "runtime").glob("*.py")):
        t = p.read_text(encoding="utf-8")
        if any(k in t for k in ("trader_v1", "live_fxtm", "hermes-trader")):
            refs.append(p.name)
    check("PATH-09 V1 isolation", not refs, str(refs))

    # PATH-10 PAPER-only（显式 PAPER 配置，避免依赖实时 config）
    ok = False
    try:
        ADP.assert_paper_only({"execution": {"execution_mode": "PAPER", "live_trading": False, "broker_demo_enabled": False},
                               "broker": {"enabled": False}}); ok = True
    except Exception:  # noqa: BLE001
        ok = False
    bad = False
    try:
        ADP.assert_paper_only({"execution": {"execution_mode": "BROKER_DEMO", "live_trading": False, "broker_demo_enabled": True},
                               "broker": {"enabled": True}})
    except ADP.RefuseToStart:
        bad = True
    check("PATH-10 PAPER-only execution", ok and bad)

    log(f"=== RESULT: {sum(_res)}/{len(_res)} PASS ===")
    return 0 if all(_res) else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
