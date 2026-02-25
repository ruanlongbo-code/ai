"""
压力测试模块 - Pydantic Schemas
"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


# ========== 测试场景 ==========
class TargetApiItem(BaseModel):
    method: str = "GET"
    url: str
    headers: Optional[Dict[str, str]] = None
    body: Optional[Any] = None
    params: Optional[Dict[str, str]] = None
    name: Optional[str] = None


class ScenarioCreate(BaseModel):
    name: str
    description: Optional[str] = None
    scenario_type: str = "single_api"
    target_apis: List[TargetApiItem] = []
    think_time: int = 0
    timeout: int = 30
    parameter_data: Optional[List[Dict]] = None
    parameter_strategy: str = "sequential"


class ScenarioUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    scenario_type: Optional[str] = None
    target_apis: Optional[List[TargetApiItem]] = None
    think_time: Optional[int] = None
    timeout: Optional[int] = None
    parameter_data: Optional[List[Dict]] = None
    parameter_strategy: Optional[str] = None


class ScenarioResponse(BaseModel):
    id: int
    project_id: int
    name: str
    description: Optional[str]
    scenario_type: str
    target_apis: list
    think_time: int
    timeout: int
    ai_generated: bool
    parameter_data: Optional[list]
    parameter_strategy: str
    creator_id: int
    created_at: datetime
    updated_at: datetime


class AIGenerateScenarioRequest(BaseModel):
    """AI智能生成场景请求"""
    api_ids: Optional[List[int]] = None
    requirement_text: Optional[str] = None
    scenario_type: str = "single_api"
    description: Optional[str] = None


# ========== 压测任务 ==========
class TaskCreate(BaseModel):
    scenario_id: int
    name: str
    load_type: str = "constant"
    concurrency: int = 10
    ramp_up_time: int = 0
    ramp_up_steps: int = 1
    duration: int = 60
    target_rps: int = 0


class TaskResponse(BaseModel):
    id: int
    project_id: int
    scenario_id: int
    name: str
    load_type: str
    concurrency: int
    ramp_up_time: int
    ramp_up_steps: int
    duration: int
    target_rps: int
    status: str
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    ai_recommended: bool
    ai_recommendation: Optional[str]
    error_message: Optional[str]
    creator_id: int
    created_at: datetime
    updated_at: datetime
    # 关联
    scenario_name: Optional[str] = None


class AIRecommendConfigRequest(BaseModel):
    """AI推荐压测配置"""
    scenario_id: int
    test_goal: Optional[str] = None  # 测试目标描述


# ========== 压测结果 ==========
class ResultResponse(BaseModel):
    id: int
    task_id: int
    total_requests: int
    success_count: int
    fail_count: int
    error_rate: float
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    p50_response_time: float
    p90_response_time: float
    p95_response_time: float
    p99_response_time: float
    tps: float
    throughput: float
    api_details: list
    error_distribution: dict
    ai_analysis: Optional[str]
    ai_suggestions: Optional[list]
    ai_risk_level: Optional[str]
    created_at: datetime


# ========== 实时指标 ==========
class MetricResponse(BaseModel):
    id: int
    task_id: int
    timestamp: float
    current_users: int
    requests_per_second: float
    avg_response_time: float
    error_count: int
    active_connections: int
    is_anomaly: bool
    anomaly_reason: Optional[str]


# ========== 性能基线 ==========
class BaselineCreate(BaseModel):
    name: str
    description: Optional[str] = None
    version: Optional[str] = None
    environment: Optional[str] = None
    source_task_id: Optional[int] = None
    thresholds: Optional[Dict] = None


class BaselineUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    version: Optional[str] = None
    environment: Optional[str] = None
    thresholds: Optional[Dict] = None
    is_active: Optional[bool] = None


class BaselineResponse(BaseModel):
    id: int
    project_id: int
    name: str
    description: Optional[str]
    version: Optional[str]
    environment: Optional[str]
    source_task_id: Optional[int]
    baseline_metrics: dict
    thresholds: dict
    is_active: bool
    ai_comparison: Optional[str]
    creator_id: int
    created_at: datetime
    updated_at: datetime


class BaselineCompareRequest(BaseModel):
    """AI基线对比请求"""
    baseline_id_a: int
    baseline_id_b: int
