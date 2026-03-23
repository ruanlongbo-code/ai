<template>
  <div class="ai-testpoint-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <h2>
            <el-icon style="color: #8b5cf6; margin-right: 8px;"><Aim /></el-icon>
            AI 生成测试用例
          </h2>
          <p class="subtitle">上传需求文档、截图或评审视频，AI 多模态智能识别内容，自动提取测试点并生成测试用例</p>
        </div>
        <div class="flow-steps">
          <div :class="['step', currentStep >= 0 ? 'active' : '']">
            <span class="step-num">1</span><span>上传需求</span>
          </div>
          <el-icon class="step-arrow"><Right /></el-icon>
          <div :class="['step', currentStep >= 1 ? 'active' : '']">
            <span class="step-num">2</span><span>AI 提取测试点</span>
          </div>
          <el-icon class="step-arrow"><Right /></el-icon>
          <div :class="['step', currentStep >= 2 ? 'active' : '']">
            <span class="step-num">3</span><span>保存测试点集</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 主体区域：左右分栏 -->
    <div class="main-body">
      <!-- 左侧：知识库文档列表 -->
      <div class="doc-sidebar" :class="{ collapsed: sidebarCollapsed }">
        <div class="sidebar-header">
          <h4 v-if="!sidebarCollapsed">
            <el-icon><FolderOpened /></el-icon> 知识库文档
          </h4>
          <el-button
            text
            size="small"
            @click="sidebarCollapsed = !sidebarCollapsed"
            :title="sidebarCollapsed ? '展开文档列表' : '收起文档列表'"
          >
            <el-icon><ArrowLeft v-if="!sidebarCollapsed" /><ArrowRight v-else /></el-icon>
          </el-button>
        </div>
        <template v-if="!sidebarCollapsed">
          <div class="sidebar-search">
            <el-input
              v-model="docKeyword"
              placeholder="搜索文档..."
              size="small"
              clearable
              :prefix-icon="Search"
            />
          </div>
          <div class="sidebar-tip">
            <el-icon><InfoFilled /></el-icon>
            <span>勾选文档作为 AI 生成输入源</span>
          </div>
          <div class="doc-list" v-loading="loadingDocs">
            <template v-if="filteredDocs.length > 0">
              <div
                v-for="doc in filteredDocs"
                :key="doc.id"
                class="doc-item"
                :class="{ selected: selectedDocIds.includes(doc.id) }"
                @click="toggleDocSelection(doc.id)"
              >
                <el-checkbox
                  :model-value="selectedDocIds.includes(doc.id)"
                  @change="toggleDocSelection(doc.id)"
                  @click.stop
                  size="small"
                />
                <div class="doc-item-info">
                  <span class="doc-item-title" :title="doc.title">{{ doc.title }}</span>
                  <div class="doc-item-meta">
                    <el-tag size="small" :type="doc.doc_type === 'file' ? 'primary' : 'success'" effect="plain">
                      {{ doc.doc_type === 'file' ? '文件' : '文本' }}
                    </el-tag>
                    <span class="doc-item-time">{{ formatDocTime(doc.created_at) }}</span>
                  </div>
                </div>
              </div>
            </template>
            <el-empty v-else description="暂无文档" :image-size="48">
              <template #description>
                <span style="font-size: 12px; color: #9ca3af;">上传文件后将自动入库</span>
              </template>
            </el-empty>
          </div>
          <div class="sidebar-footer">
            <el-button size="small" text @click="loadKnowledgeDocs">
              <el-icon><Refresh /></el-icon> 刷新
            </el-button>
            <el-tag v-if="selectedDocIds.length > 0" size="small" type="success" effect="plain">
              已选 {{ selectedDocIds.length }} 个
            </el-tag>
          </div>
        </template>
      </div>

      <!-- 右侧：主内容区 -->
      <div class="main-content">
        <!-- Step 0: 输入区域 -->
        <div v-if="currentStep === 0" class="input-section">
          <el-card class="input-card">
            <!-- 已选知识库文档提示 -->
            <div v-if="selectedDocIds.length > 0" class="selected-docs-bar">
              <el-icon style="color: #67c23a;"><CircleCheckFilled /></el-icon>
              <span>已从知识库选择 <b>{{ selectedDocIds.length }}</b> 个文档作为输入源</span>
              <el-button size="small" type="danger" plain @click="selectedDocIds = []">清除选择</el-button>
            </div>

            <div class="input-modes">
              <el-radio-group v-model="inputMode" size="large">
                <el-radio-button value="file">
                  <el-icon><UploadFilled /></el-icon> 导入文档
                </el-radio-button>
                <el-radio-button value="text">
                  <el-icon><Edit /></el-icon> 自由输入
                </el-radio-button>
              </el-radio-group>
            </div>

            <!-- 导入文档 -->
            <div v-if="inputMode === 'file'" class="input-area">
              <div v-if="uploadedFiles.length" class="file-card-list">
                <div v-for="(file, idx) in uploadedFiles" :key="idx" class="file-card">
                  <div class="file-card-inner">
                    <el-icon class="file-card-icon" :style="{ color: fileIconColor(file.name) }">
                      <VideoPlay v-if="isVideoFile(file.name)" />
                      <Picture v-else-if="isImageFile(file.name)" />
                      <Document v-else />
                    </el-icon>
                    <div class="file-card-info">
                      <span class="file-card-name">{{ file.name }}</span>
                      <span class="file-card-size">{{ formatFileSize(file.size) }}</span>
                      <el-tag v-if="isVideoFile(file.name)" size="small" type="warning" effect="plain" class="file-type-tag">视频</el-tag>
                      <el-tag v-else-if="isImageFile(file.name)" size="small" type="success" effect="plain" class="file-type-tag">图片</el-tag>
                    </div>
                    <span class="file-card-remove" @click.stop="handleRemoveSingleFile(idx)">&times;</span>
                  </div>
                </div>
              </div>
              <el-upload
                ref="uploadRef"
                :auto-upload="false"
                :show-file-list="false"
                :on-change="handleFileChange"
                accept=".md,.txt,.pdf,.docx,.doc,.png,.jpg,.jpeg,.gif,.webp,.mp4,.mov,.avi,.webm"
                multiple drag
                class="file-upload-area"
                :class="{ 'file-upload-compact': uploadedFiles.length > 0 }"
              >
                <template v-if="uploadedFiles.length === 0">
                  <el-icon class="el-icon--upload" :size="48"><UploadFilled /></el-icon>
                  <div class="el-upload__text">拖拽<b>需求文档</b>、<b>技术文档</b>、截图或视频到这里，或<em>点击上传</em></div>
                  <div class="upload-ai-hint">
                    <el-icon style="color: #67c23a;"><Picture /></el-icon>
                    <span>支持多模态 AI 识别 — 自动提取文档内嵌图片、架构图、流程图等视觉内容辅助分析</span>
                  </div>
                </template>
                <template v-else>
                  <el-icon class="el-icon--upload" :size="24"><UploadFilled /></el-icon>
                  <div class="el-upload__text" style="font-size: 13px;">继续添加文件</div>
                </template>
                <template #tip>
                  <div class="el-upload__tip">支持需求文档 / 技术文档(.md/.txt/.pdf/.docx)、截图(.png/.jpg)、评审视频(.mp4/.mov) | 最大 20MB</div>
                </template>
              </el-upload>
              <el-input
                v-model="supplementText"
                type="textarea"
                :rows="3"
                placeholder="（可选）补充说明文字"
                maxlength="3000"
                show-word-limit
                resize="vertical"
                style="margin-top: 12px;"
              />
            </div>

            <!-- 自由输入 -->
            <div v-else class="input-area">
              <el-input
                v-model="inputText"
                type="textarea"
                :rows="12"
                placeholder="粘贴需求描述、PRD 文档、用户故事等内容...

