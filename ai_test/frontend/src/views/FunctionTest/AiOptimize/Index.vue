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
          <p class="subtitle">通过 AI 智能分析，将需求描述、文档内容优化为规范的需求文档，提升需求质量与可测试性</p>
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
                  <el-radio-button value="requirement">选择已有需求</el-radio-button>
                </el-radio-group>
              </div>
            </template>

            <!-- 自由输入模式 -->
            <div v-if="inputMode === 'text'">
              <el-alert
                type="info"
                :closable="false"
                show-icon
                style="margin-bottom: 16px;"
              >
                <template #title>
                  <span>粘贴任意需求描述、产品文档、用户故事、会议纪要等文本内容，AI 将自动优化为规范的需求文档格式。</span>
                </template>
              </el-alert>
              <el-input
                v-model="inputText"
                type="textarea"
                :rows="16"
                placeholder="请输入需要优化的需求内容...

示例：
• 产品需求文档（PRD）内容
• 用户故事描述
• 会议纪要中的功能描述
• 简单的需求想法
• 其他任何需要规范化的需求文本

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

            <!-- 选择已有需求模式 -->
            <div v-else>
              <el-alert
                type="info"
                :closable="false"
                show-icon
                style="margin-bottom: 16px;"
              >
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
              
              <!-- 选中的需求预览 -->
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
                :disabled="!canOptimize"
              >
                <el-icon v-if="!optimizing"><MagicStick /></el-icon>
                {{ optimizing ? 'AI 正在优化中...' : 'AI 智能优化' }}
              </el-button>
              <el-button size="large" @click="handleReset" :disabled="optimizing">
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
                <div v-if="optimizeResult">
                  <el-button type="primary" size="small" @click="handleSaveAsRequirement" :loading="saving">
                    <el-icon><DocumentAdd /></el-icon>
                    保存为需求
                  </el-button>
                  <el-button v-if="inputMode === 'requirement' && selectedRequirementId" type="success" size="small" @click="handleApplyToRequirement" :loading="applying">
                    <el-icon><Check /></el-icon>
                    应用到原需求
                  </el-button>
                  <el-button size="small" @click="handleCopyResult">
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
              <!-- 优化摘要 -->
              <el-alert :title="optimizeResult.optimization_summary || '优化完成'" type="success" :closable="false" show-icon style="margin-bottom: 20px;" />
              
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
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { MagicStick, Loading, Check, CopyDocument, DocumentAdd } from '@element-plus/icons-vue'
import {
  getRequirementsList,
  createRequirement,
  applyAiOptimization,
  REQUIREMENT_PRIORITY_LABELS,
  REQUIREMENT_STATUS,
  REQUIREMENT_PRIORITY
} from '@/api/functional_test'
import { useProjectStore } from '@/stores'

const projectStore = useProjectStore()

// 基础数据
const inputMode = ref('text')
const inputText = ref('')
const inputTitle = ref('')
const requirementList = ref([])
const selectedRequirementId = ref(null)
const selectedRequirement = ref(null)

// 优化相关状态
const optimizing = ref(false)
const optimizeResult = ref(null)
const streamText = ref('')
const saving = ref(false)
const applying = ref(false)

// 项目ID
const projectId = computed(() => {
  return projectStore.currentProject?.id
})

// 是否可以优化
const canOptimize = computed(() => {
  if (inputMode.value === 'text') {
    return inputText.value.trim().length > 0
  } else {
    return !!selectedRequirementId.value
  }
})

// 获取优先级标签
const getPriorityLabel = (priority) => {
  return REQUIREMENT_PRIORITY_LABELS[priority] || '未知'
}

const getPriorityType = (priority) => {
  const map = { 1: 'info', 2: '', 3: 'warning', 4: 'danger' }
  return map[priority] || ''
}

// 格式化 Markdown
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

// 加载需求列表
const loadRequirements = async () => {
  if (!projectId.value) return
  try {
    const response = await getRequirementsList(projectId.value, { page: 1, page_size: 200 })
    requirementList.value = response.data?.datas || response.data?.items || []
  } catch (error) {
    console.error('加载需求列表失败:', error)
  }
}

// 选择需求
const handleRequirementSelect = (id) => {
  selectedRequirement.value = requirementList.value.find(r => r.id === id) || null
}

// 执行 AI 优化
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

    let url, body

    if (inputMode.value === 'requirement' && selectedRequirementId.value) {
      // 对已有需求进行优化
      url = `${baseUrl}/functional_test/${projectId.value}/requirements/${selectedRequirementId.value}/ai_optimize`
      body = null
    } else {
      // 对自由输入的文本进行优化
      url = `${baseUrl}/functional_test/${projectId.value}/ai_optimize_text`
      body = JSON.stringify({
        title: inputTitle.value.trim() || null,
        text: inputText.value.trim()
      })
    }

    const headers = {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }

    const response = await fetch(url, {
      method: 'POST',
      headers,
      body
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.detail || `HTTP ${response.status}`)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()

    while (true) {
      const { value, done } = await reader.read()
      if (done) break

      const text = decoder.decode(value, { stream: true })
      const lines = text.split('\n')

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
          } catch (e) {
            // ignore parse errors
          }
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

// 保存为新需求
const handleSaveAsRequirement = async () => {
  if (!optimizeResult.value || !projectId.value) return

  try {
    await ElMessageBox.confirm(
      '将优化后的需求保存到需求管理中，确认继续？',
      '保存为需求',
      { confirmButtonText: '确认保存', cancelButtonText: '取消', type: 'info' }
    )

    saving.value = true

    // 获取第一个模块作为默认模块
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
    
    // 刷新需求列表
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

// 应用到原需求
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
    
    // 刷新需求列表
    await loadRequirements()
    // 更新预览
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

// 复制结果
const handleCopyResult = async () => {
  if (!optimizeResult.value) return
  
  const text = `# ${optimizeResult.value.optimized_title}\n\n${optimizeResult.value.optimized_description}` +
    (optimizeResult.value.acceptance_criteria?.length
      ? '\n\n## 验收标准\n' + optimizeResult.value.acceptance_criteria.map((c, i) => `${i + 1}. ${c}`).join('\n')
      : '') +
    (optimizeResult.value.risks?.length
      ? '\n\n## 风险提示\n' + optimizeResult.value.risks.map((r, i) => `${i + 1}. ${r}`).join('\n')
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
  selectedRequirementId.value = null
  selectedRequirement.value = null
  optimizeResult.value = null
  streamText.value = ''
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
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
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
</style>
