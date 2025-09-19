/**
 * 轮询服务模块
 */

/**
 * 轮询放大任务状态
 * @param {string} taskId - 任务ID
 * @param {string} API_BASE - API基础URL
 * @param {Object} callbacks - 回调函数对象
 * @returns {Promise} 轮询结果
 */
export const pollUpscaleStatus = async (taskId, API_BASE, callbacks) => {
  const maxAttempts = 180  // 增加到180次（6分钟）
  let attempts = 0
  let consecutiveErrors = 0
  
  console.log(`🚀 开始轮询任务状态: ${taskId}`)
  
  const checkStatus = async () => {
    try {
      console.log(`🔍 检查任务状态 (${attempts + 1}/${maxAttempts}): ${taskId}`)
      
      const response = await fetch(`${API_BASE}/api/upscale/${taskId}`, {
        cache: 'no-cache',  // 强制不使用缓存
        headers: {
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache'
        }
      })
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
      
      const status = await response.json()
      consecutiveErrors = 0  // 重置错误计数
      
      console.log(`📊 任务状态: ${JSON.stringify(status)}`)
      
      // 使用后端返回的真实进度，而不是自己计算
      if (callbacks.onProgress) {
        callbacks.onProgress(status.progress || 50)
      }
      
      if (status.status === 'completed') {
        if (callbacks.onProgress) {
          callbacks.onProgress(100)
        }
        console.log('✅ 任务完成！')
        
        if (callbacks.onSuccess) {
          await callbacks.onSuccess(status)
        }
        return
      } else if (status.status === 'failed') {
        console.log('❌ 任务失败')
        if (callbacks.onError) {
          callbacks.onError('图片放大失败')
        }
        return
      }
      
      // 任务仍在处理中
      attempts++
      if (attempts < maxAttempts) {
        setTimeout(checkStatus, 1000) // 1秒轮询
      } else {
        console.log('⏰ 轮询超时')
        if (callbacks.onTimeout) {
          callbacks.onTimeout()
        }
      }
    } catch (error) {
      consecutiveErrors++
      console.error(`❌ 检查放大状态失败 (连续错误: ${consecutiveErrors}):`, error)
      
      // 如果连续错误太多，可能是严重问题
      if (consecutiveErrors >= 5) {
        console.log('❌ 连续错误过多，终止轮询')
        if (callbacks.onError) {
          callbacks.onError('网络连接异常，请检查网络后手动刷新页面')
        }
        return
      }
      
      // 网络错误或临时问题，继续重试
      attempts++
      if (attempts < maxAttempts) {
        console.log(`🔄 网络错误重试 (${attempts}/${maxAttempts})，${consecutiveErrors} 连续错误`)
        setTimeout(checkStatus, 2000) // 网络错误时等待2秒再重试
      } else {
        console.log('❌ 重试次数用尽')
        if (callbacks.onError) {
          callbacks.onError('放大任务检查超时，请手动刷新页面查看结果')
        }
      }
    }
  }
  
  await checkStatus()
}

/**
 * 轮询视频生成任务状态
 * @param {string} taskId - 任务ID
 * @param {string} API_BASE - API基础URL
 * @param {Object} callbacks - 回调函数对象
 * @returns {Promise} 轮询结果
 */
export const pollVideoStatus = async (taskId, API_BASE, callbacks) => {
  const maxAttempts = 300  // 5分钟轮询
  let attempts = 0
  let consecutiveErrors = 0
  
  const checkStatus = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/task/${taskId}`, {
        cache: 'no-cache',
        headers: {
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache'
        }
      })
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
      
      const status = await response.json()
      consecutiveErrors = 0
      
      if (status.status === 'completed') {
        console.log('✅ 视频生成完成！')
        if (callbacks.onSuccess) {
          await callbacks.onSuccess(status)
        }
        return
      } else if (status.status === 'failed') {
        console.log('❌ 视频生成失败')
        if (callbacks.onError) {
          callbacks.onError('视频生成失败')
        }
        return
      }
      
      // 任务仍在处理中
      attempts++
      if (attempts < maxAttempts) {
        setTimeout(checkStatus, 2000) // 2秒轮询
      } else {
        console.log('⏰ 视频轮询超时')
        if (callbacks.onTimeout) {
          callbacks.onTimeout()
        }
      }
    } catch (error) {
      consecutiveErrors++
      console.error(`❌ 检查视频状态失败 (连续错误: ${consecutiveErrors}):`, error)
      
      // 如果连续错误太多，可能是严重问题
      if (consecutiveErrors >= 5) {
        console.log('❌ 连续错误过多，终止视频轮询')
        if (callbacks.onError) {
          callbacks.onError('网络连接异常，请检查网络后手动刷新页面')
        }
        return
      }
      
      // 网络错误或临时问题，继续重试
      attempts++
      if (attempts < maxAttempts) {
        console.log(`🔄 网络错误重试 (${attempts}/${maxAttempts})，${consecutiveErrors} 连续错误`)
        setTimeout(checkStatus, 2000) // 网络错误时等待2秒再重试
      } else {
        console.log('❌ 重试次数用尽')
        if (callbacks.onError) {
          callbacks.onError('视频任务检查超时，请手动刷新页面查看结果')
        }
      }
    }
  }
  
  await checkStatus()
}

/**
 * 轮询任务状态（通用）
 * @param {string} taskId - 任务ID
 * @param {string} API_BASE - API基础URL
 * @param {Object} callbacks - 回调函数对象
 * @returns {Promise} 轮询结果
 */
export const pollTaskStatus = async (taskId, API_BASE, callbacks) => {
  const maxAttempts = 120  // 2分钟轮询
  let attempts = 0
  let consecutiveErrors = 0
  
  const checkStatus = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/task/${taskId}`, {
        cache: 'no-cache',
        headers: {
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache'
        }
      })
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
      
      const status = await response.json()
      consecutiveErrors = 0
      
      if (callbacks.onProgress) {
        callbacks.onProgress(status.progress || 0)
      }
      
      if (status.status === 'completed') {
        if (callbacks.onSuccess) {
          await callbacks.onSuccess(status)
        }
        return
      } else if (status.status === 'failed') {
        if (callbacks.onError) {
          callbacks.onError(status.error || '任务失败')
        }
        return
      }
      
      // 任务仍在处理中
      attempts++
      if (attempts < maxAttempts) {
        setTimeout(checkStatus, 2000) // 2秒轮询
      } else {
        console.log('⏰ 任务轮询超时')
        if (callbacks.onTimeout) {
          callbacks.onTimeout()
        }
      }
    } catch (error) {
      consecutiveErrors++
      console.error(`❌ 检查任务状态失败 (连续错误: ${consecutiveErrors}):`, error)
      
      // 如果连续错误太多，可能是严重问题
      if (consecutiveErrors >= 5) {
        console.log('❌ 连续错误过多，终止任务轮询')
        if (callbacks.onError) {
          callbacks.onError('网络连接异常，请检查网络后手动刷新页面')
        }
        return
      }
      
      // 网络错误或临时问题，继续重试
      attempts++
      if (attempts < maxAttempts) {
        console.log(`🔄 网络错误重试 (${attempts}/${maxAttempts})，${consecutiveErrors} 连续错误`)
        setTimeout(checkStatus, 2000) // 网络错误时等待2秒再重试
      } else {
        console.log('❌ 重试次数用尽')
        if (callbacks.onError) {
          callbacks.onError('任务检查超时，请手动刷新页面查看结果')
        }
      }
    }
  }
  
  await checkStatus()
}
