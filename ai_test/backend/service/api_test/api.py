"""
接口测试模块API路由
"""
from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from typing import List, Optional
import json
import traceback
import os
import uuid
import asyncio
from datetime import datetime, timezone
from tortoise.transactions import in_transaction

from .schemas import (
    ApiImportRequest, ApiImportResponse, OpenApiImportResponse, ApiInterfaceItem, ApiInterfaceListResponse,
    ApiInterfaceCreateRequest, ApiInterfaceCreateResponse, ApiInterfaceUpdateRequest,
    ApiInterfaceUpdateResponse, ApiDependencyGroupCreateRequest, ApiDependencyGroupCreateResponse,
    ApiDependencyGroupUpdateRequest, ApiDependencyGroupUpdateResponse,
    ApiDependencyGroupListResponse, ApiDependencyGroupItem, ApiDependencyCreateRequest,
    ApiDependencyCreateResponse, ApiDependencyUpdateRequest, ApiDependencyUpdateResponse,
    ApiDependencyDeleteResponse, ApiDependencyGroupDeleteResponse, ApiInterfaceDetailResponse,
    ApiBaseCaseListResponse, ApiBaseCaseItem, ApiTestCaseListResponse, ApiTestCaseItem, AiParseResponse,
    ApiInterfaceDeleteResponse, AiParseRequest, ApiTestCaseUpdateRequest, ApiTestCaseUpdateResponse,
    ApiBaseCaseUpdateRequest, ApiBaseCaseUpdateResponse, ApiTestCaseBatchEditRequest, ApiTestCaseBatchEditResponse,
    ApiBaseCaseGenerateRequest, ApiBaseCaseGenerateResponse, ApiTestCaseGenerateRequest, ApiTestCaseGenerateResponse,
    ApiCompleteTestCaseGenerateRequest, ApiCompleteTestCaseGenerateResponse, ApiBaseCaseDeleteResponse,
    ApiBaseCaseCreateRequest, ApiBaseCaseCreateResponse,
    # Phase 1: Quick Debug
    QuickDebugRequest, QuickDebugResponse, QuickDebugHistoryListResponse, QuickDebugHistoryItem,
    QuickDebugHistoryDetail, CurlImportRequest, CurlImportResponse, CurlExportResponse,
    # Phase 2: Scheduled Task + CI
    ScheduledTaskCreateRequest, ScheduledTaskResponse, ScheduledTaskUpdateRequest, ScheduledTaskListResponse,
    CiTriggerRequest, CiTriggerResponse, CurlToInterfaceRequest,
    # Phase 3: Webhook
    WebhookConfigCreateRequest, WebhookConfigResponse, WebhookConfigUpdateRequest, WebhookConfigListResponse,
)
from .models import ApiInterface, ApiDependencyGroup, ApiDependency, ApiBaseCase, ApiTestCase, \
    QuickDebugHistory, ScheduledTask, WebhookConfig
import httpx
import time
import shlex
import re
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

from service.user.models import User
from service.project.models import Project
from service.test_environment.models import TestEnvironment, TestEnvironmentConfig, TestEnvironmentDb
from service.test_management.models import TestTask, TestSuite, TaskSuiteRelation, SuiteCaseRelation
from service.test_execution.models import ApiCaseRun, TestSuiteRun, TestTaskRun
from utils.permissions import verify_admin_or_project_owner, verify_admin_or_project_editor, \
    verify_admin_or_project_member
from utils.auth import get_current_user
from utils.parser.swagger_document_parser import SwaggerV2Parser
from utils.parser.openapi_document_parser import OpenAPIParser
from utils.parser.ai_parser_api_document import AIAPIDocumentParser
from workflow.api_basecase_workflow import ApiBaseCaseGeneratorWorkFlow
from workflow.api_run_case_wrokflow import ApiRunCaseGeneratorWorkFlow
from workflow.api_case_generator_main_workflow import ApiCaseGenerateMainWorkFlow

router = APIRouter()


@router.post("/{project_id}/import_swagger", response_model=ApiImportResponse, summary="导入Swagger接口文档")
async def import_swagger_apis(
        project_id: int,
        swagger_file: UploadFile = File(..., description="Swagger接口文档JSON文件"),
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_editor)
):
    """
    导入Swagger接口文档到指定项目
    
    参数：
    - project_id: 项目ID
    - swagger_file: Swagger接口文档JSON文件
    
    权限要求：
    - 项目编辑者、负责人或管理员
    
    返回：
    - 导入成功/失败状态和导入的接口数量
    """
    project, current_user = project_user

    imported_count = 0
    failed_count = 0
    error_details = []
    saved_file_path = None

    try:
        # 验证文件类型
        if not swagger_file.filename.endswith('.json'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="只支持JSON格式的Swagger文档"
            )

        # 生成唯一文件名并保存文件到 datas/api_doc 目录
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        original_filename = swagger_file.filename
        file_extension = os.path.splitext(original_filename)[1]
        new_filename = f"swagger_{project_id}_{timestamp}_{unique_id}{file_extension}"

        # 确保 datas/api_doc 目录存在
        api_doc_dir = os.path.join("datas", "api_doc")
        os.makedirs(api_doc_dir, exist_ok=True)

        # 保存文件
        saved_file_path = os.path.join(api_doc_dir, new_filename)
        file_content = await swagger_file.read()

        with open(saved_file_path, "wb") as f:
            f.write(file_content)

        # 验证JSON格式
        try:
            swagger_data = json.loads(file_content)
        except json.JSONDecodeError:
            # 删除已保存的无效文件
            if os.path.exists(saved_file_path):
                os.remove(saved_file_path)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="JSON文件格式错误，请检查文件内容"
            )

        # 使用SwaggerV2Parser解析文档（传入文件路径）
        try:
            parser = SwaggerV2Parser(saved_file_path)
            parsed_apis = parser.parse()
        except Exception as e:
            # 删除已保存的无效文件
            if os.path.exists(saved_file_path):
                os.remove(saved_file_path)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Swagger文档解析失败: {str(e)}"
            )

        # 保存解析的接口到数据库
        for api_info in parsed_apis:
            try:
                # 检查接口是否已存在（基于path和method）
                existing_api = await ApiInterface.get_or_none(
                    project=project,
                    path=api_info.get('path'),
                    method=api_info.get('method')
                )

                if existing_api:
                    # 更新现有接口
                    existing_api.summary = api_info.get('summary', '')
                    existing_api.parameters = api_info.get('parameters', {})
                    existing_api.request_body = api_info.get('requestBody', {})
                    existing_api.responses = api_info.get('responses', {})
                    await existing_api.save()
                else:
                    # 创建新接口
                    await ApiInterface.create(
                        project=project,
                        method=api_info.get('method'),
                        path=api_info.get('path'),
                        summary=api_info.get('summary', ''),
                        parameters=api_info.get('parameters', {}),
                        request_body=api_info.get('requestBody', {}),
                        responses=api_info.get('responses', {})
                    )

                imported_count += 1

            except Exception as e:
                failed_count += 1
                error_details.append({
                    'path': api_info.get('path', 'unknown'),
                    'method': api_info.get('method', 'unknown'),
                    'error': str(e)
                })

        # 构建响应
        success = failed_count == 0
        message = f"导入完成，成功导入 {imported_count} 个接口"
        if failed_count > 0:
            message += f"，失败 {failed_count} 个接口"

        response_details = {
            'total_processed': len(parsed_apis),
            'success_count': imported_count,
            'failed_count': failed_count,
            'saved_file_path': saved_file_path
        }

        if error_details:
            response_details['errors'] = error_details

        return ApiImportResponse(
            success=success,
            message=message,
            imported_count=imported_count,
            failed_count=failed_count,
            details=response_details
        )

    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        # 处理其他未预期的异常
        if saved_file_path and os.path.exists(saved_file_path):
            try:
                os.remove(saved_file_path)
            except:
                pass  # 忽略删除文件时的错误

        error_msg = f"导入过程中发生错误: {str(e)}"
        return ApiImportResponse(
            success=False,
            message=error_msg,
            imported_count=0,
            failed_count=0,
            details={
                'error': error_msg,
                'traceback': traceback.format_exc()
            }
        )


@router.post("/{project_id}/import_openapi", response_model=OpenApiImportResponse, summary="导入OpenAPI接口文档")
async def import_openapi_apis(
        project_id: int,
        openapi_file: UploadFile = File(..., description="OpenAPI接口文档JSON文件"),
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_editor)
):
    """
    导入OpenAPI接口文档到指定项目
    
    参数：
    - project_id: 项目ID
    - openapi_file: OpenAPI接口文档JSON文件
    
    权限要求：
    - 项目编辑者、负责人或管理员
    
    返回：
    - 导入成功/失败状态和导入的接口数量
    """
    project, current_user = project_user

    imported_count = 0
    failed_count = 0
    error_details = []
    saved_file_path = None

    try:
        # 验证文件类型
        if not openapi_file.filename.endswith('.json'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="只支持JSON格式的OpenAPI文档文件"
            )

        # 生成唯一文件名并保存文件
        file_extension = ".json"
        unique_filename = f"openapi_{project_id}_{uuid.uuid4().hex}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{file_extension}"

        # 确保目录存在
        api_doc_dir = os.path.join("datas", "api_doc")
        os.makedirs(api_doc_dir, exist_ok=True)

        # 保存文件
        saved_file_path = os.path.join(api_doc_dir, unique_filename)
        with open(saved_file_path, "wb") as buffer:
            content = await openapi_file.read()
            buffer.write(content)

        # 验证JSON格式
        try:
            with open(saved_file_path, 'r', encoding='utf-8') as f:
                json.load(f)
        except json.JSONDecodeError as e:
            if os.path.exists(saved_file_path):
                os.remove(saved_file_path)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的JSON格式: {str(e)}"
            )

        # 使用OpenAPIParser解析文档
        try:
            parser = OpenAPIParser(saved_file_path)
            api_list = parser.parser()
        except Exception as e:
            if os.path.exists(saved_file_path):
                os.remove(saved_file_path)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"OpenAPI文档解析失败: {str(e)}"
            )

        # 保存解析出的接口到数据库
        for api_data in api_list:
            try:
                # 检查接口是否已存在（基于路径和方法）
                existing_api = await ApiInterface.get_or_none(
                    project_id=project_id,
                    path=api_data.get('path'),
                    method=api_data.get('method')

                )

                if existing_api:
                    # 更新现有接口
                    existing_api.summary = api_data.get('summary', '')
                    existing_api.description = api_data.get('description', '')
                    existing_api.request_params = json.dumps(api_data.get('parameters', {}), ensure_ascii=False)
                    existing_api.request_body = json.dumps(api_data.get('requestBody', {}), ensure_ascii=False)
                    existing_api.response_body = json.dumps(api_data.get('responses', []), ensure_ascii=False)
                    await existing_api.save()
                else:
                    # 创建新接口
                    new_api = ApiInterface(
                        project_id=project_id,
                        summary=api_data.get('summary', ''),
                        description=api_data.get('description', ''),
                        path=api_data.get('path'),
                        method=api_data.get('method'),
                        parameters=json.dumps(api_data.get('parameters', {}), ensure_ascii=False),
                        request_body=json.dumps(api_data.get('requestBody', {}), ensure_ascii=False),
                        responses=json.dumps(api_data.get('responses', []), ensure_ascii=False)
                    )
                    await new_api.save()
                imported_count += 1

            except Exception as e:
                failed_count += 1
                error_details.append({
                    'api': f"{api_data.get('method', 'UNKNOWN')} {api_data.get('path', 'UNKNOWN')}",
                    'error': str(e)
                })

        # 构建响应
        success = failed_count == 0
        if success:
            message = f"成功导入 {imported_count} 个接口"
        else:
            message = f"导入完成，成功 {imported_count} 个，失败 {failed_count} 个"

        response_details = {
            'saved_file_path': saved_file_path,
            'total_apis_found': len(api_list)
        }

        if error_details:
            response_details['errors'] = error_details

        return OpenApiImportResponse(
            success=success,
            message=message,
            imported_count=imported_count,
            failed_count=failed_count,
            details=response_details
        )

    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        # 处理其他未预期的异常
        if saved_file_path and os.path.exists(saved_file_path):
            try:
                os.remove(saved_file_path)
            except:
                pass  # 忽略删除文件时的错误

        error_msg = f"导入过程中发生错误: {str(e)}"
        return OpenApiImportResponse(
            success=False,
            message=error_msg,
            imported_count=0,
            failed_count=0,
            details={
                'error': error_msg,
                'traceback': traceback.format_exc()
            }
        )


@router.post("/{project_id}/ai_parse", response_model=AiParseResponse, summary="AI智能解析接口文档")
async def ai_parse_api_document(
        project_id: int,
        request: AiParseRequest,
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_editor)
):
    """
    使用AI智能解析接口文档的文字描述内容
    
    Args:
        project_id: 项目ID
        request: AI解析请求，包含接口文档的文字描述内容
        project_user: 项目和用户信息（权限验证）
    
    Returns:
        AiParseResponse: 解析结果，包含成功状态、消息和解析出的结构化数据
    """
    try:
        # 验证项目ID是否匹配
        project, user = project_user
        if project.id != project_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="项目ID不匹配"
            )

        # 验证输入参数
        if not request.api_document or not request.api_document.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="接口文档内容不能为空"
            )

        # 使用AI解析器解析接口文档
        ai_parser = AIAPIDocumentParser()
        parsed_result = ai_parser.parser(request.api_document)

        # 检查解析结果
        if not parsed_result:
            return AiParseResponse(
                success=False,
                message="AI解析失败，未能从文档中提取到有效的接口信息",
                parsed_data=None,
                error_details="解析器返回空结果"
            )

        # 返回成功结果
        return AiParseResponse(
            success=True,
            message="AI解析成功",
            parsed_data=parsed_result,
            error_details=None
        )

    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        # 处理其他未预期的异常
        error_msg = f"AI解析过程中发生错误: {str(e)}"
        return AiParseResponse(
            success=False,
            message=error_msg,
            parsed_data=None,
            error_details=traceback.format_exc()
        )


