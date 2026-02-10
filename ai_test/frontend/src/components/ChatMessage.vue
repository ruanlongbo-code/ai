<template>
  <div class="chat-message" :class="messageClass">
    <div class="message-avatar">
      <div class="avatar-icon" :class="avatarClass">
        <el-icon v-if="message.type === 'user'">
          <User />
        </el-icon>
        <el-icon v-else-if="message.type === 'assistant'">
          <ChatDotRound />
        </el-icon>
        <el-icon v-else-if="message.type === 'system'">
          <Setting />
        </el-icon>
        <el-icon v-else>
          <InfoFilled />
        </el-icon>
      </div>
    </div>
    
    <div class="message-content">
      <div class="message-header">
        <span class="message-role">{{ getRoleLabel(message.type) }}</span>
        <span class="message-time">{{ formatTime(message.timestamp) }}</span>
      </div>
      
      <div class="message-body">
        <div 
          v-if="message.isMarkdown" 
          class="markdown-content"
          v-html="renderedContent"
        ></div>
        <div v-else class="text-content">
          {{ message.content }}
        </div>
        
        
        <!-- 流式输出时的打字机效果 -->
        <div v-if="isStreaming" class="typing-indicator">
          <span class="typing-dot"></span>
          <span class="typing-dot"></span>
          <span class="typing-dot"></span>
        </div>
      </div>
      
      <!-- 消息操作按钮 -->
      <div v-if="showActions" class="message-actions">
        <el-button 
          size="small" 
          text 
          @click="copyMessage"
          :icon="DocumentCopy"
        >
          复制
        </el-button>
        <el-button 
          v-if="message.type === 'assistant'" 
          size="small" 
          text 
          @click="regenerateMessage"
          :icon="Refresh"
        >
          重新生成
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  User, 
  ChatDotRound, 
  Setting, 
  InfoFilled, 
  DocumentCopy, 
  Refresh 
} from '@element-plus/icons-vue'
import { renderMarkdown } from '@/utils/markdown'

// Props
const props = defineProps({
  message: {
    type: Object,
    required: true,
    default: () => ({
      id: '',
      type: 'assistant', // user, assistant, system, info
      content: '',
      timestamp: Date.now(),
      isMarkdown: true,
      isStreaming: false
    })
  },
  showActions: {
    type: Boolean,
    default: true
  },
  isStreaming: {
    type: Boolean,
    default: false
  }
})

// Emits
const emit = defineEmits(['copy', 'regenerate'])

// 计算属性
const messageClass = computed(() => ({
  'message-user': props.message.type === 'user',
  'message-assistant': props.message.type === 'assistant',
  'message-system': props.message.type === 'system',
  'message-streaming': props.isStreaming
}))

const avatarClass = computed(() => ({
  'avatar-user': props.message.type === 'user',
  'avatar-assistant': props.message.type === 'assistant',
  'avatar-system': props.message.type === 'system'
}))

const renderedContent = computed(() => {
  if (!props.message.isMarkdown) {
    return props.message.content
  }
  return renderMarkdown(props.message.content)
})

// 方法
const getRoleLabel = (type) => {
  const labels = {
    user: '用户',
    progress: 'AI助手',
    system: '系统',
    info: '信息'
  }
  return labels[type] || 'AI助手'
}

