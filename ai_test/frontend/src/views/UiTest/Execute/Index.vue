<template>
  <div class="ui-execute-page">
    <!-- 顶部操作栏 -->
    <div class="top-bar">
      <div class="top-left">
        <el-button @click="goBack" plain size="small">
          <el-icon><ArrowLeft /></el-icon> 返回
        </el-button>
        <h3 v-if="caseInfo">{{ caseInfo.name }}</h3>
        <el-tag v-if="caseInfo" :type="priorityType(caseInfo.priority)" size="small">{{ caseInfo.priority }}</el-tag>
      </div>
      <div class="top-right">
        <el-tag v-if="execStatus" :type="execStatusType" size="large" effect="dark" style="font-size: 14px;">
          {{ execStatusText }}
        </el-tag>
        <el-button
          type="success"
          @click="startExecution"
          :loading="connecting"
          :disabled="executing || connecting"
        >
          <el-icon><VideoPlay /></el-icon>
          {{ connecting ? '连接中...' : executing ? '执行中...' : '开始 AI 执行' }}
        </el-button>
      </div>
    </div>

    <div class="main-area" v-loading="caseLoading">
      <!-- 左侧：测试步骤 -->
      <div class="steps-panel">
        <div class="panel-header">
          <span>测试步骤 ({{ steps.length }})</span>
          <el-tag v-if="executing" type="warning" size="small" effect="plain" class="vision-badge">
            <el-icon style="margin-right: 2px;"><View /></el-icon> AI视觉分析中
          </el-tag>
        </div>
        <div class="steps-scroll">
          <div
            v-for="(step, idx) in steps"
            :key="step.id"
            class="step-card"
            :class="step._status"
          >
            <div class="step-top">
              <div class="step-badge" :class="step._status">
                <el-icon v-if="step._status === 'running'" class="is-loading"><Loading /></el-icon>
                <span v-else>{{ idx + 1 }}</span>
              </div>
              <div class="step-info">
                <div class="step-action-text">{{ step.action }}</div>
                <div v-if="step.input_data" class="step-sub">输入: {{ step.input_data }}</div>
                <div v-if="step.expected_result" class="step-sub">预期: {{ step.expected_result }}</div>
              </div>
              <div class="step-status-icon">
                <el-icon v-if="step._status === 'passed'" style="color:#67c23a;font-size:18px;"><SuccessFilled /></el-icon>
                <el-icon v-else-if="step._status === 'failed'" style="color:#f56c6c;font-size:18px;"><CircleCloseFilled /></el-icon>
              </div>
            </div>

            <!-- AI 决策信息 -->
            <div v-if="step._ai_description" class="step-ai-info">
              <el-icon style="color:#8b5cf6;font-size:12px;margin-right:4px;"><MagicStick /></el-icon>
              <span class="ai-label">AI视觉分析:</span>
              <span class="ai-desc">{{ step._ai_description }}</span>
            </div>

            <!-- 断言结果 -->
            <div v-if="step._assertion_type" class="step-assertion-info">
              <el-icon :style="{color: step._assertion_passed ? '#67c23a' : '#f56c6c', fontSize: '12px'}">
                <component :is="step._assertion_passed ? 'SuccessFilled' : 'CircleCloseFilled'" />
              </el-icon>
              <span class="assertion-type-label">{{ assertionLabel(step._assertion_type) }}</span>
              <span class="assertion-detail-text" :class="{ passed: step._assertion_passed, failed: !step._assertion_passed }">{{ step._assertion_detail }}</span>
            </div>

            <!-- 结果区域 -->
            <div v-if="step._actual_result || step._error" class="step-result-area">
              <div v-if="step._actual_result" class="step-result" :class="{ failed: step._status === 'failed' }">
                {{ step._actual_result }}
              </div>
              <div v-if="step._error" class="step-error">{{ step._error }}</div>
              <div v-if="step._duration" class="step-time">⏱ {{ step._duration }}ms</div>
            </div>

            <!-- 步骤截图缩略图 -->
            <div v-if="step._screenshot_url" class="step-screenshot">
              <el-image
                :src="getFullUrl(step._screenshot_url)"
                :preview-src-list="[getFullUrl(step._screenshot_url)]"
                fit="cover"
                class="step-screenshot-img"
              >
                <template #placeholder>
                  <div class="screenshot-placeholder">
                    <el-icon><Picture /></el-icon>
                  </div>
                </template>
              </el-image>
              <span class="screenshot-label">执行截图</span>
            </div>
          </div>
        </div>

        <!-- 执行结果摘要 -->
        <div v-if="executionDone" class="summary-bar" :class="finalStatus">
          <div class="summary-left">
            <el-icon v-if="finalStatus === 'passed'"><SuccessFilled /></el-icon>
            <el-icon v-else><CircleCloseFilled /></el-icon>
            <span>{{ passedCount }} 通过 / {{ failedCount }} 失败</span>
          </div>
          <el-button
            v-if="executionId || currentExecutionId"
            type="primary"
            size="small"
            @click="goReport"
          >
            <el-icon><Document /></el-icon> 查看报告
          </el-button>
        </div>
      </div>

      <!-- 右侧：内嵌浏览器 -->
      <div class="browser-panel">
        <!-- 浏览器外壳 -->
        <div class="browser-shell">
          <div class="browser-toolbar">
            <div class="traffic-lights">
              <span class="light close"></span>
              <span class="light minimize"></span>
              <span class="light maximize"></span>
            </div>
            <div class="address-bar">
              <el-icon style="color:#909399;"><Link /></el-icon>
              <span class="url-text">{{ currentUrl || '等待启动...' }}</span>
            </div>
            <div class="toolbar-actions">
              <el-tooltip v-if="executing" content="AI正在视觉分析页面截图进行操作决策" placement="bottom">
                <el-icon class="is-loading" style="color:#8b5cf6;"><MagicStick /></el-icon>
              </el-tooltip>
              <el-icon v-if="executing" class="is-loading" style="color:#e6a23c;margin-left:6px;"><Loading /></el-icon>
            </div>
          </div>

          <!-- 浏览器画面 -->
          <div class="browser-content">
            <canvas
              ref="canvasRef"
              class="browser-canvas"
              :width="1280"
              :height="720"
              @click="handleCanvasClick"
            ></canvas>

            <!-- 未执行时的占位 -->
            <div v-if="!hasFrame" class="browser-overlay">
              <div class="overlay-content">
                <el-icon style="font-size:56px;color:rgba(139,92,246,0.4);"><Monitor /></el-icon>
                <p class="overlay-title">AI 视觉驱动浏览器</p>
                <p class="overlay-desc">点击「开始 AI 执行」，AI 将通过视觉分析页面截图自动执行测试步骤</p>
                <div class="overlay-features">
                  <div class="feature-item">
                    <el-icon><View /></el-icon>
                    <span>截图视觉分析</span>
                  </div>
                  <div class="feature-item">
                    <el-icon><MagicStick /></el-icon>
                    <span>AI智能决策</span>
                  </div>
                  <div class="feature-item">
                    <el-icon><Camera /></el-icon>
                    <span>每步截图记录</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 执行日志 -->
        <div class="log-bar">
          <div class="log-header">
            <span>执行日志</span>
            <el-tag :type="executing ? 'warning' : 'info'" size="small" effect="plain">
              {{ executing ? 'LIVE' : 'LOG' }}
            </el-tag>
          </div>
          <div class="log-scroll" ref="logRef">
            <div v-for="(log, idx) in logs" :key="idx" class="log-line" :class="log.level">
              <span class="log-ts">{{ log.time }}</span>
              <span v-if="log.level === 'ai'" class="log-ai-badge">AI</span>
              <span class="log-text">{{ log.message }}</span>
            </div>
            <div v-if="logs.length === 0" class="log-empty">等待执行...</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 截图预览 -->
    <el-image-viewer
      v-if="previewVisible"
      :url-list="previewList"
      @close="previewVisible = false"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Loading, SuccessFilled, CircleCloseFilled, View, MagicStick, Camera, Picture, Document } from '@element-plus/icons-vue'
