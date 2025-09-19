/**
 * 图像生成API服务模块
 */

import { processTaskImages } from '../utils/imageUtils.js'
import { pollTaskStatus } from './pollingService.js'

/**
 * 生成图像
 * @param {Object} options - 生成选项
 * @param {string} options.prompt - 提示词
 * @param {string} options.model - 模型名称
 * @param {string} options.size - 图像尺寸
 * @param {number} options.count - 图像数量
 * @param {Array} options.referenceImages - 参考图像
 * @param {Array} options.loras - LoRA配置
 * @param {string} options.mode - 生成模式
 * @param {Object} options.videoConfig - 视频配置
 * @param {string} API_BASE - API基础URL
 * @param {Object} callbacks - 回调函数对象
 * @returns {Promise} 生成结果
 */
export const generateImage = async (options, API_BASE, callbacks) => {
  const { 
    prompt, 
    model, 
    size, 
    count, 
    referenceImages, 
    loras, 
    mode = 'single', 
    videoConfig 
  } = options

  if (!prompt?.trim()) {
    if (callbacks.onError) {
      callbacks.onError('请输入图像描述')
    }
    return
  }

  // 图片数量验证
  if (referenceImages?.length > 3) {
    if (callbacks.onError) {
      callbacks.onError('最多支持3张图片')
    }
    return
  }
  
  // 多图融合模式特殊验证
  if (mode === 'fusion' && referenceImages?.length < 2) {
    if (callbacks.onError) {
      callbacks.onError('多图融合至少需要2张图片')
    }
    return
  }
  
  // Flux模型2图融合验证
  if (model === 'flux-dev' && referenceImages?.length > 2) {
    if (callbacks.onError) {
      callbacks.onError('Flux模型最多支持2张图片融合')
    }
    return
  }
  
  // Wan模型2图验证
  if (model === 'wan2.2-video' && referenceImages?.length > 2) {
    if (callbacks.onError) {
      callbacks.onError('Wan模型最多支持2张图片')
    }
    return
  }

  if (callbacks.onStart) {
    callbacks.onStart()
  }

  try {
    // 准备FormData
    const formData = new FormData()
    formData.append('description', prompt)
    formData.append('steps', 8)
    formData.append('model', model)
    
    // 如果是视频生成，添加视频配置
    if (videoConfig) {
      formData.append('duration', videoConfig.duration)
      formData.append('fps', videoConfig.fps)
      console.log(`🎬 视频生成配置: 时长=${videoConfig.duration}秒, 帧率=${videoConfig.fps}FPS`)
    }
    
    // 根据模式设置不同的参数
    if (mode === 'fusion') {
      // 多图融合模式
      if (model === 'flux-dev') {
        // Flux模型2图融合模式
        formData.append('size', size)
        
        // 添加2张参考图片
        referenceImages.forEach((imageFile, index) => {
          if (imageFile.originFileObj instanceof File) {
            formData.append('reference_images', imageFile.originFileObj)
          } else {
            console.error(`参考图片${index + 1}文件对象无效:`, imageFile)
            if (callbacks.onError) {
              callbacks.onError(`参考图片${index + 1}文件无效，请重新选择`)
            }
            return
          }
        })
        
        console.log(`🎨 Flux 2图融合模式: 上传${referenceImages.length}张图片, 尺寸=${size}`)
      } else if (model === 'wan2.2-video') {
        // Wan模型2图视频模式
        formData.append('size', size)
        
        // 添加2张参考图片
        referenceImages.forEach((imageFile, index) => {
          if (imageFile.originFileObj instanceof File) {
            formData.append('reference_images', imageFile.originFileObj)
          } else {
            console.error(`参考图片${index + 1}文件对象无效:`, imageFile)
            if (callbacks.onError) {
              callbacks.onError(`参考图片${index + 1}文件无效，请重新选择`)
            }
            return
          }
        })
        
        console.log(`🎬 Wan 2图视频模式: 上传${referenceImages.length}张图片, 尺寸=${size}`)
      } else {
        // Qwen/Gemini多图融合模式
        formData.append('fusion_mode', 'concat')
        formData.append('cfg', 2.5)
        formData.append('size', size)
        
        // 添加多张参考图片
        referenceImages.forEach((imageFile, index) => {
          if (imageFile.originFileObj instanceof File) {
            formData.append('reference_images', imageFile.originFileObj)
          } else {
            console.error(`参考图片${index + 1}文件对象无效:`, imageFile)
            if (callbacks.onError) {
              callbacks.onError(`参考图片${index + 1}文件无效，请重新选择`)
            }
            return
          }
        })
        
        console.log(`🎨 多图融合模式: 上传${referenceImages.length}张图片, 尺寸=${size}`)
      }
    } else {
      // 单图生成模式 - 但Wan模型需要特殊处理
      if (model === 'wan2.2-video' && referenceImages?.length > 1) {
        // Wan模型自动检测多图，即使不是融合模式
        formData.append('size', size)
        
        // 添加多张参考图片
        referenceImages.forEach((imageFile, index) => {
          if (imageFile.originFileObj instanceof File) {
            formData.append('reference_images', imageFile.originFileObj)
          } else {
            console.error(`参考图片${index + 1}文件对象无效:`, imageFile)
            if (callbacks.onError) {
              callbacks.onError(`参考图片${index + 1}文件无效，请重新选择`)
            }
            return
          }
        })
        
        console.log(`🎬 Wan模型自动多图模式: 上传${referenceImages.length}张图片, 尺寸=${size}`)
      } else {
        // 真正的单图模式
        formData.append('count', count)
        formData.append('size', size)
        
        // 添加LoRA配置
        if (loras?.length > 0) {
          formData.append('loras', JSON.stringify(loras))
          console.log('🎨 添加LoRA配置:', loras)
        }
        
        // 添加参考图片（如果有的话）
        if (referenceImages?.length > 0 && referenceImages[0].originFileObj) {
          const fileObj = referenceImages[0].originFileObj
          // 验证文件对象是否有效
          if (fileObj instanceof File) {
            formData.append('reference_image', fileObj)
          } else {
            console.error('参考图片文件对象无效:', fileObj)
            if (callbacks.onError) {
              callbacks.onError('参考图片文件无效，请重新选择')
            }
            return
          }
        }
      }
    }

    // 调用后端API
    let apiEndpoint
    if (mode === 'fusion') {
      if (model === 'flux-dev' || model === 'wan2.2-video') {
        // Flux和Wan模型使用普通生成接口，但传递多张图片
        apiEndpoint = '/api/generate-image'
      } else {
        // Qwen/Gemini模型使用专门的融合接口
        apiEndpoint = '/api/generate-image-fusion'
      }
    } else {
      // 单图模式，但Wan模型可能需要多图接口
      if (model === 'wan2.2-video' && referenceImages?.length > 1) {
        // Wan模型自动多图模式，使用普通生成接口
        apiEndpoint = '/api/generate-image'
      } else {
        apiEndpoint = '/api/generate-image'
      }
    }
    
    const response = await fetch(`${API_BASE}${apiEndpoint}`, {
      method: 'POST',
      body: formData
    })

    if (response.ok) {
      const result = await response.json()
      const taskId = result.task_id
      
      if (callbacks.onTaskCreated) {
        callbacks.onTaskCreated(taskId)
      }
      
      // 开始轮询任务状态
      await pollTaskStatus(taskId, API_BASE, {
        onProgress: (progress) => {
          if (callbacks.onProgress) {
            callbacks.onProgress(progress)
          }
        },
        onSuccess: async (statusData) => {
          if (callbacks.onSuccess) {
            await callbacks.onSuccess(statusData, taskId)
          }
        },
        onError: (error) => {
          if (callbacks.onError) {
            callbacks.onError(error)
          }
        }
      })
    } else {
      throw new Error('提交任务失败')
    }
  } catch (error) {
    console.error('生成错误:', error)
    if (callbacks.onError) {
      callbacks.onError('生成失败，请稍后重试')
    }
  }
}

