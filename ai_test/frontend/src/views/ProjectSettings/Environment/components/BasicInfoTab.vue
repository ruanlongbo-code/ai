<template>
  <div class="basic-info-tab">
    <div class="tab-content">
      <el-form
        ref="basicFormRef"
        :model="formData"
        :rules="formRules"
        label-width="120px"
        label-position="left"
        class="basic-form"
      >
        <el-form-item label="环境名称" prop="name">
          <el-input
            v-model="formData.name"
            placeholder="请输入环境名称"
            maxlength="100"
            show-word-limit
            clearable
            @blur="handleNameBlur"
          />
        </el-form-item>
        
        <el-form-item label="创建时间" v-if="environmentData.created_at">
          <el-input
            :value="formatDateTime(environmentData.created_at)"
            readonly
            disabled
          />
        </el-form-item>
        
        <el-form-item label="更新时间" v-if="environmentData.updated_at">
          <el-input
            :value="formatDateTime(environmentData.updated_at)"
            readonly
            disabled
          />
        </el-form-item>
      </el-form>
      
      <div class="form-actions">
        <el-button 
          type="primary" 
          @click="handleSave"
          :loading="saving"
          :disabled="!hasChanges"
        >
          <el-icon><Check /></el-icon>
          保存基本信息
        </el-button>
        <el-button @click="handleReset" :disabled="!hasChanges">
          <el-icon><RefreshLeft /></el-icon>
          重置
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { Check, RefreshLeft } from '@element-plus/icons-vue'
import { useProjectStore } from '@/stores'
import { updateTestEnvironment } from '@/api/test_environment'

const props = defineProps({
  environmentData: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update'])

const projectStore = useProjectStore()
const basicFormRef = ref()
const saving = ref(false)

// 表单数据
const formData = reactive({
  name: ''
})

// 原始数据（用于比较是否有变更）
const originalData = ref({})

// 表单验证规则
const formRules = {
  name: [
    { required: true, message: '请输入环境名称', trigger: 'blur' },
    { min: 1, max: 100, message: '环境名称长度在 1 到 100 个字符', trigger: 'blur' }
  ]
}

// 计算属性：是否有变更
const hasChanges = computed(() => {
  return formData.name !== originalData.value.name
})

// 监听环境数据变化，更新表单
watch(() => props.environmentData, (newData) => {
  if (newData && newData.name !== undefined) {
    formData.name = newData.name || ''
    originalData.value = {
      name: newData.name || ''
    }
  }
}, { immediate: true, deep: true })

// 处理名称失焦事件
const handleNameBlur = () => {
  if (basicFormRef.value) {
    basicFormRef.value.validateField('name')
  }
}

// 保存基本信息
const handleSave = async () => {
  if (!projectStore.currentProject?.id || !props.environmentData?.id) {
    ElMessage.error('参数错误')
    return
  }

  try {
    await basicFormRef.value.validate()
    
    saving.value = true
    
    const updateData = {
      name: formData.name
    }
    
    const response = await updateTestEnvironment(
      projectStore.currentProject.id,
      props.environmentData.id,
      updateData
    )
    
    // 更新原始数据
    originalData.value = {
      name: formData.name
    }
    
    // 通知父组件更新
    emit('update', {
      ...props.environmentData,
      name: formData.name,
      updated_at: new Date().toISOString()
    })
    
    ElMessage.success('基本信息保存成功')
  } catch (error) {
    console.error('保存基本信息失败:', error)
    ElMessage.error('保存失败，请稍后重试')
  } finally {
    saving.value = false
  }
}

// 重置表单
const handleReset = () => {
  formData.name = originalData.value.name
  if (basicFormRef.value) {
    basicFormRef.value.clearValidate()
  }
}

// 格式化日期时间
const formatDateTime = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}
</script>

<style scoped>
.basic-info-tab {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.tab-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.basic-form {
  flex: 1;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  padding: 24px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}



.form-actions {
  display: flex;
  gap: 12px;
  padding: 20px 24px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}



/* 响应式设计 */
@media (max-width: 768px) {
  .basic-form {
    padding: 16px;
  }
  
  .form-actions {
    padding: 16px;
    flex-direction: column;
  }
  
  .form-actions .el-button {
    width: 100%;
  }
}
</style>