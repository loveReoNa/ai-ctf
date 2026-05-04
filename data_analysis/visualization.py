"""Visualization module for CTF benchmark data analysis - rnd_project_part2.

Generates charts for the 9-metric evaluation system:
  - 效率与资源 (Efficiency & Resources): completion rate, solve time, tool accuracy, token economy
  - 规划与智能 (Planning & Intelligence): first attempt rate, hallucination rate, attack path, error recovery
  - 能力覆盖 (Capability Coverage): vuln type coverage radar, category/difficulty breakdowns
"""

import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

try:
    import matplotlib
    matplotlib.use("Agg")  # Non-interactive backend
    import matplotlib.pyplot as plt
    import matplotlib.ticker as ticker
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

from data_analysis.log_parser import ParsedSession, ParseSummary
from data_analysis.metrics_engine import (
    BenchmarkMetrics, EfficiencyMetrics, IntelligenceMetrics,
    CoverageMetrics, MetricsEngine,
)


@dataclass
class ChartConfig:
    """Configuration for charts.

    Attributes:
        figsize: Figure size in inches (width, height).
        dpi: Resolution for saved images.
        style: Matplotlib style name.
        color_palette: Chart color palette.
        output_format: Image format (png, svg, pdf).
    """

    figsize: Tuple[int, int] = (10, 6)
    dpi: int = 150
    style: str = "seaborn-v0_8-darkgrid"
    color_palette: List[str] = None
    output_format: str = "png"

    def __post_init__(self):
        if self.color_palette is None:
            self.color_palette = [
                "#2196F3", "#4CAF50", "#FF9800", "#F44336",
                "#9C27B0", "#00BCD4", "#FFEB3B", "#795548",
            ]


