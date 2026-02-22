<template>
  <div class="daily-report-container">
    <!-- 顶部选择器 -->
    <div class="report-header">
      <div class="header-left">
        <el-select v-model="currentIterationId" placeholder="选择迭代" @change="loadMyItems" style="width: 240px">
          <el-option v-for="it in iterations" :key="it.id" :label="it.name" :value="it.id" />
        </el-select>
        <el-tag type="success" v-if="currentIterationId">
          今日: {{ todayStr }}
        </el-tag>
      </div>
      <div class="header-right">
        <el-button @click="handleRefresh">
          <el-icon><Refresh /></el-icon> 刷新
        </el-button>
      </div>
    </div>

    <!-- 我今日负责的需求列表 -->
    <el-card v-loading="loading" class="my-items-card">
      <template #header>
        <span>📋 我负责的需求排期</span>
      </template>

      <el-empty v-if="myItems.length === 0" description="当前迭代中暂无分配给你的需求" />

      <div v-for="item in myItems" :key="item.id" class="requirement-item">
        <div class="item-header">
          <div class="item-title">
            <el-tag v-if="item.priority" :type="priorityTagType(item.priority)" size="small" effect="plain">
              {{ item.priority }}
            </el-tag>
            <span class="title-text">{{ item.requirement_title }}</span>
            <el-tag v-if="item.has_today_report" type="success" size="small">今日已提交</el-tag>
          </div>
          <div class="item-meta">
            <el-progress :percentage="item.actual_progress" :stroke-width="8"
                        :color="progressColor(item.actual_progress)" style="width: 120px" />
            <span class="risk-badge">{{ riskIcon(item.risk_level) }}</span>
          </div>
        </div>

        <!-- 日报填写区域 -->
        <div class="report-form" v-if="reportForms[item.id]">
          <el-form :model="reportForms[item.id]" label-width="100px" size="default">
            <el-row :gutter="16">
              <el-col :span="24">
                <el-form-item label="今日进展" required>
                  <el-input
                    v-model="reportForms[item.id].today_progress"
                    type="textarea"
                    :rows="3"
                    placeholder="描述今日工作进展，如：1.完成了xx模块的冒烟测试 2.发现了2个Bug已提交..."
                  />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="16">
              <el-col :span="24">
                <el-form-item label="明日计划">
                  <el-input
                    v-model="reportForms[item.id].next_plan"
                    type="textarea"
                    :rows="2"
                    placeholder="明日计划（可选）"
                  />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="16">
              <el-col :span="6">
                <el-form-item label="Bug总数">
                  <el-input-number v-model="reportForms[item.id].bug_total" :min="0" style="width: 100%" />
                </el-form-item>
              </el-col>
              <el-col :span="6">
                <el-form-item label="待处理">
                  <el-input-number v-model="reportForms[item.id].bug_open" :min="0" style="width: 100%" />
                </el-form-item>
              </el-col>
              <el-col :span="6">
                <el-form-item label="已修复">
                  <el-input-number v-model="reportForms[item.id].bug_fixed" :min="0" style="width: 100%" />
                </el-form-item>
              </el-col>
              <el-col :span="6">
                <el-form-item label="已关闭">
                  <el-input-number v-model="reportForms[item.id].bug_closed" :min="0" style="width: 100%" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="16">
              <el-col :span="6">
                <el-form-item label="用例总数">
                  <el-input-number v-model="reportForms[item.id].case_total" :min="0" style="width: 100%" />
                </el-form-item>
              </el-col>
              <el-col :span="6">
                <el-form-item label="已执行">
                  <el-input-number v-model="reportForms[item.id].case_executed" :min="0" style="width: 100%" />
                </el-form-item>
              </el-col>
              <el-col :span="6">
                <el-form-item label="通过">
                  <el-input-number v-model="reportForms[item.id].case_passed" :min="0" style="width: 100%" />
                </el-form-item>
              </el-col>
              <el-col :span="6">
                <el-form-item label="失败">
                  <el-input-number v-model="reportForms[item.id].case_failed" :min="0" style="width: 100%" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="16">
              <el-col :span="12">
                <el-form-item label="更新进度">
                  <el-slider v-model="reportForms[item.id].actual_progress" :min="0" :max="100" :step="5" show-stops />
                </el-form-item>
              </el-col>
            </el-row>
            <el-form-item>
              <el-button type="primary" @click="handleSubmitReport(item)" :loading="submitting[item.id]">
                {{ item.has_today_report ? '更新日报' : '提交日报' }}
              </el-button>
              <el-button @click="handleGenerateAiReport(item)" :loading="aiGenerating[item.id]"
                        :disabled="!reportForms[item.id]._report_id">
                ✨ AI 生成报告
              </el-button>
              <el-button @click="handleSendFeishu(item)" :disabled="!reportForms[item.id]._report_id">
                📤 发送到飞书群
              </el-button>
            </el-form-item>
          </el-form>

          <!-- AI 生成的报告预览 -->
          <div v-if="reportForms[item.id]._ai_content" class="ai-report-preview">
            <div class="ai-report-header">
              <span>✨ AI 生成的报告</span>
              <el-button size="small" @click="copyReport(reportForms[item.id]._ai_content)">📋 复制</el-button>
            </div>
            <div class="ai-report-content" v-html="formatAiReport(reportForms[item.id]._ai_content)" />
          </div>
        </div>
      </div>
    </el-card>

    <!-- 历史日报 -->
    <el-card class="history-card" v-if="currentIterationId">
      <template #header>
        <span>📅 历史日报记录</span>
      </template>
      <el-table :data="historyReports" border stripe>
        <el-table-column prop="report_date" label="日期" width="110" />
        <el-table-column prop="requirement_title" label="需求" min-width="200" />
        <el-table-column prop="today_progress" label="进展" min-width="300" show-overflow-tooltip />
        <el-table-column label="Bug" width="120" align="center">
          <template #default="{ row }">
            {{ row.bug_total }}个({{ row.bug_open }}待处理)
          </template>
        </el-table-column>
        <el-table-column label="进度" width="80" align="center">
          <template #default="{ row }">{{ row.actual_progress }}%</template>
        </el-table-column>
        <el-table-column label="飞书" width="70" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.feishu_sent" type="success" size="small">已发</el-tag>
            <el-tag v-else type="info" size="small">未发</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 飞书推送弹窗 -->
    <el-dialog v-model="showFeishuDialog" title="发送到飞书群" width="500px">
      <el-form>
        <el-form-item label="选择飞书群">
          <el-checkbox-group v-model="selectedWebhookIds">
            <el-checkbox v-for="wh in feishuWebhooks" :key="wh.id" :label="wh.id">
              {{ wh.name }}
            </el-checkbox>
          </el-checkbox-group>
          <el-empty v-if="feishuWebhooks.length === 0" description="暂未配置飞书群，请在「飞书群集成」中添加" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showFeishuDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmSendFeishu" :loading="sendingFeishu"
                  :disabled="selectedWebhookIds.length === 0">
          发送
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useProjectStore } from '@/stores'
import {
  getIterations, getMyScheduleItems, submitDailyReport,
  getMyDailyReports, generateAiReport, getFeishuWebhooks, sendReportToFeishu
} from '@/api/schedule'

