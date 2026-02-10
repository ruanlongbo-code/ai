<template>
  <el-card class="requirement-filter">
    <div class="filter-content">
      <div class="filter-left">
        <el-select
          v-model="localFilters.moduleId"
          placeholder="选择模块"
          clearable
          @change="handleFilterChange"
          style="width: 200px; margin-right: 16px;"
        >
          <el-option
            v-for="module in modules"
            :key="module.id"
            :label="module.name"
            :value="module.id"
          >
            <div class="module-option">
              <span class="module-name">{{ module.name }}</span>
              <span v-if="module.description" class="module-desc">{{ module.description }}</span>
            </div>
          </el-option>
        </el-select>
        
        <el-select
          v-model="localFilters.status"
          placeholder="选择状态"
          clearable
          @change="handleFilterChange"
          style="width: 150px; margin-right: 16px;"
        >
          <el-option
            v-for="(label, value) in REQUIREMENT_STATUS_LABELS"
            :key="value"
            :label="label"
            :value="value"
          />
        </el-select>
        
        <el-select
          v-model="localFilters.priority"
          placeholder="选择优先级"
          clearable
          @change="handleFilterChange"
          style="width: 150px; margin-right: 16px;"
        >
          <el-option
            v-for="(label, value) in REQUIREMENT_PRIORITY_LABELS"
            :key="value"
            :label="label"
            :value="parseInt(value)"
          />
        </el-select>
      </div>
      
      <div class="filter-right">
        <el-input
          v-model="localFilters.keyword"
          placeholder="搜索需求标题或描述"
          @input="handleSearch"
          style="width: 300px;"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </div>
    </div>
    
    <!-- 筛选标签 -->
    <div v-if="hasActiveFilters" class="filter-tags">
      <span class="filter-label">当前筛选：</span>
      <el-tag
        v-if="localFilters.moduleId"
        closable
        @close="clearFilter('moduleId')"
        style="margin-right: 8px;"
      >
        模块：{{ getModuleName(localFilters.moduleId) }}
      </el-tag>
      <el-tag
        v-if="localFilters.status"
        closable
        @close="clearFilter('status')"
        style="margin-right: 8px;"
      >
        状态：{{ REQUIREMENT_STATUS_LABELS[localFilters.status] }}
      </el-tag>
      <el-tag
        v-if="localFilters.priority"
        closable
        @close="clearFilter('priority')"
        style="margin-right: 8px;"
      >
        优先级：{{ REQUIREMENT_PRIORITY_LABELS[localFilters.priority] }}
      </el-tag>
      <el-tag
        v-if="localFilters.keyword"
        closable
        @close="clearFilter('keyword')"
        style="margin-right: 8px;"
      >
        关键词：{{ localFilters.keyword }}
      </el-tag>
      <el-button link type="primary" @click="clearAllFilters">
        清空筛选
      </el-button>
    </div>
  </el-card>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { Search } from '@element-plus/icons-vue'
import {
  REQUIREMENT_STATUS_LABELS,
  REQUIREMENT_PRIORITY_LABELS
} from '@/api/functional_test'

const props = defineProps({
  modules: {
    type: Array,
    default: () => []
  },
  filters: {
    type: Object,
    default: () => ({
      moduleId: null,
      status: null,
      priority: null,
      keyword: ''
    })
  }
})

const emit = defineEmits(['filter-change', 'search'])

// 本地筛选状态
const localFilters = reactive({
  moduleId: null,
  status: null,
  priority: null,
  keyword: ''
})

// 搜索防抖
let searchTimer = null

// 计算属性
const hasActiveFilters = computed(() => {
  return localFilters.moduleId || localFilters.status || localFilters.priority || localFilters.keyword
})

// 方法
const getModuleName = (moduleId) => {
  if (!moduleId) return '未分配模块'
  const module = props.modules.find(m => m.id === moduleId)
  return module ? module.name : `模块 ${moduleId}`
}

const handleFilterChange = () => {
  emit('filter-change', { ...localFilters })
}

const handleSearch = () => {
  // 搜索防抖
  if (searchTimer) {
    clearTimeout(searchTimer)
  }
  searchTimer = setTimeout(() => {
    emit('search', localFilters.keyword)
  }, 300)
}

const clearFilter = (filterKey) => {
  localFilters[filterKey] = filterKey === 'keyword' ? '' : null
  handleFilterChange()
}

const clearAllFilters = () => {
  localFilters.moduleId = null
  localFilters.status = null
  localFilters.priority = null
  localFilters.keyword = ''
  handleFilterChange()
}

// 监听外部筛选条件变化
watch(
  () => props.filters,
  (newFilters) => {
    Object.assign(localFilters, newFilters)
  },
  { immediate: true, deep: true }
)
</script>

<style scoped>
.requirement-filter {
  margin-bottom: 24px;
}

.filter-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.filter-left {
  display: flex;
  align-items: center;
}

.filter-tags {
  display: flex;
  align-items: center;
  padding-top: 16px;
  border-top: 1px solid #e5e7eb;
}

.filter-label {
  color: #6b7280;
  font-size: 14px;
  margin-right: 12px;
}

.module-option {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.module-name {
  font-weight: 500;
}

.module-desc {
  font-size: 12px;
  color: #6b7280;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .filter-content {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
  
  .filter-left {
    flex-direction: column;
    gap: 12px;
  }
  
  .filter-left .el-select,
  .filter-right .el-input {
    width: 100% !important;
    margin-right: 0 !important;
  }
  
  .filter-tags {
    flex-wrap: wrap;
    gap: 8px;
  }
}
</style>