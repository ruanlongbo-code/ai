"""
压力测试模块 - API路由
"""
import asyncio
import json
import time
import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from service.stress_test.models import (
    StressTestScenario, StressTestTask, StressTestResult,
    StressTestMetric, PerformanceBaseline
)
from service.stress_test.schemas import (
    ScenarioCreate, ScenarioUpdate, ScenarioResponse,
    AIGenerateScenarioRequest, TaskCreate, TaskResponse,
    ResultResponse, MetricResponse,
    BaselineCreate, BaselineUpdate, BaselineResponse,
    BaselineCompareRequest, AIRecommendConfigRequest
)
from utils.auth import get_current_user
from service.user.models import User
from utils.stress_engine import StressEngine
from utils.stress_ai_analyzer import (
    ai_generate_scenario, ai_recommend_config,
    ai_analyze_report, ai_detect_anomaly, ai_compare_baselines
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/stress-test", tags=["压力测试"])

# 存储正在运行的压测任务
_running_tasks = {}


# ======================== 测试场景 ========================

@router.get("/scenarios")
async def list_scenarios(
    project_id: int = Query(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """获取场景列表"""
    queryset = StressTestScenario.filter(project_id=project_id)
    if keyword:
        queryset = queryset.filter(name__icontains=keyword)
    total = await queryset.count()
    items = await queryset.order_by("-created_at").offset((page - 1) * page_size).limit(page_size)
    return {
        "total": total,
        "items": [
            {
                "id": s.id, "project_id": s.project_id, "name": s.name,
                "description": s.description, "scenario_type": s.scenario_type,
                "target_apis": s.target_apis, "think_time": s.think_time,
                "timeout": s.timeout, "ai_generated": s.ai_generated,
                "parameter_data": s.parameter_data,
                "parameter_strategy": s.parameter_strategy,
                "creator_id": s.creator_id,
                "created_at": s.created_at.isoformat(),
                "updated_at": s.updated_at.isoformat(),
                "api_count": len(s.target_apis) if s.target_apis else 0,
            }
            for s in items
        ],
    }


@router.get("/scenarios/{scenario_id}")
async def get_scenario(scenario_id: int, current_user: User = Depends(get_current_user)):
    """获取场景详情"""
    s = await StressTestScenario.get_or_none(id=scenario_id)
    if not s:
        raise HTTPException(status_code=404, detail="场景不存在")
    return {
        "id": s.id, "project_id": s.project_id, "name": s.name,
        "description": s.description, "scenario_type": s.scenario_type,
        "target_apis": s.target_apis, "think_time": s.think_time,
        "timeout": s.timeout, "ai_generated": s.ai_generated,
        "ai_prompt": s.ai_prompt,
        "parameter_data": s.parameter_data,
        "parameter_strategy": s.parameter_strategy,
        "creator_id": s.creator_id,
        "created_at": s.created_at.isoformat(),
        "updated_at": s.updated_at.isoformat(),
    }


@router.post("/scenarios")
async def create_scenario(
    project_id: int = Query(...),
    data: ScenarioCreate = None,
    current_user: User = Depends(get_current_user)
):
    """创建场景"""
    scenario = await StressTestScenario.create(
        project_id=project_id,
        name=data.name,
        description=data.description,
        scenario_type=data.scenario_type,
        target_apis=[api.dict() for api in data.target_apis],
        think_time=data.think_time,
        timeout=data.timeout,
        parameter_data=data.parameter_data,
        parameter_strategy=data.parameter_strategy,
        creator_id=current_user.id,
    )
    return {"id": scenario.id, "message": "场景创建成功"}


@router.put("/scenarios/{scenario_id}")
async def update_scenario(
    scenario_id: int,
    data: ScenarioUpdate,
    current_user: User = Depends(get_current_user)
):
    """更新场景"""
    scenario = await StressTestScenario.get_or_none(id=scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="场景不存在")
    update_data = data.dict(exclude_unset=True)
    if "target_apis" in update_data and update_data["target_apis"]:
        update_data["target_apis"] = [
            api.dict() if hasattr(api, "dict") else api for api in update_data["target_apis"]
        ]
    await StressTestScenario.filter(id=scenario_id).update(**update_data)
    return {"message": "场景更新成功"}


@router.delete("/scenarios/{scenario_id}")
async def delete_scenario(scenario_id: int, current_user: User = Depends(get_current_user)):
    """删除场景"""
    deleted = await StressTestScenario.filter(id=scenario_id).delete()
    if not deleted:
        raise HTTPException(status_code=404, detail="场景不存在")
    return {"message": "场景删除成功"}


@router.post("/scenarios/ai-generate")
async def ai_generate_scenario_api(
    project_id: int = Query(...),
    data: AIGenerateScenarioRequest = None,
    current_user: User = Depends(get_current_user)
):
    """AI智能生成压测场景（LLM + RAG）"""
    # 收集API信息
    api_specs = []
    if data.api_ids:
        from service.api_test.models import ApiInterface
        for api_id in data.api_ids:
            api = await ApiInterface.get_or_none(id=api_id)
            if api:
                api_specs.append({
                    "name": api.name,
                    "method": api.method,
                    "url": api.path,
                    "description": getattr(api, "description", ""),
                })

    # RAG增强: 检索历史性能知识
    rag_context = ""
    try:
        from config.settings import RAG_SERVER_URL, LIGHTRAG_API_KEY
        if RAG_SERVER_URL:
            import httpx
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    f"{RAG_SERVER_URL}/query",
                    json={"query": f"性能测试 压力测试 {data.requirement_text or ''}", "mode": "hybrid"},
                    headers={"Authorization": f"Bearer {LIGHTRAG_API_KEY}"}
                )
                if resp.status_code == 200:
                    rag_context = resp.json().get("response", "")
    except Exception as e:
        logger.warning(f"RAG检索失败: {e}")

    # 调用AI生成
    result = await ai_generate_scenario(
        api_specs=api_specs,
        requirement_text=data.requirement_text or data.description or "",
        scenario_type=data.scenario_type,
        rag_context=rag_context
    )

    # 保存场景
    scenario = await StressTestScenario.create(
        project_id=project_id,
        name=result.get("name", "AI生成场景"),
        description=result.get("description", ""),
        scenario_type=result.get("scenario_type", data.scenario_type),
        target_apis=result.get("target_apis", []),
        think_time=result.get("think_time", 0),
        timeout=result.get("timeout", 30),
        ai_generated=True,
        ai_prompt=data.requirement_text or data.description,
        parameter_data=result.get("parameter_data"),
        parameter_strategy=result.get("parameter_strategy", "sequential"),
        creator_id=current_user.id,
    )

    return {
        "id": scenario.id,
        "message": "AI场景生成成功",
        "scenario": result,
        "recommended_concurrency": result.get("recommended_concurrency", 10),
        "recommended_duration": result.get("recommended_duration", 60),
        "test_focus": result.get("test_focus", []),
    }


# ======================== 压测任务 ========================

@router.get("/tasks")
async def list_tasks(
    project_id: int = Query(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """获取任务列表"""
    queryset = StressTestTask.filter(project_id=project_id)
    if status:
        queryset = queryset.filter(status=status)
    total = await queryset.count()
    items = await queryset.order_by("-created_at").offset((page - 1) * page_size).limit(page_size)

    result_items = []
    for t in items:
        scenario = await StressTestScenario.get_or_none(id=t.scenario_id)
        result_items.append({
            "id": t.id, "project_id": t.project_id,
            "scenario_id": t.scenario_id,
            "scenario_name": scenario.name if scenario else "已删除",
            "name": t.name, "load_type": t.load_type,
            "concurrency": t.concurrency,
            "ramp_up_time": t.ramp_up_time,
            "ramp_up_steps": t.ramp_up_steps,
            "duration": t.duration, "target_rps": t.target_rps,
            "status": t.status,
            "started_at": t.started_at.isoformat() if t.started_at else None,
            "finished_at": t.finished_at.isoformat() if t.finished_at else None,
            "ai_recommended": t.ai_recommended,
            "creator_id": t.creator_id,
            "created_at": t.created_at.isoformat(),
        })
    return {"total": total, "items": result_items}


@router.post("/tasks")
async def create_task(
    project_id: int = Query(...),
    data: TaskCreate = None,
    current_user: User = Depends(get_current_user)
):
    """创建压测任务"""
    scenario = await StressTestScenario.get_or_none(id=data.scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="场景不存在")
    task = await StressTestTask.create(
        project_id=project_id,
        scenario_id=data.scenario_id,
        name=data.name,
        load_type=data.load_type,
        concurrency=data.concurrency,
        ramp_up_time=data.ramp_up_time,
        ramp_up_steps=data.ramp_up_steps,
        duration=data.duration,
        target_rps=data.target_rps,
        creator_id=current_user.id,
    )
    return {"id": task.id, "message": "任务创建成功"}


@router.post("/tasks/{task_id}/execute")
async def execute_task(task_id: int, current_user: User = Depends(get_current_user)):
    """执行压测任务（SSE实时推送指标）"""
    task = await StressTestTask.get_or_none(id=task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task.status == "running":
        raise HTTPException(status_code=400, detail="任务正在运行中")

    scenario = await StressTestScenario.get_or_none(id=task.scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="关联场景不存在")

    async def event_stream():
        # 更新状态
        await StressTestTask.filter(id=task_id).update(
            status="running", started_at=datetime.now()
        )
        yield f"data: {json.dumps({'type': 'status', 'status': 'running', 'message': '压测开始'})}\n\n"

        metric_queue = asyncio.Queue()

        async def on_metric(snapshot, is_anomaly, anomaly_reason):
            await metric_queue.put({
                "type": "metric",
                "data": {
                    "timestamp": snapshot.timestamp,
                    "current_users": snapshot.current_users,
                    "rps": snapshot.requests_per_second,
                    "avg_rt": snapshot.avg_response_time,
                    "error_count": snapshot.error_count,
                    "active_connections": snapshot.active_connections,
                    "is_anomaly": is_anomaly,
                    "anomaly_reason": anomaly_reason,
                }
            })
            # 保存到数据库
            await StressTestMetric.create(
                task_id=task_id,
                timestamp=snapshot.timestamp,
                current_users=snapshot.current_users,
                requests_per_second=snapshot.requests_per_second,
                avg_response_time=snapshot.avg_response_time,
                error_count=snapshot.error_count,
                active_connections=snapshot.active_connections,
                is_anomaly=is_anomaly,
                anomaly_reason=anomaly_reason if is_anomaly else None,
            )

        engine = StressEngine(
            target_apis=scenario.target_apis,
            concurrency=task.concurrency,
            duration=task.duration,
            load_type=task.load_type,
            ramp_up_time=task.ramp_up_time,
            ramp_up_steps=task.ramp_up_steps,
            target_rps=task.target_rps,
            think_time=scenario.think_time,
            timeout=scenario.timeout,
            parameter_data=scenario.parameter_data,
            parameter_strategy=scenario.parameter_strategy,
            on_metric=on_metric,
        )
        _running_tasks[task_id] = engine

        # 在后台运行引擎
        engine_task = asyncio.create_task(engine.run())

        try:
            while not engine_task.done():
                try:
                    metric = await asyncio.wait_for(metric_queue.get(), timeout=2)
                    yield f"data: {json.dumps(metric, ensure_ascii=False)}\n\n"
                except asyncio.TimeoutError:
                    yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"

            # 获取最终报告
            report = engine_task.result()

            # 保存结果
            result = await StressTestResult.create(
                task_id=task_id,
                total_requests=report.total_requests,
                success_count=report.success_count,
                fail_count=report.fail_count,
                error_rate=report.error_rate,
                avg_response_time=report.avg_response_time,
                min_response_time=report.min_response_time,
                max_response_time=report.max_response_time,
                p50_response_time=report.p50_response_time,
                p90_response_time=report.p90_response_time,
                p95_response_time=report.p95_response_time,
                p99_response_time=report.p99_response_time,
                tps=report.tps,
                throughput=report.throughput,
                api_details=report.api_details,
                error_distribution=report.error_distribution,
            )

            await StressTestTask.filter(id=task_id).update(
                status="completed", finished_at=datetime.now()
            )

            yield f"data: {json.dumps({'type': 'completed', 'result_id': result.id, 'summary': {'total': report.total_requests, 'success': report.success_count, 'fail': report.fail_count, 'tps': report.tps, 'avg_rt': report.avg_response_time, 'error_rate': report.error_rate}}, ensure_ascii=False)}\n\n"

        except Exception as e:
            logger.error(f"压测执行失败: {e}")
            await StressTestTask.filter(id=task_id).update(
                status="failed", error_message=str(e), finished_at=datetime.now()
            )
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"
        finally:
            _running_tasks.pop(task_id, None)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/tasks/{task_id}/stop")
async def stop_task(task_id: int, current_user: User = Depends(get_current_user)):
    """停止压测任务"""
    engine = _running_tasks.get(task_id)
    if engine:
        engine.stop()
        await StressTestTask.filter(id=task_id).update(
            status="stopped", finished_at=datetime.now()
        )
        return {"message": "已发送停止信号"}
    raise HTTPException(status_code=400, detail="任务未在运行")


@router.delete("/tasks/{task_id}")
async def delete_task(task_id: int, current_user: User = Depends(get_current_user)):
    """删除任务"""
    await StressTestMetric.filter(task_id=task_id).delete()
    await StressTestResult.filter(task_id=task_id).delete()
    deleted = await StressTestTask.filter(id=task_id).delete()
    if not deleted:
        raise HTTPException(status_code=404, detail="任务不存在")
    return {"message": "任务删除成功"}


@router.post("/tasks/ai-recommend")
async def ai_recommend_config_api(
    data: AIRecommendConfigRequest,
    current_user: User = Depends(get_current_user)
):
    """AI推荐压测配置"""
    scenario = await StressTestScenario.get_or_none(id=data.scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="场景不存在")

    scenario_info = {
        "name": scenario.name,
        "scenario_type": scenario.scenario_type,
        "target_apis": scenario.target_apis,
    }

    result = await ai_recommend_config(
        scenario_info=scenario_info,
        test_goal=data.test_goal or "",
    )
    return {"recommendation": result}


# ======================== 性能报告 ========================

@router.get("/results/{task_id}")
async def get_result(task_id: int, current_user: User = Depends(get_current_user)):
    """获取压测结果"""
    result = await StressTestResult.get_or_none(task_id=task_id)
    if not result:
        raise HTTPException(status_code=404, detail="暂无压测结果")
    task = await StressTestTask.get_or_none(id=task_id)
    scenario = await StressTestScenario.get_or_none(id=task.scenario_id) if task else None
    return {
        "id": result.id, "task_id": result.task_id,
        "task_name": task.name if task else "",
        "scenario_name": scenario.name if scenario else "",
        "load_type": task.load_type if task else "",
        "concurrency": task.concurrency if task else 0,
        "duration": task.duration if task else 0,
        "total_requests": result.total_requests,
        "success_count": result.success_count,
        "fail_count": result.fail_count,
        "error_rate": result.error_rate,
        "avg_response_time": result.avg_response_time,
        "min_response_time": result.min_response_time,
        "max_response_time": result.max_response_time,
        "p50_response_time": result.p50_response_time,
        "p90_response_time": result.p90_response_time,
        "p95_response_time": result.p95_response_time,
        "p99_response_time": result.p99_response_time,
        "tps": result.tps,
        "throughput": result.throughput,
        "api_details": result.api_details,
        "error_distribution": result.error_distribution,
        "ai_analysis": result.ai_analysis,
        "ai_suggestions": result.ai_suggestions,
        "ai_risk_level": result.ai_risk_level,
        "created_at": result.created_at.isoformat(),
    }


@router.post("/results/{task_id}/ai-analyze")
async def ai_analyze_result(task_id: int, current_user: User = Depends(get_current_user)):
    """AI分析压测结果"""
    result = await StressTestResult.get_or_none(task_id=task_id)
    if not result:
        raise HTTPException(status_code=404, detail="暂无压测结果")

    task = await StressTestTask.get_or_none(id=task_id)
    scenario_info = None
    if task:
        scenario_info = {
            "concurrency": task.concurrency,
            "duration": task.duration,
            "load_type": task.load_type,
        }

    # 查找当前生效基线做对比
    baseline_data = None
    if task:
        baseline = await PerformanceBaseline.filter(
            project_id=task.project_id, is_active=True
        ).first()
        if baseline:
            baseline_data = baseline.baseline_metrics

    result_data = {
        "total_requests": result.total_requests,
        "success_count": result.success_count,
        "fail_count": result.fail_count,
        "error_rate": result.error_rate,
        "avg_response_time": result.avg_response_time,
        "min_response_time": result.min_response_time,
        "max_response_time": result.max_response_time,
        "p50_response_time": result.p50_response_time,
        "p90_response_time": result.p90_response_time,
        "p95_response_time": result.p95_response_time,
        "p99_response_time": result.p99_response_time,
        "tps": result.tps,
        "api_details": result.api_details,
        "error_distribution": result.error_distribution,
    }

    analysis = await ai_analyze_report(
        result_data=result_data,
        scenario_info=scenario_info,
        baseline_data=baseline_data,
    )

    # 保存分析结果
    await StressTestResult.filter(id=result.id).update(
        ai_analysis=analysis.get("analysis", ""),
        ai_suggestions=analysis.get("suggestions", []),
        ai_risk_level=analysis.get("risk_level", ""),
    )

    return {"analysis": analysis}


# ======================== 实时监控 ========================

@router.get("/metrics/{task_id}")
async def get_metrics(
    task_id: int,
    limit: int = Query(300, ge=1, le=3600),
    current_user: User = Depends(get_current_user)
):
    """获取压测指标历史"""
    metrics = await StressTestMetric.filter(task_id=task_id).order_by("-timestamp").limit(limit)
    metrics.reverse()
    return {
        "items": [
            {
                "timestamp": m.timestamp,
                "current_users": m.current_users,
                "rps": m.requests_per_second,
                "avg_rt": m.avg_response_time,
                "error_count": m.error_count,
                "active_connections": m.active_connections,
                "is_anomaly": m.is_anomaly,
                "anomaly_reason": m.anomaly_reason,
            }
            for m in metrics
        ]
    }


@router.get("/metrics/{task_id}/stream")
async def stream_metrics(task_id: int, current_user: User = Depends(get_current_user)):
    """SSE实时推送指标"""
    task = await StressTestTask.get_or_none(id=task_id)
    if not task or task.status != "running":
        raise HTTPException(status_code=400, detail="任务未在运行")

    async def event_stream():
        last_id = 0
        while True:
            metrics = await StressTestMetric.filter(
                task_id=task_id, id__gt=last_id
            ).order_by("id").limit(10)

            for m in metrics:
                last_id = m.id
                yield f"data: {json.dumps({'timestamp': m.timestamp, 'current_users': m.current_users, 'rps': m.requests_per_second, 'avg_rt': m.avg_response_time, 'error_count': m.error_count, 'is_anomaly': m.is_anomaly, 'anomaly_reason': m.anomaly_reason})}\n\n"

            # 检查任务是否还在运行
            task_check = await StressTestTask.get_or_none(id=task_id)
            if not task_check or task_check.status != "running":
                yield f"data: {json.dumps({'type': 'ended'})}\n\n"
                break

            await asyncio.sleep(1)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# ======================== 性能基线 ========================

@router.get("/baselines")
async def list_baselines(
    project_id: int = Query(...),
    current_user: User = Depends(get_current_user)
):
    """获取基线列表"""
    items = await PerformanceBaseline.filter(project_id=project_id).order_by("-created_at")
    return {
        "items": [
            {
                "id": b.id, "project_id": b.project_id, "name": b.name,
                "description": b.description, "version": b.version,
                "environment": b.environment,
                "source_task_id": b.source_task_id,
                "baseline_metrics": b.baseline_metrics,
                "thresholds": b.thresholds,
                "is_active": b.is_active,
                "ai_comparison": b.ai_comparison,
                "creator_id": b.creator_id,
                "created_at": b.created_at.isoformat(),
                "updated_at": b.updated_at.isoformat(),
            }
            for b in items
        ]
    }


@router.post("/baselines")
async def create_baseline(
    project_id: int = Query(...),
    data: BaselineCreate = None,
    current_user: User = Depends(get_current_user)
):
    """创建基线（从压测结果提取）"""
    baseline_metrics = {}
    if data.source_task_id:
        result = await StressTestResult.get_or_none(task_id=data.source_task_id)
        if result:
            baseline_metrics = {
                "overall": {
                    "avg_rt": result.avg_response_time,
                    "p50_rt": result.p50_response_time,
                    "p90_rt": result.p90_response_time,
                    "p95_rt": result.p95_response_time,
                    "p99_rt": result.p99_response_time,
                    "tps": result.tps,
                    "error_rate": result.error_rate,
                },
                "api_details": result.api_details,
            }

    baseline = await PerformanceBaseline.create(
        project_id=project_id,
        name=data.name,
        description=data.description,
        version=data.version,
        environment=data.environment,
        source_task_id=data.source_task_id,
        baseline_metrics=baseline_metrics,
        thresholds=data.thresholds or {
            "avg_rt_max": 500, "p99_rt_max": 2000,
            "error_rate_max": 1, "tps_min": 100
        },
        creator_id=current_user.id,
    )
    return {"id": baseline.id, "message": "基线创建成功"}


@router.put("/baselines/{baseline_id}")
async def update_baseline(
    baseline_id: int,
    data: BaselineUpdate,
    current_user: User = Depends(get_current_user)
):
    """更新基线"""
    update_data = data.dict(exclude_unset=True)
    # 如果设为激活，取消其他同项目基线的激活状态
    if update_data.get("is_active"):
        baseline = await PerformanceBaseline.get_or_none(id=baseline_id)
        if baseline:
            await PerformanceBaseline.filter(
                project_id=baseline.project_id, is_active=True
            ).update(is_active=False)
    await PerformanceBaseline.filter(id=baseline_id).update(**update_data)
    return {"message": "基线更新成功"}


@router.delete("/baselines/{baseline_id}")
async def delete_baseline(baseline_id: int, current_user: User = Depends(get_current_user)):
    """删除基线"""
    deleted = await PerformanceBaseline.filter(id=baseline_id).delete()
    if not deleted:
        raise HTTPException(status_code=404, detail="基线不存在")
    return {"message": "基线删除成功"}


@router.post("/baselines/ai-compare")
async def ai_compare_baselines_api(
    data: BaselineCompareRequest,
    current_user: User = Depends(get_current_user)
):
    """AI对比两个基线"""
    baseline_a = await PerformanceBaseline.get_or_none(id=data.baseline_id_a)
    baseline_b = await PerformanceBaseline.get_or_none(id=data.baseline_id_b)
    if not baseline_a or not baseline_b:
        raise HTTPException(status_code=404, detail="基线不存在")

    result = await ai_compare_baselines(
        baseline_a={
            "name": baseline_a.name, "version": baseline_a.version,
            "baseline_metrics": baseline_a.baseline_metrics,
        },
        baseline_b={
            "name": baseline_b.name, "version": baseline_b.version,
            "baseline_metrics": baseline_b.baseline_metrics,
        }
    )

    # 保存分析结果到较新的基线
    await PerformanceBaseline.filter(id=baseline_b.id).update(
        ai_comparison=json.dumps(result, ensure_ascii=False)
    )

    return {"comparison": result}
