<template>
  <div class="case-detail-modal">
    <el-dialog
      :model-value="modelValue"
      @update:model-value="$emit('update:modelValue', $event)"
      :title="caseDetail?.name || '用例详情'"
      width="70%"
      top="5vh"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
    >
      <div v-if="loading" class="loading-container">
        <el-icon class="is-loading"><Loading /></el-icon>
        <span>加载中...</span>
      </div>
      
      <div v-else-if="caseDetail" class="case-detail-content">
        <!-- 头部信息卡片 -->
        <div class="case-header-card">
          <div class="header-left">
            <div class="case-title">
              <el-icon class="title-icon"><Document /></el-icon>
              <span>{{ caseDetail.case_no }} - {{ caseDetail.case_name }}</span>
            </div>
            <!-- 编辑模式切换 -->
            <div class="edit-controls">
              
              <el-button 
                :type="isEditing ? 'success' : 'primary'" 
                :icon="isEditing ? 'Check' : 'Edit'"
                @click="toggleEdit"
              >
                {{ isEditing ? '保存' : '编辑&执行' }}
              </el-button>
              
              <el-button 
                v-if="isEditing" 
                type="info" 
                icon="Close"
                @click="cancelEdit"
              >
                取消
              </el-button>
            </div>
          </div>
          <div class="header-right">
            <div class="status-tags">
              <el-tag :type="getPriorityType(caseDetail.priority)" size="small">
                {{ getPriorityText(caseDetail.priority) }}
              </el-tag>
              <el-tag :type="getStatusType(caseDetail.status)" size="small">
                {{ getStatusText(caseDetail.status) }}
              </el-tag>
            </div>
            <div class="time-info">
              <div class="time-item">
                <el-icon><Clock /></el-icon>
                <span>创建：{{ formatDate(caseDetail.created_at) }}</span>
              </div>
              <div class="time-item">
                <el-icon><Refresh /></el-icon>
                <span>更新：{{ formatDate(caseDetail.updated_at) }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 测试要素网格布局 -->
        <div class="test-elements-grid">
          <!-- 1. 用例标题 -->
          <div class="element-card">
            <div class="element-header">
              <el-icon class="element-icon"><Document /></el-icon>
              <h4>用例标题</h4>
            </div>
            <div class="element-content">
              <el-input
                v-if="isEditing"
                v-model="editForm.case_name"
                placeholder="请输入用例标题"
                type="textarea"
                :rows="2"
              />
              <div v-else class="content-text">{{ caseDetail.case_name || '暂无标题' }}</div>
            </div>
          </div>

          <!-- 2. 前置条件 -->
          <div class="element-card preconditions-card">
            <div class="element-header">
              <el-icon class="element-icon"><Setting /></el-icon>
              <h4>前置条件</h4>
              <div v-if="isEditing" class="header-actions">
                <el-button size="small" type="primary" @click="formatPreconditions">
                  <el-icon><Document /></el-icon>
                  格式化
                </el-button>
                <el-button size="small" @click="clearPreconditions">
                  <el-icon><Delete /></el-icon>
                  清空
                </el-button>
              </div>
            </div>
            <div class="element-content">
              <div v-if="isEditing" class="preconditions-editor">
                <div class="editor-toolbar">
                  <div class="toolbar-left">
                    <el-icon class="toolbar-icon"><Edit /></el-icon>
                    <span class="toolbar-label">前置条件编辑</span>
                  </div>
                  <div class="toolbar-right">
                    <el-tag size="small" type="info">支持Markdown格式</el-tag>
                  </div>
                </div>
                <div class="editor-wrapper">
                  <el-input
                    v-model="editForm.preconditions"
                    placeholder="请输入前置条件，支持以下格式：&#10;1. 用户已登录系统&#10;2. 已完成基础数据配置&#10;3. 测试环境已准备就绪&#10;&#10;可以使用Markdown语法进行格式化"
                    type="textarea"
                    :rows="6"
                    class="preconditions-textarea"
                    resize="vertical"
                    show-word-limit
                    maxlength="1000"
                  />
                </div>
                <div class="editor-tips">
                  <el-icon class="tip-icon"><InfoFilled /></el-icon>
                  <span>提示：详细的前置条件有助于测试执行的准确性</span>
                </div>
              </div>
              <div v-else-if="caseDetail.preconditions" class="preconditions-display">
                <div class="content-wrapper">
                  <div class="content-text">{{ caseDetail.preconditions }}</div>
                </div>
              </div>
              <div v-else class="empty-content">
                <el-icon><Warning /></el-icon>
                <span>暂无前置条件</span>
              </div>
            </div>
          </div>
          <!-- 4. 测试数据 -->
          <div class="element-card">
            <div class="element-header">
              <el-icon class="element-icon"><DataBoard /></el-icon>
              <h4>测试数据</h4>
            </div>
            <div class="element-content">
              <el-input
                v-if="isEditing"
                v-model="editForm.test_data_text"
                placeholder="请输入测试数据（JSON格式）"
                type="textarea"
                :rows="6"
              />
              <div v-else-if="caseDetail.test_data" class="data-content">
                <el-scrollbar max-height="200px">
                  <pre class="data-json">{{ JSON.stringify(caseDetail.test_data, null, 2) }}</pre>
                </el-scrollbar>
              </div>
              <div v-else class="empty-content">
                <el-icon><Warning /></el-icon>
                <span>暂无测试数据</span>
              </div>
            </div>
          </div>

          <!-- 3. 测试步骤 - 参考禅道布局 -->
          <div class="element-card full-width">
            <div class="element-header">
              <el-icon class="element-icon"><List /></el-icon>
              <h4>测试步骤</h4>
              <el-button 
                v-if="isEditing" 
                type="primary" 
                size="small" 
                icon="Plus"
                @click="addTestStep"
              >
                添加步骤
              </el-button>
            </div>
            <div class="element-content">
              <div v-if="(isEditing ? editForm.test_steps : caseDetail.test_steps) && (isEditing ? editForm.test_steps : caseDetail.test_steps).length > 0" class="steps-table">
                <!-- 表格头部 -->
                <div class="steps-header">
                  <div class="step-col step-number-col">步骤</div>
                  <div class="step-col step-action-col">操作步骤</div>
                  <div v-if="isEditing" class="step-col step-actions-col">操作</div>
                </div>
                
                <!-- 步骤内容 -->
                <div class="steps-body">
                  <div 
                    v-for="(step, index) in (isEditing ? editForm.test_steps : caseDetail.test_steps)" 
                    :key="index" 
                    class="step-row"
                  >
                    <div class="step-col step-number-col">
                      <div class="step-number">{{ index + 1 }}</div>
                    </div>
                    <div class="step-col step-action-col">
                      <el-input
                        v-if="isEditing"
                        v-model="step.action"
                        placeholder="请输入操作步骤"
                        type="textarea"
                        :rows="2"
                        resize="none"
                      />
                      <div v-else class="step-content">{{ step.action || '无' }}</div>
                    </div>
                    <div v-if="isEditing" class="step-col step-actions-col">
                      <el-button 
                        type="danger" 
                        size="small" 
                        icon="Delete"
                        @click="removeTestStep(index)"
                        :disabled="editForm.test_steps.length <= 1"
                      >
                        删除
                      </el-button>
                    </div>
                  </div>
                </div>
              </div>
              <div v-else class="empty-content">
                <el-icon><Warning /></el-icon>
                <span>暂无测试步骤</span>
              </div>
            </div>
          </div>

          

          <!-- 5. 预期结果 -->
          <div class="element-card">
            <div class="element-header">
              <el-icon class="element-icon"><Check /></el-icon>
              <h4>预期结果</h4>
            </div>
            <div class="element-content">
              <el-input
                v-if="isEditing"
                v-model="editForm.expected_result"
                placeholder="请输入预期结果"
                type="textarea"
                :rows="4"
              />
              <div v-else-if="caseDetail.expected_result" class="content-text">{{ caseDetail.expected_result }}</div>
              <div v-else class="empty-content">
                <el-icon><Warning /></el-icon>
                <span>暂无预期结果</span>
              </div>
            </div>
          </div>

          <!-- 6. 实际结果 -->
          <div class="element-card">
            <div class="element-header">
              <el-icon class="element-icon"><View /></el-icon>
              <h4>实际结果</h4>
            </div>
            <div class="element-content">
              <el-input
                v-if="isEditing"
                v-model="editForm.actual_result"
                placeholder="请输入实际结果"
                type="textarea"
                :rows="4"
              />
              <div v-else-if="caseDetail.actual_result" class="content-text">{{ caseDetail.actual_result }}</div>
              <div v-else class="empty-content">
                <el-icon><Warning /></el-icon>
                <span>暂未执行</span>
              </div>
            </div>
          </div>

          <!-- 7. 执行结果 -->
          <div class="element-card">
            <div class="element-header">
              <el-icon class="element-icon"><CircleCheck /></el-icon>
              <h4>执行结果</h4>
            </div>
            <div class="element-content">
               <div v-if="isEditing" class="execution-result-edit">
                 <div class="status-selector">
                   <div class="status-label">选择用例状态</div>
                   <div class="status-cards-container">
                     <div 
                       v-for="status in statusOptions" 
                       :key="status.value"
                       class="status-card"
                       :class="{ 'active': editForm.status === status.value }"
                       @click="editForm.status = status.value"
                     >
                       <div class="status-icon" :class="status.iconClass">
                         <i :class="status.icon"></i>
                       </div>
                       <div class="status-info">
                         <div class="status-title">{{ status.label }}</div>
                         <div class="status-desc">{{ status.description }}</div>
                       </div>
                       <div class="status-check" v-if="editForm.status === status.value">
                         <el-icon><Check /></el-icon>
                       </div>
                     </div>
                   </div>
                 </div>
               </div>
               <el-tag 
                 v-else
                 :type="getStatusType(caseDetail.status)" 
                 size="large"
               >
                 {{ getStatusText(caseDetail.status) }}
               </el-tag>
             </div>
          </div>

          <!-- 8. 备注说明 -->
          <div class="element-card">
            <div class="element-header">
              <el-icon class="element-icon"><EditPen /></el-icon>
              <h4>备注说明</h4>
            </div>
            <div class="element-content">
              <el-input
                v-if="isEditing"
                v-model="editForm.remark"
                placeholder="请输入备注说明"
                type="textarea"
                :rows="3"
              />
              <div v-else-if="caseDetail.remark" class="content-text">{{ caseDetail.remark }}</div>
              <div v-else class="empty-content">
                <el-icon><Warning /></el-icon>
                <span>暂无备注</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { getFunctionalCaseDetail, updateFunctionalCase } from '@/api/functional_test'
import { 
  Loading, 
  Document, 
  Clock, 
  Refresh, 
  Star, 
  Setting, 
  List, 
  DataBoard, 
  Check, 
  View, 
  CircleCheck, 
  EditPen, 
  Warning,
  Edit,
  Plus,
  Delete,
  Close
} from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  caseId: {
    type: Number,
    default: null
  },
  projectId: {
    type: Number,
    required: true
  }
})

