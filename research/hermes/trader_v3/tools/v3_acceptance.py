# -*- coding: utf-8 -*-
"""V3-MT5-ENV-ACCEPTANCE — 汇总环境验收（只读；不连 V1/V2）。

产出 state/V3_MT5_ACCEPTANCE.json。
结论: PASS | DATA_GAP | FAIL
"""
from __future__ import annotations
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

V3 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(V3 / "mt5"))
import v3_adapter as A  # noqa: E402

OUT = V3 / "state" / "V3_MT5_ACCEPTANCE.json"
ENVJ = V3 / "state" / "V3_MT5_ENVIRONMENT.json"


def _procs():
    try:
        out = subprocess.run(["powershell", "-NoProfile", "-Command",
                              "Get-CimInstance Win32_Process -Filter \"name='terminal64.exe'\" | Select-Object -ExpandProperty CommandLine"],
                             capture_output=True, text=True, timeout=30).stdout
        return [x.strip() for x in out.splitlines() if x.strip()]
    except Exception:  # noqa: BLE001
        return []


def main():
    env = json.loads(ENVJ.read_text(encoding="utf-8"))
    checks = {}

    # 1) order_send 代码层硬拦截
    try:
        A.order_send(); checks["order_send_blocked"] = False
    except A.OrderSendBlocked:
        checks["order_send_blocked"] = True
    except Exception:
        checks["order_send_blocked"] = False
    # 2) 安全闸门全 NO
    checks["safety_all_no"] = all(str(v).upper() == "NO" for v in A.safety_flags().values())
    # 3) 隔离：只连 V3 实例
    checks["v3_only_exe"] = (A.EXE.endswith("fxtm_demo_v3\\terminal64.exe"))
    checks["data_path_is_v3"] = "fxtm_demo_v3" in (env.get("data_path") or "")
    # 4) 进程隔离证明
    procs = _procs()
    checks["v1_terminal_present"] = any("Program Files" in p and "ForexTime" in p for p in procs)
    checks["v3_terminal_present"] = any("fxtm_demo_v3" in p for p in procs)
    checks["v2_terminal_present"] = any("fxtm_demo_01" in p for p in procs)
    # 5) 核心数据能力
    caps = env.get("capabilities") or {}
    checks["core_data_ok"] = all(caps.get(k) for k in ("quote_bidask", "ticks_read", "bars_m1", "raw_tick_storage"))
    # 6) 真实下单
    checks["real_order_capability"] = "NO (为设计目的；代码层拦截 + 安全闸门 NO)"

    gaps = list(env.get("gaps") or [])
    gaps += ["independent_account=NO (§四 回退：只建实例/只读)",
             "DUKA tick 时间重叠=NONE (最新 2026-08-04) → TICK_OVERLAP=DATA_GAP",
             "M1 对照: 同日 MT5 vs DUKA 均价偏差大 → DATA_GAP",
             "aggressor_side / market_depth / queue_position = UNRESOLVABLE (MT5 零售数据无 order book)"]

    env_ok = (checks["order_send_blocked"] and checks["safety_all_no"] and checks["v3_only_exe"]
              and checks["data_path_is_v3"] and checks["v3_terminal_present"] and checks["core_data_ok"])
    if not env_ok:
        verdict = "FAIL"
    else:
        # 环境可用但存在研究粒度 DATA_GAP（独立账号 / DUKA 对照 / order book 维度）
        verdict = "DATA_GAP"
    out = {"schema": "v3_mt5_acceptance/1", "ts_utc": datetime.now(timezone.utc).isoformat(),
           "verdict": verdict, "env_core_status": ("PASS" if env_ok else "FAIL"),
           "checks": checks, "data_gaps": gaps,
           "hf_unresolvable": [k for k, v in (env.get("hf_limitations") or {}).items() if "UNRESOLVABLE" in str(v)],
           "env_json": str(ENVJ), "env_report": str(V3 / "research" / "V3_MT5_ENVIRONMENT.md")}
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"verdict": verdict, "env_core_status": out["env_core_status"], "checks": checks,
                      "data_gaps": len(gaps), "hf_unresolvable": out["hf_unresolvable"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
