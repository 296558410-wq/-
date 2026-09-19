# -*- coding: utf-8 -*-
"""REPAIR-006：状态原子写 + 跨进程 Run 锁。

范围：仅 run 生命周期/并发/状态一致性。**不触碰** trading 逻辑 / PIT / 策略 / 数据源。
- write_atomic(): 临时文件 + fsync + os.replace（防半写 JSON 损坏）。
- RunLock: 进程级互斥（O_CREAT|O_EXCL 锁文件 + pid + stale 接管），用于 start_run 关键区。
"""
from __future__ import annotations
import json, os, time
from pathlib import Path


def write_atomic(p, obj):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + f".tmp.{os.getpid()}.{int(time.time() * 1000)}")
    data = json.dumps(obj, indent=1, ensure_ascii=False)
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, p)  # 原子替换
    return p


def _alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except Exception:  # noqa: BLE001
        return False


class RunLock:
    """跨进程互斥。获取失败（被占用且非 stale）→ 抛 RuntimeError（明确拒绝，绝不静默并发）。"""

    def __init__(self, path, stale_sec=1800.0, timeout_sec=0.0):
        self.path = Path(path)
        self.stale_sec = stale_sec
        self.timeout_sec = timeout_sec

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        deadline = time.time() + self.timeout_sec
        while True:
            try:
                fd = os.open(str(self.path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(fd, str(os.getpid()).encode("ascii"))
                os.close(fd)
                return self
            except FileExistsError:
                try:
                    pid = int((self.path.read_text(encoding="ascii").strip() or "0"))
                    age = time.time() - self.path.stat().st_mtime
                    if age > self.stale_sec or not _alive(pid):
                        try:
                            self.path.unlink()
                        except FileNotFoundError:
                            pass
                        continue
                except Exception:  # noqa: BLE001
                    pass
                if time.time() >= deadline:
                    raise RuntimeError("REFUSE_TO_START: run lock held (concurrent start_run)")
                time.sleep(0.05)

    def __exit__(self, *a):
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass
