import axios from 'axios'

// 创建axios实例
const api = axios.create({
  baseURL: '/api/admin',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器 - 添加认证token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器 - 处理错误
api.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    // 暂时移除自动跳转登录页的逻辑
    // if (error.response?.status === 401) {
    //   // 未授权，跳转到登录页
    //   localStorage.removeItem('access_token')
    //   window.location.href = '/login'
    // }
    return Promise.reject(error)
  }
)

// 备份API
export const backupApi = {
  // 创建备份
  createBackup: (data) => {
    return api.post('/backup/create', data)
  },

  // 获取备份列表
  getBackupList: (params = {}) => {
    return api.get('/backup/list', { params })
  },

  // 下载备份
  downloadBackup: (backupId) => {
    return api.get(`/backup/download/${backupId}`, {
      responseType: 'blob'
    }).then(response => {
      // 创建下载链接
      const url = window.URL.createObjectURL(new Blob([response]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `backup_${backupId}.zip`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    })
  },

  // 恢复备份
  restoreBackup: (backupId, data) => {
    return api.post(`/backup/restore/${backupId}`, data)
  },

  // 删除备份
  deleteBackup: (backupId) => {
    return api.delete(`/backup/${backupId}`)
  },

  // 获取备份状态
  getBackupStatus: () => {
    return api.get('/backup/status')
  },

  // 清理过期备份
  cleanupBackups: (retentionDays = 30) => {
    return api.post('/backup/cleanup', null, {
      params: { retention_days: retentionDays }
    })
  },

  // 创建自动备份调度
  createSchedule: (data) => {
    return api.post('/backup/schedule', data)
  },

  // 获取自动备份调度列表
  getSchedules: () => {
    return api.get('/backup/schedule')
  },

  // 更新自动备份调度
  updateSchedule: (scheduleId, data) => {
    return api.put(`/backup/schedule/${scheduleId}`, data)
  },

  // 删除自动备份调度
  deleteSchedule: (scheduleId) => {
    return api.delete(`/backup/schedule/${scheduleId}`)
  },

  // 启动备份调度器
  startScheduler: () => {
    return api.post('/backup/scheduler/start')
  },

  // 停止备份调度器
  stopScheduler: () => {
    return api.post('/backup/scheduler/stop')
  },

  // 获取调度器状态
  getSchedulerStatus: () => {
    return api.get('/backup/scheduler/status')
  }
}

export default backupApi
