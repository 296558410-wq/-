# HERMES TRADER V1 — 完整架构审计报告（重构前）
> 审计日期: 2026-09-07 20:12-20:30 · 审计人: OpenClaw(总控)
> 方法: 逐行精读全部模块 + 实证探针(非凭记忆) + 生产 run_state 取证
> 范围: Protocol / Decision / Trade Plan / Trigger / Risk / Execution / Position Mgmt /
>       Review / Memory / Ledger / Dashboard / cron 调度
> 结论: **P0 观察闭环可运行且首次决策质量好, 但作为"交易生命周期系统"存在 3 个高危 + 8 个中危 + 5 个低危缺陷。
>        Position Management 实质未实现(paper_execute 从未调用, 无仓位状态机, 无 EXIT 路径)。**

---
## 一、高危缺陷（必须先修）

### H1. 同一决策可被重复消费 → 重复注册/重复下单（实证）
- 位置: engine.py `--decide` 分支
- 证据: 隔离探针——同一 decision 处理 3 次 → ledger 出现 3 个 registered（应 1）
- 根因: 决策文件无 `consumed` 标记; engine 每次 `--decide` 重读同一文件即重注册; cron 与手动/重试重叠即触发
- 后果: 真实执行阶段 = 重复下单风险
- 修复: decision 文件消费幂等(记录 consumed_cycle/文件 hash); ledger 注册查重(plan 已存在则跳过)

### H2. TRIGGERED 计划可被重复触发（实证）
- 位置: engine.py trigger 循环
- 证据: 隔离探针——触发条件持续满足且无 filled → 2 个 triggered 事件（应 1）
- 根因: plan 状态机缺失; triggered 后无 "awaiting_fill/executed" 迁移; 下轮仍满足条件即再触发
- 后果: 真实执行 = 重复下单
- 修复: 计划状态机 registered→triggered→(filled|rejected|cancelled); 每个触发点原子转移, 已处理不再评估

### H3. 状态包使用未收盘 M15 bar（轻微 look-ahead / 信号不稳定）
- 位置: state_package.py build_tf / resample
- 证据: 12:03 生成状态包, 最新 tick 12:13:41, 但 M15 last_bar=12:00(未收盘, 12:00-12:15 尚在进行)
- 根因: resample 含当前进行中 bar; engine :02 相位本应只消费已收盘 M15
- 后果: 决策用到仍在形成的 bar close → 回放/实盘口径不一致, 复现性受损
- 修复: 状态包显式排除"未收盘"顶层 bar(last bar 的结束时间 > now 则回退到上一根); 或 engine 只取 cycle 对应已收盘 bar

---
## 二、中危缺陷

### M1. Position Management 实质未实现
- paper_execute() 定义但 0 次调用(静态检查实证); paper_positions.json 不存在
- 无仓位状态机; 无 OPEN→CLOSE/PARTIAL/ADD/REDUCE 任何路径; MANAGE 分支是 print 占位
- EXIT/REVIEW 全链路断裂(review.py 从未被 engine 调用)
- 后果: 系统只能"观察+计划+WAIT", 一旦出现真实触发将无法持仓

### M2. 假风控字段
- RISK_POLICY 定义 max_daily_loss_pct / max_consecutive_losses / max_account_risk_per_trade_pct
  但在 risk_check 中从不检查(实证: 仅定义处 1 次引用)
- max_position_notional 检查存在但计算悬空(lots 算完即弃)
- 后果: 违背"Risk Engine 独立执行硬风控"要求; 真持仓后无日亏/连亏熔断

### M3. 无仓位/事件幂等与恢复
- 进程重启/网络中断后: ledger 是唯一事实源, 但无 position snapshot; 无 replay/恢复逻辑
- 部分成交/拒单/reject 后状态无定义(broker 反馈从未建模)

