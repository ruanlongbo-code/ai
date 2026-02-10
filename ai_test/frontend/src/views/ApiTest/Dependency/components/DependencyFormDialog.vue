<template>
  <el-dialog
    :model-value="visible"
    @update:model-value="$emit('update:visible', $event)"
    :title="isEdit ? '编辑接口依赖' : '添加接口依赖'"
    width="600px"
    :close-on-click-modal="false"
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="formRules"
      label-width="100px"
      @submit.prevent
    >
      <el-form-item label="依赖名称" prop="name">
        <el-input
          v-model="formData.name"
          placeholder="请输入依赖名称"
          maxlength="50"
          show-word-limit
        />
      </el-form-item>
      
      <el-form-item label="源接口" prop="source_interface_id">
        <el-select
          v-model="formData.source_interface_id"
          placeholder="请选择源接口"
          filterable
          style="width: 100%"
          @change="handleSourceInterfaceChange"
        >
          <el-option
          v-for="item in interfaceList"
          :key="item.id"
          :label="`${item.summary || '未命名接口'} - ${item.method} ${item.path}`"
          :value="item.id"
        />
        </el-select>
      </el-form-item>
      
      <el-form-item label="依赖类型" prop="dependency_type">
        <el-select
          v-model="formData.dependency_type"
          placeholder="请选择依赖类型"
          style="width: 100%"
        >
          <el-option label="请求头" value="header" />
          <el-option label="请求参数" value="param" />
          <el-option label="请求体" value="body" />
          <el-option label="响应数据" value="response" />
        </el-select>
      </el-form-item>
      
      <el-form-item label="源字段路径" prop="source_field_path">
        <el-input
          v-model="formData.source_field_path"
          placeholder="例如: data.user.id 或 headers.token"
        />
        <div class="form-tip">
          指定从源接口响应中提取数据的路径，支持点号分隔的嵌套路径
        </div>
      </el-form-item>
      
      <el-form-item label="目标字段" prop="target_field_name">
        <el-input
          v-model="formData.target_field_name"
          placeholder="例如: user_id 或 Authorization"
        />
        <div class="form-tip">
          指定将提取的数据设置到当前接口的哪个字段
        </div>
      </el-form-item>
      
      <el-form-item label="执行顺序" prop="execution_order">
        <el-input-number
          v-model="formData.execution_order"
          :min="1"
          :max="999"
          placeholder="执行顺序"
          style="width: 100%"
        />
        <div class="form-tip">在同一分组内的执行顺序，数值越小优先级越高</div>
      </el-form-item>
      
      <el-form-item label="状态" prop="is_active">
        <el-switch
          v-model="formData.is_active"
          active-text="启用"
          inactive-text="禁用"
        />
      </el-form-item>
      
      <el-form-item label="描述" prop="description">
        <el-input
          v-model="formData.description"
          type="textarea"
          :rows="3"
          placeholder="请输入依赖描述（可选）"
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
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { createDependency, updateDependency } from '@/api/apiTest'
import { getProjectInterfaces } from '@/api/apiTest'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  dependencyData: {
    type: Object,
    default: null
  },
  groupId: {
    type: Number,
    default: null
  },
  interfaceId: {
    type: Number,
    required: true
  }
})

const emit = defineEmits(['update:visible', 'success'])

// 表单引用
const formRef = ref()

// 是否为编辑模式
const isEdit = computed(() => !!props.dependencyData?.id)

// 提交状态
const submitting = ref(false)

// 接口列表
const interfaceList = ref([])

// 表单数据
const formData = reactive({
  name: '',
  source_interface_id: null,
  dependency_type: 'response',
  source_field_path: '',
  target_field_name: '',
  execution_order: 1,
  is_active: true,
  description: ''
})

// 表单验证规则
const formRules = {
  name: [
    { required: true, message: '请输入依赖名称', trigger: 'blur' },
    { min: 1, max: 50, message: '依赖名称长度在 1 到 50 个字符', trigger: 'blur' }
  ],
  source_interface_id: [
    { required: true, message: '请选择源接口', trigger: 'change' }
  ],
  dependency_type: [
    { required: true, message: '请选择依赖类型', trigger: 'change' }
  ],
  source_field_path: [
    { required: true, message: '请输入源字段路径', trigger: 'blur' }
  ],
  target_field_name: [
    { required: true, message: '请输入目标字段名称', trigger: 'blur' }
  ],
  execution_order: [
    { required: true, message: '请输入执行顺序', trigger: 'blur' },
    { type: 'number', min: 1, max: 999, message: '执行顺序必须在 1-999 之间', trigger: 'blur' }
  ],
  description: [
    { max: 200, message: '描述长度不能超过 200 个字符', trigger: 'blur' }
  ]
}

// 重置表单
const resetForm = () => {
  formData.name = ''
  formData.source_interface_id = null
  formData.dependency_type = 'response'
  formData.source_field_path = ''
  formData.target_field_name = ''
  formData.execution_order = 1
  formData.is_active = true
  formData.description = ''
  
  // 清除验证状态
  if (formRef.value) {
    formRef.value.clearValidate()
  }
}

// 组件挂载时加载接口列表
onMounted(() => {
  loadInterfaceList()
})

// 监听依赖数据变化，初始化表单
watch(() => props.dependencyData, (newData) => {
  if (newData) {
    formData.name = newData.name || ''
    formData.source_interface_id = newData.source_interface_id || null
    formData.dependency_type = newData.dependency_type || 'response'
    formData.source_field_path = newData.source_field_path || ''
    formData.target_field_name = newData.target_field_name || ''
    formData.execution_order = newData.execution_order || 1
    formData.is_active = newData.is_active !== undefined ? newData.is_active : true
    formData.description = newData.description || ''
  } else {
    resetForm()
  }
}, { immediate: true })

// 监听对话框显示状态
watch(() => props.visible, (visible) => {
  if (visible && !props.dependencyData) {
    resetForm()
  }
})

// 加载接口列表
const loadInterfaceList = async () => {
  try {
    // 从路由中获取项目ID
    const projectId = parseInt(window.location.pathname.split('/')[2])
    const response = await getProjectInterfaces(projectId, { page_size: 1000 })
    
    // 过滤掉当前接口，避免自依赖
    interfaceList.value = (response.data.interfaces || []).filter(
      item => item.id !== props.interfaceId
    )
  } catch (error) {
    console.error('加载接口列表失败:', error)
    ElMessage.error('加载接口列表失败')
  }
}

// 源接口变化处理
const handleSourceInterfaceChange = (interfaceId) => {
  // 可以在这里根据选择的接口自动填充一些字段
  // 比如根据接口类型推荐字段路径等
}

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
      source_interface_id: formData.source_interface_id,
      dependency_type: formData.dependency_type,
      source_field_path: formData.source_field_path,
      target_field_name: formData.target_field_name,
      execution_order: formData.execution_order,
      is_active: formData.is_active,
      description: formData.description
    }
    
    if (isEdit.value) {
      // 编辑依赖
      const projectId = parseInt(window.location.pathname.split('/')[2])
      await updateDependency(projectId, props.groupId, props.dependencyData.id, requestData)
      ElMessage.success('依赖更新成功')
    } else {
      // 创建依赖
      const projectId = parseInt(window.location.pathname.split('/')[2])
      await createDependency(projectId, props.groupId, requestData)
      ElMessage.success('依赖创建成功')
    }
    
    emit('success')
    emit('update:visible', false)
    resetForm()
    
  } catch (error) {
    console.error('提交依赖失败:', error)
    ElMessage.error(isEdit.value ? '依赖更新失败' : '依赖创建失败')
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