"""CTF Agent Orchestrator - core agent that drives automated CTF solving."""

import os
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from mcp_integration.mcp_client import MCPClient, ToolCallResult
from mcp_integration.mcp_server_registry import MCPServerRegistry
from mcp_integration.schemas.agent_state_schema import (
    AgentState,
    AttackPhase,
    ErrorRecord,
    VulnInfo,
)
from mcp_integration.schemas.tool_call_schema import LoggedToolCall, TokenUsage


@dataclass
class RunConfig:
    """Configuration for a single agent run.

    Attributes:
        max_turns: Maximum number of agent turns.
        max_time_seconds: Maximum total execution time.
        max_tokens: Maximum total token consumption.
        target_host: Target IP/hostname for the CTF challenge.
        target_ports: Ports to scan.
        flag_pattern: Regex pattern to detect flags in output.
        model_name: LLM model to use.
        parallel_tool_calls: Whether to allow parallel tool calls.
    """

    max_turns: int = 50
    max_time_seconds: int = 3600
    max_tokens: int = 100000
    target_host: str = ""
    target_ports: str = "1-1000"
    flag_pattern: str = r"flag\{[^}]+\}"
    model_name: str = "gpt-4"
    parallel_tool_calls: bool = False


@dataclass
class RunSummary:
    """Summary of a completed agent run.

    Attributes:
        run_id: Unique run identifier.
        success: Whether the CTF was solved (flag captured).
        flags_captured: List of captured flags.
        total_turns: Number of turns executed.
        total_time_seconds: Total wall-clock time.
        total_tokens: Total tokens consumed.
        tool_calls_total: Total tool invocations.
        tool_calls_successful: Number of successful tool calls.
        vulnerabilities_found: Number of vulnerabilities discovered.
    """

    run_id: str = ""
    success: bool = False
    flags_captured: List[str] = field(default_factory=list)
    total_turns: int = 0
    total_time_seconds: float = 0.0
    total_tokens: int = 0
    tool_calls_total: int = 0
    tool_calls_successful: int = 0
    vulnerabilities_found: int = 0


