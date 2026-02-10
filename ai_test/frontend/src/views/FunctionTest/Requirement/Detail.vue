<template>
  <div class="requirement-detail-page">
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
            <el-breadcrumb-item>需求详情</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="action-section">
          <el-button @click="handleBack">
            <el-icon><ArrowLeft /></el-icon>
            返回列表
          </el-button>
          <el-button type="primary" @click="handleEdit" :disabled="!canEdit">
            <el-icon><Edit /></el-icon>
            编辑需求
          </el-button>
        </div>
      </div>
    </div>

    <div v-loading="loading" class="page-content">
      <!-- 需求信息卡片 -->
      <div class="requirement-info">
        <el-card>
          <template #header>
            <div class="card-header">
              <div class="title-section">
                <h2>{{ requirement.title }}</h2>
                <div class="meta-info">
                  <span v-if="requirement.doc_no" class="doc-no">编号：{{ requirement.doc_no }}</span>
                  <span class="create-info">
                    创建人：{{ requirement.creator_name || '未知' }} · 
                    {{ formatDate(requirement.created_at) }}
                  </span>
                </div>
              </div>
              <div class="status-section">
                <el-tag
                  :type="getStatusTagType(requirement.status)"
                  size="large"
                >
                  {{ REQUIREMENT_STATUS_LABELS[requirement.status] }}
                </el-tag>
              </div>
            </div>
          </template>

          <div class="requirement-content">
            <div class="info-grid">
              <div class="info-item">
                <label>所属模块</label>
                <span>{{ getModuleName(requirement.module_id) }}</span>
              </div>
              <div class="info-item">
                <label>优先级</label>
                <el-tag
                  :color="REQUIREMENT_PRIORITY_COLORS[requirement.priority]"
                  effect="light"
                >
                  {{ REQUIREMENT_PRIORITY_LABELS[requirement.priority] }}
                </el-tag>
              </div>
              <div class="info-item">
                <label>创建时间</label>
                <span>{{ formatDate(requirement.created_at) }}</span>
              </div>
              <div class="info-item">
                <label>更新时间</label>
                <span>{{ formatDate(requirement.updated_at) }}</span>
              </div>
            </div>

            <div v-if="requirement.description" class="description-section">
              <label>需求描述</label>
              <div class="description-content" v-html="formatDescription(requirement.description)"></div>
            </div>
          </div>
        </el-card>
      </div>

      <!-- 编辑表单 -->
      <div v-if="isEditing" class="edit-form">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>编辑需求</span>
              <div>
                <el-button @click="cancelEdit">取消</el-button>
                <el-button type="primary" @click="saveRequirement" :loading="saving">
                  保存
                </el-button>
              </div>
            </div>
          </template>

          <el-form
            ref="editFormRef"
            :model="editForm"
            :rules="editRules"
            label-width="100px"
            label-position="top"
          >
            <div class="form-grid">
              <el-form-item label="需求标题" prop="title">
                <el-input
                  v-model="editForm.title"
                  placeholder="请输入需求标题"
                  maxlength="200"
                  show-word-limit
                />
              </el-form-item>

              <el-form-item label="优先级" prop="priority">
                <el-select v-model="editForm.priority" placeholder="选择优先级">
                  <el-option
                    v-for="(label, value) in REQUIREMENT_PRIORITY_LABELS"
                    :key="value"
                    :label="label"
                    :value="parseInt(value)"
                  />
                </el-select>
              </el-form-item>

              <el-form-item label="状态" prop="status">
                <el-select v-model="editForm.status" placeholder="选择状态">
                  <el-option
                    v-for="(label, value) in REQUIREMENT_STATUS_LABELS"
                    :key="value"
                    :label="label"
                    :value="value"
                  />
                </el-select>
              </el-form-item>
            </div>

            <el-form-item label="需求描述" prop="description">
              <el-input
                v-model="editForm.description"
                type="textarea"
                :rows="8"
                placeholder="请输入需求详细描述"
                maxlength="2000"
                show-word-limit
              />
            </el-form-item>
          </el-form>
        </el-card>
      </div>

      <!-- 关联用例 -->
      <div class="related-cases">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>关联功能用例</span>
              <div>
                <el-button
                  type="primary"
                  @click="handleGenerateCases"
                  :loading="generating"
                  :disabled="!requirement.id"
                >
                  <el-icon><MagicStick /></el-icon>
                  生成用例
                </el-button>
                <el-button @click="loadRelatedCases">
                  <el-icon><Refresh /></el-icon>
                  刷新
                </el-button>
              </div>
            </div>
          </template>

          <div v-loading="casesLoading" class="cases-content">
            <div v-if="relatedCases.length > 0">
              <el-table :data="relatedCases" stripe>
                <el-table-column prop="case_no" label="用例编号" min-width="150" />
                <el-table-column prop="case_name" label="用例名称" min-width="200" />
                <el-table-column prop="priority" label="优先级" width="100">
                  <template #default="{ row }">
                    <el-tag
                      effect="light"
                      size="small"
                      type="info"
                    >
                      {{ REQUIREMENT_PRIORITY_LABELS[row.priority] }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="status" label="状态" width="100">
                  <template #default="{ row }">
                    <el-tag size="small">{{ row.status }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="created_at" label="创建时间" width="180">
                  <template #default="{ row }">
                    {{ formatDate(row.created_at) }}
                  </template>
                </el-table-column>
                <el-table-column prop="updated_at" label="修改时间" width="180">
                  <template #default="{ row }">
                    {{ formatDate(row.updated_at) }}
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="120">
                  <template #default="{ row }">
                    <el-button
                      plain
                      type="primary"
                      size="small"
                      @click="handleViewCase(row)"
                    >
                      查看
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>
            </div>
            <div v-else class="empty-cases">
              <el-empty description="暂无关联的功能用例">
              </el-empty>
            </div>
          </div>
        </el-card>
      </div>
    </div>
  </div>

  <!-- 用例详情弹框 -->
  <FunctionalCaseDetailModal
    v-model="showCaseDetailModal"
    :case-id="selectedCaseId"
    :project-id="projectId"
  />
</template>

<script setup>
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Edit, MagicStick, Refresh } from '@element-plus/icons-vue'
import {
  getRequirementDetail,
  updateRequirement,
  generateFunctionalCases,
  getFunctionalCasesList,
  REQUIREMENT_STATUS_LABELS,
  REQUIREMENT_PRIORITY_LABELS,
  REQUIREMENT_PRIORITY_COLORS
} from '@/api/functional_test'
import { getProjectModules } from '@/api/project'
import { useProjectStore } from '@/stores'
import FunctionalCaseDetailModal from '../Case/components/FunctionalCaseDetailModal.vue'

const router = useRouter()
const route = useRoute()
const projectStore = useProjectStore()

// 响应式数据
const loading = ref(false)
const saving = ref(false)
const generating = ref(false)
const casesLoading = ref(false)
const isEditing = ref(false)
const requirement = ref({})
const modules = ref([])
const relatedCases = ref([])
const editFormRef = ref()

// 用例详情弹框相关
const showCaseDetailModal = ref(false)
const selectedCaseId = ref(null)

// 编辑表单
const editForm = reactive({
  title: '',
  description: '',
  priority: null,
  status: ''
})

// 表单验证规则
const editRules = {
  title: [
    { required: true, message: '请输入需求标题', trigger: 'blur' },
    { min: 1, max: 200, message: '标题长度在 1 到 200 个字符', trigger: 'blur' }
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

const canEdit = computed(() => {
  // 根据需求状态和用户权限判断是否可编辑
  return requirement.value.status !== 'archived'
})

// 方法
const getModuleName = (moduleId) => {
  if (!moduleId) return '未分配模块'
  if (!Array.isArray(modules.value)) return `模块 ${moduleId}`
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

const formatDescription = (description) => {
  if (!description) return ''
  // 简单的文本格式化，将换行符转换为 <br>
  return description.replace(/\n/g, '<br>')
}

const loadModules = async () => {
  if (!projectId.value) {
    return
  }
  
  try {
    const response = await getProjectModules(projectId.value)
    modules.value = response.data || []
  } catch (error) {
    console.error('加载模块列表失败:', error)
    ElMessage.error('加载模块列表失败')
  }
}

const loadRequirement = async () => {
  if (!projectId.value) {
    return
  }
  
  loading.value = true
  try {
    const response = await getRequirementDetail(projectId.value, requirementId.value)
    requirement.value = response.data || {}
    
    // 初始化编辑表单
    editForm.title = requirement.value.title || ''
    editForm.description = requirement.value.description || ''
    editForm.priority = requirement.value.priority || null
    editForm.status = requirement.value.status || ''
  } catch (error) {
    console.error('加载需求详情失败:', error)
    ElMessage.error('加载需求详情失败')
    router.push('/function-test/requirement')
  } finally {
    loading.value = false
  }
}

const loadRelatedCases = async () => {
  if (!projectId.value) {
    return
  }
  
  casesLoading.value = true
  try {
    const response = await getFunctionalCasesList(projectId.value, {
      requirement_id: requirementId.value
    })
    relatedCases.value = response.data?.cases || []
  } catch (error) {
    console.error('加载相关测试用例失败:', error)
    ElMessage.error('加载相关测试用例失败')
  } finally {
    casesLoading.value = false
  }
}

const handleBack = () => {
  router.push('/function-test/requirement')
}

const handleEdit = () => {
  isEditing.value = true
  nextTick(() => {
    // 滚动到编辑表单
    document.querySelector('.edit-form')?.scrollIntoView({ behavior: 'smooth' })
  })
}

const cancelEdit = () => {
  isEditing.value = false
  // 重置表单数据
  editForm.title = requirement.value.title || ''
  editForm.description = requirement.value.description || ''
  editForm.priority = requirement.value.priority || null
  editForm.status = requirement.value.status || ''
}

const saveRequirement = async () => {
  if (!editFormRef.value) return
  
  if (!projectId.value) {
    ElMessage.error('项目ID无效')
    return
  }
  
  try {
    await editFormRef.value.validate()
    saving.value = true
    
    await updateRequirement(projectId.value, requirementId.value, editForm)
    
    ElMessage.success('需求更新成功')
    isEditing.value = false
    await loadRequirement()
  } catch (error) {
    if (error.message) {
      console.error('更新需求失败:', error)
      ElMessage.error('更新需求失败')
    }
  } finally {
    saving.value = false
  }
}

const handleGenerateCases = async () => {
  if (!projectId.value) {
    ElMessage.error('项目ID无效')
    return
  }
  try {
    // 跳转到用例生成页面
    router.push(`/function-test/case/generate/${requirementId.value}`)
  } catch (error) {
    if (error !== 'cancel') {
      console.error('跳转用例生成页面失败:', error)
    }
  }
}


const handleViewCase = (caseItem) => {
  // 显示用例详情弹框
  selectedCaseId.value = caseItem.id
  showCaseDetailModal.value = true
}

// 生命周期
onMounted(async () => {
  await loadModules()
  await loadRequirement()
  await loadRelatedCases()
})
</script>

<style scoped>
.requirement-detail-page {
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
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.requirement-info,
.edit-form,
.related-cases {
  background: white;
  border-radius: 8px;
  overflow: hidden;
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
  line-height: 1.4;
}

.meta-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 14px;
  color: #6b7280;
}

.doc-no {
  font-weight: 500;
}

.status-section {
  margin-left: 16px;
}

.requirement-content {
  padding-top: 16px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 24px;
  margin-bottom: 32px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.info-item label {
  font-size: 14px;
  font-weight: 500;
  color: #6b7280;
}

.info-item span {
  font-size: 14px;
  color: #1f2937;
}

.description-section {
  border-top: 1px solid #e5e7eb;
  padding-top: 24px;
}

.description-section label {
  display: block;
  font-size: 16px;
  font-weight: 500;
  color: #1f2937;
  margin-bottom: 12px;
}

.description-content {
  font-size: 14px;
  line-height: 1.6;
  color: #374151;
  background: #f9fafb;
  padding: 16px;
  border-radius: 6px;
  border-left: 4px solid #8b5cf6;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 200px 200px;
  gap: 24px;
  margin-bottom: 24px;
}

.cases-content {
  min-height: 200px;
}

.cases-content .el-table {
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.cases-content .el-table th {
  background-color: #f8fafc;
  color: #374151;
  font-weight: 600;
  border-bottom: 2px solid #e5e7eb;
}

.cases-content .el-table td {
  padding: 12px 8px;
  border-bottom: 1px solid #f3f4f6;
}

.cases-content .el-table tr:hover td {
  background-color: #f8fafc;
}

.cases-content .el-table .el-tag {
  font-weight: 500;
}

.cases-content .el-table .el-button--link {
  font-weight: 500;
  padding: 4px 8px;
}

.empty-cases {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 200px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .requirement-detail-page {
    padding: 16px;
  }
  
  .header-content {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
  
  .card-header {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
  
  .info-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .form-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }
}
</style>