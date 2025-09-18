<template>
  <div class="backup-create">
    <a-form
      :model="formData"
      :label-col="{ span: 8 }"
      :wrapper-col="{ span: 16 }"
      @finish="handleSubmit"
    >
      <a-form-item
        label="备份名称"
        name="backup_name"
        :rules="[{ required: true, message: '请输入备份名称' }]"
      >
        <a-input
          v-model:value="formData.backup_name"
          placeholder="请输入备份名称"
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
        label="备份描述"
        name="description"
      >
        <a-textarea
          v-model:value="formData.description"
          placeholder="请输入备份描述（可选）"
          :rows="3"
        />
      </a-form-item>
      
      <a-form-item
        label="包含文件"
        name="include_files"
      >
        <a-switch
          v-model:checked="formData.include_files"
          checked-children="是"
          un-checked-children="否"
        />
      </a-form-item>
      
      
      <a-form-item
        label="压缩级别"
        name="compression_level"
      >
        <a-slider
          v-model:value="formData.compression_level"
          :min="1"
          :max="9"
          :marks="{
            1: '最快',
            5: '平衡',
            9: '最小'
          }"
        />
      </a-form-item>
      
      <a-form-item :wrapper-col="{ offset: 8, span: 16 }">
        <a-space>
          <a-button
            type="primary"
            html-type="submit"
            :loading="loading"
          >
            创建备份
          </a-button>
          <a-button @click="resetForm">
            重置
          </a-button>
        </a-space>
      </a-form-item>
    </a-form>
    
    <!-- 备份类型说明 -->
    <a-divider>备份类型说明</a-divider>
    <a-descriptions size="small" :column="1">
      <a-descriptions-item label="全量备份">
        备份主服务和Admin服务的所有数据，包括数据库、文件、配置等
      </a-descriptions-item>
      <a-descriptions-item label="主服务备份">
        仅备份主服务数据，包括任务记录、生成的文件等
      </a-descriptions-item>
      <a-descriptions-item label="Admin服务备份">
        仅备份Admin服务数据，包括用户配置、工作流等
      </a-descriptions-item>
    </a-descriptions>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { message } from 'ant-design-vue'
import { backupApi } from '../utils/backupApi'

// 响应式数据
const loading = ref(false)
const formData = reactive({
  backup_name: '',
  backup_type: 'full',
  description: '',
  include_files: true,
  compression_level: 6
})

// 方法
const handleSubmit = async () => {
  try {
    loading.value = true
    
    const response = await backupApi.createBackup({
      backup_type: formData.backup_type,
      backup_name: formData.backup_name,
      description: formData.description,
      include_files: formData.include_files,
      compression_level: formData.compression_level
    })
    
    message.success('备份任务已创建')
    
    // 触发父组件事件
    emit('backup-created', response)
    
  } catch (error) {
    console.error('创建备份失败:', error)
    message.error('创建备份失败')
  } finally {
    loading.value = false
  }
}

const resetForm = () => {
  formData.backup_name = ''
  formData.backup_type = 'full'
  formData.description = ''
  formData.include_files = true
  formData.compression_level = 6
}

// 定义事件
const emit = defineEmits(['backup-created'])
</script>

<style scoped>
.backup-create {
  padding: 16px;
}
</style>
