# V2 LLM / TOKEN AUDIT — 20260917 (P1-E)

方法: 静态扫描 + import-graph + 离线运行锚定。
```
STATIC_RESULT    = PASS  运行时决策路径(agent1/agent2/hermes/hermes_paper_adapter/broker_demo/fxtm/shadow_run/v2_scheduled_cycle/router)
                          均无 LLM token（openai/anthropic/gemini/ollama/litellm/chat.completions/api_key...）。
PROCESS_RESULT   = PASS  scheduler → v2_scheduled_cycle → shadow_run.run_cycle → HERMES.run(cycle)
                          （默认 source="reference_rules"，确定性）；无 model 子进程/launcher。
NETWORK_RESULT   = PASS  运行时路径无 model endpoint 字符串；仅出现市场数据 endpoint(yahoo/sina/…)。
RUNTIME_RESULT   = PASS  agent1/agent2/hermes 均可离线运行；decide_pure 确定性；import 后 sys.modules 无 LLM SDK。
FALLBACK_RESULT  = PASS  失败路径无 "→ LLM" 兜底；llm 路径仅当显式传 llm_decision 才可达
                          （shadow_run 不传 → live 恒 reference_rules）。
LLM_TOKEN_DEPENDENCY = PASS
```
## 证据
- `tests/test_llm_independence.py` 7/7。
- config 中 `agents.llm=true` / `hermes.model=deepseek/...` 仅为元数据；**运行时不调用**（无 SDK、无 key、无 endpoint）。
- `hermes.decide_pure` 无副作用且不含 LLM；`hermes.decide(source="llm")` 需外部注入 llm_decision（调度器不注入）。

## 说明/局限
- PROCESS/NETWORK 为**静态 + import-graph + 离线运行**证据（未做 OS 级 process-tree/抓包；当前系统锁定未跑全周期）。
  建议在 Shadow 阶段以 OS 级抓包复核（列入 Shadow checklist）。
