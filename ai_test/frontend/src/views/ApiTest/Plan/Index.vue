<template>
  <div class="plan-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <h1>测试计划管理</h1>
          <p class="subtitle">管理接口测试计划（测试任务）列表</p>
        </div>
        <div class="action-section">
          <el-button type="primary" @click="handleCreate">
            <el-icon>
              <Plus/>
            </el-icon>
            新建计划
          </el-button>
          <el-button @click="handleRefresh">
            <el-icon>
              <Refresh/>
            </el-icon>
            刷新
          </el-button>
        </div>
      </div>
    </div>

    <!-- 筛选工具栏（本地筛选：类型与关键字） -->
    <div class="filter-toolbar">
      <el-card>
        <div class="filter-content">
          <div class="filter-left">
            <el-select
                v-model="filters.type"
                placeholder="计划类型"
                clearable
                style="width: 180px; margin-right: 16px;"
                @change="applyLocalFilters"
            >
              <el-option label="API计划" value="api"/>
              <el-option label="UI计划" value="ui"/>
            </el-select>
          </div>
          <div class="filter-right">
            <el-input
                v-model="filters.keyword"
                placeholder="搜索计划名称或描述"
                clearable
                style="width: 300px;"
                @input="handleSearch"
            >
              <template #prefix>
                <el-icon>
                  <Search/>
                </el-icon>
              </template>
            </el-input>
          </div>
        </div>

        <!-- 已选筛选标签（本地） -->
        <div class="active-filters" v-if="hasActiveFilters">
          <span class="label">已选条件：</span>
          <el-tag
              v-if="filters.type"
              closable
              type="info"
              @close="clearFilter('type')"
          >
            类型：{{ filters.type === 'api' ? 'API' : 'UI' }}
          </el-tag>
          <el-tag
              v-if="filters.keyword"
              closable
              type="info"
              @close="clearFilter('keyword')"
          >
            关键词：{{ filters.keyword }}
          </el-tag>
          <el-button text type="primary" @click="clearAllFilters" style="margin-left: 8px;">
            清空筛选
          </el-button>
        </div>
      </el-card>
    </div>

    <!-- 列表卡片 -->
    <div class="page-content">


      <el-table :data="displayedTasks" v-loading="loading" border stripe>
        <el-table-column prop="task_name" label="计划名称" min-width="220">
          <template #default="{row}">
            <div class="name-cell">
              <el-icon class="name-icon">
                <Calendar/>
              </el-icon>
              <span class="name-text">{{ row.task_name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="类型" width="120" align="center">
          <template #default="{row}">
            <el-tag :type="typeTagType(row.type)">
              {{ typeLabel(row.type) }}
            </el-tag>
          </template>
        </el-table-column>
    
        <el-table-column prop="description" label="描述" min-width="260" show-overflow-tooltip/>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{row}">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column prop="updated_at" label="更新时间" width="180">
          <template #default="{row}">{{ formatDate(row.updated_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="260" fixed="right">
          <template #default="{row}"
          >
            <el-button size="small" type="primary" plain @click="viewDetail(row)" icon="Edit">计划详情</el-button>
            <el-button size="small" type="danger" plain @click="deleteTask(row)" icon="Delete">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="table-footer">
        <el-pagination
            background
            layout="prev, pager, next, jumper, sizes, total"
            :total="pagination.total"
            :current-page="pagination.page"
            :page-size="pagination.pageSize"
            :page-sizes="[10, 20, 30, 50]"
            @current-change="handlePageChange"
            @size-change="handleSizeChange"
        />
      </div>

    </div>
  </div>

  <!-- 新建计划对话框 -->
  <CreateTaskDialog
      v-model="createDialogVisible"
      @submit="handleCreateSubmit"
      ref="createDialogRef"
  />
</template>

<script setup>
import {ref, reactive, computed, onMounted} from 'vue'
import {useRoute, useRouter} from 'vue-router'
import {ElMessage} from 'element-plus'
import {Plus, Refresh, Search, Calendar} from '@element-plus/icons-vue'
import {useProjectStore} from '@/stores'
import {getTestTasks, createTestTask} from '@/api/test_management'
import CreateTaskDialog from './components/CreateTaskDialog.vue'

const route = useRoute()
const router = useRouter()
const projectStore = useProjectStore()

// 加载状态与数据
const loading = ref(false)
const tasks = ref([])
const displayedTasks = ref([])

// 分页
const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0,
  totalPages: 0
})

// 筛选（本地）
const filters = reactive({
  type: '',
  keyword: ''
})

const hasActiveFilters = computed(() => !!(filters.type || filters.keyword))

// 新建计划对话框
const createDialogVisible = ref(false)
const createDialogRef = ref(null)

const typeLabel = (type) => {
  const map = { api: 'API', ui: 'UI', functional: '功能测试' }
  return map[type] || type || '-'
}

const typeTagType = (type) => {
  const map = { api: 'success', ui: 'warning', functional: '' }
  return map[type] || 'info'
}

