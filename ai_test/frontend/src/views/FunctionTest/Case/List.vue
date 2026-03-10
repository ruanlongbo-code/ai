<template>
  <div class="functional-cases-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <h1>功能用例管理</h1>
          <p class="subtitle">以用例集为维度管理测试用例，支持场景分组和智能生成</p>
        </div>
        <div class="action-section">
          <el-button type="primary" @click="handleCreateCaseSet">
            <el-icon><FolderAdd /></el-icon>
            新建用例集
          </el-button>
          <el-button @click="handleRefresh">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </div>
    </div>

    <!-- 统计概览 -->
    <div class="stats-bar">
      <el-card shadow="never">
        <div class="stats-row">
          <div class="stat-item">
            <span class="stat-value">{{ caseSets.length }}</span>
            <span class="stat-label">用例集</span>
          </div>
          <el-divider direction="vertical" />
          <div class="stat-item">
            <span class="stat-value">{{ totalCases }}</span>
            <span class="stat-label">用例总数</span>
          </div>
          <el-divider direction="vertical" />
          <div class="stat-item">
            <span class="stat-value">{{ totalScenarios }}</span>
            <span class="stat-label">场景数</span>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 搜索和筛选 -->
    <div class="filter-toolbar">
      <el-input
        v-model="keyword"
        placeholder="搜索用例集名称"
        style="width: 300px;"
        clearable
        @input="handleSearch"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
    </div>

    <!-- 用例集卡片列表 -->
    <div v-loading="loading" class="case-sets-grid">
      <template v-if="filteredCaseSets.length > 0">
        <el-card
          v-for="cs in filteredCaseSets"
          :key="cs.id"
          class="case-set-card"
          shadow="hover"
          @click="handleOpenCaseSet(cs)"
        >
          <div class="card-body">
            <!-- 卡片头部 -->
            <div class="card-top">
              <div class="card-icon">
                <el-icon :size="28" color="#409EFF"><FolderOpened /></el-icon>
              </div>
              <div class="card-actions" @click.stop>
                <el-dropdown trigger="click">
                  <el-button :icon="MoreFilled" circle size="small" text />
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item @click="handleEditCaseSet(cs)">
                        <el-icon><Edit /></el-icon> 编辑
                      </el-dropdown-item>
                      <el-dropdown-item @click="handleExportXmind(cs)">
                        <el-icon><Download /></el-icon> 导出 XMind
                      </el-dropdown-item>
                      <el-dropdown-item @click="handleDeleteCaseSet(cs)" divided>
                        <el-icon color="#F56C6C"><Delete /></el-icon>
                        <span style="color: #F56C6C;">删除</span>
                      </el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
            </div>

            <!-- 卡片标题 -->
            <h3 class="card-title">{{ cs.name }}</h3>
            <p class="card-desc" v-if="cs.description">{{ cs.description }}</p>

            <!-- 关联需求 -->
            <div class="card-requirement" v-if="cs.requirement_title">
              <el-tag size="small" effect="plain" type="info">
                📋 {{ cs.requirement_title }}
              </el-tag>
            </div>

            <!-- 统计信息 -->
            <div class="card-stats">
              <div class="stat-badge">
                <span class="badge-value">{{ cs.case_count }}</span>
                <span class="badge-label">用例</span>
              </div>
              <div class="stat-badge">
                <span class="badge-value">{{ cs.scenario_count }}</span>
                <span class="badge-label">场景</span>
              </div>
            </div>

            <!-- 卡片底部 -->
            <div class="card-footer">
              <span class="creator">{{ cs.creator_name || '系统' }}</span>
              <span class="time">{{ formatDate(cs.created_at) }}</span>
            </div>
          </div>
        </el-card>
      </template>

      <!-- 空状态 -->
      <div v-else class="empty-state">
        <el-empty description="暂无用例集">
          <template #description>
            <p>还没有用例集，可以通过 <b>需求详情页</b> 的「生成用例」创建，或手动新建用例集</p>
          </template>
          <el-button type="primary" @click="handleCreateCaseSet">新建用例集</el-button>
        </el-empty>
      </div>
    </div>

    <!-- 新建/编辑用例集弹窗 -->
    <el-dialog
      v-model="caseSetDialog.visible"
      :title="caseSetDialog.isEdit ? '编辑用例集' : '新建用例集'"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form :model="caseSetDialog.form" label-width="80px">
        <el-form-item label="名称" required>
          <el-input v-model="caseSetDialog.form.name" placeholder="请输入用例集名称" maxlength="100" show-word-limit />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="caseSetDialog.form.description" type="textarea" :rows="3" placeholder="用例集描述（选填）" />
        </el-form-item>
        <el-form-item label="关联需求">
          <el-select v-model="caseSetDialog.form.requirement_id" placeholder="选择关联需求（选填）" clearable style="width: 100%;">
            <el-option v-for="req in requirements" :key="req.id" :label="req.title" :value="req.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="caseSetDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="handleSaveCaseSet" :loading="caseSetDialog.loading">
          {{ caseSetDialog.isEdit ? '保存' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { FolderAdd, Refresh, Search, FolderOpened, Edit, Delete, MoreFilled, Download } from '@element-plus/icons-vue'
import { getCaseSetList, createCaseSet, updateCaseSet, deleteCaseSet, getRequirementsList, exportCaseSetXmind } from '@/api/functional_test'
import { useProjectStore } from '@/stores'

const router = useRouter()
const route = useRoute()
const projectStore = useProjectStore()

// 响应式数据
const loading = ref(false)
const caseSets = ref([])
const requirements = ref([])
const keyword = ref('')

// 计算属性
const filteredCaseSets = computed(() => {
  if (!keyword.value) return caseSets.value
  const kw = keyword.value.toLowerCase()
  return caseSets.value.filter(cs =>
    (cs.name || '').toLowerCase().includes(kw) ||
    (cs.requirement_title || '').toLowerCase().includes(kw)
  )
})

const totalCases = computed(() => caseSets.value.reduce((sum, cs) => sum + (cs.case_count || 0), 0))
const totalScenarios = computed(() => caseSets.value.reduce((sum, cs) => sum + (cs.scenario_count || 0), 0))

// 弹窗
const caseSetDialog = reactive({
  visible: false,
  isEdit: false,
  editId: null,
  loading: false,
  form: {
    name: '',
    description: '',
    requirement_id: null
  }
})

// 工具函数
const getProjectId = () => {
  let projectId = route.params.projectId || projectStore.currentProject?.id
  if (!projectId) {
    try {
      const projectStr = localStorage.getItem('currentProject')
      if (projectStr) {
        const project = JSON.parse(projectStr)
        projectId = project.id
      }
    } catch (e) { /* ignore */ }
  }
  return projectId || 1
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const d = new Date(dateStr)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

// 加载数据
const loadCaseSets = async () => {
  loading.value = true
  try {
    const projectId = getProjectId()
    const res = await getCaseSetList(projectId)
    const data = res.data || res
    caseSets.value = data.case_sets || []
  } catch (e) {
    console.error('加载用例集失败:', e)
    ElMessage.error('加载用例集失败')
    caseSets.value = []
  } finally {
    loading.value = false
  }
}

const loadRequirements = async () => {
  try {
    const projectId = getProjectId()
    const res = await getRequirementsList(projectId, { page_size: 1000 })
    const data = res.data || res
    requirements.value = data.requirements || []
  } catch (e) {
    requirements.value = []
  }
}

const handleRefresh = async () => {
  await Promise.all([loadCaseSets(), loadRequirements()])
  ElMessage.success('刷新成功')
}

const handleSearch = () => {
  // 前端搜索，不需要重新请求
}

// 用例集操作
const handleOpenCaseSet = (cs) => {
  router.push({
    name: 'FunctionTestCaseSetDetail',
    params: { caseSetId: cs.id }
  })
}

const handleCreateCaseSet = () => {
  caseSetDialog.isEdit = false
  caseSetDialog.editId = null
  caseSetDialog.form = { name: '', description: '', requirement_id: null }
  caseSetDialog.visible = true
}

const handleEditCaseSet = (cs) => {
  caseSetDialog.isEdit = true
  caseSetDialog.editId = cs.id
  caseSetDialog.form = {
    name: cs.name,
    description: cs.description || '',
    requirement_id: cs.requirement_id
  }
  caseSetDialog.visible = true
}

const handleDeleteCaseSet = async (cs) => {
  try {
    await ElMessageBox.confirm(
      `删除用例集「${cs.name}」后，其下 ${cs.case_count} 条用例也会被删除，确定删除吗？`,
      '确认删除',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    )
    const projectId = getProjectId()
    await deleteCaseSet(projectId, cs.id)
    ElMessage.success('用例集已删除')
    await loadCaseSets()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error(e.response?.data?.detail || '删除失败')
    }
  }
}

const handleExportXmind = async (cs) => {
  try {
    const projectId = getProjectId()
    const res = await exportCaseSetXmind(projectId, cs.id)
    const blobData = res.data || res
    const blob = new Blob([blobData], { type: 'application/octet-stream' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${cs.name}_测试用例.xmind`
    a.click()
    window.URL.revokeObjectURL(url)
    ElMessage.success('XMind 导出成功')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '导出失败')
  }
}

const handleSaveCaseSet = async () => {
  if (!caseSetDialog.form.name?.trim()) {
    ElMessage.warning('请输入用例集名称')
    return
  }
  caseSetDialog.loading = true
  try {
    const projectId = getProjectId()
    if (caseSetDialog.isEdit) {
      await updateCaseSet(projectId, caseSetDialog.editId, {
        name: caseSetDialog.form.name,
        description: caseSetDialog.form.description
      })
      ElMessage.success('用例集更新成功')
    } else {
      await createCaseSet(projectId, caseSetDialog.form)
      ElMessage.success('用例集创建成功')
    }
    caseSetDialog.visible = false
    await loadCaseSets()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  } finally {
    caseSetDialog.loading = false
  }
}

// 生命周期
onMounted(() => {
  loadCaseSets()
  loadRequirements()
})
</script>

<style scoped>
.functional-cases-page {
  padding: 16px;
  background: #f5f7fa;
  min-height: auto;
}

.page-header {
  margin-bottom: 12px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: white;
  padding: 16px 20px;
  border-radius: 10px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}

.title-section h1 {
  color: #1f2937;
  margin: 0 0 2px 0;
  font-size: 18px;
  font-weight: 600;
}

.subtitle {
  color: #9ca3af;
  margin: 0;
  font-size: 13px;
}

.action-section {
  display: flex;
  gap: 10px;
}

/* 统计栏 */
.stats-bar {
  margin-bottom: 10px;
}

.stats-row {
  display: flex;
  align-items: center;
  gap: 20px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1px;
}

.stat-value {
  font-size: 20px;
  font-weight: 700;
  color: #409EFF;
}

.stat-label {
  font-size: 12px;
  color: #9ca3af;
}

/* 搜索 */
.filter-toolbar {
  margin-bottom: 10px;
}

/* 卡片网格 */
.case-sets-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px;
  min-height: 160px;
}

.case-set-card {
  cursor: pointer;
  border-radius: 12px;
  transition: all 0.25s ease;
  border: 1px solid #e5e7eb;
}

.case-set-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
  border-color: #409EFF;
}

.card-body {
  padding: 4px;
}

.card-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.card-icon {
  width: 44px;
  height: 44px;
  background: #ecf5ff;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 6px 0;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-desc {
  font-size: 13px;
  color: #6b7280;
  margin: 0 0 10px 0;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-requirement {
  margin-bottom: 12px;
}

.card-stats {
  display: flex;
  gap: 16px;
  margin-bottom: 14px;
}

.stat-badge {
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.badge-value {
  font-size: 18px;
  font-weight: 700;
  color: #374151;
}

.badge-label {
  font-size: 12px;
  color: #9ca3af;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 10px;
  border-top: 1px solid #f3f4f6;
  font-size: 12px;
  color: #9ca3af;
}

.empty-state {
  grid-column: 1 / -1;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 180px;
}

/* 响应式 */
@media (max-width: 768px) {
  .functional-cases-page {
    padding: 16px;
  }

  .header-content {
    flex-direction: column;
    gap: 16px;
  }

  .case-sets-grid {
    grid-template-columns: 1fr;
  }
}
</style>
