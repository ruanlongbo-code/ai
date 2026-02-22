<template>
  <div class="feishu-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>💬 飞书群集成</span>
          <el-button type="primary" @click="showAddDialog = true">
            <el-icon><Plus /></el-icon> 添加飞书群
          </el-button>
        </div>
      </template>

      <el-alert type="info" :closable="false" class="info-alert">
        <template #title>
          配置飞书群机器人 Webhook 地址后，测试人员可以一键将测试进度报告推送到飞书群中。
          <br />
          获取方式：飞书群设置 → 群机器人 → 添加机器人 → 自定义机器人 → 复制 Webhook 地址
        </template>
      </el-alert>

      <el-table :data="webhooks" border stripe v-loading="loading">
        <el-table-column prop="name" label="群名称" min-width="160" />
        <el-table-column label="Webhook URL" min-width="300">
          <template #default="{ row }">
            <span class="url-text">{{ maskUrl(row.webhook_url) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-switch v-model="row.is_active" @change="toggleActive(row)" size="small" />
          </template>
        </el-table-column>
        <el-table-column prop="created_by_name" label="创建人" width="100" />
        <el-table-column label="操作" width="200" align="center">
          <template #default="{ row }">
            <el-button type="success" link size="small" @click="handleTest(row)" :loading="testing[row.id]">
              测试连接
            </el-button>
            <el-button type="primary" link size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button type="danger" link size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="webhooks.length === 0 && !loading" description="暂无飞书群配置" />
    </el-card>

    <!-- 新增/编辑弹窗 -->
    <el-dialog v-model="showAddDialog" :title="editingWebhook ? '编辑飞书群' : '添加飞书群'" width="500px">
      <el-form :model="webhookForm" label-width="110px">
        <el-form-item label="群名称" required>
          <el-input v-model="webhookForm.name" placeholder="如：Payments需求同步群" />
        </el-form-item>
        <el-form-item label="Webhook URL" required>
          <el-input v-model="webhookForm.webhook_url" placeholder="https://open.feishu.cn/open-apis/bot/v2/hook/xxx" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false; editingWebhook = null">取消</el-button>
        <el-button type="primary" @click="handleSave" :loading="saving">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useProjectStore } from '@/stores'
import {
  getFeishuWebhooks, createFeishuWebhook, updateFeishuWebhook,
  deleteFeishuWebhook, testFeishuWebhook
} from '@/api/schedule'

const projectStore = useProjectStore()
const projectId = computed(() => projectStore.currentProject?.id)

const webhooks = ref([])
const loading = ref(false)

const showAddDialog = ref(false)
const editingWebhook = ref(null)
const saving = ref(false)
const webhookForm = ref({ name: '', webhook_url: '' })

const testing = reactive({})

function maskUrl(url) {
  if (!url) return ''
  if (url.length > 60) {
    return url.substring(0, 50) + '...' + url.substring(url.length - 10)
  }
  return url
}

async function loadWebhooks() {
  if (!projectId.value) return
  loading.value = true
  try {
    const res = await getFeishuWebhooks(projectId.value)
    webhooks.value = res.webhooks || res.data?.webhooks || []
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

function handleEdit(row) {
  editingWebhook.value = row
  webhookForm.value = { name: row.name, webhook_url: row.webhook_url }
  showAddDialog.value = true
}

async function handleSave() {
  if (!webhookForm.value.name || !webhookForm.value.webhook_url) {
    return ElMessage.warning('请填写完整信息')
  }
  saving.value = true
  try {
    if (editingWebhook.value) {
      await updateFeishuWebhook(projectId.value, editingWebhook.value.id, webhookForm.value)
      ElMessage.success('更新成功')
    } else {
      await createFeishuWebhook(projectId.value, webhookForm.value)
      ElMessage.success('添加成功')
    }
    showAddDialog.value = false
    editingWebhook.value = null
    webhookForm.value = { name: '', webhook_url: '' }
    await loadWebhooks()
  } catch (e) {
    ElMessage.error('操作失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    saving.value = false
  }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`确认删除飞书群「${row.name}」？`, '删除确认', { type: 'warning' })
    await deleteFeishuWebhook(projectId.value, row.id)
    ElMessage.success('已删除')
    await loadWebhooks()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  }
}

async function toggleActive(row) {
  try {
    await updateFeishuWebhook(projectId.value, row.id, { is_active: row.is_active })
    ElMessage.success(row.is_active ? '已启用' : '已禁用')
  } catch (e) {
    row.is_active = !row.is_active
    ElMessage.error('更新失败')
  }
}

async function handleTest(row) {
  testing[row.id] = true
  try {
    const res = await testFeishuWebhook(projectId.value, row.id)
    if (res.success || res.data?.success) {
      ElMessage.success('测试消息发送成功 ✅')
    } else {
      ElMessage.warning('发送失败: ' + (res.message || res.data?.message || ''))
    }
  } catch (e) {
    ElMessage.error('测试失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    testing[row.id] = false
  }
}

onMounted(loadWebhooks)
</script>

<style scoped>
.feishu-container {
  padding: 16px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.info-alert {
  margin-bottom: 16px;
}
.url-text {
  font-family: monospace;
  font-size: 12px;
  color: #666;
}
</style>
