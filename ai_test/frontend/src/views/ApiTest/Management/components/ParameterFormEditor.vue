<template>
  <div class="parameter-form-editor">
    <div class="editor-header">
      <div class="header-left">
        <span class="param-count">{{ parameters.length }} 个参数</span>
        <div class="edit-mode-switch">
          <el-radio-group v-model="editMode" size="small" :disabled="false">
            <el-radio-button value="form">表单编辑</el-radio-button>
            <el-radio-button value="json">JSON编辑</el-radio-button>
          </el-radio-group>
        </div>
      </div>
      <div class="header-right">
        <el-button v-if="editMode === 'form' && !readonly" size="small" @click="addParameter">
          <el-icon><Plus /></el-icon>
          添加参数
        </el-button>
        <el-button v-if="editMode === 'form' && parameters.length > 0 && !readonly" size="small" @click="clearAll">
          <el-icon><Delete /></el-icon>
          清空
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
      <div v-if="parameters.length > 0" class="parameters-list">
        <div 
          v-for="(param, index) in parameters"
          :key="index"
          class="parameter-item"
        >
          <div class="parameter-form">
            <el-row :gutter="12">
              <el-col :span="6">
                <el-form-item 
                  label="参数名" 
                  :label-width="60"
                >
                  <el-input 
                    v-model="param.name" 
                    placeholder="参数名"
                    size="small"
                    :readonly="readonly"
                    @blur="handleParameterUpdate"
                  />
                </el-form-item>
              </el-col>
              
              <el-col :span="4">
                <el-form-item label="类型" :label-width="40">
                  <el-select 
                    v-model="param.type" 
                    placeholder="类型"
                    size="small"
                    :disabled="readonly"
                    @change="handleTypeChange(param, index)"
                  >
                    <el-option label="string" value="string" />
                    <el-option label="integer" value="integer" />
                    <el-option label="number" value="number" />
                    <el-option label="boolean" value="boolean" />
                    <el-option label="array" value="array" />
                    <el-option label="object" value="object" />
                    <el-option label="file" value="file" />
                  </el-select>
                </el-form-item>
              </el-col>
              
              <el-col :span="2">
                <el-form-item label="必填" :label-width="40">
                  <el-switch 
                    v-model="param.required" 
                    size="small"
                    :disabled="readonly"
                    @change="handleParameterUpdate"
                  />
                </el-form-item>
              </el-col>
              
              <el-col :span="4">
                <el-form-item label="示例值" :label-width="60">
                  <el-input 
                    v-model="param.example" 
                    placeholder="示例值"
                    size="small"
                    :readonly="readonly"
                    @blur="handleParameterUpdate"
                  />
                </el-form-item>
              </el-col>
              
              <el-col :span="6">
                <el-form-item label="描述" :label-width="40">
                  <el-input 
                    v-model="param.description" 
                    placeholder="参数描述"
                    size="small"
                    :readonly="readonly"
                    @blur="handleParameterUpdate"
                  />
                </el-form-item>
              </el-col>
              
              <el-col :span="2">
                <div class="parameter-actions">
                  <el-button 
                    v-if="supportNested && param.type === 'object' && !readonly"
                    size="small" 
                    text 
                    type="primary"
                    @click="addNestedField(param)"
                    title="添加嵌套字段"
                  >
                    <el-icon><Plus /></el-icon>
                  </el-button>
                  <el-button 
                    v-if="supportNested && param.type === 'array' && !readonly"
                    size="small" 
                    text 
                    type="warning"
                    @click="addArrayItemField(param)"
                    title="添加数组项字段"
                  >
                    <el-icon><Plus /></el-icon>
                  </el-button>
                  <el-button 
                    v-if="!readonly"
                    size="small"
                    plain
                    @click="removeParameter(index)"
                    icon="Delete"
                  >

                  </el-button>
                </div>
              </el-col>
            </el-row>
            

          </div>
          
          <!-- 嵌套字段 -->
          <div v-if="param.type === 'object'" class="nested-fields">
            <div v-if="!param.nested_fields || param.nested_fields.length === 0" class="nested-fields-placeholder">
              <el-text type="info" size="small">暂无嵌套字段</el-text>
              <el-button 
                v-if="!readonly" 
                size="small" 
                plain
                @click="addNestedField(param)"
              >
                <el-icon><Plus /></el-icon>
                添加字段
              </el-button>
            </div>
            <div v-else class="nested-fields-container">
              <div class="nested-fields-header">
                <el-text type="primary" size="small">
                  <el-icon><List /></el-icon>
                  {{ param.name }} 对象字段 ({{ param.nested_fields.length }})
                </el-text>
                <el-button 
                  v-if="!readonly" 
                  size="small" 
                  plain
                  @click="addNestedField(param)"
                >
                  <el-icon><Plus /></el-icon>
                  添加字段
                </el-button>
              </div>
              <parameter-form-editor
                v-model="param.nested_fields"
                :title="`${param.name} 对象字段`"
                :support-nested="supportNested"
                :level="props.level + 1"
                :readonly="readonly"
                @update:modelValue="handleNestedFieldUpdate"
              />
            </div>
          </div>
          
          <!-- 数组项字段 -->
          <div v-if="param.type === 'array'" class="array-item-fields">
            <div v-if="!param.array_item_fields || param.array_item_fields.length === 0" class="array-fields-placeholder">
              <el-text type="info" size="small">暂无数组项字段定义</el-text>
              <el-button 
                v-if="!readonly" 
                size="small" 
                plain
                @click="addArrayItemField(param)"
              >
                <el-icon><Plus /></el-icon>
                定义数组项
              </el-button>
            </div>
            <div v-else class="array-fields-container">
              <div class="array-fields-header">
                <el-text type="warning" size="small">
                  <el-icon><List /></el-icon>
                  {{ param.name }} 数组项字段 ({{ param.array_item_fields.length }})
                </el-text>
                <el-button 
                  v-if="!readonly" 
                  size="small" 
                  plain
                  @click="addArrayItemField(param)"
                >
                  <el-icon><Plus /></el-icon>
                  添加字段
                </el-button>
              </div>
              <parameter-form-editor
                v-model="param.array_item_fields"
                :title="`${param.name} 数组项字段`"
                :support-nested="supportNested"
                :level="props.level + 1"
                :readonly="readonly"
                @update:modelValue="handleNestedFieldUpdate"
              />
            </div>
          </div>
        </div>
      </div>
      
      <el-empty v-else :description="`暂无${title}`" />
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
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, reactive, onMounted } from 'vue'
import { Plus, Delete, List, Document, DocumentCopy } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import JsonEditor from '@/components/JsonEditor.vue'

