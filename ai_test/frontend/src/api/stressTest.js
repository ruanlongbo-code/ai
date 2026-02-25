import request from '@/utils/request'

// =================== 测试场景 ===================
export function getScenarios(params) {
  return request({ url: '/stress-test/scenarios', method: 'get', params })
}

export function getScenarioDetail(scenarioId) {
  return request({ url: `/stress-test/scenarios/${scenarioId}`, method: 'get' })
}

export function createScenario(projectId, data) {
  return request({ url: '/stress-test/scenarios', method: 'post', params: { project_id: projectId }, data })
}

export function updateScenario(scenarioId, data) {
  return request({ url: `/stress-test/scenarios/${scenarioId}`, method: 'put', data })
}

export function deleteScenario(scenarioId) {
  return request({ url: `/stress-test/scenarios/${scenarioId}`, method: 'delete' })
}

export function aiGenerateScenario(projectId, data) {
  return request({ url: '/stress-test/scenarios/ai-generate', method: 'post', params: { project_id: projectId }, data })
}

// =================== 压测任务 ===================
export function getTasks(params) {
  return request({ url: '/stress-test/tasks', method: 'get', params })
}

export function createTask(projectId, data) {
  return request({ url: '/stress-test/tasks', method: 'post', params: { project_id: projectId }, data })
}

export function deleteTask(taskId) {
  return request({ url: `/stress-test/tasks/${taskId}`, method: 'delete' })
}

export function stopTask(taskId) {
  return request({ url: `/stress-test/tasks/${taskId}/stop`, method: 'post' })
}

export function aiRecommendConfig(data) {
  return request({ url: '/stress-test/tasks/ai-recommend', method: 'post', data })
}

// =================== 压测结果 ===================
export function getResult(taskId) {
  return request({ url: `/stress-test/results/${taskId}`, method: 'get' })
}

export function aiAnalyzeResult(taskId) {
  return request({ url: `/stress-test/results/${taskId}/ai-analyze`, method: 'post' })
}

// =================== 实时监控 ===================
export function getMetrics(taskId, limit = 300) {
  return request({ url: `/stress-test/metrics/${taskId}`, method: 'get', params: { limit } })
}

// =================== 性能基线 ===================
export function getBaselines(params) {
  return request({ url: '/stress-test/baselines', method: 'get', params })
}

export function createBaseline(projectId, data) {
  return request({ url: '/stress-test/baselines', method: 'post', params: { project_id: projectId }, data })
}

export function updateBaseline(baselineId, data) {
  return request({ url: `/stress-test/baselines/${baselineId}`, method: 'put', data })
}

export function deleteBaseline(baselineId) {
  return request({ url: `/stress-test/baselines/${baselineId}`, method: 'delete' })
}

export function aiCompareBaselines(data) {
  return request({ url: '/stress-test/baselines/ai-compare', method: 'post', data })
}
