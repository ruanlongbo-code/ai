"""
知识库模块API路由
"""
from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File, Form, Query
from fastapi.responses import StreamingResponse
from typing import Optional
import logging
import traceback
import json
import os

from .models import KnowledgeDocument, KnowledgeCaseSet, KnowledgeCaseItem
from .schemas import (
    KnowledgeDocumentResponse,
    KnowledgeDocumentListResponse,
    KnowledgeTextUploadRequest,
    KnowledgeSearchRequest,
    CaseSetResponse,
    CaseSetListResponse,
    CaseItemResponse,
)
from service.user.models import User
from service.project.models import Project
from utils.permissions import verify_admin_or_project_member, verify_admin_or_project_editor

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/{project_id}/documents", response_model=KnowledgeDocumentListResponse, summary="获取知识库文档列表")
async def get_document_list(
        project_id: int,
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        doc_status: Optional[str] = Query(None, alias="status"),
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_member)
):
    project, current_user = project_user

    try:
        query_filters = {"project_id": project_id}
        if doc_status:
            query_filters["status"] = doc_status

        total = await KnowledgeDocument.filter(**query_filters).count()
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        offset = (page - 1) * page_size
        documents = await KnowledgeDocument.filter(**query_filters).order_by("-created_at").offset(offset).limit(page_size).all()

        doc_list = [
            KnowledgeDocumentResponse(
                id=doc.id,
                project_id=doc.project_id,
                title=doc.title,
                doc_type=doc.doc_type,
                file_name=doc.file_name,
                content_preview=doc.content_preview,
                rag_doc_id=doc.rag_doc_id,
                status=doc.status,
                error_message=doc.error_message,
                creator_id=doc.creator_id,
                created_at=doc.created_at,
                updated_at=doc.updated_at,
            )
            for doc in documents
        ]

        return KnowledgeDocumentListResponse(
            documents=doc_list,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取知识库文档列表失败"
        )


@router.post("/{project_id}/documents/text", response_model=KnowledgeDocumentResponse, summary="上传文本到知识库")
async def upload_text_document(
        project_id: int,
        request: KnowledgeTextUploadRequest,
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_editor)
):
    project, current_user = project_user

    try:
        doc = await KnowledgeDocument.create(
            project_id=project_id,
            title=request.title,
            doc_type="text",
            content_preview=request.text[:500] if request.text else "",
            status="processing",
            creator_id=current_user.id,
        )

        try:
            from rag.rag_api import RAGClient
            rag_client = RAGClient()
            result = rag_client.add_document({
                "file_source": request.title,
                "text": request.text,
            })

            if result.get("status") == "success":
                doc.rag_doc_id = result.get("doc_on")
                doc.status = "completed"
            elif result.get("status") == "update":
                doc.status = "completed"
            else:
                doc.status = "failed"
                doc.error_message = "RAG系统处理失败"
        except Exception as rag_err:
            logger.warning(f"RAG处理失败，文档已保存到数据库: {rag_err}")
            doc.status = "failed"
            doc.error_message = str(rag_err)[:500]

        await doc.save()

        return KnowledgeDocumentResponse(
            id=doc.id,
            project_id=doc.project_id,
            title=doc.title,
            doc_type=doc.doc_type,
            file_name=doc.file_name,
            content_preview=doc.content_preview,
            rag_doc_id=doc.rag_doc_id,
            status=doc.status,
            error_message=doc.error_message,
            creator_id=doc.creator_id,
            created_at=doc.created_at,
            updated_at=doc.updated_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="上传文档失败"
        )


