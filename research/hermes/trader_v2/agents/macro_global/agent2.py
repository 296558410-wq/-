# -*- coding: utf-8 -*-
"""V2 Agent2 —— 宏观 + 全球地缘 + 黄金资金流情报 Agent（确定性快照, 无 LLM）。

产出 state/agent2_latest.json + 版本化 snapshot（任务书 §9 结构）。
只提供: 证据/状态/方向性压力/事件/冲突/不确定性。**绝不输出 LONG/SHORT/BUY/SELL。**
每条信息带 point-in-time 元数据; 拿不到的字段=null + data_gap, 不臆造。
用法: python agent2.py [--cycle <label>]
"""
from __future__ import annotations
import argparse, json, sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import sources as S  # noqa: E402
import evidence as EV  # noqa: E402
import release_registry as RR  # noqa: E402

STATE = ROOT / "state"
SNAP = STATE / "snapshots"
AGENT_VERSION = "agent2/0.2.0-pit"
CN_GOLD_ETFS = {"518880": "1.518880", "159934": "0.159934"}  # 华安/易方达 黄金ETF
BLS_SERIES = {"CUUR0000SA0": "CPI-U 全部商品(同比基)",
              "CUSR0000SA0": "CPI-U 核心(SA)",
              "LNS14000000": "U3 失业率"}
FRESHNESS_RULES = [(900, "fresh"), (86400, "stale"), (10 ** 9, "expired")]


def freshness(published_at, now_ms=None):
    """返回 (label, age_seconds)。发布时间未知 → unknown。"""
    import time as _t
    if not published_at:
        return "unknown", None
    try:
        if isinstance(published_at, (int, float)):
            pa = datetime.fromtimestamp(published_at, timezone.utc)
        else:
            pa = datetime.fromisoformat(str(published_at).replace("Z", "+00:00"))
    except Exception:  # noqa: BLE001
        return "unknown", None
    age = (datetime.now(timezone.utc) - pa).total_seconds()
    for thr, label in FRESHNESS_RULES:
        if age < thr:
            return label, int(age)
    return "expired", int(age)


def _now():
    return datetime.now(timezone.utc).isoformat()


def _compact(iso):
    return iso.replace(":", "").replace("-", "").split(".")[0]


def _safe(fn, default=None):
    try:
        r = fn()
    except Exception as e:  # noqa: BLE001
        return default if default is not None else {"error": f"{type(e).__name__}:{e}", "__failed__": True}
    if r is None:  # FIX(2026-09-15): 源返回 None(如 router 空值) → 视为失败哨兵, 避免下游 .get 崩溃
        return default if default is not None else {"error": "NoneType:empty", "__failed__": True}
    return r


def _as_list(x):
    """Coerce 到 list：list 原样，其余（None / _safe 的 dict 哨兵）→ []。防 list+dict 拼接崩溃。"""
    return x if isinstance(x, list) else []


def core_macro_status(x):
    """核心宏观字段状态：OK / SOURCE_ERROR / DATA_MISSING（禁止把缺失当作正常）。"""
    if not isinstance(x, dict) or x.get("__failed__"):
        return "SOURCE_ERROR"
    if x.get("last") is None or x.get("change_pct") is None:
        return "DATA_MISSING"
    return "OK"


def macro_state(core_degraded, score, conflicts):
    """返回 (macro_status, gold_macro_state)。
    core_degraded → 明确 DEGRADED（绝不当作 NEUTRAL）；conflicts 时禁止方向升级（反降级必须有效）。"""
    if core_degraded:
        return "DEGRADED", "DEGRADED"
    if abs(score) < 0.15:
        st = "UNCERTAIN" if conflicts else "NEUTRAL"
    elif score > 0:
        st = "BULLISH" if (score > 0.6 and not conflicts) else ("BULLISH" if (score > 0.3 and not conflicts) else "NEUTRAL")
    else:
        st = "BEARISH" if (score < -0.6 and not conflicts) else ("BEARISH" if (score < -0.3 and not conflicts) else "NEUTRAL")
    return "OK", st


