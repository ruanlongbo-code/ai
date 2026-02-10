<template>
  <div class="env-vars-tab">
    <div class="action-bar">
      <el-button type="primary" @click="openCreate">
        <el-icon><Plus /></el-icon>
        新建变量
      </el-button>
    </div>

    <el-table :data="localConfigs" empty-text="暂无变量" style="width: 100%">
      <el-table-column prop="name" label="变量名称" min-width="160" />
      <el-table-column prop="value" label="变量值" min-width="240" />
      <el-table-column label="操作" width="160">
        <template #default="{ row }">
          <el-button size="small" @click="openEdit(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="500px">
      <el-form ref="configFormRef" :model="configForm" :rules="configRules" label-width="100px">
        <el-form-item label="变量名称" prop="name">
          <el-input v-model="configForm.name" maxlength="100" show-word-limit />
        </el-form-item>
        <el-form-item label="变量值" prop="value">
          <el-input v-model="configForm.value" maxlength="500" type="textarea" />
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
import { createTestEnvironmentConfig, updateTestEnvironmentConfig, deleteTestEnvironmentConfig } from '@/api/test_environment'

const props = defineProps({
  environmentId: { type: Number, required: true },
  configs: { type: Array, default: () => [] }
})
const emit = defineEmits(['update'])

const localConfigs = ref([])
watch(() => props.configs, (list) => {
  localConfigs.value = Array.isArray(list) ? [...list] : []
}, { immediate: true, deep: true })

const dialogVisible = ref(false)
const isEdit = ref(false)
const currentId = ref(null)
const saving = ref(false)
const configFormRef = ref()
const configForm = reactive({ name: '', value: '' })

const configRules = {
  name: [
    { required: true, message: '请输入变量名称', trigger: 'blur' },
    { min: 1, max: 100, message: '长度1-100', trigger: 'blur' }
  ],
  value: [
    { required: true, message: '请输入变量值', trigger: 'blur' },
    { min: 1, max: 500, message: '长度1-500', trigger: 'blur' }
  ]
}

const dialogTitle = computed(() => isEdit.value ? '编辑变量' : '新建变量')

const openCreate = () => {
  isEdit.value = false
  currentId.value = null
  configForm.name = ''
  configForm.value = ''
  dialogVisible.value = true
}

const openEdit = (row) => {
  isEdit.value = true
  currentId.value = row.id
  configForm.name = row.name
  configForm.value = row.value
  dialogVisible.value = true
}

const handleSubmit = async () => {
  try {
    await configFormRef.value.validate()
    saving.value = true
    if (!isEdit.value) {
      const res = await createTestEnvironmentConfig(props.environmentId, { name: configForm.name, value: configForm.value })
      const newItem = { id: res.data.id, name: res.data.name, value: res.data.value, environment_id: res.data.environment_id }
      localConfigs.value.push(newItem)
    } else {
      const res = await updateTestEnvironmentConfig(props.environmentId, currentId.value, { name: configForm.name, value: configForm.value })
      const idx = localConfigs.value.findIndex(i => i.id === currentId.value)
      if (idx > -1) localConfigs.value[idx] = { id: res.data.id, name: res.data.name, value: res.data.value, environment_id: res.data.environment_id }
    }
    emit('update', { configs: localConfigs.value, updated_at: new Date().toISOString() })
    ElMessage.success('保存成功')
    dialogVisible.value = false
  } catch (error) {
    console.error('保存变量失败:', error)
    ElMessage.error('保存失败，请稍后重试')
  } finally {
    saving.value = false
  }
}

const handleDelete = (row) => {
  ElMessageBox.confirm(`确定删除变量「${row.name}」吗？`, '提示', { type: 'warning' })
    .then(async () => {
      await deleteTestEnvironmentConfig(props.environmentId, row.id)
      localConfigs.value = localConfigs.value.filter(i => i.id !== row.id)
      emit('update', { configs: localConfigs.value, updated_at: new Date().toISOString() })
      ElMessage.success('删除成功')
    })
    .catch(() => {})
}
</script>

<style scoped>
.env-vars-tab { display: flex; flex-direction: column; gap: 16px; }
.action-bar { display: flex; justify-content: flex-end; }
</style>