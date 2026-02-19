<template>
  <div class="api-management-page">
    <!-- 页面头部（与自动化用例页面一致） -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <h1>接口管理</h1>
          <p class="subtitle">管理项目中的API接口信息</p>
        </div>
        <div class="action-section">
          <el-button type="primary" @click="handleCreateInterface">
            <el-icon>
              <Plus/>
            </el-icon>
            新增接口
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

    <!-- 筛选工具栏（与自动化用例页面一致） -->
    <div class="filter-toolbar">
      <el-card>
        <div class="filter-content">
          <div class="filter-left">
            <el-input
                v-model="searchForm.search"
                placeholder="搜索接口路径或名称"
                style="width: 300px"
                clearable
                @input="handleSearch"
            >
              <template #prefix>
                <el-icon>
                  <Search/>
                </el-icon>
              </template>
            </el-input>
          </div>
          <div class="filter-right">
            <el-select
                v-model="searchForm.method"
                placeholder="HTTP方法"
                style="width: 120px"
                clearable
                @change="handleSearch"
            >
              <el-option label="GET" value="GET"/>
              <el-option label="POST" value="POST"/>
              <el-option label="PUT" value="PUT"/>
              <el-option label="PATCH" value="PATCH"/>
              <el-option label="DELETE" value="DELETE"/>
            </el-select>
            <el-select
                v-model="searchForm.module"
                placeholder="项目模块"
                style="width: 120px; margin-left: 12px"
                clearable
                @change="handleSearch"
            >
              <el-option label="用户模块" value="user"/>
              <el-option label="订单模块" value="order"/>
              <el-option label="商品模块" value="product"/>
            </el-select>
            <el-button @click="handleReset" style="margin-left: 12px">重置</el-button>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 主内容区域 -->
    <div class="main-content">
      <el-card class="content-card">

        <!-- 操作工具栏 -->
        <div class="toolbar-section">
          <div class="toolbar-left">
            <el-button @click="handleTestedInterfaces">已测接口</el-button>
          </div>
          <div class="toolbar-right">
            <!-- 批量生成用例按钮已删除 -->
          </div>
        </div>

        <!-- 接口列表表格 -->
        <div class="table-section">
          <el-table
              v-loading="loading"
              :data="interfaceList"
              @selection-change="handleSelectionChange"
              style="width: 100%"
          >
            <el-table-column type="selection" width="55"/>
            <el-table-column label="接口名称" prop="summary" min-width="150" show-overflow-tooltip/>
             <el-table-column label="HTTP方法" prop="method" min-width="100">
              <template #default="{ row }">
                <el-tag
                    :type="getMethodTagType(row.method)"
                    size="small"
                >
                  {{ row.method }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="接口路径" prop="path" min-width="200">
              <template #default="{ row }">
                <code class="interface-path">{{ row.path }}</code>
              </template>
            </el-table-column>

            <el-table-column label="更新时间" prop="updated_at" width="160">
              <template #default="{ row }">
                {{ formatDate(row.updated_at) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="300" fixed="right">
              <template #default="{ row }">
                <div class="action-buttons">
                  <el-button
                      type="primary"
                      size="small"
                      @click="handleViewDetail(row)"
                  >
                    查看
                  </el-button>
                  <el-button
                      type="success"
                      size="small"
                      @click="handleEditInterface(row)"
                  >
                    编辑
                  </el-button>
                  <el-button
                      type="warning"
                      size="small"
                      @click="handleGenerateCase(row)"
                  >
                    生成用例
                  </el-button>
                  <el-button
                      type="danger"
                      size="small"
                      @click="handleDeleteInterface(row)"
                  >
                    删除
                  </el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <!-- 分页导航 -->
        <div class="pagination-section">
          <el-pagination
              v-model:current-page="pagination.page"
              v-model:page-size="pagination.pageSize"
              :page-sizes="[10, 20, 50, 100]"
              :total="pagination.total"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="handleSizeChange"
              @current-change="handleCurrentChange"
          />
        </div>
      </el-card>
    </div>

    <!-- 新增/编辑接口弹窗 -->
    <el-dialog
        v-model="formModalVisible"
        :title="isEditMode ? '编辑接口' : '新增接口'"
        width="70%"
        :close-on-click-modal="false"
        class="interface-form-dialog"
    >
      <InterfaceForm
          ref="interfaceFormRef"
          v-model="formData"
          :visible="formModalVisible"
          :mode="isEditMode ? 'edit' : 'create'"
          @submit="handleFormSubmit"
          @cancel="handleFormCancel"
      />
    </el-dialog>

    <!-- 接口详情弹窗 -->
    <InterfaceDetailModal
        v-model:visible="detailModalVisible"
        :interface-data="currentInterface"
    />

    <!-- 用例生成选择弹窗 -->
    <el-dialog
        v-model="generateCaseDialogVisible"
        title="选择用例生成类型"
        width="500px"
        :close-on-click-modal="false"
    >
      <div class="generate-case-options">
        <div class="option-card" @click="selectedGenerateType = 'basic'"
             :class="{ active: selectedGenerateType === 'basic' }">
          <div class="option-icon">
            <el-icon size="24">
              <Document/>
            </el-icon>
          </div>
          <div class="option-content">
            <h4>生成API测试点</h4>
            <p>基于接口文档生成API测试点，可在测试点管理页面生成测试用例</p>
          </div>
          <div class="option-radio">
            <el-radio v-model="selectedGenerateType" label="basic"/>
          </div>
        </div>

        <div class="option-card" @click="selectedGenerateType = 'complete'"
             :class="{ active: selectedGenerateType === 'complete' }">
          <div class="option-icon">
            <el-icon size="24">
              <MagicStick/>
            </el-icon>
          </div>
          <div class="option-content">
            <h4>生成API测试用例</h4>
            <p>基于接口文档和测试环境生成测试点和可执行测试用例，包含环境变量和依赖处理，所需时间比较长</p>
          </div>
          <div class="option-radio">
            <el-radio v-model="selectedGenerateType" label="complete"/>
          </div>
        </div>
      </div>


      <template #footer>
        <div class="dialog-footer">
          <el-button @click="generateCaseDialogVisible = false">取消</el-button>
          <el-button
              type="primary"
              @click="confirmGenerateCase"
              :disabled="!selectedGenerateType"
          >
            确认生成
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import {ref, reactive, onMounted, computed, watch, onActivated} from 'vue'
import {useRoute, useRouter} from 'vue-router'
import {ElMessage, ElMessageBox} from 'element-plus'
import {Search, Plus, Download, Delete, Edit, View, MagicStick, Document, Refresh} from '@element-plus/icons-vue'
import { getProjectInterfaces, deleteApiInterface, createApiInterface, updateApiInterface, getInterfaceDetail } from '@/api/apiTest'
import {getTestEnvironments} from '@/api/test_environment'
import {useProjectStore} from '@/stores'
import InterfaceForm from './components/InterfaceForm.vue'
import InterfaceDetailModal from './components/InterfaceDetailModal.vue'

const route = useRoute()
const router = useRouter()
const projectStore = useProjectStore()

const projectId = computed(() => {
  // 优先从Pinia中获取项目ID
  if (projectStore.currentProject?.id) {
    return projectStore.currentProject.id
  }
  // 如果Pinia中没有，尝试从路由参数获取
  if (route.params.projectId) {
    return route.params.projectId
  }
  // 如果都没有，提示用户选择项目
  ElMessage.error('请先选择项目')
  router.push('/project')
  return null
})

// 响应式数据
const loading = ref(false)
const saving = ref(false)
const interfaceList = ref([])
const selectedInterfaces = ref([])
const formModalVisible = ref(false)
const detailModalVisible = ref(false)
const isEditMode = ref(false)
const currentInterface = ref(null)
const interfaceFormRef = ref(null)

// 用例生成相关数据
const generateCaseDialogVisible = ref(false)
const selectedGenerateType = ref('')
const selectedTestEnvId = ref(null)
const testEnvironments = ref([])
const currentGenerateInterface = ref(null)

// 表单数据
const formData = ref({
  method: 'GET',
  path: '',
  summary: '',
  description: '',
  module: '',
  parameters: {
    path: [],
    query: [],
    header: []
  },
  requestBody: {
    content_type: 'application/json',
    body: []
  },
  responses: []
})

// 搜索表单
const searchForm = reactive({
  search: '',
  method: '',
  module: ''
})

// 分页数据
const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})


// 获取接口列表
const fetchInterfaceList = async () => {
  try {
    loading.value = true
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      search: searchForm.search,
      method: searchForm.method,
      module: searchForm.module
    }

    const response = await getProjectInterfaces(projectId.value, params)
    interfaceList.value = response.data.interfaces || []
    pagination.total = response.data.total || 0

    // 已移除顶部统计信息
  } catch (error) {
    console.error('获取接口列表失败:', error)
    ElMessage.error('获取接口列表失败')
  } finally {
    loading.value = false
  }
}


