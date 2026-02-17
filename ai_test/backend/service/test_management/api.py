"""
测试管理模块API路由
"""
from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import Tuple
from service.user.models import User
from service.project.models import Project
from utils.permissions import verify_admin_or_project_editor
from .models import TestSuite, SuiteCaseRelation, TestTask, TaskSuiteRelation
from service.api_test.models import ApiTestCase, ApiBaseCase, ApiInterface
from .schemas import TestSuiteCreateRequest, TestSuiteResponse, TestSuiteDeleteResponse, TestSuiteListResponse, \
    TestSuiteDetailResponse, SuiteCaseItem, AddCaseToSuiteRequest, AddCaseToSuiteResponse, DeleteCaseFromSuiteResponse, \
    ReorderSuiteCasesRequest, ReorderSuiteCasesResponse, TestTaskCreateRequest, TestTaskResponse, \
    TestTaskDeleteResponse, TestTaskListResponse, TestTaskDetailResponse, AddSuiteToTaskRequest, AddSuiteToTaskResponse, \
    DeleteSuiteFromTaskResponse, TaskSuiteItem, ReorderTaskSuitesRequest, ReorderTaskSuitesResponse

router = APIRouter()


@router.post("/{project_id}/suites", response_model=TestSuiteResponse, summary="创建测试套件")
async def create_test_suite(
        project_id: int,
        suite_data: TestSuiteCreateRequest,
        project_and_user: Tuple[Project, User] = Depends(verify_admin_or_project_editor)
):
    """
    创建测试套件接口
    
    权限要求：
    - 只有项目负责人、项目编辑组和管理员可以访问该接口
    
    参数：
    - project_id: 项目ID
    - suite_data: 测试套件创建数据
    
    返回：
    - 创建的测试套件信息
    """
    try:
        project, current_user = project_and_user

        # 验证套件类型
        if suite_data.type not in ['api', 'ui']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="套件类型只能是 'api' 或 'ui'"
            )

        # 检查同项目下套件名称是否重复
        existing_suite = await TestSuite.get_or_none(
            project_id=project_id,
            suite_name=suite_data.suite_name
        )
        if existing_suite:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该项目下已存在同名的测试套件"
            )

        # 创建测试套件
        test_suite = await TestSuite.create(
            suite_name=suite_data.suite_name,
            description=suite_data.description,
            type=suite_data.type,
            project_id=project_id
        )

        return TestSuiteResponse(
            id=test_suite.id,
            suite_name=test_suite.suite_name,
            description=test_suite.description,
            type=test_suite.type,
            project_id=project_id,
            created_at=test_suite.created_at,
            updated_at=test_suite.updated_at
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建测试套件失败: {str(e)}"
        )


@router.delete("/{project_id}/suites/{suite_id}", response_model=TestSuiteDeleteResponse, summary="删除测试套件")
async def delete_test_suite(
        project_id: int,
        suite_id: int,
        project_and_user: Tuple[Project, User] = Depends(verify_admin_or_project_editor)
):
    """
    删除测试套件
    
    权限要求：
    - 只有项目负责人、项目编辑组和管理员可以删除测试套件
    
    业务逻辑：
    - 验证测试套件是否存在
    - 验证测试套件是否属于指定项目
    - 删除测试套件
    
    参数：
    - project_id: 项目ID
    - suite_id: 测试套件ID
    """
    project, current_user = project_and_user

    try:
        # 查询测试套件是否存在
        test_suite = await TestSuite.get_or_none(id=suite_id)
        if not test_suite:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定的测试套件不存在"
            )

        # 验证测试套件是否属于指定项目
        if test_suite.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="测试套件不属于指定项目"
            )

        # 删除测试套件
        await test_suite.delete()

        return TestSuiteDeleteResponse(message="测试套件删除成功")

    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除测试套件失败: {str(e)}"
        )


