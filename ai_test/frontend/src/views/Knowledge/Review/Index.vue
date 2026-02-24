<template>
  <div class="review-container">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="header-left">
        <h2>{{ pageTitle }}</h2>
        <p class="subtitle">{{ pageSubtitle }}</p>
      </div>
      <el-button type="primary" @click="showUploadDialog">
        <el-icon><Upload /></el-icon>
        上传评审视频
      </el-button>
    </div>

    <!-- 评审记录列表 -->
    <el-table :data="reviewList" v-loading="loading" stripe style="width: 100%">
      <el-table-column prop="title" label="评审标题" min-width="200" show-overflow-tooltip />
      <el-table-column prop="video_file_name" label="视频文件" min-width="180" show-overflow-tooltip />
      <el-table-column label="文件大小" width="120">
        <template #default="{ row }">
          {{ formatFileSize(row.video_size) }}
        </template>
      </el-table-column>
      <el-table-column label="状态" width="140">
        <template #default="{ row }">
          <el-tag :type="statusTagType(row.status)" effect="dark" round>
            {{ statusText(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="关键帧" width="90" align="center">
        <template #default="{ row }">
          <span>{{ row.frame_count || '-' }}</span>
        </template>
      </el-table-column>
      <el-table-column label="已同步RAG" width="110" align="center">
        <template #default="{ row }">
          <el-icon v-if="row.synced_to_rag" color="#67c23a"><CircleCheckFilled /></el-icon>
          <el-icon v-else color="#909399"><CircleCloseFilled /></el-icon>
        </template>
      </el-table-column>
      <el-table-column label="创建时间" width="180">
        <template #default="{ row }">
          {{ formatTime(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="260" fixed="right">
        <template #default="{ row }">
          <el-button
            v-if="row.status === 'uploaded' || row.status === 'failed'"
            type="primary" link size="small"
            @click="startAnalyze(row)"
          >
            <el-icon><VideoPlay /></el-icon> AI分析
          </el-button>
          <el-button type="success" link size="small" @click="viewDetail(row)">
            <el-icon><View /></el-icon> 查看
          </el-button>
          <el-popconfirm title="确定删除该评审记录？" @confirm="handleDelete(row)">
            <template #reference>
              <el-button type="danger" link size="small">
                <el-icon><Delete /></el-icon> 删除
              </el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <div class="pagination-wrapper" v-if="total > 0">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        @size-change="fetchList"
        @current-change="fetchList"
      />
    </div>

    <!-- 空状态 -->
    <el-empty v-if="!loading && reviewList.length === 0" description="暂无评审记录，请上传评审视频">
      <el-button type="primary" @click="showUploadDialog">上传评审视频</el-button>
    </el-empty>

    <!-- 上传对话框 -->
    <el-dialog v-model="uploadVisible" title="上传评审视频" width="560px" :close-on-click-modal="false">
      <el-form ref="uploadFormRef" :model="uploadForm" :rules="uploadRules" label-width="100px">
        <el-form-item label="评审标题" prop="title">
          <el-input v-model="uploadForm.title" placeholder="例如：V2.0 用户模块需求评审" maxlength="100" show-word-limit />
        </el-form-item>
        <el-form-item label="评审描述">
          <el-input v-model="uploadForm.description" type="textarea" :rows="3" placeholder="评审背景和主要内容（选填）" />
        </el-form-item>
        <el-form-item label="视频文件" prop="file">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="1"
            :on-change="handleFileChange"
            :on-remove="handleFileRemove"
            accept=".mp4,.avi,.mov,.mkv,.webm,.flv"
            drag
          >
            <el-icon class="el-icon--upload"><Upload /></el-icon>
            <div class="el-upload__text">
              拖拽文件到此处，或<em>点击选择文件</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                支持 MP4、AVI、MOV、MKV、WebM 格式，最大 500MB
              </div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="uploadVisible = false">取消</el-button>
        <el-button type="primary" :loading="uploading" @click="handleUpload">
          {{ uploading ? '上传中...' : '上传' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- AI分析进度对话框 -->
    <el-dialog v-model="analyzeVisible" title="AI视觉分析" width="600px" :close-on-click-modal="false" :close-on-press-escape="false">
      <div class="analyze-progress">
        <div class="progress-header">
          <el-icon class="analyzing-icon" :class="{ spinning: analyzing }"><Loading /></el-icon>
          <span class="progress-title">{{ analyzeMessage }}</span>
        </div>
        <el-progress :percentage="analyzeProgress" :status="analyzeProgressStatus" :stroke-width="12" style="margin: 20px 0;" />
        <div class="progress-steps">
          <div v-for="step in analyzeSteps" :key="step.key"
               class="step-item" :class="{ active: step.key === currentStep, done: step.done }">
            <el-icon v-if="step.done"><CircleCheckFilled /></el-icon>
            <el-icon v-else-if="step.key === currentStep"><Loading /></el-icon>
            <el-icon v-else><Clock /></el-icon>
            <span>{{ step.label }}</span>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button v-if="!analyzing" type="primary" @click="analyzeVisible = false; fetchList()">完成</el-button>
      </template>
    </el-dialog>

    <!-- 详情对话框 -->
    <el-dialog v-model="detailVisible" :title="detailRecord?.title || '评审详情'" width="800px" top="5vh">
      <div v-if="detailRecord" class="review-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="评审类型">
            <el-tag :type="reviewTypeTag(detailRecord.review_type)">{{ reviewTypeText(detailRecord.review_type) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="statusTagType(detailRecord.status)" effect="dark">{{ statusText(detailRecord.status) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="视频文件">{{ detailRecord.video_file_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="关键帧数">{{ detailRecord.frame_count || 0 }}</el-descriptions-item>
          <el-descriptions-item label="RAG同步">
            <el-tag :type="detailRecord.synced_to_rag ? 'success' : 'info'">{{ detailRecord.synced_to_rag ? '已同步' : '未同步' }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ formatTime(detailRecord.created_at) }}</el-descriptions-item>
          <el-descriptions-item v-if="detailRecord.description" label="描述" :span="2">
            {{ detailRecord.description }}
          </el-descriptions-item>
        </el-descriptions>

        <!-- 关键决策 -->
        <div v-if="parsedDecisions.length" class="detail-section">
          <h4><el-icon><Flag /></el-icon> 关键决策</h4>
          <ul class="decision-list">
            <li v-for="(item, idx) in parsedDecisions" :key="idx">{{ item }}</li>
          </ul>
        </div>

        <!-- 待办事项 -->
        <div v-if="parsedActions.length" class="detail-section">
          <h4><el-icon><Checked /></el-icon> 待办事项</h4>
          <ul class="action-list">
            <li v-for="(item, idx) in parsedActions" :key="idx">{{ item }}</li>
          </ul>
        </div>

        <!-- AI分析汇总 -->
        <div v-if="detailRecord.extracted_text" class="detail-section">
          <h4><el-icon><Document /></el-icon> AI分析汇总</h4>
          <div class="analysis-content" v-html="renderMarkdown(detailRecord.extracted_text)"></div>
        </div>

        <!-- 错误信息 -->
        <el-alert v-if="detailRecord.error_message" type="error" :title="detailRecord.error_message" show-icon style="margin-top: 16px;" />
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useProjectStore, useUserStore } from '@/stores'
import { ElMessage } from 'element-plus'
import { getReviewList, getReviewDetail, uploadReviewVideo, deleteReview } from '@/api/knowledge'
import MarkdownIt from 'markdown-it'

const route = useRoute()
const projectStore = useProjectStore()
const userStore = useUserStore()

const md = new MarkdownIt()

// Props: reviewType 由路由 meta 传入
const props = defineProps({
  reviewType: {
    type: String,
    required: true,
    validator: (v) => ['requirement', 'technical', 'testcase'].includes(v)
  }
})

const projectId = computed(() => projectStore.currentProject?.id)

// 页面标题
const pageTitles = {
  requirement: { title: '需求评审', subtitle: '导入需求评审会议视频，AI自动提取需求要点和边界条件，辅助生成更完善的测试用例' },
  technical: { title: '技术评审', subtitle: '导入技术方案评审视频，AI自动提取技术方案和接口变更，补充技术层面的测试场景' },
  testcase: { title: '用例评审', subtitle: '导入用例评审会议视频，AI自动提取评审意见和遗漏场景，完善现有测试用例' },
}
const pageTitle = computed(() => pageTitles[props.reviewType]?.title || '评审管理')
const pageSubtitle = computed(() => pageTitles[props.reviewType]?.subtitle || '')

// 列表数据
const loading = ref(false)
const reviewList = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

// 上传
const uploadVisible = ref(false)
const uploading = ref(false)
const uploadFormRef = ref()
const uploadRef = ref()
const uploadForm = ref({ title: '', description: '', file: null })
const uploadRules = {
  title: [{ required: true, message: '请输入评审标题', trigger: 'blur' }],
}

// 分析
const analyzeVisible = ref(false)
const analyzing = ref(false)
const analyzeProgress = ref(0)
const analyzeMessage = ref('')
const currentStep = ref('')
const analyzeProgressStatus = ref('')
const analyzeSteps = ref([
  { key: 'extracting', label: '提取关键帧', done: false },
  { key: 'analyzing', label: 'AI视觉分析', done: false },
  { key: 'summarizing', label: '生成汇总', done: false },
  { key: 'syncing', label: '同步知识库', done: false },
  { key: 'done', label: '分析完成', done: false },
])

// 详情
const detailVisible = ref(false)
const detailRecord = ref(null)
const parsedDecisions = computed(() => {
  try { return JSON.parse(detailRecord.value?.key_decisions || '[]') } catch { return [] }
})
const parsedActions = computed(() => {
  try { return JSON.parse(detailRecord.value?.action_items || '[]') } catch { return [] }
})

// 获取列表
const fetchList = async () => {
  if (!projectId.value) return
  loading.value = true
  try {
    const res = await getReviewList(projectId.value, {
      review_type: props.reviewType,
      page: currentPage.value,
      page_size: pageSize.value,
    })
    reviewList.value = res.data.reviews || []
    total.value = res.data.total || 0
  } catch (e) {
    console.error('获取评审列表失败:', e)
  } finally {
    loading.value = false
  }
}

// 上传视频
const showUploadDialog = () => {
  uploadForm.value = { title: '', description: '', file: null }
  uploadVisible.value = true
}

const handleFileChange = (file) => {
  uploadForm.value.file = file.raw
}
const handleFileRemove = () => {
  uploadForm.value.file = null
}

const handleUpload = async () => {
  if (!uploadFormRef.value) return
  await uploadFormRef.value.validate()
  if (!uploadForm.value.file) {
    ElMessage.warning('请选择视频文件')
    return
  }

  uploading.value = true
  try {
    const formData = new FormData()
    formData.append('file', uploadForm.value.file)
    formData.append('title', uploadForm.value.title)
    formData.append('review_type', props.reviewType)
    if (uploadForm.value.description) {
      formData.append('description', uploadForm.value.description)
    }

    await uploadReviewVideo(projectId.value, formData)
    ElMessage.success('视频上传成功！可点击"AI分析"开始分析')
    uploadVisible.value = false
    fetchList()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '上传失败')
  } finally {
    uploading.value = false
  }
}

// AI分析
const startAnalyze = async (row) => {
  analyzeVisible.value = true
  analyzing.value = true
  analyzeProgress.value = 0
  analyzeMessage.value = '准备开始分析...'
  currentStep.value = ''
  analyzeProgressStatus.value = ''
  analyzeSteps.value.forEach(s => s.done = false)

  try {
    const token = userStore.token
    const baseApi = import.meta.env.VITE_BASE_API
    const url = `${baseApi}/knowledge/${projectId.value}/reviews/${row.id}/analyze`

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Accept': 'text/event-stream',
        'Authorization': `Bearer ${token}`,
      }
    })

    if (!response.ok) throw new Error(`HTTP ${response.status}`)

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })

      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))
            if (data.type === 'progress') {
              analyzeProgress.value = data.progress || 0
              analyzeMessage.value = data.message || ''
              currentStep.value = data.step || ''
              // 标记已完成的步骤
              const stepIdx = analyzeSteps.value.findIndex(s => s.key === data.step)
              if (stepIdx > 0) {
                for (let i = 0; i < stepIdx; i++) {
                  analyzeSteps.value[i].done = true
                }
              }
            } else if (data.type === 'done') {
              analyzeSteps.value.forEach(s => s.done = true)
              analyzeProgressStatus.value = 'success'
              analyzeMessage.value = '分析完成！'
            } else if (data.type === 'error') {
              analyzeProgressStatus.value = 'exception'
              analyzeMessage.value = `分析失败: ${data.message}`
            }
          } catch {}
        }
      }
    }
  } catch (e) {
    analyzeProgressStatus.value = 'exception'
    analyzeMessage.value = `分析出错: ${e.message}`
  } finally {
    analyzing.value = false
  }
}

