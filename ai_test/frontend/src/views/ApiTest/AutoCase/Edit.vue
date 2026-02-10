<template>
  <div class="test-case-edit-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="breadcrumb-section">
        <el-breadcrumb separator="/">
          <el-breadcrumb-item>
            <router-link to="/api-test/auto-case">
              自动化用例
            </router-link>
          </el-breadcrumb-item>
          <el-breadcrumb-item>编辑用例</el-breadcrumb-item>
        </el-breadcrumb>
      </div>
      <div class="action-section">
        <el-button @click="handleCancel" plain class="back-button">
          <el-icon><ArrowLeft /></el-icon>
          返回列表
        </el-button>
      </div>
    </div>

    <!-- 编辑表单 -->
    <div class="page-content" v-loading="loading">
      <el-form
        ref="editFormRef"
        :model="editForm"
        :rules="editRules"
        label-width="120px"
        label-position="top"
        @submit.prevent="handleSave"
      >
        <!-- 基本信息 -->
        <el-card class="form-section">
          <template #header>
            <div class="section-header">
              <h3>基本信息</h3>
            </div>
          </template>

          <div class="form-grid">
            <el-form-item label="用例名称" prop="name">
              <el-input
                v-model="editForm.name"
                placeholder="请输入用例名称"
                maxlength="200"
                show-word-limit
              />
            </el-form-item>

            <el-form-item label="接口路径" prop="interface_name">
              <el-input
                v-model="editForm.interface_name"
                placeholder="请输入接口名称"
                maxlength="200"
              />
            </el-form-item>

            <el-form-item label="用例状态" prop="status">
              <div class="status-selector-compact">
                <div 
                  v-for="status in statusOptions" 
                  :key="status.value"
                  class="status-option"
                  :class="{ 'active': editForm.status === status.value }"
                  @click="editForm.status = status.value"
                >
                  <div class="status-icon" :class="status.iconClass">
                    <el-icon><component :is="status.icon" /></el-icon>
                  </div>
                  <span class="status-text">{{ status.label }}</span>
                </div>
              </div>
            </el-form-item>

            <el-form-item label="用例描述" prop="description">
              <el-input
                v-model="editForm.description"
                type="textarea"
                :rows="2"
              placeholder="请输入用例描述"
              maxlength="1000"
              show-word-limit
            />
          </el-form-item>
          </div>
        </el-card>

        <!-- 前置条件 -->
        <el-card class="form-section">
          <template #header>
            <div class="section-header">
              <h3>前置接口请求</h3>
              <el-button size="small" @click="addPrecondition">
                <el-icon><Plus /></el-icon>
                添加前置接口
              </el-button>
            </div>
          </template>

          <div v-if="editForm.preconditions.length === 0" class="empty-state">
            <el-empty description="暂无前置接口" />
          </div>

          <div v-else class="preconditions-list">
            <el-collapse v-model="activePreconditions">
              <el-collapse-item
                v-for="(precondition, index) in editForm.preconditions"
                :key="`precondition-${index}`"
                :name="`precondition-${index}`"
                class="precondition-item"
              >
                <template #title>
                  <div class="precondition-title">
                    <b class="title-text">
                      <el-icon><SetUp /></el-icon>
                      {{ precondition.name || `前置条件 ${index + 1}` }}</b>
                    <div class="title-actions" @click.stop>
                      <el-button
                        size="small"
                        plain
                        @click="removePrecondition(index)"
                      >
                        <el-icon><Delete /></el-icon>
                      </el-button>
                    </div>
                  </div>
                </template>

                <div class="precondition-content">
                  <el-form-item label="名称">
                    <el-input
                      v-model="precondition.name"
                      placeholder="请输入前置条件名称"
                    />
                  </el-form-item>

                  <el-form-item label="提取变量">
                    <div class="extract-variables">
                      <div
                        v-for="(extract, extractIndex) in precondition.extract"
                        :key="`extract-${extractIndex}`"
                        class="extract-item"
                      >
                        <el-input
                          v-model="extract[0]"
                          placeholder="变量名"
                          style="width: 200px"
                        />
                        <el-input
                          v-model="extract[1]"
                          placeholder="提取路径 (如: [0].id)"
                          style="width: 300px"
                        />
                        <el-button
                          size="small"
                          plain
                          @click="removeExtractVariable(precondition, extractIndex)"
                        >
                          <el-icon><Delete /></el-icon>
                        </el-button>
                      </div>
                      <el-button
                        size="small"
                        @click="addExtractVariable(precondition)"
                      >
                        <el-icon><Plus /></el-icon>
                        添加提取变量
                      </el-button>
                    </div>
                  </el-form-item>

                  <el-form-item label="请求配置">
                    <request-editor
                      v-model="precondition.request"
                      :show-scripts="true"
                    />
                  </el-form-item>
                </div>
              </el-collapse-item>
            </el-collapse>
          </div>
        </el-card>

        <!-- 主请求 -->
        <el-card class="form-section">
          <template #header>
            <div class="section-header">
              <h3>主接口请求</h3>
            </div>
          </template>

          <request-editor
            v-model="editForm.request"
            :show-scripts="true"
          />
        </el-card>

        <!-- 断言 -->
        <el-card class="form-section">
          <template #header>
            <div class="section-header">
              <h3>断言配置</h3>
            </div>
          </template>

          <assertions-editor v-model="editForm.assertions" />
        </el-card>
      </el-form>
    </div>

    <!-- 悬浮操作按钮 -->
    <div class="floating-actions">
      <el-button type="primary" @click="handleSave" :loading="saving" size="large">
        <el-icon><Check /></el-icon>
        保存
      </el-button>
      <el-button @click="handleCancel" size="large">
        关闭
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Check, Plus, Delete, Clock, CircleCheck, CircleClose } from '@element-plus/icons-vue'
import { getApiTestCaseDetail, updateApiTestCase } from '@/api/apiTest.js'
import RequestEditor from './components/RequestEditor.vue'
import AssertionsEditor from './components/AssertionsEditor.vue'

