<template>
  <div class="allure-detail-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <el-button @click="$router.back()" :icon="ArrowLeft" text>返回</el-button>
        <div class="header-info">
          <h2>
            <el-icon style="color: #6366f1"><DataAnalysis /></el-icon>
            {{ report?.task_name || '测试报告' }}
          </h2>
          <div class="header-meta">
            <span>执行编号 #{{ runId }}</span>
            <el-divider direction="vertical" />
            <span>{{ formatTime(report?.start_time) }} ~ {{ formatTime(report?.end_time) }}</span>
          </div>
        </div>
      </div>
      <div class="header-actions">
        <el-button @click="loadReport" :icon="Refresh">刷新</el-button>
      </div>
    </div>

    <div v-loading="loading" class="report-body">
      <!-- ========== Overview Dashboard ========== -->
      <div class="overview-section" v-if="report">
        <!-- 大通过率圆环 -->
        <div class="center-ring-card">
          <div class="ring-container">
            <el-progress
              type="circle"
              :percentage="Number(passRate)"
              :width="160"
              :stroke-width="12"
              :color="passRateColor"
            >
              <template #default>
                <div class="ring-inner">
                  <span class="ring-value">{{ passRate }}%</span>
                  <span class="ring-label">通过率</span>
                </div>
              </template>
            </el-progress>
          </div>
          <div class="ring-stats">
            <div class="ring-stat success">
              <el-icon><SuccessFilled /></el-icon>
              <span class="num">{{ summary.passed || 0 }}</span>
              <span class="txt">通过</span>
            </div>
            <div class="ring-stat danger">
              <el-icon><CircleCloseFilled /></el-icon>
              <span class="num">{{ summary.failed || 0 }}</span>
              <span class="txt">失败</span>
            </div>
            <div class="ring-stat warning">
              <el-icon><WarningFilled /></el-icon>
              <span class="num">{{ summary.skipped || 0 }}</span>
              <span class="txt">跳过</span>
            </div>
            <div class="ring-stat info">
              <el-icon><Clock /></el-icon>
              <span class="num">{{ totalDuration }}</span>
              <span class="txt">耗时</span>
            </div>
          </div>
        </div>

        <!-- 状态分布 -->
        <el-card shadow="never" class="distribution-card">
          <template #header><span class="card-title">状态分布</span></template>
          <div class="status-bars">
            <div
              v-for="(item, idx) in statusDistribution"
              :key="idx"
              class="status-bar-item"
            >
              <span class="bar-label">{{ item.label }}</span>
              <div class="bar-track">
                <div
                  class="bar-fill"
                  :style="{ width: item.pct + '%', background: item.color }"
                ></div>
              </div>
              <span class="bar-value" :style="{ color: item.color }">{{ item.count }} ({{ item.pct }}%)</span>
            </div>
          </div>
        </el-card>

        <!-- 性能统计 -->
        <el-card shadow="never" class="perf-card" v-if="report.performance_stats">
          <template #header><span class="card-title">性能指标</span></template>
          <div class="perf-grid">
            <div class="perf-item">
              <div class="perf-value">{{ report.performance_stats.avg_response_time || 0 }}ms</div>
              <div class="perf-label">平均响应</div>
            </div>
            <div class="perf-item">
              <div class="perf-value min">{{ report.performance_stats.min_response_time || 0 }}ms</div>
              <div class="perf-label">最快响应</div>
            </div>
            <div class="perf-item">
              <div class="perf-value max">{{ report.performance_stats.max_response_time || 0 }}ms</div>
              <div class="perf-label">最慢响应</div>
            </div>
            <div class="perf-item">
              <div class="perf-value p95">{{ report.performance_stats.p95_response_time || 0 }}ms</div>
              <div class="perf-label">P95 响应</div>
            </div>
          </div>
        </el-card>
      </div>

      <!-- ========== 套件概况 ========== -->
      <el-card v-if="report && report.suites && report.suites.length" shadow="never" class="section-card">
        <template #header><span class="card-title">套件执行概况</span></template>
        <div class="suite-list">
          <div
            v-for="(s, i) in report.suites"
            :key="i"
            class="suite-item"
          >
            <div class="suite-name">
              <el-icon><Folder /></el-icon>
              {{ s.suite_name }}
            </div>
            <div class="suite-stats">
              <el-tag type="success" size="small" effect="plain">{{ s.passed }} 通过</el-tag>
              <el-tag type="danger" size="small" effect="plain">{{ s.failed }} 失败</el-tag>
              <el-tag type="warning" size="small" effect="plain">{{ s.skipped || 0 }} 跳过</el-tag>
            </div>
            <div class="suite-progress">
              <el-progress
                :percentage="suitePassRate(s)"
                :stroke-width="8"
                :color="getPassRateColor(suitePassRate(s))"
                :show-text="true"
                style="width: 140px"
              />
            </div>
            <div class="suite-duration">{{ formatDuration(s.duration) }}</div>
          </div>
        </div>
      </el-card>

      <!-- ========== 趋势图 ========== -->
      <el-card v-if="report && report.trend_data && report.trend_data.length > 1" shadow="never" class="section-card">
        <template #header><span class="card-title">通过率趋势（近10次执行）</span></template>
        <div class="trend-chart">
          <div class="trend-bars">
            <div
              v-for="(t, i) in report.trend_data"
              :key="i"
              class="trend-bar-col"
            >
              <div class="trend-bar-wrap">
                <div
                  class="trend-bar"
                  :style="{ height: t.pass_rate + '%', background: getPassRateColor(t.pass_rate) }"
                >
                  <span class="trend-bar-label">{{ t.pass_rate }}%</span>
                </div>
              </div>
              <span class="trend-bar-idx" :class="{ current: t.run_id === Number(runId) }">#{{ t.run_id }}</span>
            </div>
          </div>
        </div>
      </el-card>

      <!-- ========== 用例执行详情 ========== -->
      <el-card v-if="report && report.cases && report.cases.length" shadow="never" class="section-card cases-section">
        <template #header>
          <div class="case-header">
            <span class="card-title">用例执行详情（{{ filteredCases.length }}）</span>
            <div class="case-filters">
              <el-input
                v-model="searchKey"
                placeholder="搜索用例名称"
                :prefix-icon="Search"
                clearable
                size="small"
                style="width: 180px; margin-right: 12px"
              />
              <el-radio-group v-model="caseFilter" size="small">
                <el-radio-button value="">全部</el-radio-button>
                <el-radio-button value="success">通过</el-radio-button>
                <el-radio-button value="failed">失败</el-radio-button>
                <el-radio-button value="skipped">跳过</el-radio-button>
              </el-radio-group>
            </div>
          </div>
        </template>
        <div class="case-list">
          <div
            v-for="(c, i) in filteredCases"
            :key="i"
            class="case-row"
            :class="c.status"
            @click="expandedCase === i ? expandedCase = -1 : expandedCase = i"
          >
            <div class="case-row-main">
              <div class="case-status-dot" :class="c.status"></div>
              <span class="case-name">{{ c.case_name }}</span>
              <div class="case-request" v-if="c.request_info">
                <el-tag size="small" :type="methodColor(c.request_info.method)" effect="plain">
                  {{ c.request_info.method }}
                </el-tag>
                <span class="case-url">{{ c.request_info.url }}</span>
              </div>
              <div class="case-right">
                <span class="case-resp-status" v-if="c.request_info?.response_status" :class="{ ok: c.request_info.response_status < 400 }">
                  {{ c.request_info.response_status }}
                </span>
                <span class="case-duration">{{ c.duration ? c.duration.toFixed(0) + 'ms' : '-' }}</span>
                <el-icon class="expand-icon" :class="{ expanded: expandedCase === i }"><ArrowDown /></el-icon>
              </div>
            </div>
            <!-- 展开详情 -->
            <transition name="slide">
              <div v-if="expandedCase === i" class="case-detail" @click.stop>
                <div v-if="c.error_message" class="detail-error">
                  <div class="detail-label">错误信息</div>
                  <pre class="error-pre">{{ c.error_message }}</pre>
                </div>
                <div v-if="c.api_requests_info && c.api_requests_info.length" class="detail-requests">
                  <div class="detail-label">请求详情</div>
                  <div v-for="(req, ri) in c.api_requests_info" :key="ri" class="req-item">
                    <div class="req-header">
                      <el-tag size="small" :type="methodColor(req.method)" effect="plain">{{ req.method }}</el-tag>
                      <span class="req-url">{{ req.url }}</span>
                      <span class="req-status" :class="{ ok: req.status_code && req.status_code < 400 }">{{ req.status_code || '-' }}</span>
                    </div>
                    <div v-if="req.request_body" class="req-body">
                      <div class="body-label">Request Body:</div>
                      <pre>{{ typeof req.request_body === 'string' ? req.request_body : JSON.stringify(req.request_body, null, 2) }}</pre>
                    </div>
                    <div v-if="req.response_body" class="req-body resp">
                      <div class="body-label">Response Body:</div>
                      <pre>{{ typeof req.response_body === 'string' ? req.response_body : JSON.stringify(req.response_body, null, 2) }}</pre>
                    </div>
                  </div>
                </div>
                <div v-if="!c.error_message && (!c.api_requests_info || !c.api_requests_info.length)" class="no-detail">
                  无详情数据
                </div>
              </div>
            </transition>
          </div>
        </div>
      </el-card>

      <el-empty v-if="!loading && !report" description="未找到报告数据" :image-size="120" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  ArrowLeft, Refresh, DataAnalysis, SuccessFilled, CircleCloseFilled,
  WarningFilled, Clock, Folder, Search, ArrowDown, View
} from '@element-plus/icons-vue'
import { getEnhancedExecutionReport } from '@/api/apiTest'

