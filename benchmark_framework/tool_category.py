"""Tool categorization for benchmarking - classifies security tools by CTF attack phase."""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Tuple

from mcp_integration.schemas.agent_state_schema import AttackPhase


class ToolCategory(Enum):
    """CTF security tool categories aligned with attack phases."""

    RECONNAISSANCE = auto()     # Phase 1: Port scanning, host discovery
    ENUMERATION = auto()        # Phase 2: Service enumeration, directory busting
    EXPLOITATION = auto()       # Phase 3: Vulnerability exploitation
    PRIVILEGE_ESCALATION = auto()  # Phase 4: Privilege escalation
    LATERAL_MOVEMENT = auto()   # Phase 4: Lateral movement
    POST_EXPLOITATION = auto()  # Phase 5: Search, flag capture
    GENERAL = auto()            # General-purpose utility


TOOL_PHASE_MAP: Dict[AttackPhase, ToolCategory] = {
    AttackPhase.RECONNAISSANCE: ToolCategory.RECONNAISSANCE,
    AttackPhase.ENUMERATION: ToolCategory.ENUMERATION,
    AttackPhase.EXPLOITATION: ToolCategory.EXPLOITATION,
    AttackPhase.POST_EXPLOITATION: ToolCategory.POST_EXPLOITATION,
    AttackPhase.FLAG_CAPTURE: ToolCategory.POST_EXPLOITATION,
}


@dataclass
class CategoryStats:
    """Statistics for tools in a category.

    Attributes:
        category: Tool category name.
        total_tools: Number of tools in category.
        avg_success_rate: Average success rate across tools.
        avg_execution_time_ms: Average execution time.
        top_tools: List of top-performing tool names.
    """

    category: ToolCategory
    total_tools: int = 0
    avg_success_rate: float = 0.0
    avg_execution_time_ms: float = 0.0
    top_tools: List[str] = field(default_factory=list)


# Known security tool classifications
KNOWN_TOOL_CATEGORIES: Dict[str, ToolCategory] = {
    # Reconnaissance
    "nmap_scan": ToolCategory.RECONNAISSANCE,
    "masscan": ToolCategory.RECONNAISSANCE,
    "dns_lookup": ToolCategory.RECONNAISSANCE,
    "whois_lookup": ToolCategory.RECONNAISSANCE,
    "ping_sweep": ToolCategory.RECONNAISSANCE,
    "traceroute": ToolCategory.RECONNAISSANCE,
    # Enumeration
    "gobuster_scan": ToolCategory.ENUMERATION,
    "nikto_scan": ToolCategory.ENUMERATION,
    "dirb_scan": ToolCategory.ENUMERATION,
    "enum4linux": ToolCategory.ENUMERATION,
    "smb_enum": ToolCategory.ENUMERATION,
    "dns_enum": ToolCategory.ENUMERATION,
    "sslscan": ToolCategory.ENUMERATION,
    # Exploitation
    "sqlmap_scan": ToolCategory.EXPLOITATION,
    "hydra_bruteforce": ToolCategory.EXPLOITATION,
    "searchsploit": ToolCategory.EXPLOITATION,
    "metasploit": ToolCategory.EXPLOITATION,
    "burp_scanner": ToolCategory.EXPLOITATION,
    "xss_scanner": ToolCategory.EXPLOITATION,
    "csrf_tester": ToolCategory.EXPLOITATION,
    "command_injection": ToolCategory.EXPLOITATION,
    "file_upload_exploit": ToolCategory.EXPLOITATION,
    # Privilege Escalation
    "lse_enum": ToolCategory.PRIVILEGE_ESCALATION,
    "linpeas": ToolCategory.PRIVILEGE_ESCALATION,
    "winpeas": ToolCategory.PRIVILEGE_ESCALATION,
    "privesc_check": ToolCategory.PRIVILEGE_ESCALATION,
    "sudo_exploit": ToolCategory.PRIVILEGE_ESCALATION,
    "suid_finder": ToolCategory.PRIVILEGE_ESCALATION,
    # General
    "find_command": ToolCategory.GENERAL,
    "cat_command": ToolCategory.GENERAL,
    "grep_flag": ToolCategory.GENERAL,
    "execute_command": ToolCategory.GENERAL,
    "ssh_exec": ToolCategory.GENERAL,
    "curl_request": ToolCategory.GENERAL,
    "base64_decode": ToolCategory.GENERAL,
    "hex_decode": ToolCategory.GENERAL,
}


