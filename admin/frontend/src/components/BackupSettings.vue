<template>
  <div class="backup-settings">
    <div class="mb-4">
      <a-button type="primary" @click="showCreateModal">
        添加自动备份
      </a-button>
    </div>
    
    <a-table
      :data-source="schedules"
      :loading="loading"
      :pagination="false"
      size="small"
    >
      <a-table-column
        title="调度名称"
        data-index="schedule_name"
        key="schedule_name"
      />
      
      <a-table-column
        title="备份类型"
        data-index="backup_type"
        key="backup_type"
        width="120"
      >
        <template #default="{ record }">
          <a-tag :color="getTypeColor(record.backup_type)">
            {{ getTypeText(record.backup_type) }}
          </a-tag>
        </template>
      </a-table-column>
      
      <a-table-column
        title="频率"
        data-index="frequency"
        key="frequency"
        width="80"
      >
        <template #default="{ record }">
          {{ getFrequencyText(record.frequency) }}
        </template>
      </a-table-column>
      
      <a-table-column
        title="执行时间"
        data-index="schedule_time"
        key="schedule_time"
        width="100"
      />
      
      <a-table-column
        title="保留天数"
        data-index="retention_days"
        key="retention_days"
        width="100"
      />
      
      <a-table-column
        title="状态"
        data-index="enabled"
        key="enabled"
        width="80"
      >
        <template #default="{ record }">
          <a-switch
            :checked="record.enabled"
            @change="handleToggleStatus(record)"
          />
        </template>
      </a-table-column>
      
      <a-table-column
        title="上次运行"
        data-index="last_run"
        key="last_run"
        width="150"
      >
        <template #default="{ record }">
          {{ formatDate(record.last_run) }}
        </template>
      </a-table-column>
      
      <a-table-column
        title="下次运行"
        data-index="next_run"
        key="next_run"
        width="150"
      >
        <template #default="{ record }">
          {{ formatDate(record.next_run) }}
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
              @click="handleEdit(record)"
            >
              编辑
            </a-button>
            <a-popconfirm
              title="确定要删除这个调度吗？"
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
    
    <div v-if="schedules.length === 0 && !loading" class="empty-state">
      <a-empty description="暂无自动备份调度" />
    </div>
    
    <!-- 创建/编辑模态框 -->
    <a-modal
      v-model:open="modalVisible"
      :title="isEdit ? '编辑自动备份' : '创建自动备份'"
      @ok="handleSubmit"
      @cancel="handleCancel"
    >
      <a-form
        :model="formData"
        :label-col="{ span: 6 }"
        :wrapper-col="{ span: 18 }"
        ref="formRef"
      >
        <a-form-item
          label="调度名称"
          name="schedule_name"
          :rules="[{ required: true, message: '请输入调度名称' }]"
        >
          <a-input
            v-model:value="formData.schedule_name"
            placeholder="请输入调度名称"
          />
        </a-form-item>
        
        <a-form-item
          label="备份类型"
          name="backup_type"
          :rules="[{ required: true, message: '请选择备份类型' }]"
        >
          <a-select
            v-model:value="formData.backup_type"
            placeholder="请选择备份类型"
          >
            <a-select-option value="full">全量备份</a-select-option>
            <a-select-option value="main_service">主服务备份</a-select-option>
            <a-select-option value="admin_service">Admin服务备份</a-select-option>
          </a-select>
        </a-form-item>
        
        <a-form-item
          label="备份频率"
          name="frequency"
          :rules="[{ required: true, message: '请选择备份频率' }]"
        >
          <a-select
            v-model:value="formData.frequency"
            placeholder="请选择备份频率"
          >
            <a-select-option value="daily">每日</a-select-option>
            <a-select-option value="weekly">每周</a-select-option>
            <a-select-option value="monthly">每月</a-select-option>
          </a-select>
        </a-form-item>
        
        <a-form-item
          label="执行时间"
          name="schedule_time"
          :rules="[{ required: true, message: '请选择执行时间' }]"
        >
          <a-time-picker
            v-model:value="timeValue"
            format="HH:mm"
            placeholder="请选择执行时间"
            style="width: 100%"
          />
        </a-form-item>
        
        <a-form-item
          label="保留天数"
          name="retention_days"
          :rules="[{ required: true, message: '请输入保留天数' }]"
        >
          <a-input-number
            v-model:value="formData.retention_days"
            :min="1"
            :max="365"
            style="width: 100%"
          />
        </a-form-item>
        
        <a-form-item
          label="启用调度"
          name="enabled"
        >
          <a-switch
            v-model:checked="formData.enabled"
          />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { message } from 'ant-design-vue'
import dayjs from 'dayjs'

// Props
const props = defineProps({
  schedules: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  }
})

// Emits
const emit = defineEmits(['refresh', 'create', 'update', 'delete'])

// 响应式数据
const modalVisible = ref(false)
const isEdit = ref(false)
const currentSchedule = ref(null)
const timeValue = ref(null)
const formRef = ref(null)

const formData = reactive({
  schedule_name: '',
  backup_type: 'full',
  frequency: 'daily',
  retention_days: 30,
  enabled: true
})

// 方法
const showCreateModal = () => {
  isEdit.value = false
  currentSchedule.value = null
  resetForm()
  modalVisible.value = true
}

const handleEdit = (record) => {
  isEdit.value = true
  currentSchedule.value = record
  
  formData.schedule_name = record.schedule_name
  formData.backup_type = record.backup_type
  formData.frequency = record.frequency
  formData.retention_days = record.retention_days
  formData.enabled = record.enabled
  
  // 解析时间
  const [hour, minute] = record.schedule_time.split(':')
  timeValue.value = dayjs().hour(hour).minute(minute)
  
  modalVisible.value = true
}

const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    
    const scheduleData = {
      ...formData,
      schedule_time: timeValue.value.format('HH:mm')
    }
    
    if (isEdit.value) {
      emit('update', currentSchedule.value.id, scheduleData)
    } else {
      emit('create', scheduleData)
    }
    
    modalVisible.value = false
    resetForm()
    
  } catch (error) {
    console.error('表单验证失败:', error)
  }
}

const handleCancel = () => {
  modalVisible.value = false
  resetForm()
}

const handleToggleStatus = async (record) => {
  try {
    const newStatus = !record.enabled
    const scheduleData = {
      ...record,
      enabled: newStatus
    }
    emit('update', record.id, scheduleData)
  } catch (error) {
    console.error('切换状态失败:', error)
  }
}

const handleDelete = (record) => {
  emit('delete', record.id)
}

const resetForm = () => {
  formData.schedule_name = ''
  formData.backup_type = 'full'
  formData.frequency = 'daily'
  formData.retention_days = 30
  formData.enabled = true
  timeValue.value = dayjs().hour(2).minute(0)
}

const formatDate = (dateString) => {
  if (!dateString) return '-'
  
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

const getFrequencyText = (frequency) => {
  const texts = {
    'daily': '每日',
    'weekly': '每周',
    'monthly': '每月'
  }
  return texts[frequency] || frequency
}
</script>

<style scoped>
.backup-settings {
  padding: 16px;
}

.mb-4 {
  margin-bottom: 16px;
}

.empty-state {
  text-align: center;
  padding: 40px 0;
}
</style>
