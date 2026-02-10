<template>
  <div class="dependency-management">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <h1>接口依赖设置</h1>
          <p class="subtitle" v-if="interfaceInfo">{{ interfaceInfo.method }} {{ interfaceInfo.path }}</p>
          <p class="subtitle" v-else>管理接口的依赖关系配置</p>
        </div>
        <div class="action-section">
          <el-button
              type="primary"
              @click="goBack"
          >
            <el-icon>
              <ArrowLeft/>
            </el-icon>
            返回接口列表页
          </el-button>

        </div>
      </div>
    </div>

    <!-- 主内容区域 -->
    <div class="main-content">
      <!-- 左侧：依赖分组列表 -->
      <div class="left-panel">
        <div class="panel-header">
          <h3>依赖分组</h3>
          <span class="group-count">{{ dependencyGroups.length }} 个分组</span>
        </div>

        <div class="group-list">
          <div
              v-for="group in dependencyGroups"
              :key="group.id"
              :class="['group-item', { active: selectedGroupId === group.id }]"
              @click="selectGroup(group)"
          >
            <div class="group-info">
              <div class="group-name">{{ group.name }}</div>
              <div class="group-desc">{{ group.description || '暂无描述' }}</div>
              <div class="group-meta">
                <span class="dependency-count">{{ group.dependencies?.length || 0 }} 个依赖</span>
                <span class="create-time">{{ formatTime(group.created_at) }}</span>
              </div>
            </div>
            <div class="group-actions">
              <div>
                <el-button size="small" @click.stop="handleEditGroup(group)" icon="Edit"></el-button>
              </div>
              <div>
                <el-button size="small" @click.stop="handleDeleteGroup(group)" icon="Delete"></el-button>
              </div>
            </div>
          </div>

          <!-- 空状态 -->
          <div v-if="dependencyGroups.length === 0" class="empty-state">
            <el-empty description="暂无依赖分组">
              <el-button type="primary" @click="handleCreateGroup">创建第一个分组</el-button>
            </el-empty>
          </div>
        </div>
      </div>

      <!-- 右侧：依赖配置详情 -->
      <div class="right-panel">
        <div v-if="selectedGroup" class="dependency-config">
          <div class="panel-header">
            <h3>{{ selectedGroup.name }} - 依赖配置</h3>
            <el-button type="primary" @click="handleCreateDependency">
              <el-icon>
                <Plus/>
              </el-icon>
              添加依赖
            </el-button>
          </div>

          <!-- 依赖列表 -->
          <div class="dependency-list">
            <div
                v-for="(dependency, index) in selectedGroup.dependencies"
                :key="dependency.id"
                class="dependency-item"
            >
              <div class="dependency-order">{{ index + 1 }}</div>
              <div class="dependency-content">
                <div class="dependency-header">
                  <div class="dependency-name">{{ dependency.name }}</div>
                  <div class="dependency-type">{{ getDependencyTypeLabel(dependency.dependency_type) }}</div>
                  <div class="dependency-status">
                    <el-tag :type="dependency.is_active ? 'success' : 'info'">
                      {{ dependency.is_active ? '启用' : '禁用' }}
                    </el-tag>
                  </div>
                </div>
                <div class="dependency-details">
                  <div class="detail-row">
                    <span class="label">源接口:</span>
                    <span class="value">{{ getSourceInterfaceName(dependency.source_interface_id) }}</span>
                  </div>
                  <div class="detail-row">
                    <span class="label">源字段路径:</span>
                    <span class="value">{{ dependency.source_field_path || '-' }}</span>
                  </div>
                  <div class="detail-row">
                    <span class="label">目标字段:</span>
                    <span class="value">{{ dependency.target_field_name }}</span>
                  </div>
                  <div v-if="dependency.description" class="detail-row">
                    <span class="label">描述:</span>
                    <span class="value">{{ dependency.description }}</span>
                  </div>
                </div>
              </div>
              <div class="dependency-actions">
                <el-button type="text" size="small" @click="handleEditDependency(dependency)">
                  编辑
                </el-button>
                <el-button
                    type="text"
                    size="small"
                    @click="handleDeleteDependency(dependency)"
                    class="danger-text"
                >
                  删除
                </el-button>
              </div>
            </div>

            <!-- 空状态 -->
            <div v-if="!selectedGroup.dependencies || selectedGroup.dependencies.length === 0"
                 class="empty-dependencies">
              <el-empty description="该分组暂无依赖配置">
                <el-button type="primary" @click="handleCreateDependency">添加第一个依赖</el-button>
              </el-empty>
            </div>
          </div>
        </div>

        <!-- 未选择分组状态 -->
        <div v-else class="no-selection">
          <el-empty description="请选择左侧的依赖分组查看详情"/>
        </div>
      </div>
    </div>

    <!-- 创建/编辑分组对话框 -->
    <GroupFormDialog
        v-model:visible="groupDialogVisible"
        :group-data="editingGroup"
        :interface-id="interfaceId"
        :project-id="projectId"
        @success="handleGroupSuccess"
    />

    <!-- 创建/编辑依赖对话框 -->
    <DependencyFormDialog
        v-model:visible="dependencyDialogVisible"
        :dependency-data="editingDependency"
        :group-id="selectedGroup?.id"
        :interface-id="interfaceId"
        @success="handleDependencySuccess"
    />
  </div>
