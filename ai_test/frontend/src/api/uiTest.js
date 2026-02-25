import request from '@/utils/request'

// ======================== 页面管理 ========================

export const getUiPages = (projectId) => {
  return request({ url: `/ui_test/${projectId}/pages`, method: 'get' })
}

export const createUiPage = (projectId, data) => {
  return request({ url: `/ui_test/${projectId}/pages`, method: 'post', data })
}

export const updateUiPage = (projectId, pageId, data) => {
  return request({ url: `/ui_test/${projectId}/pages/${pageId}`, method: 'put', data })
}

export const deleteUiPage = (projectId, pageId) => {
  return request({ url: `/ui_test/${projectId}/pages/${pageId}`, method: 'delete' })
}

// ======================== 用例管理 ========================

export const getUiCases = (projectId, params = {}) => {
  return request({ url: `/ui_test/${projectId}/cases`, method: 'get', params })
}

export const getUiCaseDetail = (projectId, caseId) => {
  return request({ url: `/ui_test/${projectId}/cases/${caseId}`, method: 'get' })
}

export const createUiCase = (projectId, data) => {
  return request({ url: `/ui_test/${projectId}/cases`, method: 'post', data })
}

export const updateUiCase = (projectId, caseId, data) => {
  return request({ url: `/ui_test/${projectId}/cases/${caseId}`, method: 'put', data })
}

export const deleteUiCase = (projectId, caseId) => {
  return request({ url: `/ui_test/${projectId}/cases/${caseId}`, method: 'delete' })
}

// ======================== 执行管理 ========================

export const getUiExecutions = (projectId, params = {}) => {
  return request({ url: `/ui_test/${projectId}/executions`, method: 'get', params })
}

export const getUiExecutionDetail = (projectId, executionId) => {
  return request({ url: `/ui_test/${projectId}/executions/${executionId}`, method: 'get' })
}

/**
 * AI执行UI测试用例（SSE流式）
 * 返回 EventSource URL，需在前端用 EventSource 或 fetch 处理
 */
export const getExecuteCaseUrl = (projectId, caseId) => {
  return `/ui_test/${projectId}/cases/${caseId}/execute`
}

// ======================== 测试报告 ========================

export const getUiTestReports = (projectId, params = {}) => {
  return request({ url: `/ui_test/${projectId}/reports`, method: 'get', params })
}

export const getUiTestReport = (projectId, executionId) => {
  return request({ url: `/ui_test/${projectId}/executions/${executionId}/report`, method: 'get' })
}
