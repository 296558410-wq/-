# -*- coding: utf-8 -*-
"""V2 sizing FLOOR-TO-STEP 验收测试（离线；不依赖网络；不改真实 state；不产生 broker 订单）。

覆盖:
  §五 边界: C01..C15 + min_lot 底线(小账户余额不足时不低于 0.01) + max_lot 硬拒绝(不得 clamp)
  §六 随机风险安全: >=1000 例, 所有 ACCEPT 必须 actual_risk <= target + tol
  §七 单调性: dist↑ => qty 非增, 无反向跳变
  §八 方向对称: LONG == SHORT sizing
日志: logs/test_sizing_floor.log
"""
import sys, math, random
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "execution"))
import paper_executor as PE  # noqa: E402

TMP = HERE / "_tmp"; TMP.mkdir(exist_ok=True)
PE.ACCOUNT_P = TMP / "sizing_floor_account.json"
PE.EXECUTIONS_P = TMP / "sizing_floor_execs.jsonl"
LOGS = ROOT / "logs"; LOGS.mkdir(exist_ok=True)
LOG = LOGS / "test_sizing_floor.log"
_res = []
TOL = 1e-6

BASE = {"execution": {"execution_mode": "PAPER", "live_trading": False, "broker_demo_enabled": False,
                      "cost_model": {"spread_bps_typical": 0.35, "slippage_bps": 0.30, "latency_ms": 250,
                                     "commission_per_lot_usd": 0.0},
                      "contract": {"min_lot": 0.01, "max_lot": 0.05, "contract_size_oz": 100,
                                   "price_dp": 2, "lot_dp": 2, "leverage": 500},
                      "risk": {"per_trade_pct": 1.0, "single_position": True, "max_notional_usd": 25000}},
        "account": {"initial_balance": 10000.0}}


def log(s):
    line = f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] {s}"
    print(line)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def check(n, c, d=""):
    _res.append(bool(c)); log(f"{'PASS' if c else 'FAIL'} | {n} {d}")


def cfg(equity=10000.0, max_notional=25000):
    c = deepcopy(BASE)
    c["account"]["initial_balance"] = equity
    c["execution"]["risk"]["max_notional_usd"] = max_notional
    return c


def ex(equity=10000.0, max_notional=25000):
    pe = PE.PaperExecutor(cfg(equity, max_notional))
    pe.acc = pe._fresh()
    pe.acc["balance"] = equity; pe.acc["equity"] = equity
    pe._save = lambda: None; pe._record = lambda r: None   # 不落盘
    return pe


STEP = 0.01
MIN_LOT, MAX_LOT = 0.01, 0.05


def floor_lot(raw):
    return round(math.floor(raw / STEP + 1e-9) * STEP, 2)


def raw_of(dist, equity=10000.0, per=1.0):
    return equity * per / 100.0 / (dist * 100)


def run_open(dist, equity=10000.0, direction="SHORT", mid=4400.0, qty=None, max_notional=25000):
    pe = ex(equity, max_notional)
    sl = mid + dist if direction == "SHORT" else mid - dist
    r = pe.open(direction, mid, sl=sl, tp=mid - 5 * dist if direction == "SHORT" else mid + 5 * dist,
                plan_id="SZ", spread_bps=0, slippage_bps=0, qty_lots=qty)
    q = r["position"]["qty_lots"] if r.get("ok") else 0.0
    risk = q * dist * 100.0
    return r, q, risk


def expected(dist, equity=10000.0, qty=None):
    raw = qty if qty is not None else raw_of(dist, equity)
    lot = floor_lot(raw)
    if lot < MIN_LOT:
        lot = MIN_LOT          # 平台最小手底线（Module 6.1）
    if lot > MAX_LOT:
        return lot, "MAX"
    return lot, "OK"


