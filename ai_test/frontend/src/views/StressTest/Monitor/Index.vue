<template>
  <div class="monitor-container">
    <div class="page-header">
      <div class="header-left">
        <el-button text :icon="ArrowLeft" @click="$router.back()">返回</el-button>
        <h2>实时监控</h2>
        <el-tag :type="statusTag[taskStatus]" effect="dark" size="large" style="margin-left: 12px">
          {{ statusName[taskStatus] }}
        </el-tag>
      </div>
      <div class="header-right">
        <el-button v-if="taskStatus === 'pending'" type="success" :icon="VideoPlay" :loading="starting"
          @click="startExecution">开始压测</el-button>
        <el-button v-if="taskStatus === 'running'" type="danger" :icon="VideoPause"
          @click="handleStop">停止压测</el-button>
        <el-button v-if="taskStatus === 'completed'" type="primary" :icon="DataAnalysis"
          @click="$router.push({ name: 'StressTestReport', params: { taskId } })">查看报告</el-button>
      </div>
    </div>

    <!-- 实时指标仪表盘 -->
    <el-row :gutter="16" class="live-metrics">
      <el-col :span="6">
        <div class="live-card">
          <div class="live-icon" style="background: #409eff">👥</div>
          <div class="live-info">
            <div class="live-value">{{ latestMetric.current_users || 0 }}</div>
            <div class="live-label">当前并发</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="live-card">
          <div class="live-icon" style="background: #67c23a">⚡</div>
          <div class="live-info">
            <div class="live-value">{{ latestMetric.rps?.toFixed(1) || 0 }}</div>
            <div class="live-label">RPS</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="live-card">
          <div class="live-icon" style="background: #e6a23c">⏱️</div>
          <div class="live-info">
            <div class="live-value">{{ latestMetric.avg_rt?.toFixed(0) || 0 }}<small>ms</small></div>
            <div class="live-label">平均响应时间</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="live-card" :class="{ 'anomaly-flash': latestMetric.is_anomaly }">
          <div class="live-icon" :style="{ background: latestMetric.error_count > 0 ? '#f56c6c' : '#909399' }">❌</div>
          <div class="live-info">
            <div class="live-value">{{ totalErrors }}</div>
            <div class="live-label">累计错误</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- AI 异常告警 -->
    <transition-group name="alert-fade">
      <el-alert v-for="(alert, i) in anomalyAlerts" :key="alert.ts"
        :type="alert.severity === 'critical' ? 'error' : 'warning'"
        :title="`🤖 AI异常检测: ${alert.anomaly_type}`"
        :description="alert.description + (alert.suggestion ? ' | 建议: ' + alert.suggestion : '')"
        show-icon :closable="true" @close="anomalyAlerts.splice(i, 1)"
        style="margin-bottom: 8px" />
    </transition-group>

    <!-- 实时图表区域 -->
    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :span="12">
        <el-card shadow="never">
          <template #header><strong>📈 RPS 趋势</strong></template>
          <div class="chart-placeholder">
            <div class="sparkline">
              <div v-for="(m, i) in recentMetrics" :key="i" class="spark-bar"
                :style="{ height: sparkHeight(m.rps, maxRps) + 'px', background: m.is_anomaly ? '#f56c6c' : '#409eff' }"
                :title="`RPS: ${m.rps?.toFixed(1)} | ${new Date(m.timestamp * 1000).toLocaleTimeString()}`" />
            </div>
            <div class="chart-axis">
              <span>{{ recentMetrics[0] ? new Date(recentMetrics[0].timestamp * 1000).toLocaleTimeString() : '' }}</span>
              <span>{{ recentMetrics.length ? new Date(recentMetrics[recentMetrics.length-1].timestamp * 1000).toLocaleTimeString() : '' }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="never">
          <template #header><strong>⏱️ 响应时间趋势</strong></template>
          <div class="chart-placeholder">
            <div class="sparkline">
              <div v-for="(m, i) in recentMetrics" :key="i" class="spark-bar"
                :style="{ height: sparkHeight(m.avg_rt, maxRt) + 'px', background: m.avg_rt > 500 ? '#f56c6c' : m.avg_rt > 200 ? '#e6a23c' : '#67c23a' }"
                :title="`RT: ${m.avg_rt?.toFixed(0)}ms`" />
            </div>
            <div class="chart-axis">
              <span>{{ recentMetrics[0] ? new Date(recentMetrics[0].timestamp * 1000).toLocaleTimeString() : '' }}</span>
              <span>{{ recentMetrics.length ? new Date(recentMetrics[recentMetrics.length-1].timestamp * 1000).toLocaleTimeString() : '' }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 指标日志 -->
    <el-card shadow="never" style="margin-top: 16px">
      <template #header><strong>📋 指标日志 (最近50条)</strong></template>
      <el-table :data="recentMetrics.slice(-50).reverse()" size="small" max-height="300" stripe>
        <el-table-column label="时间" width="100">
          <template #default="{ row }">{{ new Date(row.timestamp * 1000).toLocaleTimeString() }}</template>
        </el-table-column>
        <el-table-column prop="current_users" label="并发" width="70" align="center" />
        <el-table-column label="RPS" width="80" align="center">
          <template #default="{ row }">{{ row.rps?.toFixed(1) }}</template>
        </el-table-column>
        <el-table-column label="RT(ms)" width="90" align="center">
          <template #default="{ row }">
            <span :style="{ color: row.avg_rt > 500 ? '#f56c6c' : '#67c23a' }">{{ row.avg_rt?.toFixed(0) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="error_count" label="错误" width="60" align="center" />
        <el-table-column label="异常" width="200">
          <template #default="{ row }">
            <el-tag v-if="row.is_anomaly" type="danger" size="small">{{ row.anomaly_reason }}</el-tag>
            <span v-else style="color: #c0c4cc">-</span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, VideoPlay, VideoPause, DataAnalysis } from '@element-plus/icons-vue'
import { stopTask, getMetrics } from '@/api/stressTest'

const route = useRoute()
const router = useRouter()
const taskId = computed(() => route.params.taskId)

const taskStatus = ref('pending')
const starting = ref(false)
const recentMetrics = ref([])
const anomalyAlerts = ref([])
let eventSource = null

const latestMetric = computed(() => recentMetrics.value.length ? recentMetrics.value[recentMetrics.value.length - 1] : {})
const totalErrors = computed(() => recentMetrics.value.reduce((sum, m) => sum + (m.error_count || 0), 0))
const maxRps = computed(() => Math.max(...recentMetrics.value.map(m => m.rps || 0), 1))
const maxRt = computed(() => Math.max(...recentMetrics.value.map(m => m.avg_rt || 0), 1))

const sparkHeight = (val, max) => Math.max(2, (val / max) * 120)

const statusName = { pending: '待执行', running: '运行中', completed: '已完成', failed: '失败', stopped: '已停止' }
const statusTag = { pending: 'info', running: 'primary', completed: 'success', failed: 'danger', stopped: 'warning' }

// SSE 执行压测
const startExecution = async () => {
  starting.value = true
  taskStatus.value = 'running'
  recentMetrics.value = []
  anomalyAlerts.value = []

  const token = localStorage.getItem('token')
  const baseUrl = import.meta.env.VITE_BASE_API || ''
  const url = `${baseUrl}/stress-test/tasks/${taskId.value}/execute`

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` }
    })

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
        try {
          const data = JSON.parse(line.slice(6))
          handleSSEMessage(data)
        } catch {}
      }
    }
  } catch (e) {
    ElMessage.error('压测执行失败: ' + e.message)
    taskStatus.value = 'failed'
  } finally {
    starting.value = false
  }
}

const handleSSEMessage = (data) => {
  if (data.type === 'status') {
    taskStatus.value = data.status
  } else if (data.type === 'metric') {
    recentMetrics.value.push(data.data)
    // 保留最近300个点
    if (recentMetrics.value.length > 300) recentMetrics.value.shift()
    // 异常告警
    if (data.data.is_anomaly && data.data.anomaly_reason) {
      anomalyAlerts.value.push({
        ts: Date.now(),
        severity: 'warning',
        anomaly_type: '指标异常',
        description: data.data.anomaly_reason,
        suggestion: '建议观察后续趋势，如持续恶化考虑停止压测',
      })
      if (anomalyAlerts.value.length > 5) anomalyAlerts.value.shift()
    }
  } else if (data.type === 'completed') {
    taskStatus.value = 'completed'
    ElMessage.success(`✅ 压测完成！TPS: ${data.summary?.tps?.toFixed(1)}, 平均RT: ${data.summary?.avg_rt?.toFixed(0)}ms, 错误率: ${data.summary?.error_rate}%`)
  } else if (data.type === 'error') {
    taskStatus.value = 'failed'
    ElMessage.error('压测失败: ' + data.message)
  }
}

const handleStop = async () => {
  await ElMessageBox.confirm('确认停止压测？', '停止确认', { type: 'warning' })
  try {
    await stopTask(taskId.value)
    taskStatus.value = 'stopped'
    ElMessage.success('已停止')
  } catch (e) {
    ElMessage.error('停止失败')
  }
}

// 加载历史指标
const loadHistoryMetrics = async () => {
  try {
    const res = await getMetrics(taskId.value, 300)
    const data = res.data || res
    if (data.items?.length) {
      recentMetrics.value = data.items
      taskStatus.value = 'completed'
    }
  } catch {}
}

onMounted(() => {
  loadHistoryMetrics()
})

onUnmounted(() => {
  if (eventSource) eventSource.close()
})
</script>

<style scoped>
.monitor-container { padding: 4px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h2 { margin: 0 0 0 8px; font-size: 20px; }
.header-left { display: flex; align-items: center; }

.live-metrics { margin-bottom: 8px; }
.live-card {
  display: flex; align-items: center; gap: 16px;
  padding: 20px; border-radius: 12px;
  background: #f5f7fa; transition: all 0.3s;
}
.live-card:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
.live-card.anomaly-flash { animation: flash 1s infinite; border: 2px solid #f56c6c; }
@keyframes flash { 0%,100% { background: #fef0f0; } 50% { background: #f5f7fa; } }
.live-icon { width: 48px; height: 48px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 24px; }
.live-value { font-size: 28px; font-weight: 700; color: #303133; }
.live-value small { font-size: 14px; color: #909399; }
.live-label { font-size: 13px; color: #909399; }

.chart-placeholder { height: 160px; display: flex; flex-direction: column; }
.sparkline { display: flex; align-items: flex-end; gap: 1px; flex: 1; padding: 8px 0; }
.spark-bar { flex: 1; min-width: 2px; border-radius: 2px 2px 0 0; transition: height 0.3s; cursor: pointer; }
.spark-bar:hover { opacity: 0.8; }
.chart-axis { display: flex; justify-content: space-between; font-size: 11px; color: #c0c4cc; }

.alert-fade-enter-active { transition: all 0.3s; }
.alert-fade-leave-active { transition: all 0.3s; }
.alert-fade-enter-from { opacity: 0; transform: translateX(20px); }
.alert-fade-leave-to { opacity: 0; transform: translateX(-20px); }
</style>
