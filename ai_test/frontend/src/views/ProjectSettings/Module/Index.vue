<template>
  <div class="module-management">
    <div class="page-header">
      <h1>模块管理</h1>
      <p>管理项目中的功能模块</p>
    </div>

    <!-- 操作栏 -->
    <div class="action-bar">
      <el-button type="primary" @click="handleCreate" :loading="loading">
        <el-icon><Plus /></el-icon>
        新建模块
      </el-button>
      <el-button @click="refreshModules" :loading="loading">
        <el-icon><Refresh /></el-icon>
        刷新
      </el-button>
    </div>

    <!-- 模块列表 -->
    <div class="module-card">
      <el-table 
        :data="modules" 
        v-loading="loading"
        empty-text="暂无模块数据"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="模块名称" min-width="150" />
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
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
            <el-button type="primary" size="small" @click="handleEdit(row)">
              <el-icon><Edit /></el-icon>
              编辑
            </el-button>
            <el-button type="danger" size="small" @click="handleDelete(row)">
              <el-icon><Delete /></el-icon>
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 新增/编辑弹窗 -->
    <el-dialog 
      :title="dialogTitle" 
      v-model="dialogVisible" 
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form 
        ref="formRef" 
        :model="formData" 
        :rules="formRules" 
        label-width="80px"
      >
        <el-form-item label="模块名称" prop="name">
          <el-input 
            v-model="formData.name" 
            placeholder="请输入模块名称"
            maxlength="100"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="模块描述" prop="description">
          <el-input 
            v-model="formData.description" 
            type="textarea" 
            :rows="4"
            placeholder="请输入模块描述"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button  @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitLoading">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRoute } from 'vue-router'
import { useProjectStore } from '@/stores'
import { getProjectModules, createProjectModule, updateProjectModule, deleteProjectModule } from '@/api/module'

const route = useRoute()
const projectStore = useProjectStore()

// 从Pinia获取当前选中的项目ID
const projectId = computed(() => {
  return projectStore.currentProject?.id || route.params.projectId || null
})

// 响应式数据
const loading = ref(false)
const submitLoading = ref(false)
const modules = ref([])
const dialogVisible = ref(false)
const dialogTitle = ref('')
const isEdit = ref(false)
const currentModule = ref(null)

// 表单数据
const formRef = ref()
const formData = reactive({
  name: '',
  description: ''
})

// 表单验证规则
const formRules = {
  name: [
    { required: true, message: '请输入模块名称', trigger: 'blur' },
    { min: 1, max: 100, message: '模块名称长度在 1 到 100 个字符', trigger: 'blur' }
  ]
}

// 格式化日期时间
const formatDateTime = (dateTime) => {
  if (!dateTime) return '-'
  return new Date(dateTime).toLocaleString('zh-CN')
}

// 获取模块列表
const fetchModules = async () => {
  if (!projectId.value) {
    ElMessage.error('未找到项目信息，请重新选择项目')
    return
  }
  
  try {
    loading.value = true
    const response = await getProjectModules(projectId.value)
    modules.value = response.data.datas || []
  } catch (error) {
    console.error('获取模块列表失败:', error)
    ElMessage.error(error.response?.data?.detail || '获取模块列表失败')
  } finally {
    loading.value = false
  }
}

// 刷新模块列表
const refreshModules = async () => {
  await fetchModules()
  ElMessage.success('刷新成功')
}

// 重置表单
const resetForm = () => {
  formData.name = ''
  formData.description = ''
  if (formRef.value) {
    formRef.value.resetFields()
  }
}

// 新建模块
const handleCreate = () => {
  isEdit.value = false
  dialogTitle.value = '新建模块'
  resetForm()
  dialogVisible.value = true
}

// 编辑模块
const handleEdit = (row) => {
  isEdit.value = true
  dialogTitle.value = '编辑模块'
  currentModule.value = row
  formData.name = row.name
  formData.description = row.description || ''
  dialogVisible.value = true
}

// 提交表单
const handleSubmit = async () => {
  if (!projectId.value) {
    ElMessage.error('未找到项目信息，请重新选择项目')
    return
  }
  
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    submitLoading.value = true
    
    if (isEdit.value) {
      // 更新模块
      await updateProjectModule(projectId.value, currentModule.value.id, {
        name: formData.name,
        description: formData.description
      })
      ElMessage.success('更新模块成功')
    } else {
      // 创建模块
      await createProjectModule(projectId.value, {
        name: formData.name,
        description: formData.description
      })
      ElMessage.success('创建模块成功')
    }
    
    dialogVisible.value = false
    fetchModules()
  } catch (error) {
    console.error('提交失败:', error)
    ElMessage.error(error.response?.data?.detail || '操作失败')
  } finally {
    submitLoading.value = false
  }
}

// 删除模块
const handleDelete = async (row) => {
  if (!projectId.value) {
    ElMessage.error('未找到项目信息，请重新选择项目')
    return
  }
  
  try {
    await ElMessageBox.confirm(
      `确定要删除模块 "${row.name}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    loading.value = true
    await deleteProjectModule(projectId.value, row.id)
    ElMessage.success('删除模块成功')
    fetchModules()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  } finally {
    loading.value = false
  }
}

// 组件挂载时获取数据
onMounted(() => {
  fetchModules()
})
</script>

<style scoped>
.module-management {
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

.module-card {
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

:deep(.el-button--small) {
  padding: 5px 8px;
  font-size: 12px;
}





 

.subtitle {
  color: #606266;
  margin: 0;
  font-size: 14px;
}

.page-content {
  background: white;
  border-radius: 8px;
  overflow: hidden;
}

.content-card {
  border: none;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.table-container {
  min-height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>