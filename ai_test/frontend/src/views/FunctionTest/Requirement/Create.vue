<template>
  <div class="requirement-create-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="breadcrumb-section">
          <el-breadcrumb separator="/">
            <el-breadcrumb-item>
              <router-link to="/function-test/requirement">
                需求管理
              </router-link>
            </el-breadcrumb-item>
            <el-breadcrumb-item>新建需求</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="action-section">
          <el-button @click="handleCancel">
            <el-icon><ArrowLeft /></el-icon>
            返回列表
          </el-button>
        </div>
      </div>
    </div>

    <!-- AI 文档提取区域 -->
    <div class="page-content ai-extract-section">
      <el-card>
        <template #header>
          <div class="card-header">
            <div class="title-section">
              <h2>
                <el-icon style="color: #8b5cf6; margin-right: 8px;"><MagicStick /></el-icon>
                AI 智能提取需求
              </h2>
              <p class="subtitle">上传需求文档、粘贴文档内容或输入文档链接，AI 将自动提取需求信息并填充到下方表单</p>
            </div>
          </div>
        </template>

        <div class="extract-content">
          <!-- 提取方式选择 -->
          <el-radio-group v-model="extractMode" size="large" class="extract-mode-selector">
            <el-radio-button value="file">
              <el-icon><UploadFilled /></el-icon>
              上传文档
            </el-radio-button>
            <el-radio-button value="text">
              <el-icon><DocumentCopy /></el-icon>
              粘贴文本
            </el-radio-button>
            <el-radio-button value="url">
              <el-icon><Link /></el-icon>
              文档链接
            </el-radio-button>
          </el-radio-group>

          <!-- 文件上传 -->
          <div v-if="extractMode === 'file'" class="extract-input-area">
            <el-upload
              ref="uploadRef"
              v-model:file-list="uploadFileList"
              :auto-upload="false"
              :limit="1"
              :on-exceed="handleExceed"
              :on-change="handleFileChange"
              accept=".pdf,.docx,.doc,.txt,.md"
              drag
              class="doc-upload"
            >
              <div class="upload-content">
                <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
                <div class="el-upload__text">
                  将文件拖到此处，或 <em>点击选择文件</em>
                </div>
                <div class="el-upload__tip">
                  支持 PDF、Word（.docx）、TXT、Markdown 格式，文件大小不超过 10MB
                </div>
              </div>
            </el-upload>
          </div>

          <!-- 粘贴文本（推荐用于飞书等需要登录的文档） -->
          <div v-else-if="extractMode === 'text'" class="extract-input-area">
            <el-alert
              type="info"
              :closable="false"
              show-icon
              style="margin-bottom: 12px;"
            >
              <template #title>
                <span>推荐用于飞书、Notion 等需要登录才能访问的云文档。请在文档中全选复制（Ctrl+A → Ctrl+C），然后粘贴到下方输入框。</span>
              </template>
            </el-alert>
            <el-input
              v-model="extractText"
              type="textarea"
              :rows="10"
              placeholder="请将需求文档内容粘贴到此处...&#10;&#10;操作方法：&#10;1. 打开飞书/Notion/Confluence 等文档&#10;2. 全选文档内容（Ctrl+A 或 Cmd+A）&#10;3. 复制（Ctrl+C 或 Cmd+C）&#10;4. 在此处粘贴（Ctrl+V 或 Cmd+V）"
              maxlength="50000"
              show-word-limit
              resize="vertical"
            />
          </div>

          <!-- URL 输入 -->
          <div v-else class="extract-input-area">
            <el-alert
              type="warning"
              :closable="false"
              show-icon
              style="margin-bottom: 12px;"
            >
              <template #title>
                <span>⚠️ 飞书、Notion 等需要登录的云文档链接无法直接抓取，建议使用「粘贴文本」方式。此处仅支持公开可访问的网页链接。</span>
              </template>
            </el-alert>
            <el-input
              v-model="extractUrl"
              placeholder="请输入公开可访问的需求文档链接，如 https://example.com/prd.html"
              size="large"
              clearable
            >
              <template #prepend>
                <el-icon><Link /></el-icon>
              </template>
            </el-input>
          </div>

          <!-- 提取按钮 -->
          <div class="extract-actions">
            <el-button
              type="primary"
              size="large"
              @click="handleExtract"
              :loading="extracting"
              :disabled="!canExtract"
            >
              <el-icon v-if="!extracting"><MagicStick /></el-icon>
              {{ extracting ? 'AI 正在提取中...' : 'AI 智能提取' }}
            </el-button>
            <span v-if="extracting" class="extract-tip">
              <el-icon class="is-loading"><Loading /></el-icon>
              AI 正在分析文档并提取需求信息，请稍候...
            </span>
          </div>

          <!-- 提取结果提示 -->
          <el-alert
            v-if="extractSuccess"
            title="需求信息提取成功！"
            description="AI 已将提取的需求标题、描述和优先级自动填充到下方表单中，您可以进一步编辑完善。"
            type="success"
            show-icon
            closable
            @close="extractSuccess = false"
            style="margin-top: 16px;"
          />
        </div>
      </el-card>
    </div>

    <!-- 创建表单 -->
    <div class="page-content">
      <el-card>
        <template #header>
          <div class="card-header">
            <div class="title-section">
              <h2>新建功能需求</h2>
              <p class="subtitle">创建新的功能需求，为后续测试用例生成提供基础</p>
            </div>
          </div>
        </template>

        <el-form
          ref="createFormRef"
          :model="createForm"
          :rules="createRules"
          label-width="120px"
          label-position="top"
          @submit.prevent="handleSubmit"
        >
          <!-- 基本信息表单 -->
          <div class="form-section">
            <h3 class="section-title">基本信息</h3>
            <div class="form-grid">
              <el-form-item label="需求标题" prop="title" class="title-item">
                <el-input
                  v-model="createForm.title"
                  placeholder="请输入需求标题，简洁明确地描述功能需求"
                  maxlength="200"
                  show-word-limit
                  size="large"
                />
              </el-form-item>

              <el-form-item label="所属模块" prop="module_id">
                <el-select
                  v-model="createForm.module_id"
                  placeholder="选择需求所属的项目模块"
                  size="large"
                  style="width: 100%;"
                >
                  <el-option
                    v-for="module in modules"
                    :key="module.id"
                    :label="module.name"
                    :value="module.id"
                  >
                    <div class="module-option">
                      <span class="module-name">{{ module.name }}</span>
                      <span v-if="module.description" class="module-desc">{{ module.description }}</span>
                    </div>
                  </el-option>
                </el-select>
              </el-form-item>

              <el-form-item label="优先级" prop="priority">
                <el-select
                  v-model="createForm.priority"
                  placeholder="选择需求优先级"
                  size="large"
                  style="width: 100%;"
                >
                  <el-option
                    v-for="(label, value) in availablePriorityLabels"
                    :key="value"
                    :label="label"
                    :value="parseInt(value)"
                  >
                    <div class="priority-option">
                      <el-tag
                        :color="REQUIREMENT_PRIORITY_COLORS[value]"
                        effect="light"
                        size="small"
                      >
                        {{ label }}
                      </el-tag>
                      <span class="priority-desc">{{ getPriorityDescription(parseInt(value)) }}</span>
                    </div>
                  </el-option>
                </el-select>
              </el-form-item>

              <el-form-item label="初始状态" prop="status">
                <el-select
                  v-model="createForm.status"
                  placeholder="选择需求初始状态"
                  size="large"
                  style="width: 100%;"
                >
                  <el-option
                    v-for="(label, value) in availableStatuses"
                    :key="value"
                    :label="label"
                    :value="value"
                  >
                    <div class="status-option">
                      <el-tag
                        :type="getStatusTagType(value)"
                        size="small"
                      >
                        {{ label }}
                      </el-tag>
                      <span class="status-desc">{{ getStatusDescription(value) }}</span>
                    </div>
                  </el-option>
                </el-select>
              </el-form-item>
            </div>
          </div>

          <!-- 描述编辑器 -->
          <div class="form-section">
            <h3 class="section-title">需求描述</h3>
            <el-form-item prop="description">
              <el-input
                v-model="createForm.description"
                type="textarea"
                :rows="12"
                placeholder="请详细描述功能需求，包括：&#10;1. 功能目标和用途&#10;2. 用户场景和使用流程&#10;3. 功能边界和限制条件&#10;4. 预期的输入输出&#10;5. 特殊要求或约束条件&#10;&#10;详细的需求描述有助于生成更准确的测试用例。"
                maxlength="2000"
                show-word-limit
                resize="vertical"
              />
            </el-form-item>
          </div>

          <!-- 操作按钮 -->
          <div class="form-actions">
            <el-button size="large" @click="handleCancel">
              取消
            </el-button>
            <el-button
              type="primary"
              size="large"
              @click="handleSubmit"
              :loading="saving && saveType === 'submit'"
            >
              提交审核
            </el-button>
          </div>
        </el-form>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, MagicStick, UploadFilled, Link, Loading, DocumentCopy } from '@element-plus/icons-vue'
