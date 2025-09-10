/**
 * 缓存优化测试工具
 * 用于测试和验证缓存机制的性能表现
 */

import cacheManager from './cacheManager.js'

class CacheTestSuite {
  constructor() {
    this.testResults = []
    this.mockData = this.generateMockData()
  }

  /**
   * 生成模拟数据
   */
  generateMockData() {
    const tasks = []
    for (let i = 0; i < 50; i++) {
      tasks.push({
        task_id: `test_task_${i}`,
        description: `测试任务 ${i}`,
        created_at: new Date(Date.now() - i * 60000).toISOString(),
        status: 'completed',
        result_path: `/outputs/test_${i}.png`,
        parameters: { model: 'qwen-image', steps: 20 },
        is_favorited: Math.random() > 0.7 ? 1 : 0
      })
    }
    return tasks
  }

  /**
   * 模拟API加载函数
   */
  createMockLoadFunction(delay = 100) {
    return async () => {
      await new Promise(resolve => setTimeout(resolve, delay))
      return {
        data: this.mockData.slice(0, 20),
        totalCount: this.mockData.length,
        hasMore: true
      }
    }
  }

  /**
   * 测试缓存命中性能
   */
  async testCacheHit() {
    console.log('🧪 测试缓存命中性能...')
    
    const startTime = performance.now()
    
    // 第一次加载（无缓存）
    const loadFunction = this.createMockLoadFunction(200)
    const result1 = await cacheManager.smartLoad(loadFunction)
    
    const firstLoadTime = performance.now() - startTime
    
    // 第二次加载（有缓存）
    const startTime2 = performance.now()
    const result2 = await cacheManager.smartLoad(loadFunction)
    const secondLoadTime = performance.now() - startTime2
    
    const improvement = ((firstLoadTime - secondLoadTime) / firstLoadTime * 100).toFixed(1)
    
    this.testResults.push({
      test: '缓存命中性能',
      firstLoad: `${firstLoadTime.toFixed(2)}ms`,
      secondLoad: `${secondLoadTime.toFixed(2)}ms`,
      improvement: `${improvement}%`,
      status: result2.fromCache ? 'PASS' : 'FAIL'
    })
    
    console.log(`✅ 首次加载: ${firstLoadTime.toFixed(2)}ms`)
    console.log(`✅ 缓存加载: ${secondLoadTime.toFixed(2)}ms`)
    console.log(`📈 性能提升: ${improvement}%`)
  }

  /**
   * 测试缓存过期机制
   */
  async testCacheExpiration() {
    console.log('🧪 测试缓存过期机制...')
    
    // 设置较短的缓存时间进行测试
    const originalMaxAge = cacheManager.config.maxCacheAge
    cacheManager.config.maxCacheAge = 1000 // 1秒
    
    const loadFunction = this.createMockLoadFunction(100)
    
    // 第一次加载
    await cacheManager.smartLoad(loadFunction)
    
    // 等待缓存过期
    await new Promise(resolve => setTimeout(resolve, 1100))
    
    // 第二次加载（应该重新请求）
    const result = await cacheManager.smartLoad(loadFunction)
    
    // 恢复原始配置
    cacheManager.config.maxCacheAge = originalMaxAge
    
    this.testResults.push({
      test: '缓存过期机制',
      status: !result.fromCache ? 'PASS' : 'FAIL',
      note: '缓存过期后应重新请求'
    })
    
    console.log(`✅ 缓存过期测试: ${!result.fromCache ? 'PASS' : 'FAIL'}`)
  }

  /**
   * 测试增量更新
   */
  async testIncrementalUpdate() {
    console.log('🧪 测试增量更新机制...')
    
    const cachedData = this.mockData.slice(0, 10)
    const newData = [
      ...this.mockData.slice(0, 8), // 8个现有项目
      ...this.mockData.slice(10, 12), // 2个新项目
      ...this.mockData.slice(8, 10) // 2个更新的项目
    ]
    
    const diff = cacheManager.calculateDataDiff(cachedData, newData)
    
    this.testResults.push({
      test: '增量更新计算',
      newItems: diff.newItems.length,
      updatedItems: diff.updatedItems.length,
      removedItems: diff.removedItems.length,
      isIncremental: diff.isIncremental,
      status: diff.isIncremental ? 'PASS' : 'FAIL'
    })
    
    console.log(`✅ 新项目: ${diff.newItems.length}`)
    console.log(`✅ 更新项目: ${diff.updatedItems.length}`)
    console.log(`✅ 删除项目: ${diff.removedItems.length}`)
    console.log(`✅ 适合增量更新: ${diff.isIncremental}`)
  }

