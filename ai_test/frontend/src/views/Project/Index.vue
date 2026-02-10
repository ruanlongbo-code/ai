<template>
  <div class="project-selection-page">
    <!-- 顶部导航 -->
    <div class="top-nav">
      <div class="nav-left">
        <img src="@/assets/images/logo.png" alt="Logo" class="logo-image" />
        <h1 class="logo">AI测试平台</h1>
      </div>
      <div class="nav-right">
        <el-dropdown @command="handleUserAction">
          <div class="user-info">
            <el-avatar :size="32" :src="userStore.user?.avatar">
              {{ userStore.user?.username?.charAt(0).toUpperCase() }}
            </el-avatar>
            <span class="username">{{ userStore.user?.username }}</span>
            <el-icon><ArrowDown /></el-icon>
          </div>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="profile">个人设置</el-dropdown-item>
              <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="main-content">
      <div class="content-header">
        <h2>选择项目</h2>
        <p class="subtitle">请选择一个项目进入测试管理界面</p>
        <el-button type="primary" @click="showCreateDialog = true" class="create-btn">
          <el-icon><Plus /></el-icon>
          新建项目
        </el-button>
      </div>

      <!-- 项目网格 -->
      <div class="project-grid">
        <div
          v-for="project in projects"
          :key="project.id"
          class="project-card"
          
        >
          <div class="project-icon" @click="selectProject(project)">
            <el-icon size="40"><FolderOpened /></el-icon>
          </div>
          <div class="project-info" @click="selectProject(project)">
            <h3 class="project-name">{{ project.name }}</h3>
            <p class="project-desc">{{ project.description }}</p>
            <div class="project-stats">
              <span class="stat-item">
                <el-icon><Connection /></el-icon>
                {{ project.api_case_count }} 接口测试
              </span>
              <span class="stat-item">
                <el-icon><Operation /></el-icon>
                {{ project.functional_case_count }} 功能测试
              </span>
            </div>
            <div class="project-meta">
              <span class="created-date">创建于 {{ formatDate(project.created_at) }}</span>
              <span class="owner-info">负责人: {{ project.owner_name }}</span>
            </div>
          </div>
          <div class="project-actions">
            <el-dropdown @command="(command) => handleProjectAction(command, project)" trigger="click" @click.stop>
              <el-button type="text" class="action-btn">
                <el-icon><MoreFilled /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="edit">编辑项目</el-dropdown-item>
                  <el-dropdown-item command="delete" divided>删除项目</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>

        <!-- 空状态 -->
        <div v-if="projects.length === 0" class="empty-state">
          <el-icon size="80" class="empty-icon"><FolderOpened /></el-icon>
          <h3>暂无项目</h3>
          <p>创建您的第一个测试项目开始使用</p>
          <el-button type="primary" @click="showCreateDialog = true" class="empty-create-btn">
            <el-icon><Plus /></el-icon>
            创建项目
          </el-button>
        </div>
      </div>
    </div>

    <!-- 创建/编辑项目对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      :title="editingProject ? '编辑项目' : '新建项目'"
      width="500px"
      @close="resetForm"
    >
      <el-form
        ref="projectFormRef"
        :model="projectForm"
        :rules="projectRules"
        label-width="80px"
      >
        <el-form-item label="项目名称" prop="name">
          <el-input v-model="projectForm.name" placeholder="请输入项目名称" />
        </el-form-item>
        <el-form-item label="项目描述" prop="description">
          <el-input
            v-model="projectForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入项目描述"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="loading" class="submit-btn">
          {{ editingProject ? '更新' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowDown, Plus, FolderOpened, MoreFilled, Connection, Operation } from '@element-plus/icons-vue'
import { useUserStore, useProjectStore } from '@/stores'
import { getProjectList, createProject, updateProject, deleteProject } from '@/api/project'

const router = useRouter()
const userStore = useUserStore()
const projectStore = useProjectStore()

const showCreateDialog = ref(false)
const loading = ref(false)
const editingProject = ref(null)
const projectFormRef = ref()

const projects = ref([])
const pagination = ref({
  page: 1,
  page_size: 10,
  total: 0,
  total_pages: 0
})

const projectForm = reactive({
  name: '',
  description: ''
})

const projectRules = {
  name: [
    { required: true, message: '请输入项目名称', trigger: 'blur' },
    { min: 2, max: 50, message: '项目名称长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  description: [
    { required: true, message: '请输入项目描述', trigger: 'blur' },
    { max: 200, message: '项目描述不能超过 200 个字符', trigger: 'blur' }
  ]
}

// 获取项目列表
const fetchProjects = async () => {
  try {
    loading.value = true
    const response = await getProjectList({
      page: pagination.value.page,
      page_size: pagination.value.page_size
    })
    
    if (response.data) {
      projects.value = response.data.projects || []
      pagination.value = {
        page: response.data.page || 1,
        page_size: response.data.page_size || 10,
        total: response.data.total || 0,
        total_pages: response.data.total_pages || 0
      }
    }
  } catch (error) {
    console.error('获取项目列表失败:', error)
    ElMessage.error('获取项目列表失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

// 选择项目
const selectProject = (project) => {
  // 将选中的项目信息存储到Pinia
  projectStore.setCurrentProject(project)
  router.push(`/dashboard/${project.id}`)
}

// 用户操作
const handleUserAction = (command) => {
  if (command === 'logout') {
    ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }).then(() => {
      userStore.logout()
      router.push('/login')
    })
  } else if (command === 'profile') {
    ElMessage.info('个人设置功能开发中...')
  }
}

// 项目操作
const handleProjectAction = async (command, project) => {
  if (command === 'edit') {
    editingProject.value = project
    projectForm.name = project.name
    projectForm.description = project.description
    showCreateDialog.value = true
  } else if (command === 'delete') {
    ElMessageBox.confirm(`确定要删除项目"${project.name}"吗？`, '删除确认', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning'
    }).then(async () => {
      try {
        await deleteProject(project.id)
        ElMessage.success('项目删除成功')
        await fetchProjects() // 重新获取项目列表
      } catch (error) {
        console.error('删除项目失败:', error)
        ElMessage.error('删除项目失败，请稍后重试')
      }
    })
  }
}

// 提交表单
const handleSubmit = async () => {
  if (!projectFormRef.value) return
  
  try {
    await projectFormRef.value.validate()
    loading.value = true
    
    if (editingProject.value) {
      // 更新项目
      await updateProject(editingProject.value.id, {
        name: projectForm.name,
        description: projectForm.description
      })
      ElMessage.success('项目更新成功')
    } else {
      // 创建新项目
      await createProject({
        name: projectForm.name,
        description: projectForm.description
      })
      ElMessage.success('项目创建成功')
    }
    
    showCreateDialog.value = false
    resetForm()
    await fetchProjects() // 重新获取项目列表
  } catch (error) {
    console.error('操作失败:', error)
    ElMessage.error('操作失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

// 重置表单
const resetForm = () => {
  editingProject.value = null
  projectForm.name = ''
  projectForm.description = ''
  if (projectFormRef.value) {
    projectFormRef.value.clearValidate()
  }
}

// 格式化日期
const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN')
}

// 获取状态类型 - 移除不再使用的方法

onMounted(() => {
  // 页面加载时获取项目列表
  fetchProjects()
})
</script>

<style scoped>
.project-selection-page {
  min-height: 100vh;
  background: linear-gradient(180deg, #2d1b69 0%, #1a0f3a 100%);
}

.top-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 32px;
  height: 64px;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.nav-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo-image {
  height: 40px;
  width: auto;
}

.logo {
  color: white;
  font-size: 24px;
  font-weight: bold;
  margin: 0;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  color: white;
  cursor: pointer;
  padding: 8px 12px;
  border-radius: 8px;
  transition: background-color 0.3s;
}

.user-info:hover {
  background: rgba(255, 255, 255, 0.1);
}

.username {
  font-size: 14px;
}

.main-content {
  padding: 40px 32px;
  max-width: 1200px;
  margin: 0 auto;
}

.content-header {
  text-align: center;
  margin-bottom: 48px;
}

.content-header h2 {
  color: white;
  font-size: 32px;
  margin: 0 0 8px 0;
  font-weight: 300;
}

.subtitle {
  color: rgba(255, 255, 255, 0.8);
  font-size: 16px;
  margin: 0 0 24px 0;
}

.create-btn {
  background: linear-gradient(135deg, #8b5cf6, #7c3aed);
  border: 1px solid rgba(139, 92, 246, 0.3);
  color: white;
}

.create-btn:hover {
  background: linear-gradient(135deg, #7c3aed, #6d28d9);
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(139, 92, 246, 0.4);
}

.project-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 24px;
}

.project-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  position: relative;
}

.project-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.15);
}

.project-icon {
  text-align: center;
  margin-bottom: 16px;
  color: #8b5cf6;
}

.project-info {
  flex: 1;
}

.project-name {
  font-size: 18px;
  font-weight: 600;
  margin: 0 0 8px 0;
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.project-desc {
  color: #666;
  font-size: 14px;
  margin: 0 0 16px 0;
  line-height: 1.5;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  white-space: normal;
}

.project-stats {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #888;
}

.project-stats {
  display: flex;
  gap: 16px;
  margin: 12px 0;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #8b5cf6;
  font-weight: 500;
}

.stat-item .el-icon {
  font-size: 14px;
}

.project-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
  font-size: 12px;
  color: #999;
}

.created-date {
  color: #999;
}

.owner-info {
  color: #8b5cf6;
  font-weight: 500;
}

.project-actions {
  position: absolute;
  top: 16px;
  right: 16px;
}

.action-btn {
  color: #999;
  padding: 4px;
}

.action-btn:hover {
  color: #333;
}

.empty-state {
  grid-column: 1 / -1;
  text-align: center;
  padding: 80px 20px;
  color: white;
}

.empty-icon {
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 16px;
}

.empty-state h3 {
  font-size: 20px;
  margin: 0 0 8px 0;
  font-weight: 400;
}

.empty-state p {
  color: rgba(255, 255, 255, 0.8);
  margin: 0 0 24px 0;
}

.empty-create-btn {
  background: linear-gradient(135deg, #8b5cf6, #7c3aed);
  border: 1px solid rgba(139, 92, 246, 0.3);
  color: white;
}

.empty-create-btn:hover {
  background: linear-gradient(135deg, #7c3aed, #6d28d9);
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(139, 92, 246, 0.4);
}

.submit-btn {
  background: linear-gradient(135deg, #8b5cf6, #7c3aed);
  border: 1px solid rgba(139, 92, 246, 0.3);
}

.submit-btn:hover {
  background: linear-gradient(135deg, #7c3aed, #6d28d9);
}
</style>