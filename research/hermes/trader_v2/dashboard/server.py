# -*- coding: utf-8 -*-
"""V2 Dashboard — 服务端（READ-ONLY, localhost）。

- 端口默认 8788（**绝不使用 V1 的 8787**）；可用环境变量 V2_DASH_PORT 覆盖。
- FastAPI + SSE 实时推送（比 V1 的 10s 轮询更强）。
- 只读 snapshot；不写任何东西；不下任何单；不 import V1。
启动:
  C:\\AIQuant\\.venv\\Scripts\\python.exe research\\hermes\\trader_v2\\dashboard\\server.py
"""
from __future__ import annotations
import asyncio, json, os, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import datasource as DS  # noqa: E402

from fastapi import FastAPI  # noqa: E402
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse, PlainTextResponse  # noqa: E402

PORT = int(os.environ.get("V2_DASH_PORT", "8788"))
if PORT == 8787:
    raise SystemExit("REFUSED: 8787 is V1's port. Use another port (default 8788).")

app = FastAPI(title="Hermes V2 Control Panel", docs_url=None, redoc_url=None)
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
        return JSONResponse({"error": f"{type(e).__name__}: {e}"}, status_code=200)


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
    print(f"[V2 DASHBOARD] http://127.0.0.1:{PORT}  (read-only · PAPER · never touches V1:8787)")
    uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="warning")


if __name__ == "__main__":
    main()