class BenchmarkVisualizer:
    """Generates visualization charts for CTF benchmark results - rnd_project_part2.

    Charts organized by the 3 evaluation categories:
    1. 效率与资源: Completion bar, time distribution, tool accuracy bar, token economy bar
    2. 规划与智能: First attempt pie, hallucination bar, attack path histogram, error recovery bar
    3. 能力覆盖: Vuln type radar, category breakdown, difficulty breakdown, coverage bar
    """

    # Metric category colors
    COLORS_EFFICIENCY = "#2196F3"
    COLORS_INTELLIGENCE = "#4CAF50"
    COLORS_COVERAGE = "#FF9800"

    def __init__(self, config: Optional[ChartConfig] = None):
        """Initialize visualizer.

        Args:
            config: Chart configuration.
        """
        if not HAS_MATPLOTLIB:
            raise ImportError(
                "matplotlib is required for visualization. "
                "Install with: pip install matplotlib"
            )
        self.config = config or ChartConfig()
        try:
            plt.style.use(self.config.style)
        except Exception:
            pass  # Style may not be available

    def generate_all_charts(
        self,
        sessions: List[ParsedSession],
        metrics: BenchmarkMetrics,
        output_dir: str = "./charts",
        prefix: str = "benchmark",
    ) -> Dict[str, str]:
        """Generate all available charts for the 9-metric system.

        Args:
            sessions: Parsed session data.
            metrics: Calculated metrics.
            output_dir: Output directory.
            prefix: File prefix.

        Returns:
            Dictionary mapping chart names to file paths.
        """
        os.makedirs(output_dir, exist_ok=True)
        charts = {}

        # ==== 效率与资源 Charts ====
        if metrics.efficiency:
            # Chart 1: Task completion rate bar
            path = os.path.join(output_dir, f"{prefix}_efficiency_completion.{self.config.output_format}")
            self.chart_efficiency_overview(metrics.efficiency, path)
            charts["efficiency_overview"] = path

        # Chart 2: Solve time distribution
        path = os.path.join(output_dir, f"{prefix}_efficiency_time.{self.config.output_format}")
        self.chart_time_distribution(sessions, path, title="解题时间分布 (Solve Time Distribution)")
        charts["efficiency_time"] = path

        # Chart 3: Tool call accuracy bar
        if metrics.efficiency:
            path = os.path.join(output_dir, f"{prefix}_efficiency_tool_accuracy.{self.config.output_format}")
            self.chart_tool_accuracy(metrics.efficiency, path)
            charts["efficiency_tool_accuracy"] = path

        # Chart 4: Token economy bar
        if metrics.efficiency:
            path = os.path.join(output_dir, f"{prefix}_efficiency_token.{self.config.output_format}")
            self.chart_token_economy(metrics.efficiency, path)
            charts["efficiency_token"] = path

        # ==== 规划与智能 Charts ====
        if metrics.intelligence:
            # Chart 5: Intelligence overview bar
            path = os.path.join(output_dir, f"{prefix}_intelligence_overview.{self.config.output_format}")
            self.chart_intelligence_overview(metrics.intelligence, path)
            charts["intelligence_overview"] = path

        # Chart 6: First attempt success pie
        if metrics.intelligence:
            path = os.path.join(output_dir, f"{prefix}_intelligence_first_attempt.{self.config.output_format}")
            self.chart_first_attempt_pie(sessions, path)
            charts["intelligence_first_attempt"] = path

        # Chart 7: Hallucination rate bar
        if metrics.intelligence:
            path = os.path.join(output_dir, f"{prefix}_intelligence_hallucination.{self.config.output_format}")
            self.chart_hallucination_rate(metrics.intelligence, path)
            charts["intelligence_hallucination"] = path

        # Chart 8: Attack path quality histogram
        path = os.path.join(output_dir, f"{prefix}_intelligence_attack_path.{self.config.output_format}")
        self.chart_attack_path_quality(sessions, path)
        charts["intelligence_attack_path"] = path

        # Chart 9: Error recovery rate
        if metrics.intelligence:
            path = os.path.join(output_dir, f"{prefix}_intelligence_error_recovery.{self.config.output_format}")
            self.chart_error_recovery(metrics.intelligence, path)
            charts["intelligence_error_recovery"] = path

        # ==== 能力覆盖 Charts ====
        if metrics.coverage:
            # Chart 10: Coverage overview
            path = os.path.join(output_dir, f"{prefix}_coverage_overview.{self.config.output_format}")
            self.chart_coverage_overview(metrics.coverage, path)
            charts["coverage_overview"] = path

        # Chart 11: Category success breakdown
        if metrics.coverage.category_breakdown:
            path = os.path.join(output_dir, f"{prefix}_coverage_category.{self.config.output_format}")
            self.chart_category_success(metrics.coverage.category_breakdown, path,
                                        title="各类别解题成功率 (Success Rate by Category)")
            charts["coverage_category"] = path

        # Chart 12: Difficulty breakdown
        if metrics.coverage.difficulty_breakdown:
            path = os.path.join(output_dir, f"{prefix}_coverage_difficulty.{self.config.output_format}")
            self.chart_difficulty_success(metrics.coverage.difficulty_breakdown, path,
                                          title="各难度解题成功率 (Success Rate by Difficulty)")
            charts["coverage_difficulty"] = path

        # Chart 13: 9-metric radar chart
        path = os.path.join(output_dir, f"{prefix}_9metric_radar.{self.config.output_format}")
        self.chart_9metric_radar(metrics, path)
        charts["9metric_radar"] = path

        # Chart 14: Tool calls distribution
        path = os.path.join(output_dir, f"{prefix}_tool_calls.{self.config.output_format}")
        self.chart_tool_calls_distribution(sessions, path)
        charts["tool_calls"] = path

        # Chart 15: Metrics overview bar
        path = os.path.join(output_dir, f"{prefix}_overview.{self.config.output_format}")
        self.chart_overview(metrics, path)
        charts["overview"] = path

        return charts

    # ============ 效率与资源 Charts ============

    def chart_efficiency_overview(
        self,
        efficiency: EfficiencyMetrics,
        save_path: str,
    ) -> None:
        """Efficiency overview bar chart showing all 4 metrics.

        Args:
            efficiency: Efficiency metrics.
            save_path: Output file path.
        """
        fig, axes = plt.subplots(1, 2, figsize=(16, 6))

        # Subplot 1: Completion rate + Tool accuracy
        ax1 = axes[0]
        labels1 = ["任务完成率\n(Completion Rate)", "工具调用准确率\n(Tool Accuracy)"]
        values1 = [efficiency.task_completion_rate, efficiency.tool_call_accuracy]
        colors1 = ["#2196F3", "#1976D2"]
        bars1 = ax1.bar(labels1, values1, color=colors1, edgecolor="white", linewidth=0.8)
        ax1.set_ylabel("Rate (%)")
        ax1.set_title("效率指标 (Efficiency Rates)")
        ax1.set_ylim(0, 105)
        for bar, val in zip(bars1, values1):
            ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
                     f"{val:.1f}%", ha="center", va="bottom", fontsize=11)

        # Subplot 2: Solve time + Token economy
        ax2 = axes[1]
        labels2 = ["平均解题时间 (s)\n(Avg Solve Time)", "Token总消耗\n(Total Tokens)"]
        values2 = [efficiency.avg_solve_time_seconds, efficiency.token_economy_total]
        colors2 = ["#4CAF50", "#FF9800"]
        bars2 = ax2.bar(labels2, values2, color=colors2, edgecolor="white", linewidth=0.8)
        ax2.set_title("资源消耗 (Resource Consumption)")
        for bar, val in zip(bars2, values2):
            if val >= 1000:
                text = f"{val:,}"
            else:
                text = f"{val:.0f}"
            ax2.text(bar.get_x() + bar.get_width() / 2,
                     bar.get_height() + max(values2) * 0.01,
                     text, ha="center", va="bottom", fontsize=10)

        plt.tight_layout()
        fig.savefig(save_path, dpi=self.config.dpi)
        plt.close(fig)

    def chart_tool_accuracy(
        self,
        efficiency: EfficiencyMetrics,
        save_path: str,
    ) -> None:
        """Tool accuracy gauge-style chart.

        Args:
            efficiency: Efficiency metrics.
            save_path: Output file path.
        """
        fig, ax = plt.subplots(figsize=(8, 5))
        accuracy = efficiency.tool_call_accuracy

        # Draw as a horizontal bar
        ax.barh(["工具调用准确率"], [accuracy], color="#2196F3", edgecolor="white", linewidth=0.8)
        ax.axvline(x=80, color="#4CAF50", linestyle="--", linewidth=1.5, label="合格线 (80%)")
        ax.axvline(x=95, color="#FF9800", linestyle="--", linewidth=1.5, label="优秀线 (95%)")
        ax.set_xlim(0, 105)
        ax.set_xlabel("Accuracy (%)")
        ax.set_title("工具调用准确率 (Tool Call Accuracy)")
        ax.legend(loc="lower right")
        ax.text(accuracy + 1, 0, f"{accuracy:.1f}%", va="center", fontsize=12, fontweight="bold")

        plt.tight_layout()
        fig.savefig(save_path, dpi=self.config.dpi)
        plt.close(fig)

    def chart_token_economy(
        self,
        efficiency: EfficiencyMetrics,
        save_path: str,
    ) -> None:
        """Token economy stacked bar chart (input vs output).

        Args:
            efficiency: Efficiency metrics.
            save_path: Output file path.
        """
        fig, ax = plt.subplots(figsize=(10, 5))

        categories = ["Token 经济性"]
        input_vals = [efficiency.token_economy_input]
        output_vals = [efficiency.token_economy_output]

        bar1 = ax.bar(categories, input_vals, color="#2196F3", edgecolor="white",
                      linewidth=0.8, label="输入Token (Input)")
        bar2 = ax.bar(categories, output_vals, bottom=input_vals, color="#4CAF50",
                      edgecolor="white", linewidth=0.8, label="输出Token (Output)")

        total = efficiency.token_economy_total
        ax.text(0, total + total * 0.02, f"总计: {total:,}", ha="center",
                fontsize=12, fontweight="bold")

        ax.set_ylabel("Token Count")
        ax.set_title("Token经济性分析 (Token Economy Analysis)")
        ax.legend()

        plt.tight_layout()
        fig.savefig(save_path, dpi=self.config.dpi)
        plt.close(fig)

    # ============ 规划与智能 Charts ============

    def chart_intelligence_overview(
        self,
        intelligence: IntelligenceMetrics,
        save_path: str,
    ) -> None:
        """Intelligence metrics overview bar chart.

        Args:
            intelligence: Intelligence metrics.
            save_path: Output file path.
        """
        fig, axes = plt.subplots(1, 2, figsize=(16, 6))

        # Subplot 1: First attempt + Error recovery (positive metrics)
        ax1 = axes[0]
        labels1 = ["首次尝试成功率\n(First Attempt Success)", "错误恢复率\n(Error Recovery)"]
        values1 = [intelligence.first_attempt_success_rate, intelligence.error_recovery_rate]
        colors1 = ["#4CAF50", "#00BCD4"]
        bars1 = ax1.bar(labels1, values1, color=colors1, edgecolor="white", linewidth=0.8)
        ax1.set_ylabel("Rate (%)")
        ax1.set_title("规划能力 (Planning Capability)")
        ax1.set_ylim(0, 105)
        for bar, val in zip(bars1, values1):
            ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
                     f"{val:.1f}%", ha="center", va="bottom", fontsize=11)

        # Subplot 2: Hallucination rate + Attack path quality (lower is better)
        ax2 = axes[1]
        labels2 = ["幻觉率\n(Hallucination Rate)", "攻击路径步数\n(Attack Path Steps)"]
        values2 = [intelligence.hallucination_rate, intelligence.attack_path_quality]
        colors2 = ["#F44336", "#FF9800"]
        bars2 = ax2.bar(labels2, values2, color=colors2, edgecolor="white", linewidth=0.8)
        ax2.set_title("风险评估 (Risk Assessment) ↓ Lower is Better")
        for bar, val in zip(bars2, values2):
            ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(values2) * 0.01,
                     f"{val:.1f}", ha="center", va="bottom", fontsize=11)

        plt.tight_layout()
        fig.savefig(save_path, dpi=self.config.dpi)
        plt.close(fig)

    def chart_first_attempt_pie(
        self,
        sessions: List[ParsedSession],
        save_path: str,
    ) -> None:
        """Pie chart showing first attempt distribution.

        Args:
            sessions: Parsed sessions.
            save_path: Output file path.
        """
        sessions_with_data = [s for s in sessions if s.first_attempt_success is not None]
        if not sessions_with_data:
            # Create empty chart
            fig, ax = plt.subplots(figsize=(8, 8))
            ax.text(0.5, 0.5, "No first-attempt data", ha="center", va="center")
            fig.savefig(save_path, dpi=self.config.dpi)
            plt.close(fig)
            return

        first_success = sum(1 for s in sessions_with_data if s.first_attempt_success)
        first_fail = sum(1 for s in sessions_with_data if not s.first_attempt_success)
        no_data = len(sessions) - len(sessions_with_data)

        labels = []
        sizes = []
        colors = []
        if first_success:
            labels.append(f"首次正确 ({first_success})")
            sizes.append(first_success)
            colors.append("#4CAF50")
        if first_fail:
            labels.append(f"首次失败 ({first_fail})")
            sizes.append(first_fail)
            colors.append("#F44336")
        if no_data:
            labels.append(f"无数据 ({no_data})")
            sizes.append(no_data)
            colors.append("#BDBDBD")

        fig, ax = plt.subplots(figsize=(8, 8))
        ax.pie(sizes, labels=labels, colors=colors, autopct="%1.1f%%",
               startangle=90, pctdistance=0.85)
        ax.set_title("首次尝试成功率分布 (First Attempt Distribution)")

        plt.tight_layout()
        fig.savefig(save_path, dpi=self.config.dpi)
        plt.close(fig)

    def chart_hallucination_rate(
        self,
        intelligence: IntelligenceMetrics,
        save_path: str,
    ) -> None:
        """Hallucination rate gauge bar.

        Args:
            intelligence: Intelligence metrics.
            save_path: Output file path.
        """
        fig, ax = plt.subplots(figsize=(8, 5))
        rate = intelligence.hallucination_rate

        # Draw as a horizontal bar
        bar = ax.barh(["幻觉率"], [rate], color="#F44336" if rate > 20 else "#FF9800" if rate > 10 else "#4CAF50",
                      edgecolor="white", linewidth=0.8)
        ax.axvline(x=10, color="#FF9800", linestyle="--", linewidth=1.5, label="预警线 (10%)")
        ax.axvline(x=20, color="#F44336", linestyle="--", linewidth=1.5, label="危险线 (20%)")
        ax.set_xlim(0, max(rate * 1.5, 30))
        ax.set_xlabel("Rate (%)")
        ax.set_title("幻觉率 (Hallucination Rate) ↓ Lower is Better")
        ax.legend(loc="lower right")
        ax.text(rate + 0.5, 0, f"{rate:.1f}%", va="center", fontsize=12, fontweight="bold")

        plt.tight_layout()
        fig.savefig(save_path, dpi=self.config.dpi)
        plt.close(fig)

    def chart_attack_path_quality(
        self,
        sessions: List[ParsedSession],
        save_path: str,
    ) -> None:
        """Histogram of attack path steps per solve.

        Args:
            sessions: Parsed sessions.
            save_path: Output file path.
        """
        fig, ax = plt.subplots(figsize=self.config.figsize)

        path_steps = [s.attack_path_steps for s in sessions if s.attack_path_steps > 0]
        if not path_steps:
            plt.close(fig)
            return

        ax.hist(path_steps, bins=min(20, len(set(path_steps))), color="#4CAF50",
                edgecolor="white", linewidth=0.8, alpha=0.8)
        avg_steps = sum(path_steps) / len(path_steps)
        ax.axvline(avg_steps, color="#F44336", linestyle="--", linewidth=2,
                   label=f"Avg: {avg_steps:.1f} steps (fewer = better)")
        ax.set_xlabel("Attack Path Steps")
        ax.set_ylabel("Frequency")
        ax.set_title("攻击路径质量分布 (Attack Path Quality Distribution)")
        ax.legend()

        plt.tight_layout()
        fig.savefig(save_path, dpi=self.config.dpi)
        plt.close(fig)

    def chart_error_recovery(
        self,
        intelligence: IntelligenceMetrics,
        save_path: str,
    ) -> None:
        """Error recovery rate bar.

        Args:
            intelligence: Intelligence metrics.
            save_path: Output file path.
        """
        fig, ax = plt.subplots(figsize=(8, 5))
        rate = intelligence.error_recovery_rate

        bar = ax.barh(["错误恢复率"], [rate], color="#00BCD4", edgecolor="white", linewidth=0.8)
        ax.axvline(x=50, color="#FF9800", linestyle="--", linewidth=1.5, label="合格线 (50%)")
        ax.axvline(x=80, color="#4CAF50", linestyle="--", linewidth=1.5, label="优秀线 (80%)")
        ax.set_xlim(0, 105)
        ax.set_xlabel("Rate (%)")
        ax.set_title("错误恢复率 (Error Recovery Rate)")
        ax.legend(loc="lower right")
        ax.text(rate + 1, 0, f"{rate:.1f}%", va="center", fontsize=12, fontweight="bold")

        plt.tight_layout()
        fig.savefig(save_path, dpi=self.config.dpi)
        plt.close(fig)

    # ============ 能力覆盖 Charts ============

    def chart_coverage_overview(
        self,
        coverage: CoverageMetrics,
        save_path: str,
    ) -> None:
        """Coverage overview bar chart.

        Args:
            coverage: Coverage metrics.
            save_path: Output file path.
        """
        fig, axes = plt.subplots(1, 2, figsize=(16, 6))

        # Subplot 1: Challenge type coverage vs difficulty penetration
        ax1 = axes[0]
        labels1 = ["题型覆盖度\n(Type Coverage)", "难题穿透率\n(Difficulty Penetration)"]
        values1 = [coverage.challenge_type_coverage, coverage.difficulty_penetration * 100]
        colors1 = ["#FF9800", "#F44336"]
        bars1 = ax1.bar(labels1, values1, color=colors1, edgecolor="white", linewidth=0.8)
        ax1.set_ylabel("Rate (%)")
        ax1.set_title("能力覆盖指标 (Coverage Metrics)")
        ax1.set_ylim(0, 105)
        for bar, val in zip(bars1, values1):
            ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
                     f"{val:.1f}%", ha="center", va="bottom", fontsize=11)

        # Subplot 2: Vuln types mastered count
        ax2 = axes[1]
        vuln_types = coverage.vuln_types_mastered
        mastered_count = len(vuln_types)
        total_count = coverage.total_vuln_types

        # Draw a simple count bar
        ax2.bar(["已掌握类型\n(Mastered)", "总考察类型\n(Total)"],
                [mastered_count, total_count],
                color=["#4CAF50", "#9E9E9E"], edgecolor="white", linewidth=0.8)
        ax2.set_title(f"漏洞类型掌握情况 ({mastered_count}/{total_count})")

        plt.tight_layout()
        fig.savefig(save_path, dpi=self.config.dpi)
        plt.close(fig)

    def chart_9metric_radar(
        self,
        metrics: BenchmarkMetrics,
        save_path: str,
    ) -> None:
        """9-metric radar chart spanning all 3 categories.

        Args:
            metrics: Benchmark metrics.
            save_path: Output file path.
        """
        import numpy as np

        categories = [
            "完成率\n(Efficiency)",
            "解题时间\n↑ Fast",
            "工具准确\n(Efficiency)",
            "Token经济\n↓ Low",
            "首次成功\n(Planning)",
            "错误恢复\n(Planning)",
            "*攻击路径\n↓ Short",
            "*幻觉率\n↓ Low",
            "题型覆盖\n(Coverage)",
        ]
        N = len(categories)

        # Build values list (normalize to 0-1 range)
        values = [
            metrics.efficiency.task_completion_rate / 100 if metrics.efficiency else 0,
            1.0 - min(metrics.efficiency.avg_solve_time_seconds / 7200, 1.0) if metrics.efficiency else 0,  # Invert time
            metrics.efficiency.tool_call_accuracy / 100 if metrics.efficiency else 0,
            1.0 - min(metrics.efficiency.token_economy_total / 500000, 1.0) if metrics.efficiency else 0,  # Invert tokens
            metrics.intelligence.first_attempt_success_rate / 100 if metrics.intelligence else 0,
            metrics.intelligence.error_recovery_rate / 100 if metrics.intelligence else 0,
            1.0 - min(metrics.intelligence.attack_path_quality / 30, 1.0) if metrics.intelligence else 0,  # Invert steps
            1.0 - min(metrics.intelligence.hallucination_rate / 50, 1.0) if metrics.intelligence else 0,  # Invert rate
            metrics.coverage.challenge_type_coverage / 100 if metrics.coverage else 0,
        ]

        angles = [n / float(N) * 2 * np.pi for n in range(N)]
        values += values[:1]
        angles += angles[:1]

        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(polar=True))

        ax.plot(angles, values, "o-", linewidth=2, color="#2196F3", label="AI Agent")
        ax.fill(angles, values, alpha=0.25, color="#2196F3")

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, size=9)
        ax.set_ylim(0, 1.0)
        ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
        ax.set_yticklabels(["20%", "40%", "60%", "80%", "100%"], size=8)
        ax.set_title("九维能力雷达图 (9-Metric Capability Radar)\n* 指标已反向归一化", pad=20, size=14)
        ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1))

        plt.tight_layout()
        fig.savefig(save_path, dpi=self.config.dpi)
        plt.close(fig)

    # ============ Legacy Charts (maintained for backward compatibility) ============

    def chart_category_success(
        self,
        category_stats: Dict[str, float],
        save_path: str,
        title: str = "CTF Challenge Success Rate by Category",
    ) -> None:
        """Bar chart showing success rate per category.

        Args:
            category_stats: Category to success rate mapping.
            save_path: Output file path.
            title: Chart title.
        """
        fig, ax = plt.subplots(figsize=self.config.figsize)

        categories = list(category_stats.keys())
        values = [v * 100 for v in category_stats.values()]
        colors = self.config.color_palette[:len(categories)]

        bars = ax.bar(categories, values, color=colors, edgecolor="white", linewidth=0.8)
        ax.set_ylabel("Success Rate (%)")
        ax.set_title(title)
        ax.set_ylim(0, max(values) * 1.2 if values else 100)

        for bar, val in zip(bars, values):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 1,
                f"{val:.1f}%",
                ha="center", va="bottom",
            )

        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        fig.savefig(save_path, dpi=self.config.dpi)
        plt.close(fig)

    def chart_difficulty_success(
        self,
        difficulty_stats: Dict[str, float],
        save_path: str,
        title: str = "CTF Challenge Success Rate by Difficulty",
    ) -> None:
        """Bar chart showing success rate per difficulty level.

        Args:
            difficulty_stats: Difficulty to success rate mapping.
            save_path: Output file path.
            title: Chart title.
        """
        fig, ax = plt.subplots(figsize=self.config.figsize)

        diff_order = {"easy": 0, "medium": 1, "hard": 2, "expert": 3, "advanced": 3}
        sorted_diffs = sorted(
            difficulty_stats.items(),
            key=lambda x: diff_order.get(x[0].lower(), 99),
        )

        labels = [d[0].title() for d in sorted_diffs]
        values = [v[1] * 100 for v in sorted_diffs]
        colors = ["#4CAF50", "#FF9800", "#F44336", "#9C27B0", "#9C27B0"]

        bars = ax.bar(labels, values, color=colors[:len(labels)], edgecolor="white", linewidth=0.8)
        ax.set_ylabel("Success Rate (%)")
        ax.set_title(title)
        ax.set_ylim(0, max(values) * 1.2 if values else 100)

        for bar, val in zip(bars, values):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 1,
                f"{val:.1f}%",
                ha="center", va="bottom",
            )

        plt.tight_layout()
        fig.savefig(save_path, dpi=self.config.dpi)
        plt.close(fig)

    def chart_tool_calls_distribution(
        self,
        sessions: List[ParsedSession],
        save_path: str,
    ) -> None:
        """Histogram showing tool calls distribution.

        Args:
            sessions: Parsed sessions.
            save_path: Output file path.
        """
        fig, ax = plt.subplots(figsize=self.config.figsize)

        tool_calls = [s.tool_calls for s in sessions if s.tool_calls > 0]
        if not tool_calls:
            plt.close(fig)
            return

        ax.hist(tool_calls, bins=min(20, len(set(tool_calls))), color="#2196F3",
                edgecolor="white", linewidth=0.8, alpha=0.8)
        ax.axvline(sum(tool_calls) / len(tool_calls), color="#F44336",
                   linestyle="--", linewidth=2, label=f"Avg: {sum(tool_calls) / len(tool_calls):.1f}")
        ax.set_xlabel("Tool Calls per Session")
        ax.set_ylabel("Frequency")
        ax.set_title("Distribution of Tool Calls per CTF Challenge")
        ax.legend()

        plt.tight_layout()
        fig.savefig(save_path, dpi=self.config.dpi)
        plt.close(fig)

    def chart_time_distribution(
        self,
        sessions: List[ParsedSession],
        save_path: str,
        title: str = "Distribution of Solve Times per CTF Challenge",
    ) -> None:
        """Histogram showing solve time distribution.

        Args:
            sessions: Parsed sessions.
            save_path: Output file path.
            title: Chart title.
        """
        fig, ax = plt.subplots(figsize=self.config.figsize)

        times = [s.duration_seconds / 60 for s in sessions if s.duration_seconds > 0]
        if not times:
            plt.close(fig)
            return

        ax.hist(times, bins=min(20, len(set(times))), color="#4CAF50",
                edgecolor="white", linewidth=0.8, alpha=0.8)
        ax.axvline(sum(times) / len(times), color="#F44336",
                   linestyle="--", linewidth=2, label=f"Avg: {sum(times) / len(times):.1f} min")
        ax.set_xlabel("Time (minutes)")
        ax.set_ylabel("Frequency")
        ax.set_title(title)
        ax.legend()

        plt.tight_layout()
        fig.savefig(save_path, dpi=self.config.dpi)
        plt.close(fig)

    def chart_overview(
        self,
        metrics: BenchmarkMetrics,
        save_path: str,
    ) -> None:
        """Overview bar chart with key metrics.

        Args:
            metrics: Benchmark metrics.
            save_path: Output file path.
        """
        fig, ax = plt.subplots(figsize=self.config.figsize)

        metric_names = ["Accuracy", "Precision", "F1 Score", "Difficulty\nPenetration"]
        metric_values = [
            metrics.accuracy * 100,
            metrics.precision * 100,
            metrics.f1_score * 100,
            metrics.difficulty_penetration * 100,
        ]

        colors = ["#2196F3", "#4CAF50", "#FF9800", "#F44336"]
        bars = ax.bar(metric_names, metric_values, color=colors, edgecolor="white", linewidth=0.8)

        ax.set_ylabel("Score (%)")
        ax.set_title("CTF Benchmark Performance Overview")
        ax.set_ylim(0, 105)

        for bar, val in zip(bars, metric_values):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 1,
                f"{val:.1f}%",
                ha="center", va="bottom",
            )

        plt.tight_layout()
        fig.savefig(save_path, dpi=self.config.dpi)
        plt.close(fig)

    def chart_comparison(
        self,
        comparison_data: Dict[str, Dict[str, Any]],
        metric_key: str = "accuracy",
        title: str = "Benchmark Comparison",
        save_path: str = "",
    ) -> None:
        """Comparison bar chart between runs.

        Args:
            comparison_data: Comparison data from MetricsEngine.compare_runs.
            metric_key: Metric to compare.
            title: Chart title.
            save_path: Output file path.
        """
        fig, ax = plt.subplots(figsize=self.config.figsize)

        labels = list(comparison_data.get("labels", {}).keys())
        if not labels:
            plt.close(fig)
            return

        values = []
        for label in labels:
            run_metrics = comparison_data["labels"].get(label, {})
            val = run_metrics.get(metric_key, 0)
            if isinstance(val, (int, float)):
                values.append(val * 100 if metric_key in (
                    "accuracy", "precision", "f1_score", "difficulty_penetration"
                ) else val)

        x_pos = range(len(labels))
        bars = ax.bar(x_pos, values, color=self.config.color_palette[:len(labels)],
                      edgecolor="white", linewidth=0.8)

        ax.set_xticks(x_pos)
        ax.set_xticklabels(labels)
        ax.set_ylabel(f"{metric_key.replace('_', ' ').title()}")
        ax.set_title(title)

        for bar, val in zip(bars, values):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + max(values) * 0.01,
                f"{val:.2f}",
                ha="center", va="bottom",
            )

        plt.tight_layout()
        if save_path:
            fig.savefig(save_path, dpi=self.config.dpi)
        plt.close(fig)


