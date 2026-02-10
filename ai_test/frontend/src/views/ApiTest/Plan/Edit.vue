<template>
  <!-- 主要内容区域 - 左右布局 -->
  <div class="page-content">
    <div class="content-layout">

      <div class="left-panel" style="flex: 0.4;">
        <!-- 左侧：测试计划基本信息编辑表单 -->
        <div class="plan-info-section">
          <div class="modern-info-card">
            <div class="card-header">
              <div class="card-title">
                <div class="title-icon">
                  <el-icon>
                    <Edit/>
                  </el-icon>
                </div>
                <div class="title-text">
                  <h3>测试计划基本信息</h3>
                  <p>编辑和管理测试计划的基本配置</p>
                </div>
              </div>
              <div class="card-actions">
                <el-button @click="goBack">
                  <el-icon>
                    <ArrowLeft/>
                  </el-icon>
                  返回计划列表
                </el-button>
                <el-button
                    type="primary"
                    :loading="runningTest"
                    @click="runTask"
                >
                  <el-icon>
                    <VideoPlay/>
                  </el-icon>
                  运行计划
                </el-button>
              </div>
            </div>

            <div class="card-body">
              <el-form
                  :model="taskDetail"
                  label-width="0px"
                  size="large"
                  class="modern-task-form"
              >
                <div class="form-grid">
                  <div class="form-group">
                    <label class="form-label">计划名称</label>
                    <el-input
                        v-model="taskDetail.task_name"
                        placeholder="请输入计划名称"
                        @blur="updateTaskInfo"
                        maxlength="100"
                        show-word-limit
                        class="modern-input"
                    ></el-input>
                  </div>
                  <div class="form-group">
                    <label class="form-label">计划类型</label>
                    <el-select
                        v-model="taskDetail.type"
                        placeholder="选择计划类型"
                        @change="updateTaskInfo"
                        class="modern-select"
                    >
                      <el-option label="API测试" value="api"/>
                      <el-option label="UI测试" value="ui"/>
                      <el-option label="混合测试" value="mixed"/>
                    </el-select>
                  </div>
                </div>
                <div class="form-group full-width">
                  <label class="form-label">计划描述</label>
                  <el-input
                      v-model="taskDetail.description"
                      type="textarea"
                      :rows="3"
                      placeholder="请输入计划描述"
                      @blur="updateTaskInfo"
                      maxlength="500"
                      show-word-limit
                      class="modern-textarea"
                  ></el-input>
                </div>
              </el-form>
              <!-- 左侧：计划中的套件列表 -->
              <div style="margin-top: 10px;">
                <label class="form-label">计划中的套件</label>
                <span class="count" v-if="taskDetail">
                  ({{ taskDetail.suites?.length || 0 }} 个套件)
                </span>
              </div>
              <el-card class="task-suites-card">
                <div v-loading="loading" class="suites-container">
                  <div v-if="!taskDetail.suites || taskDetail.suites.length === 0" class="empty-state">
                    <el-empty description="暂无套件，请从右侧套件库中添加"/>
                  </div>
                  <div v-else class="suites-list">
                    <draggable
                        v-model="taskDetail.suites"
                        item-key="suite_id"
                        @end="handleSuiteReorder"
                        class="draggable-list"
                    >
                      <template #item="{ element: suite, index }">
                        <div class="suite-item">
                          <div class="suite-info">
                            <div class="suite-order">{{ index + 1 }}</div>
                            <div class="suite-details">
                              <div class="suite-name">{{ suite.suite_name }}</div>
                              <div class="suite-meta">
                                <el-tag size="small" type="info">套件ID: {{ suite.suite_id }}</el-tag>
                              </div>
                            </div>
                          </div>
                          <div class="suite-actions">
                            <el-button
                                type="danger"
                                size="small"
                                plain
                                @click="removeSuiteFromTask(suite.suite_id)"
                                :loading="removingSuiteId === suite.suite_id"
                                :icon="Delete"
                            >
                              移除
                            </el-button>
                          </div>
                        </div>
                      </template>
                    </draggable>
                  </div>
                </div>
              </el-card>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧：套件库和执行记录 -->
      <div class="right-panel" style="flex: 0.6;">
        <el-card class="tabs-card">
          <div class="custom-tabs">
            <div class="custom-tabs-nav">
              <button
                class="custom-tab-item"
                :class="{ 'is-active': activeTab === 'suites' }"
                @click="activeTab = 'suites'"
                type="button"
              >
                <el-icon><Collection /></el-icon>
                <span>套件库</span>
              </button>
              <button
                class="custom-tab-item"
                :class="{ 'is-active': activeTab === 'history' }"
                @click="activeTab = 'history'"
                type="button"
              >
                <el-icon><Clock /></el-icon>
                <span>执行记录</span>
              </button>
            </div>

            <!-- 套件库内容 -->
            <div class="tab-content" v-show="activeTab === 'suites'">
              <!-- 搜索栏 -->
              <div class="search-section">
                <el-input
                    v-model="searchKeyword"
                    placeholder="搜索套件名称"
                    clearable
                    @input="loadAvailableSuites"
                    class="search-input"
                >
                  <template #prefix>
                    <el-icon><Search /></el-icon>
                  </template>
                </el-input>
              </div>

              <!-- 套件列表 -->
              <div v-loading="loadingSuites" class="suites-section">
                <div v-if="!availableSuites.length" class="empty-state">
                  <el-empty
                      :description="searchKeyword ? '未找到匹配的套件' : '暂无套件'"
                  />
                </div>

                <div v-else class="suites-table">
                  <el-table
                      :data="availableSuites"
                      style="width: 100%"
                      stripe
                  >
                    <el-table-column prop="id" label="ID" width="80"/>
                    <el-table-column prop="suite_name" label="套件名称" min-width="150" show-overflow-tooltip>
                      <template #default="{ row }">
                        <div class="suite-name-cell">
                          <span>{{ row.suite_name }}</span>
                          <el-tag
                              v-if="isSuiteInTask(row.id)"
                              type="success"
                              size="small"
                              class="task-tag"
                          >
                            已添加
                          </el-tag>
                        </div>
                      </template>
                    </el-table-column>
                    <el-table-column prop="type" label="类型" width="100">
                      <template #default="{ row }">
                        <el-tag :type="row.type === 'api' ? 'success' : 'warning'" size="small">
                          {{ row.type === 'api' ? 'API' : 'UI' }}
                        </el-tag>
                      </template>
                    </el-table-column>
                    <el-table-column label="操作" width="120" fixed="right">
                      <template #default="{ row }">
                        <el-button
                            v-if="!isSuiteInTask(row.id)"
                            type="primary"
                            size="small"
                            @click="addSuiteToTask(row.id)"
                            :loading="addingSuiteId === row.id"
                            :icon="Plus"
                        >
                          加入计划
                        </el-button>
                        <el-tag v-else type="success" size="small">已在计划中</el-tag>
                      </template>
                    </el-table-column>
                  </el-table>
                </div>

                <!-- 分页 -->
                <div class="pagination-section" v-if="suitePagination.total > 0">
                  <el-pagination
                      v-model:current-page="suitePagination.page"
                      v-model:page-size="suitePagination.page_size"
                      :total="suitePagination.total"
                      :page-sizes="[10, 20, 50]"
                      layout="total, sizes, prev, pager, next"
                      @current-change="loadAvailableSuites"
                      @size-change="loadAvailableSuites"
                  />
                </div>
              </div>
            </div>

            <!-- 执行记录内容 -->
            <div class="tab-content" v-show="activeTab === 'history'">
              <TaskRunHistory 
                :task-id="taskId" 
                :project-id="projectId"
                @rerun-task="handleRerunTask"
              />
            </div>
          </div>
        </el-card>
      </div>
    </div>
  </div>

  <!-- 环境选择对话框 -->
  <el-dialog
      v-model="showEnvironmentDialog"
      title="选择测试环境"
      width="500px"
      :close-on-click-modal="false"
  >
    <div v-loading="loadingEnvironments">
      <p style="margin-bottom: 16px; color: #666;">
        请选择要运行测试计划的测试环境：
      </p>
      <div class="environment-cards">
        <div 
          v-for="env in environments" 
          :key="env.id" 
          class="environment-card"
          :class="{ 'selected': selectedEnvironmentId === env.id }"
          @click="selectedEnvironmentId = env.id"
        >
          <div class="card-header">
            <div class="env-name">{{ env.name }}</div>
            <div class="card-actions">
              <el-tag v-if="env.is_default" type="primary" size="small">默认</el-tag>
              <div class="radio-indicator" :class="{ 'checked': selectedEnvironmentId === env.id }">
                 <el-icon v-if="selectedEnvironmentId === env.id" size="12">
                   <Check />
                 </el-icon>
               </div>
            </div>
          </div>
          <div class="env-url">{{ env.base_url }}</div>
          <div class="env-description" v-if="env.description">{{ env.description }}</div>
        </div>
      </div>
      
      <div v-if="environments.length === 0 && !loadingEnvironments" style="text-align: center; color: #999; padding: 20px;">
        暂无可用的测试环境
      </div>
    </div>
    
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="cancelRunTask">取消</el-button>
        <el-button 
            type="primary" 
            @click="confirmRunTask"
            :disabled="!selectedEnvironmentId"
            :loading="runningTest"
        >
          开始运行
        </el-button>
      </span>
    </template>
  </el-dialog>

  <!-- 运行结果对话框 -->
  <el-dialog
      v-model="showResultDialog"
      title="测试计划运行结果"
      width="800px"
      :close-on-click-modal="false"
  >
    <div v-if="runResult">
      <!-- 错误状态警告 -->
      <div v-if="runResult.status === 'error'" style="margin-bottom: 20px;">
        <el-alert
            title="运行失败"
            type="error"
            :description="runResult.error_message || '运行过程中发生错误，请检查错误用例'"
            show-icon
            :closable="false"
        />
      </div>

      <!-- 运行统计（按返回的 summary 字段渲染） -->
      <div class="result-stats">
        <div class="stat-item">
          <div class="stat-label">总套件数</div>
          <div class="stat-value">{{ runResult.summary?.total_suites ?? '-' }}</div>
        </div>
        <div class="stat-item">
          <div class="stat-label">总用例数</div>
          <div class="stat-value">{{ runResult.summary?.total_cases ?? '-' }}</div>
        </div>
        <div class="stat-item success">
          <div class="stat-label">成功用例</div>
          <div class="stat-value">{{ runResult.summary?.success_cases ?? '-' }}</div>
        </div>
        <div class="stat-item danger">
          <div class="stat-label">失败用例</div>
          <div class="stat-value">{{ runResult.summary?.failed_cases ?? '-' }}</div>
        </div>
        <div class="stat-item danger">
          <div class="stat-label">错误用例</div>
          <div class="stat-value">{{ runResult.summary?.error_cases ?? '-' }}</div>
        </div>
        <div class="stat-item warning">
          <div class="stat-label">跳过用例</div>
          <div class="stat-value">{{ runResult.summary?.skip_cases ?? '-' }}</div>
        </div>
      </div>

      <!-- 运行时间 -->
      <div class="result-time">
        <p><strong>开始时间：</strong>{{ formatDateTime(runResult.start_time) }}</p>
        <p><strong>结束时间：</strong>{{ formatDateTime(runResult.end_time) }}</p>
        <p><strong>运行时长：</strong>{{ formatDuration(runResult.duration) }}</p>
      </div>
    </div>
    
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="showResultDialog = false">关闭</el-button>
        <!-- 已移除查看详细报告入口 -->
      </span>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Edit, ArrowLeft, VideoPlay, Collection, Clock, Search, 
  Plus, Delete, Check 
} from '@element-plus/icons-vue'
import draggable from 'vuedraggable'

