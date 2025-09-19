/**
 * 格式化工具函数
 */

/**
 * 格式化时间
 * @param {Date} date - 日期对象
 * @returns {string} 格式化后的时间字符串
 */
export const formatTime = (date) => {
  return new Intl.DateTimeFormat('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  }).format(date)
}

/**
 * 防抖函数
 * @param {Function} func - 要防抖的函数
 * @param {number} wait - 等待时间（毫秒）
 * @returns {Function} 防抖后的函数
 */
export const debounce = (func, wait) => {
  let timeout
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout)
      func(...args)
    }
    clearTimeout(timeout)
    timeout = setTimeout(later, wait)
  }
}

/**
 * 滚动到新内容位置
 * @param {number} newContentCount - 新内容数量
 */
export const scrollToNewContent = (newContentCount) => {
  try {
    // 等待DOM完全更新
    setTimeout(() => {
      // 查找新加载的内容元素
      const taskCards = document.querySelectorAll('.task-card')
      if (taskCards.length >= newContentCount) {
        // 滚动到第一个新内容的顶部，留出一些空间
        const targetElement = taskCards[newContentCount - 1]
        if (targetElement) {
          const targetPosition = targetElement.offsetTop - 100 // 留出100px的空间
          window.scrollTo({
            top: targetPosition,
            behavior: 'smooth'
          })
          console.log(`已滚动到新内容位置，新内容数量: ${newContentCount}`)
        }
      }
    }, 200) // 增加延迟确保DOM完全更新
  } catch (error) {
    console.error('滚动到新内容位置失败:', error)
  }
}

/**
 * 安全地滚动到指定位置，不触发滚动事件
 * @param {number} scrollTop - 滚动位置
 * @param {number} delay - 恢复滚动监听器的延迟时间
 */
export const safeScrollTo = (scrollTop, delay = 100) => {
  // 临时禁用滚动监听器，避免触发翻页
  const originalScrollHandler = window.onscroll
  window.onscroll = null
  
  // 直接设置滚动位置，不触发滚动事件
  window.scrollTo(0, scrollTop)
  
  // 恢复滚动监听器
  setTimeout(() => {
    window.onscroll = originalScrollHandler
  }, delay)
}

/**
 * 滚动到底部
 */
export const scrollToBottom = () => {
  safeScrollTo(document.documentElement.scrollHeight)
}

/**
 * 保持滚动位置的辅助函数
 * @param {number} currentScrollTop - 当前滚动位置
 * @param {number} currentScrollHeight - 当前页面高度
 * @param {number} delay - 恢复滚动监听器的延迟时间
 */
export const maintainScrollPosition = (currentScrollTop, currentScrollHeight, delay = 100) => {
  // 等待DOM更新完成
  setTimeout(() => {
    // 计算新的滚动位置：保持相对位置
    const newScrollHeight = document.documentElement.scrollHeight
    const heightDifference = newScrollHeight - currentScrollHeight
    const newScrollTop = currentScrollTop + heightDifference
    
    // 恢复滚动位置，不触发滚动事件
    safeScrollTo(newScrollTop, delay)
    
    console.log(`保持滚动位置: 原位置=${currentScrollTop}, 新位置=${newScrollTop}, 高度差=${heightDifference}`)
  }, 0)
}