import {
  createRequirement,
  extractRequirementFromDocument,
  REQUIREMENT_STATUS_LABELS,
  REQUIREMENT_PRIORITY_LABELS,
  REQUIREMENT_PRIORITY_COLORS,
  REQUIREMENT_STATUS,
  REQUIREMENT_PRIORITY
} from '@/api/functional_test'
import { getProjectModules } from '@/api/project'
import { useProjectStore } from '@/stores'

const router = useRouter()
const route = useRoute()
const projectStore = useProjectStore()

// 响应式数据
const saving = ref(false)
const saveType = ref('')
const modules = ref([])
const createFormRef = ref()

// AI 提取相关
const extractMode = ref('text') // 'file', 'text', or 'url'
const uploadFileList = ref([])
const extractUrl = ref('')
const extractText = ref('')
const extracting = ref(false)
const extractSuccess = ref(false)
const uploadRef = ref()

// 创建表单
const createForm = reactive({
  title: '',
  module_id: null,
  description: '',
  priority: REQUIREMENT_PRIORITY.MEDIUM, // 默认中等优先级
  status: REQUIREMENT_STATUS.DRAFT // 默认草稿状态
})

// 表单验证规则
const createRules = {
  title: [
    { required: true, message: '请输入需求标题', trigger: 'blur' },
    { min: 1, max: 200, message: '标题长度在 1 到 200 个字符', trigger: 'blur' }
  ],
  module_id: [
    { required: true, message: '请选择所属模块', trigger: 'change' }
  ],
  priority: [
    { required: true, message: '请选择优先级', trigger: 'change' }
  ],
  status: [
    { required: true, message: '请选择状态', trigger: 'change' }
  ]
}

