"""
压力测试模块 - 数据模型
"""
from tortoise import fields, Model


class StressTestScenario(Model):
    """压测场景"""
    id = fields.IntField(pk=True)
    project_id = fields.IntField(description="所属项目ID")
    name = fields.CharField(max_length=255, description="场景名称")
    description = fields.TextField(null=True, description="场景描述")
    scenario_type = fields.CharField(max_length=30, default="single_api",
                                     description="场景类型: single_api/multi_api/chain_api")
    # 压测配置
    target_apis = fields.JSONField(default=list,
                                   description="目标API列表: [{method, url, headers, body, params}]")
    think_time = fields.IntField(default=0, description="思考时间(ms) - 请求间隔")
    timeout = fields.IntField(default=30, description="请求超时时间(秒)")
    # AI 生成标记
    ai_generated = fields.BooleanField(default=False, description="是否由AI生成")
    ai_prompt = fields.TextField(null=True, description="AI生成时使用的提示")
    # 参数化
    parameter_data = fields.JSONField(null=True, description="参数化数据集 [{key: value}]")
    parameter_strategy = fields.CharField(max_length=20, default="sequential",
                                          description="参数化策略: sequential/random/unique")
    creator_id = fields.IntField(description="创建者ID")
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "stress_test_scenario"
        table_description = "压测场景表"


class StressTestTask(Model):
    """压测任务"""
    id = fields.IntField(pk=True)
    project_id = fields.IntField(description="所属项目ID")
    scenario_id = fields.IntField(description="关联场景ID")
    name = fields.CharField(max_length=255, description="任务名称")
    # 负载配置
    load_type = fields.CharField(max_length=20, default="constant",
                                 description="负载类型: constant/ramp_up/spike/soak")
    concurrency = fields.IntField(default=10, description="并发用户数")
    ramp_up_time = fields.IntField(default=0, description="梯度加压时间(秒)")
    ramp_up_steps = fields.IntField(default=1, description="梯度加压步骤数")
    duration = fields.IntField(default=60, description="持续时间(秒)")
    target_rps = fields.IntField(default=0, description="目标RPS(0=不限制)")
    # 状态
    status = fields.CharField(max_length=20, default="pending",
                              description="状态: pending/running/completed/failed/stopped")
    started_at = fields.DatetimeField(null=True, description="开始时间")
    finished_at = fields.DatetimeField(null=True, description="完成时间")
    # AI 推荐
    ai_recommended = fields.BooleanField(default=False, description="配置是否由AI推荐")
    ai_recommendation = fields.TextField(null=True, description="AI推荐的配置说明")
    error_message = fields.TextField(null=True, description="错误信息")
    creator_id = fields.IntField(description="创建者ID")
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "stress_test_task"
        table_description = "压测任务表"


class StressTestResult(Model):
    """压测结果汇总"""
    id = fields.IntField(pk=True)
    task_id = fields.IntField(description="关联任务ID", unique=True)
    # 核心指标
    total_requests = fields.IntField(default=0, description="总请求数")
    success_count = fields.IntField(default=0, description="成功数")
    fail_count = fields.IntField(default=0, description="失败数")
    error_rate = fields.FloatField(default=0, description="错误率(%)")
    # 响应时间
    avg_response_time = fields.FloatField(default=0, description="平均响应时间(ms)")
    min_response_time = fields.FloatField(default=0, description="最小响应时间(ms)")
    max_response_time = fields.FloatField(default=0, description="最大响应时间(ms)")
    p50_response_time = fields.FloatField(default=0, description="P50响应时间(ms)")
    p90_response_time = fields.FloatField(default=0, description="P90响应时间(ms)")
    p95_response_time = fields.FloatField(default=0, description="P95响应时间(ms)")
    p99_response_time = fields.FloatField(default=0, description="P99响应时间(ms)")
    # 吞吐量
    tps = fields.FloatField(default=0, description="TPS(每秒事务数)")
    throughput = fields.FloatField(default=0, description="吞吐量(bytes/s)")
    # 按接口明细
    api_details = fields.JSONField(default=list,
                                   description="各接口明细 [{url, method, avg_rt, p99_rt, error_rate, tps}]")
    # 错误分布
    error_distribution = fields.JSONField(default=dict,
                                          description="错误分布 {status_code: count}")
    # AI分析
    ai_analysis = fields.TextField(null=True, description="AI分析报告(Markdown)")
    ai_suggestions = fields.JSONField(null=True, description="AI优化建议列表")
    ai_risk_level = fields.CharField(max_length=20, null=True,
                                     description="AI风险评级: low/medium/high/critical")
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "stress_test_result"
        table_description = "压测结果汇总表"


class StressTestMetric(Model):
    """压测实时指标(时序数据)"""
    id = fields.IntField(pk=True)
    task_id = fields.IntField(description="关联任务ID", index=True)
    timestamp = fields.FloatField(description="采集时间戳")
    # 瞬时指标
    current_users = fields.IntField(default=0, description="当前并发用户数")
    requests_per_second = fields.FloatField(default=0, description="瞬时RPS")
    avg_response_time = fields.FloatField(default=0, description="瞬时平均响应时间(ms)")
    error_count = fields.IntField(default=0, description="本周期错误数")
    active_connections = fields.IntField(default=0, description="活跃连接数")
    # AI异常检测
    is_anomaly = fields.BooleanField(default=False, description="是否异常点")
    anomaly_reason = fields.CharField(max_length=255, null=True, description="异常原因")

    class Meta:
        table = "stress_test_metric"
        table_description = "压测实时指标表"


class PerformanceBaseline(Model):
    """性能基线"""
    id = fields.IntField(pk=True)
    project_id = fields.IntField(description="所属项目ID")
    name = fields.CharField(max_length=255, description="基线名称")
    description = fields.TextField(null=True, description="基线描述")
    version = fields.CharField(max_length=100, null=True, description="版本号")
    environment = fields.CharField(max_length=50, null=True, description="环境: dev/staging/production")
    # 基线指标(从某次压测结果提取)
    source_task_id = fields.IntField(null=True, description="来源任务ID")
    baseline_metrics = fields.JSONField(default=dict,
                                        description="基线指标 {api_url: {avg_rt, p99_rt, tps, error_rate}}")
    # 阈值配置
    thresholds = fields.JSONField(default=dict,
                                  description="告警阈值 {avg_rt_max, p99_rt_max, error_rate_max, tps_min}")
    is_active = fields.BooleanField(default=True, description="是否为当前生效基线")
    # AI对比分析
    ai_comparison = fields.TextField(null=True, description="AI与前次基线对比分析")
    creator_id = fields.IntField(description="创建者ID")
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "performance_baseline"
        table_description = "性能基线表"