class CTFAgentOrchestrator:
    """Orchestrator that coordinates the AI agent's CTF-solving process.

    Manages the agent loop: tool selection, execution, result analysis,
    state tracking, and flag detection. Interfaces with MCP servers
    through the MCPServerRegistry.
    """

    def __init__(self, registry: MCPServerRegistry):
        """Initialize orchestrator with a server registry.

        Args:
            registry: Registry of available MCP servers.
        """
        self.registry = registry
        self._tool_call_log: List[LoggedToolCall] = []
        self._state: Optional[AgentState] = None
        self._start_time: Optional[datetime] = None
        self._total_tokens: int = 0
        self._system_prompt: Optional[str] = None

    def load_system_prompt(self, prompt_path: Optional[str] = None) -> None:
        """Load the CTF solver system prompt.

        Args:
            prompt_path: Path to a markdown prompt file. Uses default if None.
        """
        if prompt_path and os.path.exists(prompt_path):
            with open(prompt_path, "r", encoding="utf-8") as f:
                self._system_prompt = f.read()
        else:
            self._system_prompt = self._get_default_prompt()

    def run(self, config: RunConfig) -> RunSummary:
        """Execute a full CTF-solving run.

        Args:
            config: Run configuration parameters.

        Returns:
            Summary of the run results.
        """
        run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        self._start_time = datetime.now()
        self._state = AgentState()
        self._tool_call_log = []
        self._total_tokens = 0

        if not self._system_prompt:
            self.load_system_prompt()

        turn = 0
        while turn < config.max_turns:
            elapsed = (datetime.now() - self._start_time).total_seconds()
            if elapsed > config.max_time_seconds:
                break

            if self._total_tokens > config.max_tokens:
                break

            self._state.turn_number = turn
            action = self._select_action(config)

            if action:
                tool_result = self._execute_action(action, config)
                self._process_result(tool_result, config)
                flags = self._detect_flags(str(tool_result.result), config)
                for flag in flags:
                    self._state.add_flag(flag)

                if self._state.flags_captured:
                    break

            turn += 1

            if turn % 5 == 0:
                self._update_phase()

        end_time = datetime.now()
        total_tool_calls = len(self._tool_call_log)
        successful_calls = sum(1 for tc in self._tool_call_log if tc.success)

        return RunSummary(
            run_id=run_id,
            success=len(self._state.flags_captured) > 0,
            flags_captured=self._state.flags_captured,
            total_turns=turn,
            total_time_seconds=(end_time - self._start_time).total_seconds(),
            total_tokens=self._total_tokens,
            tool_calls_total=total_tool_calls,
            tool_calls_successful=successful_calls,
            vulnerabilities_found=len(self._state.vulnerabilities_found),
        )

    def get_tool_call_log(self) -> List[LoggedToolCall]:
        """Get the complete tool call trace log.

        Returns:
            List of all logged tool calls.
        """
        return list(self._tool_call_log)

    def get_agent_state(self) -> Optional[AgentState]:
        """Get the current agent state snapshot.

        Returns:
            Current agent state or None if not running.
        """
        return self._state

    def _select_action(self, config: RunConfig) -> Optional[dict]:
        """Select the next tool to invoke based on current state.

        Args:
            config: Run configuration.

        Returns:
            Dict with tool_name and arguments, or None.
        """
        all_tools = self.registry.get_all_tools()
        available_tools = []
        for server_tools in all_tools.values():
            available_tools.extend(server_tools)

        if not available_tools:
            return None

        # Simple strategy: pick based on current phase
        phase_tools = {
            AttackPhase.RECONNAISSANCE: ["nmap_scan", "dns_lookup", "whois_lookup"],
            AttackPhase.ENUMERATION: ["gobuster_scan", "nikto_scan", "dirb_scan"],
            AttackPhase.EXPLOITATION: ["sqlmap_scan", "hydra_bruteforce", "searchsploit"],
            AttackPhase.POST_EXPLOITATION: ["lse_enum", "linpeas", "privesc_check"],
            AttackPhase.FLAG_CAPTURE: ["find_command", "cat_command", "grep_flag"],
        }

        preferred = phase_tools.get(self._state.current_phase, [])
        for tool in available_tools:
            if tool.name in preferred:
                return {
                    "tool_name": tool.name,
                    "server_name": tool.server_name,
                    "arguments": {"target": config.target_host},
                }

        return None

    def _execute_action(self, action: dict, config: RunConfig) -> ToolCallResult:
        """Execute a tool call through MCP client.

        Args:
            action: Tool action specification.
            config: Run configuration.

        Returns:
            Result of the tool call.
        """
        client = self._get_client_for_server(action.get("server_name", ""))
        if not client:
            return ToolCallResult(
                success=False,
                tool_name=action.get("tool_name", "unknown"),
                error_message=f"Server {action.get('server_name')} not found",
            )

        start_time = datetime.now()
        result = client.call_tool(
            action.get("tool_name", ""), action.get("arguments", {})
        )
        end_time = datetime.now()

        # Log the call
        token_usage = TokenUsage(
            input_tokens=50,
            output_tokens=30,
        )
        if result.token_usage:
            token_usage = result.token_usage

        logged_call = LoggedToolCall(
            call_id=f"call_{uuid.uuid4().hex[:8]}",
            timestamp_start=start_time,
            timestamp_end=end_time,
            tool_name=result.tool_name,
            server_name=action.get("server_name", ""),
            arguments=result.arguments,
            result=result.result,
            success=result.success,
            error_message=result.error_message,
            token_usage=token_usage,
            turn_number=self._state.turn_number if self._state else 0,
        )
        self._tool_call_log.append(logged_call)
        self._total_tokens += token_usage.total_tokens

        return result

    def _process_result(self, result: ToolCallResult, config: RunConfig) -> None:
        """Process tool call result and update agent state.

        Args:
            result: Tool call result.
            config: Run configuration.
        """
        if not result.success and self._state:
            error = ErrorRecord(
                turn_number=self._state.turn_number,
                tool_name=result.tool_name,
                error_type="tool_error",
                error_message=result.error_message or "Unknown error",
                recovered=False,
            )
            self._state.add_error(error)

    def _detect_flags(self, output: str, config: RunConfig) -> List[str]:
        """Detect CTF flags in output text.

        Args:
            output: Text output to search.
            config: Run configuration.

        Returns:
            List of detected flag strings.
        """
        import re

        flags = []
        if output:
            matches = re.findall(config.flag_pattern, output, re.IGNORECASE)
            flags.extend(matches)
        return flags

    def _update_phase(self) -> None:
        """Update the current attack phase based on state progression."""
        if not self._state:
            return

        if self._state.flags_captured:
            self._state.transition_phase(AttackPhase.FLAG_CAPTURE)
        elif self._state.vulnerabilities_found and len(self._state.vulnerabilities_found) > 1:
            self._state.transition_phase(AttackPhase.EXPLOITATION)
        elif self._state.targets_identified:
            self._state.transition_phase(AttackPhase.ENUMERATION)

    def _get_client_for_server(self, server_name: str) -> Optional[MCPClient]:
        """Get the MCP client for a specific server.

        Args:
            server_name: Server name.

        Returns:
            MCPClient instance or None.
        """
        if server_name in self.registry._clients:
            client = self.registry._clients[server_name]
            if not client._connected:
                client.connect()
            return client
        return None

    def _get_default_prompt(self) -> str:
        """Return default CTF solver system prompt.

        Returns:
            Default prompt string.
        """
        return (
            "You are an AI security agent specialized in solving CTF (Capture The Flag) "
            "challenges. Your goal is to discover vulnerabilities, exploit them, and "
            "capture flags from target systems.\n\n"
            "Follow this methodology:\n"
            "1. RECON: Scan the target for open ports and services\n"
            "2. ENUMERATE: Gather detailed information about discovered services\n"
            "3. EXPLOIT: Use appropriate tools to exploit vulnerabilities\n"
            "4. POST-EXPLOIT: Search for flags and escalate privileges if needed\n"
            "5. CAPTURE: Extract the flag and report success\n\n"
            "Use tools sequentially and analyze results before deciding next steps."
        )