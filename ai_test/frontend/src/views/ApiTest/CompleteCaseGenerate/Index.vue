<template>
  <div class="api-complete-generate-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="breadcrumb-section">
        <el-breadcrumb separator="/">
          <el-breadcrumb-item>
            <a href="javascript:void(0)" @click="goBack">
              接口管理
            </a>
          </el-breadcrumb-item>
          <el-breadcrumb-item>完整用例生成</el-breadcrumb-item>
        </el-breadcrumb>
      </div>
      <div class="action-section">
        <el-button @click="goBack" plain class="back-button">
          <el-icon><ArrowLeft /></el-icon>
          返回接口管理
        </el-button>
      </div>
    </div>

    <el-card class="interface-info-card">
      <template #header>
        <div class="card-header">
          <span>基础信息</span>
          <div class="header-actions">
            <el-select v-model="testEnvId" placeholder="选择测试环境" filterable style="width: 240px">
              <el-option v-for="env in testEnvOptions" :key="env.value" :label="env.label" :value="env.value" />
            </el-select>
            <el-tag v-if="isAdditionalInfoConfigured" type="success">已配置</el-tag>
            <el-button 
              v-if="!generating && !isCompleted" 
              type="primary" 
              :disabled="!testEnvId" 
              @click="startGeneration"
            >
              <el-icon><MagicStick /></el-icon>
              开始生成
            </el-button>
            <el-button 
              v-if="generating" 
              type="danger" 
              @click="stopGeneration"
            >
              停止生成
            </el-button>
            <el-button 
              v-if="isCompleted" 
              type="success" 
              @click="viewGeneratedCases"
            >
              查看生成的用例
            </el-button>
          </div>
        </div>
      </template>
      <div class="interface-details">
        <div class="detail-item">
          <label>接口名称：</label>
          <span>{{ interfaceInfo.summary || '未命名接口' }}</span>
        </div>
        <div class="detail-item">
          <label>接口路径：</label>
          <code class="interface-path">{{ interfaceInfo.path }}</code>
        </div>
        <div class="detail-item">
          <label>请求方法：</label>
          <el-tag :type="getMethodTagType(interfaceInfo.method)">{{ interfaceInfo.method }}</el-tag>
        </div>
      </div>
      
      <!-- 详细信息：接口信息 -->
      <div class="details-section">
        <el-tabs v-model="activeTab" class="details-tabs" type="card">
          <el-tab-pane label="接口信息" name="interface">
            <json-editor :model-value="interfaceInfo || {}" height="400px" :read-only="true" />
          </el-tab-pane>
          <el-tab-pane label="依赖接口" name="dependency">
            <dependency-manager 
              :project-id="projectId" 
              :interface-id="interfaceId"
              @change="handleDependencyChange"
            />
          </el-tab-pane>
          <el-tab-pane label="高级配置" name="config">
            <div class="tab-actions">
              <el-button @click="loadAdditionalInfoExample">填充示例</el-button>
              <el-button @click="formatAdditionalInfo">格式化</el-button>
              <el-tag :type="isAdditionalInfoValid ? 'success' : 'danger'">
                {{ isAdditionalInfoValid ? 'JSON 合法' : 'JSON 非法' }}
              </el-tag>
            </div>
            <json-editor v-model="additionalInfoText" height="400px" />
          </el-tab-pane>
        </el-tabs>
      </div>
      
      <p class="progress-text">{{ progressText }}</p>
      <el-progress :percentage="progress" :status="progressStatus" :stroke-width="12" />
    </el-card>

    <div class="content-section">
      <div class="progress-section">
        <notification-list :notifications="notifications" @mark-as-read="markNotificationAsRead" @mark-all-as-read="markAllNotificationsAsRead" />
      </div>

      <div class="generation-section">
        <chat-container :messages="chatMessages" @copy="handleCopyMessage" />
      </div>
    </div>
  </div>
</template>

