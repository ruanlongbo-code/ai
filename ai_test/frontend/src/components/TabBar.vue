<template>
  <div class="tab-bar-container">
    <!-- 左滚动按钮 -->
    <div 
      v-if="canScrollLeft" 
      class="scroll-button scroll-left"
      @click="scrollLeft"
    >
      <el-icon><ArrowLeft /></el-icon>
    </div>

    <!-- 标签栏主体 -->
    <div 
      ref="tabsContainer" 
      class="tabs-container"
      @wheel="handleWheel"
      @scroll="updateScrollState"
    >
      <div class="tabs-wrapper">
        <div
          v-for="tab in tabStore.tabs"
          :key="tab.id"
          :class="[
            'tab-item',
            { 'active': tab.active }
          ]"
          @click="handleTabClick(tab)"
          @contextmenu.prevent="handleContextMenu($event, tab)"
        >
          <!-- 标签图标 -->
          <el-icon class="tab-icon">
            <component :is="getIconComponent(tab.icon)" />
          </el-icon>
          
          <!-- 标签标题 -->
          <span class="tab-title">{{ tab.title }}</span>
          
          <!-- 关闭按钮 -->
          <div 
            v-if="tab.closable"
            class="tab-close"
            @click.stop="handleTabClose(tab)"
          >
            <el-icon><Close /></el-icon>
          </div>
        </div>
      </div>
    </div>

    <!-- 右滚动按钮 -->
    <div 
      v-if="canScrollRight" 
      class="scroll-button scroll-right"
      @click="scrollRight"
    >
      <el-icon><ArrowRight /></el-icon>
    </div>

    <!-- 关闭其他标签按钮 -->
    <div 
      class="close-others-button"
      @click="closeOtherTabs"
      title="关闭其他标签"
    >
      <el-icon><Close /></el-icon>
      <span>关闭其他</span>
    </div>

    <!-- 右键菜单 -->
    <div
      v-if="contextMenu.visible"
      ref="contextMenuRef"
      class="context-menu"
      :style="{ left: contextMenu.x + 'px', top: contextMenu.y + 'px' }"
    >
      <div class="menu-item" @click="refreshTab">
        <el-icon><Refresh /></el-icon>
        <span>刷新页面</span>
      </div>
      <div class="menu-divider"></div>
      <div 
        v-if="contextMenu.targetTab?.closable"
        class="menu-item" 
        @click="closeCurrentTab"
      >
        <el-icon><Close /></el-icon>
        <span>关闭当前标签</span>
      </div>
      <div class="menu-item" @click="closeOtherTabs">
        <el-icon><CircleClose /></el-icon>
        <span>关闭其他标签</span>
      </div>
      <div class="menu-item" @click="closeAllTabs">
        <el-icon><Delete /></el-icon>
        <span>关闭所有标签</span>
      </div>
    </div>

    <!-- 遮罩层，用于关闭右键菜单 -->
    <div
      v-if="contextMenu.visible"
      class="context-menu-overlay"
      @click="hideContextMenu"
    ></div>
  </div>
</template>

<script setup>
import { ref, reactive, nextTick, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useTabStore } from '@/stores/tabStore'
import { 
  ArrowLeft, 
  ArrowRight, 
  Close, 
  Refresh, 
  CircleClose, 
  Delete,
  DataBoard,
  FolderOpened,
  Platform,
  User,
  Grid,
  Document,
  DocumentChecked,
  Connection,
  Collection,
  Calendar,
  DataAnalysis,
  Monitor,
  View,
  UserFilled,
  Edit
} from '@element-plus/icons-vue'

const router = useRouter()
const tabStore = useTabStore()

// 滚动相关
const tabsContainer = ref(null)
const canScrollLeft = ref(false)
const canScrollRight = ref(false)

// 右键菜单
const contextMenuRef = ref(null)
const contextMenu = reactive({
  visible: false,
  x: 0,
  y: 0,
  targetTab: null
})

// 图标组件映射
const iconComponents = {
  DataBoard,
  FolderOpened,
  Platform,
  User,
  Grid,
  Document,
  DocumentChecked,
  Connection,
  Collection,
  Calendar,
  DataAnalysis,
  Monitor,
  View,
  UserFilled,
  Edit
}

// 获取图标组件
const getIconComponent = (iconName) => {
  return iconComponents[iconName] || Document
}

// 标签点击处理
const handleTabClick = (tab) => {
  if (tab.path !== router.currentRoute.value.path) {
    router.push(tab.path)
  }
  tabStore.setActiveTab(tab.id)
}

// 标签关闭处理
const handleTabClose = (tab) => {
  const redirectPath = tabStore.removeTab(tab.id)
  if (redirectPath && redirectPath !== router.currentRoute.value.path) {
    router.push(redirectPath)
  }
}

// 滚动处理
const scrollLeft = () => {
  if (tabsContainer.value) {
    tabsContainer.value.scrollBy({ left: -200, behavior: 'smooth' })
  }
}

const scrollRight = () => {
  if (tabsContainer.value) {
    tabsContainer.value.scrollBy({ left: 200, behavior: 'smooth' })
  }
}

