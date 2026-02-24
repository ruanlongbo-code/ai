<template>
  <div class="biz-management">
    <div class="page-header">
      <h1>业务线管理</h1>
      <p>管理项目业务线及其子模块，为测试人员分配对应业务线</p>
    </div>

    <!-- 操作栏 -->
    <div class="action-bar">
      <el-button type="primary" @click="handleCreateTopLevel">
        <el-icon><Plus /></el-icon> 新建业务线
      </el-button>
      <el-button @click="loadData">
        <el-icon><Refresh /></el-icon> 刷新
      </el-button>
    </div>

    <!-- 业务线树形列表 -->
    <div class="biz-content" v-loading="loading">
      <el-collapse v-model="expandedPanels">
        <el-collapse-item v-for="biz in bizTree" :key="biz.id" :name="biz.id">
          <template #title>
            <div class="biz-header">
              <el-icon><OfficeBuilding /></el-icon>
              <span class="biz-name">{{ biz.name }}</span>
              <el-tag size="small" type="info" style="margin-left: 8px">{{ biz.children?.length || 0 }} 子模块</el-tag>
              <el-tag size="small" style="margin-left: 4px">{{ biz.members?.length || 0 }} 人</el-tag>
            </div>
          </template>
          <div class="biz-detail">
            <el-descriptions :column="2" border size="small" style="margin-bottom: 12px" v-if="biz.description">
              <el-descriptions-item label="描述" :span="2">{{ biz.description || '-' }}</el-descriptions-item>
            </el-descriptions>

            <!-- 子模块 -->
            <div class="section-title">
              <span>📂 子模块</span>
              <el-button type="primary" size="small" link @click.stop="handleCreateChild(biz)">
                <el-icon><Plus /></el-icon> 添加子模块
              </el-button>
            </div>
            <el-table :data="biz.children || []" size="small" empty-text="暂无子模块" border style="margin-bottom: 16px">
              <el-table-column prop="name" label="名称" min-width="150" />
              <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
              <el-table-column label="操作" width="140">
                <template #default="{ row }">
                  <el-button type="primary" size="small" link @click="handleEdit(row)">编辑</el-button>
                  <el-button type="danger" size="small" link @click="handleDelete(row)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>

            <!-- 成员管理 -->
            <div class="section-title">
              <span>👥 成员分配</span>
              <el-button type="primary" size="small" link @click.stop="handleAddMember(biz)">
                <el-icon><Plus /></el-icon> 添加成员
              </el-button>
            </div>
            <el-table :data="biz.members || []" size="small" empty-text="暂无成员" border>
              <el-table-column prop="real_name" label="姓名" min-width="100">
                <template #default="{ row }">{{ row.real_name || row.username }}</template>
        </el-table-column>
              <el-table-column prop="role" label="角色" width="120">
          <template #default="{ row }">
                  <el-tag :type="roleTagType(row.role)" size="small">{{ roleLabel(row.role) }}</el-tag>
          </template>
        </el-table-column>
              <el-table-column label="操作" width="180">
          <template #default="{ row }">
                  <el-select v-model="row.role" size="small" style="width: 90px" @change="handleRoleChange(biz, row)">
                    <el-option label="组长" value="lead" />
                    <el-option label="测试人员" value="member" />
                  </el-select>
                  <el-button type="danger" size="small" link @click="handleRemoveMember(biz, row)" style="margin-left: 4px">移除</el-button>
          </template>
        </el-table-column>
      </el-table>

            <!-- 业务线自身操作 -->
            <div style="margin-top: 12px; text-align: right;">
              <el-button size="small" @click="handleEdit(biz)">编辑业务线</el-button>
              <el-button type="danger" size="small" @click="handleDelete(biz)">删除业务线</el-button>
            </div>
          </div>
        </el-collapse-item>
      </el-collapse>

      <el-empty v-if="!loading && bizTree.length === 0" description="暂无业务线，请点击「新建业务线」按钮创建" />
    </div>

    <!-- 新建/编辑弹窗 -->
    <el-dialog :title="dialogTitle" v-model="showDialog" width="500px" :close-on-click-modal="false">
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="80px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入名称" maxlength="100" show-word-limit />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="formData.description" type="textarea" :rows="3" placeholder="请输入描述" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="saving">确定</el-button>
      </template>
    </el-dialog>

    <!-- 添加成员弹窗 -->
    <el-dialog title="添加业务线成员" v-model="showMemberDialog" width="450px" :close-on-click-modal="false">
      <el-form label-width="80px">
        <el-form-item label="选择成员">
          <el-select v-model="memberForm.user_id" filterable placeholder="搜索并选择成员" style="width: 100%">
            <el-option v-for="u in availableUsers" :key="u.id" :label="u.real_name || u.username" :value="u.id">
              <span>{{ u.real_name || u.username }}</span>
              <span style="color: #999; margin-left: 8px; font-size: 12px">{{ u.username }}</span>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="角色">
          <el-radio-group v-model="memberForm.role">
            <el-radio value="lead">组长</el-radio>
            <el-radio value="member">测试人员</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showMemberDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSubmitMember" :loading="saving">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useProjectStore } from '@/stores'
