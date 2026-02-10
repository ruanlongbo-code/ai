<template>
  <div class="interface-detail-modal">
    <el-dialog
      :model-value="visible"
      @update:model-value="$emit('update:visible', $event)"
      title="接口详情"
      width="70%"
      top="5vh"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
    >
      <div v-if="loading" class="loading-container">
        <el-icon class="is-loading"><Loading /></el-icon>
        <span>加载中...</span>
      </div>
      
      <div v-else-if="interfaceData" class="interface-detail-content">
        <!-- 头部信息卡片 -->
        <div class="interface-header-card">
          <div class="header-left">
            <div class="interface-title">
              <el-icon class="title-icon"><Document /></el-icon>
              <span>{{ interfaceData.summary || interfaceData.path }}</span>
            </div>
            <div class="interface-path">
              <el-tag 
                :type="getMethodTagType(interfaceData.method)"
                size="large"
              >
                {{ interfaceData.method }}
              </el-tag>
              <code class="path-text">{{ interfaceData.path }}</code>
            </div>
          </div>
          <div class="header-right">
            <div class="time-info">
              <div class="time-item">
                <el-icon><Clock /></el-icon>
                <span>创建时间：{{ formatDate(interfaceData.created_at) }}</span>
              </div>
              <div class="time-item">
                <el-icon><Refresh /></el-icon>
                <span>更新时间：{{ formatDate(interfaceData.updated_at) }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 接口详情网格布局 -->
        <div class="interface-details-grid">
          <!-- 基本信息 -->
          <div class="detail-card">
            <div class="detail-header">
              <el-icon class="detail-icon"><InfoFilled /></el-icon>
              <h4>基本信息</h4>
            </div>
            <div class="detail-content">
              <div class="info-item">
                <label>接口名称：</label>
                <span>{{ interfaceData.summary || '-' }}</span>
              </div>
              <div class="info-item">
                <label>接口描述：</label>
                <span>{{ interfaceData.description || '-' }}</span>
              </div>
              <div class="info-item">
                <label>所属模块：</label>
                <span>{{ interfaceData.module || '-' }}</span>
              </div>
            </div>
          </div>

          <!-- 请求参数 -->
          <div class="detail-card full-width">
            <div class="detail-header">
              <el-icon class="detail-icon"><Setting /></el-icon>
              <h4>路径参数和请求头</h4>
            </div>
            <div class="detail-content">
              <el-tabs v-model="activeTab" class="parameter-tabs">
                <el-tab-pane label="路径参数" name="path">
                  <div v-if="interfaceData.parameters?.path?.length > 0" class="parameter-list">
                    <div v-for="param in interfaceData.parameters.path" :key="param.name" class="parameter-item">
                      <div class="param-name">{{ param.name }}</div>
                      <div class="param-type">{{ param.type || 'string' }}</div>
                      <div class="param-required">{{ param.required ? '必填' : '可选' }}</div>
                      <div class="param-description">{{ param.description || '-' }}</div>
                    </div>
                  </div>
                  <div v-else class="empty-content">
                    <el-icon><DocumentRemove /></el-icon>
                    <span>暂无路径参数</span>
                  </div>
                </el-tab-pane>
                
                <el-tab-pane label="查询参数" name="query">
                  <div v-if="interfaceData.parameters?.query?.length > 0" class="parameter-list">
                    <div v-for="param in interfaceData.parameters.query" :key="param.name" class="parameter-item">
                      <div class="param-name">{{ param.name }}</div>
                      <div class="param-type">{{ param.type || 'string' }}</div>
                      <div class="param-required">{{ param.required ? '必填' : '可选' }}</div>
                      <div class="param-description">{{ param.description || '-' }}</div>
                    </div>
                  </div>
                  <div v-else class="empty-content">
                    <el-icon><DocumentRemove /></el-icon>
                    <span>暂无查询参数</span>
                  </div>
                </el-tab-pane>
                
                <el-tab-pane label="请求头参数" name="header">
                  <div v-if="interfaceData.parameters?.header?.length > 0" class="parameter-list">
                    <div v-for="param in interfaceData.parameters.header" :key="param.name" class="parameter-item">
                      <div class="param-name">{{ param.name }}</div>
                      <div class="param-type">{{ param.type || 'string' }}</div>
                      <div class="param-required">{{ param.required ? '必填' : '可选' }}</div>
                      <div class="param-description">{{ param.description || '-' }}</div>
                    </div>
                  </div>
                  <div v-else class="empty-content">
                    <el-icon><DocumentRemove /></el-icon>
                    <span>暂无请求头参数</span>
                  </div>
                </el-tab-pane>
              </el-tabs>
            </div>
          </div>

          <!-- 请求体 -->
          <div class="detail-card full-width">
            <div class="detail-header">
              <el-icon class="detail-icon"><Document /></el-icon>
              <h4>请求体参数</h4>
            </div>
            <div class="detail-content">
              <div v-if="interfaceData.request_body && Object.keys(interfaceData.request_body).length > 0" class="request-body-content">
                <div class="json-content">
                  <pre class="json-text">{{ formatJson(interfaceData.request_body) }}</pre>
                </div>
              </div>
              <div v-else class="empty-content">
                <el-icon><DocumentRemove /></el-icon>
                <span>暂无请求体</span>
              </div>
            </div>
          </div>

          <!-- 响应信息 -->
          <div class="detail-card full-width">
            <div class="detail-header">
              <el-icon class="detail-icon"><DataLine /></el-icon>
              <h4>响应示例</h4>
            </div>
            <div class="detail-content">
              <div v-if="interfaceData.responses && interfaceData.responses.length > 0" class="responses-content">
                <div v-for="(response, index) in interfaceData.responses" :key="index" class="response-item">
                  <div class="response-header">
                    <el-tag :type="getStatusTagType(response.status_code)">
                      {{ response.status_code }}
                    </el-tag>
                    <span class="response-description">{{ response.description || '-' }}</span>
                  </div>
                  <div v-if="response.content" class="response-content">
                    <pre class="json-text">{{ formatJson(response.content) }}</pre>
                  </div>
                </div>
              </div>
              <div v-else class="empty-content">
                <el-icon><DocumentRemove /></el-icon>
                <span>暂无响应信息</span>
              </div>
            </div>
          </div>

          <!-- 依赖组信息 -->
          <div class="detail-card full-width">
            <div class="detail-header">
              <el-icon class="detail-icon"><Connection /></el-icon>
              <h4>接口前置依赖</h4>
            </div>
            <div class="detail-content">
              <div v-if="interfaceData.dependency_groups && interfaceData.dependency_groups.length > 0" class="dependency-groups-content">
                <div v-for="group in interfaceData.dependency_groups" :key="group.id" class="dependency-group-item">
                  <div class="group-header">
                    <div class="group-title">
                      <el-icon class="group-icon"><FolderOpened /></el-icon>
                      <span class="group-name">{{ group.name }}</span>
                      <el-tag size="small" type="info">{{ group.dependencies?.length || 0 }} 个依赖</el-tag>
                    </div>
                    <div class="group-description">{{ group.description || '暂无描述' }}</div>
                  </div>
                  
                  <div v-if="group.dependencies && group.dependencies.length > 0" class="dependencies-list">
                    <div class="dependencies-header">
                      <div class="dep-col-name">依赖名称</div>
                      <div class="dep-col-type">类型</div>
                      <div class="dep-col-source">源接口</div>
                      <div class="dep-col-field">源字段路径</div>
                      <div class="dep-col-target">目标字段</div>
                      <div class="dep-col-status">状态</div>
                    </div>
                    <div v-for="dependency in group.dependencies" :key="dependency.id" class="dependency-item">
                      <div class="dep-col-name">
                        <span class="dependency-name">{{ dependency.name }}</span>
                        <div class="dependency-desc">{{ dependency.description || '-' }}</div>
                      </div>
                      <div class="dep-col-type">
                        <el-tag :type="getDependencyTypeTagType(dependency.dependency_type)" size="small">
                          {{ getDependencyTypeLabel(dependency.dependency_type) }}
                        </el-tag>
                      </div>
                      <div class="dep-col-source">
                        <span v-if="dependency.source_interface_id" class="source-interface">
                          接口 #{{ dependency.source_interface_id }}
                        </span>
                        <span v-else class="no-source">-</span>
                      </div>
                      <div class="dep-col-field">
                        <code v-if="dependency.source_field_path" class="field-path">
                          {{ dependency.source_field_path }}
                        </code>
                        <span v-else class="no-field">-</span>
                      </div>
                      <div class="dep-col-target">
                        <code class="target-field">{{ dependency.target_field_name }}</code>
                      </div>
                      <div class="dep-col-status">
                        <el-tag :type="dependency.is_active ? 'success' : 'danger'" size="small">
                          {{ dependency.is_active ? '启用' : '禁用' }}
                        </el-tag>
                      </div>
                    </div>
                  </div>
                  <div v-else class="empty-dependencies">
                    <el-icon><DocumentRemove /></el-icon>
                    <span>该分组暂无依赖配置</span>
                  </div>
                </div>
              </div>
              <div v-else class="empty-content">
                <el-icon><DocumentRemove /></el-icon>
                <span>该接口暂无依赖组配置</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="$emit('update:visible', false)">关闭</el-button>
          <el-button type="primary" @click="handleEdit">编辑接口</el-button>
          <el-button type="success" @click="handleTest">测试接口</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { 
  Document, 
  InfoFilled, 
  Setting, 
  DataLine, 
  Clock, 
  Refresh, 
  DocumentRemove,
  Loading,
  Connection,
  FolderOpened
} from '@element-plus/icons-vue'

// Props
const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  interfaceData: {
    type: Object,
    default: () => ({})
  }
})

