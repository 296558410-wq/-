# -*- coding: utf-8 -*-
"""交易时段 / 日历 —— XAUUSD (FXTM MT5)。

来源：由本项目实盘 tick 数据反推（data/live_fxtm/ticks_*.parquet，MT5 服务器时间 = UTC+3），
与标准 XAUUSD 现货时段一致（web_fetch 本机不可用，故以本地 ground truth 为准）：
    周开: 周日 22:00 UTC   (= 周一 06:00 GMT+8)
    周收: 周五 21:00 UTC   (= 周六 05:00 GMT+8)
    日内休: 周一~周五 21:00-22:00 UTC
    周末: 周五21:00 -> 周日22:00 休市

"armed"（可启动引擎）= 开市前 PREOPEN_HOURS 小时起，到周收：
    周日 20:00 UTC (= 周一 04:00 GMT+8) -> 周五 21:00 UTC

只读工具，不被 V1/V2 代码 import。用法:
    python trading_hours.py --json          # 打印状态
    python trading_hours.py --gate          # armed 退出0, 否则退出1（供调度前置门）
    python trading_hours.py --selftest      # 边界自测
"""
from __future__ import annotations
import argparse, json, sys
from datetime import datetime, timedelta, timezone

OPEN_WD, OPEN_H = 6, 22      # Sunday 22:00 UTC
CLOSE_WD, CLOSE_H = 4, 21    # Friday 21:00 UTC
BREAK_H = 21                 # daily break 21:00-22:00 UTC
PREOPEN_HOURS = 2            # 开市前 2 小时启动


def _wd(dt):
    return dt.weekday()  # Mon=0 .. Sun=6


def is_armed(dt=None):
    """开市前2小时 -> 周收：允许启动/运行引擎。"""
    dt = dt or datetime.now(timezone.utc)
    wd, h = _wd(dt), dt.hour + dt.minute / 60.0
    if wd == 6:              # Sun: from 20:00
        return h >= (OPEN_H - PREOPEN_HOURS)
    if wd in (0, 1, 2, 3):   # Mon-Thu: all day
        return True
    if wd == 4:              # Fri: until 21:00
        return h < CLOSE_H
    return False             # Sat


def is_open(dt=None):
    """市场是否真开（含日内休市剔除）。"""
    dt = dt or datetime.now(timezone.utc)
    wd, h = _wd(dt), dt.hour + dt.minute / 60.0
    if wd == 6:
        return h >= OPEN_H
    if wd in (0, 1, 2, 3):
        return not (BREAK_H <= h < BREAK_H + 1)
    if wd == 4:
        return h < CLOSE_H
    return False


def status(dt=None):
    dt = dt or datetime.now(timezone.utc)
    return {"utc": dt.astimezone(timezone.utc).isoformat(),
            "local_gmt8": dt.astimezone(timezone(timedelta(hours=8))).isoformat(),
            "weekday": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][_wd(dt)],
            "open": is_open(dt), "armed": is_armed(dt),
            "window": "Sun20:00Z -> Fri21:00Z (armed); Sun22:00Z -> Fri21:00Z (open)",
            "reason": ("open" if is_open(dt) else ("pre-open/warmup" if is_armed(dt) else "weekend closed"))}


def _selftest():
    z = timezone.utc
    C = [  # (iso utc, armed, open)
        ("2026-09-13T19:59:00+00:00", False, False),  # Sun before pre-open
        ("2026-09-13T20:00:00+00:00", True,  False),  # Sun pre-open start == armed
        ("2026-09-13T21:59:00+00:00", True,  False),
        ("2026-09-13T22:00:00+00:00", True,  True),   # Sun open
        ("2026-09-14T12:00:00+00:00", True,  True),   # Mon
        ("2026-09-14T20:59:00+00:00", True,  True),
        ("2026-09-14T21:00:00+00:00", True,  False),  # Mon daily break
        ("2026-09-14T22:00:00+00:00", True,  True),
        ("2026-09-18T20:59:00+00:00", True,  True),   # Fri last minute open
        ("2026-09-18T21:00:00+00:00", False, False),  # Fri close
        ("2026-09-19T12:00:00+00:00", False, False),  # Sat
    ]
    bad = 0
    for iso, a, o in C:
        dt = datetime.fromisoformat(iso).astimezone(z)
        ga, go = is_armed(dt), is_open(dt)
        ok = (ga == a and go == o)
        bad += 0 if ok else 1
        print(f"{'PASS' if ok else 'FAIL'} | {iso} armed={ga}({a}) open={go}({o})")
    print(f"=== SELFTEST: {len(C)-bad}/{len(C)} PASS ===")
    return 0 if bad == 0 else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--gate", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--at", help="evaluate at ISO time (UTC) instead of now; for verification")
    a = ap.parse_args()
    if a.selftest:
        return _selftest()
    dt = datetime.fromisoformat(a.at).astimezone(timezone.utc) if a.at else None
    if a.gate:
        s = status(dt)
        print(json.dumps(s, ensure_ascii=False))
        return 0 if s["armed"] else 1
    print(json.dumps(status(dt), ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
