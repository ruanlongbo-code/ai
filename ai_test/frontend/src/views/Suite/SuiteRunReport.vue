<template>
  <div class="suite-run-report">
    <!-- 页面标题 -->
    <div class="page-header">
     
      <h1 class="page-title">
        <el-icon><Document /></el-icon>
        套件执行详情
      </h1>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="5" animated />
    </div>

    <!-- 报告内容 -->
    <div v-else-if="reportData" class="report-content">
      <!-- 基本信息 -->
      <el-card class="info-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <el-icon><InfoFilled /></el-icon>
            <span>基本信息</span>
          </div>
        </template>
        <div class="info-grid">
          <div class="info-item">
            <label>套件名称：</label>
            <span>{{ reportData.suite_name }}</span>
          </div>
          <div class="info-item">
            <label>执行时间：</label>
            <span>{{ formatDateTime(reportData.start_time) }}</span>
          </div>
          <div class="info-item">
            <label>执行耗时：</label>
            <span>{{ formatDuration(reportData.duration) }}</span>
          </div>
          <div class="info-item">
            <label>执行状态：</label>
            <el-tag :type="getStatusType(reportData.status)" size="large">
              {{ getStatusText(reportData.status) }}
            </el-tag>
          </div>
        </div>
      </el-card>

      <!-- 统计信息图表 -->
      <el-row :gutter="20" class="statistics-row">
        <el-col :span="12">
          <el-card class="chart-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <el-icon><PieChart /></el-icon>
                <span>执行结果统计</span>
              </div>
            </template>
            <div class="chart-container">
              <v-chart :option="pieChartOption" class="chart" />
            </div>
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card class="chart-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <el-icon><DataLine /></el-icon>
                <span>统计数据</span>
              </div>
            </template>
            <div class="statistics-grid">
              <div class="stat-item success">
                <div class="stat-number">{{ statistics.success }}</div>
                <div class="stat-label">成功</div>
              </div>
              <div class="stat-item failed">
                <div class="stat-number">{{ statistics.failed }}</div>
                <div class="stat-label">失败</div>
              </div>
              <div class="stat-item total">
                <div class="stat-number">{{ statistics.total }}</div>
                <div class="stat-label">总计</div>
              </div>
              <div class="stat-item rate">
                <div class="stat-number">{{ statistics.successRate }}%</div>
                <div class="stat-label">成功率</div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 用例执行记录列表 -->
      <el-card class="case-list-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <el-icon><List /></el-icon>
            <span>用例执行记录 ({{ reportData.case_runs.length }})</span>
          </div>
        </template>
        
        <!-- 筛选器 -->
        <div class="filter-bar">
          <el-select v-model="statusFilter" placeholder="筛选状态" clearable style="width: 150px">
            <el-option label="全部" value="" />
            <el-option label="成功" value="success" />
            <el-option label="失败" value="failed" />
            <el-option label="错误" value="error" />
            <el-option label="跳过" value="skipped" />
          </el-select>
          <el-input
            v-model="searchKeyword"
            placeholder="搜索用例名称"
            style="width: 200px; margin-left: 10px"
            clearable
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>

        <!-- 用例列表 -->
        <div class="case-list">
          <div
            v-for="caseRun in filteredCaseRuns"
            :key="caseRun.case_run_id"
            class="case-item"
            :class="{ 'case-item-failed': caseRun.status === 'failed' }"
            @click="viewCaseDetail(caseRun)"
          >
            <div class="case-header">
              <div class="case-name">
                <el-icon><Document /></el-icon>
                {{ caseRun.case_name }}
              </div>
              <div class="case-status">
                <el-tag :type="getStatusType(caseRun.status)" size="small">
                  {{ getStatusText(caseRun.status) }}
                </el-tag>
              </div>
            </div>
            <div class="case-meta">
              <span class="case-time">
                <el-icon><Clock /></el-icon>
                {{ formatDateTime(caseRun.start_time) }}
              </span>
              <span class="case-duration">
                <el-icon><Timer /></el-icon>
                {{ formatDuration(caseRun.duration) }}
              </span>
            </div>
            <div v-if="caseRun.error_message" class="case-error">
              <el-icon><WarningFilled /></el-icon>
              {{ caseRun.error_message }}
            </div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 错误状态 -->
    <div v-else class="error-container">
      <el-result
        icon="error"
        title="加载失败"
        sub-title="无法获取测试报告数据，请稍后重试"
      >
        <template #extra>
          <el-button type="primary" @click="loadReportData">重新加载</el-button>
        </template>
      </el-result>
    </div>

    <!-- 用例详情弹窗 -->
    <el-dialog
      v-model="showCaseDetail"
      :title="`用例执行详情 - ${selectedCase?.case_name || ''}`"
      width="80%"
      top="5vh"
      destroy-on-close
    >
      <div v-if="caseDetailLoading" class="dialog-loading">
        <el-skeleton :rows="3" animated />
      </div>
      <TestResultCard
        v-else-if="caseDetailData"
        :result="caseDetailData"
      />
      <div v-else class="dialog-error">
        <el-result
          icon="error"
          title="加载失败"
          sub-title="无法获取用例详情数据"
        />
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Document,
  InfoFilled,
  PieChart,
  DataLine,
  List,
  Search,
  Clock,
  Timer,
  WarningFilled
} from '@element-plus/icons-vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { PieChart as EchartsPieChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent
} from 'echarts/components'
import VChart from 'vue-echarts'
import { getSuiteRunDetail, getCaseRunDetail } from '@/api/suite'
import TestResultCard from '@/components/common/TestResultCard.vue'

