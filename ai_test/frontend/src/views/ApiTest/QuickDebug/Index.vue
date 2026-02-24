<template>
  <div class="quick-debug-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <h1>快捷调试</h1>
          <p class="subtitle">类Postman体验，快速调试API接口、查看历史记录</p>
        </div>
        <div class="action-section">
          <el-button @click="showCurlImportDialog = true">
            <el-icon><DocumentCopy /></el-icon>
            导入cURL
          </el-button>
          <el-button @click="handleExportCurl" :disabled="!requestForm.url">
            <el-icon><Download /></el-icon>
            导出cURL
          </el-button>
          <el-button type="success" @click="handleSaveAsInterface" :disabled="!lastResponse">
            <el-icon><FolderAdd /></el-icon>
            保存为接口
          </el-button>
        </div>
      </div>
    </div>

    <div class="main-content">
      <!-- 左侧：请求历史 -->
      <div class="history-panel" :class="{ collapsed: historyCollapsed }">
        <div class="panel-header">
          <span v-if="!historyCollapsed">请求历史</span>
          <el-button link @click="historyCollapsed = !historyCollapsed">
            <el-icon><component :is="historyCollapsed ? 'Expand' : 'Fold'" /></el-icon>
          </el-button>
        </div>
        <div v-if="!historyCollapsed" class="history-list">
          <div class="history-actions">
            <el-input v-model="historyKeyword" placeholder="搜索历史..." size="small" clearable>
              <template #prefix><el-icon><Search /></el-icon></template>
            </el-input>
            <el-button size="small" type="danger" link @click="handleClearHistory" :disabled="!historyList.length">
              清空
            </el-button>
          </div>
          <div v-loading="historyLoading" class="history-items">
            <div
              v-for="item in historyList"
              :key="item.id"
              class="history-item"
              :class="{ active: selectedHistoryId === item.id }"
              @click="handleLoadHistory(item)"
            >
              <div class="history-item-top">
                <el-tag :type="methodTagType(item.method)" size="small" effect="dark" class="method-tag-sm">
                  {{ item.method }}
                </el-tag>
                <span class="history-status" :class="statusClass(item.response_status)">
                  {{ item.response_status || '-' }}
                </span>
              </div>
              <div class="history-url" :title="item.url">{{ item.url }}</div>
              <div class="history-meta">
                <span>{{ item.response_time ? item.response_time.toFixed(0) + 'ms' : '-' }}</span>
                <span>{{ formatTime(item.created_at) }}</span>
                <el-button link size="small" type="danger" @click.stop="handleDeleteHistory(item.id)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </div>
            <el-empty v-if="!historyLoading && historyList.length === 0" description="暂无历史记录" :image-size="60" />
          </div>
        </div>
      </div>

      <!-- 右侧：请求 / 响应 -->
      <div class="request-panel">
        <!-- 请求URL栏 -->
        <el-card class="url-bar-card" shadow="never">
          <div class="url-bar">
            <el-select v-model="requestForm.method" class="method-select" :style="{ width: '120px' }">
              <el-option v-for="m in httpMethods" :key="m" :label="m" :value="m">
                <el-tag :type="methodTagType(m)" effect="dark" size="small" style="min-width:50px;text-align:center">{{ m }}</el-tag>
              </el-option>
            </el-select>
            <el-input
              v-model="requestForm.url"
              placeholder="输入请求URL，如 https://api.example.com/users"
              class="url-input"
              @keydown.enter="handleSendRequest"
              clearable
            />
            <el-button
              type="primary"
              :loading="sending"
              @click="handleSendRequest"
              class="send-btn"
              :disabled="!requestForm.url"
            >
              <el-icon v-if="!sending"><CaretRight /></el-icon>
              {{ sending ? '请求中...' : '发送' }}
            </el-button>
          </div>
        </el-card>

        <!-- 请求配置标签页 -->
        <el-card class="request-config-card" shadow="never">
          <el-tabs v-model="activeRequestTab" class="request-tabs">
            <!-- 查询参数 -->
            <el-tab-pane label="Params" name="params">
              <div class="kv-editor">
                <div class="kv-header">
                  <span>查询参数</span>
                  <el-button size="small" type="primary" link @click="addParam">
                    <el-icon><Plus /></el-icon> 添加参数
                  </el-button>
                </div>
                <div v-for="(param, idx) in requestForm.params" :key="idx" class="kv-row">
                  <el-checkbox v-model="param.enabled" />
                  <el-input v-model="param.key" placeholder="Key" size="small" />
                  <el-input v-model="param.value" placeholder="Value" size="small" />
                  <el-button link type="danger" size="small" @click="requestForm.params.splice(idx, 1)">
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </div>
                <el-empty v-if="requestForm.params.length === 0" description="暂无参数" :image-size="40" />
              </div>
            </el-tab-pane>

            <!-- 请求头 -->
            <el-tab-pane label="Headers" name="headers">
              <div class="kv-editor">
                <div class="kv-header">
                  <span>请求头</span>
                  <el-button size="small" type="primary" link @click="addHeader">
                    <el-icon><Plus /></el-icon> 添加请求头
                  </el-button>
                </div>
                <div v-for="(header, idx) in requestForm.headers" :key="idx" class="kv-row">
                  <el-checkbox v-model="header.enabled" />
                  <el-input v-model="header.key" placeholder="Header Name" size="small" />
                  <el-input v-model="header.value" placeholder="Header Value" size="small" />
                  <el-button link type="danger" size="small" @click="requestForm.headers.splice(idx, 1)">
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </div>
              </div>
            </el-tab-pane>

            <!-- 请求体 -->
            <el-tab-pane label="Body" name="body">
              <div class="body-editor">
                <div class="body-type-bar">
                  <el-radio-group v-model="requestForm.bodyType" size="small">
                    <el-radio-button value="none">none</el-radio-button>
                    <el-radio-button value="json">JSON</el-radio-button>
                    <el-radio-button value="form">form-data</el-radio-button>
                    <el-radio-button value="text">raw text</el-radio-button>
                  </el-radio-group>
                </div>
                <div v-if="requestForm.bodyType === 'none'" class="body-none">
                  <el-empty description="此请求没有请求体" :image-size="40" />
                </div>
                <div v-else-if="requestForm.bodyType === 'json'" class="body-json">
                  <el-input
                    v-model="requestForm.bodyJson"
                    type="textarea"
                    :rows="10"
                    placeholder='{"key": "value"}'
                    class="code-textarea"
                  />
                  <div class="json-actions">
                    <el-button size="small" @click="formatJson">格式化 JSON</el-button>
                  </div>
                </div>
                <div v-else-if="requestForm.bodyType === 'form'" class="body-form">
                  <div class="kv-header">
                    <span>Form 参数</span>
                    <el-button size="small" type="primary" link @click="addFormField">
                      <el-icon><Plus /></el-icon> 添加字段
                    </el-button>
                  </div>
                  <div v-for="(field, idx) in requestForm.formFields" :key="idx" class="kv-row">
                    <el-checkbox v-model="field.enabled" />
                    <el-input v-model="field.key" placeholder="Key" size="small" />
                    <el-input v-model="field.value" placeholder="Value" size="small" />
                    <el-button link type="danger" size="small" @click="requestForm.formFields.splice(idx, 1)">
                      <el-icon><Delete /></el-icon>
                    </el-button>
                  </div>
                </div>
                <div v-else-if="requestForm.bodyType === 'text'" class="body-text">
                  <el-input
                    v-model="requestForm.bodyText"
                    type="textarea"
                    :rows="10"
                    placeholder="输入原始文本..."
                  />
                </div>
              </div>
            </el-tab-pane>
          </el-tabs>
        </el-card>

        <!-- 响应区域 -->
        <el-card class="response-card" shadow="never">
          <template #header>
            <div class="response-header">
              <span class="response-title">响应</span>
              <div v-if="lastResponse" class="response-meta">
                <el-tag :type="responseStatusType" effect="dark" size="small">
                  {{ lastResponse.response_status }}
                </el-tag>
                <span class="meta-item">
                  <el-icon><Timer /></el-icon>
                  {{ lastResponse.response_time ? lastResponse.response_time.toFixed(0) + ' ms' : '-' }}
                </span>
                <span class="meta-item">
                  <el-icon><Document /></el-icon>
                  {{ formatSize(lastResponse.response_size) }}
                </span>
              </div>
            </div>
          </template>
          <div v-if="!lastResponse && !sending" class="response-empty">
            <el-empty description="发送请求后在此查看响应结果" :image-size="80" />
          </div>
          <div v-else-if="sending" class="response-loading">
            <el-skeleton :rows="8" animated />
          </div>
          <div v-else class="response-content">
            <el-tabs v-model="activeResponseTab">
              <el-tab-pane label="Body" name="body">
                <div class="response-body-toolbar">
                  <el-button size="small" @click="copyResponseBody">
                    <el-icon><DocumentCopy /></el-icon> 复制
                  </el-button>
                  <el-button size="small" @click="formatResponseBody">格式化</el-button>
                </div>
                <pre class="response-body-pre"><code>{{ responseBodyDisplay }}</code></pre>
              </el-tab-pane>
              <el-tab-pane label="Headers" name="headers">
                <el-table :data="responseHeadersList" size="small" stripe>
                  <el-table-column prop="key" label="Header" min-width="200" />
                  <el-table-column prop="value" label="Value" min-width="300" />
                </el-table>
              </el-tab-pane>
            </el-tabs>
          </div>
        </el-card>
      </div>
    </div>

    <!-- cURL导入弹窗 -->
    <el-dialog v-model="showCurlImportDialog" title="导入 cURL 命令" width="640px" destroy-on-close>
      <el-input
        v-model="curlInput"
        type="textarea"
        :rows="8"
        placeholder="粘贴 cURL 命令到此处，例如：&#10;curl -X GET 'https://api.example.com/users' -H 'Authorization: Bearer token'"
        class="code-textarea"
      />
      <template #footer>
        <el-button @click="showCurlImportDialog = false">取消</el-button>
        <el-button type="primary" :loading="curlParsing" @click="handleParseCurl" :disabled="!curlInput.trim()">
          解析并填充
        </el-button>
      </template>
    </el-dialog>

    <!-- 保存为接口弹窗 -->
    <el-dialog v-model="showSaveDialog" title="保存为接口" width="480px" destroy-on-close>
      <el-form :model="saveForm" label-width="80px">
        <el-form-item label="接口名称">
          <el-input v-model="saveForm.name" placeholder="输入接口名称" />
        </el-form-item>
        <el-form-item label="接口模块">
          <el-input v-model="saveForm.module" placeholder="输入模块分类（可选）" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="saveForm.description" type="textarea" :rows="3" placeholder="描述（可选）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showSaveDialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleDoSaveAsInterface">确认保存</el-button>
      </template>
    </el-dialog>

    <!-- cURL导出弹窗 -->
    <el-dialog v-model="showCurlExportDialog" title="cURL 命令" width="640px" destroy-on-close>
      <pre class="curl-export-pre"><code>{{ exportedCurl }}</code></pre>
      <template #footer>
        <el-button @click="showCurlExportDialog = false">关闭</el-button>
        <el-button type="primary" @click="copyCurlCommand">
          <el-icon><DocumentCopy /></el-icon> 复制
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus, Delete, Search, CaretRight, Timer, Document,
  DocumentCopy, Download, FolderAdd, Expand, Fold
} from '@element-plus/icons-vue'
import {
  quickDebugSend,
  getQuickDebugHistory,
  deleteQuickDebugHistory,
  clearQuickDebugHistory,
  parseCurlCommand,
  exportAsCurl,
  saveDebugAsInterface
} from '@/api/apiTest'
import { useProjectStore } from '@/stores'

