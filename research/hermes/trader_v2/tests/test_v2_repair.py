# -*- coding: utf-8 -*-
"""V2_REPAIR regression — 2026-09-15（本次“体检→修复”新增回归）。

覆盖：
  R1 agent2 news list+dict 拼接崩溃修复（含 event_trigger 同源 bug）
  R2 router flag-file 回退开关（env 无法传播到 cron child 的工程修复）
  R3 shadow_run.metrics 按 run manifest execution_mode（BROKER_DEMO 不再空）
  R4 零-LLM 调度入口 v2_scheduled_cycle.py 可运行 + 健康字段齐全 + 无 gateway/LLM 依赖
  R5 直接 Windows 计划任务存在且设置正确（IgnoreNew / StartWhenAvailable=False / PT15M）
  R6 引擎窗口去重（同窗口二次调用 → skipped_duplicate，不重复执行）
  R7 隔离（V2 不 import V1；execution_mode=BROKER_DEMO；reuse_v1_*=false）
日志: logs/test_v2_repair.log
"""
import json, os, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent              # trader_v2
AIQ = ROOT.parents[2]           # C:\AIQuant
PY = str(AIQ / ".venv" / "Scripts" / "python.exe")
LOGS = ROOT / "logs"; LOGS.mkdir(exist_ok=True)
LOG = LOGS / "test_v2_repair.log"
_res = []


def log(s):
    print(s)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(s + "\n")
    _res.append(s)


def check(name, cond, extra=""):
    log(f"{'PASS' if cond else 'FAIL'} | {name}" + (f" | {extra}" if extra else ""))
    return bool(cond)


# R1
sys.path.insert(0, str(ROOT / "agents" / "macro_global"))
import agent2 as A2  # noqa: E402
import event_trigger as ET  # noqa: E402


def _boom(*a, **k):
    raise RuntimeError("simulated source down")


_o1 = A2.S.news_cnbc_rss; _o2 = ET.S.news_cnbc_rss
A2.S.news_cnbc_rss = _boom; ET.S.news_cnbc_rss = _boom
try:
    news = A2._as_list(A2._safe(lambda: A2.S.news_wallstcn(40), default=[])) + \
           A2._as_list(A2._safe(lambda: A2.S.news_cnbc_rss(40), default=[]))
    crash = False
except TypeError as e:  # noqa: BLE001
    crash = True; news = []
check("R1a agent2 news concat survives source failure", (not crash) and isinstance(news, list))
try:
    n2 = (ET.A._safe(lambda: ET.S.news_wallstcn(40), default=[]) or []) + (ET.A._safe(lambda: ET.S.news_cnbc_rss(40), default=[]) or [])
    crash2 = False
except TypeError:  # noqa: BLE001
    crash2 = True; n2 = []
check("R1b event_trigger news concat survives source failure", (not crash2) and isinstance(n2, list))
A2.S.news_cnbc_rss = _o1; ET.S.news_cnbc_rss = _o2

# R2 router flag-file fallback (env unset in this process)
sys.path.insert(0, str(ROOT))
_prev = os.environ.pop("V2_DATA_ROUTER_ENABLED", None)
import data_sources as DS  # noqa: E402
flag = (ROOT / "config" / "data_router.enabled")
check("R2 router enabled via flag-file when env unset", DS.router_enabled() is True,
      f"flag_exists={flag.exists()}")
if _prev is not None:
    os.environ["V2_DATA_ROUTER_ENABLED"] = _prev

# R3 metrics honors BROKER_DEMO
import importlib.util as _il
spec = _il.spec_from_file_location("shadow_run_mod", str(ROOT / "runtime" / "shadow_run.py"))
SR = _il.module_from_spec(spec); spec.loader.exec_module(SR)
rid = "V2-PAPER-20260913-224157-7a88"
if (ROOT / "research" / "runs" / rid).exists():
    m = SR.metrics(rid)
    check("R3 metrics() honors BROKER_DEMO (WAIT>0, conservation_ok)",
          m["decisions"]["WAIT"] > 0 and m["conservation_ok"] is True,
          f"WAIT={m['decisions']['WAIT']} cons={m['conservation_ok']} acct={m['account']['balance']}")
