"""Batch benchmark runner for executing multiple CTF challenges in sequence."""

import json
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from mcp_integration.agent_orchestrator import CTFAgentOrchestrator, RunConfig, RunSummary
from mcp_integration.mcp_server_registry import MCPServerRegistry
from visualization_dashboard.log_collector import CollectedLog, LogCollector, LogCollectionSummary
from visualization_dashboard.sandbox_manager import SandboxManager
from visualization_dashboard.target_deployer import ChallengeDefinition, DeployedChallenge, TargetDeployer
from visualization_dashboard.xbow_runner import XBowConfig, XBowRunner, XBowRunResult


@dataclass
class BatchConfig:
    """Configuration for a batch benchmark run.

    Attributes:
        name: Batch run name.
        challenges: List of challenge definitions.
        parallel: Whether to run challenges in parallel.
        max_workers: Maximum parallel workers.
        retry_failed: Whether to retry failed challenges.
        max_retries: Maximum retries per challenge.
        output_dir: Directory for output.
        model_name: LLM model to use.
        flag_pattern: Pattern for flag detection.
    """

    name: str = ""
    challenges: List[ChallengeDefinition] = field(default_factory=list)
    parallel: bool = False
    max_workers: int = 4
    retry_failed: bool = True
    max_retries: int = 2
    output_dir: str = "./batch_output"
    model_name: str = "gpt-4"
    flag_pattern: str = r"flag\{[^}]+\}"


