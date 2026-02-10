"""
测试执行模块API路由
"""
from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks, Query
from typing import Tuple, Optional
from decimal import Decimal
from datetime import datetime
from service.user.models import User
from service.project.models import Project
from utils.permissions import verify_admin_or_project_member
from service.api_test.models import ApiTestCase
from service.test_environment.models import TestEnvironment, TestEnvironmentConfig, TestEnvironmentDb
from .models import ApiCaseRun, TestSuiteRun
from .schemas import RunSingleTestCaseRequest, RunSingleTestCaseResponse, RunTestSuiteRequest, RunTestSuiteResponse, \
    TestSuiteSummary, RunTestTaskRequest, RunTestTaskResponse, TestTaskSummary, RunTestTaskBackgroundRequest, \
    RunTestTaskBackgroundResponse, TaskStatusQueryResponse, ApiCaseRunDetailResponse, ApiCaseRunListResponse, \
    TestSuiteRunListResponse, TestSuiteRunDetailResponse, TestTaskRunListResponse, TestTaskRunDetailResponse
from api_case_run.execute import TestExecutor
from ..test_management.models import SuiteCaseRelation, TestSuite, TestTask, TaskSuiteRelation
from .models import TestTaskRun

router = APIRouter()


@router.post("/{project_id}/cases/run", response_model=RunSingleTestCaseResponse, summary="运行单条测试用例")
async def run_single_test_case(
        project_id: int,
        request_data: RunSingleTestCaseRequest,
        project_and_user: Tuple[Project, User] = Depends(verify_admin_or_project_member)
):
    """
    运行单条测试用例接口
    
    权限要求：
    - 只有项目成员和管理员可以访问该接口
    
    参数：
    - project_id: 项目ID
    - request_data: 运行测试用例请求数据
    
    返回：
    - 测试用例执行结果
    """
    try:
        project, current_user = project_and_user

        # 1. 参数校验 - 查询测试用例是否存在且属于该项目
        test_case = await ApiTestCase.get_or_none(
            id=request_data.case_id,

        )
        if not test_case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="测试用例不存在或不属于该项目"
            )

        # 2. 参数校验 - 查询测试环境是否存在且属于该项目
        test_environment = await TestEnvironment.get_or_none(
            id=request_data.environment_id,
            project_id=project_id
        )
        if not test_environment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="测试环境不存在或不属于该项目"
            )

        # 3. 查询测试环境的全局变量配置
        env_configs = await TestEnvironmentConfig.filter(
            environment_id=request_data.environment_id
        ).all()

        # 构建全局变量字典
        test_env_global = {}
        for config in env_configs:
            test_env_global[config.name] = config.value

        # 添加全局函数
        if test_environment.func_global:
            test_env_global['func_global'] = test_environment.func_global

        # 4. 查询测试环境的数据库配置
        db_configs = await TestEnvironmentDb.filter(
            environment_id=request_data.environment_id
        ).all()

        # 构建数据库配置列表
        db_config_list = []
        for db_config in db_configs:
            db_config_list.append({
                "name": db_config.name,
                "type": db_config.type,
                "config": db_config.config
            })

        # 5. 构建用例数据
        case_data = {
            "id": test_case.id,
            "name": test_case.name,
            "description": test_case.description,
            "request": test_case.request,
            "assertions": test_case.assertions,
            "skip": False,  # 单条用例执行不跳过
            # 前置条件
            "preconditions": test_case.preconditions
        }

        # 6. 调用execute_test_case方法执行用例
        executor = TestExecutor(test_env_global=test_env_global, db_config=db_config_list)
        result = executor.execute_test_case(case_data)

        # 7. 保存执行结果到ApiCaseRun表
        case_run = await ApiCaseRun.create(
            api_case_id=test_case.id,
            case_name=test_case.name,
            environment_id=request_data.environment_id,
            status=result.status,
            start_time=datetime.fromtimestamp(result.start_time) if result.start_time else None,
            end_time=datetime.fromtimestamp(result.end_time) if result.end_time else None,
            duration=Decimal(str(result.duration)) if result.duration else None,
            error_message=result.error_message,
            logs=result.logs,
            response_data=result.api_requests_info,
            request_data=case_data.get('request', {})
        )

        # 8. 返回执行结果
        return RunSingleTestCaseResponse(
            case_run_id=case_run.id,
            case_id=test_case.id,
            case_name=test_case.name,
            status=result.status,
            duration=Decimal(str(result.duration)) if result.duration else None,
            start_time=datetime.fromtimestamp(result.start_time) if result.start_time else None,
            end_time=datetime.fromtimestamp(result.end_time) if result.end_time else None,
            error_message=result.error_message,
            logs=result.logs,
            request_info=result.api_requests_info,

        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"执行测试用例时发生错误: {str(e)}"
        )


