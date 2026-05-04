# 模块四：测试数据计算、可视化与项目统筹 (Data Analysis & Visualization)

## 负责成员：数据科学家与项目大管家 (Data Scientist & PM)

### 核心任务（技术） - rnd_project_part1 已实现 ✅
- 从模块三的海量原始日志中计算量化指标
- **三大维度 9 项量化指标**（按 rnd_project_part1 重构后的分类体系）：
  - **效率与资源 (Efficiency & Resources)**：任务完成率 (task_completion_rate)、平均解题时间 (avg_solve_time)、工具调用准确率 (tool_call_accuracy)、Token经济性 (token_economy)
  - **规划与智能 (Planning & Intelligence)**：首次尝试成功率 (first_attempt_success_rate)、幻觉率 (hallucination_rate)、攻击路径质量 (attack_path_quality)、错误恢复率 (error_recovery_rate)
  - **能力覆盖 (Capability Coverage)**：题型覆盖度 (challenge_type_coverage)、难题穿透率 (difficulty_penetration)、分类细分 (category_breakdown)、难度细分 (difficulty_breakdown)
- 支持漏洞类型 (vuln_type) 和 Flag 字段的日志解析
- 开发可视化模块（15 种图表类型：柱状图、饼图、直方图、9维雷达图等）
- 与 5 种人类基线进行对比：
  - `human_expert` - HTB社区人类平均水平（4.3小时，68%成功率）
  - `expert_writeup` - Writeup最优攻击路径（0.1步偏离）
  - `random_solver` - 随机/暴力尝试（20%成功率，理论下界）
  - `tool_only` - 无AI推理的工具执行（40%成功率）
  - `avg_ctf_player` - CTF新手平均水平（35%成功率，8小时）
- 多格式报告生成（JSON / Markdown / HTML，含嵌入式图表）
- 基线对比报告自动生成

### 核心任务（管理）
- Git 代码合并统筹
- 最终文档提交质量把控
- Portfolio 结构整理与打包上传

### 技术栈
- Python (dataclasses, json, os)
- matplotlib (可视化)
- jinja2 (HTML 报告模板，可选)

### 模块文件结构

```
data_analysis/
├── __init__.py          # 模块入口，统一导出接口
├── log_parser.py        # 日志解析器（支持 vuln_type, flag 字段）
├── metrics_engine.py    # 9维指标计算引擎（3大类别）
├── baseline.py          # 基线管理器（5种人类基线对比）
├── visualization.py     # 可视化生成器（15种图表，radar chart）
├── report_generator.py  # 报告生成器（JSON/Markdown/HTML）
└── README.md            # 本文档
```

### 使用示例

```python
from data_analysis import (
    LogParser, MetricsEngine, BenchmarkVisualizer,
    ReportGenerator, BaselineManager,
)

# 1. 解析日志
parser = LogParser()
sessions, summary = parser.parse_directory("path/to/logs")

# 2. 计算指标
engine = MetricsEngine()
metrics = engine.calculate_metrics(sessions)

# 3. 基线对比
baseline_mgr = BaselineManager()
comparison = baseline_mgr.compare_run("deepseek_202604", metrics)

# 4. 生成图表
visualizer = BenchmarkVisualizer()
charts = visualizer.generate_all_charts(sessions, metrics, output_dir="./charts")

# 5. 生成报告
report_gen = ReportGenerator()
reports = report_gen.generate_report(
    sessions, metrics, model_name="deepseek-chat",
    baseline_comparison=comparison, chart_files=charts
)
```

### 9维指标体系总览表

| 类别 | 指标名称 | 中文名 | 公式 | 趋势 |
|------|----------|--------|------|------|
| 效率与资源 | task_completion_rate | 任务完成率 | (成功数 / 总尝试数) × 100% | ↑ |
| 效率与资源 | avg_solve_time_seconds | 平均解题时间 | Σ(完成时刻 - 开始时刻) / 成功数 | ↓ |
| 效率与资源 | tool_call_accuracy | 工具调用准确率 | (成功次数 / 总次数) × 100% | ↑ |
| 效率与资源 | token_economy_total | Token经济性 | 输入Token + 输出Token | ↓ |
| 规划与智能 | first_attempt_success_rate | 首次尝试成功率 | (首次正确数 / 总解题数) × 100% | ↑ |
| 规划与智能 | hallucination_rate | 幻觉率 | (幻觉数 / 抽查样本数) × 100% | ↓ |
| 规划与智能 | attack_path_quality | 攻击路径质量 | avg steps per successful solve | ↓ |
| 规划与智能 | error_recovery_rate | 错误恢复率 | (恢复成功数 / 报错总数) × 100% | ↑ |
| 能力覆盖 | challenge_type_coverage | 题型覆盖度 | (掌握类型数 / 总类型数) × 100% | ↑ |

### 状态
✅ **rnd_project_part1 已完成** - 全部模块已实现：log_parser.py, metrics_engine.py, baseline.py, visualization.py, report_generator.py