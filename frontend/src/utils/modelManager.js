/**
 * 模型配置管理器
 * 统一管理模型配置，避免重复请求和硬编码
 */

import { ref, reactive } from 'vue'

// API基础URL
const API_BASE = (() => {
  if (import.meta.env.DEV) {
    return import.meta.env.VITE_BACKEND_URL || 'http://localhost:9000'
  }
  return import.meta.env.VITE_API_BASE_URL || ''
})()

// Admin API基础URL
const ADMIN_API_BASE = (() => {
  if (import.meta.env.DEV) {
    return 'http://localhost:8888'
  }
  return import.meta.env.VITE_ADMIN_API_BASE_URL || ''
})()

// 全局状态
const models = ref([])
const loading = ref(false)
const configSource = ref('')
const lastUpdated = ref('')
const initialized = ref(false)

// 模型配置缓存
const modelConfigCache = reactive({
  isMultiImageModel: {},
  isVideoModel: {},
  supportsLora: {},
  maxImages: {}
})

// 获取模型列表
const fetchModels = async (forceRefresh = false) => {
  // 如果已经初始化且不强制刷新，直接返回缓存
  if (initialized.value && !forceRefresh) {
    return models.value
  }

  try {
    loading.value = true
    console.log('🔍 正在获取模型配置...')
    
    const response = await fetch(`${ADMIN_API_BASE}/api/admin/image-gen-config/base-models`)
    if (response.ok) {
      const data = await response.json()
      models.value = data.models || []
      configSource.value = data.config_source || 'admin_backend'
      lastUpdated.value = data.timestamp || new Date().toISOString()
      initialized.value = true
      
      // 预计算模型配置
      precomputeModelConfigs()
      
      console.log('✅ 模型配置获取成功:', models.value.length, '个模型')
      console.log('📊 配置来源:', configSource.value)
      
      return models.value
    } else {
      console.error('❌ 获取模型列表失败:', response.status)
      throw new Error(`HTTP ${response.status}`)
    }
  } catch (error) {
    console.error('❌ 获取模型列表出错:', error)
    throw error
  } finally {
    loading.value = false
  }
}

// 预计算模型配置，避免运行时重复计算
const precomputeModelConfigs = () => {
  models.value.forEach(model => {
    const modelName = model.name
    const modelType = model.model_type
    
    // 判断是否支持多图
    modelConfigCache.isMultiImageModel[modelName] = 
      modelType === 'qwen' || 
      modelType === 'gemini' || 
      modelType === 'flux' || 
      modelType === 'wan'
    
    // 判断是否为视频模型
    modelConfigCache.isVideoModel[modelName] = modelType === 'wan'
    
    // 判断是否支持LoRA
    modelConfigCache.supportsLora[modelName] = 
      modelType !== 'gemini' && modelType !== 'wan'
    
    // 设置最大图片数量
    if (modelType === 'qwen') {
      modelConfigCache.maxImages[modelName] = 3
    } else if (modelType === 'flux' || modelType === 'gemini' || modelType === 'wan') {
      modelConfigCache.maxImages[modelName] = 2
    } else {
      modelConfigCache.maxImages[modelName] = 1
    }
  })
  
  console.log('🔧 模型配置预计算完成:', modelConfigCache)
}

// 获取默认模型
const getDefaultModel = () => {
  if (models.value.length === 0) {
    return null
  }
  
  // 按 sort_order 排序，选择第一个可用的模型
  const sortedModels = [...models.value].sort((a, b) => (a.sort_order || 999) - (b.sort_order || 999))
  const firstAvailable = sortedModels.find(model => model.available) || sortedModels[0]
  
  return firstAvailable
}

// 根据模型名称获取模型信息
const getModelByName = (modelName) => {
  return models.value.find(model => model.name === modelName)
}

// 判断模型是否支持多图
const isMultiImageModel = (modelName) => {
  return modelConfigCache.isMultiImageModel[modelName] || false
}

// 判断是否为视频模型
const isVideoModel = (modelName) => {
  return modelConfigCache.isVideoModel[modelName] || false
}

// 判断模型是否支持LoRA
const supportsLora = (modelName) => {
  return modelConfigCache.supportsLora[modelName] || false
}

// 获取模型最大支持图片数量
const getMaxImages = (modelName) => {
  return modelConfigCache.maxImages[modelName] || 1
}

// 获取模型描述
const getModelDescription = (modelName) => {
  const model = getModelByName(modelName)
  return model?.description || 'AI图像生成模型'
}

// 获取所有可用模型
const getAvailableModels = () => {
  return models.value.filter(model => model.available)
}

// 重置状态
const reset = () => {
  models.value = []
  loading.value = false
  configSource.value = ''
  lastUpdated.value = ''
  initialized.value = false
  
  // 清空缓存
  Object.keys(modelConfigCache).forEach(key => {
    if (typeof modelConfigCache[key] === 'object') {
      Object.keys(modelConfigCache[key]).forEach(subKey => {
        delete modelConfigCache[key][subKey]
      })
    }
  })
}

// 导出
export {
  models,
  loading,
  configSource,
  lastUpdated,
  initialized,
  fetchModels,
  getDefaultModel,
  getModelByName,
  isMultiImageModel,
  isVideoModel,
  supportsLora,
  getMaxImages,
  getModelDescription,
  getAvailableModels,
  reset
}

// 默认导出
export default {
  models,
  loading,
  configSource,
  lastUpdated,
  initialized,
  fetchModels,
  getDefaultModel,
  getModelByName,
  isMultiImageModel,
  isVideoModel,
  supportsLora,
  getMaxImages,
  getModelDescription,
  getAvailableModels,
  reset
}