@router.post("/{project_id}/suites/run", response_model=RunTestSuiteResponse, summary="运行测试套件")
async def run_test_suite(
        project_id: int,
        request_data: RunTestSuiteRequest,
        project_and_user: Tuple[Project, User] = Depends(verify_admin_or_project_member)
):
    """
    运行测试套件接口

    权限要求：
    - 只有项目成员和管理员可以访问该接口

    参数：
    - project_id: 项目ID
    - request_data: 运行测试套件请求数据

    返回：
    - 测试套件执行结果
    """
    try:
        project, current_user = project_and_user

        # 1. 参数校验 - 查询测试套件是否存在且属于该项目
        test_suite = await TestSuite.get_or_none(
            id=request_data.suite_id,
            project_id=project_id
        )
        if not test_suite:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="测试套件不存在或不属于该项目"
            )

        # 2. 参数校验 - 查询测试环境是否存在且属于该项目
        test_environment = await TestEnvironment.get_or_none(
            id=request_data.environment_id,
            project_id=project_id
        )
        if not test_environment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="测试环境不存在或不属于该项目"
            )

        # 3. 查询测试环境的全局变量配置
        env_configs = await TestEnvironmentConfig.filter(
            environment_id=request_data.environment_id
        ).all()

        # 构建全局变量字典
        test_env_global = {}
        for config in env_configs:
            test_env_global[config.name] = config.value

        # 添加全局函数
        if test_environment.func_global:
            test_env_global['func_global'] = test_environment.func_global

        # 4. 查询测试环境的数据库配置
        db_configs = await TestEnvironmentDb.filter(
            environment_id=request_data.environment_id
        ).all()

        # 构建数据库配置列表
        db_config_list = []
        for db_config in db_configs:
            db_config_list.append({
                "name": db_config.name,
                "type": db_config.type,
                "config": db_config.config
            })

        # 5. 查询测试套件中的所有用例，并按执行顺序排序
        suite_case_relations = await SuiteCaseRelation.filter(
            suite_id=request_data.suite_id
        ).prefetch_related('case').order_by('case_order')

        if not suite_case_relations:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="测试套件中没有用例"
            )

        # 6. 构建套件数据
        cases_list = []
        for relation in suite_case_relations:
            case = relation.case
            case_data = {
                "id": case.id,
                "name": case.name,
                "description": case.description,
                "preconditions": case.preconditions,
                "request": case.request,
                "assertions": case.assertions,
                "skip": False
            }
            cases_list.append(case_data)

        suite_data = {
            "id": test_suite.id,
            "name": test_suite.suite_name,
            "cases_list": cases_list
        }

        # 7. 调用execute_test_suite方法执行套件
        executor = TestExecutor(test_env_global=test_env_global, db_config=db_config_list)
        execution_result = executor.execute_test_suite(suite_data)

        # 8. 保存执行结果到TestSuiteRun表
        start_time = datetime.now()
        end_time = datetime.now()

        # 计算套件执行状态
        summary = execution_result.get('summary', {})
        if summary.get('error', 0) > 0:
            suite_status = 'error'
        elif summary.get('failed', 0) > 0:
            suite_status = 'failed'
        else:
            suite_status = 'success'

        suite_run = await TestSuiteRun.create(
            suite_id=test_suite.id,
            status=suite_status,
            start_time=start_time,
            end_time=end_time,
            duration=Decimal(str(summary.get('duration', 0))),
            error_message=None,
            total_cases=summary.get('total', 0),
            passed_cases=summary.get('passed', 0),
            failed_cases=summary.get('failed', 0),
            skipped_cases=summary.get('skipped', 0),
            error_cases=summary.get('error', 0),
        )

        # 9. 保存每个用例的执行结果到ApiCaseRun表
        results = execution_result.get('results', [])
        for result in results:
            await ApiCaseRun.create(
                api_case_id=result.case_id,
                suite_run_id=suite_run.id,
                case_name=result.case_name,
                status=result.status,
                start_time=datetime.fromtimestamp(result.start_time) if result.start_time else None,
                end_time=datetime.fromtimestamp(result.end_time) if result.end_time else None,
                duration=Decimal(str(result.duration)) if result.duration else None,
                error_message=result.error_message,
                logs=result.logs,
                api_requests_info=getattr(result, 'api_requests_info', None),
                traceback=result.traceback
            )

        # 10. 返回执行结果
        return RunTestSuiteResponse(
            run_id=suite_run.id,
            suite_id=test_suite.id,
            environment_id=request_data.environment_id,
            status=suite_status,
            duration=float(summary.get('duration', 0)),
            error_message=None,
            start_time=start_time,
            end_time=end_time,
            summary=TestSuiteSummary(
                total=summary.get('total', 0),
                success=summary.get('success', 0),
                failed=summary.get('failed', 0),
                error=summary.get('error', 0),
                skip=summary.get('skip', 0),
                duration=summary.get('duration', 0)
            )
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"执行测试套件时发生错误: {str(e)}"
        )