// 导入API
import { 
  getTestTaskDetail, 
  getTestSuites, 
  addSuiteToTask as apiAddSuiteToTask,
  deleteSuiteFromTask as apiDeleteSuiteFromTask,
  reorderTaskSuites as apiReorderTaskSuites
} from '@/api/test_management'
import { getTestEnvironments } from '@/api/test_environment'
import { runTestTask } from '@/api/test_execution'

// 导入组件
import TaskRunHistory from './components/TaskRunHistory.vue'

const route = useRoute()
const router = useRouter()

// 路由参数
const projectId = computed(() => parseInt(route.params.projectId))
const taskId = computed(() => parseInt(route.params.taskId))

// 响应式数据
const loading = ref(false)
const loadingSuites = ref(false)
const loadingEnvironments = ref(false)
const runningTest = ref(false)

// 测试计划详情
const taskDetail = ref({
  id: null,
  task_name: '',
  description: '',
  type: 'api',
  status: 'pending',
  suites: []
})

// 右侧tabs
const activeTab = ref('suites')

// 套件库相关
const availableSuites = ref([])
const searchKeyword = ref('')
const suitePagination = reactive({
  page: 1,
  page_size: 10,
  total: 0
})

// 操作状态
const addingSuiteId = ref(null)
const removingSuiteId = ref(null)

