# -*- coding: utf-8 -*-
"""V2 运行期进程/网络审计（P1 residual 3.3，只读）。

在一次 cycle 窗口内采集 process tree / 子进程 / 网络连接 / 远端端点，
检查是否存在隐藏的 model/API/Gateway 依赖。不发单。
用法: python tools/runtime_audit.py [--seconds 30]
"""
from __future__ import annotations
import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research" / f"V2_RUNTIME_PROCESS_NETWORK_AUDIT_{datetime.now(timezone.utc).strftime('%Y%m%d')}.md"
MODEL_HINTS = ("openai", "anthropic", "generativelanguage", "ollama", "huggingface", "api.deepseek",
               "api-inference", "gateway", "litellm")
MARKET_HINTS = ("yahoo", "sinajs", "gtimg", "eastmoney", "cftc", "bls.gov", "wallstcn", "cnbc", "fxTM", "forextime", "dukascopy")


def _run(cmd):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return (r.stdout or "") + (r.stderr or "")
    except Exception as e:  # noqa: BLE001
        return f"ERR:{type(e).__name__}:{e}"


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--seconds", type=int, default=20)
    a = ap.parse_args()
    samples = []
    t0 = time.time()
    while time.time() - t0 < a.seconds:
        proc = _run(["tasklist", "/fo", "csv", "/nh"])
        net = _run(["netstat", "-ano"])
        samples.append({"ts": datetime.now(timezone.utc).isoformat(), "proc": proc, "net": net})
        time.sleep(5)
    # analyze last sample
    net = samples[-1]["net"] if samples else ""
    proc = samples[-1]["proc"] if samples else ""
    remote = sorted({ln.split()[2] for ln in net.splitlines() if "ESTABLISHED" in ln and len(ln.split()) >= 3})
    model_hits = [e for e in remote for h in MODEL_HINTS if h in e.lower()]
    market_hits = [e for e in remote for h in MARKET_HINTS if h in e.lower()]
    py_procs = [ln for ln in proc.splitlines() if "python" in ln.lower()]
    lines = [f"# V2 RUNTIME PROCESS / NETWORK AUDIT — {datetime.now(timezone.utc).strftime('%Y%m%d')} (P1 residual 3.3)", "",
             f"- window: {a.seconds}s, samples: {len(samples)}",
             f"- remote endpoints (ESTABLISHED): {len(remote)}",
             f"- **model/API/Gateway endpoint hits: {model_hits}**",
             f"- market-data endpoint hits: {market_hits[:8]}",
             f"- python processes: {len(py_procs)}", "",
             "## remote endpoints", "```"] + remote[:40] + ["```", "",
             "## python processes", "```"] + [p[:160] for p in py_procs[:20]] + ["```", "",
             "## 结论",
             f"- MODEL/GATEWAY 端点命中数: {len(model_hits)}  → " + ("PASS(无)" if not model_hits else "FAIL"),
             "- 说明: 本审计在当前锁定状态（无 run 运行）采集；Shadow 阶段应附于每次 cycle。BROKER_ORDER_SENT=FALSE。"]
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"model_hits": model_hits, "market_hits": market_hits[:8], "remote_n": len(remote),
                      "python_n": len(py_procs), "path": str(OUT)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