@router.post("/{project_id}/tasks/run", response_model=RunTestTaskResponse, summary="运行测试任务")
async def run_test_task(
        project_id: int,
        request_data: RunTestTaskRequest,
        project_and_user: Tuple[Project, User] = Depends(verify_admin_or_project_member)
):
    """
    运行测试任务接口
    
    权限要求：
    - 只有项目成员和管理员可以访问该接口
    
    参数：
    - project_id: 项目ID
    - request_data: 运行测试任务请求数据
    
    返回：
    - 测试任务执行结果
    """
    try:
        project, current_user = project_and_user

        # 1. 参数校验 - 查询测试任务是否存在且属于该项目
        test_task = await TestTask.get_or_none(
            id=request_data.task_id,
            project_id=project_id
        )
        if not test_task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="测试任务不存在或不属于该项目"
            )

        # 2. 参数校验 - 查询测试环境是否存在且属于该项目
        test_environment = await TestEnvironment.get_or_none(
            id=request_data.environment_id,
            project_id=project_id
        )
        if not test_environment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="测试环境不存在或不属于该项目"
            )

        # 3. 查询测试环境的全局变量配置
        env_configs = await TestEnvironmentConfig.filter(
            environment_id=request_data.environment_id
        ).all()

        # 构建全局变量字典
        test_env_global = {}
        for config in env_configs:
            test_env_global[config.name] = config.value

        # 添加全局函数
        if test_environment.func_global:
            test_env_global['func_global'] = test_environment.func_global

        # 4. 查询测试环境的数据库配置
        db_configs = await TestEnvironmentDb.filter(
            environment_id=request_data.environment_id
        ).all()

        # 构建数据库配置列表
        db_config_list = []
        for db_config in db_configs:
            db_config_list.append({
                "name": db_config.name,
                "type": db_config.type,
                "config": db_config.config
            })

        # 5. 查询测试任务中的所有套件（按执行顺序排序）
        task_suite_relations = await TaskSuiteRelation.filter(
            task_id=test_task.id
        ).prefetch_related('suite').order_by('suite_order')

        if not task_suite_relations:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="测试任务中没有包含任何测试套件"
            )

        # 6. 构建任务数据，包含所有套件和用例
        suites_list = []
        for relation in task_suite_relations:
            suite = relation.suite

            # 查询套件中的所有用例（按执行顺序排序）
            suite_case_relations = await SuiteCaseRelation.filter(
                suite_id=suite.id
            ).prefetch_related('case').order_by('case_order')

            # 构建用例数据列表
            cases_list = []
            for case_relation in suite_case_relations:
                test_case = case_relation.case
                case_data = {
                    "id": test_case.id,
                    "name": test_case.name,
                    "description": test_case.description,
                    "preconditions": test_case.preconditions,
                    "request": test_case.request,
                    "assertions": test_case.assertions,
                    "skip": False
                }
                cases_list.append(case_data)

            # 构建套件数据
            suite_data = {
                "id": suite.id,
                "name": suite.suite_name,
                "cases_list": cases_list
            }
            suites_list.append(suite_data)

        # 构建任务数据
        task_data = {
            "id": test_task.id,
            "name": test_task.task_name,
            "description": test_task.description,
            "type": test_task.type,
            "suites_list": suites_list
        }

        # 7. 调用execute_test_task方法执行任务
        executor = TestExecutor(test_env_global=test_env_global, db_config=db_config_list)
        execution_result = executor.execute_test_task(task_data)

        # 8. 保存执行结果到TestTaskRun表
        start_time = datetime.now()
        end_time = datetime.now()

        # 计算任务执行状态
        summary = execution_result.get('task_summary', {})
        if summary.get('error_cases', 0) > 0:
            task_status = 'error'
        elif summary.get('failed_cases', 0) > 0:
            task_status = 'failed'
        else:
            task_status = 'success'

        task_run = await TestTaskRun.create(
            task_id=test_task.id,
            status=task_status,
            start_time=start_time,
            end_time=end_time,
            duration=Decimal(str(summary.get('duration', 0))),
            total_suites=summary.get('total_suites', 0),
            total_cases=summary.get('total_cases', 0),
            passed_cases=summary.get('success_cases', 0),
            failed_cases=summary.get('failed_cases', 0),
            skipped_cases=summary.get('skip_cases', 0)
        )

        # 9. 保存每个套件的执行结果到TestSuiteRun表
        suite_results = execution_result.get('suite_results', [])
        for suite_result in suite_results:
            suite_summary = suite_result.get('summary', {})

            # 计算套件执行状态
            if suite_summary.get('error', 0) > 0:
                suite_status = 'error'
            elif suite_summary.get('failed', 0) > 0:
                suite_status = 'failed'
            else:
                suite_status = 'success'

            suite_run = await TestSuiteRun.create(
                suite_id=suite_result.get('suite_id'),
                run_task_id=task_run.id,
                status=suite_status,
                start_time=start_time,
                end_time=end_time,
                duration=Decimal(str(suite_summary.get('duration', 0))),
                total_cases=suite_summary.get('total', 0),
                passed_cases=suite_summary.get('success', 0),
                failed_cases=suite_summary.get('fail', 0),
                skipped_cases=suite_summary.get('skip', 0)
            )

            # 10. 保存每个用例的执行结果到ApiCaseRun表
            case_results = suite_result.get('results', [])
            for result in case_results:
                await ApiCaseRun.create(
                    api_case_id=result.case_id,
                    suite_run_id=suite_run.id,
                    case_name=result.case_name,
                    status=result.status,
                    start_time=datetime.fromtimestamp(result.start_time) if result.start_time else None,
                    end_time=datetime.fromtimestamp(result.end_time) if result.end_time else None,
                    duration=Decimal(str(result.duration)) if result.duration else None,
                    error_message=result.error_message,
                    logs=result.logs,
                    api_requests_info=getattr(result, 'api_requests_info', None),
                    traceback=result.traceback
                )

        # 11. 返回执行结果
        return RunTestTaskResponse(
            task_run_id=task_run.id,
            task_id=test_task.id,
            task_name=test_task.task_name,
            status=task_status,
            duration=float(summary.get('duration', 0)),
            start_time=start_time,
            end_time=end_time,
            error_message=None,
            summary=TestTaskSummary(
                total_suites=summary.get('total_suites', 0),
                total_cases=summary.get('total_cases', 0),
                success_cases=summary.get('success_cases', 0),
                failed_cases=summary.get('failed_cases', 0),
                error_cases=summary.get('error_cases', 0),
                skip_cases=summary.get('skip_cases', 0),
                duration=summary.get('duration', 0)
            )
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"执行测试任务时发生错误: {str(e)}"
        )


