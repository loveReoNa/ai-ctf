"""Benchmark parsers for LiveMCPBench and XBow log formats."""

import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class ParsedBenchmarkRun:
    """Parsed result from a benchmark run log.

    Attributes:
        challenge_name: Name of the CTF challenge.
        tool_call_count: Number of tool invocations.
        tokens_consumed: Total LLM tokens used.
        flags_found: Number of flags captured.
        success: Whether the challenge was solved.
        error_count: Number of errors encountered.
        total_time: Total execution time in seconds.
    """

    challenge_name: str = ""
    tool_call_count: int = 0
    tokens_consumed: int = 0
    flags_found: int = 0
    success: bool = False
    error_count: int = 0
    total_time: float = 0.0


class LiveMCPBenchParser:
    """Parses LiveMCPBench benchmark configuration and results.

    Handles the LiveMCPBench JSON format used for MCP server
    benchmarking, extracting tool definitions and run results.
    """

    def parse_config(self, config_path: str) -> Dict[str, Any]:
        """Parse a LiveMCPBench server configuration file.

        Args:
            config_path: Path to a LiveMCPBench config JSON file.

        Returns:
            Dictionary with server config details.
        """
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {
                "name": data.get("name", ""),
                "description": data.get("description", ""),
                "transport": data.get("transport", "stdio"),
                "command": data.get("command"),
                "args": data.get("args", []),
                "url": data.get("url"),
                "tools": data.get("tools", []),
            }
        except Exception as e:
            return {"error": str(e)}

    def parse_results(self, results_path: str) -> List[ParsedBenchmarkRun]:
        """Parse LiveMCPBench benchmark results.

        Args:
            results_path: Path to results JSON file or directory.

        Returns:
            List of parsed benchmark runs.
        """
        runs = []

        try:
            if os.path.isfile(results_path):
                with open(results_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list):
                    for entry in data:
                        runs.append(self._parse_entry(entry))
                else:
                    runs.append(self._parse_entry(data))
            elif os.path.isdir(results_path):
                for filename in os.listdir(results_path):
                    if filename.endswith(".json"):
                        filepath = os.path.join(results_path, filename)
                        with open(filepath, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        if isinstance(data, list):
                            for entry in data:
                                runs.append(self._parse_entry(entry))
                        else:
                            runs.append(self._parse_entry(data))
        except Exception as e:
            return [ParsedBenchmarkRun()]

        return runs

    def parse_tool_definitions(self, config_path: str) -> List[dict]:
        """Extract tool definitions from a LiveMCPBench config.

        Args:
            config_path: Path to config JSON file.

        Returns:
            List of tool definition dictionaries.
        """
        config = self.parse_config(config_path)
        return config.get("tools", [])

    def _parse_entry(self, entry: dict) -> ParsedBenchmarkRun:
        """Parse a single benchmark result entry.

        Args:
            entry: Raw result entry dictionary.

        Returns:
            Parsed benchmark run.
        """
        return ParsedBenchmarkRun(
            challenge_name=entry.get("challenge", entry.get("name", "unknown")),
            tool_call_count=entry.get("tool_calls", entry.get("steps", 0)),
            tokens_consumed=entry.get("tokens", entry.get("token_usage", 0)),
            flags_found=entry.get("flags", entry.get("flags_found", 0)),
            success=entry.get("success", entry.get("solved", False)),
            error_count=entry.get("errors", entry.get("error_count", 0)),
            total_time=entry.get("time", entry.get("duration_seconds", 0.0)),
        )


class XBowLogParser:
    """Parses XBow platform log outputs.

    Extracts structured information from XBow execution logs
    including tool outputs, errors, and flag captures.
    """

    def parse_log(self, log_text: str) -> Dict[str, Any]:
        """Parse XBow log text into structured data.

        Args:
            log_text: Raw XBow log output.

        Returns:
            Dictionary with parsed log information.
        """
        result: Dict[str, Any] = {
            "tool_calls": [],
            "errors": [],
            "flags": [],
            "warnings": [],
        }

        # Extract tool calls
        tool_pattern = re.compile(
            r"\[TOOL\]\s+(\w+)\s*\((.*?)\)\s*->\s*(.*?)(?=\[TOOL\]|\[ERROR\]|\[FLAG\]|\[WARN\]|$)",
            re.DOTALL,
        )
        for match in tool_pattern.finditer(log_text):
            tool_name = match.group(1)
            args_str = match.group(2)
            output = match.group(3).strip()
            result["tool_calls"].append({
                "tool": tool_name,
                "arguments": self._parse_args(args_str),
                "output": output[:200],
            })

        # Extract errors
        error_pattern = re.compile(r"\[ERROR\]\s*(.*?)(?=\[TOOL\]|\[ERROR\]|\[FLAG\]|$)")
        for match in error_pattern.finditer(log_text):
            result["errors"].append(match.group(1).strip()[:200])

        # Extract flags
        flag_patterns = [
            r"flag\{[^}]+\}",
            r"CTF\{[^}]+\}",
            r"\[FLAG\]\s*(.*?)(?=\n|$)",
        ]
        for pattern in flag_patterns:
            for match in re.finditer(pattern, log_text, re.IGNORECASE):
                flag = match.group(0)
                if flag not in result["flags"]:
                    result["flags"].append(flag)

        # Extract warnings
        warn_pattern = re.compile(r"\[WARN\]\s*(.*?)(?=\[TOOL\]|\[ERROR\]|\[FLAG\]|\[WARN\]|$)")
        for match in warn_pattern.finditer(log_text):
            result["warnings"].append(match.group(1).strip()[:100])

        return result

    def parse_log_file(self, filepath: str) -> Dict[str, Any]:
        """Parse an XBow log file.

        Args:
            filepath: Path to log file.

        Returns:
            Dictionary with parsed log information.
        """
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            return self.parse_log(content)
        except Exception as e:
            return {"error": str(e), "tool_calls": [], "errors": [], "flags": []}

    def parse_batch_logs(self, directory: str) -> Dict[str, Any]:
        """Parse all XBow log files in a directory.

        Args:
            directory: Path to directory containing log files.

        Returns:
            Dictionary with aggregated results per file.
        """
        results = {}
        try:
            for filename in sorted(os.listdir(directory)):
                if filename.endswith(".log") or filename.endswith(".txt"):
                    filepath = os.path.join(directory, filename)
                    results[filename] = self.parse_log_file(filepath)
        except Exception as e:
            results["error"] = str(e)
        return results

    @staticmethod
    def _parse_args(args_str: str) -> dict:
        """Parse tool argument string into dictionary.

        Args:
            args_str: Raw argument string.

        Returns:
            Parsed arguments dictionary.
        """
        args = {}
        # Try key=value format
        kv_pattern = re.compile(r"(\w+)\s*=\s*(\S+)")
        for match in kv_pattern.finditer(args_str):
            args[match.group(1)] = match.group(2).strip("\"'")

        if not args and args_str.strip():
            args["raw"] = args_str.strip()

        return args