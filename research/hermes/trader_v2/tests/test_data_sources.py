# -*- coding: utf-8 -*-
"""V2 Data Source Router — 测试（unit + failure injection + PIT + failover drill + isolation）。

离线；不触 broker；用故障注入替身。脚本式（与其它 V2 测试一致）: PASS| 行 + RESULT x/x。
日志: logs/test_data_sources.log
"""
from __future__ import annotations
import os, sys, time, json, re
from pathlib import Path

HERE = Path(__file__).resolve().parent                       # .../trader_v2/tests
ROOT = HERE.parent                                           # .../trader_v2
sys.path.insert(0, str(ROOT))
os.environ["V2_DATA_ROUTER_ENABLED"] = "true"                # 测试启用 router

import data_sources as DS                                    # noqa: E402
from data_sources import cache as C, net, validate, registry  # noqa: E402
from data_sources import adapters_market as AM               # noqa: E402
from data_sources import adapters_macro as AMAC              # noqa: E402
from data_sources import mt5_market as MT                    # noqa: E402

LOGS = ROOT / "logs"; LOGS.mkdir(exist_ok=True)
LOG = LOGS / "test_data_sources.log"
OUT = []
N = {"p": 0, "f": 0}


def check(name, cond, detail=""):
    tag = "PASS" if cond else "FAIL"
    N["p" if cond else "f"] += 1
    line = f"{tag} | {name} {detail}"
    OUT.append(line); print(line)


def section(t):
    OUT.append(f"\n## {t}"); print(f"\n## {t}")


def _clear_cache():
    C._store.clear()


# ---------------- 1. routing ----------------
section("1 routing / 确定性 fallback")
check("registry order 5m = mt5->local->yahoo", [s for s, _ in registry.history_sources("5m")] == ["mt5", "local_fxtm", "yahoo"])
_clear_cache()
r = DS.history("XAUUSD", "5m")
check("5m primary in (mt5,local_fxtm)", r.get("_selected_source") in ("mt5", "local_fxtm"), f"src={r.get('_selected_source')} n={r.get('n')}")
check("5m bars>100", r.get("n", 0) > 100, f"n={r.get('n')}")

# ---------------- 2. cache freshness ----------------
section("2 cache / freshness")
check("classify FRESH", C.classify(0.1, 1, 10) == C.FRESH)
check("classify STALE", C.classify(5, 1, 10) == C.STALE)
check("classify MISSING(expired)", C.classify(99, 1, 10) == C.MISSING)
check("classify MISSING(None)", C.classify(None, 1, 10) == C.MISSING)
_rec = C.put("t:key", {"a": 1}, "unit", fresh_h=1, stale_h=10)
check("cache get usable FRESH", C.get("t:key")["usable"] is True)
C.put("t:stale", {"a": 2}, "unit", observed_ts=time.time() - 5 * 3600, fresh_h=1, stale_h=10)
check("cache STALE_BUT_VALID usable", C.get("t:stale")["freshness"] == C.STALE and C.get("t:stale")["usable"])

# ---------------- 3. validation ----------------
section("3 validation (bad data -> INVALID)")
now = time.time()
good = [{"t": int(now) - 900, "o": 1, "h": 2, "l": 0.5, "c": 1.5, "v": 0},
        {"t": int(now) - 600, "o": 1.5, "h": 2, "l": 1, "c": 1.8, "v": 0}]
