import request from '@/utils/request'

// 获取生图配置
export function getImageGenConfig() {
  return request({
    url: '/admin/image-gen-config',
    method: 'get'
  })
}

// 更新生图配置
export function updateImageGenConfig(data) {
  return request({
    url: '/admin/image-gen-config',
    method: 'put',
    data
  })
}

// 获取基础模型列表用于配置
export function getBaseModelsForConfig() {
  return request({
    url: '/admin/image-gen-config/base-models',
    method: 'get'
  })
}

// 获取LoRA列表用于配置
export function getLorasForConfig() {
  return request({
    url: '/admin/image-gen-config/loras',
    method: 'get'
  })
}
