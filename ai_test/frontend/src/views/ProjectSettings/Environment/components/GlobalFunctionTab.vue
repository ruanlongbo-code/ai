<template>
  <div class="global-function-tab">
    <div class="content">
      <div style="width: 300px;padding-bottom: 10px"><el-button
          type="primary"
          @click="handleSave"
          :loading="saving"
          :disabled="!hasChanges"
      >保存全局函数
      </el-button></div>
      <CodeEditor
          v-model="formData.func_global"
          language="python"
          height="900px"
          theme="twilight"
          :font-size="14"
          :placeholder="'在此编写可用于测试执行的全局函数代码'"
      />
    </div>
  </div>
</template>

<script setup>
import {ref, reactive, computed, watch} from 'vue'
import {ElMessage} from 'element-plus'
import {Check, RefreshLeft} from '@element-plus/icons-vue'
import {useProjectStore} from '@/stores'
import {updateTestEnvironment} from '@/api/test_environment'
import CodeEditor from '@/components/CodeEditor.vue'

const props = defineProps({
  environmentData: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update'])

const projectStore = useProjectStore()
const saving = ref(false)
const funcFormRef = ref()

const formData = reactive({
  func_global: ''
})

const originalData = ref({func_global: ''})

watch(() => props.environmentData, (newData) => {
  formData.func_global = newData?.func_global || ''
  originalData.value = {func_global: newData?.func_global || ''}
}, {immediate: true, deep: true})

const hasChanges = computed(() => formData.func_global !== originalData.value.func_global)

const handleSave = async () => {
  if (!projectStore.currentProject?.id || !props.environmentData?.id) {
    ElMessage.error('参数错误')
    return
  }
  try {
    saving.value = true
    await updateTestEnvironment(
        projectStore.currentProject.id,
        props.environmentData.id,
        {func_global: formData.func_global}
    )
    originalData.value.func_global = formData.func_global
    emit('update', {
      ...props.environmentData,
      func_global: formData.func_global,
      updated_at: new Date().toISOString()
    })
    ElMessage.success('全局函数保存成功')
  } catch (error) {
    console.error('保存全局函数失败:', error)
    ElMessage.error('保存失败，请稍后重试')
  } finally {
    saving.value = false
  }
}

const handleReset = () => {
  formData.func_global = originalData.value.func_global
}
</script>

<style scoped>





</style>