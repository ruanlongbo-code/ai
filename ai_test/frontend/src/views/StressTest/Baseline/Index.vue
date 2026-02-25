<template>
  <div class="baseline-container">
    <div class="page-header">
      <div class="header-left">
        <h2>基线管理</h2>
        <span class="subtitle">管理性能基准线，AI 自动检测性能回归</span>
      </div>
      <div class="header-right">
        <el-button type="primary" :icon="Plus" @click="openCreateDialog">创建基线</el-button>
      </div>
    </div>

    <!-- 基线列表 -->
    <el-row :gutter="16">
      <el-col :span="8" v-for="baseline in baselines" :key="baseline.id">
        <el-card shadow="hover" class="baseline-card" :class="{ active: baseline.is_active }">
          <template #header>
            <div class="card-header">
              <div>
                <span class="baseline-name">{{ baseline.name }}</span>
                <el-tag v-if="baseline.is_active" type="success" size="small" style="margin-left: 6px">当前生效</el-tag>
              </div>
              <el-dropdown trigger="click" @command="(cmd) => handleCardCommand(cmd, baseline)">
                <el-button text :icon="MoreFilled" />
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="activate" :disabled="baseline.is_active">设为当前基线</el-dropdown-item>
                    <el-dropdown-item command="delete" divided>删除</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </template>

          <div class="baseline-info">
            <div class="info-row">
              <span class="info-label">版本</span>
              <el-tag size="small" type="info">{{ baseline.version || '-' }}</el-tag>
            </div>
            <div class="info-row">
              <span class="info-label">环境</span>
              <el-tag size="small" :type="envTag[baseline.environment]">{{ envName[baseline.environment] || '-' }}</el-tag>
            </div>
            <div class="info-row">
              <span class="info-label">来源任务</span>
              <span>{{ baseline.source_task_id ? `#${baseline.source_task_id}` : '手动创建' }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">创建时间</span>
              <span>{{ new Date(baseline.created_at).toLocaleDateString('zh-CN') }}</span>
            </div>
          </div>

          <!-- 基线指标概要 -->
          <div v-if="baseline.baseline_metrics?.overall" class="baseline-metrics">
            <div class="mini-metric">
              <span class="mini-value">{{ baseline.baseline_metrics.overall.tps?.toFixed(1) }}</span>
              <span class="mini-label">TPS</span>
            </div>
            <div class="mini-metric">
              <span class="mini-value">{{ baseline.baseline_metrics.overall.avg_rt?.toFixed(0) }}</span>
              <span class="mini-label">平均RT(ms)</span>
            </div>
            <div class="mini-metric">
              <span class="mini-value">{{ baseline.baseline_metrics.overall.p99_rt?.toFixed(0) }}</span>
              <span class="mini-label">P99(ms)</span>
            </div>
            <div class="mini-metric">
              <span class="mini-value">{{ baseline.baseline_metrics.overall.error_rate?.toFixed(2) }}%</span>
              <span class="mini-label">错误率</span>
            </div>
          </div>

          <!-- 阈值 -->
          <div v-if="baseline.thresholds" class="thresholds">
            <span class="info-label">告警阈值:</span>
            <el-tag size="small" v-if="baseline.thresholds.avg_rt_max">RT&lt;{{ baseline.thresholds.avg_rt_max }}ms</el-tag>
            <el-tag size="small" v-if="baseline.thresholds.error_rate_max">错误率&lt;{{ baseline.thresholds.error_rate_max }}%</el-tag>
            <el-tag size="small" v-if="baseline.thresholds.tps_min">TPS&gt;{{ baseline.thresholds.tps_min }}</el-tag>
          </div>

          <!-- 选择对比 -->
          <div class="compare-check" style="margin-top: 12px">
            <el-checkbox v-model="baseline._selected" @change="onCompareSelect(baseline)">选中对比</el-checkbox>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-empty v-if="!baselines.length" description="暂无基线数据" />

    <!-- AI对比按钮 -->
    <div v-if="compareSelection.length === 2" class="compare-action">
      <el-button type="warning" size="large" :icon="MagicStick" :loading="comparing" @click="runAICompare">
        🤖 AI 对比分析 ({{ compareSelection.map(b => b.name).join(' vs ') }})
      </el-button>
    </div>

    <!-- AI对比结果 -->
    <el-card v-if="compareResult" shadow="never" class="compare-result-card" style="margin-top: 16px">
      <template #header>
        <div class="ai-header">
          <strong>🤖 AI 基线对比分析</strong>
          <el-tag :type="compareResult.regression_detected ? 'danger' : 'success'" effect="dark">
            {{ compareResult.regression_detected ? '⚠️ 检测到性能回归' : '✅ 性能稳定' }}
          </el-tag>
        </div>
      </template>

      <el-alert :type="compareResult.overall_trend === 'degraded' ? 'error' : compareResult.overall_trend === 'improved' ? 'success' : 'info'"
        :closable="false" style="margin-bottom: 16px">
        <template #title><strong>总体趋势:</strong> {{ trendLabel[compareResult.overall_trend] }} — {{ compareResult.summary }}</template>
      </el-alert>

      <!-- 对比明细 -->
      <el-table v-if="compareResult.details?.length" :data="compareResult.details" stripe border size="small">
        <el-table-column prop="api" label="接口" min-width="150" />
        <el-table-column prop="metric" label="指标" width="120" />
        <el-table-column prop="baseline_a_value" label="基线A" width="100" align="center" />
        <el-table-column prop="baseline_b_value" label="基线B" width="100" align="center" />
        <el-table-column prop="change_percent" label="变化" width="100" align="center">
          <template #default="{ row }">
            <span :style="{ color: row.trend === 'degraded' ? '#f56c6c' : row.trend === 'improved' ? '#67c23a' : '#909399' }">
              {{ row.change_percent > 0 ? '+' : '' }}{{ row.change_percent?.toFixed(1) }}%
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="comment" label="说明" min-width="200" />
      </el-table>

      <!-- 建议 -->
      <div v-if="compareResult.recommendations?.length" style="margin-top: 16px">
        <h4>💡 建议</h4>
        <el-timeline>
          <el-timeline-item v-for="(r, i) in compareResult.recommendations" :key="i" type="primary" :hollow="true">
            {{ r }}
          </el-timeline-item>
        </el-timeline>
      </div>

      <div v-if="compareResult.risk_assessment" style="margin-top: 12px">
        <h4>⚠️ 风险评估</h4>
        <p style="color: #606266">{{ compareResult.risk_assessment }}</p>
      </div>
    </el-card>

    <!-- 创建基线对话框 -->
    <el-dialog v-model="showCreateDialog" title="创建性能基线" width="520px" :close-on-click-modal="false">
      <el-form :model="createForm" label-width="110px" ref="createFormRef" :rules="createRules">
        <el-form-item label="基线名称" prop="name">
          <el-input v-model="createForm.name" placeholder="如：v2.1.0 性能基线" />
        </el-form-item>
        <el-form-item label="版本号">
          <el-input v-model="createForm.version" placeholder="如：v2.1.0" />
        </el-form-item>
        <el-form-item label="环境">
          <el-select v-model="createForm.environment" placeholder="选择环境" style="width: 100%">
            <el-option label="开发环境" value="dev" />
            <el-option label="测试环境" value="staging" />
            <el-option label="生产环境" value="production" />
          </el-select>
        </el-form-item>
        <el-form-item label="来源压测任务">
          <el-input-number v-model="createForm.source_task_id" :min="1" placeholder="输入任务ID"
            style="width: 100%" controls-position="right" />
          <div style="font-size: 12px; color: #909399; margin-top: 4px">从已完成的压测任务中提取指标作为基线</div>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="createForm.description" type="textarea" :rows="2" placeholder="基线描述" />
        </el-form-item>

        <el-divider content-position="left">告警阈值</el-divider>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="最大平均RT">
              <el-input-number v-model="createForm.thresholds.avg_rt_max" :min="0" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="最大P99">
              <el-input-number v-model="createForm.thresholds.p99_rt_max" :min="0" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="最大错误率%">
              <el-input-number v-model="createForm.thresholds.error_rate_max" :min="0" :max="100" :step="0.5" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="最小TPS">
              <el-input-number v-model="createForm.thresholds.tps_min" :min="0" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="handleCreate">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useProjectStore } from '@/stores'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, MagicStick, MoreFilled } from '@element-plus/icons-vue'