@router.get("/{project_id}/interfaces", response_model=ApiInterfaceListResponse, summary="获取项目接口列表")
async def get_project_interfaces(
        project_id: int,
        page: int = 1,
        page_size: int = 20,
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_member)
):
    """
    获取项目接口列表（分页）
    
    参数：
    - project_id: 项目ID
    - page: 页码，从1开始
    - page_size: 每页数量，默认20
    
    权限：项目成员和管理员可以访问
    """
    try:
        project, current_user = project_user

        # 验证分页参数
        if page < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="页码必须大于0"
            )
        if page_size < 1 or page_size > 2000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="每页数量必须在1-2000之间"
            )

        # 计算偏移量
        offset = (page - 1) * page_size

        # 查询接口总数
        total = await ApiInterface.filter(project_id=project_id).count()

        # 查询接口列表
        interfaces = await ApiInterface.filter(project_id=project_id).offset(offset).limit(page_size).order_by(
            'created_at')

        # 计算总页数
        total_pages = (total + page_size - 1) // page_size

        # 构造响应数据
        interface_items = []
        for interface in interfaces:
            interface_items.append({
                "id": interface.id,
                "method": interface.method,
                "path": interface.path,
                "summary": interface.summary,
                "created_at": interface.created_at,
                "updated_at": interface.updated_at
            })

        return ApiInterfaceListResponse(
            interfaces=interface_items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )

    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        # 处理其他未预期的异常
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取接口列表时发生错误: {str(e)}"
        )


@router.post("/{project_id}/interfaces", response_model=ApiInterfaceCreateResponse, summary="新增接口")
async def create_api_interface(
        project_id: int,
        interface_data: ApiInterfaceCreateRequest,
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_editor)
):
    """
    新增接口
    
    权限要求：
    - 只有项目负责人、项目编辑者和管理员可以访问
    
    参数：
    - project_id: 项目ID
    - interface_data: 接口数据
    
    返回：
    - 新创建的接口信息
    """
    project, current_user = project_user

    try:
        # 检查接口路径和方法是否重复
        existing_interface = await ApiInterface.get_or_none(
            project=project,
            path=interface_data.path,
            method=interface_data.method
        )
        if existing_interface:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该项目中已存在相同路径和方法的接口"
            )

        # 创建新接口
        new_interface = await ApiInterface.create(
            project=project,
            method=interface_data.method,
            path=interface_data.path,
            summary=interface_data.summary,
            parameters=interface_data.parameters,
            request_body=interface_data.request_body,
            responses=interface_data.responses
        )

        return ApiInterfaceCreateResponse(
            id=new_interface.id,
            method=new_interface.method,
            path=new_interface.path,
            summary=new_interface.summary,
            parameters=new_interface.parameters,
            request_body=new_interface.request_body,
            responses=new_interface.responses,
            created_at=new_interface.created_at,
            updated_at=new_interface.updated_at
        )

    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        # 处理其他未预期的异常
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建接口时发生错误: {str(e)}"
        )


@router.delete("/{project_id}/interfaces/{interface_id}", response_model=ApiInterfaceDeleteResponse, summary="删除接口")
async def delete_api_interface(
        project_id: int,
        interface_id: int,
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_editor)
):
    """
    删除接口
    
    权限要求：
    - 只有项目成员和管理员可以删除接口
    
    业务逻辑：
    - 验证接口是否存在
    - 验证接口是否属于指定项目
    - 删除接口
    
    参数：
    - project_id: 项目ID
    - interface_id: 接口ID
    """
    project, current_user = project_user

    try:
        # 查询接口是否存在
        interface = await ApiInterface.get_or_none(id=interface_id)
        if not interface:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定的接口不存在"
            )

        # 验证接口是否属于指定项目
        if interface.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="接口不属于指定项目"
            )

        # 删除接口
        await interface.delete()

        return ApiInterfaceDeleteResponse(message="接口删除成功")

    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除接口失败，请稍后重试"
        )


@router.put("/{project_id}/interfaces/{interface_id}", response_model=ApiInterfaceUpdateResponse, summary="编辑接口")
async def update_api_interface(
        project_id: int,
        interface_id: int,
        request: ApiInterfaceUpdateRequest,
        project_user: tuple = Depends(verify_admin_or_project_editor)
):
    """
    编辑接口
    
    权限要求：项目负责人、项目编辑器或管理员
    """
    project, current_user = project_user

    try:
        # 查询接口是否存在
        interface = await ApiInterface.get_or_none(id=interface_id)
        if not interface:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定的接口不存在"
            )

        # 验证接口是否属于指定项目
        if interface.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="接口不属于指定项目"
            )

        # 更新接口信息（只更新提供的字段）
        update_data = {}
        if request.method is not None:
            update_data['method'] = request.method
        if request.path is not None:
            update_data['path'] = request.path
        if request.summary is not None:
            update_data['summary'] = request.summary
        if request.parameters is not None:
            update_data['parameters'] = request.parameters
        if request.request_body is not None:
            update_data['request_body'] = request.request_body
        if request.responses is not None:
            update_data['responses'] = request.responses

        # 如果有更新数据，则执行更新
        if update_data:
            update_data['updated_at'] = datetime.now()
            await interface.update_from_dict(update_data)
            await interface.save()

        # 重新获取更新后的接口信息
        updated_interface = await ApiInterface.get(id=interface_id)

        # 确保responses字段是列表格式
        responses_data = updated_interface.responses or []
        if isinstance(responses_data, dict):
            responses_data = []

        return ApiInterfaceUpdateResponse(
            id=updated_interface.id,
            method=updated_interface.method,
            path=updated_interface.path,
            summary=updated_interface.summary,
            parameters=updated_interface.parameters or {},
            request_body=updated_interface.request_body or {},
            responses=responses_data,
            created_at=updated_interface.created_at,
            updated_at=updated_interface.updated_at
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="编辑接口失败，请稍后重试"
        )


@router.post("/{project_id}/dependency-groups", response_model=ApiDependencyGroupCreateResponse,
             summary="创建接口依赖分组")
async def create_api_dependency_group(
        project_id: int,
        group_data: ApiDependencyGroupCreateRequest,
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_editor)
):
    """
    创建接口依赖分组
    
    权限要求：
    - 只有项目负责人、项目编辑者和管理员可以访问
    
    参数：
    - project_id: 项目ID
    - group_data: 分组数据
    
    返回：
    - 新创建的分组信息
    """
    project, current_user = project_user

    try:
        # 验证目标接口是否存在且属于当前项目
        target_interface = await ApiInterface.get_or_none(
            id=group_data.target_interface_id,
            project=project
        )
        if not target_interface:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定的目标接口不存在或不属于当前项目"
            )

        # 检查分组名称是否重复
        existing_group = await ApiDependencyGroup.get_or_none(
            project=project,
            name=group_data.name
        )
        if existing_group:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该项目中已存在相同名称的依赖分组"
            )

        # 创建新的依赖分组
        new_group = await ApiDependencyGroup.create(
            project=project,
            creator=current_user,
            target_interface=target_interface,
            name=group_data.name,
            description=group_data.description
        )

        return ApiDependencyGroupCreateResponse(
            id=new_group.id,
            name=new_group.name,
            description=new_group.description,
            target_interface_id=new_group.target_interface_id,
            created_at=new_group.created_at,
            updated_at=new_group.updated_at
        )

    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        # 处理其他未预期的异常
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建接口依赖分组时发生错误: {str(e)}"
        )


@router.put("/{project_id}/dependency-groups/{group_id}", response_model=ApiDependencyGroupUpdateResponse,
            summary="更新接口依赖分组")
async def update_api_dependency_group(
        project_id: int,
        group_id: int,
        group_data: ApiDependencyGroupUpdateRequest,
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_editor)
):
    """
    更新接口依赖分组
    
    权限要求：
    - 只有项目负责人、项目编辑者和管理员可以访问
    
    参数：
    - project_id: 项目ID
    - group_id: 分组ID
    - group_data: 更新的分组数据
    
    返回：
    - 更新后的分组信息
    """
    project, current_user = project_user

    try:
        # 验证依赖分组是否存在且属于当前项目
        dependency_group = await ApiDependencyGroup.get_or_none(
            id=group_id,
            project=project
        )
        if not dependency_group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定的依赖分组不存在或不属于当前项目"
            )

        # 检查分组名称是否重复（如果要更新名称）
        if group_data.name and group_data.name != dependency_group.name:
            existing_group = await ApiDependencyGroup.get_or_none(
                project=project,
                name=group_data.name
            )
            if existing_group:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="该项目中已存在相同名称的依赖分组"
                )

        # 更新分组信息
        update_data = {}
        if group_data.name is not None:
            update_data['name'] = group_data.name
        if group_data.description is not None:
            update_data['description'] = group_data.description

        if update_data:
            await dependency_group.update_from_dict(update_data)
            await dependency_group.save()

        return ApiDependencyGroupUpdateResponse(
            id=dependency_group.id,
            name=dependency_group.name,
            description=dependency_group.description,
            target_interface_id=dependency_group.target_interface_id,
            created_at=dependency_group.created_at,
            updated_at=dependency_group.updated_at
        )

    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        # 处理其他未预期的异常
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新接口依赖分组时发生错误: {str(e)}"
        )


@router.get("/{project_id}/dependency-groups", response_model=ApiDependencyGroupListResponse,
            summary="获取接口依赖分组列表")
async def get_api_dependency_groups(
        project_id: int,
        page: int = 1,
        page_size: int = 20,
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_editor)
):
    """
    获取接口依赖分组列表（分页）
    
    参数：
    - project_id: 项目ID
    - page: 页码，从1开始
    - page_size: 每页数量，默认20
    
    权限：项目负责人、项目编辑者和管理员可以访问
    """
    try:
        project, current_user = project_user

        # 验证分页参数
        if page < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="页码必须大于0"
            )
        if page_size < 1 or page_size > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="每页数量必须在1-100之间"
            )

        # 计算偏移量
        offset = (page - 1) * page_size

        # 查询依赖分组总数
        total = await ApiDependencyGroup.filter(project_id=project_id).count()

        # 查询依赖分组列表
        dependency_groups = await ApiDependencyGroup.filter(project_id=project_id).offset(offset).limit(
            page_size).order_by('created_at')

        # 计算总页数
        total_pages = (total + page_size - 1) // page_size

        # 构造响应数据
        group_items = []
        for group in dependency_groups:
            group_items.append({
                "id": group.id,
                "name": group.name,
                "description": group.description,
                "target_interface_id": group.target_interface_id,
                "created_at": group.created_at,
                "updated_at": group.updated_at
            })

        return ApiDependencyGroupListResponse(
            dependency_groups=group_items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )

    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        # 处理其他未预期的异常
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取接口依赖分组列表时发生错误: {str(e)}"
        )


@router.post("/{project_id}/dependency-groups/{group_id}/dependencies", response_model=ApiDependencyCreateResponse,
             summary="添加接口依赖")
async def create_api_dependency(
        project_id: int,
        group_id: int,
        dependency_data: ApiDependencyCreateRequest,
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_editor)
):
    """
    添加接口依赖
    
    权限要求：
    - 项目负责人
    - 项目编辑者
    - 管理员
    
    参数：
    - project_id: 项目ID
    - group_id: 依赖分组ID
    - dependency_data: 依赖数据
    
    返回：
    - 新创建的依赖信息
    """
    project, current_user = project_user

    try:
        # 验证依赖分组是否存在且属于当前项目
        dependency_group = await ApiDependencyGroup.get_or_none(
            id=group_id,
            project=project
        )
        if not dependency_group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定的依赖分组不存在或不属于当前项目"
            )

        # 检查依赖名称在该分组中是否重复
        existing_dependency = await ApiDependency.get_or_none(
            dependency_group=dependency_group,
            name=dependency_data.name
        )
        if existing_dependency:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该分组中已存在相同名称的依赖"
            )

        # 验证依赖类型
        valid_types = ["header", "param", "body", "response"]
        if dependency_data.dependency_type not in valid_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"依赖类型必须是以下之一: {', '.join(valid_types)}"
            )

        # 创建新的接口依赖
        new_dependency = await ApiDependency.create(
            dependency_group=dependency_group,
            name=dependency_data.name,
            description=dependency_data.description,
            dependency_type=dependency_data.dependency_type,
            source_interface_id=dependency_data.source_interface_id,
            source_field_path=dependency_data.source_field_path,
            target_field_name=dependency_data.target_field_name,
            transform_rule=dependency_data.transform_rule,
            is_active=dependency_data.is_active
        )

        # 查询源接口信息
        source_interface_name = None
        source_interface_method = None
        source_interface_path = None
        if new_dependency.source_interface_id:
            source_interface = await ApiInterface.get_or_none(id=new_dependency.source_interface_id)
            if source_interface:
                source_interface_name = source_interface.summary
                source_interface_method = source_interface.method
                source_interface_path = source_interface.path

        return ApiDependencyCreateResponse(
            id=new_dependency.id,
            name=new_dependency.name,
            description=new_dependency.description,
            dependency_type=new_dependency.dependency_type,
            source_interface_id=new_dependency.source_interface_id,
            source_interface_name=source_interface_name,
            source_interface_method=source_interface_method,
            source_interface_path=source_interface_path,
            source_field_path=new_dependency.source_field_path,
            target_field_name=new_dependency.target_field_name,
            transform_rule=new_dependency.transform_rule,
            is_active=new_dependency.is_active,
            created_at=new_dependency.created_at,
            updated_at=new_dependency.updated_at
        )

    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        # 处理其他未预期的异常
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建接口依赖时发生错误: {str(e)}"
        )


