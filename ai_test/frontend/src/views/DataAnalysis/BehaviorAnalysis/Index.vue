<template>
  <div class="behavior-analysis-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <h1>用户行为分析</h1>
          <p class="subtitle">基于AI技术的团队效能与行为数据智能分析</p>
        </div>
        <div class="action-section">
          <el-select v-model="selectedDays" @change="loadStats" style="width: 140px; margin-right: 12px;">
            <el-option label="最近7天" :value="7" />
            <el-option label="最近14天" :value="14" />
            <el-option label="最近30天" :value="30" />
            <el-option label="最近90天" :value="90" />
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
      <!-- 总览卡片 -->
      <div class="overview-cards">
        <div class="overview-card requirements">
          <div class="card-icon"><el-icon :size="24"><Document /></el-icon></div>
          <div class="card-info">
            <div class="card-value">{{ overview.requirements_created || 0 }}</div>
            <div class="card-label">新建需求</div>
          </div>
        </div>
        <div class="overview-card cases">
          <div class="card-icon"><el-icon :size="24"><List /></el-icon></div>
          <div class="card-info">
            <div class="card-value">{{ overview.cases_created || 0 }}</div>
            <div class="card-label">创建用例</div>
          </div>
        </div>
        <div class="overview-card api-cases">
          <div class="card-icon"><el-icon :size="24"><Connection /></el-icon></div>
          <div class="card-info">
            <div class="card-value">{{ overview.api_cases_created || 0 }}</div>
            <div class="card-label">API用例</div>
          </div>
        </div>
        <div class="overview-card ui-exec">
          <div class="card-icon"><el-icon :size="24"><Monitor /></el-icon></div>
          <div class="card-info">
            <div class="card-value">{{ overview.ui_executions || 0 }}</div>
            <div class="card-label">UI执行</div>
          </div>
        </div>
        <div class="overview-card defects">
          <div class="card-icon"><el-icon :size="24"><Warning /></el-icon></div>
          <div class="card-info">
            <div class="card-value">{{ overview.defects_submitted || 0 }}</div>
            <div class="card-label">提交缺陷</div>
          </div>
        </div>
        <div class="overview-card total">
          <div class="card-icon"><el-icon :size="24"><DataAnalysis /></el-icon></div>
          <div class="card-info">
            <div class="card-value">{{ overview.total_activities || 0 }}</div>
            <div class="card-label">总活动数</div>
          </div>
        </div>
      </div>

      <el-row :gutter="20">
        <!-- 活动趋势 -->
        <el-col :span="16">
          <el-card shadow="hover" class="section-card">
            <template #header><span class="chart-title">团队活动趋势</span></template>
            <div class="activity-trend" v-if="activityTrend.length">
              <div class="trend-legend">
                <span class="legend-item"><span class="legend-dot" style="background: #409eff;"></span>需求</span>
                <span class="legend-item"><span class="legend-dot" style="background: #67c23a;"></span>用例</span>
                <span class="legend-item"><span class="legend-dot" style="background: #e6a23c;"></span>API用例</span>
              </div>
              <div class="stacked-bars">
                <div v-for="item in activityTrend" :key="item.date" class="stacked-bar-item">
                  <div class="stacked-bar-col">
                    <div class="bar-segment api" :style="{ height: getBarSegmentHeight(item.api_cases) + 'px' }" :title="`API: ${item.api_cases}`"></div>
                    <div class="bar-segment cases" :style="{ height: getBarSegmentHeight(item.cases) + 'px' }" :title="`用例: ${item.cases}`"></div>
                    <div class="bar-segment reqs" :style="{ height: getBarSegmentHeight(item.requirements) + 'px' }" :title="`需求: ${item.requirements}`"></div>
                  </div>
                  <span class="bar-date">{{ item.date }}</span>
                  <span class="bar-total" v-if="item.total > 0">{{ item.total }}</span>
                </div>
              </div>
            </div>
            <el-empty v-else description="暂无趋势数据" :image-size="60" />
          </el-card>
        </el-col>

        <!-- 模块活跃度 -->
        <el-col :span="8">
          <el-card shadow="hover" class="section-card">
            <template #header><span class="chart-title">模块活跃度</span></template>
            <div class="module-heat" v-if="Object.keys(moduleHeat).length">
              <div v-for="(count, name) in sortedModuleHeat" :key="name" class="heat-item">
                <div class="heat-info">
                  <span class="heat-name">{{ name }}</span>
                  <span class="heat-count">{{ count }}</span>
                </div>
                <div class="heat-bar-bg">
                  <div class="heat-bar" :style="{ width: getHeatWidth(count) + '%' }"></div>
                </div>
              </div>
            </div>
            <el-empty v-else description="暂无模块数据" :image-size="60" />
          </el-card>
        </el-col>
      </el-row>

      <!-- 成员贡献排行 -->
      <el-card shadow="hover" class="section-card member-card">
        <template #header><span class="chart-title">团队成员贡献排行</span></template>
        <div v-if="userRanking.length">
          <el-table :data="userRanking" stripe>
            <el-table-column label="排名" width="70" align="center">
              <template #default="{ $index }">
                <span class="rank-badge" :class="'rank-' + ($index + 1)">{{ $index + 1 }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="username" label="成员" min-width="120">
              <template #default="{ row }">
                <div class="member-name">
                  <el-avatar :size="28">{{ row.username?.charAt(0) }}</el-avatar>
                  <span>{{ row.username }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="requirements" label="新建需求" width="100" align="center">
              <template #default="{ row }">
                <el-tag v-if="row.requirements > 0" type="primary" size="small" round>{{ row.requirements }}</el-tag>
                <span v-else class="zero-val">0</span>
              </template>
            </el-table-column>
            <el-table-column prop="cases" label="创建用例" width="100" align="center">
              <template #default="{ row }">
                <el-tag v-if="row.cases > 0" type="success" size="small" round>{{ row.cases }}</el-tag>
                <span v-else class="zero-val">0</span>
              </template>
            </el-table-column>
            <el-table-column prop="defects" label="提交缺陷" width="100" align="center">
              <template #default="{ row }">
                <el-tag v-if="row.defects > 0" type="warning" size="small" round>{{ row.defects }}</el-tag>
                <span v-else class="zero-val">0</span>
              </template>
            </el-table-column>
            <el-table-column prop="total" label="总贡献" width="100" align="center" sortable>
              <template #default="{ row }">
                <span class="total-contribution">{{ row.total }}</span>
              </template>
            </el-table-column>
          </el-table>
        </div>
        <el-empty v-else description="暂无成员数据" :image-size="60" />
      </el-card>

      <!-- AI 分析结果 -->
      <el-card shadow="hover" class="section-card ai-result-card" v-if="aiAnalysisResult || aiAnalyzing">
        <template #header>
          <div class="ai-header">
            <span class="chart-title">
              <el-icon><MagicStick /></el-icon>
              AI 智能行为分析报告
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
import { MagicStick, Refresh, Document, List, Connection, Monitor, Warning, DataAnalysis, Loading } from '@element-plus/icons-vue'
import { getBehaviorStats } from '@/api/dataAnalysis'
import { useProjectStore } from '@/stores'
import { useRouter } from 'vue-router'

const router = useRouter()
const projectStore = useProjectStore()

const loading = ref(false)
const selectedDays = ref(30)
const overview = ref({})
const activityTrend = ref([])
const userRanking = ref([])
const moduleHeat = ref({})
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

const sortedModuleHeat = computed(() => {
  const entries = Object.entries(moduleHeat.value)
  entries.sort((a, b) => b[1] - a[1])
  return Object.fromEntries(entries)
})

const loadStats = async () => {
  if (!projectId.value) return
  loading.value = true
  try {
    const res = await getBehaviorStats(projectId.value, { days: selectedDays.value })
    const data = res.data || res || {}
    overview.value = data.overview || {}
    activityTrend.value = data.activity_trend || []
    userRanking.value = data.user_ranking || []
    moduleHeat.value = data.module_heat || {}
  } catch (error) {
    console.error('加载行为统计失败:', error)
    ElMessage.error('加载行为统计失败')
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
    const url = `${baseUrl}/data_analysis/${projectId.value}/behavior-analysis/ai-analyze?days=${selectedDays.value}`

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
            } else if (data.type === 'error') {
              ElMessage.error(data.message || 'AI分析失败')
            }
          } catch (e) { /* ignore */ }
        }
      }
    }
  } catch (error) {
    console.error('AI行为分析失败:', error)
    ElMessage.error('AI行为分析失败')
  } finally {
    aiAnalyzing.value = false
  }
}