// 环境选择
const showEnvironmentDialog = ref(false)
const environments = ref([])
const selectedEnvironmentId = ref(null)

// 运行结果
const showResultDialog = ref(false)
const runResult = ref(null)

// 方法
const goBack = () => {
  router.push({
    name: 'ApiTestPlan',
    params: { projectId: projectId.value }
  })
}

const loadTaskDetail = async () => {
  loading.value = true
  try {
    const response = await getTestTaskDetail(projectId.value, taskId.value)
    taskDetail.value = response.data
  } catch (error) {
    console.error('加载测试计划详情失败:', error)
    ElMessage.error('加载测试计划详情失败')
  } finally {
    loading.value = false
  }
}

const updateTaskInfo = async () => {
  // 这里可以添加更新测试计划基本信息的逻辑
  ElMessage.success('计划信息已更新')
}

const loadAvailableSuites = async () => {
  loadingSuites.value = true
  try {
    const params = {
      page: suitePagination.page,
      page_size: suitePagination.page_size
    }
    if (searchKeyword.value) {
      params.search = searchKeyword.value
    }
    
    const response = await getTestSuites(projectId.value, params)
    availableSuites.value = response.data.suites
    suitePagination.total = response.data.total
  } catch (error) {
    console.error('加载套件库失败:', error)
    ElMessage.error('加载套件库失败')
  } finally {
    loadingSuites.value = false
  }
}

