<template>
  <div class="base-case-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <h1>测试点管理</h1>
          <p class="subtitle">管理接口测试点列表</p>
        </div>
        <div class="action-section">
          <el-button type="primary" @click="openCreateDialog">
            <el-icon>
              <Plus/>
            </el-icon>
            新建测试点
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
                placeholder="搜索测试点名称"
                @input="handleSearchDebounced"
                clearable
                style="width: 300px;"
            >
              <template #prefix>
                <el-icon>
                  <Search/>
                </el-icon>
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
                @close="() => clearFilter('interfaceId')"
            >接口：{{ selectedInterfaceLabel }}
            </el-tag>
            <el-tag
                v-if="filters.method"
                closable
                @close="() => clearFilter('method')"
            >方法：{{ filters.method }}
            </el-tag>
            <el-tag
                v-if="filters.status"
                closable
                @close="() => clearFilter('status')"
            >状态：{{ getStatusLabel(filters.status) }}
            </el-tag>
            <el-tag
                v-if="filters.keyword"
                closable
                @close="() => clearFilter('keyword')"
            >关键词：{{ filters.keyword }}
            </el-tag>
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
              v-if="filteredCases.length > 0"
              :data="filteredCases"
              stripe
              @row-click="handleRowClick"
              class="cases-table-inner"
          >
            <el-table-column prop="id" label="ID" width="100">
              <template #default="{ row }">
                <span>{{ row.id }}</span>
              </template>
            </el-table-column>

            <el-table-column prop="name" label="测试点" min-width="220">
              <template #default="{ row }">
                <div class="case-title">
                  <span class="title-text">{{ row.name }}</span>
                </div>
              </template>
            </el-table-column>

            <el-table-column prop="interface_name" label="所属接口" min-width="220">
              <template #default="{ row }">
                <span>{{ row.interface_name || '-' }}</span>
              </template>
            </el-table-column>

            <el-table-column prop="status" label="状态" width="120">
              <template #default="{ row }">
                <el-tag effect="light" size="small">{{ row.status || '-' }}</el-tag>
              </template>
            </el-table-column>


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

            <el-table-column label="操作" width="320" fixed="right">
              <template #default="{ row }">
                <el-button size="small" type="primary" @click.stop="handleViewCase(row)">查看</el-button>
                <el-button size="small" @click.stop="openEditDialog(row)">编辑</el-button>
                <el-button size="small" type="success" @click.stop="goToGenerate(row)">生成可执行用例</el-button>
                <el-button size="small" type="danger" @click.stop="handleDelete(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>

          <!-- 空状态 -->
          <div v-else class="empty-state">
            <el-empty description="暂无测试点数据">
              <el-button type="primary" @click="openCreateDialog">创建第一个测试点</el-button>
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
  </div>

  <!-- 新建/编辑测试点弹窗 -->
  <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="900px"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      class="base-case-dialog"
  >
    <el-form label-width="100px" class="base-case-form">
      <el-form-item label="关联接口" v-if="!isEdit">
        <el-select
            v-model="form.interface_id"
            filterable
            placeholder="请选择接口"
            style="width: 100%"
        >
          <el-option v-for="opt in interfaceOptions" :key="opt.value" :label="opt.label" :value="opt.value"/>
        </el-select>
      </el-form-item>

      <el-form-item label="用例名称">
        <el-input
            v-model="form.name"
            placeholder="请输入用例名称"
            style="width: 100%"
        />
      </el-form-item>

      <el-form-item label="测试步骤" class="json-editor-form-item">
        <div class="json-editor-wrapper">
          <div class="json-editor-header">
            <span class="editor-label">测试步骤 (JSON 数组格式)</span>

          </div>
          <JsonEditor
              v-model="form.stepsText"
              height="200px"
              placeholder='请输入测试步骤，格式如: [{"desc": "步骤1", "action": "发送请求"}, {"desc": "步骤2", "action": "验证响应"}]'
              @change="onStepsChange"
          />
        </div>
      </el-form-item>

      <el-form-item label="预期结果" class="json-editor-form-item">
        <div class="json-editor-wrapper">
          <div class="json-editor-header">
            <span class="editor-label">预期结果 (JSON 数组格式)</span>

          </div>
          <JsonEditor
              v-model="form.expectedText"
              height="180px"
              placeholder='请输入预期结果，格式如: [{"desc": "状态码为200"}, {"desc": "响应包含用户信息"}]'
              @change="onExpectedChange"
          />
        </div>
      </el-form-item>
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleCancel">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">
          {{ isEdit ? '更新' : '创建' }}
        </el-button>
      </div>
    </template>
  </el-dialog>

  <!-- 查看测试点弹窗 -->
  <el-dialog
      v-model="viewDialogVisible"
      title="查看测试点"
      width="900px"
      :close-on-click-modal="false"
      class="view-case-dialog"
  >
    <div class="view-case-content">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="用例ID">
          {{ viewData.id || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="用例名称">
          {{ viewData.name || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="关联接口">
          {{ viewData.interface_name || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag effect="light" size="small">{{ viewData.status || '-' }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">
          {{ formatDate(viewData.created_at) }}
        </el-descriptions-item>
        <el-descriptions-item label="更新时间">
          {{ formatDate(viewData.updated_at) }}
        </el-descriptions-item>
      </el-descriptions>

      <div class="view-section">
        <h4 class="section-title">测试步骤</h4>
        <div class="json-display">
          <JsonEditor
              :model-value="viewData.steps || []"
              height="200px"
              :read-only="true"
              theme="light"
          />
        </div>
      </div>

      <div class="view-section">
        <h4 class="section-title">预期结果</h4>
        <div class="json-display">
          <JsonEditor
              :model-value="viewData.expected || []"
              height="180px"
              :read-only="true"
              theme="light"
          />
        </div>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="viewDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="handleEditFromView">编辑</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import {ref, reactive, computed, onMounted} from 'vue'
import {useRouter, useRoute} from 'vue-router'
import {ElMessage, ElMessageBox} from 'element-plus'
import {Plus, Refresh} from '@element-plus/icons-vue'
import {getBasicCasesList, deleteBasicCase, createBasicCase, updateBasicCase, getProjectInterfaces} from '@/api/apiTest'
import {useProjectStore} from '@/stores'
import JsonEditor from '@/components/JsonEditor.vue'

const router = useRouter()
const route = useRoute()
const projectStore = useProjectStore()

// 响应式数据
const loading = ref(false)
const cases = ref([])
const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0,
  totalPages: 0
})

// 筛选条件
const filters = reactive({
  interfaceId: null,
  method: '',
  status: '',
  keyword: ''
})

// 计算属性
// 后端字段映射后的列表数据
const filteredCases = computed(() => {
  if (!Array.isArray(cases.value)) {
    return []
  }

  let result = cases.value

  // 关键词搜索（前端实现）
  if (filters.keyword && filters.keyword.trim()) {
    const keyword = filters.keyword.toLowerCase().trim()
    result = result.filter(item =>
        (item.name && item.name.toLowerCase().includes(keyword))
    )
  }

  // HTTP方法过滤（前端实现）
  if (filters.method) {
    result = result.filter(item => {
      // 从接口信息中获取方法，或者从用例数据中获取
      const method = item.interface?.method || item.method
      return method === filters.method
    })
  }

  // 状态过滤（前端实现）
  if (filters.status) {
    result = result.filter(item => item.status === filters.status)
  }

  return result
})

// 方法
const formatDate = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 列表字段简要预览：[{...}] 或 ['...'] 或 {...}
const formatListPreview = (list) => {
  if (!Array.isArray(list) || list.length === 0) return '-'
  const first = list[0]
  let firstText = ''
  if (typeof first === 'string') {
    firstText = first
  } else if (typeof first === 'object' && first !== null) {
    firstText = first.text || first.desc || first.name || JSON.stringify(first)
  } else {
    firstText = String(first)
  }
  return `${list.length}项，首项：${firstText}`
}

// 新增/编辑对话框
const dialogVisible = ref(false)
const dialogTitle = ref('新建测试点')
const isEdit = ref(false)
const submitting = ref(false)
const interfaceOptions = ref([])

// 查看对话框
const viewDialogVisible = ref(false)
const viewData = ref({})

const form = reactive({
  id: null,
  interface_id: null,
  name: '',
  stepsText: '[\n  { "desc": "步骤1" }\n]',
  expectedText: '[\n  { "desc": "预期1" }\n]',
  status: 'draft'
})

// 存储解析后的JSON对象，避免重复解析
const parsedSteps = ref([])
const parsedExpected = ref([])

const loadInterfaces = async () => {
  let projectId = route.params.projectId || projectStore.currentProject?.id
  if (!projectId) {
    const projectStr = localStorage.getItem('currentProject')
    if (projectStr) {
      projectId = JSON.parse(projectStr)?.id
    }
  }
  if (!projectId) return
  try {
    const res = await getProjectInterfaces(projectId, {page: 1, page_size: 100})
    const list = res?.data?.interfaces || res?.interfaces || []
    interfaceOptions.value = list.map(it => ({label: it.summary || it.path, value: it.id}))
  } catch (e) {
    console.error('加载接口列表失败', e)
  }
}

const resetForm = () => {
  form.id = null
  form.interface_id = null
  form.name = ''
  form.stepsText = '[\n  { "desc": "步骤1" }\n]'
  form.expectedText = '[\n  { "desc": "预期1" }\n]'
  form.status = 'draft'
  
  // 同时重置解析后的对象
  parsedSteps.value = [{ "desc": "步骤1" }]
  parsedExpected.value = [{ "desc": "预期1" }]
}


const onStepsChange = (value) => {
  form.stepsText = value.text
  parsedSteps.value = value.json || []
}

const onExpectedChange = (value) => {
  form.expectedText = value.text
  parsedExpected.value = value.json || []
}

const handleCancel = () => {
  dialogVisible.value = false

}

const openCreateDialog = async () => {
  isEdit.value = false
  dialogTitle.value = '新建测试点'
  resetForm()
  dialogVisible.value = true
}

const openEditDialog = async (row) => {
  resetForm()
  isEdit.value = true
  dialogTitle.value = `编辑：${row.name}`
  form.id = row.id
  form.interface_id = Number(row.interface_id)
  form.name = row.name || ''
  
  // 直接赋值，JsonEditor组件会自动处理数据类型转换
  form.stepsText = row.steps || []
  form.expectedText = row.expected || []
  
  // 同时初始化解析后的对象
  parsedSteps.value = Array.isArray(row.steps) ? row.steps : []
  parsedExpected.value = Array.isArray(row.expected) ? row.expected : []
  
  form.status = row.status || 'draft'
  dialogVisible.value = true
}

const handleSubmit = async () => {
  // 验证数据有效性
  if (!Array.isArray(parsedSteps.value)) {
    ElMessage.error('测试步骤需为合法的 JSON 数组')
    return
  }
  
  if (!Array.isArray(parsedExpected.value)) {
    ElMessage.error('预期结果需为合法的 JSON 数组')
    return
  }

  if (!form.name?.trim()) {
    ElMessage.error('用例名称不能为空')
    return
  }
  if (!form.interface_id && !isEdit.value) {
    ElMessage.error('请选择关联接口')
    return
  }

  let projectId = route.params.projectId || projectStore.currentProject?.id
  if (!projectId) {
    const projectStr = localStorage.getItem('currentProject')
    if (projectStr) {
      projectId = JSON.parse(projectStr)?.id
    }
  }
  if (!projectId) {
    ElMessage.error('项目ID不存在')
    return
  }

  // 直接使用解析后的对象，无需重复解析
  const payload = {
    name: form.name.trim(), 
    steps: parsedSteps.value, 
    expected: parsedExpected.value, 
    status: form.status
  }
  submitting.value = true
  try {
    if (isEdit.value) {
      await updateBasicCase(projectId, form.id, payload)
      ElMessage.success('测试点更新成功')
    } else {
      await createBasicCase(projectId, form.interface_id, payload)
      ElMessage.success('测试点创建成功')
    }
    dialogVisible.value = false
    await loadCases()
  } catch (e) {
    console.error('提交失败', e)
    ElMessage.error(e?.response?.data?.detail || '提交失败')
  } finally {
    submitting.value = false
  }
}
// 查看测试点
const handleViewCase = (row) => {
  viewData.value = {
    id: row.id,
    name: row.name,
    interface_name: row.interface_name,
    status: row.status,
    steps: row.steps || [],
    expected: row.expected || [],
    created_at: row.created_at,
    updated_at: row.updated_at
  }
  viewDialogVisible.value = true
}

// 从查看对话框跳转到编辑
const handleEditFromView = () => {
  viewDialogVisible.value = false
  // 使用viewData中的数据来填充编辑表单
  const row = viewData.value
  openEditDialog(row)
}

// 跳转到基于测试点生成可执行用例页面
const goToGenerate = (row) => {
  let projectId = route.params.projectId || projectStore.currentProject?.id
  if (!projectId) {
    const projectStr = localStorage.getItem('currentProject')
    if (projectStr) projectId = JSON.parse(projectStr)?.id
  }
  if (!projectId) {
    ElMessage.error('项目ID不存在')
    return
  }
  router.push({
    name: 'ApiExecutableCaseGenerate',
    params: {projectId, baseCaseId: row.id},
    query: {interfaceId: Number(row.interface_id), baseCaseName: row.name}
  })
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
        `确定要删除用例"${row.name}"吗？`,
        '确认删除',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }
    )

    let projectId = route.params.projectId || projectStore.currentProject?.id
    if (!projectId) {
      const projectStr = localStorage.getItem('currentProject')
      if (projectStr) {
        projectId = JSON.parse(projectStr)?.id
      }
    }
    if (!projectId) {
      ElMessage.error('项目ID不存在')
      return
    }

    await deleteBasicCase(projectId, row.id)
    ElMessage.success('用例删除成功')
    await loadCases()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除用例失败:', error)
      ElMessage.error(error.response?.data?.detail || '删除用例失败')
    }
  }
}

const clearFilter = (key) => {
  if (key === 'interfaceId') filters.interfaceId = null
  else if (key === 'method') filters.method = ''
  else if (key === 'status') filters.status = ''
  else if (key === 'keyword') filters.keyword = ''
  handleFilterChange()
}

const clearAllFilters = () => {
  filters.interfaceId = null
  filters.method = ''
  filters.status = ''
  filters.keyword = ''
  handleFilterChange()
}

const handleFilterChange = () => {
  pagination.page = 1
  loadCases()
}

const handleSearch = () => {
  // 搜索时不需要重新加载数据，因为是前端过滤
  // 但为了保持一致性，可以重置分页
  pagination.page = 1
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

const handleRefresh = () => {
  loadCases()
}

const handleRowClick = (row) => {
  handleViewCase(row)
}

// 数据加载
const loadCases = async () => {
  let projectId = route.params.projectId || projectStore.currentProject?.id
  if (!projectId) {
    try {
      const projectStr = localStorage.getItem('currentProject')
      if (projectStr) {
        projectId = JSON.parse(projectStr)?.id
      }
    } catch (e) {
      console.error('解析localStorage项目信息失败:', e)
    }
  }
  if (!projectId) projectId = 1

  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      // 后端支持 interface_id 过滤
      interface_id: filters.interfaceId || undefined
    }
    // 若从生成页带有接口ID，则按接口筛选
    if (route.query.interfaceId && !filters.interfaceId) {
      params.interface_id = route.query.interfaceId
      filters.interfaceId = Number(route.query.interfaceId)
    }

    const response = await getBasicCasesList(projectId, params)
    if (response && response.data) {
      cases.value = response.data.base_cases || []
      pagination.total = response.data.total || 0
      pagination.totalPages = response.data.total_pages || 0
    } else {
      cases.value = response.base_cases || []
      pagination.total = response.total || 0
      pagination.totalPages = response.total_pages || 0
    }
  } catch (error) {
    console.error('加载测试点列表失败:', error)
    ElMessage.error('加载测试点列表失败，请稍后重试')
    cases.value = []
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadInterfaces()
  loadCases()
})

