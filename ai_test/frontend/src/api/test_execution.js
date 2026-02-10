import request from '@/utils/request'

// 运行测试任务（同步执行，返回结果与摘要）
export function runTestTask(projectId, data) {
  // data: { task_id: number, environment_id: number }
  return request({
    url: `/test_execution/${projectId}/tasks/run`,
    method: 'post',
    data
  })
}

// 后台运行测试任务（立即返回任务运行ID和状态）
export function runTestTaskBackground(projectId, data) {
  // data: { task_id: number, environment_id: number }
  return request({
    url: `/test_execution/${projectId}/tasks/run-background`,
    method: 'post',
    data
  })
}

// 查询任务运行状态（适用于后台运行场景）
export function getTaskRunStatus(projectId, taskRunId) {
  return request({
    url: `/test_execution/${projectId}/tasks/run/${taskRunId}/status`,
    method: 'get'
  })
}

// 获取测试任务运行记录列表
export function getTaskRunList(projectId, params = {}) {
  return request({
    url: `/test_execution/${projectId}/tasks/run`,
    method: 'get',
    params: {
      task_id: params.task_id,
      page: params.page || 1,
      page_size: params.page_size || 10
    }
  })
}

// 获取单条运行记录详情
export function getTaskRunDetail(projectId, taskRunId) {
  return request({
    url: `/test_execution/${projectId}/tasks/run/${taskRunId}`,
    method: 'get'
  })
}