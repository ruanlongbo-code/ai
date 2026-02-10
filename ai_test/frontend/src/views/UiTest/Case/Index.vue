<template>
  <div class="ui-case-management-page">
    <div class="page-header">
      <h2>用例管理</h2>
      <p class="subtitle">管理UI测试用例</p>
    </div>

    <div class="page-content">
      <el-card class="content-card">
        <template #header>
          <div class="card-header">
            <span>用例列表</span>
            <el-button type="primary" @click="handleCreate">
              <el-icon><Plus /></el-icon>
              新建用例
            </el-button>
          </div>
        </template>
        
        <div class="table-container">
          <!-- 这里将来放置UI用例管理的具体内容 -->
          <el-empty description="UI用例管理功能开发中..." />
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'

const handleCreate = () => {
  ElMessage.info('新建用例功能开发中...')
}
</script>

<style scoped>
.ui-case-management-page {
  padding: 20px;
  background: #f5f7fa;
  min-height: 100vh;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h2 {
  color: #303133;
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
}

.subtitle {
  color: #606266;
  margin: 0;
  font-size: 14px;
}

.page-content {
  background: white;
  border-radius: 8px;
  overflow: hidden;
}

.content-card {
  border: none;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.table-container {
  min-height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>