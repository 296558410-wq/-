# V2 RUNTIME PROCESS / NETWORK AUDIT — 20260918 (P1 residual 3.3)

- window: 20s, samples: 4
- remote endpoints (ESTABLISHED): 29
- **model/API/Gateway endpoint hits: []**
- market-data endpoint hits: []
- python processes: 14

## remote endpoints
```
103.6.128.133:1953
103.6.128.163:1953
127.0.0.1:18789
127.0.0.1:49744
127.0.0.1:49745
127.0.0.1:50811
127.0.0.1:50813
127.0.0.1:52204
127.0.0.1:52851
127.0.0.1:53356
127.0.0.1:55192
127.0.0.1:56865
127.0.0.1:57226
127.0.0.1:59583
127.0.0.1:60357
127.0.0.1:61929
127.0.0.1:61930
127.0.0.1:61956
127.0.0.1:61957
127.0.0.1:64334
127.0.0.1:8748
127.0.0.1:8788
142.251.188.188:5228
203.119.238.190:443
203.119.245.36:443
4.145.79.81:443
59.82.158.203:443
60.204.2.5:443
[2408:871a:3001:3000::8]:443
```

## python processes
```
"python.exe","42524","Console","1","4,052 K"
"python.exe","38924","Console","1","50,448 K"
"python.exe","30524","Console","1","4,056 K"
"python.exe","43396","Console","1","18,436 K"
"python.exe","33232","Console","1","1,172 K"
"python.exe","4044","Console","1","5,732 K"
"python.exe","22096","Console","1","1,180 K"
"python.exe","42140","Console","1","14,640 K"
"python.exe","43444","Console","1","4,048 K"
"python.exe","42344","Console","1","31,220 K"
"python.exe","1328","Console","1","1,176 K"
"python.exe","56664","Console","1","19,316 K"
"python.exe","48944","Console","1","4,260 K"
"python.exe","53360","Console","1","15,196 K"
```

## 结论
- MODEL/GATEWAY 端点命中数: 0  → PASS(无)
- 说明: 本审计在当前锁定状态（无 run 运行）采集；Shadow 阶段应附于每次 cycle。BROKER_ORDER_SENT=FALSE。
