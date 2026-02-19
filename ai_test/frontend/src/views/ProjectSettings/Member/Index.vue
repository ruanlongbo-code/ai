<template>
  <div class="member-management">
    <div class="page-header">
      <h1>项目成员管理</h1>
      <p>管理项目团队成员权限</p>
    </div>

    <!-- 操作栏 -->
    <div class="action-bar">
      <el-button
          v-if="canManageMembers"
          type="primary"
          @click="showAddMemberDialog"
          :loading="loading"
      >
        <el-icon>
          <Plus/>
        </el-icon>
        添加成员
      </el-button>
      <el-button @click="refreshMembers" :loading="loading">
        <el-icon>
          <Refresh/>
        </el-icon>
        刷新
      </el-button>
    </div>

    <!-- 成员列表 -->
    <div class="member-card">
      <el-table
          v-loading="loading"
          :data="memberList"
          stripe
          style="width: 100%"
          empty-text="暂无成员数据"
      >
        <el-table-column prop="id" label="ID" width="80"/>
        <el-table-column prop="username" label="用户名" min-width="150"/>
        <el-table-column prop="real_name" label="真实姓名" min-width="120">
          <template #default="{ row }">
            {{ row.real_name || '未设置' }}
          </template>
        </el-table-column>
        <el-table-column prop="role_name" label="角色" width="120">
          <template #default="{ row }">
            <el-tag
                :type="getRoleTagType(row.role)"
                size="small"
            >
              {{ row.role_name }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag
                :type="row.status === 1 ? 'success' : 'danger'"
                size="small"
            >
              {{ row.status === 1 ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="加入时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column
            v-if="canManageMembers"
            label="操作"
            width="280"
            fixed="right"
        >
          <template #default="{ row }">
            <el-button
                type="primary"
                size="small"
                @click="showEditRoleDialog(row)"
                :disabled="row.role === 2 && !currentUser?.is_superuser"
            >
              编辑角色
            </el-button>
            <el-button
                :type="row.status === 1 ? 'warning' : 'success'"
                size="small"
                @click="toggleMemberStatus(row)"
                :disabled="row.role === 2 && !currentUser?.is_superuser"
            >
              {{ row.status === 1 ? '禁用' : '启用' }}
            </el-button>
            <el-button
                type="danger"
                size="small"
                @click="removeMember(row)"
                :disabled="row.role === 2 && !currentUser?.is_superuser"
            >
              移除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 添加成员对话框 -->
    <el-dialog
        v-model="addMemberDialogVisible"
        title="添加项目成员"
        width="600px"
        :close-on-click-modal="false"
        class="add-member-dialog"
    >
      <el-form
          ref="addMemberFormRef"
          :model="addMemberForm"
          :rules="addMemberRules"
          label-width="100px"
          class="add-member-form"
      >
        <el-form-item label="选择用户" prop="user_id">
          <el-select
              v-model="addMemberForm.user_id"
              placeholder="请输入用户名搜索用户"
              filterable
              remote
              :remote-method="searchUsers"
              :loading="userSearchLoading"
              style="width: 100%"
              clearable
              no-data-text="暂无用户数据，请输入用户名搜索"
              loading-text="正在搜索用户..."
              reserve-keyword
              :popper-class="'user-select-dropdown'"
          >
            <el-option
                v-for="user in availableUsers"
                :key="user.id"
                :label="user.username"
                :value="user.id"
                class="user-select-option"
            >
              <div class="user-option">
                <el-avatar :size="28" class="user-avatar">
                  {{ user.username?.charAt(0) }}
                </el-avatar>
                <div class="user-info">
                  <span class="user-name">{{ user.username }}</span>
                  <span class="user-email" v-if="user.email">{{ user.email }}</span>
                </div>
              </div>
            </el-option>
          </el-select>
          <div class="form-tip">
            <el-icon>
              <Search/>
            </el-icon>
            请输入用户名进行搜索，支持模糊匹配
          </div>
        </el-form-item>

        <el-form-item label="角色权限" prop="role">
          <div class="role-selection">
            <div class="role-cards">
              <div
                  v-for="role in roleOptions"
                  :key="role.value"
                  class="role-card"
                  :class="{ 'selected': addMemberForm.role === role.value }"
                  @click="addMemberForm.role = role.value"
              >
                <div class="role-icon">
                  <el-icon :size="20">
                    <component :is="role.icon"/>
                  </el-icon>
                </div>
                <div class="role-info">
                  <div class="role-name">{{ role.name }}</div>
                  <div class="role-desc">{{ role.description }}</div>
                </div>
                <div class="role-check">
                  <el-icon v-if="addMemberForm.role === role.value" color="#409EFF">
                    <Check/>
                  </el-icon>
                </div>
              </div>
            </div>
          </div>
        </el-form-item>

        <el-form-item label="启用状态" prop="status">
          <el-switch
              v-model="addMemberForm.status"
              :active-value="true"
              :inactive-value="false"
              active-text="启用"
              inactive-text="禁用"
              style="--el-switch-on-color: #13ce66; --el-switch-off-color: #ff4949"
          />
          <div class="form-tip">设置成员的初始状态，禁用后成员无法访问项目</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="addMemberDialogVisible = false">取消</el-button>
          <el-button
              type="primary"
              @click="confirmAddMember"
              :loading="addMemberLoading"
          >
            确认添加
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 编辑角色对话框 -->
    <el-dialog
        v-model="editRoleDialogVisible"
        title="编辑成员角色"
        width="480px"
        :close-on-click-modal="false"
        class="edit-role-dialog"
    >
      <div class="edit-role-content">
        <!-- 用户信息卡片 -->
        <div class="user-info-card">
          <div class="user-avatar">
            <el-avatar :size="50">{{ currentEditMember?.real_name?.charAt(0) }}</el-avatar>
          </div>
          <div class="user-details">
            <h3>{{ currentEditMember?.real_name }}</h3>
            <div class="current-role">
              <span>账号：</span>
              <el-tag>
                {{ currentEditMember?.username }}
              </el-tag>
              <span>当前角色：</span>
              <el-tag :type="getRoleTagType(currentEditMember?.role)" size="small">
                {{ currentEditMember?.role_name }}
              </el-tag>
            </div>
          </div>
        </div>

        <!-- 角色选择 -->
        <div class="role-selection">
          <h4>选择新角色</h4>
          <div class="role-cards">
            <div
                v-for="role in roleOptions"
                :key="role.value"
                class="role-card"
                :class="{ 'selected': editRoleForm.role === role.value }"
                @click="editRoleForm.role = role.value"
            >
              <div class="role-icon">
                <el-icon :size="24">
                  <component :is="role.icon"/>
                </el-icon>
              </div>
              <div class="role-info">
                <div class="role-name">{{ role.name }}</div>
                <div class="role-desc">{{ role.description }}</div>
              </div>
              <div class="role-check">
                <el-icon v-if="editRoleForm.role === role.value" color="#409EFF">
                  <Check/>
                </el-icon>
              </div>
            </div>
          </div>
        </div>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="editRoleDialogVisible = false">取消</el-button>
          <el-button
              type="primary"
              @click="confirmEditRole"
              :loading="editRoleLoading"
          >
            确认修改
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import {ref, reactive, onMounted, computed} from 'vue'
import {ElMessage, ElMessageBox} from 'element-plus'
import {Plus, Refresh, View, Edit, Check, Search} from '@element-plus/icons-vue'
import {useProjectStore, useUserStore} from '@/stores'
import {
  getProjectMembers,
  addProjectMember,
  removeProjectMember,
  updateProjectMemberStatus,
  updateProjectMemberRole,
  getProjectDetail
} from '@/api/project'
import {getUserList} from '@/api/user'

const projectStore = useProjectStore()
const userStore = useUserStore()

// 从Pinia获取当前选中的项目ID
const projectId = computed(() => {
  return projectStore.currentProject?.id || null
})

// 响应式数据
const loading = ref(false)
const memberList = ref([])
const currentProject = ref(null)
const currentUser = ref(null)

// 添加成员相关
const addMemberDialogVisible = ref(false)
const addMemberLoading = ref(false)
const userSearchLoading = ref(false)
const availableUsers = ref([])
const addMemberForm = reactive({
  user_id: null,
  role: 1,
  status: true
})

// 编辑角色相关
const editRoleDialogVisible = ref(false)
const editRoleLoading = ref(false)
const currentEditMember = ref(null)
const editRoleForm = reactive({
  role: 1
})

// 角色选项配置
const roleOptions = [
  {
    value: 0,
    name: '只读成员',
    description: '只能查看项目信息，无法进行任何操作',
    icon: View
  },
  {
    value: 1,
    name: '可操作成员',
    description: '可以进行项目相关操作，但无法管理成员',
    icon: Edit
  }
]

// 表单验证规则
const addMemberRules = {
  user_id: [
    {required: true, message: '请选择要添加的用户', trigger: 'change'}
  ],
  role: [
    {required: true, message: '请选择角色权限', trigger: 'change'}
  ],
  status: [
    {required: true, message: '请选择启用状态', trigger: 'change'}
  ]
}

// 权限控制
const canManageMembers = computed(() => {
  if (!currentUser.value || !currentProject.value) return false
  return currentUser.value.is_superuser || currentProject.value.owner_id === currentUser.value.id
})

// 获取角色标签类型
const getRoleTagType = (role) => {
  switch (role) {
    case 0:
      return 'info'
    case 1:
      return 'success'
    case 2:
      return 'warning'
    default:
      return 'info'
  }
}

// 格式化日期时间
const formatDateTime = (dateString) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleString('zh-CN')
}

// 获取项目成员列表
const fetchProjectMembers = async () => {
  if (!projectId.value) {
    ElMessage.error('未找到项目信息，请重新选择项目')
    return
  }

  try {
    loading.value = true
    const response = await getProjectMembers(projectId.value)
    memberList.value = response.data.members || []
  } catch (error) {
    console.error('获取项目成员失败:', error)
    ElMessage.error('获取项目成员失败')
  } finally {
    loading.value = false
  }
}

// 刷新成员列表
const refreshMembers = async () => {
  await fetchProjectMembers()
  ElMessage.success('刷新成功')
}

// 获取项目详情
const fetchProjectDetail = async () => {
  if (!projectId.value) {
    ElMessage.error('未找到项目信息，请重新选择项目')
    return
  }

  try {
    const response = await getProjectDetail(projectId.value)
    currentProject.value = response.data
  } catch (error) {
    console.error('获取项目详情失败:', error)
  }
}

// 搜索用户
const searchUsers = async (query) => {
  if (!query || query.trim().length < 1) {
    availableUsers.value = []
    return
  }

  try {
    userSearchLoading.value = true
    const response = await getUserList({
      page: 1,
      page_size: 100,
      username: query.trim()
    })

    // 过滤掉已经是项目成员的用户
    const existingUserIds = memberList.value.map(member => member.user_id)
    const filteredUsers = (response.data.users || []).filter(
        user => !existingUserIds.includes(user.id)
    )

    availableUsers.value = filteredUsers

    // 如果没有搜索结果，显示提示
    if (filteredUsers.length === 0 && query.trim().length > 0) {
      console.log('未找到匹配的用户')
    }
  } catch (error) {
    console.error('搜索用户失败:', error)
    ElMessage.error('搜索用户失败，请稍后重试')
    availableUsers.value = []
  } finally {
    userSearchLoading.value = false
  }
}

// 显示添加成员对话框
const showAddMemberDialog = () => {
  addMemberForm.user_id = null
  addMemberForm.role = 1
  addMemberForm.status = true
  availableUsers.value = []
  addMemberDialogVisible.value = true
}

// 确认添加成员
const confirmAddMember = async () => {
  if (!projectId.value) {
    ElMessage.error('未找到项目信息，请重新选择项目')
    return
  }

  try {
    await addMemberFormRef.value.validate()
    addMemberLoading.value = true

    await addProjectMember(projectId.value, {
      user_id: addMemberForm.user_id,
      role: addMemberForm.role,
      status: addMemberForm.status
    })

    ElMessage.success('添加成员成功')
    addMemberDialogVisible.value = false
    await fetchProjectMembers()
  } catch (error) {
    console.error('添加成员失败:', error)
    ElMessage.error(error.response?.data?.detail || '添加成员失败')
  } finally {
    addMemberLoading.value = false
  }
}

// 显示编辑角色对话框
const showEditRoleDialog = (member) => {
  currentEditMember.value = member
  editRoleForm.role = member.role
  editRoleDialogVisible.value = true
}

// 确认编辑角色
const confirmEditRole = async () => {
  if (!projectId.value) {
    ElMessage.error('未找到项目信息，请重新选择项目')
    return
  }

  try {
    editRoleLoading.value = true

    await updateProjectMemberRole(
        projectId.value,
        currentEditMember.value.user_id,
        {role: editRoleForm.role}
    )

    ElMessage.success('修改角色成功')
    editRoleDialogVisible.value = false
    await fetchProjectMembers()
  } catch (error) {
    console.error('修改角色失败:', error)
    ElMessage.error(error.response?.data?.detail || '修改角色失败')
  } finally {
    editRoleLoading.value = false
  }
}

// 切换成员状态
const toggleMemberStatus = async (member) => {
  if (!projectId.value) {
    ElMessage.error('未找到项目信息，请重新选择项目')
    return
  }

  const newStatus = member.status === 1 ? 0 : 1
  const statusText = newStatus === 1 ? '启用' : '禁用'

  try {
    await ElMessageBox.confirm(
        `确定要${statusText}用户 ${member.username} 吗？`,
        '确认操作',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }
    )

    await updateProjectMemberStatus(
        projectId.value,
        member.user_id,
        {status: newStatus}
    )

    ElMessage.success(`${statusText}成员成功`)
    await fetchProjectMembers()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('更新成员状态失败:', error)
      ElMessage.error(error.response?.data?.detail || '更新成员状态失败')
    }
  }
}

