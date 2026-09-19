# -*- coding: utf-8 -*-
"""V3 总控初始化：从磁盘真实状态构建 Registries + DAG + PROJECT_STATE。

只读外部数据；仅在 research/hermes/trader_v3/ 下写 V3 控制产物。
用法: python tools/v3_control_init.py
"""
from __future__ import annotations
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

V3 = Path(__file__).resolve().parents[1]
ROOM = Path(r"C:\Users\surface\HermesWorkspaces\v3")
DUKA = Path(r"C:\AIQuant\data\staging_duka")
ASSEMBLED = DUKA / "assembled"
STATE = V3 / "state"
RESEARCH = V3 / "research"
STATE.mkdir(exist_ok=True); RESEARCH.mkdir(exist_ok=True)
NOW = datetime.now(timezone.utc).isoformat()


def sha(p, buf=1 << 20):
    try:
        h = hashlib.sha256()
        with open(p, "rb") as f:
            while True:
                b = f.read(buf)
                if not b:
                    break
                h.update(b)
        return h.hexdigest()
    except Exception:  # noqa: BLE001
        return None


def wj(name, obj):
    (STATE / name).write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")


def git(*a):
    try:
        return subprocess.run(["git", *a], cwd=r"C:\AIQuant", capture_output=True, text=True, timeout=20).stdout.strip()
    except Exception:  # noqa: BLE001
        return ""


# ---------------- Data Registry ----------------
def data_registry():
    ticks = []
    try:
        import pyarrow.parquet as pq
        for f in sorted(ASSEMBLED.glob("ticks_*.parquet")):
            n = None
            try:
                n = pq.ParquetFile(f).metadata.num_rows
            except Exception:  # noqa: BLE001
                pass
            ticks.append({"file": f.name, "bytes": f.stat().st_size, "rows": n, "sha256": sha(f)})
    except Exception as e:  # noqa: BLE001
        ticks.append({"error": str(e)})
    candles = sorted(DUKA.glob("candles_*.parquet"))
    reg = {
        "schema": "v3_data_registry/1", "ts_utc": NOW,
        "primary_dataset": "duka_assembled_v1",
        "tick_dir": str(ASSEMBLED), "tick_fields": ["ts_utc", "bid", "ask", "ask_vol", "bid_vol"],
        "tick_files": ticks, "tick_total_rows": sum(t.get("rows") or 0 for t in ticks if isinstance(t.get("rows"), int)),
        "candle_dir": str(DUKA), "candle_files": len(candles),
        "candle_range": [candles[0].name, candles[-1].name] if candles else None,
        "structural_gaps": ["2023-12 (整月 0 行)", "2024-04..2026-07 (整段 0 行)", "2026-08 仅到 08-04",
                            "每日 21:00-22:59 UTC 结构性缺口(~35% 日有数据)"],
        "field_status": {"bid": "AVAILABLE", "ask": "AVAILABLE", "ts_utc": "AVAILABLE",
                         "bid_vol": "DATA_GAP(field_unusable)", "ask_vol": "DATA_GAP(field_unusable)",
                         "candle.vol": "DATA_GAP(provenance_unverified)"},
        "candle_defect": "行重复 (day,side,sec) 需去重 (x2/x3); 去重前 count/vol 求和会放大",
        "same_source": "tick 与 candle 同源 (非独立第二源)",
        "measured_spread_bp_p50": 1.644904,
        "measured_spread_usd_p50": 0.347,
        "valid_day_proposal": "hours_covered >= 21 AND n_ticks >= 1000 (PROPOSAL, 未冻结)",
        "spec_ref": "research/V3_DATA_SPEC.md",
        "mt5_env_ref": "state/V3_MT5_ENVIRONMENT.json",
        "mt5_dataset": "fxtm_demo_v3 XAUUSD (独立实例, 只读)",
    }
    wj("V3_DATA_REGISTRY.json", reg)
    return reg


