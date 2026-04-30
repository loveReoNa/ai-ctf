# 模块三：量化基准测试环境搭建与自动化运行 (Benchmark Environment & Automation)

## 负责成员：量化基准测试架构师 (Benchmark Engineer)

### 核心任务
- 部署 LiveMCPBench，复刻 XBow 竞赛架构
- 构建"靶机（目标） + MCP Server（工具层） + AI Agent（大脑层）"闭环测试沙箱
- 编写自动化测试脚本，批量运行 Agent 解题
- 设计日志拦截系统，将 Agent 运行全过程以 JSON 格式完整 dump
  - 开始/结束时间
  - Token 消耗量
  - 报错日志

### 技术栈
- Docker
- LiveMCPBench
- XBow
- Python (自动化脚本)
- JSON Logging

### 状态
🚧 待开发 - 文件夹已创建，代码待添加