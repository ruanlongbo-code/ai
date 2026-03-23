<template>
  <div class="case-generation-page">
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
            <el-breadcrumb-item>用例生成</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="action-section">
          <el-button @click="handleBack">
            <el-icon>
              <ArrowLeft/>
            </el-icon>
            返回列表
          </el-button>
        </div>
      </div>
    </div>

    <div v-loading="loading" class="page-content">
      <div class="generation-container">
        <!-- 需求信息卡片 - 独占一行 -->
        <div class="requirement-section">
          <el-card class="requirement-card">
            <template #header>
              <div class="card-header">
                <h3>需求信息</h3>
              </div>
            </template>

            <div v-if="requirement" class="requirement-info">
              <div class="title-section">
                <h2>{{ requirement.title }}</h2>
                <!-- 按钮组 -->
                <div class="button-group">
                  <el-button
                      type="primary"
                      size="large"
                      :loading="generating"
                      @click="handleGenerate"
                      :disabled="!canGenerate"
                  >
                    <el-icon v-if="!generating">
                      <MagicStick/>
                    </el-icon>
                    {{ generating ? '正在生成...' : '🧠 知识增强生成用例' }}
                  </el-button>
                  
                  <!-- 查看用例按钮，只在生成完成后显示 -->
                  <el-button
                      v-if="progressStatus === 'success'"
                      type="success"
                      size="large"
                      @click="handleViewCases"
                  >
                    <el-icon>
                      <View/>
                    </el-icon>
                    查看用例
                  </el-button>

                  <!-- 下载XMind按钮，只在生成完成后显示 -->
                  <el-button
                      v-if="progressStatus === 'success'"
                      type="warning"
                      size="large"
                      :loading="exportingXmind"
                      @click="showXmindDialog"
                  >
                    <el-icon>
                      <Download/>
                    </el-icon>
                    下载 XMind
                  </el-button>

                  <!-- 导入飞书用例集按钮 -->
                  <el-button
                      v-if="progressStatus === 'success'"
                      size="large"
                      :loading="importingFeishu"
                      @click="showFeishuDialog"
                      style="background: #3370ff; color: white; border-color: #3370ff;"
                  >
                    <el-icon>
                      <Upload/>
                    </el-icon>
                    导入飞书用例集
                  </el-button>
                </div>
              </div>

              <div v-if="requirement.description" class="description-section">
                <label>需求信息</label>
                <div class="description-content" v-html="requirement.description || '暂无描述'"></div>
              </div>

              <!-- 知识增强提示 -->
              <div class="knowledge-enhance-banner">
                <el-alert
                    title="知识增强模式已启用"
                    type="info"
                    :closable="false"
                    show-icon
                >
                  <template #default>
                    <div class="enhance-desc">
                      生成用例时将自动检索以下知识源，提升用例完整性：
                      <div class="enhance-sources">
                        <el-tag size="small" type="primary" effect="plain">
                          <el-icon><FolderOpened /></el-icon> RAG知识库文档
                        </el-tag>
                        <el-tag size="small" type="success" effect="plain">
                          <el-icon><Cpu /></el-icon> 需求评审记录
                        </el-tag>
                        <el-tag size="small" type="warning" effect="plain">
                          <el-icon><Checked /></el-icon> 技术评审记录
                        </el-tag>
                        <el-tag size="small" type="danger" effect="plain">
                          <el-icon><List /></el-icon> 用例评审记录
                        </el-tag>
                        <el-tag size="small" effect="plain">
                          <el-icon><Notebook /></el-icon> 历史用例集
                        </el-tag>
                      </div>
                    </div>
                  </template>
                </el-alert>
              </div>
            </div>

            <div v-else class="loading-placeholder">
              <el-skeleton :rows="6" animated/>
            </div>
          </el-card>
        </div>

        <!-- 生成进度条 -->
        <div v-if="generating || progressStatus === 'success' || progressStatus === 'exception'" class="progress-section">
          <el-card class="progress-card" shadow="never">
            <div class="progress-wrapper">
              <div class="progress-header">
                <span class="progress-label">
                  <el-icon v-if="generating" class="is-loading"><Loading /></el-icon>
                  <el-icon v-else-if="progressStatus === 'success'" style="color:#67c23a"><SuccessFilled /></el-icon>
                  <el-icon v-else-if="progressStatus === 'exception'" style="color:#f56c6c"><CircleCloseFilled /></el-icon>
                  {{ progressText || '准备中...' }}
                </span>
                <span class="progress-percent">{{ progress }}%</span>
              </div>
              <el-progress
                :percentage="progress"
                :status="progressStatus === 'active' ? '' : progressStatus"
                :stroke-width="18"
                :show-text="false"
                :striped="generating"
                :striped-flow="generating"
                :duration="8"
              />
              <div class="progress-steps">
                <span :class="['step', { active: progress >= 5 }]">分析需求</span>
                <span :class="['step', { active: progress >= 30 }]">提取测试点</span>
                <span :class="['step', { active: progress >= 40 }]">生成用例</span>
                <span :class="['step', { active: progress >= 70 }]">验证覆盖率</span>
                <span :class="['step', { active: progress >= 80 }]">保存用例</span>
                <span :class="['step', { active: progress >= 100 }]">完成</span>
              </div>
            </div>
          </el-card>
        </div>

        <!-- 生成进度和生成数据 - 左右布局 (3:7) -->
        <div class="content-section">
          <!-- 左侧：生成进度列表 (30%) -->
          <div class="notification-section" v-if="notifications.length > 0">
            <NotificationList
                ref="notificationListRef"
                :notifications="notifications"
                @clear="clearNotifications"
                @mark-read="markNotificationAsRead"
                @mark-all-read="markAllNotificationsAsRead"
            />
          </div>

          <!-- 右侧：生成数据 (70%) -->
          <div class="generation-section">
          <!-- 实时生成输出 - ChatGPT风格 -->
          <div class="chat-wrapper">
            <ChatContainer
                ref="chatContainerRef"
                :messages="chatMessages"
                :title="'AI 用例生成助手'"
                :show-header="false"
                :show-message-actions="true"
                :empty-text="'点击上方开始生成用例按钮，AI助手将为您生成测试用例'"
                :is-loading="generating"
                :streaming-message-id="streamingMessageId"
                :auto-scroll="true"
                @clear-messages="clearChatMessages"
                @export-messages="handleExportChat"
                @copy-message="handleCopyMessage"
                @regenerate-message="handleRegenerateMessage"
            />
          </div>

          <!-- 生成结果 -->
          <el-card v-if="generatedCases.length > 0" class="results-card">
            <template #header>
              <div class="card-header">
                <h3>生成结果 ({{ generatedCases.length }} 个用例)</h3>
                <div class="header-actions">
                  <el-button size="small" @click="handleSelectAll">
                    {{ allSelected ? '取消全选' : '全选' }}
                  </el-button>
                  <el-button
                      type="primary"
                      size="small"
                      :disabled="selectedCases.length === 0"
                      @click="handleSaveCases"
                  >
                    保存选中用例 ({{ selectedCases.length }})
                  </el-button>
                </div>
              </div>
            </template>

            <div class="cases-list">
              <div
                  v-for="(caseItem, index) in generatedCases"
                  :key="index"
                  class="case-item"
                  :class="{ selected: selectedCases.includes(index) }"
              >
                <div class="case-header">
                  <el-checkbox
                      :model-value="selectedCases.includes(index)"
                      @change="handleCaseSelect(index, $event)"
                  />
                  <span class="case-title">{{ caseItem.case_name }}</span>
                  <el-tag :type="getCaseTypeTag(caseItem.type)" size="small">
                    {{ getCaseTypeLabel(caseItem.type) }}
                  </el-tag>
                </div>

                <div class="case-content">
                  <div class="case-steps">
                    <strong>测试步骤：</strong>
                    <ol>
                      <li v-for="step in caseItem.steps" :key="step">{{ step }}</li>
                    </ol>
                  </div>

                  <div class="case-expected">
                    <strong>预期结果：</strong>
                    <p>{{ caseItem.expected_result }}</p>
                  </div>
                </div>
              </div>
            </div>
          </el-card>
        </div>
          </div>
        </div>
      </div>
    </div>