@router.put("/{project_id}/dependency-groups/{group_id}/dependencies/{dependency_id}",
            response_model=ApiDependencyUpdateResponse, summary="编辑接口依赖")
async def update_api_dependency(
        project_id: int,
        group_id: int,
        dependency_id: int,
        dependency_data: ApiDependencyUpdateRequest,
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_editor)
):
    """
    编辑接口依赖
    
    权限要求：项目负责人、项目编辑器或管理员
    """
    project, current_user = project_user

    try:
        # 查询依赖分组是否存在
        dependency_group = await ApiDependencyGroup.get_or_none(id=group_id)
        if not dependency_group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定的依赖分组不存在"
            )

        # 验证依赖分组是否属于指定项目
        if dependency_group.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="依赖分组不属于指定项目"
            )

        # 查询接口依赖是否存在
        dependency = await ApiDependency.get_or_none(id=dependency_id)
        if not dependency:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定的接口依赖不存在"
            )

        # 验证接口依赖是否属于指定分组
        if dependency.dependency_group_id != group_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="接口依赖不属于指定分组"
            )

        # 检查依赖名称是否重复（如果要更新名称）
        if dependency_data.name and dependency_data.name != dependency.name:
            existing_dependency = await ApiDependency.get_or_none(
                dependency_group_id=group_id,
                name=dependency_data.name
            )
            if existing_dependency:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="该分组中已存在同名接口依赖"
                )

        # 验证依赖类型的有效性（如果要更新依赖类型）
        if dependency_data.dependency_type:
            valid_types = ["header", "param", "body", "response"]
            if dependency_data.dependency_type not in valid_types:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"无效的依赖类型，只能设置为: {', '.join(valid_types)}"
                )

        # 更新接口依赖信息（只更新提供的字段）
        update_data = {}
        if dependency_data.name is not None:
            update_data['name'] = dependency_data.name
        if dependency_data.description is not None:
            update_data['description'] = dependency_data.description
        if dependency_data.dependency_type is not None:
            update_data['dependency_type'] = dependency_data.dependency_type
        if dependency_data.source_interface_id is not None:
            update_data['source_interface_id'] = dependency_data.source_interface_id
        if dependency_data.source_field_path is not None:
            update_data['source_field_path'] = dependency_data.source_field_path
        if dependency_data.target_field_name is not None:
            update_data['target_field_name'] = dependency_data.target_field_name
        if dependency_data.transform_rule is not None:
            update_data['transform_rule'] = dependency_data.transform_rule
        if dependency_data.is_active is not None:
            update_data['is_active'] = dependency_data.is_active

        # 如果有更新数据，则执行更新
        if update_data:
            update_data['updated_at'] = datetime.now()
            await dependency.update_from_dict(update_data)
            await dependency.save()

        # 重新获取更新后的依赖信息
        updated_dependency = await ApiDependency.get(id=dependency_id)

        # 查询源接口信息
        source_interface_name = None
        source_interface_method = None
        source_interface_path = None
        if updated_dependency.source_interface_id:
            source_interface = await ApiInterface.get_or_none(id=updated_dependency.source_interface_id)
            if source_interface:
                source_interface_name = source_interface.summary
                source_interface_method = source_interface.method
                source_interface_path = source_interface.path

        return ApiDependencyUpdateResponse(
            id=updated_dependency.id,
            name=updated_dependency.name,
            description=updated_dependency.description,
            dependency_type=updated_dependency.dependency_type,
            source_interface_id=updated_dependency.source_interface_id,
            source_interface_name=source_interface_name,
            source_interface_method=source_interface_method,
            source_interface_path=source_interface_path,
            source_field_path=updated_dependency.source_field_path,
            target_field_name=updated_dependency.target_field_name,
            transform_rule=updated_dependency.transform_rule,
            is_active=updated_dependency.is_active,
            created_at=updated_dependency.created_at,
            updated_at=updated_dependency.updated_at
        )

    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        # 处理其他未预期的异常
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"编辑接口依赖时发生错误: {str(e)}"
        )


@router.delete("/{project_id}/dependency-groups/{group_id}/dependencies/{dependency_id}",
               response_model=ApiDependencyDeleteResponse, summary="删除接口依赖")
async def delete_api_dependency(
        project_id: int,
        group_id: int,
        dependency_id: int,
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_editor)
):
    """
    删除接口依赖
    
    权限要求：
    - 只有项目成员和管理员可以删除接口依赖
    
    业务逻辑：
    - 验证依赖组是否存在且属于指定项目
    - 验证接口依赖是否存在且属于指定依赖组
    - 删除接口依赖
    
    参数：
    - project_id: 项目ID
    - group_id: 依赖组ID
    - dependency_id: 接口依赖ID
    """
    project, current_user = project_user

    try:
        # 查询依赖组是否存在
        dependency_group = await ApiDependencyGroup.get_or_none(id=group_id)
        if not dependency_group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定的依赖组不存在"
            )

        # 验证依赖组是否属于指定项目
        if dependency_group.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="依赖组不属于指定项目"
            )

        # 查询接口依赖是否存在
        dependency = await ApiDependency.get_or_none(id=dependency_id)
        if not dependency:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定的接口依赖不存在"
            )

        # 验证接口依赖是否属于指定依赖组
        if dependency.dependency_group_id != group_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="接口依赖不属于指定依赖组"
            )

        # 删除接口依赖
        await dependency.delete()

        return ApiDependencyDeleteResponse(message="接口依赖删除成功")

    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        # 处理其他未预期的异常
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除接口依赖时发生错误: {str(e)}"
        )


@router.delete("/{project_id}/dependency-groups/{group_id}", response_model=ApiDependencyGroupDeleteResponse,
               summary="删除接口依赖分组")
async def delete_api_dependency_group(
        project_id: int,
        group_id: int,
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_editor)
):
    """
    删除接口依赖分组
    
    权限要求：
    - 只有项目负责人、项目编辑者和管理员可以删除接口依赖分组
    
    业务逻辑：
    - 验证依赖分组是否存在且属于指定项目
    - 使用数据库事务同步删除分组中的所有依赖关系
    - 删除依赖分组
    
    参数：
    - project_id: 项目ID
    - group_id: 依赖分组ID
    """
    project, current_user = project_user

    try:
        # 查询依赖分组是否存在
        dependency_group = await ApiDependencyGroup.get_or_none(id=group_id)
        if not dependency_group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定的依赖分组不存在"
            )

        # 验证依赖分组是否属于指定项目
        if dependency_group.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="依赖分组不属于指定项目"
            )

        # 使用数据库事务确保数据一致性
        async with in_transaction() as conn:
            # 先删除分组中的所有依赖关系
            await ApiDependency.filter(dependency_group_id=group_id).using_db(conn).delete()

            # 再删除依赖分组
            await ApiDependencyGroup.filter(id=group_id).using_db(conn).delete()

        return ApiDependencyGroupDeleteResponse(message="接口依赖分组删除成功")

    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        # 处理其他未预期的异常
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除接口依赖分组时发生错误: {str(e)}"
        )


@router.get("/{project_id}/interfaces/{interface_id}", response_model=ApiInterfaceDetailResponse,
            summary="获取接口详情")
async def get_interface_detail(
        project_id: int,
        interface_id: int,
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_member)
):
    """
    获取接口详情，包含关联的依赖分组和详细数据
    
    参数：
    - project_id: 项目ID
    - interface_id: 接口ID
    
    权限：项目成员和管理员可以访问
    """
    try:
        project, current_user = project_user

        # 查询接口是否存在且属于指定项目
        interface = await ApiInterface.filter(id=interface_id, project_id=project_id).first()
        if not interface:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="接口不存在或不属于该项目"
            )

        # 使用数据库事务确保数据一致性
        async with in_transaction() as conn:
            # 查询接口关联的依赖分组
            dependency_groups = await ApiDependencyGroup.filter(
                target_interface_id=interface_id
            ).order_by('created_at').using_db(conn)

            # 构造依赖分组详情列表
            dependency_group_details = []
            for group in dependency_groups:
                # 查询每个分组下的依赖项
                dependencies = await ApiDependency.filter(
                    dependency_group_id=group.id
                ).order_by('created_at').using_db(conn)

                # 构造依赖项列表
                dependency_items = []
                for dependency in dependencies:
                    # 查询源接口信息
                    source_interface = None
                    source_interface_name = None
                    source_interface_method = None
                    source_interface_path = None
                    
                    if dependency.source_interface_id:
                        source_interface = await ApiInterface.filter(
                            id=dependency.source_interface_id
                        ).first().using_db(conn)
                        
                        if source_interface:
                            source_interface_name = source_interface.summary
                            source_interface_method = source_interface.method
                            source_interface_path = source_interface.path
                    
                    dependency_items.append({
                        "id": dependency.id,
                        "name": dependency.name,
                        "description": dependency.description,
                        "dependency_type": dependency.dependency_type,
                        "source_interface_id": dependency.source_interface_id,
                        "source_interface_name": source_interface_name,
                        "source_interface_method": source_interface_method,
                        "source_interface_path": source_interface_path,
                        "source_field_path": dependency.source_field_path,
                        "target_field_name": dependency.target_field_name,
                        "transform_rule": dependency.transform_rule,
                        "is_active": dependency.is_active,
                        "created_at": dependency.created_at,
                        "updated_at": dependency.updated_at
                    })

                # 构造分组详情
                dependency_group_details.append({
                    "id": group.id,
                    "name": group.name,
                    "description": group.description,
                    "created_at": group.created_at,
                    "updated_at": group.updated_at,
                    "dependencies": dependency_items
                })

        # 构造接口详情响应
        # 兼容与校正字段类型，满足响应模型要求
        parameters_data = interface.parameters or {}
        if isinstance(parameters_data, list):
            parameters_data = {}

        request_body_data = interface.request_body or {}
        if isinstance(request_body_data, list):
            request_body_data = {}

        responses_data = interface.responses or []
        if isinstance(responses_data, dict):
            responses_data = []

        return ApiInterfaceDetailResponse(
            id=interface.id,
            method=interface.method,
            path=interface.path,
            summary=interface.summary,
            parameters=parameters_data,
            request_body=request_body_data,
            responses=responses_data,
            created_at=interface.created_at,
            updated_at=interface.updated_at,
            dependency_groups=dependency_group_details
        )

    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        # 处理其他未预期的异常
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取接口详情时发生错误: {str(e)}"
        )


@router.get("/{project_id}/base-cases", response_model=ApiBaseCaseListResponse, summary="获取基础用例列表")
async def get_base_cases_list(
        project_id: int,
        page: int = Query(1, ge=1, description="页码"),
        page_size: int = Query(10, ge=1, le=100, description="每页数量"),
        interface_id: Optional[int] = Query(None, description="接口ID过滤"),
        project_user: tuple = Depends(verify_admin_or_project_member)
):
    """
    获取基础用例列表
    
    权限要求：项目成员或管理员
    """
    project, current_user = project_user

    try:
        async with in_transaction():
            # 获取该项目下的所有接口ID
            project_interfaces = await ApiInterface.filter(project_id=project_id).values_list('id', flat=True)

            if not project_interfaces:
                # 如果项目下没有接口，返回空列表
                return ApiBaseCaseListResponse(
                    base_cases=[],
                    total=0,
                    page=page,
                    page_size=page_size,
                    total_pages=0
                )

            # 构建查询条件 - 基础用例的interface_id必须在项目接口列表中
            interface_id_strs = [str(iid) for iid in project_interfaces]
            query = ApiBaseCase.filter(interface_id__in=interface_id_strs)

            # 如果指定了接口ID，添加接口过滤条件
            if interface_id is not None:
                # 验证接口是否存在且属于该项目
                if interface_id not in project_interfaces:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="指定的接口不存在或不属于该项目"
                    )
                query = query.filter(interface_id=str(interface_id))

            # 获取总数
            total = await query.count()

            # 计算分页
            offset = (page - 1) * page_size
            total_pages = (total + page_size - 1) // page_size

            # 获取分页数据，并联表加载接口以获取名称
            base_cases = await query.offset(offset).limit(page_size).order_by('-created_at').select_related('interface')

            # 构造响应数据
            def ensure_list_of_dicts(value):
                """将可能为字符串、字典或字符串列表的值规范为字典列表，以满足Schema校验。"""
                if value is None:
                    return []
                # 已是字典列表
                if isinstance(value, list) and (len(value) == 0 or isinstance(value[0], dict)):
                    return value
                # 字典 -> 包装成列表
                if isinstance(value, dict):
                    return [value]
                # 字符串列表 -> 转为带text键的字典列表
                if isinstance(value, list):
                    return [{"text": str(item)} for item in value]
                # 其它类型（如纯字符串）
                try:
                    # 尝试解析为JSON对象或数组
                    parsed = json.loads(value) if isinstance(value, str) else value
                    if isinstance(parsed, dict):
                        return [parsed]
                    if isinstance(parsed, list):
                        if len(parsed) == 0 or isinstance(parsed[0], dict):
                            return parsed
                        return [{"text": str(item)} for item in parsed]
                except Exception:
                    pass
                return [{"text": str(value)}]

            base_case_items = []
            for base_case in base_cases:
                # 接口名称优先取summary，无则回退到path
                interface_name = None
                try:
                    iface = getattr(base_case, 'interface', None)
                    if iface:
                        interface_name = getattr(iface, 'summary', None) or getattr(iface, 'path', None)
                except Exception:
                    interface_name = None
                base_case_items.append(ApiBaseCaseItem(
                    id=base_case.id,
                    interface_id=str(base_case.interface_id),
                    interface_name=interface_name,
                    name=base_case.name,
                    steps=ensure_list_of_dicts(base_case.steps),
                    expected=ensure_list_of_dicts(base_case.expected),
                    status=base_case.status,
                    created_at=base_case.created_at,
                    updated_at=base_case.updated_at
                ))

            return ApiBaseCaseListResponse(
                base_cases=base_case_items,
                total=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages
            )

    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        # 处理其他未预期的异常
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取基础用例列表时发生错误: {str(e)}"
        )


