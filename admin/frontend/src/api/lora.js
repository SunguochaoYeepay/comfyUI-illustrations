import request from '@/utils/request'

export function getLoras(page, pageSize) {
  return request({
    url: '/api/loras',
    method: 'get',
    params: { page, pageSize }
  })
}

export function getUnassociatedLoras() {
  return request({
    url: '/api/loras/unassociated',
    method: 'get'
  })
}

export function createLoraRecord(data) {
  return request({
    url: '/api/loras/create',
    method: 'post',
    data
  })
}

export function deleteLora(loraName) {
  return request({
    url: `/api/loras/${loraName}`,
    method: 'delete'
  })
}

export function updateLoraMeta(loraName, data) {
  return request({
    url: `/api/loras/${loraName}/meta`,
    method: 'post',
    data
  })
}

export function uploadLoraPreview(loraName, formData) {
  return request({
    url: `/api/loras/${loraName}/preview`,
    method: 'post',
    data: formData, // formData will be passed directly
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}