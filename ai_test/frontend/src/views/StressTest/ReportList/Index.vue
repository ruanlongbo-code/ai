<template>
  <div class="report-list-container">
    <div class="page-header">
      <div class="header-left">
        <h2>性能报告</h2>
        <span class="subtitle">查看所有已完成压测任务的性能分析报告</span>
      </div>
      <el-button :icon="Refresh" @click="loadTasks">刷新</el-button>
    </div>

    <!-- 报告卡片列表 -->
    <el-row :gutter="16">
      <el-col :span="8" v-for="task in completedTasks" :key="task.id">
        <el-card shadow="hover" class="report-card" @click="goReport(task)">
          <div class="card-top">
            <div class="card-title">{{ task.name }}</div>
            <el-tag :type="task.ai_risk_level ? riskColor[task.ai_risk_level] : 'info'" size="small" effect="dark">
              {{ task.ai_risk_level ? riskLabel[task.ai_risk_level] : '待分析' }}
            </el-tag>
          </div>

          <div class="card-meta">
            <span class="meta-item">📋 {{ task.scenario_name }}</span>
            <span class="meta-item">👥 {{ task.concurrency }} 并发</span>
            <span class="meta-item">⏱ {{ task.duration }}s</span>
          </div>

          <div class="card-metrics" v-if="task.result_summary">
            <div class="mini-metric">
              <span class="mini-value">{{ task.result_summary.tps?.toFixed(1) || '-' }}</span>
              <span class="mini-label">TPS</span>
            </div>
            <div class="mini-metric">
              <span class="mini-value">{{ task.result_summary.avg_rt?.toFixed(0) || '-' }}<small>ms</small></span>
              <span class="mini-label">平均RT</span>
            </div>
            <div class="mini-metric" :class="{ 'error': task.result_summary.error_rate > 1 }">
              <span class="mini-value">{{ task.result_summary.error_rate?.toFixed(2) || '0' }}%</span>
              <span class="mini-label">错误率</span>
            </div>
            <div class="mini-metric">
              <span class="mini-value">{{ task.result_summary.total?.toLocaleString() || '-' }}</span>
              <span class="mini-label">总请求</span>
            </div>
          </div>

          <div class="card-footer">
            <span class="time">{{ formatTime(task.finished_at) }}</span>
            <el-button type="primary" text size="small" :icon="DataAnalysis">查看报告</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-empty v-if="!loading && !completedTasks.length" description="暂无已完成的压测报告" />
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useProjectStore } from '@/stores'
import { Refresh, DataAnalysis } from '@element-plus/icons-vue'
import { getTasks, getResult } from '@/api/stressTest'

const router = useRouter()
const projectStore = useProjectStore()
const projectId = computed(() => projectStore.currentProject?.id)

const loading = ref(false)
const completedTasks = ref([])

const riskColor = { low: 'success', medium: 'warning', high: 'danger', critical: 'danger' }
const riskLabel = { low: '低风险', medium: '中风险', high: '高风险', critical: '严重' }
const formatTime = (t) => t ? new Date(t).toLocaleString('zh-CN') : '-'

const loadTasks = async () => {
  if (!projectId.value) return
  loading.value = true
  try {
    const res = await getTasks({ project_id: projectId.value, status: 'completed', page: 1, page_size: 100 })
    const tasks = (res.data || res).items || []

    // 逐个获取结果摘要
    const enriched = []
    for (const task of tasks) {
      try {
        const rRes = await getResult(task.id)
        const r = rRes.data || rRes
        task.result_summary = {
          tps: r.tps, avg_rt: r.avg_response_time,
          error_rate: r.error_rate, total: r.total_requests,
        }
        task.ai_risk_level = r.ai_risk_level
      } catch {
        task.result_summary = null
      }
      enriched.push(task)
    }
    completedTasks.value = enriched
  } catch (e) { console.error(e) } finally { loading.value = false }
}

const goReport = (task) => {
  router.push({ name: 'StressTestReport', params: { taskId: task.id } })
}

onMounted(() => loadTasks())
</script>

<style scoped>
.report-list-container { padding: 4px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h2 { margin: 0; font-size: 20px; }
.subtitle { font-size: 13px; color: #909399; margin-left: 12px; }

.report-card { margin-bottom: 16px; border-radius: 12px; cursor: pointer; transition: all 0.3s; }
.report-card:hover { transform: translateY(-3px); box-shadow: 0 6px 16px rgba(0,0,0,0.12); }

.card-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.card-title { font-weight: 600; font-size: 15px; color: #303133; }

.card-meta { display: flex; gap: 12px; margin-bottom: 14px; flex-wrap: wrap; }
.meta-item { font-size: 12px; color: #909399; }

.card-metrics {
  display: flex; justify-content: space-between;
  background: #f5f7fa; border-radius: 8px; padding: 12px; margin-bottom: 12px;
}
.mini-metric { text-align: center; flex: 1; }
.mini-value { font-size: 18px; font-weight: 700; color: #303133; display: block; }
.mini-value small { font-size: 12px; font-weight: normal; color: #909399; }
.mini-label { font-size: 11px; color: #909399; }
.mini-metric.error .mini-value { color: #f56c6c; }

.card-footer { display: flex; justify-content: space-between; align-items: center; }
.time { font-size: 12px; color: #c0c4cc; }
</style>
