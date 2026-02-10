<template>
  <div class="dependency-manager">
    <!-- 依赖分组列表 -->
    <div class="dependency-groups">
      <div class="groups-header">
        <h4>依赖分组</h4>
        <el-button
            type="primary"
            size="small"
            @click="handleCreateGroup"
            :disabled="readonly"
        >
          <el-icon>
            <Plus/>
          </el-icon>
          新建分组
        </el-button>
      </div>

      <div class="groups-list">
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
            </div>
          </div>
          <div class="group-actions" v-if="!readonly">
            <el-button size="small" @click.stop="handleEditGroup(group)" icon="Edit"></el-button>
            <el-button size="small" @click.stop="handleDeleteGroup(group)" icon="Delete"></el-button>
          </div>
        </div>

        <!-- 空状态 -->
        <div v-if="dependencyGroups.length === 0" class="empty-state">
          <el-empty description="暂无依赖分组" :image-size="80">
            <el-button v-if="!readonly" type="primary" @click="handleCreateGroup">创建第一个分组</el-button>
          </el-empty>
        </div>
      </div>
    </div>

    <!-- 依赖配置详情 -->
    <div class="dependency-details">
      <div v-if="selectedGroup" class="dependency-config">
        <div class="details-header">
          <div class="header-left">
            <h4>{{ selectedGroup.name }} - 依赖配置</h4>
          </div>
          <div class="header-right">
            <!-- 视图切换 -->
            <el-radio-group v-model="viewMode" size="small" class="view-toggle">
              <el-radio-button value="card">
                <el-icon><DataBoard /></el-icon>
                卡片视图
              </el-radio-button>
              <el-radio-button value="table">
                <el-icon><Document /></el-icon>
                表格视图
              </el-radio-button>
            </el-radio-group>
            <el-button
                v-if="!readonly"
                type="primary"
                size="small"
                @click="handleCreateDependency"
            >
              <el-icon>
                <Plus/>
              </el-icon>
              添加依赖
            </el-button>
          </div>
        </div>

        <!-- 依赖列表 -->
        <div class="dependency-list">
          <!-- 卡片视图 -->
          <div v-if="viewMode === 'card'" class="card-view">
            <div
                v-for="(dependency, index) in selectedGroup.dependencies"
                :key="dependency.id"
                class="dependency-item"
            >
              <div class="dependency-order">
                <div class="order-number">{{ index + 1 }}</div>
                <div class="order-line"></div>
              </div>
              <div class="dependency-card">
                <div class="card-header">
                  <div class="header-left">
                    <div class="dependency-name">
                      <el-icon class="name-icon"><Link /></el-icon>
                      {{ dependency.name }}
                    </div>
                    <div class="dependency-type-badge" :class="`type-${dependency.dependency_type}`">
                      <el-icon class="type-icon">
                        <component :is="getTypeIcon(dependency.dependency_type)" />
                      </el-icon>
                      {{ getDependencyTypeLabel(dependency.dependency_type) }}
                    </div>
                  </div>
                  <div class="header-right">
                    <div class="dependency-status">
                      <el-tag 
                        :type="dependency.is_active ? 'success' : 'info'" 
                        :effect="dependency.is_active ? 'dark' : 'plain'"
                        size="small"
                      >
                        <el-icon><component :is="dependency.is_active ? 'Check' : 'Close'" /></el-icon>
                        {{ dependency.is_active ? '启用' : '禁用' }}
                      </el-tag>
                    </div>
                    <div class="dependency-actions" v-if="!readonly">
                      <el-button 
                        size="small" 
                        type="primary" 
                        link 
                        @click="handleEditDependency(dependency)"
                      >
                        <el-icon><Edit /></el-icon>
                      </el-button>
                      <el-button 
                        size="small" 
                        type="danger" 
                        link 
                        @click="handleDeleteDependency(dependency)"
                      >
                        <el-icon><Delete /></el-icon>
                      </el-button>
                    </div>
                  </div>
                </div>
                
                <div class="card-body">
                  <div class="dependency-flow">
                    <div class="flow-item source">
                      <div class="flow-label">
                        <el-icon><Upload /></el-icon>
                        源接口
                      </div>
                      <div class="flow-content">
                        <div class="interface-info">{{ getSourceInterfaceName(dependency) }}</div>
                        <div class="field-path" v-if="dependency.source_field_path">
                          <code>{{ dependency.source_field_path }}</code>
                        </div>
                      </div>
                    </div>
                    
                    <div class="flow-arrow">
                      <el-icon><Right /></el-icon>
                    </div>
                    
                    <div class="flow-item target">
                      <div class="flow-label">
                        <el-icon><Download /></el-icon>
                        目标字段
                      </div>
                      <div class="flow-content">
                        <div class="target-field">
                          <code>{{ dependency.target_field_name }}</code>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <div v-if="dependency.description" class="dependency-description">
                    <el-icon><InfoFilled /></el-icon>
                    <span>{{ dependency.description }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 表格视图 -->
          <div v-else-if="viewMode === 'table'" class="table-view">
            <el-table 
              :data="selectedGroup.dependencies" 
              stripe 
              border
              class="dependency-table"
              :header-cell-style="{ background: '#f8fafc', color: '#374151', fontWeight: '600' }"
            >
              <el-table-column type="index" label="序号" width="60" align="center" />
              
              <el-table-column prop="name" label="依赖名称" min-width="150">
                <template #default="{ row }">
                  <div class="table-dependency-name">
                    <el-icon class="name-icon"><Link /></el-icon>
                    <span>{{ row.name }}</span>
                  </div>
                </template>
              </el-table-column>
              
              <el-table-column prop="dependency_type" label="类型" width="120" align="center">
                <template #default="{ row }">
                  <el-tag 
                    :class="`type-${row.dependency_type}`" 
                    size="small"
                    class="table-type-tag"
                  >
                    <el-icon class="type-icon">
                      <component :is="getTypeIcon(row.dependency_type)" />
                    </el-icon>
                    {{ getDependencyTypeLabel(row.dependency_type) }}
                  </el-tag>
                </template>
              </el-table-column>
              
              <el-table-column label="源接口" min-width="200">
                <template #default="{ row }">
                  <div class="table-source-info">
                    <div class="interface-name">{{ getSourceInterfaceName(row) }}</div>
                    <div v-if="row.source_field_path" class="field-path">
                      <code>{{ row.source_field_path }}</code>
                    </div>
                  </div>
                </template>
              </el-table-column>
              
              <el-table-column prop="target_field_name" label="目标字段" min-width="150">
                <template #default="{ row }">
                  <code class="target-field-code">{{ row.target_field_name }}</code>
                </template>
              </el-table-column>
              
              <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip>
                <template #default="{ row }">
                  <span class="description-text">{{ row.description || '-' }}</span>
                </template>
              </el-table-column>
              
              <el-table-column prop="is_active" label="状态" width="80" align="center">
                <template #default="{ row }">
                  <el-tag 
                    :type="row.is_active ? 'success' : 'info'" 
                    :effect="row.is_active ? 'dark' : 'plain'"
                    size="small"
                  >
                    <el-icon><component :is="row.is_active ? 'Check' : 'Close'" /></el-icon>
                  </el-tag>
                </template>
              </el-table-column>
              
              <el-table-column v-if="!readonly" label="操作" width="120" align="center" fixed="right">
                <template #default="{ row }">
                  <div class="table-actions">
                    <el-button 
                      size="small" 
                      type="primary" 
                      link 
                      @click="handleEditDependency(row)"
                      title="编辑"
                    >
                      <el-icon><Edit /></el-icon>
                    </el-button>
                    <el-button 
                      size="small" 
                      type="danger" 
                      link 
                      @click="handleDeleteDependency(row)"
                      title="删除"
                    >
                      <el-icon><Delete /></el-icon>
                    </el-button>
                  </div>
                </template>
              </el-table-column>
            </el-table>
          </div>

          <!-- 空状态 -->
          <div v-if="!selectedGroup.dependencies || selectedGroup.dependencies.length === 0"
               class="empty-dependencies">
            <el-empty description="该分组暂无依赖配置" :image-size="60">
              <el-button v-if="!readonly" type="primary" @click="handleCreateDependency">添加第一个依赖</el-button>
            </el-empty>
          </div>
        </div>
      </div>

      <!-- 未选择分组状态 -->
      <div v-else class="no-selection">
        <el-empty description="请选择左侧的依赖分组查看详情" :image-size="80"/>
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
import {ref, computed, onMounted, watch} from 'vue'
import {ElMessage, ElMessageBox} from 'element-plus'
import {
  Plus, Edit, Delete, Link, Upload, Download, Right, Check, Close, 
  InfoFilled, Document, Key, DataBoard, Connection
} from '@element-plus/icons-vue'
import {
  getInterfaceDetail,
  deleteDependencyGroup,
  deleteDependency,
  getProjectInterfaces
} from '@/api/apiTest'
import GroupFormDialog from '@/views/ApiTest/Dependency/components/GroupFormDialog.vue'
import DependencyFormDialog from '@/views/ApiTest/Dependency/components/DependencyFormDialog.vue'

const props = defineProps({
  projectId: {
    type: Number,
    required: true
  },
  interfaceId: {
    type: Number,
    required: true
  },
  readonly: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['change'])

// 数据状态
const dependencyGroups = ref([])
const selectedGroupId = ref(null)
const selectedGroup = computed(() =>
    dependencyGroups.value.find(group => group.id === selectedGroupId.value)
)
const interfaceList = ref([])
const viewMode = ref('card') // 视图模式：card 或 table

// 对话框状态
const groupDialogVisible = ref(false)
const dependencyDialogVisible = ref(false)
const editingGroup = ref(null)
const editingDependency = ref(null)

// 加载依赖分组数据
const loadDependencyGroups = async () => {
  try {
    // 通过接口详情API获取包含完整依赖信息的数据
    const response = await getInterfaceDetail(props.projectId, props.interfaceId)

    // 从接口详情中提取依赖分组信息
    dependencyGroups.value = response.data.dependency_groups || []

    // 如果有分组且没有选中的分组，默认选中第一个
    if (dependencyGroups.value.length > 0 && !selectedGroupId.value) {
      selectedGroupId.value = dependencyGroups.value[0].id
    }

    // 如果当前选中的分组不在列表中，重新选择第一个
    if (selectedGroupId.value && !dependencyGroups.value.find(g => g.id === selectedGroupId.value)) {
      selectedGroupId.value = dependencyGroups.value.length > 0 ? dependencyGroups.value[0].id : null
    }

    emit('change', dependencyGroups.value)
  } catch (error) {
    console.error('加载依赖分组失败:', error)
    ElMessage.error('加载依赖分组失败')
  }
}

// 加载项目接口列表
const loadProjectInterfaces = async () => {
  try {
    const response = await getProjectInterfaces(props.projectId, {page_size: 1000})
    interfaceList.value = response.data.interfaces || []
  } catch (error) {
    console.error('加载接口列表失败:', error)
  }
}

// 选择分组
const selectGroup = (group) => {
  selectedGroupId.value = group.id
}

// 获取依赖类型标签
const getDependencyTypeLabel = (type) => {
  const typeMap = {
    header: '请求头',
    param: '请求参数',
    body: '请求体',
    response: '响应'
  }
  return typeMap[type] || type
}

// 获取依赖类型图标
const getTypeIcon = (type) => {
  const iconMap = {
    header: 'Key',
    param: 'DataBoard',
    body: 'Document',
    response: 'Connection'
  }
  return iconMap[type] || 'Document'
}

// 获取源接口名称
const getSourceInterfaceName = (dependency) => {
  // 如果dependency是对象且包含源接口信息，直接使用
  if (typeof dependency === 'object' && dependency.source_interface_name) {
    const method = dependency.source_interface_method || ''
    const path = dependency.source_interface_path || ''
    return `${dependency.source_interface_name} - ${method} ${path}`
  }
  
  // 兼容旧版本：如果dependency是interfaceId数字，从interfaceList查找
  const interfaceId = typeof dependency === 'object' ? dependency.source_interface_id : dependency
  if (!interfaceId) return '-'
  
  const interface_ = interfaceList.value.find(item => item.id === interfaceId)
  return interface_ ? `${interface_.summary || '未命名接口'} - ${interface_.method} ${interface_.path}` : `接口 #${interfaceId}`
}

// 格式化时间
const formatTime = (timeStr) => {
  if (!timeStr) return ''
  return new Date(timeStr).toLocaleString()
}

// 分组操作
const handleCreateGroup = () => {
  editingGroup.value = null
  groupDialogVisible.value = true
}

const handleEditGroup = (group) => {
  editingGroup.value = group
  groupDialogVisible.value = true
}

const handleDeleteGroup = async (group) => {
  try {
    await ElMessageBox.confirm(
        `确定要删除分组"${group.name}"吗？删除后该分组下的所有依赖配置也将被删除。`,
        '删除确认',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }
    )

    await deleteDependencyGroup(props.projectId, group.id)
    ElMessage.success('分组删除成功')
    await loadDependencyGroups()

    // 如果删除的是当前选中的分组，清空选择
    if (selectedGroupId.value === group.id) {
      selectedGroupId.value = null
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除分组失败:', error)
      ElMessage.error('删除分组失败')
    }
  }
}

const handleGroupSuccess = () => {
  loadDependencyGroups()
}

// 依赖操作
const handleCreateDependency = () => {
  editingDependency.value = null
  dependencyDialogVisible.value = true
}

const handleEditDependency = (dependency) => {
  editingDependency.value = dependency
  dependencyDialogVisible.value = true
}

const handleDeleteDependency = async (dependency) => {
  try {
    await ElMessageBox.confirm(
        `确定要删除依赖"${dependency.name}"吗？`,
        '删除确认',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }
    )

    await deleteDependency(props.projectId, selectedGroup.value.id, dependency.id)
    ElMessage.success('依赖删除成功')
    await loadDependencyGroups()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除依赖失败:', error)
      ElMessage.error('删除依赖失败')
    }
  }
}