const handleRefresh = async () => {
  await fetchInterfaceList()
  ElMessage.success('刷新成功')
}

// 获取方法标签类型
const getMethodTagType = (method) => {
  const typeMap = {
    'GET': 'primary',
    'POST': 'success',
    'PUT': 'warning',
    'PATCH': 'warning',
    'DELETE': 'danger'
  }
  return typeMap[method] || 'info'
}

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN')
}

// 事件处理函数

const handleSearch = () => {
  pagination.page = 1
  fetchInterfaceList()
}

const handleReset = () => {
  searchForm.search = ''
  searchForm.method = ''
  searchForm.module = ''
  pagination.page = 1
  fetchInterfaceList()
}

const handleSelectionChange = (selection) => {
  selectedInterfaces.value = selection
}

const handleTestedInterfaces = () => {
  ElMessage.info('已测接口功能开发中...')
}

const handleCreateInterface = (prefilledData = null) => {
  currentInterface.value = null
  isEditMode.value = false

  // 如果有预填充数据，使用预填充数据，否则使用默认数据
  if (prefilledData) {
    formData.value = {
      method: prefilledData.method || 'GET',
      path: prefilledData.path || '',
      summary: prefilledData.summary || '',
      description: prefilledData.description || '',
      module: prefilledData.module || '',
      parameters: prefilledData.parameters || {
        path: [],
        query: [],
        header: []
      },
      requestBody: prefilledData.requestBody || {
        content_type: 'application/json',
        body: []
      },
      request_body: prefilledData.request_body || {},
      responses: prefilledData.responses || []
    }
  } else {
    // 重置表单数据
    formData.value = {
      method: 'GET',
      path: '',
      summary: '',
      description: '',
      parameters: {
        path: [],
        query: [],
        header: []
      },
      request_body: {},
      responses: []
    }
  }

  formModalVisible.value = true
}

