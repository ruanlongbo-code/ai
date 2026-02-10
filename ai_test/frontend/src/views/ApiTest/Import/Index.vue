<template>
  <div class="api-import-page">
    <div class="page-header">
      <h2>接口导入</h2>
      <p class="subtitle">支持Swagger、OpenAPI等多种文档导入</p>
    </div>

    <div class="page-content">
      <!-- 导入方式选择卡片 -->
      <div class="import-methods">
        <div class="import-card swagger-card" @click="handleSwaggerImport">
          <div class="card-icon">
            <el-icon><Document /></el-icon>
          </div>
          <div class="card-content">
            <h3>Swagger 2.0</h3>
            <p>导入 Swagger 2.0 格式文档</p>
            <div class="file-types">
              <el-tag size="small">JSON 格式</el-tag>
              <el-tag size="small">YAML 格式</el-tag>
              <el-tag size="small">在线链接</el-tag>
            </div>
          </div>
          <el-button type="primary" class="import-btn">
            一键导入 Swagger
          </el-button>
        </div>

        <div class="import-card openapi-card" @click="handleOpenApiImport">
          <div class="card-icon">
            <el-icon><Files /></el-icon>
          </div>
          <div class="card-content">
            <h3>OpenAPI 3.x</h3>
            <p>导入 OpenAPI 3.x 格式文档</p>
            <div class="file-types">
              <el-tag size="small" type="success">JSON 格式</el-tag>
              <el-tag size="small" type="success">YAML 格式</el-tag>
              <el-tag size="small" type="success">在线链接</el-tag>
            </div>
          </div>
          <el-button type="success" class="import-btn">
            一键导入 OpenAPI
          </el-button>
        </div>

        <div class="import-card ai-card" @click="handleAiImport">
          <div class="card-icon">
            <el-icon><MagicStick /></el-icon>
          </div>
          <div class="card-content">
            <h3>AI 智能识别</h3>
            <p>智能解析接口文档描述文本</p>
            <div class="file-types">
              <el-tag size="small" type="warning">文本描述</el-tag>
              <el-tag size="small" type="warning">自然语言</el-tag>
              <el-tag size="small" type="warning">文档片段</el-tag>
            </div>
          </div>
          <el-button type="warning" class="import-btn">
            AI 智能导入
          </el-button>
        </div>
      </div>

      <!-- 使用说明卡片 -->
      <el-card class="usage-guide">
        <template #header>
          <div class="section-header">
            <el-icon><InfoFilled /></el-icon>
            <span>使用说明</span>
            <span class="subtitle">详细的导入操作指南</span>
          </div>
        </template>
        
        <div class="usage-content">
          <div class="usage-section">
            <div class="usage-header">
              <el-icon class="usage-icon swagger-icon"><Document /></el-icon>
              <h4>Swagger 2.0 导入</h4>
            </div>
            <div class="usage-steps">
              <div class="step-item">
                <span class="step-number">1</span>
                <span class="step-text">点击"一键导入 Swagger"按钮</span>
              </div>
              <div class="step-item">
                <span class="step-number">2</span>
                <span class="step-text">选择或拖拽 JSON/YAML 格式的 Swagger 文档</span>
              </div>
              <div class="step-item">
                <span class="step-number">3</span>
                <span class="step-text">确认文件信息后点击"确认导入"</span>
              </div>
            </div>
            <div class="usage-tips">
              <el-tag size="small" type="info">支持 Swagger 2.0 规范</el-tag>
              <el-tag size="small" type="info">文件大小限制 10MB</el-tag>
            </div>
          </div>

          <div class="usage-section">
            <div class="usage-header">
              <el-icon class="usage-icon openapi-icon"><Files /></el-icon>
              <h4>OpenAPI 3.x 导入</h4>
            </div>
            <div class="usage-steps">
              <div class="step-item">
                <span class="step-number">1</span>
                <span class="step-text">点击"一键导入 OpenAPI"按钮</span>
              </div>
              <div class="step-item">
                <span class="step-number">2</span>
                <span class="step-text">选择或拖拽 JSON/YAML 格式的 OpenAPI 文档</span>
              </div>
              <div class="step-item">
                <span class="step-number">3</span>
                <span class="step-text">系统自动解析并导入接口信息</span>
              </div>
            </div>
            <div class="usage-tips">
              <el-tag size="small" type="success">支持 OpenAPI 3.0+ 规范</el-tag>
              <el-tag size="small" type="success">更完善的数据结构</el-tag>
            </div>
          </div>

          <div class="usage-section">
            <div class="usage-header">
              <el-icon class="usage-icon ai-icon"><MagicStick /></el-icon>
              <h4>AI 智能识别</h4>
            </div>
            <div class="usage-steps">
              <div class="step-item">
                <span class="step-number">1</span>
                <span class="step-text">点击"AI 智能导入"按钮</span>
              </div>
              <div class="step-item">
                <span class="step-number">2</span>
                <span class="step-text">在文本框中输入接口文档描述</span>
              </div>
              <div class="step-item">
                <span class="step-number">3</span>
                <span class="step-text">AI 自动解析并生成标准接口定义</span>
              </div>
            </div>
            <div class="usage-tips">
              <el-tag size="small" type="warning">支持自然语言描述</el-tag>
              <el-tag size="small" type="warning">智能识别接口参数</el-tag>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 最近导入记录 -->
      <el-card class="recent-imports" v-if="recentImports.length > 0">
        <template #header>
          <div class="section-header">
            <span>最近导入</span>
            <span class="subtitle">最近导入的接口文档记录</span>
            <el-button text @click="clearHistory">清空</el-button>
          </div>
        </template>
        
        <el-table :data="recentImports" style="width: 100%">
          <el-table-column prop="importTime" label="导入时间" width="180">
            <template #default="scope">
              {{ formatTime(scope.row.importTime) }}
            </template>
          </el-table-column>
          <el-table-column prop="docType" label="文档类型" width="120">
            <template #default="scope">
              <el-tag :type="getDocTypeColor(scope.row.docType)">
                {{ scope.row.docType }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="fileName" label="文件名称" />
          <el-table-column prop="status" label="导入状态" width="100">
            <template #default="scope">
              <el-tag :type="scope.row.status === '成功' ? 'success' : 'danger'">
                {{ scope.row.status }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="importCount" label="导入数量" width="100">
            <template #default="scope">
              <span class="import-count">{{ scope.row.importCount }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120">
            <template #default="scope">
              <el-button link type="primary" @click="viewDetails(scope.row)">
                查看详情
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <!-- 导入明细 -->
      <el-card class="import-details" v-if="importDetails.length > 0">
        <template #header>
          <div class="section-header">
            <span>导入明细</span>
            <span class="subtitle">共导入接口 {{ totalImported }} 个</span>
          </div>
        </template>
        
        <el-table :data="paginatedDetails" style="width: 100%">
          <el-table-column prop="method" label="请求方法" width="100">
            <template #default="scope">
              <el-tag :type="getMethodColor(scope.row.method)">
                {{ scope.row.method }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="path" label="接口路径" />
          <el-table-column prop="summary" label="接口描述" />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="scope">
              <el-tag :type="scope.row.status === '成功' ? 'success' : 'danger'">
                {{ scope.row.status }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
        
        <div class="pagination-container">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :page-sizes="[10, 20, 50, 100]"
            :total="importDetails.length"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
          />
        </div>
      </el-card>
    </div>

    <!-- 文件上传对话框 -->
    <el-dialog
      v-model="uploadDialogVisible"
      :title="uploadDialogTitle"
      width="600px"
      @close="resetUploadDialog"
    >
      <div class="upload-container">
        <el-upload
          ref="uploadRef"
          class="upload-dragger"
          drag
          :auto-upload="false"
          :on-change="handleFileChange"
          :before-upload="beforeUpload"
          accept=".json,.yaml,.yml"
          :limit="1"
        >
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text">
            将文件拖到此处，或<em>点击上传</em>
          </div>
          <template #tip>
            <div class="el-upload__tip">
              只能上传 JSON/YAML 文件，且不超过 10MB
            </div>
          </template>
        </el-upload>
        
        <div v-if="selectedFile" class="file-info">
          <h4>文件信息</h4>
          <p><strong>文件名：</strong>{{ selectedFile.name }}</p>
          <p><strong>文件大小：</strong>{{ formatFileSize(selectedFile.size) }}</p>
          <p><strong>文件类型：</strong>{{ selectedFile.type || '未知' }}</p>
        </div>
      </div>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="uploadDialogVisible = false">取消</el-button>
          <el-button 
            type="primary" 
            @click="confirmUpload"
            :loading="uploading"
            :disabled="!selectedFile"
          >
            {{ uploading ? '导入中...' : '确认导入' }}
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- AI 解析对话框 -->
    <el-dialog
      v-model="aiDialogVisible"
      title="AI 智能解析"
      width="800px"
      @close="resetAiDialog"
    >
      <div class="ai-parse-container">
        <el-form :model="aiForm" label-width="100px">
          <el-form-item label="接口文档">
            <el-input
              v-model="aiForm.apiDocument"
              type="textarea"
              :rows="10"
              placeholder="请输入接口文档的文字描述内容，支持自然语言描述..."
              show-word-limit
              maxlength="5000"
            />
          </el-form-item>
        </el-form>
      </div>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="aiDialogVisible = false">取消</el-button>
          <el-button 
            type="warning" 
            @click="confirmAiParse"
            :loading="aiParsing"
            :disabled="!aiForm.apiDocument.trim()"
          >
            {{ aiParsing ? 'AI解析中...' : '开始解析' }}
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- AI 解析结果对话框已移除，直接使用接口表单弹框 -->

    <!-- 接口表单弹框 -->
    <el-dialog
      v-model="interfaceFormVisible"
      title="AI解析的接口信息"
      width="80%"
      :close-on-click-modal="false"
    >
      <InterfaceForm
        :model-value="interfaceFormData"
        mode="create"
        @submit="handleInterfaceFormSubmit"
        @cancel="handleInterfaceFormCancel"
      />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Document, Files, MagicStick, UploadFilled, InfoFilled } from '@element-plus/icons-vue'
import { useRouter, useRoute } from 'vue-router'
import { useProjectStore } from '@/stores'
import { importSwaggerApis, importOpenApiApis, aiParseApiDocument, createApiInterface } from '@/api/apiTest'
import InterfaceForm from '../Management/components/InterfaceForm.vue'

const router = useRouter()
const route = useRoute()
const projectStore = useProjectStore()

// 获取项目ID的函数
const getProjectId = () => {
  // 优先从 Pinia store 获取
  if (projectStore.currentProject?.id) {
    return projectStore.currentProject.id
  }
  
  // 其次从路由参数获取
  if (route.params.projectId) {
    return parseInt(route.params.projectId)
  }
  
  // 最后从查询参数获取
  if (route.query.projectId) {
    return parseInt(route.query.projectId)
  }
  
  return null
}

// 响应式数据
const uploadDialogVisible = ref(false)
const uploadDialogTitle = ref('')
const aiDialogVisible = ref(false)
const interfaceFormVisible = ref(false)  // 新增：接口表单弹框显示状态
const selectedFile = ref(null)
const uploading = ref(false)
const aiParsing = ref(false)
const currentImportType = ref('')
const aiParseResult = ref(null)
const interfaceFormData = ref(null)  // 新增：接口表单数据

// 表格数据
const recentImports = ref([])
const importDetails = ref([])
const currentPage = ref(1)
const pageSize = ref(10)

// AI 表单
const aiForm = ref({
  apiDocument: ''
})

// 计算属性
const totalImported = computed(() => importDetails.value.length)
const paginatedDetails = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return importDetails.value.slice(start, end)
})

// 生命周期
onMounted(() => {
  loadRecentImports()
})

// 导入方式处理函数
const handleSwaggerImport = () => {
  currentImportType.value = 'swagger'
  uploadDialogTitle.value = 'Swagger 2.0 文档导入'
  uploadDialogVisible.value = true
}

const handleOpenApiImport = () => {
  currentImportType.value = 'openapi'
  uploadDialogTitle.value = 'OpenAPI 3.x 文档导入'
  uploadDialogVisible.value = true
}

const handleAiImport = () => {
  aiDialogVisible.value = true
}

// 文件上传处理
const handleFileChange = (file) => {
  selectedFile.value = file.raw
}

const beforeUpload = (file) => {
  const isValidType = file.type === 'application/json' || 
                     file.name.endsWith('.json') || 
                     file.name.endsWith('.yaml') || 
                     file.name.endsWith('.yml')
  
  if (!isValidType) {
    ElMessage.error('只能上传 JSON 或 YAML 格式的文件!')
    return false
  }
  
  const isLt10M = file.size / 1024 / 1024 < 10
  if (!isLt10M) {
    ElMessage.error('上传文件大小不能超过 10MB!')
    return false
  }
  
  return false // 阻止自动上传
}

const confirmUpload = async () => {
  console.log('confirmUpload 函数被调用')
  
  if (!selectedFile.value) {
    ElMessage.warning('请先选择文件')
    return
  }
  
  console.log('开始上传文件:', selectedFile.value.name)
  uploading.value = true
  
  try {
    // 获取当前项目ID
    const projectId = getProjectId()
    console.log('获取到项目ID:', projectId)
    
    if (!projectId) {
      ElMessage.error('无法获取项目ID，请刷新页面重试')
      uploading.value = false
      return
    }
    
    console.log('准备调用API，导入类型:', currentImportType.value)
    
    let response
    if (currentImportType.value === 'swagger') {
      response = await importSwaggerApis(projectId, selectedFile.value)
    } else {
      response = await importOpenApiApis(projectId, selectedFile.value)
    }
    
    console.log('API响应:', response)
    
    // 从axios响应中获取实际数据
    const result = response.data
    console.log('解析后的结果:', result)
    
    if (result.success) {
      ElMessage.success(result.message)
      
      // 添加到最近导入记录
      const importRecord = {
        id: `import_${Date.now()}`,
        importTime: new Date(),
        docType: currentImportType.value === 'swagger' ? 'Swagger' : 'OpenAPI',
        fileName: selectedFile.value.name,
        status: '成功',
        importCount: result.imported_count
      }
      recentImports.value.unshift(importRecord)
      
      // 保存到本地存储
      saveRecentImports()
      
      // 关闭对话框
      uploadDialogVisible.value = false
      
      // 延迟重置对话框，确保状态更新完成
      setTimeout(() => {
        resetUploadDialog()
      }, 100)
      
    } else {
      ElMessage.error(result.message || '导入失败')
    }
    
  } catch (error) {
    console.error('导入失败:', error)
    ElMessage.error('导入失败，请检查网络连接')
  } finally {
    uploading.value = false
    console.log('上传状态重置完成')
  }
}

// AI 解析处理
const confirmAiParse = async () => {
  if (!aiForm.value.apiDocument.trim()) {
    ElMessage.warning('请输入接口文档描述')
    return
  }
  
  aiParsing.value = true
  
  try {
    // 获取当前项目ID
    const projectId = getProjectId()
    if (!projectId) {
      ElMessage.error('无法获取项目ID，请刷新页面重试')
      aiParsing.value = false
      return
    }
    
    console.log('AI解析开始，项目ID:', projectId)
    console.log('API文档内容:', aiForm.value.apiDocument)
    
    const response = await aiParseApiDocument(projectId, aiForm.value.apiDocument)
    console.log('AI解析响应:', response)
    
    // 从axios响应中获取实际数据
    const result = response.data
    console.log('AI解析结果:', result)
    
    if (result.success) {
      ElMessage.success(result.message)
      
      // 保存解析结果
      aiParseResult.value = result
      
      // 添加到最近导入记录
      const importRecord = {
        id: `ai_parse_${Date.now()}`,
        importTime: new Date(),
        docType: 'AI解析',
        fileName: '文本描述',
        status: '成功',
        importCount: result.parsed_data ? 1 : 0
      }
      recentImports.value.unshift(importRecord)
      
      // 保存到本地存储
      saveRecentImports()
      
      // 关闭AI解析对话框，直接弹出接口表单
      aiDialogVisible.value = false
      
      // 转换AI解析结果为接口表单数据格式
      interfaceFormData.value = convertAiResultToInterfaceData(result.parsed_data)
      interfaceFormVisible.value = true
      
      resetAiDialog()
      
    } else {
      ElMessage.error(result.message || 'AI解析失败')
    }
    
  } catch (error) {
    console.error('AI解析失败:', error)
    ElMessage.error('AI解析失败，请检查网络连接')
  } finally {
    aiParsing.value = false
  }
}

// 重置对话框
const resetUploadDialog = () => {
  selectedFile.value = null
  currentImportType.value = ''
}

const resetAiDialog = () => {
  aiForm.value.apiDocument = ''
  aiParsing.value = false
}

// 清理不再需要的方法，因为现在直接使用接口表单弹框

// 将AI解析结果转换为接口表单数据格式
const convertAiResultToInterfaceData = (parsedData) => {
  if (!parsedData) return null
  
  // 处理参数数据，将不同类型的参数分别提取
  const parameters = []
  if (parsedData.parameters) {
    // 路径参数
    if (parsedData.parameters.path && Array.isArray(parsedData.parameters.path)) {
      parameters.push(...parsedData.parameters.path.map(param => ({
        ...param,
        in: 'path'
      })))
    }
    
    // 查询参数
    if (parsedData.parameters.query && Array.isArray(parsedData.parameters.query)) {
      parameters.push(...parsedData.parameters.query.map(param => ({
        ...param,
        in: 'query'
      })))
    }
    
    // 请求头参数
    if (parsedData.parameters.header && Array.isArray(parsedData.parameters.header)) {
      parameters.push(...parsedData.parameters.header.map(param => ({
        ...param,
        in: 'header'
      })))
    }
  }
  
  return {
    method: parsedData.method || 'GET',
    path: parsedData.path || '',
    summary: parsedData.summary || '',
    description: parsedData.summary || '',
    parameters: parameters,
    requestBody: {
      content_type: parsedData.requestBody?.content_type || 'application/json',
      body: parsedData.requestBody?.body || []
    },
    responses: Array.isArray(parsedData.responses) ? parsedData.responses : [parsedData.responses].filter(Boolean)
  }
}

// 工具函数
const formatTime = (time) => {
  return new Date(time).toLocaleString('zh-CN')
}

const formatFileSize = (size) => {
  if (size < 1024) return size + ' B'
  if (size < 1024 * 1024) return (size / 1024).toFixed(1) + ' KB'
  return (size / 1024 / 1024).toFixed(1) + ' MB'
}

const getDocTypeColor = (type) => {
  const colors = {
    'Swagger': '',
    'OpenAPI': 'success',
    'AI解析': 'warning'
  }
  return colors[type] || ''
}

const getMethodColor = (method) => {
  const colors = {
    'GET': 'success',
    'POST': 'primary',
    'PUT': 'warning',
    'DELETE': 'danger',
    'PATCH': 'info'
  }
  return colors[method] || ''
}

// 表格操作
const handleSizeChange = (val) => {
  pageSize.value = val
  currentPage.value = 1
}

const handleCurrentChange = (val) => {
  currentPage.value = val
}

const viewDetails = (row) => {
  ElMessage.info(`查看 ${row.fileName} 的导入详情`)
}

const clearHistory = async () => {
  try {
    await ElMessageBox.confirm('确定要清空所有导入记录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    recentImports.value = []
    importDetails.value = []
    localStorage.removeItem('api_import_history')
    ElMessage.success('清空成功')
    
  } catch {
    // 用户取消
  }
}

// 本地存储
const loadRecentImports = () => {
  try {
    const saved = localStorage.getItem('api_import_history')
    if (saved) {
      const data = JSON.parse(saved)
      recentImports.value = data.recentImports || []
      importDetails.value = data.importDetails || []
    }
  } catch (error) {
    console.error('加载历史记录失败:', error)
  }
}

const saveRecentImports = () => {
  try {
    const data = {
      recentImports: recentImports.value.slice(0, 50), // 只保存最近50条
      importDetails: importDetails.value.slice(0, 500) // 只保存最近500条
    }
    localStorage.setItem('api_import_history', JSON.stringify(data))
  } catch (error) {
    console.error('保存历史记录失败:', error)
  }
}

// 处理InterfaceForm提交
const handleInterfaceFormSubmit = async (formData) => {
  try {
    const projectId = getProjectId()
    if (!projectId) {
      ElMessage.error('请先选择项目')
      return
    }

    // 转换数据格式以匹配后端schema
    const apiData = {
      method: formData.method || 'GET',
      path: formData.path || '/',
      summary: formData.summary || '',
      parameters: formData.parameters || {},
      request_body: formData.request_body || formData.requestBody || {},
      responses: formData.responses || []
    }

    console.log('提交接口数据:', apiData)
    
    await createApiInterface(projectId, apiData)
    ElMessage.success('接口保存成功')
    interfaceFormVisible.value = false
    
    // 添加到导入历史记录
    const importRecord = {
      id: Date.now(),
      fileName: formData.summary || formData.name || '未命名接口',
      fileSize: 0,
      docType: 'AI解析',
      importTime: new Date().toISOString(),
      status: 'success',
      interfaceCount: 1,
      successCount: 1,
      failCount: 0
    }
    
    recentImports.value.unshift(importRecord)
    importDetails.value.unshift({
      id: Date.now(),
      name: formData.summary || formData.name || '未命名接口',
      method: formData.method || 'GET',
      path: formData.path || '/',
      status: 'success',
      message: '导入成功'
    })
    
    saveRecentImports()
    
  } catch (error) {
    console.error('保存接口失败:', error)
    ElMessage.error('保存接口失败: ' + (error.message || '未知错误'))
  }
}

// 处理InterfaceForm取消
const handleInterfaceFormCancel = () => {
  interfaceFormVisible.value = false
}
</script>

<style scoped>
.api-import-page {
  padding: 20px;
  background: #f5f7fa;
  min-height: 100vh;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h2 {
  color: #303133;
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
}

.subtitle {
  color: #606266;
  margin: 0;
  font-size: 14px;
}

.page-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* 导入方式卡片 */
.import-methods {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
  margin-bottom: 24px;
}

.import-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: all 0.3s ease;
  border: 2px solid transparent;
  position: relative;
  overflow: hidden;
}

.import-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px 0 rgba(0, 0, 0, 0.15);
}

.swagger-card {
  border-left: 4px solid #1890ff;
}

.swagger-card:hover {
  border-color: #1890ff;
  background: linear-gradient(135deg, #f0f8ff 0%, #ffffff 100%);
}

.openapi-card {
  border-left: 4px solid #52c41a;
}

.openapi-card:hover {
  border-color: #52c41a;
  background: linear-gradient(135deg, #f6ffed 0%, #ffffff 100%);
}

.ai-card {
  border-left: 4px solid #faad14;
}

.ai-card:hover {
  border-color: #faad14;
  background: linear-gradient(135deg, #fffbe6 0%, #ffffff 100%);
}

.card-icon {
  font-size: 32px;
  margin-bottom: 16px;
  color: #1890ff;
}

.openapi-card .card-icon {
  color: #52c41a;
}

.ai-card .card-icon {
  color: #faad14;
}

.card-content h3 {
  margin: 0 0 8px 0;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.card-content p {
  margin: 0 0 16px 0;
  color: #606266;
  font-size: 14px;
  line-height: 1.5;
}

.file-types {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 20px;
}

.import-btn {
  width: 100%;
  height: 40px;
  font-weight: 500;
}

/* 使用说明卡片样式 */
.usage-guide {
  margin: 24px 0;
  border: none;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  border-radius: 12px;
}

.usage-content {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 24px;
  padding: 8px 0;
}

.usage-section {
  padding: 20px;
  background: #fafbfc;
  border-radius: 8px;
  border-left: 4px solid #e4e7ed;
}

.usage-section:nth-child(1) {
  border-left-color: #1890ff;
}

.usage-section:nth-child(2) {
  border-left-color: #52c41a;
}

.usage-section:nth-child(3) {
  border-left-color: #faad14;
}

.usage-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}

.usage-icon {
  font-size: 20px;
}

.swagger-icon {
  color: #1890ff;
}

.openapi-icon {
  color: #52c41a;
}

.ai-icon {
  color: #faad14;
}

.usage-header h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.usage-steps {
  margin-bottom: 16px;
}

.step-item {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  padding: 8px 0;
}

.step-number {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  background: #1890ff;
  color: white;
  border-radius: 50%;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}

.usage-section:nth-child(2) .step-number {
  background: #52c41a;
}

.usage-section:nth-child(3) .step-number {
  background: #faad14;
}

.step-text {
  color: #606266;
  font-size: 14px;
  line-height: 1.5;
}

.usage-tips {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

/* 卡片和表格样式 */
.recent-imports,
.import-details {
  border: none;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  border-radius: 12px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.section-header span:first-child {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.section-header .subtitle {
  font-size: 12px;
  color: #909399;
}

.import-count {
  font-weight: 600;
  color: #1890ff;
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

/* 对话框样式 */
.upload-container {
  padding: 20px 0;
}

.upload-dragger {
  width: 100%;
}

.file-info {
  margin-top: 20px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
}

.file-info h4 {
  margin: 0 0 12px 0;
  color: #303133;
}

.file-info p {
  margin: 8px 0;
  color: #606266;
}

.ai-parse-container {
  padding: 20px 0;
}

.dialog-footer {
  display: flex;
  gap: 12px;
}

.empty-params {
  padding: 20px;
  text-align: center;
}

.response-detail {
  padding: 10px 0;
}

.response-detail p {
  margin: 8px 0;
}

.ai-result-container {
  max-height: 70vh;
  overflow-y: auto;
}

.param-section h4,
.response-section h4 {
  margin: 0 0 15px 0;
  color: #303133;
  font-weight: 600;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .import-methods {
    grid-template-columns: 1fr;
  }
  
  .api-import-page {
    padding: 16px;
  }
  
  .import-card {
    padding: 20px;
  }
}

@media (max-width: 1200px) {
  .import-methods {
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  }
}
</style>