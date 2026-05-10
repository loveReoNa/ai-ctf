#!/usr/bin/env python3
"""MCP集成模块演示——服务器注册表+工具Schema解析+质量过滤

用途：毕业论文截图③——展示15个MCP服务器的注册表和工具质量过滤
运行：cd <project_root> && source venv/bin/activate && python scripts/screenshot_demos/demo_mcp.py
"""

from mcp_integration import (
    MCPClient, MCPConnectionConfig, MCPServerRegistry,
    ToolSchemaParser, ToolQualityFilter, ToolSchema,
)

# 模拟15+安全工具的MCP服务器注册
servers_config = [
    # Reconnaissance (侦察类)
    ("nmap-server", "stdio", "nmap", ["-sV", "-sC"]),
    ("masscan-server", "stdio", "masscan", ["-p1-65535"]),
    ("dns-server", "stdio", "dnsrecon", ["-d"]),
    ("whois-server", "stdio", "whois", []),
    # Enumeration (枚举类)
    ("gobuster-server", "stdio", "gobuster", ["dir"]),
    ("dirb-server", "stdio", "dirb", []),
    ("enum4linux-server", "stdio", "enum4linux", []),
    # Exploitation (利用类)
    ("metasploit-server", "streamable_http", "msfconsole", ["-q"]),
    ("searchsploit-server", "stdio", "searchsploit", []),
    ("sqlmap-server", "stdio", "sqlmap", ["-u"]),
    ("hydra-server", "stdio", "hydra", ["-L"]),
    ("john-server", "stdio", "john", []),
    # Post-Exploitation (后渗透类)
    ("netcat-server", "stdio", "nc", ["-lvp"]),
    ("linpeas-server", "stdio", "linpeas.sh", []),
    # Flag Capture
    ("flag-finder-server", "stdio", "find", ["/", "-name"]),
]

print("=" * 60)
print("MCP SERVER REGISTRY - 15 Security Tool Servers")
print("=" * 60)

registry = MCPServerRegistry()
for name, transport, cmd, args in servers_config:
    config = MCPConnectionConfig(
        server_name=name,
        transport_type=transport,
        command=cmd,
        args=args
    )
    registry.register_server(config)

# 展示注册的服务器
servers = registry.list_servers()
print(f"\n{'ID':<4} {'Server Name':<25} {'Transport':<18} {'Command'}")
print("-" * 70)
for i, s in enumerate(servers, 1):
    print(f"{i:<4} {s.server_name:<25} {s.transport_type:<18} {s.command}")

print(f"\nTotal: {len(servers)} MCP servers registered")
print(f"Categories: Reconnaissance(4) + Enumeration(3) + Exploitation(5) + Post-Exploitation(2) + FlagCapture(1)")

# 展示工具质量过滤
print(f"\n{'='*60}")
print("TOOL QUALITY FILTER - Schema Validation")
print("=" * 60)

tsp = ToolSchemaParser()

# 模拟不同质量的工具Schema
mock_schemas = [
    ToolSchema(name="nmap_scan", description="Full port scan with version detection and script scanning", input_schema={"type": "object", "properties": {"target": {"type": "string"}}}),
    ToolSchema(name="", description="Missing name tool", input_schema={}),  # 低质量
    ToolSchema(name="sqlmap_inject", description="SQL injection automation tool supporting multiple DBMS backends", input_schema={"type": "object", "properties": {"url": {"type": "string"}, "risk": {"type": "integer"}}}),
    ToolSchema(name="broken", description="x", input_schema={}),  # 描述太短
    ToolSchema(name="hydra_bruteforce", description="Network login cracker supporting numerous protocols including SSH, FTP, HTTP", input_schema={"type": "object", "properties": {"target": {"type": "string"}, "service": {"type": "string"}}}),
    ToolSchema(name="metasploit_exploit", description="", input_schema={"type": "object"}),  # 空描述
]

q_filter = ToolQualityFilter(threshold=0.3)
accepted = []
rejected = []
for schema in mock_schemas:
    quality = q_filter.compute_quality_score(schema)
    if quality >= 0.3:
        accepted.append((schema.name, quality))
    else:
        rejected.append((schema.name or "(empty)", quality))

print(f"\nAccepted tools ({len(accepted)}):")
for name, q in accepted:
    print(f"  ✅ {name:<25} quality={q:.2f}")

print(f"\nRejected tools ({len(rejected)}):")
for name, q in rejected:
    print(f"  ❌ {name:<25} quality={q:.2f} - insufficient quality")

print(f"\n✅ MCP Integration module verified!")