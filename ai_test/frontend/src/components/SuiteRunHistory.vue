<template>
  <div class="suite-run-history">
    <!-- 筛选和操作栏 -->
    <div class="history-header">
      <div class="filter-section">
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
          @change="handleDateRangeChange"
          style="width: 240px; margin-right: 12px;"
        />
        <el-select
          v-model="statusFilter"
          placeholder="运行状态"
          clearable
          @change="handleStatusFilterChange"
          style="width: 120px; margin-right: 12px;"
        >
          <el-option label="全部" value="" />
          <el-option label="完成" value="completed" />
          <el-option label="失败" value="failed" />
          <el-option label="错误" value="error" />
          <el-option label="运行中" value="running" />
        </el-select>
        <el-button @click="refreshHistory" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
      <div class="quick-filters">
        <el-button-group>
          <el-button 
            size="small" 
            :type="quickFilter === 'today' ? 'primary' : ''" 
            @click="setQuickFilter('today')"
          >
            今天
          </el-button>
          <el-button 
            size="small" 
            :type="quickFilter === 'week' ? 'primary' : ''" 
            @click="setQuickFilter('week')"
          >
            本周
          </el-button>
          <el-button 
            size="small" 
            :type="quickFilter === 'month' ? 'primary' : ''" 
            @click="setQuickFilter('month')"
          >
            本月
          </el-button>
        </el-button-group>
      </div>
    </div>

    <!-- 运行记录表格 -->
    <div class="history-table" v-loading="loading">
      <el-table 
        :data="historyList" 
        style="width: 100%"
        :empty-text="emptyText"
        row-class-name="history-row"
      >
        <el-table-column prop="start_time" label="运行时间" min-width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.start_time) }}
          </template>
        </el-table-column>
        <el-table-column prop="total_cases" label="用例数" width="100">

        </el-table-column>
        


        <el-table-column label="用例统计" min-width="200">
          <template #default="{ row }">
            <div class="case-stats">
              <span class="stat-item success">
                成功: {{ row.passed_cases || 0 }}
              </span>
              <span class="stat-item failed">
                失败: {{ row.failed_cases || 0 }}
              </span>
              <span class="stat-item error" v-if="row.skipped_cases">
                跳过: {{ row.skipped_cases }}
              </span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" min-width="100">
          <template #default="{ row }">
            <el-tag
              :type="getStatusType(row.status)"
              size="small"
            >
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="duration" label="耗时" width="100">
          <template #default="{ row }">
            {{ formatDuration(row.duration) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="110" fixed="right">
          <template #default="{ row }">
            <el-button
              size="small"
              type="primary"
              @click.stop="viewDetails(row)"
            >
              <el-icon><View /></el-icon>
              测试报告
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper" v-if="total > 0">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Refresh, View } from '@element-plus/icons-vue'
import { getSuiteRunHistory } from '@/api/suite'

// Props
const props = defineProps({
  suiteId: {
    type: [String, Number],
    required: true
  },
  projectId: {
    type: [String, Number],
    required: true
  }
})

// Emits
const emit = defineEmits([])

// 已移除报告页面路由导航
const router = useRouter()

// 响应式数据
const loading = ref(false)
const historyList = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

// 筛选条件
const dateRange = ref([])
const statusFilter = ref('')
const quickFilter = ref('')

// 计算属性
const emptyText = computed(() => {
  return loading.value ? '加载中...' : '暂无运行记录'
})

// 方法
const loadHistory = async () => {
  if (!props.suiteId) return
  
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      size: pageSize.value,
      status: statusFilter.value || undefined,
      start_date: dateRange.value?.[0] || undefined,
      end_date: dateRange.value?.[1] || undefined
    }

    // 调用API获取运行记录
      const response = await getSuiteRunHistory(props.projectId, props.suiteId, params)
    historyList.value = response.data.items || []
    total.value = response.data.total || 0
    
  } catch (error) {
    ElMessage.error('获取运行记录失败: ' + (error.response?.data?.detail || error.message))
    historyList.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

// 监听套件ID变化
watch(() => props.suiteId, (newId) => {
  if (newId) {
    loadHistory()
  }
}, { immediate: true })

const refreshHistory = () => {
  currentPage.value = 1
  loadHistory()
}

const handleDateRangeChange = () => {
  currentPage.value = 1
  loadHistory()
}

const handleStatusFilterChange = () => {
  currentPage.value = 1
  loadHistory()
}

const setQuickFilter = (filter) => {
  quickFilter.value = filter
  const today = new Date()
  
  switch (filter) {
    case 'today':
      const todayStr = today.toISOString().split('T')[0]
      dateRange.value = [todayStr, todayStr]
      break
    case 'week':
      const weekAgo = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000)
      dateRange.value = [weekAgo.toISOString().split('T')[0], today.toISOString().split('T')[0]]
      break
    case 'month':
      const monthAgo = new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000)
      dateRange.value = [monthAgo.toISOString().split('T')[0], today.toISOString().split('T')[0]]
      break
  }
  
  currentPage.value = 1
  loadHistory()
}

