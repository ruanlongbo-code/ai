<template>
  <div class="chat-container">
    <div class="chat-header" v-if="showHeader">
      <div class="header-content">
        <h3 class="chat-title">{{ title }}</h3>
        <div class="header-actions">
          <el-button
              size="small"
              text
              @click="clearMessages"
              :icon="Delete"
              :disabled="messages.length === 0"
          >
            清空对话
          </el-button>
          <el-button
              size="small"
              text
              @click="exportMessages"
              :icon="Download"
              :disabled="messages.length === 0"
          >
            导出对话
          </el-button>
        </div>
      </div>
    </div>

    <div
        ref="messagesContainer"
        class="messages-container"
        :class="{ 'with-header': showHeader }"
    >
      <div class="messages-list">
        <!-- 空状态 -->
        <div v-if="messages.length === 0" class="empty-state">
          <el-icon class="empty-icon">
            <ChatDotRound/>
          </el-icon>
          <p class="empty-text">{{ emptyText }}</p>
        </div>

        <!-- 消息列表 -->
        <ChatMessage
            v-for="message in messages"
            :key="message.id"
            :message="message"
            :show-actions="showMessageActions"
            :is-streaming="isStreamingMessage(message.id)"
            @copy="handleCopyMessage"
            @regenerate="handleRegenerateMessage"
        />

        <!-- 加载状态 -->
        <div v-if="isLoading && messages.length <1" class="loading-message">
          <ChatMessage
              :message="loadingMessage"
              :show-actions="false"
              :is-streaming="true"
          />
        </div>
      </div>
    </div>

    <!-- 滚动到底部按钮 -->
    <transition name="fade">
      <div
          v-if="showScrollButton"
          class="scroll-to-bottom"
          @click="scrollToBottom"
      >
        <el-button
            circle
            size="small"
            :icon="ArrowDown"
        />
      </div>
    </transition>
  </div>
</template>

<script setup>
import {ref, computed, nextTick, onMounted, onUnmounted, watch} from 'vue'
import {ElMessage, ElMessageBox} from 'element-plus'
import {
  Delete,
  Download,
  ChatDotRound,
  ArrowDown
} from '@element-plus/icons-vue'
import ChatMessage from './ChatMessage.vue'

// Props
const props = defineProps({
  messages: {
    type: Array,
    default: () => []
  },
  title: {
    type: String,
    default: 'AI 对话'
  },
  showHeader: {
    type: Boolean,
    default: true
  },
  showMessageActions: {
    type: Boolean,
    default: true
  },
  emptyText: {
    type: String,
    default: '开始您的对话吧...'
  },
  isLoading: {
    type: Boolean,
    default: false
  },
  streamingMessageId: {
    type: String,
    default: ''
  },
  autoScroll: {
    type: Boolean,
    default: true
  }
})

// Emits
const emit = defineEmits([
  'clear-messages',
  'export-messages',
  'copy-message',
  'regenerate-message'
])

// Refs
const messagesContainer = ref(null)
const showScrollButton = ref(false)

// 加载消息
const loadingMessage = computed(() => ({
  id: 'loading',
  type: 'assistant',
  content: '正在思考中...',
  timestamp: Date.now(),
  isMarkdown: false,
  isStreaming: true
}))

// 方法
const isStreamingMessage = (messageId) => {
  return props.streamingMessageId === messageId
}

const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const checkScrollPosition = () => {
  if (!messagesContainer.value) return

  const {scrollTop, scrollHeight, clientHeight} = messagesContainer.value
  const isNearBottom = scrollHeight - scrollTop - clientHeight < 100
  showScrollButton.value = !isNearBottom && props.messages.length > 0
}

const handleScroll = () => {
  checkScrollPosition()
}

const clearMessages = async () => {
  try {
    await ElMessageBox.confirm(
        '确定要清空所有对话记录吗？此操作不可恢复。',
        '确认清空',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }
    )
    emit('clear-messages')
    ElMessage.success('对话记录已清空')
  } catch {
    // 用户取消
  }
}