@router.get("/{project_id}/suites", response_model=TestSuiteListResponse, summary="获取测试套件列表")
async def get_test_suites(
        project_id: int,
        page: int = Query(1, ge=1, description="页码，从1开始"),
        page_size: int = Query(20, ge=1, le=100, description="每页数量，默认20，最大100"),
        project_and_user: Tuple[Project, User] = Depends(verify_admin_or_project_editor)
):
    """
    获取测试套件列表（分页）
    
    参数：
    - project_id: 项目ID（路径参数）
    - page: 页码，从1开始
    - page_size: 每页数量，默认20，最大100
    
    权限：项目负责人、项目编辑者和管理员可以访问
    """
    try:
        project, current_user = project_and_user

        # 计算偏移量
        offset = (page - 1) * page_size

        # 查询测试套件总数
        total = await TestSuite.filter(project_id=project_id).count()

        # 查询测试套件列表
        suites = await TestSuite.filter(project_id=project_id).offset(offset).limit(page_size).order_by('created_at')

        # 计算总页数
        total_pages = (total + page_size - 1) // page_size

        # 构造响应数据
        suite_items = []
        for suite in suites:
            suite_items.append(TestSuiteResponse(
                id=suite.id,
                suite_name=suite.suite_name,
                description=suite.description,
                type=suite.type,
                project_id=suite.project_id,
                created_at=suite.created_at,
                updated_at=suite.updated_at
            ))

        return TestSuiteListResponse(
            suites=suite_items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取测试套件列表失败"
        )


@router.get("/{project_id}/suites/{suite_id}", response_model=TestSuiteDetailResponse, summary="获取单个测试套件详情")
async def get_test_suite_detail(
        project_id: int,
        suite_id: int,
        project_and_user: Tuple[Project, User] = Depends(verify_admin_or_project_editor)
):
    """
    获取单个测试套件详情接口
    
    权限要求：
    - 项目负责人
    - 项目编辑组成员
    - 管理员
    
    返回数据包含：
    - 套件基本信息
    - 套件中的所有用例（包含关联关系ID、执行顺序、用例ID、用例名称）
    """
    try:
        project, user = project_and_user

        # 验证项目ID匹配
        if project.id != project_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限访问该项目"
            )

        # 查询测试套件
        suite = await TestSuite.get_or_none(id=suite_id, project_id=project_id)
        if not suite:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="测试套件不存在"
            )
        # 查询套件中的所有用例
        case_relations = await SuiteCaseRelation.filter(suite_id=suite_id).all().prefetch_related("case")

        # 构建用例列表
        cases = []
        for relation in case_relations:
            case_ = await relation.case
            cases.append(SuiteCaseItem(
                relation_id=relation.id,
                case_order=relation.case_order,
                case_id=case_.id,
                case_name=case_.name
            ))

        return TestSuiteDetailResponse(
            id=suite.id,
            suite_name=suite.suite_name,
            description=suite.description,
            type=suite.type,
            project_id=project.id,
            created_at=suite.created_at,
            updated_at=suite.updated_at,
            cases=cases
        )
    except Exception as e:
        # raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取测试套件详情失败: {str(e)}"
        )


@router.post("/{project_id}/suites/{suite_id}/cases", response_model=AddCaseToSuiteResponse,
             summary="往测试套件中添加测试用例")
async def add_case_to_suite(
        project_id: int,
        suite_id: int,
        request_data: AddCaseToSuiteRequest,
        project_and_user: Tuple[Project, User] = Depends(verify_admin_or_project_editor)
):
    """
    往测试套件中添加测试用例
    
    权限要求：项目负责人、项目编辑组成员或管理员
    
    业务逻辑：
    1. 验证项目权限
    2. 验证测试套件是否存在且属于当前项目
    3. 验证测试用例是否存在且属于当前项目的接口
    4. 检查用例是否已经在套件中
    5. 添加用例到套件，设置执行顺序
    """
    try:
        project, user = project_and_user

        # 验证项目ID匹配
        if project.id != project_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限访问该项目"
            )

        # 验证测试套件是否存在且属于当前项目
        suite = await TestSuite.get_or_none(id=suite_id, project_id=project_id)
        if not suite:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="测试套件不存在或不属于当前项目"
            )

        # 验证测试用例是否存在
        test_case = await ApiTestCase.get_or_none(id=request_data.case_id).prefetch_related("base_case")
        if not test_case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="测试用例不存在"
            )

        # 验证测试用例是否属于当前项目的接口
        # 通过 ApiTestCase -> ApiBaseCase -> ApiInterface -> Project 的关联关系验证
        base_case = await ApiBaseCase.get_or_none(id=test_case.base_case.id).prefetch_related("interface")
        if not base_case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="测试用例对应的基础用例不存在"
            )

        interface = await ApiInterface.get_or_none(id=base_case.interface.id).prefetch_related("project")
        if not interface or interface.project.id != project.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="测试用例不属于当前项目的接口"
            )

        # 检查用例是否已经在套件中
        existing_relation = await SuiteCaseRelation.get_or_none(
            suite_id=suite.id,
            case_id=test_case.id
        )
        if existing_relation:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该用例已经在测试套件中"
            )

        # 获取当前套件中用例的最大顺序号
        max_order_query = await SuiteCaseRelation.filter(suite_id=suite.id)

        max_order = len(max_order_query)

        # 创建新的关联关系
        new_relation = await SuiteCaseRelation.create(
            suite=suite,
            case=test_case,
            case_order=max_order + 1
        )
        return AddCaseToSuiteResponse(
            message="用例添加成功",
            relation_id=new_relation.id,
            case_order=new_relation.case_order
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"添加用例到测试套件失败: {str(e)}"
        )


