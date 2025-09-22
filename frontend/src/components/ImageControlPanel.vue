<template>
  <div class="control-section">
    <a-card class="control-card">
      <div class="control-layout">

         <!-- 主要输入区域 -->
         <div class="main-input-row">
           <!-- 参考图片区域 -->
           <div class="reference-section">
             <!-- 统一使用多图上传组件，支持1-5张图片 -->
             <MultiImageUpload
               v-model:file-list="localReferenceImages"
               :show-upload-button="shouldShowUploadButton"
               @preview="$emit('preview', $event)"
               @upload-complete="$emit('upload-complete', $event)"
             />
           </div>

           <!-- 提示词输入区域 -->
           <div class="input-group">
             <div class="prompt-input-group">
               <a-textarea
                 v-model:value="localPrompt"
                 :placeholder="getPromptPlaceholder()"
                 :rows="2"
                 class="prompt-input"
               />
             </div>
           </div>
         </div>

         <!-- 模型、LoRA和生成按钮行 -->
         <div class="controls-row">
           <!-- 左侧：模型和LoRA选择器 -->
           <div class="model-lora-group">
             <!-- 基础模型选择器 -->
             <ModelSelector 
               v-model:model="localModel"
               class="model-selector-section"
             />
             
             <!-- 尺寸和数量选择器 - 仅在非视频模型时显示 -->
             <SizeSelector 
               v-if="!isVideoModel"
               v-model:size="localSize"
               v-model:count="localCount"
               class="size-selector-section"
             />
             
             <!-- 视频生成配置 - 仅在WAN2.2视频模型时显示 -->
             <VideoConfig 
               v-if="isVideoModel"
               v-model:duration="videoDuration"
               v-model:fps="videoFps"
             />
             
             <!-- LoRA选择器 -->
             <div v-if="shouldShowLoraPanel" class="lora-dropdown-section">
               <LoraDropdown
                 :available-loras="availableLoras"
                 :selected-loras="selectedLoras"
                 :lora-categories="loraCategories"
                 :selected-lora-category="selectedLoraCategory"
                 :loading="loraLoading"
                 :api-base="API_BASE"
                 @refresh="refreshLoras"
                 @category-filter="onLoraCategoryFilter"
                 @toggle-lora="toggleLora"
                 @lora-toggle="handleLoraToggle"
                 @dropdown-visible-change="handleLoraDropdownVisibleChange"
               />
             </div>
           </div>

           <!-- 右侧：生成按钮 -->
           <div class="generate-section">
             <a-button
               type="primary"
               size="large"
               :loading="isGenerating"
               @click="handleGenerate"
               class="generate-btn"
             >
               <template #icon>
                 <span v-if="!isGenerating">✨</span>
               </template>
               {{ isGenerating ? '生成中...' : '生成' }}
             </a-button>
           </div>
         </div>

         
       </div>
     </a-card>
   </div>
 </template>

 <script setup>
import { computed, ref, onMounted, watch } from 'vue'
import { message } from 'ant-design-vue'
import MultiImageUpload from './MultiImageUpload.vue'
import ModelSelector from './ModelSelector.vue'
import SizeSelector from './SizeSelector.vue'
import LoraDropdown from './LoraDropdown.vue'
import VideoConfig from './VideoConfig.vue'
import modelManager from '../utils/modelManager.js'
import { useLora } from '../composables/useLora.js'

 // API基础URL - 自动检测环境
 const API_BASE = (() => {
   if (import.meta.env.DEV) {
     return import.meta.env.VITE_BACKEND_URL || 'http://localhost:9000'  // 开发环境指向后端9000端口
   }
   return import.meta.env.VITE_API_BASE_URL || ''
 })()

 // Props
 const props = defineProps({
   prompt: {
     type: String,
     default: ''
   },
   referenceImages: {
     type: Array,
     default: () => []
   },
   loras: {
     type: Array,
     default: () => []
   },
  model: {
    type: String,
    required: true
  },
  size: {
    type: String,
    default: '1024x1024'
  },
  count: {
    type: Number,
    default: 1
  },
  isGenerating: {
    type: Boolean,
    default: false
  }
 })

 // Emits
