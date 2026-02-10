/**
 * 测试套件相关API接口
 */
import request from '@/utils/request'

/**
 * 获取测试套件详情（包含套件中的所有用例）
 * @param {number} projectId - 项目ID
 * @param {number} suiteId - 套件ID
 * @returns {Promise} 套件详情数据
 */
export const getSuiteDetail = (projectId, suiteId) => {
  return request({
    url: `/test_management/${projectId}/suites/${suiteId}`,
    method: 'get'
  })
}

/**
 * 往测试套件中添加用例
 * @param {number} projectId - 项目ID
 * @param {number} suiteId - 套件ID
 * @param {number} caseId - 用例ID
 * @returns {Promise} 添加结果
 */
export const addCaseToSuite = (projectId, suiteId, caseId) => {
  return request({
    url: `/test_management/${projectId}/suites/${suiteId}/cases`,
    method: 'post',
    data: {
      case_id: caseId
    }
  })
}

/**
 * 从测试套件中删除用例
 * @param {number} projectId - 项目ID
 * @param {number} suiteId - 套件ID
 * @param {number} caseId - 用例ID
 * @returns {Promise} 删除结果
 */
export const removeCaseFromSuite = (projectId, suiteId, caseId) => {
  return request({
    url: `/test_management/${projectId}/suites/${suiteId}/cases/${caseId}`,
    method: 'delete'
  })
}

/**
 * 调整测试套件中用例的执行顺序
 * @param {number} projectId - 项目ID
 * @param {number} suiteId - 套件ID
 * @param {Array<number>} caseIds - 用例ID列表，按新的执行顺序排列
 * @returns {Promise} 排序结果
 */
export const reorderSuiteCases = (projectId, suiteId, caseIds) => {
  return request({
    url: `/test_management/${projectId}/suites/${suiteId}/cases/reorder`,
    method: 'put',
    data: {
      case_ids: caseIds
    }
  })
}

/**
 * 获取项目的所有测试用例列表（用于添加到套件）
 * @param {number} projectId - 项目ID
 * @param {Object} params - 查询参数
 * @param {string} [params.keyword] - 搜索关键词
 * @param {number} [params.interface_id] - 接口ID过滤
 * @param {number} [params.page] - 页码
 * @param {number} [params.page_size] - 每页数量
 * @returns {Promise} 用例列表数据
 */
export const getProjectTestCases = (projectId, params = {}) => {
  return request({
    url: `/api_test/${projectId}/test-cases`,
    method: 'get',
    params: {
      page: params.page || 1,
      page_size: params.page_size || 20,
      keyword: params.keyword,
      interface_id: params.interface_id
    }
  })
}

/**
 * 运行测试套件
 * @param {number} projectId - 项目ID
 * @param {Object} data - 运行参数
 * @param {number} data.suite_id - 套件ID
 * @param {number} data.environment_id - 测试环境ID
 * @returns {Promise} 运行结果
 */
export const runTestSuite = (projectId, data) => {
  return request({
    url: `/test_execution/${projectId}/suites/run`,
    method: 'post',
    data: {
      suite_id: data.suite_id,
      environment_id: data.environment_id
    }
  })
}

/**
 * 获取套件运行记录列表
 * @param {number} projectId - 项目ID
 * @param {number} suiteId - 套件ID
 * @param {Object} params - 查询参数
 * @returns {Promise} 运行记录列表
 */
export const getSuiteRunHistory = (projectId, suiteId, params = {}) => {
  return request({
    url: `/test_execution/${projectId}/suites/run`,
    method: 'get',
    params: {
      suite_id: suiteId,
      ...params
    }
  })
}

/**
 * 获取套件运行记录详情
 * @param {number} projectId - 项目ID
 * @param {number} suiteRunId - 套件运行记录ID
 * @returns {Promise} 运行记录详情
 */
export const getSuiteRunDetail = (projectId, suiteRunId) => {
  return request({
    url: `/test_execution/${projectId}/suites/run/${suiteRunId}`,
    method: 'get'
  })
}

/**
 * 获取用例执行记录详情
 * @param {number} projectId - 项目ID
 * @param {number} caseRunId - 用例执行记录ID
 * @returns {Promise} 用例执行记录详情
 */
export const getCaseRunDetail = (projectId, caseRunId) => {
  return request({
    url: `/test_execution/${projectId}/cases/run/${caseRunId}`,
    method: 'get'
  })
}

export default {
  getSuiteDetail,
  addCaseToSuite,
  removeCaseFromSuite,
  reorderSuiteCases,
  getProjectTestCases,
  runTestSuite,
  getSuiteRunHistory,
  getSuiteRunDetail,
  getCaseRunDetail
}