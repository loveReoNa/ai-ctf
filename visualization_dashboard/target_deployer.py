"""Target challenge deployer for CTF benchmarking environments."""

import json
import os
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from visualization_dashboard.sandbox_manager import SandboxConfig, SandboxInfo, SandboxManager


@dataclass
class ChallengeDefinition:
    """Definition of a CTF challenge to deploy.

    Attributes:
        name: Challenge name/identifier.
        category: Challenge category (web, pwn, crypto, reverse, misc).
        difficulty: Difficulty level (easy, medium, hard, expert).
        flag_pattern: Pattern to detect success.
        description: Challenge description.
        setup_script: Path to setup script.
        docker_compose: Path to docker-compose file.
        ports: Required ports.
        environment: Required environment variables.
        time_limit_seconds: Time limit for solving.
    """

    name: str = ""
    category: str = "web"
    difficulty: str = "medium"
    flag_pattern: str = r"flag\{[^}]+\}"
    description: str = ""
    setup_script: str = ""
    docker_compose: str = ""
    ports: List[int] = field(default_factory=list)
    environment: Dict[str, str] = field(default_factory=dict)
    time_limit_seconds: int = 1800


@dataclass
class DeployedChallenge:
    """Information about a deployed challenge.

    Attributes:
        challenge: Challenge definition.
        sandbox: Sandbox information.
        deployed_at: Deployment timestamp.
        target_url: URL to access the challenge.
        status: Deployment status.
        logs: Deployment logs.
    """

    challenge: ChallengeDefinition
    sandbox: Optional[SandboxInfo] = None
    deployed_at: Optional[datetime] = None
    target_url: str = ""
    status: str = "pending"
    logs: List[str] = field(default_factory=list)


