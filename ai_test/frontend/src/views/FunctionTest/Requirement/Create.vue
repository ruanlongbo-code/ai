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

    <!-- AI 智能提取区域 -->
    <div class="page-content ai-extract-section">
      <el-card>
        <template #header>
          <div class="card-header">
            <div class="title-section">
              <h2>
                <el-icon style="color: #8b5cf6; margin-right: 8px;"><MagicStick /></el-icon>
                AI 智能提取需求
              </h2>
              <p class="subtitle">在下方输入框中输入文本、粘贴图片、上传文档/视频，AI 将自动提取需求信息</p>
            </div>
          </div>
        </template>

        <div class="extract-content">
          <!-- ======= 统一输入区域 ======= -->
          <div
            class="unified-input-area"
            :class="{ 'drag-over': isDragOver, 'is-focused': isInputFocused }"
            @dragover.prevent="handleDragOver"
            @dragleave="handleDragLeave"
            @drop.prevent="handleDrop"
          >
            <!-- 文本输入区 -->
            <textarea
              ref="textareaRef"
              v-model="inputText"
              class="input-textarea"
              placeholder="在此输入或粘贴需求文本、也可以直接粘贴图片 (Ctrl+V)..."
              @paste="handlePaste"
              @focus="isInputFocused = true"
              @blur="isInputFocused = false"
              rows="5"
            ></textarea>

            <!-- 附件预览区域 -->
            <div v-if="attachments.length > 0" class="attachments-area">
              <div class="attachments-title">
                <el-icon><Paperclip /></el-icon>
                <span>已添加 {{ attachments.length }} 个附件</span>
              </div>
              <div class="attachments-grid">
                <div
                  v-for="(att, idx) in attachments"
                  :key="idx"
                  class="attachment-item"
                  :class="att.type"
                >
                  <!-- 图片预览 -->
                  <template v-if="att.type === 'image'">
                    <div class="att-preview image-preview-thumb">
                      <img :src="att.previewUrl" :alt="att.name" />
                    </div>
                  </template>
                  <!-- 视频预览 -->
                  <template v-else-if="att.type === 'video'">
                    <div class="att-preview video-preview-thumb">
                      <el-icon class="file-type-icon"><VideoCamera /></el-icon>
                    </div>
                  </template>
                  <!-- 文档预览 -->
                  <template v-else>
                    <div class="att-preview doc-preview-thumb">
                      <el-icon class="file-type-icon"><Document /></el-icon>
                    </div>
                  </template>
                  <div class="att-info">
                    <span class="att-name" :title="att.name">{{ att.name }}</span>
                    <span class="att-size">{{ formatFileSize(att.size) }}</span>
                  </div>
                  <el-button
                    class="att-remove"
                    type="danger"
                    :icon="Close"
                    size="small"
                    circle
                    plain
                    @click="removeAttachment(idx)"
                  />
                </div>
              </div>
            </div>

            <!-- URL 输入（可选） -->
            <div v-if="showUrlInput" class="url-input-row">
              <el-input
                v-model="inputUrl"
                placeholder="输入公开可访问的文档链接 https://..."
                size="default"
                clearable
              >
                <template #prepend>
                  <el-icon><Link /></el-icon>
                </template>
                <template #append>
                  <el-button @click="showUrlInput = false">
                    <el-icon><Close /></el-icon>
                  </el-button>
                </template>
              </el-input>
            </div>

            <!-- 底部工具栏 -->
            <div class="input-toolbar">
              <div class="toolbar-left">
                <el-tooltip content="上传文档 (PDF/Word/TXT/MD)" placement="top">
                  <el-button text class="toolbar-btn" @click="triggerFileSelect('document')">
                    <el-icon><FolderOpened /></el-icon>
                    <span>文档</span>
                  </el-button>
                </el-tooltip>
                <el-tooltip content="上传/粘贴图片 (PNG/JPG/WebP)" placement="top">
                  <el-button text class="toolbar-btn" @click="triggerFileSelect('image')">
                    <el-icon><PictureFilled /></el-icon>
                    <span>图片</span>
                  </el-button>
                </el-tooltip>
                <el-tooltip content="上传视频 (MP4/AVI/MOV)" placement="top">
                  <el-button text class="toolbar-btn" @click="triggerFileSelect('video')">
                    <el-icon><VideoCamera /></el-icon>
                    <span>视频</span>
                  </el-button>
                </el-tooltip>
                <el-tooltip content="添加文档链接" placement="top">
                  <el-button text class="toolbar-btn" @click="showUrlInput = !showUrlInput">
                    <el-icon><Link /></el-icon>
                    <span>链接</span>
                  </el-button>
                </el-tooltip>
              </div>
              <div class="toolbar-right">
                <span class="input-hint">
                  <el-icon><InfoFilled /></el-icon>
                  支持拖拽文件、Ctrl+V 粘贴图片/文本
                </span>
              </div>
            </div>
          </div>

          <!-- 隐藏的文件选择器 -->
          <input ref="fileInputRef" type="file" style="display:none;" @change="handleFileInputChange" :accept="fileInputAccept" multiple />

          <!-- 提取按钮 & 进度 -->
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
          </div>

          <!-- 流式进度区域 -->
          <div v-if="extracting || streamMessages.length > 0" class="stream-progress-area">
            <div class="progress-bar-container" v-if="extracting">
              <el-progress :percentage="extractProgress" :stroke-width="6" :show-text="false" color="#8b5cf6" />
              <span class="progress-text">{{ extractProgressText }}</span>
            </div>
            <div class="stream-content" v-if="streamRawContent">
              <div class="stream-label">AI 分析输出：</div>
              <div class="stream-text">{{ streamRawContent }}</div>
            </div>
          </div>

          <!-- 提取成功提示 -->
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
import {
  ArrowLeft, MagicStick, UploadFilled, Link, Loading,
  PictureFilled, Delete, Close, Document, VideoCamera,
  FolderOpened, InfoFilled, Paperclip
} from '@element-plus/icons-vue'
import {
  createRequirement,
  extractRequirementStream,
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

// ===== 统一输入区域 =====
const inputText = ref('')
const inputUrl = ref('')
const showUrlInput = ref(false)
const attachments = ref([])       // [{type:'image'|'document'|'video', file:File, name, size, previewUrl?}]
const isDragOver = ref(false)
const isInputFocused = ref(false)
const textareaRef = ref()
const fileInputRef = ref()
const fileInputAccept = ref('*')  // 动态切换
const currentFileType = ref('')   // 'image'|'document'|'video'

// 提取状态
const extracting = ref(false)
const extractSuccess = ref(false)
const extractProgress = ref(0)
const extractProgressText = ref('')
const streamMessages = ref([])
const streamRawContent = ref('')

// 创建表单
const createForm = reactive({
  title: '',
  module_id: null,
  description: '',
  priority: REQUIREMENT_PRIORITY.MEDIUM,
  status: REQUIREMENT_STATUS.DRAFT
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

const availableStatuses = computed(() => ({
  [REQUIREMENT_STATUS.DRAFT]: REQUIREMENT_STATUS_LABELS[REQUIREMENT_STATUS.DRAFT],
  [REQUIREMENT_STATUS.REVIEWING]: REQUIREMENT_STATUS_LABELS[REQUIREMENT_STATUS.REVIEWING]
}))

const availablePriorityLabels = computed(() => ({
  [REQUIREMENT_PRIORITY.LOW]: REQUIREMENT_PRIORITY_LABELS[REQUIREMENT_PRIORITY.LOW],
  [REQUIREMENT_PRIORITY.MEDIUM]: REQUIREMENT_PRIORITY_LABELS[REQUIREMENT_PRIORITY.MEDIUM],
  [REQUIREMENT_PRIORITY.HIGH]: REQUIREMENT_PRIORITY_LABELS[REQUIREMENT_PRIORITY.HIGH]
}))

const canExtract = computed(() => {
  return inputText.value.trim().length > 0 ||
    attachments.value.length > 0 ||
    (showUrlInput.value && inputUrl.value.trim().length > 0)
})

// ===== 工具方法 =====
const formatFileSize = (bytes) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

const getFileCategory = (file) => {
  const name = file.name.toLowerCase()
  const type = file.type || ''
  if (type.startsWith('image/') || /\.(png|jpe?g|webp|gif|bmp|svg)$/.test(name)) return 'image'
  if (type.startsWith('video/') || /\.(mp4|avi|mov|mkv|webm|flv)$/.test(name)) return 'video'
  return 'document'
}

const addFile = (file) => {
  // 检查大小限制 20MB
  if (file.size > 20 * 1024 * 1024) {
    ElMessage.warning(`文件 "${file.name}" 超过 20MB 大小限制`)
    return
  }
  // 检查重复
  if (attachments.value.some(a => a.name === file.name && a.size === file.size)) {
    ElMessage.info(`文件 "${file.name}" 已添加`)
    return
  }

  const category = getFileCategory(file)
  const att = {
    type: category,
    file: file,
    name: file.name,
    size: file.size,
    previewUrl: ''
  }

  // 图片预览
  if (category === 'image') {
    const reader = new FileReader()
    reader.onload = (e) => { att.previewUrl = e.target.result }
    reader.readAsDataURL(file)
  }

  attachments.value.push(att)
}

const removeAttachment = (idx) => {
  attachments.value.splice(idx, 1)
}

// ===== 拖拽 =====
const handleDragOver = () => { isDragOver.value = true }
const handleDragLeave = () => { isDragOver.value = false }
const handleDrop = (event) => {
  isDragOver.value = false
  const files = event.dataTransfer?.files
  if (files) {
    for (const f of files) {
      addFile(f)
    }
  }
}

// ===== 粘贴 =====
const handlePaste = (event) => {
  const items = event.clipboardData?.items
  if (!items) return

  for (const item of items) {
    if (item.type.startsWith('image/')) {
      event.preventDefault()
      const file = item.getAsFile()
      if (file) addFile(file)
      return
    }
  }
  // 纯文本粘贴由 textarea v-model 自动处理
}

// ===== 文件选择 =====
const triggerFileSelect = (type) => {
  currentFileType.value = type
  if (type === 'document') {
    fileInputAccept.value = '.pdf,.docx,.doc,.txt,.md'
  } else if (type === 'image') {
    fileInputAccept.value = 'image/png,image/jpeg,image/jpg,image/webp,image/gif'
  } else if (type === 'video') {
    fileInputAccept.value = 'video/mp4,video/avi,video/quicktime,video/webm,.mp4,.avi,.mov,.mkv,.webm'
  }
  // 需要等 accept 更新后再 click
  setTimeout(() => {
    fileInputRef.value?.click()
  }, 50)
}

const handleFileInputChange = (event) => {
  const files = event.target.files
  if (files) {
    for (const f of files) {
      addFile(f)
    }
  }
  event.target.value = ''
}

// ===== AI 提取 =====
const handleExtract = async () => {
  if (!projectId.value) return
  if (!canExtract.value) {
    ElMessage.warning('请先输入文本、上传文件或提供链接')
    return
  }

  extracting.value = true
  extractSuccess.value = false
  extractProgress.value = 5
  extractProgressText.value = '准备数据中...'
  streamMessages.value = []
  streamRawContent.value = ''

  try {
    const formData = new FormData()

    // 文本
    if (inputText.value.trim()) {
      formData.append('text', inputText.value.trim())
    }

    // 文件
    for (const att of attachments.value) {
      formData.append('files', att.file)
    }

    // URL
    if (showUrlInput.value && inputUrl.value.trim()) {
      formData.append('url', inputUrl.value.trim())
    }

    extractProgress.value = 10
    extractProgressText.value = '上传数据中...'

    const response = await extractRequirementStream(projectId.value, formData)

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}))
      throw new Error(errData.detail || `请求失败: ${response.status}`)
    }

    // 读取 SSE 流
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
        if (!line.startsWith('data: ')) continue
        const dataStr = line.slice(6).trim()
        if (!dataStr || dataStr === '[DONE]') continue

        try {
          const data = JSON.parse(dataStr)

          if (data.type === 'progress') {
            extractProgress.value = data.progress || extractProgress.value
            extractProgressText.value = data.message || ''
            streamMessages.value.push(data.message)
          } else if (data.type === 'chunk') {
            streamRawContent.value += data.content
          } else if (data.type === 'result') {
            const result = data.data
            if (result) {
              if (result.title) createForm.title = result.title
              if (result.description) createForm.description = result.description
              if (result.priority && [1, 2, 3].includes(result.priority)) {
                createForm.priority = result.priority
              }
              extractSuccess.value = true
              ElMessage.success('AI 需求信息提取成功，已自动填充到表单中')
            }
          } else if (data.type === 'done') {
            extractProgress.value = 100
            extractProgressText.value = '提取完成'
          } else if (data.type === 'error') {
            ElMessage.error(data.message || 'AI提取失败')
          }
        } catch (e) {
          // 忽略解析错误
        }
      }
    }
  } catch (error) {
    console.error('AI提取失败:', error)
    ElMessage.error(error.message || 'AI 提取失败，请稍后重试')
  } finally {
    extracting.value = false
  }
}

