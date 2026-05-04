"""Docker sandbox manager for isolated CTF challenge environments."""

import os
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class SandboxStatus(Enum):
    """Status of a Docker sandbox."""
    CREATING = "creating"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    DESTROYED = "destroyed"


@dataclass
class SandboxConfig:
    """Configuration for a CTF sandbox container.

    Attributes:
        image: Docker image to use.
        cpu_limit: CPU cores limit (e.g., '1.0').
        memory_limit: Memory limit (e.g., '512m').
        network_mode: Docker network mode.
        environment: Environment variables for the container.
        volumes: Volume mounts as {host_path: container_path}.
        ports: Port mappings as {host_port: container_port}.
        timeout_seconds: Maximum sandbox lifetime.
    """
    image: str = "kalilinux/kali-rolling"
    cpu_limit: str = "1.0"
    memory_limit: str = "512m"
    network_mode: str = "bridge"
    environment: Dict[str, str] = field(default_factory=dict)
    volumes: Dict[str, str] = field(default_factory=dict)
    ports: Dict[int, int] = field(default_factory=dict)
    timeout_seconds: int = 3600


@dataclass
class SandboxInfo:
    """Information about a running sandbox.

    Attributes:
        container_id: Docker container ID.
        name: Container name.
        status: Current sandbox status.
        image: Docker image used.
        ip_address: Container IP address.
        created_at: Creation timestamp.
        ports: Mapped ports.
    """
    container_id: str = ""
    name: str = ""
    status: SandboxStatus = SandboxStatus.CREATING
    image: str = ""
    ip_address: str = ""
    created_at: Optional[datetime] = None
    ports: Dict[int, int] = field(default_factory=dict)


class SandboxManager:
    """Manages Docker sandboxes for isolated CTF environments.

    Creates, monitors, and destroys Docker containers used as attack
    targets. Each sandbox is an isolated environment with specific
    resource limits and network configuration.
    """

    def __init__(self):
        """Initialize sandbox manager."""
        self._sandboxes: Dict[str, SandboxInfo] = {}
        self._check_docker_available()

    def create_sandbox(self, name: str, config: SandboxConfig) -> SandboxInfo:
        """Create a new CTF sandbox container.

        Args:
            name: Unique sandbox name.
            config: Sandbox configuration.

        Returns:
            SandboxInfo for the created sandbox.
        """
        if not self._docker_available:
            return SandboxInfo(
                name=name,
                status=SandboxStatus.ERROR,
                image=config.image,
                created_at=datetime.now(),
            )

        # Build docker run command
        cmd = ["docker", "run", "-d", "--name", name]

        # Resource limits
        cmd.extend(["--cpus", config.cpu_limit])
        cmd.extend(["--memory", config.memory_limit])
        cmd.extend(["--network", config.network_mode])

        # Environment variables
        for key, value in config.environment.items():
            cmd.extend(["-e", f"{key}={value}"])

        # Volumes
        for host_path, container_path in config.volumes.items():
            cmd.extend(["-v", f"{host_path}:{container_path}"])

        # Ports
        for host_port, container_port in config.ports.items():
            cmd.extend(["-p", f"{host_port}:{container_port}"])

        # Image and optional entrypoint
        cmd.append(config.image)

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=60
            )
            if result.returncode == 0:
                container_id = result.stdout.strip()[:12]
                info = SandboxInfo(
                    container_id=container_id,
                    name=name,
                    status=SandboxStatus.RUNNING,
                    image=config.image,
                    created_at=datetime.now(),
                    ports=config.ports,
                )
                # Wait for IP assignment
                time.sleep(2)
                info.ip_address = self._get_container_ip(container_id)
                self._sandboxes[name] = info
                return info
            else:
                return SandboxInfo(
                    name=name,
                    status=SandboxStatus.ERROR,
                    image=config.image,
                    created_at=datetime.now(),
                )
        except subprocess.TimeoutExpired:
            return SandboxInfo(
                name=name,
                status=SandboxStatus.ERROR,
                image=config.image,
                created_at=datetime.now(),
            )
        except Exception as e:
            return SandboxInfo(
                name=name,
                status=SandboxStatus.ERROR,
                image=config.image,
                created_at=datetime.now(),
            )

    def stop_sandbox(self, name: str) -> bool:
        """Stop a running sandbox.

        Args:
            name: Sandbox name.

        Returns:
            True if stopped successfully.
        """
        try:
            subprocess.run(
                ["docker", "stop", name],
                capture_output=True, text=True, timeout=30,
            )
            if name in self._sandboxes:
                self._sandboxes[name].status = SandboxStatus.STOPPED
            return True
        except Exception:
            return False

    def destroy_sandbox(self, name: str) -> bool:
        """Stop and remove a sandbox container.

        Args:
            name: Sandbox name.

        Returns:
            True if destroyed successfully.
        """
        try:
            subprocess.run(
                ["docker", "rm", "-f", name],
                capture_output=True, text=True, timeout=30,
            )
            if name in self._sandboxes:
                self._sandboxes[name].status = SandboxStatus.DESTROYED
            return True
        except Exception:
            return False

    def get_sandbox(self, name: str) -> Optional[SandboxInfo]:
        """Get information about a sandbox.

        Args:
            name: Sandbox name.

        Returns:
            SandboxInfo or None if not found.
        """
        return self._sandboxes.get(name)

    def list_sandboxes(self) -> List[SandboxInfo]:
        """List all managed sandboxes.

        Returns:
            List of sandbox info objects.
        """
        return list(self._sandboxes.values())

    def get_container_ip_addr(self, name: str) -> str:
        """Get the IP address of a container.

        Args:
            name: Container name.

        Returns:
            Container IP address or empty string.
        """
        info = self._sandboxes.get(name)
        if info and info.container_id:
            return self._get_container_ip(info.container_id)
        return ""

    def cleanup_all(self) -> int:
        """Destroy all sandboxes and clean up resources.

        Returns:
            Number of sandboxes cleaned up.
        """
        count = 0
        for name in list(self._sandboxes.keys()):
            if self.destroy_sandbox(name):
                count += 1
        self._sandboxes.clear()
        return count

    def _check_docker_available(self) -> None:
        """Check if Docker is available on the system."""
        try:
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True, text=True, timeout=5,
            )
            self._docker_available = result.returncode == 0
        except Exception:
            self._docker_available = False

    @staticmethod
    def _get_container_ip(container_id: str) -> str:
        """Get the IP address of a Docker container.

        Args:
            container_id: Container ID or name.

        Returns:
            Container IP address.
        """
        try:
            result = subprocess.run(
                [
                    "docker", "inspect", "-f",
                    "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}",
                    container_id,
                ],
                capture_output=True, text=True, timeout=5,
            )
            return result.stdout.strip()
        except Exception:
            return ""