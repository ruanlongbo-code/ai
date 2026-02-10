import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

// 导出标签Store
export { useTabStore } from './tabStore'

export const useUserStore = defineStore('user', () => {
  // 从localStorage恢复用户信息
  const getUserFromStorage = () => {
    try {
      const userStr = localStorage.getItem('user')
      return userStr ? JSON.parse(userStr) : null
    } catch (error) {
      console.error('解析用户信息失败:', error)
      localStorage.removeItem('user')
      return null
    }
  }

  const user = ref(getUserFromStorage())
  const token = ref(localStorage.getItem('token') || '')
  
  const isLoggedIn = computed(() => !!token.value && !!user.value)
  
  const setUser = (userData) => {
    user.value = userData
    if (userData) {
      localStorage.setItem('user', JSON.stringify(userData))
    } else {
      localStorage.removeItem('user')
    }
  }
  
  const setToken = (tokenValue) => {
    token.value = tokenValue
    if (tokenValue) {
      localStorage.setItem('token', tokenValue)
    } else {
      localStorage.removeItem('token')
    }
  }
  
  const logout = () => {
    user.value = null
    token.value = ''
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }
  
  return {
    user,
    token,
    isLoggedIn,
    setUser,
    setToken,
    logout
  }
})

export const useAppStore = defineStore('app', () => {
  const sidebarCollapsed = ref(false)
  const theme = ref('dark')
  
  const toggleSidebar = () => {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }
  
  const setSidebarCollapsed = (collapsed) => {
    sidebarCollapsed.value = collapsed
  }
  
  const setTheme = (newTheme) => {
    theme.value = newTheme
  }
  
  return {
    sidebarCollapsed,
    theme,
    toggleSidebar,
    setSidebarCollapsed,
    setTheme
  }
})

export const useProjectStore = defineStore('project', () => {
  // 从localStorage恢复项目信息
  const getProjectFromStorage = () => {
    try {
      const projectStr = localStorage.getItem('currentProject')
      return projectStr ? JSON.parse(projectStr) : null
    } catch (error) {
      console.error('解析项目信息失败:', error)
      localStorage.removeItem('currentProject')
      return null
    }
  }

  const currentProject = ref(getProjectFromStorage())
  
  const setCurrentProject = (project) => {
    currentProject.value = project
    if (project) {
      localStorage.setItem('currentProject', JSON.stringify(project))
    } else {
      localStorage.removeItem('currentProject')
    }
  }
  
  const clearCurrentProject = () => {
    currentProject.value = null
    localStorage.removeItem('currentProject')
  }
  
  return {
    currentProject,
    setCurrentProject,
    clearCurrentProject
  }
})