@router.delete("/{project_id}/suites/{suite_id}/cases/{case_id}", response_model=DeleteCaseFromSuiteResponse,
               summary="从测试套件中删除测试用例")
async def delete_case_from_suite(
        project_id: int,
        suite_id: int,
        case_id: int,
        project_and_user: Tuple[Project, User] = Depends(verify_admin_or_project_editor)
):
    """
    从测试套件中删除测试用例
    
    权限要求：项目负责人、项目编辑组或管理员
    
    业务逻辑：
    1. 验证项目权限
    2. 验证测试套件存在且属于当前项目
    3. 验证用例存在于该套件中
    4. 删除用例关联关系
    5. 重新排序剩余用例的执行顺序
    """
    project, user = project_and_user

    # 验证项目权限
    if project.id != project_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限访问该项目"
        )

    # 验证测试套件存在且属于当前项目
    # 验证测试套件是否存在且属于当前项目
    suite = await TestSuite.get_or_none(id=suite_id, project_id=project_id)
    if not suite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="测试套件不存在或不属于当前项目"
        )

    # 验证用例关联关系存在
    suite_case_relation = await SuiteCaseRelation.get_or_none(
        suite_id=suite_id,
        case_id=case_id
    )
    if not suite_case_relation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用例不存在于该测试套件中"
        )

    # 获取被删除用例的执行顺序
    deleted_case_order = suite_case_relation.case_order
    deleted_relation_id = suite_case_relation.id

    # 删除用例关联关系
    await suite_case_relation.delete()

    # 重新排序：将所有执行顺序大于被删除用例的用例顺序减1
    reordered_relations = await SuiteCaseRelation.all().order_by("case_order")

    reordered_count = 0
    for relation in reordered_relations:
        relation.case_order = reordered_count + 1
        await relation.save()
        reordered_count += 1
    return DeleteCaseFromSuiteResponse(
        message="用例删除成功",
        deleted_relation_id=deleted_relation_id,
        reordered_count=reordered_count
    )


@router.put("/{project_id}/suites/{suite_id}/cases/reorder", response_model=ReorderSuiteCasesResponse,
            summary="对测试套件中的用例进行排序")
async def reorder_suite_cases(
        project_id: int,
        suite_id: int,
        request_data: ReorderSuiteCasesRequest,
        project_and_user: Tuple[Project, User] = Depends(verify_admin_or_project_editor)
):
    """
    对测试套件中的用例进行排序
    
    权限要求：项目负责人、项目编辑组或管理员
    
    业务逻辑：
    1. 验证项目权限
    2. 验证测试套件存在且属于当前项目
    3. 验证所有用例ID都存在于该套件中
    4. 根据传入的用例ID列表重新调整执行顺序
    """
    project, user = project_and_user

    # 验证项目权限
    if project.id != project_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限访问该项目"
        )

    # 验证测试套件存在且属于当前项目
    suite = await TestSuite.get_or_none(id=suite_id, project_id=project_id)
    if not suite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="测试套件不存在或不属于当前项目"
        )
    # 获取当前套件中的所有用例关联关系
    existing_relations = await SuiteCaseRelation.filter(suite_id=suite_id).prefetch_related("case")

    # 验证传入的用例ID是否都存在于该套件中
    existing_case_ids = {relation.case.id for relation in existing_relations}
    request_case_ids = set(request_data.case_ids)
    if request_case_ids != existing_case_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请传入套件中完整的用例ID的列表"
        )

    # 创建用例ID到关联关系的映射
    case_id_to_relation = {relation.case.id: relation for relation in existing_relations}

    # 根据新的顺序更新执行顺序
    reordered_count = 0
    updated_cases = []

    for new_order, case_id in enumerate(request_data.case_ids, start=1):
        relation = case_id_to_relation[case_id]
        if relation.case_order != new_order:
            relation.case_order = new_order
            relation.save()
            reordered_count += 1

        # 构建返回的用例信息
        case = relation.case
        updated_cases.append(SuiteCaseItem(
            relation_id=relation.id,
            case_order=relation.case_order,
            case_id=case.id,
            case_name=case.name
        ))

    return ReorderSuiteCasesResponse(
        message="用例排序成功",
        reordered_count=reordered_count,
        updated_cases=updated_cases
    )