const handleSizeChange = (size) => {
  pageSize.value = size
  currentPage.value = 1
  loadHistory()
}

const handleCurrentChange = (page) => {
  currentPage.value = page
  loadHistory()
}

// 已移除行点击跳转报告

// 已移除查看报告导航
const viewDetails = (row) => {
  try {
    const projectId = Number(props.projectId)
    const suiteId = props.suiteId ? Number(props.suiteId) : undefined
    // 兼容不同返回字段作为运行记录ID
    const runId = Number(row?.id || row?.run_id || row?.suite_run_id)

    if (!projectId || !runId) {
      ElMessage.error('无法打开测试报告：缺少必要ID')
      return
    }

    router.push({
      name: 'SuiteRunReport',
      params: { projectId, runId, suiteId }
    })
  } catch (e) {
    console.error('查看套件测试报告跳转失败', e)
    ElMessage.error('跳转测试报告失败')
  }
}

// 辅助函数
const formatDateTime = (dateTimeStr) => {
  if (!dateTimeStr) return '-'
  const date = new Date(dateTimeStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

const formatDuration = (duration) => {
  if (duration === null || duration === undefined) return '-'
  if (duration < 1) {
    return `${Math.round(duration * 1000)}ms`
  }
  return `${duration.toFixed(2)}s`
}

const getStatusType = (status) => {
  switch (status) {
    case 'completed':
    case 'success':
      return 'success'
    case 'failed':
    case 'failure':
      return 'danger'
    case 'error':
      return 'danger'
    case 'running':
      return 'warning'
    default:
      return 'info'
  }
}

const getStatusText = (status) => {
  switch (status) {
    case 'completed':
      return '完成'
    case 'success':
      return '成功'
    case 'failed':
    case 'failure':
      return '失败'
    case 'error':
      return '错误'
    case 'running':
      return '运行中'
    default:
      return status || '未知'
  }
}

// 生命周期
onMounted(() => {
  if (props.suiteId) {
    loadHistory()
  }
})

</script>

<style scoped>
.suite-run-history {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 8px;
}

.filter-section {
  display: flex;
  align-items: center;
}

.quick-filters {
  display: flex;
  align-items: center;
}

.history-table {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.history-table :deep(.el-table) {
  flex: 1;
}

.history-row {
  cursor: pointer;
}

.history-row:hover {
  background-color: #f5f7fa;
}

.case-stats {
  display: flex;
  gap: 8px;
  font-size: 12px;
}

.stat-item {
  padding: 2px 6px;
  border-radius: 4px;
  background: #f0f0f0;
}

.stat-item.success {
  color: #67c23a;
  background: #f0f9ff;
}

.stat-item.failed {
  color: #f56c6c;
  background: #fef0f0;
}

.stat-item.error {
  color: #e6a23c;
  background: #fdf6ec;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 16px;
  padding: 16px 0;
}
</style>