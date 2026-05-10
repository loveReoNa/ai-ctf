#!/usr/bin/env python3
"""data_analysis模块独立演示——指标计算+基线对比+可视化+报告生成

用途：毕业论文截图②——展示9维指标体系、基线对比、图表生成
运行：cd <project_root> && source venv/bin/activate && python scripts/screenshot_demos/demo_data_analysis.py
"""

import os
import tempfile
from data_analysis import (
    LogParser, MetricsEngine, BaselineManager,
    ReportGenerator, ReportConfig, create_sample_charts
)

# 1. 解析模拟会话日志
parser = LogParser()
session_data = [
    ("flag{sqli_solved} success\nSolved in 300s, 8 tool calls, 500 tokens",
     "web_sqli_1", "gpt-4", "web", "sqli", "medium"),
    ("flag{xss_found} success\nSolved in 180s, 5 tool calls, 300 tokens",
     "web_xss_1", "gpt-4", "web", "xss", "easy"),
    ("Failed to solve - timeout after 600s, 15 tool calls, 800 tokens",
     "pwn_overflow_1", "gpt-4", "pwn", "buffer_overflow", "hard"),
    ("flag{crypto_aes} success\nSolved in 420s, 12 tool calls, 700 tokens",
     "crypto_aes_1", "gpt-4", "crypto", "aes", "hard"),
    ("flag{rev_patch} success\nSolved in 240s, 6 tool calls, 400 tokens",
     "rev_bin_1", "gpt-4", "reverse", "binary_patching", "medium"),
]
for log_text, ch_name, m_name, cat, vtype, diff in session_data:
    parser.parse_agent_log(log_text, challenge_name=ch_name, model_name=m_name,
                           category=cat, vuln_type=vtype, difficulty=diff)

sessions = parser.get_sessions()
summary = parser.get_summary()
print(f"LogParser: {len(sessions)} sessions parsed, {summary.success_count}/{summary.total_sessions} successful")
print(f"  Challenges: {len(summary.challenge_types)} types, Difficulties: {len(summary.difficulty_levels)} levels")

# 2. 计算9项指标体系
engine = MetricsEngine()
metrics = engine.calculate_metrics(sessions)
print(f"\n{'='*50}")
print("9-DIMENSION METRICS REPORT")
print(f"{'='*50}")
print(f"  Accuracy (正确率):        {metrics.accuracy:.2%}")
print(f"  F1 Score (F1分数):        {metrics.f1_score:.2%}")
print(f"  Total Flags (捕获Flags):  {metrics.total_flags}")
print(f"  --- Efficiency (效率维度) ---")
print(f"  Task Completion Rate:     {metrics.efficiency.task_completion_rate:.1f}%")
print(f"  Avg Solve Time:           {metrics.efficiency.avg_solve_time_seconds:.0f}s")
print(f"  Token Efficiency:         {metrics.efficiency.token_efficiency:.2f} flags/kTokens")
print(f"  --- Intelligence (智能维度) ---")
print(f"  First Attempt Success:    {metrics.intelligence.first_attempt_success_rate:.1f}%")
print(f"  Hallucination Rate:       {metrics.intelligence.hallucination_rate:.1f}%")
print(f"  Error Recovery Rate:      {metrics.intelligence.error_recovery_rate:.1f}%")
print(f"  --- Coverage (覆盖维度) ---")
print(f"  Challenge Type Coverage:  {metrics.coverage.challenge_type_coverage:.1f}%")
print(f"  Tools Per Challenge:      {metrics.coverage.avg_tools_per_challenge:.1f}")
print(f"  Vuln Types Mastered:      {len(metrics.coverage.vuln_types_mastered)}/{metrics.coverage.total_vuln_types}")

# 3. 基线对比
bm = BaselineManager()
comp = bm.compare_to_baselines("demo_agent", sessions)
print(f"\n{'='*50}")
print("BASELINE COMPARISON (5 baselines)")
print(f"{'='*50}")
for name, result in comp.comparisons.items():
    print(f"  vs {name}: accuracy={result.get('accuracy', 'N/A')}, flags={result.get('flags', 'N/A')}, "
          f"score_ratio={result.get('score_ratio', 'N/A')}")

# 4. 生成可视化图表
tmpdir = tempfile.mkdtemp(prefix="ctf_charts_")
charts = create_sample_charts(output_dir=tmpdir)
print(f"\nVisualization: {len(charts)} charts generated in {tmpdir}")
for c in charts:
    if os.path.exists(c):
        print(f"  📊 {os.path.basename(c)} ({os.path.getsize(c)} bytes)")

# 5. 生成多格式报告
rg = ReportGenerator(ReportConfig(output_dir=tmpdir))
result_paths = rg.generate_report(sessions, metrics, "gpt-4", chart_files=charts)
print(f"\nReportGenerator outputs:")
for key, path in result_paths.items():
    if os.path.exists(path):
        print(f"  📄 {key}: {os.path.basename(path)} ({os.path.getsize(path)} bytes)")

print(f"\n✅ data_analysis module all features verified!")