@router.post("/{project_id}/documents/file", response_model=KnowledgeDocumentResponse, summary="上传文件到知识库")
async def upload_file_document(
        project_id: int,
        file: UploadFile = File(..., description="文档文件（PDF、DOCX、TXT、MD）"),
        title: Optional[str] = Form(None),
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_editor)
):
    project, current_user = project_user

    try:
        supported_ext = {".pdf", ".docx", ".txt", ".md", ".xmind"}
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in supported_ext:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的文件格式: {ext}，支持: PDF, DOCX, TXT, MD, XMind"
            )

        file_content = await file.read()
        if len(file_content) > 20 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="文件大小超过限制（最大20MB）"
            )

        if ext == ".xmind":
            from utils.parser.xmind_parser import parse_xmind_file, xmind_to_text_for_rag
            tree = parse_xmind_file(file_content)
            extracted_text = xmind_to_text_for_rag(tree)
        else:
            from utils.parser.requirement_document_parser import extract_text_from_file
            extracted_text = extract_text_from_file(file.filename, file_content)

        doc = await KnowledgeDocument.create(
            project_id=project_id,
            title=title or file.filename,
            doc_type="file",
            file_name=file.filename,
            content_preview=extracted_text[:500] if extracted_text else "",
            status="processing",
            creator_id=current_user.id,
        )

        try:
            from rag.rag_api import RAGClient
            rag_client = RAGClient()
            result = rag_client.add_document({
                "file_source": file.filename,
                "text": extracted_text,
            })
            if result.get("status") == "success":
                doc.rag_doc_id = result.get("doc_on")
                doc.status = "completed"
            elif result.get("status") == "update":
                doc.status = "completed"
            else:
                doc.status = "failed"
                doc.error_message = "RAG系统处理失败"
        except Exception as rag_err:
            logger.warning(f"RAG处理失败: {rag_err}")
            doc.status = "failed"
            doc.error_message = str(rag_err)[:500]

        await doc.save()

        return KnowledgeDocumentResponse(
            id=doc.id,
            project_id=doc.project_id,
            title=doc.title,
            doc_type=doc.doc_type,
            file_name=doc.file_name,
            content_preview=doc.content_preview,
            rag_doc_id=doc.rag_doc_id,
            status=doc.status,
            error_message=doc.error_message,
            creator_id=doc.creator_id,
            created_at=doc.created_at,
            updated_at=doc.updated_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传文件失败: {e}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="上传文件失败"
        )


@router.delete("/{project_id}/documents/{doc_id}", summary="删除知识库文档")
async def delete_document(
        project_id: int,
        doc_id: int,
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_editor)
):
    project, current_user = project_user

    try:
        doc = await KnowledgeDocument.get_or_none(id=doc_id, project_id=project_id)
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文档不存在"
            )

        if doc.rag_doc_id:
            try:
                from rag.rag_api import RAGClient
                rag_client = RAGClient()
                rag_client.delete_document(doc.rag_doc_id)
            except Exception as e:
                logger.warning(f"RAG文档删除失败（将继续删除数据库记录）: {e}")

        await doc.delete()
        return {"message": "文档删除成功"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除文档失败"
        )


@router.post("/{project_id}/search", summary="知识库检索")
async def search_knowledge(
        project_id: int,
        request: KnowledgeSearchRequest,
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_member)
):
    """知识库检索接口，返回SSE流式响应"""
    project, current_user = project_user

    try:
        from rag.rag_api import RAGClient
        rag_client = RAGClient()

        async def generate():
            try:
                for chunk in rag_client.query_stream(
                    request.query,
                    conversation_history=request.conversation_history,
                ):
                    if chunk:
                        yield f"data: {json.dumps({'type': 'content', 'data': chunk}, ensure_ascii=False)}\n\n"
                yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'data': str(e)}, ensure_ascii=False)}\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"知识库检索失败: {str(e)}"
        )


@router.post("/{project_id}/search/sync", summary="知识库同步检索")
async def search_knowledge_sync(
        project_id: int,
        request: KnowledgeSearchRequest,
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_member)
):
    """知识库同步检索接口，返回完整结果"""
    project, current_user = project_user

    try:
        from rag.rag_api import RAGClient
        rag_client = RAGClient()
        result = rag_client.query(
            request.query,
            conversation_history=request.conversation_history,
        )
        return {
            "query": request.query,
            "response": result.get("response", ""),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"知识库检索失败: {str(e)}"
        )


# ======================== 用例集 API ========================

@router.get("/{project_id}/case-sets", response_model=CaseSetListResponse, summary="获取用例集列表")
async def get_case_set_list(
        project_id: int,
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_member)
):
    project, current_user = project_user
    try:
        case_sets = await KnowledgeCaseSet.filter(project_id=project_id).order_by("-created_at").all()
        total = len(case_sets)
        items = [
            CaseSetResponse(
                id=cs.id, project_id=cs.project_id, name=cs.name,
                source=cs.source, total_cases=cs.total_cases,
                synced=cs.synced, creator_id=cs.creator_id,
                created_at=cs.created_at, updated_at=cs.updated_at,
            )
            for cs in case_sets
        ]
        return CaseSetListResponse(case_sets=items, total=total)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取用例集列表失败")