const router = useRouter()
const route = useRoute()

// 响应式数据
const loading = ref(false)
const saving = ref(false)
const editFormRef = ref()
const activePreconditions = ref([])

// 路由参数
const projectId = computed(() => route.params.projectId)
const testCaseId = computed(() => route.params.testCaseId)

// 编辑表单
const editForm = reactive({
  name: '',
  description: '',
  interface_name: '',
  status: 'pending',
  preconditions: [],
  request: {
    url: '',
    method: 'GET',
    params: {},
    headers: {},
    body: {},
    files: {},
    base_url: '${{base_url}}',
    interface_id: '',
    setup_script: '',
    teardown_script: ''
  },
  assertions: {
    response: []
  }
})

// 状态选项定义（与后端枚举保持一致）
const statusOptions = [
  {
    value: 'pending',
    label: '待审核',
    description: '用例待审核，不可执行',
    icon: Clock,
    iconClass: 'status-pending'
  },
  {
    value: 'ready',
    label: '可执行',
    description: '用例已审核通过，可以执行',
    icon: CircleCheck,
    iconClass: 'status-ready'
  },
  {
    value: 'disabled',
    label: '不可执行',
    description: '用例已禁用，不可执行',
    icon: CircleClose,
    iconClass: 'status-disabled'
  }
]

// 表单验证规则
const editRules = {
  name: [
    { required: true, message: '请输入用例名称', trigger: 'blur' },
    { min: 1, max: 200, message: '用例名称长度在 1 到 200 个字符', trigger: 'blur' }
  ],
  interface_name: [
    { required: true, message: '请输入接口名称', trigger: 'blur' }
  ],
  status: [
    { required: true, message: '请选择用例状态', trigger: 'change' }
  ]
}

// 加载用例详情
const loadTestCaseDetail = async () => {
  console.log('开始加载用例详情...')
  console.log('projectId:', projectId.value)
  console.log('testCaseId:', testCaseId.value)

  if (!projectId.value || !testCaseId.value) {
    ElMessage.error('参数错误')
    return
  }

  try {
    loading.value = true
    const response = await getApiTestCaseDetail(projectId.value, testCaseId.value)

    // 调试信息
    console.log('API响应数据:', response)
    console.log('当前editForm:', editForm)

    // 填充表单数据 - 使用逐个赋值确保响应式更新
    editForm.name = response.data.name || ''
    editForm.description = response.data.description || ''
    editForm.interface_name = response.data.interface_name || ''
    editForm.status = response.data.status || '可用'
    editForm.preconditions = response.data.preconditions || []

    // 填充请求数据
    editForm.request.url = response.data.request?.url || ''
    editForm.request.method = response.data.request?.method || 'GET'
    editForm.request.params = response.data.request?.params || {}
    editForm.request.headers = response.data.request?.headers || {}
    editForm.request.body = response.data.request?.body || {}
    editForm.request.files = response.data.request?.files || {}
    editForm.request.base_url = response.data.request?.base_url || '${{base_url}}'
    editForm.request.interface_id = response.data.request?.interface_id ? String(response.data.request.interface_id) : ''
    editForm.request.setup_script = response.data.request?.setup_script || ''
    editForm.request.teardown_script = response.data.request?.teardown_script || ''

    // 填充断言数据
    editForm.assertions = response.data.assertions || { response: [] }

    // 调试信息 - 数据填充后
    console.log('数据填充后的editForm:', editForm)
    console.log('editForm.request:', editForm.request)
    console.log('editForm.assertions:', editForm.assertions)

    // 默认展开第一个前置条件
    if (editForm.preconditions.length > 0) {
      activePreconditions.value = ['precondition-0']
    }
  } catch (error) {
    console.error('加载用例详情失败:', error)
    ElMessage.error('加载用例详情失败')
  } finally {
    loading.value = false
  }
}

