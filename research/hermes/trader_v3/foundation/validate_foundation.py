"""V3 Foundation validation on REAL data (read-only inputs).

Runs: tick integrity, features, labels, cost model (measured spread),
GPU benchmark, mock execution calibration, tick recorder, data registry.
Writes outputs under trader_v3/state and trader_v3/data. Does NOT send orders.
"""
from __future__ import annotations
import glob
import json
import os
import sys
import tempfile
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
V3 = os.path.dirname(HERE)
sys.path.insert(0, V3)

from foundation import (tick_schema, tick_engine, feature_engine, label_engine,
                        cost_model, gpu_engine, execution_calibration, tick_recorder,
                        registry, ledger, pit_guard, timeutil)

DUKA = r"C:\AIQuant\data\staging_duka\assembled"
OUT = os.path.join(V3, "state")


def load_duka(path, max_rows=None):
    import pyarrow.parquet as pq
    cols = pq.ParquetFile(path).schema_arrow.names
    want = [c for c in ["ts_utc", "bid", "ask", "ask_vol", "bid_vol"] if c in cols]
    t = pq.read_table(path, columns=want)
    d = {c: t.column(c).to_numpy() for c in want}
    if max_rows:
        d = {k: v[:max_rows] for k, v in d.items()}
    return d


def main():
    res = {"generated_at": timeutil.now_iso(), "duka_dir": DUKA}
    files = sorted(glob.glob(os.path.join(DUKA, "ticks_*.parquet")))
    res["duka_files"] = [os.path.basename(f) for f in files]

    # ---- 1) tick integrity on a real file ----
    f0 = files[0]
    d = load_duka(f0)
    ts_ns = d["ts_utc"].astype(np.int64) * 1_000_000  # ms -> ns
    bid = d["bid"].astype(np.float64)
    ask = d["ask"].astype(np.float64)
    mon = tick_engine.IntegrityMonitor()
    n_int = min(500_000, len(bid))
    for i in range(n_int):
        mon.feed({
            "timestamp_ns": int(ts_ns[i]), "bid": float(bid[i]), "ask": float(ask[i]),
            "spread": float(ask[i] - bid[i]), "tick_sequence": i + 1,
        })
    # prove gap/stale/dup detection on real stream via injected anomalies
    mon2 = tick_engine.IntegrityMonitor(stale_ms=1000)
    for i in range(200):
        mon2.feed({"timestamp_ns": int(ts_ns[i]), "bid": float(bid[i]), "ask": float(ask[i]),
                   "spread": float(ask[i] - bid[i]), "tick_sequence": i + 1})
    mon2.feed({"timestamp_ns": int(ts_ns[199]), "bid": float(bid[199]), "ask": float(ask[199]),
               "spread": float(ask[199] - bid[199]), "tick_sequence": 200})     # duplicate ts
    mon2.feed({"timestamp_ns": int(ts_ns[150]), "bid": float(bid[150]), "ask": float(ask[150]),
               "spread": float(ask[150] - bid[150]), "tick_sequence": 500})     # regression + seq gap
    res["tick_integrity_real"] = {"file": os.path.basename(f0), "rates": mon.rates(),
                                  "verdict": mon.verdict(), "interval_stats_ms": mon.interval_stats_ms()}
    res["tick_integrity_injected"] = {"rates": mon2.rates(), "verdict": mon2.verdict()}

    # ---- 2) cost model (MEASURED spread from all files) ----
    cm = cost_model.CostModel()
    for f in files:
        dd = load_duka(f)
        b = dd["bid"].astype(np.float64); a = dd["ask"].astype(np.float64)
        m = (b + a) / 2.0
        sp = (a - b) / m * 1e4
        cm.spread_bp.extend(sp.tolist())
    res["cost_model"] = cm.summary()
    res["cost_model"]["minimum_required_move_p55"] = cm.minimum_required_move(0.55)
    res["cost_model"]["expected_net_edge_example_bp"] = cm.expected_net_edge(5.0)

    # ---- 3) features + labels on a subset ----
    n_sub = 200_000
    ts_s = ts_ns[:n_sub]; b_s = bid[:n_sub]; a_s = ask[:n_sub]
    feats = feature_engine.compute_features(b_s, a_s, ts_s, window=50,
                                            bid_vol=d["bid_vol"][:n_sub], ask_vol=d["ask_vol"][:n_sub])
    res["feature_engine"] = {
        "n": n_sub,
        "no_future_input": feature_engine.assert_no_future(feats["meta"]),
        "feature_schema_hash": feats["meta"]["feature_schema_hash"],
        "ofi_status": feats["features"]["order_flow_imbalance_status"],
        "feature_count": len([k for k in feats["features"] if hasattr(feats["features"][k], "shape")]),
    }
    mid = (b_s + a_s) / 2.0
    labels = {}
    for h in [100, 250, 500, 1000, 2000, 5000]:
        lab = label_engine.label(mid, ts_s, h, round_trip_cost_bp=None)
        ov = label_engine.overlap_stats(ts_s, h)
        labels[f"{h}ms"] = {"NET_LABEL_STATUS": lab["NET_LABEL_STATUS"],
                            "overlap_ratio": ov["overlap_ratio"], "effective_n": ov["effective_n"]}
    res["label_engine"] = labels

    # ---- 4) GPU benchmark (real data) ----
    nb = min(500_000, len(bid))
    res["gpu_benchmark"] = gpu_engine.benchmark(bid[:nb], ask[:nb], ts_ns[:nb], window=50)
    res["gpu_info"] = gpu_engine.info()

    # ---- 5) tick recorder on real ticks (write sample to V3 data dir) ----
    rec_dir = os.path.join(V3, "data", "ticks_v3")
    rec = tick_recorder.TickRecorder(rec_dir, fsync_every=500)
    for i in range(2000):
        t = tick_schema.make_tick(
            timestamp_ns=int(ts_ns[i]), mt5_server_time=int(d["ts_utc"][i]),
            local_receive_time_ns=0, symbol="XAUUSD", bid=float(bid[i]), ask=float(ask[i]),
            tick_sequence=i + 1, source="duka_historical", terminal_id="duka_assembled",
            account_id="N/A",
            extra={"bid_vol": int(d["bid_vol"][i]), "ask_vol": int(d["ask_vol"][i])})
        rec.write(t)
    rec.close()
    res["tick_recorder"] = {"dir": rec_dir, "manifest_exists": os.path.exists(os.path.join(rec_dir, "manifest.jsonl"))}

    # ---- 6) execution calibration MOCK (no orders) ----
    with tempfile.TemporaryDirectory() as td:
        cal = execution_calibration.ExecutionCalibrator(td)
        rng = np.random.default_rng(3)
        for i in range(50):
            sig = 1_000_000 * i
            bid_i = float(bid[i]); ask_i = float(ask[i])
            create = sig + 50_000; send = sig + 120_000
            ack = sig + 900_000 + int(rng.integers(0, 200_000))
            fill = ack + 150_000 + int(rng.integers(0, 100_000))
            cal.record_entry(signal_ns=sig, create_ns=create, send_ns=send, ack_ns=ack, fill_ns=fill,
                             requested_price=ask_i, bid=bid_i, ask=ask_i, fill_price=ask_i + 0.02)
            cal.record_exit(exit_signal_ns=sig, exit_request_ns=sig + 40_000, send_ns=sig + 100_000,
                            ack_ns=sig + 800_000, fill_ns=sig + 950_000,
                            exit_requested_price=bid_i, bid=bid_i, ask=ask_i, fill_price=bid_i - 0.02)
        res["execution_calibration_mock"] = {
            "mode": "MOCK_NO_ORDERS",
            "CALIBRATION_ORDERS_SENT": cal.orders_placed,
            "entry_profile": cal.entry_profile(),
            "exit_profile": cal.exit_profile(),
        }

    # ---- 7) ledger smoke on real event chain ----
    with tempfile.TemporaryDirectory() as td:
        lg = ledger.Ledger(os.path.join(td, "v3_hft_ledger.jsonl"))
        lg.append("TICK", int(ts_ns[0]), run_id="foundation", bid=float(bid[0]), ask=float(ask[0]))
        lg.append("FEATURE", int(ts_ns[1]), run_id="foundation", feature_hash=feats["meta"]["feature_schema_hash"])
        lg.append("MODEL", int(ts_ns[2]), run_id="foundation", model_version="baseline-v0")
        lg.append("AGENT", int(ts_ns[3]), run_id="foundation", decision_id="d0")
        lg.append("ENTRY", int(ts_ns[4]), run_id="foundation", order_id="o0", fill_price=float(ask[4]))
        lg.append("EXIT", int(ts_ns[5]), run_id="foundation", pnl=0.0)
        res["ledger"] = ledger.Ledger.verify(os.path.join(td, "v3_hft_ledger.jsonl"))

    # ---- 8) data registry ----
    reg = registry.DataRegistry(os.path.join(OUT, "V3_DATA_REGISTRY_v2.json"))
    total = 0
    for f in files:
        import pyarrow.parquet as pq
        n = pq.ParquetFile(f).metadata.num_rows
        total += n
        reg.add(name=os.path.basename(f), source="duka", symbol="XAUUSD",
                period=os.path.basename(f).replace("ticks_", "").replace(".parquet", ""),
                tick_count=n, status="OBSERVED", timestamp_resolution="ms",
                sha256=registry.sha256_file(f))
    for m in ["2023-12", "2024-04..2026-07", "daily 21:00-22:59Z"]:
        reg.add(name=m, source="duka", symbol="XAUUSD", period=m, tick_count=0,
                missing_periods=[m], status="MISSING",
                notes="registered gap; reopen condition required")
    reg.add(name="L2/trade_flow", source="none", symbol="XAUUSD", period="-", tick_count=0,
            status="UNKNOWN", notes="L2_DATA_GAP; optional, does not block V3 foundation")
    doc = reg.save()
    res["data_registry"] = {"entries": len(doc["entries"]), "total_ticks": total}

    os.makedirs(OUT, exist_ok=True)
    outp = os.path.join(OUT, "V3_FOUNDATION_VALIDATION.json")
    with open(outp, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1, default=str)
    print(json.dumps(res, ensure_ascii=False, indent=1, default=str))
    print("\nWROTE", outp)


if __name__ == "__main__":
    main()
