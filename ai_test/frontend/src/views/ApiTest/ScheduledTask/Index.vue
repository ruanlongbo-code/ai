<template>
  <div class="scheduled-task-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <h1>定时任务 / CI 触发</h1>
          <p class="subtitle">配置接口测试的定时执行、CI流水线触发，实现自动化回归测试</p>
        </div>
        <div class="action-section">
          <el-button type="primary" @click="handleCreate">
            <el-icon><Plus /></el-icon>
            新建任务
          </el-button>
          <el-button @click="loadTasks">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </div>
    </div>

    <!-- 任务列表 -->
    <el-card shadow="never" class="task-list-card">
      <div v-loading="loading" class="table-content">
        <el-table v-if="taskList.length > 0" :data="taskList" stripe>
          <el-table-column prop="id" label="ID" width="70" />
          <el-table-column prop="name" label="任务名称" min-width="180">
            <template #default="{ row }">
              <span class="task-name">{{ row.name }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="task_type" label="触发类型" width="110">
            <template #default="{ row }">
              <el-tag :type="taskTypeTagType(row.task_type)" size="small" effect="light">
                {{ taskTypeLabel(row.task_type) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="关联测试计划" min-width="160">
            <template #default="{ row }">
              {{ row.test_task_name || row.test_task_id || '-' }}
            </template>
          </el-table-column>
          <el-table-column label="执行环境" width="140">
            <template #default="{ row }">
              {{ row.environment_name || row.environment_id || '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="cron_expression" label="Cron 表达式" width="150">
            <template #default="{ row }">
              <code v-if="row.cron_expression" class="cron-code">{{ row.cron_expression }}</code>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="90">
            <template #default="{ row }">
              <el-switch
                v-model="row.is_active"
                size="small"
                @change="handleToggleActive(row)"
              />
            </template>
          </el-table-column>
          <el-table-column label="上次执行" width="160">
            <template #default="{ row }">
              {{ formatDate(row.last_run_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="240" fixed="right">
            <template #default="{ row }">
              <el-button size="small" type="success" @click="handleTrigger(row)">
                <el-icon><CaretRight /></el-icon> 执行
              </el-button>
              <el-button size="small" @click="handleEdit(row)">编辑</el-button>
              <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-else description="暂无定时任务" :image-size="80">
          <el-button type="primary" @click="handleCreate">创建第一个定时任务</el-button>
        </el-empty>
      </div>

      <!-- CI Webhook 信息 -->
      <div class="ci-webhook-section">
        <el-divider content-position="left">CI Webhook 触发入口</el-divider>
        <el-alert type="info" :closable="false" show-icon>
          <template #title>
            <span>在 CI/CD 流水线中调用以下 API 即可触发测试执行：</span>
          </template>
          <div class="ci-info">
            <code class="ci-url">POST /api/api_test/{{ getProjectId() }}/ci-trigger</code>
            <p class="ci-hint">
              请求体示例：<code>{ "task_id": 1, "trigger_source": "jenkins", "branch": "main" }</code>
            </p>
          </div>
        </el-alert>
      </div>
    </el-card>

    <!-- 新建/编辑弹窗 -->
    <el-dialog
      v-model="showFormDialog"
      :title="editingTask ? '编辑定时任务' : '新建定时任务'"
      width="560px"
      destroy-on-close
    >
      <el-form :model="taskForm" :rules="formRules" ref="formRef" label-width="110px">
        <el-form-item label="任务名称" prop="name">
          <el-input v-model="taskForm.name" placeholder="输入任务名称" />
        </el-form-item>
        <el-form-item label="触发类型" prop="task_type">
          <el-select v-model="taskForm.task_type" placeholder="选择触发类型" style="width: 100%">
            <el-option label="定时执行 (Cron)" value="cron" />
            <el-option label="CI/CD 触发" value="ci" />
            <el-option label="手动触发" value="manual" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="taskForm.task_type === 'cron'" label="Cron 表达式" prop="cron_expression">
          <el-input v-model="taskForm.cron_expression" placeholder="如: 0 8 * * *（每天8点）" />
          <div class="cron-hint">
            <span>常用：</span>
            <el-button link size="small" @click="taskForm.cron_expression = '0 8 * * *'">每天8点</el-button>
            <el-button link size="small" @click="taskForm.cron_expression = '0 */2 * * *'">每2小时</el-button>
            <el-button link size="small" @click="taskForm.cron_expression = '0 8 * * 1-5'">工作日8点</el-button>
          </div>
        </el-form-item>
        <el-form-item label="关联测试计划" prop="test_task_id">
          <el-select
            v-model="taskForm.test_task_id"
            placeholder="选择测试计划"
            filterable
            style="width: 100%"
          >
            <el-option
              v-for="plan in testPlanOptions"
              :key="plan.id"
              :label="plan.task_name || plan.name"
              :value="plan.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="执行环境" prop="environment_id">
          <el-select
            v-model="taskForm.environment_id"
            placeholder="选择测试环境"
            filterable
            style="width: 100%"
          >
            <el-option
              v-for="env in envOptions"
              :key="env.id"
              :label="env.name"
              :value="env.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="启用状态">
          <el-switch v-model="taskForm.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showFormDialog = false">取消</el-button>
        <el-button type="primary" :loading="formSubmitting" @click="handleSubmitForm">
          {{ editingTask ? '保存修改' : '创建任务' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh, CaretRight } from '@element-plus/icons-vue'
import {
  createScheduledTask,
  getScheduledTasks,
  updateScheduledTask,
  deleteScheduledTask,
  triggerScheduledTask,
  getTestEnvironments
} from '@/api/apiTest'
import { useProjectStore } from '@/stores'
import request from '@/utils/request'

const route = useRoute()
const router = useRouter()
const projectStore = useProjectStore()

const loading = ref(false)
const taskList = ref([])
const showFormDialog = ref(false)
const editingTask = ref(null)
const formSubmitting = ref(false)
const formRef = ref(null)

const testPlanOptions = ref([])
const envOptions = ref([])

const taskForm = reactive({
  name: '',
  task_type: 'cron',
  cron_expression: '',
  test_task_id: null,
  environment_id: null,
  is_active: true
})

const formRules = {
  name: [{ required: true, message: '请输入任务名称', trigger: 'blur' }],
  task_type: [{ required: true, message: '请选择触发类型', trigger: 'change' }],
  test_task_id: [{ required: true, message: '请选择关联测试计划', trigger: 'change' }],
  environment_id: [{ required: true, message: '请选择执行环境', trigger: 'change' }]
}

const getProjectId = () => {
  return route.params.projectId || projectStore.currentProject?.id || 1
}

const taskTypeLabel = (type) => {
  const map = { cron: '定时执行', ci: 'CI 触发', manual: '手动触发' }
  return map[type] || type
}

const taskTypeTagType = (type) => {
  const map = { cron: 'primary', ci: 'success', manual: '' }
  return map[type] || 'info'
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN', {
    month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit'
  })
}

// ========== 加载数据 ==========
const loadTasks = async () => {
  loading.value = true
  try {
    const res = await getScheduledTasks(getProjectId())
    const data = res.data || res
    taskList.value = data.items || data.tasks || []
  } catch (e) {
    console.error('加载定时任务列表失败:', e)
    ElMessage.error('加载定时任务列表失败')
  } finally {
    loading.value = false
  }
}

const loadTestPlans = async () => {
  try {
    const res = await request({
      url: `/test_management/${getProjectId()}/tasks`,
      method: 'get',
      params: { page: 1, page_size: 200 }
    })
    const data = res.data || res
    testPlanOptions.value = data.tasks || data.items || []
  } catch (e) {
    console.error('加载测试计划失败:', e)
  }
}

const loadEnvironments = async () => {
  try {
    const res = await getTestEnvironments(getProjectId())
    const data = res.data || res
    envOptions.value = data.environments || []
  } catch (e) {
    console.error('加载测试环境失败:', e)
  }
}

// ========== CRUD ==========
const handleCreate = () => {
  editingTask.value = null
  Object.assign(taskForm, {
    name: '', task_type: 'cron', cron_expression: '',
    test_task_id: null, environment_id: null, is_active: true
  })
  showFormDialog.value = true
}

const handleEdit = (row) => {
  editingTask.value = row
  Object.assign(taskForm, {
    name: row.name,
    task_type: row.task_type,
    cron_expression: row.cron_expression || '',
    test_task_id: row.test_task_id,
    environment_id: row.environment_id,
    is_active: row.is_active
  })
  showFormDialog.value = true
}

const handleSubmitForm = async () => {
  if (!formRef.value) return
  try {
    await formRef.value.validate()
  } catch { return }

  formSubmitting.value = true
  try {
    const payload = {
      name: taskForm.name,
      task_type: taskForm.task_type,
      cron_expression: taskForm.task_type === 'cron' ? taskForm.cron_expression : null,
      test_task_id: taskForm.test_task_id,
      environment_id: taskForm.environment_id,
      is_active: taskForm.is_active
    }
    if (editingTask.value) {
      await updateScheduledTask(getProjectId(), editingTask.value.id, payload)
      ElMessage.success('任务已更新')
    } else {
      await createScheduledTask(getProjectId(), payload)
      ElMessage.success('任务已创建')
    }
    showFormDialog.value = false
    loadTasks()
  } catch (e) {
    ElMessage.error('操作失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    formSubmitting.value = false
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确认删除定时任务「${row.name}」？`, '删除确认', { type: 'warning' })
    await deleteScheduledTask(getProjectId(), row.id)
    ElMessage.success('删除成功')
    loadTasks()
  } catch {}
}

const handleToggleActive = async (row) => {
  try {
    await updateScheduledTask(getProjectId(), row.id, { is_active: row.is_active })
    ElMessage.success(row.is_active ? '已启用' : '已停用')
  } catch (e) {
    row.is_active = !row.is_active
    ElMessage.error('操作失败')
  }
}

const handleTrigger = async (row) => {
  try {
    await ElMessageBox.confirm(`确认手动触发执行「${row.name}」？`, '执行确认', { type: 'info' })
    const res = await triggerScheduledTask(getProjectId(), row.id)
    const data = res.data || res
    ElMessage.success(data.message || '已触发执行')
    loadTasks()
    // 如果返回了 task_run_id，提示用户可以查看报告
    if (data.task_run_id) {
      try {
        await ElMessageBox.confirm(
          '测试任务已开始执行，是否跳转到执行报告页面查看进度？',
          '查看报告',
          { confirmButtonText: '查看报告', cancelButtonText: '稍后查看', type: 'success' }
        )
        router.push({
          name: 'ApiExecutionReport',
          params: { projectId: getProjectId(), runId: data.task_run_id }
        })
      } catch {}
    }
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('触发失败: ' + (e.response?.data?.detail || e.message))
    }
  }
}

// ========== 初始化 ==========
onMounted(() => {
  loadTasks()
  loadTestPlans()
  loadEnvironments()
})
</script>

<style scoped>
.scheduled-task-page {
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

.task-list-card {
  border-radius: 8px;
}

.table-content {
  min-height: 200px;
}

.task-name {
  font-weight: 500;
  color: #1f2937;
}

.cron-code {
  background: #f3f4f6;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  color: #6366f1;
}

.ci-webhook-section {
  margin-top: 24px;
}

.ci-info {
  margin-top: 8px;
}

.ci-url {
  background: #1e1e2e;
  color: #cdd6f4;
  padding: 6px 12px;
  border-radius: 4px;
  font-size: 13px;
  display: inline-block;
}

.ci-hint {
  margin-top: 8px;
  font-size: 12px;
  color: #6b7280;
}

.ci-hint code {
  background: #f3f4f6;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 12px;
}

.cron-hint {
  margin-top: 4px;
  font-size: 12px;
  color: #9ca3af;
}

@media (max-width: 768px) {
  .scheduled-task-page { padding: 12px; }
  .header-content { flex-direction: column; gap: 12px; }
}
</style>
