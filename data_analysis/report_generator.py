"""Report generator for CTF benchmark analysis - rnd_project_part2.

Generates JSON, Markdown, and HTML reports using the 9-metric evaluation system:
  - 效率与资源 (Efficiency & Resources): 4 metrics
  - 规划与智能 (Planning & Intelligence): 4 metrics
  - 能力覆盖 (Capability Coverage): 1 metric + breakdowns
"""

import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

try:
    from jinja2 import Template
    HAS_JINJA2 = True
except ImportError:
    HAS_JINJA2 = False

from data_analysis.log_parser import ParsedSession, ParseSummary
from data_analysis.metrics_engine import (
    BenchmarkMetrics, EfficiencyMetrics, IntelligenceMetrics,
    CoverageMetrics, MetricsEngine,
)
from data_analysis.baseline import BaselineComparison, BaselineManager


@dataclass
class ReportConfig:
    """Configuration for report generation.

    Attributes:
        output_dir: Output directory for reports.
        include_charts: Whether to embed chart references.
        chart_dir: Directory containing chart images.
        title: Report title.
        subtitle: Report subtitle.
        author: Report author.
        include_session_details: Include per-session details.
        format: Report format (json, markdown, html, all).
    """

    output_dir: str = "./reports"
    include_charts: bool = True
    chart_dir: str = "./charts"
    title: str = "AI Agent CTF 能力量化评测报告"
    subtitle: str = "基于9维指标体系的CTF解题能力评估"
    author: str = "CAI Benchmark System"
    include_session_details: bool = True
    format: str = "all"