import {
  getBaselines, createBaseline, updateBaseline, deleteBaseline, aiCompareBaselines
} from '@/api/stressTest'

const projectStore = useProjectStore()
const projectId = computed(() => projectStore.currentProject?.id)

const baselines = ref([])
const envName = { dev: '开发', staging: '测试', production: '生产' }
const envTag = { dev: 'info', staging: 'warning', production: 'success' }
const trendLabel = { improved: '性能提升', degraded: '性能下降', stable: '性能稳定' }

const loadBaselines = async () => {
  try {
    const res = await getBaselines({ project_id: projectId.value })
    baselines.value = ((res.data || res).items || []).map(b => ({ ...b, _selected: false }))
  } catch (e) { console.error(e) }
}

// 创建基线
const showCreateDialog = ref(false)
const creating = ref(false)
const createFormRef = ref()
const createForm = reactive({
  name: '', version: '', environment: 'staging', description: '',
  source_task_id: null,
  thresholds: { avg_rt_max: 500, p99_rt_max: 2000, error_rate_max: 1, tps_min: 100 }
})
const createRules = { name: [{ required: true, message: '请输入基线名称', trigger: 'blur' }] }

const openCreateDialog = () => {
  createForm.name = ''
  createForm.version = ''
  createForm.source_task_id = null
  createForm.description = ''
  showCreateDialog.value = true
}

