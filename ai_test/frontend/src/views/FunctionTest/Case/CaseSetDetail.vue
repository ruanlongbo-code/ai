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
        <el-button type="primary" size="large" @click="handleExportXmind" class="export-xmind-btn">
          <el-icon><Download /></el-icon>
          导出 XMind 文件
        </el-button>
        <el-button
            size="large"
            :loading="importingFeishu"
            @click="showFeishuDialog"
            style="background: #3370ff; color: white; border-color: #3370ff;"
        >
          <el-icon><Upload /></el-icon>
          导入飞书用例集
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

    <!-- 飞书导入弹窗 -->
    <el-dialog v-model="feishuDialogVisible" title="导入飞书用例集" width="560px" :close-on-click-modal="false">
      <div style="background: #f0f7ff; border-radius: 8px; padding: 14px 16px; margin-bottom: 16px; font-size: 13px; line-height: 1.8; color: #303133;">
        <div style="font-weight: 600; margin-bottom: 8px; color: #3370ff;">一键获取 x-token：</div>
        <div style="margin-bottom: 8px;">
          1. 点击
          <el-button size="small" type="primary" plain @click="openFeishuPage" style="margin: 0 4px;">打开飞书用例管理页</el-button>
          登录后进入页面
        </div>
        <div style="margin-bottom: 8px;">2. 按 <kbd style="background:#e8eaed;padding:1px 5px;border-radius:3px;font-size:12px;">F12</kbd> 打开 DevTools → 切到 <b>Console</b> 标签</div>
        <div style="margin-bottom: 8px;">3. 粘贴下方脚本并回车，token 会自动复制到剪贴板：</div>
        <div style="position: relative;">
          <pre style="background: #1e1e2e; color: #a6e3a1; padding: 10px 12px; border-radius: 6px; font-size: 12px; line-height: 1.5; overflow-x: auto; margin: 0; white-space: pre-wrap; word-break: break-all;">{{ consoleScript }}</pre>
          <el-button size="small" style="position: absolute; top: 6px; right: 6px; font-size: 11px;" @click="copyConsoleScript">复制脚本</el-button>
        </div>
        <div style="margin-top: 8px; color: #909399; font-size: 12px;">4. 回到此页面，粘贴 token 到下方输入框</div>
      </div>
      <el-form label-position="top">
        <el-form-item label="飞书 x-token" required>
          <el-input v-model="feishuToken" type="textarea" :rows="2" placeholder="粘贴自动复制的 x-token..." />
        </el-form-item>
        <el-form-item label="用例集标题（可选）">
          <el-input v-model="feishuTitle" :placeholder="caseSetDetail.name || '自动使用用例集名称'" />
        </el-form-item>
      </el-form>
      <el-alert v-if="feishuResult" :title="feishuResult.success ? '导入成功' : '导入失败'" :type="feishuResult.success ? 'success' : 'error'" show-icon style="margin-top: 12px;">
        <template #default>
          <div v-if="feishuResult.success">
            共导入 {{ feishuResult.case_count }} 条用例<br/>
            <a :href="feishuResult.case_set_url" target="_blank" style="color: #3370ff;">点击查看飞书用例集 →</a>
          </div>
          <div v-else>{{ feishuResult.message }}</div>
        </template>
      </el-alert>
      <template #footer>
        <el-button @click="feishuDialogVisible = false">关闭</el-button>
        <el-button type="primary" :loading="importingFeishu" :disabled="!feishuToken" @click="handleImportFeishu" style="background: #3370ff; border-color: #3370ff;">
          <el-icon><Upload /></el-icon> 确认导入
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, FolderOpened, Download, Upload } from '@element-plus/icons-vue'
import { getCaseSetDetail, getFunctionalCasesList, reviewFunctionalCase, deleteFunctionalCase, exportCaseSetXmind, importCasesToFeishu } from '@/api/functional_test'
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
    const caseSetId = route.params.caseSetId
    const res = await exportCaseSetXmind(projectId, caseSetId)
    const blobData = res.data || res
    const blob = new Blob([blobData], { type: 'application/octet-stream' })
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

// ===== 飞书导入 =====
const feishuDialogVisible = ref(false)
const importingFeishu = ref(false)
const feishuToken = ref(localStorage.getItem('feishu_x_token') || '')
const feishuTitle = ref('')
const feishuResult = ref(null)
const consoleScript = `fetch('/m-api/v1/builtin_app/test_management/mind/query?project_key=research__development&work_item_id=1&work_item_type_key=65f2fed3067c907f0466f016&mind_type=1',{headers:{'x-token':'test'}}).catch(()=>{});let _t='';const _o=XMLHttpRequest.prototype.open;const _s=XMLHttpRequest.prototype.setRequestHeader;XMLHttpRequest.prototype.setRequestHeader=function(k,v){if(k==='x-token'&&v&&!_t){_t=v;navigator.clipboard.writeText(v).then(()=>console.log('%c✅ x-token 已复制到剪贴板!','color:green;font-size:16px')).catch(()=>console.log('x-token:',v));XMLHttpRequest.prototype.setRequestHeader=_s;}return _s.apply(this,arguments);};setTimeout(()=>{if(!_t)console.log('%c⏳ 请点击页面任意位置触发请求...','color:orange;font-size:14px')},1000);`

const openFeishuPage = () => {
  window.open('https://project.feishu.cn/research__development/meegoPlg/MII_642BBF6AC6C74001_test_management_use_case_set', '_blank')
}

const copyConsoleScript = () => {
  navigator.clipboard.writeText(consoleScript).then(() => {
    ElMessage.success('脚本已复制，请到飞书页面的 Console 中粘贴执行')
  }).catch(() => {
    ElMessage.warning('复制失败，请手动选择复制')
  })
}

const showFeishuDialog = () => {
  feishuResult.value = null
  feishuTitle.value = caseSetDetail.value.name || ''
  feishuDialogVisible.value = true
}

const handleImportFeishu = async () => {
  if (!feishuToken.value) {
    ElMessage.warning('请输入飞书 x-token')
    return
  }
  try {
    importingFeishu.value = true
    feishuResult.value = null
    localStorage.setItem('feishu_x_token', feishuToken.value)

    const projectId = getProjectId()
    const caseSetId = route.params.caseSetId
    const response = await importCasesToFeishu(projectId, {
      case_set_id: parseInt(caseSetId),
      feishu_token: feishuToken.value,
      title: feishuTitle.value || undefined,
    })
    const data = response.data || response
    feishuResult.value = { success: true, case_count: data.case_count, case_set_url: data.case_set_url }
    ElMessage.success(`成功导入 ${data.case_count} 条用例到飞书`)
  } catch (error) {
    const msg = error.response?.data?.detail || error.message || '导入失败'
    feishuResult.value = { success: false, message: msg }
    ElMessage.error(msg)
  } finally {
    importingFeishu.value = false
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

.set-actions {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-shrink: 0;
}

.export-xmind-btn {
  font-size: 16px;
  font-weight: 600;
  padding: 14px 28px;
  border-radius: 8px;
}
.export-xmind-btn:hover {
  opacity: 0.9;
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
