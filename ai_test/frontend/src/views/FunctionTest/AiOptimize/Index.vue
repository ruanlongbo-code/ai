<template>
  <div class="ai-optimize-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <h2>
            <el-icon style="color: #8b5cf6; margin-right: 8px;"><MagicStick /></el-icon>
            AI 优化需求
          </h2>
          <p class="subtitle">导入 MD 需求文档或输入文本，AI 自动优化为规范需求，并可一键生成 XMind 测试用例</p>
        </div>
      </div>
    </div>

    <!-- 功能区域 -->
    <div class="main-content-area">
      <el-row :gutter="24">
        <!-- 左侧：输入区域 -->
        <el-col :span="12">
          <el-card class="input-card">
            <template #header>
              <div class="card-header">
                <span class="card-title">📝 输入内容</span>
                <el-radio-group v-model="inputMode" size="small">
                  <el-radio-button value="text">自由输入</el-radio-button>
                  <el-radio-button value="file">导入文档</el-radio-button>
                  <el-radio-button value="requirement">选择已有需求</el-radio-button>
                </el-radio-group>
              </div>
            </template>

            <!-- 自由输入模式 -->
            <div v-if="inputMode === 'text'">
              <el-alert type="info" :closable="false" show-icon style="margin-bottom: 16px;">
                <template #title>
                  <span>粘贴任意需求描述、产品文档、用户故事、会议纪要等文本内容，AI 将自动优化为规范的需求文档格式。</span>
                </template>
              </el-alert>
              <el-input
                v-model="inputText"
                type="textarea"
                :rows="14"
                placeholder="请输入需要优化的需求内容...

示例：
• 产品需求文档（PRD）内容
• 用户故事描述
• 会议纪要中的功能描述
• 简单的需求想法

