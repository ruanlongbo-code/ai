<template>
  <el-dialog
    v-model="visible"
    title="新建测试计划"
    width="500px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="formRules"
      label-width="100px"
    >
      <el-form-item label="计划名称" prop="task_name">
        <el-input
          v-model="formData.task_name"
          placeholder="请输入测试计划名称"
          maxlength="100"
          show-word-limit
        />
      </el-form-item>
      
      <el-form-item label="计划类型" prop="type">
        <el-select
          v-model="formData.type"
          placeholder="请选择计划类型"
          style="width: 100%"
        >
          <el-option label="接口测试" value="api" />
          <el-option label="UI测试" value="ui" />
          <el-option label="功能测试" value="functional" />
        </el-select>
      </el-form-item>
      
      <el-form-item label="计划描述" prop="description">
        <el-input
          v-model="formData.description"
          type="textarea"
          :rows="4"
          placeholder="请输入测试计划描述（可选）"
          maxlength="500"
          show-word-limit
        />
      </el-form-item>
    </el-form>
    
    <template #footer>
      <el-button @click="handleCancel">取消</el-button>
      <el-button type="primary" @click="handleSubmit" :loading="submitLoading">
        确定
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'submit'])

// 响应式数据
const visible = ref(false)
const formRef = ref(null)
const submitLoading = ref(false)

// 表单数据
const formData = reactive({
  task_name: '',
  type: '',
  description: ''
})

// 表单验证规则
const formRules = {
  task_name: [
    { required: true, message: '请输入测试计划名称', trigger: 'blur' },
    { min: 1, max: 100, message: '长度在 1 到 100 个字符', trigger: 'blur' }
  ],
  type: [
    { required: true, message: '请选择计划类型', trigger: 'change' }
  ]
}

// 监听 modelValue 变化
watch(() => props.modelValue, (newVal) => {
  visible.value = newVal
})

// 监听 visible 变化
watch(visible, (newVal) => {
  emit('update:modelValue', newVal)
})

// 重置表单
const resetForm = () => {
  formData.task_name = ''
  formData.type = ''
  formData.description = ''
  if (formRef.value) {
    formRef.value.clearValidate()
  }
}

// 处理关闭
const handleClose = () => {
  resetForm()
}

// 处理取消
const handleCancel = () => {
  visible.value = false
}

// 处理提交
const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    submitLoading.value = true
    
    // 提交数据
    emit('submit', { ...formData })
    
  } catch (error) {
    console.error('表单验证失败:', error)
  } finally {
    submitLoading.value = false
  }
}

// 提交成功后关闭弹窗
const handleSubmitSuccess = () => {
  visible.value = false
  resetForm()
}

// 暴露方法给父组件
defineExpose({
  handleSubmitSuccess
})
</script>

<style scoped>
.el-form {
  padding: 20px 0;
}

.el-form-item {
  margin-bottom: 24px;
}

.el-input,
.el-select {
  width: 100%;
}

.el-textarea {
  width: 100%;
}
</style>