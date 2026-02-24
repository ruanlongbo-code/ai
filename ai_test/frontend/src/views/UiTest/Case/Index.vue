<template>
  <div class="ui-case-management">
    <div class="page-header">
      <h2>用例管理</h2>
      <p class="subtitle">管理UI测试用例，支持自然语言描述测试步骤，AI自动执行</p>
    </div>

    <div class="main-layout">
      <!-- 左侧：用例列表 -->
      <div class="case-list-panel">
        <el-card class="list-card">
          <template #header>
            <div class="card-header">
              <el-input v-model="keyword" placeholder="搜索用例..." clearable size="small" style="width: 180px" @input="fetchCases" />
              <el-button type="primary" size="small" @click="openCreateDialog">
                <el-icon><Plus /></el-icon> 新建
              </el-button>
            </div>
          </template>

          <div v-loading="loading" class="case-items">
            <div
              v-for="c in cases"
              :key="c.id"
              class="case-item"
              :class="{ active: selectedCase?.id === c.id }"
              @click="selectCase(c)"
            >
              <div class="case-item-top">
                <span class="case-name">{{ c.name }}</span>
                <el-tag :type="priorityTagType(c.priority)" size="small">{{ c.priority }}</el-tag>
              </div>
              <div class="case-item-bottom">
                <span class="page-label">{{ c.page_name || '未关联页面' }}</span>
                <el-tag :type="statusTagType(c.status)" size="small" effect="plain">{{ statusLabel(c.status) }}</el-tag>
              </div>
            </div>
            <el-empty v-if="!loading && cases.length === 0" description="暂无用例" :image-size="60" />
          </div>
        </el-card>
      </div>

      <!-- 右侧：用例详情 + 步骤编辑 -->
      <div class="case-detail-panel">
        <el-card v-if="selectedCase" class="detail-card">
          <template #header>
            <div class="card-header">
              <div>
                <span style="font-size: 16px; font-weight: 600;">{{ selectedCase.name }}</span>
                <el-tag :type="priorityTagType(selectedCase.priority)" size="small" style="margin-left: 8px;">{{ selectedCase.priority }}</el-tag>
                <el-tag :type="statusTagType(selectedCase.status)" size="small" effect="plain" style="margin-left: 4px;">{{ statusLabel(selectedCase.status) }}</el-tag>
              </div>
              <div>
                <el-button type="success" @click="goExecute(selectedCase)" :disabled="!selectedCase.page_id || selectedCase.steps.length === 0">
                  <el-icon><VideoPlay /></el-icon> AI执行
                </el-button>
                <el-button @click="openEditDialog(selectedCase)">
                  <el-icon><Edit /></el-icon> 编辑
                </el-button>
                <el-button type="danger" @click="handleDelete(selectedCase)">
                  <el-icon><Delete /></el-icon> 删除
                </el-button>
              </div>
            </div>
          </template>

          <!-- 基本信息 -->
          <el-descriptions :column="2" border size="small" style="margin-bottom: 16px;">
            <el-descriptions-item label="关联页面">
              <el-link v-if="selectedCase.page_url" :href="selectedCase.page_url" target="_blank" type="primary">
                {{ selectedCase.page_name }}
              </el-link>
              <span v-else style="color: #c0c4cc;">未关联</span>
            </el-descriptions-item>
            <el-descriptions-item label="最近执行">
              {{ selectedCase.last_run_at ? formatTime(selectedCase.last_run_at) : '未执行' }}
            </el-descriptions-item>
            <el-descriptions-item label="前置条件" :span="2">
              {{ selectedCase.preconditions || '无' }}
            </el-descriptions-item>
          </el-descriptions>

          <!-- 测试步骤 -->
          <h4 style="margin: 0 0 12px 0;">测试步骤（{{ selectedCase.steps.length }}步）</h4>
          <el-table :data="selectedCase.steps" border size="small" style="width: 100%;">
            <el-table-column type="index" label="#" width="50" />
            <el-table-column prop="action" label="操作描述" min-width="220" />
            <el-table-column prop="input_data" label="输入数据" min-width="140">
              <template #default="{ row }">{{ row.input_data || '-' }}</template>
            </el-table-column>
            <el-table-column prop="expected_result" label="预期结果" min-width="200">
              <template #default="{ row }">{{ row.expected_result || '-' }}</template>
            </el-table-column>
          </el-table>
          <el-empty v-if="selectedCase.steps.length === 0" description="暂无测试步骤，请编辑用例添加" :image-size="48" />

          <!-- 执行历史 -->
          <h4 style="margin: 20px 0 12px 0;">执行历史</h4>
          <el-table :data="executions" v-loading="executionsLoading" border size="small" style="width: 100%;">
            <el-table-column prop="created_at" label="执行时间" width="170">
              <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="statusTagType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="步骤" width="140">
              <template #default="{ row }">
                <span style="color: #67c23a;">{{ row.passed_steps }}通过</span> /
                <span style="color: #f56c6c;">{{ row.failed_steps }}失败</span> /
                共{{ row.total_steps }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100">
              <template #default="{ row }">
                <el-button size="small" link type="primary" @click="viewExecution(row)">查看详情</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>

        <el-card v-else class="detail-card empty-detail">
          <el-empty description="请从左侧选择一个用例查看详情" :image-size="100" />
        </el-card>
      </div>
    </div>

    <!-- 新建/编辑用例弹窗 -->
    <el-dialog v-model="caseDialogVisible" :title="isEdit ? '编辑用例' : '新建用例'" width="750px" :close-on-click-modal="false" top="4vh">
      <el-form ref="caseFormRef" :model="caseForm" :rules="caseRules" label-width="90px">
        <el-form-item label="用例名称" prop="name">
          <el-input v-model="caseForm.name" placeholder="如：测试用户登录流程" />
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="关联页面" prop="page_id">
              <el-select v-model="caseForm.page_id" placeholder="选择目标页面" clearable style="width: 100%;">
                <el-option v-for="p in pageOptions" :key="p.id" :label="p.name" :value="p.id">
                  <span>{{ p.name }}</span>
                  <span style="color: #909399; font-size: 12px; margin-left: 8px;">{{ p.url }}</span>
                </el-option>
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="优先级">
              <el-select v-model="caseForm.priority" style="width: 100%;">
                <el-option label="P0 - 最高" value="P0" />
                <el-option label="P1 - 高" value="P1" />
                <el-option label="P2 - 中" value="P2" />
                <el-option label="P3 - 低" value="P3" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="前置条件">
          <el-input v-model="caseForm.preconditions" type="textarea" :rows="2" placeholder="可选，如：用户已注册并有可用账号" />
        </el-form-item>

        <!-- 步骤编辑器 -->
        <el-form-item label="测试步骤">
          <div class="steps-editor">
            <div v-for="(step, idx) in caseForm.steps" :key="idx" class="step-row">
              <div class="step-number">{{ idx + 1 }}</div>
              <div class="step-fields">
                <el-input v-model="step.action" placeholder="操作描述，如：在用户名输入框输入 admin" size="small" />
                <div class="step-sub-fields">
                  <el-input v-model="step.input_data" placeholder="输入数据（可选）" size="small" style="flex: 1;" />
                  <el-input v-model="step.expected_result" placeholder="预期结果（可选），如：登录成功跳转首页" size="small" style="flex: 1;" />
                </div>
              </div>
              <div class="step-actions">
                <el-button size="small" :icon="ArrowUp" circle @click="moveStep(idx, -1)" :disabled="idx === 0" />
                <el-button size="small" :icon="ArrowDown" circle @click="moveStep(idx, 1)" :disabled="idx === caseForm.steps.length - 1" />
                <el-button size="small" type="danger" :icon="Delete" circle @click="removeStep(idx)" />
              </div>
            </div>
            <el-button type="primary" plain @click="addStep" style="width: 100%; margin-top: 8px;">
              <el-icon><Plus /></el-icon> 添加步骤
            </el-button>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="caseDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleCaseSubmit">保存</el-button>
      </template>
    </el-dialog>

    <!-- 执行详情弹窗 -->
    <el-dialog v-model="executionDetailVisible" title="执行详情" width="850px" top="4vh">
      <div v-if="executionDetail">
        <el-descriptions :column="3" border size="small" style="margin-bottom: 16px;">
          <el-descriptions-item label="状态">
            <el-tag :type="statusTagType(executionDetail.status)">{{ statusLabel(executionDetail.status) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="通过/失败">
            <span style="color: #67c23a;">{{ executionDetail.passed_steps }}</span> /
            <span style="color: #f56c6c;">{{ executionDetail.failed_steps }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="执行时间">{{ formatTime(executionDetail.start_time) }}</el-descriptions-item>
        </el-descriptions>

        <el-table :data="executionDetail.step_results" border size="small">
          <el-table-column type="index" label="#" width="50" />
          <el-table-column prop="status" label="状态" width="80">
            <template #default="{ row }">
              <el-tag :type="statusTagType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="actual_result" label="实际结果" min-width="220" show-overflow-tooltip />
          <el-table-column prop="duration_ms" label="耗时" width="90">
            <template #default="{ row }">{{ row.duration_ms ? `${row.duration_ms}ms` : '-' }}</template>
          </el-table-column>
          <el-table-column label="截图" width="120">
            <template #default="{ row }">
              <el-image
                v-if="row.screenshot_url"
                :src="getScreenshotUrl(row.screenshot_url)"
                :preview-src-list="[getScreenshotUrl(row.screenshot_url)]"
                fit="cover"
                style="width: 80px; height: 45px; cursor: pointer; border-radius: 4px;"
              />
              <span v-else>-</span>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowUp, ArrowDown, Delete } from '@element-plus/icons-vue'
import { useProjectStore } from '@/stores'
import { getUiCases, getUiCaseDetail, createUiCase, updateUiCase, deleteUiCase, getUiPages, getUiExecutions, getUiExecutionDetail } from '@/api/uiTest'

const router = useRouter()
const projectStore = useProjectStore()
const projectId = () => projectStore.currentProject?.id
const API_BASE = import.meta.env.VITE_BASE_API || 'http://localhost:8000'

const loading = ref(false)
const cases = ref([])
const keyword = ref('')
const selectedCase = ref(null)
const pageOptions = ref([])

const caseDialogVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)
const editingId = ref(null)
const caseFormRef = ref()
const caseForm = ref({ name: '', page_id: null, priority: 'P1', preconditions: '', steps: [] })
const caseRules = {
  name: [{ required: true, message: '请输入用例名称', trigger: 'blur' }],
}

const executions = ref([])
const executionsLoading = ref(false)
const executionDetailVisible = ref(false)
const executionDetail = ref(null)

const formatTime = (t) => t ? new Date(t).toLocaleString('zh-CN') : '-'

const getScreenshotUrl = (path) => {
  if (!path) return ''
  return `${API_BASE}${path}`
}

const priorityTagType = (p) => {
  const m = { P0: 'danger', P1: 'warning', P2: '', P3: 'info' }
  return m[p] || ''
}

const statusTagType = (s) => {
  const m = { draft: 'info', ready: '', running: 'warning', passed: 'success', failed: 'danger', error: 'danger', pending: 'info' }
  return m[s] || 'info'
}

const statusLabel = (s) => {
  const m = { draft: '草稿', ready: '就绪', running: '执行中', passed: '通过', failed: '失败', error: '异常', pending: '等待中', skipped: '跳过' }
  return m[s] || s
}

const fetchPages = async () => {
  if (!projectId()) return
  try {
    const res = await getUiPages(projectId())
    pageOptions.value = res.data?.pages || []
  } catch (e) { /* ignore */ }
}

const fetchCases = async () => {
  if (!projectId()) return
  loading.value = true
  try {
    const params = {}
    if (keyword.value) params.keyword = keyword.value
    const res = await getUiCases(projectId(), params)
    cases.value = res.data?.cases || []
    if (selectedCase.value) {
      const found = cases.value.find(c => c.id === selectedCase.value.id)
      if (found) selectedCase.value = found
      else selectedCase.value = null
    }
  } catch (e) {
    ElMessage.error('获取用例列表失败')
  } finally {
    loading.value = false
  }
}

const fetchExecutions = async (caseId) => {
  if (!projectId()) return
  executionsLoading.value = true
  try {
    const res = await getUiExecutions(projectId(), { case_id: caseId, page_size: 10 })
    executions.value = res.data?.executions || []
  } catch (e) { /* ignore */ } finally {
    executionsLoading.value = false
  }
}

const selectCase = async (c) => {
  if (!projectId()) return
  try {
    const res = await getUiCaseDetail(projectId(), c.id)
    selectedCase.value = res.data
  } catch (e) {
    selectedCase.value = c
  }
  fetchExecutions(c.id)
}

const openCreateDialog = () => {
  isEdit.value = false
  editingId.value = null
  caseForm.value = { name: '', page_id: null, priority: 'P1', preconditions: '', steps: [] }
  caseDialogVisible.value = true
}

const openEditDialog = (c) => {
  isEdit.value = true
  editingId.value = c.id
  caseForm.value = {
    name: c.name,
    page_id: c.page_id,
    priority: c.priority,
    preconditions: c.preconditions || '',
    steps: (c.steps || []).map(s => ({
      sort_order: s.sort_order,
      action: s.action,
      input_data: s.input_data || '',
      expected_result: s.expected_result || '',
    })),
  }
  caseDialogVisible.value = true
}

const addStep = () => {
  caseForm.value.steps.push({
    sort_order: caseForm.value.steps.length,
    action: '', input_data: '', expected_result: '',
  })
}

const removeStep = (idx) => {
  caseForm.value.steps.splice(idx, 1)
  caseForm.value.steps.forEach((s, i) => s.sort_order = i)
}

const moveStep = (idx, dir) => {
  const steps = caseForm.value.steps
  const target = idx + dir
  if (target < 0 || target >= steps.length) return
  ;[steps[idx], steps[target]] = [steps[target], steps[idx]]
  steps.forEach((s, i) => s.sort_order = i)
}

const handleCaseSubmit = async () => {
  if (!caseFormRef.value) return
  await caseFormRef.value.validate()
  submitting.value = true
  try {
    const data = {
      ...caseForm.value,
      steps: caseForm.value.steps.map((s, i) => ({ ...s, sort_order: i })),
    }
    if (isEdit.value) {
      await updateUiCase(projectId(), editingId.value, data)
      ElMessage.success('更新成功')
    } else {
      await createUiCase(projectId(), data)
      ElMessage.success('创建成功')
    }
    caseDialogVisible.value = false
    await fetchCases()
  } catch (e) {
    ElMessage.error(isEdit.value ? '更新失败' : '创建失败')
  } finally {
    submitting.value = false
  }
}

const handleDelete = async (c) => {
  await ElMessageBox.confirm(`确定删除用例 "${c.name}" 吗？`, '确认删除', { type: 'warning' })
  try {
    await deleteUiCase(projectId(), c.id)
    ElMessage.success('删除成功')
    selectedCase.value = null
    await fetchCases()
  } catch (e) {
    ElMessage.error('删除失败')
  }
}

const goExecute = (c) => {
  router.push(`/ui-test/execute/${c.id}`)
}

const viewExecution = async (row) => {
  try {
    const res = await getUiExecutionDetail(projectId(), row.id)
    executionDetail.value = res.data
    executionDetailVisible.value = true
  } catch (e) {
    ElMessage.error('获取执行详情失败')
  }
}

onMounted(() => {
  fetchPages()
  fetchCases()
})
</script>

<style scoped>
.ui-case-management { padding: 20px; }
.page-header { margin-bottom: 16px; }
.page-header h2 { color: #303133; margin: 0 0 6px 0; font-size: 22px; font-weight: 600; }
.subtitle { color: #909399; margin: 0; font-size: 13px; }

.main-layout { display: flex; gap: 16px; height: calc(100vh - 230px); }
.case-list-panel { width: 320px; flex-shrink: 0; }
.case-detail-panel { flex: 1; min-width: 0; overflow-y: auto; }

.list-card, .detail-card { height: 100%; border: none; box-shadow: 0 2px 12px rgba(0,0,0,0.06); }
.card-header { display: flex; justify-content: space-between; align-items: center; gap: 8px; }

.case-items { max-height: calc(100vh - 340px); overflow-y: auto; }
.case-item {
  padding: 10px 12px; margin-bottom: 6px; border-radius: 6px;
  cursor: pointer; transition: all .2s; border: 1px solid transparent;
}
.case-item:hover { background: #f5f7fa; }
.case-item.active { background: #ecf5ff; border-color: #409eff; }
.case-item-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
.case-name { font-size: 14px; font-weight: 500; color: #303133; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 200px; }
.case-item-bottom { display: flex; justify-content: space-between; align-items: center; }
.page-label { font-size: 12px; color: #909399; }

.empty-detail { display: flex; align-items: center; justify-content: center; }

.steps-editor { width: 100%; }
.step-row { display: flex; align-items: flex-start; gap: 8px; margin-bottom: 10px; padding: 10px; background: #fafafa; border-radius: 6px; }
.step-number { width: 28px; height: 28px; border-radius: 50%; background: #409eff; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 13px; font-weight: 600; flex-shrink: 0; margin-top: 2px; }
.step-fields { flex: 1; }
.step-sub-fields { display: flex; gap: 8px; margin-top: 6px; }
.step-actions { display: flex; flex-direction: column; gap: 2px; }
</style>