AI 会帮你整理为标准化的需求文档，包含功能描述、验收标准、风险提示等。"
                maxlength="10000"
                show-word-limit
                resize="vertical"
              />
              <el-input
                v-model="inputTitle"
                placeholder="需求标题（可选，AI会自动生成）"
                style="margin-top: 12px;"
                size="large"
                clearable
              >
                <template #prepend>标题</template>
              </el-input>
            </div>

            <!-- 导入文档模式 -->
            <div v-else-if="inputMode === 'file'">
              <el-alert type="info" :closable="false" show-icon style="margin-bottom: 16px;">
                <template #title>
                  <span>上传 MD、TXT、PDF、DOCX 格式的需求文档，AI 将自动解析、总结并优化为规范需求。</span>
                </template>
              </el-alert>

              <el-upload
                ref="uploadRef"
                :auto-upload="false"
                :limit="1"
                :on-change="handleFileChange"
                :on-remove="handleFileRemove"
                accept=".md,.txt,.pdf,.docx,.doc"
                drag
                class="file-upload-area"
              >
                <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
                <div class="el-upload__text">
                  拖拽需求文档到这里，或<em>点击上传</em>
                </div>
                <template #tip>
                  <div class="el-upload__tip">
                    支持 .md、.txt、.pdf、.docx 格式，最大 20MB
                  </div>
                </template>
              </el-upload>

              <!-- 文档预览 -->
              <div v-if="uploadedFile" class="file-preview">
                <div class="file-info">
                  <el-icon style="color: #8b5cf6; font-size: 20px;"><Document /></el-icon>
                  <div>
                    <div class="file-name">{{ uploadedFile.name }}</div>
                    <div class="file-size">{{ formatFileSize(uploadedFile.size) }}</div>
                  </div>
                </div>
              </div>

              <!-- 补充文本 -->
              <el-input
                v-model="supplementText"
                type="textarea"
                :rows="4"
                placeholder="（可选）补充说明文字，会与文档内容一起分析..."
                maxlength="3000"
                show-word-limit
                resize="vertical"
                style="margin-top: 12px;"
              />
              <el-input
                v-model="inputTitle"
                placeholder="需求标题（可选，AI会自动生成）"
                style="margin-top: 12px;"
                size="large"
                clearable
              >
                <template #prepend>标题</template>
              </el-input>
            </div>

            <!-- 选择已有需求模式 -->
            <div v-else>
              <el-alert type="info" :closable="false" show-icon style="margin-bottom: 16px;">
                <template #title>
                  <span>选择项目中已有的需求，AI 将对其进行智能优化和规范化处理。</span>
                </template>
              </el-alert>
              <el-select
                v-model="selectedRequirementId"
                placeholder="请选择需要优化的需求"
                size="large"
                style="width: 100%; margin-bottom: 16px;"
                filterable
                @change="handleRequirementSelect"
              >
                <el-option
                  v-for="req in requirementList"
                  :key="req.id"
                  :label="`[${req.id}] ${req.title}`"
                  :value="req.id"
                >
                  <div class="req-option">
                    <span class="req-title">{{ req.title }}</span>
                    <el-tag size="small" :type="getPriorityType(req.priority)">
                      {{ getPriorityLabel(req.priority) }}
                    </el-tag>
                  </div>
                </el-option>
              </el-select>
              
              <div v-if="selectedRequirement" class="requirement-preview">
                <div class="preview-title">
                  <strong>{{ selectedRequirement.title }}</strong>
                </div>
                <div class="preview-desc">
                  {{ selectedRequirement.description || '暂无描述' }}
                </div>
              </div>
              <el-empty v-else description="请选择需要优化的需求" :image-size="80" />
            </div>

            <!-- 操作按钮 -->
            <div class="action-buttons">
              <el-button
                type="primary"
                size="large"
                @click="handleOptimize"
                :loading="optimizing"
                :disabled="!canOptimize || xmindGenerating"
              >
                <el-icon v-if="!optimizing"><MagicStick /></el-icon>
                {{ optimizing ? 'AI 正在优化中...' : 'AI 智能优化' }}
              </el-button>
              <el-button size="large" @click="handleReset" :disabled="optimizing || xmindGenerating">
                清空重置
              </el-button>
            </div>
          </el-card>
        </el-col>

        <!-- 右侧：优化结果 -->
        <el-col :span="12">
          <el-card class="result-card">
            <template #header>
              <div class="card-header">
                <span class="card-title">✨ 优化结果</span>
                <div v-if="optimizeResult" class="result-header-actions">
                  <el-button type="success" size="small" @click="handleGenerateXmindFromResult" :loading="xmindGenerating">
                    <el-icon><Download /></el-icon>
                    一键生成XMind用例
                  </el-button>
                  <el-button type="primary" size="small" @click="handleTransferToGenerate">
                    <el-icon><Right /></el-icon>
                    导入AI生成用例
                  </el-button>
                  <el-button type="primary" plain size="small" @click="handleSaveAsRequirement" :loading="saving">
                    <el-icon><DocumentAdd /></el-icon>
                    保存为需求
                  </el-button>
                  <el-button v-if="inputMode === 'requirement' && selectedRequirementId" type="warning" size="small" plain @click="handleApplyToRequirement" :loading="applying">
                    <el-icon><Check /></el-icon>
                    应用到原需求
                  </el-button>
                  <el-button size="small" plain @click="handleCopyResult">
                    <el-icon><CopyDocument /></el-icon>
                    复制
                  </el-button>
                </div>
              </div>
            </template>

            <!-- 优化中 -->
            <div v-if="optimizing" class="optimizing-status">
              <div class="loading-animation">
                <el-icon class="is-loading" :size="40"><Loading /></el-icon>
              </div>
              <p class="loading-text">AI 正在分析并优化需求，请稍候...</p>
              <div class="stream-output" v-if="streamText">
                <pre>{{ streamText }}</pre>
              </div>
            </div>

            <!-- 优化结果展示 -->
            <div v-else-if="optimizeResult" class="result-display">
              <!-- 需求总结（新增） -->
              <div v-if="optimizeResult.requirement_summary" class="summary-section">
                <div class="summary-header">
                  <el-icon style="color: #8b5cf6;"><InfoFilled /></el-icon>
                  <span>需求总结</span>
                </div>
                <div class="summary-content">{{ optimizeResult.requirement_summary }}</div>
              </div>

              <!-- 优化摘要 -->
              <el-alert :title="optimizeResult.optimization_summary || '优化完成'" type="success" :closable="false" show-icon style="margin-bottom: 16px;" />

              <!-- 测试点提取（新增） -->
              <div v-if="optimizeResult.test_points && optimizeResult.test_points.length" class="test-points-section">
                <div class="test-points-header">
                  <el-icon style="color: #e6a23c;"><Aim /></el-icon>
                  <span>AI 提取的测试点（{{ optimizeResult.test_points.length }}个）</span>
                </div>
                <div class="test-points-list">
                  <el-tag
                    v-for="(tp, idx) in optimizeResult.test_points"
                    :key="idx"
                    type="warning"
                    effect="plain"
                    size="default"
                    style="margin: 4px;"
                  >
                    🎯 {{ tp }}
                  </el-tag>
                </div>
              </div>
              
              <el-tabs type="border-card">
                <!-- 优化后标题 -->
                <el-tab-pane label="📋 标题">
                  <div class="result-section">
                    <div v-if="inputMode === 'requirement' && selectedRequirement" class="compare-item original">
                      <label>原标题</label>
                      <div class="text-box">{{ selectedRequirement.title }}</div>
                    </div>
                    <div class="compare-item optimized">
                      <label>{{ inputMode === 'requirement' ? '优化后标题' : 'AI 生成标题' }}</label>
                      <div class="text-box highlight">{{ optimizeResult.optimized_title }}</div>
                    </div>
                  </div>
                </el-tab-pane>

                <!-- 优化后描述 -->
                <el-tab-pane label="📄 描述">
                  <div class="result-section">
                    <div v-if="inputMode === 'requirement' && selectedRequirement" class="compare-item original">
                      <label>原描述</label>
                      <div class="text-box desc-box">{{ selectedRequirement.description || '无描述' }}</div>
                    </div>
                    <div class="compare-item optimized">
                      <label>{{ inputMode === 'requirement' ? '优化后描述' : 'AI 规范化描述' }}</label>
                      <div class="text-box desc-box highlight" v-html="formatMarkdown(optimizeResult.optimized_description)"></div>
                    </div>
                  </div>
                </el-tab-pane>

                <!-- 验收标准 -->
                <el-tab-pane label="✅ 验收标准">
                  <div class="result-section">
                    <el-timeline v-if="optimizeResult.acceptance_criteria && optimizeResult.acceptance_criteria.length">
                      <el-timeline-item
                        v-for="(criterion, idx) in optimizeResult.acceptance_criteria"
                        :key="idx"
                        :timestamp="`验收标准 ${idx + 1}`"
                        placement="top"
                        color="#8b5cf6"
                      >
                        {{ criterion }}
                      </el-timeline-item>
                    </el-timeline>
                    <el-empty v-else description="暂无验收标准" :image-size="60" />
                  </div>
                </el-tab-pane>

                <!-- 风险提示 -->
                <el-tab-pane label="⚠️ 风险">
                  <div class="result-section">
                    <div v-if="optimizeResult.risks && optimizeResult.risks.length" class="risk-list">
                      <el-alert
                        v-for="(risk, idx) in optimizeResult.risks"
                        :key="idx"
                        :title="risk"
                        type="warning"
                        :closable="false"
                        show-icon
                        style="margin-bottom: 8px;"
                      />
                    </div>
                    <el-empty v-else description="暂未发现明显风险" :image-size="60" />
                  </div>
                </el-tab-pane>
              </el-tabs>
            </div>

            <!-- 空状态 -->
            <div v-else class="empty-result">
              <el-empty description="输入需求内容后，点击「AI 智能优化」查看结果">
                <template #image>
                  <el-icon :size="60" style="color: #d9d9d9;"><MagicStick /></el-icon>
                </template>
              </el-empty>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- XMind 生成结果区域 -->
      <div v-if="xmindGenerating || xmindResult" class="xmind-section">
        <el-card>
          <template #header>
            <div class="card-header">
              <span class="card-title">📊 XMind 测试用例生成</span>
              <div v-if="xmindResult" class="xmind-header-actions">
                <el-button type="success" @click="handleDownloadXmind">
                  <el-icon><Download /></el-icon>
                  下载 XMind 文件
                </el-button>
                <el-button type="primary" plain @click="handleSaveXmindCases">
                  <el-icon><FolderAdd /></el-icon>
                  保存为需求 & 用例
                </el-button>
                <el-button plain @click="xmindResult = null">
                  <el-icon><Close /></el-icon>
                  关闭
                </el-button>
              </div>
            </div>
          </template>

          <!-- 进度 -->
          <div v-if="xmindGenerating" class="xmind-progress">
            <el-progress :percentage="xmindProgress" :stroke-width="8" :show-text="false" color="#67c23a" />
            <span class="progress-text">{{ xmindProgressText }}</span>
          </div>

          <!-- 结果预览 -->
          <div v-if="xmindResult" class="xmind-preview">
            <div class="result-summary-bar">
              <el-icon style="color: #67c23a; font-size: 24px;"><SuccessFilled /></el-icon>
              <div>
                <strong>用例生成完成！</strong>
                <span>共 <strong>{{ xmindResult.total_scenarios }}</strong> 个测试点、<strong>{{ xmindResult.total_cases }}</strong> 条用例</span>
              </div>
            </div>

            <div class="xmind-structure-hint">
              <el-tag type="info" size="small">XMind结构</el-tag>
              <span>需求标题 → 🎯 测试点 → 测试标题 → [前置条件 / 测试步骤 / 预期结果]</span>
            </div>

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
                      <el-tag :type="getPriorityTagType(row.priority)" size="small" effect="dark">{{ row.priority }}</el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column label="用例名称" prop="case_name" min-width="180" show-overflow-tooltip />
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
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  MagicStick, Loading, Check, CopyDocument, DocumentAdd,
  UploadFilled, Document, Download, Right, Close,
  InfoFilled, Aim, SuccessFilled, FolderAdd
} from '@element-plus/icons-vue'
import {
  getRequirementsList,
  createRequirement,
  applyAiOptimization,
  aiOptimizeDocStream,
  docToXmindStream,
  REQUIREMENT_PRIORITY_LABELS,
  REQUIREMENT_STATUS,
  REQUIREMENT_PRIORITY
} from '@/api/functional_test'
import { useProjectStore } from '@/stores'

