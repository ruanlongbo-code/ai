<template>
  <div class="code-editor-wrapper">
    <div class="code-editor-container" :style="containerStyle" ref="containerRef"></div>
    <div v-if="showValidationStatus && language === 'python'" class="validation-status" :class="validationStatusClass">
      <el-icon><CircleCheck v-if="isValidCode" /><CircleClose v-else /></el-icon>
      <span>{{ validationMessage }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch, computed } from 'vue'
import { EditorView, basicSetup } from 'codemirror'
import { EditorState } from '@codemirror/state'
import { python } from '@codemirror/lang-python'
import { oneDark } from '@codemirror/theme-one-dark'
import { githubLight, githubDark } from '@uiw/codemirror-theme-github'
import { linter, lintGutter } from '@codemirror/lint'
import { CircleCheck, CircleClose } from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: { type: String, default: '' },
  language: { type: String, default: 'python' },
  height: { type: String, default: '360px' },
  readOnly: { type: Boolean, default: false },
  theme: { type: String, default: 'light' }, // 'light' | 'dark' | 'monokai'
  fontSize: { type: Number, default: 14 },
  showMinimap: { type: Boolean, default: false },
  wordWrap: { type: String, default: 'off' }, // off | on | wordWrapColumn | bounded
  tabSize: { type: Number, default: 4 },
  useSoftTabs: { type: Boolean, default: true },
  showLineNumbers: { type: Boolean, default: true },
  showGutter: { type: Boolean, default: true },
  highlightActiveLine: { type: Boolean, default: true },
  placeholder: { type: String, default: '# 请输入Python代码...' },
  showValidation: { type: Boolean, default: true } // 是否显示校验状态
})

const emit = defineEmits(['update:modelValue', 'change', 'focus', 'blur', 'validation'])

const containerRef = ref(null)
const isValidCode = ref(true)
const validationMessage = ref('代码语法正确')
const showValidationStatus = computed(() => props.showValidation && props.language === 'python')

const containerStyle = computed(() => ({ 
  height: props.height,
  '--cm-editor-height': props.height
}))

const validationStatusClass = computed(() => ({
  'validation-valid': isValidCode.value,
  'validation-invalid': !isValidCode.value
}))

let editorView = null

