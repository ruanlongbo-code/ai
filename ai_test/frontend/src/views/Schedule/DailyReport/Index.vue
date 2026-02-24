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
        <span>📋 此迭代下负责的需求</span>
      </template>

      <el-empty v-if="myItems.length === 0" description="当前迭代中暂无分配给你的需求" />

      <div v-for="item in myItems" :key="item.id" class="requirement-item">
        <div class="item-header">
          <div class="item-title">
            <el-tag v-if="item.priority" :type="priorityTagType(item.priority)" size="small" effect="plain">
              {{ item.priority }}
            </el-tag>
            <span class="title-text">{{ item.requirement_title }}</span>
            <el-tag v-if="item.category" size="small" type="info">{{ item.category }}</el-tag>
            <el-tag v-if="item.has_today_report" type="success" size="small">今日已同步</el-tag>
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

            <!-- ① 今日进展：标签选择 + 状态 + 补充说明 -->
            <el-form-item label="测试阶段" required>
              <div class="stage-tags-area">
                <el-checkbox-group v-model="reportForms[item.id].stage_tags" class="stage-tags">
                  <el-checkbox-button
                    v-for="tag in stageTagOptions"
                    :key="tag.key"
                    :value="tag.key"
                    class="stage-tag-btn"
                  >
                    {{ tag.label }}
                  </el-checkbox-button>
                </el-checkbox-group>
              </div>
            </el-form-item>

            <el-form-item label="进度状态">
              <el-radio-group v-model="reportForms[item.id].progress_status">
                <el-radio-button
                  v-for="opt in statusOptions"
                  :key="opt.key"
                  :value="opt.key"
                >
                  {{ opt.label }}
                </el-radio-button>
              </el-radio-group>
            </el-form-item>

            <el-form-item label="补充说明">
              <el-input
                v-model="reportForms[item.id].supplement"
                type="textarea"
                :rows="2"
                placeholder="选填：补充今日工作的额外说明（如遇到的问题、特殊情况等）"
              />
            </el-form-item>

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

            <!-- ⑥ Bug数据自动统计（从缺陷表读取 + 截图AI识别） -->
            <el-form-item label="缺陷概况">
              <div class="defect-stats-bar">
                <div class="stat-item">
                  <span class="stat-label">Bug总数</span>
                  <span class="stat-value">{{ reportForms[item.id].bug_total }}</span>
                </div>
                <div class="stat-item warning">
                  <span class="stat-label">待处理</span>
                  <span class="stat-value">{{ reportForms[item.id].bug_open }}</span>
                </div>
                <div class="stat-item success">
                  <span class="stat-label">已修复</span>
                  <span class="stat-value">{{ reportForms[item.id].bug_fixed }}</span>
                </div>
                <div class="stat-item info">
                  <span class="stat-label">已关闭</span>
                  <span class="stat-value">{{ reportForms[item.id].bug_closed }}</span>
                </div>
                <el-button size="small" link @click="handleViewDefects(item)">
                  📋 查看缺陷
                </el-button>
                <el-button size="small" link @click="handleRefreshDefectStats(item)">
                  🔄 刷新
                </el-button>
                <el-button size="small" link @click="openScreenshotDialog(item)">
                  📸 截图识别
                </el-button>
              </div>
            </el-form-item>

            <!-- 用例执行进度 -->
            <el-form-item label="用例执行进度">
              <div class="case-progress-area">
                <el-slider
                  v-model="reportForms[item.id].case_execution_progress"
                  :min="0" :max="100" :step="5"
                  style="flex: 1; min-width: 200px;"
                  show-stops
                />
                <span class="case-progress-value">{{ reportForms[item.id].case_execution_progress }}%</span>
              </div>
            </el-form-item>

            <!-- ② 进度智能计算 -->
            <el-form-item label="测试进度">
              <div class="progress-calc-area">
                <el-button type="primary" size="small" @click="handleCalcProgress(item)"
                           :loading="calcLoading[item.id]">
                  🧠 AI计算进度
                </el-button>
                <el-progress
                  :percentage="reportForms[item.id].actual_progress"
                  :stroke-width="14"
                  :color="progressColor(reportForms[item.id].actual_progress)"
                  style="flex: 1; min-width: 200px;"
                />
              </div>
              <!-- ±5 微调区域 -->
              <div class="progress-adjust-area">
                <span class="adjust-label">微调进度：</span>
                <el-button-group>
                  <el-button size="default" @click="adjustProgress(item, -5)" type="warning" plain>
                    <el-icon><Minus /></el-icon> 5%
                  </el-button>
                  <el-button size="default" disabled class="progress-value-btn"
                             :style="{ color: progressColor(reportForms[item.id].actual_progress) }">
                    {{ reportForms[item.id].actual_progress }}%
                  </el-button>
                  <el-button size="default" @click="adjustProgress(item, 5)" type="success" plain>
                    <el-icon><Plus /></el-icon> 5%
                  </el-button>
                </el-button-group>
                <span class="adjust-hint">（AI计算后可手动微调 ±5%）</span>
              </div>
              <!-- 计算因子展示 -->
              <div v-if="calcFactors[item.id]?.length" class="calc-factors">
                <div v-for="(f, idx) in calcFactors[item.id]" :key="idx" class="factor-item">
                  💡 {{ f }}
                </div>
              </div>
            </el-form-item>

            <el-form-item>
              <el-button type="primary" @click="handleSubmitReport(item)" :loading="submitting[item.id]">
                {{ item.has_today_report ? '更新测试进度' : '同步测试进度' }}
              </el-button>
              <el-button @click="handleGenerateAiReport(item)" :loading="aiGenerating[item.id]"
                        :disabled="!reportForms[item.id]._report_id">
                ✨ AI 生成报告
              </el-button>
              <el-button @click="handleSendFeishu(item)" :disabled="!reportForms[item.id]._report_id">
                📤 同步到需求群
              </el-button>
            </el-form-item>
          </el-form>

          <!-- ③ AI 生成的报告预览 - 可编辑 -->
          <div v-if="reportForms[item.id]._ai_content" class="ai-report-preview">
            <div class="ai-report-header">
              <span>✨ AI 生成的报告</span>
              <div class="ai-report-actions">
                <el-button size="small" @click="toggleEditAiReport(item)" type="primary" link>
                  {{ reportForms[item.id]._ai_editing ? '📖 预览' : '✏️ 编辑' }}
                </el-button>
                <el-button size="small" @click="saveAiReport(item)" type="success" link
                           v-if="reportForms[item.id]._ai_editing" :loading="aiSaving[item.id]">
                  💾 保存
                </el-button>
                <el-button size="small" @click="copyReport(reportForms[item.id]._ai_content)" link>📋 复制</el-button>
              </div>
            </div>
            <!-- 编辑模式 -->
            <el-input
              v-if="reportForms[item.id]._ai_editing"
              v-model="reportForms[item.id]._ai_content"
              type="textarea"
              :rows="10"
              class="ai-report-editor"
            />
            <!-- 预览模式 -->
            <div v-else class="ai-report-content" v-html="formatAiReport(reportForms[item.id]._ai_content)" />
          </div>
        </div>
      </div>
    </el-card>

    <!-- 历史记录 -->
    <el-card class="history-card" v-if="currentIterationId">
      <template #header>
        <span>📅 历史同步记录</span>
      </template>
      <el-table :data="historyReports" border stripe>
        <el-table-column prop="report_date" label="日期" width="110" />
        <el-table-column prop="requirement_title" label="需求" min-width="200" />
        <el-table-column label="进展" min-width="300" show-overflow-tooltip>
          <template #default="{ row }">
            {{ formatProgressDisplay(row.today_progress) }}
          </template>
        </el-table-column>
        <el-table-column label="Bug" width="120" align="center">
          <template #default="{ row }">
            {{ row.bug_total }}个({{ row.bug_open }}待处理)
          </template>
        </el-table-column>
        <el-table-column label="进度" width="80" align="center">
          <template #default="{ row }">{{ row.actual_progress }}%</template>
        </el-table-column>
        <el-table-column label="状态" width="70" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.feishu_sent" type="success" size="small">已同步</el-tag>
            <el-tag v-else type="info" size="small">未同步</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- ⑤ 飞书推送弹窗（自动匹配需求群） -->
    <el-dialog v-model="showFeishuDialog" title="同步到需求群" width="540px">
      <div v-if="matchedWebhooks.length > 0" class="matched-webhooks-hint">
        <el-alert title="已根据需求自动匹配到对应的需求群" type="success" :closable="false" show-icon />
      </div>
      <el-form>
        <el-form-item label="选择需求群">
          <el-checkbox-group v-model="selectedWebhookIds">
            <div v-for="wh in feishuWebhooks" :key="wh.id" class="webhook-check-item">
              <el-checkbox :value="wh.id">
              {{ wh.name }}
                <el-tag v-if="isWebhookMatched(wh.id)" type="success" size="small" style="margin-left: 4px;">自动匹配</el-tag>
                <el-tag v-if="wh.linked_requirement_names?.length" size="small" type="info" style="margin-left: 4px;">
                  {{ wh.linked_requirement_names.join('、') }}
                </el-tag>
                <el-tag v-else-if="!wh.linked_schedule_item_ids?.length" size="small" type="warning" style="margin-left: 4px;">
                  全局群
                </el-tag>
            </el-checkbox>
            </div>
          </el-checkbox-group>
          <el-empty v-if="feishuWebhooks.length === 0" description="暂未配置需求群，请在「需求群管理」中添加" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showFeishuDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmSendFeishu" :loading="sendingFeishu"
                  :disabled="selectedWebhookIds.length === 0">
          同步
        </el-button>
      </template>
    </el-dialog>

    <!-- ⑦ 快捷提Bug弹窗 -->
    <el-dialog v-model="showDefectDialog" title="快捷提交缺陷" width="680px" destroy-on-close>
      <el-form :model="defectForm" label-width="100px" ref="defectFormRef">
        <el-form-item label="关联需求">
          <el-input :value="defectForm._requirement_title" disabled />
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
                <el-option v-for="u in assignableUsers" :key="u.id" :label="u.real_name || u.username" :value="u.id" />
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
              <el-input v-model="defectForm.expected_result" type="textarea" :rows="2" placeholder="正确行为应该是..." />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="实际结果">
              <el-input v-model="defectForm.actual_result" type="textarea" :rows="2" placeholder="实际表现是..." />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="showDefectDialog = false">取消</el-button>
        <el-button @click="handleAiExpandDefect" :loading="aiExpandLoading" :disabled="!defectForm.title">
          🧠 AI扩写描述
        </el-button>
        <el-button type="primary" @click="handleCreateDefect(false)" :loading="defectSubmitting"
                  :disabled="!defectForm.title">
          提交缺陷
        </el-button>
        <el-button type="success" @click="handleCreateDefect(true)" :loading="defectSubmitting"
                  :disabled="!defectForm.title">
          提交并同步到飞书
        </el-button>
      </template>
    </el-dialog>

    <!-- 截图识别缺陷数据弹窗 -->
    <el-dialog v-model="showScreenshotDialog" title="📸 截图识别缺陷数据" width="720px" destroy-on-close
               @opened="onScreenshotDialogOpened" @closed="onScreenshotDialogClosed">
      <!-- 步骤1: 粘贴/上传截图 -->
      <div v-if="!screenshotResult" class="screenshot-dialog-body">
        <div class="screenshot-paste-zone"
             ref="pasteZoneRef"
             tabindex="0"
             @paste="handlePasteScreenshot"
             @dragover.prevent
             @drop.prevent="handleDropScreenshot"
             @click="triggerScreenshotFileInput"
             :class="{ 'has-image': screenshotPreviewUrl }">
          <template v-if="!screenshotPreviewUrl">
            <div class="paste-zone-icon">📋</div>
            <div class="paste-zone-title">粘贴截图到此处</div>
            <div class="paste-zone-hint">
              使用 <kbd>Ctrl</kbd>+<kbd>V</kbd> / <kbd>Cmd</kbd>+<kbd>V</kbd> 粘贴截图<br>
              或 <span class="paste-zone-link">点击此处</span> 选择图片文件<br>
              也支持拖拽图片到此区域
            </div>
          </template>
          <template v-else>
            <img :src="screenshotPreviewUrl" class="screenshot-preview-img" alt="截图预览" />
          </template>
        </div>
        <input type="file" ref="screenshotFileInputRef" accept="image/*"
               style="display: none" @change="handleFileInputChange" />

        <div v-if="screenshotPreviewUrl" class="screenshot-preview-actions">
          <el-tag type="success" size="small">✓ 截图已就绪</el-tag>
          <el-button size="small" type="danger" link @click="clearScreenshot">清除重选</el-button>
        </div>
      </div>

      <!-- 步骤2: 识别结果展示 -->
      <div v-if="screenshotResult" class="screenshot-result-area">
        <div class="result-preview-row">
          <img :src="screenshotPreviewUrl" class="result-preview-thumb" alt="识别的截图" />
          <div class="result-stats-grid">
            <div class="result-stat-card">
              <div class="result-stat-num">{{ screenshotResult.bug_total || 0 }}</div>
              <div class="result-stat-label">Bug总数</div>
            </div>
            <div class="result-stat-card warning">
              <div class="result-stat-num">{{ screenshotResult.bug_open || 0 }}</div>
              <div class="result-stat-label">待处理</div>
            </div>
            <div class="result-stat-card success">
              <div class="result-stat-num">{{ screenshotResult.bug_fixed || 0 }}</div>
              <div class="result-stat-label">已修复</div>
            </div>
            <div class="result-stat-card info">
              <div class="result-stat-num">{{ screenshotResult.bug_closed || 0 }}</div>
              <div class="result-stat-label">已关闭</div>
            </div>
          </div>
        </div>

        <!-- 按严重等级统计 -->
        <div v-if="screenshotResult.by_severity" class="result-severity-row">
          <el-tag v-for="(count, level) in screenshotResult.by_severity" :key="level"
                  :type="severityTagType(level)" style="margin-right: 8px;">
            {{ level }}: {{ count }}个
          </el-tag>
        </div>

        <!-- 缺陷明细列表 -->
        <div v-if="screenshotResult.details?.length" class="result-details">
          <div class="result-details-title">识别到的缺陷明细</div>
          <el-table :data="screenshotResult.details" border size="small" max-height="200">
            <el-table-column prop="title" label="缺陷摘要" min-width="200" show-overflow-tooltip />
            <el-table-column prop="severity" label="等级" width="70" align="center">
              <template #default="{ row }">
                <el-tag :type="severityTagType(row.severity)" size="small">{{ row.severity }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="90" align="center" />
          </el-table>
        </div>

        <el-button size="small" link @click="resetScreenshotDialog" style="margin-top: 12px;">
          🔄 重新识别
        </el-button>
      </div>

      <template #footer>
        <el-button @click="showScreenshotDialog = false">取消</el-button>
        <el-button v-if="!screenshotResult" type="primary" @click="submitScreenshotAnalysis"
                   :loading="screenshotAnalyzing" :disabled="!screenshotFile">
          🧠 开始AI识别
        </el-button>
        <el-button v-if="screenshotResult" type="success" @click="syncScreenshotResultToReport">
          ✅ 同步到报告
        </el-button>
      </template>
    </el-dialog>

    <!-- 缺陷列表弹窗 -->
    <el-dialog v-model="showDefectListDialog" title="缺陷列表" width="900px" destroy-on-close>
      <div class="defect-list-header">
        <el-tag>共 {{ defectList.length }} 个缺陷</el-tag>
        <el-button size="small" type="primary" @click="handleQuickDefectFromList">➕ 新建缺陷</el-button>
      </div>
      <el-table :data="defectList" border stripe style="margin-top: 12px">
        <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
        <el-table-column prop="defect_type" label="类型" width="90" align="center">
          <template #default="{ row }">
            {{ defectTypeLabel(row.defect_type) }}
          </template>
        </el-table-column>
        <el-table-column prop="severity" label="等级" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="severityTagType(row.severity)" size="small">{{ row.severity }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="defect_status" label="状态" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="defectStatusTagType(row.defect_status)" size="small">
              {{ defectStatusLabel(row.defect_status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="assignee_name" label="经办人" width="90" />
        <el-table-column prop="reporter_name" label="报告人" width="90" />
        <el-table-column label="飞书" width="80" align="center">
          <template #default="{ row }">
            <el-link v-if="row.feishu_ticket_url" type="primary" :href="row.feishu_ticket_url" target="_blank"
                     size="small">查看</el-link>
            <el-button v-else type="primary" link size="small" @click="handleSyncDefectToFeishu(row)"
                       :loading="syncingDefect[row.id]">同步</el-button>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" align="center">
          <template #default="{ row }">
            <el-select v-model="row.defect_status" size="small" style="width: 100px"
                       @change="handleUpdateDefectStatus(row)">
              <el-option label="待处理" value="open" />
              <el-option label="修复中" value="fixing" />
              <el-option label="已修复" value="fixed" />
              <el-option label="已验证" value="verified" />
              <el-option label="已关闭" value="closed" />
              <el-option label="已拒绝" value="rejected" />
            </el-select>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { Refresh, Plus, Minus } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useProjectStore } from '@/stores'
import {
  getIterations, getMyScheduleItems, submitDailyReport,
  getMyDailyReports, generateAiReport, getFeishuWebhooks, sendReportToFeishu,
  updateAiReportContent, calculateProgress, getProgressOptions,
  createDefect, getDefects, updateDefect, getDefectStats,
  aiExpandDefect, aiExpandDefectPreview, getMatchedWebhooks, getAssignableUsers,
  syncDefectToFeishu, analyzeScreenshot
} from '@/api/schedule'

const projectStore = useProjectStore()
const projectId = computed(() => projectStore.currentProject?.id)

const iterations = ref([])
const currentIterationId = ref(null)
const myItems = ref([])
const loading = ref(false)
// 使用本地日期（避免UTC时区导致日期不匹配）
const todayStr = (() => {
  const d = new Date()
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
})()

// 每个条目对应一个表单
const reportForms = reactive({})
const submitting = reactive({})
const aiGenerating = reactive({})
const aiSaving = reactive({})
const calcLoading = reactive({})
const calcFactors = reactive({})

// 测试阶段标签选项（按软件测试流程正序）
const stageTagOptions = ref([
  { key: 'requirement_clarify', label: '参与需求澄清' },
  { key: 'tech_review', label: '参与技术评审' },
  { key: 'case_writing', label: '用例编写' },
  { key: 'case_review', label: '用例评审' },
  { key: 'smoke_test', label: '冒烟测试' },
  { key: 'first_round_test', label: '一轮测试' },
  { key: 'functional_test', label: '功能测试' },
  { key: 'exploratory_test', label: '探索性测试' },
  { key: 'cross_test', label: '交叉测试' },
  { key: 'regression_test', label: '回归测试' },
  { key: 'bug_verify', label: 'Bug验证' },
])

// 未进入正式测试的阶段
const PRE_TESTING_STAGES = new Set(['requirement_clarify', 'tech_review', 'case_writing', 'case_review'])

// 判断是否全部是预测试阶段（此时不需要填写用例/Bug等数据）
function isPreTestingOnly(stageTags) {
  if (!stageTags || stageTags.length === 0) return true
  return stageTags.every(t => PRE_TESTING_STAGES.has(t))
}

// ====== 截图识别弹窗 ======
const showScreenshotDialog = ref(false)
const screenshotFile = ref(null)          // File对象
const screenshotPreviewUrl = ref('')      // 预览URL
const screenshotAnalyzing = ref(false)    // 正在AI分析
const screenshotResult = ref(null)        // AI识别结果
const screenshotTargetItem = ref(null)    // 当前操作的需求条目
const pasteZoneRef = ref(null)
const screenshotFileInputRef = ref(null)

const statusOptions = ref([
  { key: 'normal', label: '正常推进' },
  { key: 'blocked', label: '阻塞等待' },
  { key: 'ahead', label: '提前完成' },
  { key: 'delayed', label: '进度延迟' },
])

// 历史日报
const historyReports = ref([])

// 飞书
const showFeishuDialog = ref(false)
const feishuWebhooks = ref([])
const matchedWebhooks = ref([])
const selectedWebhookIds = ref([])
const sendingFeishu = ref(false)
const currentFeishuReportId = ref(null)

// 缺陷
const showDefectDialog = ref(false)
const showDefectListDialog = ref(false)
const defectForm = reactive({
  schedule_item_id: null,
  _requirement_title: '',
  title: '',
  description: '',
  defect_type: 'functional',
  severity: 'P2',
  assignee_id: null,
  reproduce_steps: '',
  expected_result: '',
  actual_result: '',
})
const defectSubmitting = ref(false)
const aiExpandLoading = ref(false)
const syncingDefect = reactive({})
const defectList = ref([])
const assignableUsers = ref([])
const currentDefectItem = ref(null)

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
function defectTypeLabel(t) {
  const map = { functional: '功能', ui: '界面', performance: '性能', compatibility: '兼容', other: '其他' }
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
function isWebhookMatched(whId) {
  return matchedWebhooks.value.some(m => m.id === whId)
}

// ① 将标签选择组合成today_progress文本
function buildTodayProgress(form) {
  const tags = (form.stage_tags || []).map(key => {
    const t = stageTagOptions.value.find(s => s.key === key)
    return t ? t.label : key
  })
  const status = statusOptions.value.find(s => s.key === form.progress_status)
  const statusText = status ? status.label : '正常推进'

  const parts = []
  if (tags.length > 0) parts.push(`【测试阶段】${tags.join('、')}`)
  parts.push(`【进度状态】${statusText}`)
  if (form.supplement) parts.push(`【补充说明】${form.supplement}`)

  return parts.join('\n')
}

// 解析 today_progress 文本回标签（兼容历史纯文本）
function formatProgressDisplay(text) {
  if (!text) return ''
  try {
    // 尝试解析结构化文本
    if (text.includes('【测试阶段】')) {
      return text.replace(/\n/g, ' | ')
    }
  } catch (e) { /* ignore */ }
  return text
}

function adjustProgress(item, delta) {
  const form = reportForms[item.id]
  form.actual_progress = Math.max(0, Math.min(100, form.actual_progress + delta))
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
    for (const item of items) {
      if (!reportForms[item.id]) {
        reportForms[item.id] = {
          stage_tags: [],
          progress_status: 'normal',
          supplement: '',
          next_plan: '',
          bug_total: 0,
          bug_open: 0,
          bug_fixed: 0,
          bug_closed: 0,
          case_execution_progress: 0,
          actual_progress: item.actual_progress || 0,
          _report_id: item.today_report_id || null,
          _ai_content: null,
          _ai_editing: false,
        }
      }
    }

    // 先加载历史日报
    await loadHistory()

    // 对每个条目：如果今天已提交过报告，从报告恢复数据；否则从缺陷表统计
    for (const item of items) {
      const todayReport = findTodayReport(item.id)
      if (todayReport) {
        // 今天已有报告 → 使用报告中保存的数据（含截图识别的数据）
        restoreFormFromReport(item.id, todayReport)
      } else {
        // 今天没有报告 → 从缺陷表加载初始值
        await refreshDefectStats(item)
      }
    }

    // 加载可分配用户
    await loadAssignableUsers()
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function refreshDefectStats(item) {
  if (!projectId.value) return
  try {
    const res = await getDefectStats(projectId.value, item.id)
    const stats = res.data || res
    if (reportForms[item.id]) {
      reportForms[item.id].bug_total = stats.total || 0
      reportForms[item.id].bug_open = (stats.open || 0) + (stats.fixing || 0)
      reportForms[item.id].bug_fixed = stats.fixed || 0
      reportForms[item.id].bug_closed = (stats.closed || 0) + (stats.verified || 0)
    }
  } catch (e) {
    // 没有缺陷数据时不报错
    console.debug('缺陷统计:', e)
  }
}

// 缺陷概况区域的🔄刷新按钮：优先从今日报告恢复（保留截图识别数据），无报告时才从缺陷表统计
async function handleRefreshDefectStats(item) {
  await loadHistory()
  const todayReport = findTodayReport(item.id)
  if (todayReport) {
    // 今天已有报告 → 恢复报告中的bug数据
    restoreFormFromReport(item.id, todayReport)
    ElMessage.success('已从今日报告恢复缺陷数据')
  } else {
    // 今天无报告 → 从缺陷表统计
    await refreshDefectStats(item)
    ElMessage.success('已从缺陷表刷新统计')
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

// 查找指定排期条目的今日报告
function findTodayReport(scheduleItemId) {
  if (!historyReports.value || historyReports.value.length === 0) return null
  const today = todayStr
  return historyReports.value.find(r => r.report_date === today && r.schedule_item_id === scheduleItemId) || null
}

// 从报告恢复表单数据（保证截图识别的bug数据不丢失）
function restoreFormFromReport(scheduleItemId, report) {
  const form = reportForms[scheduleItemId]
  if (!form || !report) return

  // 恢复bug数据（截图识别或手动填写的数据）
  form.bug_total = report.bug_total ?? form.bug_total
  form.bug_open = report.bug_open ?? form.bug_open
  form.bug_fixed = report.bug_fixed ?? form.bug_fixed
  form.bug_closed = report.bug_closed ?? form.bug_closed

  // 恢复用例执行进度
  if (report.case_execution_progress != null) {
    form.case_execution_progress = report.case_execution_progress
  }

  // 恢复进度
  if (report.actual_progress != null) {
    form.actual_progress = report.actual_progress
  }

  // 恢复报告ID和AI内容
  form._report_id = report.id
  if (report.ai_report_content) {
    form._ai_content = report.ai_report_content
  }

  // 尝试恢复stage_tags和其他字段（从today_progress文本解析）
  if (report.today_progress) {
    restoreProgressFields(form, report.today_progress)
  }
  if (report.next_plan) {
    form.next_plan = report.next_plan
  }
}

// 从today_progress结构化文本解析回表单字段
function restoreProgressFields(form, text) {
  if (!text) return
  // 解析【测试阶段】
  const stageMatch = text.match(/【测试阶段】(.+?)(?:\n|$)/)
  if (stageMatch) {
    const stageLabels = stageMatch[1].split('、').map(s => s.trim())
    const tags = []
    for (const label of stageLabels) {
      const opt = stageTagOptions.value.find(o => o.label === label)
      if (opt) tags.push(opt.key)
    }
    if (tags.length > 0) form.stage_tags = tags
  }
  // 解析【进度状态】
  const statusMatch = text.match(/【进度状态】(.+?)(?:\n|$)/)
  if (statusMatch) {
    const statusLabel = statusMatch[1].trim()
    const opt = statusOptions.value.find(o => o.label === statusLabel)
    if (opt) form.progress_status = opt.key
  }
  // 解析【补充说明】
  const suppMatch = text.match(/【补充说明】(.+?)(?:\n|$)/)
  if (suppMatch) {
    form.supplement = suppMatch[1].trim()
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

async function handleRefresh() {
  await loadMyItems()
  ElMessage.success('刷新成功')
}

// ② AI计算进度
async function handleCalcProgress(item) {
  const form = reportForms[item.id]
  if (form.stage_tags.length === 0) {
    return ElMessage.warning('请先选择测试阶段')
  }
  calcLoading[item.id] = true
  try {
    const res = await calculateProgress(projectId.value, {
      schedule_item_id: item.id,
      stage_tags: form.stage_tags,
      progress_status: form.progress_status,
      case_execution_progress: form.case_execution_progress || null,
    })
    const data = res.data || res
    form.actual_progress = data.suggested_progress
    calcFactors[item.id] = data.factors || []
    ElMessage.success(`AI建议进度: ${data.suggested_progress}%`)
  } catch (e) {
    ElMessage.error('进度计算失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    calcLoading[item.id] = false
  }
}

async function handleSubmitReport(item) {
  const form = reportForms[item.id]
  if (form.stage_tags.length === 0) return ElMessage.warning('请至少选择一个测试阶段')

  const todayProgress = buildTodayProgress(form)

  submitting[item.id] = true
  try {
    const res = await submitDailyReport(projectId.value, {
      schedule_item_id: item.id,
      today_progress: todayProgress,
      next_plan: form.next_plan,
      stage_tags: form.stage_tags,
      case_execution_progress: form.case_execution_progress || 0,
      actual_progress: form.actual_progress,
      bug_total: form.bug_total,
      bug_open: form.bug_open,
      bug_fixed: form.bug_fixed,
      bug_closed: form.bug_closed,
    })

    const reportData = res.data || res
    form._report_id = reportData.id
    item.has_today_report = true
    ElMessage.success('测试进度同步成功')
    await loadHistory()
  } catch (e) {
    ElMessage.error('同步失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    submitting[item.id] = false
  }
}

async function handleGenerateAiReport(item) {
  const form = reportForms[item.id]
  if (!form._report_id) return ElMessage.warning('请先同步测试进度')

  aiGenerating[item.id] = true
  try {
    const res = await generateAiReport(projectId.value, form._report_id)
    const aiData = res.data || res
    form._ai_content = aiData.ai_report_content
    form._ai_editing = false
    ElMessage.success('AI 报告已生成')
  } catch (e) {
    ElMessage.error('AI 报告生成失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    aiGenerating[item.id] = false
  }
}

// ③ 编辑/保存AI报告
function toggleEditAiReport(item) {
  const form = reportForms[item.id]
  form._ai_editing = !form._ai_editing
}

async function saveAiReport(item) {
  const form = reportForms[item.id]
  if (!form._report_id || !form._ai_content) return

  aiSaving[item.id] = true
  try {
    await updateAiReportContent(projectId.value, form._report_id, {
      ai_report_content: form._ai_content
    })
    form._ai_editing = false
    ElMessage.success('报告已保存')
  } catch (e) {
    ElMessage.error('保存失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    aiSaving[item.id] = false
  }
}

// ⑤ 飞书同步 - 自动匹配
async function handleSendFeishu(item) {
  const form = reportForms[item.id]
  if (!form._report_id) return ElMessage.warning('请先同步测试进度')
  currentFeishuReportId.value = form._report_id

  // 加载飞书群列表
  try {
    const res = await getFeishuWebhooks(projectId.value)
    const whData = res.data || res
    feishuWebhooks.value = whData.webhooks || whData || []
  } catch (e) {
    console.error(e)
  }

  // 自动匹配
  try {
    const matchRes = await getMatchedWebhooks(projectId.value, form._report_id)
    const matchData = matchRes.data || matchRes
    matchedWebhooks.value = matchData.matched_webhooks || []
    // 自动勾选匹配的群
    selectedWebhookIds.value = matchedWebhooks.value.map(m => m.id)
  } catch (e) {
    matchedWebhooks.value = []
  selectedWebhookIds.value = []
  }

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
      ElMessage.success(`已成功同步到 ${success.length} 个需求群`)
    }
    if (failed.length > 0) {
      ElMessage.warning(`${failed.length} 个群同步失败`)
    }
    showFeishuDialog.value = false
  } catch (e) {
    ElMessage.error('同步失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    sendingFeishu.value = false
  }
}

// ⑦ 快捷提Bug
function handleQuickDefect(item) {
  currentDefectItem.value = item
  Object.assign(defectForm, {
    schedule_item_id: item.id,
    _requirement_title: item.requirement_title,
    title: '',
    description: '',
    defect_type: 'functional',
    severity: 'P2',
    assignee_id: null,
    reproduce_steps: '',
    expected_result: '',
    actual_result: '',
  })
  showDefectDialog.value = true
}

function handleQuickDefectFromList() {
  showDefectListDialog.value = false
  if (currentDefectItem.value) {
    handleQuickDefect(currentDefectItem.value)
  }
}

async function handleCreateDefect(syncToFeishu = false) {
  if (!defectForm.title) return ElMessage.warning('请输入缺陷标题')
  defectSubmitting.value = true
  try {
    const createRes = await createDefect(projectId.value, {
      schedule_item_id: defectForm.schedule_item_id,
      title: defectForm.title,
      description: defectForm.description,
      defect_type: defectForm.defect_type,
      severity: defectForm.severity,
      assignee_id: defectForm.assignee_id,
      reproduce_steps: defectForm.reproduce_steps,
      expected_result: defectForm.expected_result,
      actual_result: defectForm.actual_result,
    })
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

    showDefectDialog.value = false
    // 刷新缺陷统计
    if (currentDefectItem.value) {
      await refreshDefectStats(currentDefectItem.value)
    }
  } catch (e) {
    ElMessage.error('提交失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    defectSubmitting.value = false
  }
}

async function handleSyncDefectToFeishu(row) {
  syncingDefect[row.id] = true
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
    syncingDefect[row.id] = false
  }
}

async function handleAiExpandDefect() {
  if (!defectForm.title) return ElMessage.warning('请先输入缺陷标题')

  aiExpandLoading.value = true
  try {
    // 直接调用AI扩写预览接口，不创建缺陷记录
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

// ====== 截图识别弹窗逻辑 ======

// 打开弹窗
function openScreenshotDialog(item) {
  screenshotTargetItem.value = item
  screenshotFile.value = null
  screenshotPreviewUrl.value = ''
  screenshotResult.value = null
  screenshotAnalyzing.value = false
  showScreenshotDialog.value = true
}

// 弹窗打开后自动聚焦粘贴区域
function onScreenshotDialogOpened() {
  nextTick(() => {
    pasteZoneRef.value?.focus()
  })
}

// 弹窗关闭时清理URL
function onScreenshotDialogClosed() {
  if (screenshotPreviewUrl.value) {
    URL.revokeObjectURL(screenshotPreviewUrl.value)
  }
  screenshotPreviewUrl.value = ''
  screenshotFile.value = null
  screenshotResult.value = null
}

// 设置截图文件并生成预览
function setScreenshotFile(file) {
  if (screenshotPreviewUrl.value) {
    URL.revokeObjectURL(screenshotPreviewUrl.value)
  }
  screenshotFile.value = file
  screenshotPreviewUrl.value = URL.createObjectURL(file)
  screenshotResult.value = null // 清除旧结果
}

// 处理 Ctrl+V 粘贴
function handlePasteScreenshot(event) {
  const items = event.clipboardData?.items
  if (!items) return
  for (const item of items) {
    if (item.type.startsWith('image/')) {
      const file = item.getAsFile()
      if (file) {
        setScreenshotFile(file)
        ElMessage.success('截图已粘贴')
        return
      }
    }
  }
  ElMessage.warning('剪贴板中没有图片，请先截图再粘贴')
}

// 处理拖拽
function handleDropScreenshot(event) {
  const files = event.dataTransfer?.files
  if (files && files.length > 0) {
    const file = files[0]
    if (file.type.startsWith('image/')) {
      setScreenshotFile(file)
      ElMessage.success('图片已添加')
    } else {
      ElMessage.warning('请拖入图片文件')
    }
  }
}

// 点击触发文件选择
function triggerScreenshotFileInput() {
  if (!screenshotPreviewUrl.value) {
    screenshotFileInputRef.value?.click()
  }
}

// 文件选择回调
function handleFileInputChange(event) {
  const file = event.target.files?.[0]
  if (file && file.type.startsWith('image/')) {
    setScreenshotFile(file)
    ElMessage.success('图片已选择')
  }
  // 清空 input 以允许重复选择同一文件
  event.target.value = ''
}

// 清除截图
function clearScreenshot() {
  if (screenshotPreviewUrl.value) {
    URL.revokeObjectURL(screenshotPreviewUrl.value)
  }
  screenshotFile.value = null
  screenshotPreviewUrl.value = ''
  screenshotResult.value = null
}

// 重置弹窗到初始状态
function resetScreenshotDialog() {
  clearScreenshot()
  nextTick(() => {
    pasteZoneRef.value?.focus()
  })
}

// 提交AI识别
async function submitScreenshotAnalysis() {
  if (!screenshotFile.value) return ElMessage.warning('请先粘贴或上传截图')
  screenshotAnalyzing.value = true
  try {
    const res = await analyzeScreenshot(projectId.value, screenshotFile.value)
    const result = res.data || res
    if (result.success && result.data) {
      screenshotResult.value = result.data
      ElMessage.success('AI识别完成')
    } else {
      ElMessage.warning(result.message || '截图识别失败，请重试')
    }
  } catch (e) {
    ElMessage.error('截图分析失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    screenshotAnalyzing.value = false
  }
}

// 同步识别结果到报告表单
function syncScreenshotResultToReport() {
  const item = screenshotTargetItem.value
  const data = screenshotResult.value
  if (!item || !data) return

  const form = reportForms[item.id]
  if (form) {
    form.bug_total = data.bug_total || 0
    form.bug_open = data.bug_open || 0
    form.bug_fixed = data.bug_fixed || 0
    form.bug_closed = data.bug_closed || 0
  }
  showScreenshotDialog.value = false
  ElMessage.success(`已同步: 共${data.bug_total}个缺陷，${data.bug_open}个待处理，${data.bug_fixed}个已修复，${data.bug_closed}个已关闭`)
}

// 查看缺陷列表
async function handleViewDefects(item) {
  currentDefectItem.value = item
  try {
    const res = await getDefects(projectId.value, { schedule_item_id: item.id })
    const data = res.data || res
    defectList.value = data.defects || data || []
    showDefectListDialog.value = true
  } catch (e) {
    ElMessage.error('加载缺陷列表失败')
  }
}

async function handleUpdateDefectStatus(row) {
  try {
    await updateDefect(projectId.value, row.id, { defect_status: row.defect_status })
    ElMessage.success('状态已更新')
    // 刷新统计
    if (currentDefectItem.value) {
      await refreshDefectStats(currentDefectItem.value)
    }
  } catch (e) {
    ElMessage.error('更新失败')
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

/* ① 测试阶段标签 */
.stage-tags-area {
  width: 100%;
}
.stage-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}
.stage-tag-btn {
  margin: 0 !important;
}

/* ② 进度计算 */
.progress-calc-area {
  display: flex;
  align-items: center;
  gap: 16px;
  width: 100%;
}
/* ±5 微调区域 */
.progress-adjust-area {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 10px;
  padding: 8px 12px;
  background: #f5f7fa;
  border-radius: 6px;
  border: 1px dashed #dcdfe6;
}
.adjust-label {
  font-size: 13px;
  color: #606266;
  font-weight: 500;
  white-space: nowrap;
}
.adjust-hint {
  font-size: 12px;
  color: #909399;
  white-space: nowrap;
}
.progress-value-btn {
  font-size: 18px !important;
  font-weight: 700 !important;
  min-width: 60px !important;
}
/* 用例执行进度 */
.case-progress-area {
  display: flex;
  align-items: center;
  gap: 16px;
  width: 100%;
}
.case-progress-value {
  font-size: 16px;
  font-weight: 600;
  color: #409eff;
  min-width: 50px;
}
/* ====== 截图识别弹窗 ====== */
.screenshot-dialog-body {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}
.screenshot-paste-zone {
  width: 100%;
  min-height: 240px;
  border: 2px dashed #dcdfe6;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s;
  background: #fafbfc;
  outline: none;
  padding: 20px;
}
.screenshot-paste-zone:hover,
.screenshot-paste-zone:focus {
  border-color: #409eff;
  background: #f0f7ff;
}
.screenshot-paste-zone.has-image {
  cursor: default;
  border-style: solid;
  border-color: #67c23a;
  background: #f0f9eb;
  padding: 12px;
}
.paste-zone-icon {
  font-size: 48px;
  margin-bottom: 12px;
}
.paste-zone-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
}
.paste-zone-hint {
  font-size: 13px;
  color: #909399;
  text-align: center;
  line-height: 2;
}
.paste-zone-hint kbd {
  background: #ebeef5;
  border: 1px solid #dcdfe6;
  border-radius: 3px;
  padding: 1px 5px;
  font-size: 12px;
  font-family: inherit;
  color: #606266;
}
.paste-zone-link {
  color: #409eff;
  cursor: pointer;
  text-decoration: underline;
}
.screenshot-preview-img {
  max-width: 100%;
  max-height: 360px;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.1);
}
.screenshot-preview-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
}

/* 识别结果 */
.screenshot-result-area {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.result-preview-row {
  display: flex;
  gap: 20px;
  align-items: flex-start;
}
.result-preview-thumb {
  max-width: 220px;
  max-height: 160px;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
  flex-shrink: 0;
  object-fit: contain;
}
.result-stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  flex: 1;
}
.result-stat-card {
  background: #f5f7fa;
  border-radius: 8px;
  padding: 16px;
  text-align: center;
  border: 1px solid #e4e7ed;
}
.result-stat-card.warning {
  background: #fef0e0;
  border-color: #f5dab1;
}
.result-stat-card.success {
  background: #e8f8e0;
  border-color: #b3e19d;
}
.result-stat-card.info {
  background: #f0f2f5;
  border-color: #d3d8e0;
}
.result-stat-num {
  font-size: 28px;
  font-weight: 700;
  color: #303133;
  line-height: 1.2;
}
.result-stat-card.warning .result-stat-num { color: #e6a23c; }
.result-stat-card.success .result-stat-num { color: #67c23a; }
.result-stat-card.info .result-stat-num { color: #909399; }
.result-stat-label {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
.result-severity-row {
  padding: 8px 0;
}
.result-details {
  border-top: 1px solid #ebeef5;
  padding-top: 12px;
}
.result-details-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
}
.calc-factors {
  margin-top: 8px;
  padding: 8px 12px;
  background: #f0f9ff;
  border-radius: 6px;
  font-size: 12px;
  color: #666;
}
.factor-item {
  line-height: 1.8;
}

/* ⑥ 缺陷统计栏 */
.defect-stats-bar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 8px 16px;
  background: #f5f7fa;
  border-radius: 8px;
  width: 100%;
}
.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}
.stat-label {
  font-size: 12px;
  color: #909399;
}
.stat-value {
  font-size: 18px;
  font-weight: 700;
  color: #303133;
}
.stat-item.warning .stat-value { color: #e6a23c; }
.stat-item.success .stat-value { color: #67c23a; }
.stat-item.info .stat-value { color: #909399; }

/* ③ AI报告 */
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
.ai-report-actions {
  display: flex;
  gap: 4px;
}
.ai-report-content {
  font-size: 14px;
  line-height: 1.6;
  color: #333;
}
.ai-report-editor {
  margin-top: 8px;
}

/* 飞书弹窗 */
.matched-webhooks-hint {
  margin-bottom: 12px;
}
.webhook-check-item {
  padding: 6px 0;
}

/* 缺陷列表 */
.defect-list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.history-card {
  margin-bottom: 16px;
}
</style>
