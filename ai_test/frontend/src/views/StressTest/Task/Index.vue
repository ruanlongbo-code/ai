<template>
  <div class="task-container">
    <div class="page-header">
      <div class="header-left">
        <h2>压测任务</h2>
        <span class="subtitle">创建并执行性能压测，实时查看测试进度</span>
      </div>
      <div class="header-right">
        <el-button type="primary" :icon="Plus" @click="openCreateDialog">创建任务</el-button>
      </div>
    </div>

    <!-- 筛选 -->
    <div class="filter-bar">
      <el-select v-model="filterStatus" placeholder="状态筛选" clearable style="width: 150px" @change="loadTasks">
        <el-option label="待执行" value="pending" />
        <el-option label="运行中" value="running" />
        <el-option label="已完成" value="completed" />
        <el-option label="失败" value="failed" />
        <el-option label="已停止" value="stopped" />
      </el-select>
      <el-button :icon="Refresh" @click="loadTasks">刷新</el-button>
    </div>

    <!-- 任务列表 -->
    <el-table :data="tasks" v-loading="loading" stripe border>
      <el-table-column prop="name" label="任务名称" min-width="180" />
      <el-table-column prop="scenario_name" label="关联场景" min-width="150" />
      <el-table-column prop="load_type" label="负载类型" width="120" align="center">
        <template #default="{ row }">
          <el-tag :type="loadTypeTag[row.load_type]" size="small">{{ loadTypeName[row.load_type] }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="concurrency" label="并发数" width="80" align="center" />
      <el-table-column prop="duration" label="持续时间" width="100" align="center">
        <template #default="{ row }">{{ row.duration }}s</template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="statusTag[row.status]" size="small" :effect="row.status === 'running' ? 'dark' : 'light'">
            {{ statusName[row.status] }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="320" align="center" fixed="right">
        <template #default="{ row }">
          <el-button v-if="row.status === 'pending'" size="small" type="success" text :icon="VideoPlay"
            @click="executeTask(row)">执行</el-button>
          <el-button v-if="row.status === 'running'" size="small" type="warning" text :icon="VideoPause"
            @click="handleStop(row)">停止</el-button>
          <el-button v-if="row.status === 'running'" size="small" type="primary" text :icon="Monitor"
            @click="goMonitor(row)">监控</el-button>
          <el-button v-if="row.status === 'completed'" size="small" type="primary" text :icon="DataAnalysis"
            @click="goReport(row)">报告</el-button>
          <el-button size="small" type="danger" text :icon="Delete" @click="handleDelete(row)"
            :disabled="row.status === 'running'">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination-wrapper">
      <el-pagination v-model:current-page="currentPage" v-model:page-size="pageSize"
        :total="total" :page-sizes="[10, 20, 50]" layout="total, sizes, prev, pager, next"
        @size-change="loadTasks" @current-change="loadTasks" />
    </div>

    <!-- 创建任务对话框 -->
    <el-dialog v-model="showCreateDialog" title="创建压测任务" width="640px" :close-on-click-modal="false">
      <el-form :model="createForm" label-width="110px" ref="createFormRef" :rules="createRules">
        <el-form-item label="任务名称" prop="name">
          <el-input v-model="createForm.name" placeholder="请输入任务名称" />
        </el-form-item>
        <el-form-item label="测试场景" prop="scenario_id">
          <el-select v-model="createForm.scenario_id" placeholder="选择场景" style="width: 100%"
            @change="onScenarioChange">
            <el-option v-for="s in scenarioList" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
        </el-form-item>

        <el-divider content-position="left">
          负载配置
          <el-button type="warning" text size="small" :icon="MagicStick" :loading="aiRecommending"
            @click="getAIRecommendation" style="margin-left: 8px">
            AI 推荐配置
          </el-button>
        </el-divider>

        <!-- AI推荐提示 -->
        <el-alert v-if="aiRecommendResult" type="success" :closable="true" style="margin-bottom: 16px"
          @close="aiRecommendResult = null">
          <template #title>
            <strong>🤖 AI 推荐配置</strong>
          </template>
          <div style="line-height: 1.8; font-size: 13px;">
            <p><strong>负载类型:</strong> {{ loadTypeName[aiRecommendResult.load_type] }} - {{ aiRecommendResult.load_type_reason }}</p>
            <p><strong>并发数:</strong> {{ aiRecommendResult.concurrency }} - {{ aiRecommendResult.concurrency_reason }}</p>
            <p><strong>持续时间:</strong> {{ aiRecommendResult.duration }}s - {{ aiRecommendResult.duration_reason }}</p>
            <div v-if="aiRecommendResult.suggestions?.length">
              <strong>建议: </strong>
              <el-tag v-for="(s, i) in aiRecommendResult.suggestions" :key="i" size="small" type="info"
                style="margin: 2px">{{ s }}</el-tag>
            </div>
            <el-button type="primary" size="small" style="margin-top: 8px" @click="applyAIRecommendation">
              应用此配置
            </el-button>
          </div>
        </el-alert>

        <el-form-item label="负载类型">
          <el-select v-model="createForm.load_type" style="width: 100%">
            <el-option label="恒定负载 - 固定并发持续压测" value="constant" />
            <el-option label="梯度加压 - 逐步增加并发" value="ramp_up" />
            <el-option label="尖峰测试 - 突发高峰负载" value="spike" />
            <el-option label="耐久测试 - 长时间稳定压测" value="soak" />
          </el-select>
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="并发用户数">
              <el-input-number v-model="createForm.concurrency" :min="1" :max="5000" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="持续时间(秒)">
              <el-input-number v-model="createForm.duration" :min="10" :max="3600" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16" v-if="createForm.load_type === 'ramp_up'">
          <el-col :span="12">
            <el-form-item label="加压时间(秒)">
              <el-input-number v-model="createForm.ramp_up_time" :min="0" :max="600" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="加压步骤数">
              <el-input-number v-model="createForm.ramp_up_steps" :min="1" :max="20" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="测试目标">
          <el-input v-model="testGoal" placeholder="可选：描述测试目标，用于AI推荐（如：验证支持500 TPS）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="handleCreate">创建任务</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useProjectStore } from '@/stores'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus, Refresh, Delete, VideoPlay, VideoPause, Monitor, DataAnalysis, MagicStick
} from '@element-plus/icons-vue'
import {
  getTasks, createTask, deleteTask, stopTask,
  getScenarios, aiRecommendConfig
} from '@/api/stressTest'

const route = useRoute()
const router = useRouter()
const projectStore = useProjectStore()
const projectId = computed(() => projectStore.currentProject?.id)

const loading = ref(false)
const tasks = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const filterStatus = ref('')

const loadTypeName = { constant: '恒定负载', ramp_up: '梯度加压', spike: '尖峰测试', soak: '耐久测试' }
const loadTypeTag = { constant: '', ramp_up: 'warning', spike: 'danger', soak: 'success' }
const statusName = { pending: '待执行', running: '运行中', completed: '已完成', failed: '失败', stopped: '已停止' }
const statusTag = { pending: 'info', running: 'primary', completed: 'success', failed: 'danger', stopped: 'warning' }

const loadTasks = async () => {
  if (!projectId.value) return
  loading.value = true
  try {
    const res = await getTasks({
      project_id: projectId.value, page: currentPage.value,
      page_size: pageSize.value, status: filterStatus.value || undefined,
    })
    const data = res.data || res
    tasks.value = data.items || []
    total.value = data.total || 0
  } catch (e) { console.error(e) } finally { loading.value = false }
}

// 场景列表 (用于创建任务时选择)
const scenarioList = ref([])
const loadScenarioList = async () => {
  try {
    const res = await getScenarios({ project_id: projectId.value, page: 1, page_size: 100 })
    scenarioList.value = (res.data || res).items || []
  } catch (e) { console.error(e) }
}

// 创建任务
const showCreateDialog = ref(false)
const creating = ref(false)
const createFormRef = ref()
const testGoal = ref('')
const createForm = reactive({
  name: '', scenario_id: null, load_type: 'constant',
  concurrency: 10, duration: 60, ramp_up_time: 30, ramp_up_steps: 5, target_rps: 0,
})
const createRules = {
  name: [{ required: true, message: '请输入任务名称', trigger: 'blur' }],
  scenario_id: [{ required: true, message: '请选择测试场景', trigger: 'change' }],
}

const openCreateDialog = () => {
  loadScenarioList()
  createForm.name = ''
  createForm.scenario_id = route.query.scenario_id ? Number(route.query.scenario_id) : null
  createForm.load_type = 'constant'
  createForm.concurrency = 10
  createForm.duration = 60
  testGoal.value = ''
  aiRecommendResult.value = null
  showCreateDialog.value = true
}

const onScenarioChange = () => { aiRecommendResult.value = null }

// AI 推荐配置
const aiRecommending = ref(false)
const aiRecommendResult = ref(null)
const getAIRecommendation = async () => {
  if (!createForm.scenario_id) {
    ElMessage.warning('请先选择测试场景')
    return
  }
  aiRecommending.value = true
  try {
    const res = await aiRecommendConfig({
      scenario_id: createForm.scenario_id,
      test_goal: testGoal.value,
    })
    aiRecommendResult.value = (res.data || res).recommendation
    ElMessage.success('🤖 AI推荐配置已生成')
  } catch (e) {
    ElMessage.error('AI推荐失败: ' + (e?.response?.data?.detail || e.message))
  } finally {
    aiRecommending.value = false
  }
}

const applyAIRecommendation = () => {
  if (!aiRecommendResult.value) return
  const r = aiRecommendResult.value
  createForm.load_type = r.load_type || 'constant'
  createForm.concurrency = r.concurrency || 10
  createForm.duration = r.duration || 60
  createForm.ramp_up_time = r.ramp_up_time || 30
  createForm.ramp_up_steps = r.ramp_up_steps || 5
  createForm.target_rps = r.target_rps || 0
  ElMessage.success('已应用AI推荐配置')
}

const handleCreate = async () => {
  await createFormRef.value?.validate()
  creating.value = true
  try {
    await createTask(projectId.value, createForm)
    ElMessage.success('任务创建成功')
    showCreateDialog.value = false
    loadTasks()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '创建失败')
  } finally { creating.value = false }
}

// 执行任务 -> 跳转到监控页
const executeTask = (row) => {
  router.push({ name: 'StressTestMonitor', params: { taskId: row.id } })
}

const handleStop = async (row) => {
  await ElMessageBox.confirm('确认停止正在运行的压测任务？', '停止确认', { type: 'warning' })
  await stopTask(row.id)
  ElMessage.success('已发送停止信号')
  loadTasks()
}

const goMonitor = (row) => router.push({ name: 'StressTestMonitor', params: { taskId: row.id } })
const goReport = (row) => router.push({ name: 'StressTestReport', params: { taskId: row.id } })

const handleDelete = async (row) => {
  await ElMessageBox.confirm(`确认删除任务「${row.name}」及其关联数据？`, '删除确认', { type: 'warning' })
  await deleteTask(row.id)
  ElMessage.success('删除成功')
  loadTasks()
}

onMounted(() => loadTasks())
</script>

<style scoped>
.task-container { padding: 4px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h2 { margin: 0; font-size: 20px; }
.subtitle { font-size: 13px; color: #909399; margin-left: 12px; }
.filter-bar { display: flex; gap: 8px; margin-bottom: 16px; }
.pagination-wrapper { display: flex; justify-content: flex-end; margin-top: 16px; }
</style>