@router.get("/{project_id}/test-cases", response_model=ApiTestCaseListResponse, summary="获取接口测试用例列表")
async def get_test_cases_list(
        project_id: int,
        page: int = Query(1, ge=1, description="页码"),
        page_size: int = Query(10, ge=1, le=100, description="每页数量"),
        interface_id: Optional[int] = Query(None, description="接口ID过滤"),
        keyword: Optional[str] = Query(None, description="按用例名称关键字过滤(模糊匹配)"),
        project_user: tuple = Depends(verify_admin_or_project_editor)
):
    """
    获取接口测试用例列表
    
    权限校验：
    - 只有项目成员和管理员可以访问
    
    过滤条件：
    - 通过项目进行过滤，必传参数
    - 通过接口进行过滤，非必传参数
    
    实现分页返回的功能
    """
    project, current_user = project_user

    try:
        async with in_transaction():
            # 获取该项目下的所有接口ID
            project_interfaces = await ApiInterface.filter(project_id=project_id).values_list('id', flat=True)

            if not project_interfaces:
                # 如果项目下没有接口，返回空列表
                return ApiTestCaseListResponse(
                    test_cases=[],
                    total=0,
                    page=page,
                    page_size=page_size,
                    total_pages=0
                )

            # 获取该项目下的所有基础用例ID（通过interface_id关联）
            interface_id_strs = [str(iid) for iid in project_interfaces]
            project_base_cases = await ApiBaseCase.filter(interface_id__in=interface_id_strs).values_list('id',
                                                                                                          flat=True)

            if not project_base_cases:
                # 如果项目下没有基础用例，返回空列表
                return ApiTestCaseListResponse(
                    test_cases=[],
                    total=0,
                    page=page,
                    page_size=page_size,
                    total_pages=0
                )

            # 构建查询条件 - 测试用例的base_case_id必须在项目基础用例列表中
            base_case_id_strs = [str(bcid) for bcid in project_base_cases]
            query = ApiTestCase.filter(base_case_id__in=base_case_id_strs)

            # 如果指定了接口ID，添加接口过滤条件
            if interface_id is not None:
                # 验证接口是否存在且属于该项目
                if interface_id not in project_interfaces:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="指定的接口不存在或不属于该项目"
                    )
                # 获取该接口下的基础用例ID
                interface_base_cases = await ApiBaseCase.filter(interface_id=str(interface_id)).values_list('id',
                                                                                                            flat=True)
                interface_base_case_strs = [str(bcid) for bcid in interface_base_cases]
                query = query.filter(base_case_id__in=interface_base_case_strs)

            # 名称关键词过滤（模糊匹配）
            if keyword:
                query = query.filter(name__icontains=keyword)

            # 获取总数
            total = await query.count()

            # 计算分页
            offset = (page - 1) * page_size
            total_pages = (total + page_size - 1) // page_size

            # 获取分页数据
            test_cases = await query.offset(offset).limit(page_size).order_by('-created_at')

            # 构造响应数据
            test_case_items = []
            for test_case in test_cases:
                test_case_items.append(ApiTestCaseItem(
                    id=test_case.id,
                    base_case_id=test_case.base_case_id,
                    name=test_case.name,
                    description=test_case.description,
                    interface_name=test_case.interface_name,
                    type=test_case.type,
                    preconditions=test_case.preconditions,
                    request=test_case.request,
                    assertions=test_case.assertions,
                    status=test_case.status,
                    generation_count=test_case.generation_count,
                    created_at=test_case.created_at,
                    updated_at=test_case.updated_at
                ))

            return ApiTestCaseListResponse(
                test_cases=test_case_items,
                total=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages
            )

    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        # 处理其他未预期的异常
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取接口测试用例列表时发生错误: {str(e)}"
        )


@router.get("/{project_id}/test-cases/{test_case_id}", response_model=ApiTestCaseUpdateResponse,
            summary="获取接口测试用例详情")
async def get_test_case_detail(
        project_id: int,
        test_case_id: int,
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_member)
):
    """
    获取接口测试用例详情
    
    Args:
        project_id: 项目ID
        test_case_id: 测试用例ID
        project_user: 项目和用户信息（通过权限验证）
    
    Returns:
        ApiTestCaseUpdateResponse: 测试用例详情信息
    
    Raises:
        HTTPException: 当项目不存在、用例不存在或权限不足时
    """
    project, current_user = project_user
    try:
        # 验证测试用例是否存在
        test_case = await ApiTestCase.get_or_none(id=test_case_id)
        if not test_case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="测试用例不存在"
            )

        # 验证测试用例是否属于该项目
        # 通过base_case_id -> ApiBaseCase -> interface_id -> ApiInterface -> project验证
        base_case = await ApiBaseCase.get_or_none(id=test_case.base_case_id)
        if not base_case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="关联的基础用例不存在"
            )

        interface = await ApiInterface.get_or_none(id=base_case.interface_id)
        if not interface or interface.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="测试用例不属于该项目"
            )

        # 返回测试用例详情
        return ApiTestCaseUpdateResponse(
            id=test_case.id,
            base_case_id=test_case.base_case_id,
            name=test_case.name,
            description=test_case.description,
            interface_name=test_case.interface_name,
            type=test_case.type,
            preconditions=test_case.preconditions,
            request=test_case.request,
            assertions=test_case.assertions,
            status=test_case.status,
            generation_count=test_case.generation_count,
            created_at=test_case.created_at,
            updated_at=test_case.updated_at
        )

    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        # 处理其他未预期的异常
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取测试用例详情时发生错误: {str(e)}"
        )


@router.put("/{project_id}/test-cases/{test_case_id}", response_model=ApiTestCaseUpdateResponse,
            summary="编辑接口测试用例")
async def update_test_case(
        project_id: int,
        test_case_id: int,
        request: ApiTestCaseUpdateRequest,
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_member)
):
    """
    编辑接口测试用例
    
    Args:
        project_id: 项目ID
        test_case_id: 测试用例ID
        request: 编辑请求数据
        current_user: 当前用户（通过权限验证）
    
    Returns:
        ApiTestCaseUpdateResponse: 编辑后的测试用例信息
    
    Raises:
        HTTPException: 当项目不存在、用例不存在或权限不足时
    """
    project, current_user = project_user
    try:
        async with in_transaction():
            # 验证测试用例是否存在
            test_case = await ApiTestCase.get_or_none(id=test_case_id)
            if not test_case:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="测试用例不存在"
                )

            # 验证测试用例是否属于该项目
            # 通过base_case_id -> ApiBaseCase -> interface_id -> ApiInterface -> project验证
            base_case = await ApiBaseCase.get_or_none(id=test_case.base_case_id)
            if not base_case:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="关联的基础用例不存在"
                )

            interface = await ApiInterface.get_or_none(id=base_case.interface_id)
            if not interface or interface.project_id != project_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="测试用例不属于该项目"
                )

            # 更新测试用例字段
            update_data = {}
            if request.name is not None:
                update_data['name'] = request.name
            if request.description is not None:
                update_data['description'] = request.description
            if request.interface_name is not None:
                update_data['interface_name'] = request.interface_name
            if request.type is not None:
                # 验证类型值
                if request.type not in ['api', 'business']:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="用例类型必须是 'api' 或 'business'"
                    )
                update_data['type'] = request.type
            if request.preconditions is not None:
                update_data['preconditions'] = request.preconditions
            if request.request is not None:
                update_data['request'] = request.request
            if request.assertions is not None:
                update_data['assertions'] = request.assertions
            if request.status is not None:
                # 验证状态值
                if request.status not in ['pending', 'ready', 'disabled']:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="用例状态必须是 'pending'、'ready' 或 'disabled'"
                    )
                update_data['status'] = request.status

            # 如果没有要更新的字段，返回当前用例信息
            if not update_data:
                return ApiTestCaseUpdateResponse(
                    id=test_case.id,
                    base_case_id=test_case.base_case_id,
                    name=test_case.name,
                    description=test_case.description,
                    interface_name=test_case.interface_name,
                    type=test_case.type,
                    preconditions=test_case.preconditions,
                    request=test_case.request,
                    assertions=test_case.assertions,
                    status=test_case.status,
                    generation_count=test_case.generation_count,
                    created_at=test_case.created_at,
                    updated_at=test_case.updated_at
                )

            # 执行更新
            await ApiTestCase.filter(id=test_case_id).update(**update_data)

            # 获取更新后的测试用例
            updated_test_case = await ApiTestCase.get(id=test_case_id)

            return ApiTestCaseUpdateResponse(
                id=updated_test_case.id,
                base_case_id=updated_test_case.base_case_id,
                name=updated_test_case.name,
                description=updated_test_case.description,
                interface_name=updated_test_case.interface_name,
                type=updated_test_case.type,
                preconditions=updated_test_case.preconditions,
                request=updated_test_case.request,
                assertions=updated_test_case.assertions,
                status=updated_test_case.status,
                generation_count=updated_test_case.generation_count,
                created_at=updated_test_case.created_at,
                updated_at=updated_test_case.updated_at
            )

    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        # 处理其他未预期的异常
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"编辑接口测试用例时发生错误: {str(e)}"
        )


@router.put("/{project_id}/base-cases/{base_case_id}", response_model=ApiBaseCaseUpdateResponse,
            summary="编辑接口基础用例")
async def update_base_case(
        project_id: int,
        base_case_id: int,
        request: ApiBaseCaseUpdateRequest,
        project_user: tuple = Depends(verify_admin_or_project_editor)
):
    """
    编辑接口基础测试用例
    
    权限要求：项目负责人、编辑组、管理员
    """
    project, current_user = project_user
    try:
        # 验证基础用例是否存在
        base_case = await ApiBaseCase.get_or_none(id=base_case_id)
        if not base_case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="基础用例不存在"
            )

        # 验证基础用例是否属于该项目（通过interface_id关联）
        interface = await ApiInterface.get_or_none(
            id=base_case.interface_id,
            project_id=project_id
        )
        if not interface:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="基础用例不属于该项目"
            )

        # 使用数据库事务处理更新操作
        async with in_transaction():
            # 构建更新数据
            update_data = {}
            if request.name is not None:
                if not request.name.strip():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="用例名称不能为空"
                    )
                update_data['name'] = request.name.strip()

            if request.steps is not None:
                if not isinstance(request.steps, list):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="测试步骤必须是列表格式"
                    )
                update_data['steps'] = request.steps

            if request.expected is not None:
                if not isinstance(request.expected, list):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="预期结果必须是列表格式"
                )
                update_data['expected'] = request.expected

            if request.status is not None:
                valid_statuses = ['active', 'inactive', 'draft', 'archived']
                if request.status not in valid_statuses:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"无效的用例状态，有效值为: {', '.join(valid_statuses)}"
                )
                update_data['status'] = request.status

            # 如果没有提供任何更新数据
            if not update_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="至少需要提供一个要更新的字段"
                )

            # 执行更新操作
            await ApiBaseCase.filter(id=base_case_id).update(**update_data)

            # 获取更新后的基础用例
            updated_base_case = await ApiBaseCase.get(id=base_case_id)

            return ApiBaseCaseUpdateResponse(
                success=True,
                message="基础用例更新成功",
                data=ApiBaseCaseItem(
                    id=updated_base_case.id,
                    interface_id=updated_base_case.interface_id,
                    name=updated_base_case.name,
                    steps=updated_base_case.steps,
                    expected=updated_base_case.expected,
                    status=updated_base_case.status,
                    created_at=updated_base_case.created_at,
                    updated_at=updated_base_case.updated_at
                )
            )

    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        # 处理其他未预期的异常
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"编辑基础用例时发生错误: {str(e)}"
        )


@router.post("/{project_id}/interfaces/{interface_id}/base-cases",
             response_model=ApiBaseCaseCreateResponse,
             summary="创建接口基础用例")
async def create_base_case(
        project_id: int,
        interface_id: int,
        request: ApiBaseCaseCreateRequest,
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_editor)
):
    """
    创建接口基础用例

    权限要求：项目负责人、项目编辑组或管理员

    业务逻辑：
    - 校验接口是否存在且属于项目
    - 校验字段格式与必填
    - 创建基础用例并返回
    """
    project, current_user = project_user

    try:
        # 校验接口归属
        interface = await ApiInterface.get_or_none(id=interface_id, project_id=project_id)
        if not interface:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="接口不存在或不属于该项目"
            )

        # 字段校验
        if not request.name or not request.name.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用例名称不能为空"
            )
        if not isinstance(request.steps, list):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="测试步骤必须是列表格式"
            )
        if not isinstance(request.expected, list):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="预期结果必须是列表格式"
            )

        valid_statuses = ['active', 'inactive', 'draft', 'archived']
        status_value = request.status or 'draft'
        if status_value not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的用例状态，有效值为: {', '.join(valid_statuses)}"
            )

        # 创建
        async with in_transaction():
            new_case = await ApiBaseCase.create(
                name=request.name.strip(),
                steps=request.steps,
                expected=request.expected,
                status=status_value,
                interface_id=interface_id
            )

        return ApiBaseCaseCreateResponse(
            success=True,
            message="基础用例创建成功",
            data=ApiBaseCaseItem(
                id=new_case.id,
                interface_id=new_case.interface_id,
                interface_name=interface.summary or interface.path if interface else None,
                name=new_case.name,
                steps=new_case.steps,
                expected=new_case.expected,
                status=new_case.status,
                created_at=new_case.created_at,
                updated_at=new_case.updated_at
            )
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建基础用例时发生错误: {str(e)}"
        )

