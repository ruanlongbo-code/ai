<template>
  <div class="defect-analysis-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <h1>缺陷分析</h1>
          <p class="subtitle">基于AI技术的项目缺陷数据智能分析</p>
        </div>
        <div class="action-section">
          <el-select v-model="selectedIteration" placeholder="全部迭代" clearable @change="loadStats" style="width: 200px; margin-right: 12px;">
            <el-option v-for="it in iterations" :key="it.id" :label="it.name" :value="it.id" />
          </el-select>
          <el-button type="primary" @click="handleAiAnalysis" :loading="aiAnalyzing">
            <el-icon><MagicStick /></el-icon>
            AI 智能分析
          </el-button>
          <el-button @click="loadStats">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </div>
    </div>

    <div v-loading="loading" class="page-content">
      <!-- 统计卡片 -->
      <div class="stats-cards">
        <div class="stat-card total">
          <div class="stat-icon"><el-icon :size="28"><Warning /></el-icon></div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.total || 0 }}</div>
            <div class="stat-label">缺陷总数</div>
          </div>
        </div>
        <div class="stat-card open">
          <div class="stat-icon"><el-icon :size="28"><CircleClose /></el-icon></div>
          <div class="stat-info">
            <div class="stat-value">{{ (stats.by_status || {})['待处理'] || 0 }}</div>
            <div class="stat-label">待处理</div>
          </div>
        </div>
        <div class="stat-card fixing">
          <div class="stat-icon"><el-icon :size="28"><Loading /></el-icon></div>
          <div class="stat-info">
            <div class="stat-value">{{ (stats.by_status || {})['修复中'] || 0 }}</div>
            <div class="stat-label">修复中</div>
          </div>
        </div>
        <div class="stat-card closed">
          <div class="stat-icon"><el-icon :size="28"><CircleCheck /></el-icon></div>
          <div class="stat-info">
            <div class="stat-value">{{ ((stats.by_status || {})['已关闭'] || 0) + ((stats.by_status || {})['已验证'] || 0) }}</div>
            <div class="stat-label">已关闭/验证</div>
          </div>
        </div>
      </div>

      <!-- 图表区域 -->
      <div class="charts-section">
        <el-row :gutter="20">
          <!-- 严重程度分布 -->
          <el-col :span="8">
            <el-card shadow="hover">
              <template #header><span class="chart-title">严重程度分布</span></template>
              <div class="chart-container">
                <div v-if="hasSeverityData" class="pie-chart-wrapper">
                  <div v-for="(value, key) in stats.by_severity" :key="key" class="pie-item">
                    <div class="pie-bar" :style="{ width: getPieWidth(value, stats.total) + '%', background: getSeverityColor(key) }"></div>
                    <span class="pie-label">{{ key }}</span>
                    <span class="pie-value">{{ value }} ({{ getPercent(value, stats.total) }}%)</span>
                  </div>
                </div>
                <el-empty v-else description="暂无数据" :image-size="60" />
              </div>
            </el-card>
          </el-col>

          <!-- 缺陷类型分布 -->
          <el-col :span="8">
            <el-card shadow="hover">
              <template #header><span class="chart-title">缺陷类型分布</span></template>
              <div class="chart-container">
                <div v-if="hasTypeData" class="pie-chart-wrapper">
                  <div v-for="(value, key) in stats.by_type" :key="key" class="pie-item">
                    <div class="pie-bar" :style="{ width: getPieWidth(value, stats.total) + '%', background: getTypeColor(key) }"></div>
                    <span class="pie-label">{{ key }}</span>
                    <span class="pie-value">{{ value }} ({{ getPercent(value, stats.total) }}%)</span>
                  </div>
                </div>
                <el-empty v-else description="暂无数据" :image-size="60" />
              </div>
            </el-card>
          </el-col>

          <!-- 缺陷状态分布 -->
          <el-col :span="8">
            <el-card shadow="hover">
              <template #header><span class="chart-title">缺陷状态分布</span></template>
              <div class="chart-container">
                <div v-if="hasStatusData" class="pie-chart-wrapper">
                  <div v-for="(value, key) in stats.by_status" :key="key" class="pie-item">
                    <div class="pie-bar" :style="{ width: getPieWidth(value, stats.total) + '%', background: getStatusColor(key) }"></div>
                    <span class="pie-label">{{ key }}</span>
                    <span class="pie-value">{{ value }} ({{ getPercent(value, stats.total) }}%)</span>
                  </div>
                </div>
                <el-empty v-else description="暂无数据" :image-size="60" />
              </div>
            </el-card>
          </el-col>
        </el-row>
      </div>

      <!-- 近7天趋势 -->
      <el-card shadow="hover" class="trend-card">
        <template #header><span class="chart-title">近7天缺陷趋势</span></template>
        <div class="trend-chart" v-if="stats.recent_trend?.length">
          <div class="trend-bars">
            <div v-for="item in stats.recent_trend" :key="item.date" class="trend-bar-item">
              <div class="trend-bar" :style="{ height: getTrendBarHeight(item.count) + 'px' }">
                <span class="trend-count" v-if="item.count > 0">{{ item.count }}</span>
              </div>
              <span class="trend-date">{{ item.date }}</span>
            </div>
          </div>
        </div>
        <el-empty v-else description="暂无趋势数据" :image-size="60" />
      </el-card>

      <!-- 高缺陷需求 TOP5 -->
      <el-card shadow="hover" class="top-reqs-card" v-if="stats.top_requirements?.length">
        <template #header><span class="chart-title">缺陷最多的需求 TOP5</span></template>
        <div class="top-reqs-list">
          <div v-for="(item, index) in stats.top_requirements" :key="item.requirement_id" class="top-req-item">
            <span class="top-rank" :class="'rank-' + (index + 1)">{{ index + 1 }}</span>
            <span class="top-title">{{ item.requirement_title }}</span>
            <el-tag type="danger" size="small" round>{{ item.defect_count }} 个缺陷</el-tag>
          </div>
        </div>
      </el-card>

      <!-- AI 分析结果 -->
      <el-card shadow="hover" class="ai-result-card" v-if="aiAnalysisResult || aiAnalyzing">
        <template #header>
          <div class="ai-header">
            <span class="chart-title">
              <el-icon><MagicStick /></el-icon>
              AI 智能分析报告
            </span>
            <el-tag v-if="aiAnalyzing" type="warning" effect="dark" size="small">
              <el-icon class="is-loading"><Loading /></el-icon>
              分析中...
            </el-tag>
          </div>
        </template>
        <div class="ai-analysis-content" v-html="renderMarkdown(aiAnalysisResult)"></div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { MagicStick, Refresh, Warning, CircleClose, CircleCheck, Loading } from '@element-plus/icons-vue'