const handleEditInterface = async (row) => {
  console.log('Index.vue - 编辑接口列表数据:', row)
  
  try {
    // 调用接口详情API获取完整数据
    const response = await getInterfaceDetail(projectId.value, row.id)
    console.log('Index.vue - 接口详情API响应:', response)
    
    const interfaceDetail = response.data
    console.log('Index.vue - 接口详情数据:', interfaceDetail)
    
    currentInterface.value = {...interfaceDetail}
    isEditMode.value = true

    // 设置表单数据，确保数据结构完整
    formData.value = {
      method: interfaceDetail.method || 'GET',
      path: interfaceDetail.path || '',
      summary: interfaceDetail.summary || '',
      description: interfaceDetail.description || '',
      parameters: interfaceDetail.parameters || {
        path: [],
        query: [],
        header: []
      },
      request_body: interfaceDetail.request_body || {},
      responses: Array.isArray(interfaceDetail.responses) ? interfaceDetail.responses : []
    }
    
    console.log('Index.vue - 设置的formData:', formData.value)
    formModalVisible.value = true
    
  } catch (error) {
    console.error('获取接口详情失败:', error)
    ElMessage.error('获取接口详情失败，请重试')
  }
}

const handleViewDetail = async (row) => {
  try {
    loading.value = true
    // 调用API获取完整的接口详情数据，包括依赖组信息
    const response = await getInterfaceDetail(projectId.value, row.id)
    currentInterface.value = response.data
    detailModalVisible.value = true
  } catch (error) {
    console.error('获取接口详情失败:', error)
    ElMessage.error('获取接口详情失败')
  } finally {
    loading.value = false
  }
}