class ReportGenerator:
    """Generates evaluation reports from benchmark data.

    Supports output in:
    - JSON: Structured data for programmatic analysis
    - Markdown: Human-readable text report
    - HTML: Visual report with embedded tables (requires jinja2)

    All reports include the 9-metric 3-category breakdown.
    """

    HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        body { font-family: 'Segoe UI', -apple-system, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; background: #f5f5f5; color: #333; }
        h1 { color: #1a73e8; border-bottom: 3px solid #1a73e8; padding-bottom: 10px; }
        h2 { color: #2c3e50; margin-top: 30px; border-left: 4px solid #1a73e8; padding-left: 10px; }
        h3 { color: #555; margin-top: 20px; }
        .summary { background: #e8f0fe; padding: 15px; border-radius: 8px; margin: 15px 0; }
        table { width: 100%%; border-collapse: collapse; margin: 10px 0; background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        th, td { padding: 8px 12px; text-align: left; border: 1px solid #ddd; }
        th { background: #1a73e8; color: white; }
        tr:nth-child(even) { background: #f8f9fa; }
        .metric-good { color: #0d904f; font-weight: bold; }
        .metric-warn { color: #e37400; font-weight: bold; }
        .metric-bad { color: #d93025; font-weight: bold; }
        .category-header { background: #2c3e50 !important; color: white !important; font-size: 1.1em; }
        .chart-container { margin: 20px 0; text-align: center; }
        .chart-container img { max-width: 100%%; height: auto; border: 1px solid #ddd; border-radius: 4px; }
        .json-block { background: #263238; color: #aed581; padding: 15px; border-radius: 4px; overflow-x: auto; font-family: monospace; }
    </style>
</head>
<body>
    <h1>{{ title }}</h1>
    <p><strong>{{ subtitle }}</strong></p>
    <div class="summary">
        <p><strong>模型/配置:</strong> {{ model_name }}</p>
        <p><strong>生成时间:</strong> {{ generated_at }}</p>
        <p><strong>题目数量:</strong> {{ total_challenges }}</p>
        <p><strong>成功率:</strong> {{ "%.1f%%" | format(accuracy * 100) }}</p>
        <p><strong>总Flag数:</strong> {{ total_flags }}</p>
        <p><strong>预估API成本:</strong> ${{ "%.4f" | format(cost_usd) }}</p>
    </div>

    {% if efficiency %}
    <h2>效率与资源 (Efficiency & Resources)</h2>
    <table>
        <tr>
            <th>指标</th><th>值</th><th>公式</th>
        </tr>
        <tr>
            <td>任务完成率</td><td class="{{ 'metric-good' if efficiency.task_completion_rate >= 80 else 'metric-warn' if efficiency.task_completion_rate >= 50 else 'metric-bad' }}">{{ "%.1f%%" | format(efficiency.task_completion_rate) }}</td><td>(成功数 / 总尝试数) × 100%</td>
        </tr>
        <tr>
            <td>平均解题时间</td><td>{{ "%.0f" | format(efficiency.avg_solve_time_seconds) }}秒</td><td>Σ(完成时刻 - 开始时刻) / 成功数</td>
        </tr>
        <tr>
            <td>工具调用准确率</td><td>{{ "%.1f%%" | format(efficiency.tool_call_accuracy) }}</td><td>(成功次数 / 总次数) × 100%</td>
        </tr>
        <tr>
            <td>Token经济性</td><td>{{ "{:,}".format(efficiency.token_economy_total) }}</td><td>输入Token + 输出Token</td>
        </tr>
    </table>
    {% if charts.get('efficiency_overview') %}<div class="chart-container"><img src="{{ charts.efficiency_overview }}" alt="Efficiency Overview"></div>{% endif %}
    {% endif %}

    {% if intelligence %}
    <h2>规划与智能 (Planning & Intelligence)</h2>
    <table>
        <tr>
            <th>指标</th><th>值</th><th>公式</th>
        </tr>
        <tr>
            <td>首次尝试成功率</td><td>{{ "%.1f%%" | format(intelligence.first_attempt_success_rate) }}</td><td>(首次正确数 / 总解题数) × 100%</td>
        </tr>
        <tr>
            <td>幻觉率</td><td>{{ "%.1f%%" | format(intelligence.hallucination_rate) }}</td><td>(幻觉数 / 抽查样本数) × 100%</td>
        </tr>
        <tr>
            <td>攻击路径质量</td><td>{{ "%.1f" | format(intelligence.attack_path_quality) }} 步/题</td><td>avg steps per successful solve</td>
        </tr>
        <tr>
            <td>错误恢复率</td><td>{{ "%.1f%%" | format(intelligence.error_recovery_rate) }}</td><td>(恢复成功数 / 报错总数) × 100%</td>
        </tr>
    </table>
    {% if charts.get('intelligence_overview') %}<div class="chart-container"><img src="{{ charts.intelligence_overview }}" alt="Intelligence Overview"></div>{% endif %}
    {% endif %}

    {% if coverage %}
    <h2>能力覆盖 (Capability Coverage)</h2>
    <table>
        <tr>
            <th>指标</th><th>值</th><th>公式</th>
        </tr>
        <tr>
            <td>题型覆盖度</td><td>{{ "%.1f%%" | format(coverage.challenge_type_coverage) }} ({{ coverage.vuln_types_mastered | length }}/{{ coverage.total_vuln_types }})</td><td>(掌握类型数 / 总类型数) × 100%</td>
        </tr>
        <tr>
            <td>难题穿透率</td><td>{{ "%.1f%%" | format(coverage.difficulty_penetration * 100) }}</td><td>(高难度成功数 / 高难度总数) × 100%</td>
        </tr>
    </table>
    {% if charts.get('9metric_radar') %}<div class="chart-container"><img src="{{ charts['9metric_radar'] }}" alt="9-Metric Radar"></div>{% endif %}
    {% endif %}

    <h2>其他遗留指标 (Legacy Metrics)</h2>
    <table>
        <tr><th>指标</th><th>值</th></tr>
        <tr><td>Accuracy</td><td>{{ "%.2f%%" | format(accuracy * 100) }}</td></tr>
        <tr><td>Precision</td><td>{{ "%.2f%%" | format(precision * 100) }}</td></tr>
        <tr><td>F1 Score</td><td>{{ "%.2f%%" | format(f1_score * 100) }}</td></tr>
        <tr><td>Error Rate</td><td>{{ "%.2f" | format(error_rate) }}</td></tr>
        <tr><td>Tool Efficiency</td><td>{{ "%.4f" | format(tool_efficiency) }}</td></tr>
    </table>

    {% if sessions %}
    <h2>解题详情</h2>
    <table>
        <tr><th>题目</th><th>分类</th><th>难度</th><th>结果</th><th>耗时(s)</th><th>工具调用</th><th>Token</th></tr>
        {% for s in sessions %}
        <tr>
            <td>{{ s.challenge_name }}</td>
            <td>{{ s.category }}</td>
            <td>{{ s.difficulty }}</td>
            <td class="{{ 'metric-good' if s.success else 'metric-bad' }}">{{ '✓ 成功' if s.success else '✗ 失败' }}</td>
            <td>{{ s.duration_seconds }}</td>
            <td>{{ s.tool_calls }}</td>
            <td>{{ s.tokens_used }}</td>
        </tr>
        {% endfor %}
    </table>
    {% endif %}

    <p style="text-align:center; color:#999; margin-top:40px;">
        Generated by CAI Benchmark Framework &mdash; {{ generated_at }}
    </p>
</body>
</html>"""

    def __init__(self, config: Optional[ReportConfig] = None):
        """Initialize report generator.

        Args:
            config: Report configuration.
        """
        self.config = config or ReportConfig()

    def generate_report(
        self,
        sessions: List[ParsedSession],
        metrics: BenchmarkMetrics,
        model_name: str = "unknown",
        baseline_comparison: Optional[BaselineComparison] = None,
        chart_files: Optional[Dict[str, str]] = None,
        parse_summary: Optional[ParseSummary] = None,
    ) -> Dict[str, str]:
        """Generate reports in all configured formats.

        Args:
            sessions: Parsed sessions.
            metrics: Calculated metrics.
            model_name: Model name/identifier.
            baseline_comparison: Baseline comparison results.
            chart_files: Generated chart file paths.
            parse_summary: Parsing summary.

        Returns:
            Dictionary of format -> file path.
        """
        os.makedirs(self.config.output_dir, exist_ok=True)
        generated: Dict[str, str] = {}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        fmt = self.config.format.lower()
        if fmt in ("json", "all"):
            path = os.path.join(self.config.output_dir, f"report_{timestamp}.json")
            self._generate_json(sessions, metrics, model_name, baseline_comparison, parse_summary, path)
            generated["json"] = path

        if fmt in ("markdown", "all"):
            path = os.path.join(self.config.output_dir, f"report_{timestamp}.md")
            self._generate_markdown(sessions, metrics, model_name, baseline_comparison, chart_files, parse_summary, path)
            generated["markdown"] = path

        if fmt in ("html", "all") and HAS_JINJA2:
            path = os.path.join(self.config.output_dir, f"report_{timestamp}.html")
            self._generate_html(sessions, metrics, model_name, chart_files, path)
            generated["html"] = path
        elif fmt in ("html", "all") and not HAS_JINJA2:
            # Fallback: write HTML with simple string formatting
            path = os.path.join(self.config.output_dir, f"report_{timestamp}.html")
            self._generate_html_simple(sessions, metrics, model_name, chart_files, path)
            generated["html"] = path

        return generated

    def _generate_json(
        self,
        sessions: List[ParsedSession],
        metrics: BenchmarkMetrics,
        model_name: str,
        baseline_comparison: Optional[BaselineComparison],
        parse_summary: Optional[ParseSummary],
        filepath: str,
    ) -> str:
        """Generate JSON report.

        Args:
            sessions: Parsed sessions.
            metrics: Calculated metrics.
            model_name: Model name.
            baseline_comparison: Baseline comparison results.
            parse_summary: Parsing summary.
            filepath: Output file path.

        Returns:
            Output file path.
        """
        report: Dict[str, Any] = {
            "meta": {
                "title": self.config.title,
                "subtitle": self.config.subtitle,
                "model_name": model_name,
                "generated_at": datetime.now().isoformat(),
                "framework_version": "rnd_project_part2",
            },
            "summary": {
                "total_sessions": len(sessions),
                "successful": sum(1 for s in sessions if s.success),
                "failed": sum(1 for s in sessions if not s.success),
                "total_flags": metrics.total_flags,
                "cost_estimate_usd": metrics.cost_estimate_usd,
            },
            "metrics": metrics.to_dict(),
            "9_metric_table": metrics.get_9_metrics_table(),
            "sessions": [s.to_dict() for s in sessions] if self.config.include_session_details else [],
        }

        if baseline_comparison:
            report["baseline_comparison"] = {
                "run_name": baseline_comparison.run_name,
                "summary": baseline_comparison.summary,
                "comparisons": baseline_comparison.comparisons,
            }

        if parse_summary:
            report["parse_summary"] = parse_summary.to_dict()

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        return filepath

    def _generate_markdown(
        self,
        sessions: List[ParsedSession],
        metrics: BenchmarkMetrics,
        model_name: str,
        baseline_comparison: Optional[BaselineComparison],
        chart_files: Optional[Dict[str, str]],
        parse_summary: Optional[ParseSummary],
        filepath: str,
    ) -> str:
        """Generate Markdown report with 9-metric structure.

        Args:
            sessions: Parsed sessions.
            metrics: Calculated metrics.
            model_name: Model name.
            baseline_comparison: Baseline comparison results.
            chart_files: Chart file paths.
            parse_summary: Parsing summary.
            filepath: Output file path.

        Returns:
            Output file path.
        """
        lines = []

        # Title
        lines.append(f"# {self.config.title}")
        lines.append(f"**{self.config.subtitle}**\n")
        lines.append(f"- **模型/配置:** `{model_name}`")
        lines.append(f"- **报告生成时间:** {datetime.now().isoformat()}")
        lines.append(f"- **题目总数:** {len(sessions)}")
        lines.append(f"- **Flag获取数:** {metrics.total_flags}")
        lines.append(f"- **预估API成本:** ${metrics.cost_estimate_usd:.4f}\n")

        # ---- 9-Metric Summary Table ----
        lines.append("## 九维指标总览 (9-Metric Summary)\n")
        lines.append("| 类别 | 指标 | 值 | 公式 |")
        lines.append("|------|------|----|------|")

        for row in metrics.get_9_metrics_table():
            lines.append(f"| {row['category']} | {row['metric']} | {row['value']} | {row['formula']} |")
        lines.append("")

        # ---- 效率与资源 ----
        lines.append("## 效率与资源 (Efficiency & Resources)\n")
        if metrics.efficiency:
            eff = metrics.efficiency
            lines.append(f"- **任务完成率:** {eff.task_completion_rate:.1f}% ")
            lines.append(f"  (公式: (成功数 / 总尝试数) × 100%)")
            lines.append(f"- **平均解题时间:** {eff.avg_solve_time_seconds:.0f}秒 ({eff.avg_solve_time_seconds / 60:.1f}分钟)")
            lines.append(f"  (公式: Σ(完成时刻 - 开始时刻) / 成功数)")
            lines.append(f"- **工具调用准确率:** {eff.tool_call_accuracy:.1f}%")
            lines.append(f"  (公式: (成功次数 / 总次数) × 100%)")
            lines.append(f"- **Token经济性:** {eff.token_economy_total:,} (输入: {eff.token_economy_input:,}, 输出: {eff.token_economy_output:,})")
            lines.append(f"  (公式: 输入Token + 输出Token)\n")

        # ---- 规划与智能 ----
        lines.append("## 规划与智能 (Planning & Intelligence)\n")
        if metrics.intelligence:
            intel = metrics.intelligence
            lines.append(f"- **首次尝试成功率:** {intel.first_attempt_success_rate:.1f}%")
            lines.append(f"  (公式: (首次正确数 / 总解题数) × 100%)")
            lines.append(f"- **幻觉率:** {intel.hallucination_rate:.1f}%")
            lines.append(f"  (公式: (幻觉数 / 抽查样本数) × 100%)")
            lines.append(f"- **攻击路径质量:** {intel.attack_path_quality:.1f} steps/solve (lower = better)")
            lines.append(f"  (公式: avg steps per successful solve)")
            lines.append(f"- **错误恢复率:** {intel.error_recovery_rate:.1f}%")
            lines.append(f"  (公式: (恢复成功数 / 报错总数) × 100%)\n")

        # ---- 能力覆盖 ----
        lines.append("## 能力覆盖 (Capability Coverage)\n")
        if metrics.coverage:
            cov = metrics.coverage
            lines.append(f"- **题型覆盖度:** {cov.challenge_type_coverage:.1f}% ({len(cov.vuln_types_mastered)}/{cov.total_vuln_types})")
            lines.append(f"  (公式: (掌握的漏洞类型数 / 总考察类型数) × 100%)")
            if cov.vuln_types_mastered:
                lines.append(f"  - 已掌握类型: {', '.join(cov.vuln_types_mastered)}")
            if cov.category_breakdown:
                lines.append(f"- **分类成功率:** {json.dumps(cov.category_breakdown, ensure_ascii=False)}")
            if cov.difficulty_breakdown:
                lines.append(f"- **难度成功率:** {json.dumps(cov.difficulty_breakdown, ensure_ascii=False)}")
            lines.append(f"- **难题穿透率:** {cov.difficulty_penetration * 100:.1f}%")
            lines.append(f"  (公式: (高难度成功数 / 高难度总数) × 100%)\n")

        # ---- Legacy Metrics ----
        lines.append("## 遗留指标 (Legacy Metrics)\n")
        lines.append(f"- **Accuracy:** {metrics.accuracy:.2%}")
        lines.append(f"- **Precision:** {metrics.precision:.2%}")
        lines.append(f"- **F1 Score:** {metrics.f1_score:.2%}")
        lines.append(f"- **Avg Tool Calls:** {metrics.avg_tool_calls:.1f}")
        lines.append(f"- **Avg Tokens:** {metrics.avg_tokens:.0f}")
        lines.append(f"- **Error Rate:** {metrics.error_rate:.2f}")
        lines.append(f"- **Tool Efficiency:** {metrics.tool_efficiency:.4f}\n")

        # ---- Baseline Comparison ----
        if baseline_comparison and baseline_comparison.comparisons:
            lines.append("## 基线对比 (Baseline Comparison)\n")
            for name, comp in baseline_comparison.comparisons.items():
                desc = comp.get("description", name)
                lines.append(f"### {name}\n")
                lines.append(f"> {desc}\n")
                diffs = comp.get("differences", {})
                eff_diff = diffs.get("efficiency", {})
                intel_diff = diffs.get("intelligence", {})
                cov_diff = diffs.get("coverage", {})
                lines.append(f"- 任务完成率差距: {eff_diff.get('task_completion_rate', 'N/A')}%")
                lines.append(f"- 解题时间差距: {eff_diff.get('avg_solve_time', 'N/A')}s")
                lines.append(f"- 首次成功差距: {intel_diff.get('first_attempt_success_rate', 'N/A')}%")
                lines.append(f"- 幻觉率差距: {intel_diff.get('hallucination_rate', 'N/A')}%")
                lines.append(f"- 题型覆盖差距: {cov_diff.get('challenge_type_coverage', 'N/A')}%\n")

        # ---- Charts ----
        if chart_files and self.config.include_charts:
            lines.append("## 可视化图表 (Visualization)\n")
            for name, path in chart_files.items():
                rel_path = os.path.relpath(path, os.path.dirname(filepath))
                lines.append(f"![{name}]({rel_path})\n")

        # ---- Session Details ----
        if sessions and self.config.include_session_details:
            lines.append("## 解题详情 (Session Details)\n")
            lines.append("| 题目 | 分类 | 漏洞类型 | 难度 | 结果 | 耗时(s) | 工具调用 | Token | Flag |")
            lines.append("|------|------|----------|------|------|---------|----------|-------|------|")
            for s in sessions:
                result = "✓ 成功" if s.success else "✗ 失败"
                vuln_type = s.vuln_type or "-"
                flag = s.flag[:20] + "..." if len(s.flag) > 20 else (s.flag or "-")
                lines.append(f"| {s.challenge_name} | {s.category or '-'} | {vuln_type} | {s.difficulty or '-'} | {result} | {s.duration_seconds:.0f} | {s.tool_calls} | {s.tokens_used} | {flag} |")
            lines.append("")

        content = "\n".join(lines)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return filepath

    def _generate_html(
        self,
        sessions: List[ParsedSession],
        metrics: BenchmarkMetrics,
        model_name: str,
        chart_files: Optional[Dict[str, str]],
        filepath: str,
    ) -> str:
        """Generate HTML report using Jinja2 template.

        Args:
            sessions: Parsed sessions.
            metrics: Calculated metrics.
            model_name: Model name.
            chart_files: Chart file paths.
            filepath: Output file path.

        Returns:
            Output file path.
        """
        if not HAS_JINJA2:
            return self._generate_html_simple(sessions, metrics, model_name, chart_files, filepath)

        template = Template(self.HTML_TEMPLATE)

        # Build chart paths relative to output
        charts_relative: Dict[str, str] = {}
        if chart_files:
            for name, path in chart_files.items():
                charts_relative[name] = os.path.relpath(path, os.path.dirname(filepath))

        html = template.render(
            title=self.config.title,
            subtitle=self.config.subtitle,
            model_name=model_name,
            generated_at=datetime.now().isoformat(),
            total_challenges=len(sessions),
            total_flags=metrics.total_flags,
            cost_usd=metrics.cost_estimate_usd,
            accuracy=metrics.accuracy,
            precision=metrics.precision,
            f1_score=metrics.f1_score,
            error_rate=metrics.error_rate,
            tool_efficiency=metrics.tool_efficiency,
            efficiency=metrics.efficiency,
            intelligence=metrics.intelligence,
            coverage=metrics.coverage,
            sessions=[s.to_dict() for s in sessions] if self.config.include_session_details else [],
            charts=charts_relative,
        )

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)
        return filepath

    def _generate_html_simple(
        self,
        sessions: List[ParsedSession],
        metrics: BenchmarkMetrics,
        model_name: str,
        chart_files: Optional[Dict[str, str]],
        filepath: str,
    ) -> str:
        """Generate HTML report using simple string formatting (no Jinja2).

        Args:
            sessions: Parsed sessions.
            metrics: Calculated metrics.
            model_name: Model name.
            chart_files: Chart file paths.
            filepath: Output file path.

        Returns:
            Output file path.
        """
        def metric_class(val: float, thresholds: tuple = (0.8, 0.5)) -> str:
            if val >= thresholds[0]:
                return "metric-good"
            elif val >= thresholds[1]:
                return "metric-warn"
            return "metric-bad"

        lines = []
        lines.append("<!DOCTYPE html><html lang='zh-CN'><head><meta charset='UTF-8'>")
        lines.append("<style>")
        lines.append("body{font-family:Segoe UI,Arial,sans-serif;max-width:1200px;margin:0 auto;padding:20px;background:#f5f5f5;color:#333}")
        lines.append("h1{color:#1a73e8;border-bottom:3px solid #1a73e8;padding-bottom:10px}")
        lines.append("h2{color:#2c3e50;margin-top:30px;border-left:4px solid #1a73e8;padding-left:10px}")
        lines.append("table{width:100%;border-collapse:collapse;margin:10px 0;background:white}")
        lines.append("th,td{padding:8px 12px;text-align:left;border:1px solid #ddd}")
        lines.append("th{background:#1a73e8;color:white}.metric-good{color:#0d904f;font-weight:bold}")
        lines.append(".metric-bad{color:#d93025;font-weight:bold}.summary{background:#e8f0fe;padding:15px;border-radius:8px}")
        lines.append("</style></head><body>")

        lines.append(f"<h1>{self.config.title}</h1>")
        lines.append(f"<p><strong>{self.config.subtitle}</strong></p>")
        lines.append(f"<div class='summary'><p>模型: {model_name} | 题目: {len(sessions)} | "
                     f"成功率: {metrics.accuracy * 100:.1f}% | Flag: {metrics.total_flags} | "
                     f"成本: ${metrics.cost_estimate_usd:.4f}</p></div>")

        # Efficiency section
        if metrics.efficiency:
            lines.append("<h2>效率与资源</h2><table><tr><th>指标</th><th>值</th><th>公式</th></tr>")
            e = metrics.efficiency
            lines.append(f"<tr><td>任务完成率</td><td class='{metric_class(e.task_completion_rate/100)}'>{e.task_completion_rate:.1f}%</td><td>(成功数/总尝试数)×100%</td></tr>")
            lines.append(f"<tr><td>平均解题时间</td><td>{e.avg_solve_time_seconds:.0f}s</td><td>Σ(完成-开始)/成功数</td></tr>")
            lines.append(f"<tr><td>工具调用准确率</td><td>{e.tool_call_accuracy:.1f}%</td><td>(成功次数/总次数)×100%</td></tr>")
            lines.append(f"<tr><td>Token经济性</td><td>{e.token_economy_total:,}</td><td>输入+输出Token</td></tr>")
            lines.append("</table>")

        # Intelligence section
        if metrics.intelligence:
            lines.append("<h2>规划与智能</h2><table><tr><th>指标</th><th>值</th><th>公式</th></tr>")
            i = metrics.intelligence
            lines.append(f"<tr><td>首次尝试成功率</td><td class='{metric_class(i.first_attempt_success_rate/100)}'>{i.first_attempt_success_rate:.1f}%</td><td>(首次正确数/总解题数)×100%</td></tr>")
            lines.append(f"<tr><td>幻觉率</td><td class='{metric_class(i.hallucination_rate/50, (0.2, 0.4))}'>{i.hallucination_rate:.1f}%</td><td>(幻觉数/抽查数)×100%</td></tr>")
            lines.append(f"<tr><td>攻击路径质量</td><td>{i.attack_path_quality:.1f}步</td><td>avg steps per solve</td></tr>")
            lines.append(f"<tr><td>错误恢复率</td><td class='{metric_class(i.error_recovery_rate/100)}'>{i.error_recovery_rate:.1f}%</td><td>(恢复成功/报错总数)×100%</td></tr>")
            lines.append("</table>")

        # Coverage section
        if metrics.coverage:
            lines.append("<h2>能力覆盖</h2><table><tr><th>指标</th><th>值</th><th>公式</th></tr>")
            c = metrics.coverage
            lines.append(f"<tr><td>题型覆盖度</td><td>{c.challenge_type_coverage:.1f}% ({len(c.vuln_types_mastered)}/{c.total_vuln_types})</td><td>(掌握/总类型)×100%</td></tr>")
            lines.append(f"<tr><td>难题穿透率</td><td>{c.difficulty_penetration * 100:.1f}%</td><td>(高难度成功/高难度总数)×100%</td></tr>")
            lines.append("</table>")

        # Legacy metrics
        lines.append("<h2>遗留指标</h2><table>")
        lines.append(f"<tr><td>Accuracy</td><td>{metrics.accuracy:.2%}</td></tr>")
        lines.append(f"<tr><td>F1 Score</td><td>{metrics.f1_score:.2%}</td></tr>")
        lines.append(f"<tr><td>Tool Efficiency</td><td>{metrics.tool_efficiency:.4f}</td></tr>")
        lines.append(f"<tr><td>Cost Estimate</td><td>${metrics.cost_estimate_usd:.4f}</td></tr>")
        lines.append("</table>")

        # Session details
        if sessions and self.config.include_session_details:
            lines.append("<h2>解题详情</h2><table>")
            lines.append("<tr><th>题目</th><th>分类</th><th>漏洞类型</th><th>难度</th><th>结果</th><th>耗时</th><th>工具调用</th><th>Token</th></tr>")
            for s in sessions:
                res_class = "metric-good" if s.success else "metric-bad"
                res_text = "成功" if s.success else "失败"
                vuln_type = s.vuln_type or "-"
                lines.append(f"<tr><td>{s.challenge_name}</td><td>{s.category or '-'}</td><td>{vuln_type}</td>"
                             f"<td>{s.difficulty or '-'}</td><td class='{res_class}'>{res_text}</td>"
                             f"<td>{s.duration_seconds:.0f}</td><td>{s.tool_calls}</td><td>{s.tokens_used}</td></tr>")
            lines.append("</table>")

        lines.append(f"<p style='text-align:center;color:#999;margin-top:40px'>Generated by CAI Benchmark Framework - {datetime.now().isoformat()}</p>")
        lines.append("</body></html>")

        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        return filepath

    def generate_comparison_report(
        self,
        comparison: BaselineComparison,
        title: str = "CTF Benchmark Baseline Comparison",
    ) -> str:
        """Generate a baseline comparison report in Markdown format.

        Args:
            comparison: Baseline comparison results.
            title: Report title.

        Returns:
            Filepath of generated report.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(self.config.output_dir, f"comparison_{timestamp}.md")

        lines = [f"# {title}\n", f"**Comparison generated:** {datetime.now().isoformat()}\n"]

        if comparison.run_metrics:
            rm = comparison.run_metrics
            lines.append(f"## Run: {comparison.run_name}\n")
            lines.append(f"- Accuracy: {rm.accuracy:.2%}")
            lines.append(f"- F1 Score: {rm.f1_score:.2%}")
            lines.append(f"- Total Flags: {rm.total_flags}")
            lines.append(f"- Cost: ${rm.cost_estimate_usd:.4f}\n")

        for name, comp in comparison.comparisons.items():
            lines.append(f"## vs {name}\n")
            desc = comp.get("description", "")
            if desc:
                lines.append(f"> {desc}\n")

            # 9-metric differences
            diffs = comp.get("differences", {})

            if "efficiency" in diffs:
                lines.append("### 效率与资源差异\n")
                lines.append("| 指标 | 差异 |")
                lines.append("|------|------|")
                for k, v in diffs["efficiency"].items():
                    lines.append(f"| {k} | {v} |")
                lines.append("")

            if "intelligence" in diffs:
                lines.append("### 规划与智能差异\n")
                lines.append("| 指标 | 差异 |")
                lines.append("|------|------|")
                for k, v in diffs["intelligence"].items():
                    lines.append(f"| {k} | {v} |")
                lines.append("")

            if "coverage" in diffs:
                lines.append("### 能力覆盖差异\n")
                lines.append("| 指标 | 差异 |")
                lines.append("|------|------|")
                for k, v in diffs["coverage"].items():
                    lines.append(f"| {k} | {v} |")
                lines.append("")

        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return filepath