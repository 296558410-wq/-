# -*- coding: utf-8 -*-
"""V2 Module 3 — Demo Calibration phase2 → 统一账本 迁移适配器（**原始记录只读, 不改**）。

- 读取 state/demo_calibration/phase2/*.json（只读），转成 environment=BROKER_DEMO / execution_mode=BROKER_DEMO 事件。
- 每个事件附 `source_record_hash`（对应源文件的 sha256），使迁移记录可追溯到原始文件。
- 不把 n=1 calibration 伪装成统计参数（仅作 observation 记录）。
"""
from __future__ import annotations
import hashlib, json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import ledger as L  # noqa: E402

PHASE2 = ROOT / "state" / "demo_calibration" / "phase2"
OUT_DEFAULT = ROOT / "ledger" / "hermes_v2_ledger.jsonl"
ENV = "FXTM_DEMO"
MODE = "BROKER_DEMO"


def _load(p):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None


def _sha_file(p):
    try:
        return hashlib.sha256(Path(p).read_bytes()).hexdigest()
    except Exception:  # noqa: BLE001
        return None


def migrate(phase_dir=None, out_path=None):
    pd = Path(phase_dir or PHASE2)
    out = Path(out_path or OUT_DEFAULT)
    files = {n: pd / f"{n}.json" for n in
             ("order_request", "order_response", "close_request", "close_response", "summary", "attempt1_rejected")}
    data = {n: _load(p) for n, p in files.items()}
    hashes = {n: _sha_file(p) for n, p in files.items()}
    emitted = []

    def emit(ev):
        emitted.append(L.append_event(ev, out))

    # ---- attempt 1 (rejected) ----
    a1 = data["attempt1_rejected"]
    if a1:
        h = hashes["attempt1_rejected"]
        emit(L.new_event("DECISION", environment="BROKER_DEMO", execution_mode=MODE,
                         strategy_id="demo_calibration", strategy_version="phase2", decision_id="DEMO-CALIB-1",
                         symbol=a1.get("symbol"), side="BUY", status="TRADE", retcode=None,
                         message="fixed BUY experiment (attempt1)", source_record_hash=h))
        emit(L.new_event("EXECUTION_REQUEST", environment="BROKER_DEMO", execution_mode=MODE,
                         strategy_id="demo_calibration", decision_id="DEMO-CALIB-1",
                         symbol=a1.get("symbol"), side="BUY", order_type="MARKET", volume=a1.get("volume"),
                         requested_price=a1.get("requested_price"), reference_bid=a1.get("bid"),
                         reference_ask=a1.get("ask"), reference_mid=a1.get("mid"), spread=a1.get("spread_price"),
                         request_timestamp=a1.get("request_timestamp_monotonic"), latency_ms=a1.get("response_latency_ms"),
                         order_id=a1.get("order_id"), deal_id=a1.get("deal_id"), status="REQUESTED",
                         source_record_hash=h))
        emit(L.new_event("ORDER_REJECTED", environment="BROKER_DEMO", execution_mode=MODE,
                         strategy_id="demo_calibration", decision_id="DEMO-CALIB-1", symbol=a1.get("symbol"),
                         side="BUY", volume=a1.get("volume"), retcode=a1.get("broker_retcode"),
                         message=a1.get("broker_comment"), status="REJECTED", source_record_hash=h))

    # ---- attempt 2 (executed + closed) ----
    oreq, ores, creq, cres, summ = (data["order_request"], data["order_response"], data["close_request"],
                                    data["close_response"], data["summary"])
    if oreq and ores and summ:
        ho, hc = hashes["order_response"], hashes["close_response"]
        pos_id = f"DEMOPOS-{ores.get('order_id')}"
        emit(L.new_event("DECISION", environment="BROKER_DEMO", execution_mode=MODE,
                         strategy_id="demo_calibration", strategy_version="phase2", decision_id="DEMO-CALIB-2",
                         symbol=oreq.get("symbol"), side="BUY", status="TRADE",
                         message="fixed BUY experiment (attempt2 executed)", source_record_hash=hashes["order_request"]))
        emit(L.new_event("EXECUTION_REQUEST", environment="BROKER_DEMO", execution_mode=MODE,
                         strategy_id="demo_calibration", decision_id="DEMO-CALIB-2", symbol=oreq.get("symbol"),
                         side="BUY", order_type="MARKET", volume=oreq.get("volume"),
                         requested_price=ores.get("requested_price"), reference_bid=oreq.get("bid"),
                         reference_ask=oreq.get("ask"), reference_mid=oreq.get("mid"), spread=oreq.get("spread_price"),
                         request_timestamp=ores.get("send_timestamp_monotonic"),
                         response_timestamp=ores.get("broker_response_timestamp_monotonic"),
                         latency_ms=ores.get("response_latency_ms"), status="REQUESTED",
                         source_record_hash=hashes["order_request"]))
        emit(L.new_event("EXECUTION_RESPONSE", environment="BROKER_DEMO", execution_mode=MODE,
                         order_id=ores.get("order_id"), deal_id=ores.get("deal_id"), retcode=ores.get("broker_retcode"),
                         message=ores.get("broker_comment"), latency_ms=ores.get("response_latency_ms"),
                         fill_price=ores.get("actual_fill_price"), fill_volume=ores.get("volume_done"),
                         status="EXECUTED", source_record_hash=ho))
        emit(L.new_event("ORDER_ACCEPTED", environment="BROKER_DEMO", execution_mode=MODE,
                         order_id=ores.get("order_id"), deal_id=ores.get("deal_id"), retcode=ores.get("broker_retcode"),
                         message=ores.get("broker_comment"), status="ACCEPTED", source_record_hash=ho))
        emit(L.new_event("FILL", environment="BROKER_DEMO", execution_mode=MODE, decision_id="DEMO-CALIB-2",
                         position_id=pos_id, symbol=oreq.get("symbol"), side="BUY",
                         fill_price=ores.get("actual_fill_price"), fill_volume=ores.get("volume_done"),
                         requested_price=ores.get("requested_price"), slippage=summ.get("slippage_price"),
                         order_id=ores.get("order_id"), deal_id=ores.get("deal_id"),
                         fill_timestamp=ores.get("broker_response_timestamp_wallclock"), status="FILLED",
                         source_record_hash=ho))
        emit(L.new_event("POSITION_OPEN", environment="BROKER_DEMO", execution_mode=MODE, decision_id="DEMO-CALIB-2",
                         position_id=pos_id, symbol=oreq.get("symbol"), side="BUY", volume=oreq.get("volume"),
                         fill_price=ores.get("actual_fill_price"), status="OPEN", source_record_hash=ho))
        if creq:
            emit(L.new_event("POSITION_CLOSE_REQUEST", environment="BROKER_DEMO", execution_mode=MODE,
                             position_id=pos_id, requested_price=creq.get("close_requested_price"),
                             reference_bid=creq.get("close_bid"), reference_ask=creq.get("close_ask"),
                             reference_mid=creq.get("close_mid"), status="CLOSE_REQUESTED",
                             source_record_hash=hashes["close_request"]))
        if cres and summ:
            costs = summ.get("costs") or {}
            emit(L.new_event("POSITION_CLOSED", environment="BROKER_DEMO", execution_mode=MODE, position_id=pos_id,
                             symbol=oreq.get("symbol"), side="BUY", volume=oreq.get("volume"),
                             fill_price=cres.get("close_actual_price"), close_order_id=cres.get("close_order_id"),
                             retcode=cres.get("close_retcode"), message=cres.get("close_comment"),
                             latency_ms=cres.get("close_latency_ms"),
                             gross_pnl=costs.get("gross_pnl"), net_pnl=costs.get("net_pnl"),
                             commission=costs.get("commission") if isinstance(costs.get("commission"), (int, float)) else 0,
                             swap=costs.get("swap") if isinstance(costs.get("swap"), (int, float)) else 0,
                             status="CLOSED", source_record_hash=hc))
            emit(L.new_event("PNL", environment="BROKER_DEMO", execution_mode=MODE, position_id=pos_id,
                             gross_pnl=costs.get("gross_pnl"), net_pnl=costs.get("net_pnl"),
                             commission=costs.get("commission"), swap=costs.get("swap"),
                             message="n=1 calibration observation (NOT a statistical parameter)",
                             source_record_hash=hc))
    return emitted


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    evs = migrate()
    print("migrated events:", len(evs))
    for e in evs:
        print(" ", e["seq"], e["event_type"], e.get("status"), (e.get("source_record_hash") or "")[:10])
    print("verify:", L.verify_ledger())
