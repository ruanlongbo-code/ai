<template>
  <div class="layout-container">
    <el-container>
      <!-- 侧边栏 -->
      <el-aside :width="sidebarWidth" class="sidebar">
        <div class="logo">
          <h2 v-if="!appStore.sidebarCollapsed">AI测试平台</h2>
          <h2 v-else>AI</h2>
        </div>
        <el-menu
          :default-active="$route.path"
          class="sidebar-menu"
          :collapse="appStore.sidebarCollapsed"
          router
          background-color="transparent"
          text-color="#ffffff"
          active-text-color="#8b5cf6"
        >
          

          <!-- 仪表盘（所有人可见） -->
          <el-menu-item index="/dashboard">
            <el-icon><DataBoard /></el-icon>
            <template #title>仪表盘</template>
          </el-menu-item>

          <!-- 项目管理（仅管理员可见） -->
          <el-sub-menu v-if="isAdmin" index="project-management">
            <template #title>
              <el-icon><Management /></el-icon>
              <span>项目管理</span>
            </template>
            <el-menu-item index="/project/module">
              <el-icon><Grid /></el-icon>
              <template #title>业务线管理</template>
            </el-menu-item>
            <el-menu-item index="/project/member">
              <el-icon><User /></el-icon>
              <template #title>成员管理</template>
            </el-menu-item>
          </el-sub-menu>

          <!-- 测试排期管理 -->
          <el-sub-menu index="schedule">
            <template #title>
              <el-icon><Calendar /></el-icon>
              <span>排期管理</span>
            </template>
            <el-menu-item index="/schedule/iteration">
              <el-icon><List /></el-icon>
              <template #title>排期管理</template>
            </el-menu-item>
            <el-menu-item index="/schedule/dashboard">
              <el-icon><TrendCharts /></el-icon>
              <template #title>进度看板</template>
            </el-menu-item>
            <el-menu-item index="/schedule/daily-report">
              <el-icon><Edit /></el-icon>
              <template #title>测试日报</template>
            </el-menu-item>
            <el-menu-item index="/schedule/feishu">
              <el-icon><ChatDotRound /></el-icon>
              <template #title>飞书群集成</template>
            </el-menu-item>
          </el-sub-menu>

          <!-- 知识库 -->
          <el-sub-menu index="knowledge">
            <template #title>
              <el-icon><Collection /></el-icon>
              <span>知识库</span>
            </template>
            <el-menu-item index="/knowledge/document">
              <el-icon><FolderOpened /></el-icon>
              <template #title>文档管理</template>
            </el-menu-item>
            <el-menu-item index="/knowledge/search">
              <el-icon><Search /></el-icon>
              <template #title>知识检索</template>
            </el-menu-item>
            <el-menu-item index="/knowledge/case-set">
              <el-icon><Notebook /></el-icon>
              <template #title>用例集</template>
            </el-menu-item>
          </el-sub-menu>

          <!-- 功能测试 -->
          <el-sub-menu index="function-test">
            <template #title>
              <el-icon><Operation /></el-icon>
              <span>功能测试</span>
            </template>
            <el-menu-item index="/function-test/requirement">
              <el-icon><Document /></el-icon>
              <template #title>需求管理</template>
            </el-menu-item>
            <el-menu-item index="/function-test/case">
              <el-icon><List /></el-icon>
              <template #title>功能用例</template>
            </el-menu-item>
          </el-sub-menu>

          <!-- 接口测试 -->
          <el-sub-menu index="api-test">
            <template #title>
              <el-icon><Connection /></el-icon>
              <span>接口测试</span>
            </template>
            <el-menu-item index="/api-test/import">
              <el-icon><Upload /></el-icon>
              <template #title>接口导入</template>
            </el-menu-item>
            <el-menu-item :index="`/project/${projectStore.currentProject.id}/api-management`">
              <el-icon><Setting /></el-icon>
              <template #title>接口管理</template>
            </el-menu-item>
            <el-menu-item index="/api-test/base-case">
              <el-icon><Files /></el-icon>
              <template #title>API测试点管理</template>
            </el-menu-item>
            <el-menu-item index="/api-test/auto-case">
              <el-icon><VideoPlay /></el-icon>
              <template #title>自动化用例</template>
            </el-menu-item>
            <el-menu-item index="/api-test/suite">
              <el-icon><Collection /></el-icon>
              <template #title>测试套件</template>
            </el-menu-item>
            <el-menu-item index="/api-test/plan">
              <el-icon><Calendar /></el-icon>
              <template #title>测试计划</template>
            </el-menu-item>
          </el-sub-menu>

          <!-- UI测试 -->
          <el-sub-menu index="ui-test">
            <template #title>
              <el-icon><Monitor /></el-icon>
              <span>UI测试</span>
            </template>
            <el-menu-item index="/ui-test/page">
              <el-icon><Notebook /></el-icon>
              <template #title>页面管理</template>
            </el-menu-item>
            <el-menu-item index="/ui-test/case">
              <el-icon><List /></el-icon>
              <template #title>用例管理</template>
            </el-menu-item>
          </el-sub-menu>


          <!-- 用户管理 -->
          <el-sub-menu v-if="isAdmin" index="user-management">
            <template #title>
              <el-icon><User /></el-icon>
              <span>管理员工作台</span>
            </template>
            <el-menu-item index="/user-management/users">
              <el-icon><Avatar /></el-icon>
              <template #title>用户管理</template>
            </el-menu-item>
          </el-sub-menu>

          <!-- 未来可期 -->
          <el-menu-item index="/coming-soon">
            <el-icon><MagicStick /></el-icon>
            <template #title>未来可期</template>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <!-- 主内容区域 -->
      <el-container>
        <!-- 顶部导航 -->
        <el-header class="header">
          <div class="header-left">
            <el-button
              type="text"
              @click="appStore.toggleSidebar"
              class="collapse-btn"
            >
              <el-icon><Expand v-if="appStore.sidebarCollapsed" /><Fold v-else /></el-icon>
            </el-button>
            <el-button
              type="primary"
              @click="goToProjectList"
              class="back-to-projects-btn"
            >
              <el-icon><Back /></el-icon>
              返回项目列表
            </el-button>
          </div>
          <div class="header-center">
            <h3 class="current-project-name" style="color: cornsilk">{{ currentProjectName }}</h3>
          </div>
          <div class="header-right">
            <el-dropdown @command="handleCommand">
              <span class="user-dropdown">
                <el-avatar :size="32" :src="userStore.user?.avatar || ''">
                  {{ userStore.user?.real_name?.charAt(0) || userStore.user?.username?.charAt(0) || 'U' }}
                </el-avatar>
                <span class="username">{{ userStore.user?.real_name || userStore.user?.username || '用户' }}</span>
                <el-icon><ArrowDown /></el-icon>
              </span>
              <template #dropdown>
                <el-dropdown-menu>

                  <el-dropdown-item command="change_password">修改密码</el-dropdown-item>
                  <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </el-header>

        <!-- 标签栏 -->
        <TabBar />

        <!-- 主内容 -->
        <el-main class="main-content">
          <router-view >

          </router-view>
        </el-main>

        <!-- 修改密码弹窗 -->
        <el-dialog v-model="changePwdDialogVisible" title="修改密码" width="480px" :close-on-click-modal="false">
          <el-form ref="changePwdFormRef" :model="changePwdForm" :rules="changePwdRules" label-width="110px">
            <el-form-item label="旧密码" prop="old_password">
              <el-input v-model="changePwdForm.old_password" type="password" show-password placeholder="请输入旧密码" />
            </el-form-item>
            <el-form-item label="新密码" prop="new_password">
              <el-input v-model="changePwdForm.new_password" type="password" show-password placeholder="请输入新密码" />
            </el-form-item>
            <el-form-item label="确认新密码" prop="confirm_password">
              <el-input v-model="changePwdForm.confirm_password" type="password" show-password placeholder="请再次输入新密码" />
            </el-form-item>
          </el-form>
          <template #footer>
            <span class="dialog-footer">
              <el-button @click="changePwdDialogVisible = false">取消</el-button>
              <el-button type="primary" :loading="changePwdLoading" @click="confirmChangePassword">确定</el-button>
            </span>
          </template>
        </el-dialog>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
