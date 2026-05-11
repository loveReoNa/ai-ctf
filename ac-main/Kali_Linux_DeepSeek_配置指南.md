# Kali Linux 上运行 CAI 项目并使用 DeepSeek API 完整指南

## 概述

本指南详细说明在 Kali Linux 2024/2025 上安装和配置 CAI (Cybersecurity AI) 项目，并使用 DeepSeek API 作为 AI 模型提供商的完整步骤。

## 系统要求

- **操作系统**: Kali Linux 2024.x 或 2025.x
- **Python版本**: Python 3.12+ (CAI 要求)
- **内存**: 至少 4GB RAM (推荐 8GB)
- **存储空间**: 至少 2GB 可用空间
- **网络**: 可访问互联网，能连接 DeepSeek API

## 第一步：系统准备和依赖安装

### 1.1 更新系统包

```bash
# 更新包列表
sudo apt update
sudo apt upgrade -y

# 安装基础开发工具
sudo apt install -y git curl wget build-essential
```

### 1.2 安装 Python 3.12 (如果未安装)

Kali Linux 默认可能使用 Python 3.11，需要安装 Python 3.12：

```bash
# 安装 Python 3.12 和相关开发包
sudo apt install -y python3.12 python3.12-venv python3.12-dev python3-pip

# 验证安装
python3.12 --version
# 应该显示: Python 3.12.x
```

如果系统没有 Python 3.12，可以从源码编译：

```bash
# 安装编译依赖
sudo apt install -y build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev libsqlite3-dev libbz2-dev

# 下载 Python 3.12
wget https://www.python.org/ftp/python/3.12.4/Python-3.12.4.tar.xz
tar -xf Python-3.12.4.tar.xz
cd Python-3.12.4

# 配置和编译
./configure --enable-optimizations
make -j$(nproc)
sudo make altinstall

# 验证
python3.12 --version
```

## 第二步：获取 DeepSeek API 密钥

### 2.1 注册 DeepSeek 账户

