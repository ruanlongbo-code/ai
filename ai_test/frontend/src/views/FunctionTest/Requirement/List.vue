<template>
  <div class="requirements-list-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <h1>需求管理</h1>
          <p class="subtitle">管理项目功能需求，支持需求的全生命周期管理</p>
        </div>
        <div class="action-section">
          <el-button type="primary" @click="handleCreateRequirement">
            <el-icon><Plus /></el-icon>
            新建需求
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
              v-model="filters.moduleId"
              placeholder="选择模块"
              clearable
              @change="handleFilterChange"
              style="width: 200px; margin-right: 16px;"
            >
              <el-option
                v-for="module in modules"
                :key="module.id"
                :label="module.name"
                :value="module.id"
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
                v-for="(label, value) in REQUIREMENT_STATUS_LABELS"
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
                v-for="(label, value) in REQUIREMENT_PRIORITY_LABELS"
                :key="value"
                :label="label"
                :value="parseInt(value)"
              />
            </el-select>
          </div>
          
          <div class="filter-right">
            <el-input
              v-model="filters.keyword"
              placeholder="搜索需求标题或描述"
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
            v-if="filters.moduleId"
            closable
            @close="clearFilter('moduleId')"
            style="margin-right: 8px;"
          >
            模块：{{ getModuleName(filters.moduleId) }}
          </el-tag>
          <el-tag
            v-if="filters.status"
            closable
            @close="clearFilter('status')"
            style="margin-right: 8px;"
          >
            状态：{{ REQUIREMENT_STATUS_LABELS[filters.status] }}
          </el-tag>
          <el-tag
            v-if="filters.priority"
            closable
            @close="clearFilter('priority')"
            style="margin-right: 8px;"
          >
            优先级：{{ REQUIREMENT_PRIORITY_LABELS[filters.priority] }}
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

    <!-- 需求表格 -->
    <div class="requirements-table">
      <el-card>
        <div v-loading="loading" class="table-content">
          <!-- 不分组显示，直接使用表格 -->
          <el-table
            v-if="filteredRequirements.length > 0"
            :data="filteredRequirements"
            stripe
            @row-click="handleRowClick"
            class="requirements-table-inner"
          >
            <el-table-column prop="title" label="需求标题" min-width="220">
              <template #default="{ row }">
                <div class="requirement-title">
                  <span class="title-text">{{ row.title }}</span>
                </div>
              </template>
            </el-table-column>
          
            <el-table-column prop="module_id" label="所属模块" width="160">
              <template #default="{ row }">
                {{ row.module_name || getModuleName(row.module_id) }}
              </template>
            </el-table-column>
            
            <el-table-column prop="priority" label="优先级" width="110">
              <template #default="{ row }">
                <el-tag
                  effect="light"
                  size="small"
                >
                  {{ REQUIREMENT_PRIORITY_LABELS[row.priority] }}
                </el-tag>
              </template>
            </el-table-column>
            
            <el-table-column prop="status" label="状态" width="120">
              <template #default="{ row }">
                <el-tag :type="getStatusTagType(row.status)" effect="light" size="small">
                  {{ REQUIREMENT_STATUS_LABELS[row.status] }}
                </el-tag>
              </template>
            </el-table-column>
          
            <el-table-column prop="creator_id" label="创建人" width="110">
              <template #default="{ row }">
                用户{{ row.creator_id }}
              </template>
            </el-table-column>
            
            <el-table-column prop="created_at" label="创建时间" width="170">
              <template #default="{ row }">
                {{ formatDate(row.created_at) }}
              </template>
            </el-table-column>
          
            <el-table-column label="操作" width="150" fixed="right">
              <template #default="{ row }">
                <el-button size="small" type="primary" @click.stop="handleViewDetail(row)">查看</el-button>
                <el-button size="small" type="danger" @click.stop="handleDelete(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
          
          <!-- 空状态 -->
          <div v-else class="empty-state">
            <el-empty :description="hasActiveFilters ? '没有找到符合条件的需求' : '暂无需求数据'">
              <el-button v-if="!hasActiveFilters" type="primary" @click="handleCreateRequirement">创建第一个需求</el-button>
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

    <!-- 需求审核弹框 -->
    <el-dialog
      v-model="reviewDialog.visible"
      title="需求审核"
      width="500px"
      :close-on-click-modal="false"
    >
      <div v-if="reviewDialog.requirement" class="review-content">
        <div class="requirement-info">
          <h3 style="margin-bottom: 16px; color: #303133;">{{ reviewDialog.requirement.title }}</h3>
          <div class="requirement-meta" style="margin-bottom: 24px;">
            <span style="color: #606266; margin-right: 8px;">当前状态：</span>
            <el-tag :type="getStatusTagType(reviewDialog.requirement.status)" effect="light" size="small">
              {{ REQUIREMENT_STATUS_LABELS[reviewDialog.requirement.status] }}
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
              <el-option label="草稿" value="draft" />
              <el-option label="已确认" value="reviewing" />
              <el-option label="待完善" value="approved" />
              <el-option label="完成" value="rejected" />
              <el-option label="废弃" value="changed" />
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
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh, Search } from '@element-plus/icons-vue'
import {
  getRequirementsList,
  deleteRequirement,
  generateFunctionalCases,
  reviewRequirement,
  REQUIREMENT_STATUS_LABELS,
  REQUIREMENT_PRIORITY_LABELS,
  REQUIREMENT_PRIORITY_COLORS,
  REQUIREMENT_STATUS_COLORS
} from '@/api/functional_test'
import { getProjectModules } from '@/api/project'
import { useProjectStore } from '@/stores'