import { computed, ref, onMounted, watch, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAppStore, useUserStore, useProjectStore, useTabStore } from '../stores'
import { ElMessage } from 'element-plus'
import { getProjectDetail } from '../api/project'
import { changePassword } from '@/api/user'
import TabBar from './TabBar.vue'

const router = useRouter()
const route = useRoute()
const appStore = useAppStore()
const userStore = useUserStore()
const projectStore = useProjectStore()
const tabStore = useTabStore()

// 仅管理员可见的菜单控制（以后端 is_superuser 字段为准）
const isAdmin = computed(() => {
  const u = userStore.user || {}
  return u.is_superuser === true
})

// 判断是否为项目负责人（当前项目 owner_id 与当前用户 id 一致）
const isProjectOwner = computed(() => {
  const u = userStore.user || {}
  const userId = u.id ?? u.user_id
  const ownerId = projectStore.currentProject?.owner_id
  if (userId == null || ownerId == null) return false
  return Number(userId) === Number(ownerId)
})

// 成员管理菜单显示：管理员或项目负责人
const canManageMembers = computed(() => {
  return isAdmin.value || isProjectOwner.value
})

// 从Pinia获取当前项目名称，如果没有则显示默认名称
const currentProjectName = computed(() => {
  return projectStore.currentProject?.name || 'AI测试平台'
})

