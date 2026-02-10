<template>
  <el-dialog
    v-model="visible"
    title="用例运行结果"
    width="85%"
    :before-close="handleClose"
    class="run-result-dialog"
  >
    <div class="result-content">
      <TestResultCard :result="runResult" />
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">关闭</el-button>
        <el-button type="primary" @click="handleRerun">重新运行</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import TestResultCard from '@/components/common/TestResultCard.vue'

// Props
const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  runResult: {
    type: Object,
    default: () => ({
      status: 'pending',
      case_name: '',
      case_id: null,
      case_run_id: null,
      environmentName: '',
      start_time: null,
      end_time: null,
      duration: null,
      error_message: null,
      logs: [],
      case_data: {},
      request_info: []
    })
  }
})

// Emits
const emit = defineEmits(['update:modelValue', 'rerun'])

// 响应式数据
const visible = ref(props.modelValue)

// 监听 modelValue 变化
watch(() => props.modelValue, (newVal) => {
  visible.value = newVal
})

// 监听 visible 变化
watch(visible, (newVal) => {
  emit('update:modelValue', newVal)
})

// 方法
const handleClose = () => {
  visible.value = false
}

const handleRerun = () => {
  emit('rerun')
}
</script>

<style scoped>
.run-result-dialog {
  --el-dialog-border-radius: 16px;
}

.run-result-dialog :deep(.el-dialog) {
  border-radius: 16px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
}

.run-result-dialog :deep(.el-dialog__header) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 20px 24px;
  border-radius: 16px 16px 0 0;
  margin: 0;
}

.run-result-dialog :deep(.el-dialog__title) {
  font-size: 18px;
  font-weight: 600;
  color: white;
}

.run-result-dialog :deep(.el-dialog__headerbtn) {
  top: 20px;
  right: 24px;
}

.run-result-dialog :deep(.el-dialog__headerbtn .el-dialog__close) {
  color: white;
  font-size: 18px;
}

.run-result-dialog :deep(.el-dialog__body) {
  padding: 0;
  background: #f8fafc;
}

.run-result-dialog :deep(.el-dialog__footer) {
  background: white;
  border-top: 1px solid #e4e7ed;
  padding: 16px 24px;
  border-radius: 0 0 16px 16px;
}

.result-content {
  padding: 24px;
  max-height: 70vh;
  overflow-y: auto;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.dialog-footer .el-button {
  padding: 8px 20px;
  border-radius: 8px;
  font-weight: 500;
}

/* 自定义滚动条 */
.result-content::-webkit-scrollbar {
  width: 6px;
}

.result-content::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.result-content::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.result-content::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .run-result-dialog :deep(.el-dialog) {
    width: 95% !important;
    margin: 0 auto;
  }
  
  .result-content {
    padding: 16px;
    max-height: 60vh;
  }
  
  .run-result-dialog :deep(.el-dialog__header) {
    padding: 16px 20px;
  }
  
  .run-result-dialog :deep(.el-dialog__footer) {
    padding: 12px 20px;
  }
}
</style>