const router = useRouter()
const projectStore = useProjectStore()

// 基础数据
const inputMode = ref('file')
const inputText = ref('')
const inputTitle = ref('')
const supplementText = ref('')
const uploadedFile = ref(null)
const uploadRef = ref()
const requirementList = ref([])
const selectedRequirementId = ref(null)
const selectedRequirement = ref(null)

// 优化相关状态
const optimizing = ref(false)
const optimizeResult = ref(null)
const streamText = ref('')
const saving = ref(false)
const applying = ref(false)

// XMind 生成状态
const xmindGenerating = ref(false)
const xmindProgress = ref(0)
const xmindProgressText = ref('')
const xmindResult = ref(null)
const expandedScenarios = ref([0, 1, 2])

const projectId = computed(() => projectStore.currentProject?.id)

const canOptimize = computed(() => {
  if (inputMode.value === 'text') {
    return inputText.value.trim().length > 0
  } else if (inputMode.value === 'file') {
    return !!uploadedFile.value || supplementText.value.trim().length > 0
  } else {
    return !!selectedRequirementId.value
  }
})

// 工具方法
const getPriorityLabel = (priority) => REQUIREMENT_PRIORITY_LABELS[priority] || '未知'
const getPriorityType = (priority) => ({ 1: 'info', 2: '', 3: 'warning', 4: 'danger' }[priority] || '')
const getPriorityTagType = (p) => ({ 'P0': 'danger', 'P1': 'warning', 'P2': '', 'P3': 'info' }[p] || '')
const formatSteps = (steps) => steps ? steps.replace(/\n/g, '<br/>') : ''
const formatFileSize = (bytes) => {
  if (!bytes) return '0 B'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

const formatMarkdown = (text) => {
  if (!text) return ''
  return text
    .replace(/\n/g, '<br>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/^### (.*)/gm, '<h4>$1</h4>')
    .replace(/^## (.*)/gm, '<h3>$1</h3>')
    .replace(/^# (.*)/gm, '<h2>$1</h2>')
    .replace(/^- (.*)/gm, '<li>$1</li>')
}

// 文件上传处理
const handleFileChange = (file) => {
  uploadedFile.value = file.raw || file
}
const handleFileRemove = () => {
  uploadedFile.value = null
}

// 加载需求列表
const loadRequirements = async () => {
  if (!projectId.value) return
  try {
    const response = await getRequirementsList(projectId.value, { page: 1, page_size: 200 })
    requirementList.value = response.data?.requirements || response.data?.datas || response.data?.items || []
  } catch (error) {
    console.error('加载需求列表失败:', error)
  }
}

const handleRequirementSelect = (id) => {
  selectedRequirement.value = requirementList.value.find(r => r.id === id) || null
}

// ===== 执行 AI 优化 =====
const handleOptimize = async () => {
  if (!projectId.value) {
    ElMessage.error('请先选择项目')
    return
  }

  optimizing.value = true
  streamText.value = ''
  optimizeResult.value = null

  try {
    const baseUrl = import.meta.env.VITE_API_BASE_URL || ''
    const token = localStorage.getItem('token')

    let response

    if (inputMode.value === 'requirement' && selectedRequirementId.value) {
      // 对已有需求进行优化（使用原有接口）
      const url = `${baseUrl}/functional_test/${projectId.value}/requirements/${selectedRequirementId.value}/ai_optimize`
      response = await fetch(url, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' }
      })
    } else {
      // 使用新的文档优化接口
      const formData = new FormData()
      if (inputMode.value === 'file') {
        if (uploadedFile.value) {
          formData.append('file', uploadedFile.value)
        }
        if (supplementText.value.trim()) {
          formData.append('text', supplementText.value.trim())
        }
      } else {
        formData.append('text', inputText.value.trim())
      }
      if (inputTitle.value.trim()) {
        formData.append('title', inputTitle.value.trim())
      }

      response = await aiOptimizeDocStream(projectId.value, formData)
    }

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.detail || `HTTP ${response.status}`)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { value, done } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))
            if (data.type === 'chunk') {
              streamText.value += data.content
            } else if (data.type === 'result') {
              optimizeResult.value = data.data
            } else if (data.type === 'error') {
              ElMessage.error(data.message || 'AI优化失败')
            }
          } catch (e) { /* ignore */ }
        }
      }
    }

    if (optimizeResult.value) {
      ElMessage.success('AI 优化完成')
    }
  } catch (error) {
    console.error('AI优化失败:', error)
    ElMessage.error(error.message || 'AI优化失败，请稍后重试')
  } finally {
    optimizing.value = false
  }
}