const route = useRoute()
const projectStore = useProjectStore()

// ========== 基础状态 ==========
const sending = ref(false)
const historyLoading = ref(false)
const historyCollapsed = ref(false)
const historyKeyword = ref('')
const selectedHistoryId = ref(null)

const httpMethods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']

const requestForm = reactive({
  method: 'GET',
  url: '',
  params: [],
  headers: [
    { key: 'Content-Type', value: 'application/json', enabled: true }
  ],
  bodyType: 'none',
  bodyJson: '',
  bodyText: '',
  formFields: []
})

const activeRequestTab = ref('params')
const activeResponseTab = ref('body')

const lastResponse = ref(null)
const historyList = ref([])

// cURL import
const showCurlImportDialog = ref(false)
const curlInput = ref('')
const curlParsing = ref(false)

// cURL export
const showCurlExportDialog = ref(false)
const exportedCurl = ref('')

// Save as interface
const showSaveDialog = ref(false)
const saving = ref(false)
const saveForm = reactive({
  name: '',
  module: '',
  description: ''
})

// ========== 计算属性 ==========
const getProjectId = () => {
  return route.params.projectId || projectStore.currentProject?.id || 1
}

const responseStatusType = computed(() => {
  if (!lastResponse.value) return 'info'
  const s = lastResponse.value.response_status
  if (s >= 200 && s < 300) return 'success'
  if (s >= 300 && s < 400) return 'warning'
  return 'danger'
})