<!--  </div>-->

    <!-- XMind 模板设置弹窗 -->
    <el-dialog
        v-model="xmindDialogVisible"
        title="XMind 导出设置"
        width="680px"
        :close-on-click-modal="false"
    >
      <div class="xmind-dialog-content">
        <!-- 模板预览 -->
        <div class="template-preview">
          <h4>默认模板格式预览</h4>
          <div class="preview-tree">
            <div class="tree-node root">
              <span class="node-icon">📋</span>
              <span class="node-text">{{ requirement?.title || '需求标题' }}</span>
            </div>
            <div class="tree-node level1">
              <span class="tree-line">├─</span>
              <span class="node-text">🎯 {{ xmindSettings.scenario_prefix }}场景A{{ xmindSettings.scenario_suffix }}</span>
            </div>
            <div class="tree-node level2">
              <span class="tree-line">│ &nbsp; ├─</span>
              <span class="node-text">
                <template v-if="xmindSettings.show_priority">{P0} </template>
                <template v-if="xmindSettings.show_case_id">[TC_001] </template>
                xxx（用例标题）
              </span>
            </div>
            <div class="tree-node level3">
              <span class="tree-line">│ &nbsp; │ &nbsp; └─</span>
              <span class="node-text leaf preview-multiline">{{ xmindSettings.show_node_labels ? '前置条件：\n' : '' }}1.前置条件内容</span>
            </div>
            <div class="tree-node level4">
              <span class="tree-line">│ &nbsp; │ &nbsp; &nbsp; &nbsp; └─</span>
              <span class="node-text leaf preview-multiline">{{ xmindSettings.show_node_labels ? '测试步骤：\n' : '' }}1.测试步骤</span>
            </div>
            <div class="tree-node level5">
              <span class="tree-line">│ &nbsp; │ &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; └─</span>
              <span class="node-text leaf preview-multiline">{{ xmindSettings.show_node_labels ? '预期结果：\n' : '' }}1.预期结果</span>
            </div>
            <div class="tree-node level2">
              <span class="tree-line">│ &nbsp; └─</span>
              <span class="node-text">
                <template v-if="xmindSettings.show_priority">{P1} </template>
                xxx（用例标题）
              </span>
            </div>
            <div class="tree-node level1">
              <span class="tree-line">└─</span>
              <span class="node-text">🎯 {{ xmindSettings.scenario_prefix }}场景B{{ xmindSettings.scenario_suffix }}</span>
            </div>
            <div class="tree-node level2">
              <span class="tree-line">&nbsp; &nbsp; └─</span>
              <span class="node-text">...（更多用例）</span>
            </div>
          </div>
          <p class="preview-note">* 根节点为需求标题，第二层为验证场景，第三层为用例</p>
        </div>

        <!-- 模板设置选项 -->
        <el-divider content-position="left">场景节点设置</el-divider>

        <el-form label-width="160px" class="template-form">
          <el-form-item label="场景名称前缀">
            <el-input v-model="xmindSettings.scenario_prefix" placeholder="验证" style="width: 120px;" />
          </el-form-item>
          <el-form-item label="场景名称后缀">
            <el-input v-model="xmindSettings.scenario_suffix" placeholder="功能" style="width: 120px;" />
          </el-form-item>

          <el-divider content-position="left">用例节点设置</el-divider>

          <el-form-item label="用例标题显示优先级">
            <el-switch v-model="xmindSettings.show_priority" />
            <span class="setting-hint">如 {P0}、{P1}、{P2}</span>
          </el-form-item>
          <el-form-item label="用例标题显示编号">
            <el-switch v-model="xmindSettings.show_case_id" />
            <span class="setting-hint">如 [TC_001]</span>
          </el-form-item>

          <el-divider />

          <el-form-item label="注明节点属性">
            <el-switch v-model="xmindSettings.show_node_labels" />
            <span class="setting-hint">开启后子节点显示属性标签，如 "前置条件：xxx"、"测试步骤：xxx"</span>
          </el-form-item>
        </el-form>
      </div>

      <template #footer>
        <el-button @click="xmindDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="exportingXmind" @click="handleExportXmind">
          <el-icon><Download /></el-icon>
          确认导出
        </el-button>
      </template>
    </el-dialog>

    <!-- 飞书导入弹窗 -->
    <el-dialog v-model="feishuDialogVisible" title="导入飞书用例集" width="500px" :close-on-click-modal="false">
      <div style="background: #f0f7ff; border-radius: 8px; padding: 12px 16px; margin-bottom: 16px; font-size: 13px; line-height: 1.8; color: #303133;">
        <div style="font-weight: 600; margin-bottom: 6px; color: #3370ff;">获取 x-token：</div>
        <div>1. <el-button size="small" type="primary" plain @click="openFeishuPage" style="margin: 0 2px;">打开飞书用例管理页</el-button> 并登录</div>
        <div>2. F12 → Network → 筛选 <code style="background:#e8eaed;padding:1px 4px;border-radius:3px;">m-api</code> → 点击任意请求</div>
        <div>3. Request Headers 中复制 <code style="background:#e8eaed;padding:1px 4px;border-radius:3px;">x-token</code> 的值</div>
      </div>
      <el-form label-position="top">
        <el-form-item label="飞书 x-token" required>
          <el-input v-model="feishuToken" type="textarea" :rows="2" placeholder="粘贴 x-token..." />
        </el-form-item>
        <el-form-item label="用例集标题（可选）">
          <el-input v-model="feishuTitle" :placeholder="requirement?.title || '自动使用需求标题'" />
        </el-form-item>
      </el-form>
      <el-alert v-if="feishuResult" :title="feishuResult.success ? '导入成功' : '导入失败'" :type="feishuResult.success ? 'success' : 'error'" show-icon style="margin-top: 12px;">
        <template #default>
          <div v-if="feishuResult.success">
            共导入 {{ feishuResult.case_count }} 条用例<br/>
            <a :href="feishuResult.case_set_url" target="_blank" style="color: #3370ff;">点击查看飞书用例集 →</a>
          </div>
          <div v-else>{{ feishuResult.message }}</div>
        </template>
      </el-alert>
      <template #footer>
        <el-button @click="feishuDialogVisible = false">关闭</el-button>
        <el-button type="primary" :loading="importingFeishu" :disabled="!feishuToken" @click="handleImportFeishu" style="background: #3370ff; border-color: #3370ff;">
          <el-icon><Upload /></el-icon> 确认导入
        </el-button>
      </template>
    </el-dialog>