// 查看详情
const viewDetail = async (row) => {
  try {
    const res = await getReviewDetail(projectId.value, row.id)
    detailRecord.value = res.data
    detailVisible.value = true
  } catch (e) {
    ElMessage.error('获取详情失败')
  }
}

// 删除
const handleDelete = async (row) => {
  try {
    await deleteReview(projectId.value, row.id)
    ElMessage.success('删除成功')
    fetchList()
  } catch (e) {
    ElMessage.error('删除失败')
  }
}

// 工具函数
const formatFileSize = (bytes) => {
  if (!bytes) return '-'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  return (bytes / (1024 * 1024 * 1024)).toFixed(2) + ' GB'
}

const formatTime = (t) => {
  if (!t) return '-'
  return new Date(t).toLocaleString('zh-CN')
}

const statusText = (s) => ({
  uploaded: '待分析',
  extracting: '提取帧中',
  analyzing: '分析中',
  completed: '已完成',
  failed: '失败',
}[s] || s)

const statusTagType = (s) => ({
  uploaded: 'info',
  extracting: 'warning',
  analyzing: 'warning',
  completed: 'success',
  failed: 'danger',
}[s] || 'info')

const reviewTypeText = (t) => ({
  requirement: '需求评审',
  technical: '技术评审',
  testcase: '用例评审',
}[t] || t)

