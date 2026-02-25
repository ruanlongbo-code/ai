<template>
  <div class="allure-report">
    <!-- 顶部导航条 -->
    <div class="report-nav">
      <div class="nav-left">
        <el-button @click="$router.back()" text>
          <el-icon><ArrowLeft /></el-icon> 返回
        </el-button>
        <div class="nav-divider"></div>
        <h1 class="report-logo">
          <span class="logo-icon">📊</span> UI测试报告
        </h1>
      </div>
      <div class="nav-right" v-if="report">
        <div class="nav-status" :class="report.status">
          <el-icon v-if="report.status === 'passed'"><SuccessFilled /></el-icon>
          <el-icon v-else><CircleCloseFilled /></el-icon>
          {{ statusLabel(report.status) }}
        </div>
      </div>
    </div>

    <div v-loading="loading" class="report-body">
      <template v-if="report">
        <!-- ========== 概览区 ========== -->
        <div class="overview-section">
          <!-- 左侧：用例信息 + 环形图 -->
          <div class="overview-left">
            <div class="case-info-card">
              <div class="case-icon" :class="report.status">
                <el-icon v-if="report.status === 'passed'" :size="28"><SuccessFilled /></el-icon>
                <el-icon v-else :size="28"><CircleCloseFilled /></el-icon>
              </div>
              <div class="case-info">
                <h2 class="case-title">{{ report.case_name }}</h2>
                <div class="case-meta">
                  <el-tag :type="priorityType(report.priority)" size="small">{{ report.priority }}</el-tag>
                  <span v-if="report.page_name" class="meta-item">
                    <el-icon><Notebook /></el-icon> {{ report.page_name }}
                  </span>
                  <span v-if="report.executor_name" class="meta-item">
                    <el-icon><User /></el-icon> {{ report.executor_name }}
                  </span>
                </div>
              </div>
            </div>

            <!-- 环形通过率 -->
            <div class="donut-chart-area">
              <div class="donut-chart">
                <svg viewBox="0 0 120 120" class="donut-svg">
                  <!-- 背景环 -->
                  <circle cx="60" cy="60" r="52" fill="none" stroke="#f3f4f6" stroke-width="12" />
                  <!-- 通过环 -->
                  <circle
                    cx="60" cy="60" r="52"
                    fill="none"
                    :stroke="passRateColor"
                    stroke-width="12"
                    stroke-linecap="round"
                    :stroke-dasharray="passRateArc"
                    stroke-dashoffset="0"
                    transform="rotate(-90 60 60)"
                    class="donut-progress"
                  />
                </svg>
                <div class="donut-center">
                  <span class="donut-value" :style="{ color: passRateColor }">{{ report.pass_rate }}%</span>
                  <span class="donut-label">通过率</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 右侧：数据统计 -->
          <div class="overview-right">
            <div class="stat-grid">
              <div class="stat-box">
                <div class="stat-box-value total">{{ report.total_steps }}</div>
                <div class="stat-box-label">总步骤</div>
              </div>
              <div class="stat-box">
                <div class="stat-box-value success">{{ report.passed_steps }}</div>
                <div class="stat-box-label">通过</div>
              </div>
              <div class="stat-box">
                <div class="stat-box-value danger">{{ report.failed_steps }}</div>
                <div class="stat-box-label">失败</div>
              </div>
              <div class="stat-box">
                <div class="stat-box-value time">{{ formatDuration(report.total_duration_ms) }}</div>
                <div class="stat-box-label">总耗时</div>
              </div>
              <div class="stat-box">
                <div class="stat-box-value time">{{ formatDuration(report.avg_step_duration_ms) }}</div>
                <div class="stat-box-label">平均耗时</div>
              </div>
              <div class="stat-box" v-if="report.total_assertions > 0">
                <div class="stat-box-value" :style="{ color: assertionPassRateColor }">
                  {{ assertionPassRate }}%
                </div>
                <div class="stat-box-label">断言通过率</div>
              </div>
              <div class="stat-box" v-else>
                <div class="stat-box-value" style="color:#c0c4cc; font-size: 16px;">N/A</div>
                <div class="stat-box-label">断言通过率</div>
              </div>
            </div>

            <!-- 断言统计条 -->
            <div class="assertion-bar" v-if="report.total_assertions > 0">
              <div class="assertion-bar-header">
                <span class="assertion-bar-title">断言统计</span>
                <span class="assertion-bar-count">{{ report.passed_assertions }}/{{ report.total_assertions }}</span>
              </div>
              <el-progress
                :percentage="Number(assertionPassRate)"
                :stroke-width="8"
                :color="assertionPassRateColor"
                :show-text="false"
              />
              <div class="assertion-legend">
                <span class="legend-dot-item"><span class="legend-dot" style="background:#67c23a;"></span> 通过 {{ report.passed_assertions }}</span>
                <span class="legend-dot-item"><span class="legend-dot" style="background:#f56c6c;"></span> 失败 {{ report.failed_assertions }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- ========== 执行信息 ========== -->
        <div class="info-section">
          <div class="section-title">
            <el-icon><InfoFilled /></el-icon> 执行信息
          </div>
          <div class="info-grid">
            <div class="info-item">
              <span class="info-key">用例名称</span>
              <span class="info-val">{{ report.case_name }}</span>
            </div>
            <div class="info-item">
              <span class="info-key">关联页面</span>
              <span class="info-val">
                <el-link v-if="report.page_url" :href="report.page_url" target="_blank" type="primary">{{ report.page_name }}</el-link>
                <span v-else>-</span>
              </span>
            </div>
            <div class="info-item">
              <span class="info-key">优先级</span>
              <span class="info-val"><el-tag :type="priorityType(report.priority)" size="small">{{ report.priority }}</el-tag></span>
            </div>
            <div class="info-item">
              <span class="info-key">执行者</span>
              <span class="info-val">{{ report.executor_name || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="info-key">开始时间</span>
              <span class="info-val">{{ formatTime(report.start_time) }}</span>
            </div>
            <div class="info-item">
              <span class="info-key">结束时间</span>
              <span class="info-val">{{ formatTime(report.end_time) }}</span>
            </div>
            <div class="info-item" v-if="report.preconditions" style="grid-column: 1 / -1;">
              <span class="info-key">前置条件</span>
              <span class="info-val">{{ report.preconditions }}</span>
            </div>
          </div>
        </div>

        <!-- ========== 步骤时间线 ========== -->
        <div class="timeline-section">
          <div class="section-header">
            <div class="section-title">
              <el-icon><List /></el-icon> 步骤详情
            </div>
            <div class="section-actions">
              <el-radio-group v-model="stepFilter" size="small">
                <el-radio-button value="">全部 ({{ report.steps.length }})</el-radio-button>
                <el-radio-button value="passed">通过 ({{ report.passed_steps }})</el-radio-button>
                <el-radio-button value="failed">失败 ({{ report.failed_steps }})</el-radio-button>
              </el-radio-group>
            </div>
          </div>

          <div class="timeline">
            <div
              v-for="(step, idx) in filteredSteps"
              :key="idx"
              class="timeline-item"
              :class="step.status"
            >
              <!-- 时间线指示器 -->
              <div class="tl-indicator">
                <div class="tl-dot" :class="step.status">
                  <el-icon v-if="step.status === 'passed'" :size="14"><SuccessFilled /></el-icon>
                  <el-icon v-else :size="14"><CircleCloseFilled /></el-icon>
                </div>
                <div class="tl-line" v-if="idx < filteredSteps.length - 1"></div>
              </div>

              <!-- 步骤内容 -->
              <div class="tl-content">
                <div class="tl-header">
                  <div class="tl-title">
                    <span class="tl-step-num">步骤 {{ step.sort_order + 1 }}</span>
                    <span class="tl-action">{{ step.action }}</span>
                  </div>
                  <div class="tl-meta">
                    <el-tag :type="statusType(step.status)" size="small" effect="dark">{{ statusLabel(step.status) }}</el-tag>
                    <span v-if="step.duration_ms" class="tl-duration">{{ step.duration_ms }}ms</span>
                  </div>
                </div>

                <div class="tl-body">
                  <div class="tl-details">
                    <!-- 输入数据 -->
                    <div v-if="step.input_data" class="tl-row">
                      <span class="tl-label">📝 输入数据</span>
                      <span class="tl-value">{{ step.input_data }}</span>
                    </div>
                    <!-- 预期结果 -->
                    <div v-if="step.expected_result" class="tl-row">
                      <span class="tl-label">🎯 预期结果</span>
                      <span class="tl-value">{{ step.expected_result }}</span>
                    </div>
                    <!-- AI操作 -->
                    <div v-if="step.ai_action" class="tl-row">
                      <span class="tl-label">🤖 AI操作</span>
                      <span class="tl-value ai-value">{{ formatAiAction(step.ai_action) }}</span>
                    </div>
                    <!-- 实际结果 -->
                    <div v-if="step.actual_result" class="tl-row">
                      <span class="tl-label">📋 实际结果</span>
                      <span class="tl-value" :class="{ 'text-danger': step.status === 'failed' }">{{ step.actual_result }}</span>
                    </div>
                    <!-- 错误信息 -->
                    <div v-if="step.error_message" class="tl-row error-row">
                      <span class="tl-label">❌ 错误信息</span>
                      <span class="tl-value text-danger">{{ step.error_message }}</span>
                    </div>
                    <!-- 断言结果 -->
                    <div v-if="step.assertion_type" class="tl-assertion">
                      <div class="assertion-chip" :class="{ passed: step.assertion_passed, failed: !step.assertion_passed }">
                        <el-icon v-if="step.assertion_passed"><SuccessFilled /></el-icon>
                        <el-icon v-else><CircleCloseFilled /></el-icon>
                        <span class="assertion-type">{{ assertionTypeLabel(step.assertion_type) }}</span>
                        <span class="assertion-detail">{{ step.assertion_detail || '-' }}</span>
                      </div>
                    </div>
                  </div>

                  <!-- 截图 -->
                  <div v-if="step.screenshot_url" class="tl-screenshot">
                    <el-image
                      :src="getScreenshotUrl(step.screenshot_url)"
                      :preview-src-list="allScreenshots"
                      :initial-index="getScreenshotIndex(step)"
                      fit="cover"
                      class="tl-screenshot-img"
                    />
                    <span class="tl-screenshot-hint">🔍 点击放大</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <el-empty v-if="filteredSteps.length === 0" description="无匹配步骤" :image-size="60" />
        </div>
      </template>

      <el-empty v-if="!loading && !report" description="未找到报告数据" :image-size="120" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  ArrowLeft, SuccessFilled, CircleCloseFilled,
  Notebook, User, InfoFilled, List, MagicStick
} from '@element-plus/icons-vue'
import { useProjectStore } from '@/stores'
import { getUiTestReport } from '@/api/uiTest'

const route = useRoute()
const projectStore = useProjectStore()

const loading = ref(false)
const report = ref(null)
const stepFilter = ref('')

const projectId = () => projectStore.currentProject?.id
const executionId = () => route.params.executionId

const API_BASE = import.meta.env.VITE_BASE_API || `http://${window.location.hostname}:8000`

// ============ 工具函数 ============
const formatTime = (t) => t ? new Date(t).toLocaleString('zh-CN') : '-'

const formatDuration = (ms) => {
  if (!ms && ms !== 0) return '-'
  if (ms < 1000) return ms + 'ms'
  if (ms < 60000) return (ms / 1000).toFixed(1) + 's'
  return (ms / 60000).toFixed(1) + 'min'
}

const statusType = (s) => ({ passed: 'success', failed: 'danger', error: 'danger' })[s] || 'info'
const statusLabel = (s) => ({ passed: '通过', failed: '失败', error: '异常', running: '执行中' })[s] || s
const priorityType = (p) => ({ P0: 'danger', P1: 'warning', P2: '', P3: 'info' })[p] || ''

const getScreenshotUrl = (path) => {
  if (!path) return ''
  if (path.startsWith('http')) return path
  return `${API_BASE}${path}`
}

const assertionTypeLabel = (type) => {
  const m = {
    url_contains: 'URL包含', url_equals: 'URL等于',
    title_contains: '标题包含', title_equals: '标题等于',
    element_visible: '元素可见', element_hidden: '元素隐藏',
    element_text_contains: '元素文本包含', element_text_equals: '元素文本等于',
    element_exists: '元素存在',
    page_contains: '页面包含文本', toast_contains: '提示消息包含',
  }
  return m[type] || type
}

const formatAiAction = (aiActionStr) => {
  if (!aiActionStr) return '-'
  try {
    const obj = JSON.parse(aiActionStr)
    let result = `[${obj.action || ''}]`
    if (obj.selector) result += ` ${obj.selector}`
    if (obj.value) result += ` → "${obj.value}"`
    if (obj.description) result += ` | ${obj.description}`
    return result
  } catch (e) {
    return aiActionStr
  }
}

// ============ 计算属性 ============
const CIRCUMFERENCE = 2 * Math.PI * 52 // ≈ 326.73

const passRateColor = computed(() => {
  if (!report.value) return '#909399'
  const rate = report.value.pass_rate
  if (rate >= 90) return '#67c23a'
  if (rate >= 70) return '#e6a23c'
  return '#f56c6c'
})

const passRateArc = computed(() => {
  if (!report.value) return `0 ${CIRCUMFERENCE}`
  const filled = (report.value.pass_rate / 100) * CIRCUMFERENCE
  return `${filled} ${CIRCUMFERENCE}`
})

const assertionPassRate = computed(() => {
  if (!report.value || report.value.total_assertions === 0) return '0'
  return ((report.value.passed_assertions / report.value.total_assertions) * 100).toFixed(1)
})

const assertionPassRateColor = computed(() => {
  const rate = Number(assertionPassRate.value)
  if (rate >= 90) return '#67c23a'
  if (rate >= 70) return '#e6a23c'
  return '#f56c6c'
})

const filteredSteps = computed(() => {
  if (!report.value?.steps) return []
  if (!stepFilter.value) return report.value.steps
  return report.value.steps.filter(s => s.status === stepFilter.value)
})

const allScreenshots = computed(() => {
  if (!report.value?.steps) return []
  return report.value.steps.filter(s => s.screenshot_url).map(s => getScreenshotUrl(s.screenshot_url))
})

const getScreenshotIndex = (step) => {
  if (!report.value?.steps) return 0
  const screenshotSteps = report.value.steps.filter(s => s.screenshot_url)
  return screenshotSteps.findIndex(s => s.sort_order === step.sort_order)
}

// ============ 数据加载 ============
const loadReport = async () => {
  if (!projectId() || !executionId()) return
  loading.value = true
  try {
    const res = await getUiTestReport(projectId(), executionId())
    report.value = res.data || res
  } catch (e) {
    console.error('加载报告失败:', e)
    ElMessage.error('加载测试报告失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadReport()
})
</script>

<style scoped>
.allure-report {
  min-height: 100vh;
  background: #f5f6fa;
}

/* ========== 导航栏 ========== */
.report-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 24px;
  background: #fff;
  border-bottom: 1px solid #ebeef5;
  position: sticky;
  top: 0;
  z-index: 10;
}
.nav-left { display: flex; align-items: center; gap: 8px; }
.nav-divider { width: 1px; height: 20px; background: #dcdfe6; margin: 0 4px; }
.report-logo {
  margin: 0; font-size: 18px; font-weight: 700; color: #1f2937;
  display: flex; align-items: center; gap: 6px;
}
.logo-icon { font-size: 22px; }
.nav-status {
  display: flex; align-items: center; gap: 6px;
  padding: 6px 16px; border-radius: 20px; font-weight: 600; font-size: 14px;
}
.nav-status.passed { background: #f0f9eb; color: #67c23a; }
.nav-status.failed { background: #fef0f0; color: #f56c6c; }

.report-body { padding: 20px 24px; max-width: 1200px; margin: 0 auto; }

/* ========== 概览区 ========== */
.overview-section {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 20px;
}
.overview-left, .overview-right {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 1px 6px rgba(0,0,0,0.05);
}

/* 用例信息 */
.case-info-card {
  display: flex; align-items: center; gap: 14px; margin-bottom: 20px;
}
.case-icon {
  width: 52px; height: 52px; border-radius: 12px; display: flex;
  align-items: center; justify-content: center; flex-shrink: 0;
}
.case-icon.passed { background: linear-gradient(135deg, #f0f9eb, #e1f3d8); color: #67c23a; }
.case-icon.failed { background: linear-gradient(135deg, #fef0f0, #fde2e2); color: #f56c6c; }
.case-title { font-size: 18px; font-weight: 600; color: #1f2937; margin: 0 0 6px 0; }
.case-meta {
  display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
}
.meta-item {
  font-size: 12px; color: #6b7280;
  display: flex; align-items: center; gap: 4px;
}

/* 环形图 */
.donut-chart-area {
  display: flex; justify-content: center; padding: 8px 0;
}
.donut-chart {
  position: relative; width: 140px; height: 140px;
}
.donut-svg { width: 100%; height: 100%; }
.donut-progress {
  transition: stroke-dasharray 0.8s ease;
}
.donut-center {
  position: absolute; inset: 0;
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
}
.donut-value { font-size: 28px; font-weight: 800; line-height: 1; }
.donut-label { font-size: 12px; color: #6b7280; margin-top: 4px; }

/* 统计网格 */
.stat-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 20px;
}
.stat-box {
  text-align: center;
  padding: 14px 8px;
  background: #f9fafb;
  border-radius: 10px;
  transition: transform 0.2s;
}
.stat-box:hover { transform: scale(1.03); }
.stat-box-value {
  font-size: 24px; font-weight: 700; line-height: 1.2;
}
.stat-box-value.total { color: #3b82f6; }
.stat-box-value.success { color: #67c23a; }
.stat-box-value.danger { color: #f56c6c; }
.stat-box-value.time { color: #8b5cf6; font-size: 18px; }
.stat-box-label {
  font-size: 11px; color: #9ca3af; margin-top: 4px;
}

/* 断言统计条 */
.assertion-bar { margin-top: 4px; }
.assertion-bar-header {
  display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;
}
.assertion-bar-title { font-size: 13px; font-weight: 600; color: #4b5563; }
.assertion-bar-count { font-size: 13px; color: #6b7280; }
.assertion-legend {
  display: flex; gap: 16px; margin-top: 8px;
}
.legend-dot-item {
  display: flex; align-items: center; gap: 4px; font-size: 12px; color: #6b7280;
}
.legend-dot { width: 8px; height: 8px; border-radius: 50%; }

/* ========== 执行信息 ========== */
.info-section {
  background: #fff;
  border-radius: 12px;
  padding: 20px 24px;
  margin-bottom: 20px;
  box-shadow: 0 1px 6px rgba(0,0,0,0.05);
}
.section-title {
  font-size: 16px; font-weight: 600; color: #1f2937;
  display: flex; align-items: center; gap: 6px;
  margin-bottom: 16px;
}
.info-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px 24px;
}
.info-item {
  display: flex; flex-direction: column; gap: 4px;
  padding: 8px 0;
  border-bottom: 1px solid #f3f4f6;
}
.info-key { font-size: 12px; color: #9ca3af; font-weight: 500; }
.info-val { font-size: 14px; color: #1f2937; }

/* ========== 步骤时间线 ========== */
.timeline-section {
  background: #fff;
  border-radius: 12px;
  padding: 20px 24px;
  box-shadow: 0 1px 6px rgba(0,0,0,0.05);
}
.section-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 20px;
}
.section-actions { display: flex; align-items: center; }

/* 时间线 */
.timeline { position: relative; }
.timeline-item {
  display: flex; gap: 16px; margin-bottom: 0;
}

/* 时间线指示器 */
.tl-indicator {
  display: flex; flex-direction: column; align-items: center;
  width: 28px; flex-shrink: 0;
}
.tl-dot {
  width: 28px; height: 28px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  color: #fff; flex-shrink: 0; z-index: 1;
}
.tl-dot.passed { background: #67c23a; }
.tl-dot.failed { background: #f56c6c; }
.tl-dot.pending { background: #c0c4cc; }
.tl-line {
  width: 2px; flex: 1; min-height: 20px;
  background: #e5e7eb;
}

/* 步骤内容 */
.tl-content {
  flex: 1; min-width: 0;
  padding-bottom: 20px;
}
.tl-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 10px;
}
.tl-title { display: flex; align-items: center; gap: 8px; min-width: 0; }
.tl-step-num {
  font-size: 12px; font-weight: 600; color: #6b7280;
  padding: 2px 8px; background: #f3f4f6; border-radius: 4px; flex-shrink: 0;
}
.tl-action {
  font-size: 14px; font-weight: 500; color: #1f2937;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.tl-meta { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
.tl-duration { font-size: 12px; color: #6b7280; }

.tl-body {
  display: flex; gap: 16px;
  padding: 12px 16px;
  background: #f9fafb;
  border-radius: 10px;
  border: 1px solid #f0f1f3;
}
.tl-details { flex: 1; min-width: 0; }

/* 详情行 */
.tl-row {
  display: flex; gap: 8px; margin-bottom: 8px; font-size: 13px; line-height: 1.6;
}
.tl-row:last-child { margin-bottom: 0; }
.tl-label {
  width: 100px; flex-shrink: 0; color: #6b7280; font-weight: 500;
}
.tl-value { color: #374151; word-break: break-all; }
.tl-value.ai-value {
  color: #7c3aed;
  padding: 2px 8px;
  background: linear-gradient(135deg, #f5f3ff, #ede9fe);
  border-radius: 4px;
  border: 1px solid #ddd6fe;
}
.tl-value.text-danger { color: #f56c6c; }

.error-row {
  padding: 6px 10px;
  background: #fef0f0;
  border-radius: 6px;
  border: 1px solid #fde2e2;
}

/* 断言chip */
.tl-assertion { margin-top: 8px; }
.assertion-chip {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 6px 12px; border-radius: 6px; font-size: 13px;
}
.assertion-chip.passed {
  background: #f0f9eb; color: #67c23a; border: 1px solid #c2e7b0;
}
.assertion-chip.failed {
  background: #fef0f0; color: #f56c6c; border: 1px solid #fab6b6;
}
.assertion-type { font-weight: 600; }
.assertion-detail { color: #4b5563; }
.assertion-chip.failed .assertion-detail { color: #f56c6c; }

/* 截图 */
.tl-screenshot {
  flex-shrink: 0;
  display: flex; flex-direction: column; align-items: center; gap: 4px;
}
.tl-screenshot-img {
  width: 200px; height: 112px; border-radius: 8px; cursor: pointer;
  border: 1px solid #e5e7eb; overflow: hidden;
  transition: transform 0.2s, box-shadow 0.2s;
}
.tl-screenshot-img:hover {
  transform: scale(1.03);
  box-shadow: 0 4px 16px rgba(0,0,0,0.12);
}
.tl-screenshot-hint { font-size: 10px; color: #9ca3af; }

/* ========== 响应式 ========== */
@media (max-width: 1000px) {
  .overview-section { grid-template-columns: 1fr; }
  .info-grid { grid-template-columns: repeat(2, 1fr); }
  .stat-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 600px) {
  .info-grid { grid-template-columns: 1fr; }
  .tl-body { flex-direction: column; }
  .tl-screenshot-img { width: 100%; height: auto; }
}
</style>
