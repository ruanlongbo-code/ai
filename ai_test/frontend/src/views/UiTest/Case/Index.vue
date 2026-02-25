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
            <el-table-column prop="action" label="操作描述" min-width="200" />
            <el-table-column prop="input_data" label="输入数据" min-width="120">
              <template #default="{ row }">{{ row.input_data || '-' }}</template>
            </el-table-column>
            <el-table-column prop="expected_result" label="预期结果" min-width="160">
              <template #default="{ row }">{{ row.expected_result || '-' }}</template>
            </el-table-column>
            <el-table-column label="断言" min-width="200">
              <template #default="{ row }">
                <template v-if="row.assertion_type">
                  <el-tag type="primary" size="small" effect="plain">{{ assertionTypeLabel(row.assertion_type) }}</el-tag>
                  <div style="font-size: 11px; color: #606266; margin-top: 2px;">
                    <span v-if="row.assertion_target" style="color: #409eff;">{{ row.assertion_target }}</span>
                    <span v-if="row.assertion_value"> → {{ row.assertion_value }}</span>
                  </div>
                </template>
                <span v-else style="color: #c0c4cc;">-</span>
              </template>
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
            <el-table-column label="操作" width="170">
              <template #default="{ row }">
                <el-button size="small" link type="primary" @click="viewExecution(row)">详情</el-button>
                <el-button size="small" link type="success" @click="goReport(row)" v-if="row.status === 'passed' || row.status === 'failed'">
                  <el-icon><Document /></el-icon> 报告
                </el-button>
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
    <el-dialog v-model="caseDialogVisible" :title="isEdit ? '编辑用例' : '新建用例'" width="800px" :close-on-click-modal="false" top="4vh">
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

        <!-- 步骤编辑器 — 重新设计为列表式布局 -->
        <el-form-item label="测试步骤" required>
          <div class="steps-editor">
            <div v-if="caseForm.steps.length === 0" class="steps-empty-tip">
              <el-icon><InfoFilled /></el-icon> 请添加至少一个测试步骤
            </div>

            <div v-for="(step, idx) in caseForm.steps" :key="idx" class="step-card" :class="{ 'has-error': stepErrors[idx] }">
              <!-- 步骤头部 -->
              <div class="step-card-header">
                <div class="step-badge">步骤 {{ idx + 1 }}</div>
                <div class="step-card-actions">
                  <el-button size="small" :icon="ArrowUp" circle plain @click="moveStep(idx, -1)" :disabled="idx === 0" title="上移" />
                  <el-button size="small" :icon="ArrowDown" circle plain @click="moveStep(idx, 1)" :disabled="idx === caseForm.steps.length - 1" title="下移" />
                  <el-button size="small" type="danger" :icon="Delete" circle plain @click="removeStep(idx)" title="删除" />
                </div>
              </div>

              <!-- 步骤内容：每个字段独占一行 -->
              <div class="step-card-body">
                <!-- 操作描述（必填） -->
                <div class="step-field">
                  <label class="step-field-label required">操作描述</label>
                  <el-input
                    v-model="step.action"
                    placeholder="描述操作，如：在用户名输入框输入 admin"
                    :class="{ 'is-error': stepErrors[idx]?.action }"
                  />
                  <span v-if="stepErrors[idx]?.action" class="field-error">{{ stepErrors[idx].action }}</span>
                </div>

                <!-- 输入数据（可选） -->
                <div class="step-field">
                  <label class="step-field-label">输入数据</label>
                  <el-input v-model="step.input_data" placeholder="可选，如：admin123" />
                </div>

                <!-- 预期结果（必填） -->
                <div class="step-field">
                  <label class="step-field-label required">预期结果</label>
                  <el-input
                    v-model="step.expected_result"
                    placeholder="AI判断依据，如：登录成功跳转到首页"
                    :class="{ 'is-error': stepErrors[idx]?.expected_result }"
                  />
                  <span v-if="stepErrors[idx]?.expected_result" class="field-error">{{ stepErrors[idx].expected_result }}</span>
                </div>

                <!-- 断言类型（必填） -->
                <div class="step-field">
                  <label class="step-field-label required">断言类型</label>
                  <el-select
                    v-model="step.assertion_type"
                    placeholder="请选择断言类型"
                    style="width: 100%;"
                    :class="{ 'is-error': stepErrors[idx]?.assertion_type }"
                  >
                    <el-option-group label="URL断言">
                      <el-option label="URL包含" value="url_contains" />
                      <el-option label="URL等于" value="url_equals" />
                    </el-option-group>
                    <el-option-group label="标题断言">
                      <el-option label="标题包含" value="title_contains" />
                      <el-option label="标题等于" value="title_equals" />
                    </el-option-group>
                    <el-option-group label="元素断言">
                      <el-option label="元素可见" value="element_visible" />
                      <el-option label="元素隐藏" value="element_hidden" />
                      <el-option label="元素文本包含" value="element_text_contains" />
                      <el-option label="元素文本等于" value="element_text_equals" />
                      <el-option label="元素存在" value="element_exists" />
                    </el-option-group>
                    <el-option-group label="页面断言">
                      <el-option label="页面包含文本" value="page_contains" />
                      <el-option label="提示消息包含" value="toast_contains" />
                    </el-option-group>
                  </el-select>
                  <span v-if="stepErrors[idx]?.assertion_type" class="field-error">{{ stepErrors[idx].assertion_type }}</span>
                </div>

                <!-- 断言目标（CSS选择器，元素类断言必填） -->
                <div class="step-field" v-if="needsTarget(step.assertion_type)">
                  <label class="step-field-label required">断言目标</label>
                  <el-input
                    v-model="step.assertion_target"
                    :placeholder="getTargetPlaceholder(step.assertion_type)"
                    :class="{ 'is-error': stepErrors[idx]?.assertion_target }"
                  >
                    <template #prepend>CSS</template>
                  </el-input>
                  <span v-if="stepErrors[idx]?.assertion_target" class="field-error">{{ stepErrors[idx].assertion_target }}</span>
                </div>

                <!-- 断言期望值（需要值的断言必填） -->
                <div class="step-field" v-if="needsValue(step.assertion_type)">
                  <label class="step-field-label required">期望值</label>
                  <el-input
                    v-model="step.assertion_value"
                    :placeholder="getValuePlaceholder(step.assertion_type)"
                    :class="{ 'is-error': stepErrors[idx]?.assertion_value }"
                  />
                  <span v-if="stepErrors[idx]?.assertion_value" class="field-error">{{ stepErrors[idx].assertion_value }}</span>
                </div>
              </div>
            </div>

            <el-button type="primary" plain @click="addStep" class="add-step-btn">
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
    <el-dialog v-model="executionDetailVisible" title="执行详情" width="950px" top="4vh">
      <div v-if="executionDetail">
        <!-- 执行概览 -->
        <el-descriptions :column="4" border size="small" style="margin-bottom: 16px;">
          <el-descriptions-item label="状态">
            <el-tag :type="statusTagType(executionDetail.status)" effect="dark">{{ statusLabel(executionDetail.status) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="通过步骤">
            <span style="color: #67c23a; font-weight: 600; font-size: 16px;">{{ executionDetail.passed_steps }}</span>
            <span style="color: #909399; font-size: 12px;"> / {{ executionDetail.total_steps }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="失败步骤">
            <span style="color: #f56c6c; font-weight: 600; font-size: 16px;">{{ executionDetail.failed_steps }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="执行时间">{{ formatTime(executionDetail.start_time) }}</el-descriptions-item>
        </el-descriptions>

        <!-- 步骤结果列表 -->
        <div class="step-results-list">
          <div
            v-for="(sr, idx) in executionDetail.step_results"
            :key="sr.id"
            class="step-result-card"
            :class="sr.status"
          >
            <div class="sr-header">
              <div class="sr-left">
                <span class="sr-badge" :class="sr.status">{{ idx + 1 }}</span>
                <el-tag :type="statusTagType(sr.status)" size="small" effect="dark">{{ statusLabel(sr.status) }}</el-tag>
                <span v-if="sr.duration_ms" class="sr-duration">⏱ {{ sr.duration_ms }}ms</span>
              </div>
            </div>

            <div class="sr-body">
              <!-- 左侧：结果信息 -->
              <div class="sr-info">
                <!-- AI操作信息 -->
                <div v-if="sr.ai_action" class="sr-ai-action">
                  <div class="sr-label">
                    <el-icon style="color:#8b5cf6;"><MagicStick /></el-icon> AI执行操作
                  </div>
                  <div class="sr-ai-detail">{{ formatAiAction(sr.ai_action) }}</div>
                </div>
                <!-- 实际结果 -->
                <div v-if="sr.actual_result" class="sr-actual">
                  <div class="sr-label">实际结果</div>
                  <div class="sr-text" :class="{ 'text-danger': sr.status === 'failed' }">{{ sr.actual_result }}</div>
                </div>
                <!-- 错误信息 -->
                <div v-if="sr.error_message" class="sr-error">
                  <div class="sr-label">错误信息</div>
                  <div class="sr-text text-danger">{{ sr.error_message }}</div>
                </div>
                <!-- 断言结果 -->
                <div v-if="sr.assertion_type" class="sr-assertion">
                  <div class="sr-label">
                    <el-icon :style="{color: sr.assertion_passed ? '#67c23a' : '#f56c6c'}">
                      <component :is="sr.assertion_passed ? 'SuccessFilled' : 'CircleCloseFilled'" />
                    </el-icon>
                    断言: {{ assertionTypeLabel(sr.assertion_type) }}
                  </div>
                  <div class="sr-assertion-detail" :class="{ passed: sr.assertion_passed, failed: !sr.assertion_passed }">
                    {{ sr.assertion_detail || '-' }}
                  </div>
                </div>
              </div>

              <!-- 右侧：截图 -->
              <div v-if="sr.screenshot_url" class="sr-screenshot">
                <el-image
                  :src="getScreenshotUrl(sr.screenshot_url)"
                  :preview-src-list="allScreenshots"
                  :initial-index="idx"
                  fit="cover"
                  class="sr-screenshot-img"
                />
                <span class="sr-screenshot-label">点击放大</span>
              </div>
            </div>
          </div>
        </div>

        <el-empty v-if="!executionDetail.step_results || executionDetail.step_results.length === 0" description="无步骤结果" />
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowUp, ArrowDown, Delete, MagicStick, Document, SuccessFilled, CircleCloseFilled, InfoFilled } from '@element-plus/icons-vue'
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

// 步骤级别的校验错误
const stepErrors = reactive({})

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
  clearStepErrors()
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
      assertion_type: s.assertion_type || '',
      assertion_target: s.assertion_target || '',
      assertion_value: s.assertion_value || '',
    })),
  }
  clearStepErrors()
  caseDialogVisible.value = true
}

