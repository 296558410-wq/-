# -*- coding: utf-8 -*-
"""V1 审计 PHASE A — 数据盘点 + V1_AUDIT_DATA_REGISTRY.json（只读；不改 V1/V2/V3）。

每个数据源记录: path,type,time_range,row_count,sha256,source,schema,timezone,
timestamp_resolution,completeness,whether_used,reason_if_excluded + classification。
"""
from __future__ import annotations
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

V1 = Path(r"C:\AIQuant\research\hermes\trader_v1")
AUDIT = Path(r"C:\AIQuant\research\hermes\v1_audit")
AUDIT.mkdir(parents=True, exist_ok=True)
DATA = Path(r"C:\AIQuant\data")
MT5V1 = Path(r"C:\Program Files\ForexTime (FXTM) MT5")
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


def count_lines(p):
    try:
        with open(p, "r", encoding="utf-8", errors="replace") as f:
            return sum(1 for _ in f if _.strip())
    except Exception:  # noqa: BLE001
        return None


def jsonl_range(p):
    try:
        first = last = None
        with open(p, "r", encoding="utf-8", errors="replace") as f:
            for ln in f:
                ln = ln.strip()
                if not ln:
                    continue
                try:
                    o = json.loads(ln)
                except Exception:  # noqa: BLE001
                    continue
                t = o.get("ts") or o.get("timestamp_utc") or o.get("time") or o.get("ts_utc") or o.get("timestamp")
                if t:
                    if first is None:
                        first = t
                    last = t
        return [first, last]
    except Exception:  # noqa: BLE001
        return [None, None]


def schema_of(p):
    if p.suffix == ".json":
        try:
            o = json.loads(p.read_text(encoding="utf-8"))
            return sorted(o.keys())[:30] if isinstance(o, dict) else type(o).__name__
        except Exception:  # noqa: BLE001
            return None
    if p.suffix == ".jsonl":
        try:
            with open(p, "r", encoding="utf-8", errors="replace") as f:
                for ln in f:
                    ln = ln.strip()
                    if ln:
                        o = json.loads(ln)
                        return sorted(o.keys())[:30] if isinstance(o, dict) else type(o).__name__
        except Exception:  # noqa: BLE001
            return None
    return None


def classify(path_str, name):
    s = path_str.replace("\\", "/").lower()
    if "decisions" in s or "positions" in s:
        return "RUNTIME"
    if name in ("plan_ledger.jsonl", "statistics.json", "trader_summary.txt", "workflow_history.jsonl",
                "workflow_latest.json", "state_package_latest.json", "bars_cache.json", "candle_latest.json",
                "v2_run_health.json"):
        return "RUNTIME"
    if "memory/reviews" in s.replace("\\", "/"):
        return "HISTORICAL"
    if name.startswith("E2E_REPLAY") or name.startswith("AUDIT_REPORT") or name.startswith("V12_FINAL"):
        return "HISTORICAL"
    if "contracts" in s or name.endswith(".yaml"):
        return "FROZEN"
    if name in ("00_TRADER_PROTOCOL.md", "DESIGN_V11.md"):
        return "FROZEN"
    return "HISTORICAL"


def dir_entry(d, type_, source, use=True):
    files = sorted(p for p in d.rglob("*") if p.is_file())
    tot = sum(p.stat().st_size for p in files)
    acc = hashlib.sha256()
    dups = {}
    for p in files:
        h = sha(p)
        acc.update(f"{p.name}:{p.stat().st_size}:{h}\n".encode())
        dups.setdefault(h, []).append(p.name)
    dup_groups = {h: v for h, v in dups.items() if len(v) > 1}
    ts = [p.stem for p in files]
    names = sorted(p.name for p in files)
    return {"path": str(d), "type": type_, "file_count": len(files), "total_bytes": tot,
            "sha256_aggregate": acc.hexdigest(), "source": source, "time_range": [names[0], names[-1]] if names else None,
            "schema": "dir(*)", "timezone": "UTC(filenames)", "timestamp_resolution": "15m(filename)",
            "completeness": f"{len(files)} files", "whether_used": use,
            "duplicate_sha256_groups": {h[:12]: v for h, v in list(dup_groups.items())[:10]},
            "n_duplicate_groups": len(dup_groups), "classification": classify(str(d), d.name)}


def file_entry(p, type_, source, use=True, reason=None):
    e = {"path": str(p), "type": type_, "bytes": p.stat().st_size, "sha256": sha(p), "source": source}
    if p.suffix == ".jsonl":
        e["row_count"] = count_lines(p)
        e["time_range"] = jsonl_range(p)
    e["schema"] = schema_of(p)
    e["timezone"] = "UTC(assumed; verify in PHASE C)"
    e["timestamp_resolution"] = "per-record ts (ms/s?)"
    e["completeness"] = "n/a"
    e["whether_used"] = use
    e["reason_if_excluded"] = reason
    e["classification"] = classify(str(p), p.name)
    return e