// Emits
const emit = defineEmits(['update:visible', 'edit', 'test'])

// 响应式数据
const loading = ref(false)
const activeTab = ref('path')

// 获取方法标签类型
const getMethodTagType = (method) => {
  const typeMap = {
    'GET': 'primary',
    'POST': 'success',
    'PUT': 'warning',
    'PATCH': 'warning',
    'DELETE': 'danger'
  }
  return typeMap[method] || 'info'
}

// 获取状态码标签类型
const getStatusTagType = (statusCode) => {
  if (statusCode >= 200 && statusCode < 300) return 'success'
  if (statusCode >= 300 && statusCode < 400) return 'warning'
  if (statusCode >= 400) return 'danger'
  return 'info'
}

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN')
}

// 格式化JSON
const formatJson = (obj) => {
  if (!obj) return ''
  try {
    return JSON.stringify(obj, null, 2)
  } catch (error) {
    return String(obj)
  }
}

// 获取依赖类型标签类型
const getDependencyTypeTagType = (type) => {
  const typeMap = {
    'field_mapping': 'primary',
    'response_extraction': 'success',
    'parameter_injection': 'warning',
    'header_injection': 'info'
  }
  return typeMap[type] || 'info'
}

// 获取依赖类型标签文本
const getDependencyTypeLabel = (type) => {
  const labelMap = {
    'field_mapping': '字段映射',
    'response_extraction': '响应提取',
    'parameter_injection': '参数注入',
    'header_injection': '请求头注入'
  }
  return labelMap[type] || type
}

