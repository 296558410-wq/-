# HERMES SOURCE MAP（来源地图）

> 生成：2026-09-05 · 指向 sources.yaml（机器可读）。此处给来源分类地图。

## 本轮来源分布（10 个，按质量）

| 质量级 | 来源 | 数量 |
|---|---|---|
| HIGH_CONFIDENCE（央行权威） | BIS 2025 Triennial、Fed FEDS Note | 2 |
| RESEARCH_GRADE（同行评审/工作论文） | NBER w24222、arXiv:2212.07288、Moreira-Muir 争议链、arXiv:2608.27734、SSRN 2606462、Zou | 6 |
| USEFUL_CONTEXT（行业/机构科普） | WatchGold、divitae | 2 |

## 分类覆盖（任务书 §3 要求）

- Academic Research：NBER、arXiv×3、SSRN、JF/JFE（争议链）✓
- Market Microstructure：OFI、adverse selection、price impact ✓
- Asset-specific（Gold/XAUUSD）：WatchGold、COMEX/LBMA ✓
- Professional：BIS、Fed ✓
- Execution/HFT：last look、流毒性、BIS execution landscape ✓
- Volatility/regime/adaptive：NBER regime、vol-targeting、KAMA+MSR ✓
- Failure intelligence：SSRN backtesting、LLM leakage、data-snooping ✓

## 未覆盖（诚实标注，下轮补）

- 期刊库（JF/JFE/RFS）非 arXiv 全文未直接取（此前 evidence_registry 已记 KD-G1 缺口）
- GitHub 深度审查（仅浅看 1 个 microstructure sim 仓库，未做 code-level mechanism extraction）
- 量化社区（QuantConnect/Wilmott/Futures.io/MQL5）本轮未深入（IDEA SOURCE，价值低于学术）

> 详见 global_intelligence/sources.yaml（每条含 url/author/date/quality/evidence_level）。
