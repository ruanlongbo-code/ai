<template>
  <div class="test-result-card">
    <!-- 基本信息卡片 -->
    <div class="result-card basic-info-card">
      <div class="card-header">
        <div class="status-indicator" :class="getStatusClass(result.status)">
          <component :is="getStatusIcon(result.status)" class="status-icon" />
          <span class="status-text">{{ getStatusText(result.status) }}</span>
        </div>
        <div class="case-name">{{ result.case_name || '未知用例' }}</div>
      </div>
      
      <div class="card-content">
        <div class="info-grid">
          <div class="info-item">
            <div class="info-label">开始时间</div>
            <div class="info-value">{{ formatTime(result.start_time) }}</div>
          </div>
          <div class="info-item">
            <div class="info-label">结束时间</div>
            <div class="info-value">{{ formatTime(result.end_time) }}</div>
          </div>
          <div class="info-item">
            <div class="info-label">执行耗时</div>
            <div class="info-value duration">{{ formatDuration(result.duration) }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 错误信息卡片 -->
    <div v-if="result.error_message" class="result-card error-card">
      <div class="card-header">
        <el-icon class="error-icon"><Warning /></el-icon>
        <span class="card-title">错误信息</span>
      </div>
      <div class="card-content">
        <div class="error-message">{{ result.error_message }}</div>
      </div>
    </div>

    <!-- 运行日志卡片 -->
    <div v-if="result.logs && result.logs.length > 0" class="result-card logs-card">
      <div class="card-header">
        <el-icon class="logs-icon"><Document /></el-icon>
        <span class="card-title">运行日志</span>
        <div class="logs-count">{{ result.logs.length }} 条</div>
      </div>
      <div class="card-content">
        <div class="logs-container">
          <div 
            v-for="(log, index) in result.logs" 
            :key="index" 
            class="log-item"
            :class="getLogLevelClass(log.level)"
          >
            <div class="log-timestamp">{{ formatLogTime(log.timestamp) }}</div>
            <div class="log-level">{{ log.level?.toUpperCase() || 'INFO' }}</div>
            <div class="log-message">{{ log.message }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 请求信息卡片 -->
    <div v-if="result.request_info && result.request_info.length > 0" class="result-card request-card">
      <div class="card-header">
        <el-icon class="request-icon"><Upload /></el-icon>
        <span class="card-title">接口请求与响应详情</span>
        <span v-if="result.request_info.length > 1" class="request-count">
          ({{ result.request_info.length }} 个请求)
        </span>
      </div>
      <div class="card-content">
        <div 
          v-for="(request, index) in result.request_info" 
          :key="index" 
          class="request-info"
          :class="{ 'multiple-requests': result.request_info.length > 1 }"
        >
          <div v-if="result.request_info.length > 1" class="request-index">
            请求 {{ index + 1 }}
          </div>
          
          <!-- 请求基本信息 - 一行显示 -->
          <div class="request-summary-line">
            <span class="method-tag" :class="getMethodClass(request.method)">
              {{ request.method || 'GET' }}
            </span>
            <span class="request-url-inline">{{ request.url || '-' }}</span>
            <div class="status-code-inline" :class="getStatusCodeClass(request.status_code)">
              {{ request.status_code || '-' }}
            </div>
          </div>
          
          <!-- 请求响应详情 - Tabs 展示 -->
          <div class="request-response-tabs">
            <el-tabs v-model="activeTab" type="card" class="config-tabs">
              <!-- 请求头 Tab -->
              <el-tab-pane name="headers">
                <template #label>
                  <div class="tab-label">
                    <el-icon><Document /></el-icon>
                    <span>请求头</span>
                    <span v-if="request.headers && Object.keys(request.headers).length > 0" class="tab-count">
                      {{ Object.keys(request.headers).length }}
                    </span>
                  </div>
                </template>
                <div class="config-section">
                  <div class="section-header">
                    <h4>HTTP 请求头</h4>
                    <p>显示发送请求时的所有HTTP头信息</p>
                  </div>
                  <div class="tab-content">
                    <div v-if="request.headers && Object.keys(request.headers).length > 0" class="headers-container">
                      <div 
                        v-for="(value, key) in request.headers" 
                        :key="key" 
                        class="header-item"
                      >
                        <span class="header-key">{{ key }}:</span>
                        <span class="header-value">{{ value }}</span>
                      </div>
                    </div>
                    <div v-else class="empty-content">
                      <el-icon><Document /></el-icon>
                      <span>无请求头</span>
                    </div>
                  </div>
                </div>
              </el-tab-pane>

              <!-- 请求参数 Tab -->
              <el-tab-pane name="params">
                <template #label>
                  <div class="tab-label">
                    <el-icon><List /></el-icon>
                    <span>请求参数</span>
                    <span v-if="request.params && Object.keys(request.params).length > 0" class="tab-count">
                      {{ Object.keys(request.params).length }}
                    </span>
                  </div>
                </template>
                <div class="config-section">
                  <div class="section-header">
                    <h4>请求参数</h4>
                    <p>显示URL参数和表单参数信息</p>
                  </div>
                  <div class="tab-content">
                    <div v-if="request.params && Object.keys(request.params).length > 0" class="params-container">
                      <pre class="json-content">{{ formatJson(request.params) }}</pre>
                    </div>
                    <div v-else class="empty-content">
                      <el-icon><List /></el-icon>
                      <span>无请求参数</span>
                    </div>
                  </div>
                </div>
              </el-tab-pane>

              <!-- 请求体 Tab -->
              <el-tab-pane name="body">
                <template #label>
                  <div class="tab-label">
                    <el-icon><EditPen /></el-icon>
                    <span>请求体</span>
                  </div>
                </template>
                <div class="config-section">
                  <div class="section-header">
                    <h4>请求体内容</h4>
                    <p>显示POST/PUT等请求的body数据</p>
                  </div>
                  <div class="tab-content">
                    <div v-if="request.body && (typeof request.body === 'object' ? Object.keys(request.body).length > 0 : request.body)" class="body-container">
                      <pre class="json-content">{{ formatJson(request.body) }}</pre>
                    </div>
                    <div v-else class="empty-content">
                      <el-icon><EditPen /></el-icon>
                      <span>无请求体</span>
                    </div>
                  </div>
                </div>
              </el-tab-pane>

              <!-- 响应体 Tab -->
              <el-tab-pane name="response">
                <template #label>
                  <div class="tab-label">
                    <el-icon><DataBoard /></el-icon>
                    <span>响应体</span>
                  </div>
                </template>
                <div class="config-section">
                  <div class="section-header">
                    <h4>响应详情</h4>
                    <p>显示服务器返回的响应信息</p>
                  </div>
                  <div class="tab-content">
                    <!-- 响应头 -->
                    <div v-if="request.response_headers && Object.keys(request.response_headers).length > 0" class="response-headers-section">
                      <div class="section-subtitle">
                        <el-icon><Document /></el-icon>
                        响应头 ({{ Object.keys(request.response_headers).length }} 个)
                      </div>
                      <div class="headers-container">
                        <div 
                          v-for="(value, key) in request.response_headers" 
                          :key="key" 
                          class="header-item"
                        >
                          <span class="header-key">{{ key }}:</span>
                          <span class="header-value">{{ value }}</span>
                        </div>
                      </div>
                    </div>
                    
                    <!-- 响应体 -->
                    <div v-if="request.response_body" class="response-body-container">
                      <div class="section-subtitle">
                        <el-icon><DataBoard /></el-icon>
                        响应体
                      </div>
                      <pre class="json-content">{{ formatResponseBody(request.response_body) }}</pre>
                    </div>

                    <div v-if="!request.response_body && (!request.response_headers || Object.keys(request.response_headers).length === 0)" class="empty-content">
                      <el-icon><DataBoard /></el-icon>
                      <span>无响应数据</span>
                    </div>
                  </div>
                </div>
              </el-tab-pane>

              <!-- 文件上传 Tab (如果有文件上传) -->
              <el-tab-pane v-if="request.files && Object.keys(request.files).length > 0" name="files">
                <template #label>
                  <div class="tab-label">
                    <el-icon><UploadFilled /></el-icon>
                    <span>文件上传</span>
                    <span class="tab-count">{{ Object.keys(request.files).length }}</span>
                  </div>
                </template>
                <div class="config-section">
                  <div class="section-header">
                    <h4>上传文件</h4>
                    <p>显示请求中包含的文件信息</p>
                  </div>
                  <div class="tab-content">
                    <div class="files-container">
                      <pre class="json-content">{{ formatJson(request.files) }}</pre>
                    </div>
                  </div>
                </div>
              </el-tab-pane>
            </el-tabs>
          </div>

          <div v-if="result.request_info.length > 1 && index < result.request_info.length - 1" class="request-separator"></div>
        </div>
      </div>
    </div>

    <!-- 运行中状态 -->
    <div v-if="result.status === 'running'" class="result-card running-card">
      <div class="card-header">
        <el-icon class="running-icon animate-spin"><Loading /></el-icon>
        <span class="card-title">正在运行中...</span>
      </div>
      <div class="card-content">
        <div class="running-message">
          用例正在执行中，请稍候...
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { 
  CircleCheck, 
  CircleClose, 
  Clock, 
  Warning, 
  Document, 
  Upload, 
  Download, 
  Loading,
  Setting,
  List,
  EditPen,
  UploadFilled,
  DataBoard
} from '@element-plus/icons-vue'

// Props
const props = defineProps({
  result: {
    type: Object,
    required: true,
    default: () => ({
      case_run_id: null,
      case_id: null,
      case_name: '',
      status: 'pending',
      duration: null,
      start_time: null,
      end_time: null,
      error_message: null,
      logs: [],
      case_data: {},
      request_info: []
    })
  }
})

// 添加activeTab响应式数据
const activeTab = ref('response')

// 状态相关方法
const getStatusClass = (status) => {
  const statusMap = {
    'success': 'status-success',
    'failed': 'status-failed',
    'running': 'status-running',
    'pending': 'status-pending'
  }
  return statusMap[status] || 'status-pending'
}

const getStatusIcon = (status) => {
  const iconMap = {
    'success': CircleCheck,
    'failed': CircleClose,
    'running': Loading,
    'pending': Clock
  }
  return iconMap[status] || Clock
}

const getStatusText = (status) => {
  const textMap = {
    'success': '执行成功',
    'failed': '执行失败',
    'error': '执行错误',
    'skip': '跳过执行'
  }
  return textMap[status] || '未知状态'
}

// 时间格式化
const formatTime = (timeString) => {
  if (!timeString) return '-'
  const date = new Date(timeString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

const formatLogTime = (timeString) => {
  if (!timeString) return ''
  const date = new Date(timeString)
  return date.toLocaleTimeString('zh-CN')
}

const formatDuration = (duration) => {
  if (!duration && duration !== 0) return '-'
  if (duration < 1000) {
    return `${duration}ms`
  } else {
    return `${(duration / 1000).toFixed(2)}s`
  }
}

// 日志级别样式
const getLogLevelClass = (level) => {
  const levelMap = {
    'error': 'log-error',
    'warn': 'log-warn',
    'info': 'log-info',
    'debug': 'log-debug'
  }
  return levelMap[level?.toLowerCase()] || 'log-info'
}

// HTTP方法样式
const getMethodClass = (method) => {
  const methodMap = {
    'GET': 'method-get',
    'POST': 'method-post',
    'PUT': 'method-put',
    'DELETE': 'method-delete',
    'PATCH': 'method-patch'
  }
  return methodMap[method?.toUpperCase()] || 'method-default'
}

// 状态码样式
const getStatusCodeClass = (statusCode) => {
  if (!statusCode) return 'status-code-default'
  const code = parseInt(statusCode)
  if (code >= 200 && code < 300) return 'status-code-success'
  if (code >= 400 && code < 500) return 'status-code-client-error'
  if (code >= 500) return 'status-code-server-error'
  return 'status-code-default'
}

// JSON格式化
const formatJson = (data) => {
  if (!data) return ''
  try {
    if (typeof data === 'string') {
      return JSON.stringify(JSON.parse(data), null, 2)
    }
    return JSON.stringify(data, null, 2)
  } catch (e) {
    return data.toString()
  }
}

// 调试：打印接收到的数据
console.log('TestResultCard - 接收到的result数据:', props.result)
if (props.result && props.result.request_info) {
  console.log('TestResultCard - request_info数据:', props.result.request_info)
  props.result.request_info.forEach((req, index) => {
    console.log(`TestResultCard - 请求${index + 1}:`, req)
    console.log(`TestResultCard - 请求${index + 1} headers:`, req.headers)
    console.log(`TestResultCard - 请求${index + 1} body:`, req.body)
  })
}

const formatResponseBody = (body) => {
  if (!body) return ''
  try {
    if (typeof body === 'string') {
      const parsed = JSON.parse(body)
      return JSON.stringify(parsed, null, 2)
    }
    return JSON.stringify(body, null, 2)
  } catch (e) {
    const bodyStr = body.toString()
    return bodyStr.length > 1000 ? bodyStr.substring(0, 1000) + '...' : bodyStr
  }
}

// 文件大小格式化
const formatBytes = (bytes) => {
  if (!bytes && bytes !== 0) return '-'
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  if (bytes === 0) return '0 Bytes'
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i]
}
</script>

<style scoped>
.test-result-card {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 0;
  max-width: 100%;
}

.result-card {
  background: #ffffff;
  border-radius: 16px;
  border: 1px solid #e5e7eb;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1), 0 1px 2px rgba(0, 0, 0, 0.06);
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
}

.result-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #3b82f6, #8b5cf6, #06b6d4);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.result-card:hover {
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1), 0 4px 6px rgba(0, 0, 0, 0.05);
  transform: translateY(-2px);
  border-color: #d1d5db;
}

.result-card:hover::before {
  opacity: 1;
}

.card-header {
  display: flex;
  align-items: center;
  padding: 20px 24px;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-bottom: 1px solid #e5e7eb;
  gap: 12px;
  position: relative;
}

.card-header::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 24px;
  right: 24px;
  height: 1px;
  background: linear-gradient(90deg, transparent, #e5e7eb, transparent);
}

.card-title {
  font-weight: 600;
  font-size: 16px;
  color: #111827;
  letter-spacing: -0.025em;
}

.card-content {
  padding: 24px;
  background: #ffffff;
}

/* 状态指示器 */
.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border-radius: 24px;
  font-weight: 600;
  font-size: 14px;
  letter-spacing: -0.025em;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  transition: all 0.2s ease;
}

