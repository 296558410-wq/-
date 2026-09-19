# Decision Log

> 用户最终决策记录（User = 项目所有者与最终决策者）。
> ChatGPT 负责独立审计，OpenClaw 负责本地执行，Hermes 负责交易智能。
> 本文件只记录**用户明确作出**的决策；不臆造。

## Decision Template

### DECISION-ID
日期：

决策：

背景：

依据：

影响范围：

涉及版本：

用户最终决定：

状态：

相关 Git Commit：

相关报告：

---

### DECISION-001

日期：2026-09-19

决策：**建立 GitHub 协作层 V1**

背景：
- 项目需要 `用户 → ChatGPT → GitHub → OpenClaw → Hermes → GitHub → ChatGPT → 用户` 的可追溯协作链。
- GitHub 作为共享项目事实层；此前已发布 clean baseline。

依据：
- 已冻结并通过独立复核的 GitHub baseline：`22f27df40f4f3b71fdbbcc9a92753c3bb2743241`（branch `main`，commit count = 1）。
- 用户指示：建立协作层文件与协议，`V1/V2/V3/Hermes 不因本任务修改`。

影响范围：
- 仅新增协作层文档（`PROJECT_COLLABORATION.md` 更新 + `collaboration/**`）。
- **不影响**交易系统运行、MT5 账户、broker、execution、risk、scheduler 配置。

涉及版本：V1 / V2 / V3 / Hermes —— **均不修改（READ ONLY）**

用户最终决定：
- GitHub 作为**协作事实层**
- **ChatGPT** 负责**独立审计**
- **OpenClaw** 负责**本地执行**
- **Hermes** 负责**交易智能**
- **用户**保留**最终决策权**
- GitHub baseline = `22f27df40f4f3b71fdbbcc9a92753c3bb2743241`（不改写、不 force）

状态：ACCEPTED

相关 Git Commit：（本决策随协作层 v1 commit 落库，见 `collaboration/status/COLLABORATION_LAYER_V1_REPORT.md`）

相关报告：`collaboration/status/COLLABORATION_LAYER_V1_REPORT.md`

---
