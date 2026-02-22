/**
 * 业务线管理API接口（原模块管理，已升级为二级层级 + 人员分配）
 */
import request from '@/utils/request'

// ==================== 业务线 CRUD ====================

export const getProjectModules = (projectId) => {
  return request({ url: `/project/${projectId}/modules`, method: 'get' })
}

export const createProjectModule = (projectId, data) => {
  return request({ url: `/project/${projectId}/modules`, method: 'post', data })
}

export const updateProjectModule = (projectId, moduleId, data) => {
  return request({ url: `/project/${projectId}/modules/${moduleId}`, method: 'put', data })
}

export const deleteProjectModule = (projectId, moduleId) => {
  return request({ url: `/project/${projectId}/modules/${moduleId}`, method: 'delete' })
}

// ==================== 业务线成员管理 ====================

export const addBusinessLineMember = (projectId, moduleId, data) => {
  return request({ url: `/project/${projectId}/modules/${moduleId}/members`, method: 'post', data })
}

export const updateBusinessLineMember = (projectId, moduleId, memberId, data) => {
  return request({ url: `/project/${projectId}/modules/${moduleId}/members/${memberId}`, method: 'put', data })
}

export const removeBusinessLineMember = (projectId, moduleId, memberId) => {
  return request({ url: `/project/${projectId}/modules/${moduleId}/members/${memberId}`, method: 'delete' })
}

// ==================== 用户业务线信息 ====================

export const getMyBusinessLines = (projectId) => {
  return request({ url: `/project/${projectId}/my-business-lines`, method: 'get' })
}