const isSuiteInTask = (suiteId) => {
  return taskDetail.value.suites?.some(suite => suite.suite_id === suiteId)
}

const addSuiteToTask = async (suiteId) => {
  addingSuiteId.value = suiteId
  try {
    await apiAddSuiteToTask(projectId.value, taskId.value, { suite_id: suiteId })
    ElMessage.success('套件已添加到测试计划')
    await loadTaskDetail()
  } catch (error) {
    console.error('添加套件失败:', error)
    ElMessage.error('添加套件失败')
  } finally {
    addingSuiteId.value = null
  }
}

const removeSuiteFromTask = async (suiteId) => {
  removingSuiteId.value = suiteId
  try {
    await apiDeleteSuiteFromTask(projectId.value, taskId.value, suiteId)
    ElMessage.success('套件已从测试计划中移除')
    await loadTaskDetail()
  } catch (error) {
    console.error('移除套件失败:', error)
    ElMessage.error('移除套件失败')
  } finally {
    removingSuiteId.value = null
  }
}

const handleSuiteReorder = async () => {
  try {
    const suiteIds = taskDetail.value.suites.map(suite => suite.suite_id)
    await apiReorderTaskSuites(projectId.value, taskId.value, { suite_ids: suiteIds })
    ElMessage.success('套件顺序已更新')
  } catch (error) {
    console.error('更新套件顺序失败:', error)
    ElMessage.error('更新套件顺序失败')
    await loadTaskDetail() // 重新加载以恢复原始顺序
  }
}

