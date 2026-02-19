<template>
  <div class="environment-management">
    <div class="page-header">
      <h1>测试环境</h1>
      <p>管理项目中的测试环境配置</p>
    </div>

    <!-- 操作栏 -->
    <div class="action-bar">
      <el-button type="primary" @click="handleCreate" :loading="loading">
        <el-icon><Plus /></el-icon>
        新建环境
      </el-button>
      <el-button @click="refreshEnvironments" :loading="loading">
        <el-icon><Refresh /></el-icon>
        刷新
      </el-button>
    </div>

    <!-- 测试环境列表 -->
    <div class="environment-card">
      <el-table 
        :data="environments" 
        v-loading="loading"
        empty-text="暂无环境数据"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="环境名称" min-width="150" />
        
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="updated_at" label="更新时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.updated_at) }}
          </template>
        </el-table-column>
         <el-table-column label="操作" width="180" fixed="right">
           <template #default="{ row }">
             <el-button 
               type="primary" 
               size="small" 
               @click="handleEdit(row)"
               :loading="loading"
             >
               <el-icon><Edit /></el-icon>
               编辑
             </el-button>
             <el-button 
               type="danger" 
               size="small" 
               @click="handleDelete(row)"
               :loading="loading"
             >
               <el-icon><Delete /></el-icon>
               删除
             </el-button>
           </template>
         </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </div>

    <!-- 新建/编辑环境弹窗 -->
    <el-dialog
      :title="dialogTitle"
      v-model="showDialog"
      width="600px"
      :close-on-click-modal="false"
      @close="resetForm"
    >
      <el-form
        ref="environmentFormRef"
        :model="environmentForm"
        :rules="environmentRules"
        label-width="100px"
        label-position="left"
      >
        <el-form-item label="环境名称" prop="name">
          <el-input
            v-model="environmentForm.name"
            placeholder="请输入环境名称"
            maxlength="100"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="全局函数" prop="func_global">
          <el-input
            v-model="environmentForm.func_global"
            type="textarea"
            :rows="6"
            placeholder="请输入全局函数代码（可选）"
            maxlength="5000"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitLoading">
          {{ isEdit ? '更新' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh, Edit, Delete } from '@element-plus/icons-vue'
import { useProjectStore } from '@/stores'
import { 
  getTestEnvironments, 
  createTestEnvironment, 
  updateTestEnvironment, 
  deleteTestEnvironment 
} from '@/api/test_environment'

const router = useRouter()
const projectStore = useProjectStore()

// 响应式数据
const loading = ref(false)
const submitLoading = ref(false)
const showDialog = ref(false)
const isEdit = ref(false)
const editingEnvironment = ref(null)
const environmentFormRef = ref()

const environments = ref([])
const pagination = ref({
  page: 1,
  page_size: 10,
  total: 0,
  total_pages: 0
})

const environmentForm = reactive({
  name: '',
  func_global: ''
})

// 表单验证规则
const environmentRules = {
  name: [
    { required: true, message: '请输入环境名称', trigger: 'blur' },
    { min: 1, max: 100, message: '环境名称长度在 1 到 100 个字符', trigger: 'blur' }
  ]
}

// 计算属性
const dialogTitle = computed(() => {
  return isEdit.value ? '编辑环境' : '新建环境'
})

// 获取环境列表
const fetchEnvironments = async () => {
  if (!projectStore.currentProject?.id) {
    ElMessage.error('请先选择项目')
    return
  }

  try {
    loading.value = true
    const response = await getTestEnvironments(projectStore.currentProject.id, {
      page: pagination.value.page,
      page_size: pagination.value.page_size
    })
    
    environments.value = response.data.environments || []
    pagination.value = {
      page: response.data.page || 1,
      page_size: response.data.page_size || 10,
      total: response.data.total || 0,
      total_pages: response.data.total_pages || 0
    }
  } catch (error) {
    console.error('获取环境列表失败:', error)
    ElMessage.error('获取环境列表失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

// 刷新环境列表
const refreshEnvironments = async () => {
  await fetchEnvironments()
  ElMessage.success('刷新成功')
}

// 处理分页大小变化
const handleSizeChange = (size) => {
  pagination.value.page_size = size
  pagination.value.page = 1
  fetchEnvironments()
}

// 处理页码变化
const handleCurrentChange = (page) => {
  pagination.value.page = page
  fetchEnvironments()
}

// 新建环境
const handleCreate = () => {
  isEdit.value = false
  editingEnvironment.value = null
  resetForm()
  showDialog.value = true
}

// 编辑环境 - 跳转到编辑页面
const handleEdit = (environment) => {
  if (!environment || !environment.id) {
    ElMessage.error('环境数据无效')
    return
  }
  
  console.log('跳转到编辑页面:', environment.id)
  router.push(`/project-settings/environment/${environment.id}/edit`)
}

// 删除环境
const handleDelete = async (environment) => {
  if (!projectStore.currentProject?.id) {
    ElMessage.error('项目ID不能为空')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要删除环境 "${environment.name}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    loading.value = true
    await deleteTestEnvironment(projectStore.currentProject.id, environment.id)
    ElMessage.success('删除成功')
    await fetchEnvironments()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除环境失败:', error)
      ElMessage.error('删除环境失败，请稍后重试')
    }
  } finally {
    loading.value = false
  }
}

// 提交表单
const handleSubmit = async () => {
  if (!projectStore.currentProject?.id) {
    ElMessage.error('项目ID不能为空')
    return
  }

  try {
    await environmentFormRef.value.validate()
    
    submitLoading.value = true
    
    const formData = {
      name: environmentForm.name,
      func_global: environmentForm.func_global || undefined
    }

    if (isEdit.value) {
      await updateTestEnvironment(
        projectStore.currentProject.id, 
        editingEnvironment.value.id, 
        formData
      )
      ElMessage.success('更新成功')
    } else {
      await createTestEnvironment(projectStore.currentProject.id, formData)
      ElMessage.success('创建成功')
    }

    showDialog.value = false
    await fetchEnvironments()
  } catch (error) {
    console.error('操作失败:', error)
    ElMessage.error('操作失败，请稍后重试')
  } finally {
    submitLoading.value = false
  }
}

// 重置表单
const resetForm = () => {
  environmentForm.name = ''
  environmentForm.func_global = ''
  if (environmentFormRef.value) {
    environmentFormRef.value.clearValidate()
  }
}

// 格式化日期时间
const formatDateTime = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

// 页面加载时获取数据
onMounted(() => {
  fetchEnvironments()
})
</script>

<style scoped>
.environment-management {
  padding: 24px;
  background: #ffffff;
  min-height: 100vh;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h1 {
  color: #1f2937;
  margin: 0 0 8px 0;
  font-size: 28px;
  font-weight: bold;
}

.page-header p {
  color: #6b7280;
  margin: 0;
  font-size: 14px;
}

.action-bar {
  margin-bottom: 20px;
  display: flex;
  gap: 12px;
}

.action-bar .el-button {
  background: #ffffff;
  border: 1px solid #d1d5db;
  color: #374151;
  transition: all 0.3s ease;
}

.action-bar .el-button:hover {
  background: #f9fafb;
  border-color: #9ca3af;
  transform: translateY(-2px);
}

.action-bar .el-button--primary {
  background: linear-gradient(135deg, #8b5cf6, #7c3aed);
  border-color: #8b5cf6;
  color: #ffffff;
}

.action-bar .el-button--primary:hover {
  background: linear-gradient(135deg, #7c3aed, #6d28d9);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.4);
}

.environment-card {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

:deep(.el-table) {
  background: #ffffff;
  color: #1f2937;
}

:deep(.el-table__header-wrapper) {
  background: #f8fafc;
}

:deep(.el-table th) {
  background: #f8fafc;
  color: #374151;
  border-bottom: 1px solid #e5e7eb;
}

:deep(.el-table td) {
  background: #ffffff;
  color: #1f2937;
  border-bottom: 1px solid #f3f4f6;
}

:deep(.el-table__row:hover > td) {
  background: #f9fafb !important;
}

:deep(.el-table__row--striped > td) {
  background: #f9fafb;
}

:deep(.el-table__empty-text) {
  color: #6b7280;
}

.text-placeholder {
  color: #9ca3af;
  font-style: italic;
}

/* 加载状态 */
:deep(.el-loading-mask) {
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(4px);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .environment-management {
    padding: 16px;
  }
  
  .page-header h1 {
    font-size: 24px;
  }
  
  .environment-card {
    padding: 16px;
  }
  
  .action-bar {
    flex-direction: column;
  }
  
  .action-bar .el-button {
    width: 100%;
  }
}
</style>