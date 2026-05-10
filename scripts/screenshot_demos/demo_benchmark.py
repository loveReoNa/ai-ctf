#!/usr/bin/env python3
"""模块二展示——工具封装+输出清洗+分类体系

用途：毕业论文截图⑦——展示15+安全工具按5类分类、Flag掩码处理、ANSI转义码清洗
运行：cd <project_root> && source venv/bin/activate && python scripts/screenshot_demos/demo_benchmark.py
"""

from benchmark_framework import (
    ToolWrapper, OutputSanitizer, FlagMaskingSanitizer,
    ToolCategory, ToolClassifier,
)
from rich.console import Console
from rich.table import Table

console = Console()
print("=" * 60)
print("MODULE 2: BENCHMARK FRAMEWORK - Tool Classification & Sanitization")
print("=" * 60)

# Flag掩码处理
sanitizer = FlagMaskingSanitizer()
test_outputs = [
    "Scan complete. Found flag{ctf_2024_sqli_success} in /var/www/html",
    "Credentials: admin:password123 flag{hidden_in_logs}",
    "Normal output without any flag",
    "flag{another_one} and flag{yet_another} found",
]
print("\n🔒 FLAG MASKING SANITIZER:")
for out in test_outputs:
    clean = sanitizer.sanitize(out)
    has = sanitizer.has_sensitive_data(out)
    status = "🔴 SENSITIVE" if has else "🟢 CLEAN"
    print(f"  {status} | Raw: {out[:50]}...")
    print(f"           Cleaned: {clean[:50]}...")
    print()

# 工具分类体系
classifier = ToolClassifier()
tools_to_classify = [
    "nmap", "masscan", "dnsrecon", "whois", "gobuster", "dirb",
    "enum4linux", "metasploit", "searchsploit", "sqlmap", "hydra",
    "john", "hashcat", "netcat", "linpeas", "find"
]

batch_groups = classifier.classify_batch(tools_to_classify)

table = Table(title="Tool Classification System (15+ tools)", border_style="blue")
table.add_column("Category", style="cyan bold")
table.add_column("Tools", style="green")
table.add_column("Count", justify="right", style="yellow")

category_names = {
    ToolCategory.RECONNAISSANCE: "🔍 Reconnaissance",
    ToolCategory.ENUMERATION: "📋 Enumeration",
    ToolCategory.EXPLOITATION: "💥 Exploitation",
    ToolCategory.POST_EXPLOITATION: "🔧 Post-Exploitation",
    ToolCategory.FLAG_CAPTURE: "🏁 Flag Capture",
}

for cat, names in batch_groups.items():
    cat_name = category_names.get(cat, cat.value)
    tool_list = ", ".join(names)
    table.add_row(cat_name, tool_list, str(len(names)))

console.print(table)

# OutputSanitizer - ANSI转义码清洗
ansi_sanitizer = OutputSanitizer()
dirty_output = "\x1b[31mERROR: Connection refused\x1b[0m\n\x1b[33m[WARNING]\x1b[0m Retry in 5s..."
clean_output = ansi_sanitizer.sanitize(dirty_output)
print(f"\n🧹 OUTPUT SANITIZER (ANSI escape code removal):")
print(f"  Raw:    {repr(dirty_output)[:80]}")
print(f"  Clean:  {repr(clean_output)[:80]}")

print(f"\n✅ Benchmark Framework verified!")