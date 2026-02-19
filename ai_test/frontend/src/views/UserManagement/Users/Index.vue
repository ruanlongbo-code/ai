<template>
  <div class="user-management-page">
    <!-- 页面头部（与测试套件页面一致的结构） -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <h1>用户管理</h1>
          <p class="subtitle">管理系统用户列表</p>
        </div>
        <div class="action-section">
          <el-button type="primary" @click="openCreateDialog">
            <el-icon><Plus /></el-icon>
            新建用户
          </el-button>
          <el-button @click="handleRefresh">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </div>
    </div>

    <!-- 筛选工具栏（与测试套件页面一致的结构） -->
    <div class="filter-toolbar">
      <el-card>
        <div class="filter-content">
          <div class="filter-left">
            <el-input
              v-model="query"
              placeholder="搜索用户名/真实姓名/邮箱"
              clearable
              class="search-input"
              @keyup.enter="handleSearch"
            />
          </div>
          <div class="filter-right">
            <el-button type="primary" @click="handleSearch">搜索</el-button>
            <el-button @click="handleReset">重置</el-button>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 主内容区域（与测试套件页面一致的结构） -->
    <div class="main-content">
      <el-card class="content-card">
        <div class="table-container">
          <el-table
            :data="users"
            v-loading="loading"
            border
            style="width: 100%"
          >
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column prop="username" label="用户名" min-width="140" />
            <el-table-column prop="real_name" label="真实姓名" min-width="120" />
            <el-table-column prop="email" label="邮箱" min-width="200" />
            <el-table-column prop="phone" label="手机号" min-width="140" />
            <el-table-column label="激活" width="100">
              <template #default="{ row }">
                <el-tag :type="row.is_active ? 'success' : 'danger'">
                  {{ row.is_active ? '已激活' : '未激活' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="角色" width="120">
              <template #default="{ row }">
                <el-tag :type="row.is_superuser ? 'warning' : 'info'">
                  {{ row.is_superuser ? '管理员' : '普通用户' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="最后登录" min-width="180">
              <template #default="{ row }">
                {{ formatDate(row.last_login) }}
              </template>
            </el-table-column>
            <el-table-column label="创建时间" min-width="180">
              <template #default="{ row }">
                {{ formatDate(row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="240" fixed="right">
              <template #default="{ row }">
                <el-button
                  v-if="!row.is_active"
                  type="success"
                  size="small"
                  @click="handleActivate(row)"
                >激活</el-button>
                <el-button
                  v-if="row.is_active"
                  type="warning"
                  size="small"
                  @click="handleDisable(row)"
                >禁用</el-button>
                <el-button plain size="small" @click="openResetDialog(row)">重置密码</el-button>
                <el-button type="danger" size="small" @click="confirmDelete(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
        <div class="table-footer">
          <el-pagination
            background
            layout="prev, pager, next, sizes, total"
            :total="total"
            :page-sizes="[10, 20, 50]"
            :page-size="pageSize"
            :current-page="page"
            @current-change="handlePageChange"
            @size-change="handleSizeChange"
          />
        </div>
      </el-card>
    </div>

    <!-- 新建用户弹窗 -->
    <el-dialog v-model="createDialogVisible" title="新建用户" width="520px" :close-on-click-modal="false">
      <el-form ref="createFormRef" :model="createForm" :rules="createRules" label-width="100px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="createForm.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="createForm.email" placeholder="请输入邮箱" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="createForm.password" type="password" placeholder="请输入密码" show-password />
        </el-form-item>
        <el-form-item label="真实姓名" prop="real_name">
          <el-input v-model="createForm.real_name" placeholder="可选：请输入真实姓名" />
        </el-form-item>
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="createForm.phone" placeholder="可选：请输入手机号" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="createDialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="createLoading" @click="submitCreate">确定</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 重置密码弹窗 -->
    <el-dialog v-model="resetDialogVisible" title="重置用户密码" width="480px" :close-on-click-modal="false">
      <div>
        <p style="margin-bottom: 12px;">重置目标：<strong>{{ resetTargetUser?.username }}</strong></p>
        <el-form ref="resetFormRef" :model="resetForm" :rules="resetRules" label-width="110px">
          <el-form-item label="新密码" prop="new_password">
            <el-input v-model="resetForm.new_password" type="password" show-password placeholder="请输入新密码" />
          </el-form-item>
          <el-form-item label="确认新密码" prop="confirm_password">
            <el-input v-model="resetForm.confirm_password" type="password" show-password placeholder="请再次输入新密码" />
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="resetDialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="resetLoading" @click="confirmResetPassword">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh } from '@element-plus/icons-vue'
import { getUserList, deleteUser, registerUser, activateUser, disableUser, adminResetPassword } from '@/api/user'

const loading = ref(false)
const users = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const query = ref('')

// 新建用户弹窗与表单
const createDialogVisible = ref(false)
const createLoading = ref(false)
const createFormRef = ref()
const createForm = reactive({
  username: '',
  email: '',
  password: '',
  real_name: '',
  phone: ''
})
const createRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, message: '用户名至少3个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' }
  ],
  real_name: [
    { max: 50, message: '真实姓名不超过50字符', trigger: 'blur' }
  ],
  phone: [
    { max: 20, message: '手机号不超过20字符', trigger: 'blur' }
  ]
}

// 重置密码对话框与表单
const resetDialogVisible = ref(false)
const resetLoading = ref(false)
const resetFormRef = ref()
const resetTargetUser = ref(null)
const resetForm = reactive({
  new_password: '',
  confirm_password: ''
})
const resetRules = {
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, max: 128, message: '密码长度在 6 到 128 个字符', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    { validator: (_rule, value, callback) => {
        if (value !== resetForm.new_password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      }, trigger: 'blur' }
  ]
}

const fetchUsers = async () => {
  loading.value = true
  try {
    const response = await getUserList({
      page: page.value,
      page_size: pageSize.value,
      username: query.value || undefined
    })
    const data = response?.data || {}
    users.value = data.users || []
    total.value = data.total || 0
  } catch (error) {
    console.error('获取用户列表失败:', error)
    ElMessage.error(error.response?.data?.detail || '获取用户列表失败')
  } finally {
    loading.value = false
  }
}

const openCreateDialog = () => {
  createForm.username = ''
  createForm.email = ''
  createForm.password = ''
  createForm.real_name = ''
  createForm.phone = ''
  createDialogVisible.value = true
}

const submitCreate = async () => {
  try {
    await createFormRef.value.validate()
    createLoading.value = true

    await registerUser({
      username: createForm.username,
      password: createForm.password,
      email: createForm.email,
      phone: createForm.phone || undefined,
      real_name: createForm.real_name || undefined
    })

    ElMessage.success('用户创建成功（默认未激活）')
    createDialogVisible.value = false
    await fetchUsers()
  } catch (error) {
    if (error !== 'cancel') {
      const msg = error?.response?.data?.detail || '创建用户失败'
      ElMessage.error(msg)
    }
  } finally {
    createLoading.value = false
  }
}

const handleSearch = () => {
  page.value = 1
  fetchUsers()
}

const handleReset = () => {
  query.value = ''
  page.value = 1
  fetchUsers()
}

const handleRefresh = async () => {
  await fetchUsers()
  ElMessage.success('刷新成功')
}

const handlePageChange = (p) => {
  page.value = p
  fetchUsers()
}

const handleSizeChange = (s) => {
  pageSize.value = s
  page.value = 1
  fetchUsers()
}

const confirmDelete = async (user) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除用户 ${user.username} 吗？此操作不可撤销。`,
      '删除用户',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await deleteUser(user.id)
    ElMessage.success('删除成功')
    await fetchUsers()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除用户失败:', error)
      ElMessage.error(error.response?.data?.detail || '删除用户失败')
    }
  }
}

const openResetDialog = (user) => {
  resetTargetUser.value = user
  resetForm.new_password = ''
  resetForm.confirm_password = ''
  resetDialogVisible.value = true
}

const confirmResetPassword = async () => {
  if (!resetFormRef.value || !resetTargetUser.value) return
  try {
    await resetFormRef.value.validate()
    resetLoading.value = true
    await adminResetPassword(resetTargetUser.value.id, { new_password: resetForm.new_password })
    ElMessage.success(`已重置用户 ${resetTargetUser.value.username} 的密码`)
    resetDialogVisible.value = false
  } catch (error) {
    console.error('重置密码失败:', error)
    const msg = error?.response?.data?.detail || '重置密码失败'
    ElMessage.error(msg)
  } finally {
    resetLoading.value = false
  }
}

const handleActivate = async (user) => {
  try {
    await ElMessageBox.confirm(
      `确定要激活用户 ${user.username} 吗？`,
      '激活用户',
      {
        confirmButtonText: '激活',
        cancelButtonText: '取消',
        type: 'info'
      }
    )

    await activateUser(user.id, true)
    ElMessage.success('用户已激活')
    await fetchUsers()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('激活用户失败:', error)
      ElMessage.error(error.response?.data?.detail || '激活用户失败')
    }
  }
}

const handleDisable = async (user) => {
  try {
    await ElMessageBox.confirm(
      `确定要禁用用户 ${user.username} 吗？该用户将无法登录。`,
      '禁用用户',
      {
        confirmButtonText: '禁用',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    // 优先使用后端禁用接口
    await disableUser(user.id)
    ElMessage.success('用户已禁用')
    await fetchUsers()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('禁用用户失败:', error)
      ElMessage.error(error.response?.data?.detail || '禁用用户失败')
    }
  }
}

const formatDate = (val) => {
  if (!val) return '-'
  const d = new Date(val)
  if (isNaN(d)) return String(val)
  return `${d.toLocaleDateString()} ${d.toLocaleTimeString()}`
}

onMounted(() => {
  fetchUsers()
})
</script>

<style scoped>
.user-management-page {
  padding: 24px;
  background: #f8fafc;
  min-height: 100vh;
}

.page-header {
  margin-bottom: 5px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  background: white;
  padding: 24px;
  border-radius: 8px;
}

.title-section h1 {
  margin: 0;
  font-size: 22px;
  color: #1f2937;
}

.subtitle {
  margin: 6px 0 0;
  color: #6b7280;
}

.action-section .el-button + .el-button {
  margin-left: 8px;
}

.filter-toolbar {
  margin: 16px 0;
}

.filter-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.search-input {
  width: 280px;
}

.main-content {
  
}

.content-card {
  border: none;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.08);
}

.table-container {
  min-height: 400px;
}

.table-footer {
  padding: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>