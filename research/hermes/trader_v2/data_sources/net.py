# -*- coding: utf-8 -*-
"""V2 Data Source Router — HTTP 门卫：connect/read timeout, retry, 指数退避, per-host cooldown, recovery probe。

铁律:
- 禁止 `while True: retry()`。重试有上限 + 退避；源挂了进 cooldown（冷却期内直接 SOURCE_DOWN，不再打网络）。
- 冷却期过后允许一次 recovery probe（下一次真实请求即探测），成功即自动复位。
- 不因某源失败阻塞调用方（返回结构化结果，不抛穿透）。
"""
from __future__ import annotations
import time
from urllib.parse import urlparse
import requests

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36"}

_DOWN: dict[str, float] = {}   # host -> until_ts
STATS: dict[str, dict] = {}    # host -> counters


def host_of(url: str) -> str:
    return urlparse(url).netloc


def is_cooling(host: str) -> tuple[bool, float]:
    until = _DOWN.get(host)
    if until and time.time() < until:
        return True, round(until - time.time(), 1)
    if until and time.time() >= until:
        _DOWN.pop(host, None)  # cooldown expired -> allow recovery probe
    return False, 0.0


def _stat(host):
    s = STATS.setdefault(host, {"ok": 0, "fail": 0, "consec_fail": 0, "last_error": None, "last_ok_at": None})
    return s


def fetch(url, *, headers=None, params=None, method="GET", json_body=None,
          connect_timeout=5, read_timeout=15, retries=2, backoff=0.5, cooldown=300,
          host=None) -> dict:
    """结构化 HTTP 结果。host 可覆盖（多 endpoint 同源）。

    返回: {ok, status, text, json, latency_ms, error, attempts, source_down}
    """
    host = host or host_of(url)
    cooling, rem = is_cooling(host)
    st = _stat(host)
    if cooling:
        return {"ok": False, "status": None, "text": None, "json": None, "latency_ms": 0,
                "error": f"SOURCE_DOWN(cooldown {rem}s)", "attempts": 0, "source_down": True}
    hdrs = dict(UA); hdrs.update(headers or {})
    t0 = time.time()
    last = None
    for attempt in range(retries + 1):
        try:
            to = (connect_timeout, read_timeout)
            if method == "POST":
                r = requests.post(url, headers=hdrs, params=params, json=json_body, timeout=to)
            else:
                r = requests.get(url, headers=hdrs, params=params, timeout=to)
            r.raise_for_status()
            lat = int((time.time() - t0) * 1000)
            j = None
            try:
                j = r.json()
            except Exception:  # noqa: BLE001
                pass
            st["ok"] += 1; st["consec_fail"] = 0; st["last_ok_at"] = time.time()
            return {"ok": True, "status": r.status_code, "text": r.text, "json": j,
                    "latency_ms": lat, "error": None, "attempts": attempt + 1, "source_down": False}
        except Exception as e:  # noqa: BLE001
            last = f"{type(e).__name__}:{str(e)[:120]}"
            if attempt < retries:
                time.sleep(backoff * (2 ** attempt))
    st["fail"] += 1; st["consec_fail"] += 1; st["last_error"] = last
    _DOWN[host] = time.time() + cooldown
    return {"ok": False, "status": None, "text": None, "json": None,
            "latency_ms": int((time.time() - t0) * 1000), "error": last,
            "attempts": retries + 1, "source_down": True}


def reset_cooldowns():
    _DOWN.clear()


def mark_down(host: str, cooldown: float = 300.0) -> None:
    """显式把 host 置入冷却（供 macro 等非 net.fetch 路径复用同一套 per-host cooldown）。"""
    if not host:
        return
    _DOWN[host] = max(_DOWN.get(host, 0.0), time.time() + float(cooldown))


def cooldowns() -> dict:
    return {h: round(u - time.time(), 1) for h, u in _DOWN.items()}


def stats() -> dict:
    return {h: dict(v, last_ok_at=(round(v["last_ok_at"], 1) if v["last_ok_at"] else None)) for h, v in STATS.items()}
