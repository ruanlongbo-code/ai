"""
UI测试模块API路由
"""
from fastapi import APIRouter, HTTPException, Depends, status, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from typing import Optional
import logging
import json
import os
import traceback
import asyncio
from datetime import datetime

from .models import UiTestPage, UiTestCase, UiTestStep, UiTestExecution, UiTestStepResult
from .schemas import (
    UiPageCreateRequest, UiPageUpdateRequest, UiPageResponse,
    UiCaseCreateRequest, UiCaseUpdateRequest, UiCaseResponse, UiStepResponse,
    UiExecutionResponse, UiExecutionListResponse, UiStepResultResponse,
    UiTestReportResponse, UiReportStepDetail,
    UiReportListItem, UiReportListResponse,
)
from service.user.models import User
from service.project.models import Project
from utils.permissions import verify_admin_or_project_member, verify_admin_or_project_editor

logger = logging.getLogger(__name__)
router = APIRouter()


# ======================== 页面管理 ========================

@router.get("/{project_id}/pages", summary="获取页面列表")
async def get_page_list(
    project_id: int,
    project_user: tuple[Project, User] = Depends(verify_admin_or_project_member)
):
    project, _ = project_user
    pages = await UiTestPage.filter(project_id=project_id).order_by("-created_at").all()
    return {
        "pages": [
            UiPageResponse(
                id=p.id, project_id=p.project_id, name=p.name, url=p.url,
                description=p.description, creator_id=p.creator_id,
                created_at=p.created_at, updated_at=p.updated_at,
            ) for p in pages
        ],
        "total": len(pages),
    }


@router.post("/{project_id}/pages", response_model=UiPageResponse, summary="创建页面")
async def create_page(
    project_id: int,
    request: UiPageCreateRequest,
    project_user: tuple[Project, User] = Depends(verify_admin_or_project_editor)
):
    _, current_user = project_user
    page = await UiTestPage.create(
        project_id=project_id, name=request.name, url=request.url,
        description=request.description, creator_id=current_user.id,
    )
    return UiPageResponse(
        id=page.id, project_id=page.project_id, name=page.name, url=page.url,
        description=page.description, creator_id=page.creator_id,
        created_at=page.created_at, updated_at=page.updated_at,
    )


@router.put("/{project_id}/pages/{page_id}", response_model=UiPageResponse, summary="更新页面")
async def update_page(
    project_id: int, page_id: int,
    request: UiPageUpdateRequest,
    project_user: tuple[Project, User] = Depends(verify_admin_or_project_editor)
):
    page = await UiTestPage.get_or_none(id=page_id, project_id=project_id)
    if not page:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="页面不存在")
    update_data = request.dict(exclude_unset=True)
    if update_data:
        for k, v in update_data.items():
            setattr(page, k, v)
        await page.save()
    return UiPageResponse(
        id=page.id, project_id=page.project_id, name=page.name, url=page.url,
        description=page.description, creator_id=page.creator_id,
        created_at=page.created_at, updated_at=page.updated_at,
    )


@router.delete("/{project_id}/pages/{page_id}", summary="删除页面")
async def delete_page(
    project_id: int, page_id: int,
    project_user: tuple[Project, User] = Depends(verify_admin_or_project_editor)
):
    page = await UiTestPage.get_or_none(id=page_id, project_id=project_id)
    if not page:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="页面不存在")
    await page.delete()
    return {"message": "删除成功"}


# ======================== 用例管理 ========================

async def _build_case_response(case: UiTestCase) -> UiCaseResponse:
    """构建用例响应，包含步骤和页面信息"""
    steps = await UiTestStep.filter(case_id=case.id).order_by("sort_order").all()
    page_name, page_url = None, None
    if case.page_id:
        page = await UiTestPage.get_or_none(id=case.page_id)
        if page:
            page_name = page.name
            page_url = page.url
    return UiCaseResponse(
        id=case.id, project_id=case.project_id, page_id=case.page_id,
        page_name=page_name, page_url=page_url,
        name=case.name, priority=case.priority, preconditions=case.preconditions,
        status=case.status, last_run_at=case.last_run_at,
        creator_id=case.creator_id, created_at=case.created_at, updated_at=case.updated_at,
        steps=[
            UiStepResponse(
                id=s.id, case_id=s.case_id, sort_order=s.sort_order,
                action=s.action, input_data=s.input_data,
                expected_result=s.expected_result,
                assertion_type=s.assertion_type,
                assertion_target=s.assertion_target,
                assertion_value=s.assertion_value,
            )
            for s in steps
        ],
    )


