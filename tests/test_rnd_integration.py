"""Integration test for rnd_project modules: data_analysis, mcp_integration, benchmark_framework, visualization_dashboard."""
import json
import os
import tempfile

# === Test 1: data_analysis full pipeline ===
print("=" * 60)
print("Test 1: Data Analysis Pipeline (Parse -> Metrics -> Baseline -> Report)")
print("=" * 60)

from data_analysis import LogParser, MetricsEngine, BaselineManager, ReportGenerator, ReportConfig, create_sample_charts

# 1. Parse sample sessions using parse_agent_log
parser = LogParser()
session_data = [
    ("flag{sqli_solved} success\nSolved in 300s, 8 tool calls, 500 tokens", "web_sqli_1", "gpt-4", "web", "sqli", "medium"),
    ("flag{xss_found} success\nSolved in 180s, 5 tool calls, 300 tokens", "web_xss_1", "gpt-4", "web", "xss", "easy"),
    ("Failed to solve - timeout after 600s, 15 tool calls, 800 tokens", "pwn_overflow_1", "gpt-4", "pwn", "buffer_overflow", "hard"),
    ("flag{crypto_aes} success\nSolved in 420s, 12 tool calls, 700 tokens", "crypto_aes_1", "gpt-4", "crypto", "aes", "hard"),
    ("flag{rev_patch} success\nSolved in 240s, 6 tool calls, 400 tokens", "rev_bin_1", "gpt-4", "reverse", "binary_patching", "medium"),
]
for log_text, ch_name, m_name, cat, vtype, diff in session_data:
    parser.parse_agent_log(log_text, challenge_name=ch_name, model_name=m_name,
                           category=cat, vuln_type=vtype, difficulty=diff)

sessions = parser.get_sessions()
summary = parser.get_summary()
print(f"  LogParser: {len(sessions)} sessions, {summary.success_count}/{summary.total_sessions} successful")
assert summary.total_sessions == 5
assert summary.success_count == 4

# 2. Calculate metrics (9-metric system)
engine = MetricsEngine()
metrics = engine.calculate_metrics(sessions)
print(f"  MetricsEngine: accuracy={metrics.accuracy:.2f}, F1={metrics.f1_score:.2f}, flags={metrics.total_flags}")
print(f"    Efficiency: completion={metrics.efficiency.task_completion_rate:.1f}%, solve_time={metrics.efficiency.avg_solve_time_seconds:.0f}s")
print(f"    Intelligence: first_success={metrics.intelligence.first_attempt_success_rate:.1f}%, hallucination={metrics.intelligence.hallucination_rate:.1f}%")
print(f"    Coverage: type_coverage={metrics.coverage.challenge_type_coverage:.1f}%, mastered={len(metrics.coverage.vuln_types_mastered)}/{metrics.coverage.total_vuln_types}")
assert metrics.total_flags == 4
assert metrics.accuracy > 0.7

# 3. Baseline comparison
bm = BaselineManager()
comp = bm.compare_to_baselines("integration_test", sessions)
print(f"  BaselineManager: {len(comp.comparisons)} baselines compared")
for name in list(comp.comparisons.keys())[:3]:
    print(f"    vs {name}: {json.dumps(comp.comparisons[name], default=str)[:120]}")
assert len(comp.comparisons) == 5

# 4. Charts and reports
with tempfile.TemporaryDirectory() as tmpdir:
    charts = create_sample_charts(output_dir=tmpdir)
    print(f"  Visualization: {len(charts)} charts generated")
    assert len(charts) > 0

    rg = ReportGenerator(ReportConfig(output_dir=tmpdir))
    result_paths = rg.generate_report(sessions, metrics, "gpt-4", chart_files=charts)
    print(f"  ReportGenerator:")
    for key, path in result_paths.items():
        if os.path.exists(path):
            print(f"    {key}: {os.path.basename(path)} ({os.path.getsize(path)} bytes)")
            assert os.path.getsize(path) > 0, f"{key} report is empty"
    assert "json" in result_paths or len(result_paths) >= 1

print()

# === Test 2: benchmark_framework imports and basic usage ===
print("=" * 60)
print("Test 2: Benchmark Framework Module")
print("=" * 60)

from benchmark_framework import (
    ToolWrapper, OutputSanitizer, FlagMaskingSanitizer,
    LiveMCPBenchParser, ParsedBenchmarkRun,
    ToolCategory, ToolClassifier,
)

# ToolWrapper - basic operations
tw = ToolWrapper("nmap")
tw.set_sanitizer(FlagMaskingSanitizer())
print(f"  ToolWrapper: created for 'nmap', has_sanitizer={tw.set_sanitizer is not None}")

# FlagMaskingSanitizer
sanitizer = FlagMaskingSanitizer()
clean = sanitizer.sanitize("Found flag{test123} and more")
print(f"  Sanitizer: input -> '{clean}'")
assert "test123" not in clean, f"Flag value should be masked, got: {clean}"

sanitizer2 = FlagMaskingSanitizer()
print(f"  has_sensitive_data('flag{{secret}}'): {sanitizer2.has_sensitive_data('flag{{secret}}')}")
assert sanitizer2.has_sensitive_data("flag{secret}") is True

# LiveMCPBenchParser
parser_bench = LiveMCPBenchParser()
print(f"  LiveMCPBenchParser: methods={[m for m in dir(parser_bench) if not m.startswith('_')]}")

# ToolClassifier
classifier = ToolClassifier()
cat = classifier.classify("nmap")
print(f"  ToolClassifier: nmap -> {cat.value}")
assert cat == ToolCategory.RECONNAISSANCE

