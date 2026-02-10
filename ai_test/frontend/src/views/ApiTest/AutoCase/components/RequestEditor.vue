<template>
  <div class="request-editor">
    <el-card class="editor-card" shadow="hover">
    

      <el-tabs v-model="activeTab" type="card" class="config-tabs">
        <!-- 基本信息 -->
        <el-tab-pane name="basic">
          <template #label>
            <div class="tab-label">
              <el-icon><Link /></el-icon>
              <span>基本信息</span>
            </div>
          </template>
          <div class="config-section">
            <div class="section-header">
              <h4>请求基础配置</h4>
              <p>配置请求的基本信息，包括方法、URL等</p>
            </div>
            <div class="form-container">
              <el-form :model="localRequest" label-width="120px" label-position="left">
                <el-form-item label="请求方法">
                  <el-select 
                    v-model="localRequest.method" 
                    placeholder="选择请求方法"
                    style="width: 100%"
                  >
                    <el-option label="GET" value="GET" />
                    <el-option label="POST" value="POST" />
                    <el-option label="PUT" value="PUT" />
                    <el-option label="DELETE" value="DELETE" />
                    <el-option label="PATCH" value="PATCH" />
                    <el-option label="HEAD" value="HEAD" />
                    <el-option label="OPTIONS" value="OPTIONS" />
                  </el-select>
                </el-form-item>
                
                <el-form-item label="请求URL">
                  <el-input 
                    v-model="localRequest.url" 
                    placeholder="请输入请求URL路径，如：/api/users"
                    clearable
                  />
                </el-form-item>
                
                <el-form-item label="基础URL">
                  <el-input 
                    v-model="localRequest.base_url" 
                    placeholder="请输入基础URL，如：https://api.example.com"
                    clearable
                  />
                </el-form-item>
              </el-form>
            </div>
          </div>
        </el-tab-pane>

        <!-- 请求参数 -->
        <el-tab-pane name="params">
          <template #label>
            <div class="tab-label">
              <el-icon><List /></el-icon>
              <span>请求参数</span>
            </div>
          </template>
          <div class="config-section">
            <div class="section-header">
              <h4>URL 查询参数</h4>
              <p>配置请求URL中的查询参数，如 ?key=value</p>
            </div>
            <div class="json-field">
              <div class="field-header">
                <label class="field-label">
                  <el-icon><Search /></el-icon>
                  查询参数 JSON
                </label>
                <el-button size="small" @click="formatParams">
                  <el-icon><Document /></el-icon>
                  格式化
                </el-button>
              </div>
              <json-editor
                v-model="paramsJson"
                height="300px"
                :readonly="false"
                @change="handleParamsChange"
                placeholder='{"key": "value", "page": 1, "size": 10}'
              />
            </div>
          </div>
        </el-tab-pane>

        <!-- 请求头 -->
        <el-tab-pane name="headers">
          <template #label>
            <div class="tab-label">
              <el-icon><Postcard /></el-icon>
              <span>请求头</span>
            </div>
          </template>
          <div class="config-section">
            <div class="section-header">
              <h4>HTTP 请求头</h4>
              <p>配置HTTP请求头信息，如Content-Type、Authorization等</p>
            </div>
            <div class="json-field">
              <div class="field-header">
                <label class="field-label">
                  <el-icon><Memo /></el-icon>
                  请求头 JSON
                </label>
                <el-button size="small" @click="formatHeaders">
                  <el-icon><Document /></el-icon>
                  格式化
                </el-button>
              </div>
              <json-editor
                v-model="headersJson"
                height="300px"
                :readonly="false"
                @change="handleHeadersChange"
                placeholder='{"Content-Type": "application/json", "Authorization": "Bearer token"}'
              />
            </div>
          </div>
        </el-tab-pane>

        <!-- 请求体 -->
        <el-tab-pane name="body">
          <template #label>
            <div class="tab-label">
              <el-icon><DocumentCopy /></el-icon>
              <span>请求体</span>
            </div>
          </template>
          <div class="config-section">
            <div class="section-header">
              <h4>请求体数据</h4>
              <p>配置POST、PUT等请求的请求体数据</p>
            </div>
            <div class="json-field">
              <div class="field-header">
                <label class="field-label">
                  <el-icon><Edit /></el-icon>
                  请求体 JSON
                </label>
                <el-button size="small" @click="formatBody">
                  <el-icon><Document /></el-icon>
                  格式化
                </el-button>
              </div>
              <json-editor
                v-model="bodyJson"
                height="400px"
                :readonly="false"
                @change="handleBodyChange"
                placeholder='{"name": "example", "age": 25, "active": true}'
              />
            </div>
          </div>
        </el-tab-pane>

        <!-- 文件上传 -->
        <el-tab-pane name="files">
          <template #label>
            <div class="tab-label">
              <el-icon><Upload /></el-icon>
              <span>文件上传</span>
            </div>
          </template>
          <div class="config-section">
            <div class="section-header">
              <h4>文件上传配置</h4>
              <p>配置multipart/form-data请求中的文件上传信息</p>
            </div>
            <div class="json-field">
              <div class="field-header">
                <label class="field-label">
                  <el-icon><FolderOpened /></el-icon>
                  文件配置 JSON
                </label>
                <el-button size="small" @click="formatFiles">
                  <el-icon><Document /></el-icon>
                  格式化
                </el-button>
              </div>
              <json-editor
                v-model="filesJson"
                height="300px"
                :readonly="false"
                @change="handleFilesChange"
                placeholder='{"file1": ["filename.jpg", "files/path.jpg", "image/jpeg"]}'
              />
            </div>
          </div>
        </el-tab-pane>

        <!-- 前置脚本 -->
        <el-tab-pane v-if="showScripts" name="setup">
          <template #label>
            <div class="tab-label">
              <el-icon><VideoPlay /></el-icon>
              <span>前置脚本</span>
            </div>
          </template>
          <div class="config-section">
            <div class="section-header">
              <h4>前置脚本 (Python)</h4>
              <p>在请求发送前执行的Python脚本</p>
            </div>
            <div class="json-field">
              <div class="field-header">
                <label class="field-label">
                  <el-icon><Edit /></el-icon>
                  前置脚本内容
                </label>
                <div class="script-actions">
                  <el-button size="small" @click="formatScript('setup')">
                    <el-icon><Document /></el-icon>
                    格式化
                  </el-button>
                  <el-button size="small" @click="clearScript('setup')">
                    <el-icon><Delete /></el-icon>
                    清空
                  </el-button>
                </div>
              </div>
              <code-editor
                v-model="localRequest.setup_script"
                language="python"
                height="300px"
                :readonly="false"
                placeholder="# 前置脚本，在请求发送前执行&#10;# 可以设置变量、处理数据等&#10;print('前置脚本执行')"
              />
            </div>
          </div>
        </el-tab-pane>

        <!-- 后置脚本 -->
        <el-tab-pane v-if="showScripts" name="teardown">
          <template #label>
            <div class="tab-label">
              <el-icon><VideoPause /></el-icon>
              <span>后置脚本</span>
            </div>
          </template>
          <div class="config-section">
            <div class="section-header">
              <h4>后置脚本 (Python)</h4>
              <p>在请求完成后执行的Python脚本</p>
            </div>
            <div class="json-field">
              <div class="field-header">
                <label class="field-label">
                  <el-icon><Edit /></el-icon>
                  后置脚本内容
                </label>
                <div class="script-actions">
                  <el-button size="small" @click="formatScript('teardown')">
                    <el-icon><Document /></el-icon>
                    格式化
                  </el-button>
                  <el-button size="small" @click="clearScript('teardown')">
                    <el-icon><Delete /></el-icon>
                    清空
                  </el-button>
                </div>
              </div>
              <code-editor
                v-model="localRequest.teardown_script"
                language="python"
                height="300px"
                :readonly="false"
                placeholder="# 后置脚本，在请求完成后执行&#10;# 可以处理响应数据、断言等&#10;print('后置脚本执行')"
              />
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  Plus, Delete, Document, Setting, RefreshRight, Link, Operation, 
  List, Search, Postcard, Memo, DocumentCopy, Edit, Upload, 
  FolderOpened, VideoPlay, VideoPause
} from '@element-plus/icons-vue'
import JsonEditor from '@/components/JsonEditor.vue'
import CodeEditor from '@/components/CodeEditor.vue'

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({
      url: '',
      method: 'GET',
      params: {},
      headers: {},
      body: {},
      files: {},
      base_url: '${{base_url}}',
      interface_id: '',
      setup_script: '',
      teardown_script: ''
    })
  },
  showScripts: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue'])