import { useProjectStore } from '@/stores'
import { getUiCaseDetail } from '@/api/uiTest'

const route = useRoute()
const router = useRouter()
const projectStore = useProjectStore()
const projectId = () => projectStore.currentProject?.id
const caseId = () => route.params.caseId

const API_BASE = import.meta.env.VITE_BASE_API || `http://${window.location.hostname}:8000`
const WS_BASE = API_BASE.replace(/^http/, 'ws')

const caseLoading = ref(false)
const caseInfo = ref(null)
const steps = ref([])
const connecting = ref(false)
const executing = ref(false)
const executionDone = ref(false)
const finalStatus = ref('')
const passedCount = ref(0)
const failedCount = ref(0)
const currentUrl = ref('')
const hasFrame = ref(false)
const execStatus = ref('')
const executionId = ref(null)
const currentExecutionId = ref(null)
const logs = ref([])

const canvasRef = ref(null)
const logRef = ref(null)
const previewVisible = ref(false)
const previewList = ref([])

let ws = null
let canvasCtx = null
let frameImg = null

const execStatusType = computed(() => {
  const m = { running: 'warning', passed: 'success', failed: 'danger', error: 'danger' }
  return m[execStatus.value] || 'info'
})
const execStatusText = computed(() => {
  const m = { running: '执行中', passed: '通过', failed: '失败', error: '异常' }
  return m[execStatus.value] || execStatus.value
})
const priorityType = (p) => ({ P0: 'danger', P1: 'warning', P2: '', P3: 'info' })[p] || ''