1. 访问 [DeepSeek 官网](https://platform.deepseek.com/)
2. 注册账户并登录
3. 进入 API 管理页面

### 2.2 获取 API 密钥

1. 在控制台创建新的 API 密钥
2. 复制密钥，格式类似：`sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

### 2.3 了解 API 端点

- **基础 URL**: `https://api.deepseek.com/v1`
- **可用模型**: `deepseek-chat`, `deepseek-coder` 等
- **定价**: 查看 DeepSeek 官方定价页面

## 第三步：安装 CAI 项目

### 3.1 克隆 CAI 仓库

```bash
# 克隆项目
git clone https://github.com/aliasrobotics/cai.git
cd cai

# 或者如果已有本地副本，确保更新
git pull origin main
```

### 3.2 创建虚拟环境

```bash
# 创建 Python 3.12 虚拟环境
python3.12 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 验证环境
python --version  # 应该显示 Python 3.12.x
which python      # 应该指向虚拟环境内的python
```

### 3.3 安装 CAI 依赖

```bash
# 升级 pip
pip install --upgrade pip

# 安装 CAI 框架
pip install cai-framework

# 或者从本地源码安装（开发模式）
# pip install -e .
```

### 3.4 验证安装

```bash
# 检查 CAI 是否安装成功
cai --version
# 或
python -c "import cai; print(cai.__version__)"
```

## 第四步：配置 DeepSeek API

### 4.1 创建配置文件

```bash
# 复制示例配置文件
cp .env.example .env

# 编辑 .env 文件
nano .env
```

### 4.2 配置 .env 文件内容

将 `.env` 文件修改为以下内容：

```bash
# DeepSeek API 配置
OPENAI_API_KEY="sk-your-deepseek-api-key-here"
OPENAI_BASE_URL="https://api.deepseek.com/v1"

# CAI 模型设置
CAI_MODEL="deepseek-chat"

# 其他配置
ANTHROPIC_API_KEY=""
OLLAMA=""
PROMPT_TOOLKIT_NO_CPR=1
CAI_STREAM=false
CAI_GUARDRAILS="true"
CAI_PRICE_LIMIT="0.01"
```

**重要说明**：
- 将 `sk-your-deepseek-api-key-here` 替换为你的实际 DeepSeek API 密钥
- `OPENAI_BASE_URL` 必须设置为 DeepSeek 的 API 端点
- `CAI_MODEL` 设置为 `deepseek-chat` 或你选择的其他 DeepSeek 模型

### 4.3 环境变量验证

```bash
# 测试环境变量加载
source .env
echo $OPENAI_API_KEY
echo $OPENAI_BASE_URL
```

## 第五步：测试 DeepSeek 集成

### 5.1 创建测试脚本

创建文件 `test_deepseek.py`：

```python
#!/usr/bin/env python3
"""
测试 DeepSeek API 集成
"""

import os
import asyncio
from dotenv import load_dotenv
from openai import AsyncOpenAI
from cai.sdk.agents import Agent, Runner, OpenAIChatCompletionsModel

# 加载环境变量
load_dotenv()

async def test_deepseek():
    print("🧪 测试 DeepSeek API 集成...")
    
    # 创建 DeepSeek 客户端
    client = AsyncOpenAI(
        base_url=os.getenv("OPENAI_BASE_URL"),
        api_key=os.getenv("OPENAI_API_KEY")
    )
    
    # 创建测试代理
    agent = Agent(
        name="DeepSeek测试代理",
        instructions="你是一个测试代理，请用中文回答",
        model=OpenAIChatCompletionsModel(
            model=os.getenv("CAI_MODEL", "deepseek-chat"),
            openai_client=client
        )
    )
    
    # 运行测试
    print("🤖 发送测试请求...")
    result = await Runner.run(agent, "你好，请用中文介绍一下你自己")
    
    print("✅ 测试成功!")
    print("响应内容:")
    print("-" * 40)
    print(result.final_output)
    print("-" * 40)
    
    return True

if __name__ == "__main__":
    asyncio.run(test_deepseek())
```

### 5.2 运行测试

```bash
# 确保在虚拟环境中
source venv/bin/activate

# 运行测试
python test_deepseek.py
```

预期输出应该显示 DeepSeek 的中文响应。

## 第六步：运行 CAI CTF 解题演示

### 6.1 创建 CTF 演示脚本

创建文件 `ctf_demo_deepseek.py`：

```python
#!/usr/bin/env python3
"""
使用 DeepSeek API 的 CTF 解题演示
"""

import os
import asyncio
from dotenv import load_dotenv
from openai import AsyncOpenAI
from cai.sdk.agents import Agent, Runner, OpenAIChatCompletionsModel, function_tool
from cai.tools.common import run_command

# 加载配置
load_dotenv()

@function_tool
def execute_command(cmd: str) -> str:
    """执行系统命令"""
    try:
        return run_command(cmd)
    except Exception as e:
        return f"命令执行失败: {str(e)}"

async def main():
    print("🎯 CAI CTF 解题演示 - 使用 DeepSeek API")
    print("=" * 50)
    
    # 创建 DeepSeek 客户端
    client = AsyncOpenAI(
        base_url=os.getenv("OPENAI_BASE_URL"),
        api_key=os.getenv("OPENAI_API_KEY")
    )
    
    # 创建 CTF 代理
    ctf_agent = Agent(
        name="CTF解题代理",
        description="使用 DeepSeek 模型的 CTF 解题专家",
        instructions="""你是一名网络安全专家，专门解决 CTF 挑战。
        你可以使用提供的工具执行命令。
        请用中文思考和回答。""",
        tools=[execute_command],
        model=OpenAIChatCompletionsModel(
            model=os.getenv("CAI_MODEL", "deepseek-chat"),
            openai_client=client
        )
    )
    
    # 演示 1: 基本信息收集
    print("\n1️⃣ 演示: 系统信息收集")
    result1 = await Runner.run(ctf_agent, "查看当前目录的文件列表")
    print(f"结果: {result1.final_output[:200]}...")
    
    # 演示 2: 网络扫描
    print("\n2️⃣ 演示: 网络扫描")
    result2 = await Runner.run(ctf_agent, "扫描本地主机的开放端口")
    print(f"结果: {result2.final_output[:200]}...")
    
    # 演示 3: CTF 解题
    print("\n3️⃣ 演示: CTF 解题思路")
    result3 = await Runner.run(ctf_agent, """
    假设你发现一个 Web 靶机，URL 是 http://192.168.1.100
    请给出解题思路：
    1. 如何进行信息收集
    2. 可能存在的漏洞类型
    3. 如何验证和利用
    """)
    print(f"结果: {result3.final_output[:300]}...")
    
    print("\n✅ 演示完成!")
    print("DeepSeek API 集成成功!")

if __name__ == "__main__":
    asyncio.run(main())
```

### 6.2 运行演示

```bash
# 运行演示脚本
python ctf_demo_deepseek.py
```

## 第七步：使用 CAI 命令行界面

### 7.1 启动 CAI 交互界面

```bash
# 确保在虚拟环境中且已激活 .env
source venv/bin/activate
source .env

# 启动 CAI
cai
```

在 CAI 交互界面中，你可以：
- 输入自然语言指令
- 使用 `/help` 查看帮助
- 使用 `/config` 查看配置
- 直接进行 CTF 解题

### 7.2 命令行直接运行

```bash
# 单次运行模式
cai --continue --prompt "扫描本地网络，找出开放端口"

# 指定目标
cai --continue --prompt "对 http://testphp.vulnweb.com 进行安全测试"
```

## 第八步：故障排除

### 8.1 常见问题及解决方案

#### 问题1: Python 版本错误
```
错误: CAI requires Python 3.12+
```
**解决**：
```bash
# 确认 Python 版本
python3.12 --version

# 如果未安装，参考第一步安装 Python 3.12
```

#### 问题2: API 连接失败
```
错误: 401 Unauthorized
```
**解决**：
1. 检查 API 密钥是否正确
2. 确认 `.env` 文件中的 `OPENAI_API_KEY` 和 `OPENAI_BASE_URL`
3. 测试 API 密钥：
```bash
curl -X POST https://api.deepseek.com/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "deepseek-chat", "messages": [{"role": "user", "content": "Hello"}]}'
```

#### 问题3: 模块导入错误
```
错误: No module named 'cai'
```
**解决**：
```bash
# 确保在虚拟环境中
source venv/bin/activate

# 重新安装 CAI
pip install --force-reinstall cai-framework
```

#### 问题4: 权限问题
```
错误: Permission denied
```
**解决**：
```bash
# 确保有执行权限
chmod +x *.py

# 对于网络扫描工具，可能需要 sudo
sudo apt install -y nmap
```

### 8.2 调试模式

```bash
# 启用详细日志
export CAI_DEBUG=2
cai

# 或直接运行 Python 脚本
python -m cai.cli --debug
```

## 第九步：高级配置

### 9.1 使用多个模型

创建 `.env.multi` 文件：

```bash
# DeepSeek 配置
DEEPSEEK_API_KEY="sk-xxx"
DEEPSEEK_BASE_URL="https://api.deepseek.com/v1"

# OpenAI 配置（备用）
OPENAI_API_KEY="sk-yyy"
OPENAI_BASE_URL="https://api.openai.com/v1"

# 模型选择
CAI_MODEL="deepseek-chat"
```

### 9.2 配置代理（如果需要）

```bash
# 在 .env 中添加
HTTP_PROXY="http://your-proxy:port"
HTTPS_PROXY="http://your-proxy:port"
```

### 9.3 性能优化

```bash
# 调整并发数
export CAI_MAX_CONCURRENT=3

# 设置超时
export CAI_TIMEOUT=30

# 启用缓存
export CAI_CACHE_ENABLED=true
```

## 第十步：安全注意事项

### 10.1 API 密钥安全

1. **不要提交密钥到版本控制**：
```bash
# 确保 .env 在 .gitignore 中
echo ".env" >> .gitignore
```

2. **使用环境变量而非硬编码**：
```bash
# 正确做法
export DEEPSEEK_API_KEY="your-key"
cai

# 错误做法：在代码中硬编码密钥
```

3. **定期轮换密钥**：定期在 DeepSeek 控制台更新 API 密钥

### 10.2 操作安全

1. **仅在授权范围内测试**：不要扫描未经授权的目标
2. **使用防护栏**：CAI 内置防护栏可防止危险操作
3. **人在回路**：重要操作前人工确认

## 附录

### A. 常用命令速查

```bash
# 环境管理
source venv/bin/activate          # 激活虚拟环境
deactivate                          # 退出虚拟环境

# 项目操作
git pull origin main                # 更新代码
pip install -r requirements.txt     # 安装依赖

# CAI 操作
cai                                 # 启动交互界面
cai --version                       # 查看版本
cai --help                          # 查看帮助

# 测试
python test_deepseek.py             # 测试 API
python -m pytest tests/             # 运行测试
```

### B. 资源链接

1. **CAI 项目**：
   - GitHub: https://github.com/aliasrobotics/cai
   - 文档: https://cai.aliasrobotics.com

2. **DeepSeek API**：
   - 官网: https://platform.deepseek.com
   - API 文档: https://platform.deepseek.com/api-docs

3. **Kali Linux**：
   - 官网: https://www.kali.org
   - 文档: https://www.kali.org/docs

### C. 联系支持

- **GitHub Issues**: https://github.com/aliasrobotics/cai/issues
- **Discord**: CAI 社区频道
- **邮箱**: cai@aliasrobotics.com

---

**最后更新**: 2026年3月15日  
**适用版本**: CAI v0.4.0+, Kali Linux 2024+, DeepSeek API v1

**提示**: 如果在安装过程中遇到问题，请查看 CAI 项目的 GitHub Issues 或联系社区支持。祝你使用愉快！