async def execute_test_task_background(
        project_id: int,
        task_id: int,
        environment_id: int,
        task_run_id: int
):
    """
    后台执行测试任务的函数
    
    参数：
    - project_id: 项目ID
    - task_id: 测试任务ID
    - environment_id: 测试环境ID
    - task_run_id: 任务执行记录ID
    """
    try:
        # 更新任务状态为运行中
        task_run = await TestTaskRun.get(id=task_run_id)
        task_run.status = 'running'
        task_run.start_time = datetime.now()
        await task_run.save()

        # 1. 查询测试任务
        test_task = await TestTask.get(id=task_id, project_id=project_id)

        # 2. 查询测试环境
        test_environment = await TestEnvironment.get(id=environment_id, project_id=project_id)

        # 3. 查询测试环境的全局变量配置
        env_configs = await TestEnvironmentConfig.filter(environment_id=environment_id).all()

        # 构建全局变量字典
        test_env_global = {}
        for config in env_configs:
            test_env_global[config.name] = config.value

        # 添加全局函数
        if test_environment.func_global:
            test_env_global['func_global'] = test_environment.func_global

        # 4. 查询测试环境的数据库配置
        db_configs = await TestEnvironmentDb.filter(environment_id=environment_id).all()

        # 构建数据库配置列表
        db_config_list = []
        for db_config in db_configs:
            db_config_list.append({
                "name": db_config.name,
                "type": db_config.type,
                "config": db_config.config
            })

        # 5. 查询测试任务中的所有套件（按执行顺序排序）
        task_suite_relations = await TaskSuiteRelation.filter(
            task_id=test_task.id
        ).prefetch_related('suite').order_by('suite_order')

        # 6. 构建任务数据，包含所有套件和用例
        suites_list = []
        for relation in task_suite_relations:
            suite = relation.suite

            # 查询套件中的所有用例（按执行顺序排序）
            suite_case_relations = await SuiteCaseRelation.filter(
                suite_id=suite.id
            ).prefetch_related('case').order_by('case_order')

            # 构建用例数据列表
            cases_list = []
            for case_relation in suite_case_relations:
                test_case = case_relation.case
                case_data = {
                    "id": test_case.id,
                    "name": test_case.name,
                    "description": test_case.description,
                    "preconditions": test_case.preconditions,
                    "request": test_case.request,
                    "assertions": test_case.assertions,
                    "skip": False
                }
                cases_list.append(case_data)

            # 构建套件数据
            suite_data = {
                "id": suite.id,
                "name": suite.suite_name,
                "cases_list": cases_list
            }
            suites_list.append(suite_data)

        # 构建任务数据
        task_data = {
            "id": test_task.id,
            "name": test_task.task_name,
            "description": test_task.description,
            "type": test_task.type,
            "suites_list": suites_list
        }

        # 7. 调用execute_test_task方法执行任务
        executor = TestExecutor(test_env_global=test_env_global, db_config=db_config_list)
        execution_result = executor.execute_test_task(task_data)

        # 8. 更新任务执行结果
        end_time = datetime.now()
        summary = execution_result.get('task_summary', {})

        # 计算任务执行状态
        if summary.get('error_cases', 0) > 0:
            task_status = 'error'
        elif summary.get('failed_cases', 0) > 0:
            task_status = 'failed'
        else:
            task_status = 'completed'

        # 更新任务运行记录
        task_run.status = task_status
        task_run.end_time = end_time
        task_run.duration = (end_time - task_run.start_time).total_seconds()
        task_run.total_suites = summary.get('total_suites', 0)
        task_run.total_cases = summary.get('total_cases', 0)
        task_run.passed_cases = summary.get('success_cases', 0)
        task_run.failed_cases = summary.get('failed_cases', 0)
        task_run.skipped_cases = summary.get('skip_cases', 0)
        await task_run.save()

        # 9. 保存每个套件的执行结果到TestSuiteRun表
        suite_results = execution_result.get('suite_results', [])
        for suite_result in suite_results:
            suite_summary = suite_result.get('summary', {})

            # 计算套件执行状态
            if suite_summary.get('error', 0) > 0:
                suite_status = 'error'
            elif suite_summary.get('failed', 0) > 0:
                suite_status = 'failed'
            else:
                suite_status = 'completed'

            suite_run = await TestSuiteRun.create(
                suite_id=suite_result.get('suite_id'),
                run_task_id=task_run.id,
                status=suite_status,
                start_time=task_run.start_time,
                end_time=end_time,
                duration=Decimal(str(suite_summary.get('duration', 0))),
                total_cases=suite_summary.get('total', 0),
                passed_cases=suite_summary.get('success', 0),
                failed_cases=suite_summary.get('fail', 0),
                skipped_cases=suite_summary.get('skip', 0)
            )

            # 10. 保存每个用例的执行结果到ApiCaseRun表
            case_results = suite_result.get('results', [])
            for result in case_results:
                await ApiCaseRun.create(
                    api_case_id=result.case_id,
                    suite_run_id=suite_run.id,
                    case_name=result.case_name,
                    status=result.status,
                    start_time=datetime.fromtimestamp(result.start_time) if result.start_time else None,
                    end_time=datetime.fromtimestamp(result.end_time) if result.end_time else None,
                    duration=Decimal(str(result.duration)) if result.duration else None,
                    error_message=result.error_message,
                    logs=result.logs,
                    api_requests_info=getattr(result, 'api_requests_info', None),
                    traceback=result.traceback
                )

    except Exception as e:
        # 如果执行过程中出现异常，更新任务状态为失败
        try:
            task_run = await TestTaskRun.get(id=task_run_id)
            task_run.status = 'failed'
            task_run.end_time = datetime.now()
            if task_run.start_time:
                task_run.duration = (task_run.end_time - task_run.start_time).total_seconds()
            await task_run.save()
        except:
            pass