const handleWheel = (event) => {
  if (tabsContainer.value) {
    event.preventDefault()
    tabsContainer.value.scrollBy({ left: event.deltaY, behavior: 'smooth' })
  }
}

// 更新滚动状态
const updateScrollState = () => {
  if (tabsContainer.value) {
    const { scrollLeft, scrollWidth, clientWidth } = tabsContainer.value
    canScrollLeft.value = scrollLeft > 0
    canScrollRight.value = scrollLeft < scrollWidth - clientWidth - 1
  }
}

// 右键菜单处理
const handleContextMenu = (event, tab) => {
  console.log('右键菜单触发:', { event, tab, clientX: event.clientX, clientY: event.clientY })
  
  event.preventDefault()
  event.stopPropagation()
  
  contextMenu.visible = true
  contextMenu.x = event.clientX
  contextMenu.y = event.clientY
  contextMenu.targetTab = tab
  
  console.log('菜单状态设置:', { 
    visible: contextMenu.visible, 
    x: contextMenu.x, 
    y: contextMenu.y, 
    targetTab: contextMenu.targetTab 
  })
  
  nextTick(() => {
    // 确保菜单不会超出屏幕边界
    if (contextMenuRef.value) {
      const menuRect = contextMenuRef.value.getBoundingClientRect()
      const windowWidth = window.innerWidth
      const windowHeight = window.innerHeight
      
      console.log('菜单位置调整前:', { x: contextMenu.x, y: contextMenu.y })
      console.log('菜单尺寸:', { width: menuRect.width, height: menuRect.height })
      
      if (contextMenu.x + menuRect.width > windowWidth) {
        contextMenu.x = windowWidth - menuRect.width - 10
      }
      
      if (contextMenu.y + menuRect.height > windowHeight) {
        contextMenu.y = windowHeight - menuRect.height - 10
      }
      
      console.log('菜单位置调整后:', { x: contextMenu.x, y: contextMenu.y })
    }
  })
}

const hideContextMenu = () => {
  contextMenu.visible = false
  contextMenu.targetTab = null
}

// 右键菜单操作
const refreshTab = () => {
  if (contextMenu.targetTab) {
    const path = tabStore.refreshTab(contextMenu.targetTab.id)
    if (path) {
      // 强制刷新当前页面
      router.go(0)
    }
  }
  hideContextMenu()
}

const closeCurrentTab = () => {
  if (contextMenu.targetTab) {
    handleTabClose(contextMenu.targetTab)
  }
  hideContextMenu()
}

const closeOtherTabs = () => {
  // 获取当前激活的标签
  const activeTab = tabStore.activeTab
  if (activeTab) {
    tabStore.closeOtherTabs(activeTab.id)
    // 如果当前标签被关闭，跳转到保留的标签
    if (!tabStore.tabs.find(tab => tab.path === router.currentRoute.value.path)) {
      if (activeTab) {
        router.push(activeTab.path)
      }
    }
  }
  hideContextMenu()
}

const closeAllTabs = () => {
  const redirectPath = tabStore.closeAllTabs()
  if (redirectPath && redirectPath !== router.currentRoute.value.path) {
    router.push(redirectPath)
  }
  hideContextMenu()
}

// 监听点击事件，关闭右键菜单
const handleDocumentClick = (event) => {
  if (contextMenu.visible && contextMenuRef.value && !contextMenuRef.value.contains(event.target)) {
    hideContextMenu()
  }
}

onMounted(() => {
  // 初始化滚动状态
  nextTick(() => {
    updateScrollState()
  })
  
  // 监听窗口大小变化
  window.addEventListener('resize', updateScrollState)
  
  // 监听文档点击事件
  document.addEventListener('click', handleDocumentClick)
})

onUnmounted(() => {
  window.removeEventListener('resize', updateScrollState)
  document.removeEventListener('click', handleDocumentClick)
})
</script>

<style scoped>
.tab-bar-container {
  position: relative;
  display: flex;
  align-items: center;
  height: 40px;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.1), rgba(124, 58, 237, 0.05));
  backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(139, 92, 246, 0.3);
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(139, 92, 246, 0.1);
}

.scroll-button {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 100%;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.1), rgba(124, 58, 237, 0.05));
  border-right: 1px solid rgba(139, 92, 246, 0.2);
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  color: rgba(255, 255, 255, 0.7);
  z-index: 2;
  position: relative;
}

.scroll-button::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.2), rgba(124, 58, 237, 0.1));
  opacity: 0;
  transition: opacity 0.3s ease;
}

.scroll-button:hover::before {
  opacity: 1;
}

.scroll-button:hover {
  color: rgba(255, 255, 255, 1);
  transform: scale(1.05);
}

.close-others-button {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 0 12px;
  height: 100%;
  margin: 0 8px 0 4px;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.15), rgba(124, 58, 237, 0.08));
  border: 1px solid rgba(139, 92, 246, 0.3);
  border-radius: 0;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  color: rgba(255, 255, 255, 0.8);
  font-size: 12px;
  white-space: nowrap;
  position: relative;
  overflow: hidden;
}

