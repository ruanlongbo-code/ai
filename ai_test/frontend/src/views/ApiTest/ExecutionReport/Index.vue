<template>
  <div class="execution-report-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <h1>增强执行报告</h1>
          <p class="subtitle">详细展示接口测试执行结果、通过率、耗时统计</p>
        </div>
        <div class="action-section">
          <el-button @click="loadReport">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
          <el-button @click="$router.back()">
            <el-icon><Back /></el-icon>
            返回
          </el-button>
        </div>
      </div>
    </div>

    <div v-loading="loading">
      <!-- 概览卡片 -->
      <div v-if="report" class="summary-cards">
        <el-card shadow="never" class="summary-card total-card">
          <div class="summary-value">{{ report.summary?.total_cases || 0 }}</div>
          <div class="summary-label">总用例数</div>
        </el-card>
        <el-card shadow="never" class="summary-card success-card">
          <div class="summary-value success">{{ report.summary?.passed || 0 }}</div>
          <div class="summary-label">通过</div>
        </el-card>
        <el-card shadow="never" class="summary-card fail-card">
          <div class="summary-value danger">{{ report.summary?.failed || 0 }}</div>
          <div class="summary-label">失败</div>
        </el-card>
        <el-card shadow="never" class="summary-card skip-card">
          <div class="summary-value warning">{{ report.summary?.skipped || 0 }}</div>
          <div class="summary-label">跳过</div>
        </el-card>
        <el-card shadow="never" class="summary-card rate-card">
          <div class="summary-value primary">{{ passRate }}%</div>
          <div class="summary-label">通过率</div>
        </el-card>
        <el-card shadow="never" class="summary-card time-card">
          <div class="summary-value">{{ totalDuration }}</div>
          <div class="summary-label">总耗时</div>
        </el-card>
      </div>

      <!-- 通过率进度条 -->
      <el-card v-if="report" shadow="never" class="progress-card">
        <div class="progress-section">
          <span class="progress-label">整体通过率</span>
          <el-progress
            :percentage="Number(passRate)"
            :color="passRateColor"
            :stroke-width="20"
            :text-inside="true"
            class="rate-progress"
          />
        </div>
      </el-card>

      <!-- 套件维度统计 -->
      <el-card v-if="report && report.suites && report.suites.length > 0" shadow="never" class="suite-card">
        <template #header>
          <span class="card-title">套件执行概况</span>
        </template>
        <el-table :data="report.suites" stripe>
          <el-table-column prop="suite_name" label="套件名称" min-width="200" />
          <el-table-column prop="total" label="用例数" width="100" />
          <el-table-column prop="passed" label="通过" width="80">
            <template #default="{ row }">
              <span class="text-success">{{ row.passed || 0 }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="failed" label="失败" width="80">
            <template #default="{ row }">
              <span class="text-danger">{{ row.failed || 0 }}</span>
            </template>
          </el-table-column>
          <el-table-column label="通过率" width="180">
            <template #default="{ row }">
              <el-progress
                :percentage="suitePassRate(row)"
                :color="suitePassRate(row) >= 80 ? '#67c23a' : suitePassRate(row) >= 50 ? '#e6a23c' : '#f56c6c'"
                :stroke-width="10"
                :text-inside="true"
                style="width: 120px"
              />
            </template>
          </el-table-column>
          <el-table-column label="耗时" width="120">
            <template #default="{ row }">
              {{ formatDuration(row.duration) }}
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <!-- 用例执行详情 -->
      <el-card v-if="report && report.cases && report.cases.length > 0" shadow="never" class="cases-card">
        <template #header>
          <div class="case-header">
            <span class="card-title">用例执行详情</span>
            <el-select v-model="caseFilter" placeholder="筛选状态" clearable size="small" style="width: 140px">
              <el-option label="全部" value="" />
              <el-option label="通过" value="success" />
              <el-option label="失败" value="failed" />
              <el-option label="跳过" value="skipped" />
            </el-select>
          </div>
        </template>
        <el-table :data="filteredCases" stripe>
          <el-table-column prop="case_name" label="用例名称" min-width="220" />
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="caseStatusType(row.status)" size="small" effect="dark">
                {{ caseStatusLabel(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="请求" width="200">
            <template #default="{ row }">
              <div v-if="row.request_info">
                <el-tag :type="methodColor(row.request_info.method)" size="small" effect="plain" style="margin-right: 4px;">
                  {{ row.request_info.method }}
                </el-tag>
                <span class="case-url">{{ row.request_info.url }}</span>
              </div>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column label="响应状态" width="100">
            <template #default="{ row }">
              {{ row.request_info?.response_status || '-' }}
            </template>
          </el-table-column>
          <el-table-column label="耗时" width="100">
            <template #default="{ row }">
              {{ row.duration ? row.duration.toFixed(0) + 'ms' : '-' }}
            </template>
          </el-table-column>
          <el-table-column label="错误信息" min-width="250">
            <template #default="{ row }">
              <span v-if="row.error_message" class="error-text">{{ row.error_message }}</span>
              <span v-else class="text-success">-</span>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <!-- 空状态 -->
      <el-empty v-if="!loading && !report" description="未找到执行报告数据" :image-size="120" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Refresh, Back } from '@element-plus/icons-vue'
import { getEnhancedExecutionReport } from '@/api/apiTest'
import { useProjectStore } from '@/stores'

const route = useRoute()
const router = useRouter()
const projectStore = useProjectStore()

const loading = ref(false)
const report = ref(null)
const caseFilter = ref('')

const getProjectId = () => route.params.projectId || projectStore.currentProject?.id || 1
const getRunId = () => route.params.runId

const passRate = computed(() => {
  if (!report.value?.summary) return '0'
  const s = report.value.summary
  const total = s.total_cases || 0
  if (total === 0) return '0'
  return ((s.passed / total) * 100).toFixed(1)
})

const passRateColor = computed(() => {
  const rate = Number(passRate.value)
  if (rate >= 90) return '#67c23a'
  if (rate >= 70) return '#e6a23c'
  return '#f56c6c'
})

const totalDuration = computed(() => {
  if (!report.value?.summary?.total_duration) return '-'
  return formatDuration(report.value.summary.total_duration)
})

const filteredCases = computed(() => {
  if (!report.value?.cases) return []
  if (!caseFilter.value) return report.value.cases
  return report.value.cases.filter(c => c.status === caseFilter.value)
})

const formatDuration = (ms) => {
  if (!ms && ms !== 0) return '-'
  if (ms < 1000) return ms.toFixed(0) + ' ms'
  if (ms < 60000) return (ms / 1000).toFixed(1) + ' s'
  return (ms / 60000).toFixed(1) + ' min'
}

const suitePassRate = (suite) => {
  const total = suite.total || 0
  if (total === 0) return 0
  return Number(((suite.passed / total) * 100).toFixed(1))
}

const caseStatusType = (status) => {
  const map = { success: 'success', passed: 'success', failed: 'danger', skipped: 'warning' }
  return map[status] || 'info'
}

const caseStatusLabel = (status) => {
  const map = { success: '通过', passed: '通过', failed: '失败', skipped: '跳过' }
  return map[status] || status
}

const methodColor = (method) => {
  const map = { GET: 'success', POST: 'warning', PUT: 'primary', DELETE: 'danger' }
  return map[method] || 'info'
}

const loadReport = async () => {
  loading.value = true
  try {
    const res = await getEnhancedExecutionReport(getProjectId(), getRunId())
    const data = res.data || res
    report.value = data
  } catch (e) {
    console.error('加载执行报告失败:', e)
    ElMessage.error('加载执行报告失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  if (getRunId()) {
    loadReport()
  }
})
</script>

<style scoped>
.execution-report-page {
  padding: 24px;
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

/* ========== 概览卡片 ========== */
.summary-cards {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}

.summary-card {
  border-radius: 8px;
  text-align: center;
}

.summary-card :deep(.el-card__body) {
  padding: 16px;
}

.summary-value {
  font-size: 28px;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 4px;
}

.summary-value.success { color: #67c23a; }
.summary-value.danger { color: #f56c6c; }
.summary-value.warning { color: #e6a23c; }
.summary-value.primary { color: #6366f1; }

.summary-label {
  font-size: 12px;
  color: #9ca3af;
}

/* ========== 进度条 ========== */
.progress-card {
  margin-bottom: 16px;
  border-radius: 8px;
}

.progress-section {
  display: flex;
  align-items: center;
  gap: 16px;
}

.progress-label {
  font-weight: 600;
  font-size: 14px;
  color: #1f2937;
  white-space: nowrap;
}

.rate-progress {
  flex: 1;
}

/* ========== 卡片 ========== */
.suite-card, .cases-card {
  margin-bottom: 16px;
  border-radius: 8px;
}

.card-title {
  font-weight: 600;
  font-size: 15px;
  color: #1f2937;
}

.case-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.text-success { color: #67c23a; font-weight: 600; }
.text-danger { color: #f56c6c; font-weight: 600; }

.case-url {
  font-size: 12px;
  color: #6b7280;
}

.error-text {
  color: #f56c6c;
  font-size: 12px;
}

@media (max-width: 1024px) {
  .summary-cards {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 768px) {
  .execution-report-page { padding: 12px; }
  .summary-cards { grid-template-columns: repeat(2, 1fr); }
  .header-content { flex-direction: column; gap: 12px; }
}
</style>
