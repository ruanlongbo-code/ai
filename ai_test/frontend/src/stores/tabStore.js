import { defineStore } from 'pinia'

export const useTabStore = defineStore('tabs', {
  state: () => ({
    // 标签列表
    tabs: [
      {
        id: 'dashboard',
        title: '仪表盘',
        path: '/dashboard',
        icon: 'DataBoard',
        closable: false,
        active: true,
        timestamp: Date.now()
      }
    ],
    // 当前激活的标签ID
    activeTabId: 'dashboard',
    // 最大标签数量
    maxTabs: 10,
    // 是否启用持久化
    enablePersistence: true
  }),

  getters: {
    // 获取激活的标签
    activeTab: (state) => {
      return state.tabs.find(tab => tab.id === state.activeTabId)
    },
    // 获取可关闭的标签
    closableTabs: (state) => {
      return state.tabs.filter(tab => tab.closable)
    },
    // 按时间排序的标签
    sortedTabs: (state) => {
      return [...state.tabs].sort((a, b) => b.timestamp - a.timestamp)
    }
  },

  actions: {
    // 添加标签
    addTab(tabInfo) {
      const existingTab = this.tabs.find(tab => tab.path === tabInfo.path)
      if (existingTab) {
        this.setActiveTab(existingTab.id)
        existingTab.timestamp = Date.now()
      } else {
        const newTab = {
          id: `tab_${Date.now()}`,
          title: tabInfo.title,
          path: tabInfo.path,
          icon: tabInfo.icon || 'Document',
          closable: tabInfo.path !== '/dashboard',
          active: false,
          timestamp: Date.now()
        }
        
        // 如果超过最大数量，移除最旧的可关闭标签
        if (this.tabs.length >= this.maxTabs) {
          const oldestClosableTab = this.closableTabs
            .sort((a, b) => a.timestamp - b.timestamp)[0]
          if (oldestClosableTab) {
            this.removeTab(oldestClosableTab.id)
          }
        }
        
        this.tabs.push(newTab)
        this.setActiveTab(newTab.id)
      }
      
      if (this.enablePersistence) {
        this.saveToStorage()
      }
    },

    // 移除标签
    removeTab(tabId) {
      const tabIndex = this.tabs.findIndex(tab => tab.id === tabId)
      if (tabIndex === -1) return

      const tab = this.tabs[tabIndex]
      if (!tab.closable) return

      this.tabs.splice(tabIndex, 1)

      // 如果移除的是当前激活标签，需要激活其他标签
      if (this.activeTabId === tabId) {
        if (this.tabs.length > 0) {
          // 优先激活右侧标签，如果没有则激活左侧标签
          const nextTab = this.tabs[tabIndex] || this.tabs[tabIndex - 1]
          this.setActiveTab(nextTab.id)
          return nextTab.path
        }
      }

      if (this.enablePersistence) {
        this.saveToStorage()
      }
    },

    // 设置激活标签
    setActiveTab(tabId) {
      this.tabs.forEach(tab => {
        tab.active = tab.id === tabId
      })
      this.activeTabId = tabId
      
      if (this.enablePersistence) {
        this.saveToStorage()
      }
    },

    // 关闭其他标签
    closeOtherTabs(keepTabId) {
      this.tabs = this.tabs.filter(tab => 
        !tab.closable || tab.id === keepTabId
      )
      
      if (this.enablePersistence) {
        this.saveToStorage()
      }
    },

    // 关闭所有可关闭标签
    closeAllTabs() {
      this.tabs = this.tabs.filter(tab => !tab.closable)
      
      // 激活首页
      const dashboardTab = this.tabs.find(tab => tab.path === '/dashboard')
      if (dashboardTab) {
        this.setActiveTab(dashboardTab.id)
      }
      
      if (this.enablePersistence) {
        this.saveToStorage()
      }
      
      return '/dashboard'
    },

    // 刷新当前标签页面
    refreshTab(tabId) {
      const tab = this.tabs.find(t => t.id === tabId)
      if (tab) {
        // 更新时间戳，触发页面刷新
        tab.timestamp = Date.now()
        
        if (this.enablePersistence) {
          this.saveToStorage()
        }
        
        return tab.path
      }
    },

    // 根据路由信息获取页面标题和图标
    getPageInfo(route) {
      const routeMap = {
        '/dashboard': { title: '仪表盘', icon: 'DataBoard' },
        '/project': { title: '项目管理', icon: 'FolderOpened' },
        '/project-settings/dashboard': { title: '项目概览', icon: 'DataBoard' },
        '/project-settings/environment': { title: '测试环境', icon: 'Platform' },
        '/project-settings/member': { title: '成员管理', icon: 'User' },
        '/project-settings/module': { title: '模块管理', icon: 'Grid' },
        '/project/module': { title: '模块管理', icon: 'Grid' },
        '/project/member': { title: '成员管理', icon: 'User' },
        '/function-test/requirement': { title: '需求管理', icon: 'Document' },
        '/function-test/case': { title: '功能用例', icon: 'DocumentChecked' },
        '/api-test/import': { title: '接口导入', icon: 'Upload' },
        '/api-test/management': { title: '接口管理', icon: 'Connection' },
        '/api-test/base-case': { title: '基础用例管理', icon: 'Files' },
        '/api-test/auto-case': { title: '自动化用例', icon: 'VideoPlay' },
        '/api-test/suite': { title: '测试套件', icon: 'Collection' },
        '/api-test/plan': { title: '测试计划', icon: 'Calendar' },
        '/ui-test/page': { title: '页面管理', icon: 'Monitor' },
        '/ui-test/case': { title: '用例管理', icon: 'View' },
        '/user-management/users': { title: '用户管理', icon: 'UserFilled' },
        '/data-analysis/defect': { title: '缺陷分析', icon: 'PieChart' },
        '/data-analysis/behavior': { title: '用户行为分析', icon: 'TrendCharts' }
      }

      // 优先使用路由 meta（确保编辑页等动态路由显示正确标题与图标）
      if (route.meta && (route.meta.title || route.meta.icon)) {
        return {
          title: route.meta.title || route.name || '未知页面',
          icon: route.meta.icon || 'Document'
        }
      }

      // 精确匹配
      if (routeMap[route.path]) {
        return routeMap[route.path]
      }

      // 动态路由前缀匹配
      for (const [pattern, info] of Object.entries(routeMap)) {
        if (route.path.startsWith(pattern)) {
          return info
        }
      }

      // 特殊处理接口管理页面的动态路由
      if (route.path.includes('/api-management')) {
        return { title: '接口管理', icon: 'Connection' }
      }

      // 默认信息
      return { 
        title: route.name || '未知页面', 
        icon: 'Document' 
      }
    },

    // 保存到本地存储
    saveToStorage() {
      try {
        const data = {
          tabs: this.tabs,
          activeTabId: this.activeTabId
        }
        localStorage.setItem('app_tabs', JSON.stringify(data))
      } catch (error) {
        console.error('保存标签状态失败:', error)
      }
    },

    // 从本地存储恢复
    loadFromStorage() {
      try {
        const data = localStorage.getItem('app_tabs')
        if (data) {
          const parsed = JSON.parse(data)
          if (parsed.tabs && Array.isArray(parsed.tabs)) {
            this.tabs = parsed.tabs
            this.activeTabId = parsed.activeTabId || this.tabs[0]?.id || 'dashboard'
          }
        }
      } catch (error) {
        console.error('恢复标签状态失败:', error)
      }
    },

    // 清除存储
    clearStorage() {
      try {
        localStorage.removeItem('app_tabs')
      } catch (error) {
        console.error('清除标签状态失败:', error)
      }
    }
  }
})