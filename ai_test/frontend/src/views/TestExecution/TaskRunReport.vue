<template>
  <div class="task-run-report">
    <div class="page-header">
      <h1>
        <el-icon><Document /></el-icon>
        任务执行详情
      </h1>
    </div>
    <div v-if="loading" class="loading">
      <el-skeleton :rows="6" animated />
    </div>

    <div v-else-if="report" class="content">
      <!-- 基本信息与统计 -->
      <el-card class="summary-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <el-icon><InfoFilled /></el-icon>
            <span>任务运行概要</span>
          </div>
        </template>
        <div class="info-grid">
          <div class="info-item">
            <label>任务名称：</label>
            <span>{{ report.task_name }}</span>
          </div>
          <div class="info-item">
            <label>开始时间：</label>
            <span>{{ formatDateTime(report.start_time) }}</span>
          </div>
          <div class="info-item">
            <label>结束时间：</label>
            <span>{{ formatDateTime(report.end_time) }}</span>
          </div>
          <div class="info-item">
            <label>执行耗时：</label>
            <span>{{ formatDuration(report.duration) }}</span>
          </div>
          <div class="info-item">
            <label>执行状态：</label>
            <el-tag :type="getStatusType(report.status)">{{ getStatusText(report.status) }}</el-tag>
          </div>
        </div>

        <div class="stats-grid">
          <div class="stat-item">
            <div class="stat-label">总套件</div>
            <div class="stat-value">{{ report.total_suites || 0 }}</div>
          </div>
          <div class="stat-item">
            <div class="stat-label">总用例</div>
            <div class="stat-value">{{ report.total_cases || 0 }}</div>
          </div>
          <div class="stat-item success">
            <div class="stat-label">通过</div>
            <div class="stat-value">{{ report.passed_cases || 0 }}</div>
          </div>
          <div class="stat-item danger">
            <div class="stat-label">失败</div>
            <div class="stat-value">{{ report.failed_cases || 0 }}</div>
          </div>
          <div class="stat-item warning">
            <div class="stat-label">跳过</div>
            <div class="stat-value">{{ report.skipped_cases || 0 }}</div>
          </div>
        </div>

        <div class="progress-section" v-if="report.total_cases > 0">
          <el-progress :percentage="getSuccessRate(report)" :show-text="false" :stroke-width="6" />
          <div class="progress-text">成功率: {{ getSuccessRate(report) }}%</div>
        </div>
      </el-card>

      <!-- 套件运行记录列表 -->
      <el-card class="suite-runs-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <el-icon><List /></el-icon>
            <span>套件运行记录 ({{ report.suite_runs?.length || 0 }})</span>
          </div>
        </template>
        <div class="suite-list">
          <div
            v-for="sr in report.suite_runs"
            :key="sr.id"
            class="suite-item"
            @click="openSuiteRun(sr)"
          >
            <div class="suite-header">
              <div class="suite-title">
                <el-icon><Collection /></el-icon>
                <span>{{ sr.suite_name }}</span>
              </div>
              <el-tag :type="getStatusType(sr.status)" size="small">{{ getStatusText(sr.status) }}</el-tag>
            </div>
            <div class="suite-meta">
              <span class="meta-item"><el-icon><Clock /></el-icon>{{ formatDateTime(sr.start_time) }}</span>
              <span class="meta-item"><el-icon><Timer /></el-icon>{{ formatDuration(sr.duration) }}</span>
            </div>
            <div class="suite-stats">
              <span>总用例: {{ sr.total_cases || 0 }}</span>
              <span>通过: {{ sr.passed_cases || 0 }}</span>
              <span>失败: {{ sr.failed_cases || 0 }}</span>
              <span>跳过: {{ sr.skipped_cases || 0 }}</span>
            </div>
          </div>
        </div>
      </el-card>
    </div>

    <div v-else class="error">
      <el-result icon="error" title="加载失败" sub-title="无法获取任务执行报告">
        <template #extra>
          <el-button type="primary" @click="loadReport">重新加载</el-button>
        </template>
      </el-result>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Document, InfoFilled, List, Clock, Timer, Collection } from '@element-plus/icons-vue'
import { getTaskRunDetail } from '@/api/test_execution'

const route = useRoute()
const router = useRouter()
const projectId = ref(Number(route.params.projectId))
const runId = ref(Number(route.params.runId))

const loading = ref(true)
const report = ref(null)

const formatDateTime = (dt) => {
  if (!dt) return '-'
  try { return new Date(dt).toLocaleString() } catch { return String(dt) }
}
const formatDuration = (d) => {
  if (!d && d !== 0) return '-'
  const num = Number(d)
  if (num < 60) return `${num.toFixed(1)}秒`
  const m = Math.floor(num / 60)
  const s = (num % 60).toFixed(1)
  return `${m}分${s}秒`
}
const getStatusType = (status) => {
  const map = { running: 'info', success: 'success', passed: 'success', failed: 'danger', error: 'danger', cancelled: 'warning', completed: 'success' }
  return map[status] || 'info'
}
const getStatusText = (status) => {
  const map = { running: '运行中', success: '成功', passed: '成功', failed: '失败', error: '错误', cancelled: '已取消', completed: '成功' }
  return map[status] || status
}
const getSuccessRate = (obj) => {
  const total = Number(obj?.total_cases || 0)
  const passed = Number(obj?.passed_cases || 0)
  if (!total) return 0
  return Math.round((passed / total) * 100)
}

