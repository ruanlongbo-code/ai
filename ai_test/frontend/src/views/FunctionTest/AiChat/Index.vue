<template>
  <div class="ai-chat-page">
    <!-- 左栏：对话历史 -->
    <aside class="sidebar-panel" :class="{ collapsed: sidebarCollapsed }">
      <div class="sidebar-top">
        <div v-if="!sidebarCollapsed" class="sidebar-title">
          <el-icon><ChatDotRound /></el-icon>
          <span>对话列表</span>
        </div>
        <el-button
          text
          size="small"
          @click="sidebarCollapsed = !sidebarCollapsed"
          :title="sidebarCollapsed ? '展开' : '收起'"
        >
          <el-icon><ArrowLeft v-if="!sidebarCollapsed" /><ArrowRight v-else /></el-icon>
        </el-button>
      </div>

      <template v-if="!sidebarCollapsed">
        <div class="new-chat-btn-wrap">
          <el-button type="primary" class="new-chat-btn" @click="handleNewChat">
            <el-icon><Plus /></el-icon> 新建对话
          </el-button>
        </div>

        <el-input
          v-model="searchKeyword"
          placeholder="搜索对话..."
          size="small"
          clearable
          :prefix-icon="Search"
          class="session-search"
        />

        <div class="session-list" v-loading="loadingSessions">
          <div
            v-for="session in filteredSessions"
            :key="session.id"
            class="session-item"
            :class="{ active: currentSessionId === session.id }"
            @click="switchSession(session)"
          >
            <div class="session-item-content">
              <el-icon class="session-icon"><ChatLineSquare /></el-icon>
              <div class="session-info">
                <span
                  v-if="renamingId !== session.id"
                  class="session-name"
                  :title="session.title"
                >{{ session.title || '新对话' }}</span>
                <el-input
                  v-else
                  v-model="renameText"
                  size="small"
                  @blur="confirmRename(session)"
                  @keyup.enter="confirmRename(session)"
                  autofocus
                  class="rename-input"
                />
                <span class="session-time">{{ formatSessionTime(session.updated_at || session.created_at) }}</span>
              </div>
            </div>
            <el-dropdown
              trigger="click"
              @command="(cmd) => handleSessionAction(cmd, session)"
              @click.stop
            >
              <el-button text size="small" class="session-more" @click.stop>
                <el-icon><MoreFilled /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="rename"><el-icon><Edit /></el-icon> 重命名</el-dropdown-item>
                  <el-dropdown-item command="delete" divided><el-icon><Delete /></el-icon> 删除</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
          <el-empty v-if="!loadingSessions && filteredSessions.length === 0" description="暂无对话" :image-size="48" />
        </div>
      </template>
    </aside>

    <!-- 中栏：对话区域 -->
    <main class="chat-panel">
      <div class="chat-topbar">
        <div class="chat-topbar-left">
          <h3 class="chat-session-title">{{ currentSession?.title || 'AI 测试用例助手' }}</h3>
          <el-tag v-if="currentSession" size="small" type="info" effect="plain">
            {{ messages.length }} 条消息
          </el-tag>
        </div>
        <div class="chat-topbar-right">
          <el-tooltip content="切换预览面板">
            <el-button text @click="previewCollapsed = !previewCollapsed">
              <el-icon><Setting /></el-icon>
            </el-button>
          </el-tooltip>
          <el-tooltip content="清空对话">
            <el-button text :disabled="messages.length === 0" @click="handleClearChat">
              <el-icon><Delete /></el-icon>
            </el-button>
          </el-tooltip>
        </div>
      </div>

      <div ref="chatBodyRef" class="chat-body">
        <!-- 欢迎页 -->
        <div v-if="messages.length === 0 && !isStreaming" class="welcome-area">
          <div class="welcome-icon-wrap">
            <el-icon :size="48" style="color: #8b5cf6;"><Aim /></el-icon>
          </div>
          <h2 class="welcome-title">AI 测试用例助手</h2>
          <p class="welcome-desc">上传需求文档或描述需求，AI 将为你智能生成测试用例</p>
          <div class="quick-actions">
            <div class="quick-card" @click="sendQuickMessage('帮我分析以下需求文档，提取关键测试点')">
              <el-icon><Document /></el-icon>
              <span>分析需求文档</span>
            </div>
            <div class="quick-card" @click="sendQuickMessage('根据以下功能描述，生成完整的测试用例（包含正向、反向、边界场景）')">
              <el-icon><MagicStick /></el-icon>
              <span>生成测试用例</span>
            </div>
            <div class="quick-card" @click="sendQuickMessage('请帮我审查以下测试用例，给出优化建议和遗漏的场景')">
              <el-icon><Checked /></el-icon>
              <span>审查测试用例</span>
            </div>
            <div class="quick-card" @click="sendQuickMessage('将以下功能需求转化为 XMind 脑图结构的测试用例')">
              <el-icon><Share /></el-icon>
              <span>生成脑图用例</span>
            </div>
          </div>
        </div>

        <!-- 消息列表 -->
        <div v-else class="messages-list">
          <div
            v-for="(msg, idx) in messages"
            :key="msg.id || idx"
            class="message-row"
            :class="{ 'msg-user': msg.role === 'user', 'msg-assistant': msg.role === 'assistant' }"
          >
            <div class="msg-avatar">
              <div v-if="msg.role === 'user'" class="avatar avatar-user">
                <el-icon><User /></el-icon>
              </div>
              <div v-else class="avatar avatar-ai">
                <el-icon><Aim /></el-icon>
              </div>
            </div>
            <div class="msg-body">
              <div class="msg-header">
                <span class="msg-role">{{ msg.role === 'user' ? '我' : 'AI 助手' }}</span>
                <span class="msg-time">{{ formatMsgTime(msg.created_at) }}</span>
              </div>
              <div class="msg-content">
                <div
                  v-if="msg.role === 'assistant'"
                  class="markdown-body"
                  v-html="renderMd(msg.content)"
                />
                <div v-else class="user-text">{{ msg.content }}</div>
                <div v-if="msg.files && msg.files.length" class="msg-files">
                  <div v-for="(f, fi) in msg.files" :key="fi" class="msg-file-tag">
                    <el-icon><Document /></el-icon> {{ f.name }}
                  </div>
                </div>
              </div>
              <div class="msg-actions" v-if="msg.role === 'assistant' && !isStreaming">
                <el-button text size="small" @click="copyText(msg.content)">
                  <el-icon><DocumentCopy /></el-icon> 复制
                </el-button>
                <el-button
                  v-if="hasTestCases(msg.content)"
                  text
                  size="small"
                  type="primary"
                  @click="extractAndPreview(msg.content)"
                >
                  <el-icon><View /></el-icon> 预览用例
                </el-button>
              </div>
            </div>
          </div>

          <!-- 流式输出打字指示 -->
          <div v-if="isStreaming" class="typing-bar">
            <span class="typing-dot" /><span class="typing-dot" /><span class="typing-dot" />
            <span class="typing-label">AI 正在回复...</span>
          </div>
        </div>
      </div>

      <!-- 输入区域 -->
      <div class="chat-input-area">
        <div v-if="attachedFiles.length" class="attached-files-bar">
          <div v-for="(f, idx) in attachedFiles" :key="idx" class="attached-file">
            <el-icon><Document /></el-icon>
            <span>{{ f.name }}</span>
            <el-icon class="remove-file" @click="attachedFiles.splice(idx, 1)"><Close /></el-icon>
          </div>
        </div>
        <div class="input-row">
          <el-tooltip content="上传文件">
            <el-upload
              ref="uploadRef"
              :auto-upload="false"
              :show-file-list="false"
              :on-change="handleAttachFile"
              accept=".md,.txt,.pdf,.docx,.doc,.png,.jpg,.jpeg,.gif,.webp"
              multiple
            >
              <el-button text class="attach-btn">
                <el-icon :size="18"><Paperclip /></el-icon>
              </el-button>
            </el-upload>
          </el-tooltip>
          <el-input
            ref="inputRef"
            v-model="inputText"
            type="textarea"
            :autosize="{ minRows: 1, maxRows: 6 }"
            placeholder="输入需求描述、粘贴 PRD 内容，或上传文件让 AI 分析..."
            @keydown.enter.exact="handleSend"
            @keydown.shift.enter.exact="() => {}"
            class="chat-textarea"
            resize="none"
          />
          <el-button
            type="primary"
            :disabled="!canSend"
            :loading="isStreaming"
            @click="handleSend"
            class="send-btn"
          >
            <el-icon v-if="!isStreaming"><Promotion /></el-icon>
            <el-icon v-else><Loading /></el-icon>
          </el-button>
        </div>
        <div class="input-hint">
          <span>Enter 发送，Shift+Enter 换行</span>
          <span v-if="isStreaming" class="stop-link" @click="handleStopStream">停止生成</span>
        </div>
      </div>
    </main>

    <!-- 右栏：用例预览与操作 -->
    <aside class="preview-panel" :class="{ collapsed: previewCollapsed }">
      <div class="preview-top">
        <div v-if="!previewCollapsed" class="preview-title">
          <el-icon><List /></el-icon>
          <span>用例预览</span>
        </div>
        <el-button text size="small" @click="previewCollapsed = !previewCollapsed">
          <el-icon><ArrowRight v-if="!previewCollapsed" /><ArrowLeft v-else /></el-icon>
        </el-button>
      </div>

      <template v-if="!previewCollapsed">
        <div v-if="!previewCases.length" class="preview-empty">
          <el-icon :size="36" style="color: #c0c4cc;"><Notebook /></el-icon>
          <p>AI 生成的测试用例将在这里实时预览</p>
          <p class="preview-hint">在对话中让 AI 生成用例后，点击消息中的「预览用例」按钮</p>
        </div>

        <div v-else class="preview-content">
          <div class="preview-toolbar">
            <el-tag type="success" effect="dark" size="small">{{ previewCases.length }} 条用例</el-tag>
            <div class="preview-toolbar-actions">
              <el-button size="small" @click="exportPreviewCases">
                <el-icon><Download /></el-icon> 导出
              </el-button>
              <el-button size="small" type="primary" @click="handleImportFeishu">
                <el-icon><Upload /></el-icon> 导入飞书
              </el-button>
            </div>
          </div>

          <div class="preview-cases-list">
            <div
              v-for="(tc, idx) in previewCases"
              :key="idx"
              class="preview-case-card"
              :class="{ expanded: expandedCaseIdx === idx }"
            >
              <div class="case-card-header" @click="expandedCaseIdx = expandedCaseIdx === idx ? -1 : idx">
                <div class="case-card-left">
                  <el-tag :type="priorityTagType(tc.priority)" size="small" effect="plain">{{ tc.priority || 'P2' }}</el-tag>
                  <span class="case-card-title">{{ tc.case_title || tc.name }}</span>
                </div>
                <el-icon class="expand-icon" :class="{ rotated: expandedCaseIdx === idx }"><ArrowRight /></el-icon>
              </div>
              <el-collapse-transition>
                <div v-show="expandedCaseIdx === idx" class="case-card-body">
                  <div v-if="tc.module" class="case-field">
                    <label>所属模块</label>
                    <span>{{ tc.module }}</span>
                  </div>
                  <div v-if="tc.precondition" class="case-field">
                    <label>前置条件</label>
                    <span>{{ tc.precondition }}</span>
                  </div>
                  <div v-if="tc.test_steps && tc.test_steps.length" class="case-field">
                    <label>测试步骤</label>
                    <ol class="case-steps">
                      <li v-for="(s, si) in tc.test_steps" :key="si">{{ s }}</li>
                    </ol>
                  </div>
                  <div v-if="tc.expected_results && tc.expected_results.length" class="case-field">
                    <label>预期结果</label>
                    <ol class="case-steps">
                      <li v-for="(e, ei) in tc.expected_results" :key="ei">{{ e }}</li>
                    </ol>
                  </div>
                </div>
              </el-collapse-transition>
            </div>
          </div>
        </div>
      </template>
    </aside>

    <!-- 飞书导入弹窗 -->
    <el-dialog v-model="feishuDialogVisible" title="导入飞书用例集" width="500px" :close-on-click-modal="false">
      <el-form label-position="top">
        <el-form-item label="飞书 x-token" required>
          <el-input v-model="feishuToken" type="textarea" :rows="2" placeholder="粘贴飞书 x-token..." />
        </el-form-item>
        <el-form-item label="用例集标题（可选）">
          <el-input v-model="feishuTitle" placeholder="不填则自动命名" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="feishuDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="importingFeishu" @click="confirmImportFeishu">开始导入</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onActivated, nextTick, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ChatDotRound, ChatLineSquare, ArrowLeft, ArrowRight, Plus, Search,
  MoreFilled, Edit, Delete, Setting, User, Aim, Document, MagicStick,
  Checked, Share, DocumentCopy, View, Promotion, Loading, Paperclip,
  Close, List, Notebook, Download, Upload, ArrowDown,
} from '@element-plus/icons-vue'
import { useProjectStore } from '@/stores'
import { renderMarkdown } from '@/utils/markdown'
import { importCasesToFeishu } from '@/api/functional_test'