@router.get("/{project_id}/tasks", response_model=TestTaskListResponse, summary="获取测试任务列表")
async def get_test_tasks(
        project_id: int,
        page: int = Query(1, ge=1, description="页码，从1开始"),
        page_size: int = Query(20, ge=1, le=100, description="每页数量，默认20，最大100"),
        project_and_user: Tuple[Project, User] = Depends(verify_admin_or_project_editor)
):
    """
    获取测试任务列表（分页）
    
    参数：
    - project_id: 项目ID（路径参数）
    - page: 页码，从1开始
    - page_size: 每页数量，默认20，最大100
    
    权限要求：
    - 项目负责人
    - 项目编辑组成员
    - 管理员
    """
    try:
        project, current_user = project_and_user

        # 计算偏移量
        offset = (page - 1) * page_size

        # 查询测试任务总数
        total = await TestTask.filter(project_id=project_id).count()

        # 查询测试任务列表
        tasks = await TestTask.filter(project_id=project_id).offset(offset).limit(page_size).order_by('created_at')

        # 计算总页数
        total_pages = (total + page_size - 1) // page_size

        # 构造响应数据
        task_items = []
        for task in tasks:
            task_items.append(TestTaskResponse(
                id=task.id,
                task_name=task.task_name,
                description=task.description,
                type=task.type,
                status=task.status,
                project_id=task.project_id,
                created_at=task.created_at,
                updated_at=task.updated_at
            ))

        return TestTaskListResponse(
            tasks=task_items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取测试任务列表失败"
        )


@router.get("/{project_id}/tasks/{task_id}", response_model=TestTaskDetailResponse, summary="获取单个测试任务详情")
async def get_test_task_detail(
        project_id: int,
        task_id: int,
        project_and_user: Tuple[Project, User] = Depends(verify_admin_or_project_editor)
):
    """
    获取单个测试任务的详情，包括任务基本信息和关联的测试套件列表
    
    Args:
        project_id: 项目ID
        task_id: 测试任务ID
        project_and_user: 项目和用户信息（通过权限验证获得）
    
    Returns:
        TestTaskDetailResponse: 测试任务详情响应
    
    Raises:
        HTTPException: 当任务不存在或不属于指定项目时抛出404错误
        HTTPException: 当发生其他错误时抛出500错误
    """
    try:
        project, user = project_and_user
        
        # 检查测试任务是否存在且属于指定项目
        task = await TestTask.filter(id=task_id, project_id=project_id).first()
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="测试任务不存在或不属于该项目"
            )
        
        # 获取任务关联的测试套件
        task_suite_relations = await TaskSuiteRelation.filter(task_id=task_id).order_by('suite_order').prefetch_related('suite')
        
        # 构建套件列表，保持排序
        suite_items = []
        for relation in task_suite_relations:
            suite = await relation.suite
            suite_items.append(TaskSuiteItem(
                relation_id=relation.id,
                suite_order=relation.suite_order,
                suite_id=suite.id,
                suite_name=suite.suite_name
            ))
        
        return TestTaskDetailResponse(
            id=task.id,
            task_name=task.task_name,
            description=task.description,
            type=task.type,
            status=task.status,
            project_id=project_id,
            created_at=task.created_at,
            updated_at=task.updated_at,
            suites=suite_items
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取测试任务详情失败: {str(e)}"
        )


