<template>
  <div class="backup-management">
    <!-- 页面标题和操作栏 -->
    <div class="header-bar">
      <h1>数据备份管理</h1>
      <div class="header-actions">
        <a-select
          v-model:value="backupTypeFilter"
          placeholder="备份类型筛选"
          style="width: 150px; margin-right: 8px;"
          @change="onBackupTypeFilter"
          allow-clear
        >
          <a-select-option value="all">全部类型</a-select-option>
          <a-select-option value="full">全量备份</a-select-option>
          <a-select-option value="main_service">主服务备份</a-select-option>
          <a-select-option value="admin_service">Admin服务备份</a-select-option>
        </a-select>
        <a-select
          v-model:value="statusFilter"
          placeholder="状态筛选"
          style="width: 120px; margin-right: 8px;"
          @change="onStatusFilter"
          allow-clear
        >
          <a-select-option value="all">全部状态</a-select-option>
          <a-select-option value="completed">已完成</a-select-option>
          <a-select-option value="running">进行中</a-select-option>
          <a-select-option value="failed">失败</a-select-option>
        </a-select>
        <a-button type="primary" @click="showCreateModal" style="margin-right: 8px;">
          <plus-outlined /> 创建备份
        </a-button>
        <a-button @click="showAutoBackupDrawer" style="margin-right: 8px;">
          <setting-outlined /> 自动备份
        </a-button>
        <a-button @click="loadBackups" :loading="backupListLoading">
          <reload-outlined /> 刷新
        </a-button>
      </div>
    </div>

    <!-- 备份列表表格 -->
    <a-table
      :columns="columns"
      :data-source="backups"
      row-key="backup_id"
      :pagination="pagination"
      :loading="backupListLoading"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'backup_type'">
          <a-tag :color="getBackupTypeColor(record.backup_type)">
            {{ getBackupTypeName(record.backup_type) }}
          </a-tag>
        </template>
        <template v-else-if="column.key === 'status'">
          <a-tag :color="getStatusColor(record.status)">
            {{ getStatusName(record.status) }}
          </a-tag>
        </template>
        <template v-else-if="column.key === 'backup_size'">
          {{ formatFileSize(record.backup_size) }}
        </template>
        <template v-else-if="column.key === 'created_at'">
          {{ formatDate(record.created_at) }}
        </template>
        <template v-else-if="column.key === 'action'">
          <a-space>
            <a @click="handleDownload(record)" :disabled="record.status !== 'completed'" 
               :style="{ color: record.status === 'completed' ? '#1890ff' : '#d9d9d9', cursor: record.status === 'completed' ? 'pointer' : 'not-allowed' }">
              下载
            </a>
            <a @click="handleRestore(record)" :disabled="record.status !== 'completed'"
               :style="{ color: record.status === 'completed' ? '#52c41a' : '#d9d9d9', cursor: record.status === 'completed' ? 'pointer' : 'not-allowed' }">
              恢复
            </a>
            <a-popconfirm
              title="确定要删除这个备份吗？"
              @confirm="handleDelete(record)"
            >
              <a style="color: #ff4d4f;">删除</a>
            </a-popconfirm>
          </a-space>
        </template>
      </template>
    </a-table>


    <!-- 创建备份模态框 -->
    <a-modal
      v-model:open="createModalVisible"
      title="创建备份"
      @ok="handleCreateBackup"
      :confirm-loading="createLoading"
    >
      <BackupCreate @backup-created="handleBackupCreated" />
    </a-modal>

    <!-- 自动备份设置抽屉 -->
    <a-drawer
      v-model:open="autoBackupDrawerVisible"
      title="自动备份设置"
      placement="right"
      :width="600"
    >
      <BackupSettings 
        :schedules="schedules"
        :loading="scheduleLoading"
        @refresh="loadSchedules"
        @create="handleCreateSchedule"
        @update="handleUpdateSchedule"
        @delete="handleDeleteSchedule"
      />
    </a-drawer>
    
    <!-- 进度模态框 -->
    <a-modal
      v-model:open="progressModalVisible"
      title="备份进度"
      :footer="null"
      :closable="false"
    >
      <div class="backup-progress">
        <a-progress 
          :percent="progressPercent" 
          :status="progressStatus"
          :show-info="true"
        />
        <p class="mt-2 text-center">{{ progressMessage }}</p>
        <p v-if="currentOperation" class="text-center text-gray-500">
          当前操作: {{ currentOperation }}
        </p>
        <p v-if="estimatedTime" class="text-center text-gray-500">
          预计剩余时间: {{ estimatedTime }}
        </p>
      </div>
    </a-modal>
    
    <!-- 确认恢复模态框 -->
    <a-modal
      v-model:open="restoreModalVisible"
      title="确认恢复备份"
      @ok="confirmRestore"
      @cancel="cancelRestore"
    >
      <div class="restore-confirm">
        <a-alert
          message="警告"
          description="恢复操作将覆盖当前数据，此操作不可逆。请确认您要继续。"
          type="warning"
          show-icon
          class="mb-4"
        />
        <p><strong>备份名称:</strong> {{ selectedBackup?.backup_name }}</p>
        <p><strong>备份类型:</strong> {{ selectedBackup?.backup_type }}</p>
        <p><strong>创建时间:</strong> {{ formatDate(selectedBackup?.created_at) }}</p>
        <a-checkbox v-model:checked="restoreConfirm" class="mt-4">
          我确认要进行恢复操作
        </a-checkbox>
      </div>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { message } from 'ant-design-vue'