.status-indicator:hover {
  transform: scale(1.02);
}

.status-success {
  background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
  color: #065f46;
  border: 1px solid #a7f3d0;
}

.status-failed {
  background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
  color: #991b1b;
  border: 1px solid #fca5a5;
}

.status-running {
  background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
  color: #92400e;
  border: 1px solid #fcd34d;
}

.status-pending {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  color: #475569;
  border: 1px solid #cbd5e1;
}

.status-icon {
  width: 16px;
  height: 16px;
}

.case-name {
  font-size: 20px;
  font-weight: 700;
  color: #111827;
  flex: 1;
  letter-spacing: -0.025em;
  line-height: 1.2;
}

/* 信息网格 */
.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 20px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 16px;
  background: linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%);
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  transition: all 0.2s ease;
}

.info-item:hover {
  background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.info-label {
  font-size: 12px;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.8px;
}

.info-value {
  font-size: 15px;
  color: #111827;
  font-weight: 600;
  letter-spacing: -0.025em;
}

.duration {
  color: #059669;
  font-family: 'SF Mono', 'Monaco', 'Menlo', monospace;
  background: linear-gradient(135deg, #ecfdf5, #d1fae5);
  padding: 4px 8px;
  border-radius: 6px;
  display: inline-block;
}

/* 错误信息 */
.error-card {
  border-left: 4px solid #ef4444;
}

.error-card .card-header {
  background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
  border-bottom-color: #fca5a5;
}

.error-icon {
  color: #dc2626;
  width: 20px;
  height: 20px;
}

.error-message {
  background: linear-gradient(135deg, #fef2f2 0%, #fef7f7 100%);
  border: 1px solid #fca5a5;
  border-radius: 12px;
  padding: 16px;
  color: #991b1b;
  font-family: 'SF Mono', 'Monaco', 'Menlo', monospace;
  font-size: 13px;
  line-height: 1.6;
  box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.05);
}

/* 日志 */
.logs-card {
  border-left: 4px solid #3b82f6;
}

.logs-card .card-header {
  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
  border-bottom-color: #93c5fd;
}

.logs-icon {
  color: #2563eb;
  width: 20px;
  height: 20px;
}

.logs-count {
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  color: white;
  padding: 4px 12px;
  border-radius: 16px;
  font-size: 12px;
  font-weight: 600;
  margin-left: auto;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.logs-container {
  max-height: 320px;
  overflow-y: auto;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  background: #f8fafc;
}

.log-item {
  display: grid;
  grid-template-columns: auto auto 1fr;
  gap: 16px;
  padding: 12px 16px;
  border-bottom: 1px solid #f1f5f9;
  font-family: 'SF Mono', 'Monaco', 'Menlo', monospace;
  font-size: 12px;
  align-items: center;
  transition: background-color 0.2s ease;
}

.log-item:hover {
  background: #f1f5f9;
}

.log-item:last-child {
  border-bottom: none;
}

.log-timestamp {
  color: #64748b;
  white-space: nowrap;
  font-weight: 500;
}

.log-level {
  font-weight: 700;
  padding: 3px 8px;
  border-radius: 6px;
  font-size: 10px;
  text-align: center;
  min-width: 55px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.log-error .log-level {
  background: linear-gradient(135deg, #fecaca, #fca5a5);
  color: #991b1b;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.log-warn .log-level {
  background: linear-gradient(135deg, #fed7aa, #fcd34d);
  color: #92400e;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.log-info .log-level {
  background: linear-gradient(135deg, #bfdbfe, #93c5fd);
  color: #1e40af;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.log-debug .log-level {
  background: linear-gradient(135deg, #e5e7eb, #d1d5db);
  color: #374151;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.log-message {
  color: #111827;
  word-break: break-word;
  line-height: 1.5;
}

/* 请求信息卡片优化 */
.request-card {
  border: 2px solid #409eff;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.15);
  background: linear-gradient(135deg, #ffffff 0%, #f8fbff 100%);
}

.request-card .card-header {
  background: linear-gradient(135deg, #409eff 0%, #67c23a 100%);
  color: white;
  padding: 16px 20px;
  border-radius: 8px 8px 0 0;
  margin: -1px -1px 0 -1px;
}

.request-card .card-title {
  font-size: 16px;
  font-weight: 600;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
  color: white;
}

.request-icon {
  color: white;
  width: 18px;
  height: 18px;
}

.request-count {
  background: rgba(255, 255, 255, 0.2);
  color: white;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  margin-left: 8px;
}

/* 请求摘要行 - 一行显示请求方法、地址和状态码 */
.request-summary-line {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border: 1px solid #dee2e6;
  border-radius: 8px;
  margin-bottom: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.request-url-inline {
  flex: 1;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 14px;
  color: #495057;
  background: white;
  padding: 8px 12px;
  border-radius: 4px;
  border: 1px solid #ced4da;
  word-break: break-all;
  min-width: 0;
}

.status-code-inline {
  padding: 6px 12px;
  border-radius: 6px;
  font-weight: 600;
  font-size: 14px;
  min-width: 60px;
  text-align: center;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* 状态码颜色 - 内联版本 */
.status-code-inline.success {
  background: linear-gradient(135deg, #28a745, #20c997);
  color: white;
}

.status-code-inline.error {
  background: linear-gradient(135deg, #dc3545, #e74c3c);
  color: white;
}

.status-code-inline.warning {
  background: linear-gradient(135deg, #ffc107, #fd7e14);
  color: #212529;
}

.status-code-inline.info {
  background: linear-gradient(135deg, #17a2b8, #6f42c1);
  color: white;
}

/* 优化方法标签 */
.request-summary-line .method-tag {
  padding: 8px 16px;
  border-radius: 6px;
  font-weight: 700;
  font-size: 13px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  min-width: 70px;
  text-align: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}
.request-basic-info {
  margin-bottom: 16px;
}

.request-basic-info .info-item {
  display: flex;
  align-items: center;
  margin-top: 8px;
  padding: 4px 0;
  background: none;
  border: none;
  border-radius: 0;
  flex-direction: row;
  gap: 8px;
}

.request-basic-info .info-label {
  font-weight: 500;
  color: #606266;
  margin-right: 8px;
  min-width: 80px;
  font-size: 13px;
  text-transform: none;
  letter-spacing: normal;
}

.request-basic-info .info-value {
  color: #303133;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
  font-weight: normal;
  letter-spacing: normal;
  background: none;
  padding: 0;
  border-radius: 0;
  display: inline;
}

/* 增强的节标题 */
.info-section .section-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 12px;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
  font-size: 14px;
}

.info-section .section-title .el-icon {
  color: #409eff;
  font-size: 16px;
}

.section-subtitle {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 500;
  color: #606266;
  margin: 12px 0 8px 0;
  font-size: 14px;
}

.section-subtitle .el-icon {
  color: #67c23a;
  font-size: 14px;
}

/* 响应头部分 */
.response-headers-section {
  margin-bottom: 16px;
}

/* 响应体容器 */
.response-body-container {
  margin-bottom: 16px;
}

/* 响应元数据 */
.response-meta {
  display: flex;
  gap: 24px;
  margin-top: 12px;
  padding: 12px;
  background-color: #f8f9fa;
  border-radius: 6px;
  border-left: 3px solid #409eff;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.meta-label {
  font-weight: 500;
  color: #606266;
  font-size: 13px;
}

.meta-value {
  color: #303133;
  font-weight: 600;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
}

/* 文件上传容器 */
.files-container {
  background-color: #fef7e0;
  border: 1px solid #f4d03f;
  border-radius: 6px;
  padding: 12px;
}

.files-container .json-content {
  background-color: transparent;
  border: none;
  margin: 0;
}

.request-info {
  position: relative;
}

.request-info.multiple-requests {
  padding: 16px;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  margin-bottom: 16px;
}

.request-info.multiple-requests:last-child {
  margin-bottom: 0;
}

.request-index {
  font-size: 14px;
  font-weight: 600;
  color: #059669;
  margin-bottom: 12px;
  padding: 6px 12px;
  background: linear-gradient(135deg, #ecfdf5, #d1fae5);
  border-radius: 8px;
  display: inline-block;
  border: 1px solid #a7f3d0;
}

.request-separator {
  height: 1px;
  background: linear-gradient(90deg, transparent, #e5e7eb, transparent);
  margin: 20px 0;
}

.request-line {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  padding: 12px;
  background: #f8fafc;
  border-radius: 8px;
}

.method-tag {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
}

.method-get { background: #dbeafe; color: #1e40af; }
.method-post { background: #dcfce7; color: #166534; }
.method-put { background: #fef3c7; color: #92400e; }
.method-delete { background: #fecaca; color: #991b1b; }
.method-patch { background: #e0e7ff; color: #3730a3; }
.method-default { background: #f3f4f6; color: #374151; }

.request-url {
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 13px;
  color: #111827;
  word-break: break-all;
}

/* 响应信息 */
.response-section {
  border-top: 2px solid #e5e7eb;
  padding-top: 16px;
  margin-top: 16px;
}

.response-section .section-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.section-subtitle {
  font-size: 13px;
  font-weight: 600;
  color: #6b7280;
  margin-bottom: 8px;
}

.response-card .card-header {
  background: linear-gradient(135deg, #fef7ff 0%, #f3e8ff 100%);
}

.response-icon {
  color: #7c3aed;
  width: 18px;
  height: 18px;
}

.status-code {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  margin-left: auto;
}

.status-code-success { background: #dcfce7; color: #166534; }
.status-code-client-error { background: #fef3c7; color: #92400e; }
.status-code-server-error { background: #fecaca; color: #991b1b; }
.status-code-default { background: #f3f4f6; color: #374151; }

/* Tabs样式优化 */
.request-response-tabs {
  margin-top: 16px;
}

.config-tabs {
  background: transparent;
}

.config-tabs .el-tabs__header {
  margin: 0 0 16px 0;
}

.config-tabs .el-tabs__content {
  padding: 0;
}

.config-section {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 12px;
  padding: 20px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.section-header {
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e2e8f0;
}

.section-header h4 {
  margin: 0 0 4px 0;
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
}

.section-header p {
  margin: 0;
  font-size: 14px;
  color: #64748b;
}

.tab-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
}

.tab-label .el-icon {
  font-size: 14px;
}

.tab-count {
  background: #409eff;
  color: white;
  padding: 2px 6px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 600;
  margin-left: 4px;
}

.tab-content {
  min-height: 120px;
}

.empty-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #9ca3af;
  font-style: italic;
  padding: 32px;
  text-align: center;
}

.empty-content .el-icon {
  font-size: 32px;
  opacity: 0.5;
}

.empty-content .json-content {
  display: none;
}

/* 通用信息区块 */
/* 优化信息区块显示 */
.info-section {
  margin-bottom: 24px;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  overflow: hidden;
  background: white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.02);
}

.info-section .section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: white;
  margin: 0;
  padding: 12px 16px;
  background: linear-gradient(135deg, #495057 0%, #6c757d 100%);
  font-size: 14px;
  border-bottom: none;
}

.info-section .section-title .el-icon {
  color: white;
  font-size: 16px;
}

/* 请求头容器优化 */
.headers-container {
  padding: 16px;
  background: #f8f9fa;
  max-height: 300px;
  overflow-y: auto;
}

.header-item {
  display: flex;
  margin-bottom: 8px;
  padding: 8px 12px;
  background: white;
  border-radius: 4px;
  border-left: 3px solid #007bff;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.header-key {
  font-weight: 600;
  color: #495057;
  min-width: 150px;
  margin-right: 12px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
}

.header-value {
  color: #6c757d;
  word-break: break-all;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
  flex: 1;
}

/* 请求体和响应体容器优化 */
.params-container,
.body-container,
.files-container,
.response-body-container {
  padding: 16px;
  background: #f8f9fa;
}

.json-content {
  background: #2d3748;
  color: #e2e8f0;
  padding: 16px;
  border-radius: 6px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
  line-height: 1.5;
  max-height: 400px;
  overflow-y: auto;
  margin: 0;
  border: 1px solid #4a5568;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.info-section:last-child {
  margin-bottom: 0;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: #374151;
  margin-bottom: 8px;
  padding-bottom: 4px;
  border-bottom: 2px solid #e5e7eb;
}

.headers-container {
  background: #f8fafc;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 8px;
  max-height: 200px;
  overflow-y: auto;
}

.header-item {
  display: flex;
  gap: 8px;
  padding: 4px 0;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 12px;
}

.header-key {
  color: #6b7280;
  font-weight: 600;
  min-width: 120px;
}

.header-value {
  color: #111827;
  word-break: break-word;
}

.json-content {
  background: #1f2937;
  color: #f9fafb;
  padding: 12px;
  border-radius: 6px;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 12px;
  line-height: 1.5;
  overflow-x: auto;
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
}

.params-container,
.body-container,
.response-body-container {
  max-height: 300px;
  overflow-y: auto;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
}

/* 用例配置卡片样式 */
.case-data-card .card-header {
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
}

.case-data-icon {
  color: #0284c7;
  width: 18px;
  height: 18px;
}

.script-content {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  padding: 12px;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.5;
  color: #334155;
  white-space: pre-wrap;
  word-wrap: break-word;
  max-height: 200px;
  overflow-y: auto;
}

/* 运行中状态 */
.running-card .card-header {
  background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
}

.running-icon {
  color: #d97706;
  width: 18px;
  height: 18px;
}

.running-message {
  text-align: center;
  color: #92400e;
  font-size: 14px;
  padding: 20px;
}

/* 动画 */
.animate-spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

/* 计数徽章样式 */
.count-badge {
  background: #e1f5fe;
  color: #0277bd;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  margin-left: 8px;
}

/* 空内容样式 */
.empty-content {
  color: #9ca3af;
  font-style: italic;
}

.empty-content .json-content {
  color: #9ca3af;
  background: #f8f9fa;
  border: 1px dashed #d1d5db;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .info-grid {
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;
  }
  
  .card-header {
    padding: 16px 20px;
  }
  
  .card-content {
    padding: 20px;
  }
}

@media (max-width: 768px) {
  .test-result-card {
    gap: 16px;
  }
  
  .info-grid {
    grid-template-columns: 1fr;
    gap: 12px;
  }
  
  .info-item {
    padding: 12px;
  }
  
  .request-line {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .card-header {
    padding: 14px 18px;
    flex-wrap: wrap;
  }
  
  .card-content {
    padding: 18px;
  }
  
  .case-name {
    font-size: 18px;
    line-height: 1.3;
  }
  
  .status-indicator {
    padding: 6px 12px;
    font-size: 13px;
  }
  
  .logs-container {
    max-height: 250px;
  }
  
  .log-item {
    grid-template-columns: 1fr;
    gap: 8px;
    padding: 10px 12px;
  }
  
  .log-timestamp {
    font-size: 11px;
  }
  
  .log-level {
    justify-self: start;
    min-width: auto;
    padding: 2px 6px;
  }
}

@media (max-width: 480px) {
  .card-header {
    padding: 12px 16px;
  }
  
  .card-content {
    padding: 16px;
  }
  
  .info-item {
    padding: 10px;
  }
  
  .case-name {
    font-size: 16px;
  }
  
  .status-indicator {
    padding: 5px 10px;
    font-size: 12px;
  }
  
  .card-title {
    font-size: 15px;
  }
}
</style>