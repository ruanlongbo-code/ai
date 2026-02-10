<template>
  <div class="response-form-editor">
    <div class="editor-header">
      <div class="header-left">
        <span class="response-count">{{ responses.length }} 个响应</span>
        <div class="edit-mode-switch">
          <el-radio-group v-model="editMode" size="small" :disabled="readonly">
            <el-radio-button value="form">表单编辑</el-radio-button>
            <el-radio-button value="json">JSON编辑</el-radio-button>
          </el-radio-group>
        </div>
      </div>
      <div class="header-right">
        <el-button v-if="editMode === 'form' && !readonly" size="small" @click="addResponse">
          <el-icon><Plus /></el-icon>
          添加响应
        </el-button>
        <el-button v-if="editMode === 'form' && !readonly" size="small" @click="addCommonResponses">
          <el-icon><Star /></el-icon>
          添加常用响应
        </el-button>
        <el-button v-if="editMode === 'json'" size="small" @click="formatJson">
          <el-icon><Document /></el-icon>
          格式化
        </el-button>
        <el-button v-if="editMode === 'json'" size="small" @click="copyJson">
          <el-icon><DocumentCopy /></el-icon>
          复制
        </el-button>
      </div>
    </div>

    <!-- 表单编辑模式 -->
    <div v-show="editMode === 'form'" class="form-edit-mode">
      <div v-if="responses.length > 0" class="responses-list">
        <el-collapse v-model="activeCollapseItems" class="response-collapse">
          <el-collapse-item 
            v-for="(response, index) in responses" 
            :key="response.id || index"
            :name="index.toString()"
            class="response-collapse-item"
          >
            <template #title>
              <div class="collapse-title">
                <span class="status-code-badge" :class="getStatusCodeClass(response.http_code)">
                  {{ response.http_code || '200' }}
                </span>
                <span class="media-type">{{ response.media_type || 'application/json' }}</span>
                <span class="description">{{ response.description || '响应描述' }}</span>
                <el-button 
                  v-if="!readonly"
                  size="small" 
                  text 
                  type="primary"
                  @click.stop="copyResponse(index)"
                  class="copy-btn"
                  title="复制响应"
                >
                  <el-icon><DocumentCopy /></el-icon>
                </el-button>
                <el-button 
                  v-if="!readonly"
                  size="small" 
                  text 
                  type="danger"
                  @click.stop="removeResponse(index)"
                  class="delete-btn"
                  title="删除响应"
                >
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </template>
          <div class="response-content">
            <!-- 左侧基本信息区域 40% -->
            <div class="response-left">
              <div class="response-basic-info">
                <div class="response-info-title">响应说明</div>
                
                <div class="response-form-content">
                  <el-form-item label="状态码" :label-width="80">
                    <el-input 
                      v-model="response.http_code" 
                      placeholder="200"
                      size="small"
                      :readonly="readonly"
                      @input="updateResponse(index)"
                    />
                  </el-form-item>
                  
                  <el-form-item label="媒体类型" :label-width="80">
                    <el-select 
                      v-model="response.media_type" 
                      placeholder="application/json"
                      size="small"
                      :disabled="readonly"
                      @change="updateResponse(index)"
                      style="width: 100%"
                    >
                      <el-option label="application/json" value="application/json" />
                      <el-option label="application/xml" value="application/xml" />
                      <el-option label="text/plain" value="text/plain" />
                      <el-option label="text/html" value="text/html" />
                    </el-select>
                  </el-form-item>
                  
                  <el-form-item label="描述" :label-width="80">
                    <el-input 
                      v-model="response.description" 
                      placeholder="响应描述"
                      size="small"
                      :readonly="readonly"
                      type="textarea"
                      :rows="3"
                      @input="updateResponse(index)"
                    />
                  </el-form-item>
                </div>
              </div>
            </div>
            
            <!-- 右侧响应体示例区域 60% -->
            <div class="response-right">
              <div class="response-body-editor">
                <div class="editor-label">响应体示例：</div>
                <json-editor
                  v-model="response.response_body"
                  height="300px"
                  :readonly="readonly"
                  @update:modelValue="handleResponseBodyChange(response, index, $event)"
                />
              </div>
            </div>
          </div>
        </el-collapse-item>
      </el-collapse>
      </div>
      
      <el-empty v-else description="暂无响应配置" />
    </div>

    <!-- JSON编辑模式 -->
    <div v-show="editMode === 'json'" class="json-edit-mode">
      <div class="json-editor-container">
        <json-editor
          v-model="jsonEditorData"
          height="400px"
          :readonly="readonly"
          ref="jsonEditorRef"
        />
      </div>
    </div>

    <!-- 常用响应选择对话框 -->
    <el-dialog
      v-model="commonResponsesDialogVisible"
      title="选择常用响应"
      width="60%"
    >
      <div class="common-responses-grid">
        <div 
          v-for="commonResponse in commonResponses" 
          :key="commonResponse.http_code"
          class="common-response-card"
          @click="selectCommonResponse(commonResponse)"
        >
          <div class="card-header">
            <span class="status-code">{{ commonResponse.http_code }}</span>
            <span class="status-text">{{ commonResponse.description }}</span>
          </div>
          <div class="card-body">
            <pre class="response-preview">{{ formatPreview(commonResponse.response_body) }}</pre>
          </div>
        </div>
      </div>
      
      <template #footer>
        <el-button @click="commonResponsesDialogVisible = false">取消</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { Plus, Delete, Star, Document, DocumentCopy } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import JsonEditor from '@/components/JsonEditor.vue'