# ---------------- Artifact Registry ----------------
def artifact_registry():
    room_files = ["p2_net_edge_gate.py", "targets_gate.py", "TEAM_PLAN_V3_20260917.md",
                  "CLAIM_REGISTRY_DELTA_V3_20260917.yaml", ".g0a_real/g0a_report.json",
                  ".g0a_real/V3_DATA_SPEC.md", ".g0b_real/g0b_cost_report_real.json",
                  ".g_audit/g_resolution_audit.json",
                  ".p2_r31_33333/P2_R31_FIX_33333.md", ".recheck_r32/s25_fragment.md"]
    arts = []
    for rel in room_files:
        p = ROOM / rel
        if p.exists():
            arts.append({"path": str(p), "rel": rel, "bytes": p.stat().st_size, "sha256": sha(p)})
    for rel in ["V3_ALPHA_MAP.md", "V3_MULTIPLE_TESTING_LEDGER.yaml", "V3_RESOLUTION_AUDIT.md",
                "V3_ADVERSARIAL_AUDIT.md"]:
        p = V3 / rel
        if p.exists():
            arts.append({"path": str(p), "rel": rel, "bytes": p.stat().st_size, "sha256": sha(p), "in_repo": True})
    reg = {"schema": "v3_artifact_registry/1", "ts_utc": NOW,
           "room_workspace": str(ROOM), "artifacts": arts,
           "frozen_rules": {"identity": "sha256 + 数据版本 sha256 (mtime/叙述不作身份)",
                            "chat_numbers_not_evidence": True}}
    wj("V3_ARTIFACT_REGISTRY.json", reg)
    return reg


# ---------------- Experiment Registry ----------------
def experiment_registry():
    exps = [
        {"experiment_id": "A000_2s_momentum_z25", "family": "F7", "status": "ALREADY_RUN_ONCE / INADMISSIBLE",
         "hypothesis": "2s 短周期动量 (z>2.5) 有方向性边际", "horizon_ms": 2000, "holding_ms": 30000,
         "population": "ACTUAL_SIGNAL_SET", "periods": ["2023H2", "2024Q1"],
         "result": {"mean_bp": -1.9252, "median_bp": -2.0140, "n": 5242, "period2_mean_bp": -1.7880, "period2_n": 9346,
                    "verdict": "FAIL", "cross_period": "两段独立 claim_status=VERIFIED, overlap=0.00%"},
         "latency": "declared 1000ms, 实撮合 p50 1113ms (旧 P2 实现)",
         "artifact": ".p2_r31_33333/p2_summary_r31_real_2023H2_vs_2024Q1_taker.json",
         "note": "历史结果不得删除; 纳入 multiple-testing 分母 (F7 累计)",
         "classification": "HISTORICAL / PRE-C31 RESULT"},
    ]
    planned = {"C-31_ref": "tools/p2_net_edge_gate.py@c364f060",
               "first_batch": {"horizons_ms": [1000, 5000, 10000, 30000, 60000, 180000],
                               "families": ["F1_TickImbalance", "F2_QuoteImbalance", "F3_QuoteOFI", "F4_SpreadShock",
                                            "F5_QuoteUpdateIntensity", "F6_MicroPriceDisplacement", "F7_Momentum", "F8_Reversal"],
                               "planned_tests": 48, "status": "NOT_RUN / SCOPE_FROZEN"}}
    reg = {"schema": "v3_experiment_registry/1", "ts_utc": NOW, "experiments": exps,
           "planned": planned, "ledger_ref": "V3_MULTIPLE_TESTING_LEDGER.yaml",
           "rule": "无 Experiment ID / 冻结假设 / 冻结阈值 / 冻结窗口 / 冻结样本定义 → 不得作为正式实验运行"}
    wj("V3_EXPERIMENT_REGISTRY.json", reg)
    return reg


# ---------------- Hypothesis Registry ----------------
def hypothesis_registry():
    hyps = [
        {"id": "H-F1", "family": "Tick imbalance", "class": "A", "state": "PLANNED", "direction": True},
        {"id": "H-F2", "family": "Quote imbalance (按价)", "class": "A", "state": "PLANNED", "direction": True},
        {"id": "H-F3", "family": "Quote OFI (≠ Trade OFI)", "class": "A", "state": "PLANNED", "direction": True},
        {"id": "H-F4", "family": "Spread shock", "class": "A", "state": "PLANNED", "direction": True},
        {"id": "H-F5", "family": "Quote update intensity", "class": "A", "state": "PLANNED", "direction": True,
         "note": "activity→vol 已 SUPPORTED 但非方向 (CL-01)"},
        {"id": "H-F6", "family": "Micro-price displacement", "class": "A", "state": "PLANNED", "direction": True},
        {"id": "H-F7", "family": "Short-term momentum", "class": "A", "state": "ALREADY_RUN_ONCE",
         "ref": "A000_2s_momentum_z25", "direction": True},
        {"id": "H-F8", "family": "Short-term reversal", "class": "A", "state": "PLANNED", "direction": True},
        {"id": "H-D1", "family": "Cross-market lead-lag (DXY→gold)", "class": "C", "state": "REJECTED/CONTRADICTED"},
        {"id": "H-D2", "family": "Cross-market (XAG/GC/COMEX)", "class": "C", "state": "DATA_GAP (DATA_UNLOCK 未满足)"},
        {"id": "H-ML", "family": "ML 组合", "class": "-", "state": "BLOCKED (前置=至少1个方向 KEEP; 当前 0)"},
    ]
    wj("V3_HYPOTHESIS_REGISTRY.json", {"schema": "v3_hypothesis_registry/1", "ts_utc": NOW, "hypotheses": hyps})
    return hyps