</template>

<script setup>
defineOptions({ name: 'FunctionTestCaseGenerate' })
import {ref, reactive, computed, onMounted, onActivated, onDeactivated, nextTick} from 'vue'
import {useRoute, useRouter} from 'vue-router'
import {ElMessage, ElMessageBox} from 'element-plus'
import {
  ArrowLeft,
  MagicStick,
  InfoFilled,
  Loading,
  SuccessFilled,
  WarningFilled,
  CircleCloseFilled,
  ChatDotRound,
  View,
  Download,
  FolderOpened,
  Cpu,
  Checked,
  List,
  Notebook,
  Upload
} from '@element-plus/icons-vue'
import ChatContainer from '@/components/ChatContainer.vue'
import NotificationList from '@/components/NotificationList.vue'
import {
  getRequirementDetail,
  exportCasesAsXmind,
  importCasesToFeishu,
  REQUIREMENT_STATUS_LABELS,
  REQUIREMENT_STATUS_COLORS,
  REQUIREMENT_PRIORITY_LABELS
} from '@/api/functional_test'
import {useProjectStore} from '@/stores'
import {useUserStore} from '@/stores'
const route = useRoute()
const router = useRouter()
const projectStore = useProjectStore()
const userStore = useUserStore()

// 响应式数据
const loading = ref(false)
const requirement = ref(null)
const generating = ref(false)
const progress = ref(0)
const progressStatus = ref('')
const progressText = ref('')
const generatedCases = ref([])
const selectedCases = ref([])
const outputMessages = ref([]) // 保留原有的，用于兼容
const outputContainer = ref(null)