/**
 * 加载历史记录
 * @param {number} page - 页码
 * @param {boolean} prepend - 是否前置添加
 * @param {Object} filterParams - 筛选参数
 * @param {Object} options - 选项
 * @param {string} API_BASE - API基础URL
 * @param {Object} callbacks - 回调函数对象
 * @returns {Promise} 加载结果
 */
export const loadHistory = async (page, prepend, filterParams, options, API_BASE, callbacks) => {
  const pageSize = options.pageSize || 20
  
  if (callbacks.isLoadingHistory && callbacks.isLoadingHistory.value && !options.forceRefresh && !prepend) {
    return
  }
  
  const startTime = performance.now()
  console.log(`[性能监控] 开始加载历史记录，页面: ${page}, 模式: ${prepend ? 'prepend' : 'replace'}`)
  
  try {
    // 只有在非静默刷新时才显示loading状态
    if (!options.silent && callbacks.setLoadingHistory) {
      callbacks.setLoadingHistory(true)
    }
    
    const offset = (page - 1) * pageSize
    
    // 记录当前滚动位置，用于保持滚动位置
    const currentScrollTop = window.pageYOffset || document.documentElement.scrollTop
    const currentScrollHeight = document.documentElement.scrollHeight
    
    // 构建查询参数
    const queryParams = new URLSearchParams({
      limit: pageSize.toString(),
      offset: offset.toString(),
      order: 'desc', // 降序排列，最新的任务在第一页
      _t: Date.now().toString() // 添加时间戳避免缓存
    })
    
    // 添加筛选参数
    if (filterParams.favoriteFilter && filterParams.favoriteFilter !== 'all') {
      queryParams.append('favorite_filter', filterParams.favoriteFilter)
    }
    if (filterParams.timeFilter && filterParams.timeFilter !== 'all') {
      queryParams.append('time_filter', filterParams.timeFilter)
    }

    // 使用AbortController来支持请求取消
    const controller = new AbortController()
    const timeoutId = setTimeout(() => {
      console.log('请求超时，取消请求')
      controller.abort()
    }, 15000) // 减少到15秒超时
    
    console.log('开始加载历史记录，页面:', page, '偏移量:', offset, '筛选参数:', filterParams)
    
    const response = await fetch(`${API_BASE}/api/history?${queryParams.toString()}`, {
      signal: controller.signal,
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    })
    
    clearTimeout(timeoutId)
    console.log('API响应状态:', response.status)
    
    if (!response.ok) {
      throw new Error(`API响应失败: ${response.status}`)
    }
    
    const data = await response.json()
    
    // 处理任务数据
    const processedTasks = data.tasks ? data.tasks.map(task => {
      try {
        const processedImages = processTaskImages(task, API_BASE)
        return {
          id: task.task_id,
          task_id: task.task_id,
          prompt: task.description,
          timestamp: task.created_at,
          status: task.status,
          images: processedImages,
          result_path: task.result_path,
          model: task.parameters?.model,
          parameters: task.parameters
        }
      } catch (taskError) {
        console.error('处理单个任务数据失败:', taskError, task)
        return null
      }
    }).filter(item => item !== null) : []
    
    const result = {
      data: processedTasks,
      totalCount: data.total || 0,
      hasMore: data.has_more || false
    }
    
    // 更新分页状态
    if (callbacks.setTotalCount) {
      callbacks.setTotalCount(result.totalCount)
    }
    if (callbacks.setHasMore) {
      callbacks.setHasMore(result.hasMore)
    }
    if (callbacks.setCurrentPage) {
      callbacks.setCurrentPage(page)
    }
    
    if (result.data && result.data.length > 0) {
      if (callbacks.onDataLoaded) {
        await callbacks.onDataLoaded(result.data, prepend, currentScrollTop, currentScrollHeight)
      }
    } else {
      // 如果没有数据需要处理，直接清除loading状态
      if (!prepend && callbacks.setHistory) {
        callbacks.setHistory([])
      }
    }
    
    // 立即清除loading状态（如果不是静默模式）
    if (!options.silent && callbacks.setLoadingHistory) {
      callbacks.setLoadingHistory(false)
    }
    
    const endTime = performance.now()
    console.log(`[性能监控] 历史记录加载完成，耗时: ${(endTime - startTime).toFixed(2)}ms`)
    
  } catch (error) {
    if (error.name === 'AbortError') {
      console.log('请求被取消')
    } else {
      console.error('加载历史记录失败:', error)
      // 如果API失败且是第一页，显示错误信息
      if (page === 1) {
        console.error('无法从后端加载历史记录，请检查网络连接')
      }
      if (callbacks.onError) {
        callbacks.onError('加载历史记录失败')
      }
    }
    // 在catch块中也要清除loading状态（如果不是静默模式）
    if (!options.silent && callbacks.setLoadingHistory) {
      callbacks.setLoadingHistory(false)
    }
  }
}