const addStep = () => {
  caseForm.value.steps.push({
    sort_order: caseForm.value.steps.length,
    action: '', input_data: '', expected_result: '',
    assertion_type: '', assertion_target: '', assertion_value: '',
  })
}

const removeStep = (idx) => {
  caseForm.value.steps.splice(idx, 1)
  caseForm.value.steps.forEach((s, i) => s.sort_order = i)
  clearStepErrors()
}

const moveStep = (idx, dir) => {
  const steps = caseForm.value.steps
  const target = idx + dir
  if (target < 0 || target >= steps.length) return
  ;[steps[idx], steps[target]] = [steps[target], steps[idx]]
  steps.forEach((s, i) => s.sort_order = i)
}

// ============ 步骤校验 ============
const clearStepErrors = () => {
  Object.keys(stepErrors).forEach(k => delete stepErrors[k])
}

const validateSteps = () => {
  clearStepErrors()
  let valid = true

  if (caseForm.value.steps.length === 0) {
    ElMessage.warning('请至少添加一个测试步骤')
    return false
  }

  caseForm.value.steps.forEach((step, idx) => {
    const errors = {}

    if (!step.action || !step.action.trim()) {
      errors.action = '操作描述不能为空'
      valid = false
    }
    if (!step.expected_result || !step.expected_result.trim()) {
      errors.expected_result = '预期结果不能为空'
      valid = false
    }
    if (!step.assertion_type) {
      errors.assertion_type = '请选择断言类型'
      valid = false
    }
    // 需要目标的断言类型检查
    if (step.assertion_type && needsTarget(step.assertion_type) && (!step.assertion_target || !step.assertion_target.trim())) {
      errors.assertion_target = '请输入断言目标（CSS选择器）'
      valid = false
    }
    // 需要期望值的断言类型检查
    if (step.assertion_type && needsValue(step.assertion_type) && (!step.assertion_value || !step.assertion_value.trim())) {
      errors.assertion_value = '请输入期望值'
      valid = false
    }

    if (Object.keys(errors).length > 0) {
      stepErrors[idx] = errors
    }
  })

  return valid
}