// 组件名称（用于递归引用）
defineOptions({
  name: 'ParameterFormEditor'
})

const props = defineProps({
  modelValue: {
    type: Array,
    default: () => []
  },
  type: {
    type: String,
    default: 'query'
  },
  title: {
    type: String,
    default: '参数'
  },
  supportNested: {
    type: Boolean,
    default: false
  },
  level: {
    type: Number,
    default: 0
  },
  readonly: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue'])

// 编辑模式
const editMode = ref('form')

// 参数数据
const parameters = ref([])

// JSON编辑器相关
const jsonData = ref([])
const jsonEditorRef = ref(null)

// 标记是否正在初始化，避免递归更新
const isInitializing = ref(false)



// 创建新参数
const createNewParameter = () => {
  return {
    name: '',
    type: 'string',
    required: false,
    description: '',
    nested_fields: [],
    array_item_fields: []
  }
}

// 添加参数
const addParameter = () => {
  parameters.value.push(createNewParameter())
  // 强制触发更新
  nextTick(() => {
    emit('update:modelValue', [...parameters.value])
  })
}

// 删除参数
const removeParameter = (index) => {
  parameters.value.splice(index, 1)
  emit('update:modelValue', parameters.value)
}

// 清空所有参数
const clearAll = () => {
  parameters.value = []
  emit('update:modelValue', parameters.value)
}

// 添加嵌套字段
const addNestedField = (parentParam) => {
  // 确保嵌套字段数组存在
  if (!parentParam.nested_fields) {
    parentParam.nested_fields = reactive([])
  }
  
  const newField = {
    name: '',
    type: 'string',
    required: false,
    description: '',
    nested_fields: [],
    array_item_fields: []
  }
  
  parentParam.nested_fields.push(newField)
  
  // 强制触发更新
  emit('update:modelValue', [...parameters.value])
}

// 添加数组项字段
const addArrayItemField = (parentParam) => {
  // 确保数组项字段数组存在
  if (!parentParam.array_item_fields) {
    // 使用 Vue 的响应性 API 来确保数组是响应式的
    parentParam.array_item_fields = reactive([])
  }
  
  const newField = {
    name: '',
    type: 'string',
    required: false,
    description: '',
    nested_fields: [],
    array_item_fields: []
  }
  
  // 添加新字段
  parentParam.array_item_fields.push(newField)
  
  // 强制触发更新
  emit('update:modelValue', [...parameters.value])
}

// 更新参数
const updateParameter = (index) => {
  emit('update:modelValue', parameters.value)
}

// 处理参数更新（手动触发）
const handleParameterUpdate = () => {
  if (!isInitializing.value) {
    emit('update:modelValue', parameters.value)
  }
}

// 处理嵌套字段更新
const handleNestedFieldUpdate = () => {
  if (!isInitializing.value) {
    emit('update:modelValue', parameters.value)
  }
}

// 验证参数名
const validateParameterName = (param) => {
  return param && param.name && param.name.trim() !== ''
}

// 验证参数类型
const validateParameterType = (param) => {
  const validTypes = ['string', 'integer', 'number', 'boolean', 'array', 'object', 'file']
  return param && param.type && validTypes.includes(param.type)
}

// 验证整个参数对象
const validateParameter = (param) => {
  const errors = []
  
  if (!validateParameterName(param)) {
    errors.push('参数名不能为空')
  }
  
  if (!validateParameterType(param)) {
    errors.push('参数类型无效')
  }
  
  // 检查嵌套字段
  if (param.type === 'object' && param.nested_fields) {
    param.nested_fields.forEach((nestedField, index) => {
      const nestedErrors = validateParameter(nestedField)
      if (nestedErrors.length > 0) {
        errors.push(`嵌套字段 ${index + 1}: ${nestedErrors.join(', ')}`)
      }
    })
  }
  
  // 检查数组项字段
  if (param.type === 'array' && param.array_item_fields) {
    param.array_item_fields.forEach((arrayField, index) => {
      const arrayErrors = validateParameter(arrayField)
      if (arrayErrors.length > 0) {
        errors.push(`数组项字段 ${index + 1}: ${arrayErrors.join(', ')}`)
      }
    })
  }
  
  return errors
}

// 验证所有参数
const validateAllParameters = () => {
  const allErrors = []
  
  parameters.value.forEach((param, index) => {
    const paramErrors = validateParameter(param)
    if (paramErrors.length > 0) {
      allErrors.push(`参数 ${index + 1} (${param.name || '未命名'}): ${paramErrors.join(', ')}`)
    }
  })
  
  return allErrors
}

// 处理类型变化
const handleTypeChange = (param, index) => {
  if (param.type === 'object') {
    param.nested_fields = param.nested_fields || []
  } else if (param.type === 'array') {
    param.array_item_fields = param.array_item_fields || []
  }
  updateParameter(index)
}



// JSON编辑模式相关方法
const parametersToJson = (params) => {
  try {
    const jsonObj = {}
    params.forEach(param => {
      if (param.name) {
        let value = param.example || ''
        
        // 根据类型设置默认值
        switch (param.type) {
          case 'integer':
            value = parseInt(value) || 0
            break
          case 'number':
            value = parseFloat(value) || 0.0
            break
          case 'boolean':
            value = value === 'true' || value === true
            break
          case 'array':
            value = Array.isArray(value) ? value : []
            break
          case 'object':
            value = typeof value === 'object' ? value : {}
            break
          default:
            value = String(value || '')
        }
        
        jsonObj[param.name] = value
      }
    })
    return JSON.stringify(jsonObj, null, 2)
  } catch (error) {
    console.error('转换为JSON失败:', error)
    return '{}'
  }
}

const jsonToParameters = (jsonStr) => {
  try {
    const jsonObj = JSON.parse(jsonStr)
    const params = []
    
    Object.keys(jsonObj).forEach(key => {
      const value = jsonObj[key]
      let type = 'string'
      
      // 根据值推断类型
      if (typeof value === 'number') {
        type = Number.isInteger(value) ? 'integer' : 'number'
      } else if (typeof value === 'boolean') {
        type = 'boolean'
      } else if (Array.isArray(value)) {
        type = 'array'
      } else if (typeof value === 'object' && value !== null) {
        type = 'object'
      }
      
      params.push({
        name: key,
        type: type,
        required: false,
        description: '',
        nested_fields: [],
        array_item_fields: []
      })
    })
    
    return params
  } catch (error) {
    console.error('解析JSON失败:', error)
    ElMessage.error('JSON格式错误，请检查语法')
    return parameters.value
  }
}

// 更新JSON数据
const updateJsonData = () => {
  // 过滤掉内部使用的字段，只保留API需要的字段
  const cleanParameters = parameters.value.map(param => {
    const cleanParam = {
      name: param.name,
      type: param.type,
      description: param.description,
      required: param.required
    }
    
    // 如果是对象类型且有嵌套字段，递归清理
    if (param.type === 'object' && param.nested_fields && param.nested_fields.length > 0) {
      cleanParam.nested_fields = cleanNestedFields(param.nested_fields)
    }
    
    // 如果是数组类型且有数组项字段，递归清理
    if (param.type === 'array' && param.array_item_fields && param.array_item_fields.length > 0) {
      cleanParam.array_item_fields = cleanNestedFields(param.array_item_fields)
    }
    return cleanParam
  })
  
  jsonData.value = cleanParameters
}

// 递归清理嵌套字段
const cleanNestedFields = (fields) => {
  return fields.map(field => {
    const cleanField = {
      name: field.name,
      type: field.type,
      description: field.description,
      required: field.required
    }
    
    // 递归处理嵌套字段
    if (field.type === 'object' && field.nested_fields && field.nested_fields.length > 0) {
      cleanField.nested_fields = cleanNestedFields(field.nested_fields)
    }
    
    if (field.type === 'array' && field.array_item_fields && field.array_item_fields.length > 0) {
      cleanField.array_item_fields = cleanNestedFields(field.array_item_fields)
    }
    
    return cleanField
  })
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

// 初始化参数
const initParameters = () => {
  if (props.modelValue && Array.isArray(props.modelValue)) {
    parameters.value = props.modelValue.map(param => ({
      name: param.name || '',
      type: param.type || 'string',
      required: param.required || false,
      description: param.description || '',
      nested_fields: param.nested_fields || [],
      array_item_fields: param.array_item_fields || []
    }))
  } else {
    parameters.value = []
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
      parameters.value = value
      emit('update:modelValue', parameters.value)
    }
  }
})

// 防抖函数
const debounce = (fn, delay) => {
  let timer = null
  return function(...args) {
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => {
      fn.apply(this, args)
    }, delay)
  }
}

