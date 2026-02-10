/**
 * 用户模块API接口
 */
import request from '@/utils/request'

/**
 * 用户注册
 * @param {Object} data - 注册数据
 * @param {string} data.username - 用户名 (3-50字符)
 * @param {string} data.password - 密码 (6-128字符)
 * @param {string} data.email - 邮箱
 * @param {string} [data.phone] - 手机号 (可选)
 * @param {string} [data.real_name] - 真实姓名 (可选)
 */
export const register = (data) => {
  return request({
    url: '/user/register',
    method: 'post',
    data
  })
}

/**
 * 用户登录
 * @param {Object} data - 登录数据
 * @param {string} data.username - 用户名或邮箱
 * @param {string} data.password - 密码
 */
export const login = (data) => {
  return request({
    url: '/user/login',
    method: 'post',
    data
  })
}

// 移除旧版激活接口（使用下方管理员激活/停用接口）

/**
 * 验证Token
 */
export const verifyToken = () => {
  return request({
    url: '/user/verify-token',
    method: 'post'
  })
}

/**
 * 刷新Token
 * @param {string} refreshToken - 刷新令牌
 */
export const refreshToken = (refreshToken) => {
  return request({
    url: '/user/refresh-token',
    method: 'post',
    data: { refresh_token: refreshToken }
  })
}

/**
 * 获取用户列表
 * @param {Object} params - 查询参数
 * @param {number} [params.page=1] - 页码
 * @param {number} [params.page_size=10] - 每页大小
 */
export const getUserList = (params = {}) => {
  return request({
    url: '/user/list',
    method: 'get',
    params: {
      page: 1,
      page_size: 10,
      ...params
    }
  })
}

/**
 * 删除用户
 * @param {number} userId - 用户ID
 */
export const deleteUser = (userId) => {
  return request({
    url: `/user/${userId}`,
    method: 'delete'
  })
}

/**
 * 获取用户个人信息
 */
export const getUserProfile = () => {
  return request({
    url: '/user/profile',
    method: 'get'
  })
}

/**
 * 管理员新建用户（使用注册接口）
 * @param {Object} data - 用户数据 { username, password, email, phone?, real_name? }
 */
export const registerUser = (data) => {
  return request({
    url: '/user/register',
    method: 'post',
    data
  })
}

/**
 * 管理员激活/停用用户
 * @param {number} userId - 用户ID
 * @param {boolean} isActive - 是否激活
 */
export const activateUser = (userId, isActive) => {
  return request({
    url: '/user/activate',
    method: 'post',
    data: { user_id: userId, is_active: isActive }
  })
}

/**
 * 管理员禁用用户（快捷接口，将用户设为未激活）
 * @param {number} userId - 用户ID
 */
export const disableUser = (userId) => {
  return request({
    url: '/user/disable',
    method: 'put',
    data: { user_id: userId }
  })
}

// 移除旧版禁用接口（统一使用上方管理员禁用接口）

/**
 * 修改当前用户密码
 * @param {Object} data - 密码数据
 * @param {string} data.old_password - 旧密码
 * @param {string} data.new_password - 新密码
 */
export const changePassword = (data) => {
  return request({
    url: '/user/password',
    method: 'put',
    data
  })
}

/**
 * 管理员重置指定用户密码
 * @param {number} userId - 用户ID
 * @param {Object} data - 密码数据
 * @param {string} data.new_password - 新密码
 */
export const adminResetPassword = (userId, data) => {
  return request({
    url: `/user/${userId}/password`,
    method: 'put',
    data
  })
}

/**
 * 更新用户个人信息
 * @param {Object} data - 更新数据
 * @param {string} [data.email] - 邮箱 (可选)
 * @param {string} [data.phone] - 手机号 (可选)
 * @param {string} [data.real_name] - 真实姓名 (可选)
 * @param {string} [data.avatar] - 头像URL (可选)
 */
export const updateUserProfile = (data) => {
  return request({
    url: '/user/profile',
    method: 'put',
    data
  })
}

// 默认导出所有接口
export default {
  register,
  login,
  activateUser,
  verifyToken,
  refreshToken,
  getUserList,
  deleteUser,
  getUserProfile,
  disableUser,
  updateUserProfile,
  changePassword,
  adminResetPassword
}