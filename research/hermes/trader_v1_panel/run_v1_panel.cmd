@echo off
REM V1 Control Panel (upgraded) launcher. Read-only. Does NOT touch V1 / 8787.
setlocal
set V1_PANEL_PORT=8790
"C:\AIQuant\.venv\Scripts\python.exe" "C:\AIQuant\research\hermes\trader_v1_panel\server.py"
endlocal
