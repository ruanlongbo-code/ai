<template>
  <div class="scenario-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h2>测试场景</h2>
        <span class="subtitle">配置压测目标API、参数化数据和负载模式</span>
      </div>
      <div class="header-right">
        <el-button type="primary" :icon="MagicStick" @click="showAIGenerateDialog = true">
          AI 智能生成
        </el-button>
        <el-button type="success" :icon="Plus" @click="openCreateDialog">手动创建</el-button>
      </div>
    </div>

    <!-- 搜索 -->
    <div class="search-bar">
      <el-input v-model="searchKeyword" placeholder="搜索场景名称..." clearable :prefix-icon="Search"
        style="width: 320px" @clear="loadScenarios" @keyup.enter="loadScenarios" />
      <el-button :icon="Refresh" @click="loadScenarios">刷新</el-button>
    </div>

    <!-- 场景列表 -->
    <el-table :data="scenarios" v-loading="loading" stripe border style="width: 100%">
      <el-table-column prop="name" label="场景名称" min-width="200">
        <template #default="{ row }">
          <div class="scenario-name">
            <el-tag v-if="row.ai_generated" type="warning" size="small" effect="plain" style="margin-right: 6px">
              🤖 AI
            </el-tag>
            <span>{{ row.name }}</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="scenario_type" label="场景类型" width="130" align="center">
        <template #default="{ row }">
          <el-tag :type="typeTagMap[row.scenario_type]" size="small">
            {{ typeNameMap[row.scenario_type] }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="api_count" label="API数" width="80" align="center" />
      <el-table-column prop="think_time" label="思考时间" width="100" align="center">
        <template #default="{ row }">{{ row.think_time }}ms</template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="170" align="center">
        <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="260" align="center" fixed="right">
        <template #default="{ row }">
          <el-button size="small" type="primary" text :icon="View" @click="viewScenario(row)">详情</el-button>
          <el-button size="small" type="success" text :icon="VideoPlay" @click="quickCreateTask(row)">创建任务</el-button>
          <el-button size="small" type="danger" text :icon="Delete" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <div class="pagination-wrapper">
      <el-pagination v-model:current-page="currentPage" v-model:page-size="pageSize"
        :total="total" :page-sizes="[10, 20, 50]" layout="total, sizes, prev, pager, next"
        @size-change="loadScenarios" @current-change="loadScenarios" />
    </div>

    <!-- AI智能生成对话框 -->
    <el-dialog v-model="showAIGenerateDialog" title="🤖 AI 智能生成压测场景" width="640px" :close-on-click-modal="false">
      <el-alert type="info" :closable="false" style="margin-bottom: 16px">
        <template #title>
          基于 <strong>LLM + RAG</strong> 技术，AI 将根据您的描述自动生成合理的压测场景，包括API配置、参数化数据和负载建议。
        </template>
      </el-alert>
      <el-form :model="aiForm" label-width="100px">
        <el-form-item label="场景类型">
          <el-select v-model="aiForm.scenario_type" style="width: 100%">
            <el-option label="单接口压测" value="single_api" />
            <el-option label="多接口混合" value="multi_api" />
            <el-option label="接口链路" value="chain_api" />
          </el-select>
        </el-form-item>
        <el-form-item label="测试需求">
          <el-input v-model="aiForm.requirement_text" type="textarea" :rows="4"
            placeholder="描述你的压测需求，例如：&#10;- 对用户登录接口进行压测，验证在1000并发下的性能表现&#10;- 模拟电商下单场景，依次调用：查询商品→加入购物车→创建订单→支付" />
        </el-form-item>
        <el-form-item label="补充说明">
          <el-input v-model="aiForm.description" placeholder="可选：额外的测试要求或关注点" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAIGenerateDialog = false">取消</el-button>
        <el-button type="primary" :loading="aiGenerating" :icon="MagicStick" @click="handleAIGenerate">
          {{ aiGenerating ? 'AI 生成中...' : '开始生成' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 手动创建/编辑对话框 -->
    <el-dialog v-model="showEditDialog" :title="editForm.id ? '编辑场景' : '创建场景'" width="700px" :close-on-click-modal="false">
      <el-form :model="editForm" label-width="100px" :rules="editRules" ref="editFormRef">
        <el-form-item label="场景名称" prop="name">
          <el-input v-model="editForm.name" placeholder="请输入场景名称" />
        </el-form-item>
        <el-form-item label="场景类型">
          <el-select v-model="editForm.scenario_type" style="width: 100%">
            <el-option label="单接口压测" value="single_api" />
            <el-option label="多接口混合" value="multi_api" />
            <el-option label="接口链路" value="chain_api" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="editForm.description" type="textarea" :rows="2" placeholder="场景描述" />
        </el-form-item>
        <el-form-item label="思考时间">
          <el-input-number v-model="editForm.think_time" :min="0" :max="10000" :step="100" />
          <span style="margin-left: 8px; color: #909399">ms</span>
        </el-form-item>
        <el-form-item label="超时时间">
          <el-input-number v-model="editForm.timeout" :min="1" :max="120" />
          <span style="margin-left: 8px; color: #909399">秒</span>
        </el-form-item>

        <el-divider content-position="left">目标 API 配置</el-divider>
        <div v-for="(api, index) in editForm.target_apis" :key="index" class="api-item">
          <div class="api-item-header">
            <span class="api-index">API #{{ index + 1 }}</span>
            <el-button type="danger" text size="small" @click="editForm.target_apis.splice(index, 1)">移除</el-button>
          </div>
          <el-row :gutter="12">
            <el-col :span="5">
              <el-select v-model="api.method" placeholder="方法">
                <el-option v-for="m in ['GET','POST','PUT','DELETE','PATCH']" :key="m" :label="m" :value="m" />
              </el-select>
            </el-col>
            <el-col :span="13">
              <el-input v-model="api.url" placeholder="请求URL" />
            </el-col>
            <el-col :span="6">
              <el-input v-model="api.name" placeholder="接口名称(选填)" />
            </el-col>
          </el-row>
          <el-input v-model="api.bodyStr" type="textarea" :rows="2" placeholder="请求体 JSON (选填)"
            style="margin-top: 8px" v-if="['POST','PUT','PATCH'].includes(api.method)" />
        </div>
        <el-button type="primary" plain :icon="Plus" @click="addApiItem" style="width: 100%; margin-top: 8px">
          添加 API
        </el-button>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>

    <!-- 场景详情抽屉 -->
    <el-drawer v-model="showDetail" :title="detailData?.name" size="600px">
      <template v-if="detailData">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="场景类型">
            <el-tag :type="typeTagMap[detailData.scenario_type]">{{ typeNameMap[detailData.scenario_type] }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="AI生成">
            <el-tag :type="detailData.ai_generated ? 'warning' : 'info'">
              {{ detailData.ai_generated ? '是' : '否' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="思考时间">{{ detailData.think_time }}ms</el-descriptions-item>
          <el-descriptions-item label="超时时间">{{ detailData.timeout }}s</el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">{{ detailData.description || '-' }}</el-descriptions-item>
        </el-descriptions>

        <h4 style="margin: 16px 0 8px">目标 API ({{ detailData.target_apis?.length || 0 }} 个)</h4>
        <el-card v-for="(api, idx) in detailData.target_apis" :key="idx" shadow="never" style="margin-bottom: 8px">
          <div class="api-detail-item">
            <el-tag :type="methodColor(api.method)" size="small">{{ api.method }}</el-tag>
            <span class="api-url">{{ api.url }}</span>
            <span v-if="api.name" class="api-label">{{ api.name }}</span>
          </div>
        </el-card>
      </template>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useProjectStore } from '@/stores'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Refresh, Delete, View, VideoPlay, MagicStick } from '@element-plus/icons-vue'
import {
  getScenarios, createScenario, updateScenario, deleteScenario,
  getScenarioDetail, aiGenerateScenario
} from '@/api/stressTest'

const projectStore = useProjectStore()
const router = useRouter()
const projectId = computed(() => projectStore.currentProject?.id)

const loading = ref(false)
const scenarios = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const searchKeyword = ref('')

const typeNameMap = { single_api: '单接口', multi_api: '多接口混合', chain_api: '接口链路' }
const typeTagMap = { single_api: '', multi_api: 'success', chain_api: 'warning' }

const formatTime = (t) => t ? new Date(t).toLocaleString('zh-CN') : '-'
const methodColor = (m) => ({ GET: 'success', POST: 'primary', PUT: 'warning', DELETE: 'danger', PATCH: 'info' }[m] || '')

// 加载场景列表
const loadScenarios = async () => {
  if (!projectId.value) return
  loading.value = true
  try {
    const res = await getScenarios({
      project_id: projectId.value, page: currentPage.value,
      page_size: pageSize.value, keyword: searchKeyword.value || undefined,
    })
    const data = res.data || res
    scenarios.value = data.items || []
    total.value = data.total || 0
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

// AI 生成
const showAIGenerateDialog = ref(false)
const aiGenerating = ref(false)
const aiForm = reactive({
  scenario_type: 'single_api',
  requirement_text: '',
  description: '',
})

const handleAIGenerate = async () => {
  if (!aiForm.requirement_text?.trim()) {
    ElMessage.warning('请输入测试需求描述')
    return
  }
  aiGenerating.value = true
  try {
    const res = await aiGenerateScenario(projectId.value, aiForm)
    const data = res.data || res
    ElMessage.success(`🤖 AI场景生成成功！建议并发: ${data.recommended_concurrency}, 时长: ${data.recommended_duration}s`)
    showAIGenerateDialog.value = false
    aiForm.requirement_text = ''
    aiForm.description = ''
    loadScenarios()
  } catch (e) {
    ElMessage.error('AI生成失败: ' + (e?.response?.data?.detail || e.message))
  } finally {
    aiGenerating.value = false
  }
}

// 手动创建
const showEditDialog = ref(false)
const saving = ref(false)
const editFormRef = ref()
const editForm = reactive({
  id: null, name: '', description: '', scenario_type: 'single_api',
  think_time: 0, timeout: 30, target_apis: [],
})
const editRules = { name: [{ required: true, message: '请输入场景名称', trigger: 'blur' }] }

const openCreateDialog = () => {
  Object.assign(editForm, {
    id: null, name: '', description: '', scenario_type: 'single_api',
    think_time: 0, timeout: 30, target_apis: [{ method: 'GET', url: '', name: '', bodyStr: '' }],
  })
  showEditDialog.value = true
}

const addApiItem = () => {
  editForm.target_apis.push({ method: 'GET', url: '', name: '', bodyStr: '' })
}

const handleSave = async () => {
  if (!editFormRef.value) return
  await editFormRef.value.validate()
  saving.value = true
  try {
    const apis = editForm.target_apis.map(a => ({
      method: a.method, url: a.url, name: a.name,
      body: a.bodyStr ? JSON.parse(a.bodyStr) : null,
    }))
    const payload = {
      name: editForm.name, description: editForm.description,
      scenario_type: editForm.scenario_type, think_time: editForm.think_time,
      timeout: editForm.timeout, target_apis: apis,
    }
    if (editForm.id) {
      await updateScenario(editForm.id, payload)
      ElMessage.success('场景更新成功')
    } else {
      await createScenario(projectId.value, payload)
      ElMessage.success('场景创建成功')
    }
    showEditDialog.value = false
    loadScenarios()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

// 详情
const showDetail = ref(false)
const detailData = ref(null)
const viewScenario = async (row) => {
  try {
    const res = await getScenarioDetail(row.id)
    detailData.value = res.data || res
    showDetail.value = true
  } catch (e) {
    ElMessage.error('获取详情失败')
  }
}

// 快速创建任务
const quickCreateTask = (row) => {
  router.push({ name: 'StressTestTask', query: { scenario_id: row.id, scenario_name: row.name } })
}

// 删除
const handleDelete = async (row) => {
  await ElMessageBox.confirm(`确认删除场景「${row.name}」？`, '删除确认', { type: 'warning' })
  await deleteScenario(row.id)
  ElMessage.success('删除成功')
  loadScenarios()
}

onMounted(() => loadScenarios())
</script>

<style scoped>
.scenario-container { padding: 4px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h2 { margin: 0; font-size: 20px; }
.subtitle { font-size: 13px; color: #909399; margin-left: 12px; }
.search-bar { display: flex; gap: 8px; margin-bottom: 16px; }
.pagination-wrapper { display: flex; justify-content: flex-end; margin-top: 16px; }
.scenario-name { display: flex; align-items: center; }
.api-item { border: 1px solid #ebeef5; border-radius: 8px; padding: 12px; margin-bottom: 8px; }
.api-item-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.api-index { font-weight: 600; color: #606266; }
.api-detail-item { display: flex; align-items: center; gap: 8px; }
.api-url { font-family: monospace; font-size: 13px; color: #303133; }
.api-label { font-size: 12px; color: #909399; }
</style>
