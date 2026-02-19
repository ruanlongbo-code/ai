<template>
  <div class="environment-edit">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <el-button
            @click="handleBack"
            type="text"
            class="back-button"
        >
          <el-icon>
            <ArrowLeft/>
          </el-icon>
          返回环境列表
        </el-button>

      </div>
      <div class="header-actions" style="padding-bottom: 10px;">
        <el-button @click="handleRefresh" :loading="loading">
          <el-icon>
            <Refresh/>
          </el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="8" animated/>
    </div>

    <!-- 主要内容 -->
    <div v-else-if="environmentData.id" class="page-content">
      <el-tabs
          v-model="activeTab"
          type="border-card"
          class="environment-tabs"
          @tab-change="handleTabChange"
      >
        <template #extra>
          <div class="tabs-extra-actions">
            <el-button type="text" class="back-button" @click="handleBack">
              <el-icon>
                <ArrowLeft/>
              </el-icon>
              返回环境列表
            </el-button>
            <el-button @click="handleRefresh" :loading="loading">
              <el-icon>
                <Refresh/>
              </el-icon>
              刷新
            </el-button>
          </div>
        </template>
        <!-- 基本信息 Tab -->
        <el-tab-pane label="基本信息" name="basic">
          <template #label>
            <span class="tab-label">
              <el-icon><InfoFilled/></el-icon>
              基本信息
            </span>
          </template>
          <BasicInfoTab
              :environment-data="environmentData"
              @update="handleEnvironmentUpdate"
          />
        </el-tab-pane>

        <!-- 环境变量 Tab -->
        <el-tab-pane label="环境变量" name="variables">
          <template #label>
            <span class="tab-label">
              <el-icon><Setting/></el-icon>
              环境变量
            </span>
          </template>
          <EnvironmentVariablesTab
              :environment-id="Number(environmentId)"
              :configs="environmentData.configs"
              @update="handleEnvironmentUpdate"
          />
        </el-tab-pane>

        <!-- 数据库配置 Tab -->
        <el-tab-pane label="数据库配置" name="database">
          <template #label>
            <span class="tab-label">
              <el-icon><Coin/></el-icon>
              数据库配置
            </span>
          </template>
          <DatabaseConfigTab
              :environment-id="Number(environmentId)"
              :databases="environmentData.databases"
              @update="handleEnvironmentUpdate"
          />
        </el-tab-pane>

        <!-- 全局函数 Tab -->
        <el-tab-pane label="全局函数" name="functions">
          <template #label>
            <span class="tab-label">
              <el-icon><Document/></el-icon>
              全局函数
            </span>
          </template>
          <GlobalFunctionTab
              :environment-data="environmentData"
              @update="handleEnvironmentUpdate"
          />
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 错误状态 -->
    <div v-else class="error-container">
      <el-empty
          description="环境数据加载失败"
          :image-size="120"
      >
        <el-button type="primary" @click="loadEnvironmentData">
          重新加载
        </el-button>
      </el-empty>
    </div>
  </div>
</template>

<script setup>
import {ref, reactive, onMounted, watch, computed} from 'vue'
import {useRoute, useRouter} from 'vue-router'
import {ElMessage} from 'element-plus'
import {
  ArrowLeft,
  Refresh,
  InfoFilled,
  Setting,
  Coin,
  Document
} from '@element-plus/icons-vue'
import {useProjectStore} from '@/stores'
import {getTestEnvironmentDetail} from '@/api/test_environment'

// 导入Tab组件
import BasicInfoTab from './components/BasicInfoTab.vue'
import EnvironmentVariablesTab from './components/EnvironmentVariablesTab.vue'
import DatabaseConfigTab from './components/DatabaseConfigTab.vue'
import GlobalFunctionTab from './components/GlobalFunctionTab.vue'

const route = useRoute()
const router = useRouter()
const projectStore = useProjectStore()

// 响应式数据
const loading = ref(false)
const activeTab = ref('basic')
const environmentData = reactive({
  id: null,
  name: '',
  func_global: '',
  created_at: '',
  updated_at: ''
})

// 获取环境ID
const environmentId = computed(() => {
  return route.params.environmentId
})