// 响应式数据
const activeTab = ref('basic')

// 本地请求数据
const localRequest = reactive({
  url: '',
  method: 'GET',
  params: {},
  headers: {},
  body: {},
  files: {},
  base_url: '${{base_url}}',
  interface_id: '',
  setup_script: '',
  teardown_script: ''
})

// JSON编辑器数据

const paramsJson = computed({
  get() {
    return JSON.stringify(localRequest.params, null, 2)
  },
  set(value) {
    try {
      localRequest.params = JSON.parse(value)
    } catch (error) {
      console.warn('Invalid JSON for params:', error)
    }
  }
})

const headersJson = computed({
  get() {
    return JSON.stringify(localRequest.headers, null, 2)
  },
  set(value) {
    try {
      localRequest.headers = JSON.parse(value)
    } catch (error) {
      console.warn('Invalid JSON for headers:', error)
    }
  }
})

const bodyJson = computed({
  get() {
    return JSON.stringify(localRequest.body, null, 2)
  },
  set(value) {
    try {
      localRequest.body = JSON.parse(value)
    } catch (error) {
      console.warn('Invalid JSON for body:', error)
    }
  }
})

const filesJson = computed({
  get() {
    return JSON.stringify(localRequest.files, null, 2)
  },
  set(value) {
    try {
      localRequest.files = JSON.parse(value)
    } catch (error) {
      console.warn('Invalid JSON for files:', error)
    }
  }
})