@router.delete("/{project_id}/base-cases/{base_case_id}",
               response_model=ApiBaseCaseDeleteResponse,
               summary="删除基础用例")
async def delete_base_case(
        project_id: int,
        base_case_id: int,
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_editor)
):
    """
    删除接口基础用例

    权限要求：项目负责人、项目编辑组或管理员

    业务逻辑：
    - 验证基础用例是否存在
    - 验证基础用例是否属于指定项目（通过关联接口）
    - 删除基础用例

    参数：
    - project_id: 项目ID
    - base_case_id: 基础用例ID
    """
    project, current_user = project_user

    try:
        # 查询基础用例是否存在
        base_case = await ApiBaseCase.get_or_none(id=base_case_id)
        if not base_case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="基础用例不存在"
            )

        # 验证基础用例是否属于该项目（通过interface_id关联接口）
        interface = await ApiInterface.get_or_none(id=base_case.interface_id, project_id=project_id)
        if not interface:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="基础用例不属于该项目"
            )

        # 删除基础用例
        await base_case.delete()

        return ApiBaseCaseDeleteResponse(message="基础用例删除成功")

    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception:
        # 处理其他未预期异常
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除基础用例失败，请稍后重试"
        )


@router.post("/{project_id}/interfaces/{interface_id}/generate-base-cases",
             summary="生成接口基础用例")
async def generate_api_base_cases(
        project_id: int,
        interface_id: int,
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_editor)
):
    """
    生成接口基础用例
    
    参数：
    - project_id: 项目ID
    - interface_id: 接口ID
    
    权限要求：
    - 项目负责人、项目编辑组或管理员
    
    返回：
    - SSE流式输出生成进度和结果
    """
    project, current_user = project_user

    try:
        # 1. 查询接口详情
        interface = await ApiInterface.filter(id=interface_id, project_id=project_id).first()
        if not interface:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="接口不存在"
            )

        # 2. 查询接口的依赖分组和依赖关系
        dependency_groups = await ApiDependencyGroup.filter(target_interface_id=interface_id).prefetch_related(
            'dependencies')

        # 3. 构建接口信息
        interface_info = {
            "id": interface.id,
            "method": interface.method,
            "path": interface.path,
            "summary": interface.summary,
            "parameters": interface.parameters,
            "request_body": interface.request_body,
            "responses": interface.responses
        }

        # 4. 构建依赖信息
        dependencies_info = []
        for group in dependency_groups:
            group_info = {
                "group_id": group.id,
                "group_name": group.name,
                "group_description": group.description,
                "dependencies": []
            }

            for dep in group.dependencies:
                dep_info = {
                    "id": dep.id,
                    "name": dep.name,
                    "description": dep.description,
                    "dependency_type": dep.dependency_type,
                    "source_interface_id": dep.source_interface_id,
                    "source_field_path": dep.source_field_path,
                    "target_field_name": dep.target_field_name,
                    "transform_rule": dep.transform_rule,
                    "is_active": dep.is_active
                }
                group_info["dependencies"].append(dep_info)

            dependencies_info.append(group_info)

        async def generate_stream():
            """生成基础用例的流式输出函数"""
            try:
                # 发送接口信息

                # 发送开始生成的消息
                yield f"data: {json.dumps({'type': 'info', 'message': '正在分析接口结构...'}, ensure_ascii=False)}\n\n"
                yield f"data: {json.dumps({'type': 'info', 'message': f'开始为接口 {interface.method} {interface.path} 生成基础用例'}, ensure_ascii=False)}\n\n"

                # 5. 使用工作流生成基础用例
                workflow = ApiBaseCaseGeneratorWorkFlow()
                workflow_graph = workflow.create_workflow()

                # 构建工作流输入数据
                workflow_input = {
                    "api_doc": interface_info,
                    "preconditions": dependencies_info,
                }
                yield f"data: {json.dumps({'type': 'info', 'message': '正在生成基础用例...'}, ensure_ascii=False)}\n\n"
                # 流式执行工作流
                generated_cases = []
                async for item in workflow_graph.astream(workflow_input,
                                                         config={"configurable": {}},
                                                         subgraphs=True,
                                                         context={"interface_id": interface_id},
                                                         stream_mode=["messages", "custom"]
                                                         ):
                    if len(item) >= 3:
                        if item[1] == "messages":
                            # 发送进度消息
                            message = item[2][0].content if hasattr(item[2][0], 'content') else str(item[2][0])
                            print(message, end="")
                            yield f"data: {json.dumps({'type': 'progress', 'message': message}, ensure_ascii=False)}\n\n"
                        elif item[1] == "custom":
                            print(item[2])
                            # 发送自定义消息
                            yield f"data: {json.dumps({'type': 'info', 'message': str(item[2])}, ensure_ascii=False)}\n\n"
                # 发送完成消息
                yield f"data: {json.dumps({'type': 'complete', 'message': f'基础用例生成完成', 'data': {'generated_cases': generated_cases, 'interface_info': interface_info, 'dependencies': dependencies_info}}, ensure_ascii=False)}\n\n"
            except Exception as e:
                # 发送错误消息
                error_message = f"生成基础用例时发生错误：{str(e)}"
                yield f"data: {json.dumps({'type': 'error', 'message': error_message}, ensure_ascii=False)}\n\n"
            finally:
                # 发送结束标记
                yield f"data: [DONE]\n\n"

        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
            }
        )

    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        # 处理其他未预期的异常
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成基础用例时发生错误: {str(e)}"
        )


@router.post("/{project_id}/base-cases/{base_case_id}/generate-test-cases",
             summary="基于基础用例生成接口测试用例")
async def generate_api_test_cases(
        project_id: int,
        base_case_id: int,
        request: ApiTestCaseGenerateRequest,
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_editor)
):
    """
    基于基础用例生成接口测试用例
    
    参数：
    - project_id: 项目ID
    - base_case_id: 基础用例ID
    - request: 生成请求参数，包含测试环境ID和额外配置信息
    
    权限：项目负责人、项目编辑组、管理员
    
    返回：
    - SSE流式输出生成进度和结果
    """
    try:
        project, user = project_user
        # 获取额外配置信息
        additional_info = request.additional_info or {}
        # 1. 查询基础用例
        base_case = await ApiBaseCase.get_or_none(id=base_case_id).select_related("interface")
        if not base_case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="基础用例不存在"
            )

        # 2. 查询接口信息
        interface = base_case.interface
        if not interface:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="关联接口不存在"
            )

        # 3. 查询测试环境配置
        test_env = await TestEnvironment.get_or_none(
            id=request.test_id,
            project_id=project_id
        )

        if not test_env:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="测试环境不存在"
            )

        # 4. 查询测试环境变量配置
        test_env_configs = await TestEnvironmentConfig.filter(
            environment_id=request.test_id
        ).all()

        test_data = {}
        for config in test_env_configs:
            test_data[config.name] = config.value

        # 5. 查询测试环境数据库配置
        test_env_db = await TestEnvironmentDb.filter(
            environment_id=request.test_id
        ).all()
        # 生成用例时不需要数据库配置
        db_config = []
        # for config in test_env_db:
        #     db_config.append({
        #         "name": config.name,
        #         "type": config.type,
        #         "config": json.loads(config.config) if config.config else {}
        #     })

        # 6. 查询接口依赖信息
        dependencies = await ApiDependencyGroup.get_or_none(target_interface_id=interface.id)
        preconditions_api_doc = []
        if dependencies:
            # 查询当前接口所有的依赖接口
            dependencies_list = await ApiDependency.filter(dependency_group_id=dependencies.id).all()
        else:
            dependencies_list = []
        for dependency in dependencies_list:
            # 查询依赖接口的详细信息
            dep_interface = await ApiInterface.get_or_none(id=dependency.source_interface_id)
            if dep_interface:
                # 保存依赖接口的详细文档
                preconditions_api_doc.append({
                    "id": dep_interface.id,
                    "name": dep_interface.summary,
                    "method": dep_interface.method,
                    "path": dep_interface.path,
                    "parameters": dep_interface.parameters,
                    "request_body": dep_interface.request_body,
                    "responses": dep_interface.responses,
                })
                if dependency.is_active:
                    additional_info[f"{dep_interface.summary}接口的依赖数据提取规则"] = dict(
                        description=dependency.description,
                        dependency_type=dependency.dependency_type,
                        source_interface_id=dependency.source_interface_id,
                        source_field_path=dependency.source_field_path,
                        target_field_name=dependency.target_field_name
                    )
        # 7. 准备主接口文档数据
        api_doc = {
            "id": interface.id,
            "name": interface.summary,
            "method": interface.method,
            "path": interface.path,
            "parameters": interface.parameters,
            "request_body": interface.request_body,
            "responses": interface.responses,
        }

        # 8. 准备基础用例数据
        base_case_data = {
            "id": base_case.id,
            "name": base_case.name,
            "steps": base_case.steps if base_case.steps else [],
            "expected": base_case.expected if base_case.expected else {}
        }

        async def generate_stream():
            """生成测试用例的流式输出函数"""
            try:

                # 发送开始生成的消息
                yield f"data: {json.dumps({'type': 'info', 'message': '正在分析基础用例和接口结构...'}, ensure_ascii=False)}\n\n"
                # 发送开始信息
                yield f"data: {json.dumps({'type': 'info', 'message': f'开始为基础用例 {base_case.name} 生成测试用例'}, ensure_ascii=False)}\n\n"

                # 9. 调用工作流生成测试用例
                workflow_input = {
                    "api_doc": api_doc,
                    "base_case": base_case_data,
                    "preconditions_api_doc": preconditions_api_doc,
                    "db_config": db_config,
                    "test_data": test_data,
                    "additional_info": request.additional_info or {},
                    "base_case_id": base_case_id,  # 添加基础用例ID
                    "interface_id": interface.id  # 添加接口ID
                }

                yield f"data: {json.dumps({'type': 'info', 'message': '正在生成可执行测试用例...'}, ensure_ascii=False)}\n\n"

                # 使用工作流生成测试用例
                workflow = ApiRunCaseGeneratorWorkFlow()
                workflow_graph = workflow.create_workflow()
                async for item in workflow_graph.astream(workflow_input,
                                                         config={"configurable": {}},
                                                         subgraphs=True,
                                                         stream_mode=["messages", "custom"]
                                                         ):
                    if len(item) >= 3:
                        if item[1] == "messages":
                            # 发送进度消息
                            message = item[2][0].content if hasattr(item[2][0], 'content') else str(item[2][0])
                            print(message, end="")
                            yield f"data: {json.dumps({'type': 'progress', 'message': message}, ensure_ascii=False)}\n\n"
                        elif item[1] == "custom":
                            print(item[2])
                            # 发送自定义消息
                            yield f"data: {json.dumps({'type': 'info', 'message': str(item[2])}, ensure_ascii=False)}\n\n"
                yield f"data: {json.dumps({'type': 'info', 'message': '用例生成完毕'}, ensure_ascii=False)}\n\n"
            except Exception as e:
                # 发送错误消息
                error_message = f"生成测试用例时发生错误：{str(e)}"
                yield f"data: {json.dumps({'type': 'error', 'message': error_message}, ensure_ascii=False)}\n\n"
            finally:
                # 发送结束标记
                yield f"data: [DONE]\n\n"

        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
            }
        )

    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        # 处理其他未预期的异常
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成测试用例失败: {str(e)}"
        )


@router.post("/{project_id}/interfaces/{interface_id}/generate-complete-test-cases",
             response_model=ApiCompleteTestCaseGenerateResponse,
             summary="基于接口生成完整测试用例")