.close-others-button::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.3), rgba(124, 58, 237, 0.15));
  opacity: 0;
  transition: opacity 0.3s ease;
}

.close-others-button:hover::before {
  opacity: 1;
}

.close-others-button:hover {
  color: rgba(255, 255, 255, 1);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.3);
}

.close-others-button:active {
  transform: translateY(0);
  box-shadow: 0 2px 6px rgba(139, 92, 246, 0.2);
}

.scroll-left {
  border-right: 1px solid rgba(139, 92, 246, 0.2);
}

.scroll-right {
  border-left: 1px solid rgba(139, 92, 246, 0.2);
}

.tabs-container {
  flex: 1;
  overflow-x: auto;
  overflow-y: hidden;
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.tabs-container::-webkit-scrollbar {
  display: none;
}

.tabs-wrapper {
  display: flex;
  height: 100%;
  min-width: max-content;
  gap: 4px;
  padding: 0 4px;
}

.tab-item {
  display: flex;
  align-items: center;
  padding: 0 18px;
  min-width: 140px;
  max-width: 220px;
  height: 32px;
  margin: 0;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0.03));
  border: 1px solid rgba(139, 92, 246, 0.15);
  border-radius: 0;
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  user-select: none;
  overflow: hidden;
}

.tab-item::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.15), rgba(124, 58, 237, 0.1));
  opacity: 0;
  transition: opacity 0.3s ease;
}

.tab-item:hover::before {
  opacity: 1;
}

.tab-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.2);
}

.tab-item.active {
  background: linear-gradient(135deg, #8b5cf6, #7c3aed);
  color: #ffffff;
  border-bottom: 1px solid #ffffff;
  box-shadow: 0 4px 16px rgba(139, 92, 246, 0.4);
  z-index: 1;
}

.tab-item.active::before {
  opacity: 0;
}

.tab-item.active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, #ffffff, rgba(255, 255, 255, 0.9), #ffffff);
  box-shadow: 0 0 8px rgba(255, 255, 255, 0.5);
}

.tab-icon {
  font-size: 16px;
  margin-right: 10px;
  flex-shrink: 0;
  color: inherit;
  transition: all 0.3s ease;
}

.tab-title {
  flex: 1;
  font-size: 14px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: inherit;
  transition: all 0.3s ease;
}

.tab-item:not(.active) .tab-title {
  color: rgba(255, 255, 255, 0.85);
}

.tab-item:not(.active) .tab-icon {
  color: rgba(255, 255, 255, 0.7);
}

.tab-item:hover:not(.active) .tab-title {
  color: rgba(255, 255, 255, 0.95);
}

.tab-item:hover:not(.active) .tab-icon {
  color: rgba(255, 255, 255, 0.9);
}

.tab-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  margin-left: 10px;
  border-radius: 50%;
  opacity: 0.7;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  flex-shrink: 0;
  position: relative;
}

.tab-close::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.tab-close:hover::before {
  opacity: 1;
}

.tab-close:hover {
  opacity: 1;
  transform: scale(1.15);
  box-shadow: 0 2px 8px rgba(255, 255, 255, 0.3);
}

.tab-close .el-icon {
  font-size: 12px;
  z-index: 1;
  position: relative;
}

/* 右键菜单样式 */
.context-menu {
  position: fixed;
  z-index: 99999;
  background: rgba(30, 30, 30, 0.95);
  backdrop-filter: blur(20px);
  border: 2px solid rgba(139, 92, 246, 0.6);
  border-radius: 8px;
  padding: 8px 0;
  min-width: 160px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.6), 0 0 0 1px rgba(139, 92, 246, 0.3);
  animation: contextMenuFadeIn 0.15s ease-out;
}

@keyframes contextMenuFadeIn {
  from {
    opacity: 0;
    transform: scale(0.95) translateY(-5px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

.menu-item {
  display: flex;
  align-items: center;
  padding: 10px 16px;
  cursor: pointer;
  transition: all 0.2s ease;
  color: rgba(255, 255, 255, 0.9);
  font-size: 14px;
  font-weight: 500;
  border-radius: 4px;
  margin: 2px 6px;
}

.menu-item:hover {
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.4), rgba(124, 58, 237, 0.3));
  color: #ffffff;
  transform: translateX(2px);
}

.menu-item .el-icon {
  margin-right: 8px;
  font-size: 16px;
}

.menu-divider {
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(139, 92, 246, 0.4), transparent);
  margin: 6px 12px;
}

.context-menu-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 99998;
  background: transparent;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .tab-item {
    min-width: 100px;
    max-width: 150px;
    padding: 0 12px;
  }
  
  .tab-title {
    font-size: 13px;
  }
  
  .tab-close {
    width: 24px;
    height: 24px;
  }
  
  .context-menu {
    min-width: 140px;
  }
  
  .menu-item {
    padding: 10px 16px;
    font-size: 15px;
  }
}

/* 动画效果 */
.tab-item {
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateX(-20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.context-menu {
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: scale(0.9);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}
</style>