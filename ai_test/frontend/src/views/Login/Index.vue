<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <h1>AI测试平台</h1>
        <p>欢迎登录</p>
      </div>
      
      <el-form
        ref="loginFormRef"
        :model="loginForm"
        :rules="loginRules"
        class="login-form"
        @keyup.enter="handleLogin"
      >
        <el-form-item prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="请输入用户名"
            size="large"
            prefix-icon="User"
            clearable
          />
        </el-form-item>
        
        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="请输入密码"
            size="large"
            prefix-icon="Lock"
            show-password
            clearable
          />
        </el-form-item>
        
        <el-form-item>
          <el-checkbox v-model="loginForm.remember">记住密码</el-checkbox>
        </el-form-item>
        
        <el-form-item>
          <el-button
            type="primary"
            size="large"
            :loading="loading"
            class="login-btn"
            @click="handleLogin"
          >
            {{ loading ? '登录中...' : '登录' }}
          </el-button>
        </el-form-item>
      </el-form>
      
      <div class="login-footer">
        <p>还没有账号？<a href="#" @click.prevent="handleRegister">立即注册</a></p>
      </div>
    </div>
    
    <!-- 背景装饰 -->
    <div class="bg-decoration">
      <div class="circle circle-1"></div>
      <div class="circle circle-2"></div>
      <div class="circle circle-3"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '../../stores'
import { login } from '@/api/user'

const router = useRouter()
const userStore = useUserStore()

const loginFormRef = ref()
const loading = ref(false)

const loginForm = reactive({
  username: '',
  password: '',
  remember: false
})

const loginRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度在 3 到 50 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 128, message: '密码长度在 6 到 128 个字符', trigger: 'blur' }
  ]
}

const handleLogin = async () => {
  if (!loginFormRef.value) return
  
  try {
    await loginFormRef.value.validate()
    loading.value = true
    
    // 调用真实的登录API
    const response = await login({
      username: loginForm.username,
      password: loginForm.password
    })
    
    // 从响应中提取token和用户信息
    const { access_token, user } = response.data
    
    // 保存token到localStorage和用户信息到pinia
    userStore.setToken(access_token)
    userStore.setUser(user)
    
    ElMessage.success('登录成功')
    router.push('/project')
    
  } catch (error) {
    console.error('登录失败:', error)
    ElMessage.error(error.response?.data?.detail || '登录失败，请检查用户名和密码')
  } finally {
    loading.value = false
  }
}

const handleRegister = () => {
  ElMessage.info('注册功能开发中...')
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  background: linear-gradient(180deg, #2d1b69 0%, #1a0f3a 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
}

.login-card {
  width: 400px;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 16px;
  padding: 40px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  position: relative;
  z-index: 2;
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.login-header h1 {
  color: #ffffff;
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: bold;
  background: linear-gradient(135deg, #8b5cf6, #7c3aed);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.login-header p {
  color: rgba(255, 255, 255, 0.7);
  margin: 0;
  font-size: 14px;
}

.login-form {
  margin-bottom: 24px;
}

/* 输入框样式 */
.login-form :deep(.el-input__wrapper) {
  background: transparent;
  border: none;
  border-bottom: 1px solid rgba(139, 92, 246, 0.4);
  border-radius: 0;
  box-shadow: none;
  transition: all 0.3s ease;
}

.login-form :deep(.el-input__wrapper:hover) {
  border-bottom-color: rgba(139, 92, 246, 0.7);
  background: transparent;
}

.login-form :deep(.el-input__wrapper.is-focus) {
  border-bottom-color: #8b5cf6;
  background: transparent;
  box-shadow: none;
}

/* 输入文字颜色 */
.login-form :deep(.el-input__inner) {
  color: #ffffff;
  caret-color: #ffffff;
  background: transparent !important;
  -webkit-text-fill-color: #ffffff !important;
}

.login-form :deep(.el-input__inner::placeholder) {
  color: rgba(255, 255, 255, 0.45);
  -webkit-text-fill-color: rgba(255, 255, 255, 0.45) !important;
}

/* 去除浏览器自动填充的白色背景 */
.login-form :deep(.el-input__inner:-webkit-autofill),
.login-form :deep(.el-input__inner:-webkit-autofill:hover),
.login-form :deep(.el-input__inner:-webkit-autofill:focus),
.login-form :deep(.el-input__inner:-webkit-autofill:active) {
  -webkit-box-shadow: 0 0 0 1000px transparent inset !important;
  -webkit-text-fill-color: #ffffff !important;
  background: transparent !important;
  transition: background-color 9999s ease-in-out 0s;
}

/* 前缀图标颜色 */
.login-form :deep(.el-input__prefix .el-icon) {
  color: rgba(255, 255, 255, 0.6);
}

/* 后缀图标（清除按钮、密码切换）颜色 */
.login-form :deep(.el-input__suffix .el-icon) {
  color: rgba(255, 255, 255, 0.5);
}

.login-form :deep(.el-input__suffix .el-icon:hover) {
  color: rgba(255, 255, 255, 0.8);
}

/* 去除校验失败的红色边框 */
.login-form :deep(.el-form-item.is-error .el-input__wrapper) {
  box-shadow: none;
  border-color: #f56c6c;
}

/* 记住密码复选框 */
.login-form :deep(.el-checkbox__label) {
  color: rgba(255, 255, 255, 0.7);
}

.login-btn {
  width: 100%;
  background: linear-gradient(135deg, #8b5cf6, #7c3aed);
  border: none;
  border-radius: 8px;
  font-weight: bold;
  transition: all 0.3s ease;
}

.login-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(139, 92, 246, 0.4);
}

.login-footer {
  text-align: center;
}

.login-footer p {
  color: rgba(255, 255, 255, 0.7);
  margin: 0;
  font-size: 14px;
}

.login-footer a {
  color: #8b5cf6;
  text-decoration: none;
  font-weight: bold;
  transition: color 0.3s ease;
}

.login-footer a:hover {
  color: #7c3aed;
}

.bg-decoration {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.circle {
  position: absolute;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.1), rgba(124, 58, 237, 0.1));
  animation: float 6s ease-in-out infinite;
}

.circle-1 {
  width: 200px;
  height: 200px;
  top: 10%;
  left: 10%;
  animation-delay: 0s;
}

.circle-2 {
  width: 150px;
  height: 150px;
  top: 60%;
  right: 10%;
  animation-delay: 2s;
}

.circle-3 {
  width: 100px;
  height: 100px;
  bottom: 20%;
  left: 20%;
  animation-delay: 4s;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0px) rotate(0deg);
  }
  50% {
    transform: translateY(-20px) rotate(180deg);
  }
}
</style>