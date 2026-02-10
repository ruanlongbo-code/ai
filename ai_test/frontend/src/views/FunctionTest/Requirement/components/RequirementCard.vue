<template>
  <el-card class="requirement-card" :class="{ 'is-clickable': clickable }" @click="handleClick">
    <div class="card-header">
      <div class="title-section">
        <h4 class="requirement-title">{{ requirement.title }}</h4>
        <span v-if="requirement.doc_no" class="doc-no">{{ requirement.doc_no }}</span>
      </div>
      <div class="status-section">
        <el-tag
          :type="getStatusTagType(requirement.status)"
          size="small"
        >
          {{ REQUIREMENT_STATUS_LABELS[requirement.status] }}
        </el-tag>
      </div>
    </div>

    <div v-if="requirement.description" class="card-content">
      <p class="description">{{ truncateDescription(requirement.description) }}</p>
    </div>

    <div class="card-footer">
      <div class="meta-info">
        <div class="priority-info">
          <el-tag
            :color="REQUIREMENT_PRIORITY_COLORS[requirement.priority]"
            effect="light"
            size="small"
          >
            {{ REQUIREMENT_PRIORITY_LABELS[requirement.priority] }}
          </el-tag>
        </div>
        <div class="time-info">
          <span class="create-time">{{ formatDate(requirement.created_at) }}</span>
        </div>
      </div>
      
      <div v-if="showActions" class="actions" @click.stop>
        <el-button
          link
          type="primary"
          size="small"
          @click="handleView"
        >
          查看
        </el-button>
        <el-button
          link
          type="primary"
          size="small"
          @click="handleEdit"
        >
          编辑
        </el-button>
        <el-button
          link
          type="primary"
          size="small"
          @click="handleGenerateCases"
        >
          生成用例
        </el-button>
        <el-button
          link
          type="danger"
          size="small"
          @click="handleDelete"
        >
          删除
        </el-button>
      </div>
    </div>
  </el-card>
</template>

<script setup>
import { computed } from 'vue'
import {
  REQUIREMENT_STATUS_LABELS,
  REQUIREMENT_PRIORITY_LABELS,
  REQUIREMENT_PRIORITY_COLORS
} from '@/api/functional_test'

const props = defineProps({
  requirement: {
    type: Object,
    required: true
  },
  clickable: {
    type: Boolean,
    default: true
  },
  showActions: {
    type: Boolean,
    default: true
  },
  maxDescriptionLength: {
    type: Number,
    default: 100
  }
})

const emit = defineEmits([
  'click',
  'view',
  'edit',
  'generate-cases',
  'delete'
])

// 计算属性
const getStatusTagType = (status) => {
  const typeMap = {
    draft: '',
    reviewing: 'warning',
    approved: 'success',
    rejected: 'danger',
    archived: 'info'
  }
  return typeMap[status] || ''
}

// 方法
const formatDate = (dateString) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleDateString('zh-CN')
}

const truncateDescription = (description) => {
  if (!description) return ''
  if (description.length <= props.maxDescriptionLength) {
    return description
  }
  return description.substring(0, props.maxDescriptionLength) + '...'
}

const handleClick = () => {
  if (props.clickable) {
    emit('click', props.requirement)
  }
}

const handleView = () => {
  emit('view', props.requirement)
}

const handleEdit = () => {
  emit('edit', props.requirement)
}

const handleGenerateCases = () => {
  emit('generate-cases', props.requirement)
}

const handleDelete = () => {
  emit('delete', props.requirement)
}
</script>

<style scoped>
.requirement-card {
  margin-bottom: 16px;
  transition: all 0.3s ease;
  border: 1px solid #e5e7eb;
}

.requirement-card.is-clickable {
  cursor: pointer;
}

.requirement-card.is-clickable:hover {
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.15);
  border-color: #8b5cf6;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.title-section {
  flex: 1;
  margin-right: 16px;
}

.requirement-title {
  color: #1f2937;
  margin: 0 0 4px 0;
  font-size: 16px;
  font-weight: 600;
  line-height: 1.4;
}

.doc-no {
  font-size: 12px;
  color: #6b7280;
  background: #f3f4f6;
  padding: 2px 6px;
  border-radius: 4px;
}

.status-section {
  flex-shrink: 0;
}

.card-content {
  margin-bottom: 16px;
}

.description {
  color: #6b7280;
  font-size: 14px;
  line-height: 1.5;
  margin: 0;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid #f3f4f6;
}

.meta-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.time-info {
  font-size: 12px;
  color: #9ca3af;
}

.actions {
  display: flex;
  gap: 8px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .card-footer {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
  
  .meta-info {
    justify-content: space-between;
  }
  
  .actions {
    justify-content: center;
  }
}
</style>