// ===== 表单相关 =====
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
  if (!projectId.value) return
  try {
    const response = await getProjectModules(projectId.value)
    modules.value = (response.data && response.data.datas) ? response.data.datas : []
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
  if (!projectId.value) throw new Error('项目ID不能为空')
  const formData = { ...createForm, status }
  try {
    const response = await createRequirement(projectId.value, formData)
    return response.data
  } catch (error) {
    console.error('保存需求失败:', error)
    throw error
  }
}

const handleSubmit = async () => {
  if (!(await validateForm())) return

  if (!createForm.description.trim()) {
    try {
      await ElMessageBox.confirm(
        '您还没有填写需求描述，详细的描述有助于生成更准确的测试用例。确定要继续提交吗？',
        '提示',
        { confirmButtonText: '继续提交', cancelButtonText: '返回编辑', type: 'warning' }
      )
    } catch { return }
  }

  saveType.value = 'submit'
  saving.value = true

  try {
    const targetStatus = createForm.status === REQUIREMENT_STATUS.DRAFT
      ? REQUIREMENT_STATUS.DRAFT
      : REQUIREMENT_STATUS.REVIEWING

    await saveRequirement(targetStatus)
    const message = targetStatus === REQUIREMENT_STATUS.DRAFT ? '需求创建成功' : '需求已提交审核'
    ElMessage.success(message)
    router.push('/function-test/requirement')
  } catch (error) {
    ElMessage.error('提交需求失败')
  } finally {
    saving.value = false
    saveType.value = ''
  }
}

