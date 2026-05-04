"""Visualization Dashboard Module for CTF challenge deployment and execution.

This module provides:
- SandboxManager for Docker-based CTF sandbox management
- TargetDeployer for deploying challenges to sandboxes
- XBowRunner for executing XBow CTF automatic solving
- LogCollector for aggregating logs across multiple sources
- BatchRunner for orchestrating batch challenge execution
"""

from visualization_dashboard.batch_runner import BatchConfig, BatchRunner, BatchRunResult
from visualization_dashboard.log_collector import CollectedLog, LogCollectionSummary, LogCollector
from visualization_dashboard.sandbox_manager import (
    SandboxConfig,
    SandboxInfo,
    SandboxManager,
    SandboxStatus,
)
from visualization_dashboard.target_deployer import (
    ChallengeDefinition,
    DeployedChallenge,
    TargetDeployer,
)
from visualization_dashboard.xbow_runner import XBowConfig, XBowRunner, XBowRunResult

__all__ = [
    # Sandbox
    "SandboxManager",
    "SandboxConfig",
    "SandboxInfo",
    "SandboxStatus",
    # Target deployer
    "ChallengeDefinition",
    "DeployedChallenge",
    "TargetDeployer",
    # XBow runner
    "XBowRunner",
    "XBowConfig",
    "XBowRunResult",
    # Log collector
    "LogCollector",
    "CollectedLog",
    "LogCollectionSummary",
    # Batch runner
    "BatchRunner",
    "BatchConfig",
    "BatchRunResult",
]