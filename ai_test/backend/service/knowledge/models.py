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


class ReviewRecord(Model):
    """评审记录表 - 需求评审/技术评审/用例评审"""
    id = fields.IntField(pk=True, description="主键ID")
    project_id = fields.IntField(description="所属项目ID")
    title = fields.CharField(max_length=255, description="评审标题")
    review_type = fields.CharField(max_length=20, description="评审类型: requirement/technical/testcase")
    description = fields.TextField(null=True, description="评审描述/备注")
    video_file_name = fields.CharField(max_length=255, null=True, description="原始视频文件名")
    video_file_path = fields.CharField(max_length=500, null=True, description="视频存储路径")
    video_size = fields.BigIntField(default=0, description="视频文件大小(字节)")
    frame_count = fields.IntField(default=0, description="提取的关键帧数量")
    status = fields.CharField(max_length=20, default="uploaded", description="状态: uploaded/extracting/analyzing/completed/failed")
    analysis_result = fields.TextField(null=True, description="AI视觉模型分析结果(JSON)")
    extracted_text = fields.TextField(null=True, description="提取并汇总的文字内容")
    key_decisions = fields.TextField(null=True, description="关键决策和结论(JSON列表)")
    action_items = fields.TextField(null=True, description="待办事项(JSON列表)")
    rag_doc_id = fields.CharField(max_length=255, null=True, description="同步到RAG的文档ID")
    synced_to_rag = fields.BooleanField(default=False, description="是否已同步到RAG知识库")
    error_message = fields.TextField(null=True, description="处理失败时的错误信息")
    creator_id = fields.IntField(description="上传者ID")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")

    class Meta:
        table = "review_record"
        table_description = "评审记录表"
