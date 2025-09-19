/**
 * 图像处理工具函数
 */

/**
 * 将文件路径转换为文件对象
 * @param {Array} imagePaths - 图片路径数组
 * @param {string} API_BASE - API基础URL
 * @returns {Array} 文件对象数组
 */
export const convertPathsToFiles = async (imagePaths, API_BASE) => {
  const files = []
  
  for (const path of imagePaths) {
    try {
      const imageUrl = `${API_BASE}/api/image/upload/${path}`
      console.log('正在获取参考图:', imageUrl)
      
      // 获取图片数据
      const response = await fetch(imageUrl)
      if (!response.ok) {
        console.error('获取参考图失败:', response.status, response.statusText)
        continue
      }
      
      const blob = await response.blob()
      
      // 创建文件对象
      const file = new File([blob], path.split('/').pop() || 'reference.png', {
        type: blob.type || 'image/png'
      })
      
      // 创建预览URL
      const preview = URL.createObjectURL(blob)
      
      // 创建符合ant-design-vue Upload组件格式的对象
      const fileObj = {
        uid: `reference-${Date.now()}-${Math.random()}`,
        name: file.name,
        status: 'done',
        url: preview,
        preview: preview,
        originFileObj: file
      }
      
      files.push(fileObj)
      console.log('✅ 参考图转换成功:', file.name)
      
    } catch (error) {
      console.error('转换参考图失败:', error, '路径:', path)
    }
  }
  
  return files
}

/**
 * 处理任务图片数据
 * @param {Object} task - 任务数据
 * @param {string} API_BASE - API基础URL
 * @returns {Array} 处理后的图片数组
 */