const responseBodyDisplay = ref('')

const responseHeadersList = computed(() => {
  if (!lastResponse.value?.response_headers) return []
  const h = lastResponse.value.response_headers
  return Object.entries(h).map(([key, value]) => ({ key, value: String(value) }))
})

// ========== 工具方法 ==========
const methodTagType = (method) => {
  const map = {
    GET: 'success', POST: 'warning', PUT: 'primary',
    DELETE: 'danger', PATCH: '', HEAD: 'info', OPTIONS: 'info'
  }
  return map[method] || 'info'
}

const statusClass = (status) => {
  if (!status) return ''
  if (status >= 200 && status < 300) return 'status-ok'
  if (status >= 300 && status < 400) return 'status-warn'
  return 'status-err'
}

const formatTime = (dateStr) => {
  if (!dateStr) return '-'
  const d = new Date(dateStr)
  return d.toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

const formatSize = (bytes) => {
  if (!bytes) return '-'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1024 / 1024).toFixed(2) + ' MB'
}

// ========== KV操作 ==========
const addParam = () => requestForm.params.push({ key: '', value: '', enabled: true })
const addHeader = () => requestForm.headers.push({ key: '', value: '', enabled: true })
const addFormField = () => requestForm.formFields.push({ key: '', value: '', enabled: true })