const projectStore = useProjectStore()
const projectId = computed(() => projectStore.currentProject?.id)

const sidebarCollapsed = ref(false)
const previewCollapsed = ref(false)
const searchKeyword = ref('')
const loadingSessions = ref(false)
const sessions = ref([])
const currentSessionId = ref(null)
const renamingId = ref(null)
const renameText = ref('')

const messages = ref([])
const inputText = ref('')
const attachedFiles = ref([])
const isStreaming = ref(false)
let abortController = null

const chatBodyRef = ref(null)
const inputRef = ref(null)
const uploadRef = ref(null)

const previewCases = ref([])
const expandedCaseIdx = ref(-1)

const feishuDialogVisible = ref(false)
const feishuToken = ref(localStorage.getItem('feishu_x_token') || '')
const feishuTitle = ref('')
const importingFeishu = ref(false)

const currentSession = computed(() => sessions.value.find(s => s.id === currentSessionId.value))
const filteredSessions = computed(() => {
  if (!searchKeyword.value.trim()) return sessions.value
  const kw = searchKeyword.value.trim().toLowerCase()
  return sessions.value.filter(s => (s.title || '').toLowerCase().includes(kw))
})
const canSend = computed(() => {
  return (inputText.value.trim().length > 0 || attachedFiles.value.length > 0) && !isStreaming.value
})

