<template>
  <div class="requirement-create-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="breadcrumb-section">
          <el-breadcrumb separator="/">
            <el-breadcrumb-item>
              <router-link to="/function-test/requirement">
                需求管理
              </router-link>
            </el-breadcrumb-item>
            <el-breadcrumb-item>新建需求</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="action-section">
          <el-button @click="handleCancel">
            <el-icon><ArrowLeft /></el-icon>
            返回列表
          </el-button>
        </div>
      </div>
    </div>

    <!-- 创建表单 -->
    <div class="page-content">
      <el-card>
        <template #header>
          <div class="card-header">
            <div class="title-section">
              <h2>新建功能需求</h2>
              <p class="subtitle">创建新的功能需求，为后续测试用例生成提供基础</p>
            </div>
          </div>
        </template>

        <el-form
          ref="createFormRef"
          :model="createForm"
          :rules="createRules"
          label-width="120px"
          label-position="top"
          @submit.prevent="handleSubmit"
        >
          <!-- 基本信息表单 -->
          <div class="form-section">
            <h3 class="section-title">基本信息</h3>
            <div class="form-grid">
              <el-form-item label="需求标题" prop="title" class="title-item">
                <el-input
                  v-model="createForm.title"
                  placeholder="请输入需求标题，简洁明确地描述功能需求"
                  maxlength="200"
                  show-word-limit
                  size="large"
                />
              </el-form-item>

              <el-form-item label="所属模块" prop="module_id">
                <el-select
                  v-model="createForm.module_id"
                  placeholder="选择需求所属的项目模块"
                  size="large"
                  style="width: 100%;"
                >
                  <el-option
                    v-for="module in modules"
                    :key="module.id"
                    :label="module.name"
                    :value="module.id"
                  >
                    <div class="module-option">
                      <span class="module-name">{{ module.name }}</span>
                      <span v-if="module.description" class="module-desc">{{ module.description }}</span>
                    </div>
                  </el-option>
                </el-select>
              </el-form-item>

              <el-form-item label="优先级" prop="priority">
                <el-select
                  v-model="createForm.priority"
                  placeholder="选择需求优先级"
                  size="large"
                  style="width: 100%;"
                >
                  <el-option
                    v-for="(label, value) in availablePriorityLabels"
                    :key="value"
                    :label="label"
                    :value="parseInt(value)"
                  >
                    <div class="priority-option">
                      <el-tag
                        :color="REQUIREMENT_PRIORITY_COLORS[value]"
                        effect="light"
                        size="small"
                      >
                        {{ label }}
                      </el-tag>
                      <span class="priority-desc">{{ getPriorityDescription(parseInt(value)) }}</span>
                    </div>
                  </el-option>
                </el-select>
              </el-form-item>

              <el-form-item label="初始状态" prop="status">
                <el-select
                  v-model="createForm.status"
                  placeholder="选择需求初始状态"
                  size="large"
                  style="width: 100%;"
                >
                  <el-option
                    v-for="(label, value) in availableStatuses"
                    :key="value"
                    :label="label"
                    :value="value"
                  >
                    <div class="status-option">
                      <el-tag
                        :type="getStatusTagType(value)"
                        size="small"
                      >
                        {{ label }}
                      </el-tag>
                      <span class="status-desc">{{ getStatusDescription(value) }}</span>
                    </div>
                  </el-option>
                </el-select>
              </el-form-item>
            </div>
          </div>

          <!-- 描述编辑器 -->
          <div class="form-section">
            <h3 class="section-title">需求描述</h3>
            <el-form-item prop="description">
              <el-input
                v-model="createForm.description"
                type="textarea"
                :rows="12"
                placeholder="请详细描述功能需求，包括：&#10;1. 功能目标和用途&#10;2. 用户场景和使用流程&#10;3. 功能边界和限制条件&#10;4. 预期的输入输出&#10;5. 特殊要求或约束条件&#10;&#10;详细的需求描述有助于生成更准确的测试用例。"
                maxlength="2000"
                show-word-limit
                resize="vertical"
              />
            </el-form-item>
          </div>

          <!-- 操作按钮 -->
          <div class="form-actions">
            <el-button size="large" @click="handleCancel">
              取消
            </el-button>
            <el-button
              type="primary"
              size="large"
              @click="handleSubmit"
              :loading="saving && saveType === 'submit'"
            >
              提交审核
            </el-button>
          </div>
        </el-form>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import {
  createRequirement,
  REQUIREMENT_STATUS_LABELS,
  REQUIREMENT_PRIORITY_LABELS,
  REQUIREMENT_PRIORITY_COLORS,
  REQUIREMENT_STATUS,
  REQUIREMENT_PRIORITY
} from '@/api/functional_test'
import { getProjectModules } from '@/api/project'
import { useProjectStore } from '@/stores'

