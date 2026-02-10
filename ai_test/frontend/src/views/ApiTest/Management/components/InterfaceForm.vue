<template>
  <div class="interface-form">
    <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="120px"
        class="interface-form-content"
    >
      <!-- 基本信息 -->
      <div class="form-section">
        <div class="section-title">基本信息</div>

        <el-form-item label="HTTP方法" prop="method" required>
          <el-select v-model="formData.method" placeholder="请选择HTTP方法" style="width: 100%">
            <el-option label="GET" value="GET"/>
            <el-option label="POST" value="POST"/>
            <el-option label="PUT" value="PUT"/>
            <el-option label="DELETE" value="DELETE"/>
            <el-option label="PATCH" value="PATCH"/>
            <el-option label="HEAD" value="HEAD"/>
            <el-option label="OPTIONS" value="OPTIONS"/>
          </el-select>
        </el-form-item>

        <el-form-item label="接口路径" prop="path" required>
          <el-input v-model="formData.path" placeholder="例如: /api/users/{id}"/>
        </el-form-item>

        <el-form-item label="接口名称" prop="summary" required>
          <el-input v-model="formData.summary" placeholder="请输入接口名称"/>
        </el-form-item>

        <el-form-item label="接口描述" prop="description">
          <el-input
              v-model="formData.description"
              type="textarea"
              :rows="3"
              placeholder="请输入接口描述"
          />
        </el-form-item>
      </div>

      <!-- 接口配置选项卡 -->
      <div class="form-section">
        <div class="section-title">接口配置</div>

        <el-tabs v-model="activeConfigTab" class="config-tabs">
          <!-- 路径参数 -->
          <el-tab-pane label="路径参数" name="path">
            <parameter-form-editor
                :key="`path-params-${tabKey}`"
                v-model="formData.parameters.path"
                type="path"
                title="路径参数"
                :readonly="readonly || mode === 'view'"
            />
          </el-tab-pane>

          <!-- 查询参数 -->
          <el-tab-pane label="查询参数" name="query">
            <parameter-form-editor
                :key="`query-params-${tabKey}`"
                v-model="formData.parameters.query"
                type="query"
                title="查询参数"
                :readonly="readonly || mode === 'view'"
            />
          </el-tab-pane>

          <!-- 请求头 -->
          <el-tab-pane label="请求头" name="header">
            <parameter-form-editor
                :key="`header-params-${tabKey}`"
                v-model="formData.parameters.header"
                type="header"
                title="请求头"
                :readonly="readonly || mode === 'view'"
            />
          </el-tab-pane>

          <!-- 请求体 -->
          <el-tab-pane label="请求体" name="body">
            <div class="request-body-form">
              <el-form-item label="Content-Type">
                <el-select
                    v-model="formData.requestBody.content_type"
                    placeholder="请选择Content-Type"
                    :disabled="readonly || mode === 'view'"
                >
                  <el-option label="application/json" value="application/json"/>
                  <el-option label="application/x-www-form-urlencoded" value="application/x-www-form-urlencoded"/>
                  <el-option label="multipart/form-data" value="multipart/form-data"/>
                  <el-option label="text/plain" value="text/plain"/>
                </el-select>
              </el-form-item>

              <parameter-form-editor
                  :key="`body-params-${tabKey}`"
                  v-model="formData.requestBody.body"
                  type="body"
                  title="请求体参数"
                  :support-nested="true"
                  :readonly="readonly || mode === 'view'"
              />
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>

      <!-- 响应配置单独区域 -->
      <div class="form-section">
        <div class="section-title">响应示例</div>
        <response-form-editor
            :key="`responses-${tabKey}`"
            v-model="formData.responses"
            :readonly="readonly || mode === 'view'"
        />
      </div>
    </el-form>

    <!-- 操作按钮 -->
    <div class="form-actions">
      <el-button @click="handleCancel">取消</el-button>
      <el-button
          type="primary"
          :loading="submitLoading"
          @click="handleSubmit"
      >
        {{ mode === 'edit' ? '更新' : '保存' }}
      </el-button>
    </div>
  </div>
</template>

<script setup>
import {ref, reactive, watch, nextTick, onMounted} from 'vue'
import {ElMessage} from 'element-plus'
import ParameterFormEditor from './ParameterFormEditor.vue'
import ResponseFormEditor from './ResponseFormEditor.vue'

// 确保组件正确注册
defineOptions({
  components: {
    ParameterFormEditor,
    ResponseFormEditor
  }
})

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({})
  },
  visible: {
    type: Boolean,
    default: false
  },
  mode: {
    type: String,
    default: 'create', // create, edit, view
    validator: (value) => ['create', 'edit', 'view'].includes(value)
  }
})

const emit = defineEmits(['update:modelValue', 'update:visible', 'submit', 'cancel'])

const formRef = ref(null)
const activeConfigTab = ref('path')
const isInitializing = ref(false)
const tabKey = ref(0) // 用于强制重新渲染响应配置组件
const submitLoading = ref(false) // 添加提交加载状态

// 表单数据
const formData = ref({
  method: 'GET',
  path: '',
  summary: '',
  description: '',
  parameters: {
    path: [],
    query: [],
    header: []
  },
  request_body: {},
  requestBody: {
    content_type: 'application/json',
    body: []
  },
  responses: []
})

// 表单验证规则
const formRules = {
  method: [
    {required: true, message: '请选择HTTP方法', trigger: 'change'}
  ],
  path: [
    {required: true, message: '请输入接口路径', trigger: 'blur'}
  ],
  summary: [
    {required: true, message: '请输入接口名称', trigger: 'blur'}
  ]
}