const reviewTypeTag = (t) => ({
  requirement: 'primary',
  technical: '',
  testcase: 'success',
}[t] || '')

const renderMarkdown = (text) => {
  try { return md.render(text || '') } catch { return text }
}

// 监听项目变化
watch(projectId, () => { if (projectId.value) fetchList() })

onMounted(() => {
  if (projectId.value) fetchList()
})
</script>

<style scoped>
.review-container {
  padding: 10px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  font-size: 22px;
  color: #303133;
}

.subtitle {
  color: #909399;
  font-size: 14px;
  margin-top: 6px;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

/* 分析进度 */
.analyze-progress {
  padding: 10px 0;
}

.progress-header {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 16px;
  font-weight: 500;
}

.analyzing-icon.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.progress-steps {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 20px;
}

.step-item {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #909399;
  font-size: 14px;
  transition: all 0.3s;
}

.step-item.active {
  color: #409eff;
  font-weight: 500;
}

.step-item.done {
  color: #67c23a;
}

/* 详情 */
.review-detail {
  max-height: 70vh;
  overflow-y: auto;
}

.detail-section {
  margin-top: 20px;
}

.detail-section h4 {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #303133;
  margin-bottom: 10px;
  font-size: 15px;
  border-bottom: 1px solid #ebeef5;
  padding-bottom: 8px;
}

.decision-list, .action-list {
  padding-left: 20px;
  margin: 0;
}

.decision-list li, .action-list li {
  margin-bottom: 6px;
  color: #606266;
  line-height: 1.6;
}

.decision-list li::marker {
  color: #e6a23c;
}

.action-list li::marker {
  color: #409eff;
}

.analysis-content {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 16px;
  font-size: 14px;
  line-height: 1.8;
  color: #303133;
  max-height: 400px;
  overflow-y: auto;
}

.analysis-content :deep(h2) {
  font-size: 16px;
  color: #303133;
  margin: 16px 0 8px;
  border-bottom: 1px solid #ebeef5;
  padding-bottom: 6px;
}

.analysis-content :deep(h3) {
  font-size: 14px;
  color: #606266;
  margin: 12px 0 6px;
}

.analysis-content :deep(ul) {
  padding-left: 20px;
}

.analysis-content :deep(li) {
  margin-bottom: 4px;
}
</style>