def create_sample_charts(output_dir: str = "./charts") -> Dict[str, str]:
    """Create sample charts for demonstration.

    Args:
        output_dir: Output directory for charts.

    Returns:
        Dictionary of chart paths.
    """
    if not HAS_MATPLOTLIB:
        return {}

    # Create sample data with vuln types
    vuln_types = ["sqli", "xss", "csrf", "command_injection", "file_inclusion",
                  "buffer_overflow", "reverse_engineering", "forensics"]
    sessions = [
        ParsedSession(
            session_id=f"session_{i}",
            challenge_name=f"challenge_{i}",
            category=["web", "pwn", "crypto", "reverse", "misc"][i % 5],
            vuln_type=vuln_types[i % len(vuln_types)],
            difficulty=["easy", "medium", "hard"][i % 3],
            success=i % 3 != 0,
            duration_seconds=600 + i * 120,
            tool_calls=5 + i * 2,
            tool_calls_success=4 + i * 2,
            errors=1 if i % 3 == 0 else 0,
            error_recovery_count=1 if i % 3 == 0 else 0,
            input_tokens=1000 + i * 200,
            output_tokens=500 + i * 100,
            tokens_used=1500 + i * 300,
            first_attempt_success=(i % 2 == 0),
            hallucination_count=1 if i % 5 == 0 else 0,
            attack_path_steps=5 + i % 10,
        )
        for i in range(20)
    ]

    engine = MetricsEngine()
    metrics = engine.calculate_metrics(sessions)

    visualizer = BenchmarkVisualizer()
    return visualizer.generate_all_charts(sessions, metrics, output_dir, "sample")