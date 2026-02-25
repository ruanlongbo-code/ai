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
          <el-button type="success" @click="handlePytestRun" :loading="pytestRunning">
            <el-icon><VideoPlay /></el-icon>
            pytest 批量执行
          </el-button>
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

    <!-- 筛选工具栏 -->
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

    <!-- pytest 执行结果弹窗 -->
    <el-dialog
      v-model="pytestResultDialogVisible"
      title="pytest 执行结果"
      width="780px"
      :close-on-click-modal="true"
    >
      <div class="pytest-result" v-if="pytestResult">
        <!-- 总体状态 -->
        <div class="pytest-status-bar" :class="pytestResult.status">
          <div class="status-icon-large">
            <el-icon v-if="pytestResult.status === 'passed'" :size="32"><CircleCheck /></el-icon>
            <el-icon v-else :size="32"><CircleClose /></el-icon>
          </div>
          <div class="status-text-large">
            <h2>{{ pytestResult.status === 'passed' ? '全部通过' : '存在失败' }}</h2>
            <p>{{ pytestResult.message }}</p>
          </div>
        </div>

        <!-- 统计卡片 -->
        <div class="pytest-stats">
          <div class="stat-card total">
            <div class="stat-number">{{ pytestResult.total }}</div>
            <div class="stat-label">总用例</div>
          </div>
          <div class="stat-card passed">
            <div class="stat-number">{{ pytestResult.passed }}</div>
            <div class="stat-label">通过</div>
          </div>
          <div class="stat-card failed">
            <div class="stat-number">{{ pytestResult.failed }}</div>
            <div class="stat-label">失败</div>
          </div>
          <div class="stat-card skipped">
            <div class="stat-number">{{ pytestResult.skipped || 0 }}</div>
            <div class="stat-label">跳过</div>
          </div>
          <div class="stat-card rate">
            <div class="stat-number">{{ pytestResult.pass_rate }}%</div>
            <div class="stat-label">通过率</div>
          </div>
          <div class="stat-card duration">
            <div class="stat-number">{{ pytestResult.duration }}s</div>
            <div class="stat-label">耗时</div>
          </div>
        </div>

        <!-- pytest 输出日志 -->
        <el-collapse v-if="pytestResult.stdout">
          <el-collapse-item title="pytest 执行日志">
            <pre class="pytest-log">{{ pytestResult.stdout }}</pre>
          </el-collapse-item>
        </el-collapse>
      </div>

      <template #footer>
        <el-button @click="pytestResultDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- pytest 环境选择弹窗 -->
    <el-dialog
      v-model="pytestEnvDialogVisible"
      title="选择执行环境"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form label-width="100px">
        <el-form-item label="测试环境">
          <el-select v-model="pytestEnvId" placeholder="选择测试环境（可选）" clearable style="width: 100%;">
            <el-option
              v-for="env in envOptions"
              :key="env.value"
              :label="env.label"
              :value="env.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="失败重试">
          <el-input-number v-model="pytestReruns" :min="0" :max="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="pytestEnvDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="executePytestRun" :loading="pytestRunning">
          开始执行
        </el-button>
      </template>
    </el-dialog>

    <!-- 新建用例弹窗 -->
    <el-dialog
      v-model="createDialogVisible"
      title="新建自动化用例"
      width="680px"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <el-form
        ref="createFormRef"
        :model="createForm"
        :rules="createRules"
        label-width="120px"
        label-position="top"
      >
        <el-form-item label="用例名称" prop="name">
          <el-input
            v-model="createForm.name"
            placeholder="请输入用例名称"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="接口路径" prop="interface_name">
          <el-input
            v-model="createForm.interface_name"
            placeholder="请输入接口路径，如 /api/users"
            maxlength="255"
          />
        </el-form-item>

        <div class="create-form-row">
          <el-form-item label="用例类型" prop="type" style="flex: 1;">
            <el-select v-model="createForm.type" placeholder="选择类型" style="width: 100%;">
              <el-option label="接口用例" value="api" />
              <el-option label="业务流用例" value="business" />
            </el-select>
          </el-form-item>

          <el-form-item label="用例状态" prop="status" style="flex: 1;">
            <el-select v-model="createForm.status" placeholder="选择状态" style="width: 100%;">
              <el-option label="可执行" value="ready" />
              <el-option label="待审核" value="pending" />
              <el-option label="不可执行" value="disabled" />
            </el-select>
          </el-form-item>
        </div>

        <el-form-item label="请求方法 & URL" prop="request">
          <div class="create-request-row">
            <el-select v-model="createForm.request.method" style="width: 140px;" placeholder="方法">
              <el-option label="GET" value="GET" />
              <el-option label="POST" value="POST" />
              <el-option label="PUT" value="PUT" />
              <el-option label="DELETE" value="DELETE" />
              <el-option label="PATCH" value="PATCH" />
            </el-select>
            <el-input
              v-model="createForm.request.url"
              placeholder="请输入请求URL路径"
              style="flex: 1; margin-left: 8px;"
            />
          </div>
        </el-form-item>

        <el-form-item label="基础URL">
          <el-input
            v-model="createForm.request.base_url"
            placeholder="基础URL，如 ${{base_url}}"
          />
        </el-form-item>

        <el-form-item label="用例描述">
          <el-input
            v-model="createForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入用例描述（可选）"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="createDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitCreateCase" :loading="creating">
            确认创建
          </el-button>
        </div>
      </template>
    </el-dialog>

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
import { Plus, Refresh, Search, VideoPlay, CircleCheck, CircleClose } from '@element-plus/icons-vue'
import {
  getApiTestCasesList,
  getProjectInterfaces,
  runSingleTestCase,
  getTestEnvironments,
  createApiTestCase,
  deleteApiTestCase,
  pytestRunCases,
  API_CASE_STATUS_LABELS,
  API_CASE_STATUS_TYPES
} from '@/api/apiTest'
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