import { getDefectStats } from '@/api/dataAnalysis'
import { useProjectStore } from '@/stores'
import { useRouter } from 'vue-router'

const router = useRouter()
const projectStore = useProjectStore()

const loading = ref(false)
const stats = ref({})
const iterations = ref([])
const selectedIteration = ref(null)
const aiAnalyzing = ref(false)
const aiAnalysisResult = ref('')

const projectId = computed(() => {
  const project = projectStore.currentProject
  if (!project || !project.id) {
    ElMessage.error('请先选择项目')
    router.push('/project')
    return null
  }
  return project.id
})

const hasSeverityData = computed(() => stats.value.by_severity && Object.keys(stats.value.by_severity).length > 0)
const hasTypeData = computed(() => stats.value.by_type && Object.keys(stats.value.by_type).length > 0)
const hasStatusData = computed(() => stats.value.by_status && Object.keys(stats.value.by_status).length > 0)

const loadStats = async () => {
  if (!projectId.value) return
  loading.value = true
  try {
    const params = {}
    if (selectedIteration.value) params.iteration_id = selectedIteration.value
    const res = await getDefectStats(projectId.value, params)
    stats.value = res.data || res || {}
    iterations.value = stats.value.iterations || []
  } catch (error) {
    console.error('加载缺陷统计失败:', error)
    ElMessage.error('加载缺陷统计失败')
  } finally {
    loading.value = false
  }
}

const handleAiAnalysis = async () => {
  if (!projectId.value) return
  aiAnalyzing.value = true
  aiAnalysisResult.value = ''

  try {
    const baseUrl = import.meta.env.VITE_API_BASE_URL || ''
    const token = localStorage.getItem('token')
    const params = selectedIteration.value ? `?iteration_id=${selectedIteration.value}` : ''
    const url = `${baseUrl}/data_analysis/${projectId.value}/defect-analysis/ai-analyze${params}`

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    })

    if (!response.ok) throw new Error(`HTTP ${response.status}`)

    const reader = response.body.getReader()
    const decoder = new TextDecoder()

    while (true) {
      const { value, done } = await reader.read()
      if (done) break
      const text = decoder.decode(value, { stream: true })
      const lines = text.split('\n')
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))
            if (data.type === 'chunk') {
              aiAnalysisResult.value += data.content
            } else if (data.type === 'result') {
              aiAnalysisResult.value = data.content
            } else if (data.type === 'error') {
              ElMessage.error(data.message || 'AI分析失败')
            }
          } catch (e) { /* ignore */ }
        }
      }
    }
  } catch (error) {
    console.error('AI缺陷分析失败:', error)
    ElMessage.error('AI缺陷分析失败')
  } finally {
    aiAnalyzing.value = false
  }
}