const runTask = async () => {
  if (!taskDetail.value.suites || taskDetail.value.suites.length === 0) {
    ElMessage.warning('测试计划中没有套件，无法运行')
    return
  }
  
  // 加载环境列表
  loadingEnvironments.value = true
  try {
    const response = await getTestEnvironments(projectId.value)
    environments.value = response.data.environments
    
    // 如果有默认环境，自动选择
    const defaultEnv = environments.value.find(env => env.is_default)
    if (defaultEnv) {
      selectedEnvironmentId.value = defaultEnv.id
    }
    
    showEnvironmentDialog.value = true
  } catch (error) {
    console.error('加载测试环境失败:', error)
    ElMessage.error('加载测试环境失败')
  } finally {
    loadingEnvironments.value = false
  }
}

const cancelRunTask = () => {
  showEnvironmentDialog.value = false
  selectedEnvironmentId.value = null
}

const confirmRunTask = async () => {
  runningTest.value = true
  try {
    const response = await runTestTask(projectId.value, {
      task_id: taskId.value,
      environment_id: selectedEnvironmentId.value
    })
    
    runResult.value = response.data
    showEnvironmentDialog.value = false
    showResultDialog.value = true
    
    ElMessage.success('测试计划运行完成')
  } catch (error) {
    console.error('运行测试计划失败:', error)
    ElMessage.error('运行测试计划失败')
  } finally {
    runningTest.value = false
  }
}

const handleRerunTask = (taskRunId) => {
  // 重新运行测试计划的逻辑
  ElMessage.info('重新运行功能开发中')
}

// 已移除详细报告跳转功能

const formatDateTime = (dateTime) => {
  if (!dateTime) return '-'
  return new Date(dateTime).toLocaleString()
}

const formatDuration = (duration) => {
  if (!duration) return '-'
  return `${duration.toFixed(2)}秒`
}

// 生命周期
onMounted(() => {
  loadTaskDetail()
  loadAvailableSuites()
})
</script>

<style scoped>
/* 复用测试套件编辑页面的样式，并做适当调整 */
.page-content {
  background: #f8fafc;
  min-height: 100vh;
}

.content-layout {
  display: flex;
  gap: 24px;
  height: calc(100vh - 48px);
}

.left-panel, .right-panel {
  display: flex;
  flex-direction: column;
}

.modern-info-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  overflow: hidden;
  border: none;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid #ebeef5;
  background: none;
  color: #111827;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 16px;
}

.title-icon {
  width: 32px;
  height: 32px;
  background: transparent;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  color: #6366f1;
}

.title-text h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 500;
  color: #111827;
}

.title-text p {
  margin: 4px 0 0 0;
  opacity: 1;
  font-size: 13px;
  color: #6b7280;
}

.card-actions {
  display: flex;
  gap: 12px;
}

.card-body {
  padding: 16px;
}

.modern-task-form {
  margin-bottom: 24px;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group.full-width {
  grid-column: 1 / -1;
}

.form-label {
  font-weight: 600;
  color: #374151;
  font-size: 14px;
}

.count {
  color: #6b7280;
  font-size: 14px;
  margin-left: 8px;
}

.task-suites-card {
  margin-top: 16px;
}

.suites-container {
  min-height: 200px;
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
}

.suites-list {
  max-height: 400px;
  overflow-y: auto;
}

.draggable-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.suite-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: #f8fafc;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  cursor: move;
  transition: all 0.2s ease;
}

.suite-item:hover {
  background: #f1f5f9;
  border-color: #d1d5db;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.suite-info {
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 1;
}

.suite-order {
  width: 32px;
  height: 32px;
  background: #667eea;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 14px;
}

.suite-details {
  flex: 1;
}

.suite-name {
  font-weight: 600;
  color: #374151;
  margin-bottom: 4px;
}

.suite-meta {
  display: flex;
  gap: 8px;
}

.tabs-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  border: none;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.modern-tabs {
  flex: 1;
  display: flex;
  flex-direction: column;
}

/* 统一 Tabs 样式，贴合套件页面的中性风格 */
.modern-tabs :deep(.el-tabs__nav-wrap) {
  padding: 0 12px;
}

.modern-tabs :deep(.el-tabs__item) {
  padding: 12px 16px;
  font-size: 14px;
  color: #374151;
}

.modern-tabs :deep(.el-tabs__item.is-active) {
  color: #6366f1;
}

