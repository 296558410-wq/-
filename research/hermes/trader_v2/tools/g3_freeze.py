# -*- coding: utf-8 -*-
"""V2 G3 Data-Layer Freeze — 记录冻结版本（Git / Router / 数据源 / schema / 策略/决策版本 / 后端版本）。

只读；不改任何东西。产出:
  research/V2_G3_DATA_FREEZE_YYYYMMDD.md
  state/V2_G3_FREEZE.json
用法: python tools/g3_freeze.py [--label <tag>]
"""
from __future__ import annotations
import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
RESEARCH = ROOT / "research"
STATE = ROOT / "state"
for p in ("runtime", "hermes", "execution", "ledger", "data_sources", "agents/macro_global", "agents/technical"):
    sys.path.insert(0, str(ROOT / p))


def sha(p):
    try:
        return hashlib.sha256(Path(p).read_bytes()).hexdigest()
    except Exception:  # noqa: BLE001
        return None


def git(*a):
    try:
        return subprocess.run(["git", *a], cwd=str(REPO), capture_output=True, text=True, timeout=20).stdout.strip()
    except Exception:  # noqa: BLE001
        return ""


def build(label=""):
    import registry as REG
    import pit_cache as PC
    import replay_inputs as RI
    import shadow_run as SR
    from data_sources import cache as C

    src_cfg = {}
    for attr in ("HISTORY_SOURCES", "QUOTE_SOURCES", "SOURCE_META", "MACRO_SOURCES"):
        v = getattr(REG, attr, None)
        if v is not None:
            src_cfg[attr] = v
    hist = {}
    for tf in ("5m", "15m", "60m", "4h", "1d"):
        try:
            hist[tf] = REG.history_sources(tf)
        except Exception:  # noqa: BLE001
            pass

    files = {str(x.relative_to(ROOT)): sha(x) for x in [
        ROOT / "config" / "v2_config.json", ROOT / "config" / "price_space.json",
        ROOT / "data_sources" / "registry.py", ROOT / "data_sources" / "router.py",
        ROOT / "data_sources" / "mt5_market.py", ROOT / "data_sources" / "adapters_market.py",
        ROOT / "agents" / "macro_global" / "sources.py", ROOT / "agents" / "macro_global" / "agent2.py",
        ROOT / "agents" / "technical" / "agent1.py", ROOT / "hermes" / "hermes.py",
        ROOT / "runtime" / "shadow_run.py", ROOT / "runtime" / "explain.py",
        ROOT / "dashboard" / "server.py", ROOT / "dashboard" / "datasource.py",
    ]}

    def _flag(name):
        for base in (STATE, ROOT / "config"):
            p = base / name
            if p.exists():
                try:
                    return {"exists": True, "path": str(p.relative_to(ROOT)), "value": p.read_text(encoding="utf-8").strip()}
                except Exception:  # noqa: BLE001
                    pass
        return {"exists": False, "value": None}

    freeze = {
        "schema": "v2_g3_freeze/1",
        "label": label,
        "ts_utc": datetime.now(timezone.utc).isoformat(),
        "git": {"commit": git("rev-parse", "HEAD"), "branch": git("rev-parse", "--abbrev-ref", "HEAD"),
                "short": git("rev-parse", "--short", "HEAD")},
        "versions": SR.versions(),
        "schema_versions": {"pit_cache": PC.SCHEMA_VERSION, "input_snapshot": RI.SCHEMA},
        "flags": {n: _flag(n) for n in ("FORWARD_VALIDATION_ALLOWED", "SHADOW_ALLOWED",
                                        "data_router.enabled")},
        "invariants": {"BROKER_ORDER_SENT": False, "FORWARD_STARTED": False,
                       "LIVE_TRADING": False, "V1_UNTOUCHED": True},
        "router": {"history": hist, "sources": src_cfg},
        "file_sha256": files,
        "cache_schema": getattr(C, "SCHEMA", None) or "n/a",
        "notes": [
            "技术主行情: mt5 → local_fxtm → yahoo(降级)；现价/宏观: sina/tencent(国内)",
            "COT/BLS/东财资金流/WGC/央行购金/政策利率 = 显式 GAP（无国内源）",
            "UST10Y = tencent usUST(7-10Y ETF) 收益率代理(取反)，非 ^TNX 实时收益率",
        ],
    }
    (STATE / "V2_G3_FREEZE.json").write_text(json.dumps(freeze, ensure_ascii=False, indent=1), encoding="utf-8")
    day = datetime.now(timezone.utc).strftime("%Y%m%d")
    md = [f"# V2 G3 数据层冻结清单 — {day}", "", f"- label: `{label}`", f"- ts_utc: {freeze['ts_utc']}",
          f"- git: `{freeze['git']['short']}` (branch {freeze['git']['branch']})",
          f"- versions: `{json.dumps(freeze['versions'], ensure_ascii=False)}`",
          f"- schema: pit=`{freeze['schema_versions']['pit_cache']}` input_snapshot=`{freeze['schema_versions']['input_snapshot']}`",
          f"- flags: `{json.dumps(freeze['flags'], ensure_ascii=False)}`", "",
          "## Router 历史源", "```", json.dumps(hist, ensure_ascii=False, indent=1), "```",
          "## 数据源注册", "```", json.dumps(src_cfg, ensure_ascii=False, indent=1), "```",
          "## 关键文件 sha256", "```json", json.dumps(files, ensure_ascii=False, indent=1), "```",
          "## 冻结说明", *[f"- {n}" for n in freeze["notes"]], "",
          "> 冻结后：禁止改策略/阈值/候选/风险参数。发现数据安全 bug → 单独提交 + 重新冻结 + 重启 G3 计时。"]
    p = RESEARCH / f"V2_G3_DATA_FREEZE_{day}.md"
    p.write_text("\n".join(md) + "\n", encoding="utf-8")
    return p, freeze


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--label", default="post-domestic-rewire")
    a = ap.parse_args()
    p, fz = build(a.label)
    print(json.dumps({"path": str(p), "git": fz["git"]["short"], "versions": fz["versions"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