@router.post("/{project_id}/tasks/run-background", response_model=RunTestTaskBackgroundResponse,
             summary="后台运行测试任务")
async def run_test_task_background(
        project_id: int,
        request_data: RunTestTaskBackgroundRequest,
        background_tasks: BackgroundTasks,
        project_and_user: Tuple[Project, User] = Depends(verify_admin_or_project_member)
):
    """
    后台运行测试任务接口
    
    权限要求：
    - 只有项目成员和管理员可以访问该接口
    
    参数：
    - project_id: 项目ID
    - request_data: 运行测试任务请求数据
    - background_tasks: FastAPI后台任务
    
    返回：
    - 测试任务执行记录信息（立即返回，不等待执行完成）
    """
    try:
        project, current_user = project_and_user

        # 1. 参数校验 - 查询测试任务是否存在且属于该项目
        test_task = await TestTask.get_or_none(
            id=request_data.task_id,
            project_id=project_id
        )
        if not test_task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="测试任务不存在或不属于该项目"
            )

        # 2. 参数校验 - 查询测试环境是否存在且属于该项目
        test_environment = await TestEnvironment.get_or_none(
            id=request_data.environment_id,
            project_id=project_id
        )
        if not test_environment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="测试环境不存在或不属于该项目"
            )

        # 3. 检查任务中是否包含测试套件
        task_suite_relations = await TaskSuiteRelation.filter(
            task_id=test_task.id
        ).count()

        if task_suite_relations == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="测试任务中没有包含任何测试套件"
            )

        # 4. 创建任务执行记录
        task_run = await TestTaskRun.create(
            task_id=test_task.id,
            status='pending'  # 初始状态为待执行
        )

        # 5. 添加后台任务
        background_tasks.add_task(
            execute_test_task_background,
            project_id,
            request_data.task_id,
            request_data.environment_id,
            task_run.id
        )

        # 6. 立即返回响应
        return RunTestTaskBackgroundResponse(
            task_run_id=task_run.id,
            task_id=test_task.id,
            task_name=test_task.task_name,
            status='pending',
            message="测试任务已提交到后台执行队列，请通过任务状态查询接口获取执行进度"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"提交后台任务时发生错误: {str(e)}"
        )


