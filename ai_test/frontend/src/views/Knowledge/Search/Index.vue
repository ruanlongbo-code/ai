<template>
  <div class="knowledge-search">
    <div class="page-header">
      <h2>知识检索</h2>
      <span class="subtitle">基于知识库进行智能检索，验证文档入库效果，辅助测试分析</span>
    </div>

    <!-- 对话区域 -->
    <div class="chat-container">
      <div class="chat-messages" ref="chatMessagesRef">
        <div v-if="messages.length === 0" class="empty-state">
          <el-icon :size="48" color="#c0c4cc"><Search /></el-icon>
          <p>输入问题，从知识库中检索相关信息</p>
          <div class="quick-actions">
            <el-tag
              v-for="q in quickQuestions"
              :key="q"
              class="quick-tag"
              @click="sendMessage(q)"
              effect="plain"
            >{{ q }}</el-tag>
          </div>
        </div>

        <div v-for="(msg, idx) in messages" :key="idx" :class="['message', msg.role]">
          <div class="message-avatar">
            <el-avatar :size="32" v-if="msg.role === 'user'">
              {{ userStore.user?.real_name?.charAt(0) || 'U' }}
            </el-avatar>
            <el-avatar :size="32" v-else style="background: #8b5cf6">AI</el-avatar>
          </div>
          <div class="message-content">
            <div class="message-text" v-html="renderMarkdown(msg.content)"></div>
          </div>
        </div>

        <div v-if="searching" class="message assistant">
          <div class="message-avatar">
            <el-avatar :size="32" style="background: #8b5cf6">AI</el-avatar>
          </div>
          <div class="message-content">
            <div class="message-text typing">
              <span class="dot"></span><span class="dot"></span><span class="dot"></span>
            </div>
          </div>
        </div>
      </div>

      <!-- 输入区域 -->
      <div class="chat-input">
        <el-input
          v-model="inputText"
          :placeholder="searching ? '正在检索中...' : '输入你的问题，例如：用户模块有哪些功能？'"
          :disabled="searching"
          @keyup.enter="sendMessage()"
          size="large"
        >
          <template #append>
            <el-button :icon="Promotion" :loading="searching" @click="sendMessage()" type="primary" />
          </template>
        </el-input>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted, computed } from 'vue'
import { Promotion } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useProjectStore, useUserStore } from '@/stores'
import { searchKnowledgeSync } from '@/api/knowledge'

const projectStore = useProjectStore()
const userStore = useUserStore()
const projectId = computed(() => projectStore.currentProject?.id)

const messages = ref([])
const inputText = ref('')
const searching = ref(false)
const chatMessagesRef = ref(null)
const conversationHistory = ref([])

const quickQuestions = [
  '这个项目有哪些核心模块？',
  '用户登录的业务流程是什么？',
  '有哪些需要重点测试的功能点？',
]

const renderMarkdown = (text) => {
  return text
    .replace(/\n/g, '<br>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/`(.*?)`/g, '<code>$1</code>')
}

const scrollToBottom = async () => {
  await nextTick()
  if (chatMessagesRef.value) {
    chatMessagesRef.value.scrollTop = chatMessagesRef.value.scrollHeight
  }
}

const sendMessage = async (text) => {
  const query = text || inputText.value.trim()
  if (!query || searching.value) return
  if (!projectId.value) {
    ElMessage.warning('请先选择项目')
    return
  }

  messages.value.push({ role: 'user', content: query })
  inputText.value = ''
  searching.value = true
  scrollToBottom()

  try {
    const res = await searchKnowledgeSync(projectId.value, {
      query,
      conversation_history: conversationHistory.value,
    })
    const answer = res.data.response || '未找到相关信息'
    messages.value.push({ role: 'assistant', content: answer })

    conversationHistory.value.push(
      { role: 'user', content: query },
      { role: 'assistant', content: answer }
    )
  } catch (e) {
    messages.value.push({ role: 'assistant', content: '检索失败，请检查知识库服务是否正常运行。' })
  } finally {
    searching.value = false
    scrollToBottom()
  }
}
</script>

<style scoped>
.knowledge-search {
  padding: 10px;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.page-header {
  margin-bottom: 16px;
}

.page-header h2 {
  margin: 0 0 4px 0;
  font-size: 20px;
}

.subtitle {
  color: #909399;
  font-size: 13px;
}

.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  border: 1px solid #e4e7ed;
  border-radius: 12px;
  overflow: hidden;
  min-height: 0;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: #fafafa;
}

.empty-state {
  text-align: center;
  padding: 60px 0;
  color: #909399;
}

.empty-state p {
  margin: 16px 0;
  font-size: 15px;
}

.quick-actions {
  display: flex;
  gap: 8px;
  justify-content: center;
  flex-wrap: wrap;
  margin-top: 12px;
}

.quick-tag {
  cursor: pointer;
  font-size: 13px;
}

.quick-tag:hover {
  color: #8b5cf6;
  border-color: #8b5cf6;
}

.message {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.message.user {
  flex-direction: row-reverse;
}

.message-content {
  max-width: 70%;
}

.message-text {
  padding: 12px 16px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.6;
  word-break: break-word;
}

.message.user .message-text {
  background: #8b5cf6;
  color: white;
  border-top-right-radius: 4px;
}

.message.assistant .message-text {
  background: white;
  border: 1px solid #e4e7ed;
  border-top-left-radius: 4px;
}

.message-text :deep(code) {
  background: rgba(0, 0, 0, 0.06);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 13px;
}

.typing {
  display: flex;
  gap: 4px;
  align-items: center;
  padding: 16px !important;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #c0c4cc;
  animation: typing 1.4s infinite ease-in-out;
}

.dot:nth-child(2) { animation-delay: 0.2s; }
.dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes typing {
  0%, 100% { opacity: 0.3; transform: scale(0.8); }
  50% { opacity: 1; transform: scale(1); }
}

.chat-input {
  padding: 16px;
  background: white;
  border-top: 1px solid #e4e7ed;
}
</style>