async def generate_complete_test_cases(
        project_id: int,
        interface_id: int,
        request: ApiCompleteTestCaseGenerateRequest,
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_editor)
):
    """
    基于接口生成完整测试用例
    
    权限要求：项目负责人、项目编辑组或管理员
    
    业务逻辑：
    1. 通过接口id查询出数据库中的接口数据
    2. 通过测试环境的id，去查询测试环境对应配置所有的测试变量和值
    3. 通过测试环境的id，查询当前测试环境对应的数据库配置信息
    4. 通过接口id去接口依赖分组中查询出所有的前置依赖接口文档，以及依赖的配置信息
    5. 使用工作流生成完整测试用例
    """
    try:
        project, user = project_user
        # 获取额外配置信息
        additional_info = request.additional_info or {}
        # 1. 查询接口数据
        interface = await ApiInterface.filter(id=interface_id, project_id=project_id).first()
        if not interface:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="接口不存在"
            )

        # 2. 查询测试环境配置
        test_env = await TestEnvironment.get_or_none(
            id=request.test_id,
            project_id=project_id
        )

        if not test_env:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="测试环境不存在"
            )

        # 4. 查询测试环境变量配置
        test_env_configs = await TestEnvironmentConfig.filter(
            environment_id=request.test_id
        ).all()

        test_data = {}
        for config in test_env_configs:
            test_data[config.name] = config.value
        # 生成用例时不需要数据库配置
        db_config = []
        # 构建依赖接口数据
        # 6. 查询接口依赖信息
        dependencies = await ApiDependencyGroup.get_or_none(target_interface_id=interface.id)
        preconditions_api_doc = []
        if dependencies:
            # 查询当前接口所有的依赖接口
            dependencies_list = await ApiDependency.filter(dependency_group_id=dependencies.id).all()
        else:
            dependencies_list = []
        for dependency in dependencies_list:
            # 查询依赖接口的详细信息
            dep_interface = await ApiInterface.get_or_none(id=dependency.source_interface_id)
            if dep_interface:
                # 保存依赖接口的详细文档
                preconditions_api_doc.append({
                    "id": dep_interface.id,
                    "name": dep_interface.summary,
                    "method": dep_interface.method,
                    "path": dep_interface.path,
                    "parameters": dep_interface.parameters,
                    "request_body": dep_interface.request_body,
                    "responses": dep_interface.responses,
                })
                if dependency.is_active:
                    additional_info[f"{dep_interface.summary}接口的依赖数据提取规则"] = dict(
                        description=dependency.description,
                        dependency_type=dependency.dependency_type,
                        source_interface_id=dependency.source_interface_id,
                        source_field_path=dependency.source_field_path,
                        target_field_name=dependency.target_field_name
                    )
        # 转换为字典
        # 构建工作流输入数据
        workflow_input = {
            "api_info": dict(interface),
            "preconditions": preconditions_api_doc,
            "db_config": db_config,
            "test_data": test_data,
            "additional_info": request.additional_info or {},
            "interface_id": interface.id  # 添加接口ID
        }

        # 创建工作流实例
        workflow = ApiCaseGenerateMainWorkFlow().create_workflow()

        # 定义SSE流式响应生成器
        async def generate_sse_response():
            try:
                # 生成进度消息
                progress_msg = "开始生成完整测试用例..."
                yield f"data: {json.dumps({'type': 'info', 'message': progress_msg}, ensure_ascii=False)}\n\n"

                async for item in workflow.astream(workflow_input,
                                                   config={"configurable": {}},
                                                   subgraphs=True,
                                                   stream_mode=["messages", "custom"]
                                                   ):
                    if len(item) >= 3:
                        if item[1] == "messages":
                            # 发送进度消息
                            message = item[2][0].content if hasattr(item[2][0], 'content') else str(item[2][0])
                            print(message, end="")
                            yield f"data: {json.dumps({'type': 'progress', 'message': message}, ensure_ascii=False)}\n\n"
                        elif item[1] == "custom":
                            print(item[2])
                            # 发送自定义消息
                            yield f"data: {json.dumps({'type': 'info', 'message': str(item[2])}, ensure_ascii=False)}\n\n"
                yield f"data: {json.dumps({'type': 'info', 'message': '用例生成完毕'}, ensure_ascii=False)}\n\n"

                # 生成完成消息
                complete_msg = "完整测试用例生成完成"
                yield f"data: {json.dumps({'type': 'complete', 'message': complete_msg}, ensure_ascii=False)}\n\n"

            except Exception as e:
                # 生成错误消息
                error_msg = f"生成完整测试用例失败: {str(e)}"
                yield f"data: {json.dumps({'type': 'error', 'message': error_msg}, ensure_ascii=False)}\n\n"
            finally:
                # 发送结束标记
                yield f"data: [DONE]\n\n"

        # 返回SSE流式响应
        return StreamingResponse(
            generate_sse_response(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "*",
                "Access-Control-Allow-Headers": "*",
            }
        )

    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        # 处理其他未预期的异常
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成完整测试用例失败: {str(e)}"
        )


# ==================== Phase 1: 快捷调试 ====================

def _parse_curl_command(curl_str: str) -> dict:
    """解析cURL命令字符串为请求参数字典"""
    curl_str = curl_str.strip()
    # 去掉换行续行符
    curl_str = curl_str.replace('\\\n', ' ').replace('\\\r\n', ' ')

    try:
        tokens = shlex.split(curl_str)
    except ValueError:
        # fallback: 简单空格拆分
        tokens = curl_str.split()

    if not tokens or tokens[0].lower() != 'curl':
        raise ValueError("不是有效的cURL命令")

    method = 'GET'
    url = ''
    headers = {}
    data_raw = None
    body_type = 'none'

    i = 1
    while i < len(tokens):
        token = tokens[i]
        if token in ('-X', '--request'):
            i += 1
            if i < len(tokens):
                method = tokens[i].upper()
        elif token in ('-H', '--header'):
            i += 1
            if i < len(tokens):
                header_val = tokens[i]
                if ':' in header_val:
                    k, v = header_val.split(':', 1)
                    headers[k.strip()] = v.strip()
        elif token in ('-d', '--data', '--data-raw', '--data-binary', '--data-urlencode'):
            i += 1
            if i < len(tokens):
                data_raw = tokens[i]
                if method == 'GET':
                    method = 'POST'
        elif token in ('-u', '--user'):
            i += 1  # 跳过认证
        elif token.startswith('http://') or token.startswith('https://'):
            url = token
        elif not token.startswith('-') and not url:
            url = token
        i += 1

    # 解析URL中的query参数
    parsed_url = urlparse(url)
    params = {}
    if parsed_url.query:
        for k, v_list in parse_qs(parsed_url.query).items():
            params[k] = v_list[0] if len(v_list) == 1 else v_list
        # 清理URL中的query部分
        url = urlunparse(parsed_url._replace(query=''))

    # 解析body
    body = None
    if data_raw:
        try:
            body = json.loads(data_raw)
            body_type = 'json'
        except (json.JSONDecodeError, TypeError):
            # 尝试form
            if '=' in data_raw:
                body = dict(item.split('=', 1) for item in data_raw.split('&') if '=' in item)
                body_type = 'form'
            else:
                body = data_raw
                body_type = 'text'

    return {
        'method': method,
        'url': url,
        'headers': headers,
        'params': params,
        'body': body,
        'body_type': body_type,
    }


def _build_curl_command(method: str, url: str, headers: dict = None,
                        params: dict = None, body=None, body_type: str = 'json') -> str:
    """根据请求参数构建cURL命令"""
    parts = ['curl']

    if method.upper() != 'GET':
        parts.append(f"-X {method.upper()}")

    # 添加query参数到URL
    if params:
        sep = '&' if '?' in url else '?'
        url = url + sep + urlencode(params)

    parts.append(f"'{url}'")

    if headers:
        for k, v in headers.items():
            parts.append(f"-H '{k}: {v}'")

    if body is not None:
        if body_type == 'json':
            body_str = json.dumps(body, ensure_ascii=False)
            parts.append(f"--data-raw '{body_str}'")
        elif body_type == 'form':
            if isinstance(body, dict):
                body_str = urlencode(body)
            else:
                body_str = str(body)
            parts.append(f"-d '{body_str}'")
        elif body_type == 'text':
            parts.append(f"-d '{body}'")

    return ' \\\n  '.join(parts)


@router.post("/{project_id}/quick-debug/send", response_model=QuickDebugResponse, summary="快捷调试-发送请求")
async def quick_debug_send(
        project_id: int,
        req: QuickDebugRequest,
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_member)
):
    """
    快捷调试：发送HTTP请求并保存历史记录

    类似Postman的请求发送功能，支持GET/POST/PUT/DELETE/PATCH等方法。
    """
    project, current_user = project_user

    error_msg = None
    resp_status = None
    resp_headers = None
    resp_body = None
    resp_time = None
    resp_size = None

    try:
        # 构建请求
        request_url = req.url
        if req.params:
            sep = '&' if '?' in request_url else '?'
            request_url = request_url + sep + urlencode(req.params)

        # 构建请求体
        content = None
        send_headers = dict(req.headers) if req.headers else {}
        if req.body is not None and req.body_type != 'none':
            if req.body_type == 'json':
                content = json.dumps(req.body, ensure_ascii=False).encode('utf-8')
                send_headers.setdefault('Content-Type', 'application/json')
            elif req.body_type == 'form':
                if isinstance(req.body, dict):
                    content = urlencode(req.body).encode('utf-8')
                else:
                    content = str(req.body).encode('utf-8')
                send_headers.setdefault('Content-Type', 'application/x-www-form-urlencoded')
            elif req.body_type == 'text':
                content = str(req.body).encode('utf-8')
                send_headers.setdefault('Content-Type', 'text/plain')

        # 发送请求
        start_time = time.time()
        async with httpx.AsyncClient(timeout=30, verify=False, follow_redirects=True) as client:
            response = await client.request(
                method=req.method.upper(),
                url=request_url,
                headers=send_headers,
                content=content,
            )
        elapsed = (time.time() - start_time) * 1000  # ms

        resp_status = response.status_code
        resp_headers = dict(response.headers)
        resp_body = response.text[:50000]  # 截断保存，最多50K
        resp_time = round(elapsed, 2)
        resp_size = len(response.content)

    except httpx.TimeoutException:
        error_msg = "请求超时（30秒）"
    except httpx.ConnectError as e:
        error_msg = f"连接失败: {str(e)}"
    except Exception as e:
        error_msg = f"请求失败: {str(e)}"

    # 保存历史记录
    history = await QuickDebugHistory.create(
        name=req.name,
        method=req.method.upper(),
        url=req.url,
        headers=req.headers or {},
        params=req.params or {},
        body=req.body,
        body_type=req.body_type,
        response_status=resp_status,
        response_headers=resp_headers,
        response_body=resp_body,
        response_time=resp_time,
        response_size=resp_size,
        project_id=project_id,
        user_id=current_user.id,
    )

    return QuickDebugResponse(
        history_id=history.id,
        status_code=resp_status,
        response_headers=resp_headers,
        response_body=resp_body,
        response_time=resp_time,
        response_size=resp_size,
        error=error_msg,
    )


@router.get("/{project_id}/quick-debug/history", response_model=QuickDebugHistoryListResponse,
            summary="快捷调试-请求历史列表")
async def quick_debug_history_list(
        project_id: int,
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        method: Optional[str] = Query(None, description="按HTTP方法过滤"),
        keyword: Optional[str] = Query(None, description="按URL或名称关键字过滤"),
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_member)
):
    """获取当前用户在该项目的请求历史列表"""
    project, current_user = project_user

    query = QuickDebugHistory.filter(project_id=project_id, user_id=current_user.id)
    if method:
        query = query.filter(method=method.upper())
    if keyword:
        query = query.filter(url__icontains=keyword)

    total = await query.count()
    offset = (page - 1) * page_size
    records = await query.offset(offset).limit(page_size).order_by('-created_at')

    items = [
        QuickDebugHistoryItem(
            id=r.id,
            name=r.name,
            method=r.method,
            url=r.url,
            body_type=r.body_type,
            response_status=r.response_status,
            response_time=r.response_time,
            created_at=r.created_at,
        )
        for r in records
    ]
    return QuickDebugHistoryListResponse(items=items, total=total)


@router.get("/{project_id}/quick-debug/history/{history_id}", response_model=QuickDebugHistoryDetail,
            summary="快捷调试-请求历史详情")
async def quick_debug_history_detail(
        project_id: int,
        history_id: int,
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_member)
):
    """获取某条请求历史的完整详情（含请求参数和响应体），可用于回填表单重新发送"""
    project, current_user = project_user

    record = await QuickDebugHistory.get_or_none(id=history_id, project_id=project_id)
    if not record:
        raise HTTPException(status_code=404, detail="历史记录不存在")

    return QuickDebugHistoryDetail(
        id=record.id,
        name=record.name,
        method=record.method,
        url=record.url,
        headers=record.headers,
        params=record.params,
        body=record.body,
        body_type=record.body_type,
        response_status=record.response_status,
        response_headers=record.response_headers,
        response_body=record.response_body,
        response_time=record.response_time,
        response_size=record.response_size,
        created_at=record.created_at,
    )


@router.delete("/{project_id}/quick-debug/history/{history_id}", summary="快捷调试-删除历史记录")
async def quick_debug_delete_history(
        project_id: int,
        history_id: int,
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_member)
):
    """删除某条请求历史"""
    project, current_user = project_user
    record = await QuickDebugHistory.get_or_none(id=history_id, project_id=project_id, user_id=current_user.id)
    if not record:
        raise HTTPException(status_code=404, detail="历史记录不存在")
    await record.delete()
    return {"message": "删除成功"}


@router.delete("/{project_id}/quick-debug/history", summary="快捷调试-清空历史记录")
async def quick_debug_clear_history(
        project_id: int,
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_member)
):
    """清空当前用户在该项目的所有请求历史"""
    project, current_user = project_user
    deleted_count = await QuickDebugHistory.filter(project_id=project_id, user_id=current_user.id).delete()
    return {"message": f"已清空 {deleted_count} 条历史记录"}


@router.post("/{project_id}/quick-debug/parse-curl", response_model=CurlImportResponse, summary="解析cURL命令")
async def parse_curl_command(
        project_id: int,
        req: CurlImportRequest,
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_member)
):
    """解析cURL命令字符串，返回结构化的请求参数（可回填到调试界面）"""
    try:
        result = _parse_curl_command(req.curl_command)
        return CurlImportResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"cURL解析失败: {str(e)}")


@router.post("/{project_id}/quick-debug/export-curl", response_model=CurlExportResponse,
             summary="导出为cURL命令")
async def export_as_curl(
        project_id: int,
        req: QuickDebugRequest,
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_member)
):
    """根据请求参数生成cURL命令字符串"""
    curl_cmd = _build_curl_command(
        method=req.method,
        url=req.url,
        headers=req.headers,
        params=req.params,
        body=req.body,
        body_type=req.body_type,
    )
    return CurlExportResponse(curl_command=curl_cmd)