const renderMd = (content) => {
  try {
    return renderMarkdown(content || '')
  } catch {
    return content || ''
  }
}

const formatSessionTime = (t) => {
  if (!t) return ''
  const d = new Date(t)
  const now = new Date()
  const diffDays = Math.floor((now - d) / 86400000)
  if (diffDays === 0) return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
  if (diffDays === 1) return '昨天'
  if (diffDays < 7) return `${diffDays}天前`
  return `${d.getMonth() + 1}/${d.getDate()}`
}

const formatMsgTime = (t) => {
  if (!t) return ''
  return new Date(t).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

const priorityTagType = (p) => {
  if (!p) return 'info'
  const s = String(p).toUpperCase()
  if (s === 'P0') return 'danger'
  if (s === 'P1') return 'warning'
  if (s === 'P2') return ''
  return 'info'
}

const scrollToBottom = () => {
  nextTick(() => {
    if (chatBodyRef.value) chatBodyRef.value.scrollTop = chatBodyRef.value.scrollHeight
  })
}

const loadSessions = async () => {
  if (!projectId.value) return
  loadingSessions.value = true
  try {
    const stored = JSON.parse(localStorage.getItem(`ai_chat_sessions_${projectId.value}`) || '[]')
    sessions.value = stored.sort((a, b) => new Date(b.updated_at || b.created_at) - new Date(a.updated_at || a.created_at))
  } catch {
    sessions.value = []
  } finally {
    loadingSessions.value = false
  }
}

const saveSessions = () => {
  if (!projectId.value) return
  localStorage.setItem(`ai_chat_sessions_${projectId.value}`, JSON.stringify(sessions.value))
}

const saveMessages = () => {
  if (!projectId.value || !currentSessionId.value) return
  localStorage.setItem(`ai_chat_msgs_${projectId.value}_${currentSessionId.value}`, JSON.stringify(messages.value))
}

const loadMessages = (sessionId) => {
  if (!projectId.value || !sessionId) { messages.value = []; return }
  try {
    messages.value = JSON.parse(localStorage.getItem(`ai_chat_msgs_${projectId.value}_${sessionId}`) || '[]')
  } catch {
    messages.value = []
  }
  nextTick(scrollToBottom)
}

const handleNewChat = () => {
  const id = `session_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
  const newSession = {
    id,
    title: '新对话',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  }
  sessions.value.unshift(newSession)
  saveSessions()
  switchSession(newSession)
}

const switchSession = (session) => {
  currentSessionId.value = session.id
  loadMessages(session.id)
  previewCases.value = []
  expandedCaseIdx.value = -1
}

const handleSessionAction = async (cmd, session) => {
  if (cmd === 'rename') {
    renamingId.value = session.id
    renameText.value = session.title || ''
  } else if (cmd === 'delete') {
    try {
      await ElMessageBox.confirm('确定删除该对话？', '确认', { type: 'warning' })
      const idx = sessions.value.findIndex(s => s.id === session.id)
      if (idx >= 0) sessions.value.splice(idx, 1)
      localStorage.removeItem(`ai_chat_msgs_${projectId.value}_${session.id}`)
      saveSessions()
      if (currentSessionId.value === session.id) {
        currentSessionId.value = sessions.value[0]?.id || null
        loadMessages(currentSessionId.value)
      }
      ElMessage.success('已删除')
    } catch { /* cancelled */ }
  }
}

const confirmRename = (session) => {
  if (renameText.value.trim()) {
    session.title = renameText.value.trim()
    session.updated_at = new Date().toISOString()
    saveSessions()
  }
  renamingId.value = null
}

const handleAttachFile = (file) => {
  const raw = file.raw || file
  attachedFiles.value.push(raw)
}

const sendQuickMessage = (text) => {
  inputText.value = text
  nextTick(() => inputRef.value?.focus?.())
}

const handleSend = (e) => {
  if (e && e.shiftKey) return
  if (e) e.preventDefault?.()
  if (!canSend.value) return

  if (!currentSessionId.value) handleNewChat()

  const userMsg = {
    id: `msg_${Date.now()}`,
    role: 'user',
    content: inputText.value.trim(),
    files: attachedFiles.value.map(f => ({ name: f.name, size: f.size })),
    created_at: new Date().toISOString(),
  }
  messages.value.push(userMsg)

  if (messages.value.length <= 2 && currentSession.value) {
    const title = userMsg.content.slice(0, 30) + (userMsg.content.length > 30 ? '...' : '')
    currentSession.value.title = title
    currentSession.value.updated_at = new Date().toISOString()
    saveSessions()
  }

  const sentText = inputText.value.trim()
  const sentFiles = [...attachedFiles.value]
  inputText.value = ''
  attachedFiles.value = []
  scrollToBottom()

  doStreamChat(sentText, sentFiles)
}

const doStreamChat = async (text, files) => {
  isStreaming.value = true
  abortController = new AbortController()

  const aiMsg = {
    id: `msg_${Date.now()}_ai`,
    role: 'assistant',
    content: '',
    created_at: new Date().toISOString(),
  }
  messages.value.push(aiMsg)
  scrollToBottom()

  try {
    const baseURL = import.meta.env.VITE_API_BASE_URL || '/api'
    const token = localStorage.getItem('token')

    let response
    if (files.length > 0) {
      const formData = new FormData()
      formData.append('message', text)
      for (const f of files) formData.append('files', f)
      const context = messages.value
        .filter(m => m.id !== aiMsg.id)
        .slice(-10)
        .map(m => ({ role: m.role, content: m.content }))
      formData.append('context', JSON.stringify(context))

      response = await fetch(`${baseURL}/functional_test/${projectId.value}/ai_chat/send_with_files_stream`, {
        method: 'POST',
        headers: { ...(token ? { 'Authorization': `Bearer ${token}` } : {}) },
        body: formData,
        signal: abortController.signal,
      })
    } else {
      const context = messages.value
        .filter(m => m.id !== aiMsg.id)
        .slice(-10)
        .map(m => ({ role: m.role, content: m.content }))

      response = await fetch(`${baseURL}/functional_test/${projectId.value}/ai_chat/send_stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ message: text, context }),
        signal: abortController.signal,
      })
    }

    if (!response.ok) {
      const err = await response.json().catch(() => ({}))
      throw new Error(err.detail || `HTTP ${response.status}`)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { value, done } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''
      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        const dataStr = line.slice(6).trim()
        if (!dataStr || dataStr === '[DONE]') continue
        try {
          const data = JSON.parse(dataStr)
          if (data.type === 'chunk' || data.type === 'content') {
            aiMsg.content += data.content || data.text || ''
            scrollToBottom()
          } else if (data.type === 'error') {
            throw new Error(data.message || 'AI 生成失败')
          }
        } catch (e) {
          if (e.message && !e.message.includes('JSON')) throw e
          aiMsg.content += dataStr
          scrollToBottom()
        }
      }
    }

    if (!aiMsg.content) aiMsg.content = '（AI 未返回内容，请重试）'
  } catch (err) {
    if (err.name === 'AbortError') {
      aiMsg.content += '\n\n*[已停止生成]*'
    } else {
      aiMsg.content = `生成失败: ${err.message}`
      ElMessage.error(err.message || '请求失败')
    }
  } finally {
    isStreaming.value = false
    abortController = null
    saveMessages()
    if (currentSession.value) {
      currentSession.value.updated_at = new Date().toISOString()
      saveSessions()
    }
  }
}