# ---------------- Task DAG ----------------
def task_registry():
    T = [
        {"id": "G0-A", "stage": "G0", "task": "数据接入复验 (tick/candle/覆盖/缺口)", "status": "COMPLETE",
         "artifact": ".g0a_real/g0a_report.json + V3_DATA_SPEC.md", "gate": "G0"},
        {"id": "G0-B", "stage": "G0", "task": "成本实测 (点差/延迟/转化率)", "status": "COMPLETE",
         "artifact": ".g0b_real/g0b_cost_report_real.json"},
        {"id": "G0-C", "stage": "G0", "task": "闸门工具化 (spread 实测基线)", "status": "COMPLETE", "artifact": "targets_gate.py"},
        {"id": "G0", "stage": "G0", "task": "数据完整性与能力审计 Gate", "status": "PASS_WITH_DATA_GAP",
         "deps": ["G0-A", "G0-B", "G0-C"]},
        {"id": "G1-C31", "stage": "G1", "task": "C-31 冻结 (R-31.F/C + latency ladder + cost ladder + 0ms anchor + price sanity)",
         "status": "IN_PROGRESS", "artifact": "p2_net_edge_gate.py@c364f060", "deps": ["G0"],
         "open": ["3.1 same/changed 列命名裁定", "3.2 signals-basis vs ticks-basis 裁定", "§20.10 三次 recheck + co-sign"]},
        {"id": "G1", "stage": "G1", "task": "resolution/latency/cost freeze Gate", "status": "INSUFFICIENT_EVIDENCE", "deps": ["G1-C31"]},
        {"id": "G2-A", "stage": "G2", "task": "Alpha 域 A Price/Returns", "status": "BLOCKED_ON_G1", "deps": ["G1"]},
        {"id": "G2-B", "stage": "G2", "task": "Alpha 域 B Microstructure (F1-F6)", "status": "BLOCKED_ON_G1", "deps": ["G1"]},
        {"id": "G2-C", "stage": "G2", "task": "Alpha 域 C Short-horizon stats", "status": "BLOCKED_ON_G1", "deps": ["G1"]},
        {"id": "G2-H", "stage": "G2", "task": "Alpha 域 H Execution/Cost", "status": "BLOCKED_ON_G1", "deps": ["G1"]},
        {"id": "G3", "stage": "G3", "task": "G 对抗审计 (全程并存)", "status": "RUNNING", "deps": []},
        {"id": "G4", "stage": "G4", "task": "D Cross-Market", "status": "PAUSED", "deps": ["G2"], "reason": "第二市场同精度数据未到位"},
        {"id": "G5", "stage": "G5", "task": "E Event", "status": "PENDING", "deps": ["G2"], "reason": "需事件时间戳源"},
        {"id": "G6", "stage": "G6", "task": "F ML", "status": "BLOCKED", "deps": ["G2"], "reason": "前置=≥1 方向 KEEP; 当前 0"},
        {"id": "G7", "stage": "G7", "task": "最终跨期验证", "status": "PENDING", "deps": ["G2", "G3"]},
        {"id": "G8", "stage": "G8", "task": "最终 Alpha Map", "status": "IN_PROGRESS", "deps": ["G7"]},
        {"id": "INFRA-MT5", "stage": "G0", "task": "V3 独立 MT5 环境", "status": "COMPLETE (DATA_GAP: 独立账号)", "artifact": "research/V3_MT5_ENVIRONMENT.md"},
        {"id": "META-FREEZE", "stage": "G0", "task": "VALID_DAY 定义冻结实验", "status": "PROPOSAL (未冻结)", "deps": ["G0"]},
    ]
    wj("V3_TASK_REGISTRY.json", {"schema": "v3_task_registry/1", "ts_utc": NOW, "tasks": T})
    return T


