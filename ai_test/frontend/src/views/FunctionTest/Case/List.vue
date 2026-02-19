<template>
  <div class="functional-cases-list-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <h1>功能用例管理</h1>
          <p class="subtitle">管理项目功能用例，支持用例的全生命周期管理</p>
        </div>
        <div class="action-section">
          <el-button type="primary" @click="handleCreateCase">
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
              v-model="filters.requirementId"
              placeholder="选择需求"
              clearable
              @change="handleFilterChange"
              style="width: 200px; margin-right: 16px;"
            >
              <el-option
                v-for="req in requirements"
                :key="req.id"
                :label="req.title"
                :value="req.id"
              />
            </el-select>
            
            <el-select
              v-model="filters.status"
              placeholder="选择状态"
              clearable
              @change="handleFilterChange"
              style="width: 150px; margin-right: 16px;"
            >
              <el-option
                v-for="(label, value) in CASE_STATUS_LABELS"
                :key="value"
                :label="label"
                :value="value"
              />
            </el-select>
            
            <el-select
              v-model="filters.priority"
              placeholder="选择优先级"
              clearable
              @change="handleFilterChange"
              style="width: 150px; margin-right: 16px;"
            >
              <el-option
                v-for="(label, value) in CASE_PRIORITY_LABELS"
                :key="value"
                :label="label"
                :value="parseInt(value)"
              />
            </el-select>
          </div>
          
          <div class="filter-right">
            <el-input
              v-model="filters.keyword"
              placeholder="搜索用例名称或编号"
              @input="handleSearch"
              style="width: 300px;"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </div>
        </div>
        
        <!-- 筛选标签 -->
        <div v-if="hasActiveFilters" class="filter-tags">
          <span class="filter-label">当前筛选：</span>
          <el-tag
            v-if="filters.requirementId"
            closable
            @close="clearFilter('requirementId')"
            style="margin-right: 8px;"
          >
            需求：{{ getRequirementName(filters.requirementId) }}
          </el-tag>
          <el-tag
            v-if="filters.status"
            closable
            @close="clearFilter('status')"
            style="margin-right: 8px;"
          >
            状态：{{ CASE_STATUS_LABELS[filters.status] }}
          </el-tag>
          <el-tag
            v-if="filters.priority"
            closable
            @close="clearFilter('priority')"
            style="margin-right: 8px;"
          >
            优先级：{{ CASE_PRIORITY_LABELS[filters.priority] }}
          </el-tag>
          <el-tag
            v-if="filters.keyword"
            closable
            @close="clearFilter('keyword')"
            style="margin-right: 8px;"
          >
            关键词：{{ filters.keyword }}
          </el-tag>
          <el-button link type="primary" @click="clearAllFilters">
            清空筛选
          </el-button>
        </div>
      </el-card>
    </div>

    <!-- 用例表格 -->
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
            <el-table-column prop="case_no" label="用例编号" width="120">
              <template #default="{ row }">
                <span>{{ row.case_no || '-' }}</span>
              </template>
            </el-table-column>
            
            <el-table-column prop="case_name" label="用例名称" min-width="220">
              <template #default="{ row }">
                <div class="case-title">
                  <span class="title-text">{{ row.case_name }}</span>
                </div>
              </template>
            </el-table-column>
          
            <el-table-column prop="requirement_id" label="关联需求" width="160">
              <template #default="{ row }">
                {{ row.requirement_title || '-' }}
              </template>
            </el-table-column>
            
            <el-table-column prop="priority" label="优先级" width="110">
              <template #default="{ row }">
                <el-tag
                  effect="light"
                  size="small"
                >
                  {{ CASE_PRIORITY_LABELS[row.priority] }}
                </el-tag>
              </template>
            </el-table-column>
            
            <el-table-column prop="status" label="状态" width="120">
              <template #default="{ row }">
                <el-tag :type="getStatusTagType(row.status)" effect="light" size="small">
                  {{ CASE_STATUS_LABELS[row.status] }}
                </el-tag>
              </template>
            </el-table-column>
          
            <el-table-column prop="creator_id" label="创建人" width="110">
              <template #default="{ row }">
                {{ row.creator_name || '未知' }}
              </template>
            </el-table-column>
            
            <el-table-column prop="created_at" label="创建时间" width="180">
              <template #default="{ row }">
                {{ formatDate(row.created_at) }}
              </template>
            </el-table-column>
          
            <el-table-column label="操作" width="280" fixed="right">
              <template #default="{ row }">
                <el-button size="small" type="primary" @click.stop="handleViewCase(row)">查看</el-button>
                <el-button 
                  v-if="row.status === 'design'" 
                  size="small" 
                  type="warning" 
                  @click.stop="handleReview(row)"
                >
                  审核
                </el-button>
                <el-button size="small" type="success" @click.stop="handleExecute(row)">执行</el-button>
                <el-button size="small" type="danger" @click.stop="handleDelete(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
          
          <!-- 空状态 -->
          <div v-else class="empty-state">
            <el-empty :description="hasActiveFilters ? '没有找到符合条件的用例' : '暂无用例数据'">
              <el-button v-if="!hasActiveFilters" type="primary" @click="handleCreateCase">创建第一个用例</el-button>
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

    <!-- 用例审核弹框 -->
    <el-dialog
      v-model="reviewDialog.visible"
      title="用例审核"
      width="500px"
      :close-on-click-modal="false"
    >
      <div v-if="reviewDialog.case" class="review-content">
        <div class="case-info">
          <h3 style="margin-bottom: 16px; color: #303133;">{{ reviewDialog.case.case_name }}</h3>
          <div class="case-meta" style="margin-bottom: 24px;">
            <span style="color: #606266; margin-right: 8px;">当前状态：</span>
            <el-tag :type="getStatusTagType(reviewDialog.case.status)" effect="light" size="small">
              {{ CASE_STATUS_LABELS[reviewDialog.case.status] }}
            </el-tag>
          </div>
        </div>
        
        <el-form :model="reviewDialog.form" label-width="80px" class="review-form">
          <el-form-item label="审核状态" required>
            <el-select 
              v-model="reviewDialog.form.status" 
              placeholder="请选择审核状态"
              style="width: 100%;"
            >
              <el-option label="待审核" value="design" />
              <el-option label="审核通过" value="pass" />
              <el-option label="待执行" value="wait" />
              <el-option label="执行通过" value="smoke" />
              <el-option label="执行失败" value="regression" />
              <el-option label="已废弃" value="obsolete" />
            </el-select>
          </el-form-item>
        </el-form>
      </div>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="reviewDialog.visible = false">取消</el-button>
          <el-button type="primary" @click="handleSubmitReview" :loading="reviewDialog.loading">
            提交审核
          </el-button>
        </span>
      </template>
    </el-dialog>
    <!-- 用例详情弹框 -->
    <FunctionalCaseDetailModal
      v-model="showCaseDetailModal"
      :case-id="selectedCaseId"
      :project-id="projectStore.currentProject?.id"
    />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh, Search, View } from '@element-plus/icons-vue'
