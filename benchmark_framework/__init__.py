"""Benchmark Framework Module for CTF Agent evaluation.

This module provides:
- ToolWrapper and ToolBenchmarkRunner for controlled tool execution
- OutputSanitizer and FlagMaskingSanitizer for output cleaning
- LiveMCPBenchParser and XBowLogParser for log parsing
- ToolClassifier and ToolCategory for tool categorization
"""

from benchmark_framework.output_sanitizer import FlagMaskingSanitizer, OutputSanitizer
from benchmark_framework.parsers import LiveMCPBenchParser, ParsedBenchmarkRun, XBowLogParser
from benchmark_framework.tool_category import (
    KNOWN_TOOL_CATEGORIES,
    TOOL_PHASE_MAP,
    CategoryStats,
    ToolCategory,
    ToolClassifier,
)
from benchmark_framework.tool_wrapper import (
    ToolBenchmarkRunner,
    ToolExecutionRecord,
    ToolWrapper,
)

__all__ = [
    # Tool wrapper
    "ToolWrapper",
    "ToolExecutionRecord",
    "ToolBenchmarkRunner",
    # Sanitizers
    "OutputSanitizer",
    "FlagMaskingSanitizer",
    # Parsers
    "LiveMCPBenchParser",
    "XBowLogParser",
    "ParsedBenchmarkRun",
    # Tool categories
    "ToolCategory",
    "ToolClassifier",
    "CategoryStats",
    "KNOWN_TOOL_CATEGORIES",
    "TOOL_PHASE_MAP",
]