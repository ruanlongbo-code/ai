<template>
  <div class="api-case-generate-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="breadcrumb-section">
        <el-breadcrumb separator="/">
          <el-breadcrumb-item>
            <router-link to="/api-test/management">
              接口管理
            </router-link>
          </el-breadcrumb-item>
          <el-breadcrumb-item>{{ generateTypeText }}生成</el-breadcrumb-item>
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
            <el-select v-if="generateType === 'complete'" v-model="testEnvId" placeholder="选择测试环境" filterable style="width: 240px">
              <el-option v-for="env in testEnvOptions" :key="env.value" :label="env.label" :value="env.value" />
            </el-select>
            <el-button 
              v-if="!generating && !isCompleted" 
              type="primary" 
              :disabled="!interfaceInfo.id || (generateType === 'complete' && !testEnvId)"
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
        <div class="detail-item" v-if="interfaceInfo.description">
          <label>接口描述：</label>
          <span>{{ interfaceInfo.description }}</span>
        </div>
      </div>
      
      <!-- 详细信息：接口信息 -->
      <div class="details-section">
        <el-tabs v-model="activeTab" class="details-tabs" type="card">
          <el-tab-pane label="接口信息" name="interface">
            <json-editor :model-value="interfaceInfo || {}" height="400px" :read-only="true" />
          </el-tab-pane>
          <el-tab-pane label="前置依赖" name="dependency">
            <dependency-manager
              :project-id="parseInt(projectId)"
              :interface-id="parseInt(interfaceId)"
              :readonly="false"
              @change="handleDependencyChange"
            />
          </el-tab-pane>
          <el-tab-pane v-if="generateType === 'complete'" label="高级配置" name="config">
            <div class="tab-actions">
              <el-button size="small" @click="loadAdditionalInfoExample">加载示例</el-button>
              <el-button size="small" @click="formatAdditionalInfo">格式化</el-button>
              <el-button size="small" @click="clearAdditionalInfo">清空</el-button>
            </div>
            <el-input
              v-model="additionalInfoText"
              type="textarea"
              :rows="15"
              placeholder="请输入额外的生成配置信息（JSON格式）..."
              class="additional-info-input"
            />
          </el-tab-pane>
        </el-tabs>
      </div>
    </el-card>

    <!-- 生成进度和结果 -->
    <!-- 内容区域 - 左右布局 -->
    <div class="content-section">
      <!-- 左侧：进度和通知 (30%) -->
      <div class="progress-section">
        <!-- 生成控制按钮 -->
        <el-card class="control-card">
          <template #header>
            <div class="card-header">
              <span>生成进度</span>
            </div>
          </template>
          
          <!-- 进度条 -->
          <div v-if="generating || isCompleted" class="progress-container">
            <el-progress 
              :percentage="progress" 
              :status="progressStatus"
              :stroke-width="8"
              :show-text="true"
            />
            <p class="progress-text">{{ progressText }}</p>
          </div>
          
          <div v-else class="no-progress">
            <p>点击上方"开始生成"按钮开始生成{{ generateTypeText }}</p>
          </div>
        </el-card>

        <!-- 通知列表 -->
        <div class="notification-section" v-if="notifications.length > 0">
          <NotificationList
            :notifications="notifications"
            @clear="clearNotifications"
            @mark-read="markNotificationAsRead"
            @mark-all-read="markAllNotificationsAsRead"
          />
        </div>
      </div>

      <!-- 右侧：生成数据 (70%) -->
      <div class="generation-section">
        <!-- 实时生成输出 - ChatGPT风格 -->
        <div class="chat-wrapper">
          <ChatContainer
            :messages="chatMessages"
            :title="'AI 用例生成助手'"
            :show-header="false"
            :show-message-actions="true"
            :empty-text="`点击左侧开始生成${generateTypeText}按钮，AI助手将为您生成测试用例`"
            :is-loading="generating"
            :streaming-message-id="streamingMessageId"
            :auto-scroll="true"
            @clear-messages="clearChatMessages"
            @export-messages="handleExportChat"
            @copy-message="handleCopyMessage"
            @regenerate-message="handleRegenerateMessage"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineOptions({ name: 'ApiCaseGenerate' })
import { ref, onMounted, onUnmounted, onActivated, onDeactivated, nextTick ,computed} from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Loading, CircleCheck, CircleClose, MagicStick } from '@element-plus/icons-vue'
import { getInterfaceDetail,  } from '@/api/apiTest'
import { getTestEnvironmentDetail,getTestEnvironments } from '@/api/test_environment'
import { useUserStore } from '@/stores'
import ChatContainer from '@/components/ChatContainer.vue'
import NotificationList from '@/components/NotificationList.vue'
import JsonEditor from '@/components/JsonEditor.vue'
import DependencyManager from '@/components/common/DependencyManager.vue'