const handleStopStream = () => {
  if (abortController) abortController.abort()
}

const handleClearChat = async () => {
  try {
    await ElMessageBox.confirm('确定清空当前对话记录？', '确认', { type: 'warning' })
    messages.value = []
    saveMessages()
    previewCases.value = []
    ElMessage.success('已清空')
  } catch { /* cancelled */ }
}

const copyText = async (text) => {
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success('已复制')
  } catch {
    ElMessage.error('复制失败')
  }
}

const hasTestCases = (content) => {
  if (!content) return false
  return /(?:测试用例|test\s*case|用例名称|case_title|测试步骤|预期结果)/i.test(content)
}

const extractAndPreview = (content) => {
  const cases = []
  const sections = content.split(/^(?=###\s)/m)
  for (const section of sections) {
    const titleMatch = section.match(/^###\s*(.+)/m)
    if (!titleMatch) continue

    const title = titleMatch[1].replace(/\*+/g, '').trim()
    const preMatch = section.match(/(?:前置条件|precondition)[：:]\s*(.+)/i)
    const stepsMatch = section.match(/(?:测试步骤|steps?)[：:]\s*([\s\S]*?)(?=(?:预期结果|expected)|$)/i)
    const expectedMatch = section.match(/(?:预期结果|expected)[：:]\s*([\s\S]*?)(?=(?:---|###)|$)/i)
    const priorityMatch = section.match(/(?:优先级|priority)[：:]\s*(P\d)/i)
    const moduleMatch = section.match(/(?:模块|module|分类)[：:]\s*(.+)/i)

    const parseSteps = (raw) => {
      if (!raw) return []
      return raw.split(/\n/).map(l => l.replace(/^\d+[\.\)、]\s*/, '').trim()).filter(Boolean)
    }

    cases.push({
      case_title: title,
      module: moduleMatch ? moduleMatch[1].trim() : '',
      priority: priorityMatch ? priorityMatch[1] : 'P2',
      precondition: preMatch ? preMatch[1].trim() : '',
      test_steps: parseSteps(stepsMatch?.[1]),
      expected_results: parseSteps(expectedMatch?.[1]),
    })
  }

  if (cases.length === 0) {
    const lines = content.split('\n')
    for (const line of lines) {
      const m = line.match(/^[-*]\s*(.+)/)
      if (m && /(?:验证|测试|检查|确认|校验)/.test(m[1])) {
        cases.push({
          case_title: m[1].trim(),
          module: '',
          priority: 'P2',
          precondition: '',
          test_steps: [m[1].trim()],
          expected_results: ['验证通过'],
        })
      }
    }
  }

  if (cases.length > 0) {
    previewCases.value = cases
    previewCollapsed.value = false
    expandedCaseIdx.value = 0
    ElMessage.success(`已提取 ${cases.length} 条用例`)
  } else {
    ElMessage.warning('未能从 AI 回复中提取到结构化用例，请让 AI 使用更规范的格式生成')
  }
}

const exportPreviewCases = () => {
  if (!previewCases.value.length) return
  const blob = new Blob([JSON.stringify(previewCases.value, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `testcases_${new Date().toISOString().slice(0, 10)}.json`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
  ElMessage.success('已导出')
}

const handleImportFeishu = () => {
  feishuToken.value = localStorage.getItem('feishu_x_token') || ''
  feishuTitle.value = currentSession.value?.title || ''
  feishuDialogVisible.value = true
}

const confirmImportFeishu = async () => {
  if (!feishuToken.value.trim()) {
    ElMessage.warning('请输入飞书 x-token')
    return
  }
  if (!projectId.value) {
    ElMessage.warning('请先选择项目')
    return
  }
  importingFeishu.value = true
  try {
    localStorage.setItem('feishu_x_token', feishuToken.value.trim())
    const res = await importCasesToFeishu(projectId.value, {
      cases: previewCases.value,
      title: feishuTitle.value.trim() || undefined,
      feishu_token: feishuToken.value.trim(),
    })
    ElMessage.success(`导入成功！共 ${res.data?.case_count || previewCases.value.length} 条用例`)
    feishuDialogVisible.value = false
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || e.message || '导入失败')
  } finally {
    importingFeishu.value = false
  }
}

const initPage = () => {
  loadSessions()
  if (sessions.value.length > 0 && !currentSessionId.value) {
    switchSession(sessions.value[0])
  }
}

watch(projectId, () => {
  currentSessionId.value = null
  messages.value = []
  previewCases.value = []
  initPage()
})

onMounted(initPage)
onActivated(initPage)
</script>

<style scoped>
.ai-chat-page {
  display: flex;
  height: 100%;
  background: #f0f2f5;
  border-radius: 8px;
  overflow: hidden;
}

/* ===== 左栏：对话列表 ===== */
.sidebar-panel {
  width: 280px;
  min-width: 280px;
  background: #1e1e2e;
  color: #cdd6f4;
  display: flex;
  flex-direction: column;
  transition: all 0.3s ease;
  border-right: 1px solid rgba(139, 92, 246, 0.15);
}
.sidebar-panel.collapsed {
  width: 48px;
  min-width: 48px;
}
.sidebar-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}
.sidebar-top .el-button { color: #a6adc8; }
.sidebar-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 600;
  color: #cdd6f4;
}
.new-chat-btn-wrap { padding: 8px 12px; }
.new-chat-btn {
  width: 100%;
  background: linear-gradient(135deg, #8b5cf6, #7c3aed) !important;
  border: none !important;
  font-weight: 600;
}
.session-search { padding: 0 12px 8px; }
.session-search :deep(.el-input__wrapper) {
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.08);
  box-shadow: none;
}
.session-search :deep(.el-input__inner) { color: #cdd6f4; }
.session-search :deep(.el-input__inner)::placeholder { color: #6c7086; }

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 4px 8px;
}
.session-list::-webkit-scrollbar { width: 4px; }
.session-list::-webkit-scrollbar-thumb { background: rgba(139,92,246,0.25); border-radius: 3px; }

.session-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 10px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: 2px;
}
.session-item:hover { background: rgba(139,92,246,0.12); }
.session-item.active {
  background: rgba(139,92,246,0.22);
  border-left: 3px solid #8b5cf6;
}
.session-item-content {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}
.session-icon { color: #8b5cf6; font-size: 16px; flex-shrink: 0; }
.session-info { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px; }
.session-name {
  font-size: 13px;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #cdd6f4;
}
.session-time { font-size: 11px; color: #6c7086; }
.session-more { color: #6c7086; opacity: 0; transition: opacity 0.2s; }
.session-item:hover .session-more { opacity: 1; }
.rename-input :deep(.el-input__wrapper) {
  background: rgba(255,255,255,0.1);
  box-shadow: none;
}
.rename-input :deep(.el-input__inner) { color: #cdd6f4; font-size: 13px; }

/* ===== 中栏：对话区 ===== */
.chat-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  background: #fff;
}
.chat-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  border-bottom: 1px solid #f0f0f0;
  background: #fafbfc;
}
.chat-topbar-left { display: flex; align-items: center; gap: 10px; }
.chat-session-title { margin: 0; font-size: 15px; font-weight: 600; color: #1f2937; }
.chat-topbar-right { display: flex; gap: 4px; }

.chat-body {
  flex: 1;
  overflow-y: auto;
  padding: 0;
}
.chat-body::-webkit-scrollbar { width: 6px; }
.chat-body::-webkit-scrollbar-thumb { background: rgba(139,92,246,0.2); border-radius: 3px; }

/* 欢迎页 */
.welcome-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 40px;
  text-align: center;
}
.welcome-icon-wrap {
  width: 80px;
  height: 80px;
  border-radius: 20px;
  background: linear-gradient(135deg, #f5f0ff, #ede9fe);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20px;
}
.welcome-title {
  font-size: 22px;
  font-weight: 700;
  color: #1f2937;
  margin: 0 0 8px;
}
.welcome-desc {
  font-size: 14px;
  color: #6b7280;
  margin: 0 0 32px;
}
.quick-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  max-width: 480px;
  width: 100%;
}
.quick-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 16px;
  background: #f8f9fc;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 13px;
  color: #374151;
  font-weight: 500;
}
.quick-card:hover {
  border-color: #8b5cf6;
  background: #f5f0ff;
  color: #7c3aed;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(139,92,246,0.1);
}
.quick-card .el-icon { font-size: 18px; color: #8b5cf6; }

/* 消息列表 */
.messages-list { padding: 16px 20px; }

.message-row {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}
.msg-avatar { flex-shrink: 0; }
.avatar {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  color: #fff;
}
.avatar-user { background: linear-gradient(135deg, #6366f1, #8b5cf6); }
.avatar-ai { background: linear-gradient(135deg, #8b5cf6, #a78bfa); }

.msg-body { flex: 1; min-width: 0; }
.msg-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}
.msg-role { font-size: 13px; font-weight: 600; color: #374151; }
.msg-time { font-size: 11px; color: #9ca3af; }

.msg-content {
  padding: 12px 16px;
  border-radius: 12px;
  line-height: 1.7;
  font-size: 14px;
}
.msg-user .msg-content {
  background: #f0f0ff;
  border: 1px solid #e0e0f0;
}
.msg-assistant .msg-content {
  background: #fafbfc;
  border: 1px solid #eef0f2;
}
.user-text {
  white-space: pre-wrap;
  word-break: break-word;
  color: #374151;
}

.msg-files {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}
.msg-file-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 10px;
  background: rgba(139,92,246,0.08);
  border-radius: 6px;
  font-size: 12px;
  color: #7c3aed;
}

.msg-actions {
  display: flex;
  gap: 4px;
  margin-top: 6px;
  opacity: 0;
  transition: opacity 0.2s;
}
.message-row:hover .msg-actions { opacity: 1; }

/* Markdown 渲染 */
.markdown-body { color: #374151; }
.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3) {
  margin: 14px 0 6px;
  font-weight: 700;
  color: #1f2937;
}
.markdown-body :deep(h3) { font-size: 15px; }
.markdown-body :deep(p) { margin: 6px 0; }
.markdown-body :deep(ul), .markdown-body :deep(ol) {
  margin: 6px 0;
  padding-left: 22px;
}
.markdown-body :deep(li) { margin: 3px 0; }
.markdown-body :deep(code) {
  padding: 2px 5px;
  background: #f1f2f6;
  border-radius: 4px;
  font-size: 13px;
  color: #e83e8c;
}
.markdown-body :deep(pre) {
  margin: 10px 0;
  padding: 14px;
  background: #1e1e2e;
  border-radius: 8px;
  overflow-x: auto;
  color: #cdd6f4;
}
.markdown-body :deep(pre code) {
  padding: 0;
  background: none;
  color: inherit;
}
.markdown-body :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 10px 0;
  font-size: 13px;
}
.markdown-body :deep(th),
.markdown-body :deep(td) {
  padding: 8px 10px;
  border: 1px solid #e5e7eb;
}
.markdown-body :deep(th) {
  background: #f8f9fc;
  font-weight: 600;
}
.markdown-body :deep(blockquote) {
  border-left: 4px solid #8b5cf6;
  margin: 10px 0;
  padding: 8px 14px;
  background: #f5f0ff;
  color: #6b7280;
}

/* 打字指示 */
.typing-bar {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 12px 20px;
  color: #9ca3af;
  font-size: 13px;
}
.typing-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #8b5cf6;
  animation: typing-bounce 1.4s infinite ease-in-out;
}
.typing-dot:nth-child(1) { animation-delay: -0.32s; }
.typing-dot:nth-child(2) { animation-delay: -0.16s; }
@keyframes typing-bounce {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
  40% { transform: scale(1); opacity: 1; }
}

/* 输入区域 */
.chat-input-area {
  border-top: 1px solid #f0f0f0;
  padding: 12px 20px;
  background: #fff;
}
.attached-files-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 8px;
}
.attached-file {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  background: #f0f0ff;
  border-radius: 6px;
  font-size: 12px;
  color: #6366f1;
}
.remove-file {
  cursor: pointer;
  font-size: 12px;
  margin-left: 2px;
  color: #ef4444;
}
.remove-file:hover { color: #dc2626; }

.input-row {
  display: flex;
  align-items: flex-end;
  gap: 8px;
}
.attach-btn { color: #6b7280; padding: 8px; }
.attach-btn:hover { color: #8b5cf6; }
.chat-textarea { flex: 1; }
.chat-textarea :deep(.el-textarea__inner) {
  border-radius: 10px;
  padding: 10px 14px;
  font-size: 14px;
  line-height: 1.5;
  border: 1px solid #e5e7eb;
  box-shadow: none;
  transition: border-color 0.2s;
}
.chat-textarea :deep(.el-textarea__inner):focus {
  border-color: #8b5cf6;
  box-shadow: 0 0 0 2px rgba(139,92,246,0.1);
}
.send-btn {
  border-radius: 10px;
  width: 40px;
  height: 40px;
  padding: 0;
  background: linear-gradient(135deg, #8b5cf6, #7c3aed) !important;
  border: none !important;
}
.send-btn:disabled {
  opacity: 0.5;
}

.input-hint {
  display: flex;
  justify-content: space-between;
  margin-top: 6px;
  font-size: 11px;
  color: #9ca3af;
}
.stop-link {
  color: #ef4444;
  cursor: pointer;
  font-weight: 500;
}
.stop-link:hover { text-decoration: underline; }

/* ===== 右栏：预览面板 ===== */
.preview-panel {
  width: 340px;
  min-width: 340px;
  background: #fafbfc;
  border-left: 1px solid #eef0f2;
  display: flex;
  flex-direction: column;
  transition: all 0.3s ease;
}
.preview-panel.collapsed {
  width: 48px;
  min-width: 48px;
}
.preview-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 12px;
  border-bottom: 1px solid #eef0f2;
}
.preview-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
}

.preview-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 30px;
  text-align: center;
  color: #9ca3af;
  font-size: 13px;
}
.preview-empty p { margin: 6px 0; }
.preview-hint { font-size: 11px; color: #c0c4cc; }

.preview-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.preview-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  border-bottom: 1px solid #eef0f2;
}
.preview-toolbar-actions { display: flex; gap: 6px; }

.preview-cases-list {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
}
.preview-cases-list::-webkit-scrollbar { width: 4px; }
.preview-cases-list::-webkit-scrollbar-thumb { background: rgba(139,92,246,0.2); border-radius: 3px; }

.preview-case-card {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  margin-bottom: 8px;
  overflow: hidden;
  transition: all 0.2s;
}
.preview-case-card:hover { border-color: #c4b5fd; }
.preview-case-card.expanded { border-color: #8b5cf6; box-shadow: 0 2px 8px rgba(139,92,246,0.08); }

.case-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  cursor: pointer;
}
.case-card-left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}
.case-card-title {
  font-size: 13px;
  font-weight: 500;
  color: #374151;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.expand-icon {
  font-size: 12px;
  color: #9ca3af;
  transition: transform 0.2s;
}
.expand-icon.rotated { transform: rotate(90deg); }

.case-card-body { padding: 0 14px 12px; }
.case-field {
  margin-top: 8px;
}
.case-field label {
  font-size: 11px;
  font-weight: 600;
  color: #8b5cf6;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  display: block;
  margin-bottom: 3px;
}
.case-field span {
  font-size: 13px;
  color: #4b5563;
  line-height: 1.5;
}
.case-steps {
  margin: 0;
  padding-left: 18px;
  font-size: 13px;
  color: #4b5563;
  line-height: 1.6;
}

/* 响应式 */
@media (max-width: 1200px) {
  .preview-panel:not(.collapsed) { width: 280px; min-width: 280px; }
}
@media (max-width: 1000px) {
  .sidebar-panel:not(.collapsed) { width: 220px; min-width: 220px; }
  .preview-panel { width: 48px; min-width: 48px; }
}
@media (max-width: 768px) {
  .ai-chat-page { flex-direction: column; }
  .sidebar-panel, .preview-panel { width: 100% !important; min-width: 100% !important; max-height: 200px; }
}
</style>
