# Machine Baseline Report

> 生成时间：2026-09-03 22:10 (Asia/Shanghai) · 任务：AIQuant Workstation V1
> 本文件为只读基线，任何后续环境变化以 `environment/environment.md` 与 `reports/overnight_report.md` 为准。

## 1. 系统

| 项目 | 值 |
|---|---|
| 机型 | Microsoft Surface Laptop Studio |
| OS | Windows 11 专业版 (Build 26100) |
| 主机名 | DESKTOP-LQ0B8O3 |
| 用户 | surface |
| 时区 | Asia/Shanghai |

## 2. CPU

| 项目 | 值 |
|---|---|
| 型号 | Intel Core i7-11370H (Tiger Lake) |
| 核心/线程 | 4 物理 / 8 逻辑 |
| 基频 | 3.3 GHz（睿频 4.8 GHz） |
| AVX-512 | 无（移动版阉割） |
| 缓存 | L3 12MB |
| 备注 | FP64 性能弱于桌面级；重数值靠 GPU 分担 |

## 3. RAM

| 项目 | 值 |
|---|---|
| 总容量 | 32GB LPDDR4x-4267（板载 8×4GB） |
| 策略 | 单研究进程 ≤12GB；>8GB 数据强制流式/分块 |

## 4. 磁盘

| 项目 | 值 |
|---|---|
| 型号 | SK hynix HFS001TDE9X073N 1TB NVMe SSD |
| 容量/剩余 | 953.9GB / ~870GB（基线） |
| 文件系统 | NTFS |
| 健康 | Healthy |
| 分区 | 仅 C:（无 D:，不创建分区） |

## 5. GPU — NVIDIA RTX A2000 Laptop

| 项目 | 值 |
|---|---|
| GPU 名称 | NVIDIA RTX A2000 Laptop GPU |
| 架构 | Ampere GA107（sm_86 / CC 8.6） |
| VRAM | 4096 MiB（4GB GDDR6） |
| Driver | 591.55（2025-12-09） |
| Driver CUDA 上限 | 13.1（nvidia-smi 显示，≠已装 Toolkit） |
| Tensor Core | 有（第 3 代，80 个） |
| FP16 | 支持（Tensor 与常规路径） |
| BF16 | 支持（Tensor Core 路径，Ampere） |
| FP64 | 极弱（1:64）→ 高精度统计走 CPU |
| CUDA Toolkit | **未安装**（设计如此：torch pip 轮子自带 runtime） |
| cuDNN | **未安装**（同上） |
| 第二 GPU | Intel Iris Xe（核显，非 CUDA） |
| MIG/多卡 | 无 |

## 6. 软件基线

| 组件 | 版本 | 备注 |
|---|---|---|
| PowerShell | 5.1.26100 | |
| Node | v24.18.1 | OpenClaw 运行时（C:\dtlopenclaw） |
| OpenClaw | 2026.7.1-2 | gateway 计划任务，端口 18789 |
| winget | 1.29.290 | |
| Git | 2.55.0.windows.3 | C:\Program Files\Git |
| Git LFS | 3.7.1 | 随 Git |
| OpenSSH | 9.5p2 | 客户端 |
| Python (系统) | 3.14.7 | **OpenClaw 专用，保持不动** |
| Python (研究) | 3.12.x | 本任务安装 → C:\AIQuant\.venv |
| gh CLI | 未安装 | 暂不安装（已记录） |
| Docker/WSL/RAPIDS | 未安装 | 决策排除，暂不装 |

## 7. 网络基线

| 通道 | 状态 |
|---|---|
| GitHub HTTPS | 不可达（超时） |
| GitHub SSH :22 | **可达**（host key 已响应，known_hosts 未记录） |
| PyPI 官方 | 可达但慢 |
| 清华 TUNA 镜像 | 计划使用（AIQuant venv 内 pip.ini） |
| web_search 工具 | 无 provider（禁用） |

## 8. Git 身份与密钥

| 项目 | 值 |
|---|---|
| user.name | 296558410-wq |
| user.email | 296558410@qq.com |
| SSH key | C:\Users\surface\.ssh\id_ed25519_github（ed25519，专用于 GitHub，2026-09-03 生成） |
| ~/.ssh/config | 含 github.com 条目（IdentitiesOnly yes） |
| GitHub 公钥登记 | 待用户网页添加（截至本报告时） |
| .gitconfig | 仅 name/email 两项 |

## 9. OpenClaw Memory

| 项目 | 值 |
|---|---|
| 模式 | FTS keyword（provider: none）——决策 C，2026-09-03 生效并验证 |
| 语义检索 | 暂停（未来 GPU 环境稳定后设计 Local Embedding） |

## 10. 目录归属（C:\AIResearch 与 C:\AIQuant）

- `C:\AIResearch`：早期创建，**保留、不删除、不迁移**，后续统一判断归属。
- `C:\AIQuant`：AI Quant Research Workstation 主工作区（本文档所在）。