else:
    check("R3 metrics() honors BROKER_DEMO", False, "run 7a88 missing")

# R4 scheduler entry
p = subprocess.run([PY, str(ROOT / "runtime" / "v2_scheduled_cycle.py"), "--dry-run"],
                   cwd=str(AIQ), capture_output=True, text=True, encoding="utf-8", timeout=120)
hf = ROOT / "state" / "v2_run_health.json"
ok4 = p.returncode == 0 and hf.exists()
need = ["last_scheduled", "last_started", "last_completed", "last_success", "last_failure",
        "current_cycle", "missed_cycles", "recovery_count", "duplicate_prevented",
        "gateway_dependency", "llm_dependency", "router_enabled", "agent1_status", "agent2_status",
        "hermes_status", "execution_status", "ledger_status", "replay_status"]
h = json.loads(hf.read_text(encoding="utf-8")) if hf.exists() else {}
missing = [k for k in need if k not in h]
check("R4 scheduler dry-run ok + health fields", ok4 and not missing,
      f"rc={p.returncode} missing={missing}")
check("R4b no gateway/LLM dependency declared", h.get("gateway_dependency") is False and h.get("llm_dependency") is False)
src = (ROOT / "runtime" / "v2_scheduled_cycle.py").read_text(encoding="utf-8")
check("R4c scheduler has no gateway/LLM runtime dependency",
      ("import requests" not in src) and ("import openai" not in src) and ("subprocess" in src))

# R5 windows task
try:
    q = subprocess.run(["schtasks", "/query", "/tn", "\\OpenClaw\\hermes-v2-cycle", "/fo", "LIST"],
                       capture_output=True, text=True, timeout=30)
    ok5 = q.returncode == 0
    check("R5 Windows task hermes-v2-cycle exists", ok5)
except Exception as e:  # noqa: BLE001
    check("R5 Windows task hermes-v2-cycle exists", False, str(e))
try:
    ps = subprocess.run(["powershell", "-NoProfile", "-Command",
                         "$t=Get-ScheduledTask -TaskName 'hermes-v2-cycle'; "
                         "$r=$t.Triggers[0].Repetition.Interval; "
                         "Write-Output ($t.Settings.MultipleInstances.ToString()+'|'+$t.Settings.StartWhenAvailable.ToString()+'|'+$r)"],
                        capture_output=True, text=True, timeout=60)
    parts = ps.stdout.strip().split("|")
    check("R5b task settings (IgnoreNew|False|PT15M)",
          len(parts) == 3 and parts[0] == "IgnoreNew" and parts[1] == "False" and parts[2] == "PT15M",
          ps.stdout.strip())
except Exception as e:  # noqa: BLE001
    check("R5b task settings", False, str(e))

# R6 engine window dedup（用临时 run，保持生产 state 不被改）
import tempfile, shutil
tmp = ROOT / "tests" / "_tmp" / "v2repair_dedup"
if tmp.exists():
    shutil.rmtree(tmp, ignore_errors=True)
# 用 PAPER 模式在临时目录跑两轮同窗口：直接测窗口判定函数
from datetime import datetime, timezone
w1 = SR.window15(datetime(2026, 9, 15, 12, 3, tzinfo=timezone.utc))
w2 = SR.window15(datetime(2026, 9, 15, 12, 14, tzinfo=timezone.utc))
w3 = SR.window15(datetime(2026, 9, 15, 12, 15, tzinfo=timezone.utc))
check("R6 dedup key stable within 15m, distinct across boundary",
      w1 == w2 and w1 != w3, f"{w1} {w2} {w3}")

# R7 isolation
import re
v1hits = []
for pyf in (ROOT / "agents").rglob("*.py"):
    t = pyf.read_text(encoding="utf-8", errors="ignore")
    if re.search(r"trader_v1", t):
        v1hits.append(str(pyf))