// 添加前置条件
const addPrecondition = () => {
  const newPrecondition = {
    name: '',
    extract: [],
    request: {
      url: '',
      method: 'GET',
      params: {},
      headers: {},
      body: {},
      files: {},
      base_url: '${{base_url}}',
      interface_id: '',
      setup_script: '',
      teardown_script: ''
    }
  }

  editForm.preconditions.push(newPrecondition)
  const newIndex = editForm.preconditions.length - 1
  activePreconditions.value.push(`precondition-${newIndex}`)
}

// 删除前置条件
const removePrecondition = (index) => {
  editForm.preconditions.splice(index, 1)
  // 更新激活的折叠面板
  activePreconditions.value = activePreconditions.value
    .filter(name => name !== `precondition-${index}`)
    .map(name => {
      const idx = parseInt(name.split('-')[1])
      return idx > index ? `precondition-${idx - 1}` : name
    })
}

// 添加提取变量
const addExtractVariable = (precondition) => {
  if (!precondition.extract) {
    precondition.extract = []
  }
  precondition.extract.push(['', ''])
}

// 删除提取变量
const removeExtractVariable = (precondition, index) => {
  precondition.extract.splice(index, 1)
}

// 保存用例
const handleSave = async () => {
  if (!editFormRef.value) return

  try {
    await editFormRef.value.validate()
    saving.value = true

    await updateApiTestCase(projectId.value, testCaseId.value, editForm)

    ElMessage.success('用例保存成功')

  } catch (error) {
    if (error.message) {
      console.error('保存用例失败:', error)
      ElMessage.error('保存用例失败')
    }
  } finally {
    saving.value = false
  }
}

// 取消编辑
const handleCancel = () => {
  router.push(`/api-test/auto-case`)
}

// 组件挂载时加载数据
onMounted(() => {
  loadTestCaseDetail()
})
</script>

<style scoped>
.test-case-edit-page {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding:  10px 20px;
}

.breadcrumb-section {
  flex: 1;
}

.breadcrumb-section :deep(.el-breadcrumb__inner) {
  color: #606266;
}

.breadcrumb-section :deep(.el-breadcrumb__inner:hover) {
  color: #409eff;
}

.action-section {
  display: flex;
  gap: 12px;
}

.back-button {
  padding: 8px 12px;
  font-size: 14px;
}

.back-button:hover {
  background-color: #ecf5ff;
}

.floating-actions {
  position: fixed;
  bottom: 16px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  justify-content: center;
  gap: 16px;
  padding: 0;
  z-index: 1000;
  pointer-events: none;
}

.floating-actions .el-button {
  pointer-events: auto;
}



.page-content {
  flex: 1;
  padding: 24px;
  padding-bottom: 100px; /* 为悬浮按钮留出空间 */
  overflow-y: auto;
  margin: 0 auto;
  width: 100%;
}

.form-section {
  margin-bottom: 24px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

/* 紧凑状态选择器样式 */
.status-selector-compact {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.status-option {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border: 1px solid var(--el-border-color);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  background: white;
  min-width: 80px;
  justify-content: center;
}

.status-option:hover {
  border-color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
}

.status-option.active {
  border-color: var(--el-color-primary);
  background: var(--el-color-primary-light-8);
  color: var(--el-color-primary);
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.3);
  font-weight: 600;
}

.status-option .status-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  font-size: 12px;
}

.status-option .status-icon.status-pending {
  background: #f0f9ff;
  color: #0ea5e9;
}

.status-option .status-icon.status-ready {
  background: #f0fdf4;
  color: #22c55e;
}

.status-option .status-icon.status-disabled {
  background: #fef2f2;
  color: #ef4444;
}

.status-option.active .status-icon.status-pending {
  background: #0ea5e9;
  color: white;
}

.status-option.active .status-icon.status-ready {
  background: #22c55e;
  color: white;
}

.status-option.active .status-icon.status-disabled {
  background: #ef4444;
  color: white;
}

.status-text {
  font-size: 13px;
  font-weight: 500;
}

/* 状态选择器样式 */
.status-selector {
  margin-top: 8px;
}

