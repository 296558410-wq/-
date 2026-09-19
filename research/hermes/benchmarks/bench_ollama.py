#!/usr/bin/env python3
"""HERMES-02 local model benchmark harness — hits Ollama /api/generate.
Usage: python bench_ollama.py <model> [--tasks all|speed|core]
Reads frozen task prompts from JSON; measures tok/s; writes results to stdout + JSON.
No dependencies beyond stdlib (urllib)."""
import json, sys, time, urllib.request

OLLAMA = "http://localhost:11434"
CORE_TASKS = ["task1_lookahead", "task2_overlap", "task4_cost", "task9_adversarial"]
ALL_TASKS = [f"task{i}" for i in range(1, 11)]

TASKS = {
  "task1_lookahead": "你是一名量化研究审计员。有人声称『跨周期特征 H10 预测 60 分钟收益 IC=0.24，统计显著』。请指出这个结果最可能的陷阱是什么，以及为什么常见的截断重算测试可能抓不到它。",
  "task2_overlap": "某时序研究：n≈9000 重叠样本时 p=0.0000，改用 n≈140-690 非重叠样本后 p=0.10-0.80。请解释这里发生了什么，以及根本问题是什么。",
  "task3_winrate": "某交易策略胜率 95%，是否值得上线？请说明判断依据。",
  "task4_cost": "某高频策略用中间价(mid price)回测年化 40%。这个结果可信吗？为什么？",
  "task5_redundancy": "某提案：在固定波动率目标(fixed vol-target)之上做自适应缩放。这算新研究吗？在什么条件下它应被判为 REDUNDANT？",
  "task6_causality": "观察到『活动度先上升，点差随后放宽』。能否据此说『点差/流动性领先波动』？为什么？",
  "task7_preregister": "给定假设『宏观日程窗改变市场参与者构成，从而影响价格方向』，请给出正确的研究设计流程（如何避免事后编理论）。",
  "task8_design": "某研究把 hod_sin/cos 这类时间编码特征放进市场状态聚类。这个设计有什么问题？",
  "task9_adversarial": "有人得出结论『黄金对美元(XAUUSD)没有方向性 gross edge』。这句话在什么条件下成立、在什么情况下是危险的过度泛化？请批判它。",
  "task10_unknown": "如果你是一个 XAUUSD 量化研究项目的独立研究员，当前最值得解决的未知或数据缺口可能是什么？请诚实说明你不确定的部分。",
}

def gen(model, prompt, stream=False):
    body = json.dumps({"model": model, "prompt": prompt, "stream": stream,
                       "options": {"num_predict": 400}})
    req = urllib.request.Request(OLLAMA + "/api/generate", data=body.encode(),
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=600) as r:
        out = json.loads(r.read().decode())
    dt = time.time() - t0
    tok = out.get("eval_count", 0)
    return out.get("response", ""), tok, dt

def main():
    model = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else "core"
    tasks = ALL_TASKS if mode == "all" else CORE_TASKS
    results = {}
    for t in tasks:
        prompt = TASKS[t]
        try:
            resp, tok, dt = gen(model, prompt)
            results[t] = {"tokens": tok, "seconds": round(dt, 1),
                          "tok_per_s": round(tok/dt, 2) if dt > 0 else None,
                          "response": resp}
            print(f"\n===== {t} | {tok} tok | {dt:.1f}s | {tok/dt:.2f} tok/s =====\n{resp[:800]}")
        except Exception as e:
            results[t] = {"error": str(e)}
            print(f"\n===== {t} | ERROR: {e} =====\n")
    with open(f"bench_{model.replace(':','_')}_{mode}.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nSaved results to bench_{model.replace(':','_')}_{mode}.json")

if __name__ == "__main__":
    main()
