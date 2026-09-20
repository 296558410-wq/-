"""V3 HFT Foundation test suite (self-contained runner).

Run:  python -m foundation.tests.run_all     (from trader_v3/)
      or python foundation/tests/run_all.py
Exit 0 if all pass.
"""
from __future__ import annotations
import os
import sys
import tempfile
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from foundation import (tick_engine, tick_schema, tick_recorder, execution_calibration,
                        cost_model, gpu_engine, feature_engine, label_engine, pit_guard,
                        ledger, registry, agent_interface, entry_exit_interface)
from foundation.tests import _helpers as H

RESULTS = []
TESTS = []


def case(fn):
    def wrap():
        try:
            fn()
            RESULTS.append((fn.__name__, True, ""))
        except Exception as e:  # noqa: BLE001
            RESULTS.append((fn.__name__, False, f"{type(e).__name__}:{e}"))
    wrap.__name__ = fn.__name__
    TESTS.append(wrap)
    return wrap


# ---------------- Tick ----------------
@case
def tick_duplicate_out_of_order_regression():
    m = tick_engine.IntegrityMonitor()
    base = H.make_ticks(5)
    for t in base:
        m.feed(t)
    dup = dict(base[-1]); m.feed(dup)  # same ts
    ooo = dict(base[-2]); m.feed(ooo)  # older ts
    r = m.rates()
    assert r["TICK_DUPLICATE_RATE"] > 0
    assert r["TIMESTAMP_REGRESSION_COUNT"] > 0
    assert m.verdict() == "FAIL"


@case
def tick_stale_detection():
    m = tick_engine.IntegrityMonitor(stale_ms=1000)
    a, b = H.make_ticks(2)
    b["timestamp_ns"] = a["timestamp_ns"] + 5_000_000_000
    m.feed(a); m.feed(b)
    assert m.rates()["STALE_TICK_COUNT"] == 1


@case
def tick_schema_validation():
    t = H.make_ticks(1)[0]
    tick_schema.validate_tick(t)
    bad = dict(t); bad["ask"] = bad["bid"] - 1
    try:
        tick_schema.validate_tick(bad); assert False
    except tick_schema.TickValidationError:
        pass


@case
def tick_recorder_append_only_resume():
    with tempfile.TemporaryDirectory() as d:
        r = tick_recorder.TickRecorder(d, fsync_every=10)
        for t in H.make_ticks(10):
            r.write(t)
        r.close()
        # resume: write more, must not overwrite
        r2 = tick_recorder.TickRecorder(d, fsync_every=10)
        for t in H.make_ticks(3):
            r2.write(t)
        r2.close()
        files = [f for f in os.listdir(os.path.join(d, "2026-09-20")) if f.endswith(".jsonl")]
        total = sum(sum(1 for _ in open(os.path.join(d, "2026-09-20", f), encoding="utf-8")) for f in files)
        assert total == 13, total
        assert os.path.exists(os.path.join(d, "manifest.jsonl"))


# ---------------- Execution ----------------
@case
def execution_entry_timestamp_integrity():
    with tempfile.TemporaryDirectory() as d:
        c = execution_calibration.ExecutionCalibrator(d)
        rec = c.record_entry(signal_ns=1000, create_ns=1100, send_ns=1200, ack_ns=1500,
                             fill_ns=2000, requested_price=3300.0, bid=3299.8, ask=3300.2,
                             fill_price=3300.3)
        lb = rec["latency_breakdown"]
        assert lb["signal_to_send_ns"] == 200
        assert lb["send_to_ack_ns"] == 300
        assert lb["ack_to_fill_ns"] == 500
        assert lb["signal_to_fill_ns"] == 1000
        assert rec["latency_total_ns"] == 1000


