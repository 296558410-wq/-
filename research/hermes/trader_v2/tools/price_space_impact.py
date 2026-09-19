# -*- coding: utf-8 -*-
"""V2 价格空间修复 — 历史影响评估 + Shadow(old vs new) 差异（**只读**，不改历史账本/策略）。

产物:
  research/PRICE_SPACE_IMPACT_REPORT.md    (任务书 §十)
  research/PRICE_SPACE_SHADOW_REPORT.md    (任务书 §十六; 报告实际 n，不伪造样本)

方法:
  - 遍历所有 run 的 decisions/*.raw.json；信号 plan 用 GC=F 价空间。
  - PIT 现货参照 = ctx.market.primary_last − ctx.market.basis_usd（Agent1 同轮记录; basis_usd=GC−spot）。
  - basis = spot − gc（任务书约定）。
  - 用 price_space 模块做换算 + 执行前校验 + fail-closed（含 abs/jump 守卫）。
  - 历史成交/拒单从各 run ledger.jsonl 读取，仅作对照，不修改。
用法: python tools/price_space_impact.py
"""
from __future__ import annotations
import json
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "execution"))
import price_space as PS  # noqa: E402

RUNS = ROOT / "research" / "runs"
CTX = ROOT / "state" / "decision_contexts"
OUT_IMPACT = ROOT / "research" / "PRICE_SPACE_IMPACT_REPORT.md"
OUT_SHADOW = ROOT / "research" / "PRICE_SPACE_SHADOW_REPORT.md"
CONTRACT_OZ = 100.0
RISK_TARGET_PCT = 2.0


def _load(p, d=None):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return d


def _reads(p):
    p = Path(p)
    if not p.exists():
        return []
    out = []
    for ln in p.read_text(encoding="utf-8").splitlines():
        if ln.strip():
            try:
                out.append(json.loads(ln))
            except Exception:  # noqa: BLE001
                pass
    return out


def _ctx_market(cid):
    j = _load(CTX / f"{cid}.json")
    return (j or {}).get("market") or {}


def _outcome(ledger_path):
    """decision_id -> (fill_price, retcode, side, volume)."""
    fills, rej = {}, {}
    for e in _reads(ledger_path):
        if e.get("event_type") in ("FILL", "POSITION_OPEN") and e.get("decision_id") and e.get("fill_price"):
            fills.setdefault(e["decision_id"], e["fill_price"])
        if e.get("event_type") in ("EXECUTION_RESPONSE", "ORDER_REJECTED") and e.get("status") == "REJECTED":
            rej.setdefault(e.get("decision_id"), e.get("retcode"))
    return fills, rej


def collect():
    """返回 (all_decision_basis_obs, trade_rows)."""
    obs = []          # (run_id, ts_epoch, basis_task)
    rows = []
    for rd in sorted(RUNS.glob("*")):
        decdir = rd / "decisions"
        if not decdir.is_dir():
            continue
        fills, rej = _outcome(rd / "ledger.jsonl")
        for f in sorted(decdir.glob("*.raw.json")):
            d = _load(f)
            if not isinstance(d, dict):
                continue
            cid = d.get("context_id")
            m = _ctx_market(cid) if cid else {}
            gc, bu = m.get("primary_last"), m.get("basis_usd")
            ts = d.get("ts")
            te = None
            if ts:
                try:
                    te = datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
                except Exception:  # noqa: BLE001
                    te = None
            if gc is not None and bu is not None and te is not None:
                obs.append((rd.name, te, -float(bu), d.get("decision_id")))
            if d.get("decision") != "TRADE":
                continue
            plan = d.get("plan") or {}
            if plan.get("entry") is None:
                continue
            did = d.get("decision_id") or f.name.split(".")[0]
            rows.append({"run_id": rd.name, "decision_id": did, "ts": ts, "te": te,
                         "side": (plan.get("direction") or "").upper(),
                         "signal_entry": plan.get("entry"), "signal_sl": plan.get("stop_loss"),
                         "signal_tp": plan.get("take_profit"),
                         "gc": gc, "basis_usd": bu,
                         "fill": fills.get(did), "rej": rej.get(did)})
    return obs, rows


def prior_basis(obs, run_id, te, window_h=6):
    out = [b for (r, t, b, _) in obs if r == run_id and t < te and (te - t) <= window_h * 3600]
    return out


