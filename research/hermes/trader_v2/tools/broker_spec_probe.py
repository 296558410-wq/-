# -*- coding: utf-8 -*-
"""V2 Broker 规格实测（P1-C，只读；不发任何订单）。使用 V2 独立实例 fxtm_demo_01。

用法: python tools/broker_spec_probe.py   → 写 research/V2_BROKER_SPEC_YYYYMMDD.md
BROKER_ORDER_SENT 恒为 FALSE（本脚本无下单调用）。
"""
from __future__ import annotations
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "execution"))
import fxtm_demo_adapter as FA  # noqa: E402

OUT = ROOT / "research" / f"V2_BROKER_SPEC_{datetime.now(timezone.utc).strftime('%Y%m%d')}.md"
FIELDS = ("digits", "point", "tick_size", "tick_value", "contract_size", "volume_min",
          "volume_step", "volume_max", "stops_level", "freeze_level", "filling_mode", "execution_mode")


def main():
    cfg = FA._load_cfg()
    assumed = cfg.get("execution", {}).get("contract", {})
    actual, verified, note = None, False, ""
    a = FA.FXTMDemoAdapter()
    try:
        a.connect()
        spec = a.symbol_spec("XAUUSD")
        actual = spec
        verified = bool(spec.get("ok"))
        if not spec.get("ok"):
            note = "symbol_info None"
    except Exception as e:  # noqa: BLE001
        note = f"{type(e).__name__}:{e}"
    finally:
        try:
            a.disconnect()
        except Exception:  # noqa: BLE001
            pass
    lines = [f"# V2 BROKER SPEC — {datetime.now(timezone.utc).strftime('%Y%m%d')} (P1-C)", "",
             f"- generated: {datetime.now(timezone.utc).isoformat()}",
             f"- instance: fxtm_demo_01 / symbol XAUUSD (V2 independent)",
             f"- **verified = {verified}**   note: {note}", "",
             "## 实测 (MT5 symbol_info, live)", "",
             "| field | value | source | retrieval_ts | verified |", "|---|---|---|---|---|"]
    src = (actual or {}).get("retrieval_ts")
    for f in FIELDS:
        lines.append(f"| {f} | {(actual or {}).get(f, 'UNVERIFIED')} | MT5 symbol_info | {src} | {verified} |")
    lines += ["", "## config 假设 (供对照, 非实测)", "",
              "| field | config value |", "|---|---|"]
    for k, v in assumed.items():
        lines.append(f"| {k} | {v} |")
    lines += ["", "## 说明",
              "- 实测优先；config 仅对照。未取得字段标 UNVERIFIED（不假设）。",
              "- 本脚本不发单（BROKER_ORDER_SENT=FALSE）。"]
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"verified": verified, "note": note, "actual": actual, "path": str(OUT)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