const handleDependencySuccess = () => {
  loadDependencyGroups()
}

// 监听props变化
watch(() => [props.projectId, props.interfaceId], () => {
  if (props.projectId && props.interfaceId) {
    loadDependencyGroups()
    loadProjectInterfaces()
  }
}, {immediate: true})

// 暴露方法给父组件
defineExpose({
  refresh: loadDependencyGroups,
  getDependencyGroups: () => dependencyGroups.value
})
</script>

<style scoped>
.dependency-manager {
  display: flex;
  gap: 16px;
  height: 100%;
  min-height: 400px;
}

.dependency-groups {
  flex: 0 0 300px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  overflow: hidden;
}

.groups-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f5f7fa;
  border-bottom: 1px solid #e4e7ed;
}

.groups-header h4 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
}

.groups-list {
  max-height: 350px;
  overflow-y: auto;
}

.group-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #f0f2f5;
  cursor: pointer;
  transition: background-color 0.2s;
}

.group-item:hover {
  background: #f5f7fa;
}

.group-item.active {
  background: #e6f7ff;
  border-color: #1890ff;
}

.group-info {
  flex: 1;
}

.group-name {
  font-weight: 500;
  margin-bottom: 4px;
}

.group-desc {
  font-size: 12px;
  color: #666;
  margin-bottom: 4px;
}