const handleDeleteInterface = async (row) => {
  try {
    await ElMessageBox.confirm(
        `确定要删除接口 "${row.name}" 吗？`,
        '删除确认',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }
    )

    await deleteApiInterface(projectId.value, row.id)
    ElMessage.success('删除成功')
    fetchInterfaceList()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除接口失败:', error)
      ElMessage.error('删除接口失败')
    }
  }
}

const handleGenerateCase = async (row) => {
  currentGenerateInterface.value = row
  selectedGenerateType.value = ''
  selectedTestEnvId.value = null
  generateCaseDialogVisible.value = true

  // 获取测试环境列表
  try {
    const response = await getTestEnvironments(projectId.value)
    testEnvironments.value = response.data.items || []
  } catch (error) {
    console.error('获取测试环境失败:', error)
    ElMessage.error('获取测试环境失败')
  }
}

const handleSizeChange = (size) => {
  pagination.pageSize = size
  pagination.page = 1
  fetchInterfaceList()
}

const handleCurrentChange = (page) => {
  pagination.page = page
  fetchInterfaceList()
}

const handleFormSuccess = () => {
  formModalVisible.value = false
  fetchInterfaceList()
}

// 确认生成用例
const confirmGenerateCase = () => {
  if (!currentGenerateInterface.value || !selectedGenerateType.value) {
    return
  }

  generateCaseDialogVisible.value = false

  // 根据选择的类型跳转到不同的生成页面
  if (selectedGenerateType.value === 'basic') {
    // 跳转到基础用例生成页面
    router.push({
      name: 'ApiCaseGenerate',
      params: {
        projectId: projectId.value,
        interfaceId: currentGenerateInterface.value.id
      },
      query: {
        type: 'basic'
      }
    })
  } else if (selectedGenerateType.value === 'complete') {
    // 完整用例生成 - 跳转到独立页面
    router.push({
      name: 'ApiCompleteCaseGenerate',
      params: {
        projectId: projectId.value,
        interfaceId: currentGenerateInterface.value.id
      }
    })
  }
}

// 表单提交处理
const handleFormSubmit = async (formDataValue) => {
  try {
    // 转换数据格式以符合后端API要求
  const submitData = {
    method: formDataValue.method,
    path: formDataValue.path,
    summary: formDataValue.summary,
    // 确保parameters是字典类型
    parameters: formDataValue.parameters || {
      path: [],
      query: [],
      header: []
    },
    // 请求体采用包装结构：content_type + body（参数数组）
    request_body: {
      content_type: formDataValue.requestBody?.content_type || 'application/json',
      body: Array.isArray(formDataValue.requestBody?.body) ? formDataValue.requestBody.body : []
    },
    responses: formDataValue.responses || []
  }

    if (isEditMode.value) {
      // 编辑接口
      await updateApiInterface(projectId.value, currentInterface.value.id, submitData)
      ElMessage.success('接口更新成功')
    } else {
      // 创建接口
      await createApiInterface(projectId.value, submitData)
      ElMessage.success('接口创建成功')
    }

    formModalVisible.value = false
    fetchInterfaceList()
  } catch (error) {
    console.error('保存接口失败:', error)
    ElMessage.error('保存接口失败')
  }
}