.modern-tabs :deep(.el-tabs__active-bar) {
  background-color: #6366f1;
  height: 2px;
}

.modern-tabs :deep(.el-tabs__content) {
  padding: 16px;
}

.tab-label {
  display: flex;
  align-items: center;
  gap: 8px;
  color: inherit;
}

.tab-label .el-icon {
  font-size: 16px;
  color: #6366f1;
}

.tab-content {
  padding: 20px 0;
  flex: 1;
  display: flex;
  flex-direction: column;
}

/* 自定义 Tabs 导航样式 */
.custom-tabs {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.custom-tabs-nav {
  display: flex;
  gap: 8px;
  border-bottom: 1px solid #e5e7eb;
}

.custom-tab-item {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  border-radius: 6px 6px 0 0;
  background: transparent;
  border: 1px solid transparent;
  color: #374151;
  cursor: pointer;
  transition: color 0.2s ease, background-color 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}

.custom-tab-item:hover {
  color: #111827;
  background-color: #f9fafb;
}

.custom-tab-item.is-active {
  color: #6366f1;
  background: #ffffff;
  border-color: #6366f1; /* 项目主题紫色 */
  border-bottom-color: #ffffff; /* 与内容区无缝衔接 */
  position: relative;
  margin-bottom: -1px; /* 覆盖导航的底边框，形成卡片效果 */
  z-index: 2;
}

.custom-tab-item.is-active::after {
  content: '';
  position: absolute;
  left: 0;
  bottom: -1px;
  width: 100%;
  height: 2px;
  background-color: #6366f1;
}

/* 图标颜色随状态变化 */
.custom-tab-item .el-icon {
  color: #9ca3af;
  transition: color 0.2s ease;
}
.custom-tab-item:hover .el-icon {
  color: #6b7280;
}
.custom-tab-item.is-active .el-icon {
  color: #6366f1;
}

/* 键盘可访问性焦点样式 */
.custom-tab-item:focus-visible {
  outline: none;
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.3);
  border-color: #6366f1;
}

/* 移除默认焦点黑框，并统一为主题紫色 */
.custom-tab-item:focus {
  outline: none !important;
  border-color: #6366f1;
}

/* 点击瞬间态也保持主题色边框 */
.custom-tab-item:active {
  border-color: #6366f1;
}

.custom-tab-content {
  padding: 16px;
  flex: 1;
  display: flex;
  flex-direction: column;
}

.search-section {
  margin-bottom: 20px;
}

.search-input {
  max-width: 300px;
}

.suites-section {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.suites-table {
  flex: 1;
}

.suite-name-cell {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.task-tag {
  margin-left: 8px;
}

.pagination-section {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

/* 环境选择对话框样式 */
.environment-cards {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 400px;
  overflow-y: auto;
}

.environment-card {
  padding: 16px;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.environment-card:hover {
  border-color: #d1d5db;
  background: #f9fafb;
}

.environment-card.selected {
  border-color: #667eea;
  background: #f0f4ff;
}

.environment-card .card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  padding: 0;
  border: none;
  background: none;
  color: inherit;
}

.env-name {
  font-weight: 600;
  color: #374151;
}

.card-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.radio-indicator {
  width: 20px;
  height: 20px;
  border: 2px solid #d1d5db;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.radio-indicator.checked {
  border-color: #667eea;
  background: #667eea;
  color: white;
}

.env-url {
  color: #6b7280;
  font-size: 14px;
  margin-bottom: 4px;
}

.env-description {
  color: #9ca3af;
  font-size: 13px;
}

/* 运行结果样式 */
.result-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-item {
  text-align: center;
  padding: 16px;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.stat-item.success {
  background: #f0fdf4;
  border-color: #bbf7d0;
}

.stat-item.danger {
  background: #fef2f2;
  border-color: #fecaca;
}

.stat-item.warning {
  background: #fffbeb;
  border-color: #fed7aa;
}

.stat-label {
  font-size: 14px;
  color: #6b7280;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: #374151;
}

.result-time {
  background: #f8fafc;
  padding: 16px;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.result-time p {
  margin: 8px 0;
  color: #374151;
}
</style>