import { getFunctionalCasesList, getFunctionalCaseDetail, reviewFunctionalCase, deleteFunctionalCase, CASE_STATUS_LABELS, CASE_PRIORITY_LABELS } from '@/api/functional_test'
import { getRequirementsList } from '@/api/functional_test'
import { useProjectStore } from '@/stores'
import FunctionalCaseDetailModal from './components/FunctionalCaseDetailModal.vue'

const router = useRouter()
const route = useRoute()
const projectStore = useProjectStore()

// 响应式数据
const loading = ref(false)
const cases = ref([])
const requirements = ref([])
const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0,
  totalPages: 0
})

// 筛选条件
const filters = reactive({
  requirementId: null,
  status: '',
  priority: null,
  keyword: ''
})

// 审核弹框
const reviewDialog = reactive({
  visible: false,
  case: null,
  form: {
    status: ''
  },
  loading: false
})

// 注意：CASE_STATUS_LABELS 和 CASE_PRIORITY_LABELS 已从 API 文件导入

// 计算属性
const hasActiveFilters = computed(() => {
  return filters.requirementId || filters.status || filters.priority || filters.keyword
})

const filteredCases = computed(() => {
  console.log('计算filteredCases, cases.value:', cases.value) // 调试日志
  console.log('当前筛选条件:', filters) // 调试日志
  
  let result = [...cases.value]
  
  // 关键词搜索 - 在前端进行筛选
  if (filters.keyword) {
    const keyword = filters.keyword.toLowerCase()
    result = result.filter(item => 
      (item.case_name && item.case_name.toLowerCase().includes(keyword)) ||
      (item.case_no && item.case_no.toLowerCase().includes(keyword))
    )
  }
  
  // 需求筛选 - 在前端进行筛选
  if (filters.requirementId) {
    result = result.filter(item => item.requirement_id === filters.requirementId)
  }
  
  // 状态筛选 - 在前端进行筛选
  if (filters.status) {
    result = result.filter(item => item.status === filters.status)
  }
  
  // 优先级筛选 - 在前端进行筛选
  if (filters.priority) {
    result = result.filter(item => item.priority === filters.priority)
  }
  
  console.log('筛选后的结果:', result) // 调试日志
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
// 用例详情弹框相关
const showCaseDetailModal = ref(false)
const selectedCaseId = ref(null)

// 查看用例详情
const handleViewCase = (row) => {
  selectedCaseId.value = row.id
  showCaseDetailModal.value = true
}

// 编辑用例
const handleEditCase = (row) => {
  // TODO: 实现编辑用例功能
  ElMessage.info('编辑功能待实现')
}

// 删除用例
const handleDeleteCase = (row) => {
  ElMessageBox.confirm(
    `确定要删除用例 "${row.case_name}" 吗？`,
    '确认删除',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(() => {
    // TODO: 实现删除用例功能
    ElMessage.success('删除成功')
  }).catch(() => {
    ElMessage.info('已取消删除')
  })
}

const getStatusTagType = (status) => {
  const statusTypes = {
    'design': 'info',      // 待审核
    'pass': 'success',     // 审核通过
    'wait': 'warning',     // 待执行
    'smoke': 'success',    // 执行通过
    'regression': 'danger', // 执行失败
    'obsolete': 'info'     // 已废弃
  }
  return statusTypes[status] || 'info'
}

const getPriorityTagType = (priority) => {
  const priorityTypes = {
    1: 'danger',  // P0
    2: 'warning', // P1
    3: 'primary', // P2
    4: 'info'     // P3
  }
  return priorityTypes[priority] || 'info'
}

const clearFilter = (filterKey) => {
  filters[filterKey] = filterKey === 'priority' || filterKey === 'requirementId' ? null : ''
  handleFilterChange()
}

const clearAllFilters = () => {
  filters.requirementId = null
  filters.status = ''
  filters.priority = null
  filters.keyword = ''
  handleFilterChange()
}

const handleFilterChange = () => {
  pagination.page = 1
  loadCases()
}

const handleSearch = () => {
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
  await Promise.all([loadCases(), loadRequirements()])
  ElMessage.success('刷新成功')
}

const handleRowClick = (row) => {
  handleViewDetail(row)
}

// 操作方法（暂时只显示消息）
const handleCreateCase = () => {
  ElMessage.info('新建用例功能开发中...')
}

const handleViewDetail = (row) => {
  ElMessage.info(`查看用例详情：${row.case_name}`)
}

const handleEdit = (row) => {
  ElMessage.info(`编辑用例：${row.case_name}`)
}

const handleReview = (row) => {
  reviewDialog.case = row
  reviewDialog.form.status = row.status
  reviewDialog.visible = true
}

const handleExecute = (row) => {
  selectedCaseId.value = row.id
  showCaseDetailModal.value = true
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除用例"${row.case_name}"吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    // 执行删除操作
    const projectId = route.params.projectId || projectStore.currentProject?.id
    if (!projectId) {
      ElMessage.error('项目ID不存在')
      return
    }

    await deleteFunctionalCase(projectId, row.id)
    ElMessage.success('用例删除成功')
    
    // 刷新列表
    await loadCases()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除用例失败:', error)
      ElMessage.error(error.response?.data?.detail || '删除用例失败')
    }
  }
}

const handleSubmitReview = async () => {
  if (!reviewDialog.form.status) {
    ElMessage.warning('请选择审核状态')
    return
  }

  reviewDialog.loading = true
  
  try {
    const projectId = route.params.projectId || projectStore.currentProject?.id
    if (!projectId) {
      ElMessage.error('项目ID不存在')
      return
    }

    await reviewFunctionalCase(projectId, reviewDialog.case.id, {
      status: reviewDialog.form.status
    })

    ElMessage.success('审核成功')
    reviewDialog.visible = false
    
    // 刷新列表
    await loadCases()
  } catch (error) {
    console.error('审核失败:', error)
    ElMessage.error(error.response?.data?.detail || '审核失败')
  } finally {
    reviewDialog.loading = false
  }
}

// 数据加载
const loadCases = async () => {
  console.log('loadCases 方法被调用')
  console.log('项目store状态:', projectStore.currentProject)
  console.log('路由参数:', route.params)
  
  // 获取项目ID的多种方式
  let projectId = route.params.projectId || projectStore.currentProject?.id
  
  // 如果store中没有项目ID，尝试从localStorage获取
  if (!projectId) {
    try {
      const projectStr = localStorage.getItem('currentProject')
      if (projectStr) {
        const project = JSON.parse(projectStr)
        projectId = project.id
        console.log('从localStorage获取项目ID:', projectId)
      }
    } catch (error) {
      console.error('解析localStorage项目信息失败:', error)
    }
  }
  
  // 如果还是没有项目ID，使用默认值1
  if (!projectId) {
    projectId = 1
    console.log('使用默认项目ID:', projectId)
  } else {
    console.log('使用项目ID:', projectId)
  }

  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize
    }
    
    // 添加筛选参数
    if (filters.requirementId) {
      params.requirement_id = filters.requirementId
    }
    
    // 添加关键词参数
    if (filters.keyword) {
      params.keyword = filters.keyword
    }

    console.log('API调用参数:', params)
    console.log('使用项目ID调用API:', projectId)
    console.log('API请求URL:', `/functional_test/${projectId}/functional_cases`)
    
    const response = await getFunctionalCasesList(projectId, params)
    console.log('API响应:', response)
    
    // 检查响应数据结构
    if (response && response.data) {
      cases.value = response.data.cases || []
      pagination.total = response.data.total || 0
      pagination.totalPages = response.data.total_pages || 0
    } else {
      cases.value = response.cases || []
      pagination.total = response.total || 0
      pagination.totalPages = response.total_pages || 0
    }
    
    console.log('用例数据已更新:', cases.value)
    console.log('用例数量:', cases.value.length)
    
  } catch (error) {
    console.error('加载用例列表失败:', error)
    console.error('错误详情:', error.response?.data || error.message)
    ElMessage.error('加载用例列表失败，请稍后重试')
    cases.value = []
  } finally {
    loading.value = false
  }
}