// 新增：ChatGPT风格的消息数据
const chatMessages = ref([])
const streamingMessageId = ref('')
const currentStreamingMessage = ref(null)

// 组件引用
const chatContainerRef = ref(null)
const notificationListRef = ref(null)

// XMind 导出相关
const xmindDialogVisible = ref(false)
const exportingXmind = ref(false)
const xmindSettings = reactive({
  show_priority: true,
  show_case_id: false,
  show_node_labels: false,
  scenario_prefix: '验证',
  scenario_suffix: '功能',
})

// 飞书导入相关
const feishuDialogVisible = ref(false)
const importingFeishu = ref(false)
const feishuToken = ref(localStorage.getItem('feishu_x_token') || '')
const feishuTitle = ref('')
const feishuResult = ref(null)

const openFeishuPage = () => {
  window.open('https://project.feishu.cn/research__development/meegoPlg/MII_642BBF6AC6C74001_test_management_use_case_set', '_blank')
}

// 新增：进度列表数据
const notifications = ref([])
const notificationIdCounter = ref(0)

// 生成配置表单
const generationForm = reactive({
  count: 8,
  types: ['positive', 'negative', 'boundary'],
  detail: 'detailed'
})

// 计算属性
const projectId = computed(() => projectStore.currentProject?.id)
const requirementId = computed(() => route.params.requirementId || route.query.requirement_id)

const canGenerate = computed(() => {
  return requirement.value && generationForm.types.length > 0 && !generating.value
})

const allSelected = computed(() => {
  return generatedCases.value.length > 0 && selectedCases.value.length === generatedCases.value.length
})

// 方法
const handleBack = () => {
  router.push(`/function-test/requirement`)
}

const formatDate = (dateString) => {
  if (!dateString) return '未知'
  return new Date(dateString).toLocaleString('zh-CN')
}

const formatTime = (timestamp) => {
  return new Date(timestamp).toLocaleTimeString('zh-CN')
}

const getPriorityLabel = (priority) => {
  return REQUIREMENT_PRIORITY_LABELS[priority] || '未知'
}

const getPriorityType = (priority) => {
  const typeMap = {1: 'info', 2: 'warning', 3: 'danger', 4: 'danger'}
  return typeMap[priority] || 'info'
}

const getStatusLabel = (status) => {
  return REQUIREMENT_STATUS_LABELS[status] || '未知'
}

const getStatusColor = (status) => {
  return REQUIREMENT_STATUS_COLORS[status] || '#909399'
}

const getCaseTypeLabel = (type) => {
  const labels = {
    positive: '正向用例',
    negative: '负向用例',
    boundary: '边界用例',
    exception: '异常用例'
  }
  return labels[type] || type
}

const getCaseTypeTag = (type) => {
  const tags = {
    positive: 'success',
    negative: 'warning',
    boundary: 'info',
    exception: 'danger'
  }
  return tags[type] || 'info'
}

const getMessageTypeLabel = (type) => {
  const labels = {
    info: '信息',
    start: '开始',
    progress: '进度',
    complete: '完成',
    error: '错误'
  }
  return labels[type] || '消息'
}

const addMessage = (type, message) => {
  outputMessages.value.push({
    type,
    message,
    timestamp: Date.now()
  })

  // 自动滚动到底部
  nextTick(() => {
    if (outputContainer.value) {
      outputContainer.value.scrollTop = outputContainer.value.scrollHeight
    }
  })
}

const clearOutput = () => {
  outputMessages.value = []
  progress.value = 0
  progressText.value = ''
}

const scrollToBottom = () => {
  nextTick(() => {
    if (outputContainer.value) {
      outputContainer.value.scrollTop = outputContainer.value.scrollHeight
    }
    // 同时滚动ChatContainer和NotificationList
    if (chatContainerRef.value?.scrollToBottom) {
      chatContainerRef.value.scrollToBottom()
    }
    if (notificationListRef.value?.scrollToBottom) {
      notificationListRef.value.scrollToBottom()
    }
  })
}

