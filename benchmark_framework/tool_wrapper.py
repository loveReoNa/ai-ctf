"""Benchmark tool wrapper - wraps MCP tools for controlled benchmark execution."""

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from mcp_integration.mcp_client import MCPClient, ToolCallResult, ToolSchema
from mcp_integration.mcp_server_registry import MCPServerRegistry


@dataclass
class ToolExecutionRecord:
    """Record of a single tool execution during benchmarking.

    Attributes:
        tool_name: Name of the tool executed.
        server_name: Server that provided the tool.
        arguments: Arguments passed to the tool.
        result: Structured result data.
        success: Whether execution succeeded.
        error_message: Error description if failed.
        execution_time_ms: Wall-clock execution time.
        tokens_input: Estimated input tokens consumed.
        tokens_output: Estimated output tokens consumed.
        sanitized_output: Output after sanitization.
    """

    tool_name: str = ""
    server_name: str = ""
    arguments: Dict[str, Any] = field(default_factory=dict)
    result: Any = None
    success: bool = False
    error_message: Optional[str] = None
    execution_time_ms: float = 0.0
    tokens_input: int = 0
    tokens_output: int = 0
    sanitized_output: str = ""


class ToolWrapper:
    """Wraps security tools for controlled benchmark execution.

    Provides a uniform interface for executing tools, recording results,
    and applying output sanitization. Supports both MCP-based and
    subprocess-based tool execution.
    """

    def __init__(self, registry: Optional[MCPServerRegistry] = None):
        """Initialize tool wrapper.

        Args:
            registry: Optional MCP server registry for tool access.
        """
        self.registry = registry
        self._execution_log: List[ToolExecutionRecord] = []
        self._hooks: Dict[str, Callable] = {}
        self._sanitizer: Optional[Any] = None

    def set_sanitizer(self, sanitizer: Any) -> None:
        """Set the output sanitizer for tool results.

        Args:
            sanitizer: An OutputSanitizer instance.
        """
        self._sanitizer = sanitizer

    def register_hook(self, event: str, callback: Callable) -> None:
        """Register a hook callback for tool events.

        Args:
            event: Event name ('pre_execute', 'post_execute', 'on_error').
            callback: Function to call when event occurs.
        """
        self._hooks[event] = callback

    def execute_tool_mcp(
        self, tool_name: str, server_name: str, arguments: dict
    ) -> ToolExecutionRecord:
        """Execute a tool through the MCP client.

        Args:
            tool_name: Name of the tool to execute.
            server_name: Server providing the tool.
            arguments: Tool arguments.

        Returns:
            Execution record with results.
        """
        record = ToolExecutionRecord(
            tool_name=tool_name,
            server_name=server_name,
            arguments=arguments,
        )

        if "pre_execute" in self._hooks:
            self._hooks["pre_execute"](tool_name, arguments)

        try:
            if not self.registry:
                raise RuntimeError("No MCP registry configured")

            client = self._get_client(server_name)
            if not client:
                raise RuntimeError(f"Server {server_name} not found")

            start_time = time.time()
            result = client.call_tool(tool_name, arguments)
            elapsed = (time.time() - start_time) * 1000.0

            record.success = result.success
            record.result = result.result
            record.error_message = result.error_message
            record.execution_time_ms = elapsed

            if result.token_usage:
                record.tokens_input = result.token_usage.input_tokens
                record.tokens_output = result.token_usage.output_tokens

            # Sanitize output
            raw_output = str(result.result) if result.result else ""
            record.sanitized_output = self._sanitize_output(raw_output)

        except Exception as e:
            record.success = False
            record.error_message = str(e)

        if "post_execute" in self._hooks:
            self._hooks["post_execute"](record)
        if not record.success and "on_error" in self._hooks:
            self._hooks["on_error"](record)

        self._execution_log.append(record)
        return record

    def execute_tool_subprocess(
        self, command: List[str], tool_name: str = "subprocess"
    ) -> ToolExecutionRecord:
        """Execute a tool via subprocess.

        Args:
            command: Command and arguments to execute.
            tool_name: Name label for the execution record.

        Returns:
            Execution record with results.
        """
        record = ToolExecutionRecord(tool_name=tool_name)

        if "pre_execute" in self._hooks:
            self._hooks["pre_execute"](tool_name, command)

        try:
            import subprocess

            start_time = time.time()
            proc = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=300,
            )
            elapsed = (time.time() - start_time) * 1000.0

            record.success = proc.returncode == 0
            record.result = {"stdout": proc.stdout, "stderr": proc.stderr}
            record.execution_time_ms = elapsed
            record.arguments = {"command": command}

            if not record.success:
                record.error_message = proc.stderr[:500]

            # Sanitize output
            raw_output = proc.stdout
            record.sanitized_output = self._sanitize_output(raw_output)

        except subprocess.TimeoutExpired as e:
            record.success = False
            record.error_message = f"Command timed out: {e}"
        except Exception as e:
            record.success = False
            record.error_message = str(e)

        if "post_execute" in self._hooks:
            self._hooks["post_execute"](record)
        if not record.success and "on_error" in self._hooks:
            self._hooks["on_error"](record)

        self._execution_log.append(record)
        return record

    def get_execution_log(self) -> List[ToolExecutionRecord]:
        """Get the complete execution log.

        Returns:
            List of all execution records.
        """
        return list(self._execution_log)

    def clear_log(self) -> None:
        """Clear the execution log."""
        self._execution_log = []

    def get_success_rate(self) -> float:
        """Calculate tool execution success rate.

        Returns:
            Success rate as a float between 0.0 and 1.0.
        """
        if not self._execution_log:
            return 1.0
        successes = sum(1 for r in self._execution_log if r.success)
        return successes / len(self._execution_log)

    def _get_client(self, server_name: str) -> Optional[MCPClient]:
        """Get MCP client for a server from the registry.

        Args:
            server_name: Server name.

        Returns:
            MCPClient or None.
        """
        if self.registry and server_name in self.registry._clients:
            return self.registry._clients[server_name]
        return None

    def _sanitize_output(self, output: str) -> str:
        """Apply sanitization to tool output.

        Args:
            output: Raw tool output.

        Returns:
            Sanitized output string.
        """
        if self._sanitizer:
            return self._sanitizer.sanitize(output)
        return output