// ========== JSON格式化 ==========
const formatJson = () => {
  try {
    const obj = JSON.parse(requestForm.bodyJson)
    requestForm.bodyJson = JSON.stringify(obj, null, 2)
  } catch (e) {
    ElMessage.warning('JSON 格式不正确，无法格式化')
  }
}

const formatResponseBody = () => {
  if (!lastResponse.value?.response_body) return
  try {
    const obj = JSON.parse(lastResponse.value.response_body)
    responseBodyDisplay.value = JSON.stringify(obj, null, 2)
  } catch {
    responseBodyDisplay.value = lastResponse.value.response_body
  }
}

const copyResponseBody = () => {
  navigator.clipboard.writeText(responseBodyDisplay.value || '').then(() => {
    ElMessage.success('已复制到剪贴板')
  })
}

// ========== 构建请求数据 ==========
const buildRequestPayload = () => {
  const params = {}
  requestForm.params.filter(p => p.enabled && p.key).forEach(p => { params[p.key] = p.value })

  const headers = {}
  requestForm.headers.filter(h => h.enabled && h.key).forEach(h => { headers[h.key] = h.value })

  let body = null
  let bodyType = requestForm.bodyType
  if (bodyType === 'json' && requestForm.bodyJson.trim()) {
    try {
      body = JSON.parse(requestForm.bodyJson)
    } catch {
      body = requestForm.bodyJson
    }
  } else if (bodyType === 'form') {
    body = {}
    requestForm.formFields.filter(f => f.enabled && f.key).forEach(f => { body[f.key] = f.value })
  } else if (bodyType === 'text') {
    body = requestForm.bodyText
  }

  return {
    method: requestForm.method,
    url: requestForm.url,
    headers: Object.keys(headers).length ? headers : null,
    params: Object.keys(params).length ? params : null,
    body,
    body_type: bodyType
  }
}