const emit = defineEmits(['update:modelValue'])

const visible = ref(false)
const loading = ref(false)
const caseDetail = ref(null)
const isEditing = ref(false)
const editForm = ref({})
const originalData = ref({})

// 状态选项配置
const statusOptions = ref([
  {
    value: 'design',
    label: '待审核',
    description: '用例创建后等待审核',
    icon: 'el-icon-clock',
    iconClass: 'status-pending'
  },
  {
    value: 'pass',
    label: '审核通过',
    description: '用例审核通过，可以执行',
    icon: 'el-icon-check',
    iconClass: 'status-pass'
  },
  {
    value: 'wait',
    label: '待执行',
    description: '用例等待执行',
    icon: 'el-icon-time',
    iconClass: 'status-wait'
  },
  {
    value: 'smoke',
    label: '执行通过',
    description: '用例执行成功',
    icon: 'el-icon-success',
    iconClass: 'status-success'
  },
  {
    value: 'regression',
    label: '执行失败',
    description: '用例执行失败',
    icon: 'el-icon-error',
    iconClass: 'status-error'
  },
  {
    value: 'obsolete',
    label: '已废弃',
    description: '用例已废弃不再使用',
    icon: 'el-icon-delete',
    iconClass: 'status-obsolete'
  }
])

// 监听 modelValue 变化
watch(() => props.modelValue, (newVal) => {
  visible.value = newVal
  if (newVal && props.caseId) {
    loadCaseDetail()
  } else if (!newVal) {
    // 关闭弹框时重置编辑状态
    isEditing.value = false
    editForm.value = {}
  }
})