// 注册 ECharts 组件
use([
  CanvasRenderer,
  EchartsPieChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent
])

export default {
  name: 'SuiteRunReport',
  components: {
    VChart,
    TestResultCard,
    Document,
    InfoFilled,
    PieChart,
    DataLine,
    List,
    Search,
    Clock,
    Timer,
    WarningFilled
  },
  setup() {
    const route = useRoute()
    const projectId = ref(route.params.projectId)
    const suiteId = ref(route.params.suiteId)
    const runId = ref(route.params.runId)

    // 数据状态
    const loading = ref(true)
    const reportData = ref(null)
    
    // 用例详情弹窗
    const showCaseDetail = ref(false)
    const selectedCase = ref(null)
    const caseDetailLoading = ref(false)
    const caseDetailData = ref(null)
    
    // 筛选和搜索
    const statusFilter = ref('')
    const searchKeyword = ref('')

    // 计算统计信息
    const statistics = computed(() => {
      if (!reportData.value?.case_runs) {
        return { success: 0, failed: 0, total: 0, successRate: 0 }
      }
      
      const caseRuns = reportData.value.case_runs
      const total = caseRuns.length
      const success = caseRuns.filter(item => item.status === 'success').length
      const failed = total - success
      const successRate = total > 0 ? Math.round((success / total) * 100) : 0
      
      return { success, failed, total, successRate }
    })

    // 饼图配置
    const pieChartOption = computed(() => ({
      tooltip: {
        trigger: 'item',
        formatter: '{a} <br/>{b}: {c} ({d}%)'
      },
      legend: {
        orient: 'vertical',
        left: 'left'
      },
      series: [
        {
          name: '执行结果',
          type: 'pie',
          radius: '50%',
          data: [
            { value: statistics.value.success, name: '成功', itemStyle: { color: '#67C23A' } },
            { value: statistics.value.failed, name: '失败', itemStyle: { color: '#F56C6C' } },
            { value: statistics.value.error, name: '错误', itemStyle: { color: '#909399' } },
            { value: statistics.value.skipped, name: '跳过', itemStyle: { color: '#E6A23C' } }
          ].filter(item => item.value > 0), // 只显示有数据的项
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.5)'
            }
          }
        }
      ]
    }))

    // 筛选后的用例列表
    const filteredCaseRuns = computed(() => {
      if (!reportData.value?.case_runs) return []
      
      let filtered = reportData.value.case_runs
      
      // 状态筛选
      if (statusFilter.value) {
        filtered = filtered.filter(item => item.status === statusFilter.value)
      }
      
      // 关键词搜索
      if (searchKeyword.value) {
        const keyword = searchKeyword.value.toLowerCase()
        filtered = filtered.filter(item => 
          item.case_name.toLowerCase().includes(keyword)
        )
      }
      
      return filtered
    })

    // 加载报告数据
    const loadReportData = async () => {
      try {
        loading.value = true
        const response = await getSuiteRunDetail(projectId.value, runId.value)
        reportData.value = response.data
      } catch (error) {
        console.error('加载报告数据失败:', error)
        ElMessage.error('加载报告数据失败')
      } finally {
        loading.value = false
      }
    }

    // 查看用例详情
    const viewCaseDetail = async (caseRun) => {
      selectedCase.value = caseRun
      showCaseDetail.value = true
      caseDetailLoading.value = true
      caseDetailData.value = null
      
      try {
        const response = await getCaseRunDetail(projectId.value, caseRun.id)
        caseDetailData.value = response.data
      } catch (error) {
        console.error('加载用例详情失败:', error)
        ElMessage.error('加载用例详情失败')
      } finally {
        caseDetailLoading.value = false
      }
    }

    // 工具函数
    const formatDateTime = (dateTime) => {
      if (!dateTime) return '-'
      return new Date(dateTime).toLocaleString('zh-CN')
    }

    const formatDuration = (duration) => {
      if (!duration) return '-'
      if (duration < 1) {
        return `${Math.round(duration * 1000)}ms`
      }
      return `${duration.toFixed(2)}s`
    }

    const getStatusType = (status) => {
      switch (status) {
        case 'success': return 'success'
        case 'failed': return 'danger'
        default: return 'info'
      }
    }

    const getStatusText = (status) => {
      switch (status) {
        case 'success': return '成功'
        case 'failed': return '失败'
        default: return '未知'
      }
    }

    // 初始化
    onMounted(() => {
      loadReportData()
    })

    return {
      projectId,
      suiteId,
      runId,
      loading,
      reportData,
      showCaseDetail,
      selectedCase,
      caseDetailLoading,
      caseDetailData,
      statusFilter,
      searchKeyword,
      statistics,
      pieChartOption,
      filteredCaseRuns,
      loadReportData,
      viewCaseDetail,
      formatDateTime,
      formatDuration,
      getStatusType,
      getStatusText
    }
  }
}
</script>

