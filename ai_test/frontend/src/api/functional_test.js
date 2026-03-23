/**
 * 功能测试需求管理API接口
 */
import request from '@/utils/request'

/**
 * 创建需求
 * @param {number} projectId - 项目ID
 * @param {Object} data - 需求数据
 * @param {number} data.module_id - 项目模块ID
 * @param {string} data.title - 需求标题 (1-200字符)
 * @param {string} [data.description] - 需求描述
 * @param {number} data.priority - 优先级 (1=低, 2=中, 3=高)
 */
export const createRequirement = (projectId, data) => {
  return request({
    url: `/functional_test/requirements`,
    method: 'post',
    params: { project_id: projectId },
    data
  })
}

/**
 * 获取需求列表（按模块分组）
 * @param {number} projectId - 项目ID
 * @param {Object} params - 查询参数
 * @param {number} [params.module_id] - 模块ID筛选
 * @param {string} [params.status] - 状态筛选
 * @param {number} [params.priority] - 优先级筛选
 * @param {string} [params.keyword] - 关键词搜索
 */
export const getRequirementsList = (projectId, params = {}) => {
  return request({
    url: `/functional_test/${projectId}/requirements`,
    method: 'get',
    params
  })
}



/**
 * 获取需求详情
 * @param {number} projectId - 项目ID
 * @param {number} requirementId - 需求ID
 */
export const getRequirementDetail = (projectId, requirementId) => {
  return request({
    url: `/functional_test/${projectId}/requirements/${requirementId}`,
    method: 'get'
  })
}

/**
 * 更新需求
 * @param {number} projectId - 项目ID
 * @param {number} requirementId - 需求ID
 * @param {Object} data - 需求更新数据
 * @param {string} data.title - 需求标题
 * @param {string} [data.description] - 需求描述
 * @param {number} data.priority - 优先级 (1-5)
 * @param {string} data.status - 状态
 */
export const updateRequirement = (projectId, requirementId, data) => {
  return request({
    url: `/functional_test/${projectId}/requirements/${requirementId}`,
    method: 'put',
    data
  })
}

/**
 * 删除需求
 * @param {number} projectId - 项目ID
 * @param {number} requirementId - 需求ID
 */
export const deleteRequirement = (projectId, requirementId) => {
  return request({
    url: `/functional_test/${projectId}/requirements/${requirementId}`,
    method: 'delete'
  })
}

/**
 * 获取功能用例列表
 * @param {number} projectId - 项目ID
 * @param {Object} params - 查询参数
 * @param {number} [params.page=1] - 页码
 * @param {number} [params.page_size=10] - 每页数量
 * @param {number} [params.requirement_id] - 需求ID筛选
 * @param {string} [params.keyword] - 关键词搜索
 */
export const getFunctionalCasesList = (projectId, params = {}) => {
  return request({
    url: `/functional_test/${projectId}/functional_cases`,
    method: 'get',
    params
  })
}

/**
 * 获取功能用例详情
 * @param {number} projectId - 项目ID
 * @param {number} caseId - 用例ID
 */
export const getFunctionalCaseDetail = (projectId, caseId) => {
  return request({
    url: `/functional_test/${projectId}/functional_cases/${caseId}`,
    method: 'get'
  })
}

/**
 * 基于需求生成功能用例
 * @param {number} projectId - 项目ID
 * @param {number} requirementId - 需求ID
 * @param {Object} data - 生成参数
 * @param {number} [data.case_count=5] - 生成用例数量
 */
export const generateFunctionalCases = (projectId, requirementId, data = {}) => {
  return request({
    url: `/functional_test/${projectId}/requirements/${requirementId}/generate_cases`,
    method: 'post',
    data: {
      case_count: 5,
      ...data
    }
  })
}

// 需求状态常量
export const REQUIREMENT_STATUS = {
  DRAFT: 'draft',
  REVIEWING: 'reviewing', 
  APPROVED: 'approved',
  REJECTED: 'rejected',
  CHANGED: 'changed'
}