/**
 * 删除图像
 * @param {Object} image - 图像对象
 * @param {string} API_BASE - API基础URL
 * @param {Object} callbacks - 回调函数对象
 * @returns {Promise} 删除结果
 */
export const deleteImage = async (image, API_BASE, callbacks) => {
  try {
    // 调用后端删除API
    const response = await fetch(`${API_BASE}/api/task/${image.task_id}`, {
      method: 'DELETE'
    })
    
    if (response.ok) {
      if (callbacks.onSuccess) {
        callbacks.onSuccess(image.task_id)
      }
    } else if (response.status === 404) {
      // 任务已不存在，直接从前端移除
      console.warn(`任务 ${image.task_id} 在数据库中不存在，从前端移除`)
      if (callbacks.onSuccess) {
        callbacks.onSuccess(image.task_id)
      }
    } else {
      throw new Error(`删除失败 (状态码: ${response.status})`)
    }
  } catch (error) {
    console.error('删除图像失败:', error)
    if (callbacks.onError) {
      callbacks.onError('删除失败，请重试')
    }
  }
}

/**
 * 切换收藏状态
 * @param {Object} image - 图像对象
 * @param {string} API_BASE - API基础URL
 * @param {Object} callbacks - 回调函数对象
 * @returns {Promise} 切换结果
 */