// 表单取消处理
const handleFormCancel = () => {
  formModalVisible.value = false
  interfaceFormRef.value?.resetForm()
}

// 生命周期
onMounted(() => {
  fetchInterfaceList()

  // 检查路由查询参数，如果有action=add，则打开添加接口弹框
  if (route.query.action === 'add' && route.query.data) {
    try {
      const interfaceData = JSON.parse(route.query.data)
      handleCreateInterface(interfaceData)
    } catch (error) {
      console.error('解析接口数据失败:', error)
      ElMessage.error('接口数据格式错误')
    }
  }
})

// 组件激活时重新获取数据（解决tab切换后数据不显示的问题）
// onActivated(() => {
//   fetchInterfaceList()
// })

// 监听路由参数变化
watch(() => route.params.projectId, (newProjectId) => {
  if (newProjectId) {
    fetchInterfaceList()
  }
}, {immediate: true})

// 监听路由查询参数变化
watch(() => route.query, (newQuery) => {
  if (newQuery.action === 'add' && newQuery.data) {
    try {
      const interfaceData = JSON.parse(newQuery.data)
      handleCreateInterface(interfaceData)

      // 清除查询参数，避免重复触发
      router.replace({
        path: route.path,
        query: {}
      })
    } catch (error) {
      console.error('解析接口数据失败:', error)
      ElMessage.error('接口数据格式错误')
    }
  }
}, {immediate: true})
</script>

<style scoped>
.api-management-page {
  padding: 20px;
  background: #f5f7fa;
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
  color: #606266;
  margin: 0;
  font-size: 14px;
}

/* 移除统计面板相关样式，采用与套件页一致的头部样式 */

/* 筛选工具栏 */
.filter-toolbar {
  margin: 16px 0;
}

.filter-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* 主内容区域 */
.main-content {
  background: white;
  border-radius: 8px;
  overflow: hidden;
}

.content-card {
  border: none;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

/* 筛选区域 */
.filter-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 16px 0;
  border-bottom: 1px solid #ebeef5;
}

.filter-left {
  display: flex;
  align-items: center;
}

.filter-right {
  display: flex;
  align-items: center;
}

/* 工具栏 */
.toolbar-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.toolbar-left {
  display: flex;
  align-items: center;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* 表格区域 */
.table-section {
  margin-bottom: 20px;
}

.interface-form-dialog {

.el-dialog__body {
  padding: 20px;
  max-height: 70vh;
  overflow-y: auto;
}

}

.action-buttons {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.interface-path {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
  background: #f5f7fa;
  padding: 2px 6px;
  border-radius: 4px;
  color: #e6a23c;
}

/* 分页区域 */
.pagination-section {
  display: flex;
  justify-content: center;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
}

/* 用例生成选择弹框样式 */
.generate-case-options {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.option-card {
  display: flex;
  align-items: center;
  padding: 16px;
  border: 2px solid #e4e7ed;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.option-card:hover {
  border-color: #409eff;
  background-color: #f0f9ff;
}

.option-card.active {
  border-color: #409eff;
  background-color: #f0f9ff;
}

.option-icon {
  margin-right: 16px;
  color: #409eff;
}

.option-content {
  flex: 1;
}

.option-content h4 {
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.option-content p {
  margin: 0;
  font-size: 14px;
  color: #606266;
  line-height: 1.4;
}

.option-radio {
  margin-left: 16px;
}

.test-env-selection {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #e4e7ed;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .stats-panel {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
  }

  .stats-card:nth-child(4),
  .stats-card:nth-child(5) {
    grid-column: span 1;
  }
}

@media (max-width: 768px) {
  .api-management-page {
    padding: 12px;
  }

  .stats-panel {
    grid-template-columns: 1fr;
  }

  .filter-section {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }

  .filter-right {
    justify-content: flex-start;
    flex-wrap: wrap;
    gap: 8px;
  }

  .toolbar-section {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }

  .toolbar-right {
    justify-content: flex-start;
  }
}
</style>