// ========== 发送请求 ==========
const handleSendRequest = async () => {
  if (!requestForm.url.trim()) {
    ElMessage.warning('请输入请求URL')
    return
  }
  sending.value = true
  lastResponse.value = null
  try {
    const payload = buildRequestPayload()
    const res = await quickDebugSend(getProjectId(), payload)
    const data = res.data || res
    lastResponse.value = data
    responseBodyDisplay.value = data.response_body || ''
    formatResponseBody()
    // Reload history
    loadHistory()
  } catch (e) {
    console.error('快捷调试请求失败:', e)
    ElMessage.error('请求失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    sending.value = false
  }
}

// ========== 历史记录 ==========
const loadHistory = async () => {
  historyLoading.value = true
  try {
    const res = await getQuickDebugHistory(getProjectId(), {
      page: 1,
      page_size: 50,
      keyword: historyKeyword.value || undefined
    })
    const data = res.data || res
    historyList.value = data.items || data.history || []
  } catch (e) {
    console.error('加载历史记录失败:', e)
  } finally {
    historyLoading.value = false
  }
}

const handleLoadHistory = (item) => {
  selectedHistoryId.value = item.id
  requestForm.method = item.method || 'GET'
  requestForm.url = item.url || ''

  // Restore params
  requestForm.params = []
  if (item.params && typeof item.params === 'object') {
    Object.entries(item.params).forEach(([key, value]) => {
      requestForm.params.push({ key, value: String(value), enabled: true })
    })
  }

  // Restore headers
  requestForm.headers = []
  if (item.headers && typeof item.headers === 'object') {
    Object.entries(item.headers).forEach(([key, value]) => {
      requestForm.headers.push({ key, value: String(value), enabled: true })
    })
  }
  if (requestForm.headers.length === 0) {
    requestForm.headers.push({ key: 'Content-Type', value: 'application/json', enabled: true })
  }

  // Restore body
  requestForm.bodyType = item.body_type || 'none'
  if (item.body_type === 'json' && item.body) {
    requestForm.bodyJson = typeof item.body === 'string' ? item.body : JSON.stringify(item.body, null, 2)
  } else if (item.body_type === 'form' && item.body) {
    requestForm.formFields = Object.entries(item.body).map(([key, value]) => ({ key, value: String(value), enabled: true }))
  } else if (item.body_type === 'text' && item.body) {
    requestForm.bodyText = String(item.body)
  }

  // Restore response if present
  if (item.response_status) {
    lastResponse.value = {
      response_status: item.response_status,
      response_headers: item.response_headers || {},
      response_body: item.response_body || '',
      response_time: item.response_time,
      response_size: item.response_size
    }
    responseBodyDisplay.value = item.response_body || ''
    formatResponseBody()
  } else {
    lastResponse.value = null
  }
}

const handleDeleteHistory = async (historyId) => {
  try {
    await ElMessageBox.confirm('确认删除此条历史记录？', '提示', { type: 'warning' })
    await deleteQuickDebugHistory(getProjectId(), historyId)
    ElMessage.success('删除成功')
    if (selectedHistoryId.value === historyId) {
      selectedHistoryId.value = null
    }
    loadHistory()
  } catch {}
}

const handleClearHistory = async () => {
  try {
    await ElMessageBox.confirm('确认清空所有历史记录？此操作不可撤销。', '警告', { type: 'warning' })
    await clearQuickDebugHistory(getProjectId())
    ElMessage.success('已清空')
    historyList.value = []
    selectedHistoryId.value = null
  } catch {}
}

// ========== cURL导入 ==========
const handleParseCurl = async () => {
  if (!curlInput.value.trim()) return
  curlParsing.value = true
  try {
    const res = await parseCurlCommand(getProjectId(), curlInput.value)
    const data = res.data || res
    // Fill form
    requestForm.method = data.method || 'GET'
    requestForm.url = data.url || ''
    requestForm.params = []
    if (data.params && typeof data.params === 'object') {
      Object.entries(data.params).forEach(([key, value]) => {
        requestForm.params.push({ key, value: String(value), enabled: true })
      })
    }
    requestForm.headers = []
    if (data.headers && typeof data.headers === 'object') {
      Object.entries(data.headers).forEach(([key, value]) => {
        requestForm.headers.push({ key, value: String(value), enabled: true })
      })
    }
    if (requestForm.headers.length === 0) {
      requestForm.headers.push({ key: 'Content-Type', value: 'application/json', enabled: true })
    }
    requestForm.bodyType = data.body_type || 'none'
    if (data.body) {
      if (data.body_type === 'json') {
        requestForm.bodyJson = typeof data.body === 'string' ? data.body : JSON.stringify(data.body, null, 2)
      } else if (data.body_type === 'form') {
        requestForm.formFields = Object.entries(data.body).map(([k, v]) => ({ key: k, value: String(v), enabled: true }))
      } else {
        requestForm.bodyText = String(data.body)
      }
    }
    showCurlImportDialog.value = false
    curlInput.value = ''
    ElMessage.success('cURL 解析成功，已填充请求表单')
  } catch (e) {
    ElMessage.error('cURL 解析失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    curlParsing.value = false
  }
}

// ========== cURL导出 ==========
const handleExportCurl = async () => {
  try {
    const payload = buildRequestPayload()
    const res = await exportAsCurl(getProjectId(), payload)
    const data = res.data || res
    exportedCurl.value = data.curl_command || data.curl || ''
    showCurlExportDialog.value = true
  } catch (e) {
    ElMessage.error('导出失败: ' + (e.response?.data?.detail || e.message))
  }
}

const copyCurlCommand = () => {
  navigator.clipboard.writeText(exportedCurl.value).then(() => {
    ElMessage.success('已复制到剪贴板')
  })
}

// ========== 保存为接口 ==========
const handleSaveAsInterface = () => {
  saveForm.name = ''
  saveForm.module = ''
  saveForm.description = ''
  showSaveDialog.value = true
}

const handleDoSaveAsInterface = async () => {
  if (!saveForm.name.trim()) {
    ElMessage.warning('请输入接口名称')
    return
  }
  saving.value = true
  try {
    const payload = buildRequestPayload()
    await saveDebugAsInterface(getProjectId(), {
      ...payload,
      name: saveForm.name,
      module: saveForm.module,
      description: saveForm.description
    })
    ElMessage.success('已保存为接口')
    showSaveDialog.value = false
  } catch (e) {
    ElMessage.error('保存失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    saving.value = false
  }
}

// ========== 搜索节流 ==========
let searchTimer = null
watch(historyKeyword, () => {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => loadHistory(), 300)
})

// ========== 初始化 ==========
onMounted(() => {
  loadHistory()
})
</script>

<style scoped>
.quick-debug-page {
  padding: 20px;
  background: #f8fafc;
  min-height: 100vh;
}

.page-header {
  margin-bottom: 16px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  background: white;
  padding: 20px 24px;
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}

.title-section h1 {
  color: #1f2937;
  margin: 0 0 4px 0;
  font-size: 22px;
  font-weight: 600;
}

.subtitle {
  color: #6b7280;
  margin: 0;
  font-size: 13px;
}

.action-section {
  display: flex;
  gap: 8px;
}

/* ========== 主布局 ========== */
.main-content {
  display: flex;
  gap: 16px;
  align-items: flex-start;
}

/* ========== 历史面板 ========== */
.history-panel {
  width: 280px;
  min-width: 280px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  transition: all 0.3s;
}

.history-panel.collapsed {
  width: 40px;
  min-width: 40px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #f0f0f0;
  font-weight: 600;
  font-size: 14px;
  color: #1f2937;
}

.history-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
}

.history-items {
  max-height: calc(100vh - 280px);
  overflow-y: auto;
  padding: 0 8px 8px;
}

.history-item {
  padding: 10px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s;
  margin-bottom: 4px;
  border: 1px solid transparent;
}

.history-item:hover {
  background: #f5f3ff;
}

.history-item.active {
  background: #ede9fe;
  border-color: #8b5cf6;
}

.history-item-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.method-tag-sm {
  font-size: 10px;
  padding: 0 6px;
  height: 18px;
  line-height: 18px;
}

.history-url {
  font-size: 12px;
  color: #4b5563;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 4px;
}

.history-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 11px;
  color: #9ca3af;
}