ok, reasons, clean = validate.validate_bars(good, "5m", 300, now_ts=now)
check("valid bars ok", ok and len(clean) == 2, str(reasons))
future = good + [{"t": int(now) + 300, "o": 1, "h": 1, "l": 1, "c": 1, "v": 0}]
ok2, r2, c2 = validate.validate_bars(future, "5m", 300, now_ts=now)
check("future bar dropped", any("future" in x for x in r2) and len(c2) == 2)
dup = [good[0], dict(good[0])]
ok3, r3, c3 = validate.validate_bars(dup, "5m", 300, now_ts=now)
check("duplicate dropped", any("non_monotonic" in x for x in r3))
nanb = [{"t": int(now) - 300, "o": float("nan"), "h": 1, "l": 1, "c": 1, "v": 0}]
ok4, r4, c4 = validate.validate_bars(nanb, "5m", 300, now_ts=now)
check("NaN -> invalid", (not ok4) and len(c4) == 0)
imp = [{"t": int(now) - 300, "o": -1, "h": 1, "l": -2, "c": 1, "v": 0}]
ok5, r5, c5 = validate.validate_bars(imp, "5m", 300, now_ts=now)
check("impossible price -> invalid", (not ok5))
qok, qr = validate.validate_quote({"price": 4300.0, "bid": 4299.9, "ask": 4300.1})
check("quote valid", qok)
qbad, qbr = validate.validate_quote({"price": None})
check("quote null -> invalid", not qbad)
qbad2, qbr2 = validate.validate_quote({"price": 4300.0, "bid": 4301.0, "ask": 4299.0})
check("quote bid>ask -> invalid", not qbad2)

# ---------------- 4. timeout / retry / backoff / cooldown ----------------
section("4 timeout / retry / backoff / cooldown / recovery")
net.reset_cooldowns()
t0 = time.time()
res = net.fetch("http://10.255.255.1:9/x", connect_timeout=1, read_timeout=1, retries=1, backoff=0.1, cooldown=30)
dt = time.time() - t0
check("bad host -> source_down", res["source_down"] is True and res["ok"] is False, f"err={res['error']}")
check("backoff waited (attempts=2)", res["attempts"] == 2, f"dt={dt:.2f}s")
host = net.host_of("http://10.255.255.1:9/x")
cool, rem = net.is_cooling(host)
check("host in cooldown", cool is True, f"rem={rem}s")
t1 = time.time()
res2 = net.fetch("http://10.255.255.1:9/x", connect_timeout=1, read_timeout=1, retries=1, cooldown=30)
check("cooldown short-circuits (no network)", res2["attempts"] == 0 and (time.time() - t1) < 0.3)
net.reset_cooldowns()
check("cooldown reset (recovery allowed)", net.is_cooling(host)[0] is False)

# ---------------- 5. PIT / no future leakage ----------------
section("5 PIT / no-future-leakage")
from data_sources import local_bars as LB
b = LB.build_bars("15m")
mono = all(b["bars"][i]["t"] > b["bars"][i - 1]["t"] for i in range(1, len(b["bars"])))
nowts = time.time()
no_future = all(x["t"] + 900 <= nowts for x in b["bars"])
check("local 15m monotonic", mono, f"n={b['n']}")
check("local 15m no future bar", no_future)
b2 = LB.build_bars("15m")
check("deterministic (2 runs identical)", [x["t"] for x in b["bars"]] == [x["t"] for x in b2["bars"]])

# ---------------- 6. failure injection ----------------
section("6 failure injection")
_clear_cache()
_oh, _ol, _om = AM.hist_yahoo, AM.hist_local, MT.history
AM.hist_yahoo = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("403 Forbidden (injected)"))
AM.hist_local = lambda *a, **k: {"tf": "5m", "bars": [], "n": 0, "error": "local_down(injected)"}
MT.history = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("mt5 down(injected)"))
try:
    rr = DS.history("XAUUSD", "5m")
    check("all sources down -> no crash, missing", rr.get("n") == 0 and rr.get("_freshness") == C.MISSING, f"src={rr.get('_selected_source')}")
except Exception as e:  # noqa: BLE001
    check("all sources down -> no crash", False, str(e))
finally:
    AM.hist_yahoo, AM.hist_local, MT.history = _oh, _ol, _om

# 缓存降级：先有值，再全挂 → 返回 cache(STALE)
_clear_cache()
C.put("hist:XAUUSD:5m", {"tf": "5m", "bars": [{"t": int(now) - 900, "o": 1, "h": 1, "l": 1, "c": 1, "v": 0}],
                          "n": 1, "last_bar_ts": int(now) - 900, "source": "unit"},
      "local_fxtm", observed_ts=now - 3 * 3600, fresh_h=0.5, stale_h=48)
