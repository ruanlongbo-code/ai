<template>
  <div class="coming-soon-page">
    <div class="page-header">
      <h2>🚀 未来可期</h2>
      <p class="subtitle">以下功能正在规划中，将在未来迭代中陆续上线</p>
    </div>

    <div class="roadmap-list">
      <!-- 测试环境管理 -->
      <div class="roadmap-card">
        <div class="card-icon" style="background: linear-gradient(135deg, #667eea, #764ba2);">
          <el-icon :size="32"><Platform /></el-icon>
        </div>
        <div class="card-content">
          <div class="card-header">
            <h3>测试环境管理</h3>
            <el-tag type="info" effect="plain" round>规划中</el-tag>
          </div>
          <p class="card-desc">
            集中管理和配置测试环境，支持环境变量管理、环境切换、环境状态监控等功能，
            帮助团队高效管理多套测试环境。
          </p>
          <div class="card-features">
            <span class="feature-tag">环境配置</span>
            <span class="feature-tag">变量管理</span>
            <span class="feature-tag">状态监控</span>
            <span class="feature-tag">一键切换</span>
          </div>
        </div>
      </div>

      <!-- 占位：更多未来功能可在此继续添加 -->
    </div>

    <div class="footer-note">
      <el-icon><InfoFilled /></el-icon>
      <span>有功能建议？欢迎随时反馈给管理员，你的需求将推动平台不断进化 ✨</span>
    </div>
  </div>
</template>

<script setup>
import { Platform, InfoFilled } from '@element-plus/icons-vue'
</script>

<style scoped>
.coming-soon-page {
  max-width: 900px;
  margin: 0 auto;
  padding: 32px 24px;
}

.page-header {
  text-align: center;
  margin-bottom: 40px;
}

.page-header h2 {
  font-size: 28px;
  font-weight: 700;
  color: #1a1a2e;
  margin-bottom: 8px;
}

.subtitle {
  color: #8c8c8c;
  font-size: 15px;
}

.roadmap-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.roadmap-card {
  display: flex;
  gap: 24px;
  padding: 28px;
  background: #fff;
  border: 1px solid #f0f0f0;
  border-radius: 16px;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.roadmap-card:hover {
  border-color: #d9d9ff;
  box-shadow: 0 8px 24px rgba(139, 92, 246, 0.1);
  transform: translateY(-2px);
}

.card-icon {
  flex-shrink: 0;
  width: 72px;
  height: 72px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.card-content {
  flex: 1;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 10px;
}

.card-header h3 {
  font-size: 18px;
  font-weight: 600;
  color: #1a1a2e;
  margin: 0;
}

.card-desc {
  color: #666;
  font-size: 14px;
  line-height: 1.7;
  margin-bottom: 14px;
}

.card-features {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.feature-tag {
  padding: 4px 12px;
  background: #f5f3ff;
  color: #7c3aed;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
}

.footer-note {
  margin-top: 48px;
  text-align: center;
  color: #b0b0b0;
  font-size: 13px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}
</style>