const handleCaseSubmit = async () => {
  if (!caseFormRef.value) return
  await caseFormRef.value.validate()

  // 校验步骤
  if (!validateSteps()) return

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

// 所有截图URL列表（用于预览时翻页）
const allScreenshots = computed(() => {
  if (!executionDetail.value?.step_results) return []
  return executionDetail.value.step_results
    .filter(sr => sr.screenshot_url)
    .map(sr => getScreenshotUrl(sr.screenshot_url))
})

// 格式化AI操作信息
const formatAiAction = (aiActionStr) => {
  if (!aiActionStr) return '-'
  try {
    const obj = JSON.parse(aiActionStr)
    const desc = obj.description || ''
    const action = obj.action || ''
    const selector = obj.selector || ''
    const value = obj.value || ''
    let result = `[${action}]`
    if (selector) result += ` ${selector}`
    if (value) result += ` → "${value}"`
    if (desc) result += ` | ${desc}`
    return result
  } catch (e) {
    return aiActionStr
  }
}

// 断言类型标签
const assertionTypeLabel = (type) => {
  const m = {
    url_contains: 'URL包含', url_equals: 'URL等于',
    title_contains: '标题包含', title_equals: '标题等于',
    element_visible: '元素可见', element_hidden: '元素隐藏',
    element_text_contains: '元素文本包含', element_text_equals: '元素文本等于',
    element_exists: '元素存在',
    page_contains: '页面包含文本', toast_contains: '提示消息包含',
  }
  return m[type] || type
}

// 哪些断言类型需要CSS选择器
const needsTarget = (type) => {
  return ['element_visible', 'element_hidden', 'element_text_contains', 'element_text_equals', 'element_exists'].includes(type)
}

// 哪些断言类型需要期望值
const needsValue = (type) => {
  return ['url_contains', 'url_equals', 'title_contains', 'title_equals',
    'element_text_contains', 'element_text_equals', 'page_contains', 'toast_contains'].includes(type)
}

// 获取目标placeholder
const getTargetPlaceholder = (type) => {
  const m = {
    element_visible: '如：#username 或 .login-btn',
    element_hidden: '如：.loading-spinner',
    element_text_contains: '如：.welcome-msg 或 h1.title',
    element_text_equals: '如：#status-text',
    element_exists: '如：.success-icon 或 #dashboard',
  }
  return m[type] || 'CSS选择器'
}

// 获取期望值placeholder
const getValuePlaceholder = (type) => {
  const m = {
    url_contains: '如：/dashboard 或 /home',
    url_equals: '如：https://example.com/dashboard',
    title_contains: '如：首页 或 Dashboard',
    title_equals: '如：AI测试平台 - 首页',
    element_text_contains: '如：欢迎回来 或 登录成功',
    element_text_equals: '如：操作成功',
    page_contains: '如：欢迎 或 登录成功',
    toast_contains: '如：保存成功 或 操作完成',
  }
  return m[type] || '期望值'
}

// 跳转到测试报告页
const goReport = (row) => {
  router.push(`/ui-test/report/${row.id}`)
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

/* ============ 步骤编辑器（列表式布局） ============ */
.steps-editor { width: 100%; }

.steps-empty-tip {
  padding: 24px;
  text-align: center;
  color: #909399;
  font-size: 13px;
  background: #fafafa;
  border-radius: 8px;
  border: 1px dashed #dcdfe6;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  margin-bottom: 12px;
}

.step-card {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  margin-bottom: 12px;
  overflow: hidden;
  transition: all .2s;
  background: #fff;
}
.step-card:hover {
  border-color: #c0c4cc;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.step-card.has-error {
  border-color: #f56c6c;
  box-shadow: 0 0 0 1px rgba(245,108,108,0.2);
}

.step-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 14px;
  background: #f8f9fb;
  border-bottom: 1px solid #ebeef5;
}

.step-badge {
  font-size: 13px;
  font-weight: 600;
  color: #409eff;
}

.step-card-actions {
  display: flex;
  gap: 4px;
}

.step-card-body {
  padding: 14px;
}

.step-field {
  margin-bottom: 12px;
}
.step-field:last-child {
  margin-bottom: 0;
}

.step-field-label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: #606266;
  margin-bottom: 6px;
}
.step-field-label.required::before {
  content: '*';
  color: #f56c6c;
  margin-right: 4px;
}

