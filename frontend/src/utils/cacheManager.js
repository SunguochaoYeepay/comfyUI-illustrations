/**
 * 生图列表缓存管理器
 * 实现智能缓存 + 增量更新机制
 */

class HistoryCacheManager {
  constructor() {
    this.CACHE_KEY = 'yeepay_history_cache'
    this.CACHE_META_KEY = 'yeepay_cache_meta'
    this.CACHE_VERSION = '1.0'
    
    // 缓存配置
    this.config = {
      maxCacheAge: 5 * 60 * 1000, // 5分钟缓存有效期
      maxCacheSize: 100, // 最多缓存100条记录
      incrementalThreshold: 10, // 超过10条新数据时强制全量刷新
      staleThreshold: 2 * 60 * 1000, // 2分钟后标记为过期但仍可使用
    }
  }

  /**
   * 获取缓存元数据
   */
  getCacheMeta() {
    try {
      const metaStr = localStorage.getItem(this.CACHE_META_KEY)
      if (!metaStr) return null
      
      const meta = JSON.parse(metaStr)
      
      // 检查缓存版本
      if (meta.version !== this.CACHE_VERSION) {
        this.clearCache()
        return null
      }
      
      return meta
    } catch (error) {
      console.warn('获取缓存元数据失败:', error)
      return null
    }
  }

  /**
   * 设置缓存元数据
   */
  setCacheMeta(meta) {
    try {
      const metaData = {
        ...meta,
        version: this.CACHE_VERSION,
        timestamp: Date.now()
      }
      localStorage.setItem(this.CACHE_META_KEY, JSON.stringify(metaData))
    } catch (error) {
      console.warn('设置缓存元数据失败:', error)
    }
  }

  /**
   * 获取缓存数据
   */
  getCacheData() {
    try {
      const dataStr = localStorage.getItem(this.CACHE_KEY)
      if (!dataStr) return null
      
      const data = JSON.parse(dataStr)
      const meta = this.getCacheMeta()
      
      if (!meta) {
        this.clearCache()
        return null
      }
      
      return {
        data,
        meta
      }
    } catch (error) {
      console.warn('获取缓存数据失败:', error)
      this.clearCache()
      return null
    }
  }

  /**
   * 设置缓存数据
   */
  setCacheData(data, meta) {
    try {
      // 限制缓存大小
      const limitedData = this.limitCacheSize(data)
      
      localStorage.setItem(this.CACHE_KEY, JSON.stringify(limitedData))
      this.setCacheMeta(meta)
      
      console.log(`💾 缓存已更新: ${limitedData.length} 条记录`)
    } catch (error) {
      console.warn('设置缓存数据失败:', error)
    }
  }

  /**
   * 限制缓存大小
   */
  limitCacheSize(data) {
    if (data.length <= this.config.maxCacheSize) {
      return data
    }
    
    // 保留最新的记录
    return data.slice(0, this.config.maxCacheSize)
  }

  /**
   * 检查缓存是否有效
   */
  isCacheValid() {
    const meta = this.getCacheMeta()
    if (!meta) return false
    
    const now = Date.now()
    const age = now - meta.timestamp
    
    return age < this.config.maxCacheAge
  }

  /**
   * 检查缓存是否过期但仍可使用
   */
  isCacheStale() {
    const meta = this.getCacheMeta()
    if (!meta) return false
    
    const now = Date.now()
    const age = now - meta.timestamp
    
    return age >= this.config.maxCacheAge && age < this.config.staleThreshold
  }

  /**
   * 清除缓存
   */
  clearCache() {
    try {
      localStorage.removeItem(this.CACHE_KEY)
      localStorage.removeItem(this.CACHE_META_KEY)
      console.log('🧹 缓存已清除')
    } catch (error) {
      console.warn('清除缓存失败:', error)
    }
  }

