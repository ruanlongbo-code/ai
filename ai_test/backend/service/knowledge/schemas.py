from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class KnowledgeDocumentResponse(BaseModel):
    id: int
    project_id: int
    title: str
    doc_type: str
    file_name: Optional[str] = None
    content_preview: Optional[str] = None
    rag_doc_id: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    creator_id: int
    created_at: datetime
    updated_at: datetime


class KnowledgeDocumentListResponse(BaseModel):
    documents: List[KnowledgeDocumentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class KnowledgeTextUploadRequest(BaseModel):
    title: str
    text: str


class KnowledgeSearchRequest(BaseModel):
    query: str
    conversation_history: Optional[list] = None


class KnowledgeSearchResponse(BaseModel):
    query: str
    response: str


class CaseSetResponse(BaseModel):
    id: int
    project_id: int
    name: str
    source: str
    total_cases: int
    synced: bool
    creator_id: int
    created_at: datetime
    updated_at: datetime


class CaseSetListResponse(BaseModel):
    case_sets: List[CaseSetResponse]
    total: int


class CaseItemResponse(BaseModel):
    id: int
    case_set_id: int
    parent_id: Optional[int] = None
    title: str
    node_type: str
    priority: Optional[str] = None
    preconditions: Optional[str] = None
    test_steps: Optional[str] = None
    expected_result: Optional[str] = None
    sort_order: int = 0
    children: Optional[List['CaseItemResponse']] = None

CaseItemResponse.model_rebuild()
