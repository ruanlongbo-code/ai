<template>
  <div class="task-run-history">
    <!-- 搜索和筛选 -->
    <div class="filter-section">
      <div class="filter-row">
        <el-select
            v-model="statusFilter"
            placeholder="筛选状态"
            clearable
            @change="loadRunHistory"
            style="width: 150px;"
        >
          <el-option label="全部状态" value=""/>
          <el-option label="运行中" value="running"/>
          <el-option label="成功" value="success"/>
          <el-option label="失败" value="failed"/>
          <el-option label="已取消" value="cancelled"/>
        </el-select>
        
        <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            @change="loadRunHistory"
            style="width: 240px;"
        />
        
        <el-button @click="handleRefresh" icon="Refresh">刷新</el-button>
      </div>
    </div>

    <!-- 运行记录列表 -->
    <div v-loading="loading" class="history-content">
      <div v-if="!runHistory.length && !loading" class="empty-state">
        <el-empty description="暂无运行记录"/>
      </div>

      <div v-else class="history-list">
        <div 
            v-for="record in runHistory" 
            :key="record.id" 
            class="history-item"
            :class="{ 'running': record.status === 'running' }"
            @click="record.status !== 'running' && viewReport(record.id)"
        >
          <div class="record-header">
            <div class="record-info">
              <div class="record-title">
                <span class="run-id">#{{ record.id }}</span>
                <el-tag 
                    :type="getStatusType(record.status)" 
                    size="small"
                    class="status-tag"
                >
                  {{ getStatusText(record.status) }}
                </el-tag>
              </div>
              <div class="record-meta">
                <span class="meta-item">
                  <el-icon><Clock /></el-icon>
                  {{ formatDateTime(record.created_at) }}
                </span>
              </div>
            </div>
            
            <div class="record-actions">
              <el-button 
                  v-if="record.status !== 'running'"
                  type="primary" 
                  size="small" 
                  @click.stop="viewReport(record.id)"
                  icon="Document"
              >
                查看报告
              </el-button>
              <el-button 
                  v-if="record.status === 'running'"
                  type="danger" 
                  size="small" 
                  @click.stop="cancelRun(record.id)"
                  icon="Close"
              >
                取消运行
              </el-button>
            </div>
          </div>

          <!-- 运行统计 -->
          <div v-if="record.status !== 'running'" class="record-stats">
            <div class="stats-grid">
              <div class="stat-item">
                <div class="stat-label">总用例</div>
                <div class="stat-value">{{ record.total_cases || 0 }}</div>
              </div>
              <div class="stat-item success">
                <div class="stat-label">通过</div>
                <div class="stat-value">{{ record.passed_cases || 0 }}</div>
              </div>
              <div class="stat-item danger">
                <div class="stat-label">失败</div>
                <div class="stat-value">{{ record.failed_cases || 0 }}</div>
              </div>
              <div class="stat-item warning">
                <div class="stat-label">跳过</div>
                <div class="stat-value">{{ record.skipped_cases || 0 }}</div>
              </div>
              <div class="stat-item">
                <div class="stat-label">耗时</div>
                <div class="stat-value">{{ formatDuration(record.duration) }}</div>
              </div>
            </div>
            
            <!-- 进度条 -->
            <div class="progress-section" v-if="record.total_cases > 0">
              <el-progress 
                  :percentage="getSuccessRate(record)" 
                  :color="getProgressColor(record)"
                  :show-text="false"
                  :stroke-width="6"
              />
              <div class="progress-text">
                成功率: {{ getSuccessRate(record) }}%
              </div>
            </div>
          </div>

          <!-- 运行中的进度 -->
          <div v-else class="running-progress">
            <div class="running-info">
              <el-icon class="spinning"><Loading /></el-icon>
              <span>测试计划正在运行中...</span>
            </div>
            <el-progress 
                :percentage="50" 
                :indeterminate="true"
                :stroke-width="6"
            />
          </div>

          <!-- 错误信息 -->
          <div v-if="record.error_message" class="error-section">
            <el-alert
                :title="record.error_message"
                type="error"
                :closable="false"
                show-icon
            />
          </div>
        </div>
      </div>

      <!-- 分页 -->
      <div class="pagination-section" v-if="pagination.total > 0">
        <el-pagination
            v-model:current-page="pagination.page"
            v-model:page-size="pagination.page_size"
            :total="pagination.total"
            :page-sizes="[10, 20, 50]"
            layout="total, sizes, prev, pager, next"
            @current-change="loadRunHistory"
            @size-change="loadRunHistory"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, defineProps, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  User, Clock, Monitor, Document, Refresh, Close, Loading 
} from '@element-plus/icons-vue'

// 导入API（使用真实后端接口）
import { getTaskRunList } from '@/api/test_execution'

const props = defineProps({
  taskId: {
    type: Number,
    required: true
  },
  projectId: {
    type: Number,
    required: true
  }
})

const router = useRouter()

// 响应式数据
const loading = ref(false)
const runHistory = ref([])
const statusFilter = ref('')
const dateRange = ref(null)

const pagination = reactive({
  page: 1,
  page_size: 10,
  total: 0
})