// ========== 新建用例 ==========
const createDialogVisible = ref(false)
const creating = ref(false)
const createFormRef = ref()
const createForm = reactive({
  name: '',
  description: '',
  interface_name: '',
  type: 'api',
  status: 'ready',
  request: {
    method: 'GET',
    url: '',
    base_url: '${{base_url}}',
    headers: {},
    params: {},
    body: {}
  }
})

const createRules = {
  name: [
    { required: true, message: '请输入用例名称', trigger: 'blur' },
    { min: 1, max: 200, message: '长度在 1 到 200 个字符', trigger: 'blur' }
  ]
}

const resetCreateForm = () => {
  createForm.name = ''
  createForm.description = ''
  createForm.interface_name = ''
  createForm.type = 'api'
  createForm.status = 'ready'
  createForm.request = {
    method: 'GET',
    url: '',
    base_url: '${{base_url}}',
    headers: {},
    params: {},
    body: {}
  }
}

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
  handleEdit(row)
}

// ========== 新建用例 ==========
const handleCreate = () => {
  resetCreateForm()
  createDialogVisible.value = true
}

const submitCreateCase = async () => {
  if (!createFormRef.value) return
  try {
    await createFormRef.value.validate()
    creating.value = true

    const projectId = getProjectId()
    const payload = {
      name: createForm.name,
      description: createForm.description || undefined,
      interface_name: createForm.interface_name || undefined,
      type: createForm.type,
      status: createForm.status,
      preconditions: [],
      request: createForm.request,
      assertions: { response: [] }
    }

    const res = await createApiTestCase(projectId, payload)
    ElMessage.success('用例创建成功')
    createDialogVisible.value = false
    // 刷新列表
    await loadCases()

    // 如果创建成功，可以跳转到编辑页
    const newId = res?.data?.id || res?.id
    if (newId) {
      ElMessageBox.confirm('用例创建成功，是否立即编辑完善请求和断言配置？', '提示', {
        confirmButtonText: '去编辑',
        cancelButtonText: '留在列表',
        type: 'success'
      }).then(() => {
        router.push({
          name: 'ApiTestCaseEdit',
          params: { projectId, testCaseId: newId }
        })
      }).catch(() => {})
    }
  } catch (error) {
    if (error.message) {
      console.error('创建用例失败:', error)
      ElMessage.error(`创建用例失败: ${error.response?.data?.detail || error.message}`)
    }
  } finally {
    creating.value = false
  }
}

// ========== 编辑用例 ==========
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