  /**
   * 测试缓存大小限制
   */
  async testCacheSizeLimit() {
    console.log('🧪 测试缓存大小限制...')
    
    const largeData = Array(150).fill().map((_, i) => ({
      task_id: `large_task_${i}`,
      description: `大数据任务 ${i}`,
      created_at: new Date().toISOString(),
      status: 'completed'
    }))
    
    const limitedData = cacheManager.limitCacheSize(largeData)
    
    this.testResults.push({
      test: '缓存大小限制',
      originalSize: largeData.length,
      limitedSize: limitedData.length,
      maxSize: cacheManager.config.maxCacheSize,
      status: limitedData.length <= cacheManager.config.maxCacheSize ? 'PASS' : 'FAIL'
    })
    
    console.log(`✅ 原始大小: ${largeData.length}`)
    console.log(`✅ 限制后大小: ${limitedData.length}`)
    console.log(`✅ 最大限制: ${cacheManager.config.maxCacheSize}`)
  }

  /**
   * 运行所有测试
   */
  async runAllTests() {
    console.log('🚀 开始缓存优化测试套件...')
    console.log('=' * 50)
    
    try {
      await this.testCacheHit()
      await this.testCacheExpiration()
      await this.testIncrementalUpdate()
      await this.testCacheSizeLimit()
      
      this.printResults()
      
    } catch (error) {
      console.error('❌ 测试过程中出现错误:', error)
    }
  }

  /**
   * 打印测试结果
   */
  printResults() {
    console.log('\n📊 测试结果汇总:')
    console.log('=' * 50)
    
    this.testResults.forEach(result => {
      const status = result.status === 'PASS' ? '✅' : '❌'
      console.log(`${status} ${result.test}`)
      
      Object.entries(result).forEach(([key, value]) => {
        if (key !== 'test' && key !== 'status') {
          console.log(`   ${key}: ${value}`)
        }
      })
      console.log('')
    })
    
    const passCount = this.testResults.filter(r => r.status === 'PASS').length
    const totalCount = this.testResults.length
    
    console.log(`🎯 测试通过率: ${passCount}/${totalCount} (${(passCount/totalCount*100).toFixed(1)}%)`)
  }

  /**
   * 性能基准测试
   */
  async benchmarkPerformance() {
    console.log('⚡ 开始性能基准测试...')
    
    const iterations = 10
    const loadFunction = this.createMockLoadFunction(100)
    
    // 测试无缓存性能
    const noCacheTimes = []
    for (let i = 0; i < iterations; i++) {
      cacheManager.clearCache()
      const start = performance.now()
      await loadFunction()
      noCacheTimes.push(performance.now() - start)
    }
    
    // 测试有缓存性能
    const cacheTimes = []
    await cacheManager.smartLoad(loadFunction) // 预热缓存
    for (let i = 0; i < iterations; i++) {
      const start = performance.now()
      await cacheManager.smartLoad(loadFunction)
      cacheTimes.push(performance.now() - start)
    }
    
    const avgNoCache = noCacheTimes.reduce((a, b) => a + b) / iterations
    const avgCache = cacheTimes.reduce((a, b) => a + b) / iterations
    const improvement = ((avgNoCache - avgCache) / avgNoCache * 100).toFixed(1)
    
    console.log(`📈 平均无缓存时间: ${avgNoCache.toFixed(2)}ms`)
    console.log(`📈 平均缓存时间: ${avgCache.toFixed(2)}ms`)
    console.log(`🚀 性能提升: ${improvement}%`)
    
    return {
      avgNoCache,
      avgCache,
      improvement: parseFloat(improvement)
    }
  }
}

// 导出测试套件
export default CacheTestSuite

// 如果直接运行此文件，执行测试
if (typeof window !== 'undefined') {
  window.CacheTestSuite = CacheTestSuite
  console.log('💡 缓存测试套件已加载，使用 new CacheTestSuite().runAllTests() 开始测试')
}