const props = defineProps({
  modelValue: {
    type: Array,
    default: () => []
  },
  readonly: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue'])

// 编辑模式
const editMode = ref('form')

// 响应数据
const responses = ref([])
const commonResponsesDialogVisible = ref(false)

// 折叠面板相关
const activeCollapseItems = ref([])

// JSON编辑器相关
const jsonData = ref([])
const jsonEditorRef = ref(null)

// 标记是否正在初始化，避免递归更新
const isInitializing = ref(false)

// 生成唯一ID
const generateId = () => {
  return Date.now().toString(36) + Math.random().toString(36).substr(2)
}

// 常用响应模板
const commonResponses = [
  {
    http_code: 200,
    description: '成功',
    media_type: 'application/json',
    response_body: {
      code: 200,
      message: 'success',
      data: {}
    }
  },
  {
    http_code: 201,
    description: '创建成功',
    media_type: 'application/json',
    response_body: {
      code: 201,
      message: 'created successfully',
      data: {}
    }
  },
  {
    http_code: 400,
    description: '请求参数错误',
    media_type: 'application/json',
    response_body: {
      code: 400,
      message: 'bad request',
      error: 'invalid parameters'
    }
  },
  {
    http_code: 401,
    description: '未授权',
    media_type: 'application/json',
    response_body: {
      code: 401,
      message: 'unauthorized',
      error: 'authentication required'
    }
  },
  {
    http_code: 403,
    description: '禁止访问',
    media_type: 'application/json',
    response_body: {
      code: 403,
      message: 'forbidden',
      error: 'access denied'
    }
  },
  {
    http_code: 404,
    description: '资源不存在',
    media_type: 'application/json',
    response_body: {
      code: 404,
      message: 'not found',
      error: 'resource not found'
    }
  },
  {
    http_code: 500,
    description: '服务器内部错误',
    media_type: 'application/json',
    response_body: {
      code: 500,
      message: 'internal server error',
      error: 'server error occurred'
    }
  }
]

// 创建新响应
const createNewResponse = () => {
  return {
    id: generateId(),
    http_code: 200,
    description: '成功响应',
    media_type: 'application/json',
    schema: {},
    response_body: JSON.stringify({
      code: 200,
      message: 'success',
      data: {}
    }, null, 2)
  }
}

// 添加响应
const addResponse = () => {
  responses.value.push(createNewResponse())
  emit('update:modelValue', responses.value)
}

// 删除响应
const removeResponse = (index) => {
  responses.value.splice(index, 1)
  emit('update:modelValue', responses.value)
}

// 复制响应
const copyResponse = (index) => {
  const originalResponse = responses.value[index]
  const copiedResponse = {
    id: generateId(),
    http_code: originalResponse.http_code,
    description: originalResponse.description + ' (副本)',
    media_type: originalResponse.media_type,
    schema: JSON.parse(JSON.stringify(originalResponse.schema || {})),
    response_body: originalResponse.response_body
  }
  
  // 在原响应后面插入复制的响应
  responses.value.splice(index + 1, 0, copiedResponse)
  emit('update:modelValue', responses.value)
  
  // 展开新复制的响应项
  nextTick(() => {
    const newIndex = (index + 1).toString()
    if (!activeCollapseItems.value.includes(newIndex)) {
      activeCollapseItems.value.push(newIndex)
    }
  })
}

// 更新响应
const updateResponse = (index) => {
  emit('update:modelValue', responses.value)
}

// 处理响应体变化
const handleResponseBodyChange = (response, index, newValue) => {
  response.response_body = newValue
  updateResponse(index)
}

// 添加常用响应
const addCommonResponses = () => {
  commonResponsesDialogVisible.value = true
}

// 选择常用响应
const selectCommonResponse = (commonResponse) => {
  const newResponse = {
    id: generateId(),
    http_code: commonResponse.http_code,
    description: commonResponse.description,
    media_type: commonResponse.media_type,
    schema: {},
    response_body: JSON.stringify(commonResponse.response_body, null, 2)
  }
  
  responses.value.push(newResponse)
  emit('update:modelValue', responses.value)
  commonResponsesDialogVisible.value = false
}

// 格式化预览
const formatPreview = (body) => {
  try {
    if (typeof body === 'string') {
      return JSON.stringify(JSON.parse(body), null, 2)
    }
    return JSON.stringify(body, null, 2)
  } catch (error) {
    return typeof body === 'string' ? body : JSON.stringify(body)
  }
}

// 初始化响应
const initResponses = () => {
  if (props.modelValue && Array.isArray(props.modelValue)) {
    responses.value = props.modelValue.map(response => ({
      id: generateId(),
      http_code: response.http_code || 200,
      description: response.description || '',
      media_type: response.media_type || 'application/json',
      schema: response.schema || {},
      response_body: response.response_body || '{}'
    }));
  } else {
    responses.value = []
  }
}

// JSON编辑模式相关方法
const responsesToJson = (responseList) => {
  try {
    const jsonObj = {}
    responseList.forEach(response => {
      const statusCode = response.http_code || '200'
      jsonObj[statusCode] = {
        description: response.schema?.description || '',
        content: {
          [response.media_type || 'application/json']: {
            schema: response.schema || {},
            example: response.response_body ? JSON.parse(response.response_body) : {}
          }
        }
      }
    })
    return JSON.stringify(jsonObj, null, 2)
  } catch (error) {
    console.error('转换为JSON失败:', error)
    return '{}'
  }
}

const jsonToResponses = (jsonStr) => {
  try {
    const jsonObj = JSON.parse(jsonStr)
    const responseList = []
    
    Object.keys(jsonObj).forEach(statusCode => {
      const responseData = jsonObj[statusCode]
      const content = responseData.content || {}
      const mediaType = Object.keys(content)[0] || 'application/json'
      const contentData = content[mediaType] || {}
      
      responseList.push({
        id: generateId(),
        http_code: statusCode,
        media_type: mediaType,
        schema: {
          description: responseData.description || '',
          ...contentData.schema
        },
        response_body: JSON.stringify(contentData.example || {}, null, 2)
      })
    })
    
    return responseList
  } catch (error) {
    console.error('解析JSON失败:', error)
    ElMessage.error('JSON格式错误，请检查语法')
    return responses.value
  }
}

// 更新JSON数据
const updateJsonData = () => {
  jsonData.value = responses.value
}

// 格式化JSON
const formatJson = () => {
  if (jsonEditorRef.value) {
    jsonEditorRef.value.formatJson()
  }
}

// 复制JSON
const copyJson = async () => {
  if (jsonEditorRef.value) {
    const success = await jsonEditorRef.value.copyJson()
    if (success) {
      ElMessage.success('已复制到剪贴板')
    } else {
      ElMessage.error('复制失败')
    }
  }
}

// 计算属性：JSON编辑器的数据
const jsonEditorData = computed({
  get() {
    if (editMode.value === 'json') {
      updateJsonData()
    }
    return jsonData.value
  },
  set(value) {
    jsonData.value = value
    if (editMode.value === 'json' && Array.isArray(value)) {
      responses.value = value
      emit('update:modelValue', responses.value)
    }
  }
})

// 监听响应变化（表单模式）
watch(responses, () => {
  if (!isInitializing.value) {
    if (editMode.value === 'form') {
      emit('update:modelValue', responses.value)
    }
    if (editMode.value === 'json') {
      updateJsonData()
    }
  }
}, { deep: true })

// 监听JSON数据变化（JSON模式）
watch(jsonData, (newJsonData) => {
  if (!isInitializing.value && editMode.value === 'json') {
    if (Array.isArray(newJsonData)) {
      responses.value = newJsonData
      emit('update:modelValue', responses.value)
    }
  }
}, { deep: true })

// 获取状态码样式类
const getStatusCodeClass = (statusCode) => {
  const code = parseInt(statusCode)
  if (code >= 200 && code < 300) return 'status-success'
  if (code >= 300 && code < 400) return 'status-redirect'
  if (code >= 400 && code < 500) return 'status-client-error'
  if (code >= 500) return 'status-server-error'
  return 'status-default'
}

// 初始化折叠面板
const initCollapseItems = () => {
  // 默认展开第一个响应项
  if (responses.value.length > 0) {
    activeCollapseItems.value = ['0']
  }
}

// 监听props变化
watch(() => props.modelValue, () => {
  isInitializing.value = true
  initResponses()
  initCollapseItems()
  if (editMode.value === 'json') {
    updateJsonData()
  }
  nextTick(() => {
    isInitializing.value = false
  })
}, { immediate: true, deep: true })

// 监听响应数组变化，更新折叠面板
watch(responses, () => {
  initCollapseItems()
}, { deep: true })

// 初始化
initResponses()
initCollapseItems()
</script>

<style scoped>
.response-form-editor {
  width: 100%;
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e4e7ed;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.edit-mode-switch {
  margin-left: 16px;
}

.response-count {
  font-size: 14px;
  color: #606266;
}

.header-right {
  display: flex;
  gap: 8px;
}

.responses-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 折叠面板样式 */
.response-collapse {
  border: none;
  --el-collapse-border-color: transparent;
}

.response-collapse-item {
  margin-bottom: 16px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.response-collapse-item:last-child {
  margin-bottom: 0;
}

/* 重写Element Plus折叠面板的默认样式 */
.response-collapse-item :deep(.el-collapse-item__header) {
  background-color: #f8f9fa;
  border: none;
  padding: 12px 16px;
  font-weight: 500;
  border-radius: 0;
}

.response-collapse-item :deep(.el-collapse-item__content) {
  padding: 0;
  border: none;
}

.response-collapse-item :deep(.el-collapse-item__wrap) {
  border: none;
}

.response-collapse-item :deep(.el-collapse-item__arrow) {
  margin-right: 8px;
}

/* 折叠面板标题样式 */
.collapse-title {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 0;
}

/* 状态码徽章样式 */
.status-code-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 50px;
  height: 24px;
  padding: 0 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  color: #fff;
}

.status-success {
  background: #67c23a;
}

.status-redirect {
  background: #e6a23c;
}

.status-client-error {
  background: #f56c6c;
}

.status-server-error {
  background: #909399;
}

.status-default {
  background: #409eff;
}

/* 媒体类型样式 */
.media-type {
  font-size: 13px;
  color: #606266;
  background: #f5f7fa;
  padding: 2px 8px;
  border-radius: 4px;
}

/* 描述样式 */
.description {
  flex: 1;
  font-size: 14px;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 操作按钮样式 */
.copy-btn,
.delete-btn {
  margin-left: 8px;
  opacity: 0.7;
  transition: opacity 0.2s;
  padding: 4px;
  min-width: auto;
  height: auto;
  background: none !important;
}

.copy-btn {
  margin-left: auto;
}

.copy-btn:hover {
  opacity: 1;
  color: #409eff !important;
}

.delete-btn:hover {
  opacity: 1;
  background-color: rgba(245, 108, 108, 0.1);
}

.response-item {
  border: none;
  border-radius: 0;
  padding: 20px;
  background: #fff;
  margin: 0;
}

/* 响应内容区域样式优化 */
.response-content {
  display: flex;
  gap: 20px;
  min-height: 400px;
}

.response-left {
  flex: 0 0 40%;
}

.response-right {
  flex: 1;
}

.response-content {
  display: flex;
  gap: 16px;
  align-items: flex-start;
}

.response-left {
  flex: 0 0 40%;
  min-width: 300px;
}

.response-right {
  flex: 1;
  min-width: 0;
}

.response-basic-info {
  display: flex;
  flex-direction: column;
  background: #f8f9fa;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  height: 400px;
}

.response-form-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow-y: auto;
}

.response-info-title {
  font-size: 14px;
  color: #303133;
  font-weight: 600;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 2px solid #409eff;
  display: flex;
  align-items: center;
  gap: 8px;
}

.response-info-title::before {
  content: '';
  width: 3px;
  height: 16px;
  background: #409eff;
  border-radius: 2px;
}

.response-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #ebeef5;
}

.response-basic-info .el-form-item {
  margin-bottom: 0;
}

.response-basic-info .el-form-item__label {
  font-weight: 600;
  color: #303133;
  font-size: 13px;
}

.response-basic-info .el-input__inner,
.response-basic-info .el-textarea__inner {
  border-radius: 6px;
  border-color: #dcdfe6;
  transition: all 0.2s ease;
}

.response-basic-info .el-input__inner:focus,
.response-basic-info .el-textarea__inner:focus {
  border-color: #409eff;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.1);
}

.response-basic-info .el-select {
  border-radius: 6px;
}

.response-basic-info .el-select__wrapper {
  border-radius: 6px;
  border-color: #dcdfe6;
  transition: all 0.2s ease;
}

.response-basic-info .el-select__wrapper:hover {
  border-color: #c0c4cc;
}

.response-basic-info .el-select__wrapper.is-focused {
  border-color: #409eff;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.1);
}

.response-actions .el-button {
  border-radius: 6px;
  font-weight: 500;
  padding: 8px 16px;
  transition: all 0.2s ease;
}

.response-actions .el-button--danger.is-text {
  color: #f56c6c;
  background: rgba(245, 108, 108, 0.1);
  border: 1px solid rgba(245, 108, 108, 0.2);
}

.response-actions .el-button--danger.is-text:hover {
  background: rgba(245, 108, 108, 0.15);
  border-color: rgba(245, 108, 108, 0.3);
  transform: translateY(-1px);
}

.response-body-editor {
  width: 100%;
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  height: 400px;
  display: flex;
  flex-direction: column;
}

.response-body-editor .json-editor {
  flex: 1;
  min-height: 0;
}

.editor-label {
  font-size: 14px;
  color: #303133;
  margin-bottom: 12px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}

.editor-label::before {
  content: '';
  width: 3px;
  height: 16px;
  background: #409eff;
  border-radius: 2px;
}

/* 常用响应对话框样式 */
.common-responses-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
  max-height: 400px;
  overflow-y: auto;
}

.common-response-card {
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  padding: 12px;
  cursor: pointer;
  transition: all 0.3s;
}

.common-response-card:hover {
  border-color: #409eff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.2);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.status-code {
  font-weight: bold;
  color: #409eff;
}

.status-text {
  font-size: 14px;
  color: #606266;
}

.card-body {
  background: #f5f7fa;
  border-radius: 4px;
  padding: 8px;
}

.response-preview {
  font-size: 12px;
  color: #606266;
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
}

/* JSON编辑模式样式 */
.json-edit-mode {
  margin-top: 16px;
}

.json-editor-container {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  overflow: hidden;
}

.monaco-loading {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 400px;
  background: #f5f7fa;
  color: #909399;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .common-responses-grid {
    grid-template-columns: 1fr;
  }
  
  .response-content {
    flex-direction: column;
    gap: 16px;
  }
  
  .response-left {
    flex: none;
    min-width: auto;
    width: 100%;
  }
  
  .response-right {
    flex: none;
    width: 100%;
  }
}

@media (max-width: 1024px) {
  .response-left {
    flex: 0 0 45%;
    min-width: 280px;
  }
}
</style>