.status-label {
  font-size: 14px;
  color: var(--el-text-color-regular);
  margin-bottom: 12px;
  font-weight: 500;
}

.status-cards-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 12px;
}

.status-card {
  position: relative;
  display: flex;
  align-items: center;
  padding: 16px;
  border: 2px solid var(--el-border-color-light);
  border-radius: 12px;
  background: var(--el-bg-color);
  cursor: pointer;
  transition: all 0.3s ease;
}

.status-card:hover {
  border-color: var(--el-color-primary-light-5);
  background: var(--el-color-primary-light-9);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.15);
}

.status-card.active {
  border-color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
  box-shadow: 0 4px 16px rgba(64, 158, 255, 0.2);
}

.status-card.active::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
  background: var(--el-color-primary);
  border-radius: 2px 0 0 2px;
}

.status-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  margin-right: 12px;
  font-size: 18px;
  flex-shrink: 0;
}

.status-icon.status-pending {
  background: #fdf6ec;
  color: #e6a23c;
}

.status-icon.status-ready {
  background: #f0f9f0;
  color: #67c23a;
}

.status-icon.status-disabled {
  background: #fef0f0;
  color: #f56c6c;
}

.status-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.status-title {
  font-weight: 600;
  color: var(--el-text-color-primary);
  font-size: 14px;
  line-height: 1.2;
}

.status-desc {
  font-size: 12px;
  color: var(--el-text-color-regular);
  line-height: 1.4;
}

.status-check {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--el-color-primary);
  color: white;
  font-size: 14px;
  margin-left: 8px;
  flex-shrink: 0;
}

/* 表单卡片样式优化 - 参考 RequestEditor 样式 */
.form-section {
  margin-bottom: 20px;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  overflow: hidden;
  transition: all 0.2s ease;
  background: #ffffff;
}

.form-section:hover {
  border-color: #d1d5db;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.form-section .el-card__header {
  background: #fafbfc;
  border-bottom: 1px solid #e2e8f0;
  padding: 16px 20px;
}

.form-section .el-card__body {
  padding: 20px;
  background: #fafbfc;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.section-header h3 {
  margin: 0;
  color: #374151;
  font-size: 15px;
  font-weight: 500;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px 20px;
  margin-bottom: 16px;
}

/* 表单项样式优化 - 参考 RequestEditor 样式 */
.form-section .el-form-item {
  margin-bottom: 20px;
}

.form-section .el-form-item__label {
  color: #374151;
  font-weight: 500;
  font-size: 14px;
  line-height: 1.4;
  margin-bottom: 8px;
}

.form-section .el-input__wrapper {
  border-radius: 6px;
  border: 1px solid #d1d5db;
  transition: all 0.2s ease;
}

.form-section .el-input__wrapper:hover {
  border-color: #9ca3af;
}

.form-section .el-input__wrapper.is-focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.form-section .el-textarea__inner {
  border-radius: 6px;
  border: 1px solid #d1d5db;
  transition: all 0.2s ease;
}

.form-section .el-textarea__inner:hover {
  border-color: #9ca3af;
}

.form-section .el-textarea__inner:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

/* 选择器样式优化 */
.form-section .el-select .el-input__wrapper {
  border-radius: 6px;
  border: 1px solid #d1d5db;
}

.form-section .el-select .el-input__wrapper:hover {
  border-color: #9ca3af;
}

.form-section .el-select .el-input__wrapper.is-focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.empty-state {
  padding: 40px 0;
}

.preconditions-list {
  margin-top: 16px;
}

.precondition-item {
  margin-bottom: 16px;
}

.precondition-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.title-text {
  font-weight: bold;
  font-size: 16px;
  color: #653ebb;
}

.title-actions {
  display: flex;
  gap: 8px;
}

.precondition-content {
  padding: 16px 0;
}

.extract-variables {
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  padding: 16px;
  width: 100%;
}

.extract-item {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.extract-item:last-child {
  margin-bottom: 0;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .form-grid {
    grid-template-columns: 1fr;
    gap: 12px;
  }
  
  .status-selector-compact {
    justify-content: flex-start;
  }
  
  .status-cards-container {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .page-header {
    padding: 16px 20px;
  }
  
  .header-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .page-content {
    padding: 16px 20px;
  }
  
  .form-section .el-card__header {
    padding: 12px 16px;
  }
  
  .form-section .el-card__body {
    padding: 16px;
  }
  
  .form-grid {
    gap: 10px;
  }
  
  .status-option {
    min-width: 70px;
    padding: 6px 10px;
  }
  
  .status-text {
    font-size: 12px;
  }
  
  .extract-item {
    padding: 12px;
  }
}
</style>