class ToolClassifier:
    """Classifies tools into categories based on name and function.

    Provides methods to categorize tools, group them by attack phase,
    and compute category-level statistics.
    """

    def __init__(self, custom_mappings: Dict[str, ToolCategory] = None):
        """Initialize classifier with optional custom mappings.

        Args:
            custom_mappings: Additional tool->category mappings.
        """
        self._mappings: Dict[str, ToolCategory] = dict(KNOWN_TOOL_CATEGORIES)
        if custom_mappings:
            self._mappings.update(custom_mappings)

    def classify(self, tool_name: str) -> ToolCategory:
        """Classify a single tool by name.

        Args:
            tool_name: Tool name to classify.

        Returns:
            ToolCategory classification.
        """
        # Direct match
        if tool_name in self._mappings:
            return self._mappings[tool_name]

        # Substring matching
        tool_lower = tool_name.lower()
        classification_keywords: List[Tuple[List[str], ToolCategory]] = [
            (["nmap", "scan", "masscan", "dns_scan", "whois", "ping"], ToolCategory.RECONNAISSANCE),
            (["gobuster", "nikto", "dirb", "enum", "dirbuster", "ffuf"], ToolCategory.ENUMERATION),
            (["sqlmap", "hydra", "exploit", "sploit", "searchsploit", "msf"], ToolCategory.EXPLOITATION),
            (["linpeas", "winpeas", "lse_", "privesc", "sudo", "suid"], ToolCategory.PRIVILEGE_ESCALATION),
            (["find", "cat", "grep", "ssh", "curl", "exec", "run_command"], ToolCategory.GENERAL),
        ]

        for keywords, category in classification_keywords:
            for kw in keywords:
                if kw in tool_lower:
                    return category

        return ToolCategory.GENERAL

    def classify_batch(self, tool_names: List[str]) -> Dict[ToolCategory, List[str]]:
        """Classify multiple tools and group by category.

        Args:
            tool_names: List of tool names.

        Returns:
            Dictionary mapping categories to tool name lists.
        """
        groups: Dict[ToolCategory, List[str]] = {
            cat: [] for cat in ToolCategory
        }
        for name in tool_names:
            category = self.classify(name)
            groups[category].append(name)
        return groups

    def count_by_category(self, tool_names: List[str]) -> Dict[ToolCategory, int]:
        """Count tools in each category.

        Args:
            tool_names: List of tool names.

        Returns:
            Dictionary mapping categories to counts.
        """
        counts: Dict[ToolCategory, int] = {
            cat: 0 for cat in ToolCategory
        }
        for name in tool_names:
            category = self.classify(name)
            counts[category] += 1
        return counts

    def get_phase_tools(
        self, tool_names: List[str], phase: AttackPhase
    ) -> List[str]:
        """Get tools relevant to a specific attack phase.

        Args:
            tool_names: List of tool names.
            phase: Attack phase to filter by.

        Returns:
            Tools relevant to the specified phase.
        """
        target_category = TOOL_PHASE_MAP.get(phase, ToolCategory.GENERAL)
        return [
            name for name in tool_names
            if self.classify(name) == target_category
        ]

    @staticmethod
    def get_phase_description(phase: AttackPhase) -> str:
        """Get human-readable description of an attack phase.

        Args:
            phase: Attack phase.

        Returns:
            Phase description.
        """
        descriptions = {
            AttackPhase.RECONNAISSANCE: "Target discovery and port scanning",
            AttackPhase.ENUMERATION: "Service and vulnerability enumeration",
            AttackPhase.EXPLOITATION: "Active exploitation of vulnerabilities",
            AttackPhase.POST_EXPLOITATION: "Post-compromise search and privilege escalation",
            AttackPhase.FLAG_CAPTURE: "Flag capture and verification",
        }
        return descriptions.get(phase, "Unknown phase")