// 事件处理
const handleEdit = () => {
  emit('edit', props.interfaceData)
}

const handleTest = () => {
  emit('test', props.interfaceData)
}

// 监听弹窗显示状态
watch(() => props.visible, (newVal) => {
  if (newVal) {
    activeTab.value = 'path'
  }
})
</script>

<style scoped>
.interface-detail-modal :deep(.el-dialog) {
  border-radius: 8px;
  overflow: hidden;
}

.interface-detail-modal :deep(.el-dialog__header) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 20px 24px;
  border-bottom: none;
}

.interface-detail-modal :deep(.el-dialog__title) {
  font-size: 18px;
  font-weight: 600;
  color: white;
}

.interface-detail-modal :deep(.el-dialog__headerbtn .el-dialog__close) {
  color: white;
  font-size: 20px;
}

.interface-detail-modal :deep(.el-dialog__body) {
  padding: 0;
  max-height: 70vh;
  overflow-y: auto;
}

/* 加载状态 */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: #909399;
}

.loading-container .el-icon {
  font-size: 32px;
  margin-bottom: 16px;
}

/* 接口详情内容 */
.interface-detail-content {
  padding: 24px;
  background: #f8fafc;
}

/* 头部信息卡片 */
.interface-header-card {
  background: white;
  border-radius: 8px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  border-left: 4px solid #409eff;
}

