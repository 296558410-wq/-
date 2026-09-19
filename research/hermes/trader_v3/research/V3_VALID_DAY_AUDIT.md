# V3 VALID-DAY DEFINITION AUDIT — 2026-09-17T11:33:50.000108+00:00

> 本审计**只做数据质量敏感性**，**不使用任何 Alpha 结果**反选定义（任务书 §二十 / 新硬门禁一）。

- 日历天数: 140 · 有数据天: 140
- 逐日表: `C:\AIQuant\research\hermes\trader_v3\data\v3_valid_day_table.csv`

## 分期
```json
{
 "P_A_2023H2": {
  "days_with_data": 62,
  "hours_covered_min": 1,
  "hours_covered_max": 23,
  "hours_covered_median": 21.0,
  "n_ticks_median": 102904.0
 },
 "P_B_2024Q1": {
  "days_with_data": 74,
  "hours_covered_min": 1,
  "hours_covered_max": 23,
  "hours_covered_median": 23.0,
  "n_ticks_median": 106840.5
 },
 "P_C_202608": {
  "days_with_data": 4,
  "hours_covered_min": 21,
  "hours_covered_max": 23,
  "hours_covered_median": 23.0,
  "n_ticks_median": 285952.5
 }
}
```
## 阈值敏感性 (rows=hours_covered 阈值, cols=n_ticks 阈值; 值=通过天数 [P_A/P_B])
```json
{
 "18": {
  "0": {
   "total_days": 93,
   "P_A": 36,
   "P_B": 53,
   "ticks_retained": 13531079
  },
  "100": {
   "total_days": 93,
   "P_A": 36,
   "P_B": 53,
   "ticks_retained": 13531079
  },
  "500": {
   "total_days": 93,
   "P_A": 36,
   "P_B": 53,
   "ticks_retained": 13531079
  },
  "1000": {
   "total_days": 93,
   "P_A": 36,
   "P_B": 53,
   "ticks_retained": 13531079
  },
  "5000": {
   "total_days": 93,
   "P_A": 36,
   "P_B": 53,
   "ticks_retained": 13531079
  },
  "10000": {
   "total_days": 93,
   "P_A": 36,
   "P_B": 53,
   "ticks_retained": 13531079
  }
 },
 "19": {
  "0": {
   "total_days": 91,
   "P_A": 34,
   "P_B": 53,
   "ticks_retained": 13304810
  },
  "100": {
   "total_days": 91,
   "P_A": 34,
   "P_B": 53,
   "ticks_retained": 13304810
  },
  "500": {
   "total_days": 91,
   "P_A": 34,
   "P_B": 53,
   "ticks_retained": 13304810
  },
  "1000": {
   "total_days": 91,
   "P_A": 34,
   "P_B": 53,
   "ticks_retained": 13304810
  },
  "5000": {
   "total_days": 91,
   "P_A": 34,
   "P_B": 53,
   "ticks_retained": 13304810
  },
  "10000": {
   "total_days": 91,
   "P_A": 34,
   "P_B": 53,
   "ticks_retained": 13304810
  }
 },
 "20": {
  "0": {
   "total_days": 89,
   "P_A": 32,
   "P_B": 53,
   "ticks_retained": 13108106
  },
  "100": {
   "total_days": 89,
   "P_A": 32,
   "P_B": 53,
   "ticks_retained": 13108106
  },
  "500": {
   "total_days": 89,
   "P_A": 32,
   "P_B": 53,
   "ticks_retained": 13108106
  },
  "1000": {
   "total_days": 89,
   "P_A": 32,
   "P_B": 53,
   "ticks_retained": 13108106
  },
  "5000": {
   "total_days": 89,
   "P_A": 32,
   "P_B": 53,
   "ticks_retained": 13108106
  },
  "10000": {
   "total_days": 89,
   "P_A": 32,
   "P_B": 53,
   "ticks_retained": 13108106
  }
 },
 "21": {
  "0": {
   "total_days": 87,
   "P_A": 32,
   "P_B": 51,
   "ticks_retained": 12605306
  },
  "100": {
   "total_days": 87,
   "P_A": 32,
   "P_B": 51,
   "ticks_retained": 12605306
  },
  "500": {
   "total_days": 87,
   "P_A": 32,
   "P_B": 51,
   "ticks_retained": 12605306
  },
  "1000": {
   "total_days": 87,
   "P_A": 32,
   "P_B": 51,
   "ticks_retained": 12605306
  },
  "5000": {
   "total_days": 87,
   "P_A": 32,
   "P_B": 51,
   "ticks_retained": 12605306
  },
  "10000": {
   "total_days": 87,
   "P_A": 32,
   "P_B": 51,
   "ticks_retained": 12605306
  }
 },
 "22": {
  "0": {
   "total_days": 73,
   "P_A": 27,
   "P_B": 43,
   "ticks_retained": 10352022
  },
  "100": {
   "total_days": 73,
   "P_A": 27,
   "P_B": 43,
   "ticks_retained": 10352022
  },
  "500": {
   "total_days": 73,
   "P_A": 27,
   "P_B": 43,
   "ticks_retained": 10352022
  },
  "1000": {
   "total_days": 73,
   "P_A": 27,
   "P_B": 43,
   "ticks_retained": 10352022
  },
  "5000": {
   "total_days": 73,
   "P_A": 27,
   "P_B": 43,
   "ticks_retained": 10352022
  },
  "10000": {
   "total_days": 73,
   "P_A": 27,
   "P_B": 43,
   "ticks_retained": 10352022
  }
 },
 "23": {
  "0": {
   "total_days": 61,
   "P_A": 20,
   "P_B": 38,
   "ticks_retained": 8838017
  },
  "100": {
   "total_days": 61,
   "P_A": 20,
   "P_B": 38,
   "ticks_retained": 8838017
  },
  "500": {
   "total_days": 61,
   "P_A": 20,
   "P_B": 38,
   "ticks_retained": 8838017
  },
  "1000": {
   "total_days": 61,
   "P_A": 20,
   "P_B": 38,
   "ticks_retained": 8838017
  },
  "5000": {
   "total_days": 61,
   "P_A": 20,
   "P_B": 38,
   "ticks_retained": 8838017
  },
  "10000": {
   "total_days": 61,
   "P_A": 20,
   "P_B": 38,
   "ticks_retained": 8838017
  }
 },
 "24": {
  "0": {
   "total_days": 0,
   "P_A": 0,
   "P_B": 0,
   "ticks_retained": 0
  },
  "100": {
   "total_days": 0,
   "P_A": 0,
   "P_B": 0,
   "ticks_retained": 0
  },
  "500": {
   "total_days": 0,
   "P_A": 0,
   "P_B": 0,
   "ticks_retained": 0
  },
  "1000": {
   "total_days": 0,
   "P_A": 0,
   "P_B": 0,
   "ticks_retained": 0
  },
  "5000": {
   "total_days": 0,
   "P_A": 0,
   "P_B": 0,
   "ticks_retained": 0
  },
  "10000": {
   "total_days": 0,
   "P_A": 0,
   "P_B": 0,
   "ticks_retained": 0
  }
 }
}
```
## 提案评估
```json
{
 "proposal": "hours_covered>=21 AND n_ticks>=1000",
 "valid_days": 87,
 "P_A": 32,
 "P_B": 51,
 "ticks_retained": 12605306,
 "frac_of_have": 0.6214
}
```
## 稳定性
```json
{
 "hours_20_vs_21_vs_22": [
  89,
  87,
  73
 ],
 "nticks_500_vs_1000_vs_5000": [
  87,
  87,
  87
 ]
}
```

## 判定：**INSUFFICIENT_EVIDENCE**
- 小时阈值敏感性偏高，且阈值选择本身无唯一数据依据 → INSUFFICIENT_EVIDENCE

### 处置
- 采纳（若 FROZEN_CANDIDATE）：`VALID_DAY := hours_covered >= 21 AND n_ticks >= 1000`，依据 = C4 同源高峰点 match_rate 0.9881（hours>=21 子集）+ 本敏感性稳定；**冻结后不得再改**。
- 若 INSUFFICIENT_EVIDENCE：保持 PROPOSAL，**不得进入 G2**（G2 开放条件含 Valid-Day=FROZEN）。

