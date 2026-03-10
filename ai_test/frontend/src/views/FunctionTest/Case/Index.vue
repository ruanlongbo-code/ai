<template>
  <div class="case-manage-page">
    <el-tabs v-model="activeTab" class="main-tabs" @tab-change="handleTabChange">
      <!-- Tab 1: 测试点集 -->
      <el-tab-pane name="testpoints">
        <template #label>
          <span class="tab-label">
            <el-icon><Aim /></el-icon> 测试点集
            <span class="tab-count" v-if="testPointSets.length">{{ testPointSets.length }}</span>
          </span>
        </template>

        <div class="tab-toolbar">
          <el-input v-model="tpKeyword" placeholder="搜索测试点集..." clearable style="width: 260px;" size="default" :prefix-icon="Search" />
          <el-button :icon="Refresh" size="default" @click="loadTestPointSets">刷新</el-button>
        </div>

        <el-table
          :data="filteredTestPointSets"
          stripe
          size="default"
          v-loading="loadingTP"
          empty-text="暂无测试点集，前往「AI生成测试点」创建"
          class="data-table"
        >
          <el-table-column prop="id" label="ID" width="60" align="center" />
          <el-table-column prop="name" label="测试点集名称" min-width="220">
            <template #default="{ row }">
              <div class="name-cell">
                <el-icon style="color: #8b5cf6;"><Aim /></el-icon>
                <span class="name-text">{{ row.name }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="point_count" label="测试点数" width="90" align="center">
            <template #default="{ row }">
              <el-tag size="small" type="success">{{ row.point_count }} 个</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="creator_name" label="创建人" width="90" align="center" />
          <el-table-column prop="created_at" label="创建时间" width="160" align="center">
            <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="190" align="center" fixed="right">
            <template #default="{ row }">
              <el-button type="primary" link size="small" @click="handleViewTestPointSet(row)">
                <el-icon><View /></el-icon> 查看
              </el-button>
              <el-button type="success" link size="small" @click="handleGenerateCases(row)" :loading="generatingCaseSetId === row.id">
                <el-icon><MagicStick /></el-icon> 生成XMind用例
              </el-button>
              <el-popconfirm title="确定删除该测试点集？" @confirm="handleDeleteTP(row.id)">
                <template #reference>
                  <el-button type="danger" link size="small">
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </template>
              </el-popconfirm>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- Tab 2: 测试用例集 -->
      <el-tab-pane name="casesets">
        <template #label>
          <span class="tab-label">
            <el-icon><FolderOpened /></el-icon> 测试用例集
            <span class="tab-count" v-if="caseSets.length">{{ caseSets.length }}</span>
          </span>
        </template>
        <List ref="listRef" embedded />
      </el-tab-pane>
    </el-tabs>

    <!-- 测试点集详情抽屉 -->
    <el-drawer v-model="tpDetailDrawer.visible" :title="tpDetailDrawer.data?.name || '测试点集详情'" size="500px">
      <div v-if="tpDetailDrawer.data" class="tp-detail">
        <div class="tp-meta">
          <el-tag type="success">{{ tpDetailDrawer.data.point_count }} 个测试点</el-tag>
          <span class="tp-meta-text">创建人：{{ tpDetailDrawer.data.creator_name || '系统' }}</span>
          <span class="tp-meta-text">{{ formatTime(tpDetailDrawer.data.created_at) }}</span>
        </div>
        <p v-if="tpDetailDrawer.data.description" class="tp-desc">{{ tpDetailDrawer.data.description }}</p>

        <el-divider />
        <h4>测试点列表</h4>
        <div v-if="tpDetailDrawer.points?.length" class="tp-points-list">
          <div v-for="(p, idx) in tpDetailDrawer.points" :key="p.id" class="tp-point-item">
            <span class="point-index">{{ idx + 1 }}</span>
            <span class="point-name">{{ p.name }}</span>
            <el-tag v-if="p.point_type" size="small" :type="getPointTypeTag(p.point_type)">{{ p.point_type }}</el-tag>
          </div>
        </div>
        <el-empty v-else description="暂无测试点" :image-size="60" />

        <div class="tp-detail-actions">
          <el-button type="success" @click="handleGenerateCases(tpDetailDrawer.data); tpDetailDrawer.visible = false" :loading="!!generatingCaseSetId">
            <el-icon><MagicStick /></el-icon> 根据测试点生成XMind用例
          </el-button>
        </div>
      </div>
    </el-drawer>

    <!-- 生成用例进度对话框 -->
    <el-dialog v-model="generateDialog.visible" :title="generateDialog.result ? '生成完成' : '正在生成用例集...'" width="600px" :close-on-click-modal="false" :show-close="true" @close="handleCancelGenerate">
      <div class="generate-progress">
        <el-progress :percentage="generateDialog.progress" :stroke-width="10" :color="generateDialog.result ? '#67c23a' : '#8b5cf6'" />
        <div class="progress-info">
          <p class="progress-msg">{{ generateDialog.message }}</p>
          <span class="elapsed-time" v-if="!generateDialog.result">已耗时 {{ generateDialog.elapsed }}</span>
        </div>
        <div v-if="generateDialog.streamText && !generateDialog.result" class="stream-output" ref="streamOutputRef">
          <pre>{{ generateDialog.streamText.slice(-2000) }}</pre>
        </div>
        <div v-if="generateDialog.result" class="generate-result">
          <el-result icon="success" :title="`生成完成！${generateDialog.result.total_scenarios} 个场景、${generateDialog.result.total_cases} 条用例`" :sub-title="generateDialog.result.xmind_base64 ? '已同步生成XMind思维导图' : ''">
            <template #extra>
              <el-button type="success" v-if="generateDialog.result.xmind_base64" @click="handleDownloadXmind">
                <el-icon><Download /></el-icon> 下载 XMind
              </el-button>
              <el-button type="primary" @click="handleViewGeneratedCaseSet">查看用例集</el-button>
              <el-button @click="generateDialog.visible = false">关闭</el-button>
            </template>
          </el-result>
        </div>
        <div v-if="!generateDialog.result" class="generate-footer">
          <el-button @click="handleCancelGenerate">取消</el-button>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Aim, View, Delete, MagicStick, FolderOpened,
  Search, Refresh, Download
} from '@element-plus/icons-vue'
import {
  getTestPointSetList,
  getTestPointSetDetail,
  deleteTestPointSet,
  generateCasesFromTestpoints,
  getCaseSetList,
} from '@/api/functional_test'
import { useProjectStore } from '@/stores'
import List from './List.vue'

