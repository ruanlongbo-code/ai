<template>
  <div class="requirement-create-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="breadcrumb-section">
          <el-breadcrumb separator="/">
            <el-breadcrumb-item>
              <router-link to="/function-test/requirement">需求管理</router-link>
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

    <!-- AI 智能提取 + 一键生成XMind -->
    <div class="page-content ai-extract-section">
      <el-card>
        <template #header>
          <div class="card-header">
            <div class="title-section">
              <h2>
                <el-icon style="color: #8b5cf6; margin-right: 8px;"><MagicStick /></el-icon>
                AI 智能提取需求 & 一键生成用例
              </h2>
              <p class="subtitle">输入文本、粘贴图片、上传文档，AI 自动提取需求并生成 XMind 测试用例</p>
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
            <textarea
              ref="textareaRef"
              v-model="inputText"
              class="input-textarea"
              placeholder="在此输入或粘贴需求文本，也可以直接粘贴图片 (Ctrl+V)..."
              @paste="handlePaste"
              @focus="isInputFocused = true"
              @blur="isInputFocused = false"
              rows="5"
            ></textarea>

            <!-- 附件预览 -->
            <div v-if="attachments.length > 0" class="attachments-area">
              <div class="attachments-title">
                <el-icon><Paperclip /></el-icon>
                <span>已添加 {{ attachments.length }} 个附件</span>
                </div>
              <div class="attachments-grid">
                <div v-for="(att, idx) in attachments" :key="idx" class="attachment-item" :class="att.type">
                  <template v-if="att.type === 'image'">
                    <div class="att-preview image-preview-thumb">
                      <img :src="att.previewUrl" :alt="att.name" />
                </div>
                  </template>
                  <template v-else-if="att.type === 'video'">
                    <div class="att-preview video-preview-thumb">
                      <el-icon class="file-type-icon"><VideoCamera /></el-icon>
              </div>
                  </template>
                  <template v-else>
                    <div class="att-preview doc-preview-thumb">
                      <el-icon class="file-type-icon"><Document /></el-icon>
          </div>
              </template>
                  <div class="att-info">
                    <span class="att-name" :title="att.name">{{ att.name }}</span>
                    <span class="att-size">{{ formatFileSize(att.size) }}</span>
                  </div>
                  <el-button class="att-remove" type="danger" :icon="Close" size="small" circle plain @click="removeAttachment(idx)" />
                </div>
              </div>
          </div>

          <!-- URL 输入 -->
            <div v-if="showUrlInput" class="url-input-row">
              <el-input v-model="inputUrl" placeholder="输入公开可访问的文档链接 https://..." size="default" clearable>
                <template #prepend><el-icon><Link /></el-icon></template>
                <template #append>
                  <el-button @click="showUrlInput = false"><el-icon><Close /></el-icon></el-button>
              </template>
            </el-input>
          </div>

            <!-- 底部工具栏 -->
            <div class="input-toolbar">
              <div class="toolbar-left">
                <el-tooltip content="上传文档 (PDF/Word/TXT/MD)" placement="top">
                  <el-button text class="toolbar-btn" @click="triggerFileSelect('document')">
                    <el-icon><FolderOpened /></el-icon><span>文档</span>
                  </el-button>
                </el-tooltip>
                <el-tooltip content="上传/粘贴图片 (PNG/JPG/WebP)" placement="top">
                  <el-button text class="toolbar-btn" @click="triggerFileSelect('image')">
                    <el-icon><PictureFilled /></el-icon><span>图片</span>
                  </el-button>
                </el-tooltip>
                <el-tooltip content="上传视频 (MP4/AVI/MOV)" placement="top">
                  <el-button text class="toolbar-btn" @click="triggerFileSelect('video')">
                    <el-icon><VideoCamera /></el-icon><span>视频</span>
                  </el-button>
                </el-tooltip>
                <el-tooltip content="添加文档链接" placement="top">
                  <el-button text class="toolbar-btn" @click="showUrlInput = !showUrlInput">
                    <el-icon><Link /></el-icon><span>链接</span>
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

          <input ref="fileInputRef" type="file" style="display:none;" @change="handleFileInputChange" :accept="fileInputAccept" multiple />

          <!-- 双按钮区域 -->
          <div class="extract-actions">
            <el-button
              type="primary"
              size="large"
              @click="handleExtract"
              :loading="extracting"
              :disabled="!canExtract || xmindGenerating"
            >
              <el-icon v-if="!extracting"><MagicStick /></el-icon>
              {{ extracting ? 'AI 提取中...' : 'AI 提取需求' }}
            </el-button>
            <el-button
              type="success"
              size="large"
              @click="handleGenerateXmind"
              :loading="xmindGenerating"
              :disabled="!canExtract || extracting"
            >
              <el-icon v-if="!xmindGenerating"><Download /></el-icon>
              {{ xmindGenerating ? '用例生成中...' : '⚡ 一键生成XMind用例' }}
            </el-button>
          </div>

          <!-- 流式进度（AI提取需求） -->
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

          <!-- 一键生成XMind 进度 -->
          <div v-if="xmindGenerating || xmindResult" class="xmind-progress-area">
            <div class="progress-bar-container" v-if="xmindGenerating">
              <el-progress :percentage="xmindProgress" :stroke-width="8" :show-text="false" color="#67c23a" />
              <span class="progress-text green">{{ xmindProgressText }}</span>
            </div>

            <!-- 生成结果 - 用例预览 + 下载 -->
            <div v-if="xmindResult" class="xmind-result">
              <div class="result-header">
                <div class="result-summary">
                  <el-icon style="color: #67c23a; font-size: 24px;"><SuccessFilled /></el-icon>
                  <div>
                    <h3>用例生成完成！</h3>
                    <p>共 <strong>{{ xmindResult.total_scenarios }}</strong> 个测试场景、<strong>{{ xmindResult.total_cases }}</strong> 条用例</p>
                  </div>
                </div>
                <div class="result-actions">
                  <el-button type="success" size="large" @click="handleDownloadXmind">
                    <el-icon><Download /></el-icon>
                    下载 XMind 文件
                  </el-button>
                  <el-button type="primary" plain size="large" @click="handleSaveCasesToDb">
                    <el-icon><FolderAdd /></el-icon>
                    保存为需求 & 用例
                  </el-button>
                  <el-button plain size="large" @click="xmindResult = null">
                    <el-icon><Close /></el-icon>
                    关闭预览
                  </el-button>
                </div>
              </div>

              <!-- 场景用例预览 -->
              <div class="scenarios-preview">
                <el-collapse v-model="expandedScenarios">
                  <el-collapse-item
                    v-for="(scenario, sIdx) in xmindResult.scenarios"
                    :key="sIdx"
                    :name="sIdx"
                  >
                    <template #title>
                      <div class="scenario-title">
                        <el-icon style="color: #8b5cf6;"><Aim /></el-icon>
                        <span>{{ scenario.scenario }}</span>
                        <el-tag size="small" type="info" style="margin-left: 8px;">{{ scenario.cases.length }} 条用例</el-tag>
                      </div>
                    </template>
                    <el-table :data="scenario.cases" stripe size="small" border style="width: 100%;">
                      <el-table-column label="优先级" width="80" align="center">
                        <template #default="{ row }">
                          <el-tag
                            :type="getPriorityTagType(row.priority)"
                            size="small"
                            effect="dark"
                          >{{ row.priority }}</el-tag>
                        </template>
                      </el-table-column>
                      <el-table-column label="用例名称" prop="case_name" min-width="200" show-overflow-tooltip />
                      <el-table-column label="前置条件" prop="preconditions" min-width="150" show-overflow-tooltip />
                      <el-table-column label="测试步骤" prop="test_steps" min-width="220">
                        <template #default="{ row }">
                          <div class="steps-cell" v-html="formatSteps(row.test_steps)"></div>
                        </template>
                      </el-table-column>
                      <el-table-column label="预期结果" prop="expected_result" min-width="180" show-overflow-tooltip />
                    </el-table>
                  </el-collapse-item>
                </el-collapse>
              </div>
            </div>
          </div>

          <!-- 提取成功提示 -->
          <el-alert
            v-if="extractSuccess"
            title="需求信息提取成功！"
            description="AI 已将提取的需求标题、描述和优先级自动填充到下方表单中。"
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

        <el-form ref="createFormRef" :model="createForm" :rules="createRules" label-width="120px" label-position="top" @submit.prevent="handleSubmit">
          <div class="form-section">
            <h3 class="section-title">基本信息</h3>
            <div class="form-grid">
              <el-form-item label="需求标题" prop="title" class="title-item">
                <el-input v-model="createForm.title" placeholder="请输入需求标题" maxlength="200" show-word-limit size="large" />
              </el-form-item>

              <el-form-item label="所属模块" prop="module_id">
                <el-select v-model="createForm.module_id" placeholder="选择模块" size="large" style="width: 100%;">
                  <el-option v-for="module in modules" :key="module.id" :label="module.name" :value="module.id">
                    <div class="module-option">
                      <span class="module-name">{{ module.name }}</span>
                      <span v-if="module.description" class="module-desc">{{ module.description }}</span>
                    </div>
                  </el-option>
                </el-select>
              </el-form-item>

              <el-form-item label="优先级" prop="priority">
                <el-select v-model="createForm.priority" placeholder="选择优先级" size="large" style="width: 100%;">
                  <el-option v-for="(label, value) in availablePriorityLabels" :key="value" :label="label" :value="parseInt(value)">
                    <div class="priority-option">
                      <el-tag :color="REQUIREMENT_PRIORITY_COLORS[value]" effect="light" size="small">{{ label }}</el-tag>
                      <span class="priority-desc">{{ getPriorityDescription(parseInt(value)) }}</span>
                    </div>
                  </el-option>
                </el-select>
              </el-form-item>

              <el-form-item label="初始状态" prop="status">
                <el-select v-model="createForm.status" placeholder="选择状态" size="large" style="width: 100%;">
                  <el-option v-for="(label, value) in availableStatuses" :key="value" :label="label" :value="value">
                    <div class="status-option">
                      <el-tag :type="getStatusTagType(value)" size="small">{{ label }}</el-tag>
                      <span class="status-desc">{{ getStatusDescription(value) }}</span>
                    </div>
                  </el-option>
                </el-select>
              </el-form-item>
            </div>
          </div>

          <div class="form-section">
            <h3 class="section-title">需求描述</h3>
            <el-form-item prop="description">
              <el-input
                v-model="createForm.description"
                type="textarea"
                :rows="12"
                placeholder="请详细描述功能需求..."
                maxlength="2000"
                show-word-limit
                resize="vertical"
              />
            </el-form-item>
          </div>

          <div class="form-actions">
            <el-button size="large" @click="handleCancel">取消</el-button>
            <el-button type="primary" size="large" @click="handleSubmit" :loading="saving && saveType === 'submit'">提交审核</el-button>
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
  ArrowLeft, MagicStick, Link, Close, Document, VideoCamera,
  FolderOpened, InfoFilled, Paperclip, PictureFilled, Download,
  SuccessFilled, FolderAdd, Aim
} from '@element-plus/icons-vue'
import {
  createRequirement,
  extractRequirementStream,
  docToXmindStream,
  downloadXmindFromCases,
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

// ===== 统一输入 =====
const inputText = ref('')
const inputUrl = ref('')
const showUrlInput = ref(false)
const attachments = ref([])
const isDragOver = ref(false)
const isInputFocused = ref(false)
const textareaRef = ref()
const fileInputRef = ref()
const fileInputAccept = ref('*')
const currentFileType = ref('')

// AI 提取需求状态
const extracting = ref(false)
const extractSuccess = ref(false)
const extractProgress = ref(0)
const extractProgressText = ref('')
const streamMessages = ref([])
const streamRawContent = ref('')

// 一键生成XMind状态
const xmindGenerating = ref(false)
const xmindProgress = ref(0)
const xmindProgressText = ref('')
const xmindResult = ref(null)  // { scenarios, total_cases, total_scenarios, xmind_base64, xmind_filename }
const expandedScenarios = ref([0, 1, 2])  // 默认展开前3个场景

// 创建表单
const createForm = reactive({
  title: '',
  module_id: null,
  description: '',
  priority: REQUIREMENT_PRIORITY.MEDIUM,
  status: REQUIREMENT_STATUS.DRAFT
})

const createRules = {
  title: [
    { required: true, message: '请输入需求标题', trigger: 'blur' },
    { min: 1, max: 200, message: '标题长度在 1 到 200 个字符', trigger: 'blur' }
  ],
  module_id: [{ required: true, message: '请选择所属模块', trigger: 'change' }],
  priority: [{ required: true, message: '请选择优先级', trigger: 'change' }],
  status: [{ required: true, message: '请选择状态', trigger: 'change' }]
}

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
  if (file.size > 20 * 1024 * 1024) {
    ElMessage.warning(`文件 "${file.name}" 超过 20MB 大小限制`)
    return
  }
  if (attachments.value.some(a => a.name === file.name && a.size === file.size)) {
    ElMessage.info(`文件 "${file.name}" 已添加`)
    return
  }
  const category = getFileCategory(file)
  const att = { type: category, file, name: file.name, size: file.size, previewUrl: '' }
  if (category === 'image') {
    const reader = new FileReader()
    reader.onload = (e) => { att.previewUrl = e.target.result }
    reader.readAsDataURL(file)
  }
  attachments.value.push(att)
}

