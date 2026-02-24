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

// ==================== AI报告编辑 ====================

export const updateAiReportContent = (projectId, reportId, data) => {
  return request({ url: `/schedule/${projectId}/daily-reports/${reportId}/ai-content`, method: 'put', data })
}

// ==================== 进度智能计算 ====================

export const calculateProgress = (projectId, data) => {
  return request({ url: `/schedule/${projectId}/calculate-progress`, method: 'post', data, timeout: 30000 })
}

export const getProgressOptions = (projectId) => {
  return request({ url: `/schedule/${projectId}/progress-options`, method: 'get' })
}

// ==================== 缺陷管理 ====================

export const createDefect = (projectId, data) => {
  return request({ url: `/schedule/${projectId}/defects`, method: 'post', data })
}

export const getDefects = (projectId, params) => {
  return request({ url: `/schedule/${projectId}/defects`, method: 'get', params })
}

export const updateDefect = (projectId, defectId, data) => {
  return request({ url: `/schedule/${projectId}/defects/${defectId}`, method: 'put', data })
}

export const deleteDefect = (projectId, defectId) => {
  return request({ url: `/schedule/${projectId}/defects/${defectId}`, method: 'delete' })
}

export const getDefectStats = (projectId, scheduleItemId) => {
  return request({ url: `/schedule/${projectId}/defects/stats`, method: 'get', params: { schedule_item_id: scheduleItemId } })
}

export const aiExpandDefect = (projectId, defectId) => {
  return request({ url: `/schedule/${projectId}/defects/${defectId}/ai-expand`, method: 'post', timeout: 60000 })
}

// AI扩写缺陷描述预览（不创建缺陷）
export const aiExpandDefectPreview = (projectId, data) => {
  return request({ url: `/schedule/${projectId}/defects/ai-expand-preview`, method: 'post', data, timeout: 60000 })
}

// ==================== 截图AI识别 ====================

export const analyzeScreenshot = (projectId, file) => {
  const formData = new FormData()
  formData.append('file', file)
  return request({
    url: `/schedule/${projectId}/analyze-screenshot`,
    method: 'post',
    data: formData,
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 60000,
  })
}

// ==================== 飞书集成 ====================

export const verifyFeishuConnection = (projectId) => {
  return request({ url: `/schedule/${projectId}/feishu/verify`, method: 'get' })
}

export const syncDefectToFeishu = (projectId, defectId) => {
  return request({ url: `/schedule/${projectId}/defects/${defectId}/sync-to-feishu`, method: 'post', timeout: 30000 })
}

export const getFeishuStoryIssues = (projectId, ticketUrl) => {
  return request({ url: `/schedule/${projectId}/feishu/story-issues`, method: 'get', params: { ticket_url: ticketUrl } })
}

// ==================== 需求群同步 ====================

export const getMatchedWebhooks = (projectId, reportId) => {
  return request({ url: `/schedule/${projectId}/daily-reports/${reportId}/matched-webhooks`, method: 'get' })
}

export const sendReportToFeishu = (projectId, reportId, data) => {
  return request({ url: `/schedule/${projectId}/daily-reports/${reportId}/send-feishu`, method: 'post', data })
}
