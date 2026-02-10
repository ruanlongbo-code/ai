/**
 * 项目模块管理API接口
 */
import request from '@/utils/request'

/**
 * 获取项目模块列表
 * @param {number} projectId - 项目ID
 */
export const getProjectModules = (projectId) => {
  return request({
    url: `/project/${projectId}/modules`,
    method: 'get'
  })
}

/**
 * 创建项目模块
 * @param {number} projectId - 项目ID
 * @param {Object} data - 模块数据
 * @param {string} data.name - 模块名称 (1-100字符)
 * @param {string} [data.description] - 模块描述
 */
export const createProjectModule = (projectId, data) => {
  return request({
    url: `/project/${projectId}/modules`,
    method: 'post',
    data
  })
}

/**
 * 更新项目模块
 * @param {number} projectId - 项目ID
 * @param {number} moduleId - 模块ID
 * @param {Object} data - 模块更新数据
 * @param {string} data.name - 模块名称 (1-100字符)
 * @param {string} [data.description] - 模块描述
 */
export const updateProjectModule = (projectId, moduleId, data) => {
  return request({
    url: `/project/${projectId}/modules/${moduleId}`,
    method: 'put',
    data
  })
}

/**
 * 删除项目模块
 * @param {number} projectId - 项目ID
 * @param {number} moduleId - 模块ID
 */
export const deleteProjectModule = (projectId, moduleId) => {
  return request({
    url: `/project/${projectId}/modules/${moduleId}`,
    method: 'delete'
  })
}