// 移除成员
const removeMember = async (member) => {
  if (!projectId.value) {
    ElMessage.error('未找到项目信息，请重新选择项目')
    return
  }

  try {
    await ElMessageBox.confirm(
        `确定要移除用户 ${member.username} 吗？此操作不可撤销。`,
        '确认移除',
        {
          confirmButtonText: '确定移除',
          cancelButtonText: '取消',
          type: 'warning'
        }
    )

    await removeProjectMember(projectId.value, member.user_id)
    ElMessage.success('移除成员成功')
    await fetchProjectMembers()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('移除成员失败:', error)
      ElMessage.error(error.response?.data?.detail || '移除成员失败')
    }
  }
}

// 获取当前用户信息
const getCurrentUser = () => {
  // 从用户状态管理中获取当前用户信息
  currentUser.value = userStore.user
}

// 组件挂载时获取数据
onMounted(async () => {
  getCurrentUser()
  await Promise.all([
    fetchProjectDetail(),
    fetchProjectMembers()
  ])
})

// 模板引用
const addMemberFormRef = ref()
const editRoleFormRef = ref()
</script>

<style scoped>
.member-management {
  padding: 24px;
  background: #ffffff;
  min-height: 100vh;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h1 {
  color: #1f2937;
  margin: 0 0 8px 0;
  font-size: 28px;
  font-weight: bold;
}

.page-header p {
  color: #6b7280;
  margin: 0;
  font-size: 14px;
}

.action-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
  align-items: center;
}