// ===== 一键生成 XMind（从优化结果） =====
const handleGenerateXmindFromResult = async () => {
  if (!optimizeResult.value || !projectId.value) return

  xmindGenerating.value = true
  xmindProgress.value = 5
  xmindProgressText.value = '准备数据中...'
  xmindResult.value = null

  try {
    // 将优化后的需求内容作为输入，调用 doc_to_xmind_stream
    const formData = new FormData()
    const optimizedContent = `# ${optimizeResult.value.optimized_title}\n\n${optimizeResult.value.optimized_description}` +
      (optimizeResult.value.acceptance_criteria?.length
        ? '\n\n## 验收标准\n' + optimizeResult.value.acceptance_criteria.map((c, i) => `${i + 1}. ${c}`).join('\n')
        : '')
    formData.append('text', optimizedContent)

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
          } else if (data.type === 'chunk' && data.progress) {
            xmindProgress.value = data.progress
          } else if (data.type === 'result') {
            xmindResult.value = data.data
            expandedScenarios.value = (data.data.scenarios || []).map((_, i) => i)
            ElMessage.success(`用例生成完成！共 ${data.data.total_scenarios} 个测试点、${data.data.total_cases} 条用例`)
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
    console.error('XMind生成失败:', error)
    ElMessage.error(error.message || '用例生成失败')
  } finally {
    xmindGenerating.value = false
  }
}