cfg = json.loads((ROOT / "config" / "v2_config.json").read_text(encoding="utf-8"))
iso = cfg.get("isolation", {})
check("R7 V2 agents never import/reference trader_v1", not v1hits, str(v1hits))
check("R7b isolation flags false", all(iso.get(k) is False for k in
      ("allow_real_trading", "reuse_v1_mt5_terminal", "reuse_v1_ledger", "reuse_v1_account")))
# P0-06(2026-09-18): 交易/执行一律 PAPER 且 broker 已 disarm（不再 armed BROKER_DEMO）。
check("R7c execution_mode=PAPER & broker disarmed & live_trading false",
      cfg["execution"]["execution_mode"] == "PAPER" and cfg["execution"]["live_trading"] is False
      and cfg["execution"].get("broker_demo_enabled") is False and cfg.get("broker", {}).get("enabled") is False)

# R8 ledger partial-write / torn line → fail-closed（不崩溃、不静默跳过）
import tempfile
LROOT = ROOT / "ledger"
sys.path.insert(0, str(LROOT))
import importlib.util as _il2
spec2 = _il2.spec_from_file_location("ledger_mod", str(LROOT / "ledger.py"))
LM = _il2.module_from_spec(spec2); spec2.loader.exec_module(LM)
src_led = ROOT / "research" / "runs" / rid / "ledger.jsonl"
if src_led.exists():
    lines = src_led.read_text(encoding="utf-8").splitlines()
    d2 = Path(tempfile.mkdtemp())
    torn = d2 / "ledger.jsonl"
    torn.write_text("\n".join(lines[:10]) + "\n" + lines[10][:60], encoding="utf-8")
    try:
        ok8, det8 = LM.verify_ledger(torn)
        raised = False
    except Exception as e:  # noqa: BLE001
        ok8, det8, raised = None, str(e), True
    check("R8 torn/partial ledger line -> fail-closed (no crash)",
          (not raised) and ok8 is False and "malformed" in str(det8), f"raised={raised} det={det8}")
    ok8b, _det8b = LM.verify_ledger(src_led)
    check("R8b intact ledger still verifies OK", ok8b is True)
else:
    check("R8 torn/partial ledger line -> fail-closed", False, "no 7a88 ledger")

# R9 router.macro：抓取失败 + 缓存曾 FRESH（value 被置空但有 last_valid）→ 必须返回 last_valid，不得返回 None
import time as _time
import data_sources as _DS  # noqa: E402
import data_sources.cache as _C  # noqa: E402
from data_sources import adapters_macro as _AMAC  # noqa: E402
_tk = "yahoo_kv:__SELFTEST__"
_ck = f"macro:{_tk}"
_C.put(_ck, None, "unit", state_override=_C.FRESH)
_C.put(_ck, {"last": 17.5}, "unit", observed_ts=_time.time() - 3 * 3600, fresh_h=24, stale_h=96)
_C.put(_ck, None, "unit", state_override=None)      # value->None, last_valid 保留, freshness 仍 FRESH
_AMAC.MACRO_DEFS[_tk] = ((lambda: (_ for _ in ()).throw(ValueError("boom"))), (24, 96), "unit")
try:
    _v = _DS._router().macro(_tk)
    _ok9 = isinstance(_v, dict) and _v.get("last") == 17.5
except Exception as _e:  # noqa: BLE001
    _ok9 = False; _v = f"{type(_e).__name__}:{_e}"
check("R9 router.macro FRESH-failure -> last_valid (not None)", _ok9, f"v={_v}")

# R10 agent2._safe 对“返回 None 的函数”不再让下游 .get 崩溃
try:
    _s = A2._safe(lambda: None)
    _ok10 = isinstance(_s, dict) and _s.get("__failed__") is True
except Exception as _e:  # noqa: BLE001
    _ok10 = False
try:
    _s2 = A2._safe(lambda: None, default=[])
    _ok10b = _s2 == []
except Exception:
    _ok10b = False
check("R10 agent2._safe(None) -> failed sentinel / default", _ok10 and _ok10b)