// 计算属性
const projectId = computed(() => {
  const project = projectStore.currentProject
  if (!project || !project.id) {
    ElMessage.error('请先选择项目')
    router.push('/project')
    return null
  }
  return project.id
})

// 可用的初始状态（创建时只能选择草稿或直接提交审核）
const availableStatuses = computed(() => ({
  [REQUIREMENT_STATUS.DRAFT]: REQUIREMENT_STATUS_LABELS[REQUIREMENT_STATUS.DRAFT],
  [REQUIREMENT_STATUS.REVIEWING]: REQUIREMENT_STATUS_LABELS[REQUIREMENT_STATUS.REVIEWING]
}))

// 新增：限制优先级选项为 1-3
const availablePriorityLabels = computed(() => ({
  [REQUIREMENT_PRIORITY.LOW]: REQUIREMENT_PRIORITY_LABELS[REQUIREMENT_PRIORITY.LOW],
  [REQUIREMENT_PRIORITY.MEDIUM]: REQUIREMENT_PRIORITY_LABELS[REQUIREMENT_PRIORITY.MEDIUM],
  [REQUIREMENT_PRIORITY.HIGH]: REQUIREMENT_PRIORITY_LABELS[REQUIREMENT_PRIORITY.HIGH]
}))

// 方法
const getPriorityDescription = (priority) => {
  const descriptions = {
    [REQUIREMENT_PRIORITY.LOW]: '可以延后处理的需求',
    [REQUIREMENT_PRIORITY.MEDIUM]: '正常优先级的需求',
    [REQUIREMENT_PRIORITY.HIGH]: '重要且紧急的需求',
    [REQUIREMENT_PRIORITY.URGENT]: '最高优先级，需立即处理'
  }
  return descriptions[priority] || ''
}

const getStatusDescription = (status) => {
  const descriptions = {
    [REQUIREMENT_STATUS.DRAFT]: '保存为草稿，可继续编辑',
    [REQUIREMENT_STATUS.REVIEWING]: '提交审核，等待批准'
  }
  return descriptions[status] || ''
}

const getStatusTagType = (status) => {
  const typeMap = {
    draft: '',
    reviewing: 'warning',
    approved: 'success',
    rejected: 'danger',
    archived: 'info'
  }
  return typeMap[status] || ''
}

const loadModules = async () => {
  if (!projectId.value) {
    return
  }
  
  try {
    const response = await getProjectModules(projectId.value)
    modules.value = (response.data && response.data.datas) ? response.data.datas : []
    
    // 如果只有一个模块，自动选择
    if (modules.value.length === 1) {
      createForm.module_id = modules.value[0].id
    }
  } catch (error) {
    console.error('加载模块列表失败:', error)
    ElMessage.error('加载模块列表失败')
  }
}