// 初始化表单数据
const initFormData = () => {
  if (props.modelValue && Object.keys(props.modelValue).length > 0) {
    // 处理parameters字段，确保其为正确的格式
    let parameters = {
      path: [],
      query: [],
      header: []
    }
    
    if (props.modelValue.parameters) {
      if (typeof props.modelValue.parameters === 'object' && !Array.isArray(props.modelValue.parameters)) {
        // 如果是对象格式，直接使用
        parameters = {
          path: props.modelValue.parameters.path || [],
          query: props.modelValue.parameters.query || [],
          header: props.modelValue.parameters.header || []
        }
      }
    }
    
    formData.value = {
      method: props.modelValue.method || 'GET',
      path: props.modelValue.path || '',
      summary: props.modelValue.summary || '',
      description: props.modelValue.description || '',
      parameters: parameters,
      request_body: {
        content_type: props.modelValue.request_body?.content_type || 'application/json',
        body: Array.isArray(props.modelValue.request_body?.body) ? props.modelValue.request_body.body : []
      },
      requestBody: {
        content_type: props.modelValue.request_body?.content_type || props.modelValue.requestBody?.content_type || 'application/json',
        body: Array.isArray(props.modelValue.request_body?.body)
          ? props.modelValue.request_body.body
          : (Array.isArray(props.modelValue.requestBody?.body) ? props.modelValue.requestBody.body : [])
      },
      responses: Array.isArray(props.modelValue.responses) ? props.modelValue.responses : []
    }
  } else {
    formData.value = {
      method: 'GET',
      path: '',
      summary: '',
      description: '',
      parameters: {
        path: [],
        query: [],
        header: []
      },
      request_body: {
        content_type: 'application/json',
        body: []
      },
      requestBody: {
        content_type: 'application/json',
        body: []
      },
      responses: []
    }
  }
}

// 表单验证
const validateForm = async () => {
  try {
    await formRef.value.validate()
    return true
  } catch (error) {
    return false
  }
}

// 获取表单数据
const getFormData = () => {
  return {...formData}
}

// 重置表单
const resetForm = () => {
  formRef.value?.resetFields()
  Object.assign(formData.value, {
    method: 'GET',
    path: '',
    summary: '',
    description: '',
    parameters: {
      path: [],
      query: [],
      header: []
    },
    request_body: {},
    requestBody: {
      content_type: 'application/json',
      body: []
    },
    responses: []
  })
  // 更新tabKey以强制重新渲染所有组件
  tabKey.value++
}

// 监听props变化
watch(() => [props.modelValue, props.visible], ([newModelValue, newVisible]) => {
  if (newModelValue || newVisible) {
    isInitializing.value = true
    initFormData()
    nextTick(() => {
      isInitializing.value = false
    })
  }
}, {immediate: true, deep: true})

// 提交表单
const handleSubmit = async () => {
  try {
    submitLoading.value = true
    await formRef.value.validate()
    emit('submit', formData.value)
  } catch (error) {
    console.error('表单验证失败:', error)
  } finally {
    submitLoading.value = false
  }
}

// 取消操作
const handleCancel = () => {
  emit('cancel')
}

// 监听表单数据变化，发射更新事件
watch(formData, (newValue) => {
  // 避免在初始化时触发更新事件
  if (!isInitializing.value) {
    emit('update:modelValue', {...newValue})
  }
}, {deep: true})

// 保持 requestBody.body 与 request_body 同步（数组 -> 对象）
const buildRequestBodyObject = (paramsArray) => {
  if (!Array.isArray(paramsArray)) return {}
  const obj = {}
  paramsArray.forEach(param => {
    if (!param || !param.name) return
    // 根据类型生成占位示例值
    switch (param.type) {
      case 'integer':
        obj[param.name] = 0
        break
      case 'number':
        obj[param.name] = 0.0
        break
      case 'boolean':
        obj[param.name] = false
        break
      case 'array':
        obj[param.name] = []
        break
      case 'object':
        obj[param.name] = {}
        break
      default:
        obj[param.name] = ''
    }
  })
  return obj
}

// 同步包装结构：当编辑器的 body 或 content_type 变化时，更新 request_body 以符合后端期望格式
watch(() => formData.value.requestBody.body, (newBody) => {
  if (!isInitializing.value) {
    formData.value.request_body = {
      content_type: formData.value.requestBody.content_type || 'application/json',
      body: Array.isArray(newBody) ? newBody : []
    }
  }
}, { deep: true })

watch(() => formData.value.requestBody.content_type, (newType) => {
  if (!isInitializing.value) {
    formData.value.request_body = {
      content_type: newType || 'application/json',
      body: Array.isArray(formData.value.requestBody.body) ? formData.value.requestBody.body : []
    }
  }
})

onMounted(() => {
  initFormData()
})

// 暴露方法给父组件
defineExpose({
  validateForm,
  getFormData,
  resetForm
})
</script>

<style scoped>
.interface-form {
  width: 100%;
  height: 100%;
}

.interface-form-content {
  height: 100%;
  overflow-y: auto;
}

.form-section {
  margin-bottom: 24px;
  padding: 16px;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  background: #fafbfc;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 2px solid #409eff;
}


.config-tabs {
  --el-tabs-header-height: 48px;
  margin-top: 8px;
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

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.request-body-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-actions {
  margin-top: 24px;
  padding: 16px 0;
  text-align: right;
  border-top: 1px solid #e4e7ed;
}

.form-actions .el-button {
  margin-left: 12px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .form-section {
    padding: 12px;
    margin-bottom: 16px;
  }

  .section-title {
    font-size: 14px;
    margin-bottom: 12px;
  }

  :deep(.el-form-item__label) {
    width: 100px !important;
    font-size: 13px;
  }
}
</style>