"""Inspect all module APIs to understand actual method signatures."""
import inspect

print("=== LogParser ===")
from data_analysis.log_parser import LogParser
print("Methods:", [m for m in dir(LogParser) if not m.startswith('_')])

print("\n=== ToolWrapper ===")
from benchmark_framework.tool_wrapper import ToolWrapper
print("Methods:", [m for m in dir(ToolWrapper) if not m.startswith('_')])

print("\n=== FlagMaskingSanitizer ===")
from benchmark_framework.output_sanitizer import FlagMaskingSanitizer
print("Methods:", [m for m in dir(FlagMaskingSanitizer) if not m.startswith('_')])

print("\n=== LiveMCPBenchParser ===")
from benchmark_framework.parsers import LiveMCPBenchParser
print("Methods:", [m for m in dir(LiveMCPBenchParser) if not m.startswith('_')])

print("\n=== ToolClassifier ===")
from benchmark_framework.tool_category import ToolClassifier
print("Methods:", [m for m in dir(ToolClassifier) if not m.startswith('_')])

print("\n=== MCPConnectionConfig ===")
from mcp_integration import MCPConnectionConfig
print("Fields:", [f.name for f in MCPConnectionConfig.__dataclass_fields__.values()])

print("\n=== MCPServerRegistry ===")
from mcp_integration.mcp_server_registry import MCPServerRegistry
print("Methods:", [m for m in dir(MCPServerRegistry) if not m.startswith('_')])

print("\n=== ToolSchemaParser ===")
from mcp_integration.tool_schema_parser import ToolSchemaParser
print("Methods:", [m for m in dir(ToolSchemaParser) if not m.startswith('_')])

print("\n=== PromptManager ===")
from mcp_integration.prompts.prompt_manager import PromptManager
print("Methods:", [m for m in dir(PromptManager) if not m.startswith('_')])

print("\n=== LogCollector ===")
from visualization_dashboard.log_collector import LogCollector
print("Methods:", [m for m in dir(LogCollector) if not m.startswith('_')])

print("\n=== CollectedLog ===")
from visualization_dashboard.log_collector import CollectedLog
print("Fields:", [f.name for f in CollectedLog.__dataclass_fields__.values()])

print("\n=== MetricsEngine.calculate_metrics ===")
from data_analysis.metrics_engine import MetricsEngine
print(inspect.signature(MetricsEngine.calculate_metrics))

print("\n=== BaselineManager.compare_to_baselines ===")
from data_analysis.baseline import BaselineManager
print("Methods:", [m for m in dir(BaselineManager) if not m.startswith('_')])

print("\n=== create_sample_charts ===")
from data_analysis.visualization import create_sample_charts
print(inspect.signature(create_sample_charts))

print("\n=== ReportGenerator.generate_report ===")
from data_analysis.report_generator import ReportGenerator
print(inspect.signature(ReportGenerator.generate_report))

print("\nDONE")