// 需求状态标签映射
export const REQUIREMENT_STATUS_LABELS = {
  [REQUIREMENT_STATUS.DRAFT]: '草稿',
  [REQUIREMENT_STATUS.REVIEWING]: '已确认',
  [REQUIREMENT_STATUS.APPROVED]: '待完善',
  [REQUIREMENT_STATUS.REJECTED]: '完成',
  [REQUIREMENT_STATUS.CHANGED]: '废弃'
}

// 优先级常量
export const REQUIREMENT_PRIORITY = {
  LOW: 1,
  MEDIUM: 2,
  HIGH: 3,
  URGENT: 4
}

// 优先级标签映射
export const REQUIREMENT_PRIORITY_LABELS = {
  [REQUIREMENT_PRIORITY.LOW]: '低',
  [REQUIREMENT_PRIORITY.MEDIUM]: '中',
  [REQUIREMENT_PRIORITY.HIGH]: '高',
  [REQUIREMENT_PRIORITY.URGENT]: '紧急'
}

// 优先级颜色映射
export const REQUIREMENT_PRIORITY_COLORS = {
  [REQUIREMENT_PRIORITY.LOW]: '#909399',
  [REQUIREMENT_PRIORITY.MEDIUM]: '#E6A23C',
  [REQUIREMENT_PRIORITY.HIGH]: '#F56C6C',
  [REQUIREMENT_PRIORITY.URGENT]: '#F56C6C'
}

// 状态颜色映射
export const REQUIREMENT_STATUS_COLORS = {
  [REQUIREMENT_STATUS.DRAFT]: '#909399',
  [REQUIREMENT_STATUS.REVIEWING]: '#E6A23C',
  [REQUIREMENT_STATUS.APPROVED]: '#67C23A',
  [REQUIREMENT_STATUS.REJECTED]: '#F56C6C',
  [REQUIREMENT_STATUS.CHANGED]: '#C0C4CC'
}

/**
 * 审核需求
 * @param {number} projectId - 项目ID
 * @param {number} requirementId - 需求ID
 * @param {Object} reviewData - 审核数据
 * @param {string} reviewData.status - 审核状态
 * @param {string} [reviewData.review_comment] - 审核意见
 */
export const reviewRequirement = (projectId, requirementId, reviewData) => {
  return request({
    url: `/functional_test/${projectId}/requirements/${requirementId}/review`,
    method: 'put',
    data: reviewData
  })
}

// 功能用例状态常量（根据后端模型定义）
export const CASE_STATUS = {
  DESIGN: 'design',
  PASS: 'pass',
  WAIT: 'wait',
  SMOKE: 'smoke',
  REGRESSION: 'regression',
  OBSOLETE: 'obsolete'
}

// 功能用例状态标签映射（根据后端模型定义）
export const CASE_STATUS_LABELS = {
  [CASE_STATUS.DESIGN]: '待审核',
  [CASE_STATUS.PASS]: '审核通过',
  [CASE_STATUS.WAIT]: '待执行',
  [CASE_STATUS.SMOKE]: '执行通过',
  [CASE_STATUS.REGRESSION]: '执行失败',
  [CASE_STATUS.OBSOLETE]: '已废弃'
}

// 功能用例优先级常量
export const CASE_PRIORITY = {
  P0: 1,
  P1: 2,
  P2: 3,
  P3: 4
}

// 功能用例优先级标签映射
export const CASE_PRIORITY_LABELS = {
  [CASE_PRIORITY.P0]: 'P0',
  [CASE_PRIORITY.P1]: 'P1',
  [CASE_PRIORITY.P2]: 'P2',
  [CASE_PRIORITY.P3]: 'P3'
}

/**
 * 创建功能用例
 * @param {number} projectId - 项目ID
 * @param {Object} data - 用例数据
 */
export const createFunctionalCase = (projectId, data) => {
  return request({
    url: `/functional_test/${projectId}/functional_cases`,
    method: 'post',
    data
  })
}

/**
 * 更新功能用例
 * @param {number} projectId - 项目ID
 * @param {number} caseId - 用例ID
 * @param {Object} data - 用例数据
 */
export const updateFunctionalCase = (projectId, caseId, data) => {
  return request({
    url: `/functional_test/${projectId}/functional_cases/${caseId}`,
    method: 'put',
    data
  })
}