const router = useRouter()
const route = useRoute()
const projectStore = useProjectStore()

const activeTab = ref('testpoints')
const testPointSets = ref([])
const caseSets = ref([])
const loadingTP = ref(false)
const tpKeyword = ref('')
const generatingCaseSetId = ref(null)

const tpDetailDrawer = reactive({
  visible: false,
  data: null,
  points: [],
})

const generateDialog = reactive({
  visible: false,
  progress: 0,
  message: '',
  streamText: '',
  result: null,
  elapsed: '0秒',
  abortController: null,
  timer: null,
})

const projectId = computed(() => {
  return route.params.projectId || projectStore.currentProject?.id || (() => {
    try {
      const p = JSON.parse(localStorage.getItem('currentProject'))
      return p?.id
    } catch { return null }
  })() || 1
})

const filteredTestPointSets = computed(() => {
  if (!tpKeyword.value.trim()) return testPointSets.value
  const kw = tpKeyword.value.trim().toLowerCase()
  return testPointSets.value.filter(t => t.name?.toLowerCase().includes(kw))
})

const formatTime = (t) => {
  if (!t) return ''
  return new Date(t).toLocaleString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

const getPointTypeTag = (type) => {
  const map = { '正向验证': 'success', '边界测试': 'warning', '异常处理': 'danger' }
  return map[type] || 'info'
}

const loadTestPointSets = async () => {
  loadingTP.value = true
  try {
    const res = await getTestPointSetList(projectId.value)
    testPointSets.value = res.data?.test_point_sets || []
  } catch (e) {
    console.error('加载测试点集失败:', e)
  } finally {
    loadingTP.value = false
  }
}

const loadCaseSets = async () => {
  try {
    const res = await getCaseSetList(projectId.value)
    caseSets.value = res.data?.case_sets || []
  } catch (e) {
    console.error('加载用例集失败:', e)
  }
}

const handleTabChange = (tab) => {
  if (tab === 'testpoints') loadTestPointSets()
  if (tab === 'casesets') loadCaseSets()
}

const handleViewTestPointSet = async (row) => {
  try {
    const res = await getTestPointSetDetail(projectId.value, row.id)
    const data = res.data || res
    tpDetailDrawer.data = data
    tpDetailDrawer.points = data.points || []
    tpDetailDrawer.visible = true
  } catch (e) {
    ElMessage.error('加载详情失败')
  }
}

const handleDeleteTP = async (id) => {
  try {
    await deleteTestPointSet(projectId.value, id)
    ElMessage.success('已删除')
    await loadTestPointSets()
  } catch (e) {
    ElMessage.error('删除失败')
  }
}

const handleGenerateCases = async (row) => {
  generatingCaseSetId.value = row.id
  generateDialog.visible = true
  generateDialog.progress = 0
  generateDialog.message = '正在初始化...'
  generateDialog.streamText = ''
  generateDialog.result = null
  generateDialog.elapsed = '0秒'

  const startTime = Date.now()
  const abortController = new AbortController()
  generateDialog.abortController = abortController

  generateDialog.timer = setInterval(() => {
    const sec = Math.floor((Date.now() - startTime) / 1000)
    if (sec < 60) {
      generateDialog.elapsed = `${sec}秒`
    } else {
      generateDialog.elapsed = `${Math.floor(sec / 60)}分${sec % 60}秒`
    }
  }, 1000)

  try {
    const response = await generateCasesFromTestpoints(projectId.value, row.id, abortController.signal)
    if (!response.ok) {
      const err = await response.json().catch(() => ({}))
      throw new Error(err.detail || `HTTP ${response.status}`)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { value, done } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        const dataStr = line.slice(6).trim()
        if (!dataStr || dataStr === '[DONE]') continue
        try {
          const data = JSON.parse(dataStr)
          if (data.type === 'progress') {
            generateDialog.message = data.message || ''
            generateDialog.progress = data.progress || generateDialog.progress
          } else if (data.type === 'chunk') {
            generateDialog.streamText += data.content || ''
            generateDialog.progress = data.progress || generateDialog.progress
          } else if (data.type === 'result') {
            generateDialog.result = data.data
            generateDialog.progress = 100
            generateDialog.message = '生成完成！'
            await loadCaseSets()
            await loadTestPointSets()
          } else if (data.type === 'error') {
            throw new Error(data.message || '生成失败')
          }
        } catch (e) {
          if (e.message && !e.message.includes('JSON')) throw e
        }
      }
    }

    if (!generateDialog.result && generateDialog.streamText) {
      generateDialog.message = '流已结束但未收到完成信号，请刷新查看结果'
      generateDialog.progress = 100
    }
  } catch (e) {
    if (e.name === 'AbortError') return
    ElMessage.error(e.message || '生成用例失败')
    generateDialog.visible = false
  } finally {
    generatingCaseSetId.value = null
    if (generateDialog.timer) {
      clearInterval(generateDialog.timer)
      generateDialog.timer = null
    }
    generateDialog.abortController = null
  }
}