.header-left {
  flex: 1;
}

.interface-title {
  display: flex;
  align-items: center;
  font-size: 20px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 16px;
}

.title-icon {
  font-size: 24px;
  color: #409eff;
  margin-right: 12px;
}

.interface-path {
  display: flex;
  align-items: center;
  gap: 12px;
}

.path-text {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 14px;
  background: #f5f7fa;
  padding: 8px 12px;
  border-radius: 4px;
  color: #e6a23c;
  border: 1px solid #ebeef5;
}

.header-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.time-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
  font-size: 13px;
  color: #6b7280;
}

.time-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.time-item .el-icon {
  font-size: 14px;
}

/* 详情网格布局 */
.interface-details-grid {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.detail-card {
  background: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  border: 1px solid #e5e7eb;
}

.detail-card:hover {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}

.detail-card.full-width {
  grid-column: 1 / -1;
}

/* 详情卡片头部 */
.detail-header {
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  padding: 16px 20px;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
  gap: 12px;
}

.detail-icon {
  font-size: 18px;
  color: #409eff;
}

.detail-header h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #374151;
}

/* 详情卡片内容 */
.detail-content {
  padding: 20px;
}

.info-item {
  display: flex;
  margin-bottom: 12px;
  align-items: flex-start;
}

.info-item label {
  font-weight: 600;
  color: #374151;
  min-width: 80px;
  margin-right: 12px;
}

.info-item span {
  color: #6b7280;
  line-height: 1.5;
  word-break: break-word;
}

/* 参数列表 */
.parameter-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.parameter-item {
  display: grid;
  grid-template-columns: 1fr 100px 80px 2fr;
  gap: 12px;
  padding: 12px;
  background: #f8fafc;
  border-radius: 6px;
  border-left: 3px solid #409eff;
}

.param-name {
  font-weight: 600;
  color: #374151;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}

.param-type {
  color: #e6a23c;
  font-size: 13px;
  font-weight: 500;
}

.param-required {
  color: #f56c6c;
  font-size: 13px;
  font-weight: 500;
}

.param-description {
  color: #6b7280;
  font-size: 14px;
}

/* 空内容状态 */
.empty-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #909399;
  font-style: italic;
  padding: 40px 20px;
}

.empty-content .el-icon {
  font-size: 18px;
}

/* JSON内容样式 */
.json-content,
.request-body-content {
  background: #1f2937;
  border-radius: 8px;
  overflow: hidden;
}

.json-text {
  color: #e5e7eb;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
  line-height: 1.5;
  margin: 0;
  padding: 16px;
  background: transparent;
  overflow-x: auto;
}

/* 响应内容 */
.responses-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.response-item {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
}

.response-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: #f8fafc;
  border-bottom: 1px solid #e5e7eb;
}

.response-description {
  color: #6b7280;
  font-size: 14px;
}

.response-content {
  background: #1f2937;
}


/* 选项卡头部样式优化 */
:deep(.el-tabs__header) {
  margin: 0;
  background: #ffffff;
  border-radius: 8px 8px 0 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border-bottom: 1px solid #e4e7ed;
}


:deep(.el-tabs__nav) {
  border: none;
}

:deep(.el-tabs__item) {
  height: 30px;
  line-height: 30px;
  border-radius: 6px 6px 0 0;
  padding:10px;
  width: 100px;
  font-size: 14px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  cursor: pointer;
}

:deep(.el-tabs__item:hover) {
  color: var(--el-color-primary);

}

:deep(.el-tabs__item.is-active) {

  font-weight: 600;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.25);
}

:deep(.el-tabs__item.is-active::before) {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;

}

:deep(.el-tabs__item.is-active::after) {
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%;
  width: 32px;
  height: 3px;
  box-shadow: 0 2px 3px rgba(64, 158, 255, 0.4);
}