AI 将自动：
1. 分析需求内容
2. 提取测试点（正向验证、边界测试、异常处理）
3. 保存到测试点集"
                maxlength="10000"
                show-word-limit
                resize="vertical"
              />
            </div>

            <div class="action-buttons">
              <el-button
                type="primary"
                size="large"
                @click="handleGenerate"
                :disabled="!canStart"
                class="main-action-btn"
              >
                <el-icon><Aim /></el-icon>
                AI 生成测试点
              </el-button>
              <el-button
                type="success"
                size="large"
                @click="handleReqAnalysis"
                :disabled="!canStart"
                :loading="reqAnalysisLoading"
              >
                <el-icon><Share /></el-icon>
                需求分析
              </el-button>
              <el-button
                type="warning"
                size="large"
                @click="videoDialogVisible = true"
              >
                <el-icon><VideoCamera /></el-icon>
                评审视频分析
              </el-button>
              <el-button size="large" @click="handleReset">清空重置</el-button>
            </div>
          </el-card>

          <!-- 需求分析结果（弹窗形式） -->
          <el-dialog
            v-model="reqAnalysisMode"
            title="需求文档结构化分析"
            width="90%"
            top="3vh"
            :close-on-click-modal="false"
            destroy-on-close
            @close="handleReqAnalysisClose"
          >
            <div v-if="reqAnalysisLoading" class="req-loading">
              <el-icon class="is-loading" :size="32" style="color: #67c23a;"><Loading /></el-icon>
              <h3>AI 正在分析需求文档...</h3>
              <el-progress :percentage="reqAnalysisProgress" :stroke-width="10" color="#67c23a" style="margin: 16px 0; max-width: 500px;" />
              <p style="color: #909399;">{{ reqAnalysisMessage }}</p>
            </div>
            <RequirementAnalysis v-else-if="reqAnalysisResult" :data="reqAnalysisResult" />
            <el-empty v-else description="暂无分析结果" />
          </el-dialog>

          <!-- 评审视频分析弹窗 -->
          <el-dialog
            v-model="videoDialogVisible"
            title="评审视频 AI 分析"
            width="680px"
            :close-on-click-modal="false"
            destroy-on-close
            @close="handleVideoDialogClose"
          >
            <template v-if="!videoAnalyzing && !videoResult">
              <el-form label-position="top" style="max-width: 560px; margin: 0 auto;">
                <el-form-item label="评审类型">
                  <el-radio-group v-model="videoReviewType" size="large">
                    <el-radio-button value="requirement">需求评审</el-radio-button>
                    <el-radio-button value="technical">技术评审</el-radio-button>
                    <el-radio-button value="testcase">用例评审</el-radio-button>
                  </el-radio-group>
                </el-form-item>
                <el-form-item label="评审标题">
                  <el-input v-model="videoTitle" placeholder="例如：PayFi 收单需求评审" maxlength="100" show-word-limit />
                </el-form-item>
                <el-form-item label="上传视频">
                  <el-upload
                    ref="videoUploadRef"
                    :auto-upload="false"
                    :show-file-list="true"
                    :limit="1"
                    accept=".mp4,.mov,.avi,.mkv,.webm"
                    :on-change="handleVideoFileChange"
                    :on-remove="() => { videoFile = null }"
                    drag
                    class="video-upload-area"
                  >
                    <el-icon class="el-icon--upload" :size="36"><VideoPlay /></el-icon>
                    <div class="el-upload__text">拖拽评审视频到这里，或<em>点击选择</em></div>
                    <template #tip>
                      <div class="el-upload__tip">支持 .mp4、.mov、.avi、.webm 格式，最大 500MB | AI 自动提取关键帧并识别内容</div>
                    </template>
                  </el-upload>
                </el-form-item>
              </el-form>
            </template>

            <div v-else-if="videoAnalyzing" class="video-analyzing">
              <el-icon class="is-loading" :size="32" style="color: #e6a23c;"><Loading /></el-icon>
              <h3>AI 正在分析评审视频...</h3>
              <el-progress :percentage="videoProgress" :stroke-width="10" color="#e6a23c" style="margin: 16px 0; max-width: 500px;" />
              <p class="video-step-msg">{{ videoProgressMsg }}</p>
              <div class="video-analysis-steps">
                <div :class="['v-step', videoStep >= 1 ? 'active' : '']">1. 提取关键帧</div>
                <div :class="['v-step', videoStep >= 2 ? 'active' : '']">2. 视觉模型分析</div>
                <div :class="['v-step', videoStep >= 3 ? 'active' : '']">3. 生成评审汇总</div>
                <div :class="['v-step', videoStep >= 4 ? 'active' : '']">4. 同步知识库</div>
              </div>
            </div>

            <div v-else-if="videoResult" class="video-result">
              <el-alert type="success" :closable="false" style="margin-bottom: 16px;">
                <template #title>
                  分析完成！共提取 {{ videoResult.frame_count }} 个关键帧
                </template>
              </el-alert>
              <el-collapse v-model="videoResultExpanded">
                <el-collapse-item title="评审要点汇总" name="summary">
                  <div class="video-summary-text" v-html="videoResult.summary?.replace(/\n/g, '<br/>')"></div>
                </el-collapse-item>
                <el-collapse-item v-if="videoResult.key_decisions?.length" title="关键决策" name="decisions">
                  <ul class="video-list"><li v-for="(d, i) in videoResult.key_decisions" :key="i">{{ d }}</li></ul>
                </el-collapse-item>
                <el-collapse-item v-if="videoResult.action_items?.length" title="待办事项" name="actions">
                  <ul class="video-list"><li v-for="(a, i) in videoResult.action_items" :key="i">{{ a }}</li></ul>
                </el-collapse-item>
              </el-collapse>
              <div style="text-align: center; margin-top: 16px;">
                <el-button type="primary" @click="applyVideoResultToInput">将评审要点填入补充说明</el-button>
              </div>
            </div>

            <template #footer v-if="!videoAnalyzing && !videoResult">
              <el-button @click="videoDialogVisible = false">取消</el-button>
              <el-button type="warning" :disabled="!videoFile || !videoTitle.trim()" @click="handleStartVideoAnalysis">
                <el-icon><VideoCamera /></el-icon>
                开始分析
              </el-button>
            </template>
          </el-dialog>
        </div>

        <!-- Step 1: 生成进度 -->
        <div v-else-if="currentStep === 1" class="progress-section">
          <el-card class="progress-card">
            <div class="progress-header">
              <el-icon class="is-loading" :size="32" style="color: #8b5cf6;"><Loading /></el-icon>
              <h3>AI 正在生成测试点...</h3>
            </div>
            <el-steps :active="analysisStep" finish-status="success" align-center style="margin: 24px 0;">
              <el-step title="解析文档" />
              <el-step title="提取测试点" />
              <el-step title="保存测试点集" />
            </el-steps>
            <el-progress :percentage="progressPercent" :stroke-width="10" color="#8b5cf6" style="margin: 16px 0;" />
            <p class="progress-text">{{ progressMessage }}</p>
            <div v-if="streamText" class="stream-output">
              <pre ref="streamOutputRef">{{ streamText }}</pre>
            </div>
            <div style="text-align: center; margin-top: 16px;">
              <el-button @click="handleCancel">取消</el-button>
            </div>
          </el-card>
        </div>

        <!-- Step 2: 生成结果 -->
        <div v-else class="result-section">
          <el-card class="result-card">
            <template #header>
              <div class="card-header">
                <div class="card-title-edit">
                  <el-icon style="color: #8b5cf6; font-size: 18px; flex-shrink: 0;"><Aim /></el-icon>
                  <span class="card-title-label">测试点集：</span>
                  <el-input
                    v-model="editableName"
                    size="default"
                    class="name-edit-input"
                    maxlength="100"
                    show-word-limit
                    @blur="handleSaveName"
                    @keyup.enter="handleSaveName"
                  />
                  <el-button
                    v-if="nameChanged"
                    type="primary"
                    size="small"
                    @click="handleSaveName"
                    :loading="savingName"
                  >
                    保存
                  </el-button>
                  <el-tag v-if="nameSaved" type="success" size="small" effect="plain">已保存</el-tag>
                </div>
                <el-tag type="success" effect="dark">{{ latestResult?.total_points }} 个测试点</el-tag>
              </div>
            </template>

            <!-- 操作按钮区域（置顶） -->
            <div class="result-actions-top">
              <el-button @click="handleBackToInput">
                <el-icon><Back /></el-icon> 返回重新生成
              </el-button>
              <el-button type="primary" @click="goToCaseManage">
                <el-icon><FolderOpened /></el-icon> 前往功能用例管理
              </el-button>
              <el-button type="success" @click="handleGenerateCasesFromResult" :loading="generatingCases">
                <el-icon><MagicStick /></el-icon> 测试点生成测试用例
              </el-button>
              <el-button
                :loading="importingFeishu"
                @click="showFeishuDialog"
                style="background: #3370ff; color: white; border-color: #3370ff;"
              >
                <el-icon><Upload /></el-icon> 导入飞书用例集
              </el-button>
            </div>

            <!-- 测试点列表（可折叠） -->
            <div v-if="latestResult?.points?.length" class="points-section">
              <div class="points-section-header" @click="pointsCollapsed = !pointsCollapsed">
                <div class="points-section-title">
                  <el-icon :class="{ 'is-rotated': !pointsCollapsed }"><ArrowRight /></el-icon>
                  <span>测试点列表</span>
                  <el-tag size="small" type="info" effect="plain">{{ latestResult.points.length }} 个</el-tag>
                </div>
                <span class="collapse-hint">{{ pointsCollapsed ? '展开' : '收起' }}</span>
              </div>
              <el-collapse-transition>
                <div v-show="!pointsCollapsed" class="points-list">
                  <div v-for="(p, idx) in latestResult.points" :key="p.id" class="point-item">
                    <span class="point-index">{{ idx + 1 }}</span>
                    <span class="point-name">{{ p.name }}</span>
                    <el-tag v-if="p.point_type" size="small" :type="getPointTypeTag(p.point_type)">{{ p.point_type }}</el-tag>
                    <el-tag v-if="p.cases?.length" size="small" type="info" style="margin-left: auto;">预览：{{ p.cases.length }} 条用例</el-tag>
                  </div>
                </div>
              </el-collapse-transition>
            </div>
          </el-card>
        </div>
      </div>
    </div>

    <!-- 生成用例进度弹窗 -->
    <el-dialog
      v-model="caseGenVisible"
      :title="caseGenProgress < 100 ? 'AI 正在生成测试用例...' : '测试用例生成完成'"
      width="650px"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      :show-close="caseGenProgress >= 100"
      align-center
    >
      <div class="case-gen-dialog">
        <div class="case-gen-header">
          <el-icon v-if="caseGenProgress < 100" class="is-loading" :size="28" style="color: #8b5cf6;"><Loading /></el-icon>
          <el-icon v-else :size="28" style="color: #67c23a;"><CircleCheckFilled /></el-icon>
          <span class="case-gen-title">{{ caseGenProgress < 100 ? 'AI 并发生成中...' : '生成完成！' }}</span>
          <span v-if="caseGenProgress < 100" class="case-gen-elapsed">已耗时 {{ caseGenElapsed }}</span>
        </div>
        <div v-if="caseGenProgress < 100 && caseGenEstimate" class="case-gen-estimate">{{ caseGenEstimate }}</div>
        <el-progress
          :percentage="Math.round(caseGenProgress)"
          :stroke-width="12"
          :color="caseGenProgress >= 100 ? '#67c23a' : '#8b5cf6'"
          class="case-gen-progress-bar"
        />
        <p class="case-gen-msg">{{ caseGenMessage }}</p>
        <div class="case-gen-stream" ref="caseGenStreamRef">
          <pre v-if="caseGenStreamText">{{ caseGenStreamText.slice(-3000) }}</pre>
          <pre v-else class="case-gen-stream-placeholder">等待 AI 输出...</pre>
        </div>
      </div>
      <template #footer>
        <el-button v-if="caseGenProgress < 100" @click="handleCancelCaseGen" type="danger" plain>取消生成</el-button>
        <template v-else>
          <el-button
            :loading="importingFeishu"
            @click="showFeishuDialog"
            style="background: #3370ff; color: white; border-color: #3370ff;"
          >
            <el-icon><Upload /></el-icon> 导入飞书用例集
          </el-button>
          <el-button @click="caseGenVisible = false">关闭</el-button>
        </template>
      </template>
    </el-dialog>

    <!-- 飞书导入弹窗 -->
    <el-dialog v-model="feishuDialogVisible" title="导入飞书用例集" width="520px" :close-on-click-modal="false">
      <div style="background: #f0f7ff; border-radius: 8px; padding: 12px 16px; margin-bottom: 16px; font-size: 13px; line-height: 1.8; color: #303133;">
        <div style="font-weight: 600; margin-bottom: 6px; color: #3370ff;">获取 x-token 步骤：</div>
        <div>1. 打开 <a href="https://project.feishu.cn/research__development/meegoPlg/MII_642BBF6AC6C74001_test_management_use_case_set" target="_blank" style="color: #3370ff;">飞书用例管理页面</a></div>
        <div>2. 按 F12 打开 DevTools → Network 标签</div>
        <div>3. 在 Network 筛选框输入 <code style="background: #e8eaed; padding: 1px 4px; border-radius: 3px;">m-api</code></div>
        <div>4. 点击页面上任意操作触发请求，点击该请求</div>
        <div>5. 在 Request Headers 中找到 <code style="background: #e8eaed; padding: 1px 4px; border-radius: 3px;">x-token</code> 的值并复制</div>
      </div>
      <el-form label-position="top">
        <el-form-item label="飞书 x-token" required>
          <el-input
            v-model="feishuToken"
            type="textarea"
            :rows="3"
            placeholder="粘贴从飞书 DevTools 获取的 x-token 值..."
          />
        </el-form-item>
        <el-form-item label="用例集标题（可选）">
          <el-input v-model="feishuTitle" placeholder="不填则自动使用测试点集名称" />
        </el-form-item>
      </el-form>
      <div v-if="feishuResult" style="margin-top: 12px;">
        <el-alert type="success" :closable="false" show-icon>
          <template #title>
            导入成功！共 {{ feishuResult.case_count }} 条用例
          </template>
          <a :href="feishuResult.case_set_url" target="_blank" style="color: #3370ff;">
            点击查看飞书用例集 →
          </a>
        </el-alert>
      </div>
      <template #footer>
        <el-button @click="feishuDialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          :loading="importingFeishu"
          :disabled="!feishuToken.trim()"
          @click="handleImportFeishu"
          style="background: #3370ff; border-color: #3370ff;"
        >
          开始导入
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onActivated, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Aim, Loading, Right, Back, MagicStick, Share,
  UploadFilled, Document, Edit, FolderOpened,
  Search, Refresh, ArrowLeft, ArrowRight,
  InfoFilled, CircleCheckFilled, Picture, VideoPlay, VideoCamera, Upload,
} from '@element-plus/icons-vue'
import {
  aiGenerateTestpointsStream,
  generateCasesFromTestpoints,
  updateTestPointSet,
  requirementAnalysisStream,
  importCasesToFeishu,
} from '@/api/functional_test'
import RequirementAnalysis from '@/components/RequirementAnalysis.vue'
import {
  getKnowledgeDocuments,
  uploadFileDocument,
  uploadReviewVideo,
  analyzeReviewVideoStream,
} from '@/api/knowledge'
import { getProjectList } from '@/api/project'
import { useProjectStore } from '@/stores'