<script setup>
defineOptions({ name: 'ApiCompleteCaseGenerate' })
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, MagicStick } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/index'
import { useProjectStore } from '@/stores/index'
import { getInterfaceDetail } from '@/api/apiTest'
import { getTestEnvironments } from '@/api/test_environment'
import JsonEditor from '@/components/JsonEditor.vue'
import NotificationList from '@/components/NotificationList.vue'
import ChatContainer from '@/components/ChatContainer.vue'
import DependencyManager from '@/components/common/DependencyManager.vue'
const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const projectStore = useProjectStore()

// 路由参数
const projectId = ref(Number(route.params.projectId))
const interfaceId = ref(Number(route.params.interfaceId))

// 数据状态
const interfaceInfo = ref({})
const testEnvOptions = ref([])
const testEnvId = ref('')
const additionalInfoText = ref('')
const activeTab = ref('interface')
const dependencyGroups = ref([])

// 生成状态
const generating = ref(false)
const isCompleted = ref(false)
const hasError = ref(false)
const errorMessage = ref('')
const progress = ref(0)
const progressStatus = ref('')
const progressText = ref('准备生成完整用例...')

// 通知和消息
const notifications = ref([])
const chatMessages = ref([])
const streamingMessageId = ref('')
const currentStreamingMessage = ref(null)

// 计算属性
const isAdditionalInfoConfigured = computed(() => {
  return additionalInfoText.value.trim() !== ''
})

const isAdditionalInfoValid = computed(() => {
  if (!additionalInfoText.value.trim()) return true
  try {
    JSON.parse(additionalInfoText.value)
    return true
  } catch {
    return false
  }
})


// 方法标签类型
const getMethodTagType = (method) => {
  const typeMap = {
    'GET': 'success',
    'POST': 'primary',
    'PUT': 'warning',
    'DELETE': 'danger',
    'PATCH': 'info'
  }
  return typeMap[method] || 'info'
}

// 工具函数
const addMessage = (type, content) => {
  notifications.value.push({ 
    id: `n_${Date.now()}`, 
    type, 
    message: content, 
    timestamp: Date.now(), 
    read: false 
  })
}

const addChatMessage = (role, content, isStreaming = false) => {
  const message = { 
    id: `msg_${Date.now()}_${Math.random().toString(36).slice(2)}`, 
    role, 
    content, 
    timestamp: Date.now(), 
    isStreaming 
  }
  chatMessages.value.push(message)
  return message.id
}

const startStreamingMessage = (role, initialContent = '') => {
  const id = `stream_${Date.now()}_${Math.random().toString(36).slice(2)}`
  const msg = { 
    id, 
    role, 
    content: initialContent, 
    timestamp: Date.now(), 
    isStreaming: true 
  }
  chatMessages.value.push(msg)
  currentStreamingMessage.value = msg
  streamingMessageId.value = id
  return id
}

const updateStreamingMessage = (id, content, isComplete = false) => {
  const idx = chatMessages.value.findIndex(m => m.id === id)
  if (idx !== -1) {
    chatMessages.value[idx].content = content
    chatMessages.value[idx].isStreaming = !isComplete
  }
  if (isComplete) {
    streamingMessageId.value = ''
    currentStreamingMessage.value = null
  }
}

// 页面操作
const goBack = () => {
  // 使用 path 导航，更可靠
  const pid = projectId.value || projectStore.currentProject?.id
  if (pid) {
    router.push(`/project/${pid}/api-management`)
  } else {
    router.back()
  }
}

const clearChat = () => {
  chatMessages.value = []
  streamingMessageId.value = ''
  currentStreamingMessage.value = null
}

// 数据加载
const loadInterfaceDetail = async () => {
  if (!interfaceId.value || !projectId.value) return
  try {
    const resp = await getInterfaceDetail(projectId.value, interfaceId.value)
    interfaceInfo.value = resp?.data || resp || {}
  } catch (e) {
    console.error('获取接口详情失败', e)
    ElMessage.error('加载接口详情失败')
  }
}