.group-meta {
  font-size: 12px;
  color: #999;
}

.group-actions {
  display: flex;
  gap: 4px;
}

.dependency-details {
  flex: 1;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  overflow: hidden;
}

.details-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f5f7fa;
  border-bottom: 1px solid #e4e7ed;
}

.details-header h4 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
}

.dependency-list {
  padding: 16px;
  max-height: 350px;
  overflow-y: auto;
}

.dependency-item {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
  position: relative;
}

.dependency-order {
  flex: 0 0 40px;
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
}

.order-number {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
  z-index: 2;
}

.order-line {
  width: 2px;
  flex: 1;
  background: linear-gradient(to bottom, #e1e5e9 0%, transparent 100%);
  margin-top: 8px;
  min-height: 20px;
}

.dependency-item:last-child .order-line {
  display: none;
}

.dependency-card {
  flex: 1;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  border: 1px solid #f0f2f5;
  overflow: hidden;
  transition: all 0.3s ease;
}

.dependency-card:hover {
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
  transform: translateY(-2px);
  border-color: #d9d9d9;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 20px 24px 16px;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-bottom: 1px solid #e2e8f0;
}

.header-left {
  flex: 1;
}

.dependency-name {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 12px;
}

.name-icon {
  color: #3b82f6;
  font-size: 18px;
}

.dependency-type-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.type-header {
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
  color: #92400e;
  border: 1px solid #f59e0b;
}

.type-param {
  background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
  color: #1e40af;
  border: 1px solid #3b82f6;
}

.type-body {
  background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%);
  color: #166534;
  border: 1px solid #22c55e;
}