// 监听 visible 变化
watch(visible, (newVal) => {
  emit('update:modelValue', newVal)
})

// 加载用例详情
const loadCaseDetail = async () => {
  if (!props.caseId || !props.projectId) return
  
  loading.value = true
  try {
    const response = await getFunctionalCaseDetail(props.projectId, props.caseId)
    caseDetail.value = response.data
    // 保存原始数据用于取消编辑时恢复
    originalData.value = JSON.parse(JSON.stringify(caseDetail.value))
  } catch (error) {
    console.error('获取用例详情失败:', error)
    ElMessage.error('获取用例详情失败')
  } finally {
    loading.value = false
  }
}

// 关闭弹框
const handleClose = () => {
  visible.value = false
  caseDetail.value = null
}

// 切换编辑模式
const toggleEdit = async () => {
  if (isEditing.value) {
    // 保存数据
    await saveCase()
  } else {
    // 进入编辑模式
    enterEditMode()
  }
}

// 进入编辑模式
const enterEditMode = () => {
  isEditing.value = true
  editForm.value = {
    case_name: caseDetail.value.case_name,
    preconditions: caseDetail.value.preconditions,
    test_steps: JSON.parse(JSON.stringify(caseDetail.value.test_steps || [])),
    test_data_text: caseDetail.value.test_data ? JSON.stringify(caseDetail.value.test_data, null, 2) : '',
    expected_result: caseDetail.value.expected_result,
    actual_result: caseDetail.value.actual_result,
    remark: caseDetail.value.remark,
    status: caseDetail.value.status // 添加状态字段
  }
}

