# AI-CTF项目 Kali Linux 完整部署、测试与毕业论文截图指南

> **适用对象**：毕业论文撰写者——需要在Kali Linux上部署本项目四模块、运行集成测试并截取论文所需截图
>
> **关联文档**：`rnd_project_docs/毕业论文.md`（论文正文）、`Kali_Linux_DeepSeek_配置指南.md`（已有配置参考）
>
> **所有演示脚本已内置在项目中**：`scripts/screenshot_demos/` 目录，无需手动创建任何脚本。

---

## 目录

1. [毕业论文需补充截图的位置分析](#1-毕业论文需补充截图的位置分析)
2. [系统环境准备](#2-系统环境准备)
3. [项目克隆与Python虚拟环境搭建](#3-项目克隆与python虚拟环境搭建)
4. [安装项目依赖](#4-安装项目依赖)
5. [配置LLM API密钥](#5-配置llm-api密钥)
6. [运行四模块集成测试（获取截图①）](#6-运行四模块集成测试获取截图)
7. [data_analysis模块独立测试（获取截图②）](#7-data_analysis模块独立测试获取截图)
8. [MCP集成模块展示（获取截图③）](#8-mcp集成模块展示获取截图)
9. [Rich终端推理面板演示（获取截图④⑤⑥⑨）](#9-rich终端推理面板演示获取截图)
10. [Docker沙箱与靶机部署（获取截图⑧）](#10-docker沙箱与靶机部署获取截图)
11. [技术选型与工具多样性展示（获取截图⑦⑩）](#11-技术选型与工具多样性展示获取截图)
12. [截图清单与对应论文位置速查表](#12-截图清单与对应论文位置速查表)
13. [常见问题排查](#13-常见问题排查)

---

## 1. 毕业论文需补充截图的位置分析

通读`毕业论文.md`后，识别出以下**需要补充截图（或可用截图增强说服力）的位置**，按重要性排序：

### 截图①：【最重要】四模块集成测试完整通过
- **论文位置**：第5.2节"集成测试"段（第453行）
- **论文描述**："项目级集成测试文件`tests/test_rnd_integration.py`包含四个测试用例，全部通过✅"
- **截图内容**：在终端执行`python tests/test_rnd_integration.py`后显示四个Test全部`PASSED`的输出
- **截取方法**：见[第6节](#6-运行四模块集成测试获取截图)

### 截图②：data_analysis模块指标计算与可视化输出
- **论文位置**：第2.1节（四模块架构）及第4.2节（模块D能力）
- **论文描述**："9项多维指标的自动化计算与15种可视化图表生成"
- **截图内容**：MetricsEngine输出（准确率/F1/Token效率）、图表生成目录列表
- **截取方法**：见[第7节](#7-data_analysis模块独立测试获取截图)

### 截图③：MCP Server注册表与工具聚合输出
- **论文位置**：第3.1.2节"MCP Server注册表"段（第171行）
- **论文描述**："当前已接入15个服务器，涵盖端口扫描、漏洞利用等多种CTF工具类别"
- **截图内容**：`MCPServerRegistry`注册后的服务器列表/工具聚合输出
- **截取方法**：见[第8节](#8-mcp集成模块展示获取截图)

### 截图④：Rich推理面板（蓝色Panel）
- **论文位置**：第3.4.5节"推理面板"段（第351行）
- **论文描述**："以蓝色圆角Panel展示当前轮次的完整推理过程——📍当前态势、💡核心假设+置信度..."
- **截图内容**：展示Agent推理过程的蓝色Rich Panel（包含态势、假设、置信度、选择工具）
- **截取方法**：见[第9节](#9-rich终端推理面板演示获取截图)

### 截图⑤：Rich结果面板（绿色/红色Panel）
- **论文位置**：第3.4.5节"结果面板"段（第353行）
- **论文描述**："以绿色或红色Panel展示工具执行结果——🔧工具名+⏱耗时、📋结果摘要、🧪结果vs预期对比"
- **截图内容**：工具执行成功（绿色边框）和失败（红色边框）两种结果面板
- **截取方法**：见[第9节](#9-rich终端推理面板演示获取截图)

### 截图⑥：五阶段攻击进度指示器
- **论文位置**：第3.4.5节"阶段进度指示器"段（第355行）及附录C
- **论文描述**："以品红色Panel展示攻击链五阶段的进度条——每个阶段用10格进度条表示"
- **截图内容**：品红色面板显示RECONNAISSANCE→ENUMERATION→EXPLOITATION→POST_EXPLOITATION→FLAG_CAPTURE的进度
- **截取方法**：见[第9节](#9-rich终端推理面板演示获取截图)

### 截图⑦：Benchmark工具分类体系展示
- **论文位置**：第2.2.3节（LangChain框架角色边界），以及第3.1.1节
- **论文描述**："15+安全工具的标准化封装与输出清洗"以及"工具侦察/枚举/利用等分类体系"
- **截图内容**：`ToolClassifier.classify_batch()`批量分类工具的输出
- **截取方法**：见[第11节](#11-技术选型与工具多样性展示获取截图)

### 截图⑧：Docker沙箱信息与挑战定义
- **论文位置**：第2.1节（模块三描述），第6.2节
- **论文描述**："Docker沙箱的全生命周期管理、CTF挑战靶机的自动部署"
- **截图内容**：SandboxInfo/ChallengeDefinition/XBowConfig的实例化输出
- **截取方法**：见[第10节](#10-docker沙箱与靶机部署获取截图)

### 截图⑨：Prompt模板渲染输出
- **论文位置**：第3.3节（Prompt工程管理），附录B
- **论文描述**："PromptManager提供4个默认模板的加载、渲染和动态组合"
- **截图内容**：Prompt模板渲染后的输出文本（ctf_solver_default）
- **截取方法**：见[第9节](#9-rich终端推理面板演示获取截图)

### 截图⑩：完整部署环境与项目结构
- **论文位置**：第4.2节（开发环境）
- **论文描述**："在Kali Linux环境下完整部署与测试"
- **截图内容**：项目目录树+Python环境信息
- **截取方法**：见[第11节](#11-技术选型与工具多样性展示获取截图)

---

## 2. 系统环境准备

### 2.1 更新系统

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git curl wget build-essential python3-pip python3-venv
```

### 2.2 确保Python 3.9+可用

本项目的`pyproject.toml`要求`requires-python = ">=3.9"`，但部分依赖（如`mcp`）需要Python 3.10+。**推荐使用Python 3.12**。

```bash
# 检查当前Python版本
python3 --version

# 如果版本低于3.10，安装Python 3.12
sudo apt install -y python3.12 python3.12-venv python3.12-dev

# 验证
python3.12 --version
```

### 2.3 安装Docker（可选——仅模块三完整测试需要）

```bash
# 安装Docker
sudo apt install -y docker.io
sudo systemctl enable docker --now
sudo usermod -aG docker $USER

# 重新登录后验证
docker --version
```

> **注意**：Docker环境非必需。集成测试Test 4仅实例化数据结构，不实际启动容器。所有演示脚本也不需要Docker。

### 2.4 安装截图工具

```bash
# 方法1: gnome-screenshot（推荐）
sudo apt install -y gnome-screenshot

# 方法2: scrot（轻量命令行截图）
sudo apt install -y scrot

# 方法3: xfce4-screenshooter
sudo apt install -y xfce4-screenshooter
```

---

## 3. 项目克隆与Python虚拟环境搭建

### 3.1 克隆项目

```bash
# 进入工作目录
cd ~
mkdir -p ctf_project
cd ctf_project

# 克隆项目（使用实际仓库地址）
git clone https://github.com/loveReoNa/ai-ctf.git
cd ai-ctf
```

### 3.2 创建虚拟环境

```bash
# 使用Python 3.12创建虚拟环境
python3.12 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 确认虚拟环境中的Python版本
python --version
```

---

## 4. 安装项目依赖

```bash
# 确保在项目根目录且已激活虚拟环境
pip install --upgrade pip setuptools wheel

# 安装项目依赖
pip install -e .

# （可选）安装开发依赖——用于跑测试
pip install -e ".[dev]"
```

### 验证安装

```bash
# 验证关键包已安装
python -c "import rich; print('rich:', rich.__version__)"
python -c "import openai; print('openai:', openai.__version__)"
python -c "import pydantic; print('pydantic:', pydantic.__version__)"
python -c "import flask; print('flask:', flask.__version__)"
```

---

## 5. 配置LLM API密钥

### 5.1 创建.env文件

```bash
# 在项目根目录创建.env
cp .env.example .env

# 编辑.env文件
nano .env
```

### 5.2 配置内容

根据你使用的LLM提供商，填写相应API密钥：

```bash
# 使用OpenAI（推荐用于测试）
OPENAI_API_KEY="sk-your-openai-api-key-here"

# 或使用DeepSeek
ANTHROPIC_API_KEY=""
OLLAMA=""
CAI_MODEL="deepseek-chat"
```

> **重要**：至少需要配置一个可用的LLM API密钥。集成测试中Test 1-3不实际调用LLM API（使用模拟数据），但模块一的Agent编排器在某些测试场景中可能需要API。如果你没有API密钥，Test 1-3仍可完整通过。

---

## 6. 运行四模块集成测试（获取截图①）

这是**最核心的截图来源**——证明四个模块协同工作能力。

### 6.1 执行集成测试

```bash
# 确保在项目根目录且已激活虚拟环境
cd ~/ctf_project/ai-ctf
source venv/bin/activate

python tests/test_rnd_integration.py
```

### 6.2 预期输出示例

```
============================================================
Test 1: Data Analysis Pipeline (Parse -> Metrics -> Baseline -> Report)
============================================================
  LogParser: 5 sessions, 4/5 successful
  MetricsEngine: accuracy=0.80, F1=0.84, flags=4
    Efficiency: completion=80.0%, solve_time=285s
    Intelligence: first_success=55.0%, hallucination=5.0%
    Coverage: type_coverage=80.0%, mastered=2/5
  BaselineManager: 5 baselines compared
  Visualization: 6 charts generated
  ReportGenerator:
    json: metrics_report.json (1234 bytes)
    html: metrics_report.html (5678 bytes)
    md: metrics_report.md (3456 bytes)

============================================================
Test 2: Benchmark Framework Module
============================================================
  ToolWrapper: created for 'nmap', has_sanitizer=True
  Sanitizer: input -> 'Found flag{***} and more'
  has_sensitive_data('flag{secret}'): True
  LiveMCPBenchParser: methods=[...]
  ToolClassifier: nmap -> reconnaissance
  classify_batch: nmap:reconnaissance, sqlmap:exploitation, hydra:exploitation, netcat:exploitation

============================================================
Test 3: MCP Integration Module
============================================================
  MCPConnectionConfig: server=test_nmap, transport=stdio
  MCPServerRegistry: 1 server(s) registered
  ToolSchemaParser: parsed schema for 'nmap_scan'
  PromptManager: prompt loaded, length=1379
  AgentState: phase=reconnaissance
  LoggedToolCall: tool=nmap, success=True, tokens=200
  RunConfig: target=10.0.0.1, max_turns=50

============================================================
Test 4: Visualization Dashboard Module
============================================================
  SandboxConfig: image=ubuntu:22.04, memory=1024m
  SandboxInfo: id=abc123, status=running, ip=172.17.0.2
  ChallengeDefinition: name=sql_injection_basic, category=web
  XBowConfig: model=gpt-4, timeout=1800s
  LogCollector: 1 log(s)
  BatchConfig: 1 challenges, workers=2

============================================================
=== ALL MODULE INTEGRATION TESTS PASSED ===
============================================================
```

### 6.3 截图指导

**截图①——四模块集成测试全部通过**：

1. 运行上述命令
2. 调整终端窗口大小，使所有输出在一屏内可见（或滚动截图）
3. 截图包含：从`Test 1`开始到`=== ALL MODULE INTEGRATION TESTS PASSED ===`的全部内容
4. **截图命令**：
   ```bash
   # 截取活动窗口（延迟3秒让你切换到终端）
   gnome-screenshot -w -d 3
   # 或使用scrot全屏截图
   scrot -d 3 screenshot_01_integration_tests.png
   ```
5. 保存截图命名为`screenshot_01_integration_tests.png`

---

## 7. data_analysis模块独立测试（获取截图②）

运行内置演示脚本，获取更详细的data_analysis模块输出。

### 7.1 执行脚本

```bash
cd ~/ctf_project/ai-ctf
source venv/bin/activate
python scripts/screenshot_demos/demo_data_analysis.py
```

**脚本路径**：`scripts/screenshot_demos/demo_data_analysis.py`

### 7.2 预期输出要点

- LogParser解析5个模拟会话（4成功/1失败）
- 9-DIMENSION METRICS REPORT（准确率、F1、效率、智能、覆盖三维度各3项）
- BASELINE COMPARISON（5个基线对比）
- Visualization图表生成列表
- ReportGenerator多格式输出（JSON/HTML/MD）

### 7.3 截图指导

- **截图内容**：从`9-DIMENSION METRICS REPORT`到`ReportGenerator outputs`的完整输出
- **截图命令**：
  ```bash
  gnome-screenshot -w -d 3
  ```
- 保存为`screenshot_02_metrics_report.png`

---

## 8. MCP集成模块展示（获取截图③）

运行内置演示脚本，展示15个MCP服务器的注册和工具质量过滤。

### 8.1 执行脚本

```bash
cd ~/ctf_project/ai-ctf
source venv/bin/activate
python scripts/screenshot_demos/demo_mcp.py
```

**脚本路径**：`scripts/screenshot_demos/demo_mcp.py`

### 8.2 预期输出要点

- MCP SERVER REGISTRY表格（15个安全工具服务器，按ID/Name/Transport/Command列展示）
- 分类统计：Reconnaissance(4) + Enumeration(3) + Exploitation(5) + Post-Exploitation(2) + FlagCapture(1)
- TOOL QUALITY FILTER：3个通过质量检测（✅），3个被拒绝（❌）

### 8.3 截图指导

- **截图内容**：15个MCP服务器的注册列表 + 工具质量过滤结果
- **截图命令**：
  ```bash
  gnome-screenshot -w -d 3
  ```
- 保存为`screenshot_03_mcp_servers.png`

---

## 9. Rich终端推理面板演示（获取截图④⑤⑥⑨）

运行内置演示脚本，展示推理可解释性的核心成果——结构化Rich面板和Prompt模板。

### 9.1 执行脚本

```bash
cd ~/ctf_project/ai-ctf
source venv/bin/activate
python scripts/screenshot_demos/demo_reasoning.py
```

**脚本路径**：`scripts/screenshot_demos/demo_reasoning.py`

此脚本一次输出4个Panel + 1个Token消耗表，需分次截取。

### 9.2 输出内容说明

| 输出顺序 | 内容 | 对应截图编号 |
|----------|------|-------------|
| 蓝色Panel | Agent Reasoning Round #3（态势+假设+动作+备选方案） | 截图④ |
| 绿色Panel | gobuster_dir_scan成功结果（发现8个目录） | 截图⑤（上半） |
| 红色Panel | sqlmap_inject失败结果（404错误） | 截图⑤（下半） |
| 品红色Panel | 五阶段攻击进度（RECON→ENUM→EXPLOIT→POST→FLAG） | 截图⑥ |
| Prompt模板 | ctf_solver_default渲染输出 + Token消耗表 | 截图⑨ |

### 9.3 截图指导

#### 截图④——蓝色推理面板

1. 运行脚本后，**蓝色Panel会最先输出**
2. 滚动终端确保蓝色Panel完整可见
3. 截图命令：
   ```bash
   gnome-screenshot -w -d 3
   ```
4. 保存为`screenshot_04_reasoning_panel.png`

#### 截图⑤——绿色成功 + 红色失败结果面板

1. 绿色和红色Panel**依次连续输出**
2. 若终端高度不够，可先截绿色Panel，然后向上滚动截红色Panel
3. 或调整终端窗口高度（建议 ≥40行）
4. 截图命令：
   ```bash
   gnome-screenshot -w -d 3
   ```
5. 保存为`screenshot_05_result_panels.png`

#### 截图⑥——五阶段攻击进度指示器

1. 品红色Panel紧接红色失败面板后输出
2. 展示5个阶段的进度条（RECONNAISSANCE 30% / ENUMERATION 20% / 其余0%）
3. 截图命令：
   ```bash
   gnome-screenshot -w -d 3
   ```
4. 保存为`screenshot_06_phase_progress.png`

#### 截图⑨——Prompt模板渲染输出

1. 品红色Panel之后输出Prompt模板内容（前20行）和Token消耗表
2. Rich表格展示5个组件的Token分配
3. 截图命令：
   ```bash
   gnome-screenshot -w -d 3
   ```
4. 保存为`screenshot_09_prompt_template.png`

---

## 10. Docker沙箱与靶机部署（获取截图⑧）

运行内置演示脚本，展示模块三的数据结构定义（无需Docker环境）。

### 10.1 执行脚本

```bash
cd ~/ctf_project/ai-ctf
source venv/bin/activate
python scripts/screenshot_demos/demo_sandbox.py
```

**脚本路径**：`scripts/screenshot_demos/demo_sandbox.py`

### 10.2 预期输出要点

- SandboxConfig（3个VM模板：ubuntu/kalilinux/debian）
- SandboxInfo运行实例（container_id / IP / Ports）
- Challenge Definitions表格（5个CTF挑战，web/pwn/crypto/reverse各类）
- LogCollector日志收集统计（5条日志）
- BatchConfig批量运行配置（5挑战/4workers）

### 10.3 截图指导

- **截图内容**：从SandboxConfig模板定义到BatchConfig的全部输出
- **截图命令**：
  ```bash
  gnome-screenshot -w -d 3
  ```
- 保存为`screenshot_08_sandbox.png`

---

## 11. 技术选型与工具多样性展示（获取截图⑦⑩）

### 11.1 工具分类体系展示（截图⑦）

```bash
cd ~/ctf_project/ai-ctf
source venv/bin/activate
python scripts/screenshot_demos/demo_benchmark.py
```

**脚本路径**：`scripts/screenshot_demos/demo_benchmark.py`

**预期输出要点**：
- FLAG MASKING SANITIZER（4个测试用例：敏感/清洁检测）
- Tool Classification System表格（15+工具按5类分组）
- OUTPUT SANITIZER（ANSI转义码清洗前后对比）

**截图命令**：
```bash
gnome-screenshot -w -d 3
```
保存为`screenshot_07_tool_classification.png`

### 11.2 项目结构与环境截图（截图⑩）

```bash
# 项目目录结构
cd ~/ctf_project/ai-ctf
tree -L 2 -I '__pycache__|*.pyc|venv|.git|*.egg-info|nohup.out'

# 核心依赖版本
pip freeze | grep -E "rich|openai|pydantic|flask|numpy|matplotlib|pandas|jinja2|folium|paramiko"

# Python环境
python --version
which python
```

**截图命令**：
```bash
# 先运行上述命令，然后截图
gnome-screenshot -w -d 3
```
保存为`screenshot_10_project_structure.png`

---

## 12. 截图清单与对应论文位置速查表

| 截图编号 | 截图内容 | 论文对应章节 | 论文行号/描述 | 执行命令 |
|----------|----------|-------------|-------------|----------|
| ① | 四模块集成测试全部通过 | §5.2 集成测试 | 第453行 "四个测试用例，全部通过✅" | `python tests/test_rnd_integration.py` |
| ② | 9维指标体系 + 基线对比 + 图表生成 | §2.1、§5.2 | 四模块架构 + 指标输出 | `python scripts/screenshot_demos/demo_data_analysis.py` |
| ③ | MCP Server注册表(15个服务器) + 工具质量过滤 | §3.1.2 MCP服务器注册表 | 第171行 "已接入15个服务器" | `python scripts/screenshot_demos/demo_mcp.py` |
| ④ | Rich推理面板(蓝色Panel) | §3.4.5 推理面板 | 第351行 "蓝色圆角Panel" | `python scripts/screenshot_demos/demo_reasoning.py` |
| ⑤ | Rich结果面板(绿色成功+红色失败) | §3.4.5 结果面板 | 第353行 "绿色或红色Panel" | `python scripts/screenshot_demos/demo_reasoning.py` |
| ⑥ | 五阶段攻击进度指示器 | §3.4.5 阶段进度指示器、附录C | 第355行 "品红色Panel" | `python scripts/screenshot_demos/demo_reasoning.py` |
| ⑦ | 工具分类体系(15+工具5类) | §2.2.3、§3.1.1 | 模块二工具封装 | `python scripts/screenshot_demos/demo_benchmark.py` |
| ⑧ | Docker沙箱数据结构 + 挑战定义 | §2.1 模块三 | 第73行 "模块三：测试沙箱" | `python scripts/screenshot_demos/demo_sandbox.py` |
| ⑨ | Prompt模板渲染 + Token消耗表 | §3.3.1、附录B | 第260行 "4个默认模板" | `python scripts/screenshot_demos/demo_reasoning.py` |
| ⑩ | 项目目录结构 + Python依赖环境 | §4.2 开发环境 | 第406行 "个人开发时间线" | `tree -L 2` + `pip freeze` |

---

## 13. 常见问题排查

### 问题1：`ModuleNotFoundError: No module named 'mcp_integration'`

**原因**：未在项目根目录安装包。

**解决**：
```bash
cd ~/ctf_project/ai-ctf
source venv/bin/activate
pip install -e .
```

### 问题2：`ImportError: cannot import name '...' from '...'`

**原因**：项目文件可能被编辑但未保存，或Python版本不兼容。

**解决**：
```bash
# 确认各模块可正常导入
python -c "from mcp_integration import MCPClient; print('OK')"
python -c "from data_analysis import LogParser; print('OK')"
python -c "from benchmark_framework import ToolWrapper; print('OK')"
python -c "from visualization_dashboard import SandboxManager; print('OK')"
```

### 问题3：`rich`库无法渲染Panel / 颜色不正确

**原因**：终端不支持完整的Unicode/颜色。

**解决**：
```bash
# 确认rich安装
pip install rich>=13.9.4

# 使用支持256色的终端（推荐Kali自带的gnome-terminal或qterminal）
echo $TERM  # 应该输出 xterm-256color
```

### 问题4：test_rnd_integration.py测试失败

**原因**：可能是Python版本不兼容或依赖缺失。

**解决**：
```bash
# 逐步排查
python -c "import sys; print(sys.version)"  # 确认3.10+
pip install -e ".[dev]"  # 安装所有开发和测试依赖
python -m pytest tests/test_rnd_integration.py -v  # 详细输出
```

### 问题5：截图工具不可用

**安装截图工具**：
```bash
# 方法1: gnome-screenshot（推荐）
sudo apt install -y gnome-screenshot
gnome-screenshot -w -d 3  # 3秒延迟截取活动窗口

# 方法2: scrot（命令行截图）
sudo apt install -y scrot
scrot -d 3 screenshot.png  # 3秒后全屏截图

# 方法3: xfce4-screenshooter
sudo apt install -y xfce4-screenshooter
```

---

## 一键执行全部演示

```bash
# 进入项目并激活虚拟环境
cd ~/ctf_project/ai-ctf
source venv/bin/activate

echo "=== [1/6] Running Integration Tests ==="
python tests/test_rnd_integration.py

echo ""
echo "=== [2/6] Data Analysis Demo ==="
python scripts/screenshot_demos/demo_data_analysis.py

echo ""
echo "=== [3/6] MCP Server Registry Demo ==="
python scripts/screenshot_demos/demo_mcp.py

echo ""
echo "=== [4/6] Reasoning Explainability Demo ==="
python scripts/screenshot_demos/demo_reasoning.py

echo ""
echo "=== [5/6] Benchmark Framework Demo ==="
python scripts/screenshot_demos/demo_benchmark.py

echo ""
echo "=== [6/6] Sandbox & Deployment Demo ==="
python scripts/screenshot_demos/demo_sandbox.py

echo ""
echo "=== All demos completed! ==="
echo "Project structure:"
tree -L 2 -I '__pycache__|*.pyc|venv|.git|*.egg-info'
```

---

> **文档版本**：v2.0
> **生成日期**：2026-05-10
> **适用项目**：ai-ctf (commit 110b407)
> **关联论文**：`rnd_project_docs/毕业论文.md`（759行）
> **演示脚本目录**：`scripts/screenshot_demos/`（5个脚本，无需手动创建）