// ===== 导入到 AI 生成用例 =====
const handleTransferToGenerate = () => {
  if (!optimizeResult.value) return

  // 将优化后的内容存储到 sessionStorage，供新建需求页面读取
  const transferData = {
    title: optimizeResult.value.optimized_title,
    description: optimizeResult.value.optimized_description +
      (optimizeResult.value.acceptance_criteria?.length
        ? '\n\n## 验收标准\n' + optimizeResult.value.acceptance_criteria.map((c, i) => `${i + 1}. ${c}`).join('\n')
        : ''),
    priority: 2,
    test_points: optimizeResult.value.test_points || [],
    source: 'ai_optimize'
  }
  sessionStorage.setItem('ai_optimize_transfer', JSON.stringify(transferData))

  // 跳转到新建需求页面
  router.push('/function-test/requirement/create')
  ElMessage.success('优化后的需求已导入，请在新建需求页面继续操作')
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

// ===== 保存 XMind 用例为需求 =====
const handleSaveXmindCases = async () => {
  if (!xmindResult.value?.scenarios || !projectId.value) return

  const scenarios = xmindResult.value.scenarios
  const desc = scenarios.map((s, i) => {
    const caseSummary = s.cases.map((c, j) => `  ${j + 1}. [${c.priority}] ${c.case_name}`).join('\n')
    return `### 场景${i + 1}: ${s.scenario}\n${caseSummary}`
  }).join('\n\n')

  const transferData = {
    title: optimizeResult.value?.optimized_title || '需求文档',
    description: `## AI生成的测试场景与用例\n\n${desc}`,
    priority: 2,
    source: 'xmind_generate'
  }
  sessionStorage.setItem('ai_optimize_transfer', JSON.stringify(transferData))
  router.push('/function-test/requirement/create')
  ElMessage.success('用例数据已导入新建需求页面')
}

// ===== 保存为新需求 =====
const handleSaveAsRequirement = async () => {
  if (!optimizeResult.value || !projectId.value) return

  try {
    await ElMessageBox.confirm(
      '将优化后的需求保存到需求管理中，确认继续？',
      '保存为需求',
      { confirmButtonText: '确认保存', cancelButtonText: '取消', type: 'info' }
    )

    saving.value = true
    const moduleId = requirementList.value[0]?.module_id || null

    const reqData = {
      title: optimizeResult.value.optimized_title,
      description: optimizeResult.value.optimized_description +
        (optimizeResult.value.acceptance_criteria?.length
          ? '\n\n## 验收标准\n' + optimizeResult.value.acceptance_criteria.map((c, i) => `${i + 1}. ${c}`).join('\n')
          : ''),
      priority: REQUIREMENT_PRIORITY.MEDIUM,
      status: REQUIREMENT_STATUS.DRAFT,
      module_id: moduleId
    }

    await createRequirement(projectId.value, reqData)
    ElMessage.success('需求已保存成功')
    await loadRequirements()
  } catch (e) {
    if (e !== 'cancel') {
      console.error('保存需求失败:', e)
      ElMessage.error('保存需求失败')
    }
  } finally {
    saving.value = false
  }
}

// ===== 应用到原需求 =====
const handleApplyToRequirement = async () => {
  if (!optimizeResult.value || !selectedRequirementId.value || !projectId.value) return

  try {
    await ElMessageBox.confirm(
      '将优化结果应用到原需求，将覆盖原有标题和描述，确认继续？',
      '应用优化',
      { confirmButtonText: '确认应用', cancelButtonText: '取消', type: 'warning' }
    )

    applying.value = true
    await applyAiOptimization(projectId.value, selectedRequirementId.value, optimizeResult.value)
    ElMessage.success('优化结果已应用到原需求')
    await loadRequirements()
    selectedRequirement.value = {
      ...selectedRequirement.value,
      title: optimizeResult.value.optimized_title,
      description: optimizeResult.value.optimized_description
    }
  } catch (e) {
    if (e !== 'cancel') {
      console.error('应用优化结果失败:', e)
      ElMessage.error('应用优化结果失败')
    }
  } finally {
    applying.value = false
  }
}

// ===== 复制结果 =====
const handleCopyResult = async () => {
  if (!optimizeResult.value) return
  
  const text = `# ${optimizeResult.value.optimized_title}\n\n` +
    (optimizeResult.value.requirement_summary ? `## 需求总结\n${optimizeResult.value.requirement_summary}\n\n` : '') +
    optimizeResult.value.optimized_description +
    (optimizeResult.value.acceptance_criteria?.length
      ? '\n\n## 验收标准\n' + optimizeResult.value.acceptance_criteria.map((c, i) => `${i + 1}. ${c}`).join('\n')
      : '') +
    (optimizeResult.value.risks?.length
      ? '\n\n## 风险提示\n' + optimizeResult.value.risks.map((r, i) => `${i + 1}. ${r}`).join('\n')
      : '') +
    (optimizeResult.value.test_points?.length
      ? '\n\n## 测试点\n' + optimizeResult.value.test_points.map((t, i) => `${i + 1}. ${t}`).join('\n')
      : '')

  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success('已复制到剪贴板')
  } catch {
    ElMessage.error('复制失败')
  }
}