.action-bar .el-button {
  height: 40px;
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.action-bar .el-button--primary {
  background: linear-gradient(135deg, #8b5cf6, #7c3aed);
  border: none;
  color: #ffffff;
  box-shadow: 0 2px 4px rgba(139, 92, 246, 0.2);
}

.action-bar .el-button--primary:hover {
  background: linear-gradient(135deg, #7c3aed, #6d28d9);
  box-shadow: 0 4px 8px rgba(139, 92, 246, 0.3);
  transform: translateY(-1px);
}

.action-bar .el-button:not(.el-button--primary) {
  background: #ffffff;
  border: 1px solid #d1d5db;
  color: #374151;
}

.action-bar .el-button:not(.el-button--primary):hover {
  background: #f9fafb;
  border-color: #9ca3af;
  transform: translateY(-1px);
}

.member-card {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.role-description {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
  line-height: 1.4;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

/* Element Plus 表格样式覆盖 */
:deep(.el-table) {
  background: #ffffff;
  color: #1f2937;
}

:deep(.el-table th.el-table__cell) {
  background: #f8fafc;
  border-bottom: 1px solid #e5e7eb;
  color: #374151;
  font-weight: 600;
}

:deep(.el-table td.el-table__cell) {
  border-bottom: 1px solid #f3f4f6;
  color: #1f2937;
}

:deep(.el-table--striped .el-table__body tr.el-table__row--striped td) {
  background: #f9fafb;
}

:deep(.el-table__body tr:hover > td) {
  background: #f9fafb !important;
}

:deep(.el-table__empty-text) {
  color: #6b7280;
}

/* Element Plus 按钮样式覆盖 */
:deep(.el-button--primary) {
  background: linear-gradient(135deg, #8b5cf6, #7c3aed);
  border: none;
  color: #ffffff;
  box-shadow: 0 2px 4px rgba(139, 92, 246, 0.2);
}

:deep(.el-button--primary:hover) {
  background: linear-gradient(135deg, #7c3aed, #6d28d9);
  box-shadow: 0 4px 8px rgba(139, 92, 246, 0.3);
}

:deep(.el-button--success) {
  background: linear-gradient(135deg, #10b981, #059669);
  border: none;
  color: #ffffff;
}

:deep(.el-button--warning) {
  background: linear-gradient(135deg, #f59e0b, #d97706);
  border: none;
  color: #ffffff;
}

:deep(.el-button--danger) {
  background: linear-gradient(135deg, #ef4444, #dc2626);
  border: none;
  color: #ffffff;
}

/* 编辑角色对话框样式 */
.edit-role-dialog :deep(.el-dialog) {
  border-radius: 12px;
  overflow: hidden;
}

.edit-role-content {
  padding: 0;
}

.user-info-card {
  display: flex;
  align-items: center;
  padding: 20px;

  margin-bottom: 24px;
}

.user-avatar {
  margin-right: 16px;
}

.user-details h3 {
  margin: 0 0 8px 0;
  color: #1e293b;
  font-size: 18px;
  font-weight: 600;
}

.current-role {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #64748b;
}

.role-selection {
  padding: 0 20px 20px 20px;
}

.role-selection h4 {
  margin: 0 0 16px 0;
  color: #1e293b;
  font-size: 16px;
  font-weight: 600;
}

.role-cards {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.role-card {
  display: flex;
  align-items: center;
  padding: 16px;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: #ffffff;
}

.role-card:hover {
  border-color: #8b5cf6;
  background: #faf5ff;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.15);
}

.role-card.selected {
  border-color: #8b5cf6;
  background: linear-gradient(135deg, #faf5ff, #f3e8ff);
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.2);
}

.role-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: #f8fafc;
  border-radius: 8px;
  margin-right: 12px;
  color: #64748b;
}

.role-card.selected .role-icon {
  background: #8b5cf6;
  color: #ffffff;
}

.role-info {
  flex: 1;
}

.role-name {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 4px;
}

.role-desc {
  font-size: 14px;
  color: #64748b;
  line-height: 1.4;
}

.role-check {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
}

/* 添加成员对话框样式 */
.add-member-dialog :deep(.el-dialog) {
  border-radius: 12px;
  overflow: hidden;
}

.add-member-form {
  padding: 0;
}

.add-member-form .el-form-item {
  margin-bottom: 24px;
}

.add-member-form .el-form-item__label {
  color: #374151;
  font-weight: 600;
  font-size: 14px;
}

.user-option {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 8px 0;
}

.user-avatar {
  flex-shrink: 0;
}

.user-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.user-name {
  font-weight: 500;
  color: #1f2937;
  font-size: 14px;
  line-height: 1.2;
}

.user-email {
  font-size: 12px;
  color: #6b7280;
  line-height: 1.2;
}

.form-tip {
  font-size: 12px;
  color: #6b7280;
  margin-top: 6px;
  line-height: 1.4;
  display: flex;
  align-items: center;
  gap: 4px;
}

.form-tip .el-icon {
  font-size: 14px;
}

/* 用户选择下拉框样式 */
:deep(.user-select-dropdown) {
  max-height: 400px;
  overflow-y: auto;
}

:deep(.user-select-dropdown .el-select-dropdown__item) {
  height: auto;
  padding: 8px 20px;
  line-height: normal;
}

:deep(.user-select-dropdown .el-select-dropdown__item.hover) {
  background-color: #f5f7fa;
}

:deep(.user-select-dropdown .el-select-dropdown__item.selected) {
  background-color: #ecf5ff;
  color: #409eff;
}

.user-select-option {
  height: auto !important;
  padding: 0 !important;
}

.role-selection .role-cards {
  display: flex;
  flex-direction: column;
  gap: 12px;
}


.role-card:hover {
  border-color: #8b5cf6;
  background: #faf5ff;
}

.role-card.selected {
  border-color: #8b5cf6;
  background: #faf5ff;
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.1);
}

.role-icon {
  margin-right: 12px;
  color: #8b5cf6;
}

.role-info {
  flex: 1;
}

.role-name {
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 4px;
}

.role-desc {
  font-size: 13px;
  color: #64748b;
  line-height: 1.4;
}

.role-check {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>