// ========== 删除用例 ==========
const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除用例「${row.name}」吗？删除后不可恢复。`,
      '删除确认',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: 'el-button--danger'
      }
    )

    const projectId = getProjectId()
    await deleteApiTestCase(projectId, row.id)
    ElMessage.success('用例删除成功')
    // 如果当前页删完了，回到上一页
    if (cases.value.length === 1 && pagination.page > 1) {
      pagination.page--
    }
    await loadCases()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除用例失败:', error)
      ElMessage.error(`删除用例失败: ${error.response?.data?.detail || error.message || '未知错误'}`)
    }
  }
}

// ========== 运行用例 ==========
const handleRun = (row) => {
  selectedCase.value = row
  runEnvironmentDialogVisible.value = true
}

const handleRunCase = async (runConfig) => {
  try {
    runEnvironmentDialogVisible.value = false
    
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
    
    runResultDialogVisible.value = true
    
    const response = await runSingleTestCase(projectStore.currentProject.id, {
      case_id: runConfig.caseId,
      environment_id: runConfig.environmentId
    })
    
    const result = response.data
    const endTime = result.end_time || new Date().toISOString()
    const startTime = result.start_time || runResult.start_time
    let duration = result.duration

    if (!duration && startTime && endTime) {
      duration = (new Date(endTime) - new Date(startTime))
    } else if (duration) {
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
    
    if (result.status === 'success') {
      ElMessage.success('用例运行成功')
    } else {
      ElMessage.error(`用例运行失败: ${result.error_message || '未知错误'}`)
    }
    
  } catch (error) {
    console.error('运行用例失败:', error)
    
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

const handleRerunCase = () => {
  runResultDialogVisible.value = false
  setTimeout(() => {
    runEnvironmentDialogVisible.value = true
  }, 100)
}

// ========== pytest 批量执行 ==========
const pytestRunning = ref(false)
const pytestResultDialogVisible = ref(false)
const pytestEnvDialogVisible = ref(false)
const pytestResult = ref(null)
const pytestEnvId = ref(null)
const pytestReruns = ref(0)
const envOptions = ref([])

const loadEnvOptions = async () => {
  try {
    const projectId = getProjectId()
    const res = await getTestEnvironments(projectId, { page_size: 100 })
    const envList = res?.data?.environments || res?.environments || []
    envOptions.value = envList.map(e => ({ label: e.name, value: e.id }))
  } catch (e) {
    console.error('加载环境列表失败:', e)
  }
}

const handlePytestRun = async () => {
  await loadEnvOptions()
  pytestEnvDialogVisible.value = true
}

const executePytestRun = async () => {
  pytestEnvDialogVisible.value = false
  pytestRunning.value = true
  pytestResult.value = null

  try {
    const projectId = getProjectId()
    const payload = {
      environment_id: pytestEnvId.value || undefined,
      parallel: false,
      reruns: pytestReruns.value,
    }

    const res = await pytestRunCases(projectId, payload)
    pytestResult.value = res?.data || res
    pytestResultDialogVisible.value = true

    if (pytestResult.value?.status === 'passed') {
      ElMessage.success(`pytest 执行完成: 全部通过 (${pytestResult.value.passed}条)`)
    } else {
      ElMessage.warning(`pytest 执行完成: ${pytestResult.value?.failed || 0}条失败`)
    }
  } catch (error) {
    console.error('pytest 执行失败:', error)
    ElMessage.error(`pytest 执行失败: ${error.response?.data?.detail || error.message}`)
  } finally {
    pytestRunning.value = false
  }
}

onMounted(() => {
  if (route.query.interfaceId) {
    const q = Number(route.query.interfaceId)
    if (!Number.isNaN(q)) filters.interfaceId = q
  }
  loadInterfaces()
  loadCases()
})

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

/* 新建用例弹窗表单样式 */
.create-form-row {
  display: flex;
  gap: 16px;
}

.create-request-row {
  display: flex;
  align-items: center;
  width: 100%;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

/* ========== pytest 结果弹窗样式 ========== */
.pytest-result {
  padding: 0 8px;
}

.pytest-status-bar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px 24px;
  border-radius: 12px;
  margin-bottom: 20px;
}

.pytest-status-bar.passed {
  background: linear-gradient(135deg, #f0fdf4, #dcfce7);
  border: 1px solid #86efac;
}

.pytest-status-bar.failed {
  background: linear-gradient(135deg, #fef2f2, #fecaca);
  border: 1px solid #fca5a5;
}

.status-icon-large {
  flex-shrink: 0;
}

.pytest-status-bar.passed .status-icon-large {
  color: #22c55e;
}

.pytest-status-bar.failed .status-icon-large {
  color: #ef4444;
}

.status-text-large h2 {
  margin: 0 0 4px 0;
  font-size: 18px;
  font-weight: 600;
}

.status-text-large p {
  margin: 0;
  font-size: 13px;
  color: #6b7280;
}

.pytest-stats {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 12px;
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
  padding: 16px 8px;
  border-radius: 10px;
  border: 1px solid #e5e7eb;
  background: #fafbfc;
}

.stat-card.total { border-left: 3px solid #3b82f6; }
.stat-card.passed { border-left: 3px solid #22c55e; }
.stat-card.failed { border-left: 3px solid #ef4444; }
.stat-card.skipped { border-left: 3px solid #f59e0b; }
.stat-card.rate { border-left: 3px solid #8b5cf6; }
.stat-card.duration { border-left: 3px solid #06b6d4; }

.stat-number {
  font-size: 24px;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 12px;
  color: #9ca3af;
  font-weight: 500;
}

.pytest-log {
  background: #1e293b;
  color: #e2e8f0;
  padding: 16px;
  border-radius: 8px;
  font-size: 12px;
  line-height: 1.6;
  max-height: 400px;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-all;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .auto-case-page { padding: 16px; }
  .header-content { flex-direction: column; gap: 16px; align-items: stretch; }
  .filter-content { flex-direction: column; gap: 16px; align-items: stretch; }
  .filter-left .el-select, .filter-right .el-input { width: 100% !important; }
  .create-form-row { flex-direction: column; gap: 0; }
  .pytest-stats { grid-template-columns: repeat(3, 1fr); }
}
</style>