def mt5_dir(path, source):
    if not path.exists():
        return {"path": str(path), "type": "mt5_terminal", "exists": False, "source": source}
    files = [p for p in path.rglob("*") if p.is_file()]
    return {"path": str(path), "type": "mt5_terminal", "exists": True,
            "file_count": len(files), "total_bytes": sum(p.stat().st_size for p in files),
            "terminal_exe": str(path / "terminal64.exe"), "terminal_exe_sha256": sha(path / "terminal64.exe"),
            "logs_dir": str(path / "logs"), "source": source, "whether_used": False,
            "reason_if_excluded": "V1 终端数据目录；PHASE B 决定是否用于行情恢复（不写入）",
            "classification": "RUNTIME"}


def main():
    reg = {"schema": "v1_audit_data_registry/1", "ts_utc": NOW, "v1_root": str(V1),
           "note": "PHASE A 只盘点登记，不做任何分析；不修改 V1/V2/V3", "entries": [], "market_data": [],
           "code_sha256": {}, "gaps": []}
    E = reg["entries"]
    # --- V1 run_state 关键文件 ---
    rs = V1 / "run_state"
    for nm, ty, src, use, reason in [
            ("plan_ledger.jsonl", "plan_ledger(PIT)", "V1 engine", True, None),
            ("statistics.json", "stats", "V1 metrics", True, None),
            ("trader_summary.txt", "human_summary", "V1", True, None),
            ("workflow_history.jsonl", "workflow", "V1", True, None),
            ("workflow_latest.json", "workflow_latest", "V1", True, None),
            ("state_package_latest.json", "state_package(RUNTIME snapshot)", "V1", True,
             "仅最新快照(非逐笔历史)，PHASE C 需确认能否复原逐笔"),
            ("bars_cache.json", "bars_cache", "V1", False, "缓存，非权威"),
            ("candle_latest.json", "candle_latest", "V1", False, "缓存，非权威"),
            ("E2E_REPLAY_20260907T1247.md", "replay_report", "V1", True, None),
            ("opportunity_frequency_study.txt", "study", "V1", False, "早期探索"),
            ("../trader_summary.txt", "human_summary(dup?)", "V1", False, "与 run_state 同名，需判 DUPLICATE"),
            ("../AUDIT_REPORT_20260907.md", "audit_report", "V1", True, None),
            ("../V12_FINAL_REPORT.md", "final_report", "V1", True, None)]:
        p = (rs / nm) if not nm.startswith("../") else (V1 / nm.replace("../", ""))
        if p.exists():
            E.append(file_entry(p, ty, src, use, reason))
    # --- 目录 ---
    for d, ty, src, use in [(rs / "decisions", "decisions(per-15m json)", "V1 engine", True),
                            (rs / "positions", "positions(POS-*.json)", "V1 position", True),
                            (V1 / "memory" / "reviews", "reviews(RV-*.json)", "V1 review.py", True),
                            (V1 / "contracts", "contracts(yaml)", "V1", True),
                            (rs / "tmp", "tmp", "V1", False)]:
        if d.exists():
            E.append(dir_entry(d, ty, src, use))
    # --- 代码 SHA256 ---
    for f in ["engine.py", "trader_core.py", "position.py", "position_decision.py", "ledger.py", "review.py",
              "metrics.py", "state_package.py", "stop_authority.py", "trigger.py", "opportunity.py",
              "candlestick.py", "invariants.py", "broker_mt5_demo.py", "replay_study.py"]:
        p = V1 / f
        if p.exists():
            reg["code_sha256"][f] = sha(p)
    # --- 配置/版本（不打印敏感值） ---
    env = Path(r"C:\AIQuant\.env.mt5_demo")
    kv = {}
    if env.exists():
        for ln in env.read_text(encoding="utf-8", errors="replace").splitlines():
            if "=" in ln and not ln.strip().startswith("#"):
                k = ln.split("=", 1)[0].strip()
                kv[k] = "***"
    reg["v1_config"] = {"env_file": str(env), "env_keys": sorted(kv),
                        "broker_magic_note": "V1 magic=90002 (据 fxtm_demo_adapter 注释)", "secrets_redacted": True}
    # --- 市场数据（真实行情候选） ---
    for d, ty, src in [(DATA / "live_fxtm", "ticks(local parquet)", "V1 tick collector"),
                       (DATA / "staging_mt5", "mt5 staging", "collector"),
                       (DATA / "staging_fxtm", "fxtm staging", "collector")]:
        if d.exists():
            e = dir_entry(d, ty, src, True)
            reg["market_data"].append(e)
    reg["market_data"].append(mt5_dir(MT5V1, "V1 main MT5 terminal (Program Files)"))
    # --- gaps ---
    reg["gaps"] = [
        "V1 逐笔 tick 是否覆盖全部交易时刻：待 PHASE B 核对（data/live_fxtm 起始时间 vs 交易时间）",
        "T_signal/T_order/T_fill/T_exit 的可用性：待 PHASE C 定义（plan_ledger + decisions + positions）",
        "真实 spread/slippage/commission/swap 逐笔：待 PHASE B/C 确认",
        "state_package 仅 latest 快照，历史逐笔上下文可能缺 → 可能 DATA_GAP",
    ]
    (AUDIT / "V1_AUDIT_DATA_REGISTRY.json").write_text(json.dumps(reg, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"entries": len(E), "market_data": len(reg["market_data"]),
                      "code_files": len(reg["code_sha256"])}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
