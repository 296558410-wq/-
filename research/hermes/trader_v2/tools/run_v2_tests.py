# -*- coding: utf-8 -*-
"""V2 全量回归 runner —— 一条命令跑完 tests/test_*.py 并汇总（PASS/FAIL + 退出码）。

用法:
    python tools/run_v2_tests.py            # 全部
    python tools/run_v2_tests.py broker dxy # 只跑名字含 broker/dxy 的
每个测试为脚本式（PASS| 行 + RESULT x/x），退出码 0=全 PASS。
"""
from __future__ import annotations
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PY = Path(sys.executable)


def main(argv):
    tests = sorted(p for p in (ROOT / "tests").glob("test_*.py"))
    if argv:
        tests = [t for t in tests if any(k.lower() in t.name.lower() for k in argv)]
    if not tests:
        print("no tests matched")
        return 2
    results = []
    for t in tests:
        t0 = time.time()
        try:
            p = subprocess.run([str(PY), str(t)], cwd=str(ROOT), capture_output=True,
                               text=True, encoding="utf-8", errors="replace", timeout=900)
            rc = p.returncode
            out = (p.stdout or "") + (p.stderr or "")
            res = [l for l in out.splitlines() if "RESULT" in l]
            detail = res[-1].strip() if res else (out.strip().splitlines()[-1][:100] if out.strip() else "(no output)")
        except subprocess.TimeoutExpired:
            rc, detail = 999, "TIMEOUT>900s"
        results.append((t.name, rc, round(time.time() - t0, 1), detail))
        print(f"{'OK ' if rc == 0 else 'ERR'} rc={rc:<4} {results[-1][2]:6.1f}s {t.name:34} | {detail[-96:]}")
        sys.stdout.flush()
    bad = [r for r in results if r[1] != 0]
    print(f"\n=== FULL_REGRESSION: {len(results)-len(bad)}/{len(results)} PASS ===")
    for b in bad:
        print(f"  FAIL {b[0]} rc={b[1]} :: {b[3]}")
    print("FULL_REGRESSION =", "PASS" if not bad else "FAIL")
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv[1:]))
