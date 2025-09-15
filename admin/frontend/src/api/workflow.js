import request from '@/utils/request'

// 获取工作流列表
export function getWorkflows(params = {}) {
  return request({
    url: '/admin/workflows/',
    method: 'get',
    params: {
      skip: (params.page - 1) * params.pageSize || 0,
      limit: params.pageSize || 10,
      ...params
    }
  })
}

// 获取单个工作流
export function getWorkflow(id) {
  return request({
    url: `/admin/workflows/${id}`,
    method: 'get'
  })
}

// 创建工作流
export function createWorkflow(data) {
  return request({
    url: '/admin/workflows/',
    method: 'post',
    data
  })
}

// 更新工作流
export function updateWorkflow(id, data) {
  return request({
    url: `/admin/workflows/${id}`,
    method: 'put',
    data
  })
}

// 删除工作流
export function deleteWorkflow(id) {
  return request({
    url: `/admin/workflows/${id}`,
    method: 'delete'
  })
}

// 上传工作流文件
export function uploadWorkflowFile(file, name, description) {
  const formData = new FormData()
  formData.append('file', file)
  if (name) formData.append('name', name)
  if (description) formData.append('description', description)
  
  return request({
    url: '/admin/workflows/upload',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

// 下载工作流
export function downloadWorkflow(id) {
  return request({
    url: `/admin/workflows/${id}/download`,
    method: 'get'
  })
}

export function validateWorkflow(workflowData) {
  return request({
    url: '/admin/workflows/validate',
    method: 'post',
    data: workflowData
  })
}

export function uploadAndValidateWorkflow(file, name, description) {
  const formData = new FormData()
  formData.append('file', file)
  if (name) formData.append('name', name)
  if (description) formData.append('description', description)
  
  return request({
    url: '/admin/workflows/upload-and-validate',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

export function createWorkflowFromUpload(workflowConfig) {
  return request({
    url: '/admin/workflows/create-from-upload',
    method: 'post',
    data: workflowConfig
  })
}

export function getSizeMappings() {
  return request({
    url: '/admin/workflows/size-mappings',
    method: 'get'
  })
}

export function getSizesByRatio(ratio) {
  return request({
    url: `/admin/workflows/sizes/${ratio}`,
    method: 'get'
  })
}

export function validateSize(sizeData) {
  return request({
    url: '/admin/workflows/validate-size',
    method: 'post',
    data: sizeData
  })
}

export function getRecommendedSizes(modelType, ratio) {
  return request({
    url: '/admin/workflows/recommended-sizes',
    method: 'get',
    params: {
      model_type: modelType,
      ratio: ratio
    }
  })
}

export function getDefaultSize(modelType, ratio) {
  return request({
    url: '/admin/workflows/default-size',
    method: 'get',
    params: {
      model_type: modelType,
      ratio: ratio || '1:1'
    }
  })
}
