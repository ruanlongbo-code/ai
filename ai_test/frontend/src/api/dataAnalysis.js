/**
 * 数据分析API接口
 */
import request from '@/utils/request'

// ==================== 缺陷分析 ====================

/**
 * 获取缺陷统计数据
 */
export const getDefectStats = (projectId, params = {}) => {
  return request({
    url: `/data_analysis/${projectId}/defect-analysis/stats`,
    method: 'get',
    params
  })
}

/**
 * 获取AI缺陷分析SSE URL
 */
export const getAiDefectAnalysisUrl = (projectId, iterationId) => {
  const params = iterationId ? `?iteration_id=${iterationId}` : ''
  return `/data_analysis/${projectId}/defect-analysis/ai-analyze${params}`
}

// ==================== 用户行为分析 ====================

/**
 * 获取用户行为统计数据
 */
export const getBehaviorStats = (projectId, params = {}) => {
  return request({
    url: `/data_analysis/${projectId}/behavior-analysis/stats`,
    method: 'get',
    params
  })
}

/**
 * 获取AI行为分析SSE URL
 */
export const getAiBehaviorAnalysisUrl = (projectId, days) => {
  const params = days ? `?days=${days}` : ''
  return `/data_analysis/${projectId}/behavior-analysis/ai-analyze${params}`
}
