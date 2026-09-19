# -*- coding: utf-8 -*-
"""V2 回归 — 控制面板（驾驶舱）全链路可观测性。

覆盖任务书 §34 测试 A–J + §25 未知/陈旧/错误 + 中文 UI 契约 + 旧功能保留。
日志: logs/test_dashboard_fullchain.log
"""
from __future__ import annotations
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "dashboard"))
import datasource as DS  # noqa: E402

LOGS = ROOT / "logs"; LOGS.mkdir(exist_ok=True)
LOG = LOGS / "test_dashboard_fullchain.log"
_RES = []


def log(s):
    line = f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] {s}"
    print(line)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def check(n, c, d=""):
    _RES.append(bool(c))
    log(f"{'PASS' if c else 'FAIL'} | {n} {d}")


def main():
    js = (ROOT / "dashboard" / "static" / "app.js").read_text(encoding="utf-8")
    html = (ROOT / "dashboard" / "static" / "index.html").read_text(encoding="utf-8")
    dsrc = (ROOT / "dashboard" / "datasource.py").read_text(encoding="utf-8")

    # 未知/陈旧/错误
    check("未知 -> 暂无数据 (非0)", DS._obs_item("x", None)["status"] == "暂无数据")
    check("新鲜 -> 正常", DS._obs_item("x", 100)["status"] == "正常")
    check("较旧", DS._obs_item("x", 1000)["status"] == "较旧")
    check("异常", DS._obs_item("x", 5000)["status"] == "异常")
    check("未来时间 -> 数据时间异常", DS._obs_item("x", -10)["status"] == "数据时间异常")

    # 驾驶舱聚合（broker patched -> 未知；不发 MT5）
    DS.broker_account = lambda: {"ok": False, "error": "test"}
    o = DS.observability_full()
    for k in ("system_status", "system_cls", "run_mode", "real_orders", "stage", "market", "multi_tf",
              "data_items", "decision", "why_no_trade", "account", "position", "recent_trades",
              "performance", "health", "workflow", "scheduler", "forward_gate", "v1_isolation", "last_update"):
        check(f"obs 含 {k}", k in o)
    check("A 系统状态有效", o["system_status"] in ("正常", "部分异常", "严重异常"))
    check("D broker unknown -> position.known False", (o.get("position") or {}).get("known") is False)
    check("E/F forward gate 未允许", (o.get("forward_gate") or {}).get("label") == "未允许")
    check("E real_orders 否", o.get("real_orders") == "否")
    check("decision 中文 cn", "cn" in (o.get("decision") or {}))
    check("performance 有范围", (o.get("performance") or {}).get("scope"))
    check("health 列表", isinstance(o.get("health"), list) and len(o["health"]) >= 5)
    check("workflow 列表", isinstance(o.get("workflow"), list) and len(o["workflow"]) >= 6)
    check("market symbol", (o.get("market") or {}).get("symbol"))
    check("multi_tf >=4", isinstance(o.get("multi_tf"), list) and len(o["multi_tf"]) >= 4)
    check("scheduler dict", isinstance(o.get("scheduler"), dict))
    check("v1_isolation 正常", (o.get("v1_isolation") or {}).get("status") == "正常")

    # 中文 UI 契约（首页 10 秒看懂）
    for tok in ("现在系统怎么样", "现在到底有没有交易", "账户", "系统表现", "最近交易",
                "数据是否正常", "系统健康", "V2 工作流程", "当前黄金行情", "多周期行情",
                "当前运行（Shadow）", "正式前向验证", "自动运行", "V1 安全", "技术详情"):
        check(f"UI 区块「{tok}」", tok in html)
    for tok in ("等待交易机会", "发现交易机会", "为什么现在不交易", "暂时无法确认", "真实下单",
                "未允许", "无法确认"):
        check(f"中文文案「{tok}」", tok in js)
    check("无 '虚拟账户'", "虚拟账户" not in html and "虚拟账户" not in js)
    check("无 'Paper Equity'", "Paper Equity" not in js)
    check("未知不用 0 掩盖", ("无法确认" in js) and ("未知" in js))
    check("数据时间≠页面时间 (data_age)", "data_age_s" in dsrc or "age_s" in dsrc)

    # datasource 只读 / 不读 V1
    check("datasource 暴露 observability_full", "def observability_full" in dsrc)
    check("§25-7 不引用 trader_v1", "trader_v1" not in dsrc)

    # server 只读（无 POST）
    srv = (ROOT / "dashboard" / "server.py").read_text(encoding="utf-8")
    check("server 无 POST/下单", (".post(" not in srv) and ("order" not in srv.lower()))

    # 旧功能保留（不缩水）
    for tok in ("eqChart", "donut", "sizingTbl", "ledTbl", "runsTbl", "id=\"a1\"", "id=\"a2\"", "heat"):
        check(f"保留旧面板 {tok}", tok in html)
    for fn in ("drawEquity", "drawDonut", "renderSizing", "renderLedger", "renderRuns", "renderA1", "renderA2"):
        check(f"保留旧渲染 {fn}", fn in js)

    log(f"=== RESULT: {sum(_RES)}/{len(_RES)} PASS ===")
    return 0 if all(_RES) else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