@router.get("/{project_id}/cases", summary="获取用例列表")
async def get_case_list(
    project_id: int,
    page_id: Optional[int] = Query(None),
    keyword: Optional[str] = Query(None),
    project_user: tuple[Project, User] = Depends(verify_admin_or_project_member)
):
    filters = {"project_id": project_id}
    if page_id is not None:
        filters["page_id"] = page_id

    query = UiTestCase.filter(**filters)
    if keyword:
        query = query.filter(name__icontains=keyword)

    cases = await query.order_by("-created_at").all()
    result = []
    for c in cases:
        result.append(await _build_case_response(c))
    return {"cases": result, "total": len(result)}


@router.get("/{project_id}/cases/{case_id}", response_model=UiCaseResponse, summary="获取用例详情")
async def get_case_detail(
    project_id: int, case_id: int,
    project_user: tuple[Project, User] = Depends(verify_admin_or_project_member)
):
    case = await UiTestCase.get_or_none(id=case_id, project_id=project_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用例不存在")
    return await _build_case_response(case)


@router.post("/{project_id}/cases", response_model=UiCaseResponse, summary="创建用例")
async def create_case(
    project_id: int,
    request: UiCaseCreateRequest,
    project_user: tuple[Project, User] = Depends(verify_admin_or_project_editor)
):
    _, current_user = project_user
    case = await UiTestCase.create(
        project_id=project_id, page_id=request.page_id, name=request.name,
        priority=request.priority, preconditions=request.preconditions,
        creator_id=current_user.id,
    )
    for step_req in request.steps:
        await UiTestStep.create(
            case_id=case.id, sort_order=step_req.sort_order,
            action=step_req.action, input_data=step_req.input_data,
            expected_result=step_req.expected_result,
            assertion_type=step_req.assertion_type,
            assertion_target=step_req.assertion_target,
            assertion_value=step_req.assertion_value,
        )
    return await _build_case_response(case)


@router.put("/{project_id}/cases/{case_id}", response_model=UiCaseResponse, summary="更新用例")
async def update_case(
    project_id: int, case_id: int,
    request: UiCaseUpdateRequest,
    project_user: tuple[Project, User] = Depends(verify_admin_or_project_editor)
):
    case = await UiTestCase.get_or_none(id=case_id, project_id=project_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用例不存在")

    update_data = request.dict(exclude_unset=True, exclude={"steps"})
    for k, v in update_data.items():
        setattr(case, k, v)
    await case.save()

    if request.steps is not None:
        await UiTestStep.filter(case_id=case.id).delete()
        for step_req in request.steps:
            await UiTestStep.create(
                case_id=case.id, sort_order=step_req.sort_order,
                action=step_req.action, input_data=step_req.input_data,
                expected_result=step_req.expected_result,
                assertion_type=step_req.assertion_type,
                assertion_target=step_req.assertion_target,
                assertion_value=step_req.assertion_value,
            )

    return await _build_case_response(case)


@router.delete("/{project_id}/cases/{case_id}", summary="删除用例")
async def delete_case(
    project_id: int, case_id: int,
    project_user: tuple[Project, User] = Depends(verify_admin_or_project_editor)
):
    case = await UiTestCase.get_or_none(id=case_id, project_id=project_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用例不存在")
    step_ids = await UiTestStep.filter(case_id=case.id).values_list("id", flat=True)
    if step_ids:
        await UiTestStepResult.filter(step_id__in=step_ids).delete()
    await UiTestStep.filter(case_id=case.id).delete()
    await UiTestExecution.filter(case_id=case.id).delete()
    await case.delete()
    return {"message": "删除成功"}


# ======================== 执行管理 ========================

@router.post("/{project_id}/cases/{case_id}/execute", summary="AI执行UI测试用例（SSE流式）")
async def execute_case(
    project_id: int, case_id: int,
    project_user: tuple[Project, User] = Depends(verify_admin_or_project_editor)
):
    """AI驱动的UI测试执行，通过SSE实时推送执行进度和截图"""
    _, current_user = project_user

    case = await UiTestCase.get_or_none(id=case_id, project_id=project_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用例不存在")

    if not case.page_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用例未关联页面，无法执行")

    page = await UiTestPage.get_or_none(id=case.page_id)
    if not page:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="关联页面不存在")

    steps = await UiTestStep.filter(case_id=case.id).order_by("sort_order").all()
    if not steps:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用例没有测试步骤")

    execution = await UiTestExecution.create(
        case_id=case.id, project_id=project_id, status="running",
        total_steps=len(steps), start_time=datetime.now(),
        executor_id=current_user.id,
    )

    step_data_list = [
        {
            "id": s.id, "sort_order": s.sort_order, "action": s.action,
            "input_data": s.input_data, "expected_result": s.expected_result,
            "assertion_type": s.assertion_type,
            "assertion_target": s.assertion_target,
            "assertion_value": s.assertion_value,
        }
        for s in steps
    ]

    async def generate():
        from .executor import UiTestExecutor

        executor = UiTestExecutor()
        passed_count = 0
        failed_count = 0
        exec_start = datetime.now()

        try:
            await executor.start(headless=True)

            yield f"data: {json.dumps({'type': 'execution_start', 'execution_id': execution.id, 'total_steps': len(steps)}, ensure_ascii=False)}\n\n"

            async for event in executor.run_case(page.url, step_data_list, case.preconditions):
                event_type = event.get("type")

                if event_type == "init":
                    screenshot_name = event['screenshot']
                    init_data = {
                        'type': 'init',
                        'screenshot': screenshot_name,
                        'screenshot_url': f'/screenshots/{screenshot_name}',
                        'url': event['url'],
                    }
                    yield f"data: {json.dumps(init_data, ensure_ascii=False)}\n\n"

                elif event_type == "step_start":
                    yield f"data: {json.dumps({'type': 'step_start', 'step_id': event['step_id'], 'sort_order': event['sort_order']}, ensure_ascii=False)}\n\n"

                elif event_type == "ai_thinking":
                    yield f"data: {json.dumps({'type': 'ai_thinking', 'step_id': event['step_id'], 'action': event.get('action', ''), 'description': event.get('description', '')}, ensure_ascii=False)}\n\n"

                elif event_type == "step_done":
                    step_status = event.get("status", "failed")
                    if step_status == "passed":
                        passed_count += 1
                    else:
                        failed_count += 1

                    screenshot_path = event.get("screenshot")
                    await UiTestStepResult.create(
                        execution_id=execution.id,
                        step_id=event["step_id"],
                        sort_order=event.get("sort_order", 0),
                        status=step_status,
                        screenshot_path=screenshot_path,
                        ai_action=event.get("ai_action"),
                        actual_result=event.get("actual_result"),
                        error_message=event.get("error_message"),
                        duration_ms=event.get("duration_ms"),
                        assertion_type=event.get("assertion_type"),
                        assertion_passed=event.get("assertion_passed"),
                        assertion_detail=event.get("assertion_detail"),
                    )

                    sse_data = {
                        "type": "step_done",
                        "step_id": event["step_id"],
                        "status": step_status,
                        "screenshot": screenshot_path,
                        "screenshot_url": f"/screenshots/{screenshot_path}" if screenshot_path else None,
                        "ai_action": event.get("ai_action"),
                        "actual_result": event.get("actual_result"),
                        "error_message": event.get("error_message"),
                        "duration_ms": event.get("duration_ms"),
                        "assertion_type": event.get("assertion_type"),
                        "assertion_passed": event.get("assertion_passed"),
                        "assertion_detail": event.get("assertion_detail"),
                    }
                    yield f"data: {json.dumps(sse_data, ensure_ascii=False)}\n\n"

                elif event_type == "error":
                    yield f"data: {json.dumps({'type': 'error', 'message': event.get('message', '')}, ensure_ascii=False)}\n\n"

                elif event_type == "done":
                    pass

            final_status = "passed" if failed_count == 0 else "failed"
            exec_end = datetime.now()
            total_duration = int((exec_end - exec_start).total_seconds() * 1000)

            execution.status = final_status
            execution.passed_steps = passed_count
            execution.failed_steps = failed_count
            execution.end_time = exec_end
            execution.duration_ms = total_duration
            await execution.save()

            case.status = final_status
            case.last_run_at = datetime.now()
            await case.save()

            yield f"data: {json.dumps({'type': 'execution_done', 'status': final_status, 'passed': passed_count, 'failed': failed_count, 'duration_ms': total_duration}, ensure_ascii=False)}\n\n"

        except Exception as e:
            logger.error(f"UI测试执行异常: {e}\n{traceback.format_exc()}")
            execution.status = "error"
            execution.error_message = str(e)[:1000]
            execution.end_time = datetime.now()
            await execution.save()
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

        finally:
            await executor.close()

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@router.get("/{project_id}/executions", summary="获取执行记录列表")
async def get_execution_list(
    project_id: int,
    case_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    project_user: tuple[Project, User] = Depends(verify_admin_or_project_member)
):
    filters = {"project_id": project_id}
    if case_id is not None:
        filters["case_id"] = case_id

    total = await UiTestExecution.filter(**filters).count()
    offset = (page - 1) * page_size
    executions = await UiTestExecution.filter(**filters).order_by("-created_at").offset(offset).limit(page_size).all()

    result = []
    for ex in executions:
        case = await UiTestCase.get_or_none(id=ex.case_id)
        result.append(UiExecutionResponse(
            id=ex.id, case_id=ex.case_id, project_id=ex.project_id,
            case_name=case.name if case else None,
            status=ex.status, total_steps=ex.total_steps,
            passed_steps=ex.passed_steps, failed_steps=ex.failed_steps,
            start_time=ex.start_time, end_time=ex.end_time,
            duration_ms=ex.duration_ms,
            error_message=ex.error_message, executor_id=ex.executor_id,
            created_at=ex.created_at,
        ))
    return UiExecutionListResponse(executions=result, total=total)


@router.get("/{project_id}/executions/{execution_id}", summary="获取执行详情（含步骤结果）")
async def get_execution_detail(
    project_id: int, execution_id: int,
    project_user: tuple[Project, User] = Depends(verify_admin_or_project_member)
):
    execution = await UiTestExecution.get_or_none(id=execution_id, project_id=project_id)
    if not execution:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="执行记录不存在")

    case = await UiTestCase.get_or_none(id=execution.case_id)
    step_results = await UiTestStepResult.filter(execution_id=execution.id).order_by("sort_order").all()

    return UiExecutionResponse(
        id=execution.id, case_id=execution.case_id, project_id=execution.project_id,
        case_name=case.name if case else None,
        status=execution.status, total_steps=execution.total_steps,
        passed_steps=execution.passed_steps, failed_steps=execution.failed_steps,
        start_time=execution.start_time, end_time=execution.end_time,
        duration_ms=execution.duration_ms,
        error_message=execution.error_message, executor_id=execution.executor_id,
        created_at=execution.created_at,
        step_results=[
            UiStepResultResponse(
                id=sr.id, execution_id=sr.execution_id, step_id=sr.step_id,
                sort_order=sr.sort_order, status=sr.status,
                screenshot_url=f"/screenshots/{sr.screenshot_path}" if sr.screenshot_path else None,
                ai_action=sr.ai_action, actual_result=sr.actual_result,
                error_message=sr.error_message, duration_ms=sr.duration_ms,
                assertion_type=sr.assertion_type,
                assertion_passed=sr.assertion_passed,
                assertion_detail=sr.assertion_detail,
            )
            for sr in step_results
        ],
    )


# ======================== 测试报告 ========================

@router.get("/{project_id}/reports", summary="获取测试报告列表")
async def get_report_list(
    project_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    project_user: tuple[Project, User] = Depends(verify_admin_or_project_member)
):
    """获取已完成的UI测试执行报告列表"""
    filters = {"project_id": project_id, "status__in": ["passed", "failed"]}
    if status_filter:
        filters = {"project_id": project_id, "status": status_filter}

    total = await UiTestExecution.filter(**filters).count()
    offset = (page - 1) * page_size
    executions = await UiTestExecution.filter(**filters).order_by("-created_at").offset(offset).limit(page_size).all()

    result = []
    for ex in executions:
        case = await UiTestCase.get_or_none(id=ex.case_id)
        page_name = None
        if case and case.page_id:
            pg = await UiTestPage.get_or_none(id=case.page_id)
            if pg:
                page_name = pg.name

        # 获取执行者名
        executor_name = None
        try:
            executor_user = await User.get_or_none(id=ex.executor_id)
            if executor_user:
                executor_name = executor_user.username
        except Exception:
            pass

        pass_rate = round(ex.passed_steps / ex.total_steps * 100, 1) if ex.total_steps > 0 else 0

        # 断言统计
        step_results = await UiTestStepResult.filter(execution_id=ex.id).all()
        total_assertions = sum(1 for sr in step_results if sr.assertion_type)
        passed_assertions = sum(1 for sr in step_results if sr.assertion_type and sr.assertion_passed)

        result.append(UiReportListItem(
            execution_id=ex.id,
            case_id=ex.case_id,
            case_name=case.name if case else None,
            page_name=page_name,
            status=ex.status,
            total_steps=ex.total_steps,
            passed_steps=ex.passed_steps,
            failed_steps=ex.failed_steps,
            pass_rate=pass_rate,
            duration_ms=ex.duration_ms,
            executor_name=executor_name,
            start_time=ex.start_time,
            end_time=ex.end_time,
            created_at=ex.created_at,
            total_assertions=total_assertions,
            passed_assertions=passed_assertions,
            failed_assertions=total_assertions - passed_assertions,
        ))

    return UiReportListResponse(reports=result, total=total)


@router.get("/{project_id}/executions/{execution_id}/report", summary="获取测试报告")
async def get_test_report(
    project_id: int, execution_id: int,
    project_user: tuple[Project, User] = Depends(verify_admin_or_project_member)
):
    """生成并返回UI测试执行的详细报告"""
    execution = await UiTestExecution.get_or_none(id=execution_id, project_id=project_id)
    if not execution:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="执行记录不存在")

    case = await UiTestCase.get_or_none(id=execution.case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用例不存在")

    # 获取页面信息
    page_name, page_url = None, None
    if case.page_id:
        page = await UiTestPage.get_or_none(id=case.page_id)
        if page:
            page_name = page.name
            page_url = page.url

    # 获取步骤信息
    steps = await UiTestStep.filter(case_id=case.id).order_by("sort_order").all()
    step_map = {s.id: s for s in steps}

    # 获取步骤结果
    step_results = await UiTestStepResult.filter(execution_id=execution.id).order_by("sort_order").all()

    # 计算统计信息
    total_duration = sum(sr.duration_ms or 0 for sr in step_results)
    avg_duration = total_duration // len(step_results) if step_results else 0

    # 断言统计
    total_assertions = sum(1 for sr in step_results if sr.assertion_type)
    passed_assertions = sum(1 for sr in step_results if sr.assertion_type and sr.assertion_passed)
    failed_assertions = total_assertions - passed_assertions

    # 获取执行者信息
    executor_name = None
    try:
        executor_user = await User.get_or_none(id=execution.executor_id)
        if executor_user:
            executor_name = executor_user.username
    except Exception:
        pass

    # 构建步骤详情
    report_steps = []
    for sr in step_results:
        step_info = step_map.get(sr.step_id)
        report_steps.append(UiReportStepDetail(
            sort_order=sr.sort_order,
            action=step_info.action if step_info else "未知步骤",
            input_data=step_info.input_data if step_info else None,
            expected_result=step_info.expected_result if step_info else None,
            status=sr.status,
            actual_result=sr.actual_result,
            error_message=sr.error_message,
            screenshot_url=f"/screenshots/{sr.screenshot_path}" if sr.screenshot_path else None,
            ai_action=sr.ai_action,
            duration_ms=sr.duration_ms,
            assertion_type=sr.assertion_type,
            assertion_passed=sr.assertion_passed,
            assertion_detail=sr.assertion_detail,
        ))

    pass_rate = round(execution.passed_steps / execution.total_steps * 100, 1) if execution.total_steps > 0 else 0

    return UiTestReportResponse(
        execution_id=execution.id,
        case_id=case.id,
        case_name=case.name,
        page_name=page_name,
        page_url=page_url,
        priority=case.priority,
        preconditions=case.preconditions,
        status=execution.status,
        total_steps=execution.total_steps,
        passed_steps=execution.passed_steps,
        failed_steps=execution.failed_steps,
        pass_rate=pass_rate,
        total_duration_ms=execution.duration_ms or total_duration,
        avg_step_duration_ms=avg_duration,
        total_assertions=total_assertions,
        passed_assertions=passed_assertions,
        failed_assertions=failed_assertions,
        start_time=execution.start_time,
        end_time=execution.end_time,
        executor_name=executor_name,
        steps=report_steps,
    )


# ======================== WebSocket 实时浏览器执行 ========================

@router.websocket("/{project_id}/cases/{case_id}/ws-execute")
async def ws_execute_case(websocket: WebSocket, project_id: int, case_id: int):
    """
    WebSocket 端点：AI 执行 UI 测试用例 + CDP Screencast 实时浏览器画面推流。
    """
    await websocket.accept()

    token = websocket.query_params.get("token", "")
    user = None
    if token:
        try:
            from utils.auth import AuthUtils
            import jwt as pyjwt
            payload = pyjwt.decode(
                token,
                os.getenv("SECRET_KEY", "ai-test-secret-key"),
                algorithms=[os.getenv("ALGORITHM", "HS256")],
            )
            if payload.get("type") == "access":
                user_id = payload.get("sub")
                if user_id:
                    user = await User.get_or_none(id=int(user_id))
        except Exception as e:
            logger.warning(f"WebSocket auth failed: {e}")

    if not user:
        await websocket.send_json({"type": "error", "message": "认证失败，请重新登录"})
        await websocket.close(code=4001, reason="Unauthorized")
        return

    case = await UiTestCase.get_or_none(id=case_id, project_id=project_id)
    if not case or not case.page_id:
        await websocket.send_json({"type": "error", "message": "用例不存在或未关联页面"})
        await websocket.close()
        return

    page = await UiTestPage.get_or_none(id=case.page_id)
    if not page:
        await websocket.send_json({"type": "error", "message": "关联页面不存在"})
        await websocket.close()
        return

    steps = await UiTestStep.filter(case_id=case.id).order_by("sort_order").all()
    if not steps:
        await websocket.send_json({"type": "error", "message": "用例没有测试步骤"})
        await websocket.close()
        return

    execution = await UiTestExecution.create(
        case_id=case.id, project_id=project_id, status="running",
        total_steps=len(steps), start_time=datetime.now(), executor_id=user.id,
    )

    step_data_list = [
        {
            "id": s.id, "sort_order": s.sort_order, "action": s.action,
            "input_data": s.input_data, "expected_result": s.expected_result,
            "assertion_type": s.assertion_type,
            "assertion_target": s.assertion_target,
            "assertion_value": s.assertion_value,
        }
        for s in steps
    ]

    from .executor import UiTestExecutor
    executor = UiTestExecutor()
    ws_closed = False
    exec_start = datetime.now()

    try:
        await executor.start(headless=True)

        await websocket.send_json({
            "type": "execution_start",
            "execution_id": execution.id,
            "total_steps": len(steps),
            "page_url": page.url,
        })

        async def send_frame(base64_jpeg: str):
            nonlocal ws_closed
            if ws_closed:
                return
            try:
                await websocket.send_json({"type": "frame", "data": base64_jpeg})
            except Exception:
                ws_closed = True

        await executor.start_screencast(send_frame)

        async def send_message(event: dict):
            nonlocal ws_closed
            if ws_closed:
                return
            try:
                await websocket.send_json(event)
            except Exception:
                ws_closed = True

            if event.get("type") == "step_done":
                await UiTestStepResult.create(
                    execution_id=execution.id,
                    step_id=event["step_id"],
                    sort_order=event.get("sort_order", 0),
                    status=event.get("status", "failed"),
                    screenshot_path=event.get("screenshot"),
                    ai_action=event.get("ai_action"),
                    actual_result=event.get("actual_result"),
                    error_message=event.get("error_message"),
                    duration_ms=event.get("duration_ms"),
                    assertion_type=event.get("assertion_type"),
                    assertion_passed=event.get("assertion_passed"),
                    assertion_detail=event.get("assertion_detail"),
                )

        result = await executor.run_case_live(page.url, step_data_list, send_message)

        exec_end = datetime.now()
        total_duration = int((exec_end - exec_start).total_seconds() * 1000)

        execution.status = result["status"]
        execution.passed_steps = result["passed"]
        execution.failed_steps = result["failed"]
        execution.end_time = exec_end
        execution.duration_ms = total_duration
        await execution.save()

        case.status = result["status"]
        case.last_run_at = datetime.now()
        await case.save()

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected during execution {execution.id}")
        ws_closed = True
    except Exception as e:
        logger.error(f"WebSocket execution error: {e}\n{traceback.format_exc()}")
        execution.status = "error"
        execution.error_message = str(e)[:1000]
        execution.end_time = datetime.now()
        await execution.save()
        if not ws_closed:
            try:
                await websocket.send_json({"type": "error", "message": str(e)})
            except Exception:
                pass
    finally:
        await executor.close()
        if not ws_closed:
            try:
                await websocket.close()
            except Exception:
                pass