const router = useRouter()
const route = useRoute()
const projectStore = useProjectStore()

// 响应式数据
const loading = ref(false)
const requirements = ref([])
const modules = ref([])
const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

// 筛选条件
const filters = reactive({
  moduleId: null,
  status: null,
  priority: null,
  keyword: ''
})

// 审核弹框数据
const reviewDialog = reactive({
  visible: false,
  loading: false,
  requirement: null,
  form: {
    status: ''
  }
})

// 搜索防抖
let searchTimer = null

// 计算属性
const projectId = computed(() => {
  const project = projectStore.currentProject
  if (!project || !project.id) {
    ElMessage.error('请先选择项目')
    router.push('/project')
    return null
  }
  return project.id
})

const hasActiveFilters = computed(() => {
  return filters.moduleId || filters.status || filters.priority || filters.keyword
})

const filteredRequirements = computed(() => {
  let list = requirements.value
  if (filters.keyword) {
    const keyword = filters.keyword.toLowerCase()
    list = list.filter(req => 
      req.title.toLowerCase().includes(keyword) || 
      (req.description && req.description.toLowerCase().includes(keyword))
    )
  }
  return list
})

const groupedRequirements = computed(() => {
  let filteredRequirements = requirements.value

  // 应用筛选条件
  if (filters.moduleId) {
    filteredRequirements = filteredRequirements.filter(req => req.module_id === filters.moduleId)
  }
  if (filters.status) {
    filteredRequirements = filteredRequirements.filter(req => req.status === filters.status)
  }
  if (filters.priority) {
    filteredRequirements = filteredRequirements.filter(req => req.priority === filters.priority)
  }
  if (filters.keyword) {
    const keyword = filters.keyword.toLowerCase()
    filteredRequirements = filteredRequirements.filter(req => 
      req.title.toLowerCase().includes(keyword) || 
      (req.description && req.description.toLowerCase().includes(keyword))
    )
  }

  // 按模块分组
  const groups = {}
  filteredRequirements.forEach(req => {
    const moduleId = req.module_id || 0
    if (!groups[moduleId]) {
      groups[moduleId] = {
        moduleId,
        moduleName: getModuleName(moduleId),
        requirements: []
      }
    }
    groups[moduleId].requirements.push(req)
  })

  return Object.values(groups).sort((a, b) => a.moduleName.localeCompare(b.moduleName))
})

// 方法
const getModuleName = (moduleId) => {
  if (!moduleId) return '未分配模块'
  // 优先使用需求数据中的 module_name
  const requirement = requirements.value.find(req => req.module_id === moduleId)
  if (requirement && requirement.module_name) {
    return requirement.module_name
  }
  // 备用方案：从模块列表中查找
  const module = modules.value.find(m => m.id === moduleId)
  return module ? module.name : `模块 ${moduleId}`
}

const getStatusTagType = (status) => {
  const typeMap = {
    draft: '',
    reviewing: 'warning',
    approved: 'success',
    rejected: 'danger',
    archived: 'info'
  }
  return typeMap[status] || ''
}

const formatDate = (dateString) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleString('zh-CN')
}

const loadModules = async () => {
  if (!projectId.value) {
    return
  }
  
  try {
     const response = await getProjectModules(projectId.value)
     modules.value = (response.data && response.data.datas) ? response.data.datas : []
   } catch (error) {
     console.error('加载模块列表失败:', error)
     ElMessage.error('加载模块列表失败')
   }
}

const loadRequirements = async () => {
  if (!projectId.value) {
    return
  }
  
  loading.value = true
  try {
    const response = await getRequirementsList(projectId.value, {
      module_id: filters.moduleId || undefined,
      status: filters.status || undefined,
      priority: filters.priority || undefined,
      page: pagination.page,
      page_size: pagination.pageSize
    })
    
    if (response.data) {
      requirements.value = response.data.requirements || []
      pagination.total = response.data.total || 0
      pagination.page = response.data.page || pagination.page
      pagination.pageSize = response.data.page_size || pagination.pageSize
    } else {
      requirements.value = []
      pagination.total = 0
    }
  } catch (error) {
    console.error('加载需求列表失败:', error)
    ElMessage.error('加载需求列表失败')
    requirements.value = []
    pagination.total = 0
  } finally {
    loading.value = false
  }
}

