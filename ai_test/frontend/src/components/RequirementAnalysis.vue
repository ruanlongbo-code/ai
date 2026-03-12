<template>
  <div class="requirement-analysis">
    <el-collapse v-model="activeNames" class="info-collapse">
      <!-- 1. 基础信息 -->
      <el-collapse-item title="1. 基础信息" name="basic">
        <div v-if="data.basic_info" class="info-section">
          <h4>{{ data.basic_info.title || '未知标题' }}</h4>

          <div v-if="data.basic_info.one_line_requirement" class="field-row">
            <span class="field-label">一句话需求：</span>
            <span>{{ data.basic_info.one_line_requirement }}</span>
          </div>

          <div v-if="data.basic_info.background" class="field-row">
            <span class="field-label">背景目标：</span>
            <span>{{ data.basic_info.background }}</span>
          </div>

          <div v-if="data.basic_info.business_scope" class="field-row">
            <span class="field-label">业务范围：</span>
            <span>{{ data.basic_info.business_scope }}</span>
          </div>

          <!-- 版本历史 -->
          <div v-if="data.basic_info.versions?.length" class="sub-section">
            <span class="field-label">版本历史：</span>
            <el-table :data="data.basic_info.versions" size="small" border stripe class="mini-table">
              <el-table-column prop="version" label="版本" width="80" />
              <el-table-column prop="date" label="日期" width="110" />
              <el-table-column prop="author" label="作者" width="100" />
              <el-table-column prop="changes" label="变更说明" />
            </el-table>
          </div>

          <!-- 功能范围 -->
          <div v-if="data.basic_info.functional_scope?.length" class="sub-section">
            <span class="field-label">功能范围：</span>
            <el-table :data="data.basic_info.functional_scope" size="small" border stripe class="mini-table">
              <el-table-column prop="feature" label="功能" width="160" />
              <el-table-column prop="detail" label="说明" />
              <el-table-column prop="priority" label="优先级" width="80">
                <template #default="{ row }">
                  <el-tag :type="priorityType(row.priority)" size="small">{{ row.priority }}</el-tag>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
        <el-empty v-else description="暂无基础信息" :image-size="40" />
      </el-collapse-item>

      <!-- 2. 产品概要设计 -->
      <el-collapse-item title="2. 产品概要设计 // Outline Design" name="outline">
        <div v-if="data.outline_design" class="info-section">
          <div v-if="data.outline_design.functional_architecture" class="field-row">
            <span class="field-label">功能架构：</span>
            <span>{{ data.outline_design.functional_architecture }}</span>
          </div>

          <div v-if="data.outline_design.domain_model?.entities?.length" class="sub-section">
            <span class="field-label">领域模型：</span>
            <p v-if="data.outline_design.domain_model.description" class="desc-text">
              {{ data.outline_design.domain_model.description }}
            </p>
            <div class="entity-list">
              <div v-for="entity in data.outline_design.domain_model.entities" :key="entity.name" class="entity-card">
                <span class="entity-name">{{ entity.name }}</span>
                <div class="entity-fields">
                  <el-tag v-for="field in entity.key_fields" :key="field" size="small" type="info" class="field-tag">
                    {{ field }}
                  </el-tag>
                </div>
              </div>
            </div>
          </div>

          <div v-if="data.outline_design.user_flow" class="field-row">
            <span class="field-label">用户动线：</span>
            <span>{{ data.outline_design.user_flow }}</span>
          </div>
        </div>
        <el-empty v-else description="暂无概要设计信息" :image-size="40" />
      </el-collapse-item>

      <!-- 3. 详细需求模块 -->
      <el-collapse-item title="3. 产品详细需求、流程与界面" name="detail">
        <div v-if="data.detailed_requirements?.modules?.length" class="info-section">
          <div v-for="mod in data.detailed_requirements.modules" :key="mod.name" class="module-block">
            <h5 class="module-name">{{ mod.name }}</h5>
            <div v-if="mod.sub_modules?.length" class="sub-module-list">
              <div v-for="sub in mod.sub_modules" :key="sub.name" class="sub-module-item">
                <el-tag :type="subModuleTagType(sub.type)" size="small" class="type-tag">{{ sub.type }}</el-tag>
                <span class="sub-name">{{ sub.name }}</span>
                <span v-if="sub.description" class="sub-desc">— {{ sub.description }}</span>
              </div>
            </div>
          </div>
        </div>
        <el-empty v-else description="暂无详细需求信息" :image-size="40" />
      </el-collapse-item>
    </el-collapse>

    <!-- 流程图 -->
    <div v-if="data.detailed_requirements?.flowchart?.nodes?.length" class="flowchart-section">
      <h4 class="section-title">
        <el-icon><Share /></el-icon>
        业务流程图
      </h4>
      <RequirementFlowchart :flowchart="data.detailed_requirements.flowchart" />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Share } from '@element-plus/icons-vue'
import RequirementFlowchart from './RequirementFlowchart.vue'

defineProps({
  data: {
    type: Object,
    default: () => ({})
  }
})

const activeNames = ref(['basic', 'outline', 'detail'])

function priorityType(p) {
  if (p === 'P0') return 'danger'
  if (p === 'P1') return 'warning'
  if (p === 'P2') return 'info'
  return ''
}

function subModuleTagType(type) {
  const map = { 'API': '', '页面': 'success', '事件': 'warning', '资金流': 'danger', '流程': 'info', '配置': 'info' }
  return map[type] || ''
}
</script>

<style scoped>
.requirement-analysis {
  padding: 0;
}
.info-collapse {
  margin-bottom: 20px;
}
.info-section h4 {
  margin: 0 0 12px 0;
  font-size: 16px;
  color: #303133;
}
.field-row {
  margin-bottom: 8px;
  line-height: 1.6;
  color: #606266;
  font-size: 13px;
}
.field-label {
  font-weight: 600;
  color: #303133;
}
.sub-section {
  margin: 12px 0;
}
.mini-table {
  margin-top: 8px;
}
.desc-text {
  color: #909399;
  font-size: 13px;
  margin: 4px 0 10px 0;
}
.entity-list {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 8px;
}
.entity-card {
  background: #f5f7fa;
  border-radius: 6px;
  padding: 10px 14px;
  min-width: 200px;
}
.entity-name {
  font-weight: 600;
  font-size: 13px;
  color: #303133;
  display: block;
  margin-bottom: 6px;
}
.entity-fields {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}
.field-tag {
  font-size: 11px;
}
.module-block {
  margin-bottom: 16px;
}
.module-name {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #303133;
  padding-left: 8px;
  border-left: 3px solid #409eff;
}
.sub-module-list {
  padding-left: 12px;
}
.sub-module-item {
  margin-bottom: 6px;
  font-size: 13px;
  color: #606266;
  display: flex;
  align-items: center;
  gap: 8px;
}
.type-tag {
  flex-shrink: 0;
}
.sub-name {
  font-weight: 500;
}
.sub-desc {
  color: #909399;
}
.flowchart-section {
  margin-top: 16px;
}
.section-title {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 0 0 12px 0;
  font-size: 16px;
  color: #303133;
}
</style>