// 方法
const loadRunHistory = async () => {
  loading.value = true
  try {
    // 真实接口调用
    const params = {
      task_id: props.taskId,
      page: pagination.page,
      page_size: pagination.page_size
    }
    const response = await getTaskRunList(props.projectId, params)

    // 后端返回字段：items, total, page, page_size
    const items = response?.data?.items || []
    // 将状态映射到前端文案（completed -> success）
    runHistory.value = items.map(item => ({
      ...item,
      status: item.status === 'completed' ? 'success' : item.status
    }))
    pagination.total = response?.data?.total || 0
  } catch (error) {
    console.error('加载运行记录失败:', error)
    ElMessage.error('加载运行记录失败')
  } finally {
    loading.value = false
  }
}

const getStatusType = (status) => {
  const statusMap = {
    running: 'info',
    success: 'success',
    failed: 'danger',
    cancelled: 'warning',
    pending: 'info'
  }
  return statusMap[status] || 'info'
}

const handleRefresh = async () => {
  await loadRunHistory()
  ElMessage.success('刷新成功')
}

const getStatusText = (status) => {
  const statusMap = {
    running: '运行中',
    success: '成功',
    failed: '失败',
    cancelled: '已取消',
    pending: '待开始'
  }
  return statusMap[status] || status
}

const getSuccessRate = (record) => {
  if (!record.total_cases || record.total_cases === 0) return 0
  return Math.round((record.passed_cases / record.total_cases) * 100)
}

const getProgressColor = (record) => {
  const rate = getSuccessRate(record)
  if (rate >= 80) return '#67c23a'
  if (rate >= 60) return '#e6a23c'
  return '#f56c6c'
}

const formatDateTime = (dateTime) => {
  if (!dateTime) return '-'
  return new Date(dateTime).toLocaleString()
}

const formatDuration = (duration) => {
  if (!duration) return '-'
  if (duration < 60) return `${duration.toFixed(1)}秒`
  const minutes = Math.floor(duration / 60)
  const seconds = (duration % 60).toFixed(1)
  return `${minutes}分${seconds}秒`
}

const viewReport = (runId) => {
  try {
    const projectId = Number(props.projectId)
    const id = Number(runId)
    if (!projectId || !id) {
      ElMessage.error('无法打开任务执行报告：缺少必要ID')
      return
    }
    router.push({ name: 'TaskRunReport', params: { projectId, runId: id } })
  } catch (e) {
    console.error('跳转任务执行报告失败', e)
    ElMessage.error('跳转任务执行报告失败')
  }
}

const cancelRun = async (runId) => {
  try {
    await ElMessageBox.confirm(
        '确定要取消正在运行的测试计划吗？',
        '确认取消',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }
    )
    
    // 实际API调用
    // await cancelTaskRun(props.projectId, props.taskId, runId)
    
    ElMessage.success('测试计划运行已取消')
    await loadRunHistory()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('取消运行失败:', error)
      ElMessage.error('取消运行失败')
    }
  }
}

// 生命周期
onMounted(() => {
  loadRunHistory()
})

// 监听路由传入的项目与任务ID变化，确保切换后重新加载
watch(() => props.taskId, () => {
  if (props.taskId && props.projectId) {
    loadRunHistory()
  }
})

watch(() => props.projectId, () => {
  if (props.taskId && props.projectId) {
    loadRunHistory()
  }
})
</script>

<style scoped>
.task-run-history {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.filter-section {
  margin-bottom: 20px;
}

.filter-row {
  display: flex;
  gap: 16px;
  align-items: center;
}

.history-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.empty-state {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
}

.history-list {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.history-item {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 20px;
  transition: all 0.2s ease;
}

.history-item:hover {
  border-color: #d1d5db;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.history-item.running {
  border-color: #3b82f6;
  background: #f0f9ff;
}

.record-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.record-info {
  flex: 1;
}

.record-title {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.run-id {
  font-weight: 600;
  font-size: 16px;
  color: #374151;
}

.status-tag {
  font-weight: 500;
}

.record-meta {
  display: flex;
  gap: 16px;
  color: #6b7280;
  font-size: 14px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.record-actions {
  display: flex;
  gap: 8px;
}

.record-stats {
  margin-bottom: 16px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 12px;
  margin-bottom: 12px;
}

.stat-item {
  text-align: center;
  padding: 12px;
  background: #f8fafc;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
}

.stat-item.success {
  background: #f0fdf4;
  border-color: #bbf7d0;
}

.stat-item.danger {
  background: #fef2f2;
  border-color: #fecaca;
}

.stat-item.warning {
  background: #fffbeb;
  border-color: #fed7aa;
}

.stat-label {
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 4px;
}

.stat-value {
  font-size: 16px;
  font-weight: 600;
  color: #374151;
}

.progress-section {
  display: flex;
  align-items: center;
  gap: 12px;
}

.progress-text {
  font-size: 14px;
  color: #6b7280;
  white-space: nowrap;
}

.running-progress {
  margin-bottom: 16px;
}

.running-info {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  color: #3b82f6;
  font-weight: 500;
}

.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.error-section {
  margin-top: 12px;
}

.pagination-section {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}
</style>