const removeAttachment = (idx) => { attachments.value.splice(idx, 1) }

// ===== 拖拽 & 粘贴 =====
const handleDragOver = () => { isDragOver.value = true }
const handleDragLeave = () => { isDragOver.value = false }
const handleDrop = (event) => {
  isDragOver.value = false
  const files = event.dataTransfer?.files
  if (files) for (const f of files) addFile(f)
}

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
}

// ===== 文件选择 =====
const triggerFileSelect = (type) => {
  currentFileType.value = type
  if (type === 'document') fileInputAccept.value = '.pdf,.docx,.doc,.txt,.md'
  else if (type === 'image') fileInputAccept.value = 'image/png,image/jpeg,image/jpg,image/webp,image/gif'
  else if (type === 'video') fileInputAccept.value = 'video/mp4,video/avi,video/quicktime,video/webm,.mp4,.avi,.mov,.mkv,.webm'
  setTimeout(() => { fileInputRef.value?.click() }, 50)
}

const handleFileInputChange = (event) => {
  const files = event.target.files
  if (files) for (const f of files) addFile(f)
  event.target.value = ''
}

// ===== 构建 FormData =====
const buildFormData = () => {
  const formData = new FormData()
  if (inputText.value.trim()) formData.append('text', inputText.value.trim())
  for (const att of attachments.value) formData.append('files', att.file)
  if (showUrlInput.value && inputUrl.value.trim()) formData.append('url', inputUrl.value.trim())
  return formData
}

