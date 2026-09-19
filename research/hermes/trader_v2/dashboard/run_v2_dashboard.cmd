@echo off
REM V2 Control Panel launcher (read-only, PAPER, localhost:8788; never touches V1:8787)
setlocal
set V2_DASH_PORT=8788
"C:\AIQuant\.venv\Scripts\python.exe" "C:\AIQuant\research\hermes\trader_v2\dashboard\server.py"
endlocal