@router.get("/{project_id}/tasks/run/{task_run_id}/status", response_model=TaskStatusQueryResponse,
            summary="查询测试任务执行状态")
async def get_task_run_status(
        project_id: int,
        task_run_id: int,
        project_and_user: Tuple[Project, User] = Depends(verify_admin_or_project_member)
):
    """
    查询测试任务执行状态接口
    
    权限要求：
    - 只有项目成员和管理员可以访问该接口
    
    参数：
    - project_id: 项目ID
    - task_run_id: 任务执行记录ID
    
    返回：
    - 测试任务执行状态和结果
    """
    try:
        project, current_user = project_and_user

        # 1. 查询任务执行记录
        task_run = await TestTaskRun.get_or_none(id=task_run_id).prefetch_related('task')
        if not task_run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="任务执行记录不存在"
            )

        # 2. 验证任务是否属于该项目
        if task_run.task.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="任务执行记录不属于该项目"
            )

        # 3. 构建响应数据
        summary = None
        if task_run.status in ['completed', 'failed', 'error']:
            summary = TestTaskSummary(
                total_suites=task_run.total_suites,
                total_cases=task_run.total_cases,
                success_cases=task_run.passed_cases,
                failed_cases=task_run.failed_cases,
                error_cases=0,  # 这里可以根据实际需要调整
                skip_cases=task_run.skipped_cases,
                duration=float(task_run.duration) if task_run.duration else 0.0
            )

        return TaskStatusQueryResponse(
            task_run_id=task_run.id,
            task_id=task_run.task.id,
            task_name=task_run.task.task_name,
            status=task_run.status,
            duration=float(task_run.duration) if task_run.duration else None,
            start_time=task_run.start_time,
            end_time=task_run.end_time,
            error_message=None,  # 可以根据需要添加错误信息字段
            summary=summary
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询任务状态时发生错误: {str(e)}"
        )


@router.get("/{project_id}/cases/run/{case_run_id}", response_model=ApiCaseRunDetailResponse,
            summary="获取单条测试用例运行详情")
async def get_case_run_detail(
        project_id: int,
        case_run_id: int,
        project_and_user: Tuple[Project, User] = Depends(verify_admin_or_project_member)
):
    """
    获取单条测试用例运行详情
    """
    try:
        # 1. 查询用例执行记录
        case_run = await ApiCaseRun.get_or_none(id=case_run_id).prefetch_related(
            'api_case', 'api_case__base_case', 'api_case__base_case__interface', 'suite_run', 'suite_run__suite'
        )
        if not case_run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用例执行记录不存在"
            )

        # 2. 验证用例是否属于该项目
        if case_run.api_case.base_case.interface.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用例执行记录不属于该项目"
            )

        # 3. 构建响应数据
        return ApiCaseRunDetailResponse(
            id=case_run.id,
            api_case_id=case_run.api_case.id,
            case_name=case_run.api_case.name,
            suite_run_id=case_run.suite_run.id if case_run.suite_run else None,
            error_message=case_run.error_message,
            traceback=None,  # 当前模型中没有这个字段
            start_time=case_run.start_time,
            end_time=case_run.end_time,
            duration=float(case_run.duration) if case_run.duration else 0.0,
            logs=case_run.logs,
            request_info=case_run.api_requests_info,
            created_at=case_run.created_at,
            status=case_run.status
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用例运行详情时发生错误: {str(e)}"
        )


@router.get("/{project_id}/cases/run", response_model=ApiCaseRunListResponse,
            summary="获取用例运行记录列表")