// Python语法检查器
const pythonLinter = linter((view) => {
  const diagnostics = []
  const content = view.state.doc.toString()
  
  if (!content.trim()) {
    isValidCode.value = true
    validationMessage.value = '代码语法正确'
    emit('validation', { isValid: true, message: '代码语法正确' })
    return diagnostics
  }
  
  // 基础Python语法检查
  try {
    // 检查基本的Python语法错误
    const lines = content.split('\n')
    let hasError = false
    let errorMessage = ''
    let errorLine = 0
    
    // 检查缩进错误
    let expectedIndent = 0
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i]
      if (line.trim() === '') continue
      
      const indent = line.length - line.trimStart().length
      
      // 检查是否有混合使用tab和空格
      if (line.includes('\t') && line.includes(' ')) {
        hasError = true
        errorMessage = '不能混合使用制表符和空格进行缩进'
        errorLine = i
        break
      }
      
      // 检查基本的语法结构
      const trimmedLine = line.trim()
      
      // 检查冒号后是否有内容（对于控制结构）
      if (trimmedLine.match(/^(if|elif|else|for|while|def|class|try|except|finally|with)\s.*:$/)) {
        expectedIndent = indent + (props.tabSize || 4)
      } else if (trimmedLine === 'else:' || trimmedLine === 'finally:' || trimmedLine.match(/^except.*:$/)) {
        expectedIndent = indent + (props.tabSize || 4)
      }
      
      // 检查括号匹配
      const openBrackets = (trimmedLine.match(/[\(\[\{]/g) || []).length
      const closeBrackets = (trimmedLine.match(/[\)\]\}]/g) || []).length
      
      // 检查字符串引号匹配
      const singleQuotes = (trimmedLine.match(/'/g) || []).length
      const doubleQuotes = (trimmedLine.match(/"/g) || []).length
      
      if (singleQuotes % 2 !== 0 || doubleQuotes % 2 !== 0) {
        // 简单的引号检查，可能有误报，但能捕获基本错误
        if (!trimmedLine.includes('"""') && !trimmedLine.includes("'''")) {
          hasError = true
          errorMessage = '字符串引号不匹配'
          errorLine = i
          break
        }
      }
    }
    
    if (hasError) {
      isValidCode.value = false
      validationMessage.value = `第${errorLine + 1}行: ${errorMessage}`
      
      const lineStart = content.split('\n').slice(0, errorLine).join('\n').length + (errorLine > 0 ? 1 : 0)
      const lineEnd = lineStart + lines[errorLine].length
      
      diagnostics.push({
        from: lineStart,
        to: lineEnd,
        severity: 'error',
        message: errorMessage
      })
    } else {
      isValidCode.value = true
      validationMessage.value = '代码语法正确'
    }
  } catch (error) {
    isValidCode.value = false
    validationMessage.value = `语法错误: ${error.message}`
    
    diagnostics.push({
      from: 0,
      to: content.length,
      severity: 'error',
      message: error.message
    })
  }
  
  // 发送校验结果事件
  emit('validation', {
    isValid: isValidCode.value,
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
  emit('update:modelValue', content)
  emit('change', content)
}

// 格式化代码
const formatCode = () => {
  if (!editorView) return
  
  const content = getEditorContent()
  // 简单的Python代码格式化（基础缩进修正）
  try {
    const lines = content.split('\n')
    const formatted = []
    let indentLevel = 0
    const indentSize = props.tabSize || 4
    
    for (let line of lines) {
      const trimmed = line.trim()
      if (trimmed === '') {
        formatted.push('')
        continue
      }
      
      // 减少缩进的关键字
      if (trimmed.match(/^(elif|else|except|finally|return|break|continue|pass)/)) {
        if (indentLevel > 0) indentLevel--
      }
      
      // 添加当前行
      formatted.push(' '.repeat(indentLevel * indentSize) + trimmed)
      
      // 增加缩进的关键字
      if (trimmed.endsWith(':')) {
        indentLevel++
      }
    }
    
    setEditorContent(formatted.join('\n'))
  } catch (error) {
    console.warn('代码格式化失败:', error)
  }
}

// 复制代码
const copyCode = async () => {
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

onMounted(() => {
  // 准备初始内容
  const initialContent = props.modelValue || ''

  // 创建编辑器扩展
  const extensions = [
    basicSetup,
    EditorView.updateListener.of((update) => {
      if (update.docChanged) {
        const content = update.state.doc.toString()
        handleContentChange(content)
      }
      if (update.focusChanged) {
        if (update.view.hasFocus) {
          emit('focus')
        } else {
          emit('blur')
        }
      }
    }),
    EditorState.readOnly.of(props.readOnly),
    EditorView.theme({
      '&': {
        height: '100%',
        fontSize: `${props.fontSize}px`
      },
      '.cm-editor': {
        height: '100%'
      },
      '.cm-scroller': {
        fontFamily: 'Monaco, Menlo, "Ubuntu Mono", "Consolas", "Courier New", monospace',
        lineHeight: '1.5'
      },
      '.cm-focused': {
        outline: 'none'
      },
      '.cm-content': {
        padding: '12px',
        minHeight: '100%'
      },
      '.cm-gutters': {
        backgroundColor: '#f8f9fa',
        borderRight: '1px solid #e9ecef',
        color: '#6c757d'
      },
      '.cm-lineNumbers .cm-gutterElement': {
        padding: '0 8px',
        fontSize: '12px'
      },
      '.cm-lintRange-error': {
        backgroundImage: 'url("data:image/svg+xml,<svg xmlns=\'http://www.w3.org/2000/svg\' width=\'6\' height=\'3\'><path d=\'m0 3 l3 -3 l1 0 l1 2 l1 -2 l1 0 l3 3 z\' fill=\'%23ef4444\'></path></svg>")',
        backgroundRepeat: 'repeat-x',
        backgroundPosition: 'bottom'
      }
    })
  ]

  // 添加语言支持
  if (props.language === 'python') {
    extensions.push(python())
    extensions.push(pythonLinter)
    extensions.push(lintGutter())
  }

  // 添加主题
  if (props.theme === 'dark') {
    extensions.push(oneDark)
  } else if (props.theme === 'github-light') {
    extensions.push(githubLight)
  } else if (props.theme === 'github-dark') {
    extensions.push(githubDark)
  }
  // 默认使用 CodeMirror 6 的默认亮色主题（不添加任何主题扩展）

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
  if (props.language === 'python') {
    setTimeout(() => {
      if (editorView) {
        const content = editorView.state.doc.toString()
        if (content.trim()) {
          // 触发一次校验 - 通过更新编辑器状态来触发 linter
          const transaction = editorView.state.update({
            changes: { from: 0, to: 0, insert: '' }
          })
          editorView.dispatch(transaction)
        }
      }
    }, 100)
  }
})

// 监听 modelValue 变化
watch(() => props.modelValue, (newValue) => {
  if (!editorView) return
  
  const currentContent = getEditorContent()
  const newContent = newValue || ''
  
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

// 获取校验状态
const getValidationStatus = () => {
  return {
    isValid: isValidCode.value,
    message: validationMessage.value
  }
}

// 暴露方法给父组件
defineExpose({
  formatCode,
  copyCode,
  getEditorContent,
  setEditorContent,
  getValidationStatus
})
</script>

<style scoped>
.code-editor-wrapper {
  position: relative;
  border: 1px solid #e1e5e9;
  border-radius: 6px;
  overflow: hidden;
  background: transparent; /* 让主题控制背景色 */
}

.code-editor-container {
  width: 100%;
  min-height: 200px;
  background: transparent; /* 让主题控制背景色 */
}

.validation-status {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-top: 1px solid #e1e5e9;
  background: #f8f9fa;
  font-size: 12px;
  font-weight: 500;
}

.validation-valid {
  color: #16a34a;
  background: #f0fdf4;
  border-top-color: #bbf7d0;
}

.validation-invalid {
  color: #dc2626;
  background: #fef2f2;
  border-top-color: #fecaca;
}

/* CodeMirror 自定义样式 - 减少覆盖 */
:deep(.cm-editor) {
  border: none;
  outline: none;
}

:deep(.cm-focused) {
  outline: none;
}

/* 移除强制的颜色设置，让主题控制 */
/* :deep(.cm-content) {
  caret-color: #1f2937;
}

:deep(.cm-cursor) {
  border-left-color: #1f2937;
} */

:deep(.cm-selectionBackground) {
  background: #3b82f6 !important;
}

/* 移除强制的行高亮颜色，让主题控制 */
/* :deep(.cm-activeLine) {
  background: #f8fafc;
}

:deep(.cm-activeLineGutter) {
  background: #f1f5f9;
} */

/* 错误提示样式 */
:deep(.cm-tooltip-lint) {
  background: #1f2937;
  color: #ffffff;
  border: none;
  border-radius: 4px;
  padding: 6px 8px;
  font-size: 12px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

:deep(.cm-diagnostic-error) {
  border-left: 3px solid #ef4444;
  padding-left: 8px;
}

/* 暗色主题支持 */
.dark .code-editor-wrapper {
  border-color: #374151;
  background: transparent; /* 让主题控制背景色 */
}

.dark .validation-status {
  background: #374151;
  border-top-color: #4b5563;
  color: #d1d5db;
}

.dark .validation-valid {
  color: #34d399;
  background: #064e3b;
  border-top-color: #065f46;
}

.dark .validation-invalid {
  color: #f87171;
  background: #7f1d1d;
  border-top-color: #991b1b;
}

/* 移除暗色主题的强制颜色设置，让主题控制 */
/* .dark :deep(.cm-content) {
  caret-color: #ffffff;
}

.dark :deep(.cm-cursor) {
  border-left-color: #ffffff;
}

.dark :deep(.cm-activeLine) {
  background: rgba(55, 65, 81, 0.5);
}

.dark :deep(.cm-activeLineGutter) {
  background: rgba(75, 85, 99, 0.5);
} */
</style>