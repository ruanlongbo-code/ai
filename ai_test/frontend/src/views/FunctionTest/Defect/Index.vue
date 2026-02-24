<template>
  <div class="defect-management-container">
    <!-- 顶部操作栏 -->
    <div class="page-header">
      <div class="header-left">
        <el-select v-model="filterIterationId" placeholder="选择迭代" clearable @change="loadDefects"
                   style="width: 200px">
          <el-option v-for="it in iterations" :key="it.id" :label="it.name" :value="it.id" />
        </el-select>
        <el-select v-model="filterScheduleItemId" placeholder="按需求筛选" clearable @change="loadDefects"
                   style="width: 240px">
          <el-option v-for="item in scheduleItems" :key="item.id"
                     :label="item.requirement_title" :value="item.id" />
        </el-select>
        <el-select v-model="filterStatus" placeholder="按状态筛选" clearable @change="loadDefects"
                   style="width: 140px">
          <el-option label="待处理" value="open" />
          <el-option label="修复中" value="fixing" />
          <el-option label="已修复" value="fixed" />
          <el-option label="已验证" value="verified" />
          <el-option label="已关闭" value="closed" />
          <el-option label="已拒绝" value="rejected" />
        </el-select>
        <el-select v-model="filterSeverity" placeholder="按严重程度" clearable @change="loadDefects"
                   style="width: 140px">
          <el-option label="P0 - 阻塞" value="P0" />
          <el-option label="P1 - 严重" value="P1" />
          <el-option label="P2 - 一般" value="P2" />
          <el-option label="P3 - 轻微" value="P3" />
        </el-select>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="handleCreateDefect">
          <el-icon><Plus /></el-icon> 新建缺陷
        </el-button>
        <el-button @click="loadDefects">
          <el-icon><Refresh /></el-icon> 刷新
        </el-button>
      </div>
    </div>

    <!-- 统计概览 -->
    <div class="stats-overview">
      <div class="stat-card total">
        <div class="stat-number">{{ stats.total }}</div>
        <div class="stat-label">缺陷总数</div>
      </div>
      <div class="stat-card danger">
        <div class="stat-number">{{ stats.open + stats.fixing }}</div>
        <div class="stat-label">待处理</div>
      </div>
      <div class="stat-card warning">
        <div class="stat-number">{{ stats.fixed }}</div>
        <div class="stat-label">已修复</div>
      </div>
      <div class="stat-card success">
        <div class="stat-number">{{ stats.verified + stats.closed }}</div>
        <div class="stat-label">已关闭</div>
      </div>
      <div class="stat-card info">
        <div class="stat-number">{{ stats.rejected }}</div>
        <div class="stat-label">已拒绝</div>
      </div>
    </div>

    <!-- 缺陷列表 -->
    <el-card v-loading="loading">
      <template #header>
        <div class="card-header">
          <span>📋 缺陷列表</span>
          <el-tag>共 {{ defectList.length }} 条</el-tag>
        </div>
      </template>

      <el-empty v-if="defectList.length === 0" description="暂无缺陷数据" />

      <el-table v-else :data="defectList" border stripe style="width: 100%"
                :row-class-name="tableRowClassName">
        <el-table-column prop="id" label="ID" width="70" align="center" />
        <el-table-column prop="title" label="缺陷标题" min-width="240" show-overflow-tooltip>
          <template #default="{ row }">
            <el-link type="primary" @click="handleViewDetail(row)">{{ row.title }}</el-link>
          </template>
        </el-table-column>
        <el-table-column label="关联需求" min-width="180" show-overflow-tooltip>
          <template #default="{ row }">
            {{ row.requirement_title || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="defect_type" label="类型" width="90" align="center">
          <template #default="{ row }">
            <el-tag size="small" effect="plain">{{ defectTypeLabel(row.defect_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="severity" label="严重程度" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="severityTagType(row.severity)" size="small">{{ row.severity }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="defect_status" label="状态" width="110" align="center">
          <template #default="{ row }">
            <el-select v-model="row.defect_status" size="small" style="width: 90px"
                       @change="handleUpdateStatus(row)">
              <el-option label="待处理" value="open" />
              <el-option label="修复中" value="fixing" />
              <el-option label="已修复" value="fixed" />
              <el-option label="已验证" value="verified" />
              <el-option label="已关闭" value="closed" />
              <el-option label="已拒绝" value="rejected" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column prop="reporter_name" label="报告人" width="90" />
        <el-table-column prop="assignee_name" label="经办人" width="90" />
        <el-table-column label="飞书" width="80" align="center">
          <template #default="{ row }">
            <el-link v-if="row.feishu_ticket_url" type="primary" :href="row.feishu_ticket_url"
                     target="_blank" :underline="false">
              <el-icon><Link /></el-icon>
            </el-link>
            <el-button v-else type="primary" link size="small"
                       @click="handleSyncToFeishu(row)" :loading="syncingMap[row.id]">
              同步
            </el-button>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" align="center" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="handleEditDefect(row)">编辑</el-button>
            <el-popconfirm title="确定删除此缺陷？" @confirm="handleDeleteDefect(row)">
              <template #reference>
                <el-button type="danger" link size="small">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新建/编辑缺陷弹窗 -->
    <el-dialog v-model="showFormDialog" :title="isEditing ? '编辑缺陷' : '新建缺陷'" width="720px"
               destroy-on-close :close-on-click-modal="false">
      <el-form :model="defectForm" label-width="100px" ref="defectFormRef">
        <el-form-item label="关联需求" required>
          <el-select v-model="defectForm.schedule_item_id" placeholder="选择关联需求" filterable style="width: 100%">
            <el-option v-for="item in scheduleItems" :key="item.id"
                       :label="item.requirement_title" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="缺陷标题" required>
          <el-input v-model="defectForm.title" placeholder="简要描述缺陷" maxlength="200" show-word-limit />
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="缺陷类型">
              <el-select v-model="defectForm.defect_type" style="width: 100%">
                <el-option label="功能缺陷" value="functional" />
                <el-option label="界面显示" value="ui" />
                <el-option label="性能问题" value="performance" />
                <el-option label="兼容性" value="compatibility" />
                <el-option label="其他" value="other" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="严重程度">
              <el-select v-model="defectForm.severity" style="width: 100%">
                <el-option label="P0 - 阻塞" value="P0" />
                <el-option label="P1 - 严重" value="P1" />
                <el-option label="P2 - 一般" value="P2" />
                <el-option label="P3 - 轻微" value="P3" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="经办人">
              <el-select v-model="defectForm.assignee_id" placeholder="选择开发" clearable style="width: 100%">
                <el-option v-for="u in assignableUsers" :key="u.id"
                           :label="u.real_name || u.username" :value="u.id" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="缺陷描述">
          <el-input v-model="defectForm.description" type="textarea" :rows="3"
                    placeholder="描述缺陷的表现（可简写，后续用AI扩写）" />
        </el-form-item>
        <el-form-item label="复现步骤">
          <el-input v-model="defectForm.reproduce_steps" type="textarea" :rows="3"
                    placeholder="1. 打开xx页面&#10;2. 点击xx按钮&#10;3. 出现xx问题" />
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="预期结果">
              <el-input v-model="defectForm.expected_result" type="textarea" :rows="2"
                        placeholder="正确行为应该是..." />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="实际结果">
              <el-input v-model="defectForm.actual_result" type="textarea" :rows="2"
                        placeholder="实际表现是..." />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="showFormDialog = false">取消</el-button>
        <el-button @click="handleAiExpand" :loading="aiExpandLoading" :disabled="!defectForm.title">
          🧠 AI扩写描述
        </el-button>
        <el-button type="primary" @click="handleSubmitDefect(false)" :loading="submitting"
                   :disabled="!defectForm.title || !defectForm.schedule_item_id">
          {{ isEditing ? '保存修改' : '提交缺陷' }}
        </el-button>
        <el-button v-if="!isEditing" type="success" @click="handleSubmitDefect(true)" :loading="submitting"
                   :disabled="!defectForm.title || !defectForm.schedule_item_id">
          提交并同步到飞书
        </el-button>
      </template>
    </el-dialog>

    <!-- 缺陷详情弹窗 -->
    <el-dialog v-model="showDetailDialog" title="缺陷详情" width="700px">
      <el-descriptions :column="2" border v-if="detailDefect">
        <el-descriptions-item label="缺陷ID">{{ detailDefect.id }}</el-descriptions-item>
        <el-descriptions-item label="关联需求">{{ detailDefect.requirement_title || '-' }}</el-descriptions-item>
        <el-descriptions-item label="缺陷标题" :span="2">{{ detailDefect.title }}</el-descriptions-item>
        <el-descriptions-item label="缺陷类型">{{ defectTypeLabel(detailDefect.defect_type) }}</el-descriptions-item>
        <el-descriptions-item label="严重程度">
          <el-tag :type="severityTagType(detailDefect.severity)">{{ detailDefect.severity }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="defectStatusTagType(detailDefect.defect_status)">
            {{ defectStatusLabel(detailDefect.defect_status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="经办人">{{ detailDefect.assignee_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="报告人">{{ detailDefect.reporter_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatTime(detailDefect.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="缺陷描述" :span="2">
          <div style="white-space: pre-wrap;">{{ detailDefect.description || '-' }}</div>
        </el-descriptions-item>
        <el-descriptions-item label="复现步骤" :span="2">
          <div style="white-space: pre-wrap;">{{ detailDefect.reproduce_steps || '-' }}</div>
        </el-descriptions-item>
        <el-descriptions-item label="预期结果">
          <div style="white-space: pre-wrap;">{{ detailDefect.expected_result || '-' }}</div>
        </el-descriptions-item>
        <el-descriptions-item label="实际结果">
          <div style="white-space: pre-wrap;">{{ detailDefect.actual_result || '-' }}</div>
        </el-descriptions-item>
        <el-descriptions-item label="飞书链接" :span="2" v-if="detailDefect.feishu_ticket_url">
          <el-link type="primary" :href="detailDefect.feishu_ticket_url" target="_blank">
            {{ detailDefect.feishu_ticket_url }}
          </el-link>
        </el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button @click="showDetailDialog = false">关闭</el-button>
        <el-button type="primary" @click="handleEditDefect(detailDefect); showDetailDialog = false">编辑</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { Plus, Refresh, Link } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useProjectStore } from '@/stores'
import {
  getIterations, getScheduleItems,
  createDefect, getDefects, updateDefect, deleteDefect, getDefectStats,
  aiExpandDefectPreview, getAssignableUsers, syncDefectToFeishu
} from '@/api/schedule'

const projectStore = useProjectStore()
const projectId = computed(() => projectStore.currentProject?.id)

const loading = ref(false)
const iterations = ref([])
const scheduleItems = ref([])
const defectList = ref([])
const assignableUsers = ref([])

// 筛选
const filterIterationId = ref(null)
const filterScheduleItemId = ref(null)
const filterStatus = ref(null)
const filterSeverity = ref(null)

// 统计
const stats = reactive({
  total: 0, open: 0, fixing: 0, fixed: 0, verified: 0, closed: 0, rejected: 0
})

// 表单
const showFormDialog = ref(false)
const isEditing = ref(false)
const editingDefectId = ref(null)
const submitting = ref(false)
const aiExpandLoading = ref(false)
const defectFormRef = ref()
const defectForm = reactive({
  schedule_item_id: null,
  title: '',
  description: '',
  defect_type: 'functional',
  severity: 'P2',
  assignee_id: null,
  reproduce_steps: '',
  expected_result: '',
  actual_result: '',
})

// 详情
const showDetailDialog = ref(false)
const detailDefect = ref(null)

// 同步飞书
const syncingMap = reactive({})

// 辅助函数
function defectTypeLabel(t) {
  const map = { functional: '功能缺陷', ui: '界面显示', performance: '性能问题', compatibility: '兼容性', other: '其他' }
  return map[t] || t
}
function severityTagType(s) {
  const map = { P0: 'danger', P1: 'warning', P2: '', P3: 'info' }
  return map[s] || ''
}
function defectStatusTagType(s) {
  const map = { open: 'danger', fixing: 'warning', fixed: '', verified: 'success', closed: 'info', rejected: 'info' }
  return map[s] || ''
}
function defectStatusLabel(s) {
  const map = { open: '待处理', fixing: '修复中', fixed: '已修复', verified: '已验证', closed: '已关闭', rejected: '已拒绝' }
  return map[s] || s
}
function formatTime(t) {
  if (!t) return '-'
  return new Date(t).toLocaleString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}
function tableRowClassName({ row }) {
  if (row.severity === 'P0') return 'severity-p0-row'
  if (row.severity === 'P1') return 'severity-p1-row'
  return ''
}

// 数据加载
async function loadIterations() {
  if (!projectId.value) return
  try {
    const res = await getIterations(projectId.value)
    const data = res.data || res
    iterations.value = data.iterations || data || []
  } catch (e) {
    console.error('加载迭代失败:', e)
  }
}

async function loadScheduleItems() {
  if (!projectId.value) return
  try {
    const params = {}
    if (filterIterationId.value) params.iteration_id = filterIterationId.value
    const res = await getScheduleItems(projectId.value, params)
    const data = res.data || res
    scheduleItems.value = data.items || data || []
  } catch (e) {
    console.error('加载需求列表失败:', e)
  }
}

async function loadDefects() {
  if (!projectId.value) return
  loading.value = true
  try {
    const params = {}
    if (filterScheduleItemId.value) params.schedule_item_id = filterScheduleItemId.value
    if (filterIterationId.value) params.iteration_id = filterIterationId.value
    if (filterStatus.value) params.defect_status = filterStatus.value
    if (filterSeverity.value) params.severity = filterSeverity.value

    const res = await getDefects(projectId.value, params)
    const data = res.data || res
    defectList.value = data.defects || data || []

    // 更新统计
    await loadStats()
  } catch (e) {
    console.error('加载缺陷列表失败:', e)
    ElMessage.error('加载缺陷列表失败')
  } finally {
    loading.value = false
  }
}

async function loadStats() {
  if (!projectId.value) return
  try {
    const res = await getDefectStats(projectId.value, filterScheduleItemId.value || undefined)
    const data = res.data || res
    Object.assign(stats, {
      total: data.total || 0,
      open: data.open || 0,
      fixing: data.fixing || 0,
      fixed: data.fixed || 0,
      verified: data.verified || 0,
      closed: data.closed || 0,
      rejected: data.rejected || 0,
    })
  } catch (e) {
    console.debug('统计加载:', e)
  }
}

async function loadAssignableUsers() {
  if (!projectId.value) return
  try {
    const res = await getAssignableUsers(projectId.value)
    const data = res.data || res
    assignableUsers.value = data.users || data || []
  } catch (e) {
    console.error(e)
  }
}

// 新建缺陷
function handleCreateDefect() {
  isEditing.value = false
  editingDefectId.value = null
  Object.assign(defectForm, {
    schedule_item_id: filterScheduleItemId.value || null,
    title: '',
    description: '',
    defect_type: 'functional',
    severity: 'P2',
    assignee_id: null,
    reproduce_steps: '',
    expected_result: '',
    actual_result: '',
  })
  showFormDialog.value = true
}

// 编辑缺陷
function handleEditDefect(row) {
  isEditing.value = true
  editingDefectId.value = row.id
  Object.assign(defectForm, {
    schedule_item_id: row.schedule_item_id,
    title: row.title,
    description: row.description || '',
    defect_type: row.defect_type,
    severity: row.severity,
    assignee_id: row.assignee_id,
    reproduce_steps: row.reproduce_steps || '',
    expected_result: row.expected_result || '',
    actual_result: row.actual_result || '',
  })
  showFormDialog.value = true
}

// 查看详情
function handleViewDetail(row) {
  detailDefect.value = row
  showDetailDialog.value = true
}

// 提交缺陷
async function handleSubmitDefect(syncToFeishu = false) {
  if (!defectForm.title || !defectForm.schedule_item_id) {
    return ElMessage.warning('请填写缺陷标题并选择关联需求')
  }
  submitting.value = true
  try {
    const payload = {
      schedule_item_id: defectForm.schedule_item_id,
      title: defectForm.title,
      description: defectForm.description,
      defect_type: defectForm.defect_type,
      severity: defectForm.severity,
      assignee_id: defectForm.assignee_id,
      reproduce_steps: defectForm.reproduce_steps,
      expected_result: defectForm.expected_result,
      actual_result: defectForm.actual_result,
    }

    if (isEditing.value && editingDefectId.value) {
      await updateDefect(projectId.value, editingDefectId.value, payload)
      ElMessage.success('缺陷已更新')
    } else {
      const createRes = await createDefect(projectId.value, payload)
      const created = createRes.data || createRes

      if (syncToFeishu && created.id) {
        try {
          const syncRes = await syncDefectToFeishu(projectId.value, created.id)
          const syncData = syncRes.data || syncRes
          ElMessage.success(syncData.message || '缺陷已提交并同步到飞书项目')
        } catch (syncErr) {
          ElMessage.warning('缺陷已提交，但同步到飞书失败: ' + (syncErr.response?.data?.detail || syncErr.message))
        }
      } else {
        ElMessage.success('缺陷提交成功')
      }
    }

    showFormDialog.value = false
    await loadDefects()
  } catch (e) {
    ElMessage.error('操作失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    submitting.value = false
  }
}

// AI扩写
async function handleAiExpand() {
  if (!defectForm.title) return ElMessage.warning('请先输入缺陷标题')
  aiExpandLoading.value = true
  try {
    const aiRes = await aiExpandDefectPreview(projectId.value, {
      schedule_item_id: defectForm.schedule_item_id,
      title: defectForm.title,
      description: defectForm.description || defectForm.title,
      defect_type: defectForm.defect_type,
      severity: defectForm.severity,
      reproduce_steps: defectForm.reproduce_steps,
      expected_result: defectForm.expected_result,
      actual_result: defectForm.actual_result,
    })
    const aiData = aiRes.data || aiRes
    defectForm.description = aiData.ai_expanded_description || defectForm.description
    ElMessage.success('AI已扩写缺陷描述，请检查确认后再提交')
  } catch (e) {
    ElMessage.error('AI扩写失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    aiExpandLoading.value = false
  }
}

// 更新状态
async function handleUpdateStatus(row) {
  try {
    await updateDefect(projectId.value, row.id, { defect_status: row.defect_status })
    ElMessage.success('状态已更新')
    await loadStats()
  } catch (e) {
    ElMessage.error('更新失败')
  }
}

// 删除缺陷
async function handleDeleteDefect(row) {
  try {
    await deleteDefect(projectId.value, row.id)
    ElMessage.success('缺陷已删除')
    await loadDefects()
  } catch (e) {
    ElMessage.error('删除失败: ' + (e.response?.data?.detail || e.message))
  }
}

// 同步到飞书
async function handleSyncToFeishu(row) {
  syncingMap[row.id] = true
  try {
    const res = await syncDefectToFeishu(projectId.value, row.id)
    const data = res.data || res
    if (data.feishu_issue_url) {
      row.feishu_ticket_url = data.feishu_issue_url
    }
    ElMessage.success(data.message || '同步成功')
  } catch (e) {
    ElMessage.error('同步失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    syncingMap[row.id] = false
  }
}

onMounted(async () => {
  await loadIterations()
  await loadScheduleItems()
  await loadAssignableUsers()
  await loadDefects()
})

watch(projectId, async () => {
  await loadIterations()
  await loadScheduleItems()
  await loadAssignableUsers()
  await loadDefects()
})

watch(filterIterationId, async () => {
  await loadScheduleItems()
})
</script>

<style scoped>
.defect-management-container {
  padding: 16px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 12px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.stats-overview {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.stat-card {
  flex: 1;
  min-width: 120px;
  padding: 16px 20px;
  border-radius: 10px;
  text-align: center;
  background: #f5f7fa;
  border: 1px solid #e4e7ed;
  transition: transform 0.2s;
}

.stat-card:hover {
  transform: translateY(-2px);
}

.stat-card.total {
  background: linear-gradient(135deg, #e8f4fd, #d1ecf9);
  border-color: #b3d8ff;
}

.stat-card.danger {
  background: linear-gradient(135deg, #fef0f0, #fde2e2);
  border-color: #fbc4c4;
}

.stat-card.warning {
  background: linear-gradient(135deg, #fdf6ec, #faecd8);
  border-color: #f5dab1;
}

.stat-card.success {
  background: linear-gradient(135deg, #f0f9eb, #e1f3d8);
  border-color: #c2e7b0;
}

.stat-card.info {
  background: linear-gradient(135deg, #f4f4f5, #e9e9eb);
  border-color: #d3d4d6;
}

.stat-number {
  font-size: 28px;
  font-weight: 700;
  color: #303133;
  line-height: 1.2;
}

.stat-card.danger .stat-number { color: #f56c6c; }
.stat-card.warning .stat-number { color: #e6a23c; }
.stat-card.success .stat-number { color: #67c23a; }
.stat-card.info .stat-number { color: #909399; }

.stat-label {
  font-size: 13px;
  color: #909399;
  margin-top: 4px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

:deep(.severity-p0-row) {
  background-color: #fef0f0 !important;
}

:deep(.severity-p1-row) {
  background-color: #fdf6ec !important;
}
</style>
