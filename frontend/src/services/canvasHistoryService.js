/**
 * 画布历史记录服务
 */
export class CanvasHistoryService {
  /**
   * 保存历史记录到云端
   * @param {Object} record - 历史记录对象
   * @returns {Promise<Object>} 保存结果
   */
  static async saveHistoryRecord(record) {
    try {
      console.log('💾 保存历史记录到云端:', record)
      
      const response = await fetch('/api/canvas/history', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          id: record.id,
          task_id: record.task_id || record.id,
          prompt: record.prompt,
          original_image_url: record.originalImageUrl,
          result_image_url: record.resultImageUrl,
          parameters: record.parameters,
          timestamp: record.timestamp,
          type: record.type || 'inpainting'
        })
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const data = await response.json()
      console.log('✅ 历史记录保存成功:', data)
      return data
    } catch (error) {
      console.error('❌ 保存历史记录失败:', error)
      throw error
    }
  }

  /**
   * 获取历史记录列表
   * @param {Object} params - 查询参数
   * @returns {Promise<Array>} 历史记录列表
   */
  static async getHistoryRecords(params = {}) {
    try {
      console.log('📋 获取历史记录列表:', params)
      
      const queryString = new URLSearchParams(params).toString()
      const url = `/api/canvas/history${queryString ? `?${queryString}` : ''}`
      
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const data = await response.json()
      console.log('✅ 历史记录获取成功:', data)
      return data
    } catch (error) {
      console.error('❌ 获取历史记录失败:', error)
      throw error
    }
  }

  /**
   * 更新历史记录
   * @param {string} id - 历史记录ID
   * @param {Object} updates - 更新数据
   * @returns {Promise<Object>} 更新结果
   */
  static async updateHistoryRecord(id, updates) {
    try {
      console.log('🔄 更新历史记录:', id, updates)
      
      const response = await fetch(`/api/canvas/history/${id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(updates)
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const data = await response.json()
      console.log('✅ 历史记录更新成功:', data)
      return data
    } catch (error) {
      console.error('❌ 更新历史记录失败:', error)
      throw error
    }
  }

  /**
   * 删除历史记录
   * @param {string} id - 历史记录ID
   * @returns {Promise<Object>} 删除结果
   */
  static async deleteHistoryRecord(id) {
    try {
      console.log('🗑️ 删除历史记录:', id)
      
      const response = await fetch(`/api/canvas/history/${id}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json'
        }
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const data = await response.json()
      console.log('✅ 历史记录删除成功:', data)
      return data
    } catch (error) {
      console.error('❌ 删除历史记录失败:', error)
      throw error
    }
  }

  /**
   * 批量保存历史记录
   * @param {Array} records - 历史记录数组
   * @returns {Promise<Array>} 保存结果
   */
  static async batchSaveHistoryRecords(records) {
    try {
      console.log('💾 批量保存历史记录:', records.length, '条')
      
      const response = await fetch('/api/canvas/history/batch', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          records: records.map(record => ({
            id: record.id,
            task_id: record.task_id || record.id,
            prompt: record.prompt,
            original_image_url: record.originalImageUrl,
            result_image_url: record.resultImageUrl,
            parameters: record.parameters,
            timestamp: record.timestamp,
            type: record.type || 'inpainting'
          }))
        })
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const data = await response.json()
      console.log('✅ 批量保存成功:', data)
      return data
    } catch (error) {
      console.error('❌ 批量保存失败:', error)
      throw error
    }
  }
}

/**
 * 离线存储管理
 */
export class OfflineHistoryManager {
  constructor() {
    this.storageKey = 'canvas_history_offline'
    this.maxOfflineRecords = 50
  }

  /**
   * 保存到离线存储
   * @param {Object} record - 历史记录
   */
  saveOffline(record) {
    try {
      const offlineRecords = this.getOfflineRecords()
      offlineRecords.push({
        ...record,
        offline: true,
        offlineTimestamp: Date.now()
      })
      
      // 限制离线记录数量
      if (offlineRecords.length > this.maxOfflineRecords) {
        offlineRecords.splice(0, offlineRecords.length - this.maxOfflineRecords)
      }
      
      localStorage.setItem(this.storageKey, JSON.stringify(offlineRecords))
      console.log('💾 保存到离线存储:', record.id)
    } catch (error) {
      console.error('❌ 离线存储失败:', error)
    }
  }

  /**
   * 获取离线记录
   * @returns {Array} 离线记录列表
   */
  getOfflineRecords() {
    try {
      const data = localStorage.getItem(this.storageKey)
      return data ? JSON.parse(data) : []
    } catch (error) {
      console.error('❌ 获取离线记录失败:', error)
      return []
    }
  }

  /**
   * 清除离线记录
   */
  clearOfflineRecords() {
    try {
      localStorage.removeItem(this.storageKey)
      console.log('🧹 清除离线记录')
    } catch (error) {
      console.error('❌ 清除离线记录失败:', error)
    }
  }

  /**
   * 同步离线记录到云端
   * @returns {Promise<Array>} 同步结果
   */
  async syncOfflineRecords() {
    try {
      const offlineRecords = this.getOfflineRecords()
      if (offlineRecords.length === 0) {
        return []
      }

      console.log('🔄 同步离线记录到云端:', offlineRecords.length, '条')
      
      const results = await CanvasHistoryService.batchSaveHistoryRecords(offlineRecords)
      
      // 同步成功后清除离线记录
      this.clearOfflineRecords()
      
      console.log('✅ 离线记录同步成功')
      return results
    } catch (error) {
      console.error('❌ 离线记录同步失败:', error)
      throw error
    }
  }
}

// 导出单例实例
export const offlineManager = new OfflineHistoryManager()
