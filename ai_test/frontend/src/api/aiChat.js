import request from '@/utils/request'

const baseURL = import.meta.env.VITE_API_BASE_URL || '/api'
const getToken = () => localStorage.getItem('token')

export const getChatSessions = (projectId, params = {}) => {
  return request({
    url: `/functional_test/${projectId}/ai_chat/sessions`,
    method: 'get',
    params
  })
}

export const createChatSession = (projectId, data = {}) => {
  return request({
    url: `/functional_test/${projectId}/ai_chat/sessions`,
    method: 'post',
    data
  })
}

export const deleteChatSession = (projectId, sessionId) => {
  return request({
    url: `/functional_test/${projectId}/ai_chat/sessions/${sessionId}`,
    method: 'delete'
  })
}

export const renameChatSession = (projectId, sessionId, data) => {
  return request({
    url: `/functional_test/${projectId}/ai_chat/sessions/${sessionId}`,
    method: 'put',
    data
  })
}

export const getChatMessages = (projectId, sessionId) => {
  return request({
    url: `/functional_test/${projectId}/ai_chat/sessions/${sessionId}/messages`,
    method: 'get'
  })
}

export const sendChatMessageStream = (projectId, sessionId, data, signal) => {
  const token = getToken()
  return fetch(`${baseURL}/functional_test/${projectId}/ai_chat/sessions/${sessionId}/send_stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {})
    },
    body: JSON.stringify(data),
    signal,
  })
}

export const sendChatWithFilesStream = (projectId, sessionId, formData, signal) => {
  const token = getToken()
  return fetch(`${baseURL}/functional_test/${projectId}/ai_chat/sessions/${sessionId}/send_with_files_stream`, {
    method: 'POST',
    headers: {
      ...(token ? { 'Authorization': `Bearer ${token}` } : {})
    },
    body: formData,
    signal,
  })
}
