# V2 G3 数据层冻结清单 — 20260917

- label: `post-domestic-rewire-v2`
- ts_utc: 2026-09-17T10:53:18.858395+00:00
- git: `8d997fb` (branch fix/v2-full-system-repair-20260917)
- versions: `{"strategy_version": "hermes2-prompt/0.1.0", "agent1_version": "agent1/0.1.0", "agent2_version": "agent2/0.2.0-pit", "hermes_version": "hermes2/0.1.0", "paper_engine_version": "paper/0.1.0", "ledger_version": "ledger/1"}`
- schema: pit=`pit/1` input_snapshot=`input_snapshot/1`
- flags: `{"FORWARD_VALIDATION_ALLOWED": {"exists": false, "value": null}, "SHADOW_ALLOWED": {"exists": true, "path": "state\\SHADOW_ALLOWED", "value": "true"}, "data_router.enabled": {"exists": true, "path": "config\\data_router.enabled", "value": "true"}}`

## Router 历史源
```
{
 "5m": [
  [
   "mt5",
   "primary"
  ],
  [
   "local_fxtm",
   "secondary"
  ],
  [
   "yahoo",
   "tertiary"
  ]
 ],
 "15m": [
  [
   "mt5",
   "primary"
  ],
  [
   "local_fxtm",
   "secondary"
  ],
  [
   "yahoo",
   "tertiary"
  ]
 ],
 "60m": [
  [
   "mt5",
   "primary"
  ],
  [
   "local_fxtm",
   "secondary"
  ],
  [
   "yahoo",
   "tertiary"
  ]
 ],
 "4h": [
  [
   "mt5",
   "primary"
  ],
  [
   "local_fxtm",
   "secondary"
  ],
  [
   "yahoo",
   "tertiary"
  ]
 ],
 "1d": [
  [
   "mt5",
   "primary"
  ],
  [
   "local_fxtm",
   "secondary"
  ],
  [
   "yahoo",
   "tertiary"
  ]
 ]
}
```
## 数据源注册
```
{
 "HISTORY_SOURCES": {
  "5m": [
   [
    "mt5",
    "primary"
   ],
   [
    "local_fxtm",
    "secondary"
   ],
   [
    "yahoo",
    "tertiary"
   ]
  ],
  "15m": [
   [
    "mt5",
    "primary"
   ],
   [
    "local_fxtm",
    "secondary"
   ],
   [
    "yahoo",
    "tertiary"
   ]
  ],
  "60m": [
   [
    "mt5",
    "primary"
   ],
   [
    "local_fxtm",
    "secondary"
   ],
   [
    "yahoo",
    "tertiary"
   ]
  ],
  "4h": [
   [
    "mt5",
    "primary"
   ],
   [
    "local_fxtm",
    "secondary"
   ],
   [
    "yahoo",
    "tertiary"
   ]
  ],
  "1d": [
   [
    "mt5",
    "primary"
   ],
   [
    "local_fxtm",
    "secondary"
   ],
   [
    "yahoo",
    "tertiary"
   ]
  ]
 },
 "QUOTE_SOURCES": {
  "gold_spot": [
   [
    "mt5",
    "XAUUSD"
   ],
   [
    "sina",
    "hf_XAU"
   ],
   [
    "tencent",
    "hf_XAU"
   ],
   [
    "local_fxtm",
    null
   ]
  ],
  "gold_comex": [
   [
    "sina",
    "hf_GC"
   ],
   [
    "tencent",
    "hf_GC"
   ]
  ],
  "silver": [
   [
    "mt5",
    "XAGUSD"
   ],
   [
    "sina",
    "hf_SI"
   ],
   [
    "tencent",
    "hf_SI"
   ]
  ],
  "dxy": [
   [
    "sina",
    "DINIW"
   ],
   [
    "tencent",
    "usDXY"
   ]
  ],
  "ust10y": [
   [
    "tencent",
    "usUST"
   ]
  ],
  "vix": [
   [
    "sina",
    "znb_VIX"
   ],
   [
    "tencent",
    "usVIX"
   ]
  ],
  "gld": [
   [
    "tencent",
    "usGLD"
   ]
  ],
  "tip": [
   [
    "tencent",
    "usTIP"
   ]
  ]
 },
 "SOURCE_META": {
  "mt5": {
   "data_type": "bars/quote",
   "access": "local MT5 (fxtm_demo_01, read-only)",
   "timeout": null,
   "retry": 0,
   "backoff": 0,
   "freshness_rule": "tick/bar<15m",
   "validation": "validate_bars",
   "status": "ACTIVE"
  },
  "local_fxtm": {
   "data_type": "bars/quote",
   "access": "local parquet (data/live_fxtm)",
   "timeout": null,
   "retry": 0,
   "backoff": 0,
   "freshness_rule": "tick<15m",
   "validation": "validate_bars",
   "status": "ACTIVE"
  },
  "sina": {
   "data_type": "quote",
   "access": "https hq.sinajs.cn",
   "timeout": 10,
   "retry": 1,
   "backoff": 0.4,
   "freshness_rule": "<5m",
   "validation": "validate_quote",
   "status": "ACTIVE"
  },
  "tencent": {
   "data_type": "quote",
   "access": "https qt.gtimg.cn",
   "timeout": 10,
   "retry": 1,
   "backoff": 0.4,
   "freshness_rule": "<5m",
   "validation": "validate_quote",
   "status": "ACTIVE"
  },
  "eastmoney": {
   "data_type": "quote/flow",
   "access": "https push2.eastmoney.com",
   "timeout": 12,
   "retry": 1,
   "backoff": 0.4,
   "freshness_rule": "<5m",
   "validation": "validate_quote",
   "status": "ACTIVE"
  },
  "yahoo": {
   "data_type": "bars/quote",
   "access": "https query1.finance.yahoo.com",
   "timeout": 15,
   "retry": 1,
   "backoff": 0.5,
   "freshness_rule": "<1d",
   "validation": "validate_bars",
   "status": "UNAVAILABLE(CN 403) — demoted to last resort"
  },
  "cftc": {
   "data_type": "macro",
   "access": "https publicreporting.cftc.gov",
   "timeout": 20,
   "retry": 2,
   "backoff": 0.6,
   "freshness_rule": "weekly",
   "validation": "validate_scalar",
   "status": "ACTIVE"
  },
  "bls": {
   "data_type": "macro",
   "access": "https api.bls.gov",
   "timeout": 20,
   "retry": 2,
   "backoff": 0.6,
   "freshness_rule": "monthly",
   "validation": "validate_scalar",
   "status": "ACTIVE"
  },
  "wallstcn": {
   "data_type": "news",
   "access": "https api-one.wallstcn.com",
   "timeout": 15,
   "retry": 1,
   "backoff": 0.5,
   "freshness_rule": "<1h",
   "validation": "none",
   "status": "ACTIVE"
  },
  "cnbc": {
   "data_type": "news",
   "access": "https search.cnbc.com RSS",
   "timeout": 15,
   "retry": 1,
   "backoff": 0.5,
   "freshness_rule": "<1h",
   "validation": "none",
   "status": "ACTIVE"
  }
 }
}
```
## 关键文件 sha256
```json
{
 "config\\v2_config.json": "7bfab969722ff38a2d5607257750f138241851b464007186ae101316eaf37aff",
 "config\\price_space.json": "7a62283736fdf7a3967919a2e3aa7bd34af679439d60e2b70b5505ba62dff985",
 "data_sources\\registry.py": "abfb4f5c5ba6f466cf53eba574b1598e449c9efe4455bfd827bf6408bf2b84e6",
 "data_sources\\router.py": "cf908cca2e4d4c5460dcb4b8b45a206c6de66aac829a7a97b8edad915107ec76",
 "data_sources\\mt5_market.py": "256442a90d2415c22f690eca0efb4564d26b88fe7b58e08ce9ae76ec2b97f9c5",
 "data_sources\\adapters_market.py": "d7634e357aae7e2fa0f95045c370e061b3906b07ce575d2e062e80309c7b437b",
 "agents\\macro_global\\sources.py": "70229fb4a4871df5c6ca2cbf085b81d810b87f8dde20d88a0e72f9079db177f0",
 "agents\\macro_global\\agent2.py": "249767ad60cbe0a8446a4380b92304889e3bbbeb47c34880f1129f2f360e371d",
 "agents\\technical\\agent1.py": "08c073fa8c9eaaa96d3136bde0036de1849786bef8ac01e2d7c8aedd73e41586",
 "hermes\\hermes.py": "1104dc3e4e7303a594e525af11e9aad9cae19fe4143548fb65160edffc8511f9",
 "runtime\\shadow_run.py": "eec256c8bcd2bdc763c236aa1f30639ca64140499c83c8504335e5a7ff724a8d",
 "runtime\\explain.py": "afeab0dd87651de34eae3df002de2732fb638955435b3b04c0f7ccc5e6116fc6",
 "dashboard\\server.py": "49fa2862c946a3219722af35a4ba5510bdb5d60654d9fd37ddad0102bd21341a",
 "dashboard\\datasource.py": "2c02e650911c56db14eed7be3fa4e4702e48407dcaae52d47928204c4257a411"
}
```
## 冻结说明
- 技术主行情: mt5 → local_fxtm → yahoo(降级)；现价/宏观: sina/tencent(国内)
- COT/BLS/东财资金流/WGC/央行购金/政策利率 = 显式 GAP（无国内源）
- UST10Y = tencent usUST(7-10Y ETF) 收益率代理(取反)，非 ^TNX 实时收益率

> 冻结后：禁止改策略/阈值/候选/风险参数。发现数据安全 bug → 单独提交 + 重新冻结 + 重启 G3 计时。
