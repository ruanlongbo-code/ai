<template>
  <div class="schedule-container">
    <!-- 迭代选择器 + 操作栏 -->
    <div class="schedule-header">
      <div class="header-left">
        <el-select
          v-model="currentIterationId"
          placeholder="选择迭代"
          @change="handleIterationChange"
          style="width: 240px"
        >
          <el-option
            v-for="it in iterations"
            :key="it.id"
            :label="`${it.name} (${it.status === 'active' ? '进行中' : it.status === 'completed' ? '已完成' : '草稿'})`"
            :value="it.id"
          />
        </el-select>
        <template v-if="currentIteration">
          <el-tag :type="statusTagType" class="iteration-tag">
            {{ statusLabel }}
          </el-tag>
          <span class="iteration-info">
            {{ currentIteration.start_date }} ~ {{ currentIteration.end_date }}
            <el-tag v-if="currentIteration.remaining_days <= 3" type="danger" size="small" effect="plain">
              剩余 {{ currentIteration.remaining_days }} 天
            </el-tag>
            <el-tag v-else size="small" effect="plain">
              剩余 {{ currentIteration.remaining_days }} 天
            </el-tag>
          </span>
        </template>
      </div>
      <div class="header-right">
        <el-button v-if="isAdmin" type="primary" @click="showCreateIteration = true">
          <el-icon><Plus /></el-icon> 新建迭代
        </el-button>
        <el-button @click="handleOpenCreateItem" :disabled="!currentIterationId">
          <el-icon><Plus /></el-icon> 添加需求排期
        </el-button>
        <el-button @click="handleRefresh">
          <el-icon><Refresh /></el-icon>
        </el-button>
      </div>
    </div>

    <!-- 进度概览卡片 -->
    <div class="progress-overview" v-if="currentIteration">
      <el-row :gutter="16">
        <el-col :span="6">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-title">总需求数</div>
            <div class="stat-value">{{ scheduleItems.length }}</div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-title">已完成</div>
            <div class="stat-value" style="color: #67c23a">
              {{ scheduleItems.filter(i => i.requirement_status === 'completed').length }}
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-title">测试中</div>
            <div class="stat-value" style="color: #409eff">
              {{ scheduleItems.filter(i => i.requirement_status === 'testing').length }}
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-title">整体进度</div>
            <div class="stat-value">
              {{ currentIteration.overall_progress }}%
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 排期条目表格 -->
    <el-card class="schedule-table-card" v-loading="loading">
      <template #header>
        <div class="table-header">
          <span>需求排期列表</span>
          <div class="table-filters">
            <el-select v-model="filterCategory" placeholder="全部业务线" clearable size="small" style="width: 160px; margin-right: 8px">
              <el-option label="全部业务线" value="" />
              <el-option v-for="cat in categories" :key="cat" :label="cat" :value="cat" />
            </el-select>
            <el-select v-model="filterAssignee" placeholder="负责人" clearable size="small" style="width: 140px">
              <el-option v-for="u in assigneeList" :key="u.id" :label="u.name" :value="u.id" />
            </el-select>
          </div>
        </div>
      </template>

      <el-table :data="filteredItems" border stripe style="width: 100%" row-key="id">
        <el-table-column prop="category" label="业务线" width="100" />
        <el-table-column label="需求名称" min-width="200">
          <template #default="{ row }">
            <div>
              <el-tag v-if="row.priority" :type="priorityTagType(row.priority)" size="small" effect="plain" class="priority-tag">
                {{ row.priority }}
              </el-tag>
              {{ row.requirement_title }}
            </div>
            <div v-if="row.ticket_url" class="ticket-link">
              <a :href="row.ticket_url" target="_blank">🔗 工单链接</a>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="assignee_name" label="负责人" width="90" />
        <el-table-column label="需求状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="reqStatusTagType(row.requirement_status)" size="small">
              {{ reqStatusLabel(row.requirement_status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="planned_test_date" label="提测时间" width="100" />
        <el-table-column prop="estimated_case_days" label="用例人日" width="80" align="center" />
        <el-table-column prop="case_output_date" label="用例产出" width="100" />
        <el-table-column label="用例状态" width="90" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.case_status" :type="caseStatusTagType(row.case_status)" size="small">
              {{ caseStatusLabel(row.case_status) }}
            </el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="estimated_test_days" label="测试人日" width="80" align="center" />
        <el-table-column prop="test_date_range" label="测试时间" width="110" />
        <el-table-column prop="integration_test_date" label="集成测试" width="100" />
        <el-table-column label="进度" width="100" align="center">
          <template #default="{ row }">
            <el-progress :percentage="row.actual_progress" :stroke-width="8"
                        :color="progressColor(row.actual_progress)" />
          </template>
        </el-table-column>
        <el-table-column label="风险" width="80" align="center">
          <template #default="{ row }">
            <el-tooltip :content="row.risk_reason || '无风险'" placement="top">
              <span>{{ riskIcon(row.risk_level) }}</span>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="editItem(row)" :disabled="!canEditItem(row)">编辑</el-button>
            <el-button type="danger" link size="small" @click="handleDeleteItem(row)" v-if="isAdmin">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新建迭代弹窗 -->
    <el-dialog v-model="showCreateIteration" title="新建迭代" width="500px">
      <el-form :model="iterationForm" label-width="100px">
        <el-form-item label="迭代名称" required>
          <el-input v-model="iterationForm.name" placeholder="如：2.06迭代" />
        </el-form-item>
        <el-form-item label="开始日期" required>
          <el-date-picker v-model="iterationForm.start_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="结束日期" required>
          <el-date-picker v-model="iterationForm.end_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateIteration = false">取消</el-button>
        <el-button type="primary" @click="handleCreateIteration" :loading="creating">确认创建</el-button>
      </template>
    </el-dialog>

    <!-- 新建/编辑排期条目弹窗 -->
    <el-dialog v-model="showCreateItem" :title="editingItem ? '编辑排期条目' : '添加需求排期'" width="700px">
      <el-form :model="itemForm" label-width="110px">
        <el-row :gutter="16">
          <el-col :span="24">
            <el-form-item label="需求名称" required>
              <el-input v-model="itemForm.requirement_title" placeholder="输入需求名称" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="业务线">
              <el-select v-model="itemForm.category" placeholder="请选择业务线" filterable clearable style="width: 100%">
                <el-option v-for="mod in moduleList" :key="mod.id" :label="mod.name" :value="mod.name" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="负责人" required>
              <el-select v-model="itemForm.assignee_id" placeholder="选择负责人" style="width: 100%">
                <el-option v-for="u in memberList" :key="u.id" :label="u.name" :value="u.id" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="优先级">
              <el-select v-model="itemForm.priority" placeholder="选择优先级" style="width: 100%">
                <el-option label="P0" value="P0" />
                <el-option label="P1" value="P1" />
                <el-option label="P2" value="P2" />
                <el-option label="P3" value="P3" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="需求状态">
              <el-select v-model="itemForm.requirement_status" style="width: 100%">
                <el-option label="暂停" value="paused" />
                <el-option label="已澄清&待技术评审" value="clarified_pending_review" />
                <el-option label="待排期" value="pending" />
                <el-option label="已排期待开发" value="scheduled" />
                <el-option label="开发中" value="developing" />
                <el-option label="已提测" value="submitted_testing" />
                <el-option label="测试中" value="testing" />
                <el-option label="测试完成待发布" value="test_done_pending_release" />
                <el-option label="灰度/AB中" value="gray_ab_testing" />
                <el-option label="已上线" value="released" />
                <el-option label="免测" value="no_test_needed" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="工单链接">
              <el-input v-model="itemForm.ticket_url" placeholder="需求工单链接" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="预计提测时间">
              <el-input v-model="itemForm.planned_test_date" placeholder="如 2/20" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="预估用例人日">
              <el-input-number v-model="itemForm.estimated_case_days" :min="0" :step="0.5" :precision="1" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="用例产出时间">
              <el-input v-model="itemForm.case_output_date" placeholder="如 2/18-2/19" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="用例状态">
              <el-select v-model="itemForm.case_status" clearable style="width: 100%">
                <el-option label="未开始" value="pending" />
                <el-option label="进行中" value="in_progress" />
                <el-option label="已完成" value="completed" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="预估测试人日">
              <el-input-number v-model="itemForm.estimated_test_days" :min="0" :step="0.5" :precision="1" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="测试时间段">
              <el-input v-model="itemForm.test_date_range" placeholder="如 2/20-2/22" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="集成测试时间">
              <el-input v-model="itemForm.integration_test_date" placeholder="如 2/25" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12" v-if="editingItem">
            <el-form-item label="进度(%)">
              <el-slider v-model="itemForm.actual_progress" :min="0" :max="100" :step="5" show-stops />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="备注">
              <el-input v-model="itemForm.remark" type="textarea" :rows="2" placeholder="备注" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="showCreateItem = false; editingItem = null">取消</el-button>
        <el-button type="primary" @click="handleSaveItem" :loading="saving">{{ editingItem ? '保存' : '创建' }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { Plus, Refresh } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useProjectStore } from '@/stores'
import {
  getIterations, createIteration,
  getScheduleItems, createScheduleItem, updateScheduleItem, deleteScheduleItem,
  getAssignableUsers
} from '@/api/schedule'
import { getProjectModules, getMyBusinessLines } from '@/api/module'
import { useUserStore } from '@/stores'

const projectStore = useProjectStore()
const userStore = useUserStore()
const projectId = computed(() => projectStore.currentProject?.id)
const isAdmin = computed(() => userStore.user?.is_superuser === true)

// 当前用户所属业务线
const myBusinessLines = ref([])
const myBizNames = computed(() => myBusinessLines.value.map(b => b.module_name))

// 迭代
const iterations = ref([])
const currentIterationId = ref(null)
const currentIteration = computed(() => iterations.value.find(i => i.id === currentIterationId.value))

// 排期条目
const scheduleItems = ref([])
const loading = ref(false)

// 过滤
const filterCategory = ref('')
const filterAssignee = ref(null)
const categories = computed(() => [...new Set(scheduleItems.value.map(i => i.category).filter(Boolean))])
const assigneeList = computed(() => {
  const map = new Map()
  scheduleItems.value.forEach(i => {
    if (i.assignee_id && i.assignee_name) map.set(i.assignee_id, { id: i.assignee_id, name: i.assignee_name })
  })
  return Array.from(map.values())
})
const filteredItems = computed(() => {
  let list = scheduleItems.value
  if (filterCategory.value) list = list.filter(i => i.category === filterCategory.value)
  if (filterAssignee.value) list = list.filter(i => i.assignee_id === filterAssignee.value)
  return list
})

// 成员列表
const memberList = ref([])

// 业务线（模块）列表
const moduleList = ref([])

// 表单
const showCreateIteration = ref(false)
const iterationForm = ref({ name: '', start_date: '', end_date: '' })
const creating = ref(false)

const showCreateItem = ref(false)
const editingItem = ref(null)
const saving = ref(false)
const itemForm = ref({
  requirement_title: '',
  category: '',
  assignee_id: null,
  priority: null,
  requirement_status: 'pending',
  ticket_url: '',
  planned_test_date: '',
  estimated_case_days: null,
  case_output_date: '',
  case_status: null,
  estimated_test_days: null,
  test_date_range: '',
  integration_test_date: '',
  remark: '',
  actual_progress: 0,
})

// 计算属性
const statusLabel = computed(() => {
  const map = { draft: '草稿', active: '进行中', completed: '已完成', archived: '已归档' }
  return map[currentIteration.value?.status] || ''
})
const statusTagType = computed(() => {
  const map = { draft: 'info', active: '', completed: 'success', archived: 'warning' }
  return map[currentIteration.value?.status] || ''
})

// 方法
function priorityTagType(p) {
  const map = { P0: 'danger', P1: 'warning', P2: '', P3: 'info' }
  return map[p] || ''
}
function reqStatusLabel(s) {
  const map = {
    paused: '暂停',
    clarified_pending_review: '已澄清&待技术评审',
    pending: '待排期',
    scheduled: '已排期待开发',
    developing: '开发中',
    submitted_testing: '已提测',
    testing: '测试中',
    test_done_pending_release: '测试完成待发布',
    gray_ab_testing: '灰度/AB中',
    released: '已上线',
    no_test_needed: '免测',
    completed: '已完成',
  }
  return map[s] || s
}
function reqStatusTagType(s) {
  const map = {
    paused: 'info',
    clarified_pending_review: 'warning',
    pending: 'info',
    scheduled: '',
    developing: 'warning',
    submitted_testing: '',
    testing: '',
    test_done_pending_release: 'success',
    gray_ab_testing: 'warning',
    released: 'success',
    no_test_needed: 'info',
    completed: 'success',
  }
  return map[s] || ''
}
function caseStatusLabel(s) {
  const map = { pending: '未开始', in_progress: '进行中', completed: '已完成' }
  return map[s] || s
}
function caseStatusTagType(s) {
  const map = { pending: 'info', in_progress: 'warning', completed: 'success' }
  return map[s] || ''
}
function progressColor(p) {
  if (p >= 80) return '#67c23a'
  if (p >= 50) return '#409eff'
  if (p >= 20) return '#e6a23c'
  return '#f56c6c'
}
function riskIcon(level) {
  const map = { none: '🟢', low: '🟡', medium: '🟠', high: '🔴' }
  return map[level] || '🟢'
}

async function loadIterations() {
  if (!projectId.value) return
  try {
    const res = await getIterations(projectId.value)
    const data = res.data || res
    iterations.value = data.iterations || data || []
    if (iterations.value.length > 0 && !currentIterationId.value) {
      // 默认选中第一个进行中的
      const active = iterations.value.find(i => i.status === 'active')
      currentIterationId.value = active?.id || iterations.value[0].id
    }
  } catch (e) {
    console.error('加载迭代失败', e)
  }
}

async function loadScheduleItems() {
  if (!projectId.value || !currentIterationId.value) return
  loading.value = true
  try {
    const res = await getScheduleItems(projectId.value, { iteration_id: currentIterationId.value })
    const data = res.data || res
    scheduleItems.value = data.items || data || []
  } catch (e) {
    console.error('加载排期条目失败', e)
  } finally {
    loading.value = false
  }
}

async function loadMembers() {
  if (!projectId.value) return
  try {
    const res = await getAssignableUsers(projectId.value)
    const data = res.data || res
    const users = data.users || []
    memberList.value = users.map(u => ({ id: u.id, name: u.real_name || u.username }))
  } catch (e) {
    console.error('加载成员列表失败', e)
  }
}

async function loadModules() {
  if (!projectId.value) return
  try {
    const res = await getProjectModules(projectId.value)
    const data = res.data || res
    moduleList.value = data.datas || data || []
  } catch (e) {
    console.error('加载模块列表失败', e)
  }
}

async function loadMyBusinessLines() {
  if (!projectId.value) return
  try {
    const res = await getMyBusinessLines(projectId.value)
    const data = res.data || res
    myBusinessLines.value = data.business_lines || []
    // 默认显示全部业务线，不自动筛选
  } catch (e) {
    console.error('加载用户业务线失败', e)
  }
}

// 判断当前用户是否可编辑某条排期
function canEditItem(item) {
  if (isAdmin.value) return true
  // 自己负责的条目可以编辑
  if (item.assignee_id === userStore.user?.id) return true
  // 同业务线的可以编辑
  if (item.category && myBizNames.value.includes(item.category)) return true
  return false
}

function handleIterationChange() {
  loadScheduleItems()
}

async function handleRefresh() {
  await loadIterations()
  await loadScheduleItems()
  ElMessage.success('刷新成功')
}

async function handleCreateIteration() {
  if (!iterationForm.value.name || !iterationForm.value.start_date || !iterationForm.value.end_date) {
    return ElMessage.warning('请填写完整信息')
  }
  creating.value = true
  try {
    await createIteration(projectId.value, iterationForm.value)
    ElMessage.success('迭代创建成功')
    showCreateIteration.value = false
    iterationForm.value = { name: '', start_date: '', end_date: '' }
    await loadIterations()
  } catch (e) {
    ElMessage.error('创建失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    creating.value = false
  }
}

function handleOpenCreateItem() {
  editingItem.value = null
  itemForm.value = {
    requirement_title: '',
    category: '',
    assignee_id: null,
    priority: null,
    requirement_status: 'pending',
    ticket_url: '',
    planned_test_date: '',
    estimated_case_days: null,
    case_output_date: '',
    case_status: null,
    estimated_test_days: null,
    test_date_range: '',
    integration_test_date: '',
    remark: '',
    actual_progress: 0,
  }
  showCreateItem.value = true
}

function editItem(row) {
  editingItem.value = row
  itemForm.value = {
    requirement_title: row.requirement_title,
    category: row.category,
    assignee_id: row.assignee_id,
    priority: row.priority,
    requirement_status: row.requirement_status,
    ticket_url: row.ticket_url,
    planned_test_date: row.planned_test_date,
    estimated_case_days: row.estimated_case_days,
    case_output_date: row.case_output_date,
    case_status: row.case_status,
    estimated_test_days: row.estimated_test_days,
    test_date_range: row.test_date_range,
    integration_test_date: row.integration_test_date,
    remark: row.remark,
    actual_progress: row.actual_progress || 0,
  }
  showCreateItem.value = true
}

async function handleSaveItem() {
  if (!itemForm.value.requirement_title) return ElMessage.warning('请输入需求名称')
  if (!editingItem.value && !itemForm.value.assignee_id) return ElMessage.warning('请选择负责人')

  saving.value = true
  try {
    if (editingItem.value) {
      await updateScheduleItem(projectId.value, editingItem.value.id, itemForm.value)
      ElMessage.success('更新成功')
    } else {
      await createScheduleItem(projectId.value, {
        ...itemForm.value,
        iteration_id: currentIterationId.value,
      })
      ElMessage.success('添加成功')
    }
    showCreateItem.value = false
    editingItem.value = null
    await loadScheduleItems()
  } catch (e) {
    ElMessage.error('操作失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    saving.value = false
  }
}

async function handleDeleteItem(row) {
  try {
    await ElMessageBox.confirm(`确认删除排期条目「${row.requirement_title}」？`, '删除确认', { type: 'warning' })
    await deleteScheduleItem(projectId.value, row.id)
    ElMessage.success('已删除')
    await loadScheduleItems()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  }
}

onMounted(async () => {
  await loadMyBusinessLines()
  await loadIterations()
  await loadScheduleItems()
  await loadMembers()
  await loadModules()
})

watch(projectId, () => {
  loadMyBusinessLines()
  loadIterations()
  loadMembers()
  loadModules()
})
</script>

<style scoped>
.schedule-container {
  padding: 16px;
}
.schedule-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.header-right {
  display: flex;
  gap: 8px;
}
.iteration-tag {
  margin-left: 4px;
}
.iteration-info {
  font-size: 13px;
  color: #999;
  display: flex;
  align-items: center;
  gap: 8px;
}
.progress-overview {
  margin-bottom: 16px;
}
.stat-card {
  text-align: center;
}
.stat-title {
  font-size: 13px;
  color: #999;
  margin-bottom: 8px;
}
.stat-value {
  font-size: 28px;
  font-weight: 700;
}
.schedule-table-card {
  margin-bottom: 16px;
}
.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.table-filters {
  display: flex;
  align-items: center;
}
.priority-tag {
  margin-right: 4px;
}
.ticket-link a {
  font-size: 12px;
  color: #409eff;
  text-decoration: none;
}

/* 修复固定列背景透明导致内容重叠 */
:deep(.el-table__fixed-right) {
  background-color: #fff;
}
:deep(.el-table__fixed-right .el-table__cell) {
  background-color: #fff;
}
:deep(.el-table--striped .el-table__body tr.el-table__row--striped .el-table__cell) {
  background-color: #fafafa;
}
:deep(.el-table td.el-table-fixed-column--right) {
  background-color: inherit;
}
</style>