const handleCancelGenerate = () => {
  if (generateDialog.abortController) {
    generateDialog.abortController.abort()
  }
  if (generateDialog.timer) {
    clearInterval(generateDialog.timer)
    generateDialog.timer = null
  }
  generateDialog.visible = false
  generatingCaseSetId.value = null
  loadTestPointSets()
  loadCaseSets()
}

const handleViewGeneratedCaseSet = () => {
  generateDialog.visible = false
  if (generateDialog.result?.case_set_id) {
    router.push({ name: 'FunctionTestCaseSetDetail', params: { caseSetId: generateDialog.result.case_set_id } })
  }
}

const handleDownloadXmind = () => {
  const result = generateDialog.result
  if (!result?.xmind_base64) return
  const byteChars = atob(result.xmind_base64)
  const byteNumbers = new Array(byteChars.length)
  for (let i = 0; i < byteChars.length; i++) {
    byteNumbers[i] = byteChars.charCodeAt(i)
  }
  const blob = new Blob([new Uint8Array(byteNumbers)], { type: 'application/octet-stream' })
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = result.xmind_filename || '测试用例.xmind'
  a.click()
  window.URL.revokeObjectURL(url)
  ElMessage.success('XMind 文件下载成功')
}

onMounted(() => {
  loadTestPointSets()
  loadCaseSets()
})
</script>

