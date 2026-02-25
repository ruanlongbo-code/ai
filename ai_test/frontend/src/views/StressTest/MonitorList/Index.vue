<template>
  <div class="monitor-list-container">
    <div class="page-header">
      <div class="header-left">
        <h2>实时监控</h2>
        <span class="subtitle">查看正在运行或已完成的压测任务监控数据</span>
      </div>
      <el-button :icon="Refresh" @click="loadTasks">刷新</el-button>
    </div>

    <!-- 运行中的任务 -->
    <div v-if="runningTasks.length" class="section">
      <h3 class="section-title">
        <span class="dot running" /> 运行中 ({{ runningTasks.length }})
      </h3>
      <el-row :gutter="16">
        <el-col :span="8" v-for="task in runningTasks" :key="task.id">
          <el-card shadow="hover" class="monitor-card running-card" @click="goMonitor(task)">
            <div class="card-top">
              <div class="card-title">{{ task.name }}</div>
              <el-tag type="primary" size="small" effect="dark" class="pulse-tag">运行中</el-tag>
            </div>
            <div class="card-meta">
              <span>📋 {{ task.scenario_name }}</span>
              <span>👥 {{ task.concurrency }} 并发</span>
              <span>⏱ {{ task.duration }}s</span>
              <span>🔄 {{ task.load_type === 'constant' ? '恒定' : task.load_type === 'ramp_up' ? '梯度' : task.load_type === 'spike' ? '尖峰' : '耐久' }}</span>
            </div>
            <div class="card-action">
              <el-button type="primary" :icon="Monitor" size="small">进入监控</el-button>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 待执行的任务 -->
    <div v-if="pendingTasks.length" class="section">
      <h3 class="section-title">
        <span class="dot pending" /> 待执行 ({{ pendingTasks.length }})
      </h3>
      <el-row :gutter="16">
        <el-col :span="8" v-for="task in pendingTasks" :key="task.id">
          <el-card shadow="hover" class="monitor-card" @click="goMonitor(task)">
            <div class="card-top">
              <div class="card-title">{{ task.name }}</div>
              <el-tag type="info" size="small">待执行</el-tag>
            </div>
            <div class="card-meta">
              <span>📋 {{ task.scenario_name }}</span>
              <span>👥 {{ task.concurrency }} 并发</span>
              <span>⏱ {{ task.duration }}s</span>
            </div>
            <div class="card-action">
              <el-button type="success" :icon="VideoPlay" size="small">开始压测</el-button>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 已完成的任务 -->
    <div v-if="finishedTasks.length" class="section">
      <h3 class="section-title">
        <span class="dot completed" /> 历史记录 ({{ finishedTasks.length }})
      </h3>
      <el-table :data="finishedTasks" stripe border size="small">
        <el-table-column prop="name" label="任务名称" min-width="180" />
        <el-table-column prop="scenario_name" label="场景" min-width="130" />
        <el-table-column prop="concurrency" label="并发" width="70" align="center" />
        <el-table-column prop="duration" label="时长" width="70" align="center">
          <template #default="{ row }">{{ row.duration }}s</template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="statusTag[row.status]" size="small">{{ statusName[row.status] }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="finished_at" label="完成时间" width="170">
          <template #default="{ row }">{{ formatTime(row.finished_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="140" align="center">
          <template #default="{ row }">
            <el-button size="small" type="primary" text @click="goMonitor(row)">查看数据</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-empty v-if="!loading && !runningTasks.length && !pendingTasks.length && !finishedTasks.length"
      description="暂无压测任务" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useProjectStore } from '@/stores'
import { Refresh, Monitor, VideoPlay } from '@element-plus/icons-vue'
import { getTasks } from '@/api/stressTest'

const router = useRouter()
const projectStore = useProjectStore()
const projectId = computed(() => projectStore.currentProject?.id)

const loading = ref(false)
const allTasks = ref([])
let refreshTimer = null

const runningTasks = computed(() => allTasks.value.filter(t => t.status === 'running'))
const pendingTasks = computed(() => allTasks.value.filter(t => t.status === 'pending'))
const finishedTasks = computed(() => allTasks.value.filter(t => ['completed', 'failed', 'stopped'].includes(t.status)))

const statusName = { completed: '已完成', failed: '失败', stopped: '已停止' }
const statusTag = { completed: 'success', failed: 'danger', stopped: 'warning' }
const formatTime = (t) => t ? new Date(t).toLocaleString('zh-CN') : '-'

const loadTasks = async () => {
  if (!projectId.value) return
  loading.value = true
  try {
    const res = await getTasks({ project_id: projectId.value, page: 1, page_size: 100 })
    allTasks.value = (res.data || res).items || []
  } catch (e) { console.error(e) } finally { loading.value = false }
}

const goMonitor = (task) => {
  router.push({ name: 'StressTestMonitor', params: { taskId: task.id } })
}

onMounted(() => {
  loadTasks()
  // 自动刷新（有运行中任务时每5秒刷新）
  refreshTimer = setInterval(() => {
    if (runningTasks.value.length > 0) loadTasks()
  }, 5000)
})

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer)
})
</script>

<style scoped>
.monitor-list-container { padding: 4px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h2 { margin: 0; font-size: 20px; }
.subtitle { font-size: 13px; color: #909399; margin-left: 12px; }

.section { margin-bottom: 24px; }
.section-title { font-size: 15px; color: #606266; margin-bottom: 12px; display: flex; align-items: center; gap: 8px; }
.dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
.dot.running { background: #409eff; animation: pulse 1.5s infinite; }
.dot.pending { background: #909399; }
.dot.completed { background: #67c23a; }

@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }

.monitor-card { margin-bottom: 12px; border-radius: 12px; cursor: pointer; transition: all 0.3s; }
.monitor-card:hover { transform: translateY(-3px); box-shadow: 0 6px 16px rgba(0,0,0,0.12); }
.running-card { border: 1px solid #409eff; }

.card-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.card-title { font-weight: 600; font-size: 15px; color: #303133; }

.card-meta { display: flex; gap: 12px; font-size: 12px; color: #909399; margin-bottom: 12px; flex-wrap: wrap; }
.card-action { text-align: right; }

.pulse-tag { animation: pulse 1.5s infinite; }
</style>