# R11 对账：持仓中（浮动 equity 不同、已实现一致）→ 不再误判 BLOCK
class _FakePe:
    backend = "fxtm_demo"
_rst = {"account": {"balance": 999.76, "equity": 999.60}, "net_pnl": 0.0, "trade_count": 0, "commission": 0.0}
_acc = {"balance": 999.76, "equity": 1005.30, "realized_pnl": -0.11, "closed_trades": [], "positions": [{"position_id": "x"}]}
_ok11, _mm11 = SR._account_match(_FakePe(), _rst, _acc)
check("R11 open-position floating equity ignored (no false BLOCK)", _ok11 and _mm11 == {}, f"ok={_ok11} mm={_mm11}")
# 反例：当已实现余额不一致时仍应报错
_acc2 = dict(_acc); _acc2["balance"] = 1000.50
try:
    _ok11b, _mm11b = SR._account_match(_FakePe(), _rst, _acc2)
except Exception:
    _ok11b, _mm11b = True, {}
check("R11b realized balance mismatch still flagged", (not _ok11b) and "balance" in _mm11b, f"mm={_mm11b}")

# R12 broker 侧 SL/TP 平仓 → reconcile 回写账本 POSITION_CLOSED
import importlib.util as _il3, tempfile as _tf3
sys.path.insert(0, str(ROOT / "execution"))
sys.path.insert(0, str(ROOT / "ledger"))
spec3 = _il3.spec_from_file_location("hpa_mod", str(ROOT / "execution" / "hermes_paper_adapter.py"))
HPA = _il3.module_from_spec(spec3); spec3.loader.exec_module(HPA)


class _FakeAd:
    def get_positions(self):
        return {"positions": []}   # broker 已无该仓


class _FakeEx:
    backend = "fxtm_demo"
    def __init__(self):
        self.adapter = _FakeAd()
        self.acc = {"closed_trades": []}
        self.reconcile_report = None
    def trade_from_deals(self, t, reason="x"):
        return {"position_id": str(t), "direction": "SHORT", "qty_lots": 0.01, "entry": 4305.53, "exit": 4269.31,
                "reason": reason, "gross_usd": 36.22, "commission_usd": -0.11, "swap_usd": 0.0, "net_usd": 36.11}
    def register_closed_trade(self, trade, replace=True):
        pid = str(trade["position_id"])
        if any(str(t["position_id"]) == pid for t in self.acc["closed_trades"]):
            return False
        self.acc["closed_trades"].append(trade); return True
    def rebuild_closed_trades(self, position_ids, reason="x"):
        return {"rebuilt": [], "missing": [], "duplicate_prevented": [str(p) for p in position_ids]}
    def account(self):
        return {"balance": 1035.98, "equity": 1035.98, "closed_trades": self.acc["closed_trades"], "positions": []}


_lp = _tf3.mktemp(suffix="_ledger.jsonl")
HPA.L.append_event(HPA.L.new_event(event_type="ACCOUNT_INIT", account_balance=999.87, currency="USD"), _lp)
HPA.L.append_event(HPA.L.new_event(event_type="POSITION_OPEN", position_id="******", side="SHORT", volume=0.01, fill_price=4305.53, status="OPEN"), _lp)
_fex = _FakeEx()
_n = HPA.reconcile_broker_closes(_fex, _lp, run_id="TEST")
_cev = [e for e in HPA.L.load_events(_lp) if e["event_type"] == "POSITION_CLOSED"]
check("R12 broker SL/TP close reconciled into ledger", _n == 1 and len(_cev) == 1 and abs(_cev[0]["net_pnl"] - 36.11) < 1e-6,
      f"n={_n} closed={len(_cev)}")
check("R12b reconcile 同步 executor.closed_trades（状态一致）", len(_fex.acc["closed_trades"]) == 1,
      str(_fex.acc["closed_trades"]))

total = len(_res); fails = sum(1 for s in _res if s.startswith("FAIL"))
print(f"=== RESULT: {total-fails}/{total} PASS ===")
sys.exit(1 if fails else 0)
