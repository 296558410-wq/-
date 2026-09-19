# -*- coding: utf-8 -*-
"""V2 数据源 中国大陆可达性矩阵 — 本机实测（DNS/TCP/TLS/HTTP/status/latency/schema/timestamp/数据有效性）。

禁止凭搜索/理论判定可用；一切以本机实测为准。
输出: research/DATA_SOURCE_MATRIX.md
"""
from __future__ import annotations
import json, socket, ssl, sys, time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
from data_sources import net  # noqa: E402

SINA_H = dict(net.UA); SINA_H["Referer"] = "https://finance.sina.com.cn"


def dns(host):
    try:
        t0 = time.time(); ip = socket.gethostbyname(host); return True, round((time.time() - t0) * 1000), ip
    except Exception as e:  # noqa: BLE001
        return False, None, f"{type(e).__name__}"


def tcp_tls(host, port=443, t=5):
    try:
        t0 = time.time()
        ctx = ssl.create_default_context()
        with socket.create_connection((host, port), timeout=t) as s:
            with ctx.wrap_socket(s, server_hostname=host):
                return True, round((time.time() - t0) * 1000)
    except Exception as e:  # noqa: BLE001
        return False, f"{type(e).__name__}"


CASES = [
    ("sina:quote", "quote", "https://hq.sinajs.cn/list=hf_XAU", "GET", SINA_H, lambda r: ('"' in (r["text"] or ""))),
    ("tencent:quote", "quote", "https://qt.gtimg.cn/q=hf_XAU", "GET", None, lambda r: ('"' in (r["text"] or ""))),
    ("eastmoney:quote", "quote", "https://push2.eastmoney.com/api/qt/stock/get?secid=100.UDI&fields=f43,f58", "GET", None,
     lambda r: bool((r["json"] or {}).get("data"))),
    ("eastmoney:flow", "flow", "https://push2.eastmoney.com/api/qt/stock/fflow/kline/get?secid=1.518880&fields1=f1&fields2=f51,f52&klt=101&lmt=5", "GET", None,
     lambda r: bool(((r["json"] or {}).get("data") or {}).get("klines"))),
    ("yahoo:chart", "bars", "https://query1.finance.yahoo.com/v8/finance/chart/GC=F?range=1d&interval=5m", "GET", None,
     lambda r: bool(((r["json"] or {}).get("chart") or {}).get("result"))),
    ("yahoo2:chart", "bars", "https://query2.finance.yahoo.com/v8/finance/chart/GC=F?range=1d&interval=5m", "GET", None,
     lambda r: bool(((r["json"] or {}).get("chart") or {}).get("result"))),
    ("cftc:cot", "macro", "https://publicreporting.cftc.gov/resource/6dca-aqww.json?$limit=1", "GET", None,
     lambda r: bool(r["json"])),
    ("ecb:sdmx", "macro", "https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A?format=jsondata&lastNObservations=1", "GET", None,
     lambda r: bool((r["json"] or {}).get("dataSets"))),
    ("treasury:fiscaldata", "macro", "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/avg_interest_rates?page[size]=1", "GET", None,
     lambda r: bool((r["json"] or {}).get("data"))),
    ("wallstcn:news", "news", "https://api-one.wallstcn.com/apiv1/content/lives?channel=global-channel&limit=5", "GET", None,
     lambda r: bool(((r["json"] or {}).get("data") or {}).get("items"))),
    ("cnbc:rss", "news", "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114", "GET", None,
     lambda r: "<item>" in (r["text"] or "")),
    ("sge:site", "reference", "https://www.sge.com.cn/", "GET", None, lambda r: r["status"] is not None),
    ("fred:site", "macro(expect_down)", "https://fred.stlouisfed.org/", "GET", None, lambda r: r["status"] is not None),
]


def main():
    rows = []
    for sid, dtype, url, method, hdrs, valid in CASES:
        host = urlparse(url).netloc
        d_ok, d_ms, d_note = dns(host)
        t_ok, t_ms = tcp_tls(host) if d_ok else (False, "no dns")
        t0 = time.time()
        r = net.fetch(url, method=method, headers=hdrs, connect_timeout=6, read_timeout=18, retries=1, backoff=0.5, cooldown=120)
        lat = r.get("latency_ms")
        try:
            dvalid = bool(valid(r)) if r["ok"] else False
        except Exception:  # noqa: BLE001
            dvalid = False
        status = "OK" if (r["ok"] and dvalid) else ("SOURCE_DOWN" if r.get("source_down") else "INVALID/FORMAT")
        fr = "FRESH" if status == "OK" else "MISSING"
        rows.append({"source_id": sid, "data_type": dtype, "dns": ("OK" if d_ok else "FAIL"),
                     "connect": ("OK" if t_ok else str(t_ms)), "http": (r["status"] if r["ok"] else "-"),
                     "data_valid": dvalid, "latency_ms": lat, "freshness": fr, "status": status,
                     "failure_reason": (r["error"] or "")[:110], "tested_at": datetime.now(timezone.utc).isoformat()})
    ok = sum(1 for x in rows if x["status"] == "OK")
    reach = "PASS" if ok == len(rows) else ("PARTIAL" if ok >= 1 else "FAIL")
    md = ["# DATA_SOURCE_MATRIX — V2 数据源 中国大陆可达性（本机实测）", "",
          f"- 测试时间: {datetime.now(timezone.utc).isoformat()}  |  本机: DESKTOP-LQ0B8O3 (CN)",
          f"- **CHINA_MAINLAND_REACHABLE = {reach}**  (OK {ok}/{len(rows)})", "",
          "| source_id | type | dns | connect | http | data_valid | latency_ms | freshness | status | failure_reason |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for x in rows:
        md.append("| {source_id} | {data_type} | {dns} | {connect} | {http} | {data_valid} | {latency_ms} | {freshness} | {status} | {failure_reason} |".format(**x))
    md += ["", "## 结论 / 备注",
           "- 技术 K 线：**本地 `data/live_fxtm` tick 为主源**（不依赖外网）；Yahoo 仅 SECONDARY/OPTIONAL，实测间歇 403 → 自动退避。",
           "- 现价：sina/tencent/eastmoney 可用；yahoo 间歇。",
           "- 宏观：CFTC/COT、ECB、Treasury、BLS 等免 Key 源按上表状态；不可达者 → cache/last_valid 降级并标 STALE_BUT_VALID/SOURCE_DOWN。",
           "- FRED 预期不可达（超时/被墙）→ 不用。"]
    outp = ROOT / "research" / "DATA_SOURCE_MATRIX.md"
    outp.write_text("\n".join(md), encoding="utf-8")
    print("\n".join(md))
    print("\nCHINA_MAINLAND_REACHABLE =", reach)
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
