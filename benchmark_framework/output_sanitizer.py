"""Output sanitization for benchmarking - strips sensitive data from tool outputs."""

import re
from typing import List, Tuple


class OutputSanitizer:
    """Sanitizes tool output by masking sensitive patterns.

    Ensures that tool output used for benchmarking is safe to share
    by removing IP addresses, hostnames, credentials, and other PII.
    """

    def __init__(self, custom_patterns: List[Tuple[str, str]] = None):
        """Initialize sanitizer with default and custom patterns.

        Args:
            custom_patterns: Optional list of (pattern, replacement) tuples.
        """
        self._patterns: List[Tuple[re.Pattern, str]] = self._default_patterns()
        if custom_patterns:
            for pattern, replacement in custom_patterns:
                self._patterns.append((re.compile(pattern), replacement))

    def sanitize(self, text: str) -> str:
        """Apply all sanitization patterns to text.

        Args:
            text: Raw text to sanitize.

        Returns:
            Sanitized text with patterns masked.
        """
        result = text
        for pattern, replacement in self._patterns:
            result = pattern.sub(replacement, result)
        return result

    def sanitize_record(self, record: dict) -> dict:
        """Sanitize a complete execution record dict.

        Args:
            record: Execution record dictionary.

        Returns:
            Sanitized record dictionary.
        """
        sanitized = {}
        for key, value in record.items():
            if isinstance(value, str):
                sanitized[key] = self.sanitize(value)
            elif isinstance(value, dict):
                sanitized[key] = self.sanitize_record(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    self.sanitize(item) if isinstance(item, str) else item
                    for item in value
                ]
            else:
                sanitized[key] = value
        return sanitized

    def add_pattern(self, pattern: str, replacement: str) -> None:
        """Add a custom sanitization pattern.

        Args:
            pattern: Regex pattern to match.
            replacement: Replacement string.
        """
        self._patterns.append((re.compile(pattern), replacement))

    def has_sensitive_data(self, text: str) -> bool:
        """Check if text contains any sensitive patterns.

        Args:
            text: Text to check.

        Returns:
            True if sensitive patterns detected.
        """
        for pattern, _ in self._patterns:
            if pattern.search(text):
                return True
        return False

    @staticmethod
    def _default_patterns() -> List[Tuple[re.Pattern, str]]:
        """Create default sanitization patterns.

        Returns:
            List of (compiled_pattern, replacement) tuples.
        """
        patterns = [
            # IPv4 addresses
            (re.compile(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b"), "[IP_REDACTED]"),
            # Common hostname patterns
            (re.compile(r"\b[\w-]+\.(?:com|org|net|edu|gov|io|local|lan)\b"),
             "[HOSTNAME_REDACTED]"),
            # Email addresses
            (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
             "[EMAIL_REDACTED]"),
            # Potential credentials in key=value format
            (re.compile(r"(password|passwd|pwd|secret|token|api[_-]?key)\s*=\s*\S+",
                        re.IGNORECASE),
             r"\1=[CREDENTIAL_REDACTED]"),
            # JWT tokens
            (re.compile(r"eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+"),
             "[JWT_REDACTED]"),
            # Long hex strings (potential hashes)
            (re.compile(r"\b[a-fA-F0-9]{32,64}\b"), "[HASH_REDACTED]"),
        ]
        return patterns


class FlagMaskingSanitizer(OutputSanitizer):
    """Specialized sanitizer that preserves CTF flag structure while masking values.

    Used for benchmark comparison where we need to verify flag capture
    without exposing actual flag values in published results.
    """

    FLAG_PATTERNS = [
        r"flag\{[^}]+\}",
        r"CTF\{[^}]+\}",
        r"FLAG\{[^}]+\}",
        r"ctf\{[^}]+\}",
    ]

    def __init__(self, preserve_structure: bool = True):
        """Initialize flag masking sanitizer.

        Args:
            preserve_structure: If True, replaces flag values with [FLAG_n]
                while keeping the flag format. If False, replaces the entire flag.
        """
        super().__init__()
        self.preserve_structure = preserve_structure
        self._flag_counter = 0

    def sanitize(self, text: str) -> str:
        """Apply all sanitization patterns including flag masking.

        Args:
            text: Raw text to sanitize.

        Returns:
            Sanitized text with all patterns masked.
        """
        result = super().sanitize(text)
        result, _ = self.sanitize_flags(result)
        return result

    def has_sensitive_data(self, text: str) -> bool:
        """Check if text contains any sensitive patterns including flags.

        Args:
            text: Text to check.

        Returns:
            True if sensitive patterns detected.
        """
        if super().has_sensitive_data(text):
            return True
        for pattern in self.FLAG_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def sanitize_flags(self, text: str) -> Tuple[str, int]:
        """Sanitize flag patterns in text.

        Args:
            text: Text containing potential flags.

        Returns:
            Tuple of (sanitized_text, number_of_flags_found).
        """
        self._flag_counter = 0
        result = text

        for pattern in self.FLAG_PATTERNS:
            compiled = re.compile(pattern, re.IGNORECASE)

            def replace_flag(match):
                self._flag_counter += 1
                if self.preserve_structure:
                    return f"flag{{[FLAG_{self._flag_counter}]}}"
                return "[FLAG_REDACTED]"

            result = compiled.sub(replace_flag, result)

        return result, self._flag_counter

    def extract_flags(self, text: str) -> List[str]:
        """Extract all flag strings from text.

        Args:
            text: Text to search for flags.

        Returns:
            List of unique flag strings found.
        """
        flags = []
        for pattern in self.FLAG_PATTERNS:
            found = re.findall(pattern, text, re.IGNORECASE)
            flags.extend(found)
        return list(set(flags))