// ===== AI 提取需求 =====
const handleExtract = async () => {
  if (!projectId.value || !canExtract.value) return

  extracting.value = true
  extractSuccess.value = false
  extractProgress.value = 5
  extractProgressText.value = '准备数据中...'
  streamMessages.value = []
  streamRawContent.value = ''

  try {
    const formData = buildFormData()
    extractProgress.value = 10
    extractProgressText.value = '上传数据中...'

    const response = await extractRequirementStream(projectId.value, formData)
    if (!response.ok) {
      const errData = await response.json().catch(() => ({}))
      throw new Error(errData.detail || `请求失败: ${response.status}`)
    }

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
              if (result.priority && [1, 2, 3].includes(result.priority)) createForm.priority = result.priority
              extractSuccess.value = true
              ElMessage.success('AI 需求信息提取成功')
            }
          } else if (data.type === 'done') {
            extractProgress.value = 100
            extractProgressText.value = '提取完成'
          } else if (data.type === 'error') {
            ElMessage.error(data.message || 'AI提取失败')
          }
        } catch (e) { /* ignore */ }
      }
    }
  } catch (error) {
    console.error('AI提取失败:', error)
    ElMessage.error(error.message || 'AI 提取失败')
  } finally {
    extracting.value = false
  }
}

// ===== 一键生成XMind =====
const handleGenerateXmind = async () => {
  if (!projectId.value || !canExtract.value) return

  xmindGenerating.value = true
  xmindProgress.value = 5
  xmindProgressText.value = '准备数据中...'
  xmindResult.value = null

  try {
    const formData = buildFormData()
    xmindProgress.value = 8
    xmindProgressText.value = '上传数据中...'

    const response = await docToXmindStream(projectId.value, formData)
    if (!response.ok) {
      const errData = await response.json().catch(() => ({}))
      throw new Error(errData.detail || `请求失败: ${response.status}`)
    }

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
            xmindProgress.value = data.progress || xmindProgress.value
            xmindProgressText.value = data.message || ''
          } else if (data.type === 'chunk') {
            if (data.progress) xmindProgress.value = data.progress
          } else if (data.type === 'result') {
            xmindResult.value = data.data
            // 默认展开所有场景
            expandedScenarios.value = (data.data.scenarios || []).map((_, i) => i)
            ElMessage.success(`用例生成完成！共 ${data.data.total_scenarios} 个场景、${data.data.total_cases} 条用例`)
          } else if (data.type === 'done') {
            xmindProgress.value = 100
            xmindProgressText.value = '生成完成！'
          } else if (data.type === 'error') {
            ElMessage.error(data.message || '生成失败')
          }
        } catch (e) { /* ignore */ }
      }
    }
  } catch (error) {
    console.error('一键生成XMind失败:', error)
    ElMessage.error(error.message || '用例生成失败')
  } finally {
    xmindGenerating.value = false
  }
}

