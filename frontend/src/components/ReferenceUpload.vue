<template>
  <a-upload
    v-model:file-list="localFileList"
    name="reference"
    list-type="picture-card"
    class="reference-upload"
    :show-upload-list="true"
    :before-upload="beforeUpload"
    @preview="handlePreview"
    @remove="handleRemove"
    :style="{ '--ant-upload-border': 'none !important' }"
  >
    <div v-if="localFileList.length < 1">
      <PlusOutlined />
      <div style="margin-top: 8px">参考图</div>
    </div>
  </a-upload>
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
/* 参考图片上传区域样式 */
.reference-upload {
  background: #1a1a1a;
  border-radius: 8px;
  text-align: center;
  transition: border-color 0.3s;
  width: 104px;
}

.reference-upload:hover {
  border-color: #667eea;
}

.reference-upload :deep(.ant-upload) {
  width: 100%;
}

.reference-upload :deep(.ant-upload-drag) {
  background: transparent !important;
  border: none !important;
}

.reference-upload :deep(.ant-upload-drag:hover) {
  background: rgba(102, 126, 234, 0.1) !important;
}

.reference-upload :deep(.ant-upload-drag-icon) {
  color: #667eea !important;
}

.reference-upload :deep(.ant-upload-text) {
  color: #fff !important;
}

.reference-upload :deep(.ant-upload-hint) {
  color: #999 !important;
}

.reference-upload :deep(.ant-upload-select) {
  width: 104px !important;
  height: 104px !important;
  background: rgba(255, 255, 255, 0.05) !important;
  border: 1px dashed rgba(255, 255, 255, 0.3) !important;
  border-radius: 8px !important;
  color: rgba(255, 255, 255, 0.7) !important;
  transition: all 0.3s ease !important;
}

.reference-upload :deep(.ant-upload-select:hover) {
  background: rgba(255, 255, 255, 0.1) !important;
  border-color: rgba(255, 255, 255, 0.5) !important;
  color: rgba(255, 255, 255, 0.9) !important;
}

.reference-upload :deep(.ant-upload-list-picture-card-container) {
  width: 104px !important;
  height: 104px !important;
}

.reference-upload :deep(.ant-upload-list-picture-card .ant-upload-list-item) {
  width: 104px !important;
  height: 104px !important;
  border-radius: 8px !important;
  background: rgba(255, 255, 255, 0.05) !important;
  border: 1px solid rgba(255, 255, 255, 0.2) !important;
  border: none !important;
  height: 104px !important;
  width: 104px !important;
  padding: 0 !important;
  overflow: hidden !important;
  border-radius: 6px !important;
}

.reference-upload :deep(.ant-upload-list-picture-card .ant-upload-list-item-thumbnail img) {
  border-radius: 6px !important;
  width: 100% !important;
  height: 100% !important;
  object-fit: cover !important;
  border-radius: 6px !important;
  margin: 0 !important;
  padding: 0 !important;
  border: none !important;
  background: none !important;
}

.reference-upload :deep(.ant-upload-list-picture-card .ant-upload-list-item-info) {
  width: 100% !important;
  height: 100% !important;
  padding: 0 !important;
  margin: 0 !important;
  border-radius: 6px !important;
  background: none !important;
  border: none !important;
}

.reference-upload :deep(.ant-upload-list-picture-card .ant-upload-list-item-thumbnail) {
  width: 100% !important;
  height: 100% !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  overflow: hidden !important;
  border-radius: 6px !important;
  padding: 0 !important;
  margin: 0 !important;
  background: none !important;
  border: none !important;
}

.reference-upload :deep(.ant-upload-list-picture-card .ant-upload-list-item-actions) {
  background: rgba(0, 0, 0, 0.7) !important;
  background: rgba(0, 0, 0, 0.5) !important;
}

.reference-upload :deep(.ant-upload-list-picture-card .ant-upload-list-item-actions .anticon) {
  color: rgba(255, 255, 255, 0.9) !important;
}

.reference-upload :deep(.ant-upload-list-picture-card .ant-upload-list-item-actions .anticon:hover) {
  color: #fff !important;
}

/* 确保所有子元素都使用正确的盒模型 */
.reference-upload :deep(.ant-upload-list-picture-card .ant-upload-list-item *) {
  box-sizing: border-box !important;
}

.reference-upload :deep(.ant-upload-list-picture-card .ant-upload-list-item-image) {
  width: 100% !important;
  height: 100% !important;
  object-fit: cover !important;
  border-radius: 6px !important;
}

/* 参考图片上传区域的文字颜色 */
.reference-upload :deep(.ant-upload-select .ant-upload) {
  color: #fff !important;
}

.reference-upload :deep(.ant-upload-select .ant-upload *) {
  color: #fff !important;
}

.reference-upload :deep(.ant-upload-select-picture-card) {
  color: #fff !important;
}

.reference-upload :deep(.ant-upload-select-picture-card .ant-upload-text) {
  color: #fff !important;
}

.reference-upload :deep(.ant-upload-select-picture-card .ant-upload-hint) {
  color: #999 !important;
}

.reference-images {
  margin-top: 15px;
}

.reference-images :deep(.ant-upload-list-item) {
  background: #2a2a2a !important;
  border-color: #444 !important;
}
</style>