// 加载环境数据
const loadEnvironmentData = async () => {
  if (!projectStore.currentProject?.id || !environmentId.value) {
    ElMessage.error('参数错误')
    return
  }

  try {
    loading.value = true

    const response = await getTestEnvironmentDetail(
        projectStore.currentProject.id,
        environmentId.value
    )

    if (response.data) {
      Object.assign(environmentData, response.data)
    }
  } catch (error) {
    console.error('加载环境数据失败:', error)
    ElMessage.error('加载环境数据失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

// 处理环境数据更新
const handleEnvironmentUpdate = (updatedData) => {
  Object.assign(environmentData, updatedData)
}

// 处理返回
const handleBack = () => {
  router.push('/project-settings/environment')
}

// 处理刷新
const handleRefresh = async () => {
  await loadEnvironmentData()
  ElMessage.success('刷新成功')
}

// 处理Tab切换
const handleTabChange = (tabName) => {
  console.log('切换到Tab:', tabName)
}

// 监听路由参数变化
watch(() => route.params.environmentId, (newId) => {
  if (newId) {
    loadEnvironmentData()
  }
}, {immediate: true})

// 组件挂载时加载数据
onMounted(() => {
  // 确保项目数据已加载
  if (!projectStore.currentProject?.id) {
    ElMessage.error('请先选择项目')
    router.push('/projects')
    return
  }

  loadEnvironmentData()
})
</script>

<style scoped>
.environment-edit {
  height: 100%;
  display: flex;
  flex-direction: column;
  /* 旧：min-height: 100vh; 导致与主内容高度计算冲突 */
  min-height: 0;
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 0;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  padding: 0 !important;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.back-button {
  /* 移除强制白色文字，使用默认主题色 */
  font-size: 14px;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 6px;
  transition: all 0.3s ease;
}

.back-button:hover {
  background: rgba(255, 255, 255, 0.2) !important;
  border-color: rgba(255, 255, 255, 0.3);
  transform: translateX(-2px);
}

.page-title h2 {
  color: #303133;
  margin: 0 0 4px 0;
  font-size: 24px;
  font-weight: 600;
}

.page-title p {
  color: #606266;
  margin: 0;
  font-size: 14px;
}

.header-actions .el-button {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  /* 移除白色字体，使用默认颜色 */
}

.header-actions .el-button:hover {
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(139, 92, 246, 0.4);
  color: #ffffff;
  transform: translateY(-1px);
}

.loading-container {
  flex: 1;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  padding: 24px;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.page-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.environment-tabs {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  overflow: hidden;
}

/* Tabs 右侧操作区域样式 */
.environment-tabs :deep(.el-tabs__extra) {
  display: flex;
  align-items: center;
  gap: 8px;
}

.tabs-extra-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  padding-right: 8px;
}


/* 骨架屏样式 */
.loading-container :deep(.el-skeleton__item) {
  background: rgba(255, 255, 255, 0.1);
}

.loading-container :deep(.el-skeleton__item.is-animated::after) {
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .environment-edit {
    padding: 12px;
  }

  .page-header {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
    padding: 0 !important;

  }

  .header-left {
    flex-direction: column;
    gap: 8px;
    align-items: flex-start;

  }

  .page-title h2 {
    font-size: 20px;
  }

  .environment-tabs :deep(.el-tabs__nav-wrap) {
    padding: 0 12px;
  }

  .environment-tabs :deep(.el-tabs__item) {
    padding: 12px 16px;
    font-size: 14px;
  }

  .environment-tabs :deep(.el-tabs__content) {
    padding: 16px;
  }

  .tab-label {
    gap: 4px;
  }

  .tab-label .el-icon {
    font-size: 14px;
  }
}

@media (max-width: 480px) {
  .environment-edit {
    padding: 8px;
  }

  .page-header {
    padding: 0 !important;
  }

  .page-title h2 {
    font-size: 18px;
  }

  .environment-tabs :deep(.el-tabs__nav-wrap) {
    padding: 0 8px;
  }

  .environment-tabs :deep(.el-tabs__item) {
    padding: 10px 12px;
    font-size: 13px;
  }

  .environment-tabs :deep(.el-tabs__content) {
    padding: 12px;
  }

  .back-button {
    padding: 6px 10px;
    font-size: 13px;
  }
}
</style>