const validateForm = async () => {
  try {
    await createFormRef.value.validate()
    return true
  } catch (error) {
    return false
  }
}

const saveRequirement = async (status) => {
  if (!projectId.value) {
    throw new Error('项目ID不能为空')
  }
  
  const formData = {
    ...createForm,
    status
  }
  
  try {
    const response = await createRequirement(projectId.value, formData)
    return response.data
  } catch (error) {
    console.error('保存需求失败:', error)
    throw error
  }
}

const handleSaveDraft = async () => {
  if (!(await validateForm())) return
  
  saveType.value = 'draft'
  saving.value = true
  
  try {
    await saveRequirement(REQUIREMENT_STATUS.DRAFT)
    ElMessage.success('需求草稿保存成功')
    router.push('/function-test/requirement')
  } catch (error) {
    ElMessage.error('保存草稿失败')
  } finally {
    saving.value = false
    saveType.value = ''
  }
}

const handleSubmit = async () => {
  if (!(await validateForm())) return
  
  // 如果没有填写描述，提醒用户
  if (!createForm.description.trim()) {
    try {
      await ElMessageBox.confirm(
        '您还没有填写需求描述，详细的描述有助于生成更准确的测试用例。确定要继续提交吗？',
        '提示',
        {
          confirmButtonText: '继续提交',
          cancelButtonText: '返回编辑',
          type: 'warning'
        }
      )
    } catch {
      return
    }
  }
  
  saveType.value = 'submit'
  saving.value = true
  
  try {
    const targetStatus = createForm.status === REQUIREMENT_STATUS.DRAFT 
      ? REQUIREMENT_STATUS.DRAFT 
      : REQUIREMENT_STATUS.REVIEWING
      
    await saveRequirement(targetStatus)
    
    const message = targetStatus === REQUIREMENT_STATUS.DRAFT 
      ? '需求创建成功' 
      : '需求已提交审核'
    ElMessage.success(message)
    
    router.push('/function-test/requirement')
  } catch (error) {
    ElMessage.error('提交需求失败')
  } finally {
    saving.value = false
    saveType.value = ''
  }
}

// === AI 文档提取相关方法 ===

// 是否可以执行提取
const canExtract = computed(() => {
  if (extractMode.value === 'file') {
    return uploadFileList.value.length > 0
  } else if (extractMode.value === 'text') {
    return extractText.value.trim().length > 0
  } else {
    return extractUrl.value.trim().length > 0
  }
})

// 文件数量超限处理
const handleExceed = () => {
  ElMessage.warning('只能上传一个文件，请先移除已选文件')
}

// 文件变化处理
const handleFileChange = (file) => {
  // 验证文件大小
  if (file.size > 10 * 1024 * 1024) {
    ElMessage.error('文件大小不能超过 10MB')
    uploadFileList.value = []
    return
  }
  // 验证文件类型
  const allowedExts = ['.pdf', '.docx', '.doc', '.txt', '.md']
  const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase()
  if (!allowedExts.includes(ext)) {
    ElMessage.error('不支持的文件格式，请上传 PDF、Word、TXT 或 Markdown 文件')
    uploadFileList.value = []
    return
  }
}

// 执行 AI 提取
const handleExtract = async () => {
  if (!projectId.value) return

  extracting.value = true
  extractSuccess.value = false

  try {
    const formData = new FormData()

    if (extractMode.value === 'file') {
      if (uploadFileList.value.length === 0) {
        ElMessage.warning('请先选择要上传的文档文件')
        extracting.value = false
        return
      }
      formData.append('file', uploadFileList.value[0].raw)
    } else if (extractMode.value === 'text') {
      if (!extractText.value.trim()) {
        ElMessage.warning('请粘贴需求文档内容')
        extracting.value = false
        return
      }
      formData.append('text', extractText.value.trim())
    } else {
      if (!extractUrl.value.trim()) {
        ElMessage.warning('请输入文档链接地址')
        extracting.value = false
        return
      }
      formData.append('url', extractUrl.value.trim())
    }

    const response = await extractRequirementFromDocument(projectId.value, formData)

    if (response.data && response.data.success) {
      const extractedData = response.data.data

      // 将提取的数据填充到表单
      if (extractedData.title) {
        createForm.title = extractedData.title
      }
      if (extractedData.description) {
        createForm.description = extractedData.description
      }
      if (extractedData.priority && [1, 2, 3].includes(extractedData.priority)) {
        createForm.priority = extractedData.priority
      }

      extractSuccess.value = true
      ElMessage.success('AI 需求信息提取成功，已自动填充到表单中')
    } else {
      ElMessage.error(response.data?.message || 'AI 提取失败，请稍后重试')
    }
  } catch (error) {
    console.error('AI 提取失败:', error)
    const errorMsg = error.response?.data?.detail || error.message || 'AI 提取失败，请稍后重试'
    ElMessage.error(errorMsg)
  } finally {
    extracting.value = false
  }
}

