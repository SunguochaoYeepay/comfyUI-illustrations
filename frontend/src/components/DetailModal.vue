<template>
  <a-modal
    v-model:open="visible"
    :title="null"
    width="90%"
    :footer="null"
    @cancel="closeModal"
    class="detail-modal"
  >
    <div class="detail-content" v-if="item">
      <!-- 左右布局容器 -->
      <div class="content-layout">
        <!-- 左侧图片区域 -->
        <div class="image-section">
          <img :src="item.imageUrl" :alt="item.title" class="detail-image" />
        </div>
        
        <!-- 右侧信息区域 -->
        <div class="detail-info">
          <!-- 标题 -->
          <div class="modal-title">
            <h3>生成信息</h3>
          </div>
          
          <!-- 操作按钮 -->
          <div class="action-buttons">
            <a-button @click="downloadImage" class="action-btn">
              <DownloadOutlined />
              下载
            </a-button>
            <a-button class="action-btn">
              <SearchOutlined />
              高清放大
            </a-button>
            <a-button class="action-btn">
              <VideoCameraOutlined />
              生成视频
            </a-button>
          </div>
        <!-- 参考图 -->
        <div class="info-row">
          <span class="info-label">参考图:</span>
          <div class="reference-image" v-if="getReferenceImageUrl()">
            <img :src="getReferenceImageUrl()" :alt="'参考图'" class="reference-img" />
          </div>
          <div class="reference-image" v-else>
            <ExclamationCircleOutlined />
            <span>无参考图</span>
          </div>
        </div>
        
        <!-- 提示词 -->
        <div class="info-row">
          <span class="info-label">提示词:</span>
          <div class="prompt-display">{{ item.prompt || 'Landing page, B-end product landing page, technolog' }}</div>
        </div>
        
        <!-- 生成时间 -->
        <div class="info-row">
          <span class="info-label">生成时间:</span>
          <span class="info-value">{{ formatDate(item.createdAt) }}</span>
        </div>
        
        <!-- 图片尺寸 -->
        <div class="info-row">
          <span class="info-label">图片尺寸:</span>
          <span class="info-value">{{ getImageSize() }}</span>
        </div>
        
        <!-- 任务ID -->
        <div class="info-row">
          <span class="info-label">任务ID:</span>
          <span class="info-value task-id">{{ item.task_id }}</span>
        </div>
        
        <!-- 使用模型 -->
        <div class="info-row">
          <span class="info-label">使用模型:</span>
          <span class="info-value">{{ getModelDescription() }}</span>
        </div>
        
        <!-- 使用LoRA -->
        <div class="info-row" v-if="hasLoRA()">
          <span class="info-label">使用LoRA:</span>
          <span class="info-value">{{ getLoRAName() }} (强度:{{ getLoRAStrength() }})</span>
        </div>
        
        <!-- 其他参数 -->
        <div class="info-row" v-if="hasOtherParams()">
          <span class="info-label">其他参数:</span>
          <span class="info-value"></span>
        </div>
        
        <!-- 步数 -->
        <div class="info-row" v-if="item.parameters?.steps">
          <span class="info-label">步数:</span>
          <span class="info-value">{{ item.parameters.steps }}</span>
        </div>
        </div>
      </div>
    </div>
  </a-modal>
</template>

