import request from '@/utils/request'

export function getLoras(page, pageSize, name = null, baseModel = null) {
  const params = { page, pageSize };
  if (name) params.name_filter = name;  // 修复：使用name_filter
  if (baseModel) params.base_model_filter = baseModel;  // 修复：使用base_model_filter
  
  return request({
    url: '/loras',
    method: 'get',
    params
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

export function updateLoraMeta(loraId, data) {
  return request({
    url: `/loras/${loraId}`,
    method: 'put',
    data
  })
}

export function uploadLoraPreview(loraId, formData) {
  // TODO: 后端需要实现这个路由
  return Promise.reject(new Error('uploadLoraPreview 功能暂未实现'))
  // return request({
  //   url: `/loras/${loraId}/preview`,
  //   method: 'post',
  //   data: formData,
  //   headers: {
  //     'Content-Type': 'multipart/form-data'
  //   }
  // })
}