  /**
   * 计算数据差异，确定是否需要增量更新
   */
  calculateDataDiff(cachedData, newData) {
    if (!cachedData || cachedData.length === 0) {
      return {
        isIncremental: false,
        newItems: newData,
        updatedItems: [],
        removedItems: []
      }
    }

    // 创建缓存数据的映射
    const cachedMap = new Map()
    cachedData.forEach(item => {
      cachedMap.set(item.task_id, item)
    })

    // 分析新数据
    const newItems = []
    const updatedItems = []
    const existingItems = []

    newData.forEach(item => {
      const cachedItem = cachedMap.get(item.task_id)
      if (!cachedItem) {
        // 新项目
        newItems.push(item)
      } else {
        // 检查是否有更新
        if (this.hasItemChanged(cachedItem, item)) {
          updatedItems.push(item)
        }
        existingItems.push(item)
      }
    })

    // 找出被删除的项目
    const newMap = new Map()
    newData.forEach(item => {
      newMap.set(item.task_id, item)
    })
    
    const removedItems = cachedData.filter(item => 
      !newMap.has(item.task_id)
    )

    // 判断是否适合增量更新
    const isIncremental = newItems.length <= this.config.incrementalThreshold && 
                         updatedItems.length <= this.config.incrementalThreshold &&
                         removedItems.length <= this.config.incrementalThreshold

    return {
      isIncremental,
      newItems,
      updatedItems,
      removedItems,
      existingItems
    }
  }

  /**
   * 检查项目是否有变化
   */
  hasItemChanged(oldItem, newItem) {
    // 比较关键字段
    const keyFields = ['status', 'is_favorited', 'updated_at', 'result_path']
    
    for (const field of keyFields) {
      if (oldItem[field] !== newItem[field]) {
        return true
      }
    }
    
    return false
  }

  /**
   * 执行增量更新
   */
  performIncrementalUpdate(cachedData, diff) {
    const { newItems, updatedItems, removedItems, existingItems } = diff
    
    // 创建现有项目的映射
    const existingMap = new Map()
    existingItems.forEach(item => {
      existingMap.set(item.task_id, item)
    })

    // 合并数据：新项目 + 更新项目 + 现有项目
    const mergedData = [
      ...newItems,
      ...updatedItems,
      ...existingItems.filter(item => !newItems.some(ni => ni.task_id === item.task_id))
    ]

    // 按时间排序
    mergedData.sort((a, b) => new Date(b.created_at) - new Date(a.created_at))

    console.log(`🔄 增量更新完成: +${newItems.length} 更新${updatedItems.length} 删除${removedItems.length}`)
    
    return mergedData
  }

  /**
   * 智能加载策略
   */
  async smartLoad(loadFunction, options = {}) {
    const { forceRefresh = false, useCache = true } = options
    
    // 如果强制刷新，直接加载
    if (forceRefresh) {
      console.log('🔄 强制刷新，跳过缓存')
      const result = await loadFunction()
      this.setCacheData(result.data, {
        lastUpdate: Date.now(),
        totalCount: result.totalCount,
        hasMore: result.hasMore
      })
      return result
    }

    // 检查缓存
    if (useCache) {
      const cached = this.getCacheData()
      
      if (cached && this.isCacheValid()) {
        console.log('✅ 使用有效缓存')
        return {
          data: cached.data,
          meta: cached.meta,
          fromCache: true
        }
      }
      
      if (cached && this.isCacheStale()) {
        console.log('⚠️ 使用过期缓存，后台更新')
        // 使用过期缓存，但后台更新
        this.updateInBackground(loadFunction)
        return {
          data: cached.data,
          meta: cached.meta,
          fromCache: true,
          stale: true
        }
      }
    }

    // 缓存无效或不存在，重新加载
    console.log('🔄 缓存无效，重新加载')
    const result = await loadFunction()
    this.setCacheData(result.data, {
      lastUpdate: Date.now(),
      totalCount: result.totalCount,
      hasMore: result.hasMore
    })
    
    return result
  }

  /**
   * 后台更新缓存
   */
  async updateInBackground(loadFunction) {
    try {
      const result = await loadFunction()
      this.setCacheData(result.data, {
        lastUpdate: Date.now(),
        totalCount: result.totalCount,
        hasMore: result.hasMore
      })
      console.log('🔄 后台更新完成')
    } catch (error) {
      console.warn('后台更新失败:', error)
    }
  }
}

// 创建单例实例
const cacheManager = new HistoryCacheManager()

export default cacheManager
