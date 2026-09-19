# DATA_SOURCE_MATRIX — V2 数据源 中国大陆可达性（本机实测）

- 测试时间: 2026-09-14T11:05:16.225461+00:00  |  本机: DESKTOP-LQ0B8O3 (CN)
- **CHINA_MAINLAND_REACHABLE = PARTIAL**  (OK 12/13)

| source_id | type | dns | connect | http | data_valid | latency_ms | freshness | status | failure_reason |
|---|---|---|---|---|---|---|---|---|---|
| sina:quote | quote | OK | OK | 200 | True | 1733 | FRESH | OK |  |
| tencent:quote | quote | OK | OK | 200 | True | 2310 | FRESH | OK |  |
| eastmoney:quote | quote | OK | OK | 200 | True | 4759 | FRESH | OK |  |
| eastmoney:flow | flow | OK | OK | 200 | True | 4733 | FRESH | OK |  |
| yahoo:chart | bars | OK | OK | 200 | True | 1277 | FRESH | OK |  |
| yahoo2:chart | bars | OK | OK | 200 | True | 1021 | FRESH | OK |  |
| cftc:cot | macro | OK | OK | 200 | True | 1739 | FRESH | OK |  |
| ecb:sdmx | macro | OK | OK | 200 | True | 1486 | FRESH | OK |  |
| treasury:fiscaldata | macro | OK | OK | 200 | True | 1565 | FRESH | OK |  |
| wallstcn:news | news | OK | OK | 200 | True | 1635 | FRESH | OK |  |
| cnbc:rss | news | OK | OK | 200 | True | 1155 | FRESH | OK |  |
| sge:site | reference | OK | SSLCertVerificationError | 200 | True | 3682 | FRESH | OK |  |
| fred:site | macro(expect_down) | OK | OK | - | False | 38332 | MISSING | SOURCE_DOWN | ReadTimeout:HTTPSConnectionPool(host='fred.stlouisfed.org', port=443): Read timed out. (read timeout=18) |

## 结论 / 备注
- 技术 K 线：**本地 `data/live_fxtm` tick 为主源**（不依赖外网）；Yahoo 仅 SECONDARY/OPTIONAL，实测间歇 403 → 自动退避。
- 现价：sina/tencent/eastmoney 可用；yahoo 间歇。
- 宏观：CFTC/COT、ECB、Treasury、BLS 等免 Key 源按上表状态；不可达者 → cache/last_valid 降级并标 STALE_BUT_VALID/SOURCE_DOWN。
- FRED 预期不可达（超时/被墙）→ 不用。