const handleCancel = async () => {
  // 检查是否有未保存的内容
  const hasContent = createForm.title.trim() || createForm.description.trim()
  
  if (hasContent) {
    try {
      await ElMessageBox.confirm(
        '您有未保存的内容，确定要离开吗？',
        '确认离开',
        {
          confirmButtonText: '确定离开',
          cancelButtonText: '继续编辑',
          type: 'warning'
        }
      )
    } catch {
      return
    }
  }
  
  router.push('/function-test/requirement')
}

// 生命周期
onMounted(async () => {
  await loadModules()
})
</script>

<style scoped>
.requirement-create-page {
  padding: 24px;
  background: #f8fafc;
  min-height: 100vh;
}

.page-header {
  margin-bottom: 24px;
}

/* AI 提取区域样式 */
.ai-extract-section {
  margin-bottom: 24px;
}

.ai-extract-section .card-header h2 {
  display: flex;
  align-items: center;
}

.extract-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.extract-mode-selector {
  align-self: flex-start;
}

.extract-mode-selector .el-radio-button__inner {
  display: flex;
  align-items: center;
  gap: 6px;
}

.extract-input-area {
  width: 100%;
}

.doc-upload {
  width: 100%;
}

.doc-upload :deep(.el-upload-dragger) {
  width: 100%;
  padding: 40px 20px;
  border: 2px dashed #d9d9d9;
  border-radius: 8px;
  transition: border-color 0.3s;
}

.doc-upload :deep(.el-upload-dragger:hover) {
  border-color: #8b5cf6;
}

.doc-upload :deep(.el-upload) {
  width: 100%;
}

.upload-content {
  text-align: center;
}

.upload-content .el-icon--upload {
  font-size: 48px;
  color: #8b5cf6;
  margin-bottom: 12px;
}

.upload-content .el-upload__text {
  color: #606266;
  font-size: 14px;
  margin-bottom: 8px;
}

.upload-content .el-upload__text em {
  color: #8b5cf6;
  font-style: normal;
}

.upload-content .el-upload__tip {
  color: #909399;
  font-size: 12px;
}

.extract-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.extract-tip {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #8b5cf6;
  font-size: 14px;
}

.extract-tip .is-loading {
  animation: rotate 1.5s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: white;
  padding: 20px 24px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.breadcrumb-section {
  flex: 1;
}

.action-section {
  display: flex;
  gap: 12px;
}

.page-content {
  background: white;
  border-radius: 8px;
  overflow: hidden;
}

.card-header {
  border-bottom: 1px solid #e5e7eb;
  padding-bottom: 16px;
}

.title-section h2 {
  color: #1f2937;
  margin: 0 0 8px 0;
  font-size: 20px;
  font-weight: 600;
}

.subtitle {
  color: #6b7280;
  margin: 0;
  font-size: 14px;
}

.form-section {
  margin-bottom: 32px;
}

.section-title {
  color: #1f2937;
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 20px 0;
  padding-bottom: 8px;
  border-bottom: 2px solid #8b5cf6;
}

.form-grid {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr;
  gap: 24px;
}

.title-item {
  grid-column: 1 / -1;
}

.module-option,
.priority-option,
.status-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.module-name {
  font-weight: 500;
}

.module-desc,
.priority-desc,
.status-desc {
  font-size: 12px;
  color: #6b7280;
  margin-left: 8px;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 16px;
  padding-top: 24px;
  border-top: 1px solid #e5e7eb;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .form-grid {
    grid-template-columns: 1fr 1fr;
  }
  
  .title-item {
    grid-column: 1 / -1;
  }
}

@media (max-width: 768px) {
  .requirement-create-page {
    padding: 16px;
  }
  
  .header-content {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
  
  .form-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .form-actions {
    flex-direction: column-reverse;
  }
  
  .module-option,
  .priority-option,
  .status-option {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
}

/* Element Plus 样式覆盖 */
:deep(.el-textarea__inner) {
  font-family: inherit;
  line-height: 1.6;
}

:deep(.el-form-item__label) {
  font-weight: 500;
  color: #374151;
}

:deep(.el-input__inner) {
  border-radius: 6px;
}

:deep(.el-select .el-input__inner) {
  border-radius: 6px;
}
</style>