const emit = defineEmits([
  'update:prompt',
  'update:referenceImages',
  'update:loras',
  'update:model',
  'update:size',
  'update:count',
  'generate',
  'preview',
  'upload-complete'
])

// 计算属性：根据图片数量和模型类型判断是否为融合模式
const isFusionMode = computed(() => {
  // 使用全局模型管理器判断是否支持多图
  const isMultiImageModel = modelManager.isMultiImageModel(localModel.value)
  return isMultiImageModel && localReferenceImages.value.length >= 2
})

// 计算属性：判断是否为视频模型
const isVideoModel = computed(() => {
  return modelManager.isVideoModel(localModel.value)
})

// 计算属性：判断是否应该显示LoRA面板
const shouldShowLoraPanel = computed(() => {
  // 使用全局模型管理器判断是否支持LoRA
  return modelManager.supportsLora(localModel.value)
})

// 计算属性：判断是否应该显示上传按钮
const shouldShowUploadButton = computed(() => {
  const isMultiImageModel = modelManager.isMultiImageModel(localModel.value)
  
  // 支持多图的模型：根据图片数量限制显示上传按钮
  if (isMultiImageModel) {
    // 使用全局模型管理器获取最大图片数量
    const maxImages = modelManager.getMaxImages(localModel.value)
    return localReferenceImages.value.length < maxImages
  }
  
  // 其他模型：只有没有图片时才显示上传按钮
  return localReferenceImages.value.length === 0
})

// 视频生成配置状态
const videoDuration = ref(5) // 默认5秒
const videoFps = ref('16') // 默认16 FPS

 // 双向绑定的计算属性
 const localPrompt = computed({
   get: () => props.prompt,
   set: (value) => emit('update:prompt', value)
 })

 const localReferenceImages = computed({
   get: () => props.referenceImages,
   set: (value) => emit('update:referenceImages', value)
 })

 const localModel = computed({
   get: () => props.model,
   set: (value) => emit('update:model', value)
 })

 const selectedLoras = computed({
   get: () => props.loras,
   set: (value) => emit('update:loras', value)
 })

// 使用LoRA composable
const {
  availableLoras,
  loading: loraLoading,
  loraConfigSource,
  loraLastUpdated,
  loraCategories,
  selectedLoraCategory,
  selectedLoras: loraSelectedLoras,
  filteredLoras,
  fetchLoras,
  fetchLoraCategories,
  onLoraCategoryFilter,
  getCategoryCount,
  isLoraSelected,
  addLora,
  removeLoraByName,
  toggleLora,
  handleLoraToggle,
  refreshLoras
} = useLora(API_BASE, localModel)

 // 同步composable中的selectedLoras到props
 watch(loraSelectedLoras, (newLoras) => {
   selectedLoras.value = newLoras
 }, { deep: true })

 watch(selectedLoras, (newLoras) => {
   loraSelectedLoras.value = newLoras
 }, { deep: true })

 const localSize = computed({
   get: () => props.size,
   set: (value) => emit('update:size', value)
 })

 const localCount = computed({
   get: () => props.count,
   set: (value) => emit('update:count', value)
 })

// 监听图片数量变化，自动调整模型
watch(() => localReferenceImages.value.length, (newCount) => {
  console.log('🔄 图片数量变化:', newCount)
  
  // 如果上传了2张或更多图片，且当前不是支持多图的模型，则切换到第一个支持多图的模型
  if (newCount >= 2) {
    const isMultiImageModel = modelManager.isMultiImageModel(localModel.value)
    if (!isMultiImageModel) {
      // 获取第一个支持多图的模型
      const multiImageModels = modelManager.getAvailableModels().filter(model => 
        modelManager.isMultiImageModel(model.name)
      )
      if (multiImageModels.length > 0) {
        console.log('🔄 自动切换到支持多图的模型:', multiImageModels[0].display_name)
        localModel.value = multiImageModels[0].name
      }
    }
  }
}, { immediate: true })

