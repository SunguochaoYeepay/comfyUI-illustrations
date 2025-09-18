import request from '@/utils/request'

export function getLoras(page, pageSize, name = null, baseModel = null, category = null) {
  const params = { page, pageSize };
  if (name) params.name_filter = name;
  if (baseModel) params.base_model_filter = baseModel;
  if (category) params.category_filter = category;
  
  return request({
    url: '/loras',
    method: 'get',
    params
  })
}

export function getLoraCategories() {
  return request({
    url: '/lora-categories',
    method: 'get'
  })
}

export function getUnassociatedLoras() {
  return request({
    url: '/loras/unassociated/list',
    method: 'get'
  })
}

export function createLoraRecord(data) {
  return request({
    url: '/loras',
    method: 'post',
    data
  })
}

export function deleteLora(loraId) {
  return request({
    url: `/loras/${loraId}`,
    method: 'delete'
  })
}

export function updateLoraMeta(loraCode, data) {
  return request({
    url: `/loras/code/${loraCode}`,
    method: 'put',
    data
  })
}

export function uploadLoraPreview(loraId, formData) {
  return request({
    url: `/loras/${loraId}/preview`,
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}