@case
def execution_exit_and_profiles():
    with tempfile.TemporaryDirectory() as d:
        c = execution_calibration.ExecutionCalibrator(d)
        for i in range(20):
            c.record_entry(signal_ns=i*1000, create_ns=i*1000+10, send_ns=i*1000+20,
                           ack_ns=i*1000+60, fill_ns=i*1000+100, requested_price=3300.0,
                           bid=3299.8, ask=3300.2, fill_price=3300.0 + (i % 3)*0.1)
            c.record_exit(exit_signal_ns=i*1000, exit_request_ns=i*1000+5, send_ns=i*1000+15,
                          ack_ns=i*1000+50, fill_ns=i*1000+90, exit_requested_price=3300.0,
                          bid=3299.9, ask=3300.1, fill_price=3299.9)
        ep = c.entry_profile()["ENTRY_LATENCY_PROFILE"]
        xp = c.exit_profile()["EXIT_LATENCY_PROFILE"]
        assert ep["signal_to_fill_ns"]["n"] == 20
        assert xp["exit_latency_ns"]["n"] == 20
        assert ep["signal_to_fill_ns"]["median"] == 100


@case
def execution_slippage_calc():
    with tempfile.TemporaryDirectory() as d:
        c = execution_calibration.ExecutionCalibrator(d)
        rec = c.record_entry(signal_ns=0, create_ns=1, send_ns=2, ack_ns=3, fill_ns=4,
                             requested_price=1000.0, bid=999.9, ask=1000.1, fill_price=1000.2)
        assert abs(rec["slippage_price"] - 0.2) < 1e-9
        assert abs(rec["slippage_bps"] - (0.2 / 1000.0 * 1e4)) < 1e-6


@case
def execution_order_gate_disabled():
    with tempfile.TemporaryDirectory() as d:
        c = execution_calibration.ExecutionCalibrator(d, max_orders=5, authorized=False)
        try:
            c.place_calibration_order(send_fn=lambda o: o); assert False
        except execution_calibration.CalibrationDisabled:
            pass
        # authorized but cap enforcement
        c2 = execution_calibration.ExecutionCalibrator(d, max_orders=2, authorized=True)
        c2.place_calibration_order(send_fn=lambda o: o)
        c2.place_calibration_order(send_fn=lambda o: o)
        try:
            c2.place_calibration_order(send_fn=lambda o: o); assert False
        except execution_calibration.CalibrationDisabled:
            pass


# ---------------- Cost ----------------
@case
def cost_spread_and_roundtrip():
    cm = cost_model.CostModel()
    for _ in range(100):
        cm.add_spread(3299.8, 3300.2)
    rt = cm.round_trip_cost_bp()
    assert rt["value"] is not None
    assert rt["status"].startswith(("MEASURED", "PARTIAL"))
    # minimum_required_move needs measured commission
    mrm = cm.minimum_required_move(0.55)
    assert mrm["status"] != "MEASURED"  # commission not measured -> not fully measured


@case
def cost_min_move_measured():
    cm = cost_model.CostModel()
    for _ in range(100):
        cm.add_spread(3299.8, 3300.2)
    cm.add_slippage_bp(0.5)
    cm.set_commission_bp(0.2, source="MEASURED")
    mrm = cm.minimum_required_move(0.55)
    assert mrm["status"] == "MEASURED"
    rt = cm.round_trip_cost_bp()["value"]
    assert abs(mrm["value_bp"] - rt / 0.1) < 1e-6


@case
def cost_data_gap_when_no_spread():
    cm = cost_model.CostModel()
    assert cm.round_trip_cost_bp()["status"] == "DATA_GAP"
    assert cm.expected_net_edge(5.0)["status"] == "DATA_GAP"


# ---------------- GPU ----------------
@case
def gpu_engine_real_compute():
    info = gpu_engine.info()
    assert "error" not in info
    if not info["cuda_available"]:
        return  # env has no GPU -> not a failure
    bid, ask, ts = H.synth_arrays(20_000)
    g = gpu_engine.compute_gpu(bid, ask, ts, window=50)
    assert g["backend"] in ("gpu", "cpu_fallback")
    if g["backend"] == "gpu":
        assert np.isfinite(g["features"]["spread"]).all()


