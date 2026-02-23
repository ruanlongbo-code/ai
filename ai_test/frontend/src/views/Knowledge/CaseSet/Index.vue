<template>
  <div class="case-set-page">
    <!-- 顶部操作栏 -->
    <div class="page-header">
      <div class="header-left">
        <h2>用例集</h2>
        <span class="subtitle">导入历史用例作为AI训练数据，提升测试用例生成质量</span>
      </div>
      <div class="header-actions">
        <el-button type="primary" @click="showImportXmind">
          <el-icon><Upload /></el-icon>导入XMind
        </el-button>
        <el-button @click="handleImportFunctional" :loading="importing">
          <el-icon><DocumentCopy /></el-icon>从功能用例导入
        </el-button>
      </div>
    </div>

    <div class="main-content-area">
      <!-- 左侧用例集列表 -->
      <div class="left-panel">
        <div class="panel-header">用例集列表</div>
        <div class="case-set-list" v-loading="loadingList">
          <div v-if="caseSets.length === 0" class="empty-hint">暂无用例集，请导入</div>
          <div
            v-for="cs in caseSets" :key="cs.id"
            :class="['case-set-item', { active: selectedSetId === cs.id }]"
            @click="selectCaseSet(cs)"
          >
            <div class="cs-name">
              <el-icon><FolderOpened /></el-icon>
              <span>{{ cs.name }}</span>
            </div>
            <div class="cs-meta">
              <el-tag size="small" :type="cs.synced ? 'success' : 'info'">
                {{ cs.synced ? '已入库' : '未同步' }}
              </el-tag>
              <span class="cs-count">{{ cs.total_cases }} 条</span>
              <el-popconfirm title="确定删除？" @confirm="handleDeleteSet(cs.id)">
                <template #reference>
                  <el-button type="danger" size="small" link :icon="Delete" />
                </template>
              </el-popconfirm>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧用例树 + 详情 -->
      <div class="right-panel">
        <template v-if="selectedSetId">
          <div class="tree-and-detail">
            <!-- 树形结构 -->
            <div class="tree-panel">
              <div class="panel-header">用例结构</div>
              <el-tree
                v-loading="loadingTree"
                :data="treeData"
                :props="{ label: 'title', children: 'children' }"
                node-key="id"
                highlight-current
                default-expand-all
                @node-click="handleNodeClick"
              >
                <template #default="{ node, data }">
                  <span class="tree-node">
                    <el-icon v-if="data.node_type === 'module'" color="#8b5cf6"><Folder /></el-icon>
                    <el-icon v-else color="#67c23a"><Document /></el-icon>
                    <span>{{ data.title }}</span>
                    <el-tag v-if="data.priority" size="small" class="priority-tag">{{ data.priority }}</el-tag>
                  </span>
                </template>
              </el-tree>
            </div>

            <!-- 用例详情 -->
            <div class="detail-panel">
              <div class="panel-header">用例详情</div>
              <div v-if="!selectedNode" class="empty-hint">点击左侧用例查看详情</div>
              <div v-else class="case-detail">
                <h3>{{ selectedNode.title }}</h3>
                <el-tag v-if="selectedNode.priority" style="margin-bottom:12px">{{ selectedNode.priority }}</el-tag>
                <div v-if="selectedNode.preconditions" class="detail-section">
                  <div class="detail-label">前置条件</div>
                  <div class="detail-content">{{ selectedNode.preconditions }}</div>
                </div>
                <div v-if="selectedNode.test_steps" class="detail-section">
                  <div class="detail-label">测试步骤</div>
                  <div class="detail-content pre-wrap">{{ selectedNode.test_steps }}</div>
                </div>
                <div v-if="selectedNode.expected_result" class="detail-section">
                  <div class="detail-label">预期结果</div>
                  <div class="detail-content pre-wrap">{{ selectedNode.expected_result }}</div>
                </div>
                <div v-if="selectedNode.node_type === 'module' && selectedNode.children?.length" class="detail-section">
                  <div class="detail-label">子用例 ({{ selectedNode.children.length }})</div>
                  <el-table :data="selectedNode.children" size="small" stripe max-height="360">
                    <el-table-column prop="title" label="用例名称" min-width="200" show-overflow-tooltip />
                    <el-table-column prop="priority" label="优先级" width="80" />
                    <el-table-column prop="test_steps" label="测试步骤" min-width="200" show-overflow-tooltip />
                    <el-table-column prop="expected_result" label="预期结果" min-width="180" show-overflow-tooltip />
                  </el-table>
                </div>
              </div>
            </div>
          </div>
        </template>
        <template v-else>
          <div class="empty-state-full">
            <el-icon :size="64" color="#dcdfe6"><FolderOpened /></el-icon>
            <p>选择左侧用例集查看内容</p>
          </div>
        </template>
      </div>
    </div>

    <!-- XMind导入弹窗 -->
    <el-dialog v-model="xmindDialogVisible" title="导入XMind用例集" width="500px" :close-on-click-modal="false">
      <el-upload ref="uploadRef" :auto-upload="false" :limit="1" :on-change="f => xmindFile = f.raw" accept=".xmind" drag>
        <el-icon class="el-icon--upload"><Upload /></el-icon>
        <div class="el-upload__text">拖拽XMind文件到这里，或<em>点击上传</em></div>
        <template #tip><div class="el-upload__tip">支持 .xmind 格式，最大 20MB</div></template>
      </el-upload>
      <template #footer>
        <el-button @click="xmindDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="importing" @click="handleImportXmind">导入</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Delete } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useProjectStore } from '@/stores'