const sidebarWidth = computed(() => {
  return appStore.sidebarCollapsed ? '64px' : '240px'
})

// 获取当前项目信息
const fetchCurrentProject = async () => {
  try {
    // 多种方式获取项目ID
    let projectId = route.params.projectId
    
    // 如果路由参数中没有项目ID，尝试从Pinia store获取
    if (!projectId && projectStore.currentProject?.id) {
      projectId = projectStore.currentProject.id
    }
    
    // 如果还是没有，尝试从localStorage获取
    if (!projectId) {
      try {
        const projectStr = localStorage.getItem('currentProject')
        if (projectStr) {
          const project = JSON.parse(projectStr)
          projectId = project.id
        }
      } catch (error) {
        console.error('解析localStorage项目信息失败:', error)
      }
    }
    
    // 确保项目ID存在且有效
    if (projectId && projectId !== 'undefined' && projectId !== undefined) {
      const response = await getProjectDetail(projectId)
      if (response.data) {
        // 将项目信息存储到Pinia中
        projectStore.setCurrentProject(response.data)
      }
    } else {
      console.warn('无法获取有效的项目ID，跳过项目详情获取')
    }
  } catch (error) {
    console.error('获取项目信息失败:', error)
    // 如果是404错误，说明项目不存在，清除本地存储的项目信息
    if (error.response?.status === 404) {
      projectStore.clearCurrentProject()
    }
  }
}

// 返回项目列表
const goToProjectList = () => {
  // 清除Pinia中的项目信息
  projectStore.clearCurrentProject()
  router.push('/project')
}

// 监听路由变化，更新项目信息和标签
watch(() => route.params.projectId, () => {
  fetchCurrentProject()
})

// 监听路由变化，自动添加标签
watch(route, (newRoute) => {
  // 排除登录页面
  if (newRoute.path !== '/login' && newRoute.path !== '/') {
    const pageInfo = tabStore.getPageInfo(newRoute)
    tabStore.addTab({
      title: pageInfo.title,
      path: newRoute.path,
      icon: pageInfo.icon
    })
  }
}, { immediate: true })

onMounted(() => {
  fetchCurrentProject()
  // 从本地存储恢复标签状态
  tabStore.loadFromStorage()
})

// 修改密码对话框与表单
const changePwdDialogVisible = ref(false)
const changePwdLoading = ref(false)
const changePwdFormRef = ref()
const changePwdForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: ''
})
const changePwdRules = {
  old_password: [
    { required: true, message: '请输入旧密码', trigger: 'blur' }
  ],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, max: 128, message: '密码长度在 6 到 128 个字符', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    { validator: (_rule, value, callback) => {
        if (value !== changePwdForm.new_password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      }, trigger: 'blur' }
  ]
}

const handleCommand = (command) => {
  switch (command) {
    case 'change_password':
      changePwdForm.old_password = ''
      changePwdForm.new_password = ''
      changePwdForm.confirm_password = ''
      changePwdDialogVisible.value = true
      break
    case 'logout':
      userStore.logout()
      router.push('/login')
      ElMessage.success('退出登录成功')
      break
  }
}