const getFullUrl = (path) => {
  if (!path) return ''
  if (path.startsWith('http')) return path
  return `${API_BASE}${path}`
}

const addLog = (message, level = 'info') => {
  const now = new Date()
  const time = [now.getHours(), now.getMinutes(), now.getSeconds()].map(n => String(n).padStart(2, '0')).join(':')
  logs.value.push({ time, message, level })
  nextTick(() => { if (logRef.value) logRef.value.scrollTop = logRef.value.scrollHeight })
}

const initCanvas = () => {
  if (!canvasRef.value) return
  canvasCtx = canvasRef.value.getContext('2d')
  frameImg = new Image()
  frameImg.onload = () => {
    if (canvasCtx) {
      canvasCtx.drawImage(frameImg, 0, 0, 1280, 720)
    }
  }
}

const renderFrame = (base64Jpeg) => {
  if (!frameImg) initCanvas()
  hasFrame.value = true
  frameImg.src = `data:image/jpeg;base64,${base64Jpeg}`
}

const fetchCaseDetail = async () => {
  if (!projectId() || !caseId()) return
  caseLoading.value = true
  try {
    const res = await getUiCaseDetail(projectId(), caseId())
    caseInfo.value = res.data
    steps.value = (res.data?.steps || []).map(s => ({
      ...s,
      _status: 'pending',
      _actual_result: null,
      _error: null,
      _duration: null,
      _screenshot_url: null,
      _ai_description: null,
      _ai_action: null,
      _assertion_type: null,
      _assertion_passed: null,
      _assertion_detail: null,
    }))
  } catch (e) {
    ElMessage.error('获取用例详情失败')
  } finally {
    caseLoading.value = false
  }
}

const startExecution = () => {
  if (!projectId() || !caseId()) return
  connecting.value = true
  executionDone.value = false
  passedCount.value = 0
  failedCount.value = 0
  hasFrame.value = false
  execStatus.value = 'running'
  logs.value = []

  steps.value.forEach(s => {
    s._status = 'pending'
    s._actual_result = null
    s._error = null
    s._duration = null
    s._screenshot_url = null
    s._ai_description = null
    s._ai_action = null
    s._assertion_type = null
    s._assertion_passed = null
    s._assertion_detail = null
  })
  executionId.value = null
  currentExecutionId.value = null

  initCanvas()
  if (canvasCtx) canvasCtx.clearRect(0, 0, 1280, 720)

  const token = localStorage.getItem('token') || ''
  const url = `${WS_BASE}/ui_test/${projectId()}/cases/${caseId()}/ws-execute?token=${token}`

  addLog('正在连接执行服务...')

  ws = new WebSocket(url)

  ws.onopen = () => {
    connecting.value = false
    executing.value = true
    addLog('连接成功，AI 视觉浏览器启动中...')
  }

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      handleMessage(data)
    } catch (e) {
      // skip
    }
  }

  ws.onerror = (err) => {
    connecting.value = false
    executing.value = false
    execStatus.value = 'error'
    addLog('WebSocket 连接错误', 'error')
    ElMessage.error('连接执行服务失败')
  }

  ws.onclose = () => {
    connecting.value = false
    executing.value = false
    if (!executionDone.value && execStatus.value === 'running') {
      execStatus.value = 'error'
      addLog('连接已断开', 'error')
    }
  }
}

