"""Log parser for CTF benchmark data - extracts structured data from raw logs.

Supports the rnd_project_part2 9-metric evaluation system:
  - 效率与资源: 任务完成率, 平均解题时间, 工具调用准确率, Token经济性
  - 规划与智能: 首次尝试成功率, 幻觉率, 攻击路径质量, 错误恢复率
  - 能力覆盖: 题型覆盖度
"""

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class ParsedSession:
    """Parsed data from a single CTF benchmark session.

    Attributes:
        session_id: Unique session identifier.
        challenge_name: Challenge solved.
        category: Challenge category (web, pwn, crypto, reverse, misc).
        vuln_type: Specific vulnerability type (for coverage metric).
        difficulty: Challenge difficulty.
        success: Whether the challenge was solved (flag captured).
        flag: Captured flag.
        start_time: Session start time.
        end_time: Session end time.
        duration_seconds: Session duration.
        tool_calls: Number of tool invocations.
        tool_calls_success: Number of successful tool calls.
        errors: Number of errors encountered.
        error_recovery_count: Times recovered from errors.
        input_tokens: Number of input/prompt tokens.
        output_tokens: Number of output/completion tokens.
        tokens_used: Total tokens consumed (input + output).
        model_name: LLM model used.
        first_attempt_success: Whether the first flag submission was correct.
        hallucination_count: Number of hallucination instances (manual annotation).
        attack_path_steps: Number of steps in the attack path (fewer = better).
        steps: Individual reasoning/action steps.
    """

    session_id: str = ""
    challenge_name: str = ""
    category: str = ""
    vuln_type: str = ""
    difficulty: str = ""
    success: bool = False
    flag: str = ""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0
    tool_calls: int = 0
    tool_calls_success: int = 0
    errors: int = 0
    error_recovery_count: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    tokens_used: int = 0
    model_name: str = ""
    first_attempt_success: Optional[bool] = None
    hallucination_count: int = 0
    attack_path_steps: int = 0
    steps: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def tool_call_accuracy(self) -> float:
        """Calculate tool call accuracy for this session."""
        if self.tool_calls == 0:
            return 0.0
        return self.tool_calls_success / self.tool_calls

    @property
    def token_economy(self) -> int:
        """Total token consumption (input + output)."""
        return self.input_tokens + self.output_tokens

    @property
    def error_recovery_rate(self) -> float:
        """Error recovery rate for this session."""
        if self.errors == 0:
            return 1.0
        return self.error_recovery_count / self.errors

    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary for serialization."""
        return {
            "session_id": self.session_id,
            "challenge_name": self.challenge_name,
            "category": self.category,
            "vuln_type": self.vuln_type,
            "difficulty": self.difficulty,
            "success": self.success,
            "flag": self.flag,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration_seconds,
            "tool_calls": self.tool_calls,
            "tool_calls_success": self.tool_calls_success,
            "errors": self.errors,
            "error_recovery_count": self.error_recovery_count,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "tokens_used": self.tokens_used,
            "model_name": self.model_name,
            "first_attempt_success": self.first_attempt_success,
            "hallucination_count": self.hallucination_count,
            "attack_path_steps": self.attack_path_steps,
            "steps": self.steps,
            "tool_call_accuracy": self.tool_call_accuracy,
            "error_recovery_rate": self.error_recovery_rate,
            "token_economy": self.token_economy,
        }


@dataclass
class ParseSummary:
    """Summary of parsed log data.

    Attributes:
        total_sessions: Total sessions parsed.
        success_count: Successful sessions.
        failure_count: Failed sessions.
        avg_duration: Average session duration.
        avg_tool_calls: Average tool calls per session.
        avg_tokens: Average tokens per session.
        total_input_tokens: Total input tokens across sessions.
        total_output_tokens: Total output tokens across sessions.
        categories: Per-category stats.
        vuln_types_found: Set of vulnerability types discovered (for coverage).
    """

    total_sessions: int = 0
    success_count: int = 0
    failure_count: int = 0
    avg_duration: float = 0.0
    avg_tool_calls: float = 0.0
    avg_tokens: float = 0.0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    categories: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    vuln_types_found: List[str] = field(default_factory=list)


class LogParser:
    """Parses raw CTF benchmark logs into structured session data.

    Supports multiple log formats:
    - AI agent execution logs
    - XBow run output
    - LiveMCPBench results
    - Tool execution logs
    - Structured JSON benchmark logs (rnd_project_part2 format)
    """

    FLAG_PATTERN = re.compile(r"flag\{[^}]+\}", re.IGNORECASE)
    TOOL_PATTERN = re.compile(
        r"\[TOOL\]|Tool called|Executing tool|tool_call|Function call|tool_use",
        re.IGNORECASE,
    )
    TOOL_SUCCESS_PATTERN = re.compile(
        r"tool.*?(?:success|ok|完成|成功)",
        re.IGNORECASE,
    )
    ERROR_PATTERN = re.compile(
        r"\[ERROR\]|Error:|Failed:|Traceback|exception|error occurred",
        re.IGNORECASE,
    )
    TOKEN_PATTERN = re.compile(
        r"tokens?[:\s]*(\d+)",
        re.IGNORECASE,
    )
    INPUT_TOKEN_PATTERN = re.compile(
        r"input[_\s]?tokens?[:\s]*(\d+)",
        re.IGNORECASE,
    )
    OUTPUT_TOKEN_PATTERN = re.compile(
        r"output[_\s]?tokens?[:\s]*(\d+)",
        re.IGNORECASE,
    )
    STEP_PATTERN = re.compile(
        r"(?:Step|Turn|步骤)\s*(\d+)[:\s]",
        re.IGNORECASE,
    )
    HALLUCINATION_PATTERN = re.compile(
        r"(?:hallucination|幻觉|fabricat|non-existent|虚构)",
        re.IGNORECASE,
    )
    FIRST_ATTEMPT_PATTERN = re.compile(
        r"(?:first[_\s]?(?:attempt|try)|首次)[:\s]*(success|正确|ok|失败|fail)",
        re.IGNORECASE,
    )
    RECOVERY_PATTERN = re.compile(
        r"(?:recover|恢复|retry succeeded|重试成功)",
        re.IGNORECASE,
    )
    VULN_TYPE_PATTERN = re.compile(
        r"(?:vulnerability|漏洞|CWE)[:\s]*(\S+)",
        re.IGNORECASE,
    )

    def __init__(self):
        """Initialize the log parser."""
        self._sessions: List[ParsedSession] = []

    def parse_agent_log(
        self,
        log_text: str,
        challenge_name: str = "",
        model_name: str = "",
        category: str = "",
        vuln_type: str = "",
        difficulty: str = "",
    ) -> ParsedSession:
        """Parse an AI agent execution log.

        Args:
            log_text: Agent execution log text.
            challenge_name: Challenge name.
            model_name: LLM model used.
            category: Challenge category.
            vuln_type: Vulnerability type.
            difficulty: Challenge difficulty.

        Returns:
            Parsed session data.
        """
        session = ParsedSession(
            session_id=f"session_{datetime.now().timestamp():.0f}",
            challenge_name=challenge_name,
            category=category,
            vuln_type=vuln_type,
            difficulty=difficulty,
            model_name=model_name,
        )

        # Detect flags
        flags_found = self.FLAG_PATTERN.findall(log_text)
        if flags_found:
            session.success = True
            session.flag = flags_found[-1]

        # Count tool calls (total)
        tool_matches = self.TOOL_PATTERN.findall(log_text)
        session.tool_calls = len(tool_matches)

        # Count successful tool calls
        tool_success_matches = self.TOOL_SUCCESS_PATTERN.findall(log_text)
        session.tool_calls_success = len(tool_success_matches)

        # Count errors
        error_matches = self.ERROR_PATTERN.findall(log_text)
        session.errors = len(error_matches)

        # Count error recoveries
        recovery_matches = self.RECOVERY_PATTERN.findall(log_text)
        session.error_recovery_count = len(recovery_matches)

        # Extract tokens (input/output/total)
        input_match = self.INPUT_TOKEN_PATTERN.search(log_text)
        if input_match:
            session.input_tokens = int(input_match.group(1))
        output_match = self.OUTPUT_TOKEN_PATTERN.search(log_text)
        if output_match:
            session.output_tokens = int(output_match.group(1))
        token_match = self.TOKEN_PATTERN.search(log_text)
        if token_match and session.input_tokens == 0:
            session.tokens_used = int(token_match.group(1))
        else:
            session.tokens_used = session.input_tokens + session.output_tokens

        # Detect first attempt success
        first_match = self.FIRST_ATTEMPT_PATTERN.search(log_text)
        if first_match:
            result_text = first_match.group(1).lower()
            session.first_attempt_success = result_text in ("success", "ok", "正确")

        # Count hallucinations
        hallucination_matches = self.HALLUCINATION_PATTERN.findall(log_text)
        session.hallucination_count = len(hallucination_matches)

        # Count attack path steps
        step_matches = self.STEP_PATTERN.findall(log_text)
        if step_matches:
            session.attack_path_steps = max(int(s) for s in step_matches)

        # Extract steps
        session.steps = self._extract_steps(log_text)

        self._sessions.append(session)
        return session

    def parse_xbow_log(
        self,
        log_text: str,
        challenge_name: str = "",
        category: str = "",
        vuln_type: str = "",
        difficulty: str = "",
    ) -> ParsedSession:
        """Parse an XBow execution log.

        Args:
            log_text: XBow output log.
            challenge_name: Challenge name.
            category: Challenge category.
            vuln_type: Vulnerability type.
            difficulty: Challenge difficulty.

        Returns:
            Parsed session data.
        """
        session = ParsedSession(
            session_id=f"xbow_{datetime.now().timestamp():.0f}",
            challenge_name=challenge_name,
            category=category,
            vuln_type=vuln_type,
            difficulty=difficulty,
            model_name="xbow",
        )

        # Detect flags
        flags_found = self.FLAG_PATTERN.findall(log_text)
        if flags_found:
            session.success = True
            session.flag = flags_found[-1]

        # XBow-specific tool detection
        xbow_tool_count = len(re.findall(r"Running:|Executing:|Submitting:", log_text))
        session.tool_calls = xbow_tool_count

        # Count successful operations
        success_ops = len(re.findall(r"(?:successfully|Found flag|Flag captured)", log_text, re.IGNORECASE))
        session.tool_calls_success = success_ops

        # Count errors
        error_matches = self.ERROR_PATTERN.findall(log_text)
        session.errors = len(error_matches)

        # Count error recoveries
        recovery_matches = self.RECOVERY_PATTERN.findall(log_text)
        session.error_recovery_count = len(recovery_matches)

        # Extract steps - XBow has a different step format
        session.steps = self._extract_xbow_steps(log_text)
        session.attack_path_steps = len(session.steps)

        # First attempt detection for XBow
        first_match = self.FIRST_ATTEMPT_PATTERN.search(log_text)
        if first_match:
            result_text = first_match.group(1).lower()
            session.first_attempt_success = result_text in ("success", "ok", "正确")

        # Hallucination detection
        hallucination_matches = self.HALLUCINATION_PATTERN.findall(log_text)
        session.hallucination_count = len(hallucination_matches)

        self._sessions.append(session)
        return session

    def parse_livemcpbench_result(
        self, result_path: str
    ) -> List[ParsedSession]:
        """Parse LiveMCPBench JSON results file.

        Args:
            result_path: Path to JSON results.

        Returns:
            List of parsed sessions.
        """
        sessions = []
        try:
            with open(result_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            results_list = data.get("results", []) if isinstance(data, dict) else data

            for item in results_list:
                tool_calls = item.get("tool_calls", 0)
                tool_calls_success = item.get("tool_calls_success", 0)
                session = ParsedSession(
                    session_id=item.get("run_id", ""),
                    challenge_name=item.get("challenge", ""),
                    category=item.get("category", ""),
                    vuln_type=item.get("vuln_type", ""),
                    difficulty=item.get("difficulty", ""),
                    success=item.get("success", False),
                    flag=item.get("flag", ""),
                    duration_seconds=item.get("duration_seconds", 0),
                    tool_calls=tool_calls,
                    tool_calls_success=tool_calls_success or tool_calls,
                    errors=item.get("errors", 0),
                    error_recovery_count=item.get("error_recovery_count", 0),
                    input_tokens=item.get("input_tokens", 0),
                    output_tokens=item.get("output_tokens", 0),
                    tokens_used=item.get("tokens", 0),
                    model_name=item.get("model", ""),
                    first_attempt_success=item.get("first_attempt_success"),
                    hallucination_count=item.get("hallucination_count", 0),
                    attack_path_steps=item.get("attack_path_steps", 0),
                )
                sessions.append(session)
                self._sessions.append(session)

        except Exception:
            pass

        return sessions

    def parse_batch_results(
        self, results_path: str
    ) -> List[ParsedSession]:
        """Parse batch run results JSON.

        Args:
            results_path: Path to batch results JSON.

        Returns:
            List of parsed sessions.
        """
        sessions = []
        try:
            with open(results_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            challenges = data.get("challenges", [])
            for item in challenges:
                tool_calls = item.get("tool_calls", 0)
                session = ParsedSession(
                    session_id=data.get("batch_id", ""),
                    challenge_name=item.get("name", ""),
                    category=item.get("category", ""),
                    vuln_type=item.get("vuln_type", ""),
                    difficulty=item.get("difficulty", ""),
                    success=item.get("success", False),
                    flag=item.get("flag", ""),
                    duration_seconds=item.get("duration_seconds", 0),
                    tool_calls=tool_calls,
                    tool_calls_success=item.get("tool_calls_success", tool_calls),
                    errors=item.get("errors", 0),
                    error_recovery_count=item.get("error_recovery_count", 0),
                    input_tokens=item.get("input_tokens", 0),
                    output_tokens=item.get("output_tokens", 0),
                    tokens_used=item.get("tokens", 0),
                    model_name=item.get("model", ""),
                    attack_path_steps=item.get("attack_path_steps", 0),
                )
                sessions.append(session)
                self._sessions.append(session)

        except Exception:
            pass

        return sessions

    def parse_structured_log(self, log_path: str) -> List[ParsedSession]:
        """Parse structured JSON log file (rnd_project_part2 format).

        Expected JSON format:
        {
            "runs": [
                {
                    "challenge": "web_easy_01",
                    "category": "web",
                    "vuln_type": "sqli",
                    "difficulty": "easy",
                    "success": true,
                    "flag": "flag{...}",
                    "duration_seconds": 3600,
                    "tool_calls": 15,
                    "tool_calls_success": 12,
                    "errors": 3,
                    "error_recovery_count": 2,
                    "input_tokens": 5000,
                    "output_tokens": 2000,
                    "model": "gpt-4",
                    "first_attempt_success": true,
                    "hallucination_count": 0,
                    "attack_path_steps": 8
                }
            ]
        }

        Args:
            log_path: Path to structured JSON log.

        Returns:
            List of parsed sessions.
        """
        sessions = []
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            runs = data.get("runs", []) if isinstance(data, dict) else data

            for item in runs:
                session = ParsedSession(
                    session_id=item.get("session_id", item.get("challenge", f"run_{len(sessions)}")),
                    challenge_name=item.get("challenge", item.get("challenge_name", "")),
                    category=item.get("category", ""),
                    vuln_type=item.get("vuln_type", ""),
                    difficulty=item.get("difficulty", ""),
                    success=item.get("success", False),
                    flag=item.get("flag", ""),
                    duration_seconds=item.get("duration_seconds", 0),
                    tool_calls=item.get("tool_calls", 0),
                    tool_calls_success=item.get("tool_calls_success", 0),
                    errors=item.get("errors", 0),
                    error_recovery_count=item.get("error_recovery_count", 0),
                    input_tokens=item.get("input_tokens", 0),
                    output_tokens=item.get("output_tokens", 0),
                    tokens_used=item.get("tokens", item.get("input_tokens", 0) + item.get("output_tokens", 0)),
                    model_name=item.get("model", item.get("model_name", "")),
                    first_attempt_success=item.get("first_attempt_success"),
                    hallucination_count=item.get("hallucination_count", 0),
                    attack_path_steps=item.get("attack_path_steps", 0),
                )
                sessions.append(session)
                self._sessions.append(session)

        except (json.JSONDecodeError, FileNotFoundError) as e:
            pass

        return sessions

    def get_sessions(self) -> List[ParsedSession]:
        """Get all parsed sessions.

        Returns:
            List of parsed sessions.
        """
        return list(self._sessions)

    def get_successful_sessions(self) -> List[ParsedSession]:
        """Get successful sessions.

        Returns:
            List of successful sessions.
        """
        return [s for s in self._sessions if s.success]

    def get_failed_sessions(self) -> List[ParsedSession]:
        """Get failed sessions.

        Returns:
            List of failed sessions.
        """
        return [s for s in self._sessions if not s.success]

    def get_summary(self) -> ParseSummary:
        """Generate summary statistics from parsed sessions.

        Returns:
            Parse summary with aggregated stats.
        """
        if not self._sessions:
            return ParseSummary()

        successful = self.get_successful_sessions()
        durations = [s.duration_seconds for s in self._sessions if s.duration_seconds > 0]
        tool_calls = [s.tool_calls for s in self._sessions]
        tokens = [s.tokens_used for s in self._sessions if s.tokens_used > 0]

        # Token totals
        total_input = sum(s.input_tokens for s in self._sessions)
        total_output = sum(s.output_tokens for s in self._sessions)

        # Per-category stats
        categories: Dict[str, Dict[str, Any]] = {}
        for session in self._sessions:
            cat = session.category or "unknown"
            if cat not in categories:
                categories[cat] = {"total": 0, "successes": 0, "vuln_types": []}
            categories[cat]["total"] += 1
            if session.success:
                categories[cat]["successes"] += 1
            if session.vuln_type and session.vuln_type not in categories[cat]["vuln_types"]:
                categories[cat]["vuln_types"].append(session.vuln_type)

        # Unique vuln types found (for coverage metric)
        all_vuln_types: List[str] = []
        for session in self._sessions:
            if session.vuln_type and session.vuln_type not in all_vuln_types:
                all_vuln_types.append(session.vuln_type)

        return ParseSummary(
            total_sessions=len(self._sessions),
            success_count=len(successful),
            failure_count=len(self._sessions) - len(successful),
            avg_duration=sum(durations) / len(durations) if durations else 0,
            avg_tool_calls=sum(tool_calls) / len(tool_calls) if tool_calls else 0,
            avg_tokens=sum(tokens) / len(tokens) if tokens else 0,
            total_input_tokens=total_input,
            total_output_tokens=total_output,
            categories=categories,
            vuln_types_found=all_vuln_types,
        )

    def export_json(self, filepath: str) -> str:
        """Export parsed sessions to JSON.

        Args:
            filepath: Output file path.

        Returns:
            Output file path.
        """
        data = {
            "summary": self.get_summary().__dict__,
            "parsed_at": datetime.now().isoformat(),
            "sessions": [
                {
                    "session_id": s.session_id,
                    "challenge_name": s.challenge_name,
                    "category": s.category,
                    "vuln_type": s.vuln_type,
                    "difficulty": s.difficulty,
                    "success": s.success,
                    "flag": s.flag,
                    "duration_seconds": s.duration_seconds,
                    "tool_calls": s.tool_calls,
                    "tool_calls_success": s.tool_calls_success,
                    "errors": s.errors,
                    "error_recovery_count": s.error_recovery_count,
                    "input_tokens": s.input_tokens,
                    "output_tokens": s.output_tokens,
                    "tokens_used": s.tokens_used,
                    "model_name": s.model_name,
                    "first_attempt_success": s.first_attempt_success,
                    "hallucination_count": s.hallucination_count,
                    "attack_path_steps": s.attack_path_steps,
                    "tool_call_accuracy": s.tool_call_accuracy,
                    "error_recovery_rate": s.error_recovery_rate,
                    "token_economy": s.token_economy,
                }
                for s in self._sessions
            ],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return filepath

    def _extract_steps(self, log_text: str) -> List[Dict[str, Any]]:
        """Extract reasoning steps from agent log.

        Args:
            log_text: Agent log text.

        Returns:
            List of step dictionaries.
        """
        steps = []
        # Look for steps in log output
        step_matches = re.finditer(
            r"(?:Step|Turn|步骤)\s*(\d+)[:\s]*(.*?)(?=(?:Step|Turn|步骤)\s*\d+|$)",
            log_text,
            re.IGNORECASE | re.DOTALL,
        )
        for match in step_matches:
            steps.append({
                "step_number": int(match.group(1)),
                "description": match.group(2).strip()[:200],
            })
        return steps

    def _extract_xbow_steps(self, log_text: str) -> List[Dict[str, Any]]:
        """Extract steps from XBow log.

        Args:
            log_text: XBow log text.

        Returns:
            List of step dictionaries.
        """
        steps = []
        for match in re.finditer(
            r"(Running|Executing|Submitting):\s*(.*?)(?:\n|$)",
            log_text,
        ):
            steps.append({
                "type": match.group(1).lower(),
                "description": match.group(2).strip()[:200],
            })
        return steps