// 取消编辑
const cancelEdit = () => {
  isEditing.value = false
  editForm.value = {}
  // 恢复原始数据
  caseDetail.value = JSON.parse(JSON.stringify(originalData.value))
  ElMessage.info('已取消编辑')
}

// 保存用例
const saveCase = async () => {
  try {
    // 验证数据
    if (!editForm.value.case_name?.trim()) {
      ElMessage.error('用例标题不能为空')
      return
    }

    // 处理测试数据JSON格式
    let testData = null
    if (editForm.value.test_data_text?.trim()) {
      try {
        testData = JSON.parse(editForm.value.test_data_text)
      } catch (error) {
        ElMessage.error('测试数据格式不正确，请输入有效的JSON格式')
        return
      }
    }

    // 准备更新数据
    const updateData = {
      case_name: editForm.value.case_name,
      preconditions: editForm.value.preconditions,
      test_steps: editForm.value.test_steps,
      test_data: testData,
      expected_result: editForm.value.expected_result,
      actual_result: editForm.value.actual_result,
      remark: editForm.value.remark,
      status: editForm.value.status // 包含状态更新
    }

    // 调用API更新用例
    loading.value = true
    const response = await updateFunctionalCase(props.projectId, props.caseId, updateData)

    // 更新本地数据
    caseDetail.value = {
      ...caseDetail.value,
      ...response.data,
      updated_at: new Date().toISOString()
    }

    // 更新原始数据
    originalData.value = JSON.parse(JSON.stringify(caseDetail.value))
    
    isEditing.value = false
    editForm.value = {}
    ElMessage.success('保存成功')
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error('保存失败，请重试')
  } finally {
    loading.value = false
  }
}

// 添加测试步骤
const addTestStep = () => {
  if (!editForm.value.test_steps) {
    editForm.value.test_steps = []
  }
  editForm.value.test_steps.push({
    action: '',
    expected: ''
  })
}

// 删除测试步骤
const removeTestStep = (index) => {
  if (editForm.value.test_steps.length > 1) {
    editForm.value.test_steps.splice(index, 1)
  }
}

// 获取优先级类型
const getPriorityType = (priority) => {
  const types = {
    1: 'danger',   // P0
    2: 'warning',  // P1
    3: 'primary',  // P2
    4: 'info'      // P3
  }
  return types[priority] || 'info'
}

// 获取优先级文本
const getPriorityText = (priority) => {
  const texts = {
    1: 'P0',
    2: 'P1',
    3: 'P2',
    4: 'P3'
  }
  return texts[priority] || 'P3'
}

// 获取状态类型
const getStatusType = (status) => {
  const types = {
    'design': 'info',
    'ready': 'success',
    'wait':"info",
    'smoke': 'warning',
    'regression': 'primary',
    'obsolete': 'danger'
  }
  return types[status] || 'info'
}

// 获取状态文本
const getStatusText = (status) => {
  const texts = {
    'design': '待审核',
    'pass': '审核通过',
    'wait':"待执行",
    'smoke': '执行通过',
    'regression': '执行失败',
    'obsolete': '已废弃'
  }
  return texts[status] || status
}

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return '无'
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// 获取执行结果类型
const getExecutionResultType = (actualResult) => {
  if (!actualResult || actualResult === '暂未执行') return 'info'
  if (actualResult.includes('通过') || actualResult.includes('成功')) return 'success'
  if (actualResult.includes('失败') || actualResult.includes('错误')) return 'danger'
  return 'warning'
}

