<template>
  <div class="ui-page-management">
    <div class="page-header">
      <h2>页面管理</h2>
      <p class="subtitle">管理UI测试的目标页面（URL + 描述）</p>
    </div>

    <el-card class="content-card">
      <template #header>
        <div class="card-header">
          <span>页面列表</span>
          <el-button type="primary" @click="openCreateDialog">
            <el-icon><Plus /></el-icon>
            新建页面
          </el-button>
        </div>
      </template>

      <el-table :data="pages" v-loading="loading" stripe style="width: 100%">
        <el-table-column prop="name" label="页面名称" min-width="160" />
        <el-table-column prop="url" label="URL" min-width="280">
          <template #default="{ row }">
            <el-link :href="row.url" target="_blank" type="primary">{{ row.url }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column prop="created_at" label="创建时间" width="170">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="openEditDialog(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!loading && pages.length === 0" description="暂无页面，点击右上角新建" />
    </el-card>

    <!-- 新建 / 编辑弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑页面' : '新建页面'"
      width="560px"
      :close-on-click-modal="false"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="页面名称" prop="name">
          <el-input v-model="form.name" placeholder="如：登录页面" />
        </el-form-item>
        <el-form-item label="页面URL" prop="url">
          <el-input v-model="form.url" placeholder="https://example.com/login" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="可选，描述页面功能" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useProjectStore } from '@/stores'
import { getUiPages, createUiPage, updateUiPage, deleteUiPage } from '@/api/uiTest'

const projectStore = useProjectStore()
const projectId = () => projectStore.currentProject?.id

const loading = ref(false)
const pages = ref([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)
const editingId = ref(null)
const formRef = ref()

const form = ref({ name: '', url: '', description: '' })
const rules = {
  name: [{ required: true, message: '请输入页面名称', trigger: 'blur' }],
  url: [{ required: true, message: '请输入页面URL', trigger: 'blur' }],
}

const formatTime = (t) => {
  if (!t) return '-'
  return new Date(t).toLocaleString('zh-CN')
}

const fetchPages = async () => {
  if (!projectId()) return
  loading.value = true
  try {
    const res = await getUiPages(projectId())
    pages.value = res.data?.pages || []
  } catch (e) {
    ElMessage.error('获取页面列表失败')
  } finally {
    loading.value = false
  }
}

const openCreateDialog = () => {
  isEdit.value = false
  editingId.value = null
  form.value = { name: '', url: '', description: '' }
  dialogVisible.value = true
}

const openEditDialog = (row) => {
  isEdit.value = true
  editingId.value = row.id
  form.value = { name: row.name, url: row.url, description: row.description || '' }
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate()
  submitting.value = true
  try {
    if (isEdit.value) {
      await updateUiPage(projectId(), editingId.value, form.value)
      ElMessage.success('更新成功')
    } else {
      await createUiPage(projectId(), form.value)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    await fetchPages()
  } catch (e) {
    ElMessage.error(isEdit.value ? '更新失败' : '创建失败')
  } finally {
    submitting.value = false
  }
}

const handleDelete = async (row) => {
  await ElMessageBox.confirm(`确定删除页面 "${row.name}" 吗？`, '确认删除', { type: 'warning' })
  try {
    await deleteUiPage(projectId(), row.id)
    ElMessage.success('删除成功')
    await fetchPages()
  } catch (e) {
    ElMessage.error('删除失败')
  }
}

onMounted(() => fetchPages())
</script>

<style scoped>
.ui-page-management {
  padding: 20px;
}
.page-header { margin-bottom: 20px; }
.page-header h2 { color: #303133; margin: 0 0 8px 0; font-size: 22px; font-weight: 600; }
.subtitle { color: #909399; margin: 0; font-size: 13px; }
.content-card { border: none; box-shadow: 0 2px 12px rgba(0,0,0,0.06); }
.card-header { display: flex; justify-content: space-between; align-items: center; }
</style>
