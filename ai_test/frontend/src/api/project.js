/**
 * 项目模块API接口
 */
import request from '@/utils/request'

/**
 * 获取项目列表
 * @param {Object} params - 查询参数
 * @param {number} [params.page=1] - 页码
 * @param {number} [params.page_size=10] - 每页数量
 * @param {string} [params.project_name] - 项目名称模糊查询
 */
export const getProjectList = (params = {}) => {
  return request({
    url: '/project/list',
    method: 'get',
    params: {
      page: 1,
      page_size: 10,
      ...params
    }
  })
}

/**
 * 创建项目
 * @param {Object} data - 项目数据
 * @param {string} data.name - 项目名称 (1-100字符)
 * @param {string} data.description - 项目描述
 */
export const createProject = (data) => {
  return request({
    url: '/project/create',
    method: 'post',
    data
  })
}

/**
 * 删除项目
 * @param {number} projectId - 项目ID
 */
export const deleteProject = (projectId) => {
  return request({
    url: `/project/${projectId}`,
    method: 'delete'
  })
}

/**
 * 修改项目信息
 * @param {number} projectId - 项目ID
 * @param {Object} data - 项目更新数据
 * @param {string} data.name - 项目名称 (1-100字符)
 * @param {string} data.description - 项目描述
 */
export const updateProject = (projectId, data) => {
  return request({
    url: `/project/${projectId}`,
    method: 'put',
    data
  })
}

/**
 * 添加项目成员
 * @param {number} projectId - 项目ID
 * @param {Object} data - 成员数据
 * @param {number} data.user_id - 用户ID
 * @param {number} [data.role=1] - 成员角色 (0=只读, 1=可操作)
 */
export const addProjectMember = (projectId, data) => {
  return request({
    url: `/project/${projectId}/members`,
    method: 'post',
    data
  })
}

/**
 * 移除项目成员
 * @param {number} projectId - 项目ID
 * @param {number} userId - 用户ID
 */
export const removeProjectMember = (projectId, userId) => {
  return request({
    url: `/project/${projectId}/members/${userId}`,
    method: 'delete'
  })
}

/**
 * 更新项目成员状态
 * @param {number} projectId - 项目ID
 * @param {number} userId - 用户ID
 * @param {Object} data - 状态数据
 * @param {number} data.status - 成员状态 (0=禁用, 1=启用)
 */
export const updateProjectMemberStatus = (projectId, userId, data) => {
  return request({
    url: `/project/${projectId}/members/${userId}/status`,
    method: 'put',
    data
  })
}

/**
 * 获取项目成员列表
 * @param {number} projectId - 项目ID
 */
export const getProjectMembers = (projectId) => {
  return request({
    url: `/project/${projectId}/members`,
    method: 'get'
  })
}

/**
 * 获取项目详情
 * @param {number} projectId - 项目ID
 */
export const getProjectDetail = (projectId) => {
  return request({
    url: `/project/${projectId}/detail`,
    method: 'get'
  })
}

/**
 * 修改项目成员角色
 * @param {number} projectId - 项目ID
 * @param {number} userId - 用户ID
 * @param {Object} data - 角色数据
 * @param {number} data.role - 成员角色 (0=只读, 1=可操作, 2=负责人)
 */
export const updateProjectMemberRole = (projectId, userId, data) => {
  return request({
    url: `/project/${projectId}/members/${userId}/role`,
    method: 'put',
    data
  })
}

// 项目模块管理接口

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
 * @param {string} [data.description] - 模块描述 (可选)
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
 * @param {string} [data.description] - 模块描述 (可选)
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

// 默认导出所有接口
/**
 * 获取项目仪表盘统计
 * @param {number} projectId - 项目ID
 */
export const getProjectDashboard = (projectId) => {
  return request({
    url: `/project/${projectId}/dashboard`,
    method: 'get'
  })
}
export default {
  getProjectList,
  createProject,
  deleteProject,
  updateProject,
  addProjectMember,
  removeProjectMember,
  updateProjectMemberStatus,
  getProjectMembers,
  getProjectDetail,
  updateProjectMemberRole,
  getProjectModules,
  createProjectModule,
  updateProjectModule,
  deleteProjectModule
  , getProjectDashboard
}