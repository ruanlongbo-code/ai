<template>
  <el-form
    ref="formRef"
    :model="formData"
    :rules="formRules"
    label-width="120px"
    class="requirement-form"
  >
    <el-form-item label="需求标题" prop="title">
      <el-input
        v-model="formData.title"
        placeholder="请输入需求标题"
        maxlength="100"
        show-word-limit
      />
    </el-form-item>
    
    <el-form-item label="所属模块" prop="module_id">
      <el-select
        v-model="formData.module_id"
        placeholder="请选择所属模块"
        style="width: 100%;"
      >
        <el-option
          v-for="module in modules"
          :key="module.id"
          :label="module.name"
          :value="module.id"
        >
          <div class="module-option">
            <span class="module-name">{{ module.name }}</span>
            <span v-if="module.description" class="module-desc">{{ module.description }}</span>
          </div>
        </el-option>
      </el-select>
    </el-form-item>
    
    <el-form-item label="优先级" prop="priority">
      <el-select
        v-model="formData.priority"
        placeholder="请选择优先级"
        style="width: 100%;"
      >
        <el-option
          v-for="(label, value) in REQUIREMENT_PRIORITY_LABELS"
          :key="value"
          :label="label"
          :value="value"
        >
          <div class="priority-option">
            <el-tag
              :color="REQUIREMENT_PRIORITY_COLORS[value]"
              effect="light"
              size="small"
              style="margin-right: 8px;"
            >
              {{ label }}
            </el-tag>
          </div>
        </el-option>
      </el-select>
    </el-form-item>
    
    <el-form-item v-if="showStatus" label="状态" prop="status">
      <el-select
        v-model="formData.status"
        placeholder="请选择状态"
        style="width: 100%;"
      >
        <el-option
          v-for="(label, value) in REQUIREMENT_STATUS_LABELS"
          :key="value"
          :label="label"
          :value="value"
        />
      </el-select>
    </el-form-item>
    
    <el-form-item label="需求描述" prop="description">
      <el-input
        v-model="formData.description"
        type="textarea"
        :rows="6"
        placeholder="请详细描述需求内容，包括功能要求、业务场景、验收标准等"
        maxlength="2000"
        show-word-limit
      />
    </el-form-item>
    
    <el-form-item v-if="showAttachments" label="附件">
      <el-upload
        v-model:file-list="formData.attachments"
        :action="uploadAction"
        :headers="uploadHeaders"
        :before-upload="beforeUpload"
        :on-success="handleUploadSuccess"
        :on-error="handleUploadError"
        multiple
        drag
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">
          将文件拖到此处，或<em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            支持 jpg/png/gif/pdf/doc/docx 文件，且不超过 10MB
          </div>
        </template>
      </el-upload>
    </el-form-item>
    
    <el-form-item>
      <div class="form-actions">
        <el-button @click="handleCancel">取消</el-button>
        <el-button v-if="showSaveDraft" @click="handleSaveDraft" :loading="saving">
          保存草稿
        </el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          {{ submitText }}
        </el-button>
      </div>
    </el-form-item>
  </el-form>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import {
  REQUIREMENT_STATUS_LABELS,
  REQUIREMENT_PRIORITY_LABELS,
  REQUIREMENT_PRIORITY_COLORS
} from '@/api/functional_test'

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({})
  },
  modules: {
    type: Array,
    default: () => []
  },
  mode: {
    type: String,
    default: 'create', // create, edit
    validator: (value) => ['create', 'edit'].includes(value)
  },
  showStatus: {
    type: Boolean,
    default: false
  },
  showSaveDraft: {
    type: Boolean,
    default: true
  },
  showAttachments: {
    type: Boolean,
    default: false
  },
  submitText: {
    type: String,
    default: '提交'
  }
})

const emit = defineEmits([
  'update:modelValue',
  'submit',
  'save-draft',
  'cancel'
])

// 表单引用
const formRef = ref()

// 表单数据
const formData = reactive({
  title: '',
  module_id: null,
  priority: 'medium',
  status: 'draft',
  description: '',
  attachments: []
})

// 表单验证规则
const formRules = {
  title: [
    { required: true, message: '请输入需求标题', trigger: 'blur' },
    { min: 5, max: 100, message: '标题长度应在 5 到 100 个字符之间', trigger: 'blur' }
  ],
  module_id: [
    { required: true, message: '请选择所属模块', trigger: 'change' }
  ],
  priority: [
    { required: true, message: '请选择优先级', trigger: 'change' }
  ],
  description: [
    { required: true, message: '请输入需求描述', trigger: 'blur' },
    { min: 20, max: 2000, message: '描述长度应在 20 到 2000 个字符之间', trigger: 'blur' }
  ]
}

// 状态
const saving = ref(false)
const submitting = ref(false)

// 上传配置
const uploadAction = '/api/upload'
const uploadHeaders = {
  'Authorization': `Bearer ${localStorage.getItem('token')}`
}

// 计算属性
const isEditMode = computed(() => props.mode === 'edit')

// 方法
const beforeUpload = (file) => {
  const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
  const isAllowedType = allowedTypes.includes(file.type)
  const isLt10M = file.size / 1024 / 1024 < 10

  if (!isAllowedType) {
    ElMessage.error('只能上传 jpg/png/gif/pdf/doc/docx 格式的文件!')
    return false
  }
  if (!isLt10M) {
    ElMessage.error('上传文件大小不能超过 10MB!')
    return false
  }
  return true
}

const handleUploadSuccess = (response, file) => {
  ElMessage.success('文件上传成功')
}

const handleUploadError = (error, file) => {
  ElMessage.error('文件上传失败')
}

const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    submitting.value = true
    emit('submit', { ...formData })
  } catch (error) {
    console.error('表单验证失败:', error)
  } finally {
    submitting.value = false
  }
}

const handleSaveDraft = async () => {
  try {
    // 草稿保存时只验证必填字段
    const draftRules = {
      title: formRules.title,
      module_id: formRules.module_id
    }
    
    // 临时设置验证规则
    const originalRules = formRef.value.rules
    formRef.value.rules = draftRules
    
    await formRef.value.validate()
    
    saving.value = true
    const draftData = { ...formData, status: 'draft' }
    emit('save-draft', draftData)
    
    // 恢复原始验证规则
    formRef.value.rules = originalRules
  } catch (error) {
    console.error('草稿保存验证失败:', error)
  } finally {
    saving.value = false
  }
}

const handleCancel = () => {
  emit('cancel')
}

const resetForm = () => {
  formRef.value?.resetFields()
}

// 监听外部数据变化
watch(
  () => props.modelValue,
  (newValue) => {
    if (newValue) {
      Object.assign(formData, newValue)
    }
  },
  { immediate: true, deep: true }
)

// 监听表单数据变化，同步到外部
watch(
  formData,
  (newValue) => {
    emit('update:modelValue', { ...newValue })
  },
  { deep: true }
)

// 暴露方法给父组件
defineExpose({
  validate: () => formRef.value.validate(),
  resetForm,
  formData
})
</script>

<style scoped>
.requirement-form {
  max-width: 800px;
}

.form-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  padding-top: 24px;
  border-top: 1px solid #e5e7eb;
}

.module-option {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.module-name {
  font-weight: 500;
}

.module-desc {
  font-size: 12px;
  color: #6b7280;
}

.priority-option {
  display: flex;
  align-items: center;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .requirement-form {
    max-width: 100%;
  }
  
  .form-actions {
    flex-direction: column-reverse;
  }
  
  .form-actions .el-button {
    width: 100%;
  }
}
</style>