const exportMessages = () => {
  if (props.messages.length === 0) {
    ElMessage.warning('没有对话记录可导出')
    return
  }

  try {
    const exportData = {
      title: props.title,
      exportTime: new Date().toISOString(),
      messages: props.messages.map(msg => ({
        role: msg.type,
        content: msg.content,
        timestamp: msg.timestamp,
        time: new Date(msg.timestamp).toLocaleString('zh-CN')
      }))
    }

    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: 'application/json'
    })

    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `chat-export-${new Date().toISOString().slice(0, 10)}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)

    emit('export-messages', exportData)
    ElMessage.success('对话记录已导出')
  } catch (error) {
    ElMessage.error('导出失败')
    console.error('Export error:', error)
  }
}

const handleCopyMessage = (message) => {
  emit('copy-message', message)
}

const handleRegenerateMessage = (message) => {
  emit('regenerate-message', message)
}

// 监听消息变化，自动滚动到底部
watch(
    () => props.messages.length,
    async () => {
      if (props.autoScroll) {
        await nextTick()
        scrollToBottom()
      }
    }
)

// 深度监听消息内容变化（流式更新时消息内容变化但长度不变）
watch(
    () => props.messages.map(m => m.content?.length || 0).join(','),
    async () => {
      if (props.autoScroll && props.streamingMessageId) {
        await nextTick()
        scrollToBottom()
      }
    }
)

// 监听流式消息ID变化
watch(
    () => props.streamingMessageId,
    async (newVal) => {
      if (newVal && props.autoScroll) {
        await nextTick()
        scrollToBottom()
      }
    }
)

// 监听流式输出状态变化
watch(
    () => props.isLoading,
    async (newVal) => {
      if (newVal && props.autoScroll) {
        await nextTick()
        scrollToBottom()
      }
    }
)

// 生命周期
onMounted(() => {
  if (messagesContainer.value) {
    messagesContainer.value.addEventListener('scroll', handleScroll)
    checkScrollPosition()
  }

  // 初始滚动到底部
  if (props.autoScroll && props.messages.length > 0) {
    scrollToBottom()
  }
})

onUnmounted(() => {
  if (messagesContainer.value) {
    messagesContainer.value.removeEventListener('scroll', handleScroll)
  }
})

// 暴露方法给父组件
defineExpose({
  scrollToBottom,
  checkScrollPosition
})
</script>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  background-color: #ffffff;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  position: relative;

}

.chat-header {
  flex-shrink: 0;
  padding: 16px 20px;
  border-bottom: 1px solid #e4e7ed;
  /* background-color: #fafafa; */
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.chat-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  scroll-behavior: smooth;
}

.messages-container.with-header {
  height: calc(100% - 65px);
}

.messages-list {
  /* padding: 20px; */
  background-color: #fafafa;
  min-height: 100%;
  display: flex;
  flex-direction: column;
}

/* 空状态 */
.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #909399;
  text-align: center;
  padding: 40px 20px;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.6;
}

.empty-text {
  font-size: 14px;
  margin: 0;
}

/* 加载消息 */
.loading-message {
  margin-top: 16px;
}

/* 滚动到底部按钮 */
.scroll-to-bottom {
  position: absolute;
  bottom: 20px;
  right: 20px;
  z-index: 10;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 滚动条样式 */
.messages-container::-webkit-scrollbar {
  width: 6px;
}

.messages-container::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.messages-container::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.messages-container::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .chat-header {
    padding: 12px 16px;
  }

  .header-content {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }

  .header-actions {
    align-self: stretch;
    justify-content: flex-end;
  }

  .messages-list {
    padding: 16px;
  }

  .scroll-to-bottom {
    bottom: 16px;
    right: 16px;
  }
}

/* 深色模式支持 */
@media (prefers-color-scheme: dark) {
  .chat-container {
    background-color: #1a1a1a;
    color: #e4e7ed;
  }

  .chat-header {
    background-color: #2d2d2d;
    border-bottom-color: #4c4d4f;
  }

  .chat-title {
    color: #e4e7ed;
  }

  .empty-state {
    color: #909399;
  }
}
</style>