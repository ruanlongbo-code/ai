<template>
  <el-dialog
    v-model="visible"
    title="选择运行环境"
    width="25%"
    :before-close="handleClose"
  >
    <div class="environment-selection">
      <el-form :model="form" label-width="100px">
        <el-form-item label="运行环境" required>
          <el-select
            v-model="form.environmentId"
            placeholder="请选择运行环境"
            style="width: 100%"
            :loading="environmentsLoading"
          >
            <el-option
              v-for="env in environments"
              :key="env.id"
              :label="env.name"
              :value="env.id"
            >
              <div class="environment-option">
                <span class="env-name">{{ env.name }}</span>
              </div>
            </el-option>
          </el-select>
        </el-form-item>

      </el-form>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button 
          type="primary" 
          @click="handleRun"
          :loading="running"
          :disabled="!form.environmentId"
        >
          {{ running ? '运行中...' : '开始运行' }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { getTestEnvironments } from '@/api/test_environment'
import { useProjectStore } from '@/stores/index'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  caseInfo: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:modelValue', 'run'])

const projectStore = useProjectStore()
const visible = ref(false)
const running = ref(false)
const environmentsLoading = ref(false)
const environments = ref([])

const form = reactive({
  environmentId: null
})

// 监听 modelValue 变化
watch(() => props.modelValue, (newVal) => {
  visible.value = newVal
  if (newVal) {
    loadEnvironments()
    resetForm()
  }
})

// 监听 visible 变化
watch(visible, (newVal) => {
  emit('update:modelValue', newVal)
})

// 加载环境列表
const loadEnvironments = async () => {
  environmentsLoading.value = true
  try {
    const projectId = projectStore.currentProject.id
    if (!projectId) {
      ElMessage.error('未找到项目信息')
      return
    }

    const response = await getTestEnvironments(projectId, { page_size: 100 })
    environments.value = response.data.environments || []
    
    if (environments.value.length === 0) {
      ElMessage.warning('当前项目暂无可用的测试环境')
    }
  } catch (error) {
    console.error('加载环境列表失败:', error)
    ElMessage.error('加载环境列表失败')
    environments.value = []
  } finally {
    environmentsLoading.value = false
  }
}

// 重置表单
const resetForm = () => {
  form.environmentId = null
}

// 关闭弹框
const handleClose = () => {
  visible.value = false
}

// 开始运行
const handleRun = async () => {
  if (!form.environmentId) {
    ElMessage.warning('请选择运行环境')
    return
  }

  running.value = true
  try {
    // 发送运行请求
    emit('run', {
      caseId: props.caseInfo.id,
      environmentId: form.environmentId,
      caseName: props.caseInfo.name
    })
  } catch (error) {
    console.error('运行用例失败:', error)
    ElMessage.error('运行用例失败')
  } finally {
    running.value = false
  }
}
</script>

<style scoped>
.environment-selection {
  padding: 10px 0;
}

.environment-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.env-name {
  font-weight: 500;
  color: #303133;
}

.env-url {
  font-size: 12px;
  color: #909399;
}

.case-info {
  background: #f5f7fa;
  padding: 12px;
  border-radius: 4px;
  border: 1px solid #e4e7ed;
}

.info-item {
  display: flex;
  margin-bottom: 8px;
}

.info-item:last-child {
  margin-bottom: 0;
}

.label {
  color: #606266;
  font-size: 14px;
  min-width: 80px;
}

.value {
  color: #303133;
  font-size: 14px;
  font-weight: 500;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>