const loadRequirements = async () => {
  // 获取项目ID的多种方式
  let projectId = projectStore.currentProject?.id || route.params.projectId
  
  // 如果store中没有项目ID，尝试从localStorage获取
  if (!projectId) {
    try {
      const projectStr = localStorage.getItem('currentProject')
      if (projectStr) {
        const project = JSON.parse(projectStr)
        projectId = project.id
      }
    } catch (error) {
      console.error('解析localStorage项目信息失败:', error)
    }
  }
  
  // 如果还是没有项目ID，使用默认值17
  if (!projectId) {
    projectId = 17
  }
  
  if (!projectId) {
    return
  }

  try {
    const response = await getRequirementsList(projectId, { page_size: 1000 })
    
    // 直接使用后端返回的需求数组
    if (response.data && response.data.requirements && Array.isArray(response.data.requirements)) {
      requirements.value = response.data.requirements
    } else {
      requirements.value = []
    }
  } catch (error) {
    console.error('加载需求列表失败:', error)
    requirements.value = []
  }
}

// 生命周期
onMounted(() => {
  loadCases()
  loadRequirements()
})
</script>

<style scoped>
.functional-cases-list-page {
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

.filter-tags {
  display: flex;
  align-items: center;
  padding-top: 16px;
  border-top: 1px solid #e5e7eb;
}

.filter-label {
  color: #6b7280;
  font-size: 14px;
  margin-right: 12px;
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

.review-content {
  padding: 0 8px;
}

.case-info h3 {
  font-size: 16px;
  font-weight: 600;
}

.case-meta {
  display: flex;
  align-items: center;
}

.review-form {
  margin-top: 16px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .functional-cases-list-page {
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
  
  .filter-left {
    flex-direction: column;
    gap: 12px;
  }
  
  .filter-left .el-select,
  .filter-right .el-input {
    width: 100% !important;
  }
}
</style>