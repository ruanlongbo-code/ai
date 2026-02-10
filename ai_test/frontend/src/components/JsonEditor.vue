<template>
  <div class="json-editor-wrapper">
    <div class="json-editor-container" :style="containerStyle" ref="containerRef"></div>
    <div v-if="showValidationStatus" class="validation-status" :class="validationStatusClass">
      <el-icon><CircleCheck v-if="isValidJson" /><CircleClose v-else /></el-icon>
      <span>{{ validationMessage }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch, computed } from 'vue'
import { EditorView, basicSetup } from 'codemirror'
import { EditorState } from '@codemirror/state'
import { json } from '@codemirror/lang-json'
import { oneDark } from '@codemirror/theme-one-dark'
import { linter, lintGutter } from '@codemirror/lint'
import { CircleCheck, CircleClose } from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: { type: [String, Object, Array], default: '' },
  height: { type: String, default: '300px' },
  readOnly: { type: Boolean, default: false },
  theme: { type: String, default: 'light' }, // 'light' | 'dark'
  placeholder: { type: String, default: '请输入JSON数据...' },
  showValidation: { type: Boolean, default: true } // 是否显示校验状态
})

const emit = defineEmits(['update:modelValue', 'change', 'validation'])

const containerRef = ref(null)
const isValidJson = ref(true)
const validationMessage = ref('JSON格式正确')
const showValidationStatus = computed(() => props.showValidation)

const containerStyle = computed(() => ({ 
  height: props.height,
  '--cm-editor-height': props.height
}))

const validationStatusClass = computed(() => ({
  'validation-valid': isValidJson.value,
  'validation-invalid': !isValidJson.value
}))

let editorView = null

// 格式化JSON字符串的内部工具函数
const formatJsonText = (text) => {
  try {
    const parsed = JSON.parse(text)
    return JSON.stringify(parsed, null, 2)
  } catch {
    return text
  }
}

// JSON语法检查器
const jsonLinter = linter((view) => {
  const diagnostics = []
  const content = view.state.doc.toString()
  
  if (!content.trim()) {
    return diagnostics
  }
  
  try {
    JSON.parse(content)
    // JSON有效
    isValidJson.value = true
    validationMessage.value = 'JSON格式正确'
  } catch (error) {
    // JSON无效
    isValidJson.value = false
    validationMessage.value = `JSON格式错误: ${error.message}`
    
    // 尝试找到错误位置
    let errorPos = 0
    const errorMatch = error.message.match(/position (\d+)/)
    if (errorMatch) {
      errorPos = parseInt(errorMatch[1])
    } else {
      // 如果无法精确定位，尝试解析到错误位置
      const lines = content.split('\n')
      let pos = 0
      for (let i = 0; i < lines.length; i++) {
        try {
          JSON.parse(content.substring(0, pos + lines[i].length))
          pos += lines[i].length + 1
        } catch {
          errorPos = Math.min(pos, content.length)
          break
        }
      }
    }
    
    diagnostics.push({
      from: Math.max(0, errorPos - 1),
      to: Math.min(content.length, errorPos + 1),
      severity: 'error',
      message: error.message
    })
  }
  
  // 发送校验结果事件
  emit('validation', {
    isValid: isValidJson.value,
    message: validationMessage.value
  })
  
  return diagnostics
})

// 获取编辑器内容
const getEditorContent = () => {
  return editorView ? editorView.state.doc.toString() : ''
}

// 设置编辑器内容
const setEditorContent = (content) => {
  if (!editorView) return
  
  const transaction = editorView.state.update({
    changes: {
      from: 0,
      to: editorView.state.doc.length,
      insert: content
    }
  })
  editorView.dispatch(transaction)
}

// 处理内容变化
const handleContentChange = (content) => {
  let parsed = null
  let isValid = true
  
  try {
    if (content.trim()) {
      parsed = JSON.parse(content)
    }
  } catch {
    isValid = false
  }
  
  emit('update:modelValue', content)
  emit('change', { text: content, json: parsed, isValid })
}

onMounted(() => {
  // 准备初始内容
  let initialContent = ''
  if (typeof props.modelValue === 'string') {
    initialContent = props.modelValue
  } else if (typeof props.modelValue === 'object' && props.modelValue !== null) {
    initialContent = JSON.stringify(props.modelValue, null, 2)
  } else {
    initialContent = '{}'
  }

  // 创建编辑器扩展
  const extensions = [
    basicSetup,
    json(),
    jsonLinter,
    lintGutter(),
    EditorView.updateListener.of((update) => {
      if (update.docChanged) {
        const content = update.state.doc.toString()
        handleContentChange(content)
      }
    }),
    EditorState.readOnly.of(props.readOnly),
    EditorView.theme({
      '&': {
        height: '100%',
        fontSize: '14px'
      },
      '.cm-editor': {
        height: '100%'
      },
      '.cm-scroller': {
        fontFamily: 'Monaco, Menlo, "Ubuntu Mono", "Consolas", monospace'
      },
      '.cm-focused': {
        outline: 'none'
      },
      '.cm-lintRange-error': {
        backgroundImage: 'url("data:image/svg+xml,<svg xmlns=\'http://www.w3.org/2000/svg\' width=\'6\' height=\'3\'><path d=\'m0 3 l3 -3 l1 0 l1 2 l1 -2 l1 0 l3 3 z\' fill=\'%23ef4444\'></path></svg>")',
        backgroundRepeat: 'repeat-x',
        backgroundPosition: 'bottom'
      }
    })
  ]

  // 添加主题
  if (props.theme === 'dark') {
    extensions.push(oneDark)
  }

  // 创建编辑器状态
  const state = EditorState.create({
    doc: initialContent,
    extensions
  })

  // 创建编辑器视图
  editorView = new EditorView({
    state,
    parent: containerRef.value
  })
  
  // 初始校验
  setTimeout(() => {
    if (editorView) {
      const content = editorView.state.doc.toString()
      if (content.trim()) {
        try {
          JSON.parse(content)
          isValidJson.value = true
          validationMessage.value = 'JSON格式正确'
        } catch (error) {
          isValidJson.value = false
          validationMessage.value = `JSON格式错误: ${error.message}`
        }
        emit('validation', {
          isValid: isValidJson.value,
          message: validationMessage.value
        })
      }
    }
  }, 100)
})

