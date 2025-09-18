<template>
  <div class="backup-restore">
    <a-form
      :model="formData"
      :label-col="{ span: 8 }"
      :wrapper-col="{ span: 16 }"
      @finish="handleSubmit"
    >
      <a-form-item
        label="选择备份"
        name="backup_id"
        :rules="[{ required: true, message: '请选择要恢复的备份' }]"
      >
        <a-select
          v-model:value="formData.backup_id"
          placeholder="请选择要恢复的备份"
          @change="handleBackupChange"
        >
          <a-select-option
            v-for="backup in availableBackups"
            :key="backup.backup_id"
            :value="backup.backup_id"
          >
            {{ backup.backup_name }} ({{ formatDate(backup.created_at) }})
          </a-select-option>
        </a-select>
      </a-form-item>
      
      <a-form-item
        label="恢复类型"
        name="restore_type"
        :rules="[{ required: true, message: '请选择恢复类型' }]"
      >
        <a-select
          v-model:value="formData.restore_type"
          placeholder="请选择恢复类型"
        >
          <a-select-option value="full">全量恢复</a-select-option>
          <a-select-option value="main_service">主服务恢复</a-select-option>
          <a-select-option value="admin_service">Admin服务恢复</a-select-option>
        </a-select>
      </a-form-item>
      
      <!-- 备份信息显示 -->
      <div v-if="selectedBackup" class="backup-info">
        <a-divider>备份信息</a-divider>
        <a-descriptions size="small" :column="1">
          <a-descriptions-item label="备份名称">
            {{ selectedBackup.backup_name }}
          </a-descriptions-item>
          <a-descriptions-item label="备份类型">
            <a-tag :color="getTypeColor(selectedBackup.backup_type)">
              {{ getTypeText(selectedBackup.backup_type) }}
            </a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="备份大小">
            {{ formatFileSize(selectedBackup.backup_size) }}
          </a-descriptions-item>
          <a-descriptions-item label="创建时间">
            {{ formatDate(selectedBackup.created_at) }}
          </a-descriptions-item>
          <a-descriptions-item label="状态">
            <a-tag :color="getStatusColor(selectedBackup.status)">
              {{ getStatusText(selectedBackup.status) }}
            </a-tag>
          </a-descriptions-item>
        </a-descriptions>
      </div>
      
      <a-form-item :wrapper-col="{ offset: 8, span: 16 }">
        <a-space>
          <a-button
            type="primary"
            danger
            html-type="submit"
            :loading="loading"
            :disabled="!selectedBackup || selectedBackup.status !== 'completed'"
          >
            开始恢复
          </a-button>
          <a-button @click="resetForm">
            重置
          </a-button>
        </a-space>
      </a-form-item>
    </a-form>
    
    <!-- 警告信息 -->
    <a-alert
      message="恢复操作警告"
      description="恢复操作将覆盖当前数据，此操作不可逆。请确保您已备份当前重要数据。"
      type="warning"
      show-icon
      class="mt-4"
    />
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { message } from 'ant-design-vue'

// Props
const props = defineProps({
  backups: {
    type: Array,
    default: () => []
  }
})

// Emits
const emit = defineEmits(['restore'])

// 响应式数据
const loading = ref(false)
const selectedBackup = ref(null)
const formData = reactive({
  backup_id: '',
  restore_type: 'full'
})

// 计算属性
const availableBackups = computed(() => {
  return props.backups.filter(backup => backup.status === 'completed')
})

// 方法
const handleBackupChange = (backupId) => {
  selectedBackup.value = props.backups.find(backup => backup.backup_id === backupId)
  if (selectedBackup.value) {
    formData.restore_type = selectedBackup.value.backup_type
  }
}

const handleSubmit = () => {
  if (!selectedBackup.value) {
    message.warning('请选择要恢复的备份')
    return
  }
  
  emit('restore', selectedBackup.value)
}

const resetForm = () => {
  formData.backup_id = ''
  formData.restore_type = 'full'
  selectedBackup.value = null
}

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
    'full': '全量备份',
    'main_service': '主服务备份',
    'admin_service': 'Admin服务备份'
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
</script>

<style scoped>
.backup-restore {
  padding: 16px;
}

.backup-info {
  margin-top: 16px;
}

.mt-4 {
  margin-top: 16px;
}
</style>