const loadTestEnvironments = async () => {
  if (!projectId.value) return
  try {
    const res = await getTestEnvironments(projectId.value, { page: 1, page_size: 50 })
    const list = res?.data?.environments || res?.environments || []
    testEnvOptions.value = list.map(e => ({ label: e.name, value: e.id }))
    if (testEnvOptions.value.length > 0) testEnvId.value = testEnvOptions.value[0].value
  } catch (e) {
    console.error('获取测试环境失败', e)
    ElMessage.error('加载测试环境失败')
  }
}

// 通知管理
const addNotification = (type, message) => {
  notifications.value.push({ 
    id: `n_${Date.now()}_${Math.random().toString(36).slice(2)}`, 
    type, 
    message, 
    timestamp: Date.now(), 
    read: false 
  })
}

// 依赖变化处理
const handleDependencyChange = (groups) => {
  dependencyGroups.value = groups
  addNotification('info', `依赖配置已更新，共 ${groups.length} 个分组`)
}

const markNotificationAsRead = (id) => {
  const n = notifications.value.find(n => n.id === id)
  if (n) n.read = true
}

const markAllNotificationsAsRead = () => { 
  notifications.value.forEach(n => n.read = true) 
}

// 导出和复制
const handleExportChat = () => {
  const content = chatMessages.value.map(m => 
    `[${new Date(m.timestamp).toLocaleString('zh-CN')}] ${m.role}: ${m.content}`
  ).join('\n\n')
  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `完整用例生成记录_${new Date().toLocaleDateString('zh-CN')}.txt`
  a.click()
  URL.revokeObjectURL(url)
}

const handleCopyMessage = (message) => { 
  navigator.clipboard.writeText(message.content).then(() => ElMessage.success('消息已复制')) 
}

