# -*- coding: utf-8 -*-
"""V1 控制面板 — 服务端（READ-ONLY, localhost:8790）。

- 端口默认 8790（**绝不使用 V1 的 8787**；也避开 V2 的 8788）。环境变量 V1_PANEL_PORT 可覆盖。
- 只读 V1 产物，不写任何东西，不 import V1 代码，不打开 MT5。
- SSE 实时推送。
启动: C:\\AIQuant\\.venv\\Scripts\\python.exe research\\hermes\\trader_v1_panel\\server.py
"""
from __future__ import annotations
import asyncio, json, os, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import datasource as DS  # noqa: E402

from fastapi import FastAPI  # noqa: E402
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse, PlainTextResponse  # noqa: E402

PORT = int(os.environ.get("V1_PANEL_PORT", "8790"))
if PORT in (8787, 8788):
    raise SystemExit(f"REFUSED: {PORT} is reserved (8787=V1 panel, 8788=V2 panel).")

app = FastAPI(title="Hermes V1 Control Panel", docs_url=None, redoc_url=None)
STATIC = HERE / "static"
_NC = {"Cache-Control": "no-store, no-cache, must-revalidate", "Pragma": "no-cache"}


@app.get("/", response_class=HTMLResponse)
def index():
    return HTMLResponse((STATIC / "index.html").read_text(encoding="utf-8"), headers=_NC)


@app.get("/style.css")
def css():
    return PlainTextResponse((STATIC / "style.css").read_text(encoding="utf-8"), media_type="text/css", headers=_NC)


@app.get("/app.js")
def js():
    return PlainTextResponse((STATIC / "app.js").read_text(encoding="utf-8"), media_type="application/javascript", headers=_NC)


@app.get("/api/snapshot")
def api_snapshot():
    try:
        return JSONResponse(DS.build_snapshot())
    except Exception as e:  # noqa: BLE001
        return JSONResponse({"error": f"{type(e).__name__}: {e}"})


@app.get("/api/stream")
async def api_stream():
    async def gen():
        last = None
        while True:
            try:
                s = DS.build_snapshot()
                body = json.dumps(s, ensure_ascii=False)
                if body != last:
                    last = body
                    yield "event: snap\ndata: " + body + "\n\n"
                else:
                    yield ": keepalive\n\n"
            except Exception as e:  # noqa: BLE001
                yield "event: err\ndata: " + json.dumps({"error": str(e)}) + "\n\n"
            await asyncio.sleep(2.0)
    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


def main():
    import uvicorn
    print(f"[V1 PANEL] http://127.0.0.1:{PORT}  (read-only · 不碰 V1 代码/8787)")
    uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="warning")


if __name__ == "__main__":
    main()
