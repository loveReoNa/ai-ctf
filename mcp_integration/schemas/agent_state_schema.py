"""Agent state schema definitions for runtime state tracking."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class AttackPhase(Enum):
    """Enumeration of standard attack chain phases."""

    RECONNAISSANCE = "recon"
    ENUMERATION = "enum"
    EXPLOITATION = "exploit"
    POST_EXPLOITATION = "post_exploit"
    FLAG_CAPTURE = "flag_capture"


@dataclass
class VulnInfo:
    """Information about a discovered vulnerability.

    Attributes:
        vuln_type: CWE identifier or vulnerability type name.
        severity: Severity level (critical/high/medium/low).
        description: Human-readable description.
        target_service: The service/port affected.
        exploitability_score: Estimated exploitability (0.0-10.0).
    """

    vuln_type: str = ""
    severity: str = "medium"
    description: str = ""
    target_service: str = ""
    exploitability_score: float = 0.0


@dataclass
class ErrorRecord:
    """Record of an error encountered during agent execution.

    Attributes:
        turn_number: The turn when the error occurred.
        tool_name: Which tool was being used.
        error_type: Classification of the error.
        error_message: Human-readable error description.
        recovered: Whether the agent successfully recovered from this error.
    """

    turn_number: int = 0
    tool_name: str = ""
    error_type: str = ""
    error_message: str = ""
    recovered: bool = False


@dataclass
class AgentState:
    """Runtime state snapshot of the CTF-solving agent.

    Attributes:
        turn_number: Current execution turn.
        messages: Complete conversation history as chat messages.
        tools_available: List of tool names currently available.
        targets_identified: IPs/hosts identified during recon.
        vulnerabilities_found: Vulns discovered so far.
        flags_captured: Flags successfully captured.
        current_phase: Current attack phase.
        errors_encountered: Error log.
        memory_context: Optional memory/context summary string.
    """

    turn_number: int = 0
    messages: List[Dict[str, Any]] = field(default_factory=list)
    tools_available: List[str] = field(default_factory=list)
    targets_identified: List[str] = field(default_factory=list)
    vulnerabilities_found: List[VulnInfo] = field(default_factory=list)
    flags_captured: List[str] = field(default_factory=list)
    current_phase: AttackPhase = AttackPhase.RECONNAISSANCE
    errors_encountered: List[ErrorRecord] = field(default_factory=list)
    memory_context: Optional[str] = None

    def add_vulnerability(self, vuln: VulnInfo) -> None:
        """Record a newly discovered vulnerability."""
        self.vulnerabilities_found.append(vuln)

    def add_flag(self, flag: str) -> None:
        """Record a captured flag."""
        if flag not in self.flags_captured:
            self.flags_captured.append(flag)

    def add_error(self, error: ErrorRecord) -> None:
        """Record an error occurrence."""
        self.errors_encountered.append(error)

    def transition_phase(self, new_phase: AttackPhase) -> None:
        """Transition to a new attack phase."""
        self.current_phase = new_phase