const handleCancel = async () => {
  const hasContent = createForm.title.trim() || createForm.description.trim()
  if (hasContent) {
    try {
      await ElMessageBox.confirm('您有未保存的内容，确定要离开吗？', '确认离开', {
        confirmButtonText: '确定离开',
        cancelButtonText: '继续编辑',
        type: 'warning'
      })
    } catch { return }
  }
  router.push('/function-test/requirement')
}

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

/* ====== 统一输入区域 ====== */
.unified-input-area {
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.3s;
  background: #fff;
}

.unified-input-area.is-focused {
  border-color: #8b5cf6;
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.08);
}

.unified-input-area.drag-over {
  border-color: #8b5cf6;
  border-style: dashed;
  background: #faf5ff;
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.15);
}

.input-textarea {
  width: 100%;
  border: none;
  outline: none;
  resize: vertical;
  padding: 16px 18px;
  font-size: 14px;
  line-height: 1.7;
  color: #1f2937;
  background: transparent;
  font-family: inherit;
  min-height: 120px;
  box-sizing: border-box;
}

.input-textarea::placeholder {
  color: #9ca3af;
}

/* 附件区域 */
.attachments-area {
  border-top: 1px solid #f3f4f6;
  padding: 12px 16px;
  background: #fafbfc;
}