const router = useRouter()
const route = useRoute()
const projectStore = useProjectStore()

// 响应式数据
const saving = ref(false)
const saveType = ref('')
const modules = ref([])
const createFormRef = ref()

// 创建表单
const createForm = reactive({
  title: '',
  module_id: null,
  description: '',
  priority: REQUIREMENT_PRIORITY.MEDIUM, // 默认中等优先级
  status: REQUIREMENT_STATUS.DRAFT // 默认草稿状态
})

// 表单验证规则
const createRules = {
  title: [
    { required: true, message: '请输入需求标题', trigger: 'blur' },
    { min: 1, max: 200, message: '标题长度在 1 到 200 个字符', trigger: 'blur' }
  ],
  module_id: [
    { required: true, message: '请选择所属模块', trigger: 'change' }
  ],
  priority: [
    { required: true, message: '请选择优先级', trigger: 'change' }
  ],
  status: [
    { required: true, message: '请选择状态', trigger: 'change' }
  ]
}

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

// 可用的初始状态（创建时只能选择草稿或直接提交审核）
const availableStatuses = computed(() => ({
  [REQUIREMENT_STATUS.DRAFT]: REQUIREMENT_STATUS_LABELS[REQUIREMENT_STATUS.DRAFT],
  [REQUIREMENT_STATUS.REVIEWING]: REQUIREMENT_STATUS_LABELS[REQUIREMENT_STATUS.REVIEWING]
}))

// 新增：限制优先级选项为 1-3
const availablePriorityLabels = computed(() => ({
  [REQUIREMENT_PRIORITY.LOW]: REQUIREMENT_PRIORITY_LABELS[REQUIREMENT_PRIORITY.LOW],
  [REQUIREMENT_PRIORITY.MEDIUM]: REQUIREMENT_PRIORITY_LABELS[REQUIREMENT_PRIORITY.MEDIUM],
  [REQUIREMENT_PRIORITY.HIGH]: REQUIREMENT_PRIORITY_LABELS[REQUIREMENT_PRIORITY.HIGH]
}))

// 方法
const getPriorityDescription = (priority) => {
  const descriptions = {
    [REQUIREMENT_PRIORITY.LOW]: '可以延后处理的需求',
    [REQUIREMENT_PRIORITY.MEDIUM]: '正常优先级的需求',
    [REQUIREMENT_PRIORITY.HIGH]: '重要且紧急的需求',
    [REQUIREMENT_PRIORITY.URGENT]: '最高优先级，需立即处理'
  }
  return descriptions[priority] || ''
}