/**
 * 删除功能用例
 * @param {number} projectId - 项目ID
 * @param {number} caseId - 用例ID
 */
export const deleteFunctionalCase = (projectId, caseId) => {
  return request({
    url: `/functional_test/${projectId}/functional_cases/${caseId}`,
    method: 'delete'
  })
}

/**
 * 审核功能用例
 * @param {number} projectId - 项目ID
 * @param {number} caseId - 用例ID
 * @param {Object} reviewData - 审核数据
 * @param {string} reviewData.status - 审核状态
 */
export const reviewFunctionalCase = (projectId, caseId, reviewData) => {
  return request({
    url: `/functional_test/${projectId}/functional_cases/${caseId}/review`,
    method: 'put',
    data: reviewData
  })
}

/**
 * 导出测试用例为 XMind 文件
 * @param {number} projectId - 项目ID
 * @param {number} requirementId - 需求ID
 * @param {Object} templateSettings - XMind模板设置
 * @returns {Promise} 返回 Blob 数据
 */
export const exportCasesAsXmind = (projectId, requirementId, templateSettings = {}) => {
  return request({
    url: `/functional_test/${projectId}/requirements/${requirementId}/export_xmind`,
    method: 'get',
    params: templateSettings,
    responseType: 'blob',
    timeout: 60000
  })
}

/**
 * 从文档中AI提取需求信息（旧接口，保留兼容）
 * @param {number} projectId - 项目ID
 * @param {FormData} formData - 包含 file（文件）或 url（链接）
 * @returns {Promise} 返回提取的需求信息 { title, description, priority, raw_text }
 */
export const extractRequirementFromDocument = (projectId, formData) => {
  return request({
    url: `/functional_test/extract_requirement`,
    method: 'post',
    params: { project_id: projectId },
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    },
    timeout: 120000
  })
}

/**
 * 流式混合提取需求信息（文本+图片+文档+视频+链接）
 * @param {number} projectId - 项目ID
 * @param {FormData} formData - 包含 text, files[], url
 * @returns {Promise<Response>} fetch Response (SSE stream)
 */
export const extractRequirementStream = (projectId, formData) => {
  const baseURL = import.meta.env.VITE_API_BASE_URL || '/api'
  const token = localStorage.getItem('token')
  return fetch(`${baseURL}/functional_test/extract_requirement_stream?project_id=${projectId}`, {
    method: 'POST',
    headers: {
      ...(token ? { 'Authorization': `Bearer ${token}` } : {})
    },
    body: formData
  })
}

// ==================== 一键文档生成XMind ====================

/**
 * 一键文档生成XMind用例（SSE流式）
 * @param {number} projectId - 项目ID
 * @param {FormData} formData - 包含 text, files[], url
 * @returns {Promise<Response>} fetch Response (SSE stream)
 */
export const docToXmindStream = (projectId, formData) => {
  const baseURL = import.meta.env.VITE_API_BASE_URL || '/api'
  const token = localStorage.getItem('token')
  return fetch(`${baseURL}/functional_test/${projectId}/doc_to_xmind_stream?project_id=${projectId}`, {
    method: 'POST',
    headers: {
      ...(token ? { 'Authorization': `Bearer ${token}` } : {})
    },
    body: formData
  })
}

/**
 * 根据用例数据下载XMind文件
 * @param {number} projectId - 项目ID
 * @param {Object} data - { scenarios, title }
 */
export const downloadXmindFromCases = (projectId, data) => {
  return request({
    url: `/functional_test/${projectId}/download_xmind_from_cases`,
    method: 'post',
    data,
    responseType: 'blob',
    timeout: 60000
  })
}

// ==================== AI 优化需求 ====================

/**
 * AI优化需求文档（支持MD文件上传，SSE流式）
 * @param {number} projectId - 项目ID
 * @param {FormData} formData - 包含 text, file, title
 * @returns {Promise<Response>} fetch Response (SSE stream)
 */
