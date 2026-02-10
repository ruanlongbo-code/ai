<template>
  <div class="dashboard">
    <div class="page-header">
      <h1>项目仪表盘</h1>
      <p>统计项目的概览信息</p>
    </div>

    <!-- 快捷操作（上移到统计卡片上方） -->
    <el-card class="quick-actions-card">
      <template #header>
        <div class="section-header">
          <span>快捷入口</span>
          <span class="subtitle">常用功能快速到达</span>
        </div>
      </template>
      <div class="quick-actions">
        <el-button type="primary" @click="goTo('ApiTestManagement')">
          <el-icon><Setting /></el-icon>
          接口管理
        </el-button>
        <el-button @click="goTo('ApiTestSuite')">
          <el-icon><Collection /></el-icon>
          测试套件
        </el-button>
        <el-button @click="goTo('ApiTestPlan')">
          <el-icon><Calendar /></el-icon>
          测试计划
        </el-button>
        <el-button @click="goTo('ProjectEnvironment')">
          <el-icon><Platform /></el-icon>
          测试环境
        </el-button>
        <el-button @click="goTo('ProjectMember')">
          <el-icon><User /></el-icon>
          成员管理
        </el-button>
      </div>
    </el-card>

    <!-- 统计卡片（第一行） -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon">
            <el-icon><Folder /></el-icon>
          </div>
          <div class="stat-content">
            <h3>{{ stats.projects }}</h3>
            <p>项目总数</p>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon">
            <el-icon><Connection /></el-icon>
          </div>
          <div class="stat-content">
            <h3>{{ stats.apiInterfaces }}</h3>
            <p>接口总数</p>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon">
            <el-icon><Setting /></el-icon>
          </div>
          <div class="stat-content">
            <h3>{{ stats.apiCases }}</h3>
            <p>API 用例</p>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon">
            <el-icon><Document /></el-icon>
          </div>
          <div class="stat-content">
            <h3>{{ stats.requirements }}</h3>
            <p>需求总数</p>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 统计卡片（第二行） -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon">
            <el-icon><DocumentChecked /></el-icon>
          </div>
          <div class="stat-content">
            <h3>{{ stats.functionalCases }}</h3>
            <p>功能用例</p>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon">
            <el-icon><Collection /></el-icon>
          </div>
          <div class="stat-content">
            <h3>{{ stats.suites }}</h3>
            <p>套件总数</p>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon">
            <el-icon><Calendar /></el-icon>
          </div>
          <div class="stat-content">
            <h3>{{ stats.tasks }}</h3>
            <p>任务总数</p>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon">
            <el-icon><VideoPlay /></el-icon>
          </div>
          <div class="stat-content">
            <h3>{{ stats.executions }}</h3>
            <p>近30天执行</p>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <!-- 近14天执行趋势（单独一行） -->
    <el-row :gutter="20" class="charts-row">
      <el-col :span="24">
        <div class="chart-card">
          <h3>近14天执行趋势</h3>
          <VChart :option="trendChartOption" autoresize style="height: 280px" />
        </div>
      </el-col>
    </el-row>
    <el-row :gutter="20" class="charts-row">
      <el-col :span="24">
        <div class="chart-card">
          <h3>近14天通过率趋势（折线）</h3>
          <VChart :option="caseTrend7dOption" autoresize style="height: 280px" />
        </div>
      </el-col>
    </el-row>

    <!-- 最近30次任务执行记录（卡片样式，与测试计划编辑页一致） -->
    <el-card class="task-runs-card">
      <template #header>
        <div class="section-header">
          <span>最近30次任务执行</span>
          <span class="subtitle">按时间倒序</span>
        </div>
      </template>
      <div class="history-content">
        <div v-if="!recentTaskRuns.length" class="empty-state">
          <el-empty description="暂无运行记录" />
        </div>
        <div v-else class="history-list">
          <div 
            v-for="record in recentTaskRuns" 
            :key="record.id" 
            class="history-item"
            @click="openTaskRunReport(record)"
            :class="{ 'running': record.status === 'running' }"
          >
            <div class="record-header">
              <div class="record-info">
                <div class="record-title">
                  <span class="run-id">#{{ record.id }}</span>
                  <el-tag 
                    :type="getStatusType(record.status)" 
                    size="small"
                    class="status-tag"
                  >
                    {{ getStatusText(record.status) }}
                  </el-tag>
                </div>
                <div class="record-meta">
                  <span class="meta-item">
                    <el-icon><Clock /></el-icon>
                    {{ formatDateTime(record.timestamp) }}
                  </span>
                </div>
              </div>
            </div>

            <div v-if="record.status !== 'running'" class="record-stats">
              <div class="stats-grid">
                <div class="stat-item">
                  <div class="stat-label">总用例</div>
                  <div class="stat-value">{{ record.total_cases || 0 }}</div>
                </div>
                <div class="stat-item success">
                  <div class="stat-label">通过</div>
                  <div class="stat-value">{{ record.passed_cases || 0 }}</div>
                </div>
                <div class="stat-item danger">
                  <div class="stat-label">失败</div>
                  <div class="stat-value">{{ record.failed_cases || 0 }}</div>
                </div>
                <div class="stat-item warning">
                  <div class="stat-label">跳过</div>
                  <div class="stat-value">{{ record.skipped_cases || 0 }}</div>
                </div>
                <div class="stat-item">
                  <div class="stat-label">耗时</div>
                  <div class="stat-value">{{ formatDuration(record.duration) }}</div>
                </div>
              </div>
              <div class="progress-section" v-if="record.total_cases > 0">
                <el-progress 
                  :percentage="getSuccessRate(record)" 
                  :color="getProgressColor(record)"
                  :show-text="false"
                  :stroke-width="6"
                />
                <div class="progress-text">成功率: {{ getSuccessRate(record) }}%</div>
              </div>
            </div>

            <div v-else class="running-progress">
              <div class="running-info">
                <el-icon class="spinning"><Loading /></el-icon>
                <span>测试计划正在运行中...</span>
              </div>
              <el-progress :percentage="50" :indeterminate="true" :stroke-width="6" />
            </div>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useProjectStore } from '@/stores'
