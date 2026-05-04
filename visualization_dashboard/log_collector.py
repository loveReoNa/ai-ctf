"""Log collector for CTF benchmark runs - aggregates logs from multiple sources."""

import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from benchmark_framework.parsers import XBowLogParser


@dataclass
class CollectedLog:
    """A single collected log entry.

    Attributes:
        source: Source identifier.
        challenge_name: Associated challenge.
        run_id: Associated run ID.
        timestamp: Collection timestamp.
        raw_text: Raw log text.
        tool_calls: Number of tool invocations.
        errors: Number of errors.
        flags: List of detected flags.
    """

    source: str = ""
    challenge_name: str = ""
    run_id: str = ""
    timestamp: Optional[datetime] = None
    raw_text: str = ""
    tool_calls: int = 0
    errors: int = 0
    flags: List[str] = field(default_factory=list)


@dataclass
class LogCollectionSummary:
    """Summary of collected logs.

    Attributes:
        total_entries: Total log entries collected.
        total_tool_calls: Total tool invocations across all logs.
        total_errors: Total errors across all logs.
        total_flags: Total unique flags found.
        sources: List of unique sources.
        challenges: List of unique challenges.
    """

    total_entries: int = 0
    total_tool_calls: int = 0
    total_errors: int = 0
    total_flags: int = 0
    sources: List[str] = field(default_factory=list)
    challenges: List[str] = field(default_factory=list)


