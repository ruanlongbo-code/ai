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
 * 从文档中AI提取需求信息
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

// ==================== AI 优化需求 ====================

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