const handleRefresh = async () => {
  await loadRequirements()
  ElMessage.success('刷新成功')
}

const handleCreateRequirement = () => {
  router.push(`/function-test/requirement/create`)
}

const handleRowClick = (row) => {
  handleViewDetail(row)
}

const handleViewDetail = (row) => {
  router.push(`/function-test/requirement/${row.id}`)
}

const handleEdit = (row) => {
  router.push(`/function-test/requirement/${row.id}/edit`)
}

const handleGenerateCases = async (row) => {
  try {
    // 直接跳转到用例生成页面，不需要确认
    router.push(`/function-test/case/generate/${row.id}`)
  } catch (error) {
    console.error('跳转用例生成页面失败:', error)
  }
}

// 处理审核需求
const handleReview = (row) => {
  reviewDialog.requirement = row
  reviewDialog.form.status = row.status
  reviewDialog.visible = true
}

// 提交审核
const handleSubmitReview = async () => {
  if (!reviewDialog.form.status) {
    ElMessage.warning('请选择审核状态')
    return
  }
  
  try {
    reviewDialog.loading = true
    
    // 调用审核API
    await reviewRequirement(projectId.value, reviewDialog.requirement.id, {
      status: reviewDialog.form.status
    })
    
    ElMessage.success('审核提交成功')
    reviewDialog.visible = false
    
    // 重新加载需求列表
    await loadRequirements()
  } catch (error) {
    console.error('审核提交失败:', error)
    ElMessage.error('审核提交失败')
  } finally {
    reviewDialog.loading = false
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除需求"${row.title}"吗？此操作不可恢复。`,
      '删除需求',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    loading.value = true
    await deleteRequirement(projectId.value, row.id)
    ElMessage.success('需求删除成功')
    await loadRequirements()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除需求失败:', error)
      ElMessage.error('删除需求失败')
    }
  } finally {
    loading.value = false
  }
}

const handleFilterChange = () => {
  pagination.page = 1
  loadRequirements()
}

const handlePageChange = (newPage) => {
  pagination.page = newPage
  loadRequirements()
}

const handlePageSizeChange = (newSize) => {
  pagination.pageSize = newSize
  pagination.page = 1
  loadRequirements()
}

const handleSearch = () => {
  // 搜索防抖
  if (searchTimer) {
    clearTimeout(searchTimer)
  }
  searchTimer = setTimeout(() => {
    // 搜索逻辑在计算属性中处理
  }, 300)
}

const clearFilter = (filterKey) => {
  filters[filterKey] = filterKey === 'keyword' ? '' : null
  if (['moduleId', 'status', 'priority'].includes(filterKey)) {
    pagination.page = 1
    loadRequirements()
  }
}

const clearAllFilters = () => {
  filters.moduleId = null
  filters.status = null
  filters.priority = null
  filters.keyword = ''
  pagination.page = 1
  loadRequirements()
}

// 生命周期
onMounted(async () => {
  await loadModules()
  await loadRequirements()
})
</script>

<style scoped>
.requirements-list-page {
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

.requirements-table {
  background: white;
  border-radius: 8px;
  overflow: hidden;
}

.table-content {
  min-height: 400px;
}

.module-group {
  margin-bottom: 32px;
}

.module-group:last-child {
  margin-bottom: 0;
}

.module-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 0;
  border-bottom: 2px solid #8b5cf6;
  margin-bottom: 16px;
}

.module-header h3 {
  color: #1f2937;
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.requirement-count {
  color: #6b7280;
  font-size: 14px;
}

.requirements-table-inner {
  margin-bottom: 16px;
}

.requirement-title {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.title-text {
  font-weight: 500;
  color: #1f2937;
}

.doc-no {
  font-size: 12px;
  color: #6b7280;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 400px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .requirements-list-page {
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
.table-footer {
  display: flex;
  justify-content: flex-end;
  padding: 12px 0;
}

/* 修复 fixed 列背景透明导致内容重叠 */
:deep(td.el-table-fixed-column--right) {
  background-color: var(--el-table-bg-color, #fff) !important;
  background: var(--el-table-bg-color, #fff) !important;
}

:deep(.el-table--striped .el-table__body tr.el-table__row--striped td.el-table-fixed-column--right) {
  background-color: var(--el-table-row-striped-bg-color, #fafafa) !important;
  background: var(--el-table-row-striped-bg-color, #fafafa) !important;
}

:deep(.el-table__body tr.hover-row td.el-table-fixed-column--right),
:deep(.el-table__body tr:hover td.el-table-fixed-column--right) {
  background-color: var(--el-table-row-hover-bg-color, #f5f7fa) !important;
  background: var(--el-table-row-hover-bg-color, #f5f7fa) !important;
}
</style>
