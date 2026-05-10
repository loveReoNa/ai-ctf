#!/usr/bin/env python3
"""模块三数据结构展示——Docker沙箱+靶机部署+日志收集

用途：毕业论文截图⑧——展示SandboxConfig/ChallengeDefinition/XBowConfig等数据结构
运行：cd <project_root> && source venv/bin/activate && python scripts/screenshot_demos/demo_sandbox.py
"""

from visualization_dashboard import (
    SandboxConfig, SandboxInfo, SandboxStatus,
    ChallengeDefinition,
    XBowConfig,
    LogCollector,
    BatchConfig,
)
from rich.console import Console
from rich.table import Table

console = Console()

print("=" * 60)
print("MODULE 3: VISUALIZATION DASHBOARD - DATA STRUCTURES")
print("=" * 60)

# Sandbox配置
configs = [
    SandboxConfig(image="ubuntu:22.04", memory_limit="1024m", cpu_limit="2.0"),
    SandboxConfig(image="kalilinux:latest", memory_limit="2048m", cpu_limit="4.0"),
    SandboxConfig(image="debian:bullseye", memory_limit="512m", cpu_limit="1.0"),
]
print(f"\n🏗️  SandboxConfig - {len(configs)} VM templates defined:")
for c in configs:
    print(f"    Image: {c.image:<20} Memory: {c.memory_limit:<8} CPU: {c.cpu_limit}")

# 沙箱实例
sandbox = SandboxInfo(
    container_id="ctf_web_001",
    name="sql_injection_lab",
    status=SandboxStatus.RUNNING,
    ip_address="172.17.0.5",
    ports={80: 8080, 3306: 3307}
)
print(f"\n📦 SandboxInfo (running):")
print(f"    ID: {sandbox.container_id}")
print(f"    Name: {sandbox.name}")
print(f"    Status: {sandbox.status.value}")
print(f"    IP: {sandbox.ip_address}")
print(f"    Ports: {sandbox.ports}")

# 挑战定义
challenges = [
    ChallengeDefinition(name="sql_injection_basic", category="web", difficulty="easy", ports=[80], flag_pattern=r"flag\{[a-f0-9]{32}\}", time_limit_seconds=600),
    ChallengeDefinition(name="xss_reflected", category="web", difficulty="medium", ports=[80], flag_pattern=r"flag\{[a-f0-9]{32}\}", time_limit_seconds=900),
    ChallengeDefinition(name="buffer_overflow_basic", category="pwn", difficulty="hard", ports=[1337], flag_pattern=r"flag\{[a-f0-9]{32}\}", time_limit_seconds=1200),
    ChallengeDefinition(name="rsa_weak_key", category="crypto", difficulty="medium", ports=[], flag_pattern=r"flag\{[a-f0-9]{32}\}", time_limit_seconds=600),
    ChallengeDefinition(name="elf_reverse", category="reverse", difficulty="hard", ports=[], flag_pattern=r"flag\{[a-f0-9]{32}\}", time_limit_seconds=600),
]

table = Table(title="Challenge Definitions (CTF靶机)", border_style="magenta")
table.add_column("Name", style="cyan")
table.add_column("Category", style="yellow")
table.add_column("Difficulty", style="red")
table.add_column("Ports")
table.add_column("Time(s)", justify="right")
for ch in challenges:
    table.add_row(ch.name, ch.category, ch.difficulty, str(ch.ports), str(ch.time_limit_seconds))
console.print(table)

# XBow配置
xb = XBowConfig(model_name="gpt-4", timeout_seconds=1800, retry_count=2)
print(f"\n🎯 XBowConfig: model={xb.model_name}, timeout={xb.timeout_seconds}s, retries={xb.retry_count}")

# 日志收集器
lc = LogCollector()
logs = [
    ("agent_output", "nmap scan started for 10.0.0.1"),
    ("tool_result", "Discovered open port 80/tcp on 10.0.0.1"),
    ("agent_reasoning", "Hypothesis: web vulnerability on port 80"),
    ("tool_result", "sqlmap detected SQL injection on /login.php"),
    ("agent_output", "Flag found: flag{sqli_hacked_2024}"),
]
for source, text in logs:
    lc.collect_agent_log(text, challenge_name="web_sqli", run_id="run_001")
summary = lc.get_summary()
print(f"\n📋 LogCollector: {summary.total_entries} log entries collected")

# 批量配置
batch = BatchConfig(
    name="full_benchmark_suite",
    challenges=challenges,
    model_name="gpt-4",
    max_workers=4,
    output_dir="./benchmark_results"
)
print(f"\n🚀 BatchConfig: {len(batch.challenges)} challenges, {batch.max_workers} workers, output={batch.output_dir}")

print(f"\n✅ Module 3 data structures verified!")