const loadReport = async () => {
  try {
    loading.value = true
    const resp = await getTaskRunDetail(projectId.value, runId.value)
    report.value = resp?.data || null
  } catch (e) {
    console.error('加载任务运行报告失败', e)
    ElMessage.error('加载任务运行报告失败')
  } finally {
    loading.value = false
  }
}

const openSuiteRun = (sr) => {
  try {
    const suiteRunId = Number(sr?.id)
    const pid = Number(projectId.value)
    const suiteId = sr?.suite_id ?? sr?.suiteId
    if (!suiteRunId || !pid) return
    router.push({ name: 'SuiteRunReport', params: { projectId: pid, runId: suiteRunId, suiteId } })
  } catch (e) {
    console.error('打开套件运行报告失败', e)
  }
}

onMounted(() => {
  loadReport()
})
</script>

<style scoped>

/* 页面容器与标题 */
.task-run-report { 
  padding: 20px; 

  margin: 0 auto;
}
.page-header { 
  margin-bottom: 20px; 
}
.page-header h1 { 
  display: flex; 
  align-items: center; 
  gap: 8px; 
  margin: 0 0 6px 0; 
  font-size: 22px;
  color: #1f2937;
}
.page-header p { 
  color: #6b7280; 
  margin: 0; 
  font-size: 13px;
}


.card-header { 
  display: flex; 
  align-items: center; 
  gap: 8px; 
  font-weight: 600;
}
.summary-card { 
  margin-bottom: 20px; 
}
.info-grid { 
  display: grid; 
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); 
  gap: 12px 16px; 
  margin-bottom: 16px; 
}
.info-item label { 
  color: #6b7280; 
  margin-right: 8px; 
  min-width: 72px;
}


.stats-grid { 
  display: grid; 
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); 
  gap: 12px; 
  margin-bottom: 12px; 
}
.stat-item { 
  text-align: center; 
  padding: 14px; 
  border-radius: 8px; 
  border: 1px solid #e5e7eb; 
  background: #f8fafc; 
}
.stat-item.success { 
  background: linear-gradient(135deg, #67C23A20, #67C23A10);
  border-color: #bbf7d0;
}
.stat-item.danger { 
  background: linear-gradient(135deg, #F56C6C20, #F56C6C10);
  border-color: #fecaca; 
}
.stat-item.warning { 
  background: linear-gradient(135deg, #E6A23C20, #E6A23C10);
  border-color: #fed7aa; 
}
.stat-label { 
  font-size: 12px; 
  color: #6b7280; 
  margin-bottom: 4px; 
}
.stat-value { 
  font-size: 18px; 
  font-weight: 700; 
  color: #374151; 
}


.progress-section { 
  display: flex; 
  align-items: center; 
  gap: 12px; 
  margin-top: 8px;
}
.progress-text { 
  font-size: 13px; 
  color: #6b7280; 
  white-space: nowrap; 
}


.suite-list { 
  display: grid; 
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); 
  gap: 12px; 
}
.suite-item { 
  padding: 16px; 
  border: 1px solid #EBEEF5; 
  border-radius: 10px; 
  background: #fff; 
  transition: border-color 0.15s ease, box-shadow 0.15s ease, transform 0.15s ease;
  cursor: pointer;
}
.suite-item:hover { 
  border-color: #dcdfe6; 
  box-shadow: 0 2px 8px rgba(0,0,0,0.06); 
  transform: translateY(-1px);
}
.suite-header { 
  display: flex; 
  justify-content: space-between; 
  align-items: center; 
  margin-bottom: 8px; 
}
.suite-title { 
  display: flex; 
  align-items: center; 
  gap: 8px; 
  font-weight: 600; 
  font-size: 16px; 
}
.suite-meta { 
  display: flex; 
  gap: 20px; 
  font-size: 13px; 
  color: #909399; 
  margin-bottom: 8px; 
}
.meta-item { 
  display: flex; 
  align-items: center; 
  gap: 4px; 
}
.suite-stats { 
  display: flex; 
  gap: 16px; 
  color: #374151; 
  font-size: 13px; 
}


.loading, .error { padding: 20px; }

/* 响应式优化 */
@media (max-width: 1024px) {
  .stat-value { font-size: 16px; }
  .info-grid { grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); }
}
@media (max-width: 768px) {
  .page-header h1 { font-size: 20px; }
  .progress-section { flex-direction: column; align-items: stretch; }
  .progress-text { margin-left: 0; }
}
</style>