import {
  getProjectModules, createProjectModule, updateProjectModule, deleteProjectModule,
  addBusinessLineMember, updateBusinessLineMember, removeBusinessLineMember
} from '@/api/module'
import request from '@/utils/request'

const projectStore = useProjectStore()
const projectId = computed(() => projectStore.currentProject?.id)

const loading = ref(false)
const saving = ref(false)
const bizTree = ref([])
const expandedPanels = ref([])

// 弹窗
const showDialog = ref(false)
const dialogTitle = ref('')
const editingModule = ref(null)
const parentId = ref(null)
const formRef = ref()
const formData = ref({ name: '', description: '' })
const formRules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }]
}

// 成员弹窗
const showMemberDialog = ref(false)
const memberForm = ref({ user_id: null, role: 'member' })
const currentBizForMember = ref(null)
const allMembers = ref([])

const availableUsers = computed(() => {
  if (!currentBizForMember.value) return allMembers.value
  const existingIds = new Set((currentBizForMember.value.members || []).map(m => m.user_id))
  return allMembers.value.filter(u => !existingIds.has(u.id))
})

function roleLabel(r) {
  const map = { admin: '管理员', lead: '组长', member: '测试人员' }
  return map[r] || r
}
function roleTagType(r) {
  const map = { admin: 'danger', lead: 'warning', member: '' }
  return map[r] || ''
}

async function loadData() {
  if (!projectId.value) return
  loading.value = true
  try {
    const res = await getProjectModules(projectId.value)
    const data = res.data || res
    bizTree.value = data.datas || data || []
  } catch (e) {
    console.error(e)
    ElMessage.error('加载业务线列表失败')
  } finally {
    loading.value = false
  }
}

async function loadMembers() {
  if (!projectId.value) return
  try {
    // 管理员页面：加载所有注册用户供分配
    const res = await request({ url: '/user/list', method: 'get', params: { page: 1, page_size: 200 } })
    const data = res.data || res
    allMembers.value = (data.users || []).map(u => ({
      id: u.id,
      username: u.username,
      real_name: u.real_name
    }))
  } catch (e) {
    console.error('加载用户列表失败', e)
  }
}

function handleCreateTopLevel() {
  editingModule.value = null
  parentId.value = null
  dialogTitle.value = '新建业务线'
  formData.value = { name: '', description: '' }
  showDialog.value = true
}

function handleCreateChild(parent) {
  editingModule.value = null
  parentId.value = parent.id
  dialogTitle.value = `新建子模块 — ${parent.name}`
  formData.value = { name: '', description: '' }
  showDialog.value = true
}

function handleEdit(mod) {
  editingModule.value = mod
  parentId.value = mod.parent_id || null
  dialogTitle.value = mod.parent_id ? '编辑子模块' : '编辑业务线'
  formData.value = { name: mod.name, description: mod.description || '' }
  showDialog.value = true
}

async function handleSubmit() {
  if (!formRef.value) return
  try {
    await formRef.value.validate()
    saving.value = true
    if (editingModule.value) {
      await updateProjectModule(projectId.value, editingModule.value.id, formData.value)
      ElMessage.success('更新成功')
    } else {
      await createProjectModule(projectId.value, {
        ...formData.value,
        parent_id: parentId.value
      })
      ElMessage.success('创建成功')
    }
    showDialog.value = false
    await loadData()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  } finally {
    saving.value = false
  }
}