const userStore = useUserStore()
const route = useRoute()
const router = useRouter()

// 路由参数
const projectId = computed(() => route.params.projectId)
const interfaceId = computed(() => route.params.interfaceId)
const generateType = computed(() => route.query.type || 'basic')
const testEnvId = ref(route.query.testEnvId)

// 响应式数据
const interfaceInfo = ref({})
const testEnvironmentName = ref('')
const generating = ref(false)
const isCompleted = ref(false)
const hasError = ref(false)
const errorMessage = ref('')
const messages = ref([])
const messagesContainer = ref(null)

// 新增：标签页相关
const activeTab = ref('interface')
const additionalInfoText = ref('')

// 新增：测试环境选项
const testEnvOptions = ref([])

// 新增：进度相关数据
const progress = ref(0)
const progressStatus = ref('')
const progressText = ref('')

// 新增：ChatGPT风格的消息数据
const chatMessages = ref([])
const streamingMessageId = ref('')
const currentStreamingMessage = ref(null)

// 新增：进度列表数据
const notifications = ref([])
const notificationIdCounter = ref(0)

// 新增：依赖数据
const dependencyGroups = ref([])

// 计算属性
const generateTypeText = computed(() => {
  return generateType.value === 'basic' ? '基础用例' : '完整用例'
})

// 获取HTTP方法标签类型
const getMethodTagType = (method) => {
  const typeMap = {
    'GET': 'primary',
    'POST': 'success',
    'PUT': 'warning',
    'PATCH': 'warning',
    'DELETE': 'danger'
  }
  return typeMap[method] || 'info'
}

// 格式化时间
const formatTime = (timestamp) => {
  return new Date(timestamp).toLocaleTimeString()
}

// 返回上一页
const goBack = () => {
  router.push({
    name: 'ApiManagement',
    params: { projectId: projectId.value }
  })
}

// 获取接口详情
const fetchInterfaceDetail = async () => {
  try {
    const response = await getInterfaceDetail(projectId.value, interfaceId.value)
    interfaceInfo.value = response.data
  } catch (error) {
    console.error('获取接口详情失败:', error)
    ElMessage.error('获取接口详情失败')
  }
}

// 获取测试环境名称
const fetchTestEnvironmentName = async () => {
  if (!testEnvId.value) return
  
  try {
    const response = await getTestEnvironmentDetail(projectId.value, testEnvId.value)
    testEnvironmentName.value = response.data.name
  } catch (error) {
    console.error('获取测试环境失败:', error)
  }
}

