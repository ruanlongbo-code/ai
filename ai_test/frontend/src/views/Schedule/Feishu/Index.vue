<template>
  <div class="feishu-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>📢 需求群管理</span>
          <div>
            <el-button type="success" plain @click="handleVerifyFeishu" :loading="verifying" size="small">
              🔗 验证飞书应用连接
            </el-button>
            <el-button type="primary" @click="openAddDialog">
              <el-icon><Plus /></el-icon> 添加需求群
            </el-button>
          </div>
        </div>
      </template>

      <el-alert type="info" :closable="false" class="info-alert">
        <template #title>
          配置飞书群机器人 Webhook 地址后，测试人员可以一键将测试进度报告同步到对应的需求群中。
          <br />
          关联需求后，同步进度时会自动匹配到对应需求的群，无需手动选择。不关联则为全局群。
          <br />
          获取方式：飞书群设置 → 群机器人 → 添加机器人 → 自定义机器人 → 复制 Webhook 地址
        </template>
      </el-alert>

      <el-table :data="webhooks" border stripe v-loading="loading">
        <el-table-column prop="name" label="群名称" min-width="160" />
        <el-table-column label="关联需求" min-width="280">
          <template #default="{ row }">
            <template v-if="row.linked_requirement_names?.length">
              <el-tag v-for="(name, idx) in row.linked_requirement_names" :key="idx" size="small"
                      style="margin-right: 4px; margin-bottom: 4px;" effect="plain">
                {{ name }}
              </el-tag>
            </template>
            <el-tag v-else type="info" size="small">全局群（所有需求）</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="Webhook URL" min-width="260">
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

      <el-empty v-if="webhooks.length === 0 && !loading" description="暂无需求群配置" />
    </el-card>

    <!-- 新增/编辑弹窗 -->
    <el-dialog v-model="showAddDialog" :title="editingWebhook ? '编辑需求群' : '添加需求群'" width="640px">
      <el-form :model="webhookForm" label-width="110px">
        <el-form-item label="群名称" required>
          <el-input v-model="webhookForm.name" placeholder="如：xx需求同步群" />
        </el-form-item>
        <el-form-item label="Webhook URL" required>
          <el-input v-model="webhookForm.webhook_url" placeholder="https://open.feishu.cn/open-apis/bot/v2/hook/xxx" />
        </el-form-item>
        <el-form-item label="关联需求">
          <el-select v-model="webhookForm.linked_schedule_item_ids" multiple placeholder="留空则为全局群（所有需求生效）"
                     style="width: 100%" filterable>
            <el-option-group v-for="group in groupedRequirements" :key="group.label" :label="group.label">
              <el-option v-for="item in group.items" :key="item.id" :label="item.requirement_title" :value="item.id">
                <span>{{ item.requirement_title }}</span>
                <span style="float: right; color: #8492a6; font-size: 12px">{{ item.category || '' }}</span>
              </el-option>
            </el-option-group>
          </el-select>
          <div class="form-tip">
            选择关联的需求后，对应需求在同步进度时会自动匹配此群。留空则对所有需求生效（全局群）。
          </div>
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
  deleteFeishuWebhook, testFeishuWebhook, getScheduleItems, getIterations,
  verifyFeishuConnection
} from '@/api/schedule'

const projectStore = useProjectStore()
const projectId = computed(() => projectStore.currentProject?.id)

const webhooks = ref([])
const loading = ref(false)

// 需求列表（按迭代分组）
const allRequirements = ref([])
const groupedRequirements = computed(() => {
  const groups = {}
  for (const item of allRequirements.value) {
    const label = item._iteration_name || '未知迭代'
    if (!groups[label]) groups[label] = { label, items: [] }
    groups[label].items.push(item)
  }
  return Object.values(groups)
})

const showAddDialog = ref(false)
const editingWebhook = ref(null)
const saving = ref(false)
const webhookForm = ref({ name: '', webhook_url: '', linked_schedule_item_ids: [] })

const testing = reactive({})
const verifying = ref(false)

async function handleVerifyFeishu() {
  verifying.value = true
  try {
    const res = await verifyFeishuConnection(projectId.value)
    const data = res.data || res
    const msgs = []
    if (data.open_platform?.success) {
      msgs.push('飞书开放平台 ✅')
    } else {
      msgs.push('飞书开放平台 ❌ ' + (data.open_platform?.message || ''))
    }
    if (data.project_mcp?.success) {
      msgs.push('飞书项目MCP ✅')
    } else {
      msgs.push('飞书项目MCP ❌ ' + (data.project_mcp?.message || ''))
    }
    if (data.success) {
      ElMessage.success(msgs.join(' | '))
    } else {
      ElMessage.warning(msgs.join(' | '))
    }
  } catch (e) {
    ElMessage.error('验证失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    verifying.value = false
  }
}

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

// 加载所有迭代中的需求列表（用于关联选择）
async function loadRequirements() {
  if (!projectId.value) return
  try {
    const iterRes = await getIterations(projectId.value)
    const iters = iterRes.data?.iterations || iterRes.iterations || []
    const items = []

    for (const it of iters) {
      try {
        const itemRes = await getScheduleItems(projectId.value, { iteration_id: it.id })
        const scheduleItems = itemRes.data?.items || itemRes.items || []
        scheduleItems.forEach(si => {
          items.push({ ...si, _iteration_name: it.name })
        })
      } catch (e) { /* ignore */ }
    }
    allRequirements.value = items
  } catch (e) {
    console.error(e)
  }
}

function openAddDialog() {
  editingWebhook.value = null
  webhookForm.value = { name: '', webhook_url: '', linked_schedule_item_ids: [] }
  showAddDialog.value = true
}

function handleEdit(row) {
  editingWebhook.value = row
  webhookForm.value = {
    name: row.name,
    webhook_url: row.webhook_url,
    linked_schedule_item_ids: row.linked_schedule_item_ids || [],
  }
  showAddDialog.value = true
}

async function handleSave() {
  if (!webhookForm.value.name || !webhookForm.value.webhook_url) {
    return ElMessage.warning('请填写完整信息')
  }

  const payload = {
    name: webhookForm.value.name,
    webhook_url: webhookForm.value.webhook_url,
    linked_schedule_item_ids: webhookForm.value.linked_schedule_item_ids?.length > 0
      ? webhookForm.value.linked_schedule_item_ids : null,
  }

  saving.value = true
  try {
    if (editingWebhook.value) {
      await updateFeishuWebhook(projectId.value, editingWebhook.value.id, payload)
      ElMessage.success('更新成功')
    } else {
      await createFeishuWebhook(projectId.value, payload)
      ElMessage.success('添加成功')
    }
    showAddDialog.value = false
    editingWebhook.value = null
    webhookForm.value = { name: '', webhook_url: '', linked_schedule_item_ids: [] }
    await loadWebhooks()
  } catch (e) {
    ElMessage.error('操作失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    saving.value = false
  }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`确认删除需求群「${row.name}」？`, '删除确认', { type: 'warning' })
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

onMounted(() => {
  loadWebhooks()
  loadRequirements()
})
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
.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
</style>
