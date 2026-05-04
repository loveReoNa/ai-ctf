"""CAI Benchmark Data Analysis Module - rnd_project_part2.

Provides comprehensive CTF benchmark evaluation using the 9-metric system
organized into 3 evaluation categories:

    效率与资源 (Efficiency & Resources):
        - task_completion_rate (任务完成率)
        - avg_solve_time (平均解题时间)
        - tool_call_accuracy (工具调用准确率)
        - token_economy (Token经济性)

    规划与智能 (Planning & Intelligence):
        - first_attempt_success_rate (首次尝试成功率)
        - hallucination_rate (幻觉率)
        - attack_path_quality (攻击路径质量)
        - error_recovery_rate (错误恢复率)

    能力覆盖 (Capability Coverage):
        - challenge_type_coverage (题型覆盖度)
        - difficulty_penetration (难题穿透率)
        - category_breakdown (分类细分)
        - difficulty_breakdown (难度细分)

With 5 baseline profiles for comparison:
    - human_expert (HTB社区人类平均水平, 4.3h)
    - expert_writeup (Writeup最优攻击路径)
    - random_solver (随机/暴力尝试, 理论下界)
    - tool_only (无AI推理的工具执行)
    - avg_ctf_player (CTF新手平均水平)

Usage:
    from data_analysis import (
        LogParser, MetricsEngine, BenchmarkVisualizer,
        ReportGenerator, BaselineManager,
    )
"""
from data_analysis.log_parser import LogParser, ParsedSession, ParseSummary  # noqa: F401
from data_analysis.metrics_engine import (  # noqa: F401
    BenchmarkMetrics, EfficiencyMetrics, IntelligenceMetrics,
    CoverageMetrics, MetricsEngine,
)
from data_analysis.baseline import (  # noqa: F401
    BaselineProfile, BaselineComparison, BaselineManager,
)
from data_analysis.visualization import (  # noqa: F401
    BenchmarkVisualizer, ChartConfig, create_sample_charts,
)
from data_analysis.report_generator import (  # noqa: F401
    ReportGenerator, ReportConfig,
)