# ---------------- Decision Log ----------------
def decision_log():
    entries = [
        {"ts": NOW, "actor": "总控", "decision": "采纳 room workspace (@default/1/222/33333) 既有 V3 工作为 CURRENT_STATE",
         "rationale": "任务书 §35: 先建 CURRENT_STATE, 不重复已完成工作", "effect": "classify FROZEN/VALID/HISTORICAL"},
        {"ts": NOW, "actor": "总控", "decision": "G0 = PASS_WITH_DATA_GAP",
         "rationale": "G0-A/B/C 交付完成; 缺口已登记 (2023-12/2024-04..2026-07/21-22h/vol 字段)", "effect": "G1 可开"},
        {"ts": NOW, "actor": "总控", "decision": "G1 = INSUFFICIENT_EVIDENCE (C-31 待裁定 + co-sign)",
         "rationale": "C-31-1..5 完成但 2 项待 default 终裁 + §20.10 三读 + co-sign 未完成", "effect": "Alpha Matrix 暂不放开"},
        {"ts": NOW, "actor": "总控", "decision": "未改动任何 V1/V2 文件; V3 路径 = research/hermes/trader_v3",
         "rationale": "任务书 §二 隔离", "effect": "path-limited commit"},
    ]
    with open(STATE / "V3_DECISION_LOG.jsonl", "w", encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    return entries


def main():
    dr = data_registry()
    ar = artifact_registry()
    er = experiment_registry()
    hr = hypothesis_registry()
    tr = task_registry()
    decision_log()
    state = {
        "schema": "v3_project_state/1", "ts_utc": NOW,
        "project": "XAUUSD 高频微结构 Alpha 独立研究 (V3)",
        "question": "XAUUSD 是否存在可重复/统计显著/经成本调整/在真实数据与执行条件下可实现的秒级~分钟级方向性微观 Alpha?",
        "current_stage": "G1", "current_gate": "G1_C31_FREEZE",
        "stage_status": {"G0": "PASS_WITH_DATA_GAP", "G1": "INSUFFICIENT_EVIDENCE",
                         "G2": "NOT_STARTED", "G3": "RUNNING", "G4": "PAUSED", "G5": "PENDING",
                         "G6": "BLOCKED", "G7": "PENDING", "G8": "IN_PROGRESS"},
        "running_tasks": ["G1-C31", "G3", "G8"],
        "blocked_tasks": ["G2-A", "G2-B", "G2-C", "G2-H", "G6"],
        "completed_tasks": ["G0-A", "G0-B", "G0-C", "INFRA-MT5"],
        "failed_tasks": [],
        "experiments_total": 1, "experiments_keep": 0, "experiments_reject": 1,
        "experiments_uncertain": 0, "experiments_data_gap": 0,
        "directional_keep": 0,
        "multiple_testing_status": "LEDGER_FROZEN_BATCH1 (F1-F8, 48 planned; A000 计入 F7 累计)",
        "audit_status": "G_FRAMEWORK_ACTIVE (17 attacks; A000 FAIL 已过跨期)",
        "v1_isolation": "OK (未连/未改)", "v2_isolation": "OK (未连/未改)",
        "v3_mt5_status": "COMPLETE (fxtm_demo_v3, magic 90004, 只读; DATA_GAP: 独立账号)",
        "order_send_status": "BLOCKED (code-level) — V3_ORDER_SEND_ALLOWED=NO",
        "forward_status": "NO (V3_FORWARD_ALLOWED=NO)", "live_status": "NO (V3_LIVE_ALLOWED=NO)",
        "data_registry_ref": "state/V3_DATA_REGISTRY.json", "artifact_registry_ref": "state/V3_ARTIFACT_REGISTRY.json",
        "experiment_registry_ref": "state/V3_EXPERIMENT_REGISTRY.json",
        "hypothesis_registry_ref": "state/V3_HYPOTHESIS_REGISTRY.json",
        "task_registry_ref": "state/V3_TASK_REGISTRY.json",
        "git_head": git("rev-parse", "--short", "HEAD"),
        "next_actions": [
            "裁定 C-31 §3.1/§3.2 (default 终裁) → 完成 §20.10 三读 + co-sign → 冻结 C-31 (G1)",
            "冻结 VALID_DAY 定义 (hours>=21 AND n_ticks>=1000) 作为当前提案的正式登记",
            "G1 冻结后放开 G2 A/B/C/H Alpha Matrix (F1-F6,F8, 48 格)",
            "G8: 建立 V3_ALPHA_MAP.json (机器可读)",
        ],
    }
    wj("V3_PROJECT_STATE.json", state)
    print(json.dumps({"data_files": len(dr["tick_files"]), "tick_rows": dr["tick_total_rows"],
                      "artifacts": len(ar["artifacts"]), "tasks": len(tr),
                      "stage": state["current_stage"], "gate": state["current_gate"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