.type-response {
  background: linear-gradient(135deg, #fce7f3 0%, #fbcfe8 100%);
  color: #be185d;
  border: 1px solid #ec4899;
}

.type-icon {
  font-size: 14px;
}

.header-right {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.dependency-status .el-tag {
  border-radius: 6px;
  font-weight: 500;
}

.dependency-actions {
  display: flex;
  gap: 4px;
}

.card-body {
  padding: 20px 24px 24px;
}

.dependency-flow {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 16px;
}

.flow-item {
  flex: 1;
  background: #f8fafc;
  border-radius: 8px;
  padding: 16px;
  border: 1px solid #e2e8f0;
}

.flow-item.source {
  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
  border-color: #93c5fd;
}

.flow-item.target {
  background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
  border-color: #86efac;
}

.flow-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 8px;
}

.flow-content {
  font-size: 14px;
}

.interface-info {
  color: #334155;
  font-weight: 500;
  margin-bottom: 4px;
}

.field-path code,
.target-field code {
  background: #1e293b;
  color: #e2e8f0;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}

.flow-arrow {
  flex: 0 0 auto;
  color: #64748b;
  font-size: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: #fff;
  border-radius: 50%;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border: 2px solid #e2e8f0;
}

.dependency-description {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 12px 16px;
  background: #f8fafc;
  border-radius: 6px;
  border-left: 3px solid #3b82f6;
  font-size: 13px;
  color: #475569;
  line-height: 1.5;
}

.dependency-description .el-icon {
  color: #3b82f6;
  margin-top: 2px;
  flex-shrink: 0;
}

.empty-state,
.empty-dependencies,
.no-selection {
  padding: 20px;
  text-align: center;
}

/* 头部样式 */
.details-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e2e8f0;
}

.header-left h4 {
  margin: 0;
  color: #1e293b;
  font-size: 18px;
  font-weight: 600;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.view-toggle {
  border-radius: 8px;
  overflow: hidden;
}

.view-toggle .el-radio-button__inner {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: none;
  background: #f8fafc;
  color: #64748b;
  transition: all 0.3s ease;
}

.view-toggle .el-radio-button__original-radio:checked + .el-radio-button__inner {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
}

/* 表格视图样式 */
.table-view {
  margin-top: 16px;
}

.dependency-table {
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.table-dependency-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

.table-dependency-name .name-icon {
  color: #3b82f6;
  font-size: 16px;
}

.table-type-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.table-type-tag.type-header {
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
  color: #92400e;
  border: 1px solid #f59e0b;
}

.table-type-tag.type-param {
  background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
  color: #1e40af;
  border: 1px solid #3b82f6;
}

.table-type-tag.type-body {
  background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%);
  color: #166534;
  border: 1px solid #22c55e;
}

.table-type-tag.type-response {
  background: linear-gradient(135deg, #fce7f3 0%, #fbcfe8 100%);
  color: #be185d;
  border: 1px solid #ec4899;
}

.table-source-info .interface-name {
  color: #334155;
  font-weight: 500;
  margin-bottom: 4px;
}

.table-source-info .field-path code {
  background: #1e293b;
  color: #e2e8f0;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 11px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}

.target-field-code {
  background: #1e293b;
  color: #e2e8f0;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}

.description-text {
  color: #64748b;
  font-size: 13px;
  line-height: 1.4;
}

.table-actions {
  display: flex;
  justify-content: center;
  gap: 8px;
}
</style>