### M4. M15 周期重复执行防护缺失
- engine 无"同一 cycle 只处理一次"的锁/标记; cron 与手动重叠可双跑(DB-1 同一根因)
- workflow_latest 每轮覆盖, 无 cycle 单调校验(旧 cycle 覆盖新状态风险)

### M5. workflow 时间倒挂(显示缺陷)
- 实证: OBSERVE start=11:51 > end=11:46 (engine_start 晚于 pkg 生成时间)
- 根因: write_workflow 用 engine 启动时间作 OBSERVE.start、pkg 时间为 end, 顺序颠倒
- 后果: Dashboard 显示负/倒挂耗时, 误导

### M6. 死 import 与死代码
- engine.py: pd / load_ticks / resample 导入未用; paper_positions 逻辑只读不写
- 显示代码整洁性 + 潜在维护陷阱

### M7. 契约与实现偏差
- DECISION_CONTRACT 要求 decision_id 等字段, 实现未生成/校验 decision_id
- TRIGGER_CONTRACT 说"计划注册后持续监听价格穿透", 实际仅 M15 收盘判定(P0 可接受但未标注为限制)
- MEMORY_CONTRACT statistics 要求 frequency/execution_quality, 实现仅 counters/waits
- TRADE_PLAN_CONTRACT 的 vol_ceiling/spread_ceiling/time_stop 实现未消费(仅 trigger ctx spread)

### M8. review.py 契约未接入
- REVIEW_CONTRACT 定义了完整 review, 但 build_review 需要 fill/exit 事件(不存在)
- 无"平仓后自动生成 review"的触发点

---
## 三、低危/待设计

### L1. 价格精度纪律缺失
- XAUUSD 报价 2 位小数(实证分布: 899×2位/101×1位), 代码无 round(price, 2) 纪律
- SL/TP/entry 可能带 >2 位浮点 → broker 侧拒单/舍入不一致风险

### L2. SL/TP 最小距离、min/max lot、margin 检查全部缺失
- validate_plan 只查几何顺序与 EV, 不查 SL 距 entry 最小距离(与 spread/ATR 关系)

### L3. 无单仓方向一致性约束
- "同一账户同时存在互相冲突仓位"无防护(LONG 持仓时又开 SHORT 无拒绝逻辑)

### L4. dashboard 状态推断脆弱
- Hermes 动态状态基于 workflow 步骤启发式推断, 无显式状态源; "异常"态无明确触发

### L5. cron 消息步骤冗长且无失败重试语义
- isolated 会话若中途失败, 决策文件可能半写 → 下轮读到残文件

---
## 四、未发现问题的项(确认良好)
- ledger sha256 链 + verify: 工作正常(实测 True)
- trigger 机械三态: 逻辑正确(实测 TRIGGERED/PENDING/CANCELLED)
- WAIT 合法化 + 连续计数 + 原因统计: 工作正常
- cron 每 15 分钟调度: 实测 2 轮完整跑通(11:46, 12:03), 决策质量高(Hermes 手算 EV, 纪律性等待)
- state_package 多周期数值: 合理(staging+live 同 feed, 25 上下文日)
- EV/几何自洽校验: validate_plan 正确标记 WEAK_EV(实测 -0.16R 被标)

---
## 五、审计结论与重构范围建议
1. **P0 观察闭环保留**(不破坏已工作基础设施), 但 H1/H2 必须先修(正确性红线)。
2. **Position Management 从零实现** = 本次重构主体(状态机/决策契约/幂等/恢复)。
3. 重构层次:
   - L0(必修, 正确性): H1/H2 幂等 + 计划状态机
   - L1(重构主体): Position State Machine + Position Decision Contract + 持仓管理决策优先级
   - L2(支撑): 未收盘 bar 修复(H3) + risk 熔断落地(M2) + review 接入(M8)
   - L3(质量): 价格精度/min-max lot/SL-TP 距离/单仓方向约束 + 测试矩阵 + 不变量 FAIL CLOSED
4. 所有重构遵守: 不变量先行 → 测试先行 → 再实现 → replay 验证 → 报告。