.history-status {
  font-size: 12px;
  font-weight: 600;
}

.status-ok { color: #10b981; }
.status-warn { color: #f59e0b; }
.status-err { color: #ef4444; }

/* ========== 请求面板 ========== */
.request-panel {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.url-bar-card :deep(.el-card__body) {
  padding: 12px 16px;
}

.url-bar {
  display: flex;
  gap: 8px;
  align-items: center;
}

.method-select {
  flex-shrink: 0;
}

.url-input {
  flex: 1;
}

.send-btn {
  flex-shrink: 0;
  min-width: 100px;
  font-weight: 600;
}

/* ========== 请求配置 ========== */
.request-config-card :deep(.el-card__body) {
  padding: 0 16px 16px;
}

.request-tabs :deep(.el-tabs__header) {
  margin-bottom: 12px;
}

.kv-editor {
  min-height: 100px;
}

.kv-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 13px;
  color: #6b7280;
  font-weight: 500;
}

.kv-row {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 6px;
}

.kv-row .el-checkbox {
  flex-shrink: 0;
}

.kv-row .el-input {
  flex: 1;
}

/* ========== Body编辑器 ========== */
.body-type-bar {
  margin-bottom: 12px;
}

.body-none, .body-json, .body-form, .body-text {
  min-height: 80px;
}

.code-textarea :deep(.el-textarea__inner) {
  font-family: 'Menlo', 'Monaco', 'Consolas', monospace;
  font-size: 13px;
  line-height: 1.6;
}

.json-actions {
  margin-top: 8px;
  text-align: right;
}

/* ========== 响应区域 ========== */
.response-card :deep(.el-card__header) {
  padding: 12px 16px;
  background: #fafafa;
}

.response-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.response-title {
  font-weight: 600;
  font-size: 14px;
  color: #1f2937;
}

.response-meta {
  display: flex;
  gap: 12px;
  align-items: center;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #6b7280;
}

.response-empty, .response-loading {
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.response-body-toolbar {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}

.response-body-pre {
  background: #1e1e2e;
  color: #cdd6f4;
  padding: 16px;
  border-radius: 8px;
  font-family: 'Menlo', 'Monaco', 'Consolas', monospace;
  font-size: 13px;
  line-height: 1.6;
  max-height: 500px;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-all;
  margin: 0;
}

/* ========== cURL Export ========== */
.curl-export-pre {
  background: #1e1e2e;
  color: #cdd6f4;
  padding: 16px;
  border-radius: 8px;
  font-family: 'Menlo', 'Monaco', 'Consolas', monospace;
  font-size: 13px;
  line-height: 1.6;
  max-height: 400px;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-all;
}

/* ========== 响应式 ========== */
@media (max-width: 768px) {
  .quick-debug-page { padding: 12px; }
  .main-content { flex-direction: column; }
  .history-panel { width: 100%; min-width: unset; }
  .history-panel.collapsed { width: 100%; }
  .header-content { flex-direction: column; gap: 12px; }
}
</style>
