@echo off
REM V2 Control Panel supervisor — auto-restart on exit; logs to logs\v2_dashboard.log
REM Read-only · PAPER · localhost:8788 · never touches V1:8787/V1 terminal
setlocal
set "LOG=C:\AIQuant\research\hermes\trader_v2\logs\v2_dashboard.log"
set "PY=C:\AIQuant\.venv\Scripts\python.exe"
set "APP=C:\AIQuant\research\hermes\trader_v2\dashboard\server.py"
if not exist "C:\AIQuant\research\hermes\trader_v2\logs" mkdir "C:\AIQuant\research\hermes\trader_v2\logs"
:loop
echo [%date% %time%] start V2 dashboard (pid will follow) >> "%LOG%"
"%PY%" "%APP%" >> "%LOG%" 2>&1
echo [%date% %time%] V2 dashboard exited rc=%ERRORLEVEL%; restart in 5s >> "%LOG%"
timeout /t 5 /nobreak >nul
goto loop
