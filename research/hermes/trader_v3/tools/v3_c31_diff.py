# -*- coding: utf-8 -*-
"""C-31 p2_summary 非确定性根因定位：逐字段深比较 + 分类 A-I。

用法: python v3_c31_diff.py <stored.json> <fresh.json>
输出: 差异 JSON pointer 列表 + 分类 + 是否触及研究语义字段。
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

SEMANTIC_KEYS = {"trade_count", "n", "n_trades", "n_signals", "fill_tick", "fill_tick_index", "sig_tick_index",
                 "return", "ret", "ret_bp", "mean", "median", "gross", "gross_bp", "spread", "spread_cost",
                 "slippage", "commission", "net", "net_bp", "realized_lat_ms", "declared_lat_ms",
                 "resolution_verdict", "population", "period", "effective_n", "pass", "pass_fail", "verdict",
                 "folds", "ic", "p_value", "sharpe"}
VOLATILE_KEYS = {"generated_utc", "generated_at", "ts", "timestamp", "runtime_ms", "duration_ms", "elapsed_ms",
                 "elapsed", "host", "machine", "hostname", "cwd", "outdir", "path", "pmtime", "mtime",
                 "created", "date", "time", "run_ts", "wall_clock"}


def walk(a, b, ptr="", out=None):
    out = out if out is not None else []
    if type(a) != type(b):
        out.append((ptr, "TYPE", a, b)); return out
    if isinstance(a, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a:
                out.append((ptr + "/" + k, "ONLY_IN_FRESH", None, b[k]))
            elif k not in b:
                out.append((ptr + "/" + k, "ONLY_IN_STORED", a[k], None))
            else:
                walk(a[k], b[k], ptr + "/" + k, out)
    elif isinstance(a, list):
        if len(a) != len(b):
            out.append((ptr, "LEN", len(a), len(b)))
        for i in range(min(len(a), len(b))):
            walk(a[i], b[i], ptr + f"[{i}]", out)
    else:
        if a != b:
            out.append((ptr, "VALUE", a, b))
    return out


def classify(ptr, kind, va, vb):
    key = ptr.rsplit("/", 1)[-1].split("[")[0].lower()
    if kind in ("ONLY_IN_FRESH", "ONLY_IN_STORED"):
        return "I", "新增/缺失字段"
    if key in VOLATILE_KEYS:
        return "F/G", "时间戳或路径/机器 metadata"
    if isinstance(va, float) or isinstance(vb, float):
        if isinstance(va, (int, float)) and isinstance(vb, (int, float)):
            d = abs((va or 0) - (vb or 0))
            return "B", f"浮点差异 |Δ|={d:.3e}"
        return "B", "浮点/类型"
    if key in SEMANTIC_KEYS:
        return "A", "计算/结果字段"
    if isinstance(va, (int, float)) and isinstance(vb, (int, float)):
        return "A/B", "数值差异"
    return "I", "其他(字符串/结构)"


def main():
    A = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    B = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    diffs = walk(A, B)
    print(f"total_diffs={len(diffs)}")
    buckets = {}
    semantic_hits = []
    for ptr, kind, va, vb in diffs[:400]:
        cat, why = classify(ptr, kind, va, vb)
        buckets[cat] = buckets.get(cat, 0) + 1
        key = ptr.rsplit("/", 1)[-1].split("[")[0].lower()
        if key in SEMANTIC_KEYS:
            semantic_hits.append((ptr, va, vb))
        print(f"  [{cat}] {ptr} :: {str(va)[:60]} -> {str(vb)[:60]}  ({why})")
    print("BUCKETS", json.dumps(buckets))
    print("SEMANTIC_FIELD_DIFFS", len(semantic_hits))
    for s in semantic_hits[:20]:
        print("   !!", s)
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