async function handleDelete(mod) {
  const label = mod.parent_id ? '子模块' : '业务线'
  try {
    await ElMessageBox.confirm(
      `确定删除${label}「${mod.name}」吗？${mod.parent_id ? '' : '将同时删除所有子模块和成员绑定。'}`,
      '确认删除', { type: 'warning' }
    )
    await deleteProjectModule(projectId.value, mod.id)
    ElMessage.success('删除成功')
    await loadData()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(e.response?.data?.detail || '删除失败')
  }
}

function handleAddMember(biz) {
  currentBizForMember.value = biz
  memberForm.value = { user_id: null, role: 'member' }
  showMemberDialog.value = true
}

async function handleSubmitMember() {
  if (!memberForm.value.user_id) return ElMessage.warning('请选择成员')
  saving.value = true
  try {
    await addBusinessLineMember(projectId.value, currentBizForMember.value.id, memberForm.value)
    ElMessage.success('添加成功')
    showMemberDialog.value = false
    await loadData()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '添加失败')
  } finally {
    saving.value = false
  }
}

async function handleRoleChange(biz, member) {
  try {
    await updateBusinessLineMember(projectId.value, biz.id, member.id, { role: member.role })
    ElMessage.success('角色更新成功')
  } catch (e) {
    ElMessage.error('角色更新失败')
    await loadData()
  }
}

async function handleRemoveMember(biz, member) {
  try {
    await ElMessageBox.confirm(`确定移除成员「${member.real_name || member.username}」？`, '确认移除', { type: 'warning' })
    await removeBusinessLineMember(projectId.value, biz.id, member.id)
    ElMessage.success('移除成功')
    await loadData()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('移除失败')
  }
}

onMounted(async () => {
  await loadData()
  await loadMembers()
})
</script>

<style scoped>
.biz-management {
  padding: 24px;
  background: #fff;
  min-height: 100vh;
}
.page-header { margin-bottom: 24px; }
.page-header h1 { color: #1f2937; margin: 0 0 8px; font-size: 24px; font-weight: bold; }
.page-header p { color: #6b7280; margin: 0; font-size: 14px; }

.action-bar { margin-bottom: 20px; display: flex; gap: 12px; }

.biz-content {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 16px;
}

.biz-header {
  display: flex; align-items: center; gap: 8px; font-size: 15px; font-weight: 500;
}
.biz-name { color: #1f2937; }

.biz-detail { padding: 0 16px 8px; }

.section-title {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 8px; font-size: 14px; font-weight: 500; color: #374151;
}

:deep(.el-collapse-item__header) {
  font-size: 15px; padding: 0 8px; height: 48px; background: #f9fafb;
  border-radius: 6px; margin-bottom: 4px;
}
:deep(.el-collapse-item__wrap) {
  border-bottom: 1px solid #e5e7eb;
}

/* 修复按钮文案颜色显示问题 */
:deep(.el-button--primary.is-text) {
  color: #409eff;
}
:deep(.el-button--primary.is-text:hover) {
  color: #66b1ff;
  background-color: #ecf5ff;
}
:deep(.el-button--danger.is-text) {
  color: #f56c6c;
}
:deep(.el-button--danger.is-text:hover) {
  color: #f89898;
  background-color: #fef0f0;
}

/* 确保表格内按钮文字清晰可见 */
:deep(.el-table .el-button--primary.is-link) {
  color: #409eff;
  font-weight: 500;
}
:deep(.el-table .el-button--danger.is-link) {
  color: #f56c6c;
  font-weight: 500;
}

/* 修复操作栏按钮样式 */
.biz-detail > div:last-child .el-button {
  font-weight: 500;
}
.biz-detail > div:last-child .el-button--default {
  color: #606266;
  border-color: #dcdfe6;
}
.biz-detail > div:last-child .el-button--danger {
  color: #fff;
  background-color: #f56c6c;
  border-color: #f56c6c;
}

/* section title 内的按钮确保可见 */
.section-title :deep(.el-button) {
  font-weight: 500;
  color: #409eff;
}

/* 角色选择器样式优化 */
:deep(.el-table .el-select .el-input__inner) {
  font-size: 13px;
}
</style>
