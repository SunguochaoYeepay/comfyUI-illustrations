/**
 * 画布历史记录服务测试
 * 注意：这是基础测试，实际使用时需要后端API支持
 */

import { CanvasHistoryService, OfflineHistoryManager } from '../canvasHistoryService.js'

// Mock API
const mockApi = {
  post: jest.fn(),
  get: jest.fn(),
  put: jest.fn(),
  delete: jest.fn()
}

// 模拟测试数据
const mockHistoryRecord = {
  id: 'test-123',
  task_id: 'task-456',
  prompt: '测试提示词',
  originalImageUrl: 'https://example.com/original.jpg',
  resultImageUrl: 'https://example.com/result.jpg',
  parameters: { steps: 20, cfg: 7.5 },
  timestamp: Date.now(),
  type: 'inpainting'
}

describe('CanvasHistoryService', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('saveHistoryRecord', () => {
    it('应该正确保存历史记录', async () => {
      mockApi.post.mockResolvedValue({ data: { success: true } })
      
      const result = await CanvasHistoryService.saveHistoryRecord(mockHistoryRecord)
      
      expect(mockApi.post).toHaveBeenCalledWith('/canvas/history', {
        id: mockHistoryRecord.id,
        task_id: mockHistoryRecord.task_id,
        prompt: mockHistoryRecord.prompt,
        original_image_url: mockHistoryRecord.originalImageUrl,
        result_image_url: mockHistoryRecord.resultImageUrl,
        parameters: mockHistoryRecord.parameters,
        timestamp: mockHistoryRecord.timestamp,
        type: mockHistoryRecord.type
      })
      
      expect(result).toEqual({ success: true })
    })

    it('应该处理保存失败的情况', async () => {
      mockApi.post.mockRejectedValue(new Error('网络错误'))
      
      await expect(CanvasHistoryService.saveHistoryRecord(mockHistoryRecord))
        .rejects.toThrow('网络错误')
    })
  })

  describe('getHistoryRecords', () => {
    it('应该正确获取历史记录列表', async () => {
      const mockResponse = [mockHistoryRecord]
      mockApi.get.mockResolvedValue({ data: mockResponse })
      
      const result = await CanvasHistoryService.getHistoryRecords()
      
      expect(mockApi.get).toHaveBeenCalledWith('/canvas/history', { params: {} })
      expect(result).toEqual(mockResponse)
    })
  })

  describe('deleteHistoryRecord', () => {
    it('应该正确删除历史记录', async () => {
      mockApi.delete.mockResolvedValue({ data: { success: true } })
      
      const result = await CanvasHistoryService.deleteHistoryRecord('test-123')
      
      expect(mockApi.delete).toHaveBeenCalledWith('/canvas/history/test-123')
      expect(result).toEqual({ success: true })
    })
  })
})

describe('OfflineHistoryManager', () => {
  let offlineManager

  beforeEach(() => {
    offlineManager = new OfflineHistoryManager()
    localStorage.clear()
  })

  describe('saveOffline', () => {
    it('应该保存到离线存储', () => {
      offlineManager.saveOffline(mockHistoryRecord)
      
      const saved = offlineManager.getOfflineRecords()
      expect(saved).toHaveLength(1)
      expect(saved[0]).toMatchObject({
        ...mockHistoryRecord,
        offline: true
      })
    })

    it('应该限制离线记录数量', () => {
      // 保存超过限制数量的记录
      for (let i = 0; i < 60; i++) {
        offlineManager.saveOffline({
          ...mockHistoryRecord,
          id: `test-${i}`
        })
      }
      
      const saved = offlineManager.getOfflineRecords()
      expect(saved).toHaveLength(50) // 应该只保留最新的50条
    })
  })

  describe('getOfflineRecords', () => {
    it('应该返回空数组当没有离线记录时', () => {
      const records = offlineManager.getOfflineRecords()
      expect(records).toEqual([])
    })

    it('应该返回保存的离线记录', () => {
      offlineManager.saveOffline(mockHistoryRecord)
      const records = offlineManager.getOfflineRecords()
      expect(records).toHaveLength(1)
    })
  })

  describe('clearOfflineRecords', () => {
    it('应该清除所有离线记录', () => {
      offlineManager.saveOffline(mockHistoryRecord)
      expect(offlineManager.getOfflineRecords()).toHaveLength(1)
      
      offlineManager.clearOfflineRecords()
      expect(offlineManager.getOfflineRecords()).toHaveLength(0)
    })
  })
})

// 集成测试示例
describe('集成测试', () => {
  it('应该能够处理完整的离线到在线同步流程', async () => {
    const offlineManager = new OfflineHistoryManager()
    
    // 1. 离线状态下保存记录
    offlineManager.saveOffline(mockHistoryRecord)
    expect(offlineManager.getOfflineRecords()).toHaveLength(1)
    
    // 2. 模拟网络恢复，同步到云端
    mockApi.post.mockResolvedValue({ data: { success: true } })
    
    const results = await offlineManager.syncOfflineRecords()
    expect(results).toBeDefined()
    expect(offlineManager.getOfflineRecords()).toHaveLength(0) // 同步后应该清空
  })
})