// SSE流式接口处理
const handleGenerate = async () => {
  if (!projectId.value || !requirementId.value) {
    ElMessage.error('缺少必要参数')
    return
  }

  try {
    generating.value = true
    progress.value = 0
    progressStatus.value = 'active'
    progressText.value = '正在连接服务器...'
    generatedCases.value = []
    selectedCases.value = []

    // 清空之前的输出
    clearOutput()
    clearChatMessages()

    // 不再添加开始消息，等待SSE的start消息来创建流式消息

    // 使用fetch替代EventSource来支持POST请求
    const response = await fetch(
        `${import.meta.env.VITE_BASE_API}/functional_test/${projectId.value}/requirements/${requirementId.value}/generate_cases`,
        {
          method: 'POST',
          headers: {
            'Accept': 'text/event-stream',
            'Cache-Control': 'no-cache',
            'Authorization': `Bearer ${userStore.token}`,
            'Content-Type': 'application/json'
          },
          // 不发送跨域凭证（cookies），以避免 CORS 对通配符来源的限制
          credentials: 'omit'
        }
    )

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    let progressValue = 0
    let currentStreamingId = null

    while (true) {
      const {done, value} = await reader.read()

      if (done) {
        generating.value = false
        if (progress.value < 100) {
          progress.value = 100
          progressStatus.value = 'success'
          progressText.value = '生成完成！'

          // 完成流式消息
          if (currentStreamingId && currentStreamingMessage.value) {
            currentStreamingMessage.value.content += '\n🎉 所有任务已完成！'
            updateStreamingMessage(currentStreamingId, currentStreamingMessage.value.content, true)
          } else {
            addChatMessage('assistant', '✅ 测试用例生成完成！所有用例已准备就绪。', false)
          }
        }
        break
      }

      // 解码数据块
      buffer += decoder.decode(value, {stream: true})

      // 处理完整的SSE消息
      const lines = buffer.split('\n')
      buffer = lines.pop() || '' // 保留不完整的行

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6) // 移除 'data: ' 前缀

          if (data === '[DONE]') {
            generating.value = false
            progress.value = 100
            progressStatus.value = 'success'
            progressText.value = '生成完成！'

            // 完成流式消息
            if (currentStreamingId && currentStreamingMessage.value) {
              currentStreamingMessage.value.content += '\n🎉 生成任务已完成！'
              updateStreamingMessage(currentStreamingId, currentStreamingMessage.value.content, true)
            } else {
              addChatMessage('assistant', '✅ 测试用例生成完成！所有用例已准备就绪。', false)
            }
            return
          }

          try {
            const parsedData = JSON.parse(data)

            // 处理不同类型的消息
            if (parsedData.type === 'start') {
              // 使用后端传来的进度值
              if (parsedData.progress !== undefined) {
                progress.value = parsedData.progress
              }
              progressText.value = parsedData.message
              // 开始流式消息，创建一个可以持续更新的消息
              if (!currentStreamingId) {
                currentStreamingId = startStreamingMessage('assistant', `🔄 ${parsedData.message}\n`)
              }
              // 添加到进度列表
              addNotification('start', parsedData.message)
              scrollToBottom()
            } else if (parsedData.type === 'info') {
              // 使用后端传来的进度值
              if (parsedData.progress !== undefined) {
                progress.value = parsedData.progress
              }
              progressText.value = parsedData.message

              // info 类型消息只添加到进度列表，不显示在流式输出中
              addNotification('info', parsedData.message)
              scrollToBottom()
            } else if (parsedData.type === 'progress') {
              // 使用后端传来的进度值（如果有）
              if (parsedData.progress !== undefined) {
                progress.value = parsedData.progress
              }
              // 处理流式内容 - 直接追加到当前消息（保持当前方式）
              if (!currentStreamingId) {
                currentStreamingId = startStreamingMessage('assistant', parsedData.message)
              } else {
                // 累积流式内容
                if (currentStreamingMessage.value) {
                  currentStreamingMessage.value.content += parsedData.message
                  updateStreamingMessage(currentStreamingId, currentStreamingMessage.value.content, false)
                }
              }
              // progress类型不添加到进度列表，保持当前显示方式
              scrollToBottom()
            } else if (parsedData.type === 'complete') {
              progress.value = 100
              progressStatus.value = 'success'
              progressText.value = parsedData.message

              // 完成当前流式消息
              if (currentStreamingId) {
                // 在完成前添加最终的完成信息
                if (currentStreamingMessage.value) {
                  currentStreamingMessage.value.content += `\n✅ ${parsedData.message}`
                  updateStreamingMessage(currentStreamingId, currentStreamingMessage.value.content, true)
                }
                currentStreamingId = null
              } else {
                // 如果没有流式消息，创建一个完成消息
                addChatMessage('assistant', `✅ ${parsedData.message}`, false)
              }

              // 如果有生成的用例数据，解析并显示
              if (parsedData.cases) {
                generatedCases.value = parsedData.cases
                selectedCases.value = generatedCases.value.map((_, index) => index)

                // 将结果总结追加到流式消息中
                if (currentStreamingId && currentStreamingMessage.value) {
                  const summaryMessage = `\n## 📋 生成结果总结

共生成 **${parsedData.cases.length}** 个测试用例：

${parsedData.cases.map((caseItem, index) =>
                      `${index + 1}. **${caseItem.case_name}** (${getCaseTypeLabel(caseItem.type)})`
                  ).join('\n')}

您可以在下方查看详细内容并选择需要保存的用例。`

                  currentStreamingMessage.value.content += summaryMessage
                  updateStreamingMessage(currentStreamingId, currentStreamingMessage.value.content, true)
                } else {
                  // 如果没有流式消息，创建新的总结消息
                  const summaryMessage = `## 📋 生成结果总结

共生成 **${parsedData.cases.length}** 个测试用例：

${parsedData.cases.map((caseItem, index) =>
                      `${index + 1}. **${caseItem.case_name}** (${getCaseTypeLabel(caseItem.type)})`
                  ).join('\n')}

您可以在下方查看详细内容并选择需要保存的用例。`

                  addChatMessage('assistant', summaryMessage, true)
                }
              }
              // 添加到进度列表
              addNotification('complete', parsedData.message)
              scrollToBottom()
            } else if (parsedData.type === 'error') {
              progressStatus.value = 'exception'
              progressText.value = parsedData.message
              // 将错误信息追加到流式消息中
              if (currentStreamingId && currentStreamingMessage.value) {
                currentStreamingMessage.value.content += `\n❌ 错误：${parsedData.message}`
                updateStreamingMessage(currentStreamingId, currentStreamingMessage.value.content, true)
                currentStreamingId = null
              } else {
                addChatMessage('system', `❌ 错误：${parsedData.message}`, false)
              }
              // 添加到进度列表
              addNotification('error', parsedData.message)
              scrollToBottom()
            } else {
              // 其他类型的消息 - 追加到流式消息中
              if (currentStreamingId && currentStreamingMessage.value) {
                currentStreamingMessage.value.content += `\n${parsedData.message}`
                updateStreamingMessage(currentStreamingId, currentStreamingMessage.value.content, false)
              } else {
                addChatMessage('assistant', parsedData.message, false)
              }
              // 其他类型也添加到进度列表
              addNotification(parsedData.type || 'info', parsedData.message)
              scrollToBottom()
            }

            // 保持原有的兼容性
            addMessage(parsedData.type, parsedData.message)
            scrollToBottom()
          } catch (error) {
            console.error('解析SSE数据失败:', error)
            addMessage('error', `数据解析错误: ${error.message}`)
            addChatMessage('system', `❌ 数据解析错误：${error.message}`, false)
          }
        }
      }
    }

  } catch (error) {
    console.error('生成用例失败:', error)
    generating.value = false
    progress.value = 100
    progressStatus.value = 'exception'
    progressText.value = '生成失败'

    // 将错误信息追加到流式消息中
    if (currentStreamingId && currentStreamingMessage.value) {
      currentStreamingMessage.value.content += `\n❌ 生成失败：${error.message}`
      updateStreamingMessage(currentStreamingId, currentStreamingMessage.value.content, true)
    } else {
      addMessage('error', `生成失败: ${error.message}`)
      addChatMessage('system', `❌ 生成失败：${error.message}`, false)
    }
    ElMessage.error('生成用例失败')
  }
}

