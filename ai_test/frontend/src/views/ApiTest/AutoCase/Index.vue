<template>
  <div class="auto-case-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <h1>自动化用例管理</h1>
          <p class="subtitle">管理接口自动化测试用例列表</p>
        </div>
        <div class="action-section">
          <el-button type="primary" @click="handleCreate">
            <el-icon><Plus /></el-icon>
            新建用例
          </el-button>
          <el-button @click="handleRefresh">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </div>
    </div>

    <!-- 筛选工具栏（仅支持按接口过滤） -->
    <div class="filter-toolbar">
      <el-card>
        <div class="filter-content">
          <div class="filter-left">
            <el-select
              v-model="filters.interfaceId"
              placeholder="选择接口"
              clearable
              filterable
              @change="handleFilterChange"
              style="width: 260px; margin-right: 16px;"
            >
              <el-option
                v-for="opt in interfaceOptions"
                :key="opt.value"
                :label="opt.label"
                :value="opt.value"
              />
            </el-select>
          </div>
          <div class="filter-right">
            <el-input
              v-model="filters.keyword"
              placeholder="搜索用例名称"
              @input="handleSearch"
              clearable
              style="width: 300px;"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </div>
        </div>

        <!-- 已选筛选标签 -->
        <div class="active-filters" v-if="hasActiveFilters">
          <span class="label">已选筛选：</span>
          <el-space wrap>
            <el-tag
              v-if="filters.interfaceId"
              closable
              @close="() => clearFilter('interface')"
            >接口：{{ selectedInterfaceLabel }}</el-tag>
            <el-tag
              v-if="filters.keyword"
              closable
              @close="() => clearFilter('keyword')"
            >关键词：{{ filters.keyword }}</el-tag>
          </el-space>
          <el-button link type="primary" @click="clearAllFilters">清空筛选</el-button>
        </div>
      </el-card>
    </div>

    <!-- 列表表格 -->
    <div class="cases-table">
      <el-card>
        <div v-loading="loading" class="table-content">
          <el-table
            v-if="cases.length > 0"
            :data="cases"
            stripe
            @row-click="handleRowClick"
            class="cases-table-inner"
          >
            <el-table-column prop="id" label="ID" width="90" />

            <el-table-column prop="name" label="用例名称" min-width="220">
              <template #default="{ row }">
                <div class="case-title">
                  <span class="title-text">{{ row.name }}</span>
                </div>
              </template>
            </el-table-column>

            <el-table-column prop="interface_name" label="接口路径名称" min-width="220">
              <template #default="{ row }">
                <span>{{ row.interface_name || '-' }}</span>
              </template>
            </el-table-column>

            <el-table-column prop="type" label="类型" width="120">
              <template #default="{ row }">
                <el-tag effect="light" size="small">{{ row.type || '-' }}</el-tag>
              </template>
            </el-table-column>

            <el-table-column prop="status" label="状态" width="120">
              <template #default="{ row }">
                <el-tag 
                  :type="API_CASE_STATUS_TYPES[row.status] || 'info'" 
                  effect="light" 
                  size="small"
                >
                  {{ API_CASE_STATUS_LABELS[row.status] || row.status || '-' }}
                </el-tag>
              </template>
            </el-table-column>

            <el-table-column prop="generation_count" label="生成次数" width="110" />

            <el-table-column prop="created_at" label="创建时间" width="180">
              <template #default="{ row }">
                {{ formatDate(row.created_at) }}
              </template>
            </el-table-column>

            <el-table-column prop="updated_at" label="更新时间" width="180">
              <template #default="{ row }">
                {{ formatDate(row.updated_at) }}
              </template>
            </el-table-column>

            <el-table-column label="操作" width="260" fixed="right">
              <template #default="{ row }">
                <el-button size="small" @click.stop="handleEdit(row)">编辑</el-button>
                <el-button size="small" type="success" @click.stop="handleRun(row)">运行</el-button>
                <el-button size="small" type="danger" @click.stop="handleDelete(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>

          <!-- 空状态 -->
          <div v-else class="empty-state">
            <el-empty description="暂无自动化用例数据">
              <el-button type="primary" @click="handleCreate">创建第一个用例</el-button>
            </el-empty>
          </div>
        </div>
        <div class="table-footer" v-if="pagination.total > 0">
          <el-pagination
            :current-page="pagination.page"
            :page-size="pagination.pageSize"
            :page-sizes="[10, 20, 50]"
            :total="pagination.total"
            layout="total, sizes, prev, pager, next, jumper"
            @current-change="handlePageChange"
            @size-change="handlePageSizeChange"
          />
        </div>
      </el-card>
    </div>

    <!-- 运行环境选择弹框 -->
    <RunEnvironmentDialog
      v-model="runEnvironmentDialogVisible"
      :case-info="selectedCase"
      @run="handleRunCase"
    />

    <!-- 运行结果显示弹框 -->
    <RunResultDialog
      v-model="runResultDialogVisible"
      :run-result="runResult"
      @rerun="handleRerunCase"
    />
  </div>
  
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh, Search } from '@element-plus/icons-vue'
import { getApiTestCasesList, getProjectInterfaces, runSingleTestCase, getTestEnvironments, API_CASE_STATUS_LABELS, API_CASE_STATUS_TYPES } from '@/api/apiTest'
import { useProjectStore } from '@/stores'
import RunEnvironmentDialog from './components/RunEnvironmentDialog.vue'
import RunResultDialog from './components/RunResultDialog.vue'