// 添加消息
const addMessage = (type, content) => {
  messages.value.push({
    type,
    content,
    timestamp: Date.now()
  })
  
  // 自动滚动到底部
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

// 清空消息
const clearMessages = () => {
  messages.value = []
}

// 开始生成
const startGeneration = async () => {
  if (!interfaceInfo.value.id) {
    ElMessage.error('接口信息未加载完成')
    return
  }

  generating.value = true
  isCompleted.value = false
  hasError.value = false
  errorMessage.value = ''
  messages.value = []
  
  // 重置进度相关数据
  progress.value = 0
  progressStatus.value = ''
  progressText.value = '准备开始生成...'
  
  // 重置聊天消息和通知
  chatMessages.value = []
  notifications.value = []
  streamingMessageId.value = ''
  currentStreamingMessage.value = null

  // 构建SSE请求URL
  let sseUrl = ''
  let requestBody = {}
  
  if (generateType.value === 'basic') {
    // 生成基础用例不需要测试环境ID
    sseUrl = `${import.meta.env.VITE_BASE_API}/api_test/${projectId.value}/interfaces/${interfaceId.value}/generate-base-cases`
  } else {
    // 生成完整用例需要通过POST请求体传递test_id参数
    sseUrl = `${import.meta.env.VITE_BASE_API}/api_test/${projectId.value}/interfaces/${interfaceId.value}/generate-complete-test-cases`
    if (testEnvId.value) {
      requestBody.test_id = Number(testEnvId.value)
    }
  }

  try {
    const token = userStore.token
    if (!token) {
      throw new Error('用户未登录')
    }

    const response = await fetch(sseUrl, {
      method: 'POST',
      headers: {
        'Accept': 'text/event-stream',
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(requestBody)
    })

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    let progressValue = 0
    let currentStreamingId = null

    // 添加开始消息
    addChatMessage('system', `🚀 开始生成${generateTypeText.value}，请稍候...`, false)
    addNotification('start', `开始生成${generateTypeText.value}`)

    while (true) {
      const { done, value } = await reader.read()
      
      if (done) {
        // 完成生成
        generating.value = false
        isCompleted.value = true
        progress.value = 100
        progressStatus.value = 'success'
        progressText.value = `${generateTypeText.value}生成完成`
        
        // 结束流式消息
        if (currentStreamingId && currentStreamingMessage.value) {
          updateStreamingMessage(currentStreamingId, currentStreamingMessage.value.content, true)
        } else {
          addChatMessage('assistant', `✅ ${generateTypeText.value}生成完成！所有用例已准备就绪。`, false)
        }
        return
      }

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6).trim()
          
          if (data === '[DONE]') {
            // 完成生成
            generating.value = false
            isCompleted.value = true
            progress.value = 100
            progressStatus.value = 'success'
            progressText.value = `${generateTypeText.value}生成完成`
            
            // 结束流式消息
            if (currentStreamingId && currentStreamingMessage.value) {
              updateStreamingMessage(currentStreamingId, currentStreamingMessage.value.content, true)
            } else {
              addChatMessage('assistant', `✅ ${generateTypeText.value}生成完成！所有用例已准备就绪。`, false)
            }
            return
          }

          try {
            const parsedData = JSON.parse(data)

            // 处理不同类型的消息
            if (parsedData.type === 'start') {
              // 开始流式消息，创建一个可以持续更新的消息
              if (!currentStreamingId) {
                currentStreamingId = startStreamingMessage('assistant', `🔄 ${parsedData.message}\n`)
              }
              // 添加到进度列表
              addNotification('start', parsedData.message)
            } else if (parsedData.type === 'info') {
              // 更新进度
              progressValue = Math.min(progressValue + 10, 90)
              progress.value = progressValue
              progressText.value = parsedData.message

              // info 类型消息只添加到进度列表，不显示在流式输出中
              addNotification('info', parsedData.message)
            } else if (parsedData.type === 'progress') {
              // 处理流式内容 - 直接追加到当前消息（保持当前方式）
              if (!currentStreamingId) {
                currentStreamingId = startStreamingMessage('assistant', parsedData.message)
              } else {
                // 追加内容到当前流式消息
                if (currentStreamingMessage.value) {
                  currentStreamingMessage.value.content += parsedData.message
                  updateStreamingMessage(currentStreamingId, currentStreamingMessage.value.content, false)
                }
              }
            } else {
              // 其他类型消息，添加到旧的消息列表（兼容）
              addMessage(parsedData.type || 'info', parsedData.message)
            }

          } catch (error) {
            console.error('解析SSE数据失败:', error)
            addMessage('error', `数据解析错误：${error.message}`)
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
    hasError.value = true
    errorMessage.value = error.message

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

// 停止生成
const stopGeneration = () => {
  generating.value = false
  progress.value = 100
  progressStatus.value = 'exception'
  progressText.value = '生成已停止'
  addMessage('warning', '用户手动停止了生成过程')
  addChatMessage('system', '⚠️ 生成已被用户手动停止', false)
}

// 查看生成的用例
const viewGeneratedCases = () => {
  if (generateType.value === 'basic') {
    // 跳转到基础用例列表
    router.push({
      name: 'ApiTestBaseCase',
      params: { projectId: projectId.value },
      query: { interfaceId: interfaceId.value }
    })
  } else {
    // 跳转到测试用例列表
    router.push({
      name: 'ApiTestCases',
      params: { projectId: projectId.value },
      query: { interfaceId: interfaceId.value }
    })
  }
}

// ChatGPT风格消息相关方法
const addChatMessage = (role, content, isStreaming = false) => {
  const message = {
    id: `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    role,
    content,
    timestamp: Date.now(),
    isStreaming
  }
  chatMessages.value.push(message)
  return message.id
}

const startStreamingMessage = (role, initialContent = '') => {
  const messageId = `streaming_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  const message = {
    id: messageId,
    role,
    content: initialContent,
    timestamp: Date.now(),
    isStreaming: true
  }
  
  chatMessages.value.push(message)
  currentStreamingMessage.value = message
  streamingMessageId.value = messageId
  
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

const clearChatMessages = () => {
  chatMessages.value = []
  streamingMessageId.value = ''
  currentStreamingMessage.value = null
}

const handleExportChat = () => {
  const chatContent = chatMessages.value.map(msg => {
    const time = new Date(msg.timestamp).toLocaleString('zh-CN')
    const role = msg.role === 'user' ? '用户' : msg.role === 'assistant' ? 'AI助手' : '系统'
    return `[${time}] ${role}: ${msg.content}`
  }).join('\n\n')
  
  const blob = new Blob([chatContent], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${generateTypeText.value}生成记录_${new Date().toLocaleDateString('zh-CN')}.txt`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
  
  ElMessage.success('聊天记录已导出')
}

const handleCopyMessage = (message) => {
  navigator.clipboard.writeText(message.content).then(() => {
    ElMessage.success('消息已复制到剪贴板')
  }).catch(() => {
    ElMessage.error('复制失败')
  })
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

// 加载测试环境列表
const loadTestEnvironments = async () => {
  if (generateType.value !== 'complete') return
  
  try {
    const response = await getTestEnvironments(projectId.value)
    testEnvOptions.value = response.data.map(env => ({
      label: env.name,
      value: env.id
    }))
  } catch (error) {
    console.error('加载测试环境失败:', error)
    ElMessage.error('加载测试环境失败')
  }
}

// 高级配置操作
const loadAdditionalInfoExample = () => {
  additionalInfoText.value = JSON.stringify({
    description: '基础用例生成配置',
    coverage_level: 'basic',
    include_edge_cases: false,
    test_data_variety: 'standard'
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

const clearAdditionalInfo = () => {
  additionalInfoText.value = ''
  ElMessage.success('已清空')
}

// 依赖变化处理
const handleDependencyChange = (groups) => {
  dependencyGroups.value = groups
  console.log('依赖配置已更新:', groups)
}

// 组件挂载时获取数据
onMounted(() => {
  fetchInterfaceDetail()
  loadTestEnvironments()
  if (generateType.value === 'complete') {
    fetchTestEnvironmentName()
  }
})

onActivated(() => {
  nextTick(() => {})
})

onDeactivated(() => {})

// 组件卸载时清理资源
onUnmounted(() => {
  generating.value = false
})
</script>

<style scoped>
.api-case-generate-page {
  padding: 10px;
  min-height: 100vh;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.breadcrumb-section {
  flex: 1;
}

.action-section {
  display: flex;
  gap: 12px;
}

.back-button {
  padding: 8px 12px;
  font-size: 14px;
}

.back-button:hover {
  background-color: #ecf5ff;
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
  margin-bottom: 20px;
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
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 12px;
  color: #606266;
}

.details-section {
  margin-top: 20px;
}

.details-tabs {
  margin-top: 16px;
}

.tab-actions {
  margin-bottom: 16px;
}

.additional-info-input {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 12px;
}

/* 内容区域 - 左右布局 */
.content-section {
  display: flex;
  gap: 20px;
  width: 100%;
  height: 800px;
}

/* 左侧：进度和通知 (30%) */
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

.no-progress {
  text-align: center;
  color: #909399;
  padding: 20px;
  font-size: 14px;
}

.progress-container {
  margin-top: 16px;
}

.progress-text {
  margin: 8px 0 0 0;
  font-size: 14px;
  color: #606266;
  text-align: center;
}

.notification-section {
  flex: 1;
}

/* 右侧：生成数据 (70%) */
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
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.generation-card {
  margin-bottom: 20px;
}

.generation-status {
  text-align: center;
  padding: 40px 20px;
}

.status-waiting,
.status-generating,
.status-completed,
.status-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.status-waiting p,
.status-generating p,
.status-completed p,
.status-error p {
  margin: 0;
  font-size: 16px;
  color: #606266;
}

.error-message {
  color: #f56c6c !important;
  font-size: 14px !important;
  background: #fef0f0;
  padding: 8px 12px;
  border-radius: 4px;
  border: 1px solid #fbc4c4;
}

.rotating {
  animation: rotate 2s linear infinite;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.message-container {
  margin-top: 20px;
  border-top: 1px solid #e4e7ed;
  padding-top: 20px;
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  font-weight: 600;
  color: #303133;
}

.messages-list {
  max-height: 400px;
  overflow-y: auto;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  background: #fafafa;
}

.message-item {
  display: flex;
  padding: 8px 12px;
  border-bottom: 1px solid #f0f0f0;
  font-size: 14px;
}

.message-item:last-child {
  border-bottom: none;
}

.message-time {
  min-width: 80px;
  color: #909399;
  font-size: 12px;
  margin-right: 12px;
}

.message-content {
  flex: 1;
  word-break: break-word;
}

.message-info .message-content {
  color: #606266;
}

.message-success .message-content {
  color: #67c23a;
  font-weight: 600;
}

.message-error .message-content {
  color: #f56c6c;
  font-weight: 600;
}

.message-warning .message-content {
  color: #e6a23c;
  font-weight: 600;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .content-section {
    flex-direction: column;
  }
  
  .progress-section,
  .generation-section {
    width: 100%;
  }
  
  .chat-wrapper {
    min-height: 400px;
  }
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }

  .header-left {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .interface-details {
    gap: 8px;
  }

  .detail-item {
    flex-direction: column;
    align-items: flex-start;
  }

  .detail-item label {
    min-width: auto;
    margin-right: 0;
    margin-bottom: 4px;
  }
  
  .content-section {
    gap: 12px;
  }
}
</style>