// ===== 下载 XMind =====
const handleDownloadXmind = () => {
  if (!xmindResult.value?.xmind_base64) return
  try {
    const byteCharacters = atob(xmindResult.value.xmind_base64)
    const byteNumbers = new Array(byteCharacters.length)
    for (let i = 0; i < byteCharacters.length; i++) {
      byteNumbers[i] = byteCharacters.charCodeAt(i)
    }
    const byteArray = new Uint8Array(byteNumbers)
    const blob = new Blob([byteArray], { type: 'application/octet-stream' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = xmindResult.value.xmind_filename || '测试用例.xmind'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    ElMessage.success('XMind 文件下载成功')
  } catch (e) {
    console.error('下载失败:', e)
    ElMessage.error('下载失败')
  }
}

// ===== 保存为需求 & 用例 =====
const handleSaveCasesToDb = async () => {
  if (!xmindResult.value?.scenarios) return
  // 将第一个场景的信息作为需求描述
  const scenarios = xmindResult.value.scenarios
  const desc = scenarios.map((s, i) => {
    const caseSummary = s.cases.map((c, j) => `  ${j + 1}. [${c.priority}] ${c.case_name}`).join('\n')
    return `### 场景${i + 1}: ${s.scenario}\n${caseSummary}`
  }).join('\n\n')

  // 自动填充到表单
  if (!createForm.title && inputText.value.trim()) {
    createForm.title = inputText.value.trim().substring(0, 100)
  }
  createForm.description = `## AI生成的测试场景与用例\n\n${desc}`

  ElMessage.success('用例数据已填充到需求表单，请完善后提交')
  // 滚动到表单位置
  setTimeout(() => {
    document.querySelector('.form-section')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }, 300)
}

// ===== 用例显示辅助 =====
const getPriorityTagType = (priority) => {
  const map = { 'P0': 'danger', 'P1': 'warning', 'P2': '', 'P3': 'info' }
  return map[priority] || ''
}

const formatSteps = (steps) => {
  if (!steps) return ''
  return steps.replace(/\n/g, '<br/>')
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
  const typeMap = { draft: '', reviewing: 'warning', approved: 'success', rejected: 'danger', archived: 'info' }
  return typeMap[status] || ''
}

const loadModules = async () => {
  if (!projectId.value) return
  try {
    const response = await getProjectModules(projectId.value)
    modules.value = (response.data && response.data.datas) ? response.data.datas : []
    if (modules.value.length === 1) createForm.module_id = modules.value[0].id
  } catch (error) {
    console.error('加载模块列表失败:', error)
    ElMessage.error('加载模块列表失败')
  }
}

const validateForm = async () => {
  try { await createFormRef.value.validate(); return true } catch { return false }
}

const saveRequirement = async (status) => {
  if (!projectId.value) throw new Error('项目ID不能为空')
  const formData = { ...createForm, status }
  const response = await createRequirement(projectId.value, formData)
  return response.data
}

const handleSubmit = async () => {
  if (!(await validateForm())) return
  if (!createForm.description.trim()) {
    try {
      await ElMessageBox.confirm('您还没有填写需求描述，确定要继续提交吗？', '提示', {
        confirmButtonText: '继续提交', cancelButtonText: '返回编辑', type: 'warning'
      })
    } catch { return }
  }

  saveType.value = 'submit'
  saving.value = true
  try {
    const targetStatus = createForm.status === REQUIREMENT_STATUS.DRAFT ? REQUIREMENT_STATUS.DRAFT : REQUIREMENT_STATUS.REVIEWING
    await saveRequirement(targetStatus)
    ElMessage.success(targetStatus === REQUIREMENT_STATUS.DRAFT ? '需求创建成功' : '需求已提交审核')
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
        confirmButtonText: '确定离开', cancelButtonText: '继续编辑', type: 'warning'
      })
    } catch { return }
  }
  router.push('/function-test/requirement')
}