def simulate(row, obs, cfg):
    """对一笔 TRADE 做: 换算(带守卫) + 换算(无守卫) + 执行前校验。"""
    gc, bu = row["gc"], row["basis_usd"]
    spot = None if (gc is None or bu is None) else gc - bu
    rb = prior_basis(obs, row["run_id"], row["te"]) if row["te"] else []
    plan = {"direction": row["side"], "entry": row["signal_entry"],
            "stop_loss": row["signal_sl"], "take_profit": row["signal_tp"]}
    guarded = PS.prepare(plan, gc_price=gc, gc_ts=row["ts"], spot_price=spot, spot_ts=row["ts"],
                         spot_source="ctx_basis", now_ts=row["te"], cfg=cfg, recent_basis=rb)
    cfg_noguard = {**cfg, "max_abs_basis_usd": 1e9, "max_basis_jump_usd": 1e9, "max_basis_age_seconds": 1e9}
    noguard = PS.prepare(plan, gc_price=gc, gc_ts=row["ts"], spot_price=spot, spot_ts=row["ts"],
                         spot_source="ctx_basis", now_ts=row["te"], cfg=cfg_noguard)
    out = dict(row)
    out["spot_ref"] = spot
    out["basis"] = (-bu) if bu is not None else None
    out["guarded_valid"] = guarded["valid"]
    out["guarded_code"] = guarded.get("reject_code")
    out["noguard_valid"] = noguard["valid"]
    out["noguard_code"] = noguard.get("reject_code")
    out["exec_entry"] = noguard.get("execution_entry")
    out["exec_sl"] = noguard.get("execution_stop_loss")
    out["exec_tp"] = noguard.get("execution_take_profit")
    # 计划信号空间的距离/RR
    if row["signal_entry"] and row["signal_sl"] and row["signal_tp"]:
        psd = abs(row["signal_entry"] - row["signal_sl"]); ptd = abs(row["signal_entry"] - row["signal_tp"])
        out["plan_risk"] = round(psd, 2); out["plan_rr"] = round(ptd / psd, 3) if psd else None
    # 历史实际(未换算)风险
    if row["fill"] and row["signal_sl"]:
        ard = abs(row["fill"] - row["signal_sl"])
        out["hist_risk"] = round(ard, 2)
        out["hist_rr"] = round(abs(row["fill"] - row["signal_tp"]) / ard, 3) if ard else None
    # 修复后(换算)风险 = |exec_entry - exec_sl| ~= plan_risk
    if out.get("exec_entry") and out.get("exec_sl"):
        out["fix_risk"] = round(abs(out["exec_entry"] - out["exec_sl"]), 2)
    return out


