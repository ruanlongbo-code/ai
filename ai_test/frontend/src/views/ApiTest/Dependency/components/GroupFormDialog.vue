<template>
  <el-dialog
    :model-value="visible"
    @update:model-value="$emit('update:visible', $event)"
    :title="isEdit ? '编辑依赖分组' : '新建依赖分组'"
    width="500px"
    :close-on-click-modal="false"
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="formRules"
      label-width="80px"
      @submit.prevent
    >
      <el-form-item label="分组名称" prop="name">
        <el-input
          v-model="formData.name"
          placeholder="请输入分组名称"
          maxlength="50"
          show-word-limit
        />
      </el-form-item>
      
      <el-form-item label="分组描述" prop="description">
        <el-input
          v-model="formData.description"
          type="textarea"
          :rows="3"
          placeholder="请输入分组描述（可选）"
          maxlength="200"
          show-word-limit
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleCancel">取消</el-button>
        <el-button 
          type="primary" 
          @click="handleSubmit"
          :loading="submitting"
        >
          {{ isEdit ? '保存' : '创建' }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { createDependencyGroup, updateDependencyGroup } from '@/api/apiTest'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  groupData: {
    type: Object,
    default: null
  },
  interfaceId: {
    type: Number,
    required: true
  },
  projectId: {
    type: Number,
    required: true
  }
})

const emit = defineEmits(['update:visible', 'success'])

// 表单引用
const formRef = ref()

// 是否为编辑模式
const isEdit = computed(() => !!props.groupData?.id)

// 提交状态
const submitting = ref(false)

// 表单数据
const formData = reactive({
  name: '',
  description: ''
})

// 表单验证规则
const formRules = {
  name: [
    { required: true, message: '请输入分组名称', trigger: 'blur' },
    { min: 1, max: 100, message: '分组名称长度在 1 到 100 个字符', trigger: 'blur' }
  ],
  description: [
    { max: 200, message: '描述长度不能超过 200 个字符', trigger: 'blur' }
  ]
}

// 重置表单
const resetForm = () => {
  formData.name = ''
  formData.description = ''
  
  // 清除验证状态
  if (formRef.value) {
    formRef.value.clearValidate()
  }
}

// 监听分组数据变化，初始化表单
watch(() => props.groupData, (newData) => {
  if (newData) {
    formData.name = newData.name || ''
    formData.description = newData.description || ''
  } else {
    resetForm()
  }
}, { immediate: true })

// 监听对话框显示状态
watch(() => props.visible, (visible) => {
  if (visible && !props.groupData) {
    resetForm()
  }
})

// 取消操作
const handleCancel = () => {
  emit('update:visible', false)
  resetForm()
}

// 提交表单
const handleSubmit = async () => {
  try {
    // 表单验证
    await formRef.value.validate()
    
    submitting.value = true
    
    const requestData = {
      name: formData.name,
      description: formData.description,
      target_interface_id: props.interfaceId
    }
    
    if (isEdit.value) {
      // 编辑分组
      await updateDependencyGroup(props.projectId, props.groupData.id, requestData)
      ElMessage.success('分组更新成功')
    } else {
      // 创建分组
      await createDependencyGroup(props.projectId, requestData)
      ElMessage.success('分组创建成功')
    }
    
    emit('success')
    emit('update:visible', false)
    resetForm()
    
  } catch (error) {
    console.error('提交分组失败:', error)
    ElMessage.error(isEdit.value ? '分组更新失败' : '分组创建失败')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.dialog-footer {
  text-align: right;
}
</style>