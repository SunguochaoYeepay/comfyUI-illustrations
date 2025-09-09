<template>
  <div class="multi-image-upload">
    <a-upload
      v-model:file-list="localFileList"
      name="reference"
      list-type="picture-card"
      class="multi-upload"
      :show-upload-list="true"
      :before-upload="beforeUpload"
      @preview="handlePreview"
      @remove="handleRemove"
      :max-count="2"
      multiple
      :style="{ '--ant-upload-border': 'none !important' }"
    >
      <div v-if="showUploadButton && localFileList.length < 2">
        <PlusOutlined />
        <div class="upload-text">上传图片</div>
      </div>
    </a-upload>
    

  </div>
</template>

<script setup>
import { computed } from 'vue'
import { message } from 'ant-design-vue'
import { PlusOutlined } from '@ant-design/icons-vue'

// Props
const props = defineProps({
  fileList: {
    type: Array,
    default: () => []
  },
  showUploadButton: {
    type: Boolean,
    default: true
  }
})

// Emits
const emit = defineEmits([
  'update:fileList',
  'preview'
])

// 双向绑定的计算属性
const localFileList = computed({
  get: () => props.fileList,
  set: (value) => emit('update:fileList', value)
})

// 上传前验证
const beforeUpload = (file) => {
  const isJpgOrPng = file.type === 'image/jpeg' || file.type === 'image/png'
  if (!isJpgOrPng) {
    message.error('只能上传 JPG/PNG 格式的图片!')
    return false
  }
  const isLt2M = file.size / 1024 / 1024 < 2
  if (!isLt2M) {
    message.error('图片大小不能超过 2MB!')
    return false
  }
  
  // 检查是否超过最大数量
  if (localFileList.value.length >= 2) {
    message.error('最多只能上传2张图片!')
    return false
  }
  
  // 手动处理文件，确保originFileObj正确设置
  const fileObj = {
    uid: file.uid || Date.now().toString(),
    name: file.name,
    status: 'done',
    originFileObj: file, // 确保originFileObj被正确设置
    url: URL.createObjectURL(file), // 创建预览URL
    preview: URL.createObjectURL(file)
  }
  
  // 添加到文件列表（支持多图）
  const newFileList = [...localFileList.value, fileObj]
  localFileList.value = newFileList
  
  return false // 阻止自动上传，手动处理
}

// 预览图片
const handlePreview = (file) => {
  emit('preview', file)
}

// 移除图片
const handleRemove = (file) => {
  const index = localFileList.value.indexOf(file)
  if (index > -1) {
    const newFileList = [...localFileList.value]
    newFileList.splice(index, 1)
    localFileList.value = newFileList
  }
}
</script>

<style scoped>
/* 多图上传区域样式 */
.multi-image-upload {
  background: #1a1a1a;
  border-radius: 8px;
}

.multi-upload {
  background: transparent;
  border-radius: 8px;
  text-align: center;
  transition: border-color 0.3s;
  display: flex !important;
  flex-wrap: nowrap !important;
  gap: 8px !important;
  overflow-x: auto !important;
  padding: 0px !important;
}

.multi-upload:hover {
  border-color: #667eea;
}

.multi-upload :deep(.ant-upload) {
  width: auto;
}

.multi-upload :deep(.ant-upload-select) {
  background: rgba(255, 255, 255, 0.05) !important;
  border: 1px dashed rgba(255, 255, 255, 0.3) !important;
  border-radius: 8px !important;
  color: rgba(255, 255, 255, 0.7) !important;
  transition: all 0.3s ease !important;
  width: 80px !important;
  height: 80px !important;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex-shrink: 0 !important;
}

.multi-upload :deep(.ant-upload-select:hover) {
  background: rgba(255, 255, 255, 0.1) !important;
  border-color: rgba(255, 255, 255, 0.5) !important;
  color: rgba(255, 255, 255, 0.9) !important;
}

.upload-text {
  color: #fff;
  font-size: 14px;
  margin-top: 8px;
}

.upload-hint {
  color: #999;
  font-size: 12px;
  margin-top: 4px;
}

.multi-upload :deep(.ant-upload-list-picture-card) {
  display: flex !important;
  flex-wrap: nowrap !important;
  gap: 8px !important;
  overflow-x: auto !important;
  padding: 8px 0 !important;
}

.multi-upload :deep(.ant-upload-list-picture-card .ant-upload-list-item) {
  border-radius: 8px !important;
  background: rgba(255, 255, 255, 0.05) !important;
  border: 1px solid rgba(255, 255, 255, 0.2) !important;
  padding: 0 !important;
  overflow: hidden !important;
  flex-shrink: 0 !important;
  width: 80px !important;
  height: 80px !important;
}

.multi-upload :deep(.ant-upload-list-picture-card .ant-upload-list-item-thumbnail img) {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.multi-upload :deep(.ant-upload-list-picture-card .ant-upload-list-item-actions) {
  background: rgba(0, 0, 0, 0.5);
}

.multi-upload :deep(.ant-upload-list-picture-card .ant-upload-list-item-actions .anticon) {
  color: #fff;
}

/* 上传信息样式 */
.upload-info {
  margin-top: 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
}

.image-count {
  color: #667eea;
  font-weight: 500;
}

.warning-text {
  color: #ff7875;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .multi-upload :deep(.ant-upload-list-picture-card .ant-upload-list-item) {
    width: 80px;
    height: 80px;
  }
  
  .multi-upload :deep(.ant-upload-select) {
    min-height: 100px;
  }
}
</style>