class TargetDeployer:
    """Deploys CTF challenges to Docker sandboxes.

    Manages the lifecycle of challenge deployment including
    setup scripts, environment configuration, and cleanup.
    """

    def __init__(self, sandbox_manager: SandboxManager):
        """Initialize target deployer.

        Args:
            sandbox_manager: Sandbox manager for Docker containers.
        """
        self.sandbox_manager = sandbox_manager
        self._deployments: Dict[str, DeployedChallenge] = {}

    def deploy_from_definition(
        self, challenge: ChallengeDefinition
    ) -> DeployedChallenge:
        """Deploy a single challenge from its definition.

        Args:
            challenge: Challenge definition to deploy.

        Returns:
            Deployed challenge information.
        """
        deployed = DeployedChallenge(challenge=challenge)
        deployed.deployed_at = datetime.now()

        # Configure sandbox
        config = SandboxConfig(
            image="kalilinux/kali-rolling",
            cpu_limit="1.0",
            memory_limit="512m",
            network_mode="bridge",
            environment=challenge.environment,
            ports={p: p for p in challenge.ports},
            timeout_seconds=challenge.time_limit_seconds,
        )

        sandbox_name = f"ctf_challenge_{challenge.name}"

        # Deploy docker compose if available
        if challenge.docker_compose and os.path.exists(challenge.docker_compose):
            deployed = self._deploy_docker_compose(deployed, challenge)
            deployed.status = "running"
            self._deployments[challenge.name] = deployed
            return deployed

        # Standard sandbox deployment
        sandbox = self.sandbox_manager.create_sandbox(sandbox_name, config)

        if sandbox.status.value == "running":
            deployed.sandbox = sandbox
            deployed.status = "running"
            if sandbox.ip_address:
                deployed.target_url = f"http://{sandbox.ip_address}"
                if challenge.ports:
                    deployed.target_url += f":{challenge.ports[0]}"

            # Run setup script if provided
            if challenge.setup_script and os.path.exists(challenge.setup_script):
                self._run_setup_script(sandbox_name, challenge.setup_script, deployed)
        else:
            deployed.status = "error"
            deployed.logs.append(f"Sandbox creation failed: {sandbox.status.value}")

        self._deployments[challenge.name] = deployed
        return deployed

    def deploy_from_registry(
        self, registry_path: str
    ) -> List[DeployedChallenge]:
        """Deploy challenges from a challenge registry JSON file.

        Args:
            registry_path: Path to registry JSON file.

        Returns:
            List of deployed challenges.
        """
        deployments = []
        try:
            with open(registry_path, "r", encoding="utf-8") as f:
                challenges = json.load(f)

            if isinstance(challenges, dict):
                challenges = [challenges]

            for chal_data in challenges:
                challenge = ChallengeDefinition(
                    name=chal_data.get("name", "unnamed"),
                    category=chal_data.get("category", "web"),
                    difficulty=chal_data.get("difficulty", "medium"),
                    flag_pattern=chal_data.get("flag_pattern", r"flag\{[^}]+\}"),
                    description=chal_data.get("description", ""),
                    setup_script=chal_data.get("setup_script", ""),
                    docker_compose=chal_data.get("docker_compose", ""),
                    ports=chal_data.get("ports", []),
                    environment=chal_data.get("environment", {}),
                    time_limit_seconds=chal_data.get("time_limit_seconds", 1800),
                )
                deployed = self.deploy_from_definition(challenge)
                deployments.append(deployed)

        except Exception as e:
            deployed = DeployedChallenge(
                challenge=ChallengeDefinition(name="error"),
                status="error",
                logs=[f"Failed to load registry: {e}"],
            )
            deployments.append(deployed)

        return deployments

    def get_deployment(self, name: str) -> Optional[DeployedChallenge]:
        """Get deployment information.

        Args:
            name: Challenge name.

        Returns:
            Deployed challenge or None.
        """
        return self._deployments.get(name)

    def list_deployments(self) -> List[DeployedChallenge]:
        """List all current deployments.

        Returns:
            List of deployed challenges.
        """
        return list(self._deployments.values())

    def cleanup_deployment(self, name: str) -> bool:
        """Clean up a deployed challenge.

        Args:
            name: Challenge name.

        Returns:
            True if cleaned up successfully.
        """
        if name in self._deployments:
            self.sandbox_manager.destroy_sandbox(f"ctf_challenge_{name}")
            del self._deployments[name]
            return True
        return False

    def cleanup_all(self) -> int:
        """Clean up all deployments.

        Returns:
            Number of deployments cleaned up.
        """
        count = 0
        for name in list(self._deployments.keys()):
            if self.cleanup_deployment(name):
                count += 1
            else:
                count += 1  # Count removal from dict even if sandbox destroy fails
        return count

    def _deploy_docker_compose(
        self, deployed: DeployedChallenge, challenge: ChallengeDefinition
    ) -> DeployedChallenge:
        """Deploy challenge using docker-compose.

        Args:
            deployed: Current deployment state.
            challenge: Challenge definition.

        Returns:
            Updated deployment state.
        """
        try:
            import subprocess

            result = subprocess.run(
                [
                    "docker-compose", "-f", challenge.docker_compose,
                    "up", "-d",
                ],
                capture_output=True, text=True, timeout=120,
            )

            deployed.logs.append(result.stdout)
            if result.returncode == 0:
                deployed.status = "running"
            else:
                deployed.status = "error"
                deployed.logs.append(f"Compose error: {result.stderr}")

        except Exception as e:
            deployed.status = "error"
            deployed.logs.append(f"Docker compose failed: {e}")

        return deployed

    def _run_setup_script(
        self, container_name: str, script_path: str, deployed: DeployedChallenge
    ) -> None:
        """Run a setup script inside a container.

        Args:
            container_name: Target container name.
            script_path: Path to setup script.
            deployed: Deployment to update with logs.
        """
        try:
            import subprocess

            result = subprocess.run(
                [
                    "docker", "exec", container_name,
                    "bash", "-c", f"cat {script_path} | bash",
                ],
                capture_output=True, text=True, timeout=300,
            )
            deployed.logs.append(f"Setup: {result.stdout}")
            if result.returncode != 0:
                deployed.logs.append(f"Setup error: {result.stderr}")
        except Exception as e:
            deployed.logs.append(f"Setup failed: {e}")