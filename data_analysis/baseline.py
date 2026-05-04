"""Baseline comparison system for CTF benchmark evaluation - rnd_project_part2.

Supports the 9-metric evaluation system with reference baselines:
  - Human expert: 4.3h avg solve time (HTB community average)
  - Expert writeup: Optimal attack path from official writeups
  - Previous best: Historical best run for comparison

All baselines use the 3-category / 9-metric structure.
"""

import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from data_analysis.log_parser import ParsedSession, ParseSummary
from data_analysis.metrics_engine import (
    BenchmarkMetrics, EfficiencyMetrics, IntelligenceMetrics,
    CoverageMetrics, MetricsEngine,
)


@dataclass
class BaselineProfile:
    """A baseline profile for comparison.

    Attributes:
        name: Baseline name (e.g., "human_expert", "expert_writeup").
        description: Description of the baseline.
        efficiency: 效率与资源 baseline.
        intelligence: 规划与智能 baseline.
        coverage: 能力覆盖 baseline.
        metrics: Legacy metrics (for backward compatibility).
        source: Where the baseline data came from.
        created_at: Baseline creation timestamp.
    """

    name: str = ""
    description: str = ""
    efficiency: Optional[EfficiencyMetrics] = None
    intelligence: Optional[IntelligenceMetrics] = None
    coverage: Optional[CoverageMetrics] = None
    metrics: Optional[BenchmarkMetrics] = None
    source: str = ""
    created_at: Optional[datetime] = None


@dataclass
class BaselineComparison:
    """Comparison result between current run and baselines - 9-metric system.

    Attributes:
        run_name: Name of the current run.
        run_metrics: Metrics from current run.
        comparisons: Per-baseline comparison results.
        summary: Overall comparison summary.
        compared_at: Comparison timestamp.
    """

    run_name: str = ""
    run_metrics: Optional[BenchmarkMetrics] = None
    comparisons: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    summary: Dict[str, Any] = field(default_factory=dict)
    compared_at: Optional[datetime] = None


