/**
 * 测试环境模块API接口
 */
import request from '@/utils/request'

// 测试环境管理接口

/**
 * 获取测试环境列表
 * @param {number} projectId - 项目ID
 * @param {Object} params - 查询参数
 * @param {number} [params.page=1] - 页码
 * @param {number} [params.page_size=10] - 每页数量 (1-100)
 */
export const getTestEnvironments = (projectId, params = {}) => {
  return request({
    url: `/test_environment/${projectId}/environments`,
    method: 'get',
    params: {
      page: 1,
      page_size: 10,
      ...params
    }
  })
}

/**
 * 获取测试环境详情
 * @param {number} projectId - 项目ID
 * @param {number} environmentId - 环境ID
 */
export const getTestEnvironmentDetail = (projectId, environmentId) => {
  return request({
    url: `/test_environment/${projectId}/environments/${environmentId}`,
    method: 'get'
  })
}

/**
 * 创建测试环境
 * @param {number} projectId - 项目ID
 * @param {Object} data - 环境数据
 * @param {string} data.name - 环境名称 (1-100字符)
 * @param {string} [data.func_global] - 全局函数 (可选)
 */
export const createTestEnvironment = (projectId, data) => {
  return request({
    url: `/test_environment/${projectId}/environments`,
    method: 'post',
    data
  })
}

/**
 * 编辑测试环境
 * @param {number} projectId - 项目ID
 * @param {number} environmentId - 环境ID
 * @param {Object} data - 环境更新数据
 * @param {string} [data.name] - 环境名称 (1-100字符)
 * @param {string} [data.func_global] - 全局函数
 */
export const updateTestEnvironment = (projectId, environmentId, data) => {
  return request({
    url: `/test_environment/${projectId}/environments/${environmentId}`,
    method: 'put',
    data
  })
}

/**
 * 删除测试环境
 * @param {number} projectId - 项目ID
 * @param {number} environmentId - 环境ID
 */
export const deleteTestEnvironment = (projectId, environmentId) => {
  return request({
    url: `/test_environment/${projectId}/environments/${environmentId}`,
    method: 'delete'
  })
}

// 测试环境配置管理接口

/**
 * 创建测试环境配置
 * @param {number} environmentId - 环境ID
 * @param {Object} data - 配置数据
 * @param {string} data.name - 配置名称 (1-100字符)
 * @param {string} data.value - 配置值 (1-500字符)
 */
export const createTestEnvironmentConfig = (environmentId, data) => {
  return request({
    url: `/test_environment/${environmentId}/configs`,
    method: 'post',
    data
  })
}

/**
 * 编辑测试环境配置
 * @param {number} environmentId - 环境ID
 * @param {number} configId - 配置ID
 * @param {Object} data - 配置更新数据
 * @param {string} [data.name] - 配置名称 (1-100字符)
 * @param {string} [data.value] - 配置值 (1-500字符)
 */
export const updateTestEnvironmentConfig = (environmentId, configId, data) => {
  return request({
    url: `/test_environment/${environmentId}/configs/${configId}`,
    method: 'put',
    data
  })
}

/**
 * 删除测试环境配置
 * @param {number} environmentId - 环境ID
 * @param {number} configId - 配置ID
 */
export const deleteTestEnvironmentConfig = (environmentId, configId) => {
  return request({
    url: `/test_environment/${environmentId}/configs/${configId}`,
    method: 'delete'
  })
}

// 测试环境数据库配置管理接口

/**
 * 创建测试环境数据库配置
 * @param {number} environmentId - 环境ID
 * @param {Object} data - 数据库配置数据
 * @param {string} data.name - 数据库名称 (1-100字符)
 * @param {string} data.type - 数据库类型 (1-50字符)
 * @param {Object} data.config - 数据库配置对象
 */
export const createTestEnvironmentDatabase = (environmentId, data) => {
  return request({
    url: `/test_environment/${environmentId}/databases`,
    method: 'post',
    data
  })
}

/**
 * 编辑测试环境数据库配置
 * @param {number} environmentId - 环境ID
 * @param {number} dbId - 数据库配置ID
 * @param {Object} data - 数据库配置更新数据
 * @param {string} [data.name] - 数据库名称 (1-100字符)
 * @param {string} [data.type] - 数据库类型 (1-50字符)
 * @param {Object} [data.config] - 数据库配置对象
 */
export const updateTestEnvironmentDatabase = (environmentId, dbId, data) => {
  return request({
    url: `/test_environment/${environmentId}/databases/${dbId}`,
    method: 'put',
    data
  })
}

/**
 * 删除测试环境数据库配置
 * @param {number} environmentId - 环境ID
 * @param {number} dbId - 数据库配置ID
 */
export const deleteTestEnvironmentDatabase = (environmentId, dbId) => {
  return request({
    url: `/test_environment/${environmentId}/databases/${dbId}`,
    method: 'delete'
  })
}

// 默认导出所有接口
export default {
  getTestEnvironments,
  getTestEnvironmentDetail,
  createTestEnvironment,
  updateTestEnvironment,
  deleteTestEnvironment,
  createTestEnvironmentConfig,
  updateTestEnvironmentConfig,
  deleteTestEnvironmentConfig,
  createTestEnvironmentDatabase,
  updateTestEnvironmentDatabase,
  deleteTestEnvironmentDatabase
}