async def get_case_run_list(
        project_id: int,
        suite_run_id: int = None,
        case_id: int = None,
        page: int = 1,
        page_size: int = 20,
        project_and_user: Tuple[Project, User] = Depends(verify_admin_or_project_member)
):
    """
    获取用例运行记录列表，支持使用套件运行记录id过滤、用例ID过滤和翻页
    """
    try:
        # 构建查询条件 - 使用正确的关联路径
        query = ApiCaseRun.filter(api_case__base_case__interface__project_id=project_id)
        
        # 如果指定了套件运行记录ID，则过滤
        if suite_run_id:
            query = query.filter(suite_run_id=suite_run_id)
        
        # 如果指定了用例ID，则过滤
        if case_id:
            query = query.filter(api_case_id=case_id)
        
        # 计算总数
        total = await query.count()
        
        # 分页查询
        offset = (page - 1) * page_size
        case_runs = await query.prefetch_related(
            'api_case', 'suite_run', 'suite_run__suite'
        ).order_by('-created_at').offset(offset).limit(page_size)
        
        # 构建响应数据
        items = []
        for case_run in case_runs:
            items.append({
                "id": case_run.id,
                "api_case_id": case_run.api_case.id,
                "case_name": case_run.api_case.name,
                "suite_run_id": case_run.suite_run.id if case_run.suite_run else None,
                "suite_name": case_run.suite_run.suite.suite_name if case_run.suite_run else None,
                "status": case_run.status if hasattr(case_run, 'status') else 'error',
                "start_time": case_run.start_time,
                "end_time": case_run.end_time,
                "duration": float(case_run.duration) if case_run.duration else 0.0,
                "created_at": case_run.created_at
            })
        
        return ApiCaseRunListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用例运行记录列表时发生错误: {str(e)}"
        )


@router.get("/{project_id}/suites/run", response_model=TestSuiteRunListResponse,
            summary="获取测试套件运行记录列表")
async def get_suite_run_list(
        project_id: int,
        task_run_id: int = None,
        suite_id: int = None,
        page: int = 1,
        page_size: int = 20,
        project_and_user: Tuple[Project, User] = Depends(verify_admin_or_project_member)
):
    """
    获取测试套件运行记录列表，支持使用任务运行记录id和套件id过滤，支持分页
    """
    try:
        # 构建查询条件
        query = TestSuiteRun.filter(suite__project_id=project_id)
        
        # 如果指定了任务运行记录ID，则过滤
        if task_run_id:
            query = query.filter(run_task_id=task_run_id)
        
        # 如果指定了套件ID，则过滤
        if suite_id:
            query = query.filter(suite_id=suite_id)
        
        # 计算总数
        total = await query.count()
        
        # 计算偏移量
        offset = (page - 1) * page_size
        
        # 查询套件运行记录（分页）
        suite_runs = await query.prefetch_related(
            'suite', 'run_task', 'run_task__task'
        ).order_by('-created_at').offset(offset).limit(page_size)
        
        # 构建响应数据
        items = []
        for suite_run in suite_runs:
            items.append({
                "id": suite_run.id,
                "suite_id": suite_run.suite.id,
                "suite_name": suite_run.suite.suite_name,
                "run_task_id": suite_run.run_task.id if suite_run.run_task else None,
                "status": suite_run.status,
                "total_cases": suite_run.total_cases,
                "passed_cases": suite_run.passed_cases,
                "failed_cases": suite_run.failed_cases,
                "skipped_cases": suite_run.skipped_cases,
                "error_cases":suite_run.error_cases,
                "start_time": suite_run.start_time,
                "end_time": suite_run.end_time,
                "duration": float(suite_run.duration) if suite_run.duration else 0.0,
                "created_at": suite_run.created_at
            })
        
        return TestSuiteRunListResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=items
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取套件运行记录列表时发生错误: {str(e)}"
        )


@router.get("/{project_id}/suites/run/{suite_run_id}", response_model=TestSuiteRunDetailResponse,
            summary="获取测试套件运行详情")
async def get_suite_run_detail(
        project_id: int,
        suite_run_id: int,
        project_and_user: Tuple[Project, User] = Depends(verify_admin_or_project_member)
):
    """
    获取测试套件运行详情
    """
    try:
        # 1. 查询套件执行记录
        suite_run = await TestSuiteRun.get_or_none(id=suite_run_id).prefetch_related(
            'suite', 'run_task', 'run_task__task'
        )
        if not suite_run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="套件执行记录不存在"
            )

        # 2. 验证套件是否属于该项目
        if suite_run.suite.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="套件执行记录不属于该项目"
            )

        # 3. 获取该套件运行的用例记录
        case_runs = await ApiCaseRun.filter(suite_run_id=suite_run_id).prefetch_related('api_case')
        case_run_details = []
        for case_run in case_runs:
            # 根据error_message推断执行状态
            if case_run.error_message:
                status = "failed"
            elif case_run.end_time:
                status = "passed"
            else:
                status = "running"
                
            case_run_details.append({
                "id": case_run.id,
                "suite_run_id": case_run.suite_run_id,
                "api_case_id": case_run.api_case.id,
                "case_name": case_run.case_name,
                "status": status,
                "start_time": case_run.start_time,
                "end_time": case_run.end_time,
                "duration": float(case_run.duration) if case_run.duration else 0.0,
                "created_at": case_run.created_at
            })

        # 4. 构建响应数据
        return TestSuiteRunDetailResponse(
            id=suite_run.id,
            suite_id=suite_run.suite.id,
            suite_name=suite_run.suite.suite_name,
            run_task_id=suite_run.run_task.id if suite_run.run_task else None,
            status=suite_run.status,
            start_time=suite_run.start_time,
            end_time=suite_run.end_time,
            duration=float(suite_run.duration) if suite_run.duration else 0.0,
            total_cases=suite_run.total_cases,
            passed_cases=suite_run.passed_cases,
            failed_cases=suite_run.failed_cases,
            skipped_cases=suite_run.skipped_cases,
            error_cases=suite_run.error_cases,
            case_runs=case_run_details,
            created_at=suite_run.created_at,
            updated_at=suite_run.updated_at
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取套件运行详情时发生错误: {str(e)}"
        )


