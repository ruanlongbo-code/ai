<template>
  <div class="notification-list">
    <div class="notification-header">
      <h4>生成进度</h4>
      <div class="header-actions">
        <el-button 
          size="small" 
          :icon="Delete" 
          circle 
          @click="clearNotifications"
          :disabled="notifications.length === 0"
          title="清空进度记录"
        />
      </div>
    </div>
    
    <div ref="notificationContentRef" class="notification-content">
      <div v-if="notifications.length === 0" class="empty-notifications">
        <el-empty description="暂无生成进度" :image-size="80" />
      </div>
      
      <div v-else class="notifications-wrapper">
          <div 
            v-for="notification in displayNotifications" 
            :key="notification.id"
            class="notification-item"
            :class="[
              `notification-${notification.type}`,
              { 'unread': !notification.read }
            ]"
            @click="markAsRead(notification.id)"
          >
            <div class="notification-icon">
              <el-icon v-if="notification.type === 'start'"><VideoPlay /></el-icon>
              <el-icon v-else-if="notification.type === 'info'"><InfoFilled /></el-icon>
              <el-icon v-else-if="notification.type === 'complete'"><SuccessFilled /></el-icon>
              <el-icon v-else-if="notification.type === 'error'"><CircleCloseFilled /></el-icon>
              <el-icon v-else><Bell /></el-icon>
            </div>
            
            <div class="notification-body">
              <div class="notification-message">
                <span class="message-content">{{ getDisplayMessage(notification.message) }}</span>
                <el-tag 
                  v-if="notification.type" 
                  :type="getMessageTypeTag(notification.type)" 
                  size="small" 
                  class="message-type-tag"
                >
                  {{ getMessageTypeLabel(notification.type) }}
                </el-tag>
              </div>
              <div class="notification-time">{{ formatTime(notification.timestamp) }}</div>
            </div>
            
            <div v-if="!notification.read" class="unread-indicator"></div>
          </div>
        </div>
      </div>
    </div>

</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { 
  Delete, 
  VideoPlay, 
  InfoFilled, 
  SuccessFilled, 
  CircleCloseFilled 
} from '@element-plus/icons-vue'

// Props
const props = defineProps({
  notifications: {
    type: Array,
    default: () => []
  }
})

// 自动滚动到底部
const notificationContentRef = ref(null)

const scrollToBottom = async () => {
  await nextTick()
  if (notificationContentRef.value) {
    notificationContentRef.value.scrollTop = notificationContentRef.value.scrollHeight
  }
}

// 监听通知数量变化，自动滚动
watch(
  () => props.notifications.length,
  () => {
    scrollToBottom()
  }
)

// Emits
const emit = defineEmits(['clear', 'mark-read', 'mark-all-read'])

// 计算属性
const displayNotifications = computed(() => {
  // 按时间戳升序排序，从早到晚显示
  const sorted = [...props.notifications].sort((a, b) => a.timestamp - b.timestamp)
  // 显示所有消息，不再限制数量
  return sorted
})

const clearNotifications = () => {
  emit('clear')
}

const markAsRead = (id) => {
  emit('mark-read', id)
}

const markAllAsRead = () => {
  emit('mark-all-read')
}

const formatTime = (timestamp) => {
  const now = Date.now()
  const diff = now - timestamp
  
  if (diff < 60000) { // 1分钟内
    return '刚刚'
  } else if (diff < 3600000) { // 1小时内
    return `${Math.floor(diff / 60000)}分钟前`
  } else if (diff < 86400000) { // 24小时内
    return `${Math.floor(diff / 3600000)}小时前`
  } else {
    return new Date(timestamp).toLocaleString('zh-CN', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }
}

// 获取消息类型标签样式
const getMessageTypeTag = (type) => {
  const typeMap = {
    'start': 'primary',
    'info': 'info', 
    'complete': 'success',
    'error': 'danger'
  }
  return typeMap[type] || 'info'
}

// 获取消息类型标签文本
const getMessageTypeLabel = (type) => {
  const labelMap = {
    'start': '开始',
    'info': '进度',
    'complete': '完成', 
    'error': '错误'
  }
  return labelMap[type] || '消息'
}

// 过滤消息内容，移除需求标题
const getDisplayMessage = (message) => {
  if (!message) return ''
  
  // 移除以"需求："开头的内容
  const lines = message.split('\n')
  const filteredLines = lines.filter(line => {
    const trimmedLine = line.trim()
    return !trimmedLine.startsWith('需求：') && 
           !trimmedLine.startsWith('需求:') &&
           !trimmedLine.match(/^需求\s*[:：]/)
  })
  
  return filteredLines.join('\n').trim()
}

// 暴露方法给父组件
defineExpose({
  markAllAsRead,
  scrollToBottom
})
</script>

<style scoped>
.notification-list {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: white;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.notification-header {
  padding: 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #e4e7ed;
  flex-shrink: 0;
}

.notification-header h4 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.notification-content {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.empty-notifications {
  padding: 20px;
  text-align: center;
}

.notifications-wrapper {
  padding: 8px 0;
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
}

.notification-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 16px;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
  border-left: 3px solid transparent;
}

.notification-item:hover {
  background-color: #f5f7fa;
}

.notification-item.unread {
  background-color: #f0f9ff;
  border-left-color: #409eff;
}

.notification-item.unread:hover {
  background-color: #e6f4ff;
}

/* 不同类型消息的左边框颜色 */
.notification-item.notification-start {
  border-left-color: #409eff;
}

.notification-item.notification-info {
  border-left-color: #909399;
}

.notification-item.notification-complete {
  border-left-color: #67c23a;
}

.notification-item.notification-error {
  border-left-color: #f56c6c;
}

.notification-icon {
  flex-shrink: 0;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-top: 2px;
}

.notification-start .notification-icon {
  color: #409eff;
}

.notification-info .notification-icon {
  color: #909399;
}

.notification-complete .notification-icon {
  color: #67c23a;
}

.notification-error .notification-icon {
  color: #f56c6c;
}

.notification-body {
  flex: 1;
  min-width: 0;
}

.notification-message {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  line-height: 1.4;
  color: #303133;
  margin-bottom: 4px;
  word-break: break-word;
}

.message-content {
  flex: 1;
  min-width: 0;
}

.message-type-tag {
  flex-shrink: 0;
  font-size: 11px;
  height: 18px;
  line-height: 16px;
  padding: 0 6px;
  border-radius: 9px;
}

.notification-time {
  font-size: 12px;
  color: #909399;
}

.unread-indicator {
  flex-shrink: 0;
  width: 8px;
  height: 8px;
  background-color: #409eff;
  border-radius: 50%;
  margin-top: 6px;
}

.show-more {
  padding: 8px 16px;
  text-align: center;
  border-top: 1px solid #f0f0f0;
}

/* 滚动条样式 */
.notification-content::-webkit-scrollbar {
  width: 4px;
}

.notification-content::-webkit-scrollbar-track {
  background: #f1f1f1;
}

.notification-content::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 2px;
}

.notification-content::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .notification-content {
    max-height: 300px;
  }
  
  .notification-item {
    padding: 10px 12px;
  }
  
  .notification-message {
    font-size: 13px;
  }
}
</style>