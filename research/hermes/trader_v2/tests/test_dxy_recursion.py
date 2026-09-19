# -*- coding: utf-8 -*-
"""V2 回归测试 — DXY RecursionError 根因防护 + 有界重试 + 降级（离线）。

事故（2026-09-14T11:01Z → 2026-09-16）：`macro:yahoo_kv:DX-Y.NYB` 以 ~0.4 行/秒刷审计，
2 天产出 39MB / 97,009 行，错误为 `RecursionError: maximum recursion depth exceeded`
（异常还出现 `RuntimeError:macro source down ... (RuntimeError:macro source down ...)` 自嵌套）。

根因类别：router.macro ↔ sources.<fn> 之间的**重入回流**如果绕过 `_REENTRANT` 守卫
（进程代码为旧版 / 模块被二次加载 / 任意调用方直连），就会形成真正的 Python 互递归；
retry 包装只是把内层异常再包一层（嵌套是症状，不是根因）。
另：macro 路径当时**无 per-source cooldown、无审计限速** → 坏源可无限高速刷日志。

本测试**离线**（注入故障替身，不触网）；断言修复后的结构性边界：
  dxy_recursion_regression: 守卫被绕过也不能递归（有界、无 RecursionError）
  dxy_retry_bound        : retry 有硬上限、retries 参数被截断
  dxy_failure_degradation: 有 last_valid → STALE 返回；无 → 干净 SOURCE_DOWN；冷却期不再打网络；不影响其它源

日志: logs/test_dxy_recursion.log
"""
from __future__ import annotations
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "agents" / "macro_global"))

import data_sources as DS  # noqa: E402
import data_sources.router as RT  # noqa: E402
from data_sources import audit, cache, net  # noqa: E402
import sources as S  # noqa: E402

LOGS = ROOT / "logs"; LOGS.mkdir(exist_ok=True)
LOG = LOGS / "test_dxy_recursion.log"
_RES = []


def log(s):
    line = f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] {s}"
    print(line)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def check(n, c, d=""):
    _RES.append(bool(c))
    log(f"{'PASS' if c else 'FAIL'} | {n} {d}")


TMP = Path(tempfile.mkdtemp(prefix="v2_dxy_"))
_ORIG_RMACRO = None


def _isolate():
    """把审计/缓存/冷却指向临时位置，绝不污染生产文件。"""
    audit.LOG = TMP / "audit.jsonl"
    cache.CACHE = TMP / "cache.json"
    cache._store.clear()
    net.reset_cooldowns()
    audit.reset_limiter()
    RT.AMAC.MACRO_DEFS.pop("t:bad", None)
    RT.AMAC.MACRO_DEFS.pop("t:good", None)
    RT.AMAC.MACRO_DEFS.pop("yahoo_kv:TESTREC", None)


def _rows():
    p = audit.LOG
    return p.read_text(encoding="utf-8").splitlines() if p.exists() else []


def _bust_recursion_guard():
    """模拟守卫失效：让 sources._rmacro 无条件回流到 router.macro（旧版进程 / 双模块实例）。"""
    global _ORIG_RMACRO
    _ORIG_RMACRO = S._rmacro

    def _unguarded(name):
        try:
            import data_sources.adapters_macro as _am
            if name not in _am.MACRO_DEFS:
                return S._MISS
        except Exception:  # noqa: BLE001
            return S._MISS
        return DS.macro(name)

    S._rmacro = _unguarded


def _restore_guard():
    global _ORIG_RMACRO
    if _ORIG_RMACRO is not None:
        S._rmacro = _ORIG_RMACRO
        _ORIG_RMACRO = None


# ---------------------------------------------------------------- 1
def dxy_recursion_regression():
    _isolate()
    stats = {"adapter_calls": 0, "rmacro_calls": 0}

    def adapter_fn():
        stats["adapter_calls"] += 1
        return RT.AMAC.yahoo_kv("TESTREC", "1d", "5d")   # 走 _legacy → sources.yahoo_kv（真实回流路径）

    # 模拟旧版进程：fn 经 adapter→sources 回流，而守卫失效
    RT.AMAC.MACRO_DEFS["yahoo_kv:TESTREC"] = (adapter_fn, (1, 10), "host-rec")
    _bust_recursion_guard()
    _rmacro_orig = S._rmacro

    def _counting_unguarded(name):
        stats["rmacro_calls"] += 1
        return _rmacro_orig(name)

    S._rmacro = _counting_unguarded
    try:
        t0 = time.time()
        exc = None
        try:
            S.yahoo_kv("TESTREC")        # → _rmacro(失效) → router.macro → adapter → sources → router.macro …
        except BaseException as e:  # noqa: BLE001
            exc = e
        dt = time.time() - t0
        check("递归回归：无 RecursionError 逃逸", not isinstance(exc, RecursionError), f"{type(exc).__name__}")
        check("递归回归：有界完成(<20s)", dt < 20, f"dt={dt:.2f}s")
        check("递归回归：结构性阻断已生效",
              isinstance(exc, RuntimeError) and "REENTRANT_SOURCE_LOOP" in str(exc), str(exc)[:140])
        check("递归回归：回流深度有界(_rmacro <= MAX_RETRIES+2)",
              stats["rmacro_calls"] <= RT.MAX_RETRIES + 2, f"rmacro_calls={stats['rmacro_calls']}")
        check("递归回归：网络层未被触发(fn 调用有界)",
              stats["adapter_calls"] <= RT.MAX_RETRIES + 1, f"adapter_calls={stats['adapter_calls']}")
    finally:
        _restore_guard()