</template>

<script setup>
import {ref, reactive, onMounted, computed} from 'vue'
import {useRoute, useRouter} from 'vue-router'
import {ElMessage, ElMessageBox} from 'element-plus'
import {ArrowLeft, Plus} from '@element-plus/icons-vue'
import {
  getDependencyGroups,
  deleteDependencyGroup,
  deleteDependency,
  getInterfaceDetail
} from '@/api/apiTest'
import {getProjectInterfaces} from '@/api/apiTest'
import GroupFormDialog from './components/GroupFormDialog.vue'
import DependencyFormDialog from './components/DependencyFormDialog.vue'

const route = useRoute()
const router = useRouter()

// 路由参数
const projectId = computed(() => parseInt(route.params.projectId))
const interfaceId = computed(() => parseInt(route.params.interfaceId))

// 数据状态
const interfaceInfo = ref(null)
const dependencyGroups = ref([])
const selectedGroupId = ref(null)
const selectedGroup = computed(() =>
    dependencyGroups.value.find(group => group.id === selectedGroupId.value)
)

// 对话框状态
const groupDialogVisible = ref(false)
const dependencyDialogVisible = ref(false)
const editingGroup = ref(null)
const editingDependency = ref(null)

// 接口列表缓存（用于显示源接口名称）
const interfaceList = ref([])

// 页面初始化
onMounted(async () => {
  await Promise.all([
    loadDependencyGroups(),
    loadInterfaceList()
  ])
})

// 加载接口信息
const loadInterfaceInfo = async () => {
  try {
    const response = await getInterfaceDetail(projectId.value, interfaceId.value)
    interfaceInfo.value = response.data
  } catch (error) {
    console.error('加载接口信息失败:', error)
    ElMessage.error('加载接口信息失败')
  }
}

// 加载依赖分组列表
const loadDependencyGroups = async () => {
  try {
    // 通过接口详情API获取包含完整依赖信息的数据
    const response = await getInterfaceDetail(projectId.value, interfaceId.value)
    
    // 更新接口信息
    interfaceInfo.value = response.data
    
    // 从接口详情中提取依赖分组信息
    dependencyGroups.value = response.data.dependency_groups || []
    
    // 如果有依赖分组且当前没有选中任何分组，默认选中第一个
    if (dependencyGroups.value.length > 0 && !selectedGroupId.value) {
      selectedGroupId.value = dependencyGroups.value[0].id
    }
    
    // 如果当前选中的分组不在列表中，重新选择第一个
    if (selectedGroupId.value && !dependencyGroups.value.find(g => g.id === selectedGroupId.value)) {
      selectedGroupId.value = dependencyGroups.value.length > 0 ? dependencyGroups.value[0].id : null
    }
  } catch (error) {
    console.error('加载依赖分组失败:', error)
    ElMessage.error('加载依赖分组失败')
  }
}

// 加载接口列表（用于显示源接口名称）
const loadInterfaceList = async () => {
  try {
    const response = await getProjectInterfaces(projectId.value, {page_size: 1000})
    interfaceList.value = response.data.interfaces || []
  } catch (error) {
    console.error('加载接口列表失败:', error)
  }
}

// 选择分组
const selectGroup = (group) => {
  selectedGroupId.value = group.id
}

// 返回接口管理页面
const goBack = () => {
  router.push(`/project/${projectId.value}/api-management`)
}

// 创建分组
const handleCreateGroup = () => {
  editingGroup.value = null
  groupDialogVisible.value = true
}

// 编辑分组
const handleEditGroup = (group) => {
  editingGroup.value = {...group}
  groupDialogVisible.value = true
}

// 删除分组
const handleDeleteGroup = async (group) => {
  try {
    await ElMessageBox.confirm(
        `确定要删除分组"${group.name}"吗？删除后该分组下的所有依赖配置将一并删除。`,
        '删除确认',
        {
          confirmButtonText: '确定删除',
          cancelButtonText: '取消',
          type: 'warning',
        }
    )

    await deleteDependencyGroup(projectId.value, group.id)
    ElMessage.success('删除成功')

    // 如果删除的是当前选中的分组，清空选中状态
    if (selectedGroupId.value === group.id) {
      selectedGroupId.value = null
    }

    await loadDependencyGroups()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除分组失败:', error)
      ElMessage.error('删除分组失败')
    }
  }
}