// 监听模型变化，处理图片数量限制
watch(() => localModel.value, (newModel) => {
  const isMultiImageModel = modelManager.isMultiImageModel(newModel)
  
  // 如果切换到不支持多图的模型，且有多张图片，只保留第一张
  if (!isMultiImageModel && localReferenceImages.value.length > 1) {
    console.log('🔄 切换到不支持多图的模型，只保留第一张图片')
    localReferenceImages.value = [localReferenceImages.value[0]]
  }
  
  // 如果切换到支持多图的模型，根据模型的最大图片数量限制
  if (isMultiImageModel) {
    const maxImages = modelManager.getMaxImages(newModel)
    if (localReferenceImages.value.length > maxImages) {
      console.log(`🔄 切换到${newModel}模型，只保留前${maxImages}张图片`)
      localReferenceImages.value = localReferenceImages.value.slice(0, maxImages)
    }
  }
}, { immediate: true })

// 获取提示词占位符
const getPromptPlaceholder = () => {
  if (isVideoModel.value) {
    return '请描述您想要的视频效果，支持中文输入（如：弹吉他、人物微笑、镜头推进）'
  } else if (isFusionMode.value) {
    const maxImages = modelManager.getMaxImages(localModel.value)
    if (maxImages === 2) {
      return '请描述2图融合的效果，支持中文输入（如：将两张图像融合，让左边的人物拿着右边的物品）'
    } else {
      return '请描述多图融合的效果，支持中文输入（如：将三张图像拼接后，让左边的女人手里拎着中间棕色的包，坐在白色沙发上）'
    }
  } else {
    return '请详细描述您想要生成的图像，支持中文输入（如：一只可爱的橙色小猫坐在花园里，阳光明媚，高清摄影风格）'
  }
}

// 处理生成按钮点击
const handleGenerate = () => {
  const options = { 
    mode: isFusionMode.value ? 'fusion' : 'single' 
  }
  
  // 如果是视频模型，添加视频配置
  if (isVideoModel.value) {
    options.videoConfig = {
      duration: videoDuration.value,
      fps: videoFps.value
    }
  }
  
  emit('generate', options)
}