import { ElMessage } from 'element-plus'
import { getProjectDashboard } from '@/api/project'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, BarChart } from 'echarts/charts'
import { TitleComponent, TooltipComponent, LegendComponent, GridComponent } from 'echarts/components'
import { Clock, Loading } from '@element-plus/icons-vue'

// 注册 ECharts 组件
use([CanvasRenderer, LineChart, BarChart, TitleComponent, TooltipComponent, LegendComponent, GridComponent])

const route = useRoute()
const router = useRouter()
const projectStore = useProjectStore()

// 项目ID来源优先级：路由参数 > Pinia当前项目 > localStorage备份 > 默认1
const getProjectId = () => {
  const fromRoute = Number(route.params.projectId)
  if (fromRoute) return fromRoute
  const fromStore = Number(projectStore.currentProject?.id)
  if (fromStore) return fromStore
  try {
    const cached = localStorage.getItem('currentProject')
    const parsed = cached ? JSON.parse(cached) : null
    const fromStorage = Number(parsed?.id)
    if (fromStorage) return fromStorage
  } catch {}
  return 1
}

const projectId = ref(getProjectId())

const stats = ref({
  projects: 0,
  apiInterfaces: 0,
  apiCases: 0,
  requirements: 0,
  functionalCases: 0,
  suites: 0,
  tasks: 0,
  executions: 0
})

const activities = ref([])

const trendChartOption = ref({
  grid: { left: 40, right: 20, top: 60, bottom: 60, containLabel: true },
  tooltip: { trigger: 'axis' },
  legend: { data: ['执行次数', '通过', '失败', '错误', '跳过'], top: 8, left: 'center' },
  xAxis: { type: 'category', data: [] },
  yAxis: { type: 'value' },
  series: [
    { name: '执行次数', type: 'line', data: [], smooth: true, itemStyle: { color: '#909399' } },
    { name: '通过', type: 'line', data: [], smooth: true, itemStyle: { color: '#67C23A' } },
    { name: '失败', type: 'line', data: [], smooth: true, itemStyle: { color: '#F56C6C' } },
    { name: '错误', type: 'line', data: [], smooth: true, itemStyle: { color: '#E6A23C' } },
    { name: '跳过', type: 'line', data: [], smooth: true, itemStyle: { color: '#409EFF' } }
  ]
})



const caseTrend7dOption = ref({
  grid: { left: 40, right: 20, top: 60, bottom: 60, containLabel: true },
  tooltip: { trigger: 'axis' },
  legend: { data: ['通过率'], top: 8, left: 'center' },
  xAxis: { type: 'category', data: [] },
  yAxis: { type: 'value', name: '通过率(%)', min: 0, max: 100 },
  series: [
    { name: '通过率', type: 'line', data: [], smooth: true, itemStyle: { color: '#67C23A' } }
  ]
})