// 清空重置
const handleReset = () => {
  inputText.value = ''
  inputTitle.value = ''
  supplementText.value = ''
  uploadedFile.value = null
  selectedRequirementId.value = null
  selectedRequirement.value = null
  optimizeResult.value = null
  streamText.value = ''
  xmindResult.value = null
  if (uploadRef.value) {
    uploadRef.value.clearFiles()
  }
}

onMounted(() => {
  loadRequirements()
})
</script>

<style scoped>
.ai-optimize-page {
  padding: 24px;
  background: #f8fafc;
  min-height: 100%;
}

.page-header {
  margin-bottom: 24px;
}

.header-content {
  background: white;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.title-section h2 {
  display: flex;
  align-items: center;
  color: #1f2937;
  margin: 0 0 8px 0;
  font-size: 22px;
  font-weight: 600;
}

.subtitle {
  color: #6b7280;
  margin: 0;
  font-size: 14px;
}

.main-content-area {
  min-height: calc(100vh - 280px);
}

.input-card,
.result-card {
  height: 100%;
  min-height: 600px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.result-header-actions {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

/* 文件上传 */
.file-upload-area {
  margin-bottom: 12px;
}

.file-preview {
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 8px;
  padding: 12px;
  margin-top: 12px;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.file-name {
  font-size: 14px;
  font-weight: 500;
  color: #1f2937;
}

.file-size {
  font-size: 12px;
  color: #6b7280;
}

.req-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.req-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-right: 12px;
}

.requirement-preview {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 16px;
  max-height: 300px;
  overflow-y: auto;
}

.preview-title {
  font-size: 15px;
  color: #1f2937;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e5e7eb;
}

.preview-desc {
  font-size: 13px;
  color: #6b7280;
  white-space: pre-wrap;
  line-height: 1.8;
}

.action-buttons {
  display: flex;
  gap: 12px;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}

/* 需求总结 */
.summary-section {
  background: linear-gradient(135deg, #ede9fe, #fae8ff);
  border: 1px solid #d8b4fe;
  border-radius: 10px;
  padding: 16px;
  margin-bottom: 16px;
}

.summary-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #6d28d9;
  margin-bottom: 8px;
}

.summary-content {
  font-size: 14px;
  line-height: 1.8;
  color: #4c1d95;
}

/* 测试点 */
.test-points-section {
  background: #fffbeb;
  border: 1px solid #fde68a;
  border-radius: 10px;
  padding: 14px;
  margin-bottom: 16px;
}

.test-points-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #b45309;
  margin-bottom: 10px;
}

.test-points-list {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

/* 优化结果样式 */
.optimizing-status {
  text-align: center;
  padding: 40px 0;
}

.loading-animation {
  color: #8b5cf6;
  margin-bottom: 16px;
}

.loading-text {
  color: #6b7280;
  font-size: 14px;
  margin-bottom: 20px;
}

.stream-output {
  background: #1a1a2e;
  color: #a5f3fc;
  border-radius: 8px;
  padding: 16px;
  max-height: 400px;
  overflow-y: auto;
  text-align: left;
}

.stream-output pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 13px;
  line-height: 1.6;
}

.result-display {
  padding: 0;
}

.result-section {
  padding: 8px 0;
}

.compare-item {
  margin-bottom: 16px;
}

.compare-item label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: #6b7280;
  margin-bottom: 6px;
}

.compare-item.original .text-box {
  background: #fef3c7;
  border-color: #fcd34d;
}

.compare-item.optimized .text-box.highlight {
  background: #ecfdf5;
  border-color: #6ee7b7;
}

.text-box {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 12px;
  font-size: 14px;
  line-height: 1.6;
  color: #1f2937;
}

.desc-box {
  max-height: 300px;
  overflow-y: auto;
  white-space: pre-wrap;
}

.empty-result {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 400px;
}

/* XMind 区域 */
.xmind-section {
  margin-top: 24px;
}

.xmind-header-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.xmind-progress {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.xmind-progress .el-progress {
  flex: 1;
}

.progress-text {
  font-size: 13px;
  color: #67c23a;
  white-space: nowrap;
  min-width: 120px;
}

.result-summary-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: #f0fdf4;
  border-radius: 8px;
  margin-bottom: 12px;
}

.result-summary-bar strong {
  color: #166534;
}

.xmind-structure-hint {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 13px;
  color: #64748b;
  margin-bottom: 16px;
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

/* 滚动条 */
.stream-output::-webkit-scrollbar,
.desc-box::-webkit-scrollbar,
.requirement-preview::-webkit-scrollbar {
  width: 5px;
}

.stream-output::-webkit-scrollbar-thumb,
.desc-box::-webkit-scrollbar-thumb,
.requirement-preview::-webkit-scrollbar-thumb {
  background: rgba(139, 92, 246, 0.3);
  border-radius: 3px;
}

/* Element Plus 覆盖 */
:deep(.el-tabs--border-card) {
  border-radius: 8px;
  overflow: hidden;
}

:deep(.el-timeline-item__timestamp) {
  color: #8b5cf6 !important;
  font-weight: 600;
}

:deep(.el-upload-dragger) {
  border: 2px dashed #d9d9d9;
  border-radius: 8px;
  padding: 30px 20px;
  transition: all 0.3s;
}

:deep(.el-upload-dragger:hover) {
  border-color: #8b5cf6;
}

:deep(.el-collapse-item__header) {
  font-size: 15px;
  padding: 12px 16px;
}

:deep(.el-collapse-item__content) {
  padding: 0 16px 16px;
}
</style>