// 完整用例生成逻辑
const startGeneration = async () => {
  if (!projectId.value || !interfaceId.value) {
    ElMessage.error('缺少必要参数')
    return
  }
  if (!testEnvId.value) {
    ElMessage.error('请选择测试环境')
    return
  }
  if (!isAdditionalInfoValid.value) {
    ElMessage.error('additional_info JSON 无效，请修正后再试')
    return
  }

  generating.value = true
  isCompleted.value = false
  hasError.value = false
  errorMessage.value = ''
  progress.value = 0
  progressStatus.value = ''
  progressText.value = '准备开始生成...'
  clearChat()
  notifications.value = []

  // 使用完整用例生成的API端点
  const sseUrl = `${import.meta.env.VITE_BASE_API}/api_test/${projectId.value}/interfaces/${interfaceId.value}/generate-complete-test-cases`

  try {
    const token = userStore.token
    if (!token) throw new Error('用户未登录')

    // 使用POST + SSE
    let additionalInfoObj = {}
    const t = (additionalInfoText.value || '').trim()
    if (t) {
      try { 
        additionalInfoObj = JSON.parse(t) 
      } catch { 
        throw new Error('additional_info 不是合法 JSON') 
      }
    }

    const response = await fetch(sseUrl, {
      method: 'POST',
      headers: {
        'Accept': 'text/event-stream',
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ 
        test_id: Number(testEnvId.value), 
        additional_info: additionalInfoObj 
      })
    })

    if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`)

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    let progressValue = 0
    let currentStreamingId = null

    addChatMessage('system', '🚀 开始生成完整用例，正在连接服务器...')
    addNotification('start', '开始生成完整用例')

    while (true) {
      const { done, value } = await reader.read()
      if (done) {
        generating.value = false
        isCompleted.value = true
        progress.value = 100
        progressStatus.value = 'success'
        progressText.value = '生成完成'
        if (currentStreamingId && currentStreamingMessage.value) {
          updateStreamingMessage(currentStreamingId, currentStreamingMessage.value.content, true)
        } else {
          addChatMessage('assistant', '✅ 生成完成！')
        }
        break
      }

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''
      
      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        const data = line.slice(6).trim()
        if (!data) continue
        
        if (data === '[DONE]') {
          generating.value = false
          isCompleted.value = true
          progress.value = 100
          progressStatus.value = 'success'
          progressText.value = '生成完成'
          if (currentStreamingId && currentStreamingMessage.value) {
            updateStreamingMessage(currentStreamingId, currentStreamingMessage.value.content, true)
          } else {
            addChatMessage('assistant', '✅ 生成完成！')
          }
          return
        }
        
        try {
          const payload = JSON.parse(data)
          if (payload.type === 'start') {
            if (!currentStreamingId) {
              currentStreamingId = startStreamingMessage('assistant', `🔄 ${payload.message}\n`)
            }
            addNotification('start', payload.message)
          } else if (payload.type === 'info') {
            progressValue = Math.min(progressValue + 10, 90)
            progress.value = progressValue
            progressText.value = payload.message
            addNotification('info', payload.message)
          } else if (payload.type === 'progress') {
            if (!currentStreamingId) {
              currentStreamingId = startStreamingMessage('assistant', payload.message)
            } else if (currentStreamingMessage.value) {
              currentStreamingMessage.value.content += payload.message
              updateStreamingMessage(currentStreamingId, currentStreamingMessage.value.content, false)
            }
          } else if (payload.type === 'complete') {
            generating.value = false
            isCompleted.value = true
            progress.value = 100
            progressStatus.value = 'success'
            progressText.value = payload.message || '生成完成'
            if (currentStreamingId && currentStreamingMessage.value) {
              updateStreamingMessage(currentStreamingId, currentStreamingMessage.value.content + '\n✅ ' + (payload.message || '生成完成'), true)
            } else {
              addChatMessage('assistant', '✅ ' + (payload.message || '生成完成'))
            }
            addNotification('success', payload.message || '生成完成')
          } else if (payload.type === 'error') {
            generating.value = false
            hasError.value = true
            errorMessage.value = payload.message
            progress.value = 100
            progressStatus.value = 'exception'
            progressText.value = '生成失败'
            addChatMessage('system', `❌ ${payload.message}`)
            addNotification('error', payload.message)
          } else {
            addMessage(payload.type || 'info', payload.message)
          }
        } catch (err) {
          console.error('SSE数据解析失败', err)
          addMessage('error', `数据解析错误：${err.message}`)
          addChatMessage('system', `❌ 数据解析错误：${err.message}`)
        }
      }
    }

  } catch (error) {
    console.error('生成失败', error)
    generating.value = false
    progress.value = 100
    progressStatus.value = 'exception'
    progressText.value = '生成失败'
    hasError.value = true
    errorMessage.value = error.message
    if (currentStreamingMessage.value) {
      currentStreamingMessage.value.content += `\n❌ 生成失败：${error.message}`
      updateStreamingMessage(streamingMessageId.value, currentStreamingMessage.value.content, true)
    } else {
      addChatMessage('system', `❌ 生成失败：${error.message}`)
    }
    ElMessage.error('生成完整用例失败')
  }
}

const stopGeneration = () => {
  generating.value = false
  progress.value = 100
  progressStatus.value = 'exception'
  progressText.value = '生成已停止'
  addMessage('warning', '用户手动停止了生成过程')
  addChatMessage('system', '⚠️ 生成已被用户手动停止')
}

const viewGeneratedCases = () => {
  // 跳转至自动化用例列表（按接口过滤）
  router.push({ 
    name: 'ApiTestAutoCase', 
    query: { interfaceId: interfaceId.value } 
  })
}

// 高级配置操作
const loadAdditionalInfoExample = () => {
  additionalInfoText.value = JSON.stringify({
    description: '完整用例生成配置',
    coverage_level: 'comprehensive',
    include_edge_cases: true,
    test_data_variety: 'high'
  }, null, 2)
}

const formatAdditionalInfo = () => {
  const text = (additionalInfoText.value || '').trim()
  if (!text) return
  try {
    additionalInfoText.value = JSON.stringify(JSON.parse(text), null, 2)
    ElMessage.success('已格式化')
  } catch {
    ElMessage.error('不是合法 JSON，无法格式化')
  }
}

onMounted(() => {
  if (!projectId.value) {
    const p = projectStore.currentProject?.id || JSON.parse(localStorage.getItem('currentProject') || '{}')?.id
    if (p) projectId.value = Number(p)
  }
  loadInterfaceDetail()
  loadTestEnvironments()
})

onUnmounted(() => {
  generating.value = false
})
</script>

<style scoped>
.api-complete-generate-page { 
  padding: 10px; 
  min-height: 100vh; 
}

.page-header { 
  display: flex; 
  justify-content: space-between;
  align-items: center; 
  margin-bottom: 20px; 
}

.header-left { 
  display: flex; 
  align-items: center; 
  gap: 16px; 
}

.back-button { 
  padding: 8px 12px; 
  font-size: 14px; 
}

.back-button:hover { 
  background-color: #ecf5ff; 
}

.title-section h2 { 
  color: #303133; 
  margin: 0 0 4px 0; 
  font-size: 24px; 
  font-weight: 600; 
}

.subtitle { 
  color: #606266; 
  margin: 0; 
  font-size: 14px; 
  font-family: 'Monaco','Menlo','Ubuntu Mono', monospace; 
}

.interface-info-card { 
  margin-bottom: 20px; 
}

.card-header { 
  display: flex; 
  justify-content: space-between; 
  align-items: center; 
  font-weight: 600; 
}

.header-actions { 
  display: flex; 
  gap: 12px; 
}

.interface-details { 
  display: flex; 
  flex-direction: row; 
  gap: 12px; 
  border: 1px solid #e4e7ed; 
  padding: 12px; 
  border-radius: 8px; 
}

.detail-item { 
  display: flex; 
  align-items: center;
  flex: 1; 
}

.detail-item label { 
  font-weight: 600; 
  color: #606266; 
  min-width: 80px; 
  margin-right: 12px; 
}

.interface-path { 
  background: #f5f7fa; 
  padding: 4px 8px; 
  border-radius: 4px; 
  font-family: 'Monaco','Menlo','Ubuntu Mono', monospace; 
  font-size: 12px; 
  color: #606266; 
}

.content-section { 
  display: flex; 
  gap: 20px; 
  width: 100%; 
  height: 800px; 
}

.progress-section { 
  width: 30%; 
  display: flex; 
  flex-direction: column; 
  gap: 20px; 
  height: 800px; 
  overflow-y: auto; 
}

.control-card { 
  margin-bottom: 0; 
}

.control-actions { 
  margin-bottom: 16px; 
}

.progress-text { 
  margin: 8px 0 0 0; 
  font-size: 14px; 
  color: #606266; 
  text-align: center; 
}

.generation-section { 
  width: 70%; 
  display: flex; 
  flex-direction: column; 
  height: 800px; 
  overflow-y: auto; 
}

.chat-wrapper { 
  flex: 1; 
  min-height: 600px; 
  background: white; 
  border-radius: 8px; 
  box-shadow: 0 2px 12px rgba(0,0,0,0.1); 
}

.details-section { 
  display: flex; 
  flex-direction: column; 
  gap: 16px; 
  margin-top: 16px; 
}

.detail-card { }

.detail-grid { 
  display: grid; 
  grid-template-columns: 1fr 1fr; 
  gap: 16px; 
}

.detail-grid .full-row { 
  grid-column: 1 / -1; 
}

.editor-label { 
  font-size: 13px; 
  color: #606266; 
  margin-bottom: 6px; 
}

.details-tabs { 
  margin-top: 8px; 
}

.tab-actions { 
  display: flex; 
  align-items: center; 
  gap: 12px; 
  margin-bottom: 8px; 
}
</style>