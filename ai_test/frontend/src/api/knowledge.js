import request from '../utils/request'

export function getKnowledgeDocuments(projectId, params) {
  return request({ url: `/knowledge/${projectId}/documents`, method: 'get', params })
}

export function uploadTextDocument(projectId, data) {
  return request({ url: `/knowledge/${projectId}/documents/text`, method: 'post', data })
}

export function uploadFileDocument(projectId, formData) {
  return request({ url: `/knowledge/${projectId}/documents/file`, method: 'post', data: formData, headers: { 'Content-Type': 'multipart/form-data' } })
}

export function deleteKnowledgeDocument(projectId, docId) {
  return request({ url: `/knowledge/${projectId}/documents/${docId}`, method: 'delete' })
}

export function searchKnowledgeSync(projectId, data) {
  return request({ url: `/knowledge/${projectId}/search/sync`, method: 'post', data })
}

// 用例集 API
export function getCaseSetList(projectId) {
  return request({ url: `/knowledge/${projectId}/case-sets`, method: 'get' })
}

export function getCaseSetTree(projectId, caseSetId) {
  return request({ url: `/knowledge/${projectId}/case-sets/${caseSetId}/tree`, method: 'get' })
}

export function importXmindCaseSet(projectId, formData) {
  return request({ url: `/knowledge/${projectId}/case-sets/import-xmind`, method: 'post', data: formData, headers: { 'Content-Type': 'multipart/form-data' }, timeout: 120000 })
}

export function importFunctionalCaseSet(projectId, requirementIds) {
  const params = requirementIds ? { requirement_ids: requirementIds } : {}
  return request({ url: `/knowledge/${projectId}/case-sets/import-functional`, method: 'post', params })
}

export function deleteCaseSet(projectId, caseSetId) {
  return request({ url: `/knowledge/${projectId}/case-sets/${caseSetId}`, method: 'delete' })
}

// ======================== 评审记录 API ========================

export function getReviewList(projectId, params) {
  return request({ url: `/knowledge/${projectId}/reviews`, method: 'get', params })
}

export function getReviewDetail(projectId, reviewId) {
  return request({ url: `/knowledge/${projectId}/reviews/${reviewId}`, method: 'get' })
}

export function uploadReviewVideo(projectId, formData) {
  return request({
    url: `/knowledge/${projectId}/reviews/upload`,
    method: 'post',
    data: formData,
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 600000 // 10分钟超时，视频文件可能较大
  })
}

export function deleteReview(projectId, reviewId) {
  return request({ url: `/knowledge/${projectId}/reviews/${reviewId}`, method: 'delete' })
}