const lastTaskSummary = ref(null)
const recentTaskRuns = ref([])

// 状态映射与展示辅助
const getStatusType = (status) => {
  const map = { running: 'info', success: 'success', failed: 'danger', cancelled: 'warning', pending: 'info', completed: 'success' }
  return map[status] || 'info'
}

const getStatusText = (status) => {
  const map = { running: '运行中', success: '成功', failed: '失败', cancelled: '已取消', pending: '待开始', completed: '成功' }
  return map[status] || status
}

const formatDateTime = (dateTime) => {
  if (!dateTime) return '-'
  try {
    return new Date(dateTime).toLocaleString()
  } catch { return String(dateTime) }
}

const formatDuration = (duration) => {
  if (!duration) return '-'
  if (duration < 60) return `${Number(duration).toFixed(1)}秒`
  const minutes = Math.floor(Number(duration) / 60)
  const seconds = (Number(duration) % 60).toFixed(1)
  return `${minutes}分${seconds}秒`
}

const getSuccessRate = (record) => {
  const total = Number(record?.total_cases || 0)
  const passed = Number(record?.passed_cases || 0)
  if (!total) return 0
  return Math.round((passed / total) * 100)
}

const getProgressColor = (record) => {
  const rate = getSuccessRate(record)
  if (rate >= 80) return '#67c23a'
  if (rate >= 60) return '#e6a23c'
  return '#f56c6c'
}

const fetchDashboard = async () => {
  try {
    const pid = Number(projectId.value)
    if (!pid) throw new Error('缺少项目ID')
    const resp = await getProjectDashboard(pid)
    const data = resp.data || {}

    // 映射统计卡片（兼容缺省字段）
    stats.value.projects = data.projects ?? 1
    stats.value.apiInterfaces = data.api_interfaces ?? 0
    stats.value.apiCases = data.api_cases ?? 0
    stats.value.requirements = data.requirements ?? 0
    stats.value.functionalCases = data.functional_cases ?? 0
    stats.value.suites = data.suites ?? 0
    stats.value.tasks = data.tasks ?? 0
    stats.value.executions = data.executions ?? 0

    // 最近活动
    activities.value = Array.isArray(data.activities) ? data.activities : []

    // 近14天执行趋势（五条曲线：执行次数/通过/失败/错误/跳过）
    const labels = (data.trend || []).map(i => i.date)
    const runs = (data.trend || []).map(i => i.runs ?? 0)
    const passed = (data.trend || []).map(i => i.passed ?? 0)
    const failed = (data.trend || []).map(i => i.failed ?? 0)
    const errors = (data.trend || []).map(i => i.errors ?? 0)
    const skipped = (data.trend || []).map(i => i.skipped ?? 0)
    trendChartOption.value = {
      ...trendChartOption.value,
      xAxis: { type: 'category', data: labels },
      series: [
        { name: '执行次数', type: 'line', data: runs, smooth: true, itemStyle: { color: '#909399' } },
        { name: '通过', type: 'line', data: passed, smooth: true, itemStyle: { color: '#67C23A' } },
        { name: '失败', type: 'line', data: failed, smooth: true, itemStyle: { color: '#F56C6C' } },
        { name: '错误', type: 'line', data: errors, smooth: true, itemStyle: { color: '#E6A23C' } },
        { name: '跳过', type: 'line', data: skipped, smooth: true, itemStyle: { color: '#409EFF' } }
      ]
    }



    // 近14天通过率趋势（基于 trend：passed / runs * 100）
    const tPoints = Array.isArray(data.trend) ? data.trend : []
    const rateLabels = tPoints.map(i => i.date)
    const rateSeries = tPoints.map(i => {
      const runs = Number(i?.runs || 0)
      const passed = Number(i?.passed || 0)
      return runs > 0 ? Math.round((passed / runs) * 10000) / 100 : 0
    })
    caseTrend7dOption.value = {
      ...caseTrend7dOption.value,
      xAxis: { type: 'category', data: rateLabels },
      series: [
        { name: '通过率', type: 'line', data: rateSeries, smooth: true, itemStyle: { color: '#67C23A' } }
      ]
    }

    // 最近一次任务摘要与最近30次任务
    lastTaskSummary.value = data.last_task_summary || null
    recentTaskRuns.value = Array.isArray(data.recent_task_runs) ? data.recent_task_runs : []
  } catch (e) {
    console.error('获取仪表盘失败', e)
    ElMessage.error('获取仪表盘数据失败')
  }
}

