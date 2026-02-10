/**
 * 认证相关工具函数
 */
import { useUserStore } from '@/stores'
import { getUserProfile } from '@/api/user'

/**
 * 初始化用户信息
 * 在应用启动时调用，验证token并恢复用户信息
 */
export const initUserInfo = async () => {
  const userStore = useUserStore()
  
  // 如果没有token，直接返回
  if (!userStore.token) {
    return false
  }
  
  // 如果已经有用户信息，检查token是否有效
  if (userStore.user) {
    try {
      // 验证token有效性
      await getUserProfile()
      return true
    } catch (error) {
      console.warn('Token已失效，清除用户信息')
      userStore.logout()
      return false
    }
  }
  
  // 如果有token但没有用户信息，尝试获取用户信息
  try {
    const response = await getUserProfile()
    if (response.data) {
      userStore.setUser(response.data)
      return true
    }
  } catch (error) {
    console.warn('获取用户信息失败，清除token')
    userStore.logout()
  }
  
  return false
}

/**
 * 检查用户是否已登录
 */
export const isAuthenticated = () => {
  const userStore = useUserStore()
  return userStore.isLoggedIn
}

/**
 * 获取当前用户信息
 */
export const getCurrentUser = () => {
  const userStore = useUserStore()
  return userStore.user
}

/**
 * 获取当前token
 */
export const getToken = () => {
  const userStore = useUserStore()
  return userStore.token
}