AM.hist_yahoo = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("403"))
AM.hist_local = lambda *a, **k: {"tf": "5m", "bars": [], "n": 0, "error": "x"}
MT.history = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("mt5 down"))
try:
    rc = DS.history("XAUUSD", "5m")
    check("fallback -> cache STALE", rc.get("_fallback_level") == "cache" and rc.get("_freshness") == C.STALE)
finally:
    AM.hist_yahoo, AM.hist_local, MT.history = _oh, _ol, _om

# invalid JSON / bad source → macro raises → caller sees failure (no fabrication)
section("6b failure injection (macro)")
AMAC.MACRO_DEFS["cot:gold"] = ((lambda: (_ for _ in ()).throw(ValueError("invalid json"))), (24 * 8, 24 * 21), "cftc")
_clear_cache()
try:
    DS.macro("cot:gold"); check("macro all-down -> raises (no fabrication)", False)
except Exception:  # noqa: BLE001
    check("macro all-down -> raises (no fabrication)", True)
# 但若有 last_valid → 返回 STALE 值
C.put("macro:cot:gold", {"noncommercial_net": 123}, "cftc", observed_ts=now - 200 * 3600, fresh_h=24 * 8, stale_h=24 * 21)
try:
    v = DS.macro("cot:gold"); check("macro stale -> last_valid returned", isinstance(v, dict) and v.get("noncommercial_net") == 123)
except Exception as e:  # noqa: BLE001
    check("macro stale -> last_valid returned", False, str(e))

# ---------------- 7. failover drill ----------------
section("7 failover drill (all external + mt5 down)")
_clear_cache()
_backs = [AM.q_sina, AM.q_tencent, AM.q_eastmoney, AM.q_yahoo, AM.hist_yahoo, MT.quote, MT.history]
def mk(fn):
    return lambda *a, **k: (_ for _ in ()).throw(RuntimeError("source_down(injected)"))
try:
    AM.q_sina, AM.q_tencent, AM.q_eastmoney, AM.q_yahoo, AM.hist_yahoo, MT.quote, MT.history = [mk(x) for x in _backs]
    drill_hist = DS.history("XAUUSD", "15m")
    check("drill: technical still OK (local)", drill_hist.get("_selected_source") in ("local_fxtm", "cache(local_fxtm)") and drill_hist.get("n", 0) > 50)
    dq = DS.quote("gold_spot")
    check("drill: gold_spot local fallback", dq.get("_selected_source") in ("local_fxtm", "cache(local_fxtm)", None) or dq.get("price") is not None)
finally:
    AM.q_sina, AM.q_tencent, AM.q_eastmoney, AM.q_yahoo, AM.hist_yahoo, MT.quote, MT.history = _backs

# ---------------- 8. isolation ----------------
section("8 isolation (V1 / broker / ledger / replay)")
src = "\n".join(p.read_text(encoding="utf-8") for p in (ROOT / "data_sources").glob("*.py"))
check("no trader_v1 coupling", "trader_v1" not in src)
check("no broker executor coupling", ("order_send" not in src) and ("BrokerDemoExecutor" not in src) and ("place_market_order" not in src))
check("no ledger import", not re.search(r"^\s*import\s+ledger", src, re.M))
check("no replay import", not re.search(r"^\s*import\s+replay", src, re.M))

# ---------------- 9. health gate ----------------
section("9 data health gate")
hr = DS.health_report()
check("health has agent1/agent2/vars", all(k in hr for k in ("agent1", "agent2", "vars")))
check("health agent1 technical_status present", hr["agent1"]["technical_status"] in ("READY", "TECHNICAL_DATA_UNAVAILABLE"), hr["agent1"]["technical_status"])

# ---------------- result ----------------
tot = N["p"] + N["f"]
res_line = f"=== RESULT: {N['p']}/{tot} PASS ==="
OUT.append(res_line); print("\n" + res_line)
LOG.write_text("\n".join(OUT), encoding="utf-8")
sys.exit(1 if N["f"] else 0)
