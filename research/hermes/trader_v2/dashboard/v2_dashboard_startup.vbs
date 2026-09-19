' V2 Dashboard hidden autostart (logon). Launches supervisor without a console window.
Set sh = CreateObject("WScript.Shell")
sh.Run "cmd /c ""C:\AIQuant\research\hermes\trader_v2\dashboard\v2_dashboard_supervisor.cmd""", 0, False