.field-error {
  display: block;
  font-size: 12px;
  color: #f56c6c;
  margin-top: 4px;
  line-height: 1;
}

.step-field :deep(.is-error .el-input__wrapper) {
  box-shadow: 0 0 0 1px #f56c6c inset;
}
.step-field :deep(.is-error .el-select__wrapper) {
  box-shadow: 0 0 0 1px #f56c6c inset;
}

.add-step-btn {
  width: 100%;
  margin-top: 4px;
  border-style: dashed;
}

/* ============ 执行详情弹窗样式 ============ */
.step-results-list { max-height: 55vh; overflow-y: auto; }

.step-result-card {
  margin-bottom: 10px; padding: 12px 14px; border-radius: 8px;
  border: 1px solid #ebeef5; transition: all .2s;
}
.step-result-card.passed { border-left: 3px solid #67c23a; background: #fafff5; }
.step-result-card.failed { border-left: 3px solid #f56c6c; background: #fff5f5; }
.step-result-card.pending { border-left: 3px solid #c0c4cc; }
.step-result-card.skipped { border-left: 3px solid #e6a23c; background: #fdf6ec; }

.sr-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.sr-left { display: flex; align-items: center; gap: 8px; }
.sr-badge {
  width: 22px; height: 22px; border-radius: 50%; display: flex;
  align-items: center; justify-content: center; font-size: 11px;
  font-weight: 700; color: #fff; background: #c0c4cc;
}
.sr-badge.passed { background: #67c23a; }
.sr-badge.failed { background: #f56c6c; }
.sr-duration { font-size: 12px; color: #909399; }

.sr-body { display: flex; gap: 14px; }
.sr-info { flex: 1; min-width: 0; }

.sr-ai-action, .sr-actual, .sr-error {
  margin-bottom: 6px;
}
.sr-label {
  font-size: 11px; color: #909399; font-weight: 600; margin-bottom: 2px;
  display: flex; align-items: center; gap: 4px;
}
.sr-ai-detail {
  font-size: 12px; color: #7c3aed; padding: 4px 8px;
  background: linear-gradient(135deg, #f5f3ff 0%, #ede9fe 100%);
  border-radius: 4px; border: 1px solid #ddd6fe; word-break: break-all;
}
.sr-text { font-size: 12px; color: #303133; line-height: 1.5; word-break: break-all; }
.sr-text.text-danger { color: #f56c6c; }

.sr-screenshot { flex-shrink: 0; display: flex; flex-direction: column; align-items: center; gap: 4px; }
.sr-screenshot-img {
  width: 160px; height: 90px; border-radius: 6px; cursor: pointer;
  border: 1px solid #e0e0e0; overflow: hidden;
  transition: transform .2s, box-shadow .2s;
}
.sr-screenshot-img:hover {
  transform: scale(1.03); box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}
.sr-screenshot-label { font-size: 10px; color: #909399; }

/* 断言结果样式 */
.sr-assertion { margin-bottom: 6px; }
.sr-assertion-detail {
  font-size: 12px; padding: 4px 8px; border-radius: 4px;
  line-height: 1.5; word-break: break-all;
}
.sr-assertion-detail.passed {
  background: #f0f9eb; color: #67c23a; border: 1px solid #b3e19d;
}
.sr-assertion-detail.failed {
  background: #fef0f0; color: #f56c6c; border: 1px solid #fab6b6;
}

.step-results-list::-webkit-scrollbar { width: 4px; }
.step-results-list::-webkit-scrollbar-thumb { background: #dcdfe6; border-radius: 2px; }
</style>
