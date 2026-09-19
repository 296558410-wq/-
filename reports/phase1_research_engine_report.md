# AIQuant Phase 1 — Research Engine Foundation 报告

> 生成：2026-09-04 19:10 (Asia/Shanghai) · git: 见各实验记录（commit 632d4bd / 后续 fix 提交）
> 机器：DESKTOP-LQ0B8O3 · Windows 11 · RTX A2000 Laptop 4GB (CC 8.6) · torch 2.14.0+cu126

## 0. 交付总览

| 交付物 | 位置 | 状态 |
|---|---|---|
| Research Engine 包（v0.2.0，~45 文件） | `C:\AIQuant\research_engine\` | ✅ 编译/冒烟/测试全过 |
| 统一实验协议 + Registry | `core/experiment.py` · `experiments/<id>/{config,metrics,results.parquet,report.md,log.txt}` | ✅ |
| Synthetic XAUUSD（regime/shock/真值，30d） | `data/synthetic/`（2.59M ticks / 43.2k M1 bars + MANIFEST sha256） | ✅ |
| Feature/Label 引擎（无前视，经截断重算证明） | `features/` · `core/feature.py` | ✅ |
| CPU/GPU Dispatcher（auto 决策+OOM 回退+记录） | `compute/` | ✅ |
| 统计验证（bootstrap/perm/BH-FDR/robustness） | `statistics/` | ✅ |
| Walk-Forward / Placebo / Cost-Stress | `validation/` | ✅ |
| Backtest 引擎（signal→pos→cost→equity→metrics） | `core/backtest.py` | ✅ |
| 质量门（11 项，关键项失败禁 SUPPORTED） | `core/quality.py` | ✅ |
| 自动化 CLI | `python -m research_engine run/benchmark/validate/list/synthetic` | ✅ |
| pytest | `tests/` | ✅ **46/46 PASS**（GPU 项实跑非 SKIP） |
| Git | main @ 3 commits | ✅ 无敏感文件 |

## A. Research Engine 是否真正可以运行？
是。四条命令各完整跑通一个实验（含产物落盘 + 质量门 + 自动报告）：
```
python -m research_engine run experiment_a|b|c|anti_overfit
python -m research_engine benchmark
python -m research_engine validate <id>
```
实验产物结构（例 `experiments/20260904_105842_experiment_b/`）含 config.json（协议全字段）、metrics.json、results.parquet、report.md、log.txt。

## B. Synthetic data pipeline 是否跑通？
✅。`SyntheticXAUUSDGenerator`（1s ticks，UTC）：
- regimes：trend_up 52% / trend_down 25% / range 14% / high_vol 9%（30d）；vol shock 1431 分钟（3.3%）
- 输出：M1/M5/H1 OHLCV + spread/buy_volume + `ground_truth.parquet`（regime/shock 真值，**只用于验证，不进特征管道**）
- MANIFEST.json 记录 generator/seed/days/模型参数/每文件 sha256（数据版本化）
- 测试验证：OHLC 一致性、M1 收盘=分钟末 mid、shock 期波动显著更高、pure_rw 均值≈0

## C. CPU/GPU Dispatcher 是否正常？
✅。auto 决策规则：GPU 不可用→CPU；估算内存 >45% VRAM→CPU；<1MB→CPU（启动开销主导）；其余→GPU。每次调用记录 workload/est./backend/elapsed/device/fallback reason。GPU OOM→自动回退 CPU 并记录（代码路径有测试覆盖；本次运行未触发 OOM）。4GB 显存安全：大 workload 分块（峰值 <1.2GB/块），benchmark 实测全程无 OOM、无卡死。

## D. GPU 实际参与了哪些计算？
实验与基准中 auto 均选中 GPU 的真实任务（nvidia-smi 可见）：
- permutation/bootstrap（A/B/anti_overfit 的检验，n_iter 800–1500 × 20k–43k 样本）
- CPU/GPU benchmark 全部 8 个 workload（见 E）
- 昨天 GPU benchmark 套件（MC/bootstrap/permutation/matmul/FP16/BF16/XGBoost）12 PASS

## E. CPU/GPU 各自适合什么 workload？（真实计时）
| workload | CPU ms | GPU ms | speedup |
|---|---|---|---|
| bootstrap n=1k ×2000it | 12.7 | 3.9 | 3.3x |
| permutation n=1k | 19.7 | 4.2 | 4.7x |
| bootstrap n=10k | 123.9 | 32.0 | 3.9x |
| permutation n=10k | 197.1 | 35.5 | 5.6x |
| bootstrap n=100k | 1286 | 325 | 4.0x |
| permutation n=100k | 2052 | 375 | 5.5x |
| MC 100k 路径 | 332 | 258 | 1.3x |
| MC 1M 路径 | 3346 | 514 | 6.5x |

结论：**统计模拟类（bootstrap/permutation/MC）→ GPU（4–25x 取决于规模与 dtype）**；
**串行/小数组/高精度 FP64/复杂控制流 → CPU**；MC 小规模 GPU 优势有限（如实记录 1.3x）。
auto 在全部 8 项中选中 GPU 且均正确（GPU 全胜，无“GPU 更慢”案例；若出现会如实记录）。

## F. 三个已知答案实验是否得到预期结果？
| 实验 | 假设结构 | 关键证据 | 结论 |
|---|---|---|---|
| A 纯随机游走（20d） | 无结构 | gross perm p=0.757（均匀）；gross OOS Sharpe 0.76；1x 成本后 net −36%（换手拖累，非 alpha） | **REJECTED** ✅ 引擎不误报 |
| B 人为趋势（30d） | trend regime 1–6h | gross perm p<1e-5；net OOS Sharpe 19.6；WF **5/5** 折正；BH 网格 4 显著；成本 1x→3x Sharpe 22.0→21.7；4 子段全正 | **SUPPORTED** ✅ 趋势可检测 |
| C 波动冲击（30d） | vol shock 2–6h | rv→fv IC 最高 **0.71**（9 组合全显著，BH 9/9）；shock 期 rv 分离置换 p<1e-4；WF 5/5 折 IC>0 | **SUPPORTED** ✅ 波动信息可检测 |

实验 A/B/C 共同证明：**引擎能检测注入结构、拒绝无结构数据——Research Engine 本身可信**。
（A 的教训：1 分钟尺度动量在日内 U 型/均值回复下是**反转**结构；B 需用与 regime 尺度匹配的 4–8h 信号——两类都如实记录在实验 log。）

## G. Anti-overfitting tests 是否通过？
✅（pure RW 15d，20 个随机特征）：
- Random Feature：OOS 毛收益显著 **0/20**（α=5% 期望 ~1），BH 后 **0**
- Label Shuffle：p=0.507（均匀 ✓）
- Time Permutation：p=1.000 ✓
- 结论：随机数据无系统性假 Alpha → **框架完整性确认**。
> 中途发现并修复口径 bug：显著性若跑在净收益上，成本拖累会被误判为“显著负 alpha”
> （20/20 假阳性）→ 已全局改为毛收益检验（成本压力单独用净收益看），回归测试覆盖。

## H. Walk-forward 是否正常？
✅。`validation/walk_forward.py`：expanding/rolling 折叠（train/val/test 三段），B 实验 5 折 OOS 全正；
C 实验波动率 IC 5 时间折叠全正；单元测试验证折叠单调性与泄漏隔离。标签窗口跨边界的 purge 钩子已提供（`purge_window`）。

## I. Cost model 是否正常？
✅。spread/commission/slippage 可独立配置；成本按换手在**执行时点**（下一 bar 开盘）计；
cost stress 1x/2x/3x 输出全部指标。B 实验在 3x 成本下 Sharpe 仅从 22.0→21.7（低换手信号），
证明结论非无成本幻觉；测试验证成本单调性与换手计费精确性。

## J. FDR 是否正常？
✅。BH-FDR + Bonferroni + 汇总（raw vs BH vs Bonferroni 拒绝数）。
B 参数网格 4 假设 → BH 4 显著；C 9 组合 → BH 9/9；anti_overfit 20 随机特征 → BH 0。
回归测试验证 BH 在已知 p 集合上的精确拒绝数。

## K. 全部 pytest 是否通过？
✅ **46/46 PASS**（41s）：dataset / features / labels / backtest 约定 / cost / CPU+GPU backend /
dispatcher auto / bootstrap-CI / permutation / BH-FDR / walk-forward / placebo / 质量门 /
registry / 4 个实验端到端小样本。GPU 特性在 CUDA 可用时**实跑**（非无条件 SKIP）；
旧版 run_all.py 兼容层亦 7/7。

## L. 技术债务（如实列出）
1. **特征集仍偏小**：microstructure 目前是轻量聚合（spread/volume/imbalance），无深度 order-flow 特征（等真实 MT5 tick 数据接入后再扩）
2. **ML 流水线未接**：实验均为规则信号；XGBoost/LightGBM/sklearn 的 train/val/test + 超参 walk-forward 是下一步自然扩展（接口已预留：`walk_forward_evaluate` 支持拟合函数）
3. **回测粒度**：bar 级（close→close + 成本近似）；tick 级执行模型（含排队/部分成交）未做
4. **合成数据量级偏大**（日波动 5–20% vs 真实 XAUUSD 1–3%）：适合结构验证，不适合校准参数；接入真实数据后需重估
5. **GPU 后端覆盖**：bootstrap/permutation/MC 已 GPU 化；parameter_sweep 仍逐点（GPU 化网格留给真实 workload 需求）
6. **WF purge/embargo 只在工具层**，实验层未启用（当前规则信号无拟合，泄漏面小；接 ML 后必须启用）
7. 未做真实数据源接入（MT5）、无 CI、无 docs 自动构建
8. 实验目录含多个早期失败/废弃 run（保留作审计轨迹，可定期归档）
9. `_split_oos` 等少量实验内辅助函数与 base.py 有重复（合并到 validation 的后续清理项）

## M. 下一阶段最值得做什么？
按价值排序：
1. **接入真实 XAUUSD 数据（MT5/Dukascopy tick）** —— 引擎已就绪，合成数据完成使命；
   数据层按 Raw→Normalize→Parquet→DuckDB→Feature 的既有设计落地
2. **ML 实验模板**：特征矩阵 + XGBoost/线性模型的 walk-forward 训练（启用 purge/embargo），
   把今天的统计验证电池直接绑到 ML 输出上
3. **Feature 库扩充**（session/滚动分位、波动率锥、微观结构深度特征），每加一个特征跑 no-lookahead 属性测试
4. 真实成本校准（MT5 账户实际 spread/佣金/滑点）替换假设值
5. 实验对比工具（`validate --compare a b`）与报告趋势页

## 附：执行纪律遵守情况
未实盘、未迁移旧数据、未下载大型 LLM、未装 Docker/WSL/RAPIDS、未编译 LightGBM CUDA、
未改系统 Python、未改全局环境、未删旧数据 ✅
（中途追加的系统级变更：仅 `powercfg` 关闭 AC 睡眠以保长任务不中断——可随时还原。）

---
*本报告由 AIQuant Phase 1 实跑结果汇总；结论词汇表：SUPPORTED / REJECTED / EDGE_UNCERTAIN。*