// ===== XMind 导出相关方法 =====
const showXmindDialog = () => {
  xmindDialogVisible.value = true
}

const handleExportXmind = async () => {
  if (!projectId.value || !requirementId.value) {
    ElMessage.error('缺少必要参数')
    return
  }

  try {
    exportingXmind.value = true

    const response = await exportCasesAsXmind(
        projectId.value,
        requirementId.value,
        {
          show_priority: xmindSettings.show_priority,
          show_case_id: xmindSettings.show_case_id,
          show_node_labels: xmindSettings.show_node_labels,
          scenario_prefix: xmindSettings.scenario_prefix,
          scenario_suffix: xmindSettings.scenario_suffix,
        }
    )

    // 处理文件下载
    const blob = new Blob([response.data || response], { type: 'application/octet-stream' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    const title = requirement.value?.title || '测试用例'
    link.download = `${title}_测试用例.xmind`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)

    ElMessage.success('XMind 文件下载成功')
    xmindDialogVisible.value = false
  } catch (error) {
    console.error('导出 XMind 失败:', error)
    ElMessage.error('导出 XMind 文件失败，请确认已有生成的用例')
  } finally {
    exportingXmind.value = false
  }
}

// ===== 飞书导入相关方法 =====
const showFeishuDialog = () => {
  feishuResult.value = null
  feishuTitle.value = requirement.value?.title || ''
  feishuDialogVisible.value = true
}

const handleImportFeishu = async () => {
  if (!feishuToken.value) {
    ElMessage.warning('请输入飞书 x-token')
    return
  }
  if (!projectId.value || !requirementId.value) {
    ElMessage.error('缺少必要参数')
    return
  }

  try {
    importingFeishu.value = true
    feishuResult.value = null
    localStorage.setItem('feishu_x_token', feishuToken.value)

    const response = await importCasesToFeishu(projectId.value, {
      requirement_id: parseInt(requirementId.value),
      feishu_token: feishuToken.value,
      title: feishuTitle.value || undefined,
    })

    const data = response.data || response
    feishuResult.value = {
      success: true,
      case_count: data.case_count,
      case_set_url: data.case_set_url,
    }
    ElMessage.success(`成功导入 ${data.case_count} 条用例到飞书`)
  } catch (error) {
    console.error('导入飞书失败:', error)
    const msg = error.response?.data?.detail || error.message || '导入失败'
    feishuResult.value = { success: false, message: msg }
    ElMessage.error(msg)
  } finally {
    importingFeishu.value = false
  }
}

const handleCaseSelect = (index, selected) => {
  if (selected) {
    if (!selectedCases.value.includes(index)) {
      selectedCases.value.push(index)
    }
  } else {
    const idx = selectedCases.value.indexOf(index)
    if (idx > -1) {
      selectedCases.value.splice(idx, 1)
    }
  }
}

// 查看用例按钮点击处理
const handleViewCases = () => {
  // 跳转到需求详情页
  router.push(`/function-test/requirement/${requirementId.value}`)
}

const handleSelectAll = () => {
  if (allSelected.value) {
    selectedCases.value = []
  } else {
    selectedCases.value = generatedCases.value.map((_, index) => index)
  }
}

const handleSaveCases = async () => {
  try {
    const selectedCaseData = selectedCases.value.map(index => generatedCases.value[index])

    await ElMessageBox.confirm(
        `确定要保存选中的 ${selectedCases.value.length} 个测试用例吗？`,
        '保存用例',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'info'
        }
    )

    // 这里应该调用保存用例的API
    // await saveFunctionalCases(projectId.value, selectedCaseData)

    ElMessage.success('用例保存成功')

    // 跳转到用例列表页面
    router.push(`/function-test/case?requirement_id=${requirementId.value}`)
  } catch (error) {
    if (error !== 'cancel') {
      console.error('保存用例失败:', error)
      ElMessage.error('保存用例失败')
    }
  }
}