const renderMarkdown = (text) => {
  if (!text) return ''
  // Simple markdown rendering
  return text
    .replace(/### (.*)/g, '<h3>$1</h3>')
    .replace(/## (.*)/g, '<h2>$1</h2>')
    .replace(/# (.*)/g, '<h1>$1</h1>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/^\- (.*)/gm, '<li>$1</li>')
    .replace(/^\d+\. (.*)/gm, '<li>$1</li>')
    .replace(/\n/g, '<br>')
}

const getPieWidth = (value, total) => total > 0 ? Math.max((value / total) * 100, 5) : 0
const getPercent = (value, total) => total > 0 ? Math.round((value / total) * 100) : 0

const getTrendBarHeight = (count) => {
  const maxCount = Math.max(...(stats.value.recent_trend || []).map(i => i.count), 1)
  return Math.max((count / maxCount) * 120, 4)
}

const getSeverityColor = (key) => {
  const colors = { 'P0-阻塞': '#f56c6c', 'P1-严重': '#e6a23c', 'P2-一般': '#409eff', 'P3-轻微': '#67c23a' }
  return colors[key] || '#909399'
}

const getTypeColor = (key) => {
  const colors = { '功能缺陷': '#409eff', '界面显示': '#67c23a', '性能问题': '#e6a23c', '兼容性': '#f56c6c', '其他': '#909399' }
  return colors[key] || '#909399'
}

const getStatusColor = (key) => {
  const colors = { '待处理': '#f56c6c', '修复中': '#e6a23c', '已修复': '#409eff', '已验证': '#67c23a', '已关闭': '#909399', '已拒绝': '#c0c4cc' }
  return colors[key] || '#909399'
}

onMounted(() => {
  loadStats()
})
</script>

<style scoped>
.defect-analysis-page {
  padding: 24px;
  background: #f8fafc;
  min-height: 100vh;
}

.page-header {
  margin-bottom: 24px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: white;
  padding: 20px 24px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.title-section h1 {
  margin: 0;
  font-size: 22px;
  font-weight: 700;
  background: linear-gradient(135deg, #f56c6c, #e6a23c);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.subtitle {
  margin: 4px 0 0;
  font-size: 13px;
  color: #909399;
}

.action-section {
  display: flex;
  align-items: center;
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px 24px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  transition: transform 0.2s;
}

.stat-card:hover {
  transform: translateY(-2px);
}

.stat-card.total .stat-icon { color: #409eff; background: rgba(64, 158, 255, 0.1); }
.stat-card.open .stat-icon { color: #f56c6c; background: rgba(245, 108, 108, 0.1); }
.stat-card.fixing .stat-icon { color: #e6a23c; background: rgba(230, 162, 60, 0.1); }
.stat-card.closed .stat-icon { color: #67c23a; background: rgba(103, 194, 58, 0.1); }

.stat-icon {
  width: 52px;
  height: 52px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #303133;
}

.stat-label {
  font-size: 13px;
  color: #909399;
  margin-top: 2px;
}

.charts-section {
  margin-bottom: 24px;
}

.chart-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  display: flex;
  align-items: center;
  gap: 6px;
}

.chart-container {
  min-height: 180px;
}

.pie-chart-wrapper {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.pie-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.pie-bar {
  height: 24px;
  border-radius: 4px;
  min-width: 8px;
  transition: width 0.5s ease;
}

.pie-label {
  font-size: 13px;
  color: #606266;
  min-width: 70px;
}

.pie-value {
  font-size: 12px;
  color: #909399;
  white-space: nowrap;
}

.trend-card {
  margin-bottom: 24px;
}

.trend-chart {
  padding: 16px 0;
}

.trend-bars {
  display: flex;
  align-items: flex-end;
  justify-content: space-around;
  height: 160px;
  padding: 0 20px;
}

.trend-bar-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.trend-bar {
  width: 36px;
  background: linear-gradient(180deg, #409eff, #66b1ff);
  border-radius: 6px 6px 0 0;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  min-height: 4px;
  transition: height 0.5s ease;
}

.trend-count {
  font-size: 12px;
  color: white;
  font-weight: 600;
  margin-top: 4px;
}

.trend-date {
  font-size: 12px;
  color: #909399;
}

.top-reqs-card {
  margin-bottom: 24px;
}

.top-reqs-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.top-req-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: #fafbfc;
  border-radius: 8px;
  transition: background 0.2s;
}

.top-req-item:hover {
  background: #f0f2f5;
}

.top-rank {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  font-size: 13px;
  font-weight: 700;
  color: white;
  background: #909399;
}

.top-rank.rank-1 { background: #f56c6c; }
.top-rank.rank-2 { background: #e6a23c; }
.top-rank.rank-3 { background: #409eff; }

.top-title {
  flex: 1;
  font-size: 14px;
  color: #303133;
}

.ai-result-card {
  margin-bottom: 24px;
}

.ai-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.ai-analysis-content {
  font-size: 14px;
  line-height: 1.8;
  color: #303133;
  padding: 8px;
}

.ai-analysis-content :deep(h1) { font-size: 20px; margin: 16px 0 8px; color: #303133; }
.ai-analysis-content :deep(h2) { font-size: 17px; margin: 14px 0 8px; color: #303133; border-bottom: 1px solid #ebeef5; padding-bottom: 6px; }
.ai-analysis-content :deep(h3) { font-size: 15px; margin: 12px 0 6px; color: #409eff; }
.ai-analysis-content :deep(li) { margin: 4px 0; padding-left: 8px; }
.ai-analysis-content :deep(strong) { color: #303133; }

@media (max-width: 768px) {
  .stats-cards { grid-template-columns: repeat(2, 1fr); }
  .header-content { flex-direction: column; gap: 16px; }
}
</style>