<style scoped>
.case-manage-page {
  padding: 16px;
  background: #f8fafc;
  min-height: 100%;
}

.main-tabs {
  background: white;
  border-radius: 10px;
  padding: 12px 16px 8px;
  box-shadow: 0 1px 6px rgba(0, 0, 0, 0.05);
}
:deep(.el-tabs__header) {
  margin-bottom: 12px;
}
.tab-label {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 14px;
}
.tab-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  margin-left: 4px;
  font-size: 11px;
  font-weight: 600;
  color: #6b7280;
  background: #f3f4f6;
  border-radius: 9px;
  line-height: 1;
}

.tab-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.name-cell {
  display: flex;
  align-items: center;
  gap: 6px;
}
.name-text { font-weight: 500; }

/* 测试点集详情抽屉 */
.tp-detail { padding: 0 4px; }
.tp-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 8px;
}
.tp-meta-text { font-size: 13px; color: #9ca3af; }
.tp-desc { color: #6b7280; font-size: 14px; line-height: 1.6; margin: 0; }

.tp-points-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.tp-point-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}
.point-index {
  width: 22px; height: 22px; border-radius: 50%;
  background: linear-gradient(135deg, #8b5cf6, #7c3aed);
  color: white;
  display: flex; align-items: center; justify-content: center;
  font-size: 11px; font-weight: 700; flex-shrink: 0;
}
.point-name { flex: 1; font-size: 13px; color: #374151; }
.tp-detail-actions { margin-top: 20px; text-align: center; }

/* 生成进度 */
.generate-progress { padding: 4px 0; }
.progress-info {
  display: flex; justify-content: space-between; align-items: center;
  margin: 8px 0;
}
.progress-msg {
  color: #8b5cf6; font-size: 14px; margin: 0;
}
.elapsed-time {
  font-size: 12px; color: #9ca3af; flex-shrink: 0;
}
.generate-footer {
  text-align: center; margin-top: 12px;
}
.stream-output {
  background: #1a1a2e; color: #a5f3fc;
  border-radius: 8px; padding: 10px;
  max-height: 180px; overflow-y: auto; margin: 10px 0;
}
.stream-output pre {
  margin: 0; white-space: pre-wrap; word-break: break-word;
  font-family: 'Monaco', 'Menlo', monospace; font-size: 12px; line-height: 1.5;
}
.generate-result { margin-top: 12px; }

:deep(.el-tabs__nav-wrap::after) { height: 1px; }

/* 嵌入 List.vue 时去掉其自带的外层padding和重复头部 */
:deep(.functional-cases-page) {
  padding: 0 !important;
  background: transparent !important;
  min-height: auto !important;
}
:deep(.functional-cases-page > .page-header) {
  display: none !important;
}
:deep(.functional-cases-page > .stats-bar) {
  margin-bottom: 10px;
}
:deep(.functional-cases-page > .stats-bar .el-card) {
  box-shadow: none;
  border: 1px solid #eee;
}
:deep(.functional-cases-page > .filter-toolbar) {
  margin-bottom: 10px;
}
:deep(.functional-cases-page > .case-sets-grid) {
  gap: 12px;
  min-height: 120px;
}
:deep(.functional-cases-page .empty-state) {
  min-height: 200px;
}
</style>
