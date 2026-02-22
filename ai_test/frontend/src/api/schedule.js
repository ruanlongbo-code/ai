/**
 * 测试排期管理API接口
 */
import request from '@/utils/request'

// ==================== 迭代管理 ====================

export const createIteration = (projectId, data) => {
  return request({ url: `/schedule/${projectId}/iterations`, method: 'post', data })
}

export const getIterations = (projectId, params = {}) => {
  return request({ url: `/schedule/${projectId}/iterations`, method: 'get', params })
}

export const updateIteration = (projectId, iterationId, data) => {
  return request({ url: `/schedule/${projectId}/iterations/${iterationId}`, method: 'put', data })
}

export const deleteIteration = (projectId, iterationId) => {
  return request({ url: `/schedule/${projectId}/iterations/${iterationId}`, method: 'delete' })
}

// ==================== 可分配用户 ====================

export const getAssignableUsers = (projectId) => {
  return request({ url: `/schedule/${projectId}/assignable-users`, method: 'get' })
}

// ==================== 排期条目 ====================

export const createScheduleItem = (projectId, data) => {
  return request({ url: `/schedule/${projectId}/schedule-items`, method: 'post', data })
}

export const getScheduleItems = (projectId, params) => {
  return request({ url: `/schedule/${projectId}/schedule-items`, method: 'get', params })
}

export const updateScheduleItem = (projectId, itemId, data) => {
  return request({ url: `/schedule/${projectId}/schedule-items/${itemId}`, method: 'put', data })
}

export const deleteScheduleItem = (projectId, itemId) => {
  return request({ url: `/schedule/${projectId}/schedule-items/${itemId}`, method: 'delete' })
}

// ==================== 日报 ====================

export const submitDailyReport = (projectId, data) => {
  return request({ url: `/schedule/${projectId}/daily-reports`, method: 'post', data })
}

export const getMyDailyReports = (projectId, params) => {
  return request({ url: `/schedule/${projectId}/daily-reports/my`, method: 'get', params })
}

export const getMyScheduleItems = (projectId, params) => {
  return request({ url: `/schedule/${projectId}/my-schedule-items`, method: 'get', params })
}

// ==================== AI报告 ====================

export const generateAiReport = (projectId, reportId) => {
  return request({
    url: `/schedule/${projectId}/daily-reports/${reportId}/generate-ai-report`,
    method: 'post',
    timeout: 60000
  })
}

// ==================== Dashboard ====================

export const getDashboardDaily = (projectId, params) => {
  return request({ url: `/schedule/${projectId}/dashboard/daily`, method: 'get', params })
}

export const getDashboardIterationSummary = (projectId, params) => {
  return request({ url: `/schedule/${projectId}/dashboard/iteration-summary`, method: 'get', params })
}

// ==================== 飞书Webhook ====================

export const createFeishuWebhook = (projectId, data) => {
  return request({ url: `/schedule/${projectId}/feishu-webhooks`, method: 'post', data })
}

export const getFeishuWebhooks = (projectId) => {
  return request({ url: `/schedule/${projectId}/feishu-webhooks`, method: 'get' })
}

export const updateFeishuWebhook = (projectId, webhookId, data) => {
  return request({ url: `/schedule/${projectId}/feishu-webhooks/${webhookId}`, method: 'put', data })
}

export const deleteFeishuWebhook = (projectId, webhookId) => {
  return request({ url: `/schedule/${projectId}/feishu-webhooks/${webhookId}`, method: 'delete' })
}

export const testFeishuWebhook = (projectId, webhookId) => {
  return request({ url: `/schedule/${projectId}/feishu-webhooks/${webhookId}/test`, method: 'post' })
}

// ==================== 飞书推送 ====================

export const sendReportToFeishu = (projectId, reportId, data) => {
  return request({ url: `/schedule/${projectId}/daily-reports/${reportId}/send-feishu`, method: 'post', data })
}