export const toggleFavorite = async (image, API_BASE, callbacks) => {
  try {
    // 调用后端API切换单张图片收藏状态
    const response = await fetch(`${API_BASE}/api/image/${image.task_id}/${image.image_index || 0}/favorite`, {
      method: 'POST'
    })
    
    if (response.ok) {
      const result = await response.json()
      
      if (callbacks.onSuccess) {
        callbacks.onSuccess(result, image)
      }
    } else {
      throw new Error('切换收藏状态失败')
    }
  } catch (error) {
    console.error('切换收藏状态失败:', error)
    if (callbacks.onError) {
      callbacks.onError('操作失败，请重试')
    }
  }
}

/**
 * 切换视频收藏状态
 * @param {Object} video - 视频对象
 * @param {string} API_BASE - API基础URL
 * @param {Object} callbacks - 回调函数对象
 * @returns {Promise} 切换结果
 */
export const toggleVideoFavorite = async (video, API_BASE, callbacks) => {
  try {
    // 调用后端API切换视频收藏状态
    const response = await fetch(`${API_BASE}/api/video/${video.task_id}/favorite`, {
      method: 'POST'
    })
    
    if (response.ok) {
      const result = await response.json()
      
      if (callbacks.onSuccess) {
        callbacks.onSuccess(result, video)
      }
    } else {
      throw new Error('切换收藏状态失败')
    }
  } catch (error) {
    console.error('切换视频收藏状态失败:', error)
    if (callbacks.onError) {
      callbacks.onError('操作失败，请重试')
    }
  }
}

/**
 * 清空历史记录
 * @param {string} API_BASE - API基础URL
 * @param {Object} callbacks - 回调函数对象
 * @returns {Promise} 清空结果
 */
export const clearHistory = async (API_BASE, callbacks) => {
  try {
    // 调用后端清空API
    const response = await fetch(`${API_BASE}/api/history`, {
      method: 'DELETE'
    })
    
    if (response.ok) {
      if (callbacks.onSuccess) {
        callbacks.onSuccess()
      }
    } else {
      throw new Error('清空失败')
    }
  } catch (error) {
    console.error('清空历史记录失败:', error)
    if (callbacks.onError) {
      callbacks.onError('清空失败，请重试')
    }
  }
}