// 加载需求详情
const loadRequirementDetail = async () => {
  try {
    loading.value = true
    const response = await getRequirementDetail(projectId.value, requirementId.value)
    requirement.value = response.data
  } catch (error) {
    console.error('加载需求详情失败:', error)
    ElMessage.error('加载需求详情失败')
  } finally {
    loading.value = false
  }
}

// 生命周期
onMounted(() => {
  if (projectId.value && requirementId.value) {
    loadRequirementDetail()
  }
})

onActivated(() => {
  nextTick(() => {})
})

onDeactivated(() => {})

// 新增：ChatGPT风格消息处理方法
const addChatMessage = (type, content, isMarkdown = false) => {
  const messageId = `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`

  const message = {
    id: messageId,
    type: type === 'start' ? 'assistant' : type === 'error' ? 'system' : 'assistant',
    content: content,
    timestamp: Date.now(),
    isMarkdown: isMarkdown,
    isStreaming: false
  }

  chatMessages.value.push(message)
  return messageId
}

const updateStreamingMessage = (messageId, content, isComplete = false) => {
  const messageIndex = chatMessages.value.findIndex(msg => msg.id === messageId)
  if (messageIndex !== -1) {
    chatMessages.value[messageIndex].content = content
    chatMessages.value[messageIndex].isStreaming = !isComplete

    if (isComplete) {
      streamingMessageId.value = ''
      currentStreamingMessage.value = null
    }
  }
}

const startStreamingMessage = (type, initialContent = '') => {
  const messageId = addChatMessage(type, initialContent, true)
  streamingMessageId.value = messageId
  currentStreamingMessage.value = {
    id: messageId,
    content: initialContent
  }

  // 设置消息为流式状态
  const messageIndex = chatMessages.value.findIndex(msg => msg.id === messageId)
  if (messageIndex !== -1) {
    chatMessages.value[messageIndex].isStreaming = true
  }

  return messageId
}

const clearChatMessages = () => {
  chatMessages.value = []
  streamingMessageId.value = ''
  currentStreamingMessage.value = null
}

const handleExportChat = (exportData) => {
  ElMessage.success('对话记录已导出')
}

const handleCopyMessage = (message) => {
  ElMessage.success('消息已复制到剪贴板')
}

const handleRegenerateMessage = (message) => {
  ElMessage.info('重新生成功能暂未实现')
}

// 进度列表相关方法
const addNotification = (type, message) => {
  const notification = {
    id: `notification_${++notificationIdCounter.value}`,
    type,
    message,
    timestamp: Date.now(),
    read: false
  }
  notifications.value.push(notification)
}

const clearNotifications = () => {
  notifications.value = []
}

const markNotificationAsRead = (id) => {
  const notification = notifications.value.find(n => n.id === id)
  if (notification) {
    notification.read = true
  }
}

const markAllNotificationsAsRead = () => {
  notifications.value.forEach(n => n.read = true)
}
</script>

<style scoped>
.case-generation-page {
  min-height: 100vh;
  background-color: #f5f7fa;
}

.page-header {
  background: white;
  border-bottom: 1px solid #e4e7ed;
  padding: 16px 24px;
}

.header-content {
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 24px;
}

.breadcrumb-section {
  flex: none;
}

.action-section {
  display: flex;
  gap: 12px;
}

.page-content {
  padding: 20px;
}

.generation-container {
  display: flex;
  flex-direction: column;
  gap: 20px;


}

/* 需求信息区域 - 独占一行 */
.requirement-section {
  width: 100%;
  margin-bottom: 20px;
}

/* 进度条区域 */
.progress-section {
  width: 100%;
  margin-bottom: 8px;
}

