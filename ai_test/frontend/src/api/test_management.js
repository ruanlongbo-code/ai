/**
 * 测试管理模块 API 客户端
 */
import request from '@/utils/request'

/**
 * 获取测试套件列表（分页）
 * @param {number} projectId - 项目ID
 * @param {Object} params - 查询参数
 * @param {number} [params.page=1] - 页码
 * @param {number} [params.page_size=10] - 每页数量
 */
export const getTestSuites = (projectId, params = {}) => {
  return request({
    url: `/test_management/${projectId}/suites`,
    method: 'get',
    params: {
      page: params.page || 1,
      page_size: params.page_size || 10
    }
  })
}

/**
 * 获取测试套件详情
 * @param {number} projectId - 项目ID
 * @param {number} suiteId - 套件ID
 */
export const getTestSuiteDetail = (projectId, suiteId) => {
  return request({
    url: `/test_management/${projectId}/suites/${suiteId}`,
    method: 'get'
  })
}

/**
 * 获取测试任务（测试计划）列表（分页）
 * @param {number} projectId - 项目ID
 * @param {Object} params - 查询参数
 * @param {number} [params.page=1] - 页码
 * @param {number} [params.page_size=10] - 每页数量
 */
export const getTestTasks = (projectId, params = {}) => {
  return request({
    url: `/test_management/${projectId}/tasks`,
    method: 'get',
    params: {
      page: params.page || 1,
      page_size: params.page_size || 10
    }
  })
}

/**
 * 获取测试任务（测试计划）详情
 * @param {number} projectId - 项目ID
 * @param {number} taskId - 任务ID
 */
export const getTestTaskDetail = (projectId, taskId) => {
  return request({
    url: `/test_management/${projectId}/tasks/${taskId}`,
    method: 'get'
  })
}

/**
 * 创建测试套件
 * @param {number} projectId - 项目ID
 * @param {Object} data - 套件数据
 * @param {string} data.suite_name - 套件名称
 * @param {string} [data.description] - 套件描述
 * @param {string} data.type - 套件类型 (api/ui)
 */// 创建测试套件
export const createTestSuite = (projectId, data) => {
  return request({
    url: `/test_management/${projectId}/suites`,
    method: 'post',
    data
  })
}

// 删除测试套件
export const deleteTestSuite = (projectId, suiteId) => {
  return request({
    url: `/test_management/${projectId}/suites/${suiteId}`,
    method: 'delete'
  })
}

/**
 * 创建测试任务（测试计划）
 * @param {number} projectId - 项目ID
 * @param {Object} data - 任务数据
 * @param {string} data.task_name - 任务名称
 * @param {string} [data.description] - 任务描述
 * @param {string} data.type - 任务类型 (api/ui/functional)
 */
export const createTestTask = (projectId, data) => {
  return request({
    url: `/test_management/${projectId}/tasks`,
    method: 'post',
    data
  })
}

/**
 * 删除测试任务（测试计划）
 * @param {number} projectId - 项目ID
 * @param {number} taskId - 任务ID
 */
export const deleteTestTask = (projectId, taskId) => {
  return request({
    url: `/test_management/${projectId}/tasks/${taskId}`,
    method: 'delete'
  })
}

/**
 * 向测试任务中添加套件
 * @param {number} projectId - 项目ID
 * @param {number} taskId - 任务ID
 * @param {Object} data - 套件数据
 * @param {number} data.suite_id - 套件ID
 */
export const addSuiteToTask = (projectId, taskId, data) => {
  return request({
    url: `/test_management/${projectId}/tasks/${taskId}/suites`,
    method: 'post',
    data
  })
}

/**
 * 从测试任务中删除套件
 * @param {number} projectId - 项目ID
 * @param {number} taskId - 任务ID
 * @param {number} suiteId - 套件ID
 */
export const deleteSuiteFromTask = (projectId, taskId, suiteId) => {
  return request({
    url: `/test_management/${projectId}/tasks/${taskId}/suites/${suiteId}`,
    method: 'delete'
  })
}

/**
 * 重新排序测试任务中的套件
 * @param {number} projectId - 项目ID
 * @param {number} taskId - 任务ID
 * @param {Object} data - 排序数据
 * @param {number[]} data.suite_ids - 套件ID数组（按新顺序）
 */