@router.get("/{project_id}/tasks/run", response_model=TestTaskRunListResponse,
            summary="获取项目测试任务运行记录列表")
async def get_task_run_list(
        project_id: int,
        task_id: Optional[int] = Query(None, description="任务ID过滤"),
        page: int = Query(1, ge=1, description="页码"),
        page_size: int = Query(10, ge=1, le=100, description="每页大小"),
        project_and_user: Tuple[Project, User] = Depends(verify_admin_or_project_member)
):
    """
    获取项目测试任务运行记录列表
    """
    try:
        # 构建查询条件
        query_filter = {"task__project_id": project_id}
        if task_id:
            query_filter["task_id"] = task_id
        
        # 查询总数
        total = await TestTaskRun.filter(**query_filter).count()
        
        # 分页查询任务运行记录
        offset = (page - 1) * page_size
        task_runs = await TestTaskRun.filter(**query_filter).prefetch_related(
            'task'
        ).order_by('-created_at').offset(offset).limit(page_size)
        
        # 构建响应数据
        items = []
        for task_run in task_runs:
            items.append({
                "id": task_run.id,
                "task_id": task_run.task.id,
                "task_name": task_run.task.task_name,
                "status": task_run.status,
                "start_time": task_run.start_time,
                "end_time": task_run.end_time,
                "duration": float(task_run.duration) if task_run.duration else 0.0,
                "total_suites": task_run.total_suites,
                "total_cases": task_run.total_cases,
                "passed_cases": task_run.passed_cases,
                "failed_cases": task_run.failed_cases,
                "skipped_cases": task_run.skipped_cases,
                "created_at": task_run.created_at
            })
        
        return TestTaskRunListResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=items
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取任务运行记录列表时发生错误: {str(e)}"
        )


@router.get("/{project_id}/tasks/run/{task_run_id}", response_model=TestTaskRunDetailResponse,
            summary="获取项目运行记录详情")
async def get_task_run_detail(
        project_id: int,
        task_run_id: int,
        project_and_user: Tuple[Project, User] = Depends(verify_admin_or_project_member)
):
    """
    获取项目运行记录详情
    """
    try:
        # 1. 查询任务执行记录
        task_run = await TestTaskRun.get_or_none(id=task_run_id).prefetch_related('task')
        if not task_run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="任务执行记录不存在"
            )

        # 2. 验证任务是否属于该项目
        if task_run.task.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="任务执行记录不属于该项目"
            )

        # 3. 获取该任务运行的套件记录
        # 修复过滤字段：模型字段为 run_task_id，而非 task_run_id
        suite_runs = await TestSuiteRun.filter(run_task_id=task_run_id).prefetch_related('suite')
        suite_run_details = []
        error_cases_total = 0
        for suite_run in suite_runs:
            # 累加套件级错误用例数，用于任务级统计
            try:
                error_cases_total += int(suite_run.error_cases or 0)
            except Exception:
                pass
            suite_run_details.append({
                "id": suite_run.id,
                "suite_id": suite_run.suite.id,
                "suite_name": suite_run.suite.suite_name,
                "status": suite_run.status,
                "start_time": suite_run.start_time,
                "end_time": suite_run.end_time,
                "duration": float(suite_run.duration) if suite_run.duration else 0.0,
                "total_cases": suite_run.total_cases,
                "passed_cases": suite_run.passed_cases,
                "failed_cases": suite_run.failed_cases,
                "skipped_cases": suite_run.skipped_cases,
                "error_cases": suite_run.error_cases,
                "created_at": suite_run.created_at
            })

        # 4. 构建响应数据
        return TestTaskRunDetailResponse(
            id=task_run.id,
            task_id=task_run.task.id,
            task_name=task_run.task.task_name,
            status=task_run.status,
            start_time=task_run.start_time,
            end_time=task_run.end_time,
            duration=float(task_run.duration) if task_run.duration else 0.0,
            total_suites=task_run.total_suites,
            total_cases=task_run.total_cases,
            passed_cases=task_run.passed_cases,
            failed_cases=task_run.failed_cases,
            skipped_cases=task_run.skipped_cases,
            error_cases=error_cases_total,
            suite_runs=suite_run_details,
            created_at=task_run.created_at,
            updated_at=task_run.updated_at
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取任务运行详情时发生错误: {str(e)}"
        )