# ---- P1-A: Macro Data Contract helpers（纯函数, 便于单测）----
def macro_field_status(value):
    """AVAILABLE / MISSING / ERROR（宏观字段完整性）。"""
    if value is None:
        return "MISSING"
    if isinstance(value, dict) and value.get("__failed__"):
        return "ERROR"
    return "AVAILABLE"


def news_source_status(raw, error=None, last_data_ts=None):
    """新闻源状态: OK / NEWS_SOURCE_ERROR / EMPTY（失败不得静默为空）。"""
    if error:
        return {"source_status": "NEWS_SOURCE_ERROR", "error_type": str(error)[:120], "last_data_ts": last_data_ts}
    if not raw:
        return {"source_status": "EMPTY", "error_type": None, "last_data_ts": last_data_ts}
    return {"source_status": "OK", "error_type": None, "last_data_ts": last_data_ts}


def macro_completeness(fields):
    """fields: {name: label} → 只保留显式标签（AVAILABLE/MISSING/STALE/ERROR/PIT_RISK）。"""
    return dict(fields)


TRADE_CRITICAL_MACRO = ("DXY", "UST10Y", "VIX")   # Hermes gold_macro_state 依赖
CONTEXT_ONLY_MACRO = ("TIP", "BLS", "COT", "ETF_FLOW_CN", "NEWS", "GEOPOLITICS")


def collect():
    dxy = _safe(lambda: S.macro_kv("dxy"))          # 国内: sina DINIW
    tnx = _safe(lambda: S.macro_kv("ust10y"))       # 国内: tencent usUST(7-10Y ETF, 反向代理)
    vix = _safe(lambda: S.macro_kv("vix"))          # 国内: sina znb_VIX
    tip = _safe(lambda: S.macro_kv("tip"))          # 国内: tencent usTIP(实际利率代理)
    gld = _safe(lambda: S.macro_kv("gld"))          # 国内: tencent usGLD
    cot = {"error": "no_domestic_source", "__failed__": True}   # COT: 无国内源(CFTC 403)
    em_flows = {k: _safe(lambda sec=v: S.em_flow(sec)) for k, v in CN_GOLD_ETFS.items()}
    # FIX(2026-09-15): _safe() 默认回退是 dict 哨兵 {"__failed__":True}；若某一新闻源失败，
    # 旧写法 `(_safe(...) or []) + (...)` 会做 list + dict → "can only concatenate list (not dict) to list"
    # → 整轮 agent2 崩溃（历史上 5 个窗口复现）。改为 default=[] 且只保留 list 内 dict 元素。
    def _src(fn):
        try:
            return fn(), None
        except Exception as e:  # noqa: BLE001
            return None, f"{type(e).__name__}:{e}"
    news_w, err_w = _src(lambda: S.news_wallstcn(40))
    news_c, err_c = _src(lambda: S.news_cnbc_rss(40))
    news = _as_list(news_w) + _as_list(news_c)
    news = [n for n in news if isinstance(n, dict) and not n.get("__failed__")]
    news_status = {"wallstcn": news_source_status(news_w, err_w), "cnbc": news_source_status(news_c, err_c)}
    bls = {"error": "no_domestic_source", "__failed__": True}   # BLS: 无国内源(api.bls.gov 403)
    return {"dxy": dxy, "tnx": tnx, "vix": vix, "tip": tip, "gld": gld, "cot": cot,
            "em_flows": em_flows, "news": news, "news_status": news_status, "bls": bls}


def _pct(x):
    return None if not isinstance(x, dict) or x.get("change_pct") is None else x["change_pct"]


def _dir_from_pct(p, up_is, thr=0.15):
    if p is None: return "unknown"
    if p > thr: return up_is[0]
    if p < -thr: return up_is[1]
    return "flat"