const router = useRouter()
const projectStore = useProjectStore()

const inputMode = ref('file')
const inputText = ref('')
const supplementText = ref('')
const uploadedFiles = ref([])
const uploadRef = ref()

const currentStep = ref(0)
const analysisStep = ref(0)
const progressPercent = ref(0)
const progressMessage = ref('')
const streamText = ref('')
const streamOutputRef = ref(null)

const latestResult = ref(null)
const generatingCases = ref(false)
let abortController = null

// 飞书导入相关
const feishuDialogVisible = ref(false)
const importingFeishu = ref(false)
const feishuToken = ref(localStorage.getItem('feishu_x_token') || '')
const feishuTitle = ref('')
const feishuResult = ref(null)

// 需求分析相关
const reqAnalysisMode = ref(false)
const reqAnalysisLoading = ref(false)
const reqAnalysisProgress = ref(0)
const reqAnalysisMessage = ref('')
const reqAnalysisResult = ref(null)
let reqAbortController = null

// 评审视频分析相关
const videoDialogVisible = ref(false)
const videoReviewType = ref('requirement')
const videoTitle = ref('')
const videoFile = ref(null)
const videoUploadRef = ref()
const videoAnalyzing = ref(false)
const videoProgress = ref(0)
const videoProgressMsg = ref('')
const videoStep = ref(0)
const videoResult = ref(null)
const videoResultExpanded = ref(['summary', 'decisions', 'actions'])
let videoAbortController = null