// 注意：JSON数据变化的处理已移至jsonEditorData计算属性中

// 监听props变化（仅在初始化时）
watch(() => props.modelValue, (newValue) => {
  if (JSON.stringify(newValue) !== JSON.stringify(parameters.value)) {
    isInitializing.value = true
    initParameters()
    if (editMode.value === 'json') {
      updateJsonData()
    }
    nextTick(() => {
      isInitializing.value = false
    })
  }
}, { immediate: true, deep: true })

// 组件挂载时初始化一次
onMounted(() => {
  isInitializing.value = true
  initParameters()
  nextTick(() => {
    isInitializing.value = false
  })
})
</script>

<style scoped>
.parameter-form-editor {
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

.param-count {
  font-size: 14px;
  color: #606266;
}

.header-right {
  display: flex;
  gap: 8px;
}

.parameters-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.parameter-item {
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  padding: 16px;
  background: #fff;
}

.parameter-item.nested {
  background: #f9fafc;
  border-color: #d9ecff;
}

.parameter-form {
  width: 100%;
}

.parameter-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 4px;
  height: 32px;
}

.nested-fields,
.array-item-fields {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px dashed #e4e7ed;
}

.nested-fields-placeholder,
.array-fields-placeholder {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: #f8f9fa;
  border: 1px dashed #d9ecff;
  border-radius: 4px;
  margin-top: 8px;
}

.nested-fields-header,
.array-fields-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: #f0f9ff;
  border: 1px solid #e1f5fe;
  border-radius: 4px;
  margin-bottom: 12px;
}

.nested-fields-header {
  background: #f0f9ff;
  border-color: #e1f5fe;
}

.array-fields-header {
  background: #fff7ed;
  border-color: #fed7aa;
}

.nested-fields-container,
.array-fields-container {
  background: rgba(255, 255, 255, 0.5);
  border-radius: 6px;
  padding: 8px;
}

.array-item-title {
  font-size: 13px;
  color: #909399;
  margin-bottom: 12px;
  font-weight: 500;
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
  .parameter-form :deep(.el-row) {
    flex-direction: column;
  }
  
  .parameter-form :deep(.el-col) {
    width: 100% !important;
    margin-bottom: 8px;
  }
  
  .parameter-actions {
    justify-content: center;
    margin-top: 8px;
  }
}
</style>