// JSON编辑器变化处理

const handleParamsChange = ({ json, isValid }) => {
  if (isValid && json) {
    localRequest.params = json
  }
}

const handleHeadersChange = ({ json, isValid }) => {
  if (isValid && json) {
    localRequest.headers = json
  }
}

const handleBodyChange = ({ json, isValid }) => {
  if (isValid && json) {
    localRequest.body = json
  }
}

const handleFilesChange = ({ json, isValid }) => {
  if (isValid && json) {
    localRequest.files = json
  }
}

// 格式化功能

const formatParams = () => {
  try {
    const params = JSON.parse(paramsJson.value)
    paramsJson.value = JSON.stringify(params, null, 2)
    ElMessage.success('请求参数格式化完成')
  } catch (error) {
    ElMessage.error('请求参数JSON格式错误')
  }
}

const formatHeaders = () => {
  try {
    const headers = JSON.parse(headersJson.value)
    headersJson.value = JSON.stringify(headers, null, 2)
    ElMessage.success('请求头格式化完成')
  } catch (error) {
    ElMessage.error('请求头JSON格式错误')
  }
}

const formatBody = () => {
  try {
    const body = JSON.parse(bodyJson.value)
    bodyJson.value = JSON.stringify(body, null, 2)
    ElMessage.success('请求体格式化完成')
  } catch (error) {
    ElMessage.error('请求体JSON格式错误')
  }
}

const formatFiles = () => {
  try {
    const files = JSON.parse(filesJson.value)
    filesJson.value = JSON.stringify(files, null, 2)
    ElMessage.success('文件配置格式化完成')
  } catch (error) {
    ElMessage.error('文件配置JSON格式错误')
  }
}