@dataclass
class BatchRunResult:
    """Result from a batch benchmark run.

    Attributes:
        batch_name: Name of the batch.
        batch_id: Unique batch identifier.
        total_challenges: Total challenges attempted.
        successes: Number of successful solves.
        failures: Number of failed solves.
        total_flags: Total flags captured.
        total_run_time_seconds: Total time for all challenges.
        per_challenge_results: Individual challenge results.
        log_summary: Summary of collected logs.
        started_at: Batch start time.
        completed_at: Batch completion time.
    """

    batch_name: str = ""
    batch_id: str = ""
    total_challenges: int = 0
    successes: int = 0
    failures: int = 0
    total_flags: int = 0
    total_run_time_seconds: float = 0.0
    per_challenge_results: List[XBowRunResult] = field(default_factory=list)
    log_summary: Optional[LogCollectionSummary] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class BatchRunner:
    """Orchestrates batch execution of multiple CTF challenges.

    Coordinates the full pipeline: deployment, execution, log collection,
    and cleanup for multiple challenges.
    """

    def __init__(
        self,
        sandbox_manager: Optional[SandboxManager] = None,
        registry: Optional[MCPServerRegistry] = None,
    ):
        """Initialize batch runner.

        Args:
            sandbox_manager: Optional sandbox manager.
            registry: Optional MCP server registry.
        """
        self.sandbox_manager = sandbox_manager or SandboxManager()
        self.target_deployer = TargetDeployer(self.sandbox_manager)
        self.registry = registry
        self.xbow_runner = XBowRunner(registry)
        self.log_collector = LogCollector()
        self._batch_results: List[BatchRunResult] = []

    def run_batch(self, config: BatchConfig) -> BatchRunResult:
        """Execute a batch of CTF challenges.

        Full pipeline: deploy -> run -> collect logs -> cleanup.

        Args:
            config: Batch configuration.

        Returns:
            Batch run result.
        """
        batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        result = BatchRunResult(
            batch_name=config.name,
            batch_id=batch_id,
            started_at=datetime.now(),
        )
        result.total_challenges = len(config.challenges)

        os.makedirs(config.output_dir, exist_ok=True)
        self.log_collector.clear()

        # Deploy challenges
        deployed = self._deploy_challenges(config)
        successfully_deployed = [d for d in deployed if d.status == "running"]
        failed_deploy = [d for d in deployed if d.status != "running"]

        # Track failures from deployment
        for failed in failed_deploy:
            result.per_challenge_results.append(
                XBowRunResult(
                    challenge_name=failed.challenge.name,
                    error_message=f"Deployment failed: {failed.status}",
                )
            )

        # Run challenges
        if config.parallel:
            challenge_results = self._run_parallel(successfully_deployed, config)
        else:
            challenge_results = self._run_sequential(successfully_deployed, config)

        result.per_challenge_results.extend(challenge_results)

        # Handle retries
        if config.retry_failed:
            retry_results = self._retry_failures(config, challenge_results)
            result.per_challenge_results.extend(retry_results)

        # Aggregate results
        result.successes = sum(1 for r in result.per_challenge_results if r.success)
        result.failures = sum(1 for r in result.per_challenge_results if not r.success)
        result.total_flags = sum(len(r.flags_captured) for r in result.per_challenge_results)

        if result.started_at:
            result.total_run_time_seconds = (
                datetime.now() - result.started_at
            ).total_seconds()

        result.completed_at = datetime.now()
        result.log_summary = self.log_collector.get_summary()

        # Save results
        self._save_batch_result(result, config.output_dir)

        # Cleanup
        self.target_deployer.cleanup_all()

        self._batch_results.append(result)
        return result

    def run_from_registry(
        self, registry_path: str, batch_config: Optional[BatchConfig] = None
    ) -> BatchRunResult:
        """Run batch from a challenge registry JSON file.

        Args:
            registry_path: Path to challenge registry.
            batch_config: Optional batch configuration.

        Returns:
            Batch run result.
        """
        # Load challenges from registry
        try:
            with open(registry_path, "r", encoding="utf-8") as f:
                challenges_data = json.load(f)
        except Exception as e:
            return BatchRunResult(
                batch_name="registry_error",
                error_message=f"Failed to load registry: {e}",
            )

        if isinstance(challenges_data, dict):
            challenges_data = [challenges_data]

        challenges = []
        for data in challenges_data:
            challenges.append(
                ChallengeDefinition(
                    name=data.get("name", "unnamed"),
                    category=data.get("category", "web"),
                    difficulty=data.get("difficulty", "medium"),
                    description=data.get("description", ""),
                    setup_script=data.get("setup_script", ""),
                    docker_compose=data.get("docker_compose", ""),
                    ports=data.get("ports", []),
                    environment=data.get("environment", {}),
                    time_limit_seconds=data.get("time_limit", 1800),
                )
            )

        config = batch_config or BatchConfig(
            name=os.path.basename(registry_path).replace(".json", ""),
        )
        config.challenges = challenges
        return self.run_batch(config)

    def get_results(self) -> List[BatchRunResult]:
        """Get all batch run results.

        Returns:
            List of batch results.
        """
        return list(self._batch_results)

    def export_results_json(self, filepath: str = "") -> str:
        """Export all batch results to JSON.

        Args:
            filepath: Output file path.

        Returns:
            Path to output file.
        """
        if not filepath:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"./batch_output/results_{timestamp}.json"

        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        data = {
            "batches": [],
            "summary": {
                "total_batches": len(self._batch_results),
                "total_successes": sum(b.successes for b in self._batch_results),
                "total_failures": sum(b.failures for b in self._batch_results),
                "total_flags": sum(b.total_flags for b in self._batch_results),
            },
        }

        for batch in self._batch_results:
            data["batches"].append({
                "batch_name": batch.batch_name,
                "batch_id": batch.batch_id,
                "successes": batch.successes,
                "failures": batch.failures,
                "total_flags": batch.total_flags,
                "run_time_seconds": batch.total_run_time_seconds,
                "started_at": batch.started_at.isoformat() if batch.started_at else None,
                "completed_at": batch.completed_at.isoformat() if batch.completed_at else None,
            })

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return filepath

    def _deploy_challenges(
        self, config: BatchConfig
    ) -> List[DeployedChallenge]:
        """Deploy all challenges in a batch.

        Args:
            config: Batch configuration.

        Returns:
            List of deployed challenges.
        """
        deployed = []
        for challenge in config.challenges:
            dep = self.target_deployer.deploy_from_definition(challenge)
            deployed.append(dep)
        return deployed

    def _run_sequential(
        self,
        deployed: List[DeployedChallenge],
        config: BatchConfig,
    ) -> List[XBowRunResult]:
        """Run challenges sequentially.

        Args:
            deployed: Deployed challenges.
            config: Batch configuration.

        Returns:
            List of run results.
        """
        results = []
        for dep in deployed:
            if dep.status == "running" and dep.target_url:
                result = self.xbow_runner.run_xbow_challenge(
                    dep.challenge.name,
                    dep.target_url,
                )
                results.append(result)

                # Collect logs
                self.log_collector.collect_xbow_log(
                    result.output_log,
                    dep.challenge.name,
                    result.run_id,
                )

                time.sleep(1)  # Small pause between challenges
            else:
                results.append(
                    XBowRunResult(
                        challenge_name=dep.challenge.name,
                        error_message=f"Not running: {dep.status}",
                    )
                )
        return results

    def _run_parallel(
        self,
        deployed: List[DeployedChallenge],
        config: BatchConfig,
    ) -> List[XBowRunResult]:
        """Run challenges in parallel.

        Args:
            deployed: Deployed challenges.
            config: Batch configuration.

        Returns:
            List of run results.
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed

        results: Dict[str, XBowRunResult] = {}
        max_workers = min(config.max_workers, len(deployed))

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {}
            for dep in deployed:
                if dep.status == "running" and dep.target_url:
                    future = executor.submit(
                        self.xbow_runner.run_xbow_challenge,
                        dep.challenge.name,
                        dep.target_url,
                    )
                    futures[future] = dep

            for future in as_completed(futures):
                dep = futures[future]
                try:
                    result = future.result()
                    results[dep.challenge.name] = result

                    # Collect logs
                    self.log_collector.collect_xbow_log(
                        result.output_log,
                        dep.challenge.name,
                        result.run_id,
                    )
                except Exception as e:
                    results[dep.challenge.name] = XBowRunResult(
                        challenge_name=dep.challenge.name,
                        error_message=str(e),
                    )

        # Handle challenges that weren't deployed
        for dep in deployed:
            if dep.challenge.name not in results:
                results[dep.challenge.name] = XBowRunResult(
                    challenge_name=dep.challenge.name,
                    error_message=f"Not deployed: {dep.status}",
                )

        return list(results.values())

    def _retry_failures(
        self,
        config: BatchConfig,
        original_results: List[XBowRunResult],
    ) -> List[XBowRunResult]:
        """Retry failed challenges.

        Args:
            config: Batch configuration.
            original_results: Original run results.

        Returns:
            List of retry results.
        """
        retry_results = []
        failures = [r for r in original_results if not r.success]

        for failed in failures:
            for attempt in range(config.max_retries):
                # Find the deployed challenge
                deployment = self.target_deployer.get_deployment(failed.challenge_name)
                if not deployment or not deployment.target_url:
                    break

                result = self.xbow_runner.run_xbow_challenge(
                    failed.challenge_name,
                    deployment.target_url,
                )
                if result.success:
                    retry_results.append(result)
                    break
                elif attempt == config.max_retries - 1:
                    retry_results.append(result)

        return retry_results

    def _save_batch_result(
        self, result: BatchRunResult, output_dir: str
    ) -> None:
        """Save batch result to JSON file.

        Args:
            result: Batch result to save.
            output_dir: Output directory.
        """
        os.makedirs(output_dir, exist_ok=True)
        filename = f"{result.batch_id}_results.json"
        filepath = os.path.join(output_dir, filename)

        data = {
            "batch_name": result.batch_name,
            "batch_id": result.batch_id,
            "successes": result.successes,
            "failures": result.failures,
            "total_flags": result.total_flags,
            "run_time_seconds": result.total_run_time_seconds,
            "started_at": result.started_at.isoformat() if result.started_at else None,
            "completed_at": result.completed_at.isoformat() if result.completed_at else None,
            "challenges": [
                {
                    "name": r.challenge_name,
                    "success": r.success,
                    "flags": r.flags_captured,
                    "error": r.error_message[:200] if r.error_message else None,
                }
                for r in result.per_challenge_results
            ],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)