# classify_batch
batch_groups = classifier.classify_batch(["nmap", "sqlmap", "hydra", "netcat"])
items_str = []
for cat_name, names in batch_groups.items():
    for name in names:
        items_str.append(f"{name}:{cat_name.value}")
print(f"  classify_batch: {', '.join(items_str)}")

print()

# === Test 3: mcp_integration imports and operations ===
print("=" * 60)
print("Test 3: MCP Integration Module")
print("=" * 60)

from mcp_integration import (
    MCPClient, MCPConnectionConfig, ToolSchema, ToolCallResult,
    MCPServerRegistry, LiveMCPBenchLoader,
    ToolSchemaParser, ToolQualityFilter,
    CTFAgentOrchestrator, RunConfig, RunSummary,
    PromptManager,
    AgentState, AttackPhase, ErrorRecord, VulnInfo,
    LoggedToolCall, TokenUsage,
)

# MCPConnectionConfig
config = MCPConnectionConfig(
    server_name="test_nmap",
    transport_type="stdio",
    command="nmap",
    args=["--script", "vuln"]
)
print(f"  MCPConnectionConfig: server={config.server_name}, transport={config.transport_type}")
assert config.server_name == "test_nmap"

# MCPServerRegistry
registry = MCPServerRegistry()
registry.register_server(config)
servers = registry.list_servers()
print(f"  MCPServerRegistry: {len(servers)} server(s) registered")
assert len(servers) == 1

# ToolSchemaParser
tsp = ToolSchemaParser()
# ToolSchema uses input_schema not parameters
schema = ToolSchema(name="nmap_scan", description="Network scanner", input_schema={})
func_def = tsp.parse_schema_to_function_def(schema)
print(f"  ToolSchemaParser: parsed schema for '{func_def.get('name', 'unknown')}'")

# PromptManager
pm = PromptManager()
template = pm.get_template("ctf_attack_v1")
if template:
    prompt_text = template.content
else:
    prompt_text = pm.get_ctf_prompt_with_tools("web", [])
print(f"  PromptManager: prompt loaded, length={len(prompt_text)}")

# Schema dataclasses - use actual field names
state = AgentState()
state.current_phase = AttackPhase.RECONNAISSANCE
print(f"  AgentState: phase={state.current_phase.value}")

# TokenUsage uses input_tokens/output_tokens not prompt_tokens/completion_tokens
token_usage = TokenUsage(input_tokens=150, output_tokens=50)
assert token_usage.total_tokens == 200

# LoggedToolCall uses result not output, no timestamp_utc
tool_call = LoggedToolCall(
    tool_name="nmap",
    arguments={"target": "10.0.0.1"},
    result="Open ports: 22, 80, 443",
    success=True,
    token_usage=token_usage,
)
print(f"  LoggedToolCall: tool={tool_call.tool_name}, success={tool_call.success}, tokens={tool_call.token_usage.total_tokens}")

# RunConfig
run_config = RunConfig(
    max_turns=50,
    max_time_seconds=3600,
    target_host="10.0.0.1",
    model_name="gpt-4"
)
print(f"  RunConfig: target={run_config.target_host}, max_turns={run_config.max_turns}")

print()

# === Test 4: visualization_dashboard imports and operations ===
print("=" * 60)
print("Test 4: Visualization Dashboard Module")
print("=" * 60)

from visualization_dashboard import (
    SandboxManager, SandboxConfig, SandboxInfo, SandboxStatus,
    ChallengeDefinition, DeployedChallenge, TargetDeployer,
    XBowRunner, XBowConfig, XBowRunResult,
    LogCollector, CollectedLog, LogCollectionSummary,
    BatchRunner, BatchConfig, BatchRunResult,
)

# SandboxConfig
sb_config = SandboxConfig(image="ubuntu:22.04", memory_limit="1024m", cpu_limit="2.0")
print(f"  SandboxConfig: image={sb_config.image}, memory={sb_config.memory_limit}")

# SandboxInfo
sb_info = SandboxInfo(
    container_id="abc123",
    name="ctf_sandbox_1",
    status=SandboxStatus.RUNNING,
    ip_address="172.17.0.2",
    ports={22: 2222, 80: 8080}
)
print(f"  SandboxInfo: id={sb_info.container_id}, status={sb_info.status.value}, ip={sb_info.ip_address}")

from datetime import datetime as dt

# ChallengeDefinition
challenge = ChallengeDefinition(
    name="sql_injection_basic",
    category="web",
    difficulty="easy",
    ports=[80],
    flag_pattern=r"flag\{[a-f0-9]{32}\}",
    time_limit_seconds=600
)
print(f"  ChallengeDefinition: name={challenge.name}, category={challenge.category}")

# XBowConfig
xb_config = XBowConfig(
    model_name="gpt-4",
    timeout_seconds=1800,
    retry_count=2
)
print(f"  XBowConfig: model={xb_config.model_name}, timeout={xb_config.timeout_seconds}s")

# LogCollector
lc = LogCollector()
log = CollectedLog(
    source="agent_output",
    challenge_name="test",
    run_id="run1",
    timestamp=dt.now(),
    raw_text="All tasks completed"
)
lc.collect_agent_log(log.raw_text, challenge_name=log.challenge_name, run_id=log.run_id)
summary_log = lc.get_summary()
print(f"  LogCollector: {summary_log.total_entries} log(s)")

# BatchConfig
batch_cfg = BatchConfig(
    name="batch_test",
    challenges=[challenge],
    model_name="gpt-4",
    max_workers=2,
    output_dir="./batch_results"
)
print(f"  BatchConfig: {len(batch_cfg.challenges)} challenges, workers={batch_cfg.max_workers}")

print()
print("=" * 60)
print("=== ALL MODULE INTEGRATION TESTS PASSED ===")
print("=" * 60)