def build(cycle=None):
    cycle = cycle or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    d = collect()
    dxy, tnx, vix, tip, gld, cot, em = d["dxy"], d["tnx"], d["vix"], d["tip"], d["gld"], d["cot"], d["em_flows"]
    news = d["news"]
    news_status = d.get("news_status", {})
    gaps = []

    # ---- 宏观: 美元/利率/实际利率/央行/经济数据 ----
    macro = {
        "usd": {"value": dxy.get("last"), "change_pct_1d": _pct(dxy), "source": "sina:DINIW(国内)",
                "data_ts": dxy.get("data_ts"), "retrieved_at": dxy.get("retrieved_at")},
        "rates": {"ust10y_pct": tnx.get("last"), "change_1d": tnx.get("change"),
                  "change_pct_1d": _pct(tnx), "source": "tencent:usUST(7-10Y ETF代理,反向; 非^TNX)",
                  "proxy": True, "note": "国内无 ^TNX 直连 → 用 7-10Y 国债ETF 价格代理; change_pct 已取反(价格↑=收益率↓)",
                  "data_ts": tnx.get("data_ts")},
        "real_rates": {"proxy": "TIP(TIPS ETF)", "value": tip.get("last"),
                       "change_pct_1d": _pct(tip), "source": "tencent:usTIP(国内)",
                       "note": "实际利率代理(非 TIPS 收益率本身); 真值需 FRED/官方, 已列 data_gap"},
        "central_banks": {"fed": None, "ecb": None, "boj": None, "pboc": None,
                          "note": "政策利率/决议无免 Key 直连 API → placeholder; 以新闻事件代替"},
        "economic_data": [],  # 由新闻事件抽取(见下)
    }
    if tip.get("__failed__"): gaps.append("real_rates:TIP_fetch_failed")
    gaps.append("central_bank_policy_rates:no_direct_api(placeholder)")

    # ---- 地缘/宏观事件(路由进 Evidence Registry; 每条可回溯原始内容) ----
    geo_events, econ_events, cb_events, ev_refs = [], [], [], []
    for n in news:
        txt = (n.get("title", "") + " " + n.get("content", ""))
        tags = S.classify(txt)
        rec = _safe(lambda nn=n: EV.record_news(nn))
        if not isinstance(rec, dict) or rec.get("__failed__"):
            rec = {}
        fr, age = freshness(n.get("published_at") or n.get("published_at_raw"))
        eid = rec.get("evidence_id")
        if eid: ev_refs.append(eid)
        ev = {"title": n.get("title"),
              "published_at": n.get("published_at") or n.get("published_at_raw"),
              "source": n.get("source"), "source_url": n.get("source_url"),
              "credibility": "REPORTED", "tags": tags,
              "evidence_id": eid, "content_sha256": rec.get("content_sha256"),
              "version": rec.get("version"), "first_seen_at": rec.get("retrieved_at"),
              "freshness": fr, "age_seconds": age,
              "impact_direction": None, "priced_in": None}
        if "geopolitics" in tags: geo_events.append(ev)
        if "central_bank" in tags: cb_events.append(ev)
        if "economic_data" in tags: econ_events.append(ev)
    for e in econ_events:  # 财经日历诚实处理: 无官方 release timestamp
        e["release_timestamp"] = None
        e["release_timestamp_source"] = "unavailable"
        e["point_in_time_confidence"] = "low"
    macro["economic_data"] = econ_events[:12]
    macro["central_banks"]["recent_headlines"] = cb_events[:8]
    if not econ_events: gaps.append("economic_data:no_items_this_pull")
    for _sn, _st in news_status.items():  # P1-A: 新闻源失败必须可见（不得静默为空）
        if _st.get("source_status") != "OK":
            gaps.append(f"news_{_sn}:{_st.get('source_status')}")

    # ---- 官方结构化宏观: BLS(免Key) + 观察式修订登记 ----
    bls = d.get("bls")
    releases = []
    if isinstance(bls, list) and bls:
        for item in bls:
            rr = _safe(lambda it=item: RR.observe(
                release_id=it["series_id"], release_period=it["period"], value=it["value"],
                source=it["source"], source_url=it["source_url"],
                release_timestamp=it.get("release_timestamp"),
                release_timestamp_source=it.get("release_timestamp_source")))
            if isinstance(rr, dict):
                releases.append({"series_id": item["series_id"], "name": BLS_SERIES.get(item["series_id"]),
                                 "period": item["period"], "value": item["value"],
                                 "first_published_value": rr.get("first_published_value"),
                                 "latest_known_value": rr.get("latest_known_value"),
                                 "revision_number": rr.get("revision_number"),
                                 "release_timestamp": None, "release_timestamp_source": "unavailable",
                                 "point_in_time_confidence": "low"})
                _safe(lambda it=item: EV.record_data("macro", it["source"], it["source_url"],
                     {"series_id": it["series_id"], "period": it["period"], "value": it["value"]},
                     published_at=None, extra={"release_id": it["series_id"], "release_period": it["period"]}))
    else:
        gaps.append("bls_macro:no_domestic_source(BLS 403)")
    macro["releases"] = releases

    # ---- 黄金资金流 ----
    etf_hist_vol = gld.get("change_pct")
    cn_flow_vals = {k: (v.get("main_net_inflow") if isinstance(v, dict) and not v.get("__failed__") else None)
                    for k, v in em.items()}
    cn_flow_sum = None
    vals = [x for x in cn_flow_vals.values() if isinstance(x, (int, float))]
    if vals: cn_flow_sum = sum(vals)
    gold_flows = {
        "etf": {"gld_price": gld.get("last"), "gld_change_pct_1d": etf_hist_vol,
                "cn_gold_etf_net_inflow_cny": cn_flow_vals, "cn_gold_etf_net_inflow_sum_cny": cn_flow_sum,
                "asof": {k: (v.get("date") if isinstance(v, dict) else None) for k, v in em.items()},
                "publication_ts": None,
                "pit_status": ("PASS" if cn_flow_sum is not None else "MISSING"),
                "global_etf_holdings": None,
                "note": "全球ETF持仓/净流(WGC)页面为 JS, 未取到 → data_gap; 国内ETF净流为真实流量(东财); asof=数据所属日",
                "source": "eastmoney + yahoo:GLD"},
        "central_bank": {"purchases": None, "reserves": None,
                         "note": "央行购金/储备披露无免 Key 直连 → placeholder; 待 WGC/官方接口"},
        "cot": {"contract": cot.get("contract"), "report_date": cot.get("report_date"),
                "publication_date": cot.get("publication_date"),
                "publication_timestamp_unknown": cot.get("publication_timestamp_unknown", True),
                "pit_status": ("UNKNOWN" if (cot.get("publication_timestamp_unknown", True) or not cot.get("publication_date")) else "PASS"),
                "timestamp_precision": cot.get("timestamp_precision", "approximate"),
                "open_interest": cot.get("open_interest"),
                "noncommercial_net": cot.get("noncommercial_net"),
                "commercial_net": (cot.get("commercial_long") or 0) - (cot.get("commercial_short") or 0)
                if not cot.get("__failed__") else None,
                "source": cot.get("source"), "credibility": "CONFIRMED",
                "note": "存量(stock)项; managed money 口径以 noncommercial 近似; 精确发布时刻未知"},
        "comex": {"open_interest": cot.get("open_interest"), "price": None,
                  "note": "OI 取 CFTC; 实时 OI/仓单无免 Key 源 → 部分覆盖"},
    }
    if not isinstance(cot.get("noncommercial_net"), (int, float)): gaps.append("cot:no_domestic_source(CFTC 403)")
    gaps.append("global_gold_etf_flows:WGC_JS(未取)")
    gaps.append("central_bank_gold_purchases:no_source")

    # ---- narrative vs flow ----
    narr = S.narrative_score(news)
    flow_dir = 0
    if cn_flow_sum is not None:
        flow_dir = 1 if cn_flow_sum > 0 else (-1 if cn_flow_sum < 0 else 0)
    divergence = bool(narr["net"] > 0.2 and flow_dir < 0) or bool(narr["net"] < -0.2 and flow_dir > 0)
    narrative_vs_flow = {"narrative": narr, "flow_direction": ("inflow" if flow_dir > 0 else "outflow" if flow_dir < 0 else "flat/none"),
                         "narrative_flow_divergence": divergence,
                         "note": "叙事(新闻措辞)与实际资金流(国内黄金ETF净流)方向冲突时置 TRUE; 供 Hermes 判断是否存在机会"}

    # ---- 方向性压力打分(透明启发式, 非交易信号) ----
    ev, score = [], 0.0
    dxy_p = _pct(dxy)
    if dxy_p is not None:
        s = -dxy_p  # 美元涨→黄金承压
        score += s * 0.4; ev.append(f"DXY 1d {dxy_p:+.2f}% → 压力 {(-dxy_p):+.2f}")
    tnx_p = _pct(tnx)
    if tnx_p is not None:
        s = -tnx_p
        score += s * 0.4; ev.append(f"UST10Y 1d {tnx_p:+.2f}% → 压力 {(-tnx_p):+.2f}(名义,实际利率见TIP)")
    vix_p = _pct(vix)
    if vix_p is not None:
        score += (vix_p * 0.2); ev.append(f"VIX 1d {vix_p:+.2f}% → 风险溢价 {vix_p*0.2:+.2f}")
    if cn_flow_sum is not None:
        fl = 0.5 if cn_flow_sum > 0 else -0.5
        score += fl; ev.append(f"国内黄金ETF净流 {cn_flow_sum/1e8:+.2f}亿 → {fl:+.2f}")
    if divergence:
        ev.append("narrative_flow_divergence=TRUE → 不确定性提升")
    conflicts = []
    if divergence: conflicts.append("叙事与资金流背离")
    if tnx_p is not None and dxy_p is not None and (tnx_p > 0) != (dxy_p > 0):
        conflicts.append("美元与美债收益率方向不一致")

    # P0-03：核心宏观字段状态（失败/缺失必须可见，且不得退化为 NEUTRAL）
    core = {"dxy": core_macro_status(dxy), "ust10y": core_macro_status(tnx), "vix": core_macro_status(vix)}
    for _k, _v in core.items():
        if _v != "OK":
            gaps.append(f"core_macro_{_k}:{_v}")
    core_degraded = any(v != "OK" for v in core.values())
    macro_status, state = macro_state(core_degraded, score, conflicts)

    completeness = macro_completeness({
        "DXY": ("AVAILABLE" if core.get("dxy") == "OK" else ("ERROR" if core.get("dxy") == "SOURCE_ERROR" else "MISSING")),
        "UST10Y": ("AVAILABLE" if core.get("ust10y") == "OK" else ("ERROR" if core.get("ust10y") == "SOURCE_ERROR" else "MISSING")),
        "VIX": ("AVAILABLE" if core.get("vix") == "OK" else ("ERROR" if core.get("vix") == "SOURCE_ERROR" else "MISSING")),
        "TIP": ("AVAILABLE" if (macro_field_status(tip) == "AVAILABLE" and tip.get("last") is not None) else macro_field_status(tip)),
        "BLS": ("AVAILABLE" if releases else "MISSING"),
        "COT": ("AVAILABLE" if isinstance(cot.get("noncommercial_net"), (int, float)) else "ERROR"),
        "ETF_FLOW_CN": ("AVAILABLE" if cn_flow_sum is not None else "MISSING"),
        "NEWS": ("AVAILABLE" if news else ("ERROR" if any(s["source_status"] == "NEWS_SOURCE_ERROR" for s in news_status.values()) else "MISSING")),
        "GEOPOLITICS": ("AVAILABLE" if geo_events else "MISSING"),
    })
    macro_pit_risk = []
    if gold_flows["cot"].get("pit_status") == "UNKNOWN":
        macro_pit_risk.append("COT")
    if (not releases) or any(r.get("point_in_time_confidence") == "low" for r in releases):
        macro_pit_risk.append("BLS")
    macro["completeness"] = completeness
    macro["news_status"] = news_status
    macro["macro_pit_risk"] = macro_pit_risk

    snap = {
        "agent": "agent2-macro-global", "agent_version": AGENT_VERSION,
        "snapshot_ts": _now(), "cycle": cycle, "symbol": "XAUUSD",
        "instrument": {"instrument": "XAUUSD", "reference_market": "GC_F", "spot_futures_proxy": False,
                       "note": "P0-01: 交易标的=XAUUSD; 本 Agent2 不含技术序列"},
        "market_regime": None,  # 技术 regime 属 Agent1; 此处留空避免越界
        "macro": macro,
        "geopolitics": {"events": geo_events[:20],
                        "levels_note": "CONFIRMED|MARKET_CONFIRMED|REPORTED|UNVERIFIED|SPECULATION; 本阶段新闻默认 REPORTED"},
        "gold_flows": gold_flows,
        "narrative_vs_flow": narrative_vs_flow,
        "gold_macro_state": state,
        "macro_status": macro_status,
        "core_macro_status": core,
        "key_evidence": ev,
        "conflicts": conflicts,
        "risks": ["无免Key的央行政策/购金/全球ETF流量直连源 → 覆盖不完整",
                  "新闻可信度默认 REPORTED, 未做事实核验"],
        "data_gaps": gaps,
        "macro_completeness": completeness,
        "macro_pit_risk": macro_pit_risk,
        "evidence": {"n_refs": len(set(ev_refs)), "refs": sorted(set(ev_refs))[:40],
                     "registry": "state/evidence_registry.jsonl", "raw_dir": "data_cache/evidence_raw/",
                     "note": "Hermes 可经 evidence_id → registry → raw → sha256 回溯当时看到的原内容"},
        "point_in_time": {"retrieved_at": _now(),
                          "cot_timestamp_confidence": "approximate(report_date only)",
                          "calendar_release_timestamp": "unavailable(官方源未提供精确发布时刻)",
                          "note": "每条记录带 published_at/retrieved_at; 新闻发布≠事件发生≠市场反应; 严禁用后更新污染历史"},
        "signal_guard": "本快照不包含任何 LONG/SHORT/BUY/SELL 交易信号(任务书 §10)",
    }
    STATE.mkdir(parents=True, exist_ok=True); SNAP.mkdir(parents=True, exist_ok=True)
    (STATE / "agent2_latest.json").write_text(json.dumps(snap, indent=1, ensure_ascii=False), encoding="utf-8")
    ver = SNAP / f"agent2_{_compact(cycle)}.json"
    if ver.exists():  # 不可变快照: 同 cycle 不覆盖, 追加序号
        n = 2
        while (SNAP / f"agent2_{_compact(cycle)}_{n}.json").exists():
            n += 1
        ver = SNAP / f"agent2_{_compact(cycle)}_{n}.json"
    ver.write_text(json.dumps(snap, indent=1, ensure_ascii=False), encoding="utf-8")
    return snap, ver


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(); ap.add_argument("--cycle", default=None)
    a = ap.parse_args()
    snap, ver = build(a.cycle)
    print("AGENT2_SNAPSHOT written:", ver)
    print("  gold_macro_state:", snap["gold_macro_state"])
    print("  DXY:", snap["macro"]["usd"]["value"], snap["macro"]["usd"]["change_pct_1d"], "%")
    print("  UST10Y:", snap["macro"]["rates"]["ust10y_pct"], snap["macro"]["rates"]["change_pct_1d"], "%")
    print("  COT net:", snap["gold_flows"]["cot"]["noncommercial_net"])
    print("  CN ETF flow(sum):", snap["gold_flows"]["etf"]["cn_gold_etf_net_inflow_sum_cny"])
    print("  narrative/flow divergence:", snap["narrative_vs_flow"]["narrative_flow_divergence"])
    print("  geopolitics events:", len(snap["geopolitics"]["events"]))
    print("  data_gaps:", snap["data_gaps"])