const confirmChangePassword = async () => {
  if (!changePwdFormRef.value) return
  try {
    await changePwdFormRef.value.validate()
    if (changePwdForm.old_password === changePwdForm.new_password) {
      ElMessage.warning('新密码不能与旧密码相同')
      return
    }
    changePwdLoading.value = true
    await changePassword({
      old_password: changePwdForm.old_password,
      new_password: changePwdForm.new_password
    })
    ElMessage.success('密码修改成功')
    changePwdDialogVisible.value = false
  } catch (error) {
    console.error('修改密码失败:', error)
    const msg = error?.response?.data?.detail || '修改密码失败'
    ElMessage.error(msg)
  } finally {
    changePwdLoading.value = false
  }
}
</script>

<style scoped>
.layout-container {
  height: 100vh;
  background: linear-gradient(180deg, #2d1b69 0%, #1a0f3a 100%);
}

.sidebar {
  background: rgba(0, 0, 0, 0.2);
  backdrop-filter: blur(10px);
  border-right: 1px solid rgba(139, 92, 246, 0.2);
  transition: width 0.3s ease;
  overflow-y: auto;
  height: 100vh;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-bottom: 1px solid rgba(139, 92, 246, 0.2);
  margin-bottom: 20px;
}

.logo h2 {
  color: #8b5cf6;
  margin: 0;
  font-weight: bold;
  background: linear-gradient(135deg, #8b5cf6, #7c3aed);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.sidebar-menu {
  border: none;
}

.sidebar-menu .el-menu-item {
  border-radius: 8px;
  margin: 4px 12px;
  transition: all 0.3s ease;
}

.sidebar-menu .el-menu-item:hover {
  background: rgba(139, 92, 246, 0.2);
  transform: translateX(4px);
}

.sidebar-menu .el-menu-item.is-active {
  background: linear-gradient(135deg, #8b5cf6, #7c3aed);
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.3);
  color: #ffffff !important;
}

.sidebar-menu .el-menu-item.is-active .el-icon {
  color: #ffffff !important;
}

.sidebar-menu .el-sub-menu.is-active > .el-sub-menu__title {
  color: #8b5cf6 !important;
}

.sidebar-menu .el-sub-menu .el-menu-item.is-active {
  background: linear-gradient(135deg, #8b5cf6, #7c3aed);
  color: #ffffff !important;
}

.header {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(139, 92, 246, 0.2);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
}

.header-left {
  display: flex;
  align-items: center;
}

.collapse-btn {
  color: #ffffff;
  font-size: 18px;
}

.collapse-btn:hover {
  color: #8b5cf6;
}

.back-to-projects-btn {
  font-weight: normal !important;
  background-color: rgba(139, 92, 246, 0.15) !important;
  border-color: rgba(139, 92, 246, 0.3) !important;
  margin-left: 12px;
}

.back-to-projects-btn:hover {
  background-color: rgba(139, 92, 246, 0.25) !important;
  border-color: rgba(139, 92, 246, 0.5) !important;
}

.header-right {
  display: flex;
  align-items: center;
}

.user-dropdown {
  display: flex;
  align-items: center;
  cursor: pointer;
  color: #ffffff;
  padding: 8px 12px;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.user-dropdown:hover {
  background: rgba(139, 92, 246, 0.2);
}

.username {
  margin: 0 8px;
  font-size: 14px;
}

.main-content {
  background: #ffffff;
  border-radius: 12px;
  margin: 5px;
  padding: 10px;
  height: calc(100vh - 160px);
  overflow-y: auto;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

/* 左侧菜单滚动条样式 */
.sidebar::-webkit-scrollbar {
  width: 6px;
}

.sidebar::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
}

.sidebar::-webkit-scrollbar-thumb {
  background: rgba(139, 92, 246, 0.5);
  border-radius: 3px;
}

.sidebar::-webkit-scrollbar-thumb:hover {
  background: rgba(139, 92, 246, 0.7);
}

/* 主内容区滚动条样式 */
.main-content::-webkit-scrollbar {
  width: 6px;
}

.main-content::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
}

.main-content::-webkit-scrollbar-thumb {
  background: rgba(139, 92, 246, 0.5);
  border-radius: 3px;
}

.main-content::-webkit-scrollbar-thumb:hover {
  background: rgba(139, 92, 246, 0.7);
}
</style>