#!/usr/bin/env python3
"""推理可解释性演示——Rich终端面板+Prompt模板渲染

用途：
  截图④——Rich推理面板(蓝色Panel，展示Agent的WHAT+HOW+WHY层)
  截图⑤——Rich结果面板(绿色成功+红色失败Panel)
  截图⑥——五阶段攻击进度指示器(品红色Panel)
  截图⑨——Prompt模板渲染输出+Token消耗表

运行：cd <project_root> && source venv/bin/activate && python scripts/screenshot_demos/demo_reasoning.py
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from mcp_integration.prompts.prompt_manager import PromptManager

console = Console(width=100)

# ================================================================
# 截图④：推理面板（蓝色Panel）- 展示Agent的WHY层思考
# ================================================================
console.print("\n")
reasoning_content = Text()
reasoning_content.append("📍 Current Situation:\n", style="bold white")
reasoning_content.append("  Attack Phase: RECONNAISSANCE\n")
reasoning_content.append("  Access Level: None (external)\n")
reasoning_content.append("  Discovered: Port 80 (Apache/2.4.41), Port 22 (OpenSSH 8.2)\n")
reasoning_content.append("  Attempted: TCP SYN scan complete\n\n")
reasoning_content.append("💡 Core Hypothesis:\n", style="bold white")
reasoning_content.append("  Target likely runs a vulnerable web application on port 80.\n")
reasoning_content.append("  Apache 2.4.41 has known path traversal vulnerabilities.\n")
reasoning_content.append("  Confidence: ", style="bold")
reasoning_content.append("72%", style="bold yellow")
reasoning_content.append(" (moderate - requires further enumeration)\n")
reasoning_content.append("  Evidence: Version string from HTTP banner, no WAF detected\n")
reasoning_content.append("  Risk Level: ", style="bold")
reasoning_content.append("MEDIUM", style="bold yellow")
reasoning_content.append("\n\n🎯 Selected Action:\n", style="bold white")
reasoning_content.append("  Tool: ", style="bold")
reasoning_content.append("gobuster_dir_scan\n", style="bold green")
reasoning_content.append("  Reason: Need to discover hidden directories before attempting exploitation\n")
reasoning_content.append("  Parameters: {\"url\": \"http://10.0.0.1\", \"wordlist\": \"common.txt\"}\n\n")
reasoning_content.append("🔄 Alternatives Considered:\n", style="dim white")
reasoning_content.append("  ✗ nmap_vuln_scan - too broad, better suited after service identification\n", style="dim")
reasoning_content.append("  ✗ sqlmap_scan - premature, no confirmation of SQL backend yet\n", style="dim")
reasoning_content.append("⏱ Expected Outcome: List of hidden paths/directories for further analysis", style="italic cyan")

panel_reasoning = Panel(
    reasoning_content,
    title="[bold]🧠 Agent Reasoning - Round #3[/bold]",
    border_style="blue",
    padding=(1, 2)
)
console.print(panel_reasoning)

# ================================================================
# 截图⑤：结果面板（绿色=成功，红色=失败）
# ================================================================

# 成功结果面板（绿色）
success_content = Text()
success_content.append("🔧 Tool: gobuster_dir_scan\n", style="bold")
success_content.append("⏱  Execution Time: 12.4s\n")
success_content.append("📋 Result Summary:\n", style="bold")
success_content.append("  Found 8 directories:\n")
success_content.append("    /admin (HTTP 200)\n")
success_content.append("    /login (HTTP 200)\n")
success_content.append("    /uploads (HTTP 403)\n")
success_content.append("    /backup (HTTP 200) ← INTERESTING!\n")
success_content.append("    /config (HTTP 403)\n")
success_content.append("    /api (HTTP 200)\n")
success_content.append("    /wp-admin (HTTP 200)\n")
success_content.append("    /.git (HTTP 403)\n\n")
success_content.append("🧪 Result vs Expected: ", style="bold")
success_content.append("✅ MATCH", style="bold green")
success_content.append(" - Directories discovered successfully\n")
success_content.append("💡 New finding: /backup directory accessible - potential sensitive data exposure", style="italic")

panel_success = Panel(
    success_content,
    title="[bold]✅ Tool Execution Result[/bold]",
    border_style="green",
    padding=(1, 2)
)
console.print(panel_success)
console.print("")

# 失败结果面板（红色）
fail_content = Text()
fail_content.append("🔧 Tool: sqlmap_inject\n", style="bold")
fail_content.append("⏱  Execution Time: 45.2s\n")
fail_content.append("📋 Error Summary:\n", style="bold")
fail_content.append("  Target URL returned HTTP 404\n")
fail_content.append("  Injection point not found\n")
fail_content.append("  Error type: network_error\n\n")
fail_content.append("🧪 Result vs Expected: ", style="bold")
fail_content.append("❌ MISMATCH", style="bold red")
fail_content.append(" - Expected SQL injection detection\n")
fail_content.append("💡 Interpretation: Target endpoint does not accept POST requests. ", style="italic")
fail_content.append("Need to identify correct parameterized URL first.", style="italic")

panel_fail = Panel(
    fail_content,
    title="[bold]❌ Tool Execution Result[/bold]",
    border_style="red",
    padding=(1, 2)
)
console.print(panel_fail)

# ================================================================
# 截图⑥：五阶段攻击进度指示器
# ================================================================
console.print("\n")

phase_panel_content = Text()
phases = [
    ("RECONNAISSANCE", "侦察", "███░░░░░░░  30%", "green", "nmap scan complete"),
    ("ENUMERATION",   "枚举", "██░░░░░░░░  20%", "yellow", "in progress - gobuster running"),
    ("EXPLOITATION",  "利用", "░░░░░░░░░░   0%", "dim", "waiting"),
    ("POST_EXPLOIT",  "后渗透","░░░░░░░░░░   0%", "dim", "waiting"),
    ("FLAG_CAPTURE",  "Flag", "░░░░░░░░░░   0%", "dim", "waiting"),
]
for phase_name, label, bar, color, note in phases:
    if color == "green":
        phase_panel_content.append(f"✅ {phase_name:<16} [{bar}] ", style=color)
    elif color == "yellow":
        phase_panel_content.append(f"▶  {phase_name:<16} [{bar}] ", style="bold yellow")
    else:
        phase_panel_content.append(f"⬜ {phase_name:<16} [{bar}] ", style="dim")
    phase_panel_content.append(f"{note}\n", style="dim")

panel_phase = Panel(
    phase_panel_content,
    title="[bold]🎯 Attack Phase Progress[/bold]",
    border_style="magenta",
    padding=(1, 2)
)
console.print(panel_phase)

# ================================================================
# 截图⑨：Prompt模板渲染输出
# ================================================================
console.print("\n")
console.print("=" * 60)
console.print("[bold]PROMPT TEMPLATE RENDERING (ctf_solver_default)[/bold]")
console.print("=" * 60)

pm = PromptManager()
prompt_text = pm.get_ctf_prompt_with_tools("web", [])
# 输出前10行作为示例展示
lines = prompt_text.split('\n')
console.print(f"[dim]Template length: {len(prompt_text)} characters[/dim]")
console.print(f"[dim]Showing first 20 lines of {len(lines)}:[/dim]")
console.print("-" * 60)
for line in lines[:20]:
    console.print(f"  {line}")

console.print(f"\n[dim]... ({len(lines) - 20} more lines)[/dim]")
console.print(f"\n[bold green]✅ 4 templates available: ctf_solver_default, naive_baseline, tool_rich, explainable_chain_of_thought[/bold green]")

# Token消耗概览表
console.print("\n")
token_table = Table(title="Token Consumption Overview (Sample Run)", border_style="blue")
token_table.add_column("Component", style="cyan")
token_table.add_column("Tokens", justify="right", style="green")
token_table.add_column("Percentage", justify="right", style="yellow")
token_table.add_row("System Prompt (含工具描述)", "520", "12.5%")
token_table.add_row("Tool Descriptions", "680", "16.3%")
token_table.add_row("LLM Reasoning Output", "2,450", "58.8%")
token_table.add_row("Tool Return Text", "520", "12.5%")
token_table.add_row("Total", "4,170", "100.0%")
console.print(token_table)

console.print("\n[bold green]✅ Reasoning Explainability Demo Complete![/bold green]")