// 获取执行结果文本
const getExecutionResultText = (actualResult) => {
  if (!actualResult || actualResult === '暂未执行') return '未执行'
  if (actualResult.includes('通过') || actualResult.includes('成功')) return '通过'
  if (actualResult.includes('失败') || actualResult.includes('错误')) return '失败'
  return '待确认'
}

// 格式化前置条件
const formatPreconditions = () => {
  if (!editForm.value.preconditions) return
  
  // 简单的格式化：添加适当的换行和缩进
  let formatted = editForm.value.preconditions
    .replace(/([。！？])/g, '$1\n')  // 在句号、感叹号、问号后换行
    .replace(/(\d+[\.、])/g, '\n$1')  // 在数字列表前换行
    .replace(/([：:])/g, '$1\n  ')   // 在冒号后换行并缩进
    .replace(/\n\s*\n/g, '\n')       // 移除多余的空行
    .trim()
  
  editForm.value.preconditions = formatted
  ElMessage.success('前置条件已格式化')
}

// 清空前置条件
const clearPreconditions = () => {
  ElMessageBox.confirm(
    '确定要清空前置条件内容吗？',
    '确认清空',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(() => {
    editForm.value.preconditions = ''
    ElMessage.success('前置条件已清空')
  }).catch(() => {
    // 用户取消操作
  })
}

</script>

<style scoped>
/* 弹框整体样式 */
.case-detail-modal {
  --primary-color: #409eff;
  --success-color: #67c23a;
  --warning-color: #e6a23c;
  --danger-color: #f56c6c;
  --info-color: #909399;
  --border-radius: 12px;
  --shadow-light: 0 2px 12px rgba(0, 0, 0, 0.1);
  --shadow-medium: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.case-detail-modal :deep(.el-dialog) {
  border-radius: var(--border-radius);
  overflow: hidden;
}

.case-detail-modal :deep(.el-dialog__header) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 20px 24px;
  border-bottom: none;
}

.case-detail-modal :deep(.el-dialog__title) {
  font-size: 18px;
  font-weight: 600;
  color: white;
}

.case-detail-modal :deep(.el-dialog__headerbtn .el-dialog__close) {
  color: white;
  font-size: 20px;
}

.case-detail-modal :deep(.el-dialog__body) {
  padding: 0;
  max-height: 80vh;
  overflow-y: auto;
}

/* 加载状态 */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: var(--info-color);
}

.loading-container .el-icon {
  font-size: 32px;
  margin-bottom: 16px;
}

/* 用例详情内容 */
.case-detail-content {
  padding: 24px;
  background: #f8fafc;
}

/* 头部信息卡片 */
.case-header-card {
  background: white;
  border-radius: var(--border-radius);
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: var(--shadow-light);
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  border-left: 4px solid var(--primary-color);
}

.header-left {
  flex: 1;
}

.case-title {
  display: flex;
  align-items: center;
  font-size: 20px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 8px;
}

.title-icon {
  font-size: 24px;
  color: var(--primary-color);
  margin-right: 12px;
}

.header-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 16px;
}

.status-tags {
  display: flex;
  gap: 8px;
}

.time-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
  font-size: 13px;
  color: #6b7280;
}

.time-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.time-item .el-icon {
  font-size: 14px;
}

/* 编辑控制样式 */
.edit-controls {
  display: flex;
  gap: 12px;
  margin-top: 16px;
  padding: 0;
  background: transparent;
  border-radius: 0;
  box-shadow: none;
}

/* 测试要素网格布局 */
.test-elements-grid {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.element-card {
  background: white;
  border-radius: var(--border-radius);
  overflow: hidden;
  box-shadow: var(--shadow-light);
  transition: all 0.3s ease;
  border: 1px solid #e5e7eb;
}

.element-card:hover {
  box-shadow: var(--shadow-medium);
  transform: translateY(-2px);
}

.element-card.full-width {
  grid-column: 1 / -1;
}

/* 要素卡片头部 */
.element-header {
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  padding: 16px 20px;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
  gap: 12px;
}

.element-icon {
  font-size: 18px;
  color: var(--primary-color);
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.element-header h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #374151;
  line-height: 1.2;
}

/* 要素卡片内容 */
.element-content {
  padding: 20px;
  min-height: 80px;
}

.content-text {
  line-height: 1.6;
  color: #4b5563;
  word-break: break-word;
  white-space: pre-wrap;
}

/* 空内容状态 */
.empty-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: var(--info-color);
  font-style: italic;
  padding: 20px;
}

