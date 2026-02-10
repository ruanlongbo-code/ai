<template>
  <div class="assertions-editor">
    <div class="editor-header">
      <div class="header-left">
        <span class="assertions-count">{{ localAssertions.response.length }} 个断言</span>
        <div class="edit-mode-switch">
          <el-radio-group v-model="editMode" size="small">
            <el-radio-button value="form">表单编辑</el-radio-button>
            <el-radio-button value="json">JSON编辑</el-radio-button>
          </el-radio-group>
        </div>
      </div>
      <div class="header-right">
        <el-button v-if="editMode === 'form'" size="small" @click="addAssertion">
          <el-icon><Plus /></el-icon>
          添加断言
        </el-button>
        <el-button v-if="editMode === 'form' && localAssertions.response.length > 0" size="small" @click="clearAll">
          <el-icon><Delete /></el-icon>
          清空断言
        </el-button>
        <el-button v-if="editMode === 'json'" size="small" @click="formatJson">
          <el-icon><Document /></el-icon>
          格式化
        </el-button>
      </div>
    </div>

    <!-- 表单编辑模式 -->
    <div v-show="editMode === 'form'" class="form-edit-mode">
      <div v-if="localAssertions.response.length === 0" class="empty-assertions">
        <el-empty description="暂无断言配置" />
      </div>
      
      <div v-else class="assertions-list">
        <div
          v-for="(assertion, index) in localAssertions.response"
          :key="`assertion-${index}`"
          class="assertion-item"
        >
          <div class="assertion-header">
            <span class="assertion-title">断言 {{ index + 1 }}</span>
            <el-button
              size="small"
              plain
              @click="removeAssertion(index)"
            >
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>
          
          <el-form label-width="100px" class="assertion-form">
            <el-form-item label="断言类型">
              <el-select
                v-model="assertion.type"
                placeholder="请选择断言类型"
                @change="handleAssertionTypeChange(assertion, $event)"
              >
                <el-option
                  v-for="type in assertionTypes"
                  :key="type.value"
                  :label="type.label"
                  :value="type.value"
                />
              </el-select>
            </el-form-item>
            
            <el-form-item label="字段路径">
              <el-input
                v-model="assertion.field"
                placeholder="字段路径，如 http_code, data.id, message"
              />
            </el-form-item>
            
            <el-form-item label="期望值">
              <div class="expected-value-editor">
                <el-input
                  v-if="getExpectedInputType(assertion.type) === 'text'"
                  v-model="assertion.expected"
                  placeholder="请输入期望值"
                />
                
                <el-input-number
                  v-else-if="getExpectedInputType(assertion.type) === 'number'"
                  v-model="assertion.expected"
                  placeholder="请输入数字"
                  style="width: 100%"
                />
                
                <el-switch
                  v-else-if="getExpectedInputType(assertion.type) === 'boolean'"
                  v-model="assertion.expected"
                  active-text="true"
                  inactive-text="false"
                />
                
                <json-editor
                  v-else-if="getExpectedInputType(assertion.type) === 'json'"
                  v-model="assertion.expected"
                  height="150px"
                  :readonly="false"
                />
                
                <el-input
                  v-else
                  v-model="assertion.expected"
                  placeholder="请输入期望值"
                />
              </div>
            </el-form-item>
            
            <el-form-item v-if="assertion.type === 'regex'" label="正则选项">
              <el-checkbox-group v-model="assertion.options">
                <el-checkbox value="ignoreCase">忽略大小写</el-checkbox>
                <el-checkbox value="multiline">多行模式</el-checkbox>
                <el-checkbox value="dotAll">点匹配所有字符</el-checkbox>
              </el-checkbox-group>
            </el-form-item>
          </el-form>
        </div>
      </div>
    </div>

    <!-- JSON编辑模式 -->
    <div v-show="editMode === 'json'" class="json-edit-mode">
      <json-editor
        v-model="jsonEditorData"
        height="400px"
        :readonly="false"
        @change="handleJsonChange"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Delete, Document } from '@element-plus/icons-vue'
import JsonEditor from '@/components/JsonEditor.vue'

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({
      response: []
    })
  }
})

const emit = defineEmits(['update:modelValue'])

// 响应式数据
const editMode = ref('form')

// 本地断言数据
const localAssertions = reactive({
  response: []
})

