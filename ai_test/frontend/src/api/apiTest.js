import request from '@/utils/request'

// 获取项目接口列表
export function getProjectInterfaces(projectId, params = {}) {
  return request({
    url: `/api_test/${projectId}/interfaces`,
    method: 'get',
    params: {
      page: params.page || 1,
      page_size: params.page_size || 20,
      search: params.search || '',
      method: params.method || '',
      module: params.module || ''
    }
  })
}

// 新增接口
export function createApiInterface(projectId, data) {
  return request({
    url: `/api_test/${projectId}/interfaces`,
    method: 'post',
    data
  })
}

// 编辑接口
export function updateApiInterface(projectId, interfaceId, data) {
  return request({
    url: `/api_test/${projectId}/interfaces/${interfaceId}`,
    method: 'put',
    data
  })
}

// 删除接口
export function deleteApiInterface(projectId, interfaceId) {
  return request({
    url: `/api_test/${projectId}/interfaces/${interfaceId}`,
    method: 'delete'
  })
}

// 获取接口详情
export function getInterfaceDetail(projectId, interfaceId) {
  return request({
    url: `/api_test/${projectId}/interfaces/${interfaceId}`,
    method: 'get'
  })
}

// 导入Swagger接口文档
export function importSwaggerApis(projectId, file) {
  const formData = new FormData()
  formData.append('swagger_file', file)
  return request({
    url: `/api_test/${projectId}/import_swagger`,
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

// 导入OpenAPI接口文档
export function importOpenApiApis(projectId, file) {
  const formData = new FormData()
  formData.append('openapi_file', file)
  return request({
    url: `/api_test/${projectId}/import_openapi`,
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

// AI解析接口文档
export function aiParseApiDocument(projectId, apiDocument) {
  return request({
    url: `/api_test/${projectId}/ai_parse`,
    method: 'post',
    timeout: 60000, // AI解析需要更长时间，设置为60秒
    data: {
      project_id: projectId,
      api_document: apiDocument
    }
  })
}

// 获取基础用例列表
export function getBasicCasesList(projectId, params = {}) {
  return request({
    url: `/api_test/${projectId}/base-cases`,
    method: 'get',
    params: {
      page: params.page || 1,
      page_size: params.page_size || 10,
      // 仅支持 interface_id 过滤，其它参数后端未实现
      interface_id: params.interface_id
    }
  })
}

// 删除基础用例
export function deleteBasicCase(projectId, caseId) {
  return request({
    url: `/api_test/${projectId}/base-cases/${caseId}`,
    method: 'delete'
  })
}

// 创建基础用例
export function createBasicCase(projectId, interfaceId, data) {
  return request({
    url: `/api_test/${projectId}/interfaces/${interfaceId}/base-cases`,
    method: 'post',
    data
  })
}

// 更新基础用例
export function updateBasicCase(projectId, baseCaseId, data) {
  return request({
    url: `/api_test/${projectId}/base-cases/${baseCaseId}`,
    method: 'put',
    data
  })
}

// 获取接口测试用例（自动化用例）列表
export function getApiTestCasesList(projectId, params = {}) {
  return request({
    url: `/api_test/${projectId}/test-cases`,
    method: 'get',
    params: {
      page: params.page || 1,
      page_size: params.page_size || 10,
      // 支持 interface_id 与 keyword 过滤
      interface_id: params.interface_id,
      keyword: params.keyword
    }
  })
}

// 获取接口测试用例详情
export function getApiTestCaseDetail(projectId, testCaseId) {
  return request({
    url: `/api_test/${projectId}/test-cases/${testCaseId}`,
    method: 'get'
  })
}

// 更新接口测试用例
export function updateApiTestCase(projectId, testCaseId, data) {
  return request({
    url: `/api_test/${projectId}/test-cases/${testCaseId}`,
    method: 'put',
    data
  })
}

// 运行单条测试用例
export function runSingleTestCase(projectId, data) {
  return request({
    url: `/test_execution/${projectId}/cases/run`,
    method: 'post',
    data: {
      case_id: data.case_id,
      environment_id: data.environment_id
    }
  })
}

// 获取测试环境列表
export function getTestEnvironments(projectId, params = {}) {
  return request({
    url: `/test_environment/${projectId}/environments`,
    method: 'get',
    params: {
      page: params.page || 1,
      page_size: params.page_size || 100  // 获取所有环境用于选择
    }
  })
}

// ==================== 接口依赖管理 ====================

// 获取接口依赖分组列表
export function getDependencyGroups(projectId, params = {}) {
  return request({
    url: `/api_test/${projectId}/dependency-groups`,
    method: 'get',
    params: {
      page: params.page || 1,
      page_size: params.page_size || 10,
      target_interface_id: params.target_interface_id
    }
  })
}

// 创建接口依赖分组
export function createDependencyGroup(projectId, data) {
  return request({
    url: `/api_test/${projectId}/dependency-groups`,
    method: 'post',
    data
  })
}

// 更新接口依赖分组
export function updateDependencyGroup(projectId, groupId, data) {
  return request({
    url: `/api_test/${projectId}/dependency-groups/${groupId}`,
    method: 'put',
    data
  })
}

// 删除接口依赖分组
export function deleteDependencyGroup(projectId, groupId) {
  return request({
    url: `/api_test/${projectId}/dependency-groups/${groupId}`,
    method: 'delete'
  })
}

// 创建接口依赖
export function createDependency(projectId, groupId, data) {
  return request({
    url: `/api_test/${projectId}/dependency-groups/${groupId}/dependencies`,
    method: 'post',
    data
  })
}

// 更新接口依赖
export function updateDependency(projectId, groupId, dependencyId, data) {
  return request({
    url: `/api_test/${projectId}/dependency-groups/${groupId}/dependencies/${dependencyId}`,
    method: 'put',
    data
  })
}

// 删除接口依赖
export function deleteDependency(projectId, groupId, dependencyId) {
  return request({
    url: `/api_test/${projectId}/dependency-groups/${groupId}/dependencies/${dependencyId}`,
    method: 'delete'
  })
}

// 自动化用例状态常量（根据后端模型定义）
export const API_CASE_STATUS = {
  PENDING: 'pending',
  READY: 'ready',
  DISABLED: 'disabled'
}

// 自动化用例状态标签映射
export const API_CASE_STATUS_LABELS = {
  [API_CASE_STATUS.PENDING]: '待审核',
  [API_CASE_STATUS.READY]: '可执行',
  [API_CASE_STATUS.DISABLED]: '不可执行'
}

// 自动化用例状态颜色映射
export const API_CASE_STATUS_COLORS = {
  [API_CASE_STATUS.PENDING]: '#E6A23C',    // 橙色 - 待审核
  [API_CASE_STATUS.READY]: '#67C23A',      // 绿色 - 可执行
  [API_CASE_STATUS.DISABLED]: '#F56C6C'    // 红色 - 不可执行
}

// 自动化用例状态类型映射（用于Element Plus Tag组件）
export const API_CASE_STATUS_TYPES = {
  [API_CASE_STATUS.PENDING]: 'warning',    // 橙色
  [API_CASE_STATUS.READY]: 'success',      // 绿色
  [API_CASE_STATUS.DISABLED]: 'danger'     // 红色
}

// ==================== Phase 1: 快捷调试 ====================

// 快捷调试 - 发送请求
export function quickDebugSend(projectId, data) {
  return request({
    url: `/api_test/${projectId}/quick-debug/send`,
    method: 'post',
    timeout: 60000,
    data
  })
}

// 快捷调试 - 获取请求历史列表
export function getQuickDebugHistory(projectId, params = {}) {
  return request({
    url: `/api_test/${projectId}/quick-debug/history`,
    method: 'get',
    params: {
      page: params.page || 1,
      page_size: params.page_size || 20,
      method: params.method,
      keyword: params.keyword
    }
  })
}

// 快捷调试 - 获取历史详情
export function getQuickDebugHistoryDetail(projectId, historyId) {
  return request({
    url: `/api_test/${projectId}/quick-debug/history/${historyId}`,
    method: 'get'
  })
}

// 快捷调试 - 删除历史记录
export function deleteQuickDebugHistory(projectId, historyId) {
  return request({
    url: `/api_test/${projectId}/quick-debug/history/${historyId}`,
    method: 'delete'
  })
}

// 快捷调试 - 清空历史记录
export function clearQuickDebugHistory(projectId) {
  return request({
    url: `/api_test/${projectId}/quick-debug/history`,
    method: 'delete'
  })
}

// 快捷调试 - 解析cURL
export function parseCurlCommand(projectId, curlCommand) {
  return request({
    url: `/api_test/${projectId}/quick-debug/parse-curl`,
    method: 'post',
    data: { curl_command: curlCommand }
  })
}

// 快捷调试 - 导出为cURL
export function exportAsCurl(projectId, data) {
  return request({
    url: `/api_test/${projectId}/quick-debug/export-curl`,
    method: 'post',
    data
  })
}

// 快捷调试 - 保存为接口
export function saveDebugAsInterface(projectId, data) {
  return request({
    url: `/api_test/${projectId}/quick-debug/save-as-interface`,
    method: 'post',
    data
  })
}

// ==================== Phase 2: 定时任务 / CI触发 ====================

// 创建定时任务
export function createScheduledTask(projectId, data) {
  return request({
    url: `/api_test/${projectId}/scheduled-tasks`,
    method: 'post',
    data
  })
}

// 获取定时任务列表
export function getScheduledTasks(projectId, params = {}) {
  return request({
    url: `/api_test/${projectId}/scheduled-tasks`,
    method: 'get',
    params: {
      page: params.page || 1,
      page_size: params.page_size || 20
    }
  })
}

// 更新定时任务
export function updateScheduledTask(projectId, taskId, data) {
  return request({
    url: `/api_test/${projectId}/scheduled-tasks/${taskId}`,
    method: 'put',
    data
  })
}

// 删除定时任务
export function deleteScheduledTask(projectId, taskId) {
  return request({
    url: `/api_test/${projectId}/scheduled-tasks/${taskId}`,
    method: 'delete'
  })
}

// 触发定时任务执行
export function triggerScheduledTask(projectId, taskId) {
  return request({
    url: `/api_test/${projectId}/scheduled-tasks/${taskId}/trigger`,
    method: 'post'
  })
}

// CI Webhook触发执行
export function ciTriggerExecution(projectId, data) {
  return request({
    url: `/api_test/${projectId}/ci-trigger`,
    method: 'post',
    data
  })
}

// cURL导入为接口
export function curlImportAsInterface(projectId, data) {
  return request({
    url: `/api_test/${projectId}/curl-to-interface`,
    method: 'post',
    data
  })
}

// ==================== Phase 3: Webhook通知配置 ====================

// 创建Webhook通知配置
export function createWebhookConfig(projectId, data) {
  return request({
    url: `/api_test/${projectId}/webhook-configs`,
    method: 'post',
    data
  })
}

// 获取Webhook通知配置列表
export function getWebhookConfigs(projectId) {
  return request({
    url: `/api_test/${projectId}/webhook-configs`,
    method: 'get'
  })
}

// 更新Webhook通知配置
export function updateWebhookConfig(projectId, configId, data) {
  return request({
    url: `/api_test/${projectId}/webhook-configs/${configId}`,
    method: 'put',
    data
  })
}

// 删除Webhook通知配置
export function deleteWebhookConfig(projectId, configId) {
  return request({
    url: `/api_test/${projectId}/webhook-configs/${configId}`,
    method: 'delete'
  })
}

// 测试Webhook连通性
export function testWebhookConfig(projectId, configId) {
  return request({
    url: `/api_test/${projectId}/webhook-configs/${configId}/test`,
    method: 'post'
  })
}

// 获取增强执行报告
export function getEnhancedExecutionReport(projectId, runId) {
  return request({
    url: `/api_test/${projectId}/execution-report/${runId}`,
    method: 'get'
  })
}