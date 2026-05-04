"""XBow benchmark runner - executes XBow-based CTF automated tests."""

import json
import os
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from mcp_integration.agent_orchestrator import CTFAgentOrchestrator, RunConfig, RunSummary
from mcp_integration.mcp_server_registry import MCPServerRegistry
from visualization_dashboard.sandbox_manager import SandboxInfo
from visualization_dashboard.target_deployer import DeployedChallenge


@dataclass
class XBowConfig:
    """Configuration for an XBow benchmark run.

    Attributes:
        xbow_binary_path: Path to the XBow executable.
        challenge_config_path: Path to XBow challenge config file.
        output_dir: Directory for XBow output.
        timeout_seconds: Timeout per challenge.
        retry_count: Number of retries on failure.
        auto_solve: Whether to use AI agent for solving.
        model_name: LLM model to use.
        flag_pattern: Regex pattern for flag detection.
    """

    xbow_binary_path: str = "xbow"
    challenge_config_path: str = ""
    output_dir: str = "./xbow_output"
    timeout_seconds: int = 1800
    retry_count: int = 1
    auto_solve: bool = True
    model_name: str = "gpt-4"
    flag_pattern: str = r"flag\{[^}]+\}"


@dataclass
class XBowRunResult:
    """Result from a single XBow benchmark run.

    Attributes:
        challenge_name: Name of the challenge.
        run_id: Unique run ID.
        success: Whether the challenge was solved.
        flags_captured: List of captured flags.
        output_log: Raw XBow output.
        agent_log: Log from the AI agent.
        start_time: Run start timestamp.
        end_time: Run end timestamp.
        error_message: Error if failed.
    """

    challenge_name: str = ""
    run_id: str = ""
    success: bool = False
    flags_captured: List[str] = field(default_factory=list)
    output_log: str = ""
    agent_log: str = ""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_message: str = ""


class XBowRunner:
    """Executes XBow-based CTF challenge tests.

    Integrates with the XBow platform for automated CTF challenge
    solving. Supports both direct XBow execution and AI-agent-driven
    solving through the orchestrator.
    """

    def __init__(
        self,
        registry: Optional[MCPServerRegistry] = None,
        config: Optional[XBowConfig] = None,
    ):
        """Initialize XBow runner.

        Args:
            registry: MCP server registry for AI-agent mode.
            config: XBow configuration.
        """
        self.registry = registry
        self.config = config or XBowConfig()
        self._results: List[XBowRunResult] = []
        self._orchestrator: Optional[CTFAgentOrchestrator] = None
        if registry:
            self._orchestrator = CTFAgentOrchestrator(registry)

    def run_xbow_challenge(
        self, challenge_name: str, target_url: str
    ) -> XBowRunResult:
        """Run XBow against a single challenge.

        Args:
            challenge_name: Name of the challenge.
            target_url: URL of the target challenge.

        Returns:
            Result of the run.
        """
        run_id = f"xbow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        result = XBowRunResult(
            challenge_name=challenge_name,
            run_id=run_id,
            start_time=datetime.now(),
        )

        try:
            if self.config.auto_solve and self._orchestrator:
                result = self._run_with_agent(result, target_url)
            else:
                result = self._run_xbow_direct(result, target_url)

        except Exception as e:
            result.error_message = str(e)
            result.success = False

        result.end_time = datetime.now()
        self._results.append(result)
        return result

    def run_challenge_batch(
        self, challenges: List[DeployedChallenge]
    ) -> List[XBowRunResult]:
        """Run XBow against multiple deployed challenges.

        Args:
            challenges: List of deployed challenges.

        Returns:
            List of run results.
        """
        results = []
        for challenge in challenges:
            if challenge.status == "running" and challenge.target_url:
                result = self.run_xbow_challenge(
                    challenge.challenge.name,
                    challenge.target_url,
                )
                results.append(result)
            else:
                results.append(
                    XBowRunResult(
                        challenge_name=challenge.challenge.name,
                        error_message=f"Challenge not running: {challenge.status}",
                    )
                )
        return results

    def run_xbow_subprocess(self, args: List[str]) -> XBowRunResult:
        """Run XBow directly via subprocess.

        Args:
            args: Command-line arguments for XBow.

        Returns:
            Result of the run.
        """
        run_id = f"xbow_sub_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        result = XBowRunResult(run_id=run_id, start_time=datetime.now())

        try:
            cmd = [self.config.xbow_binary_path] + args
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config.timeout_seconds,
            )
            result.output_log = proc.stdout
            result.success = proc.returncode == 0
            if not result.success:
                result.error_message = proc.stderr[:500]

            # Try to detect flags in output
            flags_detected = self._detect_flags(proc.stdout)
            result.flags_captured = flags_detected

        except subprocess.TimeoutExpired:
            result.error_message = "XBow process timed out"
        except Exception as e:
            result.error_message = str(e)

        result.end_time = datetime.now()
        self._results.append(result)
        return result

    def get_results(self) -> List[XBowRunResult]:
        """Get all run results.

        Returns:
            List of results.
        """
        return list(self._results)

    def get_success_rate(self) -> float:
        """Get the success rate across all runs.

        Returns:
            Success rate as a float 0.0-1.0.
        """
        if not self._results:
            return 0.0
        successes = sum(1 for r in self._results if r.success)
        return successes / len(self._results)

    def _run_with_agent(
        self, result: XBowRunResult, target_url: str
    ) -> XBowRunResult:
        """Run a challenge using the AI agent orchestrator.

        Args:
            result: Result to update.
            target_url: Target challenge URL.

        Returns:
            Updated result.
        """
        if not self._orchestrator:
            result.error_message = "No orchestrator configured"
            return result

        # Extract host from URL
        host = target_url.replace("http://", "").replace("https://", "").split(":")[0]

        run_config = RunConfig(
            max_turns=30,
            max_time_seconds=self.config.timeout_seconds,
            target_host=host,
            flag_pattern=self.config.flag_pattern,
            model_name=self.config.model_name,
        )

        summary = self._orchestrator.run(run_config)
        result.success = summary.success
        result.flags_captured = summary.flags_captured
        result.agent_log = f"Turns: {summary.total_turns}, "
        result.agent_log += f"Tools: {summary.tool_calls_total}, "
        result.agent_log += f"Tokens: {summary.total_tokens}"
        return result

    def _run_xbow_direct(
        self, result: XBowRunResult, target_url: str
    ) -> XBowRunResult:
        """Run XBow directly as a subprocess.

        Args:
            result: Result to update.
            target_url: Target challenge URL.

        Returns:
            Updated result.
        """
        args = [
            "--target", target_url,
            "--config", self.config.challenge_config_path,
            "--output-dir", self.config.output_dir,
            "--timeout", str(self.config.timeout_seconds),
        ]
        direct_result = self.run_xbow_subprocess(args)
        result.success = direct_result.success
        result.flags_captured = direct_result.flags_captured
        result.output_log = direct_result.output_log
        result.error_message = direct_result.error_message
        return result

    def _detect_flags(self, output: str) -> List[str]:
        """Detect CTF flags in text output.

        Args:
            output: Text to search.

        Returns:
            List of detected flags.
        """
        import re

        flags = []
        if output:
            matches = re.findall(self.config.flag_pattern, output, re.IGNORECASE)
            flags.extend(matches)
        return flags