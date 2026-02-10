<template>


    <!-- 主要内容区域 - 左右布局 -->
    <div class="page-content">
      <div class="content-layout">

        <div class="left-panel" style="flex: 0.4;">
          <!-- 左侧：套件基本信息编辑表单 -->
          <div class="suite-info-section">
            <div class="modern-info-card">
              <div class="card-header">
                <div class="card-title">
                  <div class="title-icon">
                    <el-icon>
                      <Edit/>
                    </el-icon>
                  </div>
                  <div class="title-text">
                    <h3>套件基本信息</h3>
                    <p>编辑和管理测试套件的基本配置</p>
                  </div>
                </div>
                <div class="card-actions">

                  <el-button @click="goBack">
                    <el-icon>
                      <ArrowLeft/>
                    </el-icon>
                    返回套件列表
                  </el-button>
                  <el-button
                      type="primary"
                      :loading="runningTest"
                      @click="runSuite"
                  >
                    <el-icon>
                      <VideoPlay/>
                    </el-icon>
                    运行套件
                  </el-button>
                </div>
              </div>

              <div class="card-body">
                <el-form
                    :model="suiteDetail"
                    label-width="0px"
                    size="large"
                    class="modern-suite-form"
                >
                  <div class="form-grid">
                    <div class="form-group">
                      <label class="form-label">套件名称</label>
                      <el-input
                          v-model="suiteDetail.suite_name"
                          placeholder="请输入套件名称"
                          @blur="updateSuiteInfo"
                          maxlength="100"
                          show-word-limit
                          class="modern-input"
                      />
                    </div>
                    <div class="form-group">
                      <label class="form-label">套件类型</label>
                      <el-select
                          v-model="suiteDetail.type"
                          placeholder="选择套件类型"
                          @change="updateSuiteInfo"
                          class="modern-select"
                      >
                        <el-option label="API测试" value="api"/>
                        <el-option label="UI测试" value="ui"/>
                      </el-select>
                    </div>
                  </div>
                  <div class="form-group full-width">
                    <label class="form-label">套件描述</label>
                    <el-input
                        v-model="suiteDetail.description"
                        type="textarea"
                        :rows="3"
                        placeholder="请输入套件描述"
                        @blur="updateSuiteInfo"
                        maxlength="500"
                        show-word-limit
                        class="modern-textarea"
                    />
                  </div>
                </el-form>
                <!-- 左侧：套件用例列表 -->
                <div style="margin-top: 10px;">
                  <label class="form-label">套件中的用例
                  </label>
                  <span class="count" v-if="suiteDetail">
                  ({{ suiteDetail.cases?.length || 0 }} 个用例)
                </span>
                </div>
                <el-card class="suite-cases-card">
                  <div v-loading="loading" class="cases-container">
                    <div v-if="!suiteDetail?.cases?.length" class="empty-state">
                      <el-empty description="暂无用例，请从右侧用例库中添加用例"/>
                    </div>
                    <!-- 拖拽用例列表 -->
                    <draggable
                        v-else
                        v-model="suiteDetail.cases"
                        @end="handleDragEnd"
                        item-key="case_id"
                        class="draggable-list"
                        :disabled="loading"
                    >
                      <template #item="{ element: caseItem, index }">
                        <div class="case-item">
                          <div class="case-content">
                            <div class="case-header">
                              <div class="case-info">
                                <el-icon class="drag-handle">
                                  <Rank/>
                                </el-icon>
                                <span class="case-name">{{ caseItem.case_name }}</span>
                                <el-tag size="small" type="info" class="order-tag">
                                  #{{ index + 1 }}
                                </el-tag>
                              </div>
                              <el-button
                                  size="small"
                                  @click="removeCaseFromSuite(caseItem)"
                                  :loading="removingCaseId === caseItem.case_id"

                              >
                                <el-icon>
                                  <Delete/>
                                </el-icon>
                              </el-button>
                            </div>
                            <div class="case-description" v-if="caseItem.description">
                              {{ caseItem.description }}
                            </div>
                          </div>
                        </div>
                      </template>
                    </draggable>
                  </div>
                </el-card>

              </div>
            </div>


          </div>
        </div>

        <!-- 右侧：标签页面板 -->
        <div class="right-panel" style="flex: 0.6; width: auto;">
          <el-card class="tabs-card">
            <el-tabs v-model="activeTab" class="suite-tabs" @tab-change="handleTabChange">
              <!-- 用例库标签 -->
              <el-tab-pane label="用例库" name="cases">
                <template #label>
                  <span class="tab-label">
                    <el-icon><Collection /></el-icon>
                    用例库
                  </span>
                </template>
                
                <div class="tab-content">
                  <!-- 筛选控制栏 -->
                  <div class="filter-controls">
                    <el-select
                        v-model="selectedInterfaceId"
                        placeholder="选择接口过滤"
                        clearable
                        style="width: 300px; margin-right: 10px;"
                        :loading="loadingInterfaces"
                    >
                      <el-option
                          v-for="interfaceItem in interfaces"
                          :key="interfaceItem.id"
                          :label="`${interfaceItem.summary} ${interfaceItem.method} ${interfaceItem.path}`"
                          :value="interfaceItem.id"
                      />
                    </el-select>
                    <el-input
                        v-model="searchKeyword"
                        placeholder="搜索可用用例..."
                        style="width: 250px;"
                        clearable
                    >
                      <template #prefix>
                        <el-icon>
                          <Search/>
                        </el-icon>
                      </template>
                    </el-input>
                  </div>

                  <!-- 用例列表 -->
                  <div v-loading="loadingCases" class="available-cases">
                    <div v-if="!availableCases.length" class="empty-state">
                      <el-empty
                          :description="searchKeyword ? '未找到匹配的用例' : '暂无用例'"
                      />
                    </div>

                    <div v-else class="cases-table">
                      <el-table
                          :data="availableCases"
                          style="width: 100%"
                          stripe
                      >
                        <el-table-column prop="id" label="ID" width="80"/>
                        <el-table-column prop="name" label="用例名称" min-width="150" show-overflow-tooltip>
                          <template #default="{ row }">
                            <div class="case-name-cell">
                              <span>{{ row.name }}</span>
                              <el-tag
                                  v-if="isCaseInSuite(row.id)"
                                  type="success"
                                  size="small"
                                  class="suite-tag"
                              >
                                已添加
                              </el-tag>
                            </div>
                          </template>
                        </el-table-column>
                        <el-table-column prop="interface_name" label="接口地址" min-width="200" show-overflow-tooltip/>
                        <el-table-column label="操作" width="120" fixed="right">
                          <template #default="{ row }">
                            <el-button
                                v-if="!isCaseInSuite(row.id)"
                                type="primary"
                                size="small"
                                @click="addCaseToSuite(row.id)"
                                :loading="addingCaseId === row.id"
                                icon="Plus"
                            >
                              加入套件
                            </el-button>
                            <el-tag v-else type="success" size="small">已在套件中</el-tag>
                          </template>
                        </el-table-column>
                      </el-table>
                    </div>

                    <!-- 分页 -->
                    <div class="pagination-section" v-if="casePagination.total > 0">
                      <el-pagination
                          v-model:current-page="casePagination.page"
                          v-model:page-size="casePagination.page_size"
                          :total="casePagination.total"
                          :page-sizes="[10, 20, 50]"
                          layout="total, sizes, prev, pager, next"
                          @current-change="loadAvailableCases"
                          @size-change="loadAvailableCases"
                      />
                    </div>
                  </div>
                </div>
              </el-tab-pane>

              <!-- 运行记录标签 -->
              <el-tab-pane label="运行记录" name="history">
                <template #label>
                  <span class="tab-label">
                    <el-icon><Clock /></el-icon>
                    运行记录
                  </span>
                </template>
                
                <div class="tab-content">
                   <SuiteRunHistory 
                     :suite-id="suiteId" 
                     :project-id="projectId"
                     @rerun-suite="handleRerunSuite"
                   />
                 </div>
              </el-tab-pane>
            </el-tabs>
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
          请选择要运行套件的测试环境：
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
          <el-button @click="cancelRunSuite">取消</el-button>
          <el-button 
              type="primary" 
              @click="confirmRunSuite"
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
        title="套件运行结果"
        width="800px"
        :close-on-click-modal="false"
    >
      <div v-if="runResult">
        <!-- 错误状态警告 -->
        <div v-if="runResult.status === 'error'" style="margin-bottom: 20px;">
          <el-alert
            title="套件运行出现错误"
            :description="runResult.error_message || '运行过程中发生未知错误'"
            type="error"
            :closable="false"
            show-icon
          />
        </div>

        <!-- 运行基本信息 -->
        <div style="margin-bottom: 20px; padding: 16px; background: #f8f9fa; border-radius: 8px;">
          <h4 style="margin-bottom: 12px; color: #333;">运行信息</h4>
          <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; font-size: 14px;">
            <div><strong>运行ID:</strong> {{ runResult.run_id }}</div>
            <div><strong>套件ID:</strong> {{ runResult.suite_id }}</div>
            <div><strong>环境ID:</strong> {{ runResult.environment_id }}</div>
            <div>
              <strong>运行状态:</strong> 
              <el-tag 
                :type="getStatusType(runResult.status)" 
                size="small"
              >
                {{ getStatusText(runResult.status) }}
              </el-tag>
            </div>
            <div><strong>开始时间:</strong> {{ formatDateTime(runResult.start_time) }}</div>
            <div><strong>结束时间:</strong> {{ formatDateTime(runResult.end_time) }}</div>
            <div><strong>总耗时:</strong> {{ formatDuration(runResult.duration) }}</div>
            <div v-if="runResult.error_message && runResult.status !== 'error'">
              <strong>错误信息:</strong> 
              <span style="color: #f56c6c;">{{ runResult.error_message }}</span>
            </div>
          </div>
        </div>

        <!-- 运行摘要 -->
        <div style="margin-bottom: 20px;">
          <h4 style="margin-bottom: 12px; color: #333;">运行摘要</h4>
          <div style="display: flex; gap: 16px; margin-bottom: 16px; flex-wrap: wrap;">
            <el-tag type="info" size="large">
              总计: {{ runResult.summary?.total || 0 }}
            </el-tag>
            <el-tag type="success" size="large">
              成功: {{ runResult.summary?.success || 0 }}
            </el-tag>
            <el-tag type="danger" size="large">
              失败: {{ runResult.summary?.failed || 0 }}
            </el-tag>
            <el-tag type="warning" size="large">
              错误: {{ runResult.summary?.error || 0 }}
            </el-tag>
            <el-tag type="info" size="large" v-if="runResult.summary?.skip">
              跳过: {{ runResult.summary.skip }}
            </el-tag>
          </div>
          <div style="font-size: 14px; color: #666;">
            <p><strong>摘要耗时:</strong> {{ formatDuration(runResult.summary?.duration) }}</p>
          </div>
        </div>

        <!-- 用例执行详情 -->
        <div v-if="runResult.case_results && runResult.case_results.length > 0">
          <h4 style="margin-bottom: 12px; color: #333;">用例执行详情</h4>
          <el-table :data="runResult.case_results" style="width: 100%;" max-height="400">
            <el-table-column prop="case_name" label="用例名称" width="200" />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag 
                  :type="getStatusType(row.status)" 
                  size="small"
                >
                  {{ getStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="duration" label="耗时" width="100">
              <template #default="{ row }">
                {{ formatDuration(row.duration) }}
              </template>
            </el-table-column>
            <el-table-column prop="error_message" label="错误信息" show-overflow-tooltip>
              <template #default="{ row }">
                <span v-if="row.error_message" style="color: #f56c6c;">{{ row.error_message }}</span>
                <span v-else>-</span>
              </template>
            </el-table-column>
          </el-table>
        </div>
        
        <!-- 如果没有详细用例结果，显示提示信息 -->
        <div v-else style="text-align: center; padding: 20px; color: #999;">
          <p>暂无详细用例执行信息</p>
          <p v-if="runResult.status === 'error'" style="color: #f56c6c; margin-top: 8px;">
            由于运行出错，无法获取用例执行详情
          </p>
        </div>
      </div>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showResultDialog = false">关闭</el-button>
        </span>
      </template>
    </el-dialog>

</template>

<script setup>
import {ref, reactive, computed, onMounted, watch} from 'vue'
import {useRoute, useRouter} from 'vue-router'
import {ElMessage, ElMessageBox} from 'element-plus'
import {
  ArrowLeft, Plus, Search, Rank, Delete, Edit, Document,
  CircleCheck, Warning, TrendCharts, VideoPlay, Refresh,
  Download, ArrowDown, CopyDocument, Loading, Check,
  Collection, Clock
} from '@element-plus/icons-vue'
import SuiteRunHistory from '@/components/SuiteRunHistory.vue'
import draggable from 'vuedraggable'
import {
  getSuiteDetail,
  addCaseToSuite as addCaseToSuiteApi,
  removeCaseFromSuite as removeCaseFromSuiteApi,
  reorderSuiteCases,
  getProjectTestCases,
  runTestSuite
} from '@/api/suite'
import {getProjectInterfaces} from '@/api/apiTest'
import {getTestEnvironments} from '@/api/test_environment'

const route = useRoute()
const router = useRouter()

// 响应式数据
const loading = ref(false)
const loadingCases = ref(false)
const searchKeyword = ref('')
const caseSearchKeyword = ref('')
const selectedInterfaceId = ref('')
const removingCaseId = ref(null)
const addingCaseId = ref(null)
const reordering = ref(false)
const runningTest = ref(false)

// 测试环境相关
const environments = ref([])
const loadingEnvironments = ref(false)
const showEnvironmentDialog = ref(false)
const selectedEnvironmentId = ref(null)

// 运行结果相关
const runResult = ref(null)
const showResultDialog = ref(false)

// 标签页相关
const activeTab = ref('cases')

// 接口列表相关
const interfaces = ref([])
const loadingInterfaces = ref(false)

// 套件详情
const suiteDetail = ref({
  id: null,
  suite_name: '',
  description: '',
  type: '',
  cases: []
})

// 可用用例列表
const availableCases = ref([])
const casePagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

// 计算属性
const filteredAvailableCases = computed(() => {
  if (!searchKeyword.value) return availableCases.value
  return availableCases.value.filter(testCase =>
      testCase.name.toLowerCase().includes(searchKeyword.value.toLowerCase())
  )
})

// 检查用例是否已在套件中
const isCaseInSuite = (caseId) => {
  return suiteDetail.value?.cases?.some(item => item.case_id === caseId) || false
}

// 获取路由参数
const projectId = computed(() => route.params.projectId)
const suiteId = computed(() => route.params.suiteId)

// 方法
const goBack = () => {
  router.go(-1)
}

// 加载套件详情
const loadSuiteDetail = async () => {
  try {
    loading.value = true
    const response = await getSuiteDetail(projectId.value, suiteId.value)
    suiteDetail.value = response.data
  } catch (error) {
    ElMessage.error('加载套件详情失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}

// 获取项目接口列表
const loadProjectInterfaces = async () => {
  try {
    loadingInterfaces.value = true
    const response = await getProjectInterfaces(projectId.value, {
      page: 1,
      page_size: 100 // 获取所有接口用于选择
    })
    console.log('接口列表API响应:', response.data)
    interfaces.value = response.data.interfaces || []
    console.log('设置的接口列表:', interfaces.value)
  } catch (error) {
    console.error('获取接口列表失败:', error)
    ElMessage.error('获取接口列表失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    loadingInterfaces.value = false
  }
}

// 加载可用用例
const loadAvailableCases = async () => {
  try {
    loadingCases.value = true
    const params = {
      page: casePagination.page,
      page_size: casePagination.page_size
    }

    // 添加搜索关键词
    if (searchKeyword.value) {
      params.keyword = searchKeyword.value
    }

    // 添加接口过滤
    if (selectedInterfaceId.value) {
      params.interface_id = selectedInterfaceId.value
    }

    const response = await getProjectTestCases(projectId.value, params)

    // 显示所有用例，不过滤已添加的用例
    availableCases.value = response.data.test_cases

    casePagination.total = response.data.total
  } catch (error) {
    ElMessage.error('加载用例列表失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    loadingCases.value = false
  }
}

// 搜索可用用例
const searchAvailableCases = () => {
  casePagination.page = 1
  loadAvailableCases()
}

// 显示添加用例对话框
const showAddCaseDialog = () => {
  loadAvailableCases()
}

// 添加用例到套件
const addCaseToSuite = async (caseId) => {
  try {
    addingCaseId.value = caseId
    await addCaseToSuiteApi(projectId.value, suiteId.value, caseId)
    ElMessage.success('用例添加成功')
    await loadSuiteDetail()
  } catch (error) {
    ElMessage.error('添加用例失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    addingCaseId.value = null
  }
}

// 从套件移除用例
const removeCaseFromSuite = async (caseItem) => {
  try {
    await ElMessageBox.confirm(
        `确定要从套件中移除用例"${caseItem.case_name}"吗？`,
        '确认移除',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }
    )

    removingCaseId.value = caseItem.case_id
    await removeCaseFromSuiteApi(projectId.value, suiteId.value, caseItem.case_id)

    ElMessage.success('用例移除成功')
    await loadSuiteDetail()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('移除用例失败: ' + (error.response?.data?.detail || error.message))
    }
  } finally {
    removingCaseId.value = null
  }
}

// 处理拖拽结束
const handleDragEnd = async (evt) => {
  if (evt.oldIndex === evt.newIndex) return

  try {
    reordering.value = true
    const caseIds = suiteDetail.value.cases.map(item => item.case_id)
    await reorderSuiteCases(projectId.value, suiteId.value, caseIds)
    ElMessage.success('用例顺序调整成功')
  } catch (error) {
    ElMessage.error('调整用例顺序失败: ' + (error.response?.data?.detail || error.message))
    // 重新加载套件详情以恢复原始顺序
    await loadSuiteDetail()
  } finally {
    reordering.value = false
  }
}

// 新增方法：更新套件基本信息
const updateSuiteInfo = async () => {
  try {
    // 这里应该调用更新套件信息的API
    // await updateSuiteInfo(projectId.value, suiteId.value, {
    //   suite_name: suiteDetail.value.suite_name,
    //   description: suiteDetail.value.description,
    //   type: suiteDetail.value.type
    // })
    ElMessage.success('套件信息更新成功')
  } catch (error) {
    ElMessage.error('更新套件信息失败: ' + (error.response?.data?.detail || error.message))
  }
}

// 加载测试环境列表
const loadTestEnvironments = async () => {
  try {
    loadingEnvironments.value = true
    const response = await getTestEnvironments(projectId.value, {
      page: 1,
      page_size: 100
    })
    environments.value = response.data.environments || []
  } catch (error) {
    ElMessage.error('加载测试环境失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    loadingEnvironments.value = false
  }
}

// 运行套件
const runSuite = async () => {
  try {
    // 检查套件是否有用例
    if (!suiteDetail.value.cases || suiteDetail.value.cases.length === 0) {
      ElMessage.warning('套件中没有用例，无法运行')
      return
    }

    // 加载测试环境
    await loadTestEnvironments()
    
    // 如果没有测试环境，提示用户
    if (environments.value.length === 0) {
      ElMessage.warning('项目中没有可用的测试环境，请先创建测试环境')
      return
    }

    // 显示环境选择对话框
    showEnvironmentDialog.value = true
  } catch (error) {
    ElMessage.error('准备运行套件失败: ' + (error.response?.data?.detail || error.message))
  }
}

// 确认运行套件
const confirmRunSuite = async () => {
  if (!selectedEnvironmentId.value) {
    ElMessage.warning('请选择测试环境')
    return
  }

  try {
    runningTest.value = true
    showEnvironmentDialog.value = false
    
    ElMessage.info(`开始运行套件"${suiteDetail.value.suite_name}"，共 ${suiteDetail.value.cases.length} 个用例`)

    // 调用运行套件的API
    const response = await runTestSuite(projectId.value, {
      suite_id: parseInt(suiteId.value),
      environment_id: selectedEnvironmentId.value
    })

    // 保存运行结果
    runResult.value = response.data
    
    // 显示运行结果
    const summary = response.data.summary
    const successCount = summary.success || 0
    const failedCount = summary.failed || 0
    const errorCount = summary.error || 0
    const totalCount = summary.total || 0
    
    // 根据运行状态显示不同的消息
    if (response.data.status === 'error') {
      ElMessage.error(`套件运行出错！${response.data.error_message || '未知错误'}`)
    } else if (failedCount === 0 && errorCount === 0) {
      ElMessage.success(`套件运行完成！全部 ${totalCount} 个用例执行成功`)
    } else {
      ElMessage.warning(`套件运行完成！${successCount} 个成功，${failedCount} 个失败，${errorCount} 个错误`)
    }
    
    // 显示详细结果对话框
    showResultDialog.value = true
    
    console.log('套件运行结果:', response.data)
  } catch (error) {
    ElMessage.error('运行套件失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    runningTest.value = false
    selectedEnvironmentId.value = null
  }
}

// 取消运行套件
const cancelRunSuite = () => {
  showEnvironmentDialog.value = false
  selectedEnvironmentId.value = null
}

// 格式化日期时间
const formatDateTime = (dateTimeStr) => {
  if (!dateTimeStr) return '-'
  try {
    const date = new Date(dateTimeStr)
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  } catch (error) {
    return dateTimeStr
  }
}

// 格式化持续时间
const formatDuration = (duration) => {
  if (!duration && duration !== 0) return '-'
  if (duration < 1) {
    return `${Math.round(duration * 1000)}ms`
  } else if (duration < 60) {
    return `${duration.toFixed(2)}s`
  } else {
    const minutes = Math.floor(duration / 60)
    const seconds = (duration % 60).toFixed(2)
    return `${minutes}m ${seconds}s`
  }
}

// 获取状态对应的标签类型
const getStatusType = (status) => {
  switch (status) {
    case 'completed':
    case 'success':
    case 'passed':
      return 'success'
    case 'failed':
    case 'failure':
      return 'danger'
    case 'error':
      return 'danger'
    case 'running':
    case 'pending':
      return 'warning'
    case 'skip':
    case 'skipped':
      return 'info'
    default:
      return 'info'
  }
}

// 获取状态对应的中文文本
const getStatusText = (status) => {
  switch (status) {
    case 'completed':
      return '完成'
    case 'success':
    case 'passed':
      return '成功'
    case 'failed':
    case 'failure':
      return '失败'
    case 'error':
      return '错误'
    case 'running':
      return '运行中'
    case 'pending':
      return '等待中'
    case 'skip':
    case 'skipped':
      return '跳过'
    default:
      return status || '未知'
  }
}

// 导出套件
const exportSuite = () => {
  ElMessage.info('导出功能开发中...')
}

// 标签页切换处理
const handleTabChange = (tabName) => {
  activeTab.value = tabName
}

// 处理重跑套件
const handleRerunSuite = (runRecord) => {
  // 设置环境ID并显示运行对话框
  selectedEnvironmentId.value = runRecord.environment_id
  showEnvironmentDialog.value = true
}

// 处理更多操作
const handleMoreAction = async (command) => {
  switch (command) {
    case 'duplicate':
      ElMessage.info('复制套件功能开发中...')
      break
    case 'delete':
      try {
        await ElMessageBox.confirm(
            `确定要删除套件"${suiteDetail.value.suite_name}"吗？此操作不可恢复。`,
            '确认删除',
            {
              confirmButtonText: '确定',
              cancelButtonText: '取消',
              type: 'warning'
            }
        )
        ElMessage.info('删除套件功能开发中...')
      } catch (error) {
        // 用户取消删除
      }
      break
  }
}


// 监听搜索关键词变化
watch(searchKeyword, () => {
  casePagination.page = 1
  loadAvailableCases()
}, {debounce: 300})

// 监听接口选择变化
watch(selectedInterfaceId, () => {
  casePagination.page = 1
  loadAvailableCases()
})

// 生命周期钩子
onMounted(() => {
  loadSuiteDetail()
  loadAvailableCases()
  loadProjectInterfaces()
})
</script>

<style scoped>
/* 全局样式 */
.suite-edit-page {
  padding: 24px;
  background: #f8fafc;
  height: 100vh;
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.suite-edit-page::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
}

/* 现代化页面头部 */
.modern-page-header {
  position: relative;
  z-index: 1;
  margin-bottom: 32px;
}

/* 面包屑导航 */
.breadcrumb-section {
  margin-bottom: 24px;
}

/* 套件信息区域 */
.suite-info-section {
  min-width: 0;
  height: 100%;
  overflow-y: auto;
  overflow-x: hidden;
}

.modern-info-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.3);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1),
  inset 0 1px 0 rgba(255, 255, 255, 0.5);
  overflow: hidden;
  transition: all 0.3s ease;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.card-header {
  padding: 10px 10px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 16px;
}

.title-icon {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 20px;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.title-text h3 {
  margin: 0 0 4px 0;
  font-size: 20px;
  font-weight: 600;
  color: #1a1a1a;
}

.title-text p {
  margin: 0;
  font-size: 14px;
  opacity: 0.8;
}

.card-body {
  padding: 28px;
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
}

/* 现代化表单样式 */
.modern-suite-form {
  margin: 0;
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
  font-size: 14px;
  font-weight: 600;
  color: #374151;
  margin-bottom: 4px;
}

.modern-input,
.modern-select,
.modern-textarea {
  border-radius: 12px;
  border: 2px solid #e5e7eb;
  transition: all 0.3s ease;
}

.modern-input:focus-within,
.modern-select:focus-within,
.modern-textarea:focus-within {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.stats-header h4 {
  margin: 0 0 4px 0;
  font-size: 18px;
  font-weight: 600;
  color: #1a1a1a;
}

.stats-header p {
  margin: 0;
  font-size: 13px;
  color: #666;
  opacity: 0.8;
}

.modern-stat-card.total .stat-icon {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.modern-stat-card.success .stat-icon {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
}

.modern-stat-card.warning .stat-icon {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
}

.modern-stat-card.rate .stat-icon {
  background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
}

.actions-header h4 {
  margin: 0 0 4px 0;
  font-size: 18px;
  font-weight: 600;
  color: #1a1a1a;
}

.actions-header p {
  margin: 0;
  font-size: 13px;
  color: #666;
  opacity: 0.8;
}

.more-dropdown .modern-btn {
  width: 100%;
}

/* 原有样式保持不变 */
.main-content {
  display: flex;
  gap: 20px;
}

.left-panel {
  flex: 0 0 400px;
}

.right-panel {
  flex: 1;
}

.suite-cases-card {
  margin-bottom: 20px;
  margin-top: 10px;
}

.case-count {
  color: #909399;
  font-size: 14px;
  margin-bottom: 15px;
}

.case-list {
  max-height: 400px;
  overflow-y: auto;
}

.case-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  margin-bottom: 8px;
  background: white;
  cursor: move;
  transition: all 0.3s ease;
}

.case-item:hover {
  border-color: #409eff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.1);
}

.case-item.sortable-ghost {
  opacity: 0.5;
}

.case-item.sortable-chosen {
  border-color: #409eff;
}

.case-info h4 {
  margin: 0 0 4px 0;
  font-size: 14px;
  color: #303133;
}

.case-info p {
  margin: 0;
  font-size: 12px;
  color: #909399;
}

.case-actions {
  display: flex;
  gap: 8px;
}

.available-cases-card {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.filter-section {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.filter-section .el-select {
  width: 200px;
}

.filter-section .el-input {
  flex: 1;
}

.cases-table {
  margin-top: 16px;
}

.interface-info {
  font-size: 12px;
  color: #909399;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .content-layout {
    flex-direction: column;
    gap: 16px;
  }

  .left-panel,
  .right-panel {
    flex: none;
    height: 50vh;
    min-height: 400px;
  }

  .filter-controls {
    flex-direction: column;
    gap: 8px;
  }

  .filter-controls .el-select,
  .filter-controls .el-input {
    width: 100%;
  }
}

@media (max-width: 768px) {
  .suite-edit-page {
    padding: 16px;
    height: 100vh;
  }

  .left-panel,
  .right-panel {
    height: 45vh;
    min-height: 300px;
  }

  .form-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }

  .card-header {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }

  .card-actions {
    justify-content: center;
  }

  .suite-tabs :deep(.el-tabs__header) {
    padding: 0 4px;
  }

  .tab-content {
    padding: 12px;
  }
}

.subtitle {
  color: #909399;
  font-size: 14px;
  margin: 0;
}

.back-btn {
  padding: 4px 8px;
  font-size: 14px;
  color: #409eff;
}

.page-content {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.content-layout {
  display: flex;
  gap: 20px;
  height: calc(100vh - 130px);
  overflow: hidden;
}

.left-panel {
  flex: 0.4;
  min-width: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.right-panel {
  flex: 0.6;
  min-width: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.suite-cases-card,
.add-cases-card,
.tabs-card {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.suite-cases-card :deep(.el-card__body),
.add-cases-card :deep(.el-card__body),
.tabs-card :deep(.el-card__body) {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header .title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.card-header .filter-controls {
  display: flex;
  align-items: center;
}

.card-header .count {
  font-size: 14px;
  color: #909399;
  margin-left: 8px;
}

.cases-container {
  flex: 1;
  min-height: 0;
}

.draggable-list {
  padding: 0;
  /*min-height: 100%;*/
}

.case-item {
  border-bottom: 1px solid #ebeef5;
  transition: background-color 0.2s;
}

.case-item:hover {
  background-color: #f5f7fa;
}

.case-content {
  padding: 12px;
}

.case-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.case-info {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.drag-handle {
  cursor: move;
  color: #c0c4cc;
}

.case-name {
  font-size: 14px;
  color: #303133;
  font-weight: 500;
  flex: 1;
}

.order-tag {
  margin-left: 8px;
  flex-shrink: 0;
}

/* 删除按钮样式 - 确保靠右显示 */
.case-header .el-button {
  margin-left: auto;
  flex-shrink: 0;
}

.remove-btn {
  color: #f56c6c;
}

.case-description {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.empty-state {
  padding: 40px 20px;
  text-align: center;
}

/* 标签页容器样式 - 保持布局结构 */
.suite-tabs {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.suite-tabs :deep(.el-tabs__content) {
  flex: 1;
  overflow: hidden;
  padding: 0;
}

.suite-tabs :deep(.el-tab-pane) {
  height: 100%;
  overflow: hidden;
}

.tab-content {
  height: 100%;
  padding: 20px;
  overflow-y: auto;
  overflow-x: hidden;
}

/* Tab标签样式优化 */
.suite-tabs :deep(.el-tabs__item) {
  padding: 12px 20px !important;
  margin: 0 4px !important;
  border-radius: 8px 8px 0 0 !important;
  background: #f8f9fa !important;
  border: 1px solid #e9ecef !important;
  border-bottom: none !important;
  color: #6c757d !important;
  font-weight: 500 !important;
  transition: all 0.3s ease !important;
  position: relative !important;
}

.suite-tabs :deep(.el-tabs__item:hover) {
  background: #e9ecef !important;
  color: #495057 !important;
  transform: translateY(-1px) !important;
}

.suite-tabs :deep(.el-tabs__item.is-active) {
  background: #ffffff !important;
  color: #7a37ff !important;
  border-color:#7a37ff !important;
  box-shadow: 0 -2px 8px rgba(0, 123, 255, 0.15) !important;
  z-index: 1 !important;
}

.suite-tabs :deep(.el-tabs__active-bar) {
  display: none !important;
}

.suite-tabs :deep(.el-tabs__nav-wrap::after) {
  background: #e9ecef !important;
  height: 1px !important;
}

.tab-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  white-space: nowrap;
}

.tab-label .el-icon {
  font-size: 16px;
}
/* 筛选控制栏样式 */
.filter-controls {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  flex-shrink: 0;
}

.filter-controls .el-select {
  width: 300px;
}

.filter-controls .el-input {
  width: 250px;
}

/* 右侧添加用例面板样式 */

.search-input {
  width: 100%;
}

.available-cases {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.cases-table {
  flex: 1;
  overflow: hidden;
  min-height: 0;
}

.cases-table :deep(.el-table) {
  height: 100%;
}

.cases-table :deep(.el-table__body-wrapper) {
  overflow-y: auto;
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 200px;
}

.pagination-section {
  margin-top: 16px;
  text-align: center;
  padding: 16px 20px;
  border-top: 1px solid #ebeef5;
  flex-shrink: 0;
  background: #fff;
}

/* 用例名称单元格样式 */
.case-name-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.suite-tag {
  flex-shrink: 0;
}

/* 运行套件按钮样式 */
.card-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.run-suite-btn {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  border: none;
  border-radius: 10px;
  padding: 10px 20px;
  font-weight: 600;
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
  transition: all 0.3s ease;
}

.run-suite-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(16, 185, 129, 0.4);
}

.run-suite-btn:active {
  transform: translateY(0);
}

/* 环境选择卡片样式 */
.environment-cards {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.environment-card {
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  background: #ffffff;
  position: relative;
  overflow: hidden;
}

.environment-card:hover {
  border-color: #3b82f6;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
  transform: translateY(-2px);
}

.environment-card:active {
  transform: translateY(0);
  transition: transform 0.1s ease;
}

.environment-card.selected {
  border-color: #3b82f6;
  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
  box-shadow: 0 4px 16px rgba(59, 130, 246, 0.2);
  transform: translateY(-1px);
}

.environment-card.selected::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
  background: linear-gradient(180deg, #3b82f6 0%, #1d4ed8 100%);
}

.environment-card.selected::after {
  content: '';
  position: absolute;
  top: 0;
  right: 0;
  width: 0;
  height: 0;
  border-left: 20px solid transparent;
  border-top: 20px solid #3b82f6;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 8px;
}

.env-name {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 4px;
  transition: color 0.2s ease;
}

.environment-card.selected .env-name {
  color: #1e40af;
}

.card-actions {
  display: flex;
  align-items: center;
  gap: 12px;
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
  background: #ffffff;
  position: relative;
}

.radio-indicator.checked {
  border-color: #3b82f6;
  background: #3b82f6;
  color: #ffffff;
  animation: checkPulse 0.3s ease-out;
}

@keyframes checkPulse {
  0% {
    transform: scale(0.8);
  }
  50% {
    transform: scale(1.1);
  }
  100% {
    transform: scale(1);
  }
}

.env-url {
  font-size: 13px;
  color: #6b7280;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  background: #f9fafb;
  padding: 6px 10px;
  border-radius: 6px;
  margin-bottom: 8px;
  border: 1px solid #e5e7eb;
  transition: all 0.2s ease;
  word-break: break-all;
}

.environment-card:hover .env-url {
  background: #f3f4f6;
  border-color: #d1d5db;
}

.environment-card.selected .env-url {
  background: rgba(255, 255, 255, 0.9);
  border-color: #bfdbfe;
  color: #1e40af;
}

.env-description {
  font-size: 12px;
  color: #9ca3af;
  line-height: 1.4;
  transition: color 0.2s ease;
}

.environment-card.selected .env-description {
  color: #6b7280;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .environment-card {
    padding: 12px;
  }
  
  .env-name {
    font-size: 14px;
  }
  
  .env-url {
    font-size: 12px;
    padding: 4px 8px;
  }
}

.run-suite-btn .el-icon {
  margin-right: 6px;
}

/* 标签页样式 */
.tabs-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.tabs-card :deep(.el-card__body) {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 0;
}

.suite-tabs {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.suite-tabs :deep(.el-tabs__content) {
  flex: 1;
  padding: 0;
  overflow: hidden;
}

.suite-tabs :deep(.el-tab-pane) {
  height: 100%;
  overflow: hidden;
}

.tab-label {
  display: flex;
  align-items: center;
  gap: 6px;
}

.tab-content {
  height: 100%;
  padding: 20px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.filter-controls {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
  flex-shrink: 0;
}
</style>