@router.post("/{project_id}/tasks", response_model=TestTaskResponse, summary="创建测试任务")
async def create_test_task(
        project_id: int,
        task_data: TestTaskCreateRequest,
        project_and_user: Tuple[Project, User] = Depends(verify_admin_or_project_editor)
):
    """
    创建测试任务
    
    权限要求：项目负责人、项目编辑组或管理员
    
    Args:
        project_id: 项目ID
        task_data: 测试任务创建请求数据
        project_and_user: 项目和用户信息（通过权限验证获得）
    
    Returns:
        TestTaskResponse: 创建的测试任务信息
    
    Raises:
        HTTPException: 400 - 任务类型无效
    """
    project, user = project_and_user

    # 验证任务类型
    valid_types = ['api', 'ui', 'functional']
    if task_data.type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"任务类型无效，支持的类型：{', '.join(valid_types)}"
        )

    # 创建测试任务
    task = await TestTask.create(
        project=project,
        task_name=task_data.task_name,
        description=task_data.description,
        type=task_data.type,
        status='pending'  # 默认状态为待执行
    )

    # 返回创建的任务信息
    return TestTaskResponse(
        id=task.id,
        task_name=task.task_name,
        description=task.description,
        type=task.type,
        status=task.status,
        project_id=project.id,
        created_at=task.created_at,
        updated_at=task.updated_at
    )


@router.delete("/{project_id}/tasks/{task_id}", response_model=TestTaskDeleteResponse, summary="删除测试任务")
async def delete_test_task(
        project_id: int,
        task_id: int,
        project_and_user: Tuple[Project, User] = Depends(verify_admin_or_project_editor)
):
    """
    删除测试任务
    权限要求：
    - 项目负责人
    - 项目编辑组成员
    - 管理员
    """
    project, user = project_and_user

    # 查找测试任务
    task = await TestTask.filter(id=task_id, project_id=project.id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="测试任务不存在"
        )

    # 删除测试任务
    await task.delete()

    return TestTaskDeleteResponse(
        message=f"测试任务 '{task.task_name}' 删除成功"
    )


@router.post("/{project_id}/tasks/{task_id}/suites", response_model=AddSuiteToTaskResponse,
             summary="往测试任务中添加测试套件")
async def add_suite_to_task(
        project_id: int,
        task_id: int,
        request_data: AddSuiteToTaskRequest,
        project_and_user: Tuple[Project, User] = Depends(verify_admin_or_project_editor)
):
    """
    往测试任务中添加测试套件

    权限要求：项目负责人、项目编辑组成员或管理员

    业务逻辑：
    1. 验证项目权限
    2. 验证测试任务是否存在且属于当前项目
    3. 验证测试套件是否存在且属于当前项目
    4. 检查套件是否已经在任务中
    5. 添加套件到任务，设置执行顺序
    """
    try:
        project, user = project_and_user

        # 验证项目ID匹配
        if project.id != project_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限访问该项目"
            )

        # 验证测试任务是否存在且属于当前项目
        task = await TestTask.get_or_none(id=task_id, project_id=project_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="测试任务不存在或不属于当前项目"
            )

        # 验证测试套件是否存在且属于当前项目
        suite = await TestSuite.get_or_none(id=request_data.suite_id, project_id=project_id)
        if not suite:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="测试套件不存在或不属于当前项目"
            )

        # 检查套件是否已经在任务中
        existing_relation = await TaskSuiteRelation.get_or_none(
            task_id=task.id,
            suite_id=suite.id
        )
        if existing_relation:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该套件已经在测试任务中"
            )

        # 获取当前任务中套件的最大顺序号
        max_order_query = await TaskSuiteRelation.filter(task_id=task.id)
        max_order = len(max_order_query)

        # 创建新的关联关系
        new_relation = await TaskSuiteRelation.create(
            task=task,
            suite=suite,
            suite_order=max_order + 1
        )
        return AddSuiteToTaskResponse(
            message="套件添加成功",
            relation_id=new_relation.id,
            suite_order=new_relation.suite_order
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"添加套件到测试任务失败: {str(e)}"
        )


@router.delete("/{project_id}/tasks/{task_id}/suites/{suite_id}", response_model=DeleteSuiteFromTaskResponse,
               summary="从测试任务中删除测试套件")