const projectStore = useProjectStore()
const projectId = computed(() => projectStore.currentProject?.id)

const iterations = ref([])
const currentIterationId = ref(null)
const myItems = ref([])
const loading = ref(false)
const todayStr = new Date().toISOString().split('T')[0]

// 每个条目对应一个表单
const reportForms = reactive({})
const submitting = reactive({})
const aiGenerating = reactive({})

// 历史日报
const historyReports = ref([])

// 飞书
const showFeishuDialog = ref(false)
const feishuWebhooks = ref([])
const selectedWebhookIds = ref([])
const sendingFeishu = ref(false)
const currentFeishuReportId = ref(null)

function priorityTagType(p) {
  const map = { P0: 'danger', P1: 'warning', P2: '', P3: 'info' }
  return map[p] || ''
}
function progressColor(p) {
  if (p >= 80) return '#67c23a'
  if (p >= 50) return '#409eff'
  if (p >= 20) return '#e6a23c'
  return '#f56c6c'
}
function riskIcon(level) {
  const map = { none: '🟢', low: '🟡', medium: '🟠', high: '🔴' }
  return map[level] || '🟢'
}
function formatAiReport(content) {
  if (!content) return ''
  return content.replace(/\n/g, '<br>').replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
}
function copyReport(content) {
  navigator.clipboard.writeText(content)
  ElMessage.success('已复制到剪贴板')
}

async function loadIterations() {
  if (!projectId.value) return
  try {
    const res = await getIterations(projectId.value)
    const data = res.data || res
    iterations.value = data.iterations || data || []
    if (iterations.value.length > 0 && !currentIterationId.value) {
      const active = iterations.value.find(i => i.status === 'active')
      currentIterationId.value = active?.id || iterations.value[0].id
    }
  } catch (e) {
    console.error(e)
  }
}