onMounted(async () => {
  await loadModules()

  // 检查是否有来自「AI优化需求」页面的转入数据
  const transferJson = sessionStorage.getItem('ai_optimize_transfer')
  if (transferJson) {
    try {
      const transfer = JSON.parse(transferJson)
      if (transfer.title) createForm.title = transfer.title
      if (transfer.description) createForm.description = transfer.description
      if (transfer.priority) createForm.priority = transfer.priority
      // 同时填充输入区域以便直接生成XMind
      if (transfer.description) inputText.value = transfer.description
      ElMessage.success('已导入AI优化后的需求内容')
    } catch (e) {
      console.error('解析转入数据失败:', e)
    } finally {
      sessionStorage.removeItem('ai_optimize_transfer')
    }
  }
})
</script>

<style scoped>
.requirement-create-page {
  padding: 24px;
  background: #f8fafc;
  min-height: 100vh;
}

.page-header { margin-bottom: 24px; }
.ai-extract-section { margin-bottom: 24px; }
.ai-extract-section .card-header h2 { display: flex; align-items: center; }
.extract-content { display: flex; flex-direction: column; gap: 20px; }

/* 统一输入区域 */
.unified-input-area {
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.3s;
  background: #fff;
}
.unified-input-area.is-focused { border-color: #8b5cf6; box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.08); }
.unified-input-area.drag-over { border-color: #8b5cf6; border-style: dashed; background: #faf5ff; box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.15); }

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
.input-textarea::placeholder { color: #9ca3af; }

/* 附件区域 */
.attachments-area { border-top: 1px solid #f3f4f6; padding: 12px 16px; background: #fafbfc; }
.attachments-title { display: flex; align-items: center; gap: 6px; font-size: 12px; color: #6b7280; margin-bottom: 10px; }
.attachments-grid { display: flex; flex-wrap: wrap; gap: 10px; }
.attachment-item {
  display: flex; align-items: center; gap: 10px; padding: 8px 12px;
  background: #fff; border: 1px solid #e5e7eb; border-radius: 8px;
  min-width: 180px; max-width: 280px; position: relative; transition: all 0.2s;
}
.attachment-item:hover { border-color: #8b5cf6; box-shadow: 0 2px 8px rgba(139, 92, 246, 0.1); }
.att-preview { width: 40px; height: 40px; border-radius: 6px; overflow: hidden; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.image-preview-thumb { background: #f3f4f6; }
.image-preview-thumb img { width: 100%; height: 100%; object-fit: cover; }
.video-preview-thumb { background: linear-gradient(135deg, #667eea, #764ba2); color: #fff; }
.doc-preview-thumb { background: linear-gradient(135deg, #f093fb, #f5576c); color: #fff; }
.file-type-icon { font-size: 20px; }
.att-info { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px; }
.att-name { font-size: 13px; color: #374151; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.att-size { font-size: 11px; color: #9ca3af; }
.att-remove { position: absolute; top: -6px; right: -6px; width: 20px !important; height: 20px !important; padding: 0 !important; }

/* URL & Toolbar */
.url-input-row { border-top: 1px solid #f3f4f6; padding: 10px 16px; background: #fafbfc; }
.input-toolbar { display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #f3f4f6; padding: 8px 12px; background: #fafbfc; }
.toolbar-left { display: flex; gap: 4px; }
.toolbar-btn { font-size: 13px; color: #6b7280; padding: 6px 10px; border-radius: 6px; }
.toolbar-btn:hover { color: #8b5cf6; background: #f3e8ff; }
.toolbar-btn .el-icon { margin-right: 4px; }
.toolbar-right { display: flex; align-items: center; }
.input-hint { font-size: 12px; color: #9ca3af; display: flex; align-items: center; gap: 4px; }

/* 双按钮 */
.extract-actions { display: flex; align-items: center; gap: 16px; flex-wrap: wrap; }

/* 流式进度 - AI提取 */
.stream-progress-area {
  background: #faf5ff; border: 1px solid #e9d5ff; border-radius: 8px; padding: 16px;
}
.progress-bar-container { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
.progress-bar-container .el-progress { flex: 1; }
.progress-text { font-size: 13px; color: #8b5cf6; white-space: nowrap; min-width: 120px; }
.progress-text.green { color: #67c23a; }
.stream-content { max-height: 200px; overflow-y: auto; }
.stream-label { font-size: 12px; color: #8b5cf6; font-weight: 600; margin-bottom: 6px; }
.stream-text { font-size: 13px; color: #4b5563; line-height: 1.6; white-space: pre-wrap; word-break: break-word; font-family: 'SF Mono', monospace; background: #fff; padding: 10px; border-radius: 6px; max-height: 160px; overflow-y: auto; }

/* XMind 生成结果 */
.xmind-progress-area {
  background: linear-gradient(135deg, #f0fdf4, #ecfdf5);
  border: 1px solid #bbf7d0;
  border-radius: 12px;
  padding: 20px;
}

.xmind-result {
  margin-top: 16px;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
  gap: 16px;
  flex-wrap: wrap;
}

.result-summary {
  display: flex;
  align-items: center;
  gap: 12px;
}

.result-summary h3 {
  margin: 0;
  color: #166534;
  font-size: 18px;
}

.result-summary p {
  margin: 4px 0 0;
  color: #4b5563;
  font-size: 14px;
}

.result-summary strong {
  color: #166534;
  font-size: 16px;
}

.result-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

/* 场景预览 */
.scenarios-preview {
  background: #fff;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  overflow: hidden;
}

.scenario-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
  color: #1f2937;
}

.steps-cell {
  font-size: 12px;
  line-height: 1.6;
  color: #4b5563;
  max-height: 120px;
  overflow-y: auto;
}

/* 其余表单样式 */
.header-content {
  display: flex; justify-content: space-between; align-items: center;
  background: white; padding: 20px 24px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}
.breadcrumb-section { flex: 1; }
.action-section { display: flex; gap: 12px; }
.page-content { background: white; border-radius: 8px; overflow: hidden; }
.card-header { border-bottom: 1px solid #e5e7eb; padding-bottom: 16px; }
.title-section h2 { color: #1f2937; margin: 0 0 8px 0; font-size: 20px; font-weight: 600; }
.subtitle { color: #6b7280; margin: 0; font-size: 14px; }
.form-section { margin-bottom: 32px; }
.section-title { color: #1f2937; font-size: 16px; font-weight: 600; margin: 0 0 20px 0; padding-bottom: 8px; border-bottom: 2px solid #8b5cf6; }
.form-grid { display: grid; grid-template-columns: 2fr 1fr 1fr 1fr; gap: 24px; }
.title-item { grid-column: 1 / -1; }
.module-option, .priority-option, .status-option { display: flex; align-items: center; justify-content: space-between; width: 100%; }
.module-name { font-weight: 500; }
.module-desc, .priority-desc, .status-desc { font-size: 12px; color: #6b7280; margin-left: 8px; }
.form-actions { display: flex; justify-content: flex-end; gap: 16px; padding-top: 24px; border-top: 1px solid #e5e7eb; }

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
  .result-header { flex-direction: column; }
  .result-actions { width: 100%; }
}

:deep(.el-textarea__inner) { font-family: inherit; line-height: 1.6; }
:deep(.el-form-item__label) { font-weight: 500; color: #374151; }
:deep(.el-input__inner) { border-radius: 6px; }
:deep(.el-select .el-input__inner) { border-radius: 6px; }
:deep(.el-collapse-item__header) { font-size: 15px; padding: 12px 16px; }
:deep(.el-collapse-item__content) { padding: 0 16px 16px; }
</style>
