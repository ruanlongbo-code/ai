from tortoise.models import Model
from tortoise import fields


class KnowledgeDocument(Model):
    """知识库文档表"""
    id = fields.IntField(pk=True, description="主键ID")
    project_id = fields.IntField(description="所属项目ID")
    title = fields.CharField(max_length=255, description="文档标题")
    doc_type = fields.CharField(max_length=20, default="text", description="文档类型(text/file/url/xmind)")
    file_name = fields.CharField(max_length=255, null=True, description="原始文件名")
    content_preview = fields.TextField(null=True, description="内容预览(前500字)")
    rag_doc_id = fields.CharField(max_length=255, null=True, description="RAG系统中的文档ID")
    status = fields.CharField(max_length=20, default="pending", description="处理状态(pending/processing/completed/failed)")
    error_message = fields.TextField(null=True, description="处理失败时的错误信息")
    creator_id = fields.IntField(description="上传者ID")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "knowledge_document"
        table_description = "知识库文档表"


class KnowledgeCaseSet(Model):
    """知识库用例集"""
    id = fields.IntField(pk=True, description="主键ID")
    project_id = fields.IntField(description="所属项目ID")
    name = fields.CharField(max_length=255, description="用例集名称")
    source = fields.CharField(max_length=20, default="xmind", description="来源(xmind/import/manual)")
    total_cases = fields.IntField(default=0, description="用例总数")
    rag_doc_id = fields.CharField(max_length=255, null=True, description="同步到RAG的文档ID")
    synced = fields.BooleanField(default=False, description="是否已同步到知识库")
    creator_id = fields.IntField(description="创建者ID")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "knowledge_case_set"
        table_description = "知识库用例集"


class KnowledgeCaseItem(Model):
    """知识库用例集中的单条用例"""
    id = fields.IntField(pk=True, description="主键ID")
    case_set_id = fields.IntField(description="所属用例集ID")
    parent_id = fields.IntField(null=True, description="父节点ID（用于树形结构）")
    title = fields.CharField(max_length=500, description="标题/用例名")
    node_type = fields.CharField(max_length=20, default="case", description="节点类型(module/case)")
    priority = fields.CharField(max_length=10, null=True, description="优先级")
    preconditions = fields.TextField(null=True, description="前置条件")
    test_steps = fields.TextField(null=True, description="测试步骤")
    expected_result = fields.TextField(null=True, description="预期结果")
    sort_order = fields.IntField(default=0, description="排序")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")

    class Meta:
        table = "knowledge_case_item"
        table_description = "知识库用例项"
