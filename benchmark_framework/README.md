# 模块二：安全工具封装与 MCP 适配 (Security Tool Wrapping & MCP)

## 负责成员：安全生态与工具集成工程师 (The Hands)

### 核心任务
- 对 LiveMCPBench 提供的工具进行大语言模型友好型封装
- 安全工具命令行输出 → 纯净 JSON/文本格式的清洗与解析
- 确保底层工具链路畅通，后续直接作为 Tool 挂载给 Agent

### 技术栈
- Python
- MCP Server Protocol
- 各类安全工具 (sqlmap, nmap, OWASP ZAP, Burp Suite 等) 的输出解析

### 状态
🚧 待开发 - 文件夹已创建，代码待添加