// 监听 modelValue 变化
watch(() => props.modelValue, (newValue) => {
  if (!editorView) return
  
  const currentContent = getEditorContent()
  let newContent = ''
  
  if (typeof newValue === 'string') {
    newContent = newValue
  } else if (typeof newValue === 'object' && newValue !== null) {
    newContent = JSON.stringify(newValue, null, 2)
  } else {
    newContent = '{}'
  }
  
  if (currentContent !== newContent) {
    setEditorContent(newContent)
  }
})

onBeforeUnmount(() => {
  if (editorView) {
    editorView.destroy()
    editorView = null
  }
})

// 暴露方法给父组件
const formatJson = () => {
  if (!editorView) return
  
  const content = getEditorContent()
  try {
    const parsed = JSON.parse(content)
    const formatted = JSON.stringify(parsed, null, 2)
    setEditorContent(formatted)
  } catch (error) {
    console.warn('JSON格式化失败:', error)
  }
}

const copyJson = async () => {
  if (!editorView) return false
  
  try {
    const content = getEditorContent()
    await navigator.clipboard.writeText(content)
    return true
  } catch (error) {
    console.warn('复制失败:', error)
    return false
  }
}

// 获取校验状态
const getValidationStatus = () => {
  return {
    isValid: isValidJson.value,
    message: validationMessage.value
  }
}

defineExpose({
  formatJson,
  copyJson,
  getEditorContent,
  setEditorContent,
  getValidationStatus
})
</script>

<style scoped>
.json-editor-wrapper {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.json-editor-container {
  border: 1px solid var(--el-border-color-light);
  border-radius: 6px;
  overflow: hidden;
  background-color: #fff;
  position: relative;
}

.validation-status {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.validation-status.validation-valid {
  background-color: #f0f9ff;
  color: #16a34a;
  border: 1px solid #bbf7d0;
}

.validation-status.validation-invalid {
  background-color: #fef2f2;
  color: #dc2626;
  border: 1px solid #fecaca;
}

.validation-status .el-icon {
  font-size: 14px;
}

:deep(.cm-editor) {
  height: var(--cm-editor-height, 300px);
  font-size: 14px;
  line-height: 1.6;
}

:deep(.cm-content) {
  padding: 12px;
  min-height: 100%;
}

:deep(.cm-focused) {
  outline: none;
}

:deep(.cm-scroller) {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', 'Consolas', monospace;
}

:deep(.cm-gutters) {
  background-color: #f8f9fa;
  border-right: 1px solid var(--el-border-color-lighter);
  color: #999;
}

:deep(.cm-lineNumbers .cm-gutterElement) {
  padding: 0 8px;
  font-size: 12px;
}

/* JSON语法高亮 */
:deep(.cm-string) {
  color: #22c55e;
}

:deep(.cm-number) {
  color: #f59e0b;
}

:deep(.cm-keyword) {
  color: #3b82f6;
}

:deep(.cm-atom) {
  color: #8b5cf6;
}

:deep(.cm-property) {
  color: #ef4444;
}

:deep(.cm-punctuation) {
  color: #6b7280;
}

/* 选中状态 */
:deep(.cm-selectionBackground) {
  background-color: #dbeafe !important;
}

:deep(.cm-activeLine) {
  background-color: #f8fafc;
}

/* 错误状态 */
:deep(.cm-diagnostic-error) {
  border-bottom: 2px wavy #ef4444;
}

/* 暗色主题支持 */
:deep(.cm-theme-dark) {
  background-color: #1f2937;
  color: #f9fafb;
}

:deep(.cm-theme-dark .cm-gutters) {
  background-color: #374151;
  border-right-color: #4b5563;
  color: #9ca3af;
}

:deep(.cm-theme-dark .cm-activeLine) {
  background-color: #374151;
}

:deep(.cm-theme-dark .cm-selectionBackground) {
  background-color: #1e40af !important;
}

/* 暗色主题下的校验状态样式 */
.dark .validation-status.validation-valid {
  background-color: #0f1419;
  color: #4ade80;
  border-color: #166534;
}

.dark .validation-status.validation-invalid {
  background-color: #1f1113;
  color: #f87171;
  border-color: #991b1b;
}
</style>