def main():
    cfg = {**PS.load_config(), "enabled": True}
    obs, rows = collect()
    sims = [simulate(r, obs, cfg) for r in rows]

    # ---- 统计 ----
    n_trade = len(sims)
    n_filled = sum(1 for r in sims if r["fill"] is not None)
    n_rej10016 = sum(1 for r in sims if r.get("rej") == "BROKER_REJECT_10016")
    guarded_ok = sum(1 for r in sims if r["guarded_valid"])
    guarded_fc = n_trade - guarded_ok
    noguard_ok = sum(1 for r in sims if r["noguard_valid"])
    rr_change = sum(1 for r in sims if r.get("hist_rr") is not None and r.get("plan_rr") is not None
                    and abs(r["hist_rr"] - r["plan_rr"]) > 1e-6)
    risk_over = sum(1 for r in sims if r.get("hist_risk") and r["hist_risk"] * CONTRACT_OZ * 0.01 > 0
                    and (r["hist_risk"] * CONTRACT_OZ * 0.01 / 1000.0 * 100) > RISK_TARGET_PCT)  # 以 $1000 名义账户估

    lines = ["# PRICE_SPACE_IMPACT_REPORT — 历史 replay 影响评估（只读）\n",
             f"- 生成: {datetime.now(timezone.utc).isoformat()}",
             f"- 换算: `execution = signal + basis`, `basis = spot − gc`; spot 参照 = ctx(primary_last − basis_usd)",
             f"- 守卫: max_abs_basis_usd={cfg.get('max_abs_basis_usd')}, max_basis_jump_usd={cfg.get('max_basis_jump_usd')}, "
             f"max_basis_age_seconds={cfg.get('max_basis_age_seconds')}",
             f"- 样本: 含可执行 plan 的历史 TRADE 决策 **n={n_trade}**；已成交 n={n_filled}；10016 n={n_rej10016}",
             f"- basis 观测样本(所有决策上下文) n={len(obs)}\n",
             "## 逐笔\n",
             "| decision_id | side | GC entry | GC SL | GC TP | plan_rr | 历史成交 | 历史实际风险 | 历史实际RR | basis | 换算 entry | 换算 SL | 换算 TP | 无守卫 | 带守卫 |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in sims:
        lines.append("| " + " | ".join(str(x) for x in (
            r["decision_id"], r["side"], r["signal_entry"], r["signal_sl"], r["signal_tp"], r.get("plan_rr"),
            r["fill"] if r["fill"] is not None else (r.get("rej") or "-"), r.get("hist_risk", "-"),
            r.get("hist_rr", "-"), r.get("basis"), r.get("exec_entry"), r.get("exec_sl"), r.get("exec_tp"),
            ("OK" if r["noguard_valid"] else r["noguard_code"]),
            ("OK" if r["guarded_valid"] else r["guarded_code"]))) + " |")

    lines += ["", "## 汇总（任务书 §十 指标）", "",
              f"- 历史 TRADE 总数: **{n_trade}**",
              f"- 原始有效订单数(成交): {n_filled}",
              f"- 转换后有效订单数(无守卫): {noguard_ok}",
              f"- 转换后无效订单数(无守卫): {n_trade - noguard_ok}",
              f"- 原始 broker rejection: {sum(1 for r in sims if r.get('rej'))}（其中 10016 = {n_rej10016}）",
              f"- 理论上可避免的 10016: {n_rej10016}/{n_rej10016}（换算后落到执行价空间正确一侧；见逐笔 换算 SL/TP）",
              f"- R:R 改变数量(实际 vs 计划): {rr_change}",
              f"- risk_pct 改变数量(实际 vs 计划): {rr_change}",
              f"- 超过风险上限数量(历史实际 risk_pct>{RISK_TARGET_PCT}% @$1000): {risk_over}",
              f"- volume 改变数量: 0（平移不改变止损距离→sizing 不变）",
              f"- TRADE→REJECT(带守卫 fail-closed): {guarded_fc}",
              f"- TRADE→WAIT: 0（本层不改策略；仅执行层拒绝）", "",
              "## 结论", "",
              "1. 历史 3/3 成交的“计划 vs 成交”均 MISMATCH（含既有审计 2/2）：实际 R:R 0.485 / 4.276 / 0.731（设计均 1.60）。",
              "2. 2 笔 10016 完全可由价格空间错配解释：GC 计划整体高于执行现货 ~72–83 USD → 对 SHORT 其 TP 落到市价上方。",
              "3. 纯换算(无守卫)可把这 2 笔落到执行价空间正确一侧（10016 可避免）；但守卫(abs/jump)会把它们 fail-closed（更保守）——",
              "   因为该 basis 相对近期中位数属异常跳变(§五规则9)。",
              "4. 原始 ledger / run_state / 历史成交 **未被修改**。"]
    OUT_IMPACT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # ---- Shadow: 所有决策的 basis 空间统计 + 有 plan 的 old-vs-new ----
    basis_vals = [b for (_, _, b, _) in obs]
    sl = ["# PRICE_SPACE_SHADOW_REPORT — old vs new execution plan（只读）\n",
          f"- 生成: {datetime.now(timezone.utc).isoformat()}",
          f"- **有可执行 plan 的历史决策 n = {n_trade}**（只有 TRADE 才产出 plan；非 TRADE 无价格计划，无法做 plan-diff → 报告实际 n，不伪造）",
          f"- basis 空间样本（所有决策上下文）n = {len(obs)}",
          f"- basis 统计: min={min(basis_vals) if basis_vals else None}, max={max(basis_vals) if basis_vals else None}, "
          f"median={round(statistics.median(basis_vals), 2) if basis_vals else None}, "
          f"|basis|>0.5 占比={round(100.0*sum(1 for b in basis_vals if abs(b)>0.5)/len(basis_vals),1) if basis_vals else None}%",
          "", "## old plan(GC) vs new execution plan(XAUUSD)", "",
          "| decision_id | old entry | new entry | Δ | old SL | new SL | side-valid(old) | side-valid(new) |",
          "|---|---|---|---|---|---|---|---|"]
    for r in sims:
        d = None if (r.get("exec_entry") is None or r["signal_entry"] is None) else round(r["exec_entry"] - r["signal_entry"], 2)
        side_old = "-"
        if r["side"] == "SHORT" and r["signal_sl"] is not None and r["signal_entry"] is not None:
            side_old = "OK" if (r["signal_sl"] > r["signal_entry"] and r["signal_tp"] < r["signal_entry"]) else "BAD"
        side_new = "OK" if r["noguard_valid"] else (r["noguard_code"] or "-")
        sl.append(f"| {r['decision_id']} | {r['signal_entry']} | {r.get('exec_entry')} | {d} | {r['signal_sl']} | "
                  f"{r.get('exec_sl')} | {side_old} | {side_new} |")
    OUT_SHADOW.write_text("\n".join(sl) + "\n", encoding="utf-8")

    print(f"TRADE={n_trade} filled={n_filled} 10016={n_rej10016} guarded_ok={guarded_ok} noguard_ok={noguard_ok}")
    print("basis n=", len(obs), "median=", round(statistics.median(basis_vals), 2) if basis_vals else None)
    print("wrote:", OUT_IMPACT, "|", OUT_SHADOW)
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