const getStatusDescription = (status) => {
  const descriptions = {
    [REQUIREMENT_STATUS.DRAFT]: '保存为草稿，可继续编辑',
    [REQUIREMENT_STATUS.REVIEWING]: '提交审核，等待批准'
  }
  return descriptions[status] || ''
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

const loadModules = async () => {
  if (!projectId.value) {
    return
  }
  
  try {
    const response = await getProjectModules(projectId.value)
    modules.value = (response.data && response.data.datas) ? response.data.datas : []
    
    // 如果只有一个模块，自动选择
    if (modules.value.length === 1) {
      createForm.module_id = modules.value[0].id
    }
  } catch (error) {
    console.error('加载模块列表失败:', error)
    ElMessage.error('加载模块列表失败')
  }
}

const validateForm = async () => {
  try {
    await createFormRef.value.validate()
    return true
  } catch (error) {
    return false
  }
}

const saveRequirement = async (status) => {
  if (!projectId.value) {
    throw new Error('项目ID不能为空')
  }
  
  const formData = {
    ...createForm,
    status
  }
  
  try {
    const response = await createRequirement(projectId.value, formData)
    return response.data
  } catch (error) {
    console.error('保存需求失败:', error)
    throw error
  }
}

const handleSaveDraft = async () => {
  if (!(await validateForm())) return
  
  saveType.value = 'draft'
  saving.value = true
  
  try {
    await saveRequirement(REQUIREMENT_STATUS.DRAFT)
    ElMessage.success('需求草稿保存成功')
    router.push('/function-test/requirement')
  } catch (error) {
    ElMessage.error('保存草稿失败')
  } finally {
    saving.value = false
    saveType.value = ''
  }
}

const handleSubmit = async () => {
  if (!(await validateForm())) return
  
  // 如果没有填写描述，提醒用户
  if (!createForm.description.trim()) {
    try {
      await ElMessageBox.confirm(
        '您还没有填写需求描述，详细的描述有助于生成更准确的测试用例。确定要继续提交吗？',
        '提示',
        {
          confirmButtonText: '继续提交',
          cancelButtonText: '返回编辑',
          type: 'warning'
        }
      )
    } catch {
      return
    }
  }
  
  saveType.value = 'submit'
  saving.value = true
  
  try {
    const targetStatus = createForm.status === REQUIREMENT_STATUS.DRAFT 
      ? REQUIREMENT_STATUS.DRAFT 
      : REQUIREMENT_STATUS.REVIEWING
      
    await saveRequirement(targetStatus)
    
    const message = targetStatus === REQUIREMENT_STATUS.DRAFT 
      ? '需求创建成功' 
      : '需求已提交审核'
    ElMessage.success(message)
    
    router.push('/function-test/requirement')
  } catch (error) {
    ElMessage.error('提交需求失败')
  } finally {
    saving.value = false
    saveType.value = ''
  }
}

const handleCancel = async () => {
  // 检查是否有未保存的内容
  const hasContent = createForm.title.trim() || createForm.description.trim()
  
  if (hasContent) {
    try {
      await ElMessageBox.confirm(
        '您有未保存的内容，确定要离开吗？',
        '确认离开',
        {
          confirmButtonText: '确定离开',
          cancelButtonText: '继续编辑',
          type: 'warning'
        }
      )
    } catch {
      return
    }
  }
  
  router.push('/function-test/requirement')
}

// 生命周期
onMounted(async () => {
  await loadModules()
})
</script>

<style scoped>
.requirement-create-page {
  padding: 24px;
  background: #f8fafc;
  min-height: 100vh;
}

.page-header {
  margin-bottom: 24px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: white;
  padding: 20px 24px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.breadcrumb-section {
  flex: 1;
}

.action-section {
  display: flex;
  gap: 12px;
}

.page-content {
  background: white;
  border-radius: 8px;
  overflow: hidden;
}

.card-header {
  border-bottom: 1px solid #e5e7eb;
  padding-bottom: 16px;
}

.title-section h2 {
  color: #1f2937;
  margin: 0 0 8px 0;
  font-size: 20px;
  font-weight: 600;
}

.subtitle {
  color: #6b7280;
  margin: 0;
  font-size: 14px;
}

.form-section {
  margin-bottom: 32px;
}

.section-title {
  color: #1f2937;
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 20px 0;
  padding-bottom: 8px;
  border-bottom: 2px solid #8b5cf6;
}

.form-grid {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr;
  gap: 24px;
}

.title-item {
  grid-column: 1 / -1;
}

.module-option,
.priority-option,
.status-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.module-name {
  font-weight: 500;
}

.module-desc,
.priority-desc,
.status-desc {
  font-size: 12px;
  color: #6b7280;
  margin-left: 8px;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 16px;
  padding-top: 24px;
  border-top: 1px solid #e5e7eb;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .form-grid {
    grid-template-columns: 1fr 1fr;
  }
  
  .title-item {
    grid-column: 1 / -1;
  }
}

@media (max-width: 768px) {
  .requirement-create-page {
    padding: 16px;
  }
  
  .header-content {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
  
  .form-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .form-actions {
    flex-direction: column-reverse;
  }
  
  .module-option,
  .priority-option,
  .status-option {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
}

/* Element Plus 样式覆盖 */
:deep(.el-textarea__inner) {
  font-family: inherit;
  line-height: 1.6;
}

:deep(.el-form-item__label) {
  font-weight: 500;
  color: #374151;
}

:deep(.el-input__inner) {
  border-radius: 6px;
}

:deep(.el-select .el-input__inner) {
  border-radius: 6px;
}
</style>