# ---------------------------------------------------------------- 2
def dxy_retry_bound():
    _isolate()
    calls = {"n": 0}

    def bad():
        calls["n"] += 1
        raise RuntimeError("boom")

    RT.AMAC.MACRO_DEFS["t:bad"] = (bad, (1, 10), "host-bad2")
    r = RT.Router()
    net.reset_cooldowns()
    calls["n"] = 0
    try:
        r.macro("t:bad", retries=2, backoff=0.05)
    except Exception:  # noqa: BLE001
        pass
    check("retry 上限：retries=2 → 调用 <=3", calls["n"] <= 3, f"calls={calls['n']}")
    net.reset_cooldowns()
    calls["n"] = 0
    try:
        r.macro("t:bad", retries=10_000, backoff=0.05)   # 必须被截断
    except Exception:  # noqa: BLE001
        pass
    check("retry 上限：retries=10000 被截断 <= MAX_RETRIES+1",
          calls["n"] <= RT.MAX_RETRIES + 1, f"calls={calls['n']} MAX={RT.MAX_RETRIES}")
    net.reset_cooldowns()


# ---------------------------------------------------------------- 3
def dxy_failure_degradation():
    _isolate()
    calls = {"n": 0}

    def bad():
        calls["n"] += 1
        raise RuntimeError("source down")

    RT.AMAC.MACRO_DEFS["t:bad"] = (bad, (1, 10), "host-bad3")
    RT.AMAC.MACRO_DEFS["t:good"] = (lambda: {"v": 42}, (1, 10), "host-good3")
    r = RT.Router()

    # (a) 无缓存 → 干净 SOURCE_DOWN（不是 RecursionError）
    try:
        r.macro("t:bad")
        check("降级(a) 无缓存 → 抛 SOURCE_DOWN", False, "unexpected ok")
    except Exception as e:  # noqa: BLE001
        check("降级(a) 无缓存 → 干净 SOURCE_DOWN",
              isinstance(e, RuntimeError) and "macro source down" in str(e), f"{type(e).__name__}")
    check("降级(a) host 已进入冷却", "host-bad3" in net.cooldowns(), str(net.cooldowns()))

    # (b) 冷却期内再次调用 → 不再打网络（fn 不再被调用）
    before = calls["n"]
    try:
        r.macro("t:bad")
    except Exception:  # noqa: BLE001
        pass
    check("降级(b) 冷却期不再重试网络", calls["n"] == before, f"{before} -> {calls['n']}")

    # (c) 有 last_valid → 返回 STALE 而不是抛
    net.reset_cooldowns()
    cache.put("macro:t:bad", {"v": 7}, "t:bad", fresh_h=1, stale_h=10)
    v = r.macro("t:bad")
    rec = cache.get("macro:t:bad")
    check("降级(c) 有 last_valid → 返回旧值", isinstance(v, dict) and v.get("v") == 7, str(v))
    check("降级(c) 状态标 STALE_BUT_VALID", rec.get("freshness") == cache.STALE, str(rec.get("freshness")))

    # (d) 坏源不影响其它源
    net.reset_cooldowns()
    check("降级(d) 健康源不受影响", r.macro("t:good") == {"v": 42})

    # (e) 审计限速：坏源连续失败不得线性刷日志
    _isolate()
    RT.AMAC.MACRO_DEFS["t:bad"] = (bad, (1, 10), "host-bad3")
    n0 = len(_rows())
    for _ in range(12):
        net.reset_cooldowns()          # 强制每次真的尝试（放大压力）
        try:
            r.macro("t:bad", retries=0)
        except Exception:  # noqa: BLE001
            pass
    grew = len(_rows()) - n0
    check("降级(e) 审计限速生效(12 次失败 → 直写 <= MAX_DIRECT+1)", grew <= audit.MAX_DIRECT + 1,
          f"rows +{grew}")

    # (f) health_report 不因坏源崩溃（agent2 依赖）
    try:
        hr = DS.health_report()
        check("降级(f) health_report 可用", isinstance(hr, dict) and "agent1" in hr)
    except Exception as e:  # noqa: BLE001
        check("降级(f) health_report 可用", False, f"{type(e).__name__}:{e}")


def main():
    _isolate()
    dxy_recursion_regression()
    dxy_retry_bound()
    dxy_failure_degradation()
    audit.reset_limiter()
    net.reset_cooldowns()
    log(f"=== RESULT: {sum(_RES)}/{len(_RES)} PASS ===")
    return 0 if all(_RES) else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