const route = useRoute()
const router = useRouter()
const projectStore = useProjectStore()

const loading = ref(false)
const cases = ref([])
const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0,
  totalPages: 0
})

const filters = reactive({
  interfaceId: null,
  keyword: ''
})

const interfaceOptions = ref([])

// 运行相关的响应式数据
const runEnvironmentDialogVisible = ref(false)
const runResultDialogVisible = ref(false)
const selectedCase = ref({})
const runResult = reactive({
  status: 'pending',
  case_name: '',
  case_id: null,
  case_run_id: null,
  environmentName: '',
  start_time: null,
  end_time: null,
  duration: null,
  error_message: null,
  logs: [],
  case_data: {},
  request_info: []
})

const formatDate = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit'
  })
}

const getProjectId = () => {
  let projectId = route.params.projectId || projectStore.currentProject.id
  if (!projectId) {
    try {
      const projectStr = localStorage.getItem('currentProject')
      if (projectStr) projectId = JSON.parse(projectStr)?.id
    } catch {}
  }
  return projectId || 1
}

const loadInterfaces = async () => {
  const projectId = getProjectId()
  try {
    const res = await getProjectInterfaces(projectId, { page: 1, page_size: 200 })
    const list = res?.data?.interfaces || res?.interfaces || []
    interfaceOptions.value = list.map(it => ({ label: it.summary || it.path, value: it.id }))
  } catch (e) {
    console.error('加载接口列表失败', e)
  }
}

const loadCases = async () => {
  const projectId = getProjectId()
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      interface_id: filters.interfaceId || undefined,
      keyword: filters.keyword || undefined
    }
    const res = await getApiTestCasesList(projectId, params)
    if (res && res.data) {
      cases.value = res.data.test_cases || []
      pagination.total = res.data.total || 0
      pagination.totalPages = res.data.total_pages || 0
    } else {
      cases.value = res.test_cases || []
      pagination.total = res.total || 0
      pagination.totalPages = res.total_pages || 0
    }
  } catch (e) {
    console.error('加载自动化用例列表失败', e)
    ElMessage.error('加载自动化用例列表失败，请稍后重试')
    cases.value = []
  } finally {
    loading.value = false
  }
}

const handleFilterChange = () => {
  pagination.page = 1
  loadCases()
}

const hasActiveFilters = computed(() => !!(filters.interfaceId || (filters.keyword && filters.keyword.trim())))
const selectedInterfaceLabel = computed(() => {
  const opt = interfaceOptions.value.find(o => o.value === filters.interfaceId)
  return opt ? opt.label : '-'
})

const clearFilter = (key) => {
  if (key === 'interface') filters.interfaceId = null
  if (key === 'keyword') filters.keyword = ''
  pagination.page = 1
  loadCases()
}

const clearAllFilters = () => {
  filters.interfaceId = null
  filters.keyword = ''
  pagination.page = 1
  loadCases()
}

const handlePageChange = (page) => {
  pagination.page = page
  loadCases()
}

const handlePageSizeChange = (pageSize) => {
  pagination.pageSize = pageSize
  pagination.page = 1
  loadCases()
}

const handleRefresh = async () => {
  await Promise.all([loadCases(), loadInterfaces()])
  ElMessage.success('刷新成功')
}

const handleRowClick = (row) => {
  handleView(row)
}

// 占位操作：按钮功能后续实现
const handleCreate = () => ElMessage.info('新建用例功能开发中...')
// 编辑用例 - 跳转到独立编辑页面
const handleEdit = (row) => {
  const projectId = getProjectId()
  router.push({
    name: 'ApiTestCaseEdit',
    params: {
      projectId: projectId,
      testCaseId: row.id
    }
  })
}

const handleDelete = (row) => ElMessage.info(`删除用例（待实现）：${row.name}`)

// 运行用例 - 打开环境选择弹框
const handleRun = (row) => {
  selectedCase.value = row
  runEnvironmentDialogVisible.value = true
}

