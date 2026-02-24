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
        <div class="panel-header">测试步骤 ({{ steps.length }})</div>
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
            <div v-if="step._actual_result || step._error" class="step-result-area">
              <div v-if="step._actual_result" class="step-result" :class="{ failed: step._status === 'failed' }">
                {{ step._actual_result }}
              </div>
              <div v-if="step._error" class="step-error">{{ step._error }}</div>
              <div v-if="step._duration" class="step-time">{{ step._duration }}ms</div>
            </div>
          </div>
        </div>

        <!-- 执行结果摘要 -->
        <div v-if="executionDone" class="summary-bar" :class="finalStatus">
          <el-icon v-if="finalStatus === 'passed'"><SuccessFilled /></el-icon>
          <el-icon v-else><CircleCloseFilled /></el-icon>
          <span>{{ passedCount }} 通过 / {{ failedCount }} 失败</span>
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
              <el-icon v-if="executing" class="is-loading" style="color:#e6a23c;"><Loading /></el-icon>
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
                <p class="overlay-title">AI 内嵌浏览器</p>
                <p class="overlay-desc">点击「开始 AI 执行」，AI 将自动操作浏览器执行测试步骤</p>
                <p class="overlay-desc">执行过程中可实时观看浏览器操作画面</p>
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
import { Loading, SuccessFilled, CircleCloseFilled } from '@element-plus/icons-vue'
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
  })

  initCanvas()
  if (canvasCtx) canvasCtx.clearRect(0, 0, 1280, 720)

  const token = localStorage.getItem('token') || ''
  const url = `${WS_BASE}/ui_test/${projectId()}/cases/${caseId()}/ws-execute?token=${token}`

  addLog('正在连接执行服务...')

  ws = new WebSocket(url)

  ws.onopen = () => {
    connecting.value = false
    executing.value = true
    addLog('连接成功，AI 浏览器启动中...')
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
    addLog(`AI 决策: ${data.action}`, 'info')
  } else if (type === 'step_done') {
    const step = steps.value.find(s => s.id === data.step_id)
    if (step) {
      step._status = data.status
      step._actual_result = data.actual_result
      step._error = data.error_message
      step._duration = data.duration_ms
    }
    if (data.status === 'passed') {
      passedCount.value++
      addLog(`  ✓ 通过 — ${data.actual_result || ''}`, 'success')
    } else {
      failedCount.value++
      addLog(`  ✗ 失败 — ${data.error_message || data.actual_result || ''}`, 'error')
    }
  } else if (type === 'done') {
    executionDone.value = true
    executing.value = false
    finalStatus.value = data.status
    execStatus.value = data.status
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
  width: 300px; flex-shrink: 0; display: flex; flex-direction: column;
  background: #fff; border-radius: 8px; box-shadow: 0 1px 6px rgba(0,0,0,0.06); overflow: hidden;
}
.panel-header {
  padding: 10px 14px; font-weight: 600; font-size: 13px; color: #303133;
  border-bottom: 1px solid #f0f0f0; background: #fafafa;
}
.steps-scroll { flex: 1; overflow-y: auto; padding: 8px; }

.step-card {
  padding: 8px 10px; margin-bottom: 6px; border-radius: 6px;
  border: 1px solid #ebeef5; transition: all .15s;
}
.step-card.running { border-color: #e6a23c; background: #fdf6ec; }
.step-card.passed { border-color: #b3e19d; background: #f0f9eb; }
.step-card.failed { border-color: #fab6b6; background: #fef0f0; }

.step-top { display: flex; align-items: flex-start; gap: 8px; }
.step-badge {
  width: 22px; height: 22px; border-radius: 50%; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  font-size: 11px; font-weight: 700; color: #fff; background: #c0c4cc;
}
.step-badge.running { background: #e6a23c; }
.step-badge.passed { background: #67c23a; }
.step-badge.failed { background: #f56c6c; }

.step-info { flex: 1; min-width: 0; }
.step-action-text { font-size: 13px; color: #303133; line-height: 1.4; word-break: break-all; }
.step-sub { font-size: 11px; color: #909399; margin-top: 2px; }

.step-result-area { margin-top: 6px; padding-top: 6px; border-top: 1px dashed #ebeef5; }
.step-result { font-size: 11px; color: #67c23a; }
.step-result.failed { color: #f56c6c; }
.step-error { font-size: 11px; color: #f56c6c; }
.step-time { font-size: 10px; color: #c0c4cc; margin-top: 2px; }

.summary-bar {
  padding: 10px 14px; display: flex; align-items: center; gap: 8px;
  font-weight: 600; font-size: 13px;
}
.summary-bar.passed { background: #f0f9eb; color: #67c23a; }
.summary-bar.failed { background: #fef0f0; color: #f56c6c; }

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
.toolbar-actions { width: 24px; }

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
.overlay-desc { font-size: 13px; color: #909399; margin: 2px 0; }

/* ============ 日志栏 ============ */
.log-bar {
  height: 130px; background: #1a1a2e; border-radius: 8px; overflow: hidden;
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
.log-line { padding: 1px 0; display: flex; gap: 10px; }
.log-ts { color: #4a5568; flex-shrink: 0; }
.log-text { color: #e2e8f0; }
.log-line.success .log-text { color: #68d391; }
.log-line.error .log-text { color: #fc8181; }
.log-empty { color: #4a5568; font-style: italic; }

.log-scroll::-webkit-scrollbar { width: 4px; }
.log-scroll::-webkit-scrollbar-thumb { background: #2d3748; border-radius: 2px; }
.steps-scroll::-webkit-scrollbar { width: 4px; }
.steps-scroll::-webkit-scrollbar-thumb { background: #dcdfe6; border-radius: 2px; }
</style>