@router.post("/{project_id}/quick-debug/save-as-interface", summary="快捷调试结果保存为接口")
async def save_debug_as_interface(
        project_id: int,
        req: QuickDebugRequest,
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_editor)
):
    """将快捷调试的请求保存为项目接口（从调试场景一键转为接口管理）"""
    project, current_user = project_user

    parsed = urlparse(req.url)
    path = parsed.path or req.url

    # 检查重复
    existing = await ApiInterface.get_or_none(project_id=project_id, path=path, method=req.method.upper())
    if existing:
        raise HTTPException(status_code=400, detail="该路径和方法的接口已存在")

    # 构建parameters
    parameters = {}
    if req.params:
        parameters = {"query": {k: {"type": "string", "example": v} for k, v in req.params.items()}}

    # 构建request_body
    request_body = {}
    if req.body:
        request_body = {"content_type": req.body_type, "example": req.body}

    new_interface = await ApiInterface.create(
        project_id=project_id,
        method=req.method.upper(),
        path=path,
        summary=req.name or f"{req.method.upper()} {path}",
        parameters=parameters,
        request_body=request_body,
        responses={},
    )

    return {
        "message": "已保存为接口",
        "interface_id": new_interface.id,
        "method": new_interface.method,
        "path": new_interface.path,
    }


# ==================== Phase 2: 定时任务 / CI触发 ====================

@router.post("/{project_id}/scheduled-tasks", response_model=ScheduledTaskResponse, summary="创建定时任务")
async def create_scheduled_task(
        project_id: int,
        req: ScheduledTaskCreateRequest,
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_editor)
):
    """创建定时/CI触发执行任务"""
    project, current_user = project_user

    # 验证测试任务存在
    test_task = await TestTask.get_or_none(id=req.test_task_id, project_id=project_id)
    if not test_task:
        raise HTTPException(status_code=404, detail="关联的测试任务不存在")

    env = await TestEnvironment.get_or_none(id=req.environment_id, project_id=project_id)
    if not env:
        raise HTTPException(status_code=404, detail="测试环境不存在")

    # 计算下次执行时间
    next_run = _calc_next_run(req.cron_expression) if req.cron_expression and req.task_type == 'cron' else None

    task = await ScheduledTask.create(
        name=req.name,
        task_type=req.task_type,
        cron_expression=req.cron_expression,
        test_task_id=req.test_task_id,
        environment_id=req.environment_id,
        is_active=req.is_active,
        next_run_at=next_run,
        project_id=project_id,
        creator_id=current_user.id,
    )

    return ScheduledTaskResponse(
        id=task.id,
        name=task.name,
        task_type=task.task_type,
        cron_expression=task.cron_expression,
        test_task_id=task.test_task_id,
        test_task_name=test_task.task_name,
        environment_id=task.environment_id,
        environment_name=env.name,
        is_active=task.is_active,
        last_run_at=task.last_run_at,
        next_run_at=task.next_run_at,
        created_at=task.created_at,
    )


def _calc_next_run(cron_expr: str) -> Optional[datetime]:
    """简单计算下次执行时间（支持基本的cron格式）"""
    try:
        # 简单实现：解析 minute hour 部分
        parts = cron_expr.strip().split()
        if len(parts) < 5:
            return None
        minute, hour = parts[0], parts[1]
        now = datetime.now()
        if minute.isdigit() and hour.isdigit():
            target = now.replace(hour=int(hour), minute=int(minute), second=0, microsecond=0)
            if target <= now:
                from datetime import timedelta
                target += timedelta(days=1)
            return target
    except Exception:
        pass
    return None


@router.get("/{project_id}/scheduled-tasks", response_model=ScheduledTaskListResponse, summary="获取定时任务列表")
async def list_scheduled_tasks(
        project_id: int,
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_member)
):
    """获取项目的定时任务列表"""
    project, current_user = project_user

    query = ScheduledTask.filter(project_id=project_id)
    total = await query.count()
    offset = (page - 1) * page_size
    tasks = await query.offset(offset).limit(page_size).order_by('-created_at')

    items = []
    for t in tasks:
        test_task = await TestTask.get_or_none(id=t.test_task_id)
        env = await TestEnvironment.get_or_none(id=t.environment_id)
        items.append(ScheduledTaskResponse(
            id=t.id,
            name=t.name,
            task_type=t.task_type,
            cron_expression=t.cron_expression,
            test_task_id=t.test_task_id,
            test_task_name=test_task.task_name if test_task else None,
            environment_id=t.environment_id,
            environment_name=env.name if env else None,
            is_active=t.is_active,
            last_run_at=t.last_run_at,
            next_run_at=t.next_run_at,
            created_at=t.created_at,
        ))

    return ScheduledTaskListResponse(items=items, total=total)


@router.put("/{project_id}/scheduled-tasks/{task_id}", response_model=ScheduledTaskResponse, summary="更新定时任务")
async def update_scheduled_task(
        project_id: int,
        task_id: int,
        req: ScheduledTaskUpdateRequest,
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_editor)
):
    """更新定时任务配置"""
    project, current_user = project_user

    task = await ScheduledTask.get_or_none(id=task_id, project_id=project_id)
    if not task:
        raise HTTPException(status_code=404, detail="定时任务不存在")

    update_data = {}
    if req.name is not None:
        update_data['name'] = req.name
    if req.task_type is not None:
        update_data['task_type'] = req.task_type
    if req.cron_expression is not None:
        update_data['cron_expression'] = req.cron_expression
        update_data['next_run_at'] = _calc_next_run(req.cron_expression)
    if req.test_task_id is not None:
        tt = await TestTask.get_or_none(id=req.test_task_id, project_id=project_id)
        if not tt:
            raise HTTPException(status_code=404, detail="关联的测试任务不存在")
        update_data['test_task_id'] = req.test_task_id
    if req.environment_id is not None:
        env = await TestEnvironment.get_or_none(id=req.environment_id, project_id=project_id)
        if not env:
            raise HTTPException(status_code=404, detail="测试环境不存在")
        update_data['environment_id'] = req.environment_id
    if req.is_active is not None:
        update_data['is_active'] = req.is_active

    if update_data:
        await task.update_from_dict(update_data)
        await task.save()

    # 重新获取
    task = await ScheduledTask.get(id=task_id)
    test_task = await TestTask.get_or_none(id=task.test_task_id)
    env = await TestEnvironment.get_or_none(id=task.environment_id)

    return ScheduledTaskResponse(
        id=task.id,
        name=task.name,
        task_type=task.task_type,
        cron_expression=task.cron_expression,
        test_task_id=task.test_task_id,
        test_task_name=test_task.task_name if test_task else None,
        environment_id=task.environment_id,
        environment_name=env.name if env else None,
        is_active=task.is_active,
        last_run_at=task.last_run_at,
        next_run_at=task.next_run_at,
        created_at=task.created_at,
    )


@router.delete("/{project_id}/scheduled-tasks/{task_id}", summary="删除定时任务")
async def delete_scheduled_task(
        project_id: int,
        task_id: int,
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_editor)
):
    """删除定时任务"""
    project, current_user = project_user
    task = await ScheduledTask.get_or_none(id=task_id, project_id=project_id)
    if not task:
        raise HTTPException(status_code=404, detail="定时任务不存在")
    await task.delete()
    return {"message": "删除成功"}


async def _collect_task_cases(test_task_id: int):
    """从测试任务中收集所有关联的测试用例ID"""
    # 通过 TestTask -> TaskSuiteRelation -> TestSuite -> SuiteCaseRelation -> ApiTestCase
    suite_relations = await TaskSuiteRelation.filter(task_id=test_task_id).order_by('suite_order')
    all_case_ids = []
    suite_info = []
    for sr in suite_relations:
        case_relations = await SuiteCaseRelation.filter(suite_id=sr.suite_id).order_by('case_order')
        case_ids = [cr.case_id for cr in case_relations]
        all_case_ids.extend(case_ids)
        suite_info.append({"suite_id": sr.suite_id, "case_ids": case_ids})
    return all_case_ids, suite_info


@router.post("/{project_id}/scheduled-tasks/{task_id}/trigger", response_model=CiTriggerResponse,
             summary="手动/CI触发执行")
async def trigger_task_execution(
        project_id: int,
        task_id: int,
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_member)
):
    """手动触发定时任务立即执行一次"""
    project, current_user = project_user

    task = await ScheduledTask.get_or_none(id=task_id, project_id=project_id)
    if not task:
        raise HTTPException(status_code=404, detail="定时任务不存在")

    test_task = await TestTask.get_or_none(id=task.test_task_id)
    if not test_task:
        raise HTTPException(status_code=404, detail="关联的测试任务不存在")

    all_case_ids, suite_info = await _collect_task_cases(test_task.id)
    if not all_case_ids:
        raise HTTPException(status_code=400, detail="测试任务没有关联用例")

    # 创建执行记录
    _now = datetime.now(timezone.utc)
    task_run = await TestTaskRun.create(
        task_id=test_task.id,
        status='running',
        total_suites=len(suite_info),
        total_cases=len(all_case_ids),
        passed_cases=0,
        failed_cases=0,
        skipped_cases=0,
        start_time=_now,
    )

    # 更新定时任务最后执行时间
    task.last_run_at = _now
    if task.cron_expression:
        task.next_run_at = _calc_next_run(task.cron_expression)
    await task.save()

    # 异步执行
    asyncio.create_task(_execute_task_run(task_run.id, suite_info, task.environment_id, project_id))

    return CiTriggerResponse(
        task_run_id=task_run.id,
        status='running',
        message=f"已触发执行，共 {len(all_case_ids)} 个用例",
    )


@router.post("/{project_id}/ci-trigger", response_model=CiTriggerResponse, summary="CI Webhook触发接口")
async def ci_webhook_trigger(
        project_id: int,
        req: CiTriggerRequest,
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_member)
):
    """CI/CD流水线通过Webhook调用此接口来触发测试执行"""
    project, current_user = project_user

    test_task = await TestTask.get_or_none(id=req.task_id, project_id=project_id)
    if not test_task:
        scheduled = await ScheduledTask.get_or_none(id=req.task_id, project_id=project_id)
        if scheduled:
            test_task = await TestTask.get_or_none(id=scheduled.test_task_id)
        if not test_task:
            raise HTTPException(status_code=404, detail="找不到对应的测试任务")

    all_case_ids, suite_info = await _collect_task_cases(test_task.id)
    if not all_case_ids:
        raise HTTPException(status_code=400, detail="测试任务没有关联用例")

    task_run = await TestTaskRun.create(
        task_id=test_task.id,
        status='running',
        total_suites=len(suite_info),
        total_cases=len(all_case_ids),
        passed_cases=0,
        failed_cases=0,
        skipped_cases=0,
        start_time=datetime.now(timezone.utc),
    )

    asyncio.create_task(_execute_task_run(task_run.id, suite_info, 0, project_id))

    return CiTriggerResponse(
        task_run_id=task_run.id,
        status='running',
        message=f"CI触发执行成功，共 {len(all_case_ids)} 个用例",
    )


async def _execute_task_run(task_run_id: int, suite_info: list, environment_id: int, project_id: int):
    """异步执行测试任务（Phase 3：并行执行 + Webhook通知）"""
    from api_case_run.execute import TestExecutor

    total_passed = 0
    total_failed = 0
    total_skipped = 0

    # 获取环境配置
    env_vars = {}
    if environment_id:
        env_configs = await TestEnvironmentConfig.filter(environment_id=environment_id).all()
        for cfg in env_configs:
            env_vars[cfg.name] = cfg.value

    # 获取数据库配置
    db_configs = []
    if environment_id:
        env_dbs = await TestEnvironmentDb.filter(environment_id=environment_id).all()
        for db in env_dbs:
            try:
                db_configs.append({
                    "name": db.name,
                    "type": db.type,
                    "config": json.loads(db.config) if isinstance(db.config, str) else db.config
                })
            except Exception:
                pass

    for si in suite_info:
        suite_id = si["suite_id"]
        case_ids = si["case_ids"]

        # 创建套件运行记录
        suite_run = await TestSuiteRun.create(
            suite_id=suite_id,
            run_task_id=task_run_id,
            status='running',
            total_cases=len(case_ids),
            start_time=datetime.now(timezone.utc),
        )

        suite_passed = 0
        suite_failed = 0
        suite_skipped = 0
        suite_error = 0

        # Phase 3: 并行执行用例（最多5个并发）
        semaphore = asyncio.Semaphore(5)
        results_lock = asyncio.Lock()

        async def run_single_case(case_id):
            nonlocal suite_passed, suite_failed, suite_skipped, suite_error
            async with semaphore:
                test_case = await ApiTestCase.get_or_none(id=case_id)
                if not test_case:
                    async with results_lock:
                        suite_skipped += 1
                    return

                try:
                    # 构建用例数据（兼容现有executor格式）
                    case_data = {
                        "id": test_case.id,
                        "name": test_case.name,
                        "preconditions": test_case.preconditions or [],
                        "request": test_case.request or {},
                        "assertions": test_case.assertions or {},
                    }

                    # 在线程中执行同步的TestExecutor
                    loop = asyncio.get_event_loop()
                    executor = TestExecutor(env_vars, db_configs)
                    result = await loop.run_in_executor(None, executor.execute_test_case, case_data)

                    # 保存用例执行记录
                    await ApiCaseRun.create(
                        suite_run_id=suite_run.id,
                        api_case_id=test_case.id,
                        case_name=test_case.name,
                        status=result.status,
                        error_message=result.error_message,
                        traceback=result.traceback,
                        start_time=datetime.fromtimestamp(result.start_time) if result.start_time else None,
                        end_time=datetime.fromtimestamp(result.end_time) if result.end_time else None,
                        duration=result.duration,
                        logs=result.logs if hasattr(result, 'logs') else None,
                        api_requests_info=result.api_requests_info if hasattr(result, 'api_requests_info') else None,
                    )

                    async with results_lock:
                        if result.status == 'success':
                            suite_passed += 1
                        elif result.status == 'failed':
                            suite_failed += 1
                        elif result.status == 'skip':
                            suite_skipped += 1
                        else:
                            suite_error += 1

                except Exception as e:
                    await ApiCaseRun.create(
                        suite_run_id=suite_run.id,
                        api_case_id=case_id,
                        case_name=test_case.name if test_case else f"case_{case_id}",
                        status='error',
                        error_message=str(e),
                        traceback=traceback.format_exc(),
                    )
                    async with results_lock:
                        suite_error += 1

        # 并行执行所有用例
        await asyncio.gather(*[run_single_case(cid) for cid in case_ids])

        # 更新套件运行记录
        suite_run.status = 'completed'
        suite_run.passed_cases = suite_passed
        suite_run.failed_cases = suite_failed
        suite_run.skipped_cases = suite_skipped
        suite_run.error_cases = suite_error
        suite_run.end_time = datetime.now(timezone.utc)
        if suite_run.start_time:
            suite_run.duration = (suite_run.end_time - suite_run.start_time).total_seconds()
        await suite_run.save()

        total_passed += suite_passed
        total_failed += suite_failed + suite_error
        total_skipped += suite_skipped

    # 更新任务运行记录
    task_run = await TestTaskRun.get(id=task_run_id)
    task_run.status = 'completed'
    task_run.passed_cases = total_passed
    task_run.failed_cases = total_failed
    task_run.skipped_cases = total_skipped
    task_run.end_time = datetime.now(timezone.utc)
    if task_run.start_time:
        task_run.duration = (task_run.end_time - task_run.start_time).total_seconds()
    await task_run.save()

    # Phase 3: 发送Webhook通知
    await _send_webhook_notifications(project_id, task_run)