export const processTaskImages = (task, API_BASE) => {
  try {
    if (!task || !task.task_id) {
      console.warn('无效的任务数据:', task)
      return []
    }
    
    // 对于失败的任务，返回一个表示失败状态的图片对象
    if (task.status === 'failed') {
      return [{
        url: null, // 失败的任务没有图片URL
        directUrl: null,
        filename: `failed_${task.task_id}.png`,
        task_id: task.task_id,
        prompt: task.description || '',
        createdAt: new Date(task.created_at || Date.now()),
        referenceImage: task.reference_image_path ? (Array.isArray(task.reference_image_path) ? JSON.stringify(task.reference_image_path.map(path => `${API_BASE}/api/image/upload/${path.replace(/^uploads[\/\\]/, '').replace(/\\/g, '/').replace(/\/\//g, '/')}`)) : `${API_BASE}/api/image/upload/${task.reference_image_path.replace(/^uploads[\/\\]/, '').replace(/\\/g, '/').replace(/\/\//g, '/')}`) : null,
        isFavorited: task.is_favorited === 1 || task.is_favorited === true,
        status: 'failed',
        error: task.error || '生成失败',
        parameters: task.parameters || {},  // 添加任务参数信息
        result_path: task.result_path  // 保留result_path字段
      }]
    }
    
    // 对于其他非完成状态，也返回一个状态对象
    if (task.status !== 'completed') {
      return [{
        url: null,
        directUrl: null,
        filename: `${task.status}_${task.task_id}.png`,
        task_id: task.task_id,
        prompt: task.description || '',
        createdAt: new Date(task.created_at || Date.now()),
        referenceImage: task.reference_image_path ? (Array.isArray(task.reference_image_path) ? JSON.stringify(task.reference_image_path.map(path => `${API_BASE}/api/image/upload/${path.replace(/^uploads[\/\\]/, '').replace(/\\/g, '/').replace(/\/\//g, '/')}`)) : `${API_BASE}/api/image/upload/${task.reference_image_path.replace(/^uploads[\/\\]/, '').replace(/\\/g, '/').replace(/\/\//g, '/')}`) : null,
        isFavorited: task.is_favorited === 1 || task.is_favorited === true,
        status: task.status,
        error: task.error || `状态: ${task.status}`,
        parameters: task.parameters || {},  // 添加任务参数信息
        result_path: task.result_path  // 保留result_path字段
      }]
    }
    
    // 检查是否有image_urls数组
    if (!task.image_urls || !Array.isArray(task.image_urls) || task.image_urls.length === 0) {
      console.warn('任务没有有效的image_urls:', task)
      return []
    }
    
    // 获取参考图信息
    let referenceImageUrl = null
    if (task.reference_image_path && task.reference_image_path !== 'uploads/blank.png' && task.reference_image_path !== 'uploads\\blank.png') {
      // 处理多图融合的情况，reference_image_path可能是数组
      let referencePath = task.reference_image_path
      if (Array.isArray(referencePath)) {
        // 多图融合时，处理所有参考图路径
        const cleanPaths = referencePath.map(path => {
          let cleanPath = path
          
          // 处理uploads/或uploads\前缀
          if (cleanPath.startsWith('uploads/') || cleanPath.startsWith('uploads\\')) {
            // 去掉uploads/或uploads\前缀
            cleanPath = cleanPath.replace(/^uploads[\/\\]/, '')
          }
          
          // 将Windows路径分隔符转换为URL路径分隔符
          cleanPath = cleanPath.replace(/\\/g, '/')
          
          // 处理双斜杠问题
          cleanPath = cleanPath.replace(/\/\//g, '/')
          
          return `${API_BASE}/api/image/upload/${cleanPath}`
        })
        
        // 多图融合时，将完整的URL数组作为JSON字符串传递
        referenceImageUrl = JSON.stringify(cleanPaths)
      } else {
        // 单图情况，保持原有逻辑
        let cleanPath = referencePath
        
        // 处理uploads/或uploads\前缀
        if (cleanPath.startsWith('uploads/') || cleanPath.startsWith('uploads\\')) {
          // 去掉uploads/或uploads\前缀
          cleanPath = cleanPath.replace(/^uploads[\/\\]/, '')
        }
        
        // 将Windows路径分隔符转换为URL路径分隔符
        cleanPath = cleanPath.replace(/\\/g, '/')
        
        // 处理双斜杠问题
        cleanPath = cleanPath.replace(/\/\//g, '/')
        
        referenceImageUrl = `${API_BASE}/api/image/upload/${cleanPath}`
      }
    }
    
    // 处理image_urls数组，使用后端提供的收藏状态
    const images = task.image_urls.map((imageUrl, index) => {
      try {
        // 从后端提供的images数组中获取收藏状态
        let isFavorited = false
        if (task.images && Array.isArray(task.images)) {
          const imageData = task.images.find(img => img.image_index === index)
          if (imageData) {
            isFavorited = imageData.isFavorited || false
          }
        }
        
        return {
          url: imageUrl,
          directUrl: null,
          thumbnailUrl: task.thumbnail_urls && task.thumbnail_urls[index] ? `${API_BASE}${task.thumbnail_urls[index]}` : null,
          filename: `generated_${task.task_id}_${index + 1}.png`,
          task_id: task.task_id,
          image_index: index, // 使用与后端一致的字段名
          prompt: task.description || '',
          createdAt: new Date(task.created_at || Date.now()),
          referenceImage: referenceImageUrl,
          isFavorited: isFavorited,  // 使用后端提供的收藏状态
          parameters: task.parameters || {},  // 添加任务参数信息
          result_path: task.result_path  // 保留result_path字段
        }
      } catch (imageError) {
        console.error('处理单个图片数据失败:', imageError, { imageUrl, index, task })
        return null
      }
    }).filter(img => img !== null) // 过滤掉处理失败的图片
    
    return images
  } catch (error) {
    console.error('processTaskImages 函数执行失败:', error, task)
    return []
  }
}

/**
 * 下载图像
 * @param {Object} image - 图像对象
 */
export const downloadImage = async (image) => {
  try {
    // 使用直接URL或常规URL
    const imageUrl = image.directUrl || image.url
    const filename = image.filename || `ai-generated-${Date.now()}.png`
    
    // 创建一个临时链接
    const link = document.createElement('a')
    link.href = imageUrl
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    return { success: true, filename }
  } catch (error) {
    console.error('下载失败:', error)
    return { success: false, error: error.message }
  }
}

/**
 * 下载全部图片
 * @param {Array} group - 图片组
 */
export const downloadAllImages = async (group) => {
  try {
    for (let i = 0; i < group.length; i++) {
      const image = group[i]
      const response = await fetch(image.url)
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `ai-generated-${image.task_id}-${i + 1}.png`
      link.click()
      window.URL.revokeObjectURL(url)
      
      // 添加延迟避免浏览器阻止多个下载
      if (i < group.length - 1) {
        await new Promise(resolve => setTimeout(resolve, 500))
      }
    }
    return { success: true, count: group.length }
  } catch (error) {
    console.error('批量下载失败:', error)
    return { success: false, error: error.message }
  }
}

/**
 * 分享图像
 * @param {Object} image - 图像对象
 */
export const shareImage = (image) => {
  if (navigator.share) {
    navigator.share({
      title: 'AI生成的图像',
      text: image.prompt,
      url: image.url
    })
  } else {
    navigator.clipboard.writeText(image.url)
    return { success: true, method: 'clipboard' }
  }
}