// 创建依赖
const handleCreateDependency = () => {
  if (!selectedGroup.value) {
    ElMessage.warning('请先选择一个依赖分组')
    return
  }
  editingDependency.value = null
  dependencyDialogVisible.value = true
}

// 编辑依赖
const handleEditDependency = (dependency) => {
  editingDependency.value = {...dependency}
  dependencyDialogVisible.value = true
}

// 删除依赖
const handleDeleteDependency = async (dependency) => {
  try {
    await ElMessageBox.confirm(
        `确定要删除依赖"${dependency.name}"吗？`,
        '删除确认',
        {
          confirmButtonText: '确定删除',
          cancelButtonText: '取消',
          type: 'warning',
        }
    )

    await deleteDependency(projectId.value, selectedGroup.value.id, dependency.id)
    ElMessage.success('删除成功')
    await loadDependencyGroups()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除依赖失败:', error)
      ElMessage.error('删除依赖失败')
    }
  }
}

// 分组操作成功回调
const handleGroupSuccess = async () => {
  groupDialogVisible.value = false
  await loadDependencyGroups()
}

// 依赖操作成功回调
const handleDependencySuccess = async () => {
  dependencyDialogVisible.value = false
  await loadDependencyGroups()
}

// 获取依赖类型标签
const getDependencyTypeLabel = (type) => {
  const typeMap = {
    header: '请求头',
    param: '参数',
    body: '请求体',
    response: '响应'
  }
  return typeMap[type] || type
}

// 获取源接口名称
const getSourceInterfaceName = (interfaceId) => {
  if (!interfaceId) return '-'
  const sourceInterface = interfaceList.value.find(item => item.id === interfaceId)
  return sourceInterface ? `${sourceInterface.method} ${sourceInterface.path}` : `接口ID: ${interfaceId}`
}

// 格式化时间
const formatTime = (time) => {
  if (!time) return ''
  return new Date(time).toLocaleDateString()
}
</script>

<style scoped>
.dependency-management {
  padding: 24px;
  background: #f8fafc;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.page-header {
  margin-bottom: 20px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  background: white;
  padding: 24px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.title-section {
  flex: 1;
}

.title-section h1 {
  color: #1f2937;
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
}

.subtitle {
  color: #6b7280;
  margin: 0;
  font-size: 14px;
}

.action-section {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.back-button {
  color: #6b7280;
  font-size: 14px;
  padding: 8px 12px;
  transition: color 0.2s;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
}

.back-button:hover {
  color: #409eff;
  border-color: #409eff;
}

.main-content {
  flex: 1;
  display: flex;
  gap: 20px;
  overflow: hidden;
}

.left-panel, .right-panel {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
}

.left-panel {
  width: 400px;
  min-width: 350px;
}

.right-panel {
  flex: 1;
}

.panel-header {
  padding: 16px 20px;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.panel-header h3 {
  margin: 0;
  font-size: 16px;
  color: #303133;
}

.group-count {
  font-size: 12px;
  color: #909399;
}

.group-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.group-item {
  padding: 16px;
  margin-bottom: 8px;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.group-item:hover {
  border-color: #409eff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.1);
}

.group-item.active {
  border-color: #409eff;
  background-color: #f0f9ff;
}

.group-info {
  flex: 1;
}

.group-name {
  font-weight: 500;
  color: #303133;
  margin-bottom: 4px;
}

.group-desc {
  font-size: 12px;
  color: #606266;
  margin-bottom: 8px;
}

.group-meta {
  display: flex;
  gap: 12px;
  font-size: 11px;
  color: #909399;
}

.group-actions {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.dependency-config {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.dependency-list {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.dependency-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  margin-bottom: 12px;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  background: #fafafa;
}

.dependency-order {
  width: 24px;
  height: 24px;
  background: #409eff;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 500;
  flex-shrink: 0;
}

.dependency-content {
  flex: 1;
}

.dependency-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.dependency-name {
  font-weight: 500;
  color: #303133;
}

.dependency-type {
  font-size: 12px;
  color: #409eff;
  background: #ecf5ff;
  padding: 2px 8px;
  border-radius: 12px;
}

.dependency-details {
  font-size: 12px;
}

.detail-row {
  display: flex;
  margin-bottom: 4px;
}

.detail-row .label {
  width: 80px;
  color: #909399;
  flex-shrink: 0;
}

.detail-row .value {
  color: #606266;
  flex: 1;
}

.dependency-actions {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.danger-text {
  color: #f56c6c !important;
}

.empty-state, .empty-dependencies, .no-selection {
  padding: 40px 20px;
  text-align: center;
}
</style>