.attachments-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 10px;
}

.attachments-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.attachment-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  min-width: 180px;
  max-width: 280px;
  position: relative;
  transition: all 0.2s;
}

.attachment-item:hover {
  border-color: #8b5cf6;
  box-shadow: 0 2px 8px rgba(139, 92, 246, 0.1);
}

.att-preview {
  width: 40px;
  height: 40px;
  border-radius: 6px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.image-preview-thumb {
  background: #f3f4f6;
}

.image-preview-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.video-preview-thumb {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff;
}

.doc-preview-thumb {
  background: linear-gradient(135deg, #f093fb, #f5576c);
  color: #fff;
}

.file-type-icon {
  font-size: 20px;
}

.att-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.att-name {
  font-size: 13px;
  color: #374151;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.att-size {
  font-size: 11px;
  color: #9ca3af;
}

.att-remove {
  position: absolute;
  top: -6px;
  right: -6px;
  width: 20px !important;
  height: 20px !important;
  padding: 0 !important;
}

/* URL 输入 */
.url-input-row {
  border-top: 1px solid #f3f4f6;
  padding: 10px 16px;
  background: #fafbfc;
}

/* 底部工具栏 */
.input-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-top: 1px solid #f3f4f6;
  padding: 8px 12px;
  background: #fafbfc;
}

.toolbar-left {
  display: flex;
  gap: 4px;
}

.toolbar-btn {
  font-size: 13px;
  color: #6b7280;
  padding: 6px 10px;
  border-radius: 6px;
}

.toolbar-btn:hover {
  color: #8b5cf6;
  background: #f3e8ff;
}

.toolbar-btn .el-icon {
  margin-right: 4px;
}

.toolbar-right {
  display: flex;
  align-items: center;
}

.input-hint {
  font-size: 12px;
  color: #9ca3af;
  display: flex;
  align-items: center;
  gap: 4px;
}

/* 提取按钮 */
.extract-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

/* 流式进度 */
.stream-progress-area {
  background: #faf5ff;
  border: 1px solid #e9d5ff;
  border-radius: 8px;
  padding: 16px;
}

.progress-bar-container {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.progress-bar-container .el-progress {
  flex: 1;
}

.progress-text {
  font-size: 13px;
  color: #8b5cf6;
  white-space: nowrap;
  min-width: 120px;
}

.stream-content {
  max-height: 200px;
  overflow-y: auto;
}

.stream-label {
  font-size: 12px;
  color: #8b5cf6;
  font-weight: 600;
  margin-bottom: 6px;
}

.stream-text {
  font-size: 13px;
  color: #4b5563;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: 'SF Mono', 'Fira Code', monospace;
  background: #fff;
  padding: 10px;
  border-radius: 6px;
  max-height: 160px;
  overflow-y: auto;
}

/* 其余样式 */
.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: white;
  padding: 20px 24px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.breadcrumb-section { flex: 1; }
.action-section { display: flex; gap: 12px; }

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

.form-section { margin-bottom: 32px; }

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

.title-item { grid-column: 1 / -1; }

.module-option,
.priority-option,
.status-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.module-name { font-weight: 500; }

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

@media (max-width: 1024px) {
  .form-grid { grid-template-columns: 1fr 1fr; }
  .title-item { grid-column: 1 / -1; }
}

@media (max-width: 768px) {
  .requirement-create-page { padding: 16px; }
  .header-content { flex-direction: column; gap: 16px; align-items: stretch; }
  .form-grid { grid-template-columns: 1fr; gap: 16px; }
  .form-actions { flex-direction: column-reverse; }
  .input-toolbar { flex-direction: column; gap: 8px; }
}

:deep(.el-textarea__inner) { font-family: inherit; line-height: 1.6; }
:deep(.el-form-item__label) { font-weight: 500; color: #374151; }
:deep(.el-input__inner) { border-radius: 6px; }
:deep(.el-select .el-input__inner) { border-radius: 6px; }
</style>