<style scoped>
.suite-run-report {
  padding: 20px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 20px;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 10px 0;
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.loading-container,
.error-container {
  padding: 40px;
  text-align: center;
}

.report-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}

.info-card {
  margin-bottom: 20px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 16px;
}

.info-item {
  display: flex;
  align-items: center;
}

.info-item label {
  font-weight: 600;
  color: #606266;
  margin-right: 8px;
  min-width: 80px;
}

.statistics-row {
  margin-bottom: 20px;
}

.chart-card {
  height: 300px;
}

.chart-container {
  height: 220px;
}

.chart {
  height: 100%;
  width: 100%;
}

.statistics-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
  height: 220px;
  align-content: center;
}

.stat-item {
  text-align: center;
  padding: 20px;
  border-radius: 8px;
  background: #f8f9fa;
}

.stat-item.success {
  background: linear-gradient(135deg, #67C23A20, #67C23A10);
  border: 1px solid #67C23A30;
}

.stat-item.failed {
  background: linear-gradient(135deg, #F56C6C20, #F56C6C10);
  border: 1px solid #F56C6C30;
}

.stat-item.total {
  background: linear-gradient(135deg, #409EFF20, #409EFF10);
  border: 1px solid #409EFF30;
}

.stat-item.rate {
  background: linear-gradient(135deg, #E6A23C20, #E6A23C10);
  border: 1px solid #E6A23C30;
}

.stat-number {
  font-size: 28px;
  font-weight: bold;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: #606266;
}

.case-list-card {
  min-height: 400px;
}

.filter-bar {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #EBEEF5;
}

.case-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.case-item {
  padding: 16px;
  border: 1px solid #EBEEF5;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  background: #fff;
}

.case-item:hover {
  border-color: #409EFF;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.1);
}

.case-item-failed {
  border-left: 4px solid #F56C6C;
}

.case-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.case-name {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 16px;
}

.case-meta {
  display: flex;
  gap: 20px;
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}

.case-time,
.case-duration {
  display: flex;
  align-items: center;
  gap: 4px;
}

.case-error {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #FEF0F0;
  border: 1px solid #FCDEDE;
  border-radius: 4px;
  color: #F56C6C;
  font-size: 14px;
}

.dialog-loading,
.dialog-error {
  padding: 20px;
  text-align: center;
}
</style>