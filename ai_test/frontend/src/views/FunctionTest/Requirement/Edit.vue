<template>
  <div class="requirement-edit-page">
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
            <el-breadcrumb-item>编辑需求</el-breadcrumb-item>
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

    <!-- 编辑表单 -->
    <div class="page-content" v-loading="loading">
      <el-card>
        <template #header>
          <div class="card-header">
            <div class="title-section">
              <h2>编辑功能需求</h2>
              <p class="subtitle">修改需求信息，更新后将重新进入审核流程</p>
            </div>
          </div>
        </template>

        <el-form
          ref="editFormRef"
          :model="editForm"
          :rules="editRules"
          label-width="120px"
          label-position="top"
          @submit.prevent="handleSubmit"
        >
          <!-- 基本信息表单 -->
          <div class="form-section">
            <h3 class="section-title">基本信息</h3>
            <div class="form-grid">
              <el-form-item label="需求标题" prop="title">
                <el-input
                  v-model="editForm.title"
                  placeholder="请输入需求标题"
                  maxlength="200"
                  show-word-limit
                />
              </el-form-item>

              <el-form-item label="所属模块" prop="module_id">
                <el-select
                  v-model="editForm.module_id"
                  placeholder="请选择所属模块"
                  style="width: 100%"
                >
                  <el-option
                    v-for="module in modules"
                    :key="module.id"
                    :label="module.name"
                    :value="module.id"
                  />
                </el-select>
              </el-form-item>

              <el-form-item label="优先级" prop="priority">
                <el-select
                  v-model="editForm.priority"
                  placeholder="请选择优先级"
                  style="width: 100%"
                >
                  <el-option
                    v-for="(label, value) in REQUIREMENT_PRIORITY_LABELS"
                    :key="value"
                    :label="label"
                    :value="value"
                  >
                    <div class="priority-option">
                      <el-tag
                        :color="REQUIREMENT_PRIORITY_COLORS[value]"
                        effect="light"
                        size="small"
                      >
                        {{ label }}
                      </el-tag>
                    </div>
                  </el-option>
                </el-select>
              </el-form-item>

              <el-form-item label="状态" prop="status">
                <el-select
                  v-model="editForm.status"
                  placeholder="请选择状态"
                  style="width: 100%"
                >
                  <el-option
                    v-for="(label, value) in REQUIREMENT_STATUS_LABELS"
                    :key="value"
                    :label="label"
                    :value="value"
                  >
                    <div class="status-option">
                      <el-tag
                        :type="getStatusTagType(value)"
                        effect="light"
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
                v-model="editForm.description"
                type="textarea"
                :rows="12"
                placeholder="请详细描述功能需求..."
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
              :loading="saving"
            >
              保存修改
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
  getRequirementDetail,
  updateRequirement,
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
const loading = ref(false)
const saving = ref(false)
const modules = ref([])
const editFormRef = ref()

// 编辑表单
const editForm = reactive({
  title: '',
  module_id: null,
  description: '',
  priority: REQUIREMENT_PRIORITY.MEDIUM,
  status: REQUIREMENT_STATUS.DRAFT
})

// 表单验证规则
const editRules = {
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

const requirementId = computed(() => parseInt(route.params.id))

// 方法
const getStatusTagType = (status) => {
  const typeMap = {
    'draft': '',
    'reviewing': 'warning',
    'approved': 'success',
    'rejected': 'danger',
    'archived': 'info'
  }
  return typeMap[status] || ''
}

const getStatusDescription = (status) => {
  const descMap = {
    'draft': '草稿状态，可以继续编辑',
    'reviewing': '审核中，等待审批',
    'approved': '已通过审核',
    'rejected': '审核被拒绝',
    'archived': '已归档'
  }
  return descMap[status] || ''
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

const loadRequirement = async () => {
  if (!projectId.value || !requirementId.value) {
    return
  }
  
  loading.value = true
  try {
    const response = await getRequirementDetail(projectId.value, requirementId.value)
    const requirement = response.data
    
    // 填充表单数据
    editForm.title = requirement.title || ''
    editForm.module_id = requirement.module_id || null
    editForm.description = requirement.description || ''
    editForm.priority = requirement.priority || REQUIREMENT_PRIORITY.MEDIUM
    editForm.status = requirement.status || REQUIREMENT_STATUS.DRAFT
  } catch (error) {
    console.error('加载需求详情失败:', error)
    ElMessage.error('加载需求详情失败')
    router.push('/function-test/requirement')
  } finally {
    loading.value = false
  }
}

const validateForm = async () => {
  if (!editFormRef.value) return false
  
  try {
    await editFormRef.value.validate()
    return true
  } catch (error) {
    return false
  }
}

const handleSubmit = async () => {
  if (!(await validateForm())) return
  
  // 如果没有填写描述，提醒用户
  if (!editForm.description.trim()) {
    try {
      await ElMessageBox.confirm(
        '您还没有填写需求描述，详细的描述有助于生成更准确的测试用例。确定要继续保存吗？',
        '提示',
        {
          confirmButtonText: '继续保存',
          cancelButtonText: '返回编辑',
          type: 'warning'
        }
      )
    } catch {
      return
    }
  }
  
  saving.value = true
  
  try {
    await updateRequirement(projectId.value, requirementId.value, editForm)
    ElMessage.success('需求更新成功')
    router.push('/function-test/requirement')
  } catch (error) {
    console.error('更新需求失败:', error)
    ElMessage.error('更新需求失败')
  } finally {
    saving.value = false
  }
}

const handleCancel = async () => {
  // 检查是否有未保存的修改
  try {
    await ElMessageBox.confirm(
      '您有未保存的修改，确定要离开吗？',
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
  
  router.push('/function-test/requirement')
}

// 生命周期
onMounted(async () => {
  await loadModules()
  await loadRequirement()
})
</script>

<style scoped>
.requirement-edit-page {
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
  padding: 16px 24px;
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
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.title-section h2 {
  color: #1f2937;
  margin: 0 0 8px 0;
  font-size: 20px;
  font-weight: 600;
}

.title-section .subtitle {
  color: #6b7280;
  margin: 0;
  font-size: 14px;
}

.form-section {
  margin-bottom: 32px;
}

.section-title {
  color: #374151;
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 16px 0;
  padding-bottom: 8px;
  border-bottom: 1px solid #e5e7eb;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

.priority-option,
.status-option {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-desc {
  color: #6b7280;
  font-size: 12px;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 24px;
  border-top: 1px solid #e5e7eb;
}

:deep(.el-form-item__label) {
  color: #374151;
  font-weight: 700;
  font-size: 14px;
  line-height: 1.4;
  margin-bottom: 8px;
  letter-spacing: 0.3px;
}

:deep(.el-input__wrapper) {
  border-radius: 6px;
}

:deep(.el-select .el-input__wrapper) {
  border-radius: 6px;
}

:deep(.el-textarea__inner) {
  border-radius: 6px;
  font-family: inherit;
}
</style>