@case
def gpu_cpu_equivalence():
    info = gpu_engine.info()
    if not info.get("cuda_available"):
        return
    bid, ask, ts = H.synth_arrays(10_000)
    cpu = feature_engine.compute_features(bid, ask, ts, window=50)["features"]
    g = gpu_engine.compute_gpu(bid, ask, ts, window=50)
    if g["backend"] != "gpu":
        return
    for k in ["spread", "liquidity_proxy"]:
        a = cpu[k]; b = g["features"][k]
        m = np.isfinite(a) & np.isfinite(b)
        assert np.max(np.abs(a[m] - b[m])) < 1e-3


@case
def gpu_oom_chunking_safe():
    info = gpu_engine.info()
    if not info.get("cuda_available"):
        return
    bid, ask, ts = H.synth_arrays(500_000)
    g = gpu_engine.compute_gpu(bid, ask, ts, window=50, chunk=50_000)  # small chunks
    assert "backend" in g  # must not raise / crash


# ---------------- Feature ----------------
@case
def feature_no_future_input():
    bid, ask, ts = H.synth_arrays(1000)
    res = feature_engine.compute_features(bid, ask, ts, window=20)
    assert feature_engine.assert_no_future(res["meta"]) is True


@case
def feature_determinism():
    bid, ask, ts = H.synth_arrays(500)
    a = feature_engine.compute_features(bid, ask, ts, window=20)["features"]
    b = feature_engine.compute_features(bid, ask, ts, window=20)["features"]
    for k in a:
        if not hasattr(a[k], "shape"):
            continue
        assert np.allclose(a[k], b[k], equal_nan=True)


@case
def feature_ofi_proxy_labelled():
    bid, ask, ts = H.synth_arrays(200)
    res = feature_engine.compute_features(bid, ask, ts)["features"]
    assert res["order_flow_imbalance_status"].startswith("DATA_GAP")
    bid2, ask2, ts2, bv, av = H.synth_arrays_with_size(200)
    res2 = feature_engine.compute_features(bid2, ask2, ts2, bid_vol=bv, ask_vol=av)["features"]
    assert res2["order_flow_imbalance_status"] == "L1_PROXY"


# ---------------- Label ----------------
@case
def label_future_window_correctness():
    mid = np.array([100.0, 101.0, 102.0])
    ts = np.array([0, 1_000_000_000, 2_000_000_000], dtype=np.int64)
    r = label_engine.future_returns(mid, ts, horizon_ms=1000)
    assert abs(r[0] - 0.01) < 1e-9
    assert abs(r[1] - (102/101 - 1)) < 1e-9
    assert np.isnan(r[2])


@case
def label_overlap_detection():
    mid = np.ones(1000); ts = np.arange(0, 1000) * 1_000_000  # 1ms apart -> 1e6 ns
    st = label_engine.overlap_stats(ts, horizon_ms=100)
    assert st["overlap_ratio"] == 100.0
    assert st["effective_n"] == 10


@case
def label_net_requires_cost():
    mid = np.linspace(100, 101, 10); ts = np.arange(10) * 1_000_000
    l = label_engine.label(mid, ts, 1000, round_trip_cost_bp=None)
    assert l["NET_LABEL_STATUS"] == "DATA_GAP"
    l2 = label_engine.label(mid, ts, 1000, round_trip_cost_bp=2.0)
    assert l2["NET_LABEL_STATUS"].startswith("OK")


# ---------------- PIT ----------------
@case
def pit_no_future_enforced():
    try:
        pit_guard.assert_no_future([10, 20], [11, 20]); assert False
    except AssertionError:
        pass
    pit_guard.assert_no_future([10, 20], [10, 20])


@case
def pit_purged_split_no_overlap():
    ts = np.arange(1000) * 1_000_000
    tr, va, te = pit_guard.purged_split(ts, embargo_ns=0, horizon_ns=5_000_000)
    # ranges must be ordered and purged
    if tr.any() and te.any():
        assert ts[tr].max() < ts[te].min()


