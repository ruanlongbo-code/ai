import { createRouter, createWebHistory } from 'vue-router'
import Layout from '../components/Layout.vue'
import { isAuthenticated } from '../utils/auth'
import { useUserStore } from '../stores'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login/Index.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/project',
    name: 'Project',
    component: () => import('../views/Project/Index.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/',
    component: Layout,
    redirect: '/dashboard',
    meta: { requiresAuth: true },
    children: [
      {
        path: 'dashboard/:projectId?',
        name: 'Dashboard',
        component: () => import('../views/ProjectSettings/Dashboard/Index.vue'),
        meta: { title: '仪表盘', icon: 'DataBoard' }
      },
      // 项目管理（仅管理员可访问）
      {
        path: 'project/module',
        name: 'ProjectModule',
        component: () => import('../views/ProjectSettings/Module/Index.vue'),
        meta: { title: '业务线管理', icon: 'Grid', requiresAdmin: true }
      },
      {
        path: 'project-settings/environment',
        name: 'ProjectEnvironment',
        component: () => import('../views/ProjectSettings/Environment/Index.vue'),
        meta: { title: '测试环境', icon: 'Platform', requiresAdmin: true }
      },
      {
        path: 'project-settings/environment/:environmentId/edit',
        name: 'EnvironmentEdit',
        component: () => import('../views/ProjectSettings/Environment/Edit.vue'),
        meta: { title: '编辑测试环境', icon: 'Edit', requiresAdmin: true }
      },
      {
        path: 'project/member',
        name: 'ProjectMember',
        component: () => import('../views/ProjectSettings/Member/Index.vue'),
        meta: { title: '成员管理', icon: 'User', requiresAdmin: true }
      },
      // 知识库
      {
        path: 'knowledge/document',
        name: 'KnowledgeDocument',
        component: () => import('../views/Knowledge/Document/Index.vue'),
        meta: { title: '文档管理', icon: 'FolderOpened' }
      },
      {
        path: 'knowledge/search',
        name: 'KnowledgeSearch',
        component: () => import('../views/Knowledge/Search/Index.vue'),
        meta: { title: '知识检索', icon: 'Search' }
      },
      {
        path: 'knowledge/case-set',
        name: 'KnowledgeCaseSet',
        component: () => import('../views/Knowledge/CaseSet/Index.vue'),
        meta: { title: '用例集', icon: 'Notebook' }
      },
      // 评审管理
      {
        path: 'knowledge/review/requirement',
        name: 'RequirementReview',
        component: () => import('../views/Knowledge/Review/Index.vue'),
        props: { reviewType: 'requirement' },
        meta: { title: '需求评审', icon: 'Document' }
      },
      {
        path: 'knowledge/review/technical',
        name: 'TechnicalReview',
        component: () => import('../views/Knowledge/Review/Index.vue'),
        props: { reviewType: 'technical' },
        meta: { title: '技术评审', icon: 'Cpu' }
      },
      {
        path: 'knowledge/review/testcase',
        name: 'TestcaseReview',
        component: () => import('../views/Knowledge/Review/Index.vue'),
        props: { reviewType: 'testcase' },
        meta: { title: '用例评审', icon: 'Checked' }
      },
      // 功能测试
      {
        path: 'function-test/requirement',
        name: 'FunctionTestRequirement',
        component: () => import('../views/FunctionTest/Requirement/List.vue'),
        meta: { title: '需求管理', icon: 'Document' }
      },
      {
        path: 'function-test/requirement/create',
        name: 'FunctionTestRequirementCreate',
        component: () => import('../views/FunctionTest/Requirement/Create.vue'),
        meta: { title: '新建需求', icon: 'Plus' }
      },
      {
        path: 'function-test/requirement/:id',
        name: 'FunctionTestRequirementDetail',
        component: () => import('../views/FunctionTest/Requirement/Detail.vue'),
        meta: { title: '需求详情', icon: 'View' }
      },
      {
        path: 'function-test/requirement/:id/edit',
        name: 'FunctionTestRequirementEdit',
        component: () => import('../views/FunctionTest/Requirement/Edit.vue'),
        meta: { title: '编辑需求', icon: 'Edit' }
      },
      {
        path: 'function-test/case/:projectId?',
        name: 'FunctionTestCase',
        component: () => import('../views/FunctionTest/Case/Index.vue'),
        meta: { title: '功能用例', icon: 'List' }
      },
      {
        path: 'function-test/defect',
        name: 'FunctionTestDefect',
        component: () => import('../views/FunctionTest/Defect/Index.vue'),
        meta: { title: '缺陷管理', icon: 'Warning' }
      },
      {
        path: 'function-test/case/generate/:requirementId',
        name: 'FunctionTestCaseGenerate',
        component: () => import('../views/FunctionTest/Case/Generate.vue'),
        meta: { title: '功能用例生成', icon: 'Magic' }
      },
      {
        path: 'function-test/case-set/:caseSetId',
        name: 'FunctionTestCaseSetDetail',
        component: () => import('../views/FunctionTest/Case/CaseSetDetail.vue'),
        meta: { title: '用例集详情', icon: 'Folder' }
      },
      // 接口测试
      {
        path: 'api-test/import',
        name: 'ApiTestImport',
        component: () => import('../views/ApiTest/Import/Index.vue'),
        meta: { title: '接口导入', icon: 'Upload' }
      },
      {
        path: 'project/:projectId/api-management',
        name: 'ApiTestManagement',
        component: () => import('../views/ApiTest/Management/Index.vue'),
        meta: { title: '接口管理', icon: 'Setting' }
      },
      {
        path: 'project/:projectId/api-dependency/:interfaceId',
        name: 'ApiDependencyManagement',
        component: () => import('../views/ApiTest/Dependency/Index.vue'),
        meta: { title: '接口依赖设置', icon: 'Connection' }
      },
      {
        path: 'project/:projectId/api-case-generate/:interfaceId',
        name: 'ApiCaseGenerate',
        component: () => import('../views/ApiTest/CaseGenerate/Index.vue'),
        meta: { title: 'API基础测试点生成', icon: 'Magic' }
      },
      {
        path: 'project/:projectId/api-complete-case-generate/:interfaceId',
        name: 'ApiCompleteCaseGenerate',
        component: () => import('../views/ApiTest/CompleteCaseGenerate/Index.vue'),
        meta: { title: 'API完整用例生成', icon: 'Magic' }
      },
      {
        path: 'project/:projectId/api-executable-generate/:baseCaseId',
        name: 'ApiExecutableCaseGenerate',
        component: () => import('../views/ApiTest/ExecutableCaseGenerate/Index.vue'),
        meta: { title: 'API可执行用例生成', icon: 'Magic' }
      },
      {
        path: 'api-test/base-case',
        name: 'ApiTestBaseCase',
        component: () => import('../views/ApiTest/BaseCase/Index.vue'),
        meta: { title: 'API测试点管理', icon: 'Files' }
      },
      {
        path: 'api-test/auto-case',
        name: 'ApiTestAutoCase',
        component: () => import('../views/ApiTest/AutoCase/Index.vue'),
        meta: { title: '自动化用例', icon: 'VideoPlay' }
      },
      {
        path: 'api-test/test-case/:projectId/:testCaseId/edit',
        name: 'ApiTestCaseEdit',
        component: () => import('../views/ApiTest/AutoCase/Edit.vue'),
        meta: { title: '编辑自动化用例', icon: 'Edit' }
      },
      {
        path: 'api-test/suite',
        name: 'ApiTestSuite',
        component: () => import('../views/ApiTest/Suite/Index.vue'),
        meta: { title: '测试套件', icon: 'Collection' }
      },
      {
        path: 'api-test/suite/:projectId/:suiteId/edit',
        name: 'ApiTestSuiteEdit',
        component: () => import('../views/ApiTest/Suite/Edit.vue'),
        meta: { title: '编辑测试套件', icon: 'Edit' }
      },
      {
        path: 'api-test/plan',
        name: 'ApiTestPlan',
        component: () => import('../views/ApiTest/Plan/Index.vue'),
        meta: { title: '测试计划', icon: 'Calendar' }
      },
      {
        path: 'api-test/plan/:projectId/:taskId/edit',
        name: 'ApiTestPlanEdit',
        component: () => import('../views/ApiTest/Plan/Edit.vue'),
        meta: { title: '编辑测试计划', icon: 'Edit' }
      },
      // Phase 1: 快捷调试
      {
        path: 'api-test/quick-debug',
        name: 'ApiQuickDebug',
        component: () => import('../views/ApiTest/QuickDebug/Index.vue'),
        meta: { title: '快捷调试', icon: 'Lightning' }
      },
      // Phase 2: 定时任务
      {
        path: 'api-test/scheduled-tasks',
        name: 'ApiScheduledTasks',
        component: () => import('../views/ApiTest/ScheduledTask/Index.vue'),
        meta: { title: '定时任务', icon: 'Timer' }
      },
      // Phase 3: Webhook通知配置
      {
        path: 'api-test/webhook-config',
        name: 'ApiWebhookConfig',
        component: () => import('../views/ApiTest/WebhookConfig/Index.vue'),
        meta: { title: '通知配置', icon: 'Bell' }
      },
      // Phase 3: 增强执行报告
      {
        path: 'api-test/execution-report/:projectId/:runId',
        name: 'ApiExecutionReport',
        component: () => import('../views/ApiTest/ExecutionReport/Index.vue'),
        meta: { title: '执行报告', icon: 'DataAnalysis' }
      },
      // Allure风格接口测试报告
      {
        path: 'api-test/allure-reports',
        name: 'ApiAllureReportList',
        component: () => import('../views/ApiTest/AllureReport/List.vue'),
        meta: { title: '测试报告', icon: 'TrendCharts' }
      },
      {
        path: 'api-test/allure-report/:projectId/:runId',
        name: 'ApiAllureReportDetail',
        component: () => import('../views/ApiTest/AllureReport/Detail.vue'),
        meta: { title: '报告详情', icon: 'TrendCharts' }
      },
      {
        path: 'test-execution/task-run/:projectId/:runId',
        name: 'TaskRunReport',
        component: () => import('../views/TestExecution/TaskRunReport.vue'),
        meta: { title: '任务执行报告', icon: 'Document' }
      },
      {
        path: 'suite/run/:projectId/:runId/:suiteId?',
        name: 'SuiteRunReport',
        component: () => import('../views/Suite/SuiteRunReport.vue'),
        meta: { title: '套件运行报告', icon: 'Document' }
      },
      // UI测试
      {
        path: 'ui-test/page',
        name: 'UiTestPage',
        component: () => import('../views/UiTest/Page/Index.vue'),
        meta: { title: '页面管理', icon: 'Notebook' }
      },
      {
        path: 'ui-test/case',
        name: 'UiTestCase',
        component: () => import('../views/UiTest/Case/Index.vue'),
        meta: { title: '用例管理', icon: 'List' }
      },
      {
        path: 'ui-test/execute/:caseId',
        name: 'UiTestExecute',
        component: () => import('../views/UiTest/Execute/Index.vue'),
        meta: { title: 'AI执行', icon: 'VideoPlay' }
      },
      {
        path: 'ui-test/reports',
        name: 'UiTestReportList',
        component: () => import('../views/UiTest/ReportList/Index.vue'),
        meta: { title: '测试报告', icon: 'DataAnalysis' }
      },
      {
        path: 'ui-test/report/:executionId',
        name: 'UiTestReport',
        component: () => import('../views/UiTest/Report/Index.vue'),
        meta: { title: '报告详情', icon: 'Document' }
      },
      // 压力测试
      {
        path: 'stress-test/scenario',
        name: 'StressTestScenario',
        component: () => import('../views/StressTest/Scenario/Index.vue'),
        meta: { title: '测试场景', icon: 'Document' }
      },
      {
        path: 'stress-test/task',
        name: 'StressTestTask',
        component: () => import('../views/StressTest/Task/Index.vue'),
        meta: { title: '压测任务', icon: 'VideoPlay' }
      },
      {
        path: 'stress-test/report/:taskId',
        name: 'StressTestReport',
        component: () => import('../views/StressTest/Report/Index.vue'),
        meta: { title: '性能报告', icon: 'DataAnalysis' }
      },
      {
        path: 'stress-test/monitor/:taskId',
        name: 'StressTestMonitor',
        component: () => import('../views/StressTest/Monitor/Index.vue'),
        meta: { title: '实时监控', icon: 'TrendCharts' }
      },
      {
        path: 'stress-test/reports',
        name: 'StressTestReportList',
        component: () => import('../views/StressTest/ReportList/Index.vue'),
        meta: { title: '性能报告', icon: 'DataAnalysis' }
      },
      {
        path: 'stress-test/monitors',
        name: 'StressTestMonitorList',
        component: () => import('../views/StressTest/MonitorList/Index.vue'),
        meta: { title: '实时监控', icon: 'TrendCharts' }
      },
      {
        path: 'stress-test/baseline',
        name: 'StressTestBaseline',
        component: () => import('../views/StressTest/Baseline/Index.vue'),
        meta: { title: '基线管理', icon: 'Histogram' }
      },
      // 测试排期管理
      {
        path: 'schedule/iteration',
        name: 'ScheduleIteration',
        component: () => import('../views/Schedule/Iteration/Index.vue'),
        meta: { title: '排期管理', icon: 'Calendar' }
      },
      {
        path: 'schedule/daily-report',
        name: 'ScheduleDailyReport',
        component: () => import('../views/Schedule/DailyReport/Index.vue'),
        meta: { title: '同步进度', icon: 'Edit' }
      },
      {
        path: 'schedule/dashboard',
        name: 'ScheduleDashboard',
        component: () => import('../views/Schedule/Dashboard/Index.vue'),
        meta: { title: '进度看板', icon: 'TrendCharts' }
      },
      {
        path: 'schedule/feishu',
        name: 'ScheduleFeishu',
        component: () => import('../views/Schedule/Feishu/Index.vue'),
        meta: { title: '需求群管理', icon: 'ChatDotRound' }
      },
      // 数据分析
      {
        path: 'data-analysis/defect',
        name: 'DataAnalysisDefect',
        component: () => import('../views/DataAnalysis/DefectAnalysis/Index.vue'),
        meta: { title: '缺陷分析', icon: 'PieChart' }
      },
      {
        path: 'data-analysis/behavior',
        name: 'DataAnalysisBehavior',
        component: () => import('../views/DataAnalysis/BehaviorAnalysis/Index.vue'),
        meta: { title: '用户行为分析', icon: 'TrendCharts' }
      },
      // 用户管理
      {
        path: 'user-management/users',
        name: 'UserManagementUsers',
        component: () => import('../views/UserManagement/Users/Index.vue'),
        meta: { title: '用户管理', icon: 'Avatar', requiresAdmin: true }
      },
      // 未来可期
      {
        path: 'coming-soon',
        name: 'ComingSoon',
        component: () => import('../views/ComingSoon/Index.vue'),
        meta: { title: '未来可期', icon: 'MagicStick' }
      },
      ]
    },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/dashboard'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由切换后重置内容区域滚动位置
router.afterEach(() => {
  const mainContent = document.querySelector('.main-content')
  if (mainContent) {
    mainContent.scrollTop = 0
  }
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  
  // 检查是否需要认证
  if (to.meta.requiresAuth && !userStore.isLoggedIn) {
    next('/login')
  } else if (to.meta.requiresAdmin && !(userStore.user?.is_superuser === true)) {
    // 非管理员访问管理员页面时，重定向到仪表盘
    next('/dashboard')
  } else if (to.path === '/login' && userStore.isLoggedIn) {
    next('/project')
  } else {
    next()
  }
})

export default router