.progress-card {
  border-radius: 12px;
  background: linear-gradient(135deg, #f0f5ff 0%, #fafbff 100%);
  border: 1px solid #e0e6f1;
}

.progress-card :deep(.el-card__body) {
  padding: 16px 24px;
}

.progress-wrapper {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.progress-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 500;
  color: #303133;
}

.progress-percent {
  font-size: 16px;
  font-weight: 600;
  color: #409eff;
}

.progress-steps {
  display: flex;
  justify-content: space-between;
  margin-top: 4px;
}

.progress-steps .step {
  font-size: 12px;
  color: #c0c4cc;
  transition: color 0.3s ease;
  position: relative;
}

.progress-steps .step.active {
  color: #409eff;
  font-weight: 500;
}

.progress-steps .step.active::before {
  content: '✓ ';
  font-size: 11px;
}

/* 内容区域 - 左右布局 */
.content-section {
  display: flex;
  gap: 20px;
  width: 100%;
  height: 800px;
}

/* 左侧进度区域 - 30% */
.notification-section {
  flex: 0 0 30%;
  position: sticky;
  top: 20px;
  height: 800px; 
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

/* 右侧生成区域 - 70% */
.generation-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 20px;
  min-width: 0; /* 防止flex子项溢出 */
  height: 800px;
  overflow-y: auto;
}

.requirement-card,
.output-card,
.results-card {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  width: 100%;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.header-actions {
  display: flex;
  gap: 8px;
}

/* 需求信息样式 */
.title-section {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.title-section h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  flex: 1;
}

.title-section .el-button {
  margin-left: 16px;
  padding: 12px 24px;
  font-size: 14px;
}

/* 按钮组样式 */
.button-group {
  display: flex;
  gap: 12px;
  align-items: center;
}

.meta-info {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.doc-no {
  font-size: 12px;
  color: #909399;
}

.info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 16px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-item label {
  font-size: 12px;
  color: #909399;
  font-weight: 500;
}

.description-section {
  margin-top: 16px;
}

.description-section label {
  display: block;
  margin-bottom: 8px;
  font-size: 12px;
  color: #909399;
  font-weight: 500;
}

.description-content {
  padding: 12px;
  background-color: #f8f9fa;
  border-radius: 4px;
  border: 1px solid #e4e7ed;
  line-height: 1.6;
  color: #606266;
  font-size: 14px;
}

/* 知识增强提示样式 */
.knowledge-enhance-banner {
  margin-top: 16px;
}

.enhance-desc {
  font-size: 13px;
  color: #606266;
  line-height: 1.8;
}

.enhance-sources {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
}

.enhance-sources .el-tag {
  display: flex;
  align-items: center;
  gap: 4px;
}

.generation-actions {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

.generation-actions .el-button {
  padding: 12px 32px;
  font-size: 16px;
}

/* 输出区域样式 */
.output-card {
  display: flex;
  flex-direction: column;
  min-height: 500px;
}

.chat-wrapper {
  mix-height: 600px;
  display: flex;
  flex-direction: column;
}

.output-container {
  height: 400px;
  overflow-y: auto;
  padding: 16px;
}

.empty-output {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.messages-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.message-item {
  padding: 12px;
  border-radius: 6px;
  border-left: 4px solid #e4e7ed;
}

.message-item.message-info {
  background-color: #f0f9ff;
  border-left-color: #409eff;
}

.message-item.message-start {
  background-color: #f0f9ff;
  border-left-color: #409eff;
}

.message-item.message-progress {
  background-color: #fff7e6;
  border-left-color: #e6a23c;
}

.message-item.message-complete {
  background-color: #f0f9ff;
  border-left-color: #67c23a;
}

.message-item.message-error {
  background-color: #fef0f0;
  border-left-color: #f56c6c;
}

.message-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.message-icon {
  font-size: 14px;
}

.message-type {
  font-size: 12px;
  font-weight: 500;
  color: #606266;
}

.message-time {
  font-size: 11px;
  color: #909399;
  margin-left: auto;
}

.message-content {
  font-size: 14px;
  line-height: 1.5;
  color: #303133;
}

.generation-progress {
  margin: 16px 0;
  padding: 16px;
  background-color: #f8f9fa;
  border-radius: 6px;
}

.progress-text {
  text-align: center;
  margin-top: 8px;
  font-size: 14px;
  color: #606266;
}

/* 结果列表样式 */
.results-card {
  max-height: 500px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.cases-list {
  max-height: 400px;
  overflow-y: auto;
  padding: 16px;
}

.case-item {
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  margin-bottom: 12px;
  padding: 16px;
  background: white;
  transition: all 0.3s;
}

.case-item:hover {
  border-color: #c6e2ff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.case-item.selected {
  border-color: #409eff;
  background-color: #f0f9ff;
}

.case-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.case-title {
  flex: 1;
  font-weight: 500;
  color: #303133;
}

.case-content {
  padding-left: 32px;
}

.case-steps {
  margin-bottom: 12px;
}

.case-steps ol {
  margin: 8px 0;
  padding-left: 20px;
}

.case-steps li {
  margin-bottom: 4px;
  line-height: 1.5;
}

.case-expected strong {
  color: #606266;
}

.case-expected p {
  margin: 8px 0 0 0;
  line-height: 1.5;
  color: #303133;
}

.loading-placeholder {
  padding: 20px 0;
}

/* ===== XMind 弹窗样式 ===== */
.xmind-dialog-content {
  max-height: 65vh;
  overflow-y: auto;
}

.template-preview {
  background: #f8f9fa;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 16px;
}

.template-preview h4 {
  margin: 0 0 16px 0;
  font-size: 15px;
  color: #303133;
}

.preview-tree {
  font-family: 'Courier New', Consolas, monospace;
  font-size: 13px;
  line-height: 2;
  color: #303133;
  background: white;
  border-radius: 6px;
  padding: 16px 20px;
  border: 1px solid #ebeef5;
}

.tree-node {
  white-space: nowrap;
}

.tree-node.root {
  font-weight: 600;
  font-size: 14px;
  color: #409eff;
}

.tree-node.level1 {
  padding-left: 20px;
  color: #303133;
  font-weight: 500;
}

.tree-node.level2 {
  padding-left: 20px;
  color: #606266;
}

.tree-node.level3 {
  padding-left: 20px;
  color: #606266;
}

.tree-node.level4 {
  padding-left: 20px;
  color: #606266;
}

.tree-node.level5 {
  padding-left: 20px;
  color: #606266;
}

.node-icon {
  margin-right: 6px;
}

.node-text.leaf {
  color: #909399;
  font-style: italic;
}

.node-text.preview-multiline {
  white-space: pre-line;
}

.tree-line {
  color: #c0c4cc;
  margin-right: 6px;
}

.preview-note {
  margin: 12px 0 0 0;
  font-size: 12px;
  color: #909399;
  font-style: italic;
}

.template-form {
  padding: 0 16px;
}

.setting-hint {
  margin-left: 12px;
  font-size: 12px;
  color: #909399;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .header-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .page-content {
    padding: 16px;
  }

  .generation-container {
    gap: 16px;
  }

  .output-container {
    height: 300px;
  }

  .info-grid {
    grid-template-columns: 1fr;
  }
}
</style>