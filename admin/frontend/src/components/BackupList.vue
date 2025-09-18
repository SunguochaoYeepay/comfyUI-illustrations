<template>
  <div class="backup-list">
    <div class="mb-3">
      <a-button @click="$emit('refresh')" :loading="loading">
        刷新列表
      </a-button>
    </div>
    
    <a-table
      :data-source="backups"
      :loading="loading"
      :pagination="false"
      size="small"
      :scroll="{ y: 300 }"
    >
      <a-table-column
        title="备份名称"
        data-index="backup_name"
        key="backup_name"
      />
      
      <a-table-column
        title="类型"
        data-index="backup_type"
        key="backup_type"
        width="100"
      >
        <template #default="{ record }">
          <a-tag :color="getTypeColor(record.backup_type)">
            {{ getTypeText(record.backup_type) }}
          </a-tag>
        </template>
      </a-table-column>
      
      <a-table-column
        title="大小"
        data-index="backup_size"
        key="backup_size"
        width="100"
      >
        <template #default="{ record }">
          {{ formatFileSize(record.backup_size) }}
        </template>
      </a-table-column>
      
      <a-table-column
        title="状态"
        data-index="status"
        key="status"
        width="80"
      >
        <template #default="{ record }">
          <a-tag :color="getStatusColor(record.status)">
            {{ getStatusText(record.status) }}
          </a-tag>
        </template>
      </a-table-column>
      
      <a-table-column
        title="创建时间"
        data-index="created_at"
        key="created_at"
        width="150"
      >
        <template #default="{ record }">
          {{ formatDate(record.created_at) }}
        </template>
      </a-table-column>
      
      <a-table-column
        title="操作"
        key="action"
        width="120"
      >
        <template #default="{ record }">
          <a-space size="small">
            <a-button
              type="link"
              size="small"
              @click="handleDownload(record)"
              :disabled="record.status !== 'completed'"
            >
              下载
            </a-button>
            <a-popconfirm
              title="确定要删除这个备份吗？"
              @confirm="handleDelete(record)"
            >
              <a-button
                type="link"
                size="small"
                danger
              >
                删除
              </a-button>
            </a-popconfirm>
          </a-space>
        </template>
      </a-table-column>
    </a-table>
    
    <div v-if="backups.length === 0 && !loading" class="empty-state">
      <a-empty description="暂无备份记录" />
    </div>
  </div>
</template>

<script setup>
import { message } from 'ant-design-vue'

// Props
defineProps({
  backups: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  }
})

// Emits
const emit = defineEmits(['refresh', 'download', 'delete'])

// 方法
const formatFileSize = (bytes) => {
  if (!bytes) return '0 B'
  
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatDate = (dateString) => {
  if (!dateString) return ''
  
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const getTypeColor = (type) => {
  const colors = {
    'full': 'blue',
    'main_service': 'green',
    'admin_service': 'orange'
  }
  return colors[type] || 'default'
}

const getTypeText = (type) => {
  const texts = {
    'full': '全量',
    'main_service': '主服务',
    'admin_service': 'Admin'
  }
  return texts[type] || type
}

const getStatusColor = (status) => {
  const colors = {
    'pending': 'processing',
    'running': 'processing',
    'completed': 'success',
    'failed': 'error'
  }
  return colors[status] || 'default'
}

const getStatusText = (status) => {
  const texts = {
    'pending': '等待中',
    'running': '运行中',
    'completed': '已完成',
    'failed': '失败'
  }
  return texts[status] || status
}

const handleDownload = (record) => {
  emit('download', record.backup_id)
}

const handleDelete = (record) => {
  emit('delete', record.backup_id)
}
</script>

<style scoped>
.backup-list {
  padding: 16px;
}

.mb-3 {
  margin-bottom: 12px;
}

.empty-state {
  text-align: center;
  padding: 40px 0;
}
</style>
