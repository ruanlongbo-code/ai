<template>
  <div class="db-config-tab">
    <div class="action-bar">
      <el-button type="primary" @click="openCreate">
        <el-icon><Plus /></el-icon>
        新建数据库配置
      </el-button>
    </div>

    <el-table :data="localDatabases" empty-text="暂无数据库配置" style="width: 100%">
      <el-table-column prop="name" label="数据库名称" min-width="160" />
      <el-table-column prop="type" label="数据库类型" width="140" />
      <el-table-column label="配置" min-width="240">
        <template #default="{ row }">
          <span class="config-preview">{{ stringify(row.config) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="180">
        <template #default="{ row }">
          <el-button size="small" @click="openEdit(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="800px">
      <el-form ref="dbFormRef" :model="dbForm" :rules="dbRules" label-width="110px">
        <el-form-item label="数据库名称" prop="name">
          <el-input v-model="dbForm.name" maxlength="100" show-word-limit />
        </el-form-item>
        <el-form-item label="数据库类型" prop="type">
          <el-select v-model="dbForm.type" placeholder="请选择类型">
            <el-option v-for="t in dbTypes" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
        <el-form-item label="配置(JSON)" prop="config">
          <JsonEditor v-model="dbForm.config" height="320px"  />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible=false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSubmit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { createTestEnvironmentDatabase, updateTestEnvironmentDatabase, deleteTestEnvironmentDatabase } from '@/api/test_environment'
import JsonEditor from '@/components/JsonEditor.vue'

const props = defineProps({
  environmentId: { type: Number, required: true },
  databases: { type: Array, default: () => [] }
})
const emit = defineEmits(['update'])

const localDatabases = ref([])
watch(() => props.databases, (list) => {
  localDatabases.value = Array.isArray(list) ? [...list] : []
}, { immediate: true, deep: true })

const dialogVisible = ref(false)
const isEdit = ref(false)
const currentId = ref(null)
const saving = ref(false)
const dbFormRef = ref()
const dbForm = reactive({ name: '', type: '', config: '' })

const dbRules = {
  name: [
    { required: true, message: '请输入数据库名称', trigger: 'blur' },
    { min: 1, max: 100, message: '长度1-100', trigger: 'blur' }
  ],
  type: [
    { required: true, message: '请选择数据库类型', trigger: 'change' }
  ],
  config: [
    { required: true, message: '请输入JSON配置', trigger: 'blur' }
  ]
}

const dbTypes = ['mysql', 'postgres', 'oracle',"sqlserver",'redis', 'mongodb']

const dialogTitle = computed(() => isEdit.value ? '编辑数据库配置' : '新建数据库配置')

const openCreate = () => {
  isEdit.value = false
  currentId.value = null
  dbForm.name = ''
  dbForm.type = ''
  dbForm.config = '{}'
  dialogVisible.value = true
}

const openEdit = (row) => {
  isEdit.value = true
  currentId.value = row.id
  dbForm.name = row.name
  dbForm.type = row.type
  dbForm.config = JSON.stringify(row.config ?? {}, null, 2)
  dialogVisible.value = true
}

const parseJson = (text) => {
  try { return JSON.parse(text) } catch { return null }
}

const handleSubmit = async () => {
  try {
    await dbFormRef.value.validate()
    const cfg = parseJson(dbForm.config)
    if (!cfg) { ElMessage.error('配置需为合法JSON'); return }
    saving.value = true
    if (!isEdit.value) {
      const res = await createTestEnvironmentDatabase(props.environmentId, { name: dbForm.name, type: dbForm.type, config: cfg })
      const newItem = { id: res.data.id, name: res.data.name, type: res.data.type, config: res.data.config, environment_id: res.data.environment_id }
      localDatabases.value.push(newItem)
    } else {
      const res = await updateTestEnvironmentDatabase(props.environmentId, currentId.value, { name: dbForm.name, type: dbForm.type, config: cfg })
      const idx = localDatabases.value.findIndex(i => i.id === currentId.value)
      if (idx > -1) localDatabases.value[idx] = { id: res.data.id, name: res.data.name, type: res.data.type, config: res.data.config, environment_id: res.data.environment_id }
    }
    emit('update', { databases: localDatabases.value, updated_at: new Date().toISOString() })
    ElMessage.success('保存成功')
    dialogVisible.value = false
  } catch (error) {
    console.error('保存数据库配置失败:', error)
    ElMessage.error('保存失败，请稍后重试')
  } finally {
    saving.value = false
  }
}

const handleDelete = (row) => {
  ElMessageBox.confirm(`确定删除数据库配置「${row.name}」吗？`, '提示', { type: 'warning' })
    .then(async () => {
      await deleteTestEnvironmentDatabase(props.environmentId, row.id)
      localDatabases.value = localDatabases.value.filter(i => i.id !== row.id)
      emit('update', { databases: localDatabases.value, updated_at: new Date().toISOString() })
      ElMessage.success('删除成功')
    })
    .catch(() => {})
}

const stringify = (obj) => {
  try { return JSON.stringify(obj) } catch { return '' }
}
</script>

<style scoped>
.db-config-tab { display: flex; flex-direction: column; gap: 16px; }
.action-bar { display: flex; justify-content: flex-end; }
.config-preview { color: var(--el-text-color-regular); }
</style>