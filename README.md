# AI-CTF: Intelligent Attack Simulation System for CTF Challenges

AI Agent CTF Capability Quantitative Evaluation System — Graduation Project

## Project Overview

This project aims to build an intelligent CTF attack simulation system based on the ReAct architecture. It interfaces with security tools via the MCP (Model Context Protocol) and uses LiveMCPBench / XBow as the benchmarking platform to perform multi-dimensional quantitative evaluation of AI Agent CTF problem-solving capabilities.

## Module Division

| Module | Name | Owner | Status |
|--------|------|-------|--------|
| Module 1 | MCP Protocol Adaptation & Agent Brain | AI Brain Architect | 🚧 In Development |
| Module 2 | Security Tool Wrapping & MCP Adaptation | Security Ecosystem & Tool Integration Engineer | 🚧 In Development |
| Module 3 | Benchmark Environment & Automation | Quantitative Benchmark Architect | 🚧 In Development |
| Module 4 | Data Analysis & Visualization | Data Scientist & Project Manager | 🚧 In Development |

## Directory Structure

```
ai-ctf/
├── src/cai/                   # Core Agent Framework (ReAct Agent + MCP SDK)
├── mcp_integration/           # Module 1: MCP Protocol Adaptation & Agent Brain
├── benchmark_framework/       # Module 2: Security Tool Wrapping & MCP Adaptation
├── visualization_dashboard/   # Module 3: Benchmark Environment & Automation
├── data_analysis/             # Module 4: Data Analysis & Visualization Panel
├── portfolio/                 # Final Portfolio
└── rnd_project_docs/          # Graduation Project Related Documents
```

## Quantitative Metrics

### Efficiency Dimension
- Problem-solving success rate
- Average problem-solving time
- Token consumption efficiency

### Intelligence Dimension
- Tool invocation accuracy (success count / total count)
- Attack path correctness rate
- Strategy adaptability

### Coverage Dimension
- Vulnerability type coverage
- Tool usage coverage
- Attack technique coverage

## Tech Stack

- **Agent Framework**: Python, OpenAI API, ReAct Agent Pattern
- **MCP Protocol**: MCP (Model Context Protocol), LiveMCPBench
- **Security Tools**: sqlmap, nmap, OWASP ZAP, Burp Suite, etc.
- **Testing Platform**: Docker, XBow, CTF target machines
- **Visualization**: Python (matplotlib, pandas), Web frontend

## License

Copyright (c) 2025 Alias Robotics S.L.

This project contains open-source components under the MIT License (see LICENSE-MIT) and proprietary additions licensed for research purposes only. Commercial use requires a commercial license.

See LICENSE and DISCLAIMER for full terms.