"""
测试执行模块API路由
"""
from fastapi import APIRouter, HTTPException, Depends, status
from typing import Tuple
from decimal import Decimal
from datetime import datetime
from service.user.models import User
from service.project.models import Project
from utils.permissions import verify_admin_or_project_member
from service.api_test.models import ApiTestCase
from service.test_environment.models import TestEnvironment, TestEnvironmentConfig, TestEnvironmentDb
from .models import ApiCaseRun, TestSuiteRun
from .schemas import RunSingleTestCaseRequest, RunSingleTestCaseResponse, RunTestSuiteRequest, RunTestSuiteResponse, \
    TestSuiteSummary, RunTestTaskRequest, RunTestTaskResponse, TestTaskSummary
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
            project_id=project_id
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
            "skip": False  # 单条用例执行不跳过
        }

        # 6. 调用execute_test_case方法执行用例
        executor = TestExecutor(test_env_global=test_env_global, db_config=db_config_list)
        result = executor.execute_test_case(case_data)

        # 7. 保存执行结果到ApiCaseRun表
        case_run = await ApiCaseRun.create(
            case_id=test_case.id,
            case_name=test_case.name,
            environment_id=request_data.environment_id,
            status=result.status,
            start_time=datetime.fromtimestamp(result.start_time) if result.start_time else None,
            end_time=datetime.fromtimestamp(result.end_time) if result.end_time else None,
            duration=Decimal(str(result.duration)) if result.duration else None,
            error_message=result.error_message,
            logs=result.logs,
            response_data=getattr(result, 'response_data', None),
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
            error_message=result.error_message
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
            skipped_cases=summary.get('skipped', 0)
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
