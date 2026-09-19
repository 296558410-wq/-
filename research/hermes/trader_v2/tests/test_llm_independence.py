# -*- coding: utf-8 -*-
"""V2 回归 — P1-E LLM/Token 依赖审计（static + import-graph + runtime-path）。

断言:
- 运行时决策路径 (agent1/agent2/hermes/hermes_paper_adapter/shadow_run/v2_scheduled_cycle/router) 无 LLM 调用
- 运行时不导入任何 LLM SDK
- live 决策源 = reference_rules（确定性），llm 路径仅显式传入才可达
- 失败路径无 "fallback -> LLM"
日志: logs/test_llm_independence.log
"""
from __future__ import annotations
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
for sub in ("hermes", "execution", "data_sources", "agents/technical", "agents/macro_global", "runtime", "ledger"):
    sys.path.insert(0, str(ROOT / sub))

LOGS = ROOT / "logs"; LOGS.mkdir(exist_ok=True)
LOG = LOGS / "test_llm_independence.log"
_RES = []
RUNTIME_FILES = ["agents/technical/agent1.py", "agents/technical/market_data.py", "agents/technical/features.py",
                 "agents/macro_global/agent2.py", "agents/macro_global/sources.py", "hermes/hermes.py",
                 "hermes/context.py", "hermes/discovery.py", "execution/hermes_paper_adapter.py",
                 "execution/broker_demo_executor.py", "execution/fxtm_demo_adapter.py", "runtime/shadow_run.py",
                 "runtime/v2_scheduled_cycle.py", "data_sources/router.py"]
LLM_TOKENS = ("openai", "anthropic", "google.generativeai", "gemini", "ollama", "litellm",
              "chat.completions", "ChatCompletion", "api_key", "API_KEY", "OPENAI_API_KEY", "DEEPSEEK_API_KEY")


def log(s):
    line = f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] {s}"
    print(line)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def check(n, c, d=""):
    _RES.append(bool(c))
    log(f"{'PASS' if c else 'FAIL'} | {n} {d}")


def main():
    # STATIC
    hits = []
    for f in RUNTIME_FILES:
        t = (ROOT / f).read_text(encoding="utf-8")
        for tok in LLM_TOKENS:
            if tok in t:
                hits.append(f"{f}:{tok}")
    check("STATIC: runtime path has no LLM tokens", not hits, ",".join(hits[:5]))

    # runtime imports
    import agent1, agent2, hermes as H, shadow_run as SR  # noqa: F401
    bad_mods = [m for m in ("openai", "anthropic", "google.generativeai", "ollama", "litellm") if m in sys.modules]
    check("IMPORT: no LLM SDK loaded", not bad_mods, ",".join(bad_mods))

    # live decision source is deterministic (reference_rules)
    src = (ROOT / "runtime" / "shadow_run.py").read_text(encoding="utf-8")
    check("RUNTIME: shadow_run uses HERMES.run (default reference_rules)", "HERMES.run(cycle)" in src)
    hsrc = (ROOT / "hermes" / "hermes.py").read_text(encoding="utf-8")
    check("hermes default source=reference_rules", 'def run(cycle=None, source="reference_rules"' in hsrc)
    check("llm only via explicit llm_decision", "llm_decision is not None" in hsrc or "llm_decision=None" in hsrc)

    # FALLBACK: no "-> LLM" in failure paths
    fb = []
    for f in ("runtime/shadow_run.py", "hermes/hermes.py", "execution/hermes_paper_adapter.py", "agents/macro_global/agent2.py"):
        t = (ROOT / f).read_text(encoding="utf-8").lower()
        if "fallback" in t and "llm" in t and "llm_decision" not in t:
            fb.append(f)
    check("FALLBACK: no failure->LLM fallback", not fb, ",".join(fb))

    # deterministic decision runnable offline (no LLM)
    ctx = {"context_id": "x", "context_hash": "h", "agent1": {"freshness": "fresh"}, "agent2": {"freshness": "fresh"},
           "market": {"instrument": "XAUUSD", "primary_last": 4350.0}, "health": {"overall_status": "PASS"}}
    a1 = {"market_regime": {"regime": "mixed"}, "timeframes": {}, "data_quality": {"gaps": []}}
    d, _, _ = H.decide_pure(ctx, a1, {}, )
    check("deterministic decide_pure runs (no LLM)", d.get("instrument") == "XAUUSD")

    log(f"=== RESULT: {sum(_RES)}/{len(_RES)} PASS ===")
    return 0 if all(_RES) else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
