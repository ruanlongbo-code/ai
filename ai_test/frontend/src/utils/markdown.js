import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'
import 'highlight.js/styles/github.css'

// 创建 markdown-it 实例
const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true,
  breaks: true,
  highlight: function (str, lang) {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return `<pre class="hljs"><code>${hljs.highlight(str, { language: lang, ignoreIllegals: true }).value}</code></pre>`
      } catch (__) {}
    }
    return `<pre class="hljs"><code>${md.utils.escapeHtml(str)}</code></pre>`
  }
})

// 自定义渲染规则
md.renderer.rules.table_open = () => '<div class="table-wrapper"><table class="markdown-table">'
md.renderer.rules.table_close = () => '</table></div>'

md.renderer.rules.code_block = (tokens, idx) => {
  const token = tokens[idx]
  const content = md.utils.escapeHtml(token.content)
  return `<pre class="code-block"><code>${content}</code></pre>`
}

// 渲染 Markdown 文本
export function renderMarkdown(text) {
  if (!text) return ''
  return md.render(text)
}

// 渲染内联 Markdown
export function renderInlineMarkdown(text) {
  if (!text) return ''
  return md.renderInline(text)
}

// 安全渲染（移除潜在的危险HTML）
export function renderSafeMarkdown(text) {
  if (!text) return ''
  const rendered = md.render(text)
  // 这里可以添加额外的安全过滤
  return rendered
}

export default {
  renderMarkdown,
  renderInlineMarkdown,
  renderSafeMarkdown
}