@router.post("/{project_id}/curl-to-interface", summary="cURL导入为接口")
async def curl_import_as_interface(
        project_id: int,
        req: CurlToInterfaceRequest,
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_editor)
):
    """将cURL命令解析并直接创建为项目接口"""
    project, current_user = project_user

    try:
        parsed = _parse_curl_command(req.curl_command)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"cURL解析失败: {str(e)}")

    parsed_url = urlparse(parsed['url'])
    path = parsed_url.path or parsed['url']

    existing = await ApiInterface.get_or_none(project_id=project_id, path=path, method=parsed['method'])
    if existing:
        raise HTTPException(status_code=400, detail="该路径和方法的接口已存在")

    parameters = {}
    if parsed['params']:
        parameters = {"query": {k: {"type": "string", "example": v} for k, v in parsed['params'].items()}}

    request_body = {}
    if parsed['body']:
        request_body = {"content_type": parsed['body_type'], "example": parsed['body']}

    new_interface = await ApiInterface.create(
        project_id=project_id,
        method=parsed['method'],
        path=path,
        summary=req.summary or f"{parsed['method']} {path}",
        parameters=parameters,
        request_body=request_body,
        responses={},
    )

    return {
        "message": "cURL导入为接口成功",
        "interface_id": new_interface.id,
        "method": new_interface.method,
        "path": new_interface.path,
        "summary": new_interface.summary,
    }


# ==================== Phase 3: Webhook通知配置 ====================

@router.post("/{project_id}/webhook-configs", response_model=WebhookConfigResponse, summary="创建Webhook通知配置")
async def create_webhook_config(
        project_id: int,
        req: WebhookConfigCreateRequest,
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_editor)
):
    """创建Webhook通知配置（飞书/钉钉/自定义）"""
    project, current_user = project_user

    config = await WebhookConfig.create(
        name=req.name,
        webhook_url=req.webhook_url,
        webhook_type=req.webhook_type,
        trigger_on=req.trigger_on,
        is_active=req.is_active,
        project_id=project_id,
    )

    return WebhookConfigResponse(
        id=config.id,
        name=config.name,
        webhook_url=config.webhook_url,
        webhook_type=config.webhook_type,
        trigger_on=config.trigger_on,
        is_active=config.is_active,
        created_at=config.created_at,
    )


@router.get("/{project_id}/webhook-configs", response_model=WebhookConfigListResponse,
            summary="获取Webhook配置列表")
async def list_webhook_configs(
        project_id: int,
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_member)
):
    """获取项目的所有Webhook通知配置"""
    project, current_user = project_user

    configs = await WebhookConfig.filter(project_id=project_id).order_by('-created_at')
    items = [
        WebhookConfigResponse(
            id=c.id,
            name=c.name,
            webhook_url=c.webhook_url,
            webhook_type=c.webhook_type,
            trigger_on=c.trigger_on,
            is_active=c.is_active,
            created_at=c.created_at,
        )
        for c in configs
    ]
    return WebhookConfigListResponse(items=items, total=len(items))


@router.put("/{project_id}/webhook-configs/{config_id}", response_model=WebhookConfigResponse,
            summary="更新Webhook配置")
async def update_webhook_config(
        project_id: int,
        config_id: int,
        req: WebhookConfigUpdateRequest,
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_editor)
):
    """更新Webhook通知配置"""
    project, current_user = project_user

    config = await WebhookConfig.get_or_none(id=config_id, project_id=project_id)
    if not config:
        raise HTTPException(status_code=404, detail="Webhook配置不存在")

    update_data = {}
    if req.name is not None:
        update_data['name'] = req.name
    if req.webhook_url is not None:
        update_data['webhook_url'] = req.webhook_url
    if req.webhook_type is not None:
        update_data['webhook_type'] = req.webhook_type
    if req.trigger_on is not None:
        update_data['trigger_on'] = req.trigger_on
    if req.is_active is not None:
        update_data['is_active'] = req.is_active

    if update_data:
        await config.update_from_dict(update_data)
        await config.save()

    config = await WebhookConfig.get(id=config_id)
    return WebhookConfigResponse(
        id=config.id,
        name=config.name,
        webhook_url=config.webhook_url,
        webhook_type=config.webhook_type,
        trigger_on=config.trigger_on,
        is_active=config.is_active,
        created_at=config.created_at,
    )


@router.delete("/{project_id}/webhook-configs/{config_id}", summary="删除Webhook配置")
async def delete_webhook_config(
        project_id: int,
        config_id: int,
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_editor)
):
    """删除Webhook通知配置"""
    project, current_user = project_user
    config = await WebhookConfig.get_or_none(id=config_id, project_id=project_id)
    if not config:
        raise HTTPException(status_code=404, detail="Webhook配置不存在")
    await config.delete()
    return {"message": "删除成功"}


@router.post("/{project_id}/webhook-configs/{config_id}/test", summary="测试Webhook连通性")
async def test_webhook_config(
        project_id: int,
        config_id: int,
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_editor)
):
    """发送测试消息验证Webhook是否连通"""
    project, current_user = project_user

    config = await WebhookConfig.get_or_none(id=config_id, project_id=project_id)
    if not config:
        raise HTTPException(status_code=404, detail="Webhook配置不存在")

    try:
        test_msg = _build_webhook_message(
            webhook_type=config.webhook_type,
            title="🔔 Webhook连通性测试",
            content=f"项目: {project.name}\n这是一条测试消息，如果您看到此消息，说明Webhook配置正确。",
        )

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(config.webhook_url, json=test_msg)

        if resp.status_code == 200:
            return {"success": True, "message": "Webhook测试消息发送成功"}
        else:
            return {"success": False, "message": f"发送失败，状态码: {resp.status_code}，响应: {resp.text[:200]}"}
    except Exception as e:
        return {"success": False, "message": f"发送失败: {str(e)}"}


def _build_webhook_message(webhook_type: str, title: str, content: str) -> dict:
    """根据Webhook类型构建消息体"""
    if webhook_type == 'feishu':
        return {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {"tag": "plain_text", "content": title},
                    "template": "blue",
                },
                "elements": [
                    {"tag": "div", "text": {"tag": "lark_md", "content": content}},
                ],
            },
        }
    elif webhook_type == 'dingtalk':
        return {
            "msgtype": "markdown",
            "markdown": {"title": title, "text": f"### {title}\n\n{content}"},
        }
    else:
        # 自定义格式
        return {"title": title, "content": content}


async def _send_webhook_notifications(project_id: int, execution):
    """执行完成后发送Webhook通知"""
    configs = await WebhookConfig.filter(project_id=project_id, is_active=True)

    for config in configs:
        # 检查触发条件
        should_send = False
        if config.trigger_on == 'always':
            should_send = True
        elif config.trigger_on == 'on_failure' and execution.failed_cases > 0:
            should_send = True
        elif config.trigger_on == 'on_success' and execution.failed_cases == 0:
            should_send = True

        if not should_send:
            continue

        # 构建通知内容
        status_icon = "✅" if execution.failed_cases == 0 else "❌"
        title = f"{status_icon} 测试执行完成通知"
        content = (
            f"**执行ID**: {execution.id}\n"
            f"**总用例数**: {execution.total_cases}\n"
            f"**通过**: {execution.passed_cases}  |  **失败**: {execution.failed_cases}  |  **跳过**: {execution.skipped_cases}\n"
            f"**通过率**: {round(execution.passed_cases / max(execution.total_cases, 1) * 100, 1)}%\n"
        )

        msg = _build_webhook_message(config.webhook_type, title, content)

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                await client.post(config.webhook_url, json=msg)
        except Exception:
            pass  # 通知失败不影响主流程


# ==================== Phase 3: 增强执行报告 ====================

@router.get("/{project_id}/execution-report/{run_id}", summary="获取增强执行报告")
async def get_enhanced_execution_report(
        project_id: int,
        run_id: int,
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_member)
):
    """获取执行报告的增强版本，包含详细统计、趋势数据和用例结果"""
    project, current_user = project_user

    task_run = await TestTaskRun.get_or_none(id=run_id)
    if not task_run:
        raise HTTPException(status_code=404, detail="执行记录不存在")

    # 获取套件运行记录
    suite_runs = await TestSuiteRun.filter(run_task_id=run_id).order_by('id')

    # 获取所有用例执行记录
    status_distribution = {}
    response_times = []
    cases = []
    suites = []

    for sr in suite_runs:
        # 获取套件名称
        suite = await TestSuite.get_or_none(id=sr.suite_id)
        suite_name = suite.suite_name if suite else f"套件 {sr.suite_id}"

        suites.append({
            "suite_id": sr.suite_id,
            "suite_name": suite_name,
            "total": sr.total_cases or 0,
            "passed": sr.passed_cases or 0,
            "failed": (sr.failed_cases or 0) + (sr.error_cases or 0),
            "skipped": sr.skipped_cases or 0,
            "duration": round((sr.duration or 0) * 1000, 2),  # 转毫秒
        })

        case_runs = await ApiCaseRun.filter(suite_run_id=sr.id).order_by('id')
        for cr in case_runs:
            s = cr.status or 'unknown'
            status_distribution[s] = status_distribution.get(s, 0) + 1
            duration_ms = round((cr.duration or 0) * 1000, 2)
            if cr.duration:
                response_times.append(duration_ms)

            # 从 api_requests_info 提取第一条请求信息给前端展示
            request_info = None
            if cr.api_requests_info and isinstance(cr.api_requests_info, list) and len(cr.api_requests_info) > 0:
                first_req = cr.api_requests_info[0]
                request_info = {
                    "method": first_req.get("method", ""),
                    "url": first_req.get("url", ""),
                    "response_status": first_req.get("status_code"),
                }

            cases.append({
                "case_id": cr.api_case_id,
                "case_name": cr.case_name,
                "status": cr.status,
                "duration": duration_ms,
                "error_message": cr.error_message,
                "request_info": request_info,
                "api_requests_info": cr.api_requests_info,
            })

    # 性能统计
    perf_stats = {}
    if response_times:
        sorted_times = sorted(response_times)
        perf_stats = {
            "avg_response_time": round(sum(response_times) / len(response_times), 2),
            "min_response_time": round(min(response_times), 2),
            "max_response_time": round(max(response_times), 2),
            "p95_response_time": round(sorted_times[int(len(sorted_times) * 0.95)] if sorted_times else 0, 2),
        }

    # 获取历史趋势（最近10次执行）
    history_runs = await TestTaskRun.filter(
        task_id=task_run.task_id, status='completed'
    ).order_by('-id').limit(10)

    trend_data = []
    for hr in reversed(list(history_runs)):
        trend_data.append({
            "run_id": hr.id,
            "total": hr.total_cases,
            "passed": hr.passed_cases,
            "failed": hr.failed_cases,
            "pass_rate": round(hr.passed_cases / max(hr.total_cases, 1) * 100, 1),
            "created_at": hr.created_at.isoformat() if hr.created_at else None,
        })

    return {
        # 前端需要的结构化格式
        "summary": {
            "total_cases": task_run.total_cases or 0,
            "passed": task_run.passed_cases or 0,
            "failed": task_run.failed_cases or 0,
            "skipped": task_run.skipped_cases or 0,
            "total_duration": round((task_run.duration or 0) * 1000, 2),  # 毫秒
        },
        "suites": suites,
        "cases": cases,
        # 附加信息
        "run_id": task_run.id,
        "task_id": task_run.task_id,
        "status": task_run.status,
        "pass_rate": round(task_run.passed_cases / max(task_run.total_cases, 1) * 100, 1),
        "start_time": task_run.start_time.isoformat() if task_run.start_time else None,
        "end_time": task_run.end_time.isoformat() if task_run.end_time else None,
        "duration": task_run.duration,
        "status_distribution": status_distribution,
        "performance_stats": perf_stats,
        "trend_data": trend_data,
    }