export const reorderTaskSuites = (projectId, taskId, data) => {
  return request({
    url: `/test_management/${projectId}/tasks/${taskId}/suites/reorder`,
    method: 'put',
    data
  })
}
// ==================== 接口依赖管理 API ====================

/**
 * 获取接口依赖分组列表
 * @param {number} projectId - 项目ID
 * @param {Object} params - 查询参数
 * @param {number} [params.page=1] - 页码
 * @param {number} [params.page_size=20] - 每页数量
 */
export const getDependencyGroups = (projectId, params = {}) => {
  return request({
    url: `/api_test/${projectId}/dependency-groups`,
    method: 'get',
    params: {
      page: params.page || 1,
      page_size: params.page_size || 20
    }
  })
}

/**
 * 创建接口依赖分组
 * @param {number} projectId - 项目ID
 * @param {Object} data - 分组数据
 * @param {string} data.name - 分组名称
 * @param {string} [data.description] - 分组描述
 * @param {number} data.target_interface_id - 目标接口ID
 */
export const createDependencyGroup = (projectId, data) => {
  return request({
    url: `/api_test/${projectId}/dependency-groups`,
    method: 'post',
    data
  })
}

/**
 * 删除接口依赖分组
 * @param {number} projectId - 项目ID
 * @param {number} groupId - 分组ID
 */
export const deleteDependencyGroup = (projectId, groupId) => {
  return request({
    url: `/api_test/${projectId}/dependency-groups/${groupId}`,
    method: 'delete'
  })
}

/**
 * 创建接口依赖
 * @param {number} projectId - 项目ID
 * @param {number} groupId - 分组ID
 * @param {Object} data - 依赖数据
 * @param {string} data.name - 依赖名称
 * @param {string} [data.description] - 依赖描述
 * @param {string} data.dependency_type - 依赖类型（header/param/body/response）
 * @param {number} [data.source_interface_id] - 源接口ID
 * @param {string} [data.source_field_path] - 源字段路径
 * @param {string} data.target_field_name - 目标字段名称
 * @param {Object} [data.transform_rule] - 转换规则
 * @param {boolean} [data.is_active=true] - 是否启用
 */
export const createDependency = (projectId, groupId, data) => {
  return request({
    url: `/api_test/${projectId}/dependency-groups/${groupId}/dependencies`,
    method: 'post',
    data
  })
}

/**
 * 更新接口依赖
 * @param {number} projectId - 项目ID
 * @param {number} groupId - 分组ID
 * @param {number} dependencyId - 依赖ID
 * @param {Object} data - 依赖数据
 */
export const updateDependency = (projectId, groupId, dependencyId, data) => {
  return request({
    url: `/api_test/${projectId}/dependency-groups/${groupId}/dependencies/${dependencyId}`,
    method: 'put',
    data
  })
}

/**
 * 删除接口依赖
 * @param {number} projectId - 项目ID
 * @param {number} groupId - 分组ID
 * @param {number} dependencyId - 依赖ID
 */
export const deleteDependency = (projectId, groupId, dependencyId) => {
  return request({
    url: `/api_test/${projectId}/dependency-groups/${groupId}/dependencies/${dependencyId}`,
    method: 'delete'
  })
}

/**
 * 获取接口详情（包含依赖分组信息）
 * @param {number} projectId - 项目ID
 * @param {number} interfaceId - 接口ID
 */
export const getInterfaceDetail = (projectId, interfaceId) => {
  return request({
    url: `/api_test/${projectId}/interfaces/${interfaceId}`,
    method: 'get'
  })
}

export default {
  getTestSuites,
  getTestSuiteDetail,
  getTestTasks,
  getTestTaskDetail,
  createTestSuite,
  deleteTestSuite,
  createTestTask,
  deleteTestTask,
  addSuiteToTask,
  deleteSuiteFromTask,
  reorderTaskSuites,
  getDependencyGroups,
  createDependencyGroup,
  deleteDependencyGroup,
  createDependency,
  updateDependency,
  deleteDependency,
  getInterfaceDetail
}