class BaselineManager:
    """Manages baseline profiles and compares benchmark results.

    Provides baseline profiles aligned with rnd_project_part2:
    - Human expert (theoretical upper bound)
      * 4.3h avg solve time (HTB community human average)
    - Expert writeup (optimal attack path)
    - Random solver (theoretical lower bound)
    - Tool-only (no AI agent) baseline
    - Average CTF player

    All profiles use the 9-metric 3-category structure.
    """

    # Total vuln types in standard benchmark set
    TOTAL_VULN_TYPES = 27

    def __init__(self, total_vuln_types: int = 27):
        """Initialize baseline manager with default profiles.

        Args:
            total_vuln_types: Total vuln types in benchmark set.
        """
        self._baselines: Dict[str, BaselineProfile] = {}
        self._engine = MetricsEngine(total_vuln_types=total_vuln_types)
        self._total_vuln_types = total_vuln_types
        self._create_default_baselines()

    def add_baseline(self, profile: BaselineProfile) -> None:
        """Add a custom baseline profile.

        Args:
            profile: Baseline profile to add.
        """
        profile.created_at = profile.created_at or datetime.now()
        self._baselines[profile.name] = profile

    def get_baseline(self, name: str) -> Optional[BaselineProfile]:
        """Get a baseline by name.

        Args:
            name: Baseline name.

        Returns:
            Baseline profile or None.
        """
        return self._baselines.get(name)

    def list_baselines(self) -> List[BaselineProfile]:
        """List all available baselines.

        Returns:
            List of baseline profiles.
        """
        return list(self._baselines.values())

    def save_baseline_from_run(
        self,
        name: str,
        sessions: List[ParsedSession],
        description: str = "",
    ) -> BaselineProfile:
        """Create and save a baseline from a benchmark run.

        Args:
            name: Baseline name.
            sessions: Parsed sessions from the run.
            description: Baseline description.

        Returns:
            Created baseline profile.
        """
        metrics = self._engine.calculate_metrics(sessions)
        profile = BaselineProfile(
            name=name,
            description=description,
            efficiency=metrics.efficiency,
            intelligence=metrics.intelligence,
            coverage=metrics.coverage,
            metrics=metrics,
            source="benchmark_run",
            created_at=datetime.now(),
        )
        self._baselines[name] = profile
        return profile

    def compare_to_baselines(
        self,
        run_name: str,
        sessions: List[ParsedSession],
        baseline_names: Optional[List[str]] = None,
    ) -> BaselineComparison:
        """Compare a benchmark run to saved baselines using 9-metric system.

        Args:
            run_name: Name of the current run.
            sessions: Parsed sessions from the run.
            baseline_names: Specific baselines to compare to (all if None).

        Returns:
            Comparison results with 9-metric breakdowns.
        """
        run_metrics = self._engine.calculate_metrics(sessions)

        comparison = BaselineComparison(
            run_name=run_name,
            run_metrics=run_metrics,
            compared_at=datetime.now(),
        )

        baselines_to_use = (
            [self._baselines[n] for n in baseline_names if n in self._baselines]
            if baseline_names
            else list(self._baselines.values())
        )

        for baseline in baselines_to_use:
            comp = self._build_comparison_entry(run_metrics, baseline)
            if comp:
                comparison.comparisons[baseline.name] = comp

        # Calculate overall summary
        comparison.summary = self._build_comparison_summary(comparison)

        return comparison

    def export_baselines(self, filepath: str) -> str:
        """Export baselines to JSON.

        Args:
            filepath: Output file path.

        Returns:
            Output file path.
        """
        data = {
            "exported_at": datetime.now().isoformat(),
            "total_vuln_types": self._total_vuln_types,
            "baselines": {},
        }

        for name, profile in self._baselines.items():
            entry: Dict[str, Any] = {
                "description": profile.description,
                "source": profile.source,
                "created_at": profile.created_at.isoformat() if profile.created_at else None,
            }
            if profile.efficiency:
                entry["efficiency"] = profile.efficiency.to_dict()
            if profile.intelligence:
                entry["intelligence"] = profile.intelligence.to_dict()
            if profile.coverage:
                entry["coverage"] = profile.coverage.to_dict()
            if profile.metrics:
                entry["metrics"] = profile.metrics.to_dict()
            data["baselines"][name] = entry

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return filepath

    def import_baselines(self, filepath: str) -> int:
        """Import baselines from JSON file.

        Args:
            filepath: Path to JSON file.

        Returns:
            Number of baselines imported.
        """
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            count = 0
            for name, bdata in data.get("baselines", {}).items():
                profile = BaselineProfile(
                    name=name,
                    description=bdata.get("description", ""),
                    source=bdata.get("source", ""),
                )

                # Import 9-metric efficiency
                if "efficiency" in bdata:
                    profile.efficiency = EfficiencyMetrics(**bdata["efficiency"])

                # Import 9-metric intelligence
                if "intelligence" in bdata:
                    profile.intelligence = IntelligenceMetrics(**bdata["intelligence"])

                # Import 9-metric coverage
                if "coverage" in bdata:
                    profile.coverage = CoverageMetrics(**bdata["coverage"])

                # Legacy metrics
                if "metrics" in bdata:
                    metrics = BenchmarkMetrics()
                    for key, value in bdata["metrics"].items():
                        if hasattr(metrics, key):
                            setattr(metrics, key, value)
                    profile.metrics = metrics

                self._baselines[name] = profile
                count += 1

            return count
        except Exception:
            return 0

    def _create_default_baselines(self) -> None:
        """Create standard baseline profiles with 9-metric structure."""
        # Human expert baseline (HTB community human average: 4.3h)
        self._baselines["human_expert"] = BaselineProfile(
            name="human_expert",
            description="HTB社区人类CTF选手平均水平（平均解题时间4.3小时）",
            efficiency=EfficiencyMetrics(
                task_completion_rate=95.0,
                avg_solve_time_seconds=15480,  # 4.3 hours
                tool_call_accuracy=98.0,
                token_economy_total=0,
                token_economy_input=0,
                token_economy_output=0,
            ),
            intelligence=IntelligenceMetrics(
                first_attempt_success_rate=70.0,
                hallucination_rate=5.0,
                attack_path_quality=8.0,  # ~8 steps per solve
                error_recovery_rate=90.0,
            ),
            coverage=CoverageMetrics(
                challenge_type_coverage=85.0,
                vuln_types_mastered=self._engine.STANDARD_VULN_TYPES[:23],
                total_vuln_types=self._total_vuln_types,
                category_breakdown={"web": 0.90, "pwn": 0.72, "crypto": 0.75, "reverse": 0.68, "misc": 0.78},
                difficulty_breakdown={"easy": 0.98, "medium": 0.75, "hard": 0.45},
                difficulty_penetration=0.45,
            ),
            metrics=BenchmarkMetrics(
                accuracy=0.95, precision=0.98, f1_score=0.965,
                avg_time_to_solve=15480, avg_tool_calls=8,
                avg_tokens=0, error_rate=0.1,
                difficulty_penetration=0.45, tool_efficiency=0.12,
                cost_estimate_usd=0, total_flags=23,
            ),
            source="HTB_community",
        )

        # Expert writeup baseline (optimal path reference)
        self._baselines["expert_writeup"] = BaselineProfile(
            name="expert_writeup",
            description="题目Writeup中的最优攻击路径（理论最优步数）",
            efficiency=EfficiencyMetrics(
                task_completion_rate=100.0,
                avg_solve_time_seconds=3600,  # 1 hour ideal
                tool_call_accuracy=100.0,
                token_economy_total=0,
                token_economy_input=0,
                token_economy_output=0,
            ),
            intelligence=IntelligenceMetrics(
                first_attempt_success_rate=100.0,
                hallucination_rate=0.0,
                attack_path_quality=5.0,  # ~5 optimal steps
                error_recovery_rate=100.0,
            ),
            coverage=CoverageMetrics(
                challenge_type_coverage=100.0,
                vuln_types_mastered=list(self._engine.STANDARD_VULN_TYPES),
                total_vuln_types=self._total_vuln_types,
                category_breakdown={"web": 1.0, "pwn": 1.0, "crypto": 1.0, "reverse": 1.0, "misc": 1.0},
                difficulty_breakdown={"easy": 1.0, "medium": 1.0, "hard": 1.0},
                difficulty_penetration=1.0,
            ),
            metrics=BenchmarkMetrics(
                accuracy=1.0, precision=1.0, f1_score=1.0,
                avg_time_to_solve=3600, avg_tool_calls=5,
                avg_tokens=0, error_rate=0,
                difficulty_penetration=1.0, tool_efficiency=0.25,
                cost_estimate_usd=0, total_flags=27,
            ),
            source="writeup_optimal",
        )

        # Random solver baseline (theoretical lower bound)
        self._baselines["random_solver"] = BaselineProfile(
            name="random_solver",
            description="随机/暴力尝试方法（理论下界）",
            efficiency=EfficiencyMetrics(
                task_completion_rate=3.0,
                avg_solve_time_seconds=7200,  # 2 hours
                tool_call_accuracy=5.0,
                token_economy_total=500000,
                token_economy_input=300000,
                token_economy_output=200000,
            ),
            intelligence=IntelligenceMetrics(
                first_attempt_success_rate=2.0,
                hallucination_rate=80.0,
                attack_path_quality=50.0,
                error_recovery_rate=10.0,
            ),
            coverage=CoverageMetrics(
                challenge_type_coverage=5.0,
                vuln_types_mastered=["sqli"],
                total_vuln_types=self._total_vuln_types,
                category_breakdown={"web": 0.02, "pwn": 0.01, "crypto": 0.01, "reverse": 0.0, "misc": 0.01},
                difficulty_breakdown={"easy": 0.05, "medium": 0.01, "hard": 0.0},
                difficulty_penetration=0.0,
            ),
            metrics=BenchmarkMetrics(
                accuracy=0.02, precision=0.01, f1_score=0.015,
                avg_time_to_solve=7200, avg_tool_calls=50,
                avg_tokens=500000, error_rate=5.0,
                difficulty_penetration=0.0, tool_efficiency=0.0004,
                cost_estimate_usd=0.25, total_flags=1,
            ),
            source="theoretical",
        )

        # Tool-only baseline (no AI reasoning)
        self._baselines["tool_only"] = BaselineProfile(
            name="tool_only",
            description="无AI推理的自动化工具执行基线",
            efficiency=EfficiencyMetrics(
                task_completion_rate=25.0,
                avg_solve_time_seconds=900,  # 15 minutes
                tool_call_accuracy=80.0,
                token_economy_total=0,
                token_economy_input=0,
                token_economy_output=0,
            ),
            intelligence=IntelligenceMetrics(
                first_attempt_success_rate=50.0,
                hallucination_rate=0.0,  # No AI = no hallucinations
                attack_path_quality=20.0,
                error_recovery_rate=30.0,
            ),
            coverage=CoverageMetrics(
                challenge_type_coverage=25.0,
                vuln_types_mastered=["sqli", "xss", "command_injection", "file_inclusion", "reverse_engineering"],
                total_vuln_types=self._total_vuln_types,
                category_breakdown={"web": 0.35, "pwn": 0.05, "crypto": 0.05, "reverse": 0.10, "misc": 0.10},
                difficulty_breakdown={"easy": 0.45, "medium": 0.10, "hard": 0.00},
                difficulty_penetration=0.00,
            ),
            metrics=BenchmarkMetrics(
                accuracy=0.25, precision=0.30, f1_score=0.27,
                avg_time_to_solve=900, avg_tool_calls=20,
                avg_tokens=0, error_rate=2.0,
                difficulty_penetration=0.00, tool_efficiency=0.0125,
                cost_estimate_usd=0, total_flags=5,
            ),
            source="theoretical",
        )

        # Average beginner CTF player baseline
        self._baselines["avg_ctf_player"] = BaselineProfile(
            name="avg_ctf_player",
            description="CTF新手参与者平均水平",
            efficiency=EfficiencyMetrics(
                task_completion_rate=35.0,
                avg_solve_time_seconds=5400,  # 1.5 hours
                tool_call_accuracy=60.0,
                token_economy_total=200000,
                token_economy_input=120000,
                token_economy_output=80000,
            ),
            intelligence=IntelligenceMetrics(
                first_attempt_success_rate=35.0,
                hallucination_rate=20.0,
                attack_path_quality=18.0,
                error_recovery_rate=55.0,
            ),
            coverage=CoverageMetrics(
                challenge_type_coverage=30.0,
                vuln_types_mastered=["sqli", "xss", "csrf", "command_injection",
                                     "file_inclusion", "buffer_overflow",
                                     "reverse_engineering", "forensics"],
                total_vuln_types=self._total_vuln_types,
                category_breakdown={"web": 0.45, "pwn": 0.15, "crypto": 0.15, "reverse": 0.25, "misc": 0.20},
                difficulty_breakdown={"easy": 0.60, "medium": 0.20, "hard": 0.02},
                difficulty_penetration=0.02,
            ),
            metrics=BenchmarkMetrics(
                accuracy=0.35, precision=0.40, f1_score=0.37,
                avg_time_to_solve=5400, avg_tool_calls=18,
                avg_tokens=200000, error_rate=2.5,
                difficulty_penetration=0.02, tool_efficiency=0.02,
                cost_estimate_usd=0.10, total_flags=8,
            ),
            source="theoretical",
        )

    def _build_comparison_entry(
        self,
        run_metrics: BenchmarkMetrics,
        baseline: BaselineProfile,
    ) -> Optional[Dict[str, Any]]:
        """Build a 9-metric comparison entry between run and baseline.

        Args:
            run_metrics: Current run metrics.
            baseline: Baseline profile.

        Returns:
            Comparison entry dictionary, or None if no data.
        """
        entry: Dict[str, Any] = {
            "description": baseline.description,
            "run": {},
            "baseline": {},
            "differences": {},
        }

        # Efficiency comparison
        if run_metrics.efficiency and baseline.efficiency:
            entry["run"]["efficiency"] = run_metrics.efficiency.to_dict()
            entry["baseline"]["efficiency"] = baseline.efficiency.to_dict()
            entry["differences"]["efficiency"] = {
                "task_completion_rate": round(
                    run_metrics.efficiency.task_completion_rate -
                    baseline.efficiency.task_completion_rate, 2
                ),
                "avg_solve_time": round(
                    run_metrics.efficiency.avg_solve_time_seconds -
                    baseline.efficiency.avg_solve_time_seconds, 2
                ),
                "tool_call_accuracy": round(
                    run_metrics.efficiency.tool_call_accuracy -
                    baseline.efficiency.tool_call_accuracy, 2
                ),
                "token_economy": (
                    run_metrics.efficiency.token_economy_total -
                    baseline.efficiency.token_economy_total
                ),
            }

        # Intelligence comparison
        if run_metrics.intelligence and baseline.intelligence:
            entry["run"]["intelligence"] = run_metrics.intelligence.to_dict()
            entry["baseline"]["intelligence"] = baseline.intelligence.to_dict()
            entry["differences"]["intelligence"] = {
                "first_attempt_success_rate": round(
                    run_metrics.intelligence.first_attempt_success_rate -
                    baseline.intelligence.first_attempt_success_rate, 2
                ),
                "hallucination_rate": round(
                    run_metrics.intelligence.hallucination_rate -
                    baseline.intelligence.hallucination_rate, 2
                ),
                "attack_path_quality": round(
                    run_metrics.intelligence.attack_path_quality -
                    baseline.intelligence.attack_path_quality, 2
                ),
                "error_recovery_rate": round(
                    run_metrics.intelligence.error_recovery_rate -
                    baseline.intelligence.error_recovery_rate, 2
                ),
            }

        # Coverage comparison
        if run_metrics.coverage and baseline.coverage:
            entry["run"]["coverage"] = run_metrics.coverage.to_dict()
            entry["baseline"]["coverage"] = {
                "challenge_type_coverage": baseline.coverage.challenge_type_coverage,
                "difficulty_penetration": baseline.coverage.difficulty_penetration,
                "vuln_types_mastered_count": len(baseline.coverage.vuln_types_mastered),
                "total_vuln_types": baseline.coverage.total_vuln_types,
            }
            entry["differences"]["coverage"] = {
                "challenge_type_coverage": round(
                    run_metrics.coverage.challenge_type_coverage -
                    baseline.coverage.challenge_type_coverage, 2
                ),
                "difficulty_penetration": round(
                    run_metrics.coverage.difficulty_penetration -
                    baseline.coverage.difficulty_penetration, 4
                ),
            }

        # Legacy differences
        entry["differences"]["legacy"] = {
            "accuracy": round(run_metrics.accuracy - (baseline.metrics.accuracy if baseline.metrics else 0), 4),
            "f1_score": round(run_metrics.f1_score - (baseline.metrics.f1_score if baseline.metrics else 0), 4),
        }

        return entry

    def _build_comparison_summary(
        self, comparison: BaselineComparison
    ) -> Dict[str, Any]:
        """Build overall comparison summary.

        Args:
            comparison: Baseline comparison data.

        Returns:
            Summary dictionary.
        """
        if not comparison.comparisons:
            return {
                "best_baseline_match": "none",
                "baselines_compared": 0,
            }

        # Find best matching baseline by closest task completion rate
        best_match = "none"
        best_diff = float("inf")
        for name, comp in comparison.comparisons.items():
            eff_diff = comp.get("differences", {}).get("efficiency", {})
            rate_diff = abs(eff_diff.get("task_completion_rate", 100))
            if rate_diff < best_diff:
                best_diff = rate_diff
                best_match = name

        return {
            "best_baseline_match": best_match,
            "baselines_compared": len(comparison.comparisons),
            "closest_completion_rate_diff": best_diff,
        }

    def _metrics_to_dict(self, metrics: Optional[BenchmarkMetrics]) -> Dict[str, Any]:
        """Convert BenchmarkMetrics to dictionary.

        Args:
            metrics: Metrics to convert.

        Returns:
            Dictionary representation.
        """
        if not metrics:
            return {}
        return metrics.to_dict()

    def _find_best_baseline(self, diffs: List[float]) -> str:
        """Find baseline with closest accuracy to run.

        Args:
            diffs: List of accuracy differences.

        Returns:
            Best baseline name.
        """
        if not diffs:
            return "none"
        names = list(self._baselines.keys())
        if not names:
            return "none"
        min_diff = min(abs(d) for d in diffs)
        idx = [abs(d) for d in diffs].index(min_diff)
        return names[idx] if idx < len(names) else "none"