async function loadMyItems() {
  if (!projectId.value || !currentIterationId.value) return
  loading.value = true
  try {
    const res = await getMyScheduleItems(projectId.value, { iteration_id: currentIterationId.value })
    const data = res.data || res
    const items = data.items || data || []
    myItems.value = items

    // 初始化表单
    items.forEach(item => {
      if (!reportForms[item.id]) {
        reportForms[item.id] = {
          today_progress: '',
          next_plan: '',
          bug_total: 0,
          bug_open: 0,
          bug_fixed: 0,
          bug_closed: 0,
          case_total: 0,
          case_executed: 0,
          case_passed: 0,
          case_failed: 0,
          actual_progress: item.actual_progress || 0,
          _report_id: item.today_report_id || null,
          _ai_content: null,
        }
      }
    })

    // 加载历史日报
    await loadHistory()
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function loadHistory() {
  if (!projectId.value || !currentIterationId.value) return
  try {
    const res = await getMyDailyReports(projectId.value, { iteration_id: currentIterationId.value })
    const data = res.data || res
    historyReports.value = data.reports || data || []
  } catch (e) {
    console.error(e)
  }
}

async function handleRefresh() {
  await loadMyItems()
  ElMessage.success('刷新成功')
}

async function handleSubmitReport(item) {
  const form = reportForms[item.id]
  if (!form.today_progress) return ElMessage.warning('请填写今日进展')

  submitting[item.id] = true
  try {
    const res = await submitDailyReport(projectId.value, {
      schedule_item_id: item.id,
      today_progress: form.today_progress,
      next_plan: form.next_plan,
      bug_total: form.bug_total,
      bug_open: form.bug_open,
      bug_fixed: form.bug_fixed,
      bug_closed: form.bug_closed,
      case_total: form.case_total,
      case_executed: form.case_executed,
      case_passed: form.case_passed,
      case_failed: form.case_failed,
      actual_progress: form.actual_progress,
    })

    const reportData = res.data || res
    form._report_id = reportData.id
    item.has_today_report = true
    ElMessage.success('日报提交成功')
    await loadHistory()
  } catch (e) {
    ElMessage.error('提交失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    submitting[item.id] = false
  }
}

async function handleGenerateAiReport(item) {
  const form = reportForms[item.id]
  if (!form._report_id) return ElMessage.warning('请先提交日报')

  aiGenerating[item.id] = true
  try {
    const res = await generateAiReport(projectId.value, form._report_id)
    const aiData = res.data || res
    form._ai_content = aiData.ai_report_content
    ElMessage.success('AI 报告已生成')
  } catch (e) {
    ElMessage.error('AI 报告生成失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    aiGenerating[item.id] = false
  }
}

async function handleSendFeishu(item) {
  const form = reportForms[item.id]
  if (!form._report_id) return ElMessage.warning('请先提交日报')
  currentFeishuReportId.value = form._report_id

  // 加载飞书群列表
  try {
    const res = await getFeishuWebhooks(projectId.value)
    const whData = res.data || res
    feishuWebhooks.value = whData.webhooks || whData || []
  } catch (e) {
    console.error(e)
  }

  selectedWebhookIds.value = []
  showFeishuDialog.value = true
}

async function confirmSendFeishu() {
  sendingFeishu.value = true
  try {
    const res = await sendReportToFeishu(projectId.value, currentFeishuReportId.value, {
      webhook_ids: selectedWebhookIds.value,
      report_id: currentFeishuReportId.value,
    })

    const results = res.results || res.data?.results || []
    const success = results.filter(r => r.success)
    const failed = results.filter(r => !r.success)

    if (success.length > 0) {
      ElMessage.success(`已成功发送到 ${success.length} 个群`)
    }
    if (failed.length > 0) {
      ElMessage.warning(`${failed.length} 个群发送失败`)
    }
    showFeishuDialog.value = false
  } catch (e) {
    ElMessage.error('发送失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    sendingFeishu.value = false
  }
}

onMounted(async () => {
  await loadIterations()
  await loadMyItems()
})

watch(projectId, () => {
  loadIterations()
})
</script>

<style scoped>
.daily-report-container {
  padding: 16px;
}
.report-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.my-items-card {
  margin-bottom: 16px;
}
.requirement-item {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  background: #fafafa;
}
.item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.item-title {
  display: flex;
  align-items: center;
  gap: 8px;
}
.title-text {
  font-weight: 600;
  font-size: 15px;
}
.item-meta {
  display: flex;
  align-items: center;
  gap: 12px;
}
.risk-badge {
  font-size: 18px;
}
.report-form {
  border-top: 1px solid #e4e7ed;
  padding-top: 12px;
}
.ai-report-preview {
  margin-top: 12px;
  padding: 16px;
  background: #f0f9ff;
  border: 1px solid #b3d8ff;
  border-radius: 8px;
}
.ai-report-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-weight: 600;
}
.ai-report-content {
  font-size: 14px;
  line-height: 1.6;
  color: #333;
}
.history-card {
  margin-bottom: 16px;
}
</style>