@router.get("/{project_id}/case-sets/{case_set_id}/tree", summary="获取用例集树形结构")
async def get_case_set_tree(
        project_id: int,
        case_set_id: int,
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_member)
):
    project, current_user = project_user
    try:
        case_set = await KnowledgeCaseSet.get_or_none(id=case_set_id, project_id=project_id)
        if not case_set:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用例集不存在")

        all_items = await KnowledgeCaseItem.filter(case_set_id=case_set_id).order_by("sort_order").all()

        item_map = {}
        for item in all_items:
            item_map[item.id] = {
                "id": item.id, "case_set_id": item.case_set_id,
                "parent_id": item.parent_id, "title": item.title,
                "node_type": item.node_type, "priority": item.priority,
                "preconditions": item.preconditions, "test_steps": item.test_steps,
                "expected_result": item.expected_result, "sort_order": item.sort_order,
                "children": [],
            }

        roots = []
        for item in all_items:
            node = item_map[item.id]
            if item.parent_id and item.parent_id in item_map:
                item_map[item.parent_id]["children"].append(node)
            else:
                roots.append(node)

        return {"case_set": CaseSetResponse(
            id=case_set.id, project_id=case_set.project_id, name=case_set.name,
            source=case_set.source, total_cases=case_set.total_cases,
            synced=case_set.synced, creator_id=case_set.creator_id,
            created_at=case_set.created_at, updated_at=case_set.updated_at,
        ), "tree": roots}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取用例集树形结构失败")


@router.post("/{project_id}/case-sets/import-xmind", summary="从XMind文件导入用例集")
async def import_case_set_from_xmind(
        project_id: int,
        file: UploadFile = File(..., description="XMind文件"),
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_editor)
):
    project, current_user = project_user
    try:
        if not file.filename.lower().endswith('.xmind'):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请上传.xmind格式文件")

        file_content = await file.read()
        if len(file_content) > 20 * 1024 * 1024:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="文件大小超过限制（最大20MB）")

        from utils.parser.xmind_parser import parse_xmind_file, xmind_to_text_for_rag

        tree = parse_xmind_file(file_content)
        if not tree:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="XMind文件内容为空")

        set_name = os.path.splitext(file.filename)[0]
        case_set = await KnowledgeCaseSet.create(
            project_id=project_id, name=set_name,
            source="xmind", creator_id=current_user.id,
        )

        case_count = await _save_tree_to_db(tree, case_set.id)
        case_set.total_cases = case_count
        await case_set.save()

        # 自动同步到 RAG 知识库
        rag_text = xmind_to_text_for_rag(tree)
        try:
            from rag.rag_api import RAGClient
            rag_client = RAGClient()
            result = rag_client.add_document({"file_source": f"用例集:{set_name}", "text": rag_text})
            if result.get("status") in ("success", "update"):
                case_set.synced = True
                case_set.rag_doc_id = result.get("doc_on")
                await case_set.save()
        except Exception as rag_err:
            logger.warning(f"用例集同步到RAG失败: {rag_err}")

        return {"message": f"导入成功，共解析 {case_count} 条用例", "case_set_id": case_set.id, "total_cases": case_count}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"XMind导入失败: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"导入失败: {str(e)}")


