<template>
  <div class="webhook-config-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <h1>通知配置</h1>
          <p class="subtitle">配置测试执行完成后的飞书 / 钉钉 / 自定义 Webhook 通知</p>
        </div>
        <div class="action-section">
          <el-button type="primary" @click="handleCreate">
            <el-icon><Plus /></el-icon>
            新建配置
          </el-button>
          <el-button @click="loadConfigs">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </div>
    </div>

    <!-- 配置列表 -->
    <el-card shadow="never" class="config-list-card">
      <div v-loading="loading" class="table-content">
        <el-table v-if="configList.length > 0" :data="configList" stripe>
          <el-table-column prop="id" label="ID" width="70" />
          <el-table-column prop="name" label="配置名称" min-width="180">
            <template #default="{ row }">
              <span class="config-name">{{ row.name }}</span>
            </template>
          </el-table-column>
          <el-table-column label="通知类型" width="120">
            <template #default="{ row }">
              <el-tag :type="webhookTypeTag(row.webhook_type)" size="small" effect="light">
                {{ webhookTypeLabel(row.webhook_type) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="触发条件" width="130">
            <template #default="{ row }">
              <el-tag size="small" effect="plain">{{ triggerLabel(row.trigger_on) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="webhook_url" label="Webhook URL" min-width="280">
            <template #default="{ row }">
              <span class="url-text" :title="row.webhook_url">{{ row.webhook_url }}</span>
            </template>
          </el-table-column>
          <el-table-column label="启用" width="80">
            <template #default="{ row }">
              <el-switch v-model="row.is_active" size="small" @change="handleToggleActive(row)" />
            </template>
          </el-table-column>
          <el-table-column label="操作" width="240" fixed="right">
            <template #default="{ row }">
              <el-button size="small" type="success" @click="handleTest(row)">
                <el-icon><Connection /></el-icon> 测试
              </el-button>
              <el-button size="small" @click="handleEdit(row)">编辑</el-button>
              <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-else description="暂无Webhook配置" :image-size="80">
          <el-button type="primary" @click="handleCreate">创建第一个通知配置</el-button>
        </el-empty>
      </div>
    </el-card>

    <!-- 新建/编辑弹窗 -->
    <el-dialog
      v-model="showFormDialog"
      :title="editingConfig ? '编辑通知配置' : '新建通知配置'"
      width="560px"
      destroy-on-close
    >
      <el-form :model="configForm" :rules="formRules" ref="formRef" label-width="100px">
        <el-form-item label="配置名称" prop="name">
          <el-input v-model="configForm.name" placeholder="如：测试失败通知群" />
        </el-form-item>
        <el-form-item label="通知类型" prop="webhook_type">
          <el-select v-model="configForm.webhook_type" placeholder="选择通知类型" style="width: 100%">
            <el-option label="飞书" value="feishu" />
            <el-option label="钉钉" value="dingtalk" />
            <el-option label="自定义 Webhook" value="custom" />
          </el-select>
        </el-form-item>
        <el-form-item label="Webhook URL" prop="webhook_url">
          <el-input v-model="configForm.webhook_url" placeholder="输入Webhook URL" />
        </el-form-item>
        <el-form-item label="触发条件" prop="trigger_on">
          <el-select v-model="configForm.trigger_on" placeholder="选择触发条件" style="width: 100%">
            <el-option label="每次执行后通知" value="always" />
            <el-option label="仅失败时通知" value="on_failure" />
            <el-option label="仅成功时通知" value="on_success" />
          </el-select>
        </el-form-item>
        <el-form-item label="启用状态">
          <el-switch v-model="configForm.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showFormDialog = false">取消</el-button>
        <el-button type="primary" :loading="formSubmitting" @click="handleSubmitForm">
          {{ editingConfig ? '保存修改' : '创建配置' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh, Connection } from '@element-plus/icons-vue'
import {
  createWebhookConfig,
  getWebhookConfigs,
  updateWebhookConfig,
  deleteWebhookConfig,
  testWebhookConfig
} from '@/api/apiTest'
import { useProjectStore } from '@/stores'

const route = useRoute()
const projectStore = useProjectStore()

const loading = ref(false)
const configList = ref([])
const showFormDialog = ref(false)
const editingConfig = ref(null)
const formSubmitting = ref(false)
const formRef = ref(null)

const configForm = reactive({
  name: '',
  webhook_type: 'feishu',
  webhook_url: '',
  trigger_on: 'always',
  is_active: true
})

const formRules = {
  name: [{ required: true, message: '请输入配置名称', trigger: 'blur' }],
  webhook_type: [{ required: true, message: '请选择通知类型', trigger: 'change' }],
  webhook_url: [{ required: true, message: '请输入Webhook URL', trigger: 'blur' }],
  trigger_on: [{ required: true, message: '请选择触发条件', trigger: 'change' }]
}

const getProjectId = () => {
  return route.params.projectId || projectStore.currentProject?.id || 1
}

const webhookTypeLabel = (type) => {
  const map = { feishu: '飞书', dingtalk: '钉钉', custom: '自定义' }
  return map[type] || type
}

const webhookTypeTag = (type) => {
  const map = { feishu: 'primary', dingtalk: 'success', custom: '' }
  return map[type] || 'info'
}

const triggerLabel = (trigger) => {
  const map = { always: '每次通知', on_failure: '失败通知', on_success: '成功通知' }
  return map[trigger] || trigger
}

// ========== 加载 ==========
const loadConfigs = async () => {
  loading.value = true
  try {
    const res = await getWebhookConfigs(getProjectId())
    const data = res.data || res
    configList.value = data.items || data.configs || []
  } catch (e) {
    console.error('加载Webhook配置失败:', e)
    ElMessage.error('加载通知配置失败')
  } finally {
    loading.value = false
  }
}

// ========== CRUD ==========
const handleCreate = () => {
  editingConfig.value = null
  Object.assign(configForm, {
    name: '', webhook_type: 'feishu', webhook_url: '',
    trigger_on: 'always', is_active: true
  })
  showFormDialog.value = true
}

const handleEdit = (row) => {
  editingConfig.value = row
  Object.assign(configForm, {
    name: row.name,
    webhook_type: row.webhook_type,
    webhook_url: row.webhook_url,
    trigger_on: row.trigger_on,
    is_active: row.is_active
  })
  showFormDialog.value = true
}

const handleSubmitForm = async () => {
  if (!formRef.value) return
  try {
    await formRef.value.validate()
  } catch { return }

  formSubmitting.value = true
  try {
    const payload = {
      name: configForm.name,
      webhook_type: configForm.webhook_type,
      webhook_url: configForm.webhook_url,
      trigger_on: configForm.trigger_on,
      is_active: configForm.is_active
    }
    if (editingConfig.value) {
      await updateWebhookConfig(getProjectId(), editingConfig.value.id, payload)
      ElMessage.success('配置已更新')
    } else {
      await createWebhookConfig(getProjectId(), payload)
      ElMessage.success('配置已创建')
    }
    showFormDialog.value = false
    loadConfigs()
  } catch (e) {
    ElMessage.error('操作失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    formSubmitting.value = false
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确认删除通知配置「${row.name}」？`, '删除确认', { type: 'warning' })
    await deleteWebhookConfig(getProjectId(), row.id)
    ElMessage.success('删除成功')
    loadConfigs()
  } catch {}
}

const handleToggleActive = async (row) => {
  try {
    await updateWebhookConfig(getProjectId(), row.id, { is_active: row.is_active })
    ElMessage.success(row.is_active ? '已启用' : '已停用')
  } catch (e) {
    row.is_active = !row.is_active
    ElMessage.error('操作失败')
  }
}

const handleTest = async (row) => {
  try {
    const res = await testWebhookConfig(getProjectId(), row.id)
    const data = res.data || res
    if (data.success !== false) {
      ElMessage.success('Webhook 连通性测试成功！')
    } else {
      ElMessage.warning('Webhook 测试失败: ' + (data.message || '请检查URL'))
    }
  } catch (e) {
    ElMessage.error('测试失败: ' + (e.response?.data?.detail || e.message))
  }
}

// ========== 初始化 ==========
onMounted(() => {
  loadConfigs()
})
</script>

<style scoped>
.webhook-config-page {
  padding: 24px;
  background: #f8fafc;
  min-height: 100vh;
}

.page-header {
  margin-bottom: 16px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  background: white;
  padding: 20px 24px;
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}

.title-section h1 {
  color: #1f2937;
  margin: 0 0 4px 0;
  font-size: 22px;
  font-weight: 600;
}

.subtitle {
  color: #6b7280;
  margin: 0;
  font-size: 13px;
}

.action-section {
  display: flex;
  gap: 8px;
}

.config-list-card {
  border-radius: 8px;
}

.table-content {
  min-height: 200px;
}

.config-name {
  font-weight: 500;
  color: #1f2937;
}

.url-text {
  font-size: 12px;
  color: #6b7280;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  display: inline-block;
  max-width: 280px;
}

@media (max-width: 768px) {
  .webhook-config-page { padding: 12px; }
  .header-content { flex-direction: column; gap: 12px; }
}
</style>