const formatDate = (val) => {
  if (!val) return '-'
  const d = new Date(val)
  if (Number.isNaN(d.getTime())) return val
  const pad = (n) => (n < 10 ? `0${n}` : `${n}`)
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

const statusLabel = (s) => {
  switch (s) {
    case 'pending':
      return '待执行'
    case 'running':
      return '执行中'
    case 'completed':
      return '已完成'
    case 'failed':
      return '失败'
    default:
      return s || '-'
  }
}
const statusType = (s) => {
  switch (s) {
    case 'pending':
      return 'info'
    case 'running':
      return 'warning'
    case 'completed':
      return 'success'
    case 'failed':
      return 'danger'
    default:
      return 'default'
  }
}

const getProjectId = () => {
  if (projectStore.currentProject?.id) return projectStore.currentProject.id
  if (route.params.projectId) return parseInt(route.params.projectId)
  if (route.query.projectId) return parseInt(route.query.projectId)
  try {
    const projectStr = localStorage.getItem('currentProject')
    if (projectStr) return JSON.parse(projectStr)?.id
  } catch (e) {
    console.error('解析localStorage项目信息失败:', e)
  }
  // 兜底：无法获取项目ID时提示并跳转项目页
  ElMessage.error('请先选择项目')
  router.push('/project')
  return null
}

const loadTasks = async () => {
  const projectId = getProjectId()
  if (!projectId) return
  loading.value = true
  try {
    const res = await getTestTasks(projectId, {page: pagination.page, page_size: pagination.pageSize})
    const data = res?.data || res
    tasks.value = data?.tasks || []
    pagination.total = data?.total || 0
    pagination.totalPages = data?.total_pages || 0
    applyLocalFilters()
  } catch (e) {
    console.error('加载测试计划失败:', e)
    ElMessage.error('加载测试计划失败，请稍后重试')
    tasks.value = []
    displayedTasks.value = []
  } finally {
    loading.value = false
  }
}

const applyLocalFilters = () => {
  let list = [...tasks.value]
  if (filters.type) list = list.filter(t => t.type === filters.type)
  if (filters.keyword) {
    const kw = filters.keyword.trim().toLowerCase()
    list = list.filter(t => (t.task_name || '').toLowerCase().includes(kw) || (t.description || '').toLowerCase().includes(kw))
  }
  displayedTasks.value = list
}

let searchTimer = null
const handleSearch = () => {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => applyLocalFilters(), 300)
}

const clearFilter = (key) => {
  filters[key] = ''
  applyLocalFilters()
}
const clearAllFilters = () => {
  filters.type = ''
  filters.keyword = ''
  applyLocalFilters()
}

const handleCreate = () => {
  createDialogVisible.value = true
}

const handleCreateSubmit = async (payload) => {
  const projectId = getProjectId()
  if (!projectId) return
  try {
    const res = await createTestTask(projectId, {
      task_name: payload.task_name,
      type: payload.type,
      description: payload.description
    })
    const data = res?.data || res
    const newTaskId = data?.id

    ElMessage.success('测试计划创建成功')
    // 关闭对话框并重置
    if (createDialogRef.value && createDialogRef.value.handleSubmitSuccess) {
      createDialogRef.value.handleSubmitSuccess()
    } else {
      createDialogVisible.value = false
    }

    // 跳转到编辑页面
    if (newTaskId) {
      router.push({
        name: 'ApiTestPlanEdit',
        params: { projectId, taskId: newTaskId }
      })
    } else {
      // 回退方案：刷新列表
      await loadTasks()
    }
  } catch (e) {
    console.error('创建测试计划失败:', e)
    ElMessage.error('创建测试计划失败，请稍后重试')
  }
}
const handleRefresh = async () => {
  // 清空筛选条件，重新加载全部数据
  filters.type = ''
  filters.keyword = ''
  pagination.page = 1
  await loadTasks()
  ElMessage.success('刷新成功')
}
const viewDetail = (row) => {
  const pid = getProjectId()
  if (!pid) return
  router.push({
    name: 'ApiTestPlanEdit',
    params: {
      projectId: pid,
      taskId: row.id
    }
  })
}
const deleteTask = (row) => {
  ElMessage.info(`删除计划（开发中）：${row.task_name}`)
}

const handlePageChange = (p) => {
  pagination.page = p
  loadTasks()
}
const handleSizeChange = (ps) => {
  pagination.pageSize = ps
  pagination.page = 1
  loadTasks()
}

onMounted(() => {
  loadTasks()
})
</script>

<style scoped>
.plan-page {
  padding: 24px;
  background: #f8fafc;
  min-height: 100vh;
}

.page-header {
  margin-bottom: 5px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  background: white;
  padding: 24px;
  border-radius: 8px;
}

.title-section h1 {
  margin: 0;
  font-size: 22px;
  color: #1f2937;
}

.subtitle {
  margin: 6px 0 0;
  color: #6b7280;
}

.action-section .el-button + .el-button {
  margin-left: 8px;
}

.filter-toolbar {
  margin: 16px 0;
}

.filter-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.active-filters {
  margin-top: 10px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.active-filters .label {
  color: #6b7280;
  font-size: 13px;
}

.content-card {
  border: none;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.08);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.table-footer {
  padding: 16px;
  display: flex;
  justify-content: flex-end;
}

.name-cell {
  display: flex;
  align-items: center;
}

.name-icon {
  margin-right: 6px;
  color: #6366f1;
}

.name-text {
  font-weight: 500;
  color: #111827;
}
</style>