:deep(.el-tabs__active-bar) {
  display: none;
}

:deep(.el-tabs__content) {
  padding: 20px;
  background: #ffffff;
  border-radius: 0 0 8px 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border: 1px solid #e4e7ed;
  border-top: none;
  min-height: 200px;
}

:deep(.el-tab-pane) {
  animation: fadeInUp 0.3s ease-out;
}



/* 对话框底部 */
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  background: #f8fafc;
  border-top: 1px solid #e5e7eb;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .interface-header-card {
    flex-direction: column;
    gap: 20px;
  }
  
  .header-right {
    align-items: flex-start;
    width: 100%;
  }
}

@media (max-width: 768px) {
  .interface-detail-content {
    padding: 16px;
  }
  
  .interface-header-card {
    padding: 20px;
  }
  
  .detail-content {
    padding: 16px;
  }
  
  .parameter-item {
    grid-template-columns: 1fr;
    gap: 8px;
  }
  
  .interface-detail-modal :deep(.el-dialog) {
    margin: 10px;
    width: calc(100vw - 20px) !important;
  }
}

/* 依赖组信息样式 */
.dependency-groups-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.dependency-group-item {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
  background: white;
}

.group-header {
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  padding: 16px 20px;
  border-bottom: 1px solid #e5e7eb;
}

.group-title {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.group-icon {
  font-size: 16px;
  color: #409eff;
}

.group-name {
  font-size: 16px;
  font-weight: 600;
  color: #374151;
}

.group-description {
  color: #6b7280;
  font-size: 14px;
  line-height: 1.5;
}

.dependencies-list {
  background: #fafbfc;
}

.dependencies-header {
  display: grid;
  grid-template-columns: 2fr 1fr 1.5fr 2fr 1.5fr 1fr;
  gap: 12px;
  padding: 12px 20px;
  background: #f1f5f9;
  border-bottom: 1px solid #e5e7eb;
  font-weight: 600;
  font-size: 13px;
  color: #374151;
}

.dependency-item {
  display: grid;
  grid-template-columns: 2fr 1fr 1.5fr 2fr 1.5fr 1fr;
  gap: 12px;
  padding: 16px 20px;
  border-bottom: 1px solid #f1f5f9;
  align-items: start;
}

.dependency-item:last-child {
  border-bottom: none;
}

.dependency-item:hover {
  background: #f8fafc;
}

.dep-col-name .dependency-name {
  font-weight: 500;
  color: #374151;
  display: block;
  margin-bottom: 4px;
}

.dep-col-name .dependency-desc {
  font-size: 12px;
  color: #6b7280;
  line-height: 1.4;
}

.source-interface {
  color: #059669;
  font-size: 13px;
}

.no-source,
.no-field {
  color: #9ca3af;
  font-style: italic;
}

.field-path,
.target-field {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 12px;
  background: #f3f4f6;
  padding: 2px 6px;
  border-radius: 4px;
  color: #374151;
  border: 1px solid #e5e7eb;
}

.empty-dependencies {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #9ca3af;
  font-style: italic;
  padding: 30px 20px;
  background: #fafbfc;
}

.empty-dependencies .el-icon {
  font-size: 16px;
}

/* 依赖组响应式设计 */
@media (max-width: 1200px) {
  .dependencies-header,
  .dependency-item {
    grid-template-columns: 1fr;
    gap: 8px;
  }
  
  .dependencies-header {
    display: none;
  }
  
  .dependency-item {
    display: flex;
    flex-direction: column;
    padding: 16px;
  }
  
  .dep-col-name,
  .dep-col-type,
  .dep-col-source,
  .dep-col-field,
  .dep-col-target,
  .dep-col-status {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  
  .dep-col-name::before { content: "名称: "; font-weight: 600; }
  .dep-col-type::before { content: "类型: "; font-weight: 600; }
  .dep-col-source::before { content: "源接口: "; font-weight: 600; }
  .dep-col-field::before { content: "源字段: "; font-weight: 600; }
  .dep-col-target::before { content: "目标字段: "; font-weight: 600; }
  .dep-col-status::before { content: "状态: "; font-weight: 600; }
}
</style>