export const aiOptimizeDocStream = (projectId, formData) => {
  const baseURL = import.meta.env.VITE_API_BASE_URL || '/api'
  const token = localStorage.getItem('token')
  return fetch(`${baseURL}/functional_test/${projectId}/ai_optimize_doc_stream?project_id=${projectId}`, {
    method: 'POST',
    headers: {
      ...(token ? { 'Authorization': `Bearer ${token}` } : {})
    },
    body: formData
  })
}

/**
 * AI生成测试点并存储到用例集（SSE流式）
 * @param {number} projectId - 项目ID
 * @param {FormData} formData - 包含 text, files, case_set_name
 * @returns {Promise<Response>} fetch Response (SSE stream)
 */
export const aiGenerateTestpointsStream = (projectId, formData, signal) => {
  const baseURL = import.meta.env.VITE_API_BASE_URL || '/api'
  const token = localStorage.getItem('token')
  return fetch(`${baseURL}/functional_test/${projectId}/ai_generate_testpoints_stream?project_id=${projectId}`, {
    method: 'POST',
    headers: {
      ...(token ? { 'Authorization': `Bearer ${token}` } : {})
    },
    body: formData,
    signal,
  })
}

/**
 * 需求文档结构化分析（SSE流式）
 */
export const requirementAnalysisStream = (projectId, formData, signal) => {
  const baseURL = import.meta.env.VITE_API_BASE_URL || '/api'
  const token = localStorage.getItem('token')
  return fetch(`${baseURL}/functional_test/${projectId}/requirement_analysis_stream?project_id=${projectId}`, {
    method: 'POST',
    headers: {
      ...(token ? { 'Authorization': `Bearer ${token}` } : {})
    },
    body: formData,
    signal,
  })
}

// ===== 测试点集 API =====

export const getTestPointSetList = (projectId, params = {}) => {
  return request({
    url: `/functional_test/${projectId}/test_point_sets`,
    method: 'get',
    params
  })
}

export const getTestPointSetDetail = (projectId, tpSetId) => {
  return request({
    url: `/functional_test/${projectId}/test_point_sets/${tpSetId}`,
    method: 'get',
  })
}

export const deleteTestPointSet = (projectId, tpSetId) => {
  return request({
    url: `/functional_test/${projectId}/test_point_sets/${tpSetId}`,
    method: 'delete',
  })
}

/**
 * 根据测试点集生成用例集（SSE流式）
 */
export const generateCasesFromTestpoints = (projectId, tpSetId, signal) => {
  const baseURL = import.meta.env.VITE_API_BASE_URL || '/api'
  const token = localStorage.getItem('token')
  return fetch(`${baseURL}/functional_test/${projectId}/test_point_sets/${tpSetId}/generate_cases?project_id=${projectId}`, {
    method: 'POST',
    headers: {
      ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
      'Content-Type': 'application/json',
    },
    signal,
  })
}

/**
 * AI优化需求（SSE流式）
 * @param {number} projectId - 项目ID
 * @param {number} requirementId - 需求ID
 * @returns {string} SSE URL
 */
export const getAiOptimizeRequirementUrl = (projectId, requirementId) => {
  return `/functional_test/${projectId}/requirements/${requirementId}/ai_optimize`
}

/**
 * AI优化需求（POST请求获取EventSource）
 */
export const aiOptimizeRequirement = (projectId, requirementId) => {
  return request({
    url: `/functional_test/${projectId}/requirements/${requirementId}/ai_optimize`,
    method: 'post',
    responseType: 'stream',
    timeout: 120000
  })
}

/**
 * 应用AI优化结果
 * @param {number} projectId - 项目ID
 * @param {number} requirementId - 需求ID
 * @param {Object} data - 优化数据
 */
export const applyAiOptimization = (projectId, requirementId, data) => {
  return request({
    url: `/functional_test/${projectId}/requirements/${requirementId}/apply_optimization`,
    method: 'put',
    data
  })
}

// ==================== 排期需求关联 API ====================

/**
 * 获取可关联的排期需求列表
 * @param {number} projectId - 项目ID
 * @param {Object} params - 查询参数
 * @param {string} [params.keyword] - 按需求标题搜索
 */
