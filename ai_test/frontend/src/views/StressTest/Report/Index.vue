<template>
  <div class="report-container">
    <div class="page-header">
      <div class="header-left">
        <el-button text :icon="ArrowLeft" @click="$router.back()">返回</el-button>
        <h2>性能报告</h2>
        <el-tag v-if="result?.ai_risk_level" :type="riskColor[result.ai_risk_level]" size="large" effect="dark"
          style="margin-left: 12px">
          风险: {{ riskLabel[result.ai_risk_level] }}
        </el-tag>
      </div>
      <div class="header-right">
        <el-button type="warning" :icon="MagicStick" :loading="aiAnalyzing" @click="runAIAnalysis">
          {{ aiAnalyzing ? 'AI 分析中...' : '🤖 AI 深度分析' }}
        </el-button>
      </div>
    </div>

    <div v-loading="loading">
      <template v-if="result">
        <!-- 核心指标卡片 -->
        <el-row :gutter="16" class="metric-cards">
          <el-col :span="4">
            <div class="metric-card">
              <div class="metric-value">{{ result.total_requests?.toLocaleString() }}</div>
              <div class="metric-label">总请求数</div>
            </div>
          </el-col>
          <el-col :span="4">
            <div class="metric-card success">
              <div class="metric-value">{{ result.tps?.toFixed(1) }}</div>
              <div class="metric-label">TPS</div>
            </div>
          </el-col>
          <el-col :span="4">
            <div class="metric-card primary">
              <div class="metric-value">{{ result.avg_response_time?.toFixed(1) }}<small>ms</small></div>
              <div class="metric-label">平均响应时间</div>
            </div>
          </el-col>
          <el-col :span="4">
            <div class="metric-card warning">
              <div class="metric-value">{{ result.p99_response_time?.toFixed(1) }}<small>ms</small></div>
              <div class="metric-label">P99</div>
            </div>
          </el-col>
          <el-col :span="4">
            <div class="metric-card" :class="result.error_rate > 1 ? 'danger' : 'success'">
              <div class="metric-value">{{ result.error_rate?.toFixed(2) }}%</div>
              <div class="metric-label">错误率</div>
            </div>
          </el-col>
          <el-col :span="4">
            <div class="metric-card">
              <div class="metric-value">{{ result.concurrency || '-' }}</div>
              <div class="metric-label">并发数</div>
            </div>
          </el-col>
        </el-row>

        <!-- 响应时间分布 -->
        <el-card shadow="never" style="margin-bottom: 16px">
          <template #header><strong>📊 响应时间分布</strong></template>
          <el-row :gutter="32">
            <el-col :span="4" v-for="p in rtMetrics" :key="p.key">
              <el-statistic :title="p.label" :value="result[p.key]?.toFixed(1)" suffix="ms" />
            </el-col>
          </el-row>
        </el-card>

        <!-- 接口明细 -->
        <el-card shadow="never" style="margin-bottom: 16px">
          <template #header><strong>🔍 接口性能明细</strong></template>
          <el-table :data="result.api_details" stripe border size="small">
            <el-table-column prop="method" label="方法" width="80" align="center">
              <template #default="{ row }">
                <el-tag :type="methodColor(row.method)" size="small">{{ row.method }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="url" label="URL" min-width="250" show-overflow-tooltip />
            <el-table-column prop="total" label="请求数" width="80" align="center" />
            <el-table-column prop="avg_rt" label="平均RT(ms)" width="110" align="center">
              <template #default="{ row }">
                <span :style="{ color: row.avg_rt > 500 ? '#f56c6c' : '#67c23a' }">{{ row.avg_rt }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="p99_rt" label="P99(ms)" width="100" align="center" />
            <el-table-column prop="tps" label="TPS" width="80" align="center" />
            <el-table-column prop="error_rate" label="错误率" width="90" align="center">
              <template #default="{ row }">
                <span :style="{ color: row.error_rate > 1 ? '#f56c6c' : '#67c23a' }">{{ row.error_rate }}%</span>
              </template>
            </el-table-column>
          </el-table>
        </el-card>

        <!-- 错误分布 -->
        <el-card v-if="Object.keys(result.error_distribution || {}).length" shadow="never" style="margin-bottom: 16px">
          <template #header><strong>❌ 错误分布</strong></template>
          <el-row :gutter="16">
            <el-col :span="6" v-for="(count, code) in result.error_distribution" :key="code">
              <el-statistic :title="`状态码: ${code}`" :value="count" />
            </el-col>
          </el-row>
        </el-card>

        <!-- AI分析报告 -->
        <el-card v-if="aiAnalysis" shadow="never" class="ai-analysis-card">
          <template #header>
            <div class="ai-header">
              <strong>🤖 AI 性能分析报告</strong>
              <el-tag :type="riskColor[aiAnalysis.risk_level]" effect="dark">
                风险等级: {{ riskLabel[aiAnalysis.risk_level] }}
              </el-tag>
            </div>
          </template>

          <el-alert v-if="aiAnalysis.summary" type="info" :closable="false" style="margin-bottom: 16px">
            <template #title><strong>总结:</strong> {{ aiAnalysis.summary }}</template>
          </el-alert>

          <!-- 分析内容 -->
          <div class="analysis-content" v-html="renderMarkdown(aiAnalysis.analysis || '')" />

          <!-- 瓶颈分析 -->
          <div v-if="aiAnalysis.bottleneck_analysis" style="margin-top: 16px">
            <h4>🔍 瓶颈分析</h4>
            <p>{{ aiAnalysis.bottleneck_analysis }}</p>
          </div>

          <!-- 优化建议 -->
          <div v-if="aiAnalysis.suggestions?.length" style="margin-top: 16px">
            <h4>💡 优化建议</h4>
            <el-timeline>
              <el-timeline-item v-for="(s, i) in aiAnalysis.suggestions" :key="i" type="primary" :hollow="true">
                {{ s }}
              </el-timeline-item>
            </el-timeline>
          </div>

          <!-- 关注点 -->
          <div v-if="aiAnalysis.concerns?.length" style="margin-top: 12px">
            <h4>⚠️ 关注点</h4>
            <el-tag v-for="(c, i) in aiAnalysis.concerns" :key="i" type="warning" style="margin: 4px">{{ c }}</el-tag>
          </div>
        </el-card>
      </template>

      <el-empty v-else description="暂无压测结果" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, MagicStick } from '@element-plus/icons-vue'
import { getResult, aiAnalyzeResult } from '@/api/stressTest'

const route = useRoute()
const taskId = computed(() => route.params.taskId)

const loading = ref(false)
const result = ref(null)
const aiAnalysis = ref(null)
const aiAnalyzing = ref(false)

const riskColor = { low: 'success', medium: 'warning', high: 'danger', critical: 'danger' }
const riskLabel = { low: '低风险', medium: '中风险', high: '高风险', critical: '严重' }

const rtMetrics = [
  { key: 'min_response_time', label: 'Min' },
  { key: 'p50_response_time', label: 'P50' },
  { key: 'p90_response_time', label: 'P90' },
  { key: 'p95_response_time', label: 'P95' },
  { key: 'p99_response_time', label: 'P99' },
  { key: 'max_response_time', label: 'Max' },
]
const methodColor = (m) => ({ GET: 'success', POST: 'primary', PUT: 'warning', DELETE: 'danger' }[m] || '')

const renderMarkdown = (text) => {
  return text
    .replace(/### (.*)/g, '<h4>$1</h4>')
    .replace(/## (.*)/g, '<h3>$1</h3>')
    .replace(/# (.*)/g, '<h2>$1</h2>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br/>')
}

const loadResult = async () => {
  loading.value = true
  try {
    const res = await getResult(taskId.value)
    const data = res.data || res
    result.value = data
    if (data.ai_analysis) {
      try {
        aiAnalysis.value = typeof data.ai_analysis === 'string' ? { analysis: data.ai_analysis, suggestions: data.ai_suggestions, risk_level: data.ai_risk_level } : data.ai_analysis
      } catch { aiAnalysis.value = null }
    }
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const runAIAnalysis = async () => {
  aiAnalyzing.value = true
  try {
    const res = await aiAnalyzeResult(taskId.value)
    aiAnalysis.value = (res.data || res).analysis
    ElMessage.success('🤖 AI分析完成')
    // 刷新结果
    loadResult()
  } catch (e) {
    ElMessage.error('AI分析失败: ' + (e?.response?.data?.detail || e.message))
  } finally {
    aiAnalyzing.value = false
  }
}

onMounted(() => loadResult())
</script>

<style scoped>
.report-container { padding: 4px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h2 { margin: 0 0 0 8px; font-size: 20px; }
.header-left { display: flex; align-items: center; }

.metric-cards { margin-bottom: 16px; }
.metric-card {
  background: #f5f7fa; border-radius: 12px; padding: 20px; text-align: center;
  border-left: 4px solid #909399; transition: transform 0.2s;
}
.metric-card:hover { transform: translateY(-2px); }
.metric-card.success { border-left-color: #67c23a; }
.metric-card.primary { border-left-color: #409eff; }
.metric-card.warning { border-left-color: #e6a23c; }
.metric-card.danger { border-left-color: #f56c6c; }
.metric-value { font-size: 28px; font-weight: 700; color: #303133; }
.metric-value small { font-size: 14px; font-weight: normal; color: #909399; }
.metric-label { font-size: 13px; color: #909399; margin-top: 4px; }

.ai-analysis-card { border: 1px solid #e6a23c; }
.ai-header { display: flex; justify-content: space-between; align-items: center; }
.analysis-content { line-height: 1.8; color: #606266; }
</style>