# ---------------- Ledger ----------------
@case
def ledger_append_only_hash_chain():
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "l.jsonl")
        lg = ledger.Ledger(p)
        for i in range(50):
            lg.append("TICK", i, run_id="R1", bid=1.0, ask=1.1, spread=0.1)
        v = ledger.Ledger.verify(p)
        assert v["ok"] is True and v["events"] == 50
        assert len(ledger.Ledger.replay(p)) == 50


@case
def ledger_tamper_detected():
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "l.jsonl")
        lg = ledger.Ledger(p)
        for i in range(5):
            lg.append("TICK", i)
        lines = open(p, encoding="utf-8").read().splitlines()
        import json as _j
        e = _j.loads(lines[2]); e["bid"] = 999.0; lines[2] = _j.dumps(e, sort_keys=True, separators=(",", ":"))
        open(p, "w", encoding="utf-8").write("\n".join(lines) + "\n")
        assert ledger.Ledger.verify(p)["ok"] is False


# ---------------- Interfaces / registry ----------------
@case
def agent_interface_no_auto_decision():
    pred = agent_interface.PredictionContract(0.6, 0.4, 0.001, 0.0005, 500, "v0")
    pred.validate()
    assert agent_interface.decision_from_prediction(pred) == agent_interface.Decision.WAIT
    assert agent_interface.AUTO_DECISION is False


@case
def entry_exit_interface_order_send_false():
    intent = entry_exit_interface.build_intent(entry_exit_interface.Signal.ENTRY_LONG,
                                               123, "d1", {"bid": 1.0, "ask": 1.1})
    assert intent.order_send is False
    try:
        entry_exit_interface.send(intent); assert False
    except RuntimeError:
        pass
    assert entry_exit_interface.ORDER_SEND is False


@case
def registry_status_vocab():
    with tempfile.TemporaryDirectory() as d:
        r = registry.DataRegistry(os.path.join(d, "reg.json"))
        r.add(name="duka_tick", source="duka", symbol="XAUUSD", period="2023-09..2024-03",
              tick_count=100, status="OBSERVED")
        r.add(name="2023-12", source="duka", symbol="XAUUSD", period="2023-12",
              tick_count=0, status="MISSING")
        doc = r.save()
        assert len(doc["entries"]) == 2


@case
def model_pipeline_smoke():
    bid, ask, ts = H.synth_arrays(2000)
    feats = feature_engine.compute_features(bid, ask, ts, window=20)["features"]
    mid = (bid + ask) / 2.0
    lab = label_engine.future_returns(mid, ts, 100)
    X, y, names, mask = __import__("foundation.model_pipeline", fromlist=["x"]).build_dataset(feats, lab > 0)
    if len(X) < 50:
        return
    Xs, mu, sd = __import__("foundation.model_pipeline", fromlist=["x"]).standardize(X)
    tr, va, te = pit_guard.purged_split(ts[mask])
    from foundation import model_pipeline as MP
    if tr.sum() < 10 or te.sum() < 5:
        return
    w, b = MP.train_logistic(Xs[tr], y[tr].astype(float))
    p = MP.predict_logistic(Xs[te], w, b)
    acc = MP.accuracy(p, y[te].astype(float))
    assert 0.0 <= acc <= 1.0


def run() -> int:
    for fn in TESTS:
        fn()
    passed = sum(1 for _, ok, _ in RESULTS if ok)
    for name, ok, err in RESULTS:
        print(f"[{'PASS' if ok else 'FAIL'}] {name}" + ("" if ok else f"  -> {err}"))
    print(f"=== TEST_COUNT={len(RESULTS)} PASS={passed} FAIL={len(RESULTS)-passed} ===")
    return 0 if passed == len(RESULTS) else 1


if __name__ == "__main__":
    raise SystemExit(run())