export const getScheduleItemsForLink = (projectId, params = {}) => {
  return request({
    url: `/functional_test/${projectId}/schedule-items-for-link`,
    method: 'get',
    params
  })
}

// ==================== 用例集 API ====================

/**
 * 获取用例集列表
 * @param {number} projectId - 项目ID
 * @param {Object} params - 查询参数
 */
export const getCaseSetList = (projectId, params = {}) => {
  return request({
    url: `/functional_test/${projectId}/case_sets`,
    method: 'get',
    params
  })
}

/**
 * 获取用例集详情（含场景分组）
 * @param {number} projectId - 项目ID
 * @param {number} caseSetId - 用例集ID
 */
export const getCaseSetDetail = (projectId, caseSetId) => {
  return request({
    url: `/functional_test/${projectId}/case_sets/${caseSetId}`,
    method: 'get'
  })
}

/**
 * 创建用例集
 * @param {number} projectId - 项目ID
 * @param {Object} data - 用例集数据
 */
export const createCaseSet = (projectId, data) => {
  return request({
    url: `/functional_test/${projectId}/case_sets`,
    method: 'post',
    data
  })
}

/**
 * 更新用例集
 * @param {number} projectId - 项目ID
 * @param {number} caseSetId - 用例集ID
 * @param {Object} data - 更新数据
 */
export const updateCaseSet = (projectId, caseSetId, data) => {
  return request({
    url: `/functional_test/${projectId}/case_sets/${caseSetId}`,
    method: 'put',
    data
  })
}

/**
 * 删除用例集
 * @param {number} projectId - 项目ID
 * @param {number} caseSetId - 用例集ID
 */
export const deleteCaseSet = (projectId, caseSetId) => {
  return request({
    url: `/functional_test/${projectId}/case_sets/${caseSetId}`,
    method: 'delete'
  })
}

/**
 * 根据用例集ID导出XMind文件
 * @param {number} projectId - 项目ID
 * @param {number} caseSetId - 用例集ID
 */
export const exportCaseSetXmind = (projectId, caseSetId) => {
  return request({
    url: `/functional_test/${projectId}/case_sets/${caseSetId}/export_xmind`,
    method: 'get',
    responseType: 'blob',
    timeout: 60000
  })
}

/**
 * AI根据用例集测试点生成XMind测试用例（SSE流式）
 * @param {number} projectId - 项目ID
 * @param {number} caseSetId - 用例集ID
 * @param {AbortSignal} [signal] - 可选的取消信号
 * @returns {Promise<Response>} fetch Response (SSE stream)
 */
export const aiGenerateXmindFromCaseSet = (projectId, caseSetId, signal) => {
  const baseURL = import.meta.env.VITE_API_BASE_URL || '/api'
  const token = localStorage.getItem('token')
  return fetch(`${baseURL}/functional_test/${projectId}/case_sets/${caseSetId}/ai_generate_xmind`, {
    method: 'POST',
    headers: {
      ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
      'Content-Type': 'application/json',
    },
    signal,
  })
}

/**
 * 更新测试点集（名称等）
 * @param {number} projectId - 项目ID
 * @param {number} tpSetId - 测试点集ID
 * @param {Object} data - { name, description }
 */
export const updateTestPointSet = (projectId, tpSetId, data) => {
  return request({
    url: `/functional_test/${projectId}/test_point_sets/${tpSetId}`,
    method: 'put',
    data
  })
}

// ==================== 飞书用例集导入 ====================

/**
 * 导入用例到飞书用例集
 * @param {number} projectId - 项目ID
 * @param {Object} data - 导入参数
 * @param {number} [data.requirement_id] - 需求ID
 * @param {number} [data.case_set_id] - 用例集ID
 * @param {Array} [data.cases] - 直接传入用例数组
 * @param {string} [data.title] - 用例集标题
 * @param {string} data.feishu_token - 飞书 x-token
 * @param {string} [data.dir_id] - 飞书目录ID
 */
export const importCasesToFeishu = (projectId, data) => {
  return request({
    url: `/functional_test/${projectId}/import_to_feishu`,
    method: 'post',
    data,
    timeout: 60000
  })
}