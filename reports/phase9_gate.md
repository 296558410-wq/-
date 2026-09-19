# PHASE 9A GATE — PRE-REGISTRATION LOCK 判定

> 判定时间 UTC：2026-09-04T23:12:08Z（audit 运行）· 冻结时间 UTC：2026-09-04T23:03:07Z
> Audit：`scripts/phase9a_audit.py`（独立 dry-run：只读 registry/代码，未触碰行情数据与 MT5 终端）
> 证据：`reports/phase9_gate_evidence.json`（22/22 检查通过）· 权威 registry：
> `research/phase9/registry/phase9_detector_registry.yaml`

# GATE VERDICT: PASS

Phase 9A（Pre-Registration Lock）通过。P1–P7 已从研究概念转换为**完全可执行、可复现、已冻结**的
实验注册表（27 探测器 × 27 字段）。**DISCOVERY 未启动**；等待 Research Gate 放行后才可进入
Phase 9 Discovery（届时仍受本注册表所有冻结约束）。

---

## 完成标准对照（14/14）

| # | 完成标准 | 状态 | 证据 |
|---|---|---|---|
| 1 | P1–P7 executable definition 完整 | ✅ PASS | 27 detectors × 27 字段非空（audit C04）；数学定义/特征/数据字段逐探测器冻结 |
| 2 | 所有参数冻结 | ✅ PASS | registry `meta.frozen=true`；重生成字节一致（C12）；z 阶梯闭式+固定阈值+依据（C07） |
| 3 | 所有 baseline 冻结 | ✅ PASS | 每族 B3/B4/B5/B7/B8 嵌套基线声明于 registry `families.*.baseline`（C03 全字段校验覆盖 field 16） |
| 4 | Cost model 冻结 | ✅ PASS | 全局 cost_model：FXTM 0.26 USD/DUKA 0.41–0.80 USD 往返，×1/2/3 压力，taker-only（field 15） |
| 5 | Discovery/Validation/OOS 冻结 | ✅ PASS | 两层时段按 UTC 日期锁定，D≤V≤OOS 单调（C09）；tick 层 OOS=PENDING(DUKA tick) 显式声明，无静默跳过 |
| 6 | FDR family 冻结 | ✅ PASS | BH q=0.05 两层（族×层 + 整轮 VALIDATION）；每族 FDR 集合冻结，禁事后重定义（field 22） |
| 7 | dependency-aware statistics 冻结 | ✅ PASS | 非重叠入场/日聚类 bootstrap/effective n≥300/150/1000/正天数门槛（field 13/14） |
| 8 | overlap rule 冻结 | ✅ PASS | 同一探测器相邻入场≥持期；同族跨尺度去重；重叠>30%→联合 FDR 单元；重叠矩阵必报（field 13） |
| 9 | historical REJECT registry 接入 | ✅ PASS | `research/registry/hypothesis_registry.yaml` 固化 17 条终审 + P1–P7 redundancy map；registry 显式引用；差异化缺失→自动 REJECT（C10/C10b/C10c） |
| 10 | no-lookahead audit PASS | ✅ PASS | 静态语义审计：entry ≥ t_sig+delay、信号时间戳仅用 ≤t 信息、exit>entry（C08）；实现契约（ts-leak 冒烟）写入 global_protocol，Discovery 代码 gate 前必跑 |
| 11 | MT5 safety PASS | ✅ PASS | REAL 账户已记录（env_smoke_mt5.json）；`configs/mt5_research_readonly.env` + `tools/mt5_readonly.py` guard（fail-closed，置换 order_send/account_update/calc_*）；代码静态扫描 0 命中；token 清单 registry↔guard 一致（C11/C11b） |
| 12 | registry 可机器读取 | ✅ PASS | 两个 YAML safe_load 通过（C02/C02b）；无 merge-key/锚点，全展开；27 字段 schema 在 meta 声明（C03b） |
| 13 | 独立 dry-run PASS | ✅ PASS | `scripts/phase9a_audit.py` 独立运行 22/22 通过、exit 0；dry-run 隔离校验：未 import MetaTrader5/pandas/duckdb、未触数据（C13） |
| 14 | Git commit | ✅ PASS | commit `cf76214`（本文件随 commit 记录；锁内容提交见同 commit） |

---

## Audit 摘要（reports/phase9_gate_evidence.json）

- 22 项检查全部 PASS，0 FAIL；GATE_VERDICT = PASS。
- 冻结物：
  - `research/phase9/registry/phase9_detector_registry.yaml`（27 detectors，164,938 bytes）
  - `research/phase9/registry/build_phase9_registry.py`（冻结 spec + 确定性生成器）
  - `research/registry/hypothesis_registry.yaml`（历史终审 + P1–P7 冗余守卫）
  - `tools/mt5_readonly.py` · `configs/mt5_research_readonly.env`
  - `reports/phase9_preregistration.md`（人读冻结声明）

## 范围声明（诚实记录）

1. **no-lookahead 审计范围**：当前无任何 Discovery 实现代码，审计在“定义层静态语义 + 实现契约”上
   成立；Discovery 代码落地后每个 gate 须重跑静态审计 + ts-leak 冒烟（契约已冻结）。
2. **tick 层 OOS**：FXTM 23 日窗内无法再切 OOS 段；tick 层 OOS 与 CROSS-FEED 依赖 DUKA tick
   （下载中）→ 任何 ≤1m 候选至多 VALIDATION 级，**PASS 必须等 DUKA tick 独立验证**
   （framework §5/§15 Gate 7，非本 Gate 阻塞项）。
3. **MT5 REAL 账户**：无法在本环境切换 DEMO（单一终端已登录 live）；以代码级只读模式 + 静态扫描
   0 命中 + 全程不连接终端的 dry-run 作为本 Gate 的 MT5 safety 边界。后续任何 MT5 接触必须先过
   `tools/mt5_readonly.py` guard。

---

*终审措辞纪律：本文件只使用 PASS/REJECT/EDGE UNCERTAIN 判定词；结论为 **PASS**。
Phase 9A 完成后停止。不自动进入 Discovery，等待 Research Gate。*