// 过滤相关的计算属性和方法
const hasActiveFilters = computed(() => {
  if (!filters) return false
  return !!(
      filters.interfaceId ||
      filters.method ||
      filters.status ||
      (filters.keyword && filters.keyword.trim())
  )
})

const selectedInterfaceLabel = computed(() => {
  if (!interfaceOptions.value || !Array.isArray(interfaceOptions.value)) {
    return '-'
  }
  const opt = interfaceOptions.value.find(o => o.value === filters.interfaceId)
  return opt ? opt.label : '-'
})

const getStatusLabel = (status) => {
  const statusMap = {
    'draft': '草稿',
    'published': '已发布',
    'archived': '已归档'
  }
  return statusMap[status] || status
}

// 搜索输入节流/防抖
let searchTimer = null
const handleSearchDebounced = () => {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    handleSearch()
  }, 300)
}
</script>

<style scoped>
.base-case-page {
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

.case-title {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.title-text {
  font-weight: 500;
  color: #1f2937;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 400px;
}

.table-footer {
  display: flex;
  justify-content: flex-end;
  padding: 12px 0;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .base-case-page {
    padding: 16px;
  }

  .header-content {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }

  .filter-content {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }

  .filter-left .el-select,
  .filter-right .el-input {
    width: 100% !important;
  }
}

/* 测试点编辑弹窗样式 */
.base-case-dialog {

.el-dialog__body {
  padding: 20px 24px;
}

}

.base-case-form {

.el-form-item {
  margin-bottom: 24px;
}

.el-form-item__label {
  font-weight: 500;
  color: #374151;
}

}

.json-editor-form-item {

.el-form-item__content {
  line-height: 1.2;
}

}

.json-editor-wrapper {
  width: 100%;
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  overflow: hidden;
  background: #fff;

&
:hover {
  border-color: #c0c4cc;
}

&
:focus-within {
  border-color: #409eff;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.1);
}

}

.json-editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #f8f9fa;
  border-bottom: 1px solid #e9ecef;

.editor-label {
  font-size: 13px;
  color: #6c757d;
  font-weight: 500;
}

.editor-actions {
  display: flex;
  gap: 6px;

.el-button {
  padding: 4px 8px;
  font-size: 12px;
  height: auto;
  min-height: auto;
}

}
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 16px;
  border-top: 1px solid #e5e7eb;
}

/* 查看对话框样式 */
.view-case-dialog {
  .view-case-content {
    padding: 0;
  }

  .view-section {
    margin-top: 24px;

    .section-title {
      font-size: 16px;
      font-weight: 600;
      color: #374151;
      margin: 0 0 12px 0;
      padding-bottom: 8px;
      border-bottom: 2px solid #e5e7eb;
    }

    .json-display {
      border: 1px solid #e5e7eb;
      border-radius: 6px;
      overflow: hidden;
      background: #f8f9fa;
    }
  }

  .el-descriptions {
    margin-bottom: 0;
  }

  .el-descriptions__label {
    font-weight: 600;
    color: #374151;
  }

  .el-descriptions__content {
    color: #6b7280;
  }
}
</style>