const route = useRoute()
const runId = computed(() => route.params.runId)
const projectId = computed(() => route.params.projectId)

const loading = ref(false)
const report = ref(null)
const caseFilter = ref('')
const searchKey = ref('')
const expandedCase = ref(-1)

const summary = computed(() => report.value?.summary || {})

const passRate = computed(() => {
  const s = summary.value
  const total = s.total_cases || 0
  if (total === 0) return '0'
  return ((s.passed / total) * 100).toFixed(1)
})

const passRateColor = computed(() => {
  const r = Number(passRate.value)
  if (r >= 90) return '#67c23a'
  if (r >= 70) return '#e6a23c'
  return '#f56c6c'
})

const totalDuration = computed(() => {
  if (!summary.value.total_duration && summary.value.total_duration !== 0) return '-'
  return formatDuration(summary.value.total_duration)
})

const statusDistribution = computed(() => {
  const dist = report.value?.status_distribution || {}
  const total = Object.values(dist).reduce((a, b) => a + b, 0)
  if (total === 0) return []
  const map = {
    success: { label: '成功', color: '#67c23a' },
    failed: { label: '失败', color: '#f56c6c' },
    error: { label: '错误', color: '#e6a23c' },
    skip: { label: '跳过', color: '#909399' },
  }
  return Object.entries(dist).map(([k, v]) => {
    const m = map[k] || { label: k, color: '#909399' }
    return { ...m, count: v, pct: total ? Number(((v / total) * 100).toFixed(1)) : 0 }
  })
})