const handleCreate = async () => {
  await createFormRef.value?.validate()
  creating.value = true
  try {
    await createBaseline(projectId.value, createForm)
    ElMessage.success('基线创建成功')
    showCreateDialog.value = false
    loadBaselines()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '创建失败')
  } finally { creating.value = false }
}

// 卡片操作
const handleCardCommand = async (cmd, baseline) => {
  if (cmd === 'activate') {
    await updateBaseline(baseline.id, { is_active: true })
    ElMessage.success('已设为当前生效基线')
    loadBaselines()
  } else if (cmd === 'delete') {
    await ElMessageBox.confirm(`确认删除基线「${baseline.name}」？`, '删除确认', { type: 'warning' })
    await deleteBaseline(baseline.id)
    ElMessage.success('删除成功')
    loadBaselines()
  }
}

// AI 对比
const compareSelection = ref([])
const comparing = ref(false)
const compareResult = ref(null)

const onCompareSelect = (baseline) => {
  if (baseline._selected) {
    if (compareSelection.value.length >= 2) {
      // 取消最早选中的
      const oldest = compareSelection.value.shift()
      const found = baselines.value.find(b => b.id === oldest.id)
      if (found) found._selected = false
    }
    compareSelection.value.push(baseline)
  } else {
    compareSelection.value = compareSelection.value.filter(b => b.id !== baseline.id)
  }
  compareResult.value = null
}

const runAICompare = async () => {
  if (compareSelection.value.length !== 2) return
  comparing.value = true
  try {
    const res = await aiCompareBaselines({
      baseline_id_a: compareSelection.value[0].id,
      baseline_id_b: compareSelection.value[1].id,
    })
    compareResult.value = (res.data || res).comparison
    ElMessage.success('🤖 AI对比分析完成')
  } catch (e) {
    ElMessage.error('AI对比失败: ' + (e?.response?.data?.detail || e.message))
  } finally { comparing.value = false }
}

onMounted(() => loadBaselines())
</script>

<style scoped>
.baseline-container { padding: 4px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h2 { margin: 0; font-size: 20px; }
.subtitle { font-size: 13px; color: #909399; margin-left: 12px; }

.baseline-card { margin-bottom: 16px; border-radius: 12px; transition: all 0.3s; }
.baseline-card.active { border-color: #67c23a; box-shadow: 0 0 0 2px rgba(103, 194, 58, 0.2); }
.baseline-card:hover { transform: translateY(-2px); }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.baseline-name { font-weight: 600; font-size: 15px; }

.baseline-info { margin-bottom: 12px; }
.info-row { display: flex; justify-content: space-between; align-items: center; padding: 4px 0; font-size: 13px; color: #606266; }
.info-label { color: #909399; }

.baseline-metrics {
  display: flex; justify-content: space-between;
  background: #f5f7fa; border-radius: 8px; padding: 12px; margin-top: 8px;
}
.mini-metric { text-align: center; }
.mini-value { font-size: 18px; font-weight: 700; color: #303133; display: block; }
.mini-label { font-size: 11px; color: #909399; }

.thresholds { margin-top: 8px; display: flex; gap: 4px; align-items: center; flex-wrap: wrap; }

.compare-action { text-align: center; margin-top: 20px; }
.compare-result-card { border: 1px solid #e6a23c; }
.ai-header { display: flex; justify-content: space-between; align-items: center; }
</style>