const handleMessage = (data) => {
  const type = data.type

  if (type === 'frame') {
    renderFrame(data.data)
    return
  }

  if (type === 'execution_start') {
    currentUrl.value = data.page_url || ''
    currentExecutionId.value = data.execution_id || null
    addLog(`开始执行，共 ${data.total_steps} 个步骤`)
  } else if (type === 'page_loaded') {
    currentUrl.value = data.url || ''
    addLog(`页面已加载: ${data.title || data.url}`)
  } else if (type === 'step_start') {
    const step = steps.value.find(s => s.id === data.step_id)
    if (step) {
      step._status = 'running'
      addLog(`步骤 ${data.sort_order + 1}: ${data.action}`)
    }
  } else if (type === 'ai_thinking') {
    const step = steps.value.find(s => s.id === data.step_id)
    if (step) {
      step._ai_description = data.description || ''
      try {
        step._ai_action = data.action ? JSON.parse(data.action) : null
      } catch (e) {
        step._ai_action = null
      }
    }
    const desc = data.description || ''
    addLog(`🔍 AI视觉分析: ${desc || data.action}`, 'ai')
  } else if (type === 'step_done') {
    const step = steps.value.find(s => s.id === data.step_id)
    if (step) {
      step._status = data.status
      step._actual_result = data.actual_result
      step._error = data.error_message
      step._duration = data.duration_ms
      step._assertion_type = data.assertion_type || null
      step._assertion_passed = data.assertion_passed
      step._assertion_detail = data.assertion_detail || null
      // 设置步骤截图
      if (data.screenshot) {
        step._screenshot_url = `/screenshots/${data.screenshot}`
      }
    }
    if (data.status === 'passed') {
      passedCount.value++
      addLog(`  ✓ 通过 — ${data.actual_result || ''}`, 'success')
    } else {
      failedCount.value++
      addLog(`  ✗ 失败 — ${data.error_message || data.actual_result || ''}`, 'error')
    }
    // 断言日志
    if (data.assertion_type) {
      const icon = data.assertion_passed ? '✅' : '❌'
      addLog(`  ${icon} 断言[${data.assertion_type}]: ${data.assertion_detail || '-'}`, data.assertion_passed ? 'success' : 'error')
    }
  } else if (type === 'done') {
    executionDone.value = true
    executing.value = false
    finalStatus.value = data.status
    execStatus.value = data.status
    executionId.value = data.execution_id || currentExecutionId.value
    addLog(`执行完成: ${data.passed} 通过, ${data.failed} 失败`, data.status === 'passed' ? 'success' : 'error')
  } else if (type === 'error') {
    addLog(`错误: ${data.message}`, 'error')
    execStatus.value = 'error'
  }
}

const handleCanvasClick = () => {
  if (!hasFrame.value || !canvasRef.value) return
  const dataUrl = canvasRef.value.toDataURL('image/png')
  previewList.value = [dataUrl]
  previewVisible.value = true
}

const assertionLabel = (type) => {
  const m = {
    url_contains: 'URL包含', url_equals: 'URL等于',
    title_contains: '标题包含', title_equals: '标题等于',
    element_visible: '元素可见', element_hidden: '元素隐藏',
    element_text_contains: '元素文本包含', element_text_equals: '元素文本等于',
    element_exists: '元素存在', page_contains: '页面包含', toast_contains: '提示消息',
  }
  return m[type] || type
}

const goReport = () => {
  const eid = executionId.value || currentExecutionId.value
  if (eid) router.push(`/ui-test/report/${eid}`)
}

const goBack = () => router.push('/ui-test/case')

onMounted(() => {
  fetchCaseDetail()
  nextTick(initCanvas)
})

onUnmounted(() => {
  if (ws) {
    ws.close()
    ws = null
  }
})
</script>

<style scoped>
.ui-execute-page {
  display: flex; flex-direction: column; height: 100%; padding: 12px; gap: 10px;
}