const sidebarCollapsed = ref(false)
const loadingDocs = ref(false)
const knowledgeDocs = ref([])
const docKeyword = ref('')
const selectedDocIds = ref([])

const editableName = ref('')
const savingName = ref(false)
const nameSaved = ref(false)
const originalName = ref('')
const pointsCollapsed = ref(false)

const caseGenVisible = ref(false)
const caseGenProgress = ref(0)
const caseGenMessage = ref('')
const caseGenStreamText = ref('')
const caseGenStreamRef = ref(null)
const caseGenElapsed = ref('0秒')
const caseGenEstimate = ref('')
let caseGenAbortController = null
let caseGenElapsedTimer = null
let caseGenSmoothTimer = null
let caseGenTargetProgress = 0
let caseGenStartTime = 0

const projectId = computed(() => projectStore.currentProject?.id)

const canStart = computed(() => {
  if (selectedDocIds.value.length > 0) return true
  if (inputMode.value === 'text') return inputText.value.trim().length > 0
  return uploadedFiles.value.length > 0 || supplementText.value.trim().length > 0
})

const nameChanged = computed(() => editableName.value !== originalName.value)

const filteredDocs = computed(() => {
  if (!docKeyword.value.trim()) return knowledgeDocs.value
  const kw = docKeyword.value.trim().toLowerCase()
  return knowledgeDocs.value.filter(d => d.title?.toLowerCase().includes(kw))
})

const isVideoFile = (name) => /\.(mp4|avi|mov|mkv|webm)$/i.test(name)
const isImageFile = (name) => /\.(png|jpg|jpeg|gif|webp|bmp|svg)$/i.test(name)
const fileIconColor = (name) => {
  if (isVideoFile(name)) return '#e6a23c'
  if (isImageFile(name)) return '#67c23a'
  return '#8b5cf6'
}

const getPointTypeTag = (type) => {
  const map = { '正向验证': 'success', '边界测试': 'warning', '异常处理': 'danger' }
  return map[type] || 'info'
}