// 处理LoRA下拉菜单显示状态变化
// 处理LoRA下拉菜单显示状态变化
const handleLoraDropdownVisibleChange = (visible) => {
  if (visible) {
    if (availableLoras.value.length === 0) {
      fetchLoras()
    }
    if (loraCategories.value.length === 0) {
      fetchLoraCategories()
    }
  }
}
 </script>

 <style scoped>
 .control-section {
   position: fixed;
   bottom: 0px;
   left: 52%;
   transform: translateX(-50%);
   z-index: 1999;
   max-width: 1000px;
   width: 90%;
   border-radius: 16px;
   overflow: hidden;
   pointer-events: auto;
   border: 1px solid rgba(255, 255, 255, 0.1);
 }

 .control-card {
   border-radius: 16px;
   box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
   background: #1a1a1a;
   border: 0px solid #333;
 }

 .control-card :deep(.ant-card-body) {
   background: #1a1a1a;
   color: #fff;
   padding: 16px;
 }

 .control-card :deep(.ant-card-head) {
   background: #1a1a1a;
   border-bottom: 1px solid #333;
 }

 .control-card :deep(.ant-card-head-title) {
   color: #fff;
 }

 .control-layout {
   display: flex;
   flex-direction: column;
   margin: 0 auto;
 }

 /* 模式选择区域 */


   .main-input-row {
    display: flex;
    align-items: flex-start;
  }

  .reference-section {
    flex-shrink: 0;
  }

  .input-group {
    flex: 1;
  }

  .prompt-input-group {
    width: 100%;
  }

  /* 控制行布局 */
  .controls-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
    margin-bottom: 8px;
  }

  .model-lora-group {
    display: flex;
    gap: 8px;
    align-items: center;
    flex: 1;
  }

  .model-selector-section {
    width: 140px;
    flex-shrink: 0;
  }
  
  .video-config-section {
    display: flex;
    gap: 12px;
    align-items: center;
    flex-shrink: 0;
  }
  
  .video-config-item {
    display: flex;
    align-items: center;
    gap: 6px;
  }
  
  .video-config-item label {
    color: #999;
    font-size: 12px;
    white-space: nowrap;
  }
  
  .video-config-input {
    width: 60px;
  }
  
  .video-config-select {
    width: 80px;
  }

  .lora-dropdown-section {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-shrink: 0;
  }

  .generate-section {
    flex-shrink: 0;
  }

 .prompt-input {
   background: #2a2a2a;
   border: 1px solid #444;
   color: #fff;
   border-radius: 8px;
 }

 .prompt-input:focus {
   border-color: #1890ff;
   box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
 }

 .generate-btn {
   border-radius: 8px;
   background: linear-gradient(135deg, #1890ff, #096dd9);
   border: none;
   font-weight: 600;
   min-width: 80px;
 }

 .generate-btn:hover {
   background: linear-gradient(135deg, #40a9ff, #1890ff);
   transform: translateY(-1px);
 }

 /* LoRA集成区域样式 */
 .lora-integrated-section {
   background: #2a2a2a;
   border-radius: 8px;
   padding: 12px;
   border: 1px solid #444;
 }

 .lora-header {
   display: flex;
   justify-content: space-between;
   align-items: center;
   margin-bottom: 8px;
 }

 .lora-title {
   font-size: 14px;
   font-weight: 600;
   color: #fff;
 }

 .lora-header-controls {
   display: flex;
   gap: 8px;
 }

 .lora-quick-select {
   display: flex;
   flex-wrap: wrap;
   gap: 8px;
   margin-bottom: 8px;
 }

 .lora-quick-item {
   display: flex;
   align-items: center;
   gap: 8px;
   padding: 6px 10px;
   background: #3a3a3a;
   border: 1px solid #555;
   border-radius: 6px;
   cursor: pointer;
   transition: all 0.2s;
   min-width: 120px;
 }

 .lora-quick-item:hover {
   background: #4a4a4a;
   border-color: #666;
 }

 .lora-quick-item.lora-selected {
   background: #1890ff;
   border-color: #1890ff;
   color: #fff;
 }

 .lora-quick-info {
   flex: 1;
   min-width: 0;
 }

 .lora-quick-name {
   font-size: 12px;
   font-weight: 500;
   white-space: nowrap;
   overflow: hidden;
   text-overflow: ellipsis;
 }

 .lora-quick-size {
   font-size: 10px;
   color: #999;
   margin-top: 2px;
 }

 .no-loras {
   padding: 8px;
   text-align: center;
 }

 .no-loras-text {
   font-size: 12px;
   color: #999;
 }

   .selected-loras-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
    align-items: center;
  }

  .selected-lora-tag {
   display: flex;
   align-items: center;
   gap: 6px;
   background: #2a2a2a;
   border: 1px solid #444;
   border-radius: 4px;
   padding: 2px 6px;
   font-size: 11px;
   color: #fff;
 }

 .lora-tag-preview {
   width: 20px;
   height: 20px;
   display: flex;
   align-items: center;
   justify-content: center;
   background: rgba(255, 255, 255, 0.1);
   border-radius: 4px;
   flex-shrink: 0;
 }

 .lora-tag-image {
   width: 100%;
   height: 100%;
   border-radius: 4px;
   overflow: hidden;
 }

 .lora-tag-image img {
   width: 100%;
   height: 100%;
   object-fit: cover;
 }

 .lora-tag-icon {
   font-size: 12px;
 }

 .lora-tag-name {
   font-weight: 500;
   max-width: 120px;
   overflow: hidden;
   text-overflow: ellipsis;
   white-space: nowrap;
 }

   .lora-tag-remove {
    padding: 0;
    height: 16px;
    width: 16px;
    min-width: 16px;
    color: #fff;
    border: none;
    background: transparent;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    font-weight: bold;
  }

 .lora-tag-remove:hover {
   background: rgba(255, 255, 255, 0.2);
   color: #fff;
 }

   /* 响应式设计 */
  @media (max-width: 768px) {
    .main-input-row {
      flex-direction: column;
    }
    
    .controls-row {
      flex-direction: column;
      align-items: stretch;
    }
    
    .model-lora-group {
      flex-direction: column;
      width: 100%;
    }
    
         .model-selector-section {
       width: 100%;
     }
     
     .lora-dropdown-section {
       flex-direction: column;
       align-items: stretch;
       width: 100%;
     }
    
    .generate-section {
      width: 100%;
    }
    
    .generate-btn {
      width: 100%;
      height: 48px;
    }
    
    .selected-loras-tags {
      flex-direction: column;
    }
  }

/* LoRA下拉菜单区域样式 */
.lora-dropdown-section {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}
 </style>