async def delete_suite_from_task(
        project_id: int,
        task_id: int,
        suite_id: int,
        project_and_user: Tuple[Project, User] = Depends(verify_admin_or_project_editor)
):
    """
    从测试任务中删除测试套件

    权限要求：项目负责人、项目编辑组或管理员

    业务逻辑：
    1. 验证项目权限
    2. 验证测试任务存在且属于当前项目
    3. 验证套件存在于该任务中
    4. 删除套件关联关系
    5. 重新排序剩余套件的执行顺序
    """
    project, user = project_and_user

    try:
        # 验证项目权限
        if project.id != project_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限访问该项目"
            )

        # 验证测试任务存在且属于当前项目
        task = await TestTask.get_or_none(id=task_id, project_id=project_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="测试任务不存在或不属于当前项目"
            )

        # 验证套件关联关系存在
        task_suite_relation = await TaskSuiteRelation.get_or_none(
            task_id=task_id,
            suite_id=suite_id
        )
        if not task_suite_relation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="套件不存在于该测试任务中"
            )

        # 获取被删除套件的执行顺序
        deleted_suite_order = task_suite_relation.suite_order
        deleted_relation_id = task_suite_relation.id

        # 删除套件关联关系
        await task_suite_relation.delete()

        # 重新排序：获取该任务下所有剩余的套件关联关系，按顺序重新编号
        remaining_relations = await TaskSuiteRelation.filter(task_id=task_id).order_by("suite_order")

        reordered_count = 0
        for relation in remaining_relations:
            relation.suite_order = reordered_count + 1
            await relation.save()
            reordered_count += 1

        return DeleteSuiteFromTaskResponse(
            message="套件删除成功",
            deleted_relation_id=deleted_relation_id,
            reordered_count=reordered_count
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除套件时发生错误: {str(e)}"
        )


@router.put("/{project_id}/tasks/{task_id}/suites/reorder", response_model=ReorderTaskSuitesResponse,
            summary="对测试任务中的套件进行排序")
async def reorder_task_suites(
        project_id: int,
        task_id: int,
        request_data: ReorderTaskSuitesRequest,
        project_and_user: Tuple[Project, User] = Depends(verify_admin_or_project_editor)
):
    """
    对测试任务中的套件进行排序

    权限要求：项目负责人、项目编辑组或管理员

    业务逻辑：
    1. 验证项目权限
    2. 验证测试任务存在且属于当前项目
    3. 验证所有套件ID都存在于该任务中
    4. 根据传入的套件ID列表重新调整执行顺序
    """
    project, user = project_and_user

    try:
        # 验证项目权限
        if project.id != project_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限访问该项目"
            )

        # 验证测试任务存在且属于当前项目
        task = await TestTask.get_or_none(id=task_id, project_id=project_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="测试任务不存在或不属于当前项目"
            )

        # 获取当前任务中的所有套件关联关系
        existing_relations = await TaskSuiteRelation.filter(task_id=task_id).prefetch_related("suite")

        # 验证传入的套件ID是否都存在于该任务中
        existing_suite_ids = {relation.suite.id for relation in existing_relations}
        request_suite_ids = set(request_data.suite_ids)
        if request_suite_ids != existing_suite_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="请传入任务中完整的套件ID列表"
            )

        # 创建套件ID到关联关系的映射
        suite_id_to_relation = {relation.suite.id: relation for relation in existing_relations}

        # 根据新的顺序更新执行顺序
        reordered_count = 0
        updated_suites = []

        for new_order, suite_id in enumerate(request_data.suite_ids, start=1):
            relation = suite_id_to_relation[suite_id]
            if relation.suite_order != new_order:
                relation.suite_order = new_order
                await relation.save()
                reordered_count += 1

            # 构建返回的套件信息
            suite = relation.suite
            updated_suites.append(TaskSuiteItem(
                relation_id=relation.id,
                suite_order=relation.suite_order,
                suite_id=suite.id,
                suite_name=suite.suite_name
            ))

        return ReorderTaskSuitesResponse(
            message="套件排序成功",
            reordered_count=reordered_count,
            updated_suites=updated_suites
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"套件排序时发生错误: {str(e)}"
        )


"""
需要实现的功能：
1、创建测试套件，删除测试套件、获取测试套件列表，获取单个测试套件的详情(测试套件中包含的所有用例)
2、往测试套件中添加用例，删除测试套件中的用例

3、创建测试任务(测试计划)、删除测试任何、获取测试任务列表，获取测试任务中的所有套件
4、往测试任务中添加测试套件，删除测试任务中的套件

"""
