<template>
  <div class="allure-list-page">
    <div class="page-header">
      <h2><el-icon style="color: #6366f1;"><TrendCharts /></el-icon> 接口测试报告</h2>
      <p class="subtitle">查看所有接口测试执行报告，分析质量趋势与性能指标</p>
    </div>

    <!-- 筛选栏 -->
    <el-card shadow="never" class="filter-card">
      <div class="filter-bar">
        <el-radio-group v-model="statusFilter" @change="fetchReports" size="default">
          <el-radio-button value="">全部</el-radio-button>
          <el-radio-button value="passed">通过</el-radio-button>
          <el-radio-button value="failed">失败</el-radio-button>
        </el-radio-group>
        <div class="filter-right">
          <span class="total-count">共 {{ total }} 条报告</span>
          <el-button @click="fetchReports" :icon="Refresh" circle size="small" title="刷新" />
        </div>
      </div>
    </el-card>

    <!-- 报告卡片列表 -->
    <div v-loading="loading" class="report-cards">
      <div
        v-for="item in reports"
        :key="item.run_id"
        class="report-card"
        :class="item.status"
        @click="goDetail(item)"
      >
        <div class="card-status-bar" :class="item.status"></div>
        <div class="card-content">
          <!-- 头部 -->
          <div class="card-top">
            <div class="card-title-area">
              <h3 class="card-title">{{ item.task_name }}</h3>
              <div class="card-meta">
                <span class="meta-time">{{ formatTime(item.start_time) }}</span>
                <el-tag size="small" effect="plain" type="info">{{ item.suite_count }} 套件</el-tag>
              </div>
            </div>
            <el-tag :type="item.status === 'passed' ? 'success' : 'danger'" effect="dark" size="default" class="status-tag">
              {{ item.status === 'passed' ? '通过' : '失败' }}
            </el-tag>
          </div>

          <!-- 统计指标 -->
          <div class="card-stats">
            <div class="stat-item">
              <div class="stat-num" :style="{ color: getPassRateColor(item.pass_rate) }">{{ item.pass_rate }}%</div>
              <div class="stat-name">通过率</div>
            </div>
            <div class="stat-divider"></div>
            <div class="stat-item">
              <div class="stat-num success">{{ item.passed_cases }}</div>
              <div class="stat-name">通过</div>
            </div>
            <div class="stat-divider"></div>
            <div class="stat-item">
              <div class="stat-num danger">{{ item.failed_cases }}</div>
              <div class="stat-name">失败</div>
            </div>
            <div class="stat-divider"></div>
            <div class="stat-item">
              <div class="stat-num warning">{{ item.skipped_cases }}</div>
              <div class="stat-name">跳过</div>
            </div>
            <div class="stat-divider"></div>
            <div class="stat-item">
              <div class="stat-num total">{{ item.total_cases }}</div>
              <div class="stat-name">总用例</div>
            </div>
            <div class="stat-divider"></div>
            <div class="stat-item">
              <div class="stat-num time">{{ formatDuration(item.duration_ms) }}</div>
              <div class="stat-name">耗时</div>
            </div>
          </div>

          <!-- 通过率进度条 -->
          <div class="card-progress">
            <el-progress
              :percentage="item.pass_rate"
              :stroke-width="6"
              :color="getPassRateColor(item.pass_rate)"
              :show-text="false"
            />
          </div>

          <!-- 底部 -->
          <div class="card-footer">
            <div class="footer-left">
              <span class="run-id">#{{ item.run_id }}</span>
            </div>
            <div class="footer-right">
              <el-button type="primary" size="small" plain class="view-btn">
                <el-icon><View /></el-icon> 查看报告
              </el-button>
            </div>
          </div>
        </div>
      </div>

      <el-empty v-if="!loading && reports.length === 0" description="暂无测试报告" :image-size="120">
        <template #description>
          <p>执行测试任务后，报告会自动生成</p>
        </template>
      </el-empty>
    </div>

    <!-- 分页 -->
    <div class="pagination-bar" v-if="total > pageSize">
      <el-pagination
        v-model:current-page="currentPage"
        :page-size="pageSize"
        :total="total"
        layout="prev, pager, next"
        @current-change="fetchReports"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { TrendCharts, Refresh, View } from '@element-plus/icons-vue'
import { useProjectStore } from '@/stores'
import { getApiAllureReports } from '@/api/apiTest'

const router = useRouter()
const projectStore = useProjectStore()
const projectId = () => projectStore.currentProject?.id