// 执行用例运行
const handleRunCase = async (runConfig) => {
  try {
    // 关闭环境选择弹框
    runEnvironmentDialogVisible.value = false
    
    // 获取环境名称
    let environmentName = `环境ID: ${runConfig.environmentId}`
    try {
      const envResponse = await getTestEnvironments(projectStore.currentProject.id, { page_size: 100 })
      const environment = envResponse.data.environments?.find(env => env.id === runConfig.environmentId)
      if (environment) {
        environmentName = environment.name
      }
    } catch (error) {
      console.warn('获取环境名称失败:', error)
    }
    
    // 设置运行结果初始状态
    Object.assign(runResult, {
      status: 'running',
      case_name: runConfig.caseName,
      case_id: runConfig.caseId,
      case_run_id: null,
      environmentName: environmentName,
      start_time: new Date().toISOString(),
      end_time: null,
      duration: null
    })
    
    // 显示运行结果弹框
    runResultDialogVisible.value = true
    
    // 调用后端API执行用例
    const response = await runSingleTestCase(projectStore.currentProject.id, {
      case_id: runConfig.caseId,
      environment_id: runConfig.environmentId
    })
    
    // 处理运行结果
    const result = response.data
    const endTime = result.end_time || new Date().toISOString()
    const startTime = result.start_time || runResult.start_time
    let duration = result.duration

    // 如果后端没有返回duration，则计算（转换为毫秒）
    if (!duration && startTime && endTime) {
      duration = (new Date(endTime) - new Date(startTime))
    } else if (duration) {
      // 后端返回的是秒，转换为毫秒
      duration = parseFloat(duration) * 1000
    }
    
    Object.assign(runResult, {
      status: result.status === 'success' ? 'success' : 'failed',
      case_name: result.case_name || runConfig.caseName,
      case_id: result.case_id || runConfig.caseId,
      case_run_id: result.case_run_id,
      environmentName: environmentName,
      start_time: result.start_time || startTime,
      end_time: endTime,
      duration: duration,
      error_message: result.error_message || null,
      logs: result.logs || [],
      case_data: result.case_data || {},
      request_info: result.request_info || []
    })
    
    // 显示运行结果消息
    if (result.status === 'success') {
      ElMessage.success('用例运行成功')
    } else {
      ElMessage.error(`用例运行失败: ${result.error_message || '未知错误'}`)
    }
    
  } catch (error) {
    console.error('运行用例失败:', error)
    
    // 更新运行结果为失败状态
    Object.assign(runResult, {
      status: 'failed',
      end_time: new Date().toISOString(),
      duration: (new Date() - new Date(runResult.start_time)),
      error_message: error.response?.data?.detail || error.message || '运行用例时发生未知错误',
      logs: [],
      case_data: {},
      request_info: []
    })
    
    ElMessage.error(`运行用例失败: ${error.response?.data?.detail || error.message || '未知错误'}`)
  }
}

// 重新运行用例
const handleRerunCase = () => {
  runResultDialogVisible.value = false
  // 重新打开环境选择弹框
  setTimeout(() => {
    runEnvironmentDialogVisible.value = true
  }, 100)
}

onMounted(() => {
  // 路由带入的接口过滤（如 ?interfaceId=123）
  if (route.query.interfaceId) {
    const q = Number(route.query.interfaceId)
    if (!Number.isNaN(q)) filters.interfaceId = q
  }
  loadInterfaces()
  loadCases()
})

// 搜索输入节流/防抖
let searchTimer = null
const handleSearch = () => {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    pagination.page = 1
    loadCases()
  }, 300)
}
</script>

<style scoped>
.auto-case-page {
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
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.title-section h1 {
  color: #1f2937;
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
}

.subtitle {
  color: #6b7280;
  margin: 0;
  font-size: 14px;
}

.action-section {
  display: flex;
  gap: 12px;
}

.filter-toolbar {
  margin-bottom: 5px;
}

.filter-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-left {
  display: flex;
  align-items: center;
}

.active-filters {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 12px;
}

.active-filters .label {
  color: #6b7280;
  font-size: 13px;
}

.cases-table {
  background: white;
  border-radius: 8px;
  overflow: hidden;
}

.table-content {
  min-height: 400px;
}

.cases-table-inner {
  width: 100%;
}

.case-title { display: flex; flex-direction: column; gap: 4px; }
.title-text { font-weight: 500; color: #1f2937; }

/* 状态标签样式优化 */
.el-tag {
  font-weight: 500;
  border-radius: 4px;
  padding: 0 8px;
  height: 24px;
  line-height: 22px;
}

.el-tag.el-tag--success {
  background-color: #f0f9ff;
  border-color: #67c23a;
  color: #67c23a;
}

.el-tag.el-tag--warning {
  background-color: #fef3e2;
  border-color: #e6a23c;
  color: #e6a23c;
}

.el-tag.el-tag--danger {
  background-color: #fef2f2;
  border-color: #f56c6c;
  color: #f56c6c;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 400px;
}

.table-footer { display: flex; justify-content: flex-end; padding: 12px 0; }

/* 响应式设计 */
@media (max-width: 768px) {
  .auto-case-page { padding: 16px; }
  .header-content { flex-direction: column; gap: 16px; align-items: stretch; }
  .filter-content { flex-direction: column; gap: 16px; align-items: stretch; }
  .filter-left .el-select, .filter-right .el-input { width: 100% !important; }
}
</style>