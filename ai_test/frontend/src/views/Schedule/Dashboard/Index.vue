<template>
  <div class="dashboard-container">
    <!-- 顶部选择器 -->
    <div class="dashboard-header">
      <div class="header-left">
        <el-select v-model="currentIterationId" placeholder="选择迭代" @change="loadDashboard" style="width: 240px">
          <el-option v-for="it in iterations" :key="it.id" :label="it.name" :value="it.id" />
        </el-select>
        <el-radio-group v-model="viewMode" @change="loadDashboard" style="margin-left: 12px">
          <el-radio-button value="daily">当日动态</el-radio-button>
          <el-radio-button value="summary">迭代汇总</el-radio-button>
        </el-radio-group>
      </div>
      <div class="header-right">
        <el-date-picker
          v-if="viewMode === 'daily'"
          v-model="targetDate"
          type="date"
          value-format="YYYY-MM-DD"
          placeholder="选择日期"
          @change="loadDaily"
          style="width: 160px"
        />
        <el-button @click="loadDashboard">
          <el-icon><Refresh /></el-icon> 刷新
        </el-button>
      </div>
    </div>

    <!-- ========== 当日动态视图 ========== -->
    <div v-if="viewMode === 'daily'" v-loading="loading">
      <!-- 当日统计概览 -->
      <el-row :gutter="16" class="daily-stats">
        <el-col :span="8">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-icon">🧪</div>
            <div>
              <div class="stat-label">今日执行用例</div>
              <div class="stat-num">{{ dailyData.daily_cases_executed || 0 }}</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="8">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-icon">🐛</div>
            <div>
              <div class="stat-label">今日新增Bug</div>
              <div class="stat-num">{{ dailyData.daily_bugs_new || 0 }}</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="8">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-icon">✅</div>
            <div>
              <div class="stat-label">今日关闭Bug</div>
              <div class="stat-num">{{ dailyData.daily_bugs_closed || 0 }}</div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 未提交日报提醒 -->
      <el-alert
        v-if="dailyData.no_report_users && dailyData.no_report_users.length > 0"
        type="warning"
        :closable="false"
        class="no-report-alert"
      >
        <template #title>
          ⚠️ 以下成员今日未提交日报：{{ dailyData.no_report_users.join('、') }}
        </template>
      </el-alert>

      <!-- 按人分组的日报卡片 -->
      <div v-for="update in dailyData.updates" :key="update.reporter_id" class="person-card">
        <el-card>
          <template #header>
            <div class="person-header">
              <el-avatar :size="32">{{ update.reporter_name.charAt(0) }}</el-avatar>
              <span class="person-name">{{ update.reporter_name }}</span>
              <el-tag type="success" size="small">{{ update.reports.length }} 条更新</el-tag>
            </div>
          </template>

          <div v-for="report in update.reports" :key="report.id" class="report-item">
            <div class="report-requirement">
              <strong>{{ report.requirement_title }}</strong>
              <span class="report-progress">进度: {{ report.actual_progress }}%</span>
              <span class="report-risk">{{ riskIcon(report.risk_level) }}</span>
            </div>
            <div class="report-detail">
              <div class="report-progress-text">{{ report.today_progress }}</div>
              <div class="report-meta" v-if="report.bug_total > 0 || report.case_execution_progress > 0">
                <span v-if="report.case_execution_progress > 0">用例执行: {{ report.case_execution_progress }}%</span>
                <span v-if="report.bug_total > 0">Bug: {{ report.bug_total }}个({{ report.bug_open }}待处理)</span>
              </div>
              <div class="report-plan" v-if="report.next_plan">
                <span class="plan-label">明日计划：</span>{{ report.next_plan }}
              </div>
            </div>
          </div>
        </el-card>
      </div>

      <el-empty v-if="!dailyData.updates || dailyData.updates.length === 0" description="暂无当日动态" />
    </div>

    <!-- ========== 迭代汇总视图 ========== -->
    <div v-if="viewMode === 'summary'" v-loading="loading">
      <template v-if="summaryData.iteration_id">
        <!-- 迭代信息卡 -->
        <el-card class="iteration-overview">
          <el-row :gutter="24">
            <el-col :span="6">
              <div class="overview-item">
                <div class="overview-label">整体进度</div>
                <el-progress type="circle" :percentage="summaryData.overall_progress" :width="80"
                            :color="progressColor(summaryData.overall_progress)" />
              </div>
            </el-col>
            <el-col :span="4">
              <div class="overview-item">
                <div class="overview-label">总需求</div>
                <div class="overview-value">{{ summaryData.total_requirements }}</div>
              </div>
            </el-col>
            <el-col :span="4">
              <div class="overview-item">
                <div class="overview-label">已完成</div>
                <div class="overview-value" style="color: #67c23a">{{ summaryData.completed_requirements }}</div>
              </div>
            </el-col>
            <el-col :span="4">
              <div class="overview-item">
                <div class="overview-label">测试中</div>
                <div class="overview-value" style="color: #409eff">{{ summaryData.testing_requirements }}</div>
              </div>
            </el-col>
            <el-col :span="3">
              <div class="overview-item">
                <div class="overview-label">总Bug</div>
                <div class="overview-value">{{ summaryData.total_bugs }}</div>
              </div>
            </el-col>
            <el-col :span="3">
              <div class="overview-item">
                <div class="overview-label">剩余天数</div>
                <div class="overview-value" :class="{ 'text-danger': summaryData.remaining_days <= 3 }">
                  {{ summaryData.remaining_days }}
                </div>
              </div>
            </el-col>
          </el-row>
        </el-card>

        <!-- 风险预警区域（收尾模式） -->
        <template v-if="summaryData.is_closing && summaryData.high_risk_items.length > 0">
          <el-card class="risk-section">
            <template #header>
              <span>🔴 高风险需求 ({{ summaryData.high_risk_items.length }})</span>
            </template>
            <el-table :data="summaryData.high_risk_items" border>
              <el-table-column prop="requirement_title" label="需求" min-width="200" />
              <el-table-column prop="assignee_name" label="负责人" width="90" />
              <el-table-column label="进度" width="100" align="center">
                <template #default="{ row }">
                  <el-progress :percentage="row.actual_progress" :stroke-width="8" :color="'#f56c6c'" />
                </template>
              </el-table-column>
              <el-table-column prop="risk_reason" label="风险原因" min-width="200" />
              <el-table-column label="Bug" width="100" align="center">
                <template #default="{ row }">{{ row.bug_total }}({{ row.bug_open }})</template>
              </el-table-column>
            </el-table>
          </el-card>
        </template>

        <!-- 需求汇总表格 -->
        <el-card class="summary-table">
          <template #header>
            <span>📊 需求进度汇总</span>
          </template>
          <el-table :data="summaryData.items" border stripe>
            <el-table-column prop="requirement_title" label="需求名称" min-width="200" />
            <el-table-column prop="assignee_name" label="负责人" width="90" />
            <el-table-column label="状态" width="90" align="center">
              <template #default="{ row }">
                <el-tag :type="reqStatusTagType(row.requirement_status)" size="small">
                  {{ reqStatusLabel(row.requirement_status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="进度" width="100" align="center">
              <template #default="{ row }">
                <el-progress :percentage="row.actual_progress" :stroke-width="8"
                            :color="progressColor(row.actual_progress)" />
              </template>
            </el-table-column>
            <el-table-column label="用例进度" width="100" align="center">
              <template #default="{ row }">{{ row.case_execution_progress || 0 }}%</template>
            </el-table-column>
            <el-table-column label="Bug" width="100" align="center">
              <template #default="{ row }">
                {{ row.bug_total }}
                <el-tag v-if="row.bug_open > 0" type="danger" size="small" effect="plain">{{ row.bug_open }}待处理</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="风险" width="80" align="center">
              <template #default="{ row }">
                <el-tooltip :content="row.risk_reason || '无风险'" placement="top">
                  <span>{{ riskIcon(row.risk_level) }}</span>
                </el-tooltip>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </template>

      <el-empty v-else description="请选择迭代查看汇总" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useProjectStore } from '@/stores'
import { getIterations, getDashboardDaily, getDashboardIterationSummary } from '@/api/schedule'

const projectStore = useProjectStore()
const projectId = computed(() => projectStore.currentProject?.id)

const iterations = ref([])
const currentIterationId = ref(null)
const viewMode = ref('daily')
const targetDate = ref(null)
const loading = ref(false)

const dailyData = ref({})
const summaryData = ref({})

function riskIcon(level) {
  const map = { none: '🟢', low: '🟡', medium: '🟠', high: '🔴' }
  return map[level] || '🟢'
}
function progressColor(p) {
  if (p >= 80) return '#67c23a'
  if (p >= 50) return '#409eff'
  if (p >= 20) return '#e6a23c'
  return '#f56c6c'
}
function reqStatusLabel(s) {
  const map = { pending: '待排期', scheduled: '已排期', developing: '开发中', testing: '测试中', completed: '已完成' }
  return map[s] || s
}
function reqStatusTagType(s) {
  const map = { pending: 'info', scheduled: '', developing: 'warning', testing: '', completed: 'success' }
  return map[s] || ''
}

async function loadIterations() {
  if (!projectId.value) return
  try {
    const res = await getIterations(projectId.value)
    const data = res.data || res
    iterations.value = data.iterations || data || []
    if (iterations.value.length > 0 && !currentIterationId.value) {
      const active = iterations.value.find(i => i.status === 'active')
      currentIterationId.value = active?.id || iterations.value[0].id
    }
  } catch (e) {
    console.error(e)
  }
}

async function loadDaily() {
  if (!projectId.value || !currentIterationId.value) return
  loading.value = true
  try {
    const params = { iteration_id: currentIterationId.value }
    if (targetDate.value) params.target_date = targetDate.value
    const res = await getDashboardDaily(projectId.value, params)
    dailyData.value = res.data || res
  } catch (e) {
    console.error(e)
    dailyData.value = {}
  } finally {
    loading.value = false
  }
}

async function loadSummary() {
  if (!projectId.value || !currentIterationId.value) return
  loading.value = true
  try {
    const res = await getDashboardIterationSummary(projectId.value, { iteration_id: currentIterationId.value })
    summaryData.value = res.data || res
  } catch (e) {
    console.error(e)
    summaryData.value = {}
  } finally {
    loading.value = false
  }
}

async function loadDashboard() {
  if (viewMode.value === 'daily') {
    await loadDaily()
  } else {
    await loadSummary()
  }
}

onMounted(async () => {
  await loadIterations()
  await loadDashboard()
})

watch(projectId, async () => {
  await loadIterations()
  await loadDashboard()
})
</script>

<style scoped>
.dashboard-container {
  padding: 16px;
}
.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.header-left {
  display: flex;
  align-items: center;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}
.daily-stats {
  margin-bottom: 16px;
}
.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 8px 0;
}
.stat-card :deep(.el-card__body) {
  display: flex;
  align-items: center;
  gap: 16px;
}
.stat-icon {
  font-size: 36px;
}
.stat-label {
  font-size: 13px;
  color: #999;
}
.stat-num {
  font-size: 28px;
  font-weight: 700;
}
.no-report-alert {
  margin-bottom: 16px;
}
.person-card {
  margin-bottom: 16px;
}
.person-header {
  display: flex;
  align-items: center;
  gap: 10px;
}
.person-name {
  font-weight: 600;
  font-size: 15px;
}
.report-item {
  border-bottom: 1px dashed #e4e7ed;
  padding: 12px 0;
}
.report-item:last-child {
  border-bottom: none;
}
.report-requirement {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}
.report-progress {
  font-size: 13px;
  color: #999;
}
.report-risk {
  font-size: 16px;
}
.report-detail {
  padding-left: 8px;
}
.report-progress-text {
  margin-bottom: 4px;
  white-space: pre-wrap;
}
.report-meta {
  display: flex;
  gap: 16px;
  font-size: 13px;
  color: #666;
  margin-bottom: 4px;
}
.report-plan {
  font-size: 13px;
  color: #666;
}
.plan-label {
  font-weight: 600;
}
.iteration-overview {
  margin-bottom: 16px;
}
.overview-item {
  text-align: center;
  padding: 8px 0;
}
.overview-label {
  font-size: 13px;
  color: #999;
  margin-bottom: 8px;
}
.overview-value {
  font-size: 28px;
  font-weight: 700;
}
.text-danger {
  color: #f56c6c !important;
}
.risk-section {
  margin-bottom: 16px;
}
.summary-table {
  margin-bottom: 16px;
}
</style>
