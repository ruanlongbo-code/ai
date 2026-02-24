<template>
  <div class="case-set-detail-page">
    <!-- 面包屑 + 返回 -->
    <div class="page-nav">
      <el-button text @click="goBack">
        <el-icon><ArrowLeft /></el-icon>
        返回用例集列表
      </el-button>
    </div>

    <!-- 用例集信息头部 -->
    <div class="set-header" v-loading="loading">
      <div class="set-info">
        <div class="set-icon">
          <el-icon :size="32" color="#409EFF"><FolderOpened /></el-icon>
        </div>
        <div class="set-meta">
          <h2>{{ caseSetDetail.name }}</h2>
          <p v-if="caseSetDetail.description" class="set-desc">{{ caseSetDetail.description }}</p>
          <div class="set-tags">
            <el-tag v-if="caseSetDetail.requirement_title" size="small" effect="plain" type="info">
              📋 {{ caseSetDetail.requirement_title }}
            </el-tag>
            <el-tag size="small" effect="plain">
              {{ caseSetDetail.case_count }} 用例
            </el-tag>
            <el-tag size="small" effect="plain" type="success">
              {{ caseSetDetail.scenario_count }} 场景
            </el-tag>
            <span class="set-creator">创建者: {{ caseSetDetail.creator_name || '系统' }}</span>
          </div>
        </div>
      </div>
      <div class="set-actions">
        <el-button v-if="caseSetDetail.requirement_id" type="primary" @click="handleExportXmind">
          <el-icon><Download /></el-icon>
          导出 XMind
        </el-button>
      </div>
    </div>

    <!-- 场景分组内容 -->
    <div class="scenario-content" v-loading="casesLoading">
      <template v-if="scenarioGroups.length > 0">
        <el-collapse v-model="expandedScenarios">
          <el-collapse-item
            v-for="(group, idx) in scenarioGroups"
            :key="group.scenario"
            :name="idx"
          >
            <template #title>
              <div class="scenario-header">
                <span class="scenario-icon">🎯</span>
                <span class="scenario-name">{{ group.scenario }}</span>
                <el-tag size="small" effect="plain" round class="scenario-count">
                  {{ group.cases.length }} 条用例
                </el-tag>
              </div>
            </template>

            <!-- 用例表格 -->
            <el-table
              :data="group.cases"
              stripe
              class="scenario-table"
              @row-click="(row) => handleViewCase(row)"
            >
              <el-table-column prop="case_no" label="编号" width="100">
                <template #default="{ row }">
                  <span class="case-no">{{ row.case_no || '-' }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="case_name" label="用例名称" min-width="250">
                <template #default="{ row }">
                  <span class="case-name-text">{{ row.case_name }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="priority" label="优先级" width="90" align="center">
                <template #default="{ row }">
                  <el-tag
                    :type="getPriorityType(row.priority)"
                    effect="light"
                    size="small"
                    round
                  >
                    {{ priorityLabel(row.priority) }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="status" label="状态" width="100" align="center">
                <template #default="{ row }">
                  <el-tag :type="getStatusType(row.status)" effect="light" size="small">
                    {{ statusLabel(row.status) }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="220" align="center" fixed="right">
                <template #default="{ row }">
                  <el-button size="small" type="primary" plain @click.stop="handleViewCase(row)">查看</el-button>
                  <el-button
                    v-if="row.status === 'design'"
                    size="small"
                    type="warning"
                    plain
                    @click.stop="handleReview(row)"
                  >审核</el-button>
                  <el-button size="small" type="danger" plain @click.stop="handleDeleteCase(row)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-collapse-item>
        </el-collapse>

        <!-- 底部统计 + 分页 -->
        <div class="cases-pagination">
          <span class="pagination-stats">
            共 <b>{{ casesTotal }}</b> 条用例
          </span>
          <el-pagination
            v-model:current-page="casesPage"
            v-model:page-size="casesPageSize"
            :page-sizes="[50, 100]"
            :total="casesTotal"
            layout="sizes, prev, pager, next"
            @size-change="handleCasesPageSizeChange"
            @current-change="handleCasesPageChange"
          />
        </div>
      </template>

      <!-- 空状态 -->
      <el-empty v-else description="该用例集下暂无测试用例" />
    </div>

    <!-- 用例详情弹框 -->
    <FunctionalCaseDetailModal
      v-model="showCaseDetail"
      :case-id="selectedCaseId"
      :project-id="getProjectId()"
    />

    <!-- 审核弹框 -->
    <el-dialog v-model="reviewDialog.visible" title="用例审核" width="450px" :close-on-click-modal="false">
      <div v-if="reviewDialog.caseItem" style="margin-bottom: 16px;">
        <h4 style="margin: 0 0 8px 0;">{{ reviewDialog.caseItem.case_name }}</h4>
      </div>
      <el-form label-width="80px">
        <el-form-item label="审核状态" required>
          <el-select v-model="reviewDialog.status" placeholder="选择状态" style="width: 100%;">
            <el-option label="审核通过" value="pass" />
            <el-option label="待执行" value="wait" />
            <el-option label="执行通过" value="smoke" />
            <el-option label="执行失败" value="regression" />
            <el-option label="已废弃" value="obsolete" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="reviewDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmitReview" :loading="reviewDialog.loading">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, FolderOpened, Download } from '@element-plus/icons-vue'
import { getCaseSetDetail, getFunctionalCasesList, reviewFunctionalCase, deleteFunctionalCase, exportCasesAsXmind } from '@/api/functional_test'
import { useProjectStore } from '@/stores'
import FunctionalCaseDetailModal from './components/FunctionalCaseDetailModal.vue'

const router = useRouter()
const route = useRoute()
const projectStore = useProjectStore()

const loading = ref(false)
const casesLoading = ref(false)
const caseSetDetail = ref({})
const expandedScenarios = ref([])
const showCaseDetail = ref(false)
const selectedCaseId = ref(null)

// 用例数据与分页（真实后端分页）
const relatedCases = ref([])
const casesTotal = ref(0)
const casesPage = ref(1)
const casesPageSize = ref(50)

// 按场景分组（基于当前页返回的用例数据）
const scenarioGroups = computed(() => {
  if (!relatedCases.value || relatedCases.value.length === 0) return []
  const groupMap = {}
  for (const c of relatedCases.value) {
    const scenario = c.scenario || '未分类场景'
    if (!groupMap[scenario]) {
      groupMap[scenario] = { scenario, cases: [] }
    }
    groupMap[scenario].cases.push(c)
  }
  return Object.values(groupMap)
})

const handleCasesPageChange = (page) => {
  casesPage.value = page
  loadCases()
}

const handleCasesPageSizeChange = (size) => {
  casesPageSize.value = size
  casesPage.value = 1
  loadCases()
}

const reviewDialog = reactive({
  visible: false,
  caseItem: null,
  status: '',
  loading: false
})

const getProjectId = () => {
  let pid = projectStore.currentProject?.id
  if (!pid) {
    try {
      const str = localStorage.getItem('currentProject')
      if (str) pid = JSON.parse(str).id
    } catch (e) { /* ignore */ }
  }
  return pid || 1
}

const goBack = () => {
  router.push({ name: 'FunctionTestCase' })
}

const priorityLabel = (p) => ({ 1: 'P0', 2: 'P1', 3: 'P2', 4: 'P3' }[p] || `P${p}`)
const getPriorityType = (p) => ({ 1: 'danger', 2: 'warning', 3: '', 4: 'info' }[p] || 'info')
const statusLabel = (s) => ({
  design: '待审核', pass: '审核通过', wait: '待执行',
  smoke: '执行通过', regression: '执行失败', obsolete: '已废弃'
}[s] || s)
const getStatusType = (s) => ({
  design: 'info', pass: 'success', wait: 'warning',
  smoke: 'success', regression: 'danger', obsolete: 'info'
}[s] || 'info')

const loadDetail = async () => {
  loading.value = true
  try {
    const caseSetId = route.params.caseSetId
    const projectId = getProjectId()
    const res = await getCaseSetDetail(projectId, caseSetId)
    caseSetDetail.value = res.data || res
    // 加载用例列表（后端分页）
    await loadCases()
  } catch (e) {
    console.error('加载用例集详情失败:', e)
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

const loadCases = async () => {
  const projectId = getProjectId()
  const caseSetId = route.params.caseSetId
  casesLoading.value = true
  try {
    const response = await getFunctionalCasesList(projectId, {
      case_set_id: caseSetId,
      page: casesPage.value,
      page_size: casesPageSize.value
    })
    const data = response.data || response
    relatedCases.value = data.cases || []
    casesTotal.value = data.total || 0
    // 默认展开当前页所有场景组
    expandedScenarios.value = scenarioGroups.value.map((_, i) => i)
  } catch (e) {
    console.error('加载用例列表失败:', e)
    ElMessage.error('加载用例列表失败')
  } finally {
    casesLoading.value = false
  }
}

const handleViewCase = (row) => {
  selectedCaseId.value = row.id
  showCaseDetail.value = true
}

const handleReview = (row) => {
  reviewDialog.caseItem = row
  reviewDialog.status = ''
  reviewDialog.visible = true
}

const handleSubmitReview = async () => {
  if (!reviewDialog.status) {
    ElMessage.warning('请选择状态')
    return
  }
  reviewDialog.loading = true
  try {
    const projectId = getProjectId()
    await reviewFunctionalCase(projectId, reviewDialog.caseItem.id, { status: reviewDialog.status })
    ElMessage.success('审核成功')
    reviewDialog.visible = false
    await loadCases()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '审核失败')
  } finally {
    reviewDialog.loading = false
  }
}

const handleDeleteCase = async (row) => {
  try {
    await ElMessageBox.confirm(`确定删除用例「${row.case_name}」吗？`, '确认', { type: 'warning' })
    const projectId = getProjectId()
    await deleteFunctionalCase(projectId, row.id)
    ElMessage.success('已删除')
    await loadCases()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error(e.response?.data?.detail || '删除失败')
    }
  }
}

const handleExportXmind = async () => {
  try {
    const projectId = getProjectId()
    const reqId = caseSetDetail.value.requirement_id
    if (!reqId) {
      ElMessage.warning('该用例集未关联需求，无法导出')
      return
    }
    const res = await exportCasesAsXmind(projectId, reqId)
    // 下载文件
    const blob = new Blob([res], { type: 'application/octet-stream' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${caseSetDetail.value.name}_测试用例.xmind`
    a.click()
    window.URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch (e) {
    ElMessage.error('导出失败')
  }
}

onMounted(() => {
  loadDetail()
})
</script>

<style scoped>
.case-set-detail-page {
  padding: 24px;
  background: #f5f7fa;
  min-height: 100vh;
}

.page-nav {
  margin-bottom: 16px;
}

/* 头部 */
.set-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  background: white;
  padding: 24px;
  border-radius: 12px;
  margin-bottom: 16px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}

.set-info {
  display: flex;
  gap: 16px;
}

.set-icon {
  width: 56px;
  height: 56px;
  background: #ecf5ff;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.set-meta h2 {
  margin: 0 0 6px 0;
  font-size: 20px;
  font-weight: 600;
  color: #1f2937;
}

.set-desc {
  color: #6b7280;
  font-size: 13px;
  margin: 0 0 10px 0;
}

.set-tags {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.set-creator {
  font-size: 12px;
  color: #9ca3af;
}

/* 场景内容 */
.scenario-content {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}

.scenario-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.scenario-icon {
  font-size: 18px;
}

.scenario-name {
  font-size: 15px;
  font-weight: 600;
  color: #1f2937;
}

.scenario-count {
  margin-left: 8px;
}

.scenario-table {
  margin-top: 4px;
}

.case-no {
  color: #9ca3af;
  font-family: monospace;
  font-size: 13px;
}

.case-name-text {
  font-weight: 500;
  color: #1f2937;
  cursor: pointer;
}

.case-name-text:hover {
  color: #409EFF;
}

:deep(.el-collapse-item__header) {
  font-size: 15px;
  height: 48px;
  line-height: 48px;
  padding: 0 8px;
  background: #fafbfc;
  border-radius: 8px;
  margin-bottom: 4px;
}

:deep(.el-collapse-item__content) {
  padding: 8px 0;
}

/* 底部统计+分页 */
.cases-pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  margin-top: 16px;
  padding: 12px 0;
  border-top: 1px solid #f0f0f0;
}

.pagination-stats {
  font-size: 13px;
  color: #606266;
  white-space: nowrap;
}

/* 操作按钮样式增强 */
.scenario-table :deep(.el-button--small) {
  font-size: 13px;
  font-weight: 500;
  padding: 5px 12px;
}

@media (max-width: 768px) {
  .case-set-detail-page {
    padding: 16px;
  }

  .set-header {
    flex-direction: column;
    gap: 16px;
  }
}
</style>