.empty-content .el-icon {
  font-size: 18px;
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

/* 测试步骤表格样式 */
.steps-table {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
}

.steps-header {
  display: flex;
  background: #f8fafc;
  border-bottom: 2px solid #e5e7eb;
  font-weight: 600;
  color: #374151;
}

.steps-body {
  display: flex;
  flex-direction: column;
}

.step-row {
  display: flex;
  border-bottom: 1px solid #e5e7eb;
}

.step-row:last-child {
  border-bottom: none;
}

.step-col {
  padding: 12px;
  border-right: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
}

.step-col:last-child {
  border-right: none;
}

.step-number-col {
  width: 80px;
  justify-content: center;
}

.step-action-col {
  flex: 2;
}

.step-expected-col {
  flex: 2;
}

.step-actions-col {
  width: 100px;
  justify-content: center;
}

.step-number {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  background: var(--primary-color);
  color: white;
  border-radius: 50%;
  font-size: 14px;
  font-weight: 600;
}

.step-content {
  line-height: 1.5;
  color: #374151;
  word-break: break-word;
  white-space: pre-wrap;
}

/* 测试步骤样式 */
.steps-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.step-item {
  display: flex;
  gap: 16px;
  padding: 16px;
  background: #f8fafc;
  border-radius: 8px;
  border-left: 3px solid var(--primary-color);
  transition: all 0.2s ease;
}

.step-item:hover {
  background: #f1f5f9;
  transform: translateX(4px);
}

.step-details {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.step-action,
.step-expected {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.step-label {
  font-size: 13px;
  font-weight: 600;
  color: #6b7280;
}

.step-text {
  color: #374151;
  line-height: 1.5;
}

/* 测试数据样式 */
.data-content {
  background: #1f2937;
  border-radius: 8px;
  overflow: hidden;
}

.data-json {
  color: #e5e7eb;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
  line-height: 1.5;
  margin: 0;
  padding: 16px;
  background: transparent;
}

/* 滚动条样式 */
:deep(.el-scrollbar__wrap) {
  border-radius: 8px;
}

:deep(.el-scrollbar__bar) {
  border-radius: 4px;
}

/* 标签样式优化 */
.el-tag {
  border-radius: 6px;
  font-weight: 500;
}

/* 前置条件编辑框样式 */
.preconditions-editor {
  position: relative;
}

.editor-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding: 8px 12px;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.toolbar-icon {
  font-size: 14px;
  color: #475569;
  display: flex;
  align-items: center;
}

.toolbar-label {
  font-size: 13px;
  font-weight: 600;
  color: #475569;
  line-height: 1;
}

.format-tag {
  font-size: 11px;
  padding: 2px 6px;
  background: #e0f2fe;
  color: #0369a1;
  border-radius: 4px;
  border: none;
}

.toolbar-actions {
  display: flex;
  gap: 8px;
}

.toolbar-btn {
  padding: 4px 8px;
  font-size: 12px;
  border-radius: 4px;
  border: 1px solid #d1d5db;
  background: white;
  color: #6b7280;
  cursor: pointer;
  transition: all 0.2s ease;
}

.toolbar-btn:hover {
  background: #f3f4f6;
  border-color: #9ca3af;
  color: #374151;
}

.toolbar-btn.format-btn:hover {
  background: #dbeafe;
  border-color: #3b82f6;
  color: #1d4ed8;
}

.toolbar-btn.clear-btn:hover {
  background: #fee2e2;
  border-color: #ef4444;
  color: #dc2626;
}

.preconditions-editor :deep(.el-textarea) {
  border-radius: 8px;
  overflow: hidden;
}

.preconditions-editor :deep(.el-textarea__inner) {
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  padding: 16px;
  font-size: 14px;
  line-height: 1.6;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  transition: all 0.3s ease;
  resize: vertical;
  min-height: 120px;
}

.preconditions-editor :deep(.el-textarea__inner):focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
  outline: none;
}

.preconditions-editor :deep(.el-textarea__inner)::placeholder {
  color: #9ca3af;
  font-style: italic;
}

.editor-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
  padding: 0 4px;
  font-size: 12px;
  color: #6b7280;
}

.char-count {
  color: #9ca3af;
}

.char-count.warning {
  color: #f59e0b;
}

.char-count.danger {
  color: #ef4444;
}

.edit-tips {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #6b7280;
  margin-top: 8px;
  padding: 8px 12px;
  background: #f8fafc;
  border-radius: 6px;
  border-left: 3px solid #3b82f6;
}

.tip-icon {
  font-size: 14px;
  color: #3b82f6;
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.edit-tips span {
  font-size: 12px;
  line-height: 1.4;
}

.preconditions-display {
  position: relative;
}

.content-wrapper {
  padding: 16px;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  min-height: 60px;
  line-height: 1.6;
  color: #374151;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.content-wrapper:empty::before {
  content: "暂无前置条件";
  color: #9ca3af;
  font-style: italic;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .test-elements-grid {
    gap: 16px;
  }
  
  .case-header-card {
    flex-direction: column;
    gap: 20px;
  }
  
  .header-right {
    align-items: flex-start;
    width: 100%;
  }
  
  .status-tags {
    justify-content: flex-start;
  }
}

@media (max-width: 768px) {
  .case-detail-content {
    padding: 16px;
  }
  
  .case-header-card {
    padding: 20px;
  }
  
  .element-content {
    padding: 16px;
  }
  
  .step-item {
    padding: 12px;
  }
  
  .case-detail-modal :deep(.el-dialog) {
    margin: 10px;
    width: calc(100vw - 20px) !important;
  }
}

/* 执行结果编辑区域样式 */
.execution-result-edit {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.current-result {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-selector {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.status-label {
  font-weight: 600;
  color: var(--el-text-color-primary);
  font-size: 16px;
  margin-bottom: 8px;
}

.status-cards-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 12px;
}

.status-card {
  position: relative;
  display: flex;
  align-items: center;
  padding: 16px;
  border: 2px solid var(--el-border-color-light);
  border-radius: 12px;
  background: var(--el-bg-color);
  cursor: pointer;
  transition: all 0.3s ease;
  overflow: hidden;
}

.status-card:hover {
  border-color: var(--el-color-primary-light-5);
  background: var(--el-color-primary-light-9);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.15);
}

.status-card.active {
  border-color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
  box-shadow: 0 4px 16px rgba(64, 158, 255, 0.2);
}

.status-card.active::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
  background: var(--el-color-primary);
}

.status-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  margin-right: 12px;
  font-size: 18px;
}

.status-icon.status-pending {
  background: #fdf6ec;
  color: #e6a23c;
}

.status-icon.status-pass {
  background: #f0f9ff;
  color: #409eff;
}

.status-icon.status-wait {
  background: #fef0f0;
  color: #f56c6c;
}

.status-icon.status-success {
  background: #f0f9f0;
  color: #67c23a;
}

.status-icon.status-error {
  background: #fef0f0;
  color: #f56c6c;
}

.status-icon.status-obsolete {
  background: #f4f4f5;
  color: #909399;
}

.status-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.status-title {
  font-weight: 600;
  color: var(--el-text-color-primary);
  font-size: 14px;
}

.status-desc {
  font-size: 12px;
  color: var(--el-text-color-regular);
  line-height: 1.4;
}

.status-check {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--el-color-primary);
  color: white;
  font-size: 14px;
  margin-left: 8px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .status-cards-container {
    grid-template-columns: 1fr;
  }
  
  .status-card {
    padding: 12px;
  }
  
  .status-icon {
    width: 32px;
    height: 32px;
    font-size: 16px;
  }
}

