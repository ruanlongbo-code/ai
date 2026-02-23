<template>
  <div class="knowledge-document">
    <div class="page-header">
      <div class="header-left">
        <h2>文档管理</h2>
        <span class="subtitle">上传业务文档、需求文档，构建项目知识库，提升AI生成测试用例的准确性</span>
      </div>
      <div class="header-actions">
        <el-button type="primary" @click="showUploadTextDialog">
          <el-icon><EditPen /></el-icon>粘贴文本
        </el-button>
        <el-button type="primary" @click="showUploadFileDialog">
          <el-icon><Upload /></el-icon>上传文件
        </el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-row">
      <div class="stat-card">
        <div class="stat-value">{{ total }}</div>
        <div class="stat-label">文档总数</div>
      </div>
      <div class="stat-card success">
        <div class="stat-value">{{ completedCount }}</div>
        <div class="stat-label">已入库</div>
      </div>
      <div class="stat-card warning">
        <div class="stat-value">{{ processingCount }}</div>
        <div class="stat-label">处理中</div>
      </div>
      <div class="stat-card danger">
        <div class="stat-value">{{ failedCount }}</div>
        <div class="stat-label">失败</div>
      </div>
    </div>

    <!-- 文档列表 -->
    <el-table :data="documents" v-loading="loading" stripe style="width: 100%">
      <el-table-column prop="title" label="文档标题" min-width="200" show-overflow-tooltip />
      <el-table-column prop="doc_type" label="类型" width="100">
        <template #default="{ row }">
          <el-tag size="small" :type="row.doc_type === 'file' ? 'primary' : 'success'">
            {{ row.doc_type === 'file' ? '文件' : '文本' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag size="small" :type="statusTagType(row.status)">
            {{ statusLabel(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="content_preview" label="内容预览" min-width="300" show-overflow-tooltip />
      <el-table-column prop="created_at" label="上传时间" width="180">
        <template #default="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="100" fixed="right">
        <template #default="{ row }">
          <el-popconfirm title="确定删除该文档？" @confirm="handleDelete(row)">
            <template #reference>
              <el-button type="danger" size="small" link>删除</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <div class="pagination-wrapper" v-if="total > 0">
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :total="total"
        layout="total, prev, pager, next"
        @current-change="fetchDocuments"
      />
    </div>

    <!-- 上传文本弹窗 -->
    <el-dialog v-model="textDialogVisible" title="粘贴文本到知识库" width="640px" :close-on-click-modal="false">
      <el-form :model="textForm" label-width="80px">
        <el-form-item label="标题" required>
          <el-input v-model="textForm.title" placeholder="给文档起个标题" />
        </el-form-item>
        <el-form-item label="内容" required>
          <el-input
            v-model="textForm.text"
            type="textarea"
            :rows="12"
            placeholder="粘贴需求文档、设计文档、历史用例等文本内容..."
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="textDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="uploading" @click="handleUploadText">上传到知识库</el-button>
      </template>
    </el-dialog>

    <!-- 上传文件弹窗 -->
    <el-dialog v-model="fileDialogVisible" title="上传文件到知识库" width="500px" :close-on-click-modal="false">
      <el-upload
        ref="uploadRef"
        :auto-upload="false"
        :limit="1"
        :on-change="handleFileChange"
        accept=".pdf,.docx,.txt,.md,.xmind"
        drag
      >
        <el-icon class="el-icon--upload"><Upload /></el-icon>
        <div class="el-upload__text">拖拽文件到这里，或<em>点击上传</em></div>
        <template #tip>
          <div class="el-upload__tip">支持 PDF、DOCX、TXT、MD、XMind 格式，最大 10MB</div>
        </template>
      </el-upload>
      <template #footer>
        <el-button @click="fileDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="uploading" @click="handleUploadFile">上传到知识库</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { useProjectStore } from '@/stores'
import {
  getKnowledgeDocuments,
  uploadTextDocument,
  uploadFileDocument,
  deleteKnowledgeDocument
} from '@/api/knowledge'

const projectStore = useProjectStore()
const projectId = computed(() => projectStore.currentProject?.id)

const loading = ref(false)
const uploading = ref(false)
const documents = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)

const completedCount = computed(() => documents.value.filter(d => d.status === 'completed').length)
const processingCount = computed(() => documents.value.filter(d => d.status === 'processing').length)
const failedCount = computed(() => documents.value.filter(d => d.status === 'failed').length)

const textDialogVisible = ref(false)
const fileDialogVisible = ref(false)
const textForm = ref({ title: '', text: '' })
const selectedFile = ref(null)

const statusTagType = (s) => ({ completed: 'success', processing: 'warning', failed: 'danger', pending: 'info' }[s] || 'info')
const statusLabel = (s) => ({ completed: '已入库', processing: '处理中', failed: '失败', pending: '待处理' }[s] || s)
const formatDate = (d) => d ? new Date(d).toLocaleString('zh-CN') : ''

const fetchDocuments = async () => {
  if (!projectId.value) return
  loading.value = true
  try {
    const res = await getKnowledgeDocuments(projectId.value, { page: page.value, page_size: pageSize.value })
    documents.value = res.data.documents
    total.value = res.data.total
  } catch (e) {
    ElMessage.error('获取文档列表失败')
  } finally {
    loading.value = false
  }
}

const showUploadTextDialog = () => {
  textForm.value = { title: '', text: '' }
  textDialogVisible.value = true
}

const showUploadFileDialog = () => {
  selectedFile.value = null
  fileDialogVisible.value = true
}

const handleUploadText = async () => {
  if (!textForm.value.title || !textForm.value.text) {
    ElMessage.warning('标题和内容不能为空')
    return
  }
  uploading.value = true
  try {
    await uploadTextDocument(projectId.value, textForm.value)
    ElMessage.success('文档上传成功')
    textDialogVisible.value = false
    fetchDocuments()
  } catch (e) {
    ElMessage.error('上传失败')
  } finally {
    uploading.value = false
  }
}

const handleFileChange = (file) => {
  selectedFile.value = file.raw
}

const handleUploadFile = async () => {
  if (!selectedFile.value) {
    ElMessage.warning('请选择文件')
    return
  }
  uploading.value = true
  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    await uploadFileDocument(projectId.value, formData)
    ElMessage.success('文件上传成功')
    fileDialogVisible.value = false
    fetchDocuments()
  } catch (e) {
    ElMessage.error('上传失败')
  } finally {
    uploading.value = false
  }
}

const handleDelete = async (row) => {
  try {
    await deleteKnowledgeDocument(projectId.value, row.id)
    ElMessage.success('删除成功')
    fetchDocuments()
  } catch (e) {
    ElMessage.error('删除失败')
  }
}

onMounted(() => {
  fetchDocuments()
})
</script>

<style scoped>
.knowledge-document {
  padding: 10px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0 0 4px 0;
  font-size: 20px;
}

.subtitle {
  color: #909399;
  font-size: 13px;
}

.stats-row {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
}

.stat-card {
  flex: 1;
  padding: 16px 20px;
  border-radius: 8px;
  background: #f4f4f5;
  text-align: center;
}

.stat-card.success { background: #f0f9eb; }
.stat-card.warning { background: #fdf6ec; }
.stat-card.danger { background: #fef0f0; }

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
}

.stat-card.success .stat-value { color: #67c23a; }
.stat-card.warning .stat-value { color: #e6a23c; }
.stat-card.danger .stat-value { color: #f56c6c; }

.stat-label {
  font-size: 13px;
  color: #909399;
  margin-top: 4px;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