/* 顶部栏 */
.top-bar { display: flex; justify-content: space-between; align-items: center; }
.top-left { display: flex; align-items: center; gap: 10px; }
.top-left h3 { margin: 0; font-size: 18px; color: #303133; }
.top-right { display: flex; align-items: center; gap: 10px; }

/* 主内容区 */
.main-area { display: flex; gap: 12px; flex: 1; min-height: 0; }

/* ============ 左侧步骤面板 ============ */
.steps-panel {
  width: 340px; flex-shrink: 0; display: flex; flex-direction: column;
  background: #fff; border-radius: 8px; box-shadow: 0 1px 6px rgba(0,0,0,0.06); overflow: hidden;
}
.panel-header {
  padding: 10px 14px; font-weight: 600; font-size: 13px; color: #303133;
  border-bottom: 1px solid #f0f0f0; background: #fafafa;
  display: flex; justify-content: space-between; align-items: center;
}
.vision-badge {
  animation: pulse 2s ease-in-out infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}
.steps-scroll { flex: 1; overflow-y: auto; padding: 8px; }

.step-card {
  padding: 10px 12px; margin-bottom: 8px; border-radius: 8px;
  border: 1px solid #ebeef5; transition: all .2s;
}
.step-card.running { border-color: #e6a23c; background: #fdf6ec; }
.step-card.passed { border-color: #b3e19d; background: #f0f9eb; }
.step-card.failed { border-color: #fab6b6; background: #fef0f0; }

.step-top { display: flex; align-items: flex-start; gap: 8px; }
.step-badge {
  width: 24px; height: 24px; border-radius: 50%; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  font-size: 11px; font-weight: 700; color: #fff; background: #c0c4cc;
}
.step-badge.running { background: #e6a23c; }
.step-badge.passed { background: #67c23a; }
.step-badge.failed { background: #f56c6c; }

.step-info { flex: 1; min-width: 0; }
.step-action-text { font-size: 13px; color: #303133; line-height: 1.4; word-break: break-all; }
.step-sub { font-size: 11px; color: #909399; margin-top: 2px; }

/* AI决策信息 */
.step-ai-info {
  margin-top: 6px; padding: 5px 8px; border-radius: 4px;
  background: linear-gradient(135deg, #f5f3ff 0%, #ede9fe 100%);
  display: flex; align-items: flex-start; font-size: 11px;
  border: 1px solid #ddd6fe;
}
.ai-label { color: #7c3aed; font-weight: 600; margin-right: 4px; white-space: nowrap; }
.ai-desc { color: #6d28d9; line-height: 1.4; word-break: break-all; }

.step-result-area { margin-top: 6px; padding-top: 6px; border-top: 1px dashed #ebeef5; }
.step-result { font-size: 11px; color: #67c23a; line-height: 1.4; word-break: break-all; }
.step-result.failed { color: #f56c6c; }
.step-error { font-size: 11px; color: #f56c6c; line-height: 1.4; word-break: break-all; }
.step-time { font-size: 10px; color: #c0c4cc; margin-top: 3px; }

/* 步骤截图缩略图 */
.step-screenshot {
  margin-top: 6px; display: flex; align-items: center; gap: 6px;
}
.step-screenshot-img {
  width: 100px; height: 56px; border-radius: 4px; cursor: pointer;
  border: 1px solid #e0e0e0; overflow: hidden;
  transition: transform .2s, box-shadow .2s;
}
.step-screenshot-img:hover {
  transform: scale(1.05);
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
}
.screenshot-placeholder {
  width: 100%; height: 100%; display: flex; align-items: center; justify-content: center;
  background: #f5f7fa; color: #c0c4cc;
}
.screenshot-label { font-size: 10px; color: #909399; }

.summary-bar {
  padding: 10px 14px; display: flex; align-items: center; justify-content: space-between;
  font-weight: 600; font-size: 13px;
}
.summary-left { display: flex; align-items: center; gap: 8px; }
.summary-bar.passed { background: #f0f9eb; color: #67c23a; }
.summary-bar.failed { background: #fef0f0; color: #f56c6c; }

/* 断言信息 */
.step-assertion-info {
  margin-top: 6px; padding: 4px 8px; border-radius: 4px;
  display: flex; align-items: flex-start; gap: 4px; font-size: 11px;
  background: #f8fafc; border: 1px solid #e2e8f0;
}
.assertion-type-label { color: #475569; font-weight: 600; white-space: nowrap; }
.assertion-detail-text { line-height: 1.4; word-break: break-all; }
.assertion-detail-text.passed { color: #67c23a; }
.assertion-detail-text.failed { color: #f56c6c; }

/* ============ 右侧浏览器面板 ============ */
.browser-panel { flex: 1; display: flex; flex-direction: column; gap: 8px; min-width: 0; }

.browser-shell {
  flex: 1; display: flex; flex-direction: column;
  border-radius: 10px; overflow: hidden;
  box-shadow: 0 4px 20px rgba(0,0,0,0.12);
  border: 1px solid #e0e0e0;
}

.browser-toolbar {
  height: 38px; background: linear-gradient(180deg, #f7f7f7 0%, #ececec 100%);
  display: flex; align-items: center; padding: 0 12px; gap: 10px;
  border-bottom: 1px solid #d5d5d5;
}
.traffic-lights { display: flex; gap: 6px; }
.light {
  width: 11px; height: 11px; border-radius: 50%;
  box-shadow: inset 0 1px 2px rgba(0,0,0,0.15);
}
.light.close { background: #ff5f57; }
.light.minimize { background: #febc2e; }
.light.maximize { background: #28c840; }

.address-bar {
  flex: 1; display: flex; align-items: center; gap: 6px;
  background: #fff; border: 1px solid #d5d5d5; border-radius: 5px;
  padding: 3px 10px; font-size: 12px; color: #606266;
  overflow: hidden; white-space: nowrap; text-overflow: ellipsis;
}
.url-text { overflow: hidden; text-overflow: ellipsis; }
.toolbar-actions { display: flex; align-items: center; }

.browser-content {
  flex: 1; position: relative; background: #f5f5f5; overflow: hidden;
}
.browser-canvas {
  width: 100%; height: 100%; object-fit: contain; display: block; cursor: zoom-in;
}
.browser-overlay {
  position: absolute; inset: 0; display: flex; align-items: center; justify-content: center;
  background: linear-gradient(135deg, #f8f7ff 0%, #f0eeff 100%);
}
.overlay-content { text-align: center; }
.overlay-title { font-size: 18px; font-weight: 600; color: #303133; margin: 12px 0 4px; }
.overlay-desc { font-size: 13px; color: #909399; margin: 2px 0 16px; }

.overlay-features {
  display: flex; gap: 20px; justify-content: center;
}
.feature-item {
  display: flex; flex-direction: column; align-items: center; gap: 4px;
  font-size: 12px; color: #606266;
}
.feature-item .el-icon {
  font-size: 22px; color: #8b5cf6;
}

/* ============ 日志栏 ============ */
.log-bar {
  height: 140px; background: #1a1a2e; border-radius: 8px; overflow: hidden;
  display: flex; flex-direction: column;
}
.log-header {
  padding: 6px 12px; display: flex; justify-content: space-between; align-items: center;
  background: #16213e; color: #a0aec0; font-size: 12px; font-weight: 600;
}
.log-scroll {
  flex: 1; overflow-y: auto; padding: 6px 12px;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace; font-size: 12px;
}
.log-line { padding: 1px 0; display: flex; gap: 10px; align-items: flex-start; }
.log-ts { color: #4a5568; flex-shrink: 0; }
.log-text { color: #e2e8f0; word-break: break-all; }
.log-line.success .log-text { color: #68d391; }
.log-line.error .log-text { color: #fc8181; }
.log-line.ai .log-text { color: #b794f4; }
.log-ai-badge {
  flex-shrink: 0; font-size: 10px; font-weight: 700; color: #fff;
  background: linear-gradient(135deg, #8b5cf6 0%, #6d28d9 100%);
  padding: 0 5px; border-radius: 3px; line-height: 16px;
}
.log-empty { color: #4a5568; font-style: italic; }

.log-scroll::-webkit-scrollbar { width: 4px; }
.log-scroll::-webkit-scrollbar-thumb { background: #2d3748; border-radius: 2px; }
.steps-scroll::-webkit-scrollbar { width: 4px; }
.steps-scroll::-webkit-scrollbar-thumb { background: #dcdfe6; border-radius: 2px; }
</style>
