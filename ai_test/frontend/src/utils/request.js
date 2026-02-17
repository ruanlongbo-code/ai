import axios from 'axios'
import {ElMessage, ElNotification} from 'element-plus'
import { useUserStore } from '../stores'
import router from '../router'

// 创建 axios 实例
const request = axios.create({
	baseURL: import.meta.env.VITE_BASE_API, // 后端 API 基础地址
	timeout: 10000,
	headers: {
		'Content-Type': 'application/json'
	}
})

// 请求拦截器
request.interceptors.request.use(
	(config) => {
		const userStore = useUserStore()
		if (userStore.token) {
			config.headers.Authorization = `Bearer ${userStore.token}`
		}
		return config
	},
	(error) => {
		return Promise.reject(error)
	}
)

// 响应拦截器
request.interceptors.response.use(
	(response) => {
		return response
	},
	(error) => {
		const userStore = useUserStore()

		// 处理401未授权错误（token过期或无效）
		if (error.response && error.response.status === 401) {
			// 排除登录接口本身的401（用户名密码错误）
			const requestUrl = error.response.config?.url || ''
			if (!requestUrl.includes('/login')) {
				ElMessage.error('登录已过期，请重新登录')
				userStore.logout()
				router.push('/login')
				return Promise.reject(error)
			}
		}

		// 处理403权限不足
		if (error.response && error.response.status === 403) {
			ElMessage.error('没有操作权限')
			return Promise.reject(error)
		}

		// 处理500服务器错误
		if (error.response && error.response.status === 500) {
			ElMessage.error('服务器内部错误')
			return Promise.reject(error)
		}

		// 网络错误处理
		if (error.code === 'ERR_NETWORK' || error.message?.includes('Network Error')) {
			ElNotification({
				title: '网络错误',
				message: '网络错误，请检查网络是否正常，检查后端服务状态！',
				type: 'error',
				duration: 3000
			})
		}

		return Promise.reject(error)
	}
)

export default request