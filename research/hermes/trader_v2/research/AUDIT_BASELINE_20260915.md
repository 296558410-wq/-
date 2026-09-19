# V2_FULL_AUDIT_BASELINE — 2026-09-15T07:05+08:00 (2026-09-14T23:05Z)

## Repo / Git
- repo: C:\AIQuant (本地 git, 无 remote)
- branch: main
- HEAD (BASE_COMMIT): `fa935489743c69f6ecb3434dd55dc47ee92a7fc3`
- tag: `V2_FULL_AUDIT_BASELINE` → fa93548
- dirty files: **623**（绝大多数是 V1/V2 运行态产物：run_state/*.jsonl、decisions/*、reviews/*、state/*；非本次引入）

## Freeze / Hash
- V2 config_hash: `ad8ccb185686d3e88d8d121fc7280d644949abff8aca5453b588eba55493bd26`
- strategy_version: `hermes2-prompt/0.1.0` · agent1/0.1.0 · agent2/0.2.0-pit · hermes2/0.1.0 · paper/0.1.0 · ledger/1
- execution_mode: BROKER_DEMO（demo ******, magic=90003, 实例 fxtm_demo_01）

## V1 (只读基线)
- trader_summary 末行: 2026-09-14T22:47Z, FLAT(0 pos/0 ord), equity 2102.24, mid 4295.65, engine CYCLE_DONE
- V1 主终端 PID 1348 (C:\Program Files\ForexTime (FXTM) MT5\terminal64.exe)

## V2 运行态基线
- run 7a88: status=STOPPED (已 finalize), ledger verify=PASS, conservation=PASS, account 999.87
- ACTIVE.json: 7a88 stopped=true

## Broker / 其它
- MT5 实例 ×2: 1348(V1主) + 36460(fxtm_demo_01, portable)
- 端口: 8787(V1原) / 8788(V2) / 8790(V1升级) 均 listen
- Windows 计划任务: `\OpenClaw\hermes-tick-collect` (Ready, PT15M, poweshell wrapper, Interactive\surface, MultipleInstances=IgnoreNew, StartWhenAvailable=False)

## 本次任务前已修（本任务基线之上）
- `fa93548`: agent2/event_trigger news list+dict crash；router flag-file 回退；shadow_run metrics BROKER_DEMO