const loading = ref(false)
const reports = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = 12
const statusFilter = ref('')

const formatTime = (t) => t ? new Date(t).toLocaleString('zh-CN') : '-'

const formatDuration = (ms) => {
  if (!ms && ms !== 0) return '-'
  if (ms < 1000) return ms + 'ms'
  if (ms < 60000) return (ms / 1000).toFixed(1) + 's'
  return (ms / 60000).toFixed(1) + 'min'
}

const getPassRateColor = (rate) => {
  if (rate >= 90) return '#67c23a'
  if (rate >= 70) return '#e6a23c'
  return '#f56c6c'
}

const fetchReports = async () => {
  if (!projectId()) return
  loading.value = true
  try {
    const params = { page: currentPage.value, page_size: pageSize }
    if (statusFilter.value) params.status = statusFilter.value
    const res = await getApiAllureReports(projectId(), params)
    const data = res.data || res
    reports.value = data.reports || []
    total.value = data.total || 0
  } catch (e) {
    ElMessage.error('加载报告列表失败')
  } finally {
    loading.value = false
  }
}

const goDetail = (item) => {
  router.push(`/api-test/allure-report/${projectId()}/${item.run_id}`)
}

onMounted(() => {
  fetchReports()
})
</script>

<style scoped>
.allure-list-page { padding: 20px 24px; }

.page-header { margin-bottom: 16px; }
.page-header h2 {
  color: #1f2937; margin: 0 0 6px 0; font-size: 22px; font-weight: 600;
  display: flex; align-items: center; gap: 8px;
}
.subtitle { color: #6b7280; margin: 0; font-size: 13px; }

.filter-card { margin-bottom: 16px; border: none; }
.filter-bar { display: flex; justify-content: space-between; align-items: center; }
.filter-right { display: flex; align-items: center; gap: 12px; }
.total-count { font-size: 13px; color: #6b7280; }

.report-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(440px, 1fr));
  gap: 16px;
}

.report-card {
  background: #fff; border-radius: 12px; overflow: hidden;
  cursor: pointer; transition: all 0.25s;
  box-shadow: 0 1px 6px rgba(0,0,0,0.06); border: 1px solid #f0f0f0;
  display: flex;
}
.report-card:hover {
  transform: translateY(-3px); box-shadow: 0 8px 24px rgba(0,0,0,0.1);
  border-color: #e0e0e0;
}

.card-status-bar { width: 4px; flex-shrink: 0; }
.card-status-bar.passed { background: linear-gradient(to bottom, #67c23a, #95d475); }
.card-status-bar.failed { background: linear-gradient(to bottom, #f56c6c, #f89898); }

.card-content { flex: 1; padding: 16px 18px; min-width: 0; }

.card-top { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 14px; }
.card-title-area { min-width: 0; flex: 1; }
.card-title {
  font-size: 15px; font-weight: 600; color: #1f2937; margin: 0 0 6px 0;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.card-meta { display: flex; align-items: center; gap: 8px; }
.meta-time { font-size: 12px; color: #9ca3af; }
.status-tag { flex-shrink: 0; margin-left: 12px; }

.card-stats {
  display: flex; align-items: center; gap: 0; margin-bottom: 12px;
  padding: 10px 0; background: #f9fafb; border-radius: 8px;
}
.stat-item { flex: 1; text-align: center; }
.stat-num { font-size: 20px; font-weight: 700; line-height: 1.2; color: #1f2937; }
.stat-num.success { color: #67c23a; }
.stat-num.danger { color: #f56c6c; }
.stat-num.warning { color: #e6a23c; }
.stat-num.total { color: #3b82f6; }
.stat-num.time { color: #8b5cf6; font-size: 16px; }
.stat-name { font-size: 11px; color: #9ca3af; margin-top: 2px; }
.stat-divider { width: 1px; height: 28px; background: #e5e7eb; }

.card-progress { margin-bottom: 12px; }

.card-footer { display: flex; justify-content: space-between; align-items: center; }
.footer-left { display: flex; align-items: center; gap: 8px; }
.run-id { font-size: 12px; color: #c0c4cc; font-weight: 500; }
.footer-right { display: flex; align-items: center; gap: 12px; }
.view-btn { border-radius: 6px; }

.pagination-bar { display: flex; justify-content: center; margin-top: 24px; }

@media (max-width: 900px) {
  .report-cards { grid-template-columns: 1fr; }
}
</style>