const formatAllJson = () => {
  formatParams()
  formatHeaders()
  formatBody()
  formatFiles()
  ElMessage.success('所有配置格式化完成')
}

// 重置配置
const resetConfig = () => {
  localRequest.url = ''
  localRequest.method = 'GET'
  localRequest.params = {}
  localRequest.headers = {}
  localRequest.body = {}
  localRequest.files = {}
  localRequest.base_url = '${{base_url}}'
  localRequest.interface_id = ''
  localRequest.setup_script = ''
  localRequest.teardown_script = ''
  ElMessage.success('配置已重置')
}

// 格式化脚本
const formatScript = (type) => {
  // 这里可以添加Python代码格式化逻辑
  ElMessage.success('脚本格式化完成')
}

// 清空脚本
const clearScript = (type) => {
  if (type === 'setup') {
    localRequest.setup_script = ''
  } else if (type === 'teardown') {
    localRequest.teardown_script = ''
  }
}

// 防止循环更新的标志
const isUpdatingFromParent = ref(false)

// 监听props变化
watch(() => props.modelValue, (newValue) => {
  if (newValue && !isUpdatingFromParent.value) {
    isUpdatingFromParent.value = true
    
    // 直接赋值，保持对象格式
    localRequest.url = newValue.url || ''
    localRequest.method = newValue.method || 'GET'
    localRequest.params = newValue.params || {}
    localRequest.headers = newValue.headers || {}
    localRequest.body = newValue.body || {}
    localRequest.files = newValue.files || {}
    localRequest.base_url = newValue.base_url || '${{base_url}}'
    localRequest.interface_id = newValue.interface_id || ''
    localRequest.setup_script = newValue.setup_script || ''
    localRequest.teardown_script = newValue.teardown_script || ''
    
    // 重置标志
    nextTick(() => {
      isUpdatingFromParent.value = false
    })
  }
}, { immediate: true, deep: true })

// 监听本地数据变化，同步到父组件
watch(localRequest, (newValue) => {
  // 只有在不是从父组件更新时才emit
  if (!isUpdatingFromParent.value) {
    emit('update:modelValue', { ...newValue })
  }
}, { deep: true })
</script>

<style scoped>
.request-editor {
  width: 100%;
  background: #f8fafc;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.editor-card {
  border: none;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  border-radius: 12px;
  overflow: hidden;
}