const formatTime = (timestamp) => {
  return new Date(timestamp).toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

const copyMessage = async () => {
  try {
    await navigator.clipboard.writeText(props.message.content)
    ElMessage.success('已复制到剪贴板')
    emit('copy', props.message)
  } catch (error) {
    ElMessage.error('复制失败')
  }
}

const regenerateMessage = () => {
  emit('regenerate', props.message)
}
</script>

<style scoped>
.chat-message {
  display: flex;
  gap: 12px;
  padding: 16px 0;
  border-bottom: 1px solid #f0f0f0;
  transition: background-color 0.2s;

}

.chat-message:hover {
  background-color: #fafafa;
}

.chat-message:last-child {
  border-bottom: none;
}

.message-avatar {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
}

.avatar-icon {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  color: white;
}

.avatar-user {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.avatar-assistant {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.avatar-system {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.message-content {
  flex: 1;
  min-width: 0;
}

.message-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.message-role {
  font-weight: 600;
  font-size: 14px;
  color: #303133;
}

.message-time {
  font-size: 12px;
  color: #909399;
}

.message-body {
  position: relative;
}

.text-content {
  line-height: 1.6;
  color: #303133;
  font-size: 14px;
  white-space: pre-wrap;
  word-break: break-word;
}

.markdown-content {
  line-height: 1.6;
  color: #303133;
  font-size: 14px;
}

/* Markdown样式 */
.markdown-content :deep(h1),
.markdown-content :deep(h2),
.markdown-content :deep(h3),
.markdown-content :deep(h4),
.markdown-content :deep(h5),
.markdown-content :deep(h6) {
  margin: 16px 0 8px 0;
  font-weight: 600;
  line-height: 1.4;
}

.markdown-content :deep(h1) { font-size: 24px; }
.markdown-content :deep(h2) { font-size: 20px; }
.markdown-content :deep(h3) { font-size: 18px; }
.markdown-content :deep(h4) { font-size: 16px; }
.markdown-content :deep(h5) { font-size: 14px; }
.markdown-content :deep(h6) { font-size: 12px; }

.markdown-content :deep(p) {
  margin: 8px 0;
}

.markdown-content :deep(ul),
.markdown-content :deep(ol) {
  margin: 8px 0;
  padding-left: 24px;
}

.markdown-content :deep(li) {
  margin: 4px 0;
}

.markdown-content :deep(blockquote) {
  margin: 16px 0;
  padding: 8px 16px;
  border-left: 4px solid #e4e7ed;
  background-color: #f8f9fa;
  color: #606266;
}

.markdown-content :deep(code) {
  padding: 2px 4px;
  background-color: #f1f2f6;
  border-radius: 3px;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  color: #e83e8c;
}

.markdown-content :deep(pre) {
  margin: 16px 0;
  padding: 16px;
  background-color: #f8f9fa;
  border-radius: 6px;
  overflow-x: auto;
  border: 1px solid #e4e7ed;
}

.markdown-content :deep(pre code) {
  padding: 0;
  background: none;
  color: inherit;
  font-size: 13px;
  line-height: 1.5;
}

.markdown-content :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 16px 0;
}

.markdown-content :deep(th),
.markdown-content :deep(td) {
  padding: 8px 12px;
  border: 1px solid #e4e7ed;
  text-align: left;
}

.markdown-content :deep(th) {
  background-color: #f8f9fa;
  font-weight: 600;
}

.markdown-content :deep(a) {
  color: #409eff;
  text-decoration: none;
}

.markdown-content :deep(a:hover) {
  text-decoration: underline;
}

/* 打字机效果 */
.typing-indicator {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  margin-left: 8px;
}

.typing-dot {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background-color: #909399;
  animation: typing 1.4s infinite ease-in-out;
}

.typing-dot:nth-child(1) { animation-delay: -0.32s; }
.typing-dot:nth-child(2) { animation-delay: -0.16s; }

@keyframes typing {
  0%, 80%, 100% {
    transform: scale(0);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

/* 消息操作 */
.message-actions {
  margin-top: 8px;
  display: flex;
  gap: 8px;
  opacity: 0;
  transition: opacity 0.2s;
}

.chat-message:hover .message-actions {
  opacity: 1;
}

/* 流式输出动画 */
.message-streaming .message-body {
  position: relative;
}

.message-streaming .message-body::after {
  content: '';
  display: inline-block;
  width: 2px;
  height: 1.2em;
  background-color: #409eff;
  margin-left: 2px;
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .chat-message {
    padding: 12px 0;
    gap: 8px;
  }
  
  .message-avatar {
    width: 28px;
    height: 28px;
  }
  
  .avatar-icon {
    width: 28px;
    height: 28px;
    font-size: 14px;
  }
  
  .message-role {
    font-size: 13px;
  }
  
  .text-content,
  .markdown-content {
    font-size: 13px;
  }
}
</style>