/* 动画效果 */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.element-card {
  animation: fadeInUp 0.3s ease-out;
}

.element-card:nth-child(1) { animation-delay: 0.1s; }
.element-card:nth-child(2) { animation-delay: 0.2s; }
.element-card:nth-child(3) { animation-delay: 0.3s; }
.element-card:nth-child(4) { animation-delay: 0.4s; }
.element-card:nth-child(5) { animation-delay: 0.5s; }
.element-card:nth-child(6) { animation-delay: 0.6s; }
.element-card:nth-child(7) { animation-delay: 0.7s; }
.element-card:nth-child(8) { animation-delay: 0.8s; }

.case-detail-modal :deep(.el-dialog) {
  border-radius: var(--border-radius);
  overflow: hidden;
}

.case-detail-modal :deep(.el-dialog__header) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 20px 24px;
  border-bottom: none;
}

.case-detail-modal :deep(.el-dialog__title) {
  font-size: 18px;
  font-weight: 600;
  color: white;
}

.case-detail-modal :deep(.el-dialog__headerbtn .el-dialog__close) {
  color: white;
  font-size: 20px;
}

.case-detail-modal :deep(.el-dialog__body) {
  padding: 0;
  max-height: 80vh;
  overflow-y: auto;
}

/* 加载状态 */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: var(--info-color);
}

.loading-container .el-icon {
  font-size: 32px;
  margin-bottom: 16px;
}

