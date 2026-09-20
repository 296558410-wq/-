@echo off
setlocal
cd /d C:\AIQuant\research\hermes\trader_v3
if not exist logs mkdir logs
echo [%date% %time%] V3 calibration pilot start >> logs\calibration_pilot.log
C:\AIQuant\.venv\Scripts\python.exe -m foundation.calibration_pilot --run --n 10 >> logs\calibration_pilot.log 2>&1
echo [%date% %time%] V3 calibration pilot exit=%errorlevel% >> logs\calibration_pilot.log
endlocal