const goTo = (name) => {
  // 将项目ID带入到需要的路由
  const namedRoutesWithProject = new Set(['ApiTestManagement'])
  if (namedRoutesWithProject.has(name)) {
    router.push({ name, params: { projectId: projectId.value } })
  } else {
    router.push({ name })
  }
}

const openTaskRunReport = (record) => {
  try {
    const runId = Number(record?.id)
    const pid = Number(projectId.value)
    if (!runId || !pid) return
    router.push({ name: 'TaskRunReport', params: { projectId: pid, runId } })
  } catch (e) {
    console.error('打开任务执行报告失败', e)
  }
}

onMounted(() => {
  fetchDashboard()
})
</script>

<style scoped>
.dashboard {
  padding: 20px;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h1 {
  color: #1f2937;
  margin: 0 0 8px 0;
  font-size: 28px;
  font-weight: 700;
}

.page-header p {
  color: #6b7280;
  margin: 0;
  font-size: 14px;
}

/* 统计卡片 */
.stats-row {
  margin-bottom: 24px;
}

.stat-card {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 24px;
  display: flex;
  align-items: center;
  transition: all 0.2s ease;
  cursor: pointer;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(31, 41, 55, 0.08);
  border-color: #d1d5db;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  background: linear-gradient(135deg, #ede9fe, #e9d5ff);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16px;
  box-shadow: 0 4px 10px rgba(139, 92, 246, 0.15);
}

.stat-icon .el-icon {
  font-size: 24px;
  color: #7c3aed;
}

.stat-content h3 {
  color: #1f2937;
  margin: 0 0 4px 0;
  font-size: 24px;
  font-weight: 700;
}

.stat-content p {
  color: #6b7280;
  margin: 0;
  font-size: 14px;
}

/* 图表卡片 */
.charts-row {
  margin-bottom: 24px;
}

.chart-card {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 24px;
  height: 300px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}

.chart-card h3 {
  color: #1f2937;
  margin: 0 0 20px 0;
  font-size: 18px;
  font-weight: 600;
}

.chart-placeholder {
  height: 220px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #9ca3af;
}

.chart-placeholder .el-icon {
  font-size: 48px;
  margin-bottom: 12px;
  color: #9ca3af;
}

/* 最近活动 */
.activity-card {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}

.activity-card h3 {
  color: #1f2937;
  margin: 0 0 20px 0;
  font-size: 18px;
  font-weight: 600;
}

:deep(.el-timeline-item__timestamp) {
  color: #6b7280;
}

:deep(.el-timeline-item__content) {
  color: #1f2937;
}

.quick-actions-card {
  margin-bottom: 24px;
}

.quick-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.section-header .subtitle {
  font-size: 12px;
  color: #909399;
}

.summary-card {
  margin-top: 24px;
}
.summary-content {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px 16px;
}
.summary-item {
  color: #1f2937;
}

.task-runs-card {
  margin-top: 24px;
}

/* 执行记录卡片样式（与测试计划编辑页面一致） */
.history-content {
  display: flex;
  flex-direction: column;
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.history-item {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 20px;
  transition: all 0.2s ease;
}

.history-item:hover {
  border-color: #d1d5db;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.history-item.running {
  border-color: #3b82f6;
  background: #f0f9ff;
}

.record-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.record-info { flex: 1; }

.record-title {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.run-id { font-weight: 600; font-size: 16px; color: #374151; }
.status-tag { font-weight: 500; }

.record-meta {
  display: flex;
  gap: 16px;
  color: #6b7280;
  font-size: 14px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.record-stats { margin-bottom: 16px; }
.stats-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 12px;
  margin-bottom: 12px;
}

.stat-item {
  text-align: center;
  padding: 12px;
  background: #f8fafc;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
}
.stat-item.success { background: #f0fdf4; border-color: #bbf7d0; }
.stat-item.danger { background: #fef2f2; border-color: #fecaca; }
.stat-item.warning { background: #fffbeb; border-color: #fed7aa; }

.stat-label { font-size: 12px; color: #6b7280; margin-bottom: 4px; }
.stat-value { font-size: 16px; font-weight: 600; color: #374151; }

.progress-section { display: flex; align-items: center; gap: 12px; }
.progress-text { font-size: 14px; color: #6b7280; white-space: nowrap; }

.running-progress { margin-bottom: 16px; }
.running-info {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  color: #3b82f6;
  font-weight: 500;
}

.spinning { animation: spin 1s linear infinite; }
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
</style>