/* 用例详情内容 */
.case-detail-content {
  padding: 24px;
  background: #f8fafc;
}

/* 头部信息卡片 */
.case-header-card {
  background: white;
  border-radius: var(--border-radius);
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: var(--shadow-light);
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  border-left: 4px solid var(--primary-color);
}

.header-left {
  flex: 1;
}

.case-title {
  display: flex;
  align-items: center;
  font-size: 20px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 8px;
}

.title-icon {
  font-size: 24px;
  color: var(--primary-color);
  margin-right: 12px;
}

.case-number {
  font-size: 14px;
  color: var(--info-color);
  font-weight: 500;
}

.header-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 16px;
}

.status-tags {
  display: flex;
  gap: 8px;
}

.time-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
  font-size: 13px;
  color: #6b7280;
}

.time-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.time-item .el-icon {
  font-size: 14px;
}

/* 测试要素网格布局 */
.test-elements-grid {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.element-card {
  background: white;
  border-radius: var(--border-radius);
  overflow: hidden;
  box-shadow: var(--shadow-light);
  transition: all 0.3s ease;
  border: 1px solid #e5e7eb;
}

.element-card:hover {
  box-shadow: var(--shadow-medium);
  transform: translateY(-2px);
}

.element-card.full-width {
  grid-column: 1 / -1;
}

/* 要素卡片头部 */
.element-header {
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  padding: 16px 20px;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
  gap: 12px;
}

.element-icon {
  font-size: 18px;
  color: var(--primary-color);
}

.element-header h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #374151;
}

/* 要素卡片内容 */
.element-content {
  padding: 20px;
  min-height: 80px;
}

.content-text {
  line-height: 1.6;
  color: #4b5563;
  word-break: break-word;
  white-space: pre-wrap;
}

/* 空内容状态 */
.empty-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: var(--info-color);
  font-style: italic;
  padding: 20px;
}

.empty-content .el-icon {
  font-size: 18px;
}

/* 测试步骤样式 */
.steps-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.step-item {
  display: flex;
  gap: 16px;
  padding: 16px;
  background: #f8fafc;
  border-radius: 8px;
  border-left: 3px solid var(--primary-color);
  transition: all 0.2s ease;
}

.step-item:hover {
  background: #f1f5f9;
  transform: translateX(4px);
}

.step-number {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: var(--primary-color);
  color: white;
  border-radius: 50%;
  font-size: 14px;
  font-weight: 600;
  flex-shrink: 0;
}

.step-details {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.step-action,
.step-expected {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.step-label {
  font-size: 13px;
  font-weight: 600;
  color: #6b7280;
}

.step-text {
  color: #374151;
  line-height: 1.5;
}

/* 测试数据样式 */
.data-content {
  background: #1f2937;
  border-radius: 8px;
  overflow: hidden;
}

.data-json {
  color: #e5e7eb;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
  line-height: 1.5;
  margin: 0;
  padding: 16px;
  background: transparent;
}

/* 滚动条样式 */
:deep(.el-scrollbar__wrap) {
  border-radius: 8px;
}

:deep(.el-scrollbar__bar) {
  border-radius: 4px;
}

/* 标签样式优化 */
.el-tag {
  border-radius: 6px;
  font-weight: 500;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .test-elements-grid {
    gap: 16px;
  }
  
  .case-header-card {
    flex-direction: column;
    gap: 20px;
  }
  
  .header-right {
    align-items: flex-start;
    width: 100%;
  }
  
  .status-tags {
    justify-content: flex-start;
  }
}

@media (max-width: 768px) {
  .case-detail-content {
    padding: 16px;
  }
  
  .case-header-card {
    padding: 20px;
  }
  
  .element-content {
    padding: 16px;
  }
  
  .step-item {
    padding: 12px;
  }
  
  .case-detail-modal :deep(.el-dialog) {
    margin: 10px;
    width: calc(100vw - 20px) !important;
  }
}

/* 动画效果 */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.element-card {
  animation: fadeInUp 0.3s ease-out;
}

.element-card:nth-child(1) { animation-delay: 0.1s; }
.element-card:nth-child(2) { animation-delay: 0.2s; }
.element-card:nth-child(3) { animation-delay: 0.3s; }
.element-card:nth-child(4) { animation-delay: 0.4s; }
.element-card:nth-child(5) { animation-delay: 0.5s; }
.element-card:nth-child(6) { animation-delay: 0.6s; }
.element-card:nth-child(7) { animation-delay: 0.7s; }
.element-card:nth-child(8) { animation-delay: 0.8s; }
</style>