class ToolBenchmarkRunner:
    """Runs tool-level benchmarks to measure performance and accuracy.

    Executes specific tools against known challenges and records
    correctness, execution time, and token usage metrics.
    """

    def __init__(self, wrapper: ToolWrapper):
        """Initialize benchmark runner.

        Args:
            wrapper: ToolWrapper instance for tool execution.
        """
        self.wrapper = wrapper
        self._benchmark_results: List[Dict[str, Any]] = []

    def run_tool_benchmark(
        self,
        tool_name: str,
        server_name: str,
        test_cases: List[dict],
    ) -> Dict[str, Any]:
        """Run a benchmark for a specific tool.

        Args:
            tool_name: Tool to benchmark.
            server_name: Server providing the tool.
            test_cases: List of test cases with input and expected output.

        Returns:
            Benchmark summary with per-case results.
        """
        results = []
        for i, case in enumerate(test_cases):
            record = self.wrapper.execute_tool_mcp(
                tool_name=tool_name,
                server_name=server_name,
                arguments=case.get("input", {}),
            )
            expected = case.get("expected", "")
            correct = self._check_correctness(str(record.result), expected)
            results.append(
                {
                    "case_id": i,
                    "success": record.success,
                    "correct": correct,
                    "execution_time_ms": record.execution_time_ms,
                    "error": record.error_message,
                }
            )

        total = len(results)
        successful = sum(1 for r in results if r["success"])
        correct_count = sum(1 for r in results if r["correct"])

        summary = {
            "tool_name": tool_name,
            "total_cases": total,
            "successful_executions": successful,
            "correct_results": correct_count,
            "accuracy": correct_count / total if total > 0 else 0.0,
            "cases": results,
        }
        self._benchmark_results.append(summary)
        return summary

    def _check_correctness(self, output: str, expected: str) -> bool:
        """Check if tool output matches expected result.

        Args:
            output: Actual tool output.
            expected: Expected output pattern.

        Returns:
            True if output matches expected.
        """
        if not expected:
            return True
        return expected.lower() in output.lower()