const formatFileSize = (bytes) => {
  if (!bytes) return '0 B'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

const formatDocTime = (t) => {
  if (!t) return ''
  const d = new Date(t)
  return `${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

const loadKnowledgeDocs = async () => {
  if (!projectId.value) return
  loadingDocs.value = true
  try {
    const res = await getKnowledgeDocuments(projectId.value, { page: 1, page_size: 200 })
    const data = res.data || res
    knowledgeDocs.value = (data.documents || []).filter(d => d.status === 'completed')
  } catch (e) {
    console.error('加载知识库文档失败:', e)
  } finally {
    loadingDocs.value = false
  }
}

const toggleDocSelection = (docId) => {
  const idx = selectedDocIds.value.indexOf(docId)
  if (idx >= 0) {
    selectedDocIds.value.splice(idx, 1)
  } else {
    selectedDocIds.value.push(docId)
  }
}

const handleFileChange = async (file) => {
  const raw = file.raw || file
  const exists = uploadedFiles.value.some(f => f.name === raw.name && f.size === raw.size)
  if (!exists) {
    uploadedFiles.value.push(raw)
    await autoUploadSingleFile(raw)
  }
}
const handleRemoveSingleFile = (idx) => {
  uploadedFiles.value.splice(idx, 1)
  if (uploadRef.value) uploadRef.value.clearFiles()
}

const autoUploadSingleFile = async (file) => {
  if (!projectId.value) return
  try {
    const formData = new FormData()
    formData.append('file', file)
    await uploadFileDocument(projectId.value, formData)
    ElMessage.success(`「${file.name}」已同步到知识库`)
    await loadKnowledgeDocs()
  } catch (e) {
    console.warn(`文件 ${file.name} 入库知识库失败:`, e)
  }
}

const processSSEStream = async (response, onData, timeoutMs = 120000) => {
  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  while (true) {
    const timeoutPromise = new Promise((_, reject) =>
      setTimeout(() => reject(new Error('SSE 流超时，服务器长时间无响应')), timeoutMs)
    )
    const { value, done } = await Promise.race([reader.read(), timeoutPromise])
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''
    for (const line of lines) {
      if (!line.startsWith('data: ')) continue
      const dataStr = line.slice(6).trim()
      if (!dataStr || dataStr === '[DONE]') continue
      try { onData(JSON.parse(dataStr)) } catch { /* ignore */ }
    }
  }
}

const autoScrollStream = () => {
  nextTick(() => {
    if (streamOutputRef.value) streamOutputRef.value.scrollTop = streamOutputRef.value.scrollHeight
  })
}

const handleGenerate = async () => {
  if (!projectId.value) {
    ElMessage.error('请先选择项目')
    return
  }

  currentStep.value = 1
  analysisStep.value = 0
  progressPercent.value = 5
  progressMessage.value = '正在解析文档内容...'
  streamText.value = ''
  latestResult.value = null
  nameSaved.value = false
  abortController = new AbortController()

  try {
    const formData = new FormData()
    if (inputMode.value === 'file') {
      for (const f of uploadedFiles.value) formData.append('files', f)
      if (supplementText.value.trim()) formData.append('text', supplementText.value.trim())
    } else {
      formData.append('text', inputText.value.trim())
    }

    if (selectedDocIds.value.length > 0) {
      formData.append('knowledge_doc_ids', selectedDocIds.value.join(','))
    }

    const response = await aiGenerateTestpointsStream(projectId.value, formData, abortController.signal)
    if (!response.ok) {
      const err = await response.json().catch(() => ({}))
      throw new Error(err.detail || `HTTP ${response.status}`)
    }

    analysisStep.value = 1
    progressPercent.value = 15
    progressMessage.value = 'AI 正在生成测试点...'

    await processSSEStream(response, (data) => {
      if (data.type === 'chunk') {
        streamText.value += data.content
        progressPercent.value = Math.min(data.progress || progressPercent.value + 2, 70)
        autoScrollStream()
      } else if (data.type === 'progress') {
        progressMessage.value = data.message || ''
        progressPercent.value = data.progress || progressPercent.value
        if (data.progress >= 75) analysisStep.value = 2
      } else if (data.type === 'result') {
        latestResult.value = data.data
        editableName.value = data.data?.test_point_set_name || ''
        originalName.value = data.data?.test_point_set_name || ''
        analysisStep.value = 2
        progressPercent.value = 100
      } else if (data.type === 'error') {
        throw new Error(data.message || 'AI生成失败')
      }
    })

    if (!latestResult.value) throw new Error('未获取到生成结果')
    currentStep.value = 2
    ElMessage.success(`生成完成！共 ${latestResult.value.total_points} 个测试点已保存`)
  } catch (error) {
    if (error.name === 'AbortError') return
    console.error('生成失败:', error)
    ElMessage.error(error.message || '生成失败')
    currentStep.value = 0
  }
}

const handleSaveName = async () => {
  if (!nameChanged.value || !latestResult.value?.test_point_set_id || !projectId.value) return
  if (!editableName.value.trim()) {
    ElMessage.warning('测试点集名称不能为空')
    editableName.value = originalName.value
    return
  }
  savingName.value = true
  try {
    await updateTestPointSet(projectId.value, latestResult.value.test_point_set_id, {
      name: editableName.value.trim()
    })
    originalName.value = editableName.value.trim()
    latestResult.value.test_point_set_name = editableName.value.trim()
    nameSaved.value = true
    ElMessage.success('名称已更新')
    setTimeout(() => { nameSaved.value = false }, 3000)
  } catch (e) {
    ElMessage.error('更新名称失败')
  } finally {
    savingName.value = false
  }
}

const stopCaseGenTimer = () => {
  if (caseGenElapsedTimer) {
    clearInterval(caseGenElapsedTimer)
    caseGenElapsedTimer = null
  }
  if (caseGenSmoothTimer) {
    clearInterval(caseGenSmoothTimer)
    caseGenSmoothTimer = null
  }
}

const startSmoothProgress = () => {
  caseGenSmoothTimer = setInterval(() => {
    const current = caseGenProgress.value
    if (current >= 100) {
      clearInterval(caseGenSmoothTimer)
      caseGenSmoothTimer = null
      return
    }
    const target = caseGenTargetProgress
    if (current < target) {
      caseGenProgress.value = Math.min(current + Math.max(0.3, (target - current) * 0.15), target)
    } else if (current < 70) {
      caseGenProgress.value = Math.min(current + 0.08, 70)
    }
  }, 300)
}

const updateCaseGenEstimate = () => {
  const elapsed = (Date.now() - caseGenStartTime) / 1000
  const progress = caseGenProgress.value
  if (progress > 5 && progress < 95) {
    const totalEstimate = elapsed / (progress / 100)
    const remaining = Math.max(0, totalEstimate - elapsed)
    if (remaining < 60) {
      caseGenEstimate.value = `预计剩余 ${Math.ceil(remaining)} 秒`
    } else {
      caseGenEstimate.value = `预计剩余 ${Math.floor(remaining / 60)}分${Math.ceil(remaining % 60)}秒`
    }
  } else if (progress >= 95) {
    caseGenEstimate.value = '即将完成...'
  } else {
    caseGenEstimate.value = '正在预估...'
  }
}

const setCaseGenTarget = (target) => {
  caseGenTargetProgress = Math.max(caseGenTargetProgress, Math.min(target, 99))
}

const handleGenerateCasesFromResult = async () => {
  if (!latestResult.value?.test_point_set_id || !projectId.value) return
  generatingCases.value = true
  caseGenVisible.value = true
  caseGenProgress.value = 0
  caseGenTargetProgress = 0
  caseGenMessage.value = '正在准备生成测试用例...'
  caseGenStreamText.value = ''
  caseGenElapsed.value = '0秒'
  caseGenEstimate.value = '正在预估...'
  caseGenAbortController = new AbortController()

  caseGenStartTime = Date.now()
  stopCaseGenTimer()
  caseGenElapsedTimer = setInterval(() => {
    const sec = Math.floor((Date.now() - caseGenStartTime) / 1000)
    caseGenElapsed.value = sec < 60 ? `${sec}秒` : `${Math.floor(sec / 60)}分${sec % 60}秒`
    updateCaseGenEstimate()
  }, 1000)
  startSmoothProgress()

  try {
    const response = await generateCasesFromTestpoints(
      projectId.value,
      latestResult.value.test_point_set_id,
      caseGenAbortController.signal
    )
    if (!response.ok) {
      const err = await response.json().catch(() => ({}))
      throw new Error(err.detail || `HTTP ${response.status}`)
    }

    let caseSetId = null
    await processSSEStream(response, (data) => {
      if (data.type === 'chunk') {
        caseGenStreamText.value += data.content
        const newProgress = data.progress || caseGenTargetProgress
        setCaseGenTarget(Math.min(newProgress, 74))
        if (data.batch && data.total_batches) {
          caseGenMessage.value = `正在生成第 ${data.batch}/${data.total_batches} 批...`
        }
        nextTick(() => {
          if (caseGenStreamRef.value) caseGenStreamRef.value.scrollTop = caseGenStreamRef.value.scrollHeight
        })
      } else if (data.type === 'progress') {
        caseGenMessage.value = data.message || ''
        const newProgress = data.progress || caseGenTargetProgress
        setCaseGenTarget(newProgress)
      } else if (data.type === 'result') {
        caseSetId = data.data?.case_set_id
        caseGenTargetProgress = 100
        caseGenProgress.value = 100
        caseGenMessage.value = `生成完成！共 ${data.data?.total_cases} 条用例`
        caseGenEstimate.value = ''
        stopCaseGenTimer()
        ElMessage.success(`用例集生成完成！共 ${data.data?.total_cases} 条用例`)
      } else if (data.type === 'done') {
        caseGenTargetProgress = 100
        caseGenProgress.value = 100
        caseGenEstimate.value = ''
        stopCaseGenTimer()
      } else if (data.type === 'error') {
        throw new Error(data.message || '生成失败')
      }
    }, 600000)

    if (caseSetId) {
      setTimeout(() => {
        caseGenVisible.value = false
        router.push({ name: 'FunctionTestCaseSetDetail', params: { caseSetId } })
      }, 1500)
    }
  } catch (e) {
    if (e.name === 'AbortError') {
      caseGenMessage.value = '已取消生成'
      caseGenProgress.value = 0
      caseGenEstimate.value = ''
      setTimeout(() => { caseGenVisible.value = false }, 1000)
      return
    }
    caseGenMessage.value = `生成失败: ${e.message}`
    caseGenEstimate.value = ''
    ElMessage.error(e.message || '生成用例集失败')
  } finally {
    generatingCases.value = false
    caseGenAbortController = null
    stopCaseGenTimer()
  }
}

const handleCancelCaseGen = () => {
  if (caseGenAbortController) caseGenAbortController.abort()
}

const handleCancel = () => {
  if (abortController) abortController.abort()
  currentStep.value = 0
}

const handleBackToInput = () => { currentStep.value = 0 }

// ===== 需求分析 =====
const handleReqAnalysis = async () => {
  if (!projectId.value) {
    ElMessage.warning('请先选择项目')
    return
  }
  reqAnalysisMode.value = true
  reqAnalysisLoading.value = true
  reqAnalysisProgress.value = 0
  reqAnalysisMessage.value = '正在准备...'
  reqAnalysisResult.value = null

  const formData = new FormData()
  if (inputMode.value === 'file') {
    for (const f of uploadedFiles.value) formData.append('files', f)
    if (supplementText.value.trim()) formData.append('text', supplementText.value.trim())
  } else {
    formData.append('text', inputText.value.trim())
  }
  if (selectedDocIds.value.length > 0) {
    formData.append('knowledge_doc_ids', selectedDocIds.value.join(','))
  }

  reqAbortController = new AbortController()
  try {
    const response = await requirementAnalysisStream(projectId.value, formData, reqAbortController.signal)
    if (!response.ok) {
      const err = await response.text()
      throw new Error(err || '请求失败')
    }
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''
      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        try {
          const evt = JSON.parse(line.slice(6))
          if (evt.type === 'progress') {
            reqAnalysisProgress.value = evt.progress || 0
            reqAnalysisMessage.value = evt.message || ''
          } else if (evt.type === 'chunk') {
            reqAnalysisProgress.value = evt.progress || reqAnalysisProgress.value
          } else if (evt.type === 'result') {
            reqAnalysisResult.value = evt.data
            reqAnalysisLoading.value = false
          } else if (evt.type === 'error') {
            ElMessage.error(evt.message || '分析失败')
            reqAnalysisLoading.value = false
          }
        } catch {}
      }
    }
  } catch (e) {
    if (e.name !== 'AbortError') {
      ElMessage.error(e.message || '需求分析失败')
    }
  } finally {
    reqAnalysisLoading.value = false
    reqAbortController = null
  }
}

const handleReqAnalysisClose = () => {
  if (reqAbortController) reqAbortController.abort()
  reqAnalysisLoading.value = false
}

// ===== 评审视频分析 =====
const handleVideoFileChange = (file) => {
  videoFile.value = file.raw || file
}

const handleStartVideoAnalysis = async () => {
  if (!projectId.value) {
    ElMessage.warning('请先选择项目')
    return
  }
  if (!videoFile.value || !videoTitle.value.trim()) return

  videoAnalyzing.value = true
  videoProgress.value = 0
  videoProgressMsg.value = '正在上传视频...'
  videoStep.value = 0
  videoResult.value = null

  try {
    const formData = new FormData()
    formData.append('file', videoFile.value)
    formData.append('title', videoTitle.value.trim())
    formData.append('review_type', videoReviewType.value)

    const uploadRes = await uploadReviewVideo(projectId.value, formData)
    const reviewId = uploadRes.data?.id || uploadRes.id
    if (!reviewId) throw new Error('视频上传失败，未获取到记录ID')

    videoProgress.value = 5
    videoProgressMsg.value = '上传完成，开始分析...'
    videoStep.value = 1

    videoAbortController = new AbortController()
    const response = await analyzeReviewVideoStream(projectId.value, reviewId, videoAbortController.signal)
    if (!response.ok) {
      const err = await response.text()
      throw new Error(err || '分析请求失败')
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''
      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        try {
          const evt = JSON.parse(line.slice(6))
          if (evt.type === 'progress') {
            videoProgress.value = evt.progress || videoProgress.value
            videoProgressMsg.value = evt.message || ''
            const stepMap = { extracting: 1, analyzing: 2, summarizing: 3, syncing: 4, done: 4 }
            videoStep.value = stepMap[evt.step] || videoStep.value
          } else if (evt.type === 'result') {
            videoResult.value = evt.data
            videoAnalyzing.value = false
          } else if (evt.type === 'error') {
            ElMessage.error(evt.message || '视频分析失败')
            videoAnalyzing.value = false
          }
        } catch {}
      }
    }
  } catch (e) {
    if (e.name !== 'AbortError') {
      ElMessage.error(e.message || '评审视频分析失败')
    }
  } finally {
    videoAnalyzing.value = false
    videoAbortController = null
  }
}

const handleVideoDialogClose = () => {
  if (videoAbortController) videoAbortController.abort()
  videoAnalyzing.value = false
  videoResult.value = null
  videoFile.value = null
  videoTitle.value = ''
  videoProgress.value = 0
  videoStep.value = 0
}

const applyVideoResultToInput = () => {
  if (!videoResult.value?.summary) return
  const reviewTypeNames = { requirement: '需求评审', technical: '技术评审', testcase: '用例评审' }
  const typeName = reviewTypeNames[videoReviewType.value] || '评审'
  const text = `【${typeName}：${videoTitle.value}】\n${videoResult.value.summary}`

  if (inputMode.value === 'file') {
    supplementText.value = supplementText.value
      ? supplementText.value + '\n\n' + text
      : text
  } else {
    inputText.value = inputText.value
      ? inputText.value + '\n\n' + text
      : text
  }
  videoDialogVisible.value = false
  ElMessage.success('评审要点已填入补充说明，可结合需求文档一起生成测试点')
}

const handleReset = () => {
  inputText.value = ''
  supplementText.value = ''
  uploadedFiles.value = []
  latestResult.value = null
  streamText.value = ''
  currentStep.value = 0
  nameSaved.value = false
  if (uploadRef.value) uploadRef.value.clearFiles()
}

const goToCaseManage = () => {
  router.push({ name: 'FunctionTestCase' })
}

watch(streamText, () => autoScrollStream())

const ensureProject = async () => {
  if (projectId.value) return true
  try {
    const res = await getProjectList({ page: 1, page_size: 1 })
    const list = res.data?.projects || res.data?.list || []
    if (list.length > 0) {
      projectStore.setCurrentProject(list[0])
      return true
    }
  } catch (e) {
    console.error('自动获取项目失败:', e)
  }
  return false
}

const initPage = async () => {
  if (!projectId.value) await ensureProject()
  if (projectId.value) loadKnowledgeDocs()
}

onMounted(() => initPage())

onActivated(() => initPage())

// ===== 飞书导入 =====
const showFeishuDialog = () => {
  feishuResult.value = null
  feishuTitle.value = editableName.value || ''
  feishuDialogVisible.value = true
}

const handleImportFeishu = async () => {
  if (!feishuToken.value.trim()) {
    ElMessage.warning('请输入飞书 x-token')
    return
  }
  if (!projectId.value) {
    ElMessage.warning('请先选择项目')
    return
  }

  localStorage.setItem('feishu_x_token', feishuToken.value.trim())
  importingFeishu.value = true
  feishuResult.value = null

  try {
    const cases = []
    const points = latestResult.value?.points || []
    for (const point of points) {
      if (point.cases && point.cases.length > 0) {
        for (const c of point.cases) {
          const steps = []
          const expected = []
          if (c.test_steps) {
            for (const step of c.test_steps) {
              if (typeof step === 'object' && step !== null) {
                steps.push(step.action || step.step || String(step))
                expected.push(step.expected || '')
              } else {
                steps.push(String(step))
              }
            }
          }
          if (!expected.length || expected.every(e => !e)) {
            if (c.expected_result) {
              if (Array.isArray(c.expected_result)) {
                expected.splice(0, expected.length, ...c.expected_result)
              } else {
                expected.splice(0, expected.length, String(c.expected_result))
              }
            }
          }
          cases.push({
            case_title: c.case_name || c.name || point.name,
            module: c.scenario || point.point_type || '未分类',
            priority: c.priority ? `P${c.priority}` : 'P2',
            precondition: c.preconditions || c.precondition || '',
            test_steps: steps.length ? steps : ['执行测试'],
            expected_results: expected.length ? expected : ['验证通过'],
          })
        }
      } else {
        cases.push({
          case_title: point.name,
          module: point.point_type || '未分类',
          priority: 'P2',
          precondition: '',
          test_steps: ['执行测试'],
          expected_results: ['验证通过'],
        })
      }
    }

    if (!cases.length) {
      ElMessage.warning('没有可导入的用例，请先生成测试用例')
      return
    }

    const res = await importCasesToFeishu(projectId.value, {
      cases,
      title: feishuTitle.value.trim() || undefined,
      feishu_token: feishuToken.value.trim(),
    })
    feishuResult.value = res.data
    ElMessage.success(`导入成功！共 ${res.data.case_count} 条用例`)
  } catch (e) {
    console.error('飞书导入失败:', e)
    const msg = e.response?.data?.detail || e.message || '导入失败'
    ElMessage.error(msg)
  } finally {
    importingFeishu.value = false
  }
}
</script>

<style scoped>
.ai-testpoint-page {
  padding: 20px;
  background: #f8fafc;
  min-height: 100%;
}

.page-header { margin-bottom: 20px; }
.header-content {
  background: white;
  padding: 20px 24px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
}
.title-section h2 {
  display: flex;
  align-items: center;
  color: #1f2937;
  margin: 0 0 4px 0;
  font-size: 20px;
}
.subtitle { color: #6b7280; margin: 0; font-size: 13px; }

.flow-steps { display: flex; align-items: center; gap: 8px; }
.flow-steps .step {
  display: flex; align-items: center; gap: 6px;
  padding: 6px 14px; border-radius: 20px;
  background: #f3f4f6; color: #9ca3af;
  font-size: 13px; font-weight: 500; transition: all 0.3s;
}
.flow-steps .step.active {
  background: linear-gradient(135deg, #8b5cf6, #7c3aed); color: white;
}
.flow-steps .step-num {
  width: 20px; height: 20px; border-radius: 50%;
  background: rgba(255,255,255,0.3);
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 700;
}
.step-arrow { color: #d1d5db; font-size: 14px; }

/* 左右分栏布局 */
.main-body {
  display: flex;
  gap: 16px;
  align-items: flex-start;
}

/* 左侧知识库面板 */
.doc-sidebar {
  width: 300px;
  min-width: 300px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  display: flex;
  flex-direction: column;
  max-height: calc(100vh - 220px);
  transition: all 0.3s ease;
}
.doc-sidebar.collapsed {
  width: 48px;
  min-width: 48px;
}
.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px 10px;
  border-bottom: 1px solid #f0f0f0;
}
.sidebar-header h4 {
  margin: 0;
  font-size: 14px;
  color: #1f2937;
  display: flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
}
.sidebar-search {
  padding: 10px 12px 0;
}
.sidebar-tip {
  padding: 6px 12px;
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: #9ca3af;
}
.doc-list {
  flex: 1;
  overflow-y: auto;
  padding: 4px 8px;
  min-height: 100px;
}
.doc-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 10px 8px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid transparent;
}
.doc-item:hover {
  background: #f8fafc;
}
.doc-item.selected {
  background: #f0f7ff;
  border-color: #c6d9f1;
}
.doc-item-info {
  flex: 1;
  min-width: 0;
}
.doc-item-title {
  font-size: 13px;
  font-weight: 500;
  color: #1f2937;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  line-height: 1.4;
  word-break: break-all;
}
.doc-item-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 4px;
}
.doc-item-time {
  font-size: 11px;
  color: #9ca3af;
}
.sidebar-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  border-top: 1px solid #f0f0f0;
}

/* 右侧主内容 */
.main-content {
  flex: 1;
  min-width: 0;
}

.selected-docs-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  background: #f0f9eb;
  border: 1px solid #e1f3d8;
  border-radius: 8px;
  margin-bottom: 16px;
  font-size: 13px;
  color: #67c23a;
}
.selected-docs-bar .el-button {
  margin-left: auto;
}

.input-card { max-width: 800px; margin: 0 auto; }
.input-modes { text-align: center; margin-bottom: 20px; }
.input-area { min-height: 280px; }
.file-card-list { display: flex; flex-direction: column; gap: 8px; margin-bottom: 12px; }
.file-card-inner {
  display: flex; align-items: center; gap: 12px;
  background: #f8fafc; border: 1px solid #e2e8f0;
  border-radius: 10px; padding: 14px 18px; transition: all 0.2s;
}
.file-card-inner:hover { border-color: #c4b5fd; background: #faf5ff; }
.file-card-icon { font-size: 28px; color: #8b5cf6; flex-shrink: 0; }
.file-card-info { flex: 1; min-width: 0; display: flex; align-items: baseline; gap: 10px; }
.file-card-name { font-weight: 600; font-size: 14px; color: #1e293b; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.file-card-size { font-size: 12px; color: #94a3b8; flex-shrink: 0; }
.file-card-remove {
  width: 28px; height: 28px; border-radius: 50%;
  background: #fee2e2; color: #ef4444; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  font-size: 18px; font-weight: 700; border: 1px solid #fecaca; transition: all 0.2s;
}
.file-card-remove:hover { background: #ef4444; color: #fff; border-color: #ef4444; }
.file-type-tag { flex-shrink: 0; font-size: 11px; }

.action-buttons {
  display: flex; gap: 12px; margin-top: 24px; padding-top: 16px;
  border-top: 1px solid #f0f0f0; justify-content: center;
}
.main-action-btn {
  padding: 12px 32px; font-size: 16px; font-weight: 600;
  background: linear-gradient(135deg, #8b5cf6, #7c3aed); border: none;
}
.main-action-btn:hover { background: linear-gradient(135deg, #7c3aed, #6d28d9); }

.progress-card { max-width: 700px; margin: 0 auto; }
.progress-header { display: flex; align-items: center; gap: 12px; justify-content: center; margin-bottom: 8px; }
.progress-header h3 { margin: 0; color: #1f2937; font-size: 18px; }
.progress-text { text-align: center; color: #8b5cf6; font-size: 14px; font-weight: 500; }
.stream-output {
  background: #1a1a2e; color: #a5f3fc; border-radius: 8px;
  padding: 14px; max-height: 280px; overflow-y: auto; margin-top: 16px;
}
.stream-output pre {
  margin: 0; white-space: pre-wrap; word-break: break-word;
  font-family: 'Monaco', 'Menlo', monospace; font-size: 13px; line-height: 1.6;
}

.result-card { max-width: 800px; margin: 0 auto; }
.card-header {
  display: flex; justify-content: space-between; align-items: center;
  flex-wrap: wrap; gap: 8px;
}
.card-title-edit {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}
.card-title-label {
  font-size: 15px;
  font-weight: 600;
  color: #1f2937;
  white-space: nowrap;
}
.name-edit-input {
  flex: 1;
  min-width: 200px;
  max-width: 600px;
}
:deep(.name-edit-input .el-input__inner) {
  font-size: 15px;
  font-weight: 600;
  color: #1f2937;
}

.points-list { display: flex; flex-direction: column; gap: 8px; }
.point-item {
  display: flex; align-items: center; gap: 10px;
  padding: 12px 16px; background: #f8fafc;
  border-radius: 8px; border: 1px solid #e2e8f0;
}
.point-index {
  width: 28px; height: 28px; border-radius: 50%;
  background: linear-gradient(135deg, #8b5cf6, #7c3aed);
  color: white; display: flex; align-items: center; justify-content: center;
  font-size: 13px; font-weight: 700; flex-shrink: 0;
}
.point-name { flex: 1; font-size: 14px; color: #374151; font-weight: 500; }

.result-actions-top {
  display: flex; gap: 12px; justify-content: center;
  margin-bottom: 20px; padding-bottom: 16px; border-bottom: 1px solid #f0f0f0;
}

.points-section {
  margin-top: 4px;
}
.points-section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  background: #f8fafc;
  border-radius: 8px;
  cursor: pointer;
  user-select: none;
  transition: background 0.2s;
  margin-bottom: 8px;
}
.points-section-header:hover {
  background: #f0f0f5;
}
.points-section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #374151;
}
.points-section-title .el-icon {
  transition: transform 0.3s;
  font-size: 14px;
  color: #6b7280;
}
.points-section-title .el-icon.is-rotated {
  transform: rotate(90deg);
}
.collapse-hint {
  font-size: 12px;
  color: #9ca3af;
}

:deep(.el-upload-dragger) { border: 2px dashed #d9d9d9; border-radius: 8px; padding: 30px 20px; transition: all 0.3s; }
:deep(.el-upload-dragger:hover) { border-color: #8b5cf6; }
.file-upload-compact :deep(.el-upload-dragger) { padding: 12px 16px; }
.file-upload-compact :deep(.el-upload) { width: 100%; }
:deep(.el-steps) { padding: 0 20px; }

.stream-output::-webkit-scrollbar { width: 5px; }
.stream-output::-webkit-scrollbar-thumb { background: rgba(139, 92, 246, 0.3); border-radius: 3px; }
.doc-list::-webkit-scrollbar { width: 4px; }
.doc-list::-webkit-scrollbar-thumb { background: rgba(139, 92, 246, 0.2); border-radius: 3px; }

.case-gen-dialog {
  padding: 0 4px;
}
.case-gen-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}
.case-gen-title {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}
.case-gen-elapsed {
  margin-left: auto;
  font-size: 12px;
  color: #9ca3af;
  flex-shrink: 0;
}
.case-gen-estimate {
  text-align: right;
  font-size: 12px;
  color: #8b5cf6;
  margin-bottom: 4px;
  font-weight: 500;
}
.case-gen-progress-bar {
  margin: 12px 0;
}
.case-gen-progress-bar :deep(.el-progress-bar__inner) {
  transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}
.case-gen-msg {
  text-align: center;
  color: #8b5cf6;
  font-size: 13px;
  font-weight: 500;
  margin: 8px 0;
}
.case-gen-stream {
  background: #1a1a2e;
  color: #a5f3fc;
  border-radius: 8px;
  padding: 12px;
  max-height: 260px;
  min-height: 80px;
  overflow-y: auto;
  margin-top: 12px;
}
.case-gen-stream pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 12px;
  line-height: 1.5;
}
.case-gen-stream-placeholder {
  color: #6b7280;
  font-style: italic;
}
.case-gen-stream::-webkit-scrollbar { width: 5px; }
.case-gen-stream::-webkit-scrollbar-thumb { background: rgba(139, 92, 246, 0.3); border-radius: 3px; }

@media (max-width: 900px) {
  .main-body {
    flex-direction: column;
  }
  .doc-sidebar {
    width: 100% !important;
    min-width: 100% !important;
    max-height: 300px;
  }
  .doc-sidebar.collapsed {
    width: 100% !important;
    min-width: 100% !important;
    max-height: 48px;
  }
}

/* 上传区多模态提示 */
.upload-ai-hint {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  margin-top: 8px;
  font-size: 12px;
  color: #8c8c8c;
  line-height: 1.4;
}

/* 需求分析弹窗 */
.req-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px 20px;
}
.req-loading h3 {
  margin: 12px 0 0;
  color: #303133;
}

/* 评审视频分析弹窗 */
.video-upload-area {
  width: 100%;
}
.video-analyzing {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 30px 20px;
}
.video-analyzing h3 {
  margin: 12px 0 0;
  color: #303133;
}
.video-step-msg {
  color: #909399;
  margin: 8px 0 16px;
  font-size: 13px;
}
.video-analysis-steps {
  display: flex;
  gap: 16px;
  margin-top: 8px;
}
.v-step {
  font-size: 12px;
  color: #c0c4cc;
  padding: 4px 10px;
  border-radius: 12px;
  background: #f5f7fa;
  transition: all 0.3s;
}
.v-step.active {
  color: #e6a23c;
  background: #fdf6ec;
  font-weight: 600;
}
.video-result {
  padding: 0 8px;
}
.video-summary-text {
  font-size: 13px;
  line-height: 1.7;
  color: #606266;
}
.video-list {
  padding-left: 20px;
  font-size: 13px;
  color: #606266;
  line-height: 1.8;
}
</style>