<script setup>
import { ref, watch } from 'vue'
import { 
  DownloadOutlined, 
  DeleteOutlined, 
  SearchOutlined, 
  DownOutlined, 
  VideoCameraOutlined,
  ExclamationCircleOutlined 
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:9000'

const props = defineProps({
  open: {
    type: Boolean,
    default: false
  },
  item: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['update:open', 'remove-favorite'])

const visible = ref(false)

watch(() => props.open, (newVal) => {
  visible.value = newVal
})

watch(visible, (newVal) => {
  emit('update:open', newVal)
})

const closeModal = () => {
  visible.value = false
}

const downloadImage = () => {
  if (props.item?.imageUrl) {
    const link = document.createElement('a')
    link.href = props.item.imageUrl
    link.download = `${props.item.title || 'image'}.png`
    link.click()
    message.success('图片下载已开始')
  }
}

const removeFavorite = () => {
  emit('remove-favorite', props.item)
  closeModal()
  message.success('已取消收藏')
}

const formatDate = (dateString) => {
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN')
}

const getImageSize = () => {
  if (props.item?.parameters?.width && props.item?.parameters?.height) {
    return `${props.item.parameters.width} × ${props.item.parameters.height}`
  }
  return '512 × 512' // 默认尺寸
}

const getModelName = () => {
  if (props.item?.parameters?.model) {
    return props.item.parameters.model
  }
  return 'flux1'
}

const getModelDescription = () => {
  const model = getModelName()
  if (model === 'flux1') {
    return 'Flux模型- 更精确控制'
  } else if (model === 'qwen-image') {
    return 'Qwen模型- 支持多图融合'
  }
  return 'AI图像生成模型'
}

const hasLoRA = () => {
  return props.item?.parameters?.loras && props.item.parameters.loras.length > 0
}

const getLoRAName = () => {
  if (hasLoRA()) {
    return props.item.parameters.loras[0].name || 'FLUX-文创品牌设计_品牌LOGO_v1.0'
  }
  return 'FLUX-文创品牌设计_品牌LOGO_v1.0'
}

const getLoRAStrength = () => {
  if (hasLoRA()) {
    return props.item.parameters.loras[0].strength_model || 1
  }
  return 1
}

const hasOtherParams = () => {
  return props.item?.parameters?.steps || props.item?.parameters?.cfg
}

const getReferenceImageUrl = () => {
  if (!props.item?.referenceImagePath) {
    return null
  }
  
  // 如果是数组（多图融合），取第一张
  if (Array.isArray(props.item.referenceImagePath)) {
    if (props.item.referenceImagePath.length > 0) {
      const imagePath = props.item.referenceImagePath[0]
      return `${API_BASE}/api/image/upload/${imagePath}`
    }
    return null
  }
  
  // 如果是字符串（单图）
  if (typeof props.item.referenceImagePath === 'string') {
    return `${API_BASE}/api/image/upload/${props.item.referenceImagePath}`
  }
  
  return null
}
</script>

<style scoped>
.detail-modal :deep(.ant-modal-content) {
  background: #1a1a1a !important;
  color: #fff;
  border-radius: 8px;
}

/* 强制覆盖Ant Design的高优先级样式 - 使用更具体的选择器 */
.detail-modal:where(.css-dev-only-do-not-override-1p3hq3p).ant-modal .ant-modal-content {
  background-color: #1a1a1a !important;
}

.detail-modal:where(.css-dev-only-do-not-override-1p3hq3p).ant-modal .ant-modal-header {
  background: #1a1a1a !important;
  color: #ffffff !important;
}

/* 使用属性选择器覆盖 */
[class*="css-dev-only-do-not-override"].ant-modal .ant-modal-content {
  background-color: #1a1a1a !important;
}

[class*="css-dev-only-do-not-override"].ant-modal .ant-modal-header {
  background: #1a1a1a !important;
  color: #ffffff !important;
}

/* 全局覆盖所有可能的Ant Design模态框样式 */
.ant-modal .ant-modal-content {
  background-color: #1a1a1a !important;
}

.ant-modal .ant-modal-header {
  background: #1a1a1a !important;
  color: #ffffff !important;
}

/* 使用最高优先级的选择器 */
html body .detail-modal:where(.css-dev-only-do-not-override-1p3hq3p).ant-modal .ant-modal-content {
  background-color: #1a1a1a !important;
}

html body .detail-modal:where(.css-dev-only-do-not-override-1p3hq3p).ant-modal .ant-modal-header {
  background: #1a1a1a !important;
  color: #ffffff !important;
}

/* 自定义模态框位置 - 可配置距离 */
.detail-modal:where(.css-dev-only-do-not-override-1p3hq3p).ant-modal {
  top: 50px; /* 可配置的顶部距离，可以根据需要调整 */
}

.detail-modal[class*="css-dev-only-do-not-override"].ant-modal {
  top: 50px; /* 可配置的顶部距离 */
}

.detail-modal :deep(.ant-modal) {
  background: rgba(0, 0, 0, 0.8) !important;
}

.detail-modal :deep(.ant-modal-wrap) {
  background: rgba(0, 0, 0, 0.8) !important;
}

.detail-modal :deep(.ant-modal-header) {
  background: #1a1a1a;
  border-bottom: none;
  padding: 16px 20px 0 20px;
}

.detail-modal :deep(.ant-modal-title) {
  color: #fff;
  font-size: 16px;
  font-weight: 600;
}

.detail-modal :deep(.ant-modal-close) {
  color: #fff !important;
  background: transparent !important;
  border: none !important;
  width: 32px !important;
  height: 32px !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  border-radius: 4px !important;
  transition: all 0.3s !important;
}

.detail-modal :deep(.ant-modal-close:hover) {
  background: rgba(255, 255, 255, 0.1) !important;
  color: #fff !important;
}

.detail-modal :deep(.ant-modal-close:focus) {
  background: rgba(255, 255, 255, 0.1) !important;
  color: #fff !important;
  outline: none !important;
}

/* 使用最高优先级选择器强制设置高度 */
.detail-modal:where(.css-dev-only-do-not-override-1p3hq3p).ant-modal {
  height: 100vh !important;
}

.detail-modal:where(.css-dev-only-do-not-override-1p3hq3p).ant-modal .ant-modal-content {
  height: 100vh !important;
}

.detail-modal:where(.css-dev-only-do-not-override-1p3hq3p).ant-modal .ant-modal-body {
  background: #1a1a1a !important;
  padding: 0 20px 0 20px;
  height: calc(100vh - 60px) !important;
  overflow-y: auto;
}

/* 备用选择器 */
.detail-modal[class*="css-dev-only-do-not-override"].ant-modal {
  height: 100vh !important;
}

.detail-modal[class*="css-dev-only-do-not-override"].ant-modal .ant-modal-content {
  height: 100vh !important;
}

.detail-modal[class*="css-dev-only-do-not-override"].ant-modal .ant-modal-body {
  background: #1a1a1a !important;
  padding: 0 20px 0 20px;
  height: calc(100vh - 60px) !important;
  overflow-y: auto;
}

.detail-modal :deep(.ant-modal-mask) {
  background: rgba(0, 0, 0, 0.8) !important;
}

.detail-content {
  display: flex;
  flex-direction: column;
}

.content-layout {
  display: flex;
  gap: 20px;
  flex: 1;
  height: 100%;
}

.action-buttons {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.image-section {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #000000;
  border-radius: 8px;
}

.detail-image {
  max-width: 100%;
  max-height: 100%;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  object-fit: contain;
}

.action-btn {
  background: #2a2a2a;
  border: 1px solid #444;
  color: #fff;
  border-radius: 6px;
  height: 32px;
  padding: 0 12px;
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.action-btn:hover {
  background: #333;
  border-color: #555;
  color: #fff;
}

.detail-info {
  display: flex;
  flex-direction: column;
  gap: 16px;
  flex: 1;
  min-width: 320px;
  max-width: 400px;
  border-left:1px solid #1a1a1a;
  padding: 24px;
}

.modal-title {
  margin-bottom: 8px;
}

.modal-title h3 {
  color: #fff;
  font-size: 16px;
  font-weight: 600;
  margin: 0;
  padding: 0;
}

.info-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 8px 0;
}

.info-label {
  color: #888;
  font-size: 14px;
  font-weight: 500;
  min-width: 80px;
  flex-shrink: 0;
}

.info-value {
  color: #fff;
  font-size: 14px;
  flex: 1;
}

.task-id {
  font-family: monospace;
  font-size: 12px;
  color: #666;
  word-break: break-all;
}

.reference-image {
  background: #2a2a2a;
  border: 1px solid #444;
  border-radius: 6px;
  padding: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #888;
  font-size: 14px;
  flex: 1;
}

.reference-image .anticon {
  font-size: 16px;
  color: #ffa500;
}

.reference-img {
  width: 100px;
  height: 100px;
  object-fit: cover;
  border-radius: 8px;
  border: 1px solid #333;
}

.prompt-display {
  background: #2a2a2a;
  border: 1px solid #444;
  border-radius: 6px;
  padding: 12px;
  color: #ccc;
  font-size: 14px;
  flex: 1;
  min-height: 40px;
  line-height: 1.4;
  word-break: break-word;
}
</style>
