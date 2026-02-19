<template>
  <div class="suite-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <h1>测试套件管理</h1>
          <p class="subtitle">管理接口测试套件列表</p>
        </div>
        <div class="action-section">
          <el-button type="primary" @click="handleCreate">
            <el-icon>
              <Plus/>
            </el-icon>
            新建套件
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
                placeholder="套件类型"
                clearable
                style="width: 180px; margin-right: 16px;"
                @change="applyLocalFilters"
            >
              <el-option label="API套件" value="api"/>
              <el-option label="UI套件" value="ui"/>
            </el-select>
          </div>
          <div class="filter-right">
            <el-input
                v-model="filters.keyword"
                placeholder="搜索套件名称或描述"
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


      <el-table :data="displayedSuites" v-loading="loading" border stripe>
        <el-table-column prop="suite_name" label="套件名称" min-width="220">
          <template #default="{row}">
            <div class="name-cell">
              <el-icon class="name-icon">
                <Collection/>
              </el-icon>
              <span class="name-text">{{ row.suite_name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="类型" width="120" align="center">
          <template #default="{row}">
            <el-tag :type="row.type === 'api' ? 'success' : 'warning'">
              {{ row.type === 'api' ? 'API' : 'UI' }}
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
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{row}">
            <el-button type="primary" size="small" plain @click="editSuite(row)" icon="Edit">套件详情</el-button>
            <el-button type="danger" size="small" plain @click="deleteSuite(row)" icon="Delete">删除</el-button>
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

    <!-- 新建测试套件对话框 -->
    <el-dialog
        v-model="dialogVisible"
        title="新建测试套件"
        width="600px"
        :close-on-click-modal="false"
        :close-on-press-escape="false"
    >
      <el-form
          :model="form"
          label-width="100px"
          label-position="left"
          :disabled="submitting"
      >
        <el-form-item label="套件名称" required>
          <el-input
              v-model="form.suite_name"
              placeholder="请输入测试套件名称"
              maxlength="100"
              show-word-limit
          />
        </el-form-item>

        <el-form-item label="套件类型" required>
          <el-radio-group v-model="form.type">
            <el-radio value="api">API套件</el-radio>
            <el-radio value="ui">UI套件</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="套件描述">
          <el-input
              v-model="form.description"
              type="textarea"
              :rows="4"
              placeholder="请输入测试套件描述（可选）"
              maxlength="500"
              show-word-limit
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="dialogVisible = false" :disabled="submitting">
            取消
          </el-button>
          <el-button
              type="primary"
              @click="handleSubmit"
              :loading="submitting"
              :disabled="!form.suite_name?.trim()"
          >
            {{ submitting ? '创建中...' : '确定创建' }}
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 删除确认对话框 -->
    <el-dialog
        v-model="deleteDialogVisible"
        title="删除测试套件"
        width="500px"
        :close-on-click-modal="false"
        :close-on-press-escape="false"
    >
      <div class="delete-confirm-content">
        <el-icon class="warning-icon" color="#E6A23C" size="24">
          <Warning/>
        </el-icon>
        <div class="confirm-text">
          <p>确定要删除测试套件 <strong>"{{ deletingSuite?.suite_name }}"</strong> 吗？</p>
          <p class="warning-text">删除后将无法恢复，请谨慎操作！</p>
        </div>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="deleteDialogVisible = false" :disabled="deleting">
            取消
          </el-button>
          <el-button
              type="danger"
              @click="handleDeleteConfirm"
              :loading="deleting"
          >
            {{ deleting ? '删除中...' : '确定删除' }}
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import {ref, reactive, computed, onMounted} from 'vue'
import {useRoute, useRouter} from 'vue-router'
import {ElMessage} from 'element-plus'
import {Plus, Refresh, Search, Collection, Warning} from '@element-plus/icons-vue'
import {useProjectStore} from '@/stores'
import {getTestSuites, createTestSuite, deleteTestSuite} from '@/api/test_management'

const route = useRoute()
const router = useRouter()
const projectStore = useProjectStore()

// 加载状态与数据
const loading = ref(false)
const suites = ref([])
const displayedSuites = ref([])

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

// 新建套件对话框相关
const dialogVisible = ref(false)
const submitting = ref(false)
const form = ref({
  suite_name: '',
  description: '',
  type: 'api'
})

// 删除确认对话框相关
const deleteDialogVisible = ref(false)
const deletingSuite = ref(null)
const deleting = ref(false)

const hasActiveFilters = computed(() => !!(filters.type || filters.keyword))

const formatDate = (val) => {
  if (!val) return '-'
  const d = new Date(val)
  if (Number.isNaN(d.getTime())) return val
  const pad = (n) => (n < 10 ? `0${n}` : `${n}`)
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
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
  return 1
}

const loadSuites = async () => {
  const projectId = getProjectId()
  loading.value = true
  try {
    const res = await getTestSuites(projectId, {page: pagination.page, page_size: pagination.pageSize})
    const data = res?.data || res
    suites.value = data?.suites || []
    pagination.total = data?.total || 0
    pagination.totalPages = data?.total_pages || 0
    applyLocalFilters()
  } catch (e) {
    console.error('加载测试套件失败:', e)
    ElMessage.error('加载测试套件失败，请稍后重试')
    suites.value = []
    displayedSuites.value = []
  } finally {
    loading.value = false
  }
}

const applyLocalFilters = () => {
  let list = [...suites.value]
  if (filters.type) list = list.filter(s => s.type === filters.type)
  if (filters.keyword) {
    const kw = filters.keyword.trim().toLowerCase()
    list = list.filter(s => (s.suite_name || '').toLowerCase().includes(kw) || (s.description || '').toLowerCase().includes(kw))
  }
  displayedSuites.value = list
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
  // 重置表单
  form.value.suite_name = ''
  form.value.description = ''
  form.value.type = 'api'
  dialogVisible.value = true
}

const handleSubmit = async () => {
  // 表单验证
  if (!form.value.suite_name.trim()) {
    ElMessage.warning('请输入套件名称')
    return
  }

  const projectId = getProjectId()
  submitting.value = true

  try {
    const data = {
      suite_name: form.value.suite_name.trim(),
      description: form.value.description.trim() || '',
      type: form.value.type
    }

    await createTestSuite(projectId, data)
    ElMessage.success('测试套件创建成功')
    dialogVisible.value = false

    // 刷新列表
    await loadSuites()
  } catch (error) {
    console.error('创建测试套件失败:', error)
    ElMessage.error(error?.response?.data?.detail || '创建测试套件失败，请稍后重试')
  } finally {
    submitting.value = false
  }
}
const handleRefresh = async () => {
  await loadSuites()
  ElMessage.success('刷新成功')
}
const viewDetail = (row) => {
  ElMessage.info(`查看套件（开发中）：${row.suite_name}`)
}
const deleteSuite = (row) => {
  deletingSuite.value = row
  deleteDialogVisible.value = true
}

const handleDeleteConfirm = async () => {
  if (!deletingSuite.value) return

  const projectId = getProjectId()
  deleting.value = true

  try {
    await deleteTestSuite(projectId, deletingSuite.value.id)
    ElMessage.success('测试套件删除成功')
    deleteDialogVisible.value = false

    // 刷新列表
    await loadSuites()
  } catch (error) {
    console.error('删除测试套件失败:', error)
    ElMessage.error(error?.response?.data?.detail || '删除测试套件失败，请稍后重试')
  } finally {
    deleting.value = false
    deletingSuite.value = null
  }
}

// 编辑套件
const editSuite = (suite) => {
  router.push({
    name: 'ApiTestSuiteEdit',
    params: {
      projectId: suite.project_id,
      suiteId: suite.id
    }
  })
}

const handlePageChange = (p) => {
  pagination.page = p
  loadSuites()
}
const handleSizeChange = (ps) => {
  pagination.pageSize = ps
  pagination.page = 1
  loadSuites()
}

onMounted(() => {
  loadSuites()
})
</script>

<style scoped>
.suite-page {
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

/* 新建套件对话框样式 */
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.el-form-item.is-required .el-form-item__label::before {
  content: '*';
  color: #f56c6c;
  margin-right: 4px;
}

/* 删除确认对话框样式 */
.delete-confirm-content {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 16px 0;
}

.warning-icon {
  flex-shrink: 0;
  margin-top: 2px;
}

.confirm-text p {
  margin: 0 0 8px 0;
  line-height: 1.5;
}

.confirm-text .warning-text {
  color: #f56c6c;
  font-size: 14px;
}
</style>