const filteredCases = computed(() => {
  let list = report.value?.cases || []
  if (caseFilter.value) list = list.filter(c => c.status === caseFilter.value)
  if (searchKey.value) {
    const k = searchKey.value.toLowerCase()
    list = list.filter(c => (c.case_name || '').toLowerCase().includes(k))
  }
  return list
})

const formatTime = (t) => t ? new Date(t).toLocaleString('zh-CN') : '-'
const formatDuration = (ms) => {
  if (!ms && ms !== 0) return '-'
  if (ms < 1000) return ms.toFixed(0) + 'ms'
  if (ms < 60000) return (ms / 1000).toFixed(1) + 's'
  return (ms / 60000).toFixed(1) + 'min'
}
const getPassRateColor = (rate) => {
  if (rate >= 90) return '#67c23a'
  if (rate >= 70) return '#e6a23c'
  return '#f56c6c'
}
const suitePassRate = (s) => {
  const total = s.total || 0
  if (total === 0) return 0
  return Number(((s.passed / total) * 100).toFixed(1))
}
const methodColor = (m) => {
  const map = { GET: 'success', POST: 'warning', PUT: 'primary', DELETE: 'danger', PATCH: '' }
  return map[m] || 'info'
}

const loadReport = async () => {
  loading.value = true
  try {
    const res = await getEnhancedExecutionReport(projectId.value, runId.value)
    report.value = res.data || res
  } catch (e) {
    ElMessage.error('加载报告失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => { loadReport() })
</script>

<style scoped>
.allure-detail-page { padding: 20px 24px; }

.page-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 20px; background: #fff; padding: 16px 20px; border-radius: 10px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}
.header-left { display: flex; align-items: center; gap: 12px; }
.header-info h2 {
  margin: 0 0 4px 0; font-size: 20px; font-weight: 600; color: #1f2937;
  display: flex; align-items: center; gap: 8px;
}
.header-meta { font-size: 12px; color: #9ca3af; }
.header-actions { display: flex; gap: 8px; }

.report-body { max-width: 1200px; }

/* ========== Overview ========== */
.overview-section {
  display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 20px;
}

.center-ring-card {
  background: #fff; border-radius: 12px; padding: 28px;
  display: flex; align-items: center; gap: 40px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.04); grid-column: 1 / 2;
}
.ring-container { flex-shrink: 0; }
.ring-inner { text-align: center; }
.ring-value { display: block; font-size: 32px; font-weight: 800; color: #1f2937; }
.ring-label { display: block; font-size: 12px; color: #9ca3af; }

.ring-stats { display: flex; flex-direction: column; gap: 14px; flex: 1; }
.ring-stat {
  display: flex; align-items: center; gap: 10px; font-size: 14px; color: #4b5563;
}
.ring-stat .num { font-size: 22px; font-weight: 700; min-width: 40px; }
.ring-stat .txt { font-size: 13px; color: #9ca3af; }
.ring-stat.success .num, .ring-stat.success .el-icon { color: #67c23a; }
.ring-stat.danger .num, .ring-stat.danger .el-icon { color: #f56c6c; }
.ring-stat.warning .num, .ring-stat.warning .el-icon { color: #e6a23c; }
.ring-stat.info .num, .ring-stat.info .el-icon { color: #8b5cf6; }

.distribution-card, .perf-card {
  border-radius: 12px; border: none;
  box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}

.status-bars { display: flex; flex-direction: column; gap: 12px; }
.status-bar-item { display: flex; align-items: center; gap: 10px; }
.bar-label { width: 40px; font-size: 13px; color: #4b5563; font-weight: 500; text-align: right; }
.bar-track { flex: 1; height: 12px; background: #f3f4f6; border-radius: 6px; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 6px; transition: width 0.6s ease; }
.bar-value { width: 90px; font-size: 12px; font-weight: 600; text-align: left; }

.perf-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }
.perf-item { text-align: center; }
.perf-value { font-size: 24px; font-weight: 700; color: #1f2937; }
.perf-value.min { color: #67c23a; }
.perf-value.max { color: #f56c6c; }
.perf-value.p95 { color: #e6a23c; }
.perf-label { font-size: 12px; color: #9ca3af; margin-top: 4px; }

/* ========== Cards ========== */
.section-card { margin-bottom: 16px; border-radius: 12px; border: none; box-shadow: 0 1px 4px rgba(0,0,0,0.04); }
.card-title { font-weight: 600; font-size: 15px; color: #1f2937; }

/* 套件列表 */
.suite-item {
  display: flex; align-items: center; gap: 16px; padding: 10px 0;
  border-bottom: 1px solid #f3f4f6;
}
.suite-item:last-child { border: none; }
.suite-name { flex: 1; font-size: 14px; font-weight: 500; display: flex; align-items: center; gap: 6px; color: #374151; }
.suite-stats { display: flex; gap: 6px; }
.suite-duration { font-size: 13px; color: #9ca3af; min-width: 60px; text-align: right; }

/* 趋势图 */
.trend-chart { padding: 8px 0; }
.trend-bars { display: flex; align-items: flex-end; gap: 8px; height: 160px; }
.trend-bar-col { flex: 1; display: flex; flex-direction: column; align-items: center; height: 100%; }
.trend-bar-wrap { flex: 1; width: 100%; display: flex; align-items: flex-end; justify-content: center; }
.trend-bar {
  width: 100%; max-width: 40px; border-radius: 4px 4px 0 0; position: relative;
  min-height: 4px; transition: height 0.4s ease;
}
.trend-bar-label {
  position: absolute; top: -18px; left: 50%; transform: translateX(-50%);
  font-size: 10px; font-weight: 600; color: #6b7280; white-space: nowrap;
}
.trend-bar-idx { font-size: 11px; color: #c0c4cc; margin-top: 4px; }
.trend-bar-idx.current { color: #6366f1; font-weight: 700; }

/* ========== 用例列表 ========== */
.case-header { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; }
.case-filters { display: flex; align-items: center; }

.case-list { display: flex; flex-direction: column; gap: 4px; }

.case-row {
  border-radius: 8px; overflow: hidden; cursor: pointer;
  transition: background 0.2s; border: 1px solid #f0f0f0;
}
.case-row:hover { background: #fafafa; }
.case-row.success .case-status-dot { background: #67c23a; }
.case-row.failed .case-status-dot { background: #f56c6c; }
.case-row.skipped .case-status-dot { background: #909399; }
.case-row.error .case-status-dot { background: #e6a23c; }

.case-row-main {
  display: flex; align-items: center; gap: 10px; padding: 10px 14px;
}
.case-status-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.case-name { font-size: 13px; font-weight: 500; color: #1f2937; min-width: 140px; max-width: 280px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.case-request { display: flex; align-items: center; gap: 6px; flex: 1; min-width: 0; }
.case-url { font-size: 12px; color: #6b7280; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.case-right { display: flex; align-items: center; gap: 12px; flex-shrink: 0; }
.case-resp-status { font-size: 13px; font-weight: 600; color: #f56c6c; }
.case-resp-status.ok { color: #67c23a; }
.case-duration { font-size: 12px; color: #9ca3af; }
.expand-icon { transition: transform 0.2s; color: #c0c4cc; }
.expand-icon.expanded { transform: rotate(180deg); }

/* 展开详情 */
.case-detail { padding: 0 14px 14px; border-top: 1px dashed #eee; }
.detail-label { font-size: 12px; font-weight: 600; color: #374151; margin: 10px 0 6px; }
.error-pre { background: #fef2f2; border: 1px solid #fecaca; color: #b91c1c; border-radius: 6px; padding: 10px; font-size: 12px; white-space: pre-wrap; word-break: break-all; max-height: 160px; overflow: auto; }

.req-item { margin-bottom: 10px; border: 1px solid #f3f4f6; border-radius: 6px; overflow: hidden; }
.req-header { display: flex; align-items: center; gap: 8px; padding: 8px 10px; background: #f9fafb; }
.req-url { font-size: 12px; color: #6b7280; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.req-status { font-size: 13px; font-weight: 600; color: #f56c6c; }
.req-status.ok { color: #67c23a; }
.req-body { padding: 8px 10px; }
.req-body.resp { border-top: 1px solid #f3f4f6; }
.body-label { font-size: 11px; font-weight: 600; color: #6b7280; margin-bottom: 4px; }
.req-body pre { font-size: 12px; background: #f8f9fa; padding: 8px; border-radius: 4px; max-height: 200px; overflow: auto; white-space: pre-wrap; word-break: break-all; margin: 0; }
.no-detail { font-size: 13px; color: #9ca3af; padding: 10px 0; }

.slide-enter-active, .slide-leave-active { transition: all 0.2s ease; }
.slide-enter-from, .slide-leave-to { opacity: 0; max-height: 0; }
.slide-enter-to, .slide-leave-from { opacity: 1; max-height: 800px; }

@media (max-width: 900px) {
  .overview-section { grid-template-columns: 1fr; }
  .center-ring-card { flex-direction: column; }
  .perf-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