class LogCollector:
    """Collects and aggregates logs from multiple benchmark sources.

    Supports log collection from:
    - XBow execution output files
    - AI agent orchestrator logs
    - LiveMCPBench JSON results
    - Raw tool execution logs
    """

    def __init__(self, output_dir: str = "./collected_logs"):
        """Initialize log collector.

        Args:
            output_dir: Directory for storing collected logs.
        """
        self.output_dir = output_dir
        self._logs: List[CollectedLog] = []
        self._xbow_parser = XBowLogParser()

    def collect_xbow_log(
        self,
        log_text: str,
        challenge_name: str,
        run_id: str = "",
    ) -> CollectedLog:
        """Collect and parse an XBow execution log.

        Args:
            log_text: Raw XBow log output.
            challenge_name: Challenge being solved.
            run_id: Unique run identifier.

        Returns:
            Collected log entry.
        """
        parsed = self._xbow_parser.parse_log(log_text)
        entry = CollectedLog(
            source="xbow",
            challenge_name=challenge_name,
            run_id=run_id,
            timestamp=datetime.now(),
            raw_text=log_text[:5000],
            tool_calls=len(parsed.get("tool_calls", [])),
            errors=len(parsed.get("errors", [])),
            flags=parsed.get("flags", []),
        )
        self._logs.append(entry)
        return entry

    def collect_xbow_file(
        self, filepath: str, challenge_name: str = ""
    ) -> CollectedLog:
        """Collect a log from an XBow output file.

        Args:
            filepath: Path to log file.
            challenge_name: Optional challenge name.

        Returns:
            Collected log entry.
        """
        parsed = self._xbow_parser.parse_log_file(filepath)
        if parsed.get("error"):
            entry = CollectedLog(
                source="xbow_file",
                challenge_name=challenge_name,
                timestamp=datetime.now(),
                errors=1,
            )
            self._logs.append(entry)
            return entry

        entry = CollectedLog(
            source="xbow_file",
            challenge_name=challenge_name or filepath,
            timestamp=datetime.now(),
            tool_calls=len(parsed.get("tool_calls", [])),
            errors=len(parsed.get("errors", [])),
            flags=parsed.get("flags", []),
        )
        self._logs.append(entry)
        return entry

    def collect_agent_log(
        self,
        log_text: str,
        challenge_name: str,
        run_id: str = "",
    ) -> CollectedLog:
        """Collect an AI agent orchestrator log.

        Args:
            log_text: Agent execution log.
            challenge_name: Challenge being solved.
            run_id: Unique run identifier.

        Returns:
            Collected log entry.
        """
        # Parse agent log for tool calls and flags
        tool_count = len(re.findall(r"\[TOOL\]|Tool called|tool_call", log_text, re.IGNORECASE))
        flags = re.findall(r"flag\{[^}]+\}", log_text, re.IGNORECASE)
        errors = len(re.findall(r"\[ERROR\]|Error:|Failed:", log_text))

        entry = CollectedLog(
            source="agent",
            challenge_name=challenge_name,
            run_id=run_id,
            timestamp=datetime.now(),
            raw_text=log_text[:5000],
            tool_calls=tool_count,
            errors=errors,
            flags=list(set(flags)),
        )
        self._logs.append(entry)
        return entry

    def collect_livemcpbench_result(
        self, result_path: str, challenge_name: str = ""
    ) -> List[CollectedLog]:
        """Collect logs from a LiveMCPBench results file.

        Args:
            result_path: Path to LiveMCPBench JSON results.
            challenge_name: Optional challenge name.

        Returns:
            List of collected log entries.
        """
        entries = []
        try:
            with open(result_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, list):
                data = [data]

            for item in data:
                entry = CollectedLog(
                    source="livemcpbench",
                    challenge_name=challenge_name or item.get("name", "unknown"),
                    run_id=item.get("run_id", ""),
                    timestamp=datetime.now(),
                    tool_calls=item.get("tool_calls", 0),
                    errors=item.get("errors", 0),
                    flags=item.get("flags", []),
                )
                entries.append(entry)
                self._logs.append(entry)

        except Exception:
            entry = CollectedLog(
                source="livemcpbench",
                challenge_name=challenge_name,
                errors=1,
            )
            entries.append(entry)
            self._logs.append(entry)

        return entries

    def collect_tool_execution_log(
        self,
        tool_name: str,
        output: str,
        duration_ms: float,
        challenge_name: str = "",
        run_id: str = "",
    ) -> CollectedLog:
        """Collect a single tool execution log.

        Args:
            tool_name: Name of the tool.
            output: Tool output text.
            duration_ms: Execution duration.
            challenge_name: Challenge name.
            run_id: Run identifier.

        Returns:
            Collected log entry.
        """
        flags = re.findall(r"flag\{[^}]+\}", output, re.IGNORECASE)
        entry = CollectedLog(
            source=f"tool:{tool_name}",
            challenge_name=challenge_name,
            run_id=run_id,
            timestamp=datetime.now(),
            raw_text=output[:5000],
            tool_calls=1,
            errors=0,
            flags=list(set(flags)),
        )
        self._logs.append(entry)
        return entry

    def get_logs(self) -> List[CollectedLog]:
        """Get all collected logs.

        Returns:
            List of collected log entries.
        """
        return list(self._logs)

    def get_logs_by_source(self, source: str) -> List[CollectedLog]:
        """Get logs filtered by source.

        Args:
            source: Source identifier.

        Returns:
            Filtered log entries.
        """
        return [log for log in self._logs if log.source == source]

    def get_logs_by_challenge(self, challenge_name: str) -> List[CollectedLog]:
        """Get logs filtered by challenge.

        Args:
            challenge_name: Challenge name.

        Returns:
            Filtered log entries.
        """
        return [log for log in self._logs if log.challenge_name == challenge_name]

    def get_summary(self) -> LogCollectionSummary:
        """Generate a summary of all collected logs.

        Returns:
            Summary of the collection.
        """
        all_flags: List[str] = []
        for log in self._logs:
            all_flags.extend(log.flags)

        return LogCollectionSummary(
            total_entries=len(self._logs),
            total_tool_calls=sum(log.tool_calls for log in self._logs),
            total_errors=sum(log.errors for log in self._logs),
            total_flags=len(set(all_flags)),
            sources=sorted(set(log.source for log in self._logs)),
            challenges=sorted(set(
                log.challenge_name for log in self._logs if log.challenge_name
            )),
        )

    def export_json(self, filepath: str = "") -> str:
        """Export collected logs to JSON.

        Args:
            filepath: Output file path. Auto-generated if empty.

        Returns:
            Path to output file.
        """
        if not filepath:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = os.path.join(self.output_dir, f"logs_{timestamp}.json")

        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        data = {
            "summary": {
                "total_entries": len(self._logs),
                "collected_at": datetime.now().isoformat(),
            },
            "entries": [
                {
                    "source": log.source,
                    "challenge_name": log.challenge_name,
                    "run_id": log.run_id,
                    "timestamp": log.timestamp.isoformat() if log.timestamp else None,
                    "tool_calls": log.tool_calls,
                    "errors": log.errors,
                    "flags": log.flags,
                    "raw_text": log.raw_text[:1000],
                }
                for log in self._logs
            ],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return filepath

    def clear(self) -> None:
        """Clear all collected logs."""
        self._logs.clear()