@router.post("/{project_id}/case-sets/import-functional", summary="从项目功能用例导入用例集")
async def import_case_set_from_functional(
        project_id: int,
        requirement_ids: Optional[str] = Query(None, description="需求ID列表,逗号分隔; 为空则导入全部"),
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_editor)
):
    """将项目中已有的功能用例批量导入为知识库用例集"""
    project, current_user = project_user
    try:
        from service.functional_test.models import FunctionalCase, RequirementDoc
        from service.project.models import ProjectModule

        modules = await ProjectModule.filter(project_id=project_id).all()
        module_ids = [m.id for m in modules]
        if not module_ids:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="项目下无模块数据")

        requirements = await RequirementDoc.filter(module_id__in=module_ids).all()
        if requirement_ids:
            req_id_list = [int(x.strip()) for x in requirement_ids.split(",") if x.strip()]
            requirements = [r for r in requirements if r.id in req_id_list]

        if not requirements:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="没有找到需求数据")

        case_set = await KnowledgeCaseSet.create(
            project_id=project_id, name=f"{project.name}-功能用例集",
            source="import", creator_id=current_user.id,
        )

        total_count = 0
        rag_lines = []

        for req in requirements:
            req_node = await KnowledgeCaseItem.create(
                case_set_id=case_set.id, parent_id=None,
                title=req.title, node_type="module", sort_order=req.id,
            )
            rag_lines.append(f"\n## {req.title}")

            cases = await FunctionalCase.filter(requirement_id=req.id).all()
            for idx, case in enumerate(cases):
                steps_text = ""
                if case.test_steps:
                    if isinstance(case.test_steps, list):
                        steps_text = "\n".join(
                            s.get("action", str(s)) if isinstance(s, dict) else str(s)
                            for s in case.test_steps
                        )
                    else:
                        steps_text = str(case.test_steps)

                await KnowledgeCaseItem.create(
                    case_set_id=case_set.id, parent_id=req_node.id,
                    title=case.case_name, node_type="case",
                    priority=f"P{case.priority}" if case.priority else None,
                    preconditions=case.preconditions,
                    test_steps=steps_text,
                    expected_result=case.expected_result,
                    sort_order=idx,
                )
                total_count += 1
                rag_lines.append(f"### {case.case_name}")
                if case.preconditions:
                    rag_lines.append(f"前置条件：{case.preconditions}")
                if steps_text:
                    rag_lines.append(f"测试步骤：{steps_text}")
                if case.expected_result:
                    rag_lines.append(f"预期结果：{case.expected_result}")

        case_set.total_cases = total_count
        await case_set.save()

        if rag_lines:
            try:
                from rag.rag_api import RAGClient
                rag_client = RAGClient()
                result = rag_client.add_document({"file_source": case_set.name, "text": "\n".join(rag_lines)})
                if result.get("status") in ("success", "update"):
                    case_set.synced = True
                    case_set.rag_doc_id = result.get("doc_on")
                    await case_set.save()
            except Exception as rag_err:
                logger.warning(f"用例集同步到RAG失败: {rag_err}")

        return {"message": f"导入成功，共 {total_count} 条用例", "case_set_id": case_set.id, "total_cases": total_count}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"功能用例导入失败: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="导入失败")


@router.delete("/{project_id}/case-sets/{case_set_id}", summary="删除用例集")
async def delete_case_set(
        project_id: int,
        case_set_id: int,
        project_user: tuple[Project, User] = Depends(verify_admin_or_project_editor)
):
    project, current_user = project_user
    try:
        case_set = await KnowledgeCaseSet.get_or_none(id=case_set_id, project_id=project_id)
        if not case_set:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用例集不存在")

        if case_set.rag_doc_id:
            try:
                from rag.rag_api import RAGClient
                rag_client = RAGClient()
                rag_client.delete_document(case_set.rag_doc_id)
            except Exception:
                pass

        await KnowledgeCaseItem.filter(case_set_id=case_set_id).delete()
        await case_set.delete()
        return {"message": "用例集删除成功"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="删除失败")


async def _save_tree_to_db(tree: list, case_set_id: int, parent_id=None) -> int:
    """递归保存 XMind 解析出的树形结构到数据库"""
    count = 0
    for idx, node in enumerate(tree):
        has_children = 'children' in node and node['children']
        is_case = 'test_steps' in node or 'expected_result' in node
        node_type = "module" if has_children and not is_case else "case"

        item = await KnowledgeCaseItem.create(
            case_set_id=case_set_id,
            parent_id=parent_id,
            title=node.get('title', ''),
            node_type=node_type,
            priority=node.get('priority'),
            preconditions=node.get('preconditions'),
            test_steps=node.get('test_steps'),
            expected_result=node.get('expected_result'),
            sort_order=idx,
        )

        if is_case:
            count += 1

        if has_children:
            count += await _save_tree_to_db(node['children'], case_set_id, item.id)

    return count