def main():
    open(LOG, "a", encoding="utf-8").write("\n" + "=" * 60 + "\n")
    log("=== V2 sizing FLOOR-TO-STEP acceptance tests ===")
    mid = 4400.0

    # ---------- §五 边界用例 ----------
    cases = [
        ("C01 dist=20.0 raw=0.05 exact", 20.0, 10000.0, None, 0.05, "OK"),
        ("C02 dist=17.74 (real signal)", 17.74, 10000.0, None, 0.05, "OK"),
        ("C03 dist=17.73 (real signal)", 17.73, 10000.0, None, 0.05, "OK"),
        ("C04 raw=0.049 -> 0.04", 20.408163265306122, 10000.0, None, 0.04, "OK"),
        ("C08 raw=0.045 -> 0.04", 22.22222222222222, 10000.0, None, 0.04, "OK"),
        ("C11 raw=0.025 -> 0.02", 40.0, 10000.0, None, 0.02, "OK"),
        ("C12 raw=0.015 -> 0.01", 66.66666666666667, 10000.0, None, 0.01, "OK"),
        ("C13 dist=100 raw=0.01", 100.0, 10000.0, None, 0.01, "OK"),
        ("C14 dist=101 -> min_lot 0.01", 101.0, 10000.0, None, 0.01, "OK"),
        ("C15 dist=250 -> min_lot 0.01", 250.0, 10000.0, None, 0.01, "OK"),
        ("MAXLOT dist=16 raw=0.0625 -> 0.06 REJECT", 16.0, 10000.0, None, 0.06, "MAX"),
        ("PASSTHRU qty=0.06 -> REJECT", 20.0, 10000.0, 0.06, 0.06, "MAX"),
        ("PASSTHRU qty=0.05 -> OK", 20.0, 10000.0, 0.05, 0.05, "OK"),
    ]
    for name, dist, eq, qty, exp_lot, exp_kind in cases:
        r, q, risk = run_open(dist, eq, qty=qty)
        if exp_kind == "OK":
            allowed = max(eq * 0.01, MIN_LOT * dist * 100.0)
            ok = (r.get("ok") and abs(q - exp_lot) < 1e-9 and abs(raw_of(dist, eq, 1.0) if qty is None else qty) >= 0
                  and risk <= allowed + TOL)
            check(f"§五 {name}", ok and q == exp_lot, f"qty={q} exp={exp_lot} risk={risk:.2f}/allowed={allowed:.1f} ok={r.get('ok')}")
        else:
            kind_ok = (r.get("failure_code") == "RISK_LIMIT" and (exp_kind == "MAX" or exp_kind == "MIN"))
            check(f"§五 {name}", (not r.get("ok")) and kind_ok, f"code={r.get('failure_code')} reason={r.get('reason')}")

    # 关键断言: max_lot 不得 clamp
    r, q, risk = run_open(16.0)
    check("§五 max_lot 是硬拒绝(不 clamp 到 0.05)", (not r.get("ok")) and r.get("failure_code") == "RISK_LIMIT",
          f"code={r.get('failure_code')} reason={r.get('reason')}")

    # ---------- §六 随机风险安全 (>=1000) ----------
    random.seed(20260912)
    n_accept = n_reject = n_over = 0
    worst = 0.0
    N = 1200
    for i in range(N):
        eq = random.uniform(500.0, 200000.0)
        dist = random.choice([random.uniform(0.5, 3.0), random.uniform(3.0, 30.0),
                              random.uniform(30.0, 120.0), random.uniform(120.0, 600.0)])
        direction = random.choice(["LONG", "SHORT"])
        mid = random.uniform(3800.0, 4800.0)
        # 偶发 step 边界
        if i % 7 == 0:
            dist = round(random.choice([STEP * k for k in range(1, 60)]), 4)
        r, q, risk = run_open(dist, eq, direction=direction, mid=mid)
        target = eq * 0.01
        allowed = max(target, MIN_LOT * dist * 100.0)   # 平台最小手底线
        if r.get("ok"):
            n_accept += 1
            worst = max(worst, risk - allowed)
            if risk > allowed + TOL or risk > eq + TOL:
                n_over += 1
                check("§六 RANDOM RISK VIOLATION", False, f"i={i} eq={eq:.1f} dist={dist:.4f} q={q} risk={risk:.4f} allowed={allowed:.4f}")
                break
            exp_q = max(floor_lot(raw_of(dist, eq)), MIN_LOT)
            if abs(q - exp_q) > 1e-9:
                n_over += 1
                check("§六 RANDOM FLOOR MISMATCH", False, f"i={i} q={q} exp={exp_q}")
                break
            if not (MIN_LOT - 1e-9 <= q <= MAX_LOT + 1e-9):
                n_over += 1
                check("§六 RANDOM LOT BAND VIOLATION", False, f"i={i} q={q}")
                break
        else:
            n_reject += 1
    check("§六 1000+ 随机: 所有 ACCEPT 满足 actual_risk <= max(target, min_lot_risk) 且 risk<=equity", n_over == 0 and n_accept + n_reject == N,
          f"N={N} accept={n_accept} reject={n_reject} worst_excess={worst:.2e}")

    # 反向证明: 旧 round-nearest 会违反 (数学证)
    viol = sum(1 for k in range(1, 200)
               if round(raw_of(STEP * k * 100, 10000.0) + 1e-9, 2) * (STEP * k * 100) * 100 > 100 + TOL)
    check("§六 对照: round-nearest 存在超风险点(说明本次修复必要)", viol > 0, f"nearest_over_risk_points={viol}")

    # ---------- §九 小账户底线: 风险预算 < min_lot 风险 → 仍按 0.01 交易 ----------
    for eq in (200.0, 150.0, 300.0):
        for dist in (10.0, 17.74, 20.0, 25.0):
            r, q, risk = run_open(dist, eq)
            allowed = max(eq * 0.01, MIN_LOT * dist * 100.0)
            ok = r.get("ok") and abs(q - MIN_LOT) < 1e-9 and risk <= allowed + TOL and risk <= eq + TOL
            check(f"§九 小账户 ${eq:.0f} dist={dist} -> min_lot 0.01", ok,
                  f"ok={r.get('ok')} q={q} risk={risk:.2f} allowed={allowed:.2f}")

    # ---------- §七 单调性 ----------
    pe_mono = ex(10000.0)
    mono_ok = True; bad = None; prev = None
    for dist_i in [x / 100.0 for x in range(100, 40001)]:   # 1.00 .. 400.00 step 0.01
        q = pe_mono.size_position_raw(4400.0, 4400.0 + dist_i)
        if prev is not None and q > prev + 1e-12:
            mono_ok = False; bad = (dist_i, prev, q); break
        prev = q
    check("§七 单调性 dist↑ => qty 非增 (1..400 step .01)", mono_ok, f"bad={bad}")
    for w in [(17.0, 25.0), (28.0, 35.0), (40.0, 55.0), (65.0, 105.0)]:
        wok = True; pw = None
        d = w[0]
        while d <= w[1] + 1e-9:
            q = pe_mono.size_position_raw(4400.0, 4400.0 + d)
            if pw is not None and q > pw + 1e-12:
                wok = False; break
            pw = q; d = round(d + 0.005, 4)
        check(f"§七 单调窗口 {w}", wok)

    # ---------- §八 方向对称 ----------
    sym_ok = True; det = ""
    pe_sym = ex(10000.0)
    for dist in [5.0, 12.3, 17.74, 20.0, 20.5, 25.0, 33.33, 50.0, 66.67, 100.0, 101.0, 250.0]:
        ql = pe_sym.size_position_raw(4400.0, 4400.0 - dist)
        qs = pe_sym.size_position_raw(4400.0, 4400.0 + dist)
        if abs(ql - qs) > 1e-12:
            sym_ok = False; det = f"dist={dist} L={ql} S={qs}"; break
    check("§八 LONG sizing == SHORT sizing", sym_ok, det)

    log(f"=== RESULT: {sum(_res)}/{len(_res)} PASS ===")
    return 0 if all(_res) else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