// 断言类型配置
const assertionTypes = [
  { label: 'HTTP状态码', value: 'http_code' },
  { label: '等于', value: 'equals' },
  { label: '不等于', value: 'not_equals' },
  { label: '包含', value: 'contains' },
  { label: '不包含', value: 'not_contains' },
  { label: '大于', value: 'greater_than' },
  { label: '大于等于', value: 'greater_than_or_equal' },
  { label: '小于', value: 'less_than' },
  { label: '小于等于', value: 'less_than_or_equal' },
  { label: '为空', value: 'is_null' },
  { label: '不为空', value: 'not_null' },
  { label: '为真', value: 'is_true' },
  { label: '为假', value: 'is_false' },
  { label: '正则匹配', value: 'regex' },
  { label: '数组长度', value: 'array_length' },
  { label: '对象包含键', value: 'has_key' },
  { label: '类型检查', value: 'type_check' }
]

// JSON编辑器数据
const jsonEditorData = computed({
  get() {
    return JSON.stringify(localAssertions, null, 2)
  },
  set(value) {
    try {
      const parsed = JSON.parse(value)
      if (parsed && typeof parsed === 'object') {
        Object.assign(localAssertions, parsed)
      }
    } catch {
      // JSON解析失败，忽略
    }
  }
})

// 获取期望值输入类型
const getExpectedInputType = (assertionType) => {
  switch (assertionType) {
    case 'http_code':
    case 'greater_than':
    case 'greater_than_or_equal':
    case 'less_than':
    case 'less_than_or_equal':
    case 'array_length':
      return 'number'
    case 'is_null':
    case 'not_null':
    case 'is_true':
    case 'is_false':
      return 'boolean'
    case 'equals':
    case 'not_equals':
      return 'json'
    default:
      return 'text'
  }
}

// 添加断言
const addAssertion = () => {
  const newAssertion = {
    type: 'equals',
    field: '',
    expected: ''
  }
  localAssertions.response.push(newAssertion)
}

// 删除断言
const removeAssertion = (index) => {
  localAssertions.response.splice(index, 1)
}

// 清空所有断言
const clearAll = () => {
  ElMessageBox.confirm(
    '确定要清空所有断言吗？',
    '确认清空',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    localAssertions.response = []
    ElMessage.success('已清空所有断言')
  }).catch(() => {
    // 用户取消
  })
}

// 处理断言类型变化
const handleAssertionTypeChange = (assertion, newType) => {
  // 根据断言类型设置默认值
  switch (newType) {
    case 'http_code':
      assertion.field = 'http_code'
      assertion.expected = 200
      break
    case 'is_null':
    case 'not_null':
    case 'is_true':
    case 'is_false':
      assertion.expected = true
      break
    case 'greater_than':
    case 'greater_than_or_equal':
    case 'less_than':
    case 'less_than_or_equal':
    case 'array_length':
      assertion.expected = 0
      break
    case 'regex':
      assertion.expected = ''
      assertion.options = []
      break
    default:
      assertion.expected = ''
  }
}

// 格式化JSON
const formatJson = () => {
  try {
    const formatted = JSON.stringify(localAssertions, null, 2)
    jsonEditorData.value = formatted
    ElMessage.success('JSON格式化完成')
  } catch (error) {
    ElMessage.error('JSON格式化失败')
  }
}

// 处理JSON变化
const handleJsonChange = ({ json, isValid }) => {
  if (isValid && json) {
    Object.assign(localAssertions, json)
  }
}

// 监听props变化
watch(() => props.modelValue, (newValue) => {
  if (newValue) {
    // 使用逐个赋值确保响应式更新
    localAssertions.response = newValue.response || []
  }
}, { immediate: true, deep: true })

// 监听本地数据变化，同步到父组件
watch(localAssertions, (newValue) => {
  emit('update:modelValue', { ...newValue })
}, { deep: true })
</script>

<style scoped>
.assertions-editor {
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

.assertions-count {
  font-size: 14px;
  color: #606266;
}

.header-right {
  display: flex;
  gap: 8px;
}

.form-edit-mode {
  margin-top: 16px;
}

.empty-assertions {
  padding: 40px 0;
}

.assertions-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 16px;
}

.assertion-item {
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  padding: 16px;
  background: #fff;
}

.assertion-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px dashed #e4e7ed;
}

.assertion-title {
  font-weight: 500;
  color: #303133;
}

.assertion-form {
  width: 100%;
}

.expected-value-editor {
  width: 100%;
}

.json-edit-mode {
  margin-top: 16px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .editor-header {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
  
  .header-left {
    flex-direction: column;
    gap: 8px;
    align-items: stretch;
  }
  
  .edit-mode-switch {
    margin-left: 0;
  }
  
  .header-right {
    justify-content: center;
  }
  
  .assertions-list {
    grid-template-columns: 1fr;
  }
  
  .assertion-header {
    flex-direction: column;
    gap: 8px;
    align-items: stretch;
  }
}

@media (min-width: 769px) and (max-width: 1024px) {
  .assertions-list {
    grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  }
}

@media (min-width: 1025px) {
  .assertions-list {
    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  }
}
</style>