import { getCaseSetList, getCaseSetTree, importXmindCaseSet, importFunctionalCaseSet, deleteCaseSet } from '@/api/knowledge'

const projectStore = useProjectStore()
const projectId = computed(() => projectStore.currentProject?.id)

const caseSets = ref([])
const loadingList = ref(false)
const loadingTree = ref(false)
const importing = ref(false)
const selectedSetId = ref(null)
const treeData = ref([])
const selectedNode = ref(null)
const xmindDialogVisible = ref(false)
const xmindFile = ref(null)

const fetchCaseSets = async () => {
  if (!projectId.value) return
  loadingList.value = true
  try {
    const res = await getCaseSetList(projectId.value)
    caseSets.value = res.data.case_sets
  } catch { ElMessage.error('获取用例集列表失败') }
  finally { loadingList.value = false }
}

const selectCaseSet = async (cs) => {
  selectedSetId.value = cs.id
  selectedNode.value = null
  loadingTree.value = true
  try {
    const res = await getCaseSetTree(projectId.value, cs.id)
    treeData.value = res.data.tree
  } catch { ElMessage.error('获取用例集结构失败') }
  finally { loadingTree.value = false }
}

const handleNodeClick = (data) => { selectedNode.value = data }

const showImportXmind = () => { xmindFile.value = null; xmindDialogVisible.value = true }

const handleImportXmind = async () => {
  if (!xmindFile.value) { ElMessage.warning('请选择XMind文件'); return }
  importing.value = true
  try {
    const fd = new FormData()
    fd.append('file', xmindFile.value)
    const res = await importXmindCaseSet(projectId.value, fd)
    ElMessage.success(res.data.message)
    xmindDialogVisible.value = false
    fetchCaseSets()
  } catch (e) { ElMessage.error(e?.response?.data?.detail || '导入失败') }
  finally { importing.value = false }
}

const handleImportFunctional = async () => {
  if (!projectId.value) { ElMessage.warning('请先选择项目'); return }
  importing.value = true
  try {
    const res = await importFunctionalCaseSet(projectId.value)
    ElMessage.success(res.data.message)
    fetchCaseSets()
  } catch (e) { ElMessage.error(e?.response?.data?.detail || '导入失败') }
  finally { importing.value = false }
}

const handleDeleteSet = async (id) => {
  try {
    await deleteCaseSet(projectId.value, id)
    ElMessage.success('删除成功')
    if (selectedSetId.value === id) { selectedSetId.value = null; treeData.value = [] }
    fetchCaseSets()
  } catch { ElMessage.error('删除失败') }
}

onMounted(fetchCaseSets)
</script>

<style scoped>
.case-set-page { height: 100%; display: flex; flex-direction: column; padding: 10px; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px; }
.page-header h2 { margin: 0 0 4px 0; font-size: 20px; }
.subtitle { color: #909399; font-size: 13px; }
.main-content-area { flex: 1; display: flex; gap: 12px; min-height: 0; }
.left-panel { width: 280px; flex-shrink: 0; border: 1px solid #e4e7ed; border-radius: 8px; display: flex; flex-direction: column; overflow: hidden; }
.right-panel { flex: 1; border: 1px solid #e4e7ed; border-radius: 8px; overflow: hidden; display: flex; flex-direction: column; }
.panel-header { padding: 10px 14px; font-weight: 600; font-size: 13px; color: #606266; background: #f5f7fa; border-bottom: 1px solid #e4e7ed; }
.case-set-list { flex: 1; overflow-y: auto; padding: 8px; }
.case-set-item { padding: 10px 12px; border-radius: 6px; cursor: pointer; margin-bottom: 4px; transition: all .2s; }
.case-set-item:hover { background: #f5f7fa; }
.case-set-item.active { background: #ecf5ff; border-left: 3px solid #8b5cf6; }
.cs-name { display: flex; align-items: center; gap: 6px; font-size: 14px; font-weight: 500; margin-bottom: 6px; }
.cs-meta { display: flex; align-items: center; gap: 8px; font-size: 12px; color: #909399; }
.cs-count { margin-left: auto; }
.empty-hint { text-align: center; color: #c0c4cc; padding: 40px 0; font-size: 13px; }
.empty-state-full { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; color: #c0c4cc; }
.tree-and-detail { display: flex; flex: 1; min-height: 0; }
.tree-panel { width: 320px; flex-shrink: 0; border-right: 1px solid #e4e7ed; display: flex; flex-direction: column; overflow-y: auto; }
.detail-panel { flex: 1; display: flex; flex-direction: column; overflow-y: auto; }
.tree-node { display: flex; align-items: center; gap: 4px; font-size: 13px; }
.priority-tag { margin-left: 4px; }
.case-detail { padding: 16px; }
.case-detail h3 { margin: 0 0 8px; font-size: 16px; }
.detail-section { margin-bottom: 16px; }
.detail-label { font-size: 12px; color: #909399; margin-bottom: 4px; font-weight: 600; }
.detail-content { font-size: 14px; line-height: 1.6; color: #303133; background: #f9f9f9; padding: 10px 12px; border-radius: 6px; }
.pre-wrap { white-space: pre-wrap; }
</style>