const renderMarkdown = (text) => {
  if (!text) return ''
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

const getBarSegmentHeight = (count) => {
  const maxTotal = Math.max(...activityTrend.value.map(i => i.total), 1)
  return Math.max((count / maxTotal) * 100, count > 0 ? 4 : 0)
}

const getHeatWidth = (count) => {
  const maxCount = Math.max(...Object.values(moduleHeat.value), 1)
  return Math.max((count / maxCount) * 100, 8)
}

onMounted(() => {
  loadStats()
})
</script>

<style scoped>
.behavior-analysis-page {
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
  background: linear-gradient(135deg, #409eff, #67c23a);
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

/* 总览卡片 */
.overview-cards {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 14px;
  margin-bottom: 24px;
}

.overview-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 18px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  transition: transform 0.2s;
}

.overview-card:hover {
  transform: translateY(-2px);
}

.card-icon {
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
}

.overview-card.requirements .card-icon { color: #409eff; background: rgba(64, 158, 255, 0.1); }
.overview-card.cases .card-icon { color: #67c23a; background: rgba(103, 194, 58, 0.1); }
.overview-card.api-cases .card-icon { color: #e6a23c; background: rgba(230, 162, 60, 0.1); }
.overview-card.ui-exec .card-icon { color: #8b5cf6; background: rgba(139, 92, 246, 0.1); }
.overview-card.defects .card-icon { color: #f56c6c; background: rgba(245, 108, 108, 0.1); }
.overview-card.total .card-icon { color: #303133; background: rgba(48, 49, 51, 0.08); }

.card-value {
  font-size: 24px;
  font-weight: 700;
  color: #303133;
}

.card-label {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
}

/* 图表区域 */
.section-card {
  margin-bottom: 20px;
}

.chart-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  display: flex;
  align-items: center;
  gap: 6px;
}

/* 活动趋势 */
.trend-legend {
  display: flex;
  gap: 16px;
  margin-bottom: 12px;
  justify-content: flex-end;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #909399;
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 2px;
}

.stacked-bars {
  display: flex;
  align-items: flex-end;
  justify-content: space-around;
  height: 160px;
  padding: 0 10px;
}

.stacked-bar-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  flex: 1;
  position: relative;
}

.stacked-bar-col {
  display: flex;
  flex-direction: column;
  width: 28px;
}

.bar-segment {
  min-height: 0;
  transition: height 0.5s ease;
}

.bar-segment.reqs { background: #409eff; border-radius: 4px 4px 0 0; }
.bar-segment.cases { background: #67c23a; }
.bar-segment.api { background: #e6a23c; border-radius: 0 0 4px 4px; }

.bar-date {
  font-size: 11px;
  color: #909399;
}

.bar-total {
  font-size: 11px;
  color: #606266;
  font-weight: 600;
  position: absolute;
  top: -16px;
}

/* 模块活跃度 */
.module-heat {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.heat-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.heat-info {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
}

.heat-name {
  color: #606266;
}

.heat-count {
  color: #303133;
  font-weight: 600;
}

.heat-bar-bg {
  height: 8px;
  background: #f0f2f5;
  border-radius: 4px;
  overflow: hidden;
}

.heat-bar {
  height: 100%;
  background: linear-gradient(90deg, #409eff, #67c23a);
  border-radius: 4px;
  transition: width 0.5s ease;
}

/* 成员排行 */
.member-card {
  margin-bottom: 20px;
}

.rank-badge {
  width: 24px;
  height: 24px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  font-size: 12px;
  font-weight: 700;
  color: white;
  background: #c0c4cc;
}

.rank-badge.rank-1 { background: linear-gradient(135deg, #f7ba2a, #f5a623); }
.rank-badge.rank-2 { background: linear-gradient(135deg, #b8c1cc, #909399); }
.rank-badge.rank-3 { background: linear-gradient(135deg, #cd7f32, #a0522d); }

.member-name {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #303133;
}

.zero-val {
  color: #c0c4cc;
  font-size: 13px;
}

.total-contribution {
  font-size: 16px;
  font-weight: 700;
  color: #303133;
}

/* AI 分析 */
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

.ai-analysis-content :deep(h1) { font-size: 20px; margin: 16px 0 8px; }
.ai-analysis-content :deep(h2) { font-size: 17px; margin: 14px 0 8px; border-bottom: 1px solid #ebeef5; padding-bottom: 6px; }
.ai-analysis-content :deep(h3) { font-size: 15px; margin: 12px 0 6px; color: #409eff; }
.ai-analysis-content :deep(li) { margin: 4px 0; padding-left: 8px; }

@media (max-width: 768px) {
  .overview-cards { grid-template-columns: repeat(3, 1fr); }
  .header-content { flex-direction: column; gap: 16px; }
}
</style>
