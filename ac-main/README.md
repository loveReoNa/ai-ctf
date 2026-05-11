# AI-CTF: Intelligent Attack Simulation System for CTF Challenges

AI Agent CTF 能力量化评测系统 — 毕设项目

## 项目概述

本项目旨在构建一个基于 ReAct 架构的智能 CTF 攻击模拟系统，通过 MCP (Model Context Protocol) 协议对接安全工具，并使用 LiveMCPBench / XBow 作为基准测试平台，对 AI Agent 的 CTF 解题能力进行多维度量化评测。

## 模块划分

| 模块 | 名称 | 负责人 | 状态 |
|------|------|--------|------|
| 模块一 | MCP 协议适配与 Agent 大脑 | AI 大脑架构师 | 🚧 待开发 |
| 模块二 | 安全工具封装与 MCP 适配 | 安全生态与工具集成工程师 | 🚧 待开发 |
| 模块三 | 基准测试环境与自动化 | 量化基准测试架构师 | 🚧 待开发 |
| 模块四 | 数据分析与可视化 | 数据科学家与项目大管家 | 🚧 待开发 |

## 目录结构

```
ai-ctf/
├── src/cai/                   # 核心 Agent 框架（ReAct Agent + MCP SDK）
├── mcp_integration/           # 模块一：MCP 协议适配与 Agent 大脑
├── benchmark_framework/       # 模块二：安全工具封装与 MCP 适配
├── visualization_dashboard/   # 模块三：基准测试环境与自动化
├── data_analysis/             # 模块四：数据分析与可视化面板
├── portfolio/                 # Final Portfolio
└── rnd_project_docs/          # 毕设相关文档
```

## 量化指标

### 效率维度
- 解题成功率
- 平均解题时间
- Token 消耗效率

### 智能维度
- 工具调用准确率（成功次数/总次数）
- 攻击路径正确率
- 策略自适应能力

### 覆盖度维度
- 漏洞类型覆盖度
- 工具使用覆盖度
- 攻击技术覆盖度

## 技术栈

- **Agent 框架**：Python, OpenAI API, ReAct Agent Pattern
- **MCP 协议**：MCP (Model Context Protocol), LiveMCPBench
- **安全工具**：sqlmap, nmap, OWASP ZAP, Burp Suite 等
- **测试平台**：Docker, XBow, CTF 靶机
- **可视化**：Python (matplotlib, pandas), Web 前端

## License

Copyright (c) 2025 Alias Robotics S.L.

This project contains open-source components under the MIT License (see LICENSE-MIT) and proprietary additions licensed for research purposes only. Commercial use requires a commercial license.

See LICENSE and DISCLAIMER for full terms.