:deep(.el-card__header) {
  background: linear-gradient(135deg, #9266ea 0%, #764ba2 100%);
  color: white;
  padding: 15px 10px;
  border-bottom: none;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 18px;
  font-weight: 600;
  color: white;
}

.title-icon {
  font-size: 20px;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.header-actions .el-button {
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: white;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.header-actions .el-button:hover {
  background: rgba(255, 255, 255, 0.3);
  border-color: rgba(255, 255, 255, 0.5);
  transform: translateY(-1px);
}

:deep(.el-card__body) {
  padding: 0;
  background: white;
}

.config-tabs {
  background: white;

}

:deep(.el-tabs__header) {

  margin-top:4px ;


}

:deep(.el-tabs__nav-wrap) {
  padding: 10px 0;
}

:deep(.el-tabs__item) {
  color: #64748b;
  font-weight: 500;
  font-size: 14px;
  padding: 12px 20px;
  margin-right: 8px;
  border-radius: 8px 8px 0 0;
  transition: all 0.3s ease;
  border: none;
  background: transparent;
}

:deep(.el-tabs__item:hover) {
  color: #3f2d77;
  background: rgba(59, 130, 246, 0.05);
}

:deep(.el-tabs__nav is-top){
  margin-top:0;
  padding: 0;
}
:deep(.el-tabs--card .el-tabs__nav){
  padding: 0;
}

:deep(.el-tabs__item.is-active) {
  color: #3b82f6;
  background: white;
  border-bottom: 2px solid #3b82f6;
  font-weight: 600;
}

:deep(.el-tabs__active-bar) {
  display: none;
}

:deep(.el-tabs__content) {
  padding: 1px;
  margin:0;
  background: white;
  /* 移除固定高度，让内容自适应 */
}

.tab-label {
  display: flex;
  align-items: center;
  gap: 8px;
}

.config-section {
  background: white;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  overflow: hidden;
  margin-bottom: 24px; /* 增加卡片间距 */
  transition: all 0.3s ease;
  animation: fadeInUp 0.5s ease-out;
  /* 确保卡片不会重叠 */
  position: relative;
  z-index: 1;
}

.config-section:hover {
  border-color: #3b82f6;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.1);
}

.section-header {
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  padding: 16px 20px;
  border-bottom: 1px solid #e2e8f0;
}

.section-header h4 {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
  margin: 0 0 4px 0;
}

.section-header p {
  font-size: 14px;
  color: #64748b;
  margin: 0;
}

.json-field {
  padding: 20px;
  /* 确保内容不会溢出 */
  overflow: hidden;
}

.field-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px; /* 增加标题与编辑器间距 */
}

.field-label {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
  display: flex;
  align-items: center;
  gap: 8px;
}

.field-header .el-button {
  padding: 6px 12px;
  font-size: 12px;
  border-radius: 6px;
  transition: all 0.3s ease;
}

/* JSON编辑器容器优化 */
:deep(.json-editor-wrapper) {
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #e2e8f0;
  transition: border-color 0.3s ease;
}

:deep(.json-editor-wrapper:focus-within) {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.script-actions {
  display: flex;
  gap: 8px;
}

.script-actions .el-button {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: white;
  padding: 6px 12px;
  font-size: 12px;
  border-radius: 6px;
  transition: all 0.3s ease;
}

.script-actions .el-button:hover {
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.3);
}

/* 动画效果 */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 滚动条美化 */
:deep(.el-scrollbar__wrap) {
  scrollbar-width: thin;
  scrollbar-color: #cbd5e1 #f1f5f9;
}

:deep(.el-scrollbar__wrap::-webkit-scrollbar) {
  width: 6px;
}

:deep(.el-scrollbar__wrap::-webkit-scrollbar-track) {
  background: #f1f5f9;
  border-radius: 3px;
}

:deep(.el-scrollbar__wrap::-webkit-scrollbar-thumb) {
  background: #cbd5e1;
  border-radius: 3px;
}

:deep(.el-scrollbar__wrap::-webkit-scrollbar-thumb:hover) {
  background: #94a3b8;
}

/* 表单容器样式 */
.form-container {
  padding: 20px;
  background: #fafbfc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.form-container .el-form-item {
  margin-bottom: 20px;
}

.form-container .el-form-item__label {
  color: #374151;
  font-weight: 500;
  font-size: 14px;
}

.form-container .el-input__wrapper {
  border-radius: 6px;
  border: 1px solid #d1d5db;
  transition: all 0.2s ease;
}

.form-container .el-input__wrapper:hover {
  border-color: #9ca3af;
}

.form-container .el-input__wrapper.is-focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.form-container .el-select .el-input__wrapper {
  border-radius: 6px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .card-header {
    flex-direction: column;
    gap: 12px;
    text-align: center;
  }
  
  .header-actions {
    width: 100%;
    justify-content: center;
  }
  
  :deep(.el-tabs__content) {
    padding: 16px;
  }
  
  .section-header {
    padding: 12px 16px;
  }
  
  .json-field {
    padding: 16px;
  }
  
  .form-container {
    padding: 16px;
  }
  
  .form-container .el-form-item {
    margin-bottom: 16px;
  }
  
  .field-header {
    flex-direction: column;
    gap: 8px;
    align-items: flex-start;
  }
  
  .script-actions {
    justify-content: center;
  }
}
</style>