import { PlusOutlined, ReloadOutlined, SettingOutlined } from '@ant-design/icons-vue'
import BackupCreate from '../components/BackupCreate.vue'
import BackupSettings from '../components/BackupSettings.vue'
import { backupApi } from '../utils/backupApi'

// 响应式数据
const backups = ref([])
const schedules = ref([])
const backupListLoading = ref(false)
const scheduleLoading = ref(false)

// 筛选条件
const backupTypeFilter = ref('all')
const statusFilter = ref('all')

// 分页
const pagination = ref({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`
})

// 表格列定义
const columns = [
  {
    title: '备份名称',
    dataIndex: 'backup_name',
    key: 'backup_name',
    width: 200,
  },
  {
    title: '备份类型',
    dataIndex: 'backup_type',
    key: 'backup_type',
    width: 120,
  },
  {
    title: '大小',
    dataIndex: 'backup_size',
    key: 'backup_size',
    width: 100,
  },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status',
    width: 100,
  },
  {
    title: '创建时间',
    dataIndex: 'created_at',
    key: 'created_at',
    width: 160,
  },
  {
    title: '操作',
    key: 'action',
    width: 150,
  },
]

// 进度相关
const progressModalVisible = ref(false)
const progressPercent = ref(0)
const progressStatus = ref('active')
const progressMessage = ref('')
const currentOperation = ref('')
const estimatedTime = ref('')

// 创建备份模态框
const createModalVisible = ref(false)
const createLoading = ref(false)

// 自动备份抽屉
const autoBackupDrawerVisible = ref(false)

// 恢复确认
const restoreModalVisible = ref(false)
const selectedBackup = ref(null)
const restoreConfirm = ref(false)

// 工具方法
const formatDate = (dateString) => {
  if (!dateString) return ''
  return new Date(dateString).toLocaleString('zh-CN')
}

const formatFileSize = (bytes) => {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const getBackupTypeName = (type) => {
  const typeMap = {
    'full': '全量备份',
    'main_service': '主服务备份',
    'admin_service': 'Admin服务备份'
  }
  return typeMap[type] || type
}

const getBackupTypeColor = (type) => {
  const colorMap = {
    'full': 'blue',
    'main_service': 'green',
    'admin_service': 'orange'
  }
  return colorMap[type] || 'default'
}

const getStatusName = (status) => {
  const statusMap = {
    'completed': '已完成',
    'running': '进行中',
    'pending': '等待中',
    'failed': '失败'
  }
  return statusMap[status] || status
}

const getStatusColor = (status) => {
  const colorMap = {
    'completed': 'green',
    'running': 'blue',
    'pending': 'orange',
    'failed': 'red'
  }
  return colorMap[status] || 'default'
}

// 方法
const loadBackups = async () => {
  try {
    backupListLoading.value = true
    const response = await backupApi.getBackupList({
      page: pagination.value.current,
      limit: pagination.value.pageSize,
      backup_type: backupTypeFilter.value === 'all' ? 'all' : backupTypeFilter.value
    })
    
    console.log('API响应:', response)
    console.log('响应类型:', typeof response)
    
    backups.value = (response && response.backups) ? response.backups : []
    pagination.value.total = (response && response.total) ? response.total : 0
  } catch (error) {
    console.error('加载备份列表失败:', error)
    message.error('加载备份列表失败')
  } finally {
    backupListLoading.value = false
  }
}

// 筛选方法
const onBackupTypeFilter = () => {
  pagination.value.current = 1
  loadBackups()
}

const onStatusFilter = () => {
  pagination.value.current = 1
  loadBackups()
}

// 操作方法
const showCreateModal = () => {
  createModalVisible.value = true
}

const showAutoBackupDrawer = () => {
  autoBackupDrawerVisible.value = true
}

const handleDownload = async (record) => {
  try {
    const response = await backupApi.downloadBackup(record.backup_id)
    // 创建下载链接
    const url = window.URL.createObjectURL(new Blob([response]))
    const link = document.createElement('a')
    link.href = url
    link.download = `${record.backup_name}.zip`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    message.success('下载开始')
  } catch (error) {
    console.error('下载备份失败:', error)
    message.error('下载备份失败')
  }
}

const handleRestore = (record) => {
  selectedBackup.value = record
  restoreModalVisible.value = true
}

const handleDelete = async (record) => {
  try {
    await backupApi.deleteBackup(record.backup_id)
    message.success('删除成功')
    loadBackups()
  } catch (error) {
    console.error('删除备份失败:', error)
    message.error('删除备份失败')
  }
}

const loadSchedules = async () => {
  try {
    scheduleLoading.value = true
    const response = await backupApi.getSchedules()
    schedules.value = response || []
  } catch (error) {
    console.error('加载备份调度失败:', error)
    message.error('加载备份调度失败')
  } finally {
    scheduleLoading.value = false
  }
}

const handleBackupCreated = (backupData) => {
  console.log('备份已创建:', backupData)
  message.success('备份任务已创建，正在后台执行')
  createModalVisible.value = false
  showProgressModal()
  loadBackups()
}

const handleCreateBackup = () => {
  // 这个方法会被BackupCreate组件内部处理
}





const confirmRestore = async () => {
  if (!restoreConfirm.value) {
    message.warning('请确认恢复操作')
    return
  }
  
  try {
    await backupApi.restoreBackup(selectedBackup.value.backup_id, {
      restore_type: selectedBackup.value.backup_type,
      confirm: true
    })
    message.success('恢复任务已创建，正在后台执行')
    restoreModalVisible.value = false
    showProgressModal()
  } catch (error) {
    console.error('恢复备份失败:', error)
    message.error('恢复备份失败')
  }
}

const cancelRestore = () => {
  restoreModalVisible.value = false
  selectedBackup.value = null
  restoreConfirm.value = false
}

const handleCreateSchedule = async (scheduleData) => {
  try {
    await backupApi.createSchedule(scheduleData)
    message.success('自动备份调度已创建')
    loadSchedules()
  } catch (error) {
    console.error('创建调度失败:', error)
    message.error('创建调度失败')
  }
}

const handleUpdateSchedule = async (scheduleId, scheduleData) => {
  try {
    await backupApi.updateSchedule(scheduleId, scheduleData)
    message.success('自动备份调度已更新')
    loadSchedules()
  } catch (error) {
    console.error('更新调度失败:', error)
    message.error('更新调度失败')
  }
}

const handleDeleteSchedule = async (scheduleId) => {
  try {
    await backupApi.deleteSchedule(scheduleId)
    message.success('自动备份调度已删除')
    loadSchedules()
  } catch (error) {
    console.error('删除调度失败:', error)
    message.error('删除调度失败')
  }
}

const showProgressModal = () => {
  progressModalVisible.value = true
  progressPercent.value = 0
  progressStatus.value = 'active'
  progressMessage.value = '正在处理...'
  currentOperation.value = ''
  estimatedTime.value = ''
  
  // 模拟进度更新
  const interval = setInterval(() => {
    if (progressPercent.value < 90) {
      progressPercent.value += Math.random() * 10
    }
  }, 1000)
  
  // 5秒后关闭模态框
  setTimeout(() => {
    clearInterval(interval)
    progressPercent.value = 100
    progressStatus.value = 'success'
    progressMessage.value = '操作完成'
    
    setTimeout(() => {
      progressModalVisible.value = false
      loadBackups()
    }, 2000)
  }, 5000)
}

// 生命周期
onMounted(() => {
  loadBackups()
  loadSchedules()
})

</script>

<style scoped>
.backup-management {
  padding: 24px;
}

.header-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #303030;
}

.header-bar h1 {
  margin: 0;
  color: #fff;
  font-size: 24px;
  font-weight: 600;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.h-full {
  height: 100%;
}

.backup-progress {
  text-align: center;
}

.restore-confirm {
  padding: 16px 0;
}

.mb-4 {
  margin-bottom: 16px;
}

.mt-2 {
  margin-top: 8px;
}

.mt-4 {
  margin-top: 16px;
}

.text-center {
  text-align: center;
}

.text-gray-500 {
  color: #6b7280;
}
</style>
