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
             <div v-if="isVideoModel" class="video-config-section">
               <div class="video-config-item">
                 <label>时长(秒):</label>
                 <a-input-number 
                   v-model:value="videoDuration" 
                   :min="1" 
                   :max="10" 
                   :step="1"
                   size="small"
                   class="video-config-input"
                 />
               </div>
               <div class="video-config-item">
                 <label>帧率:</label>
                 <a-select 
                   v-model:value="videoFps" 
                   size="small"
                   class="video-config-select"
                 >
                   <a-select-option value="8">8 FPS</a-select-option>
                   <a-select-option value="16">16 FPS</a-select-option>
                   <a-select-option value="24">24 FPS</a-select-option>
                 </a-select>
               </div>
             </div>
             
                           <!-- LoRA选择器 - 下拉菜单样式 -->
              <div v-if="shouldShowLoraPanel" class="lora-dropdown-section">
                                 <a-dropdown 
                   :trigger="['click']" 
                   placement="bottomLeft"
                   @openChange="handleLoraDropdownVisibleChange"
                   :overlayStyle="{ pointerEvents: 'auto' }"
                 >
                  <div class="lora-dropdown-trigger">
                    <div class="lora-trigger-content">
                      <div class="lora-trigger-icon">🎨</div>
                                             <div class="lora-trigger-info">
                         <div class="lora-trigger-name">风格模型</div>
                       </div>
                      
                    </div>
                    <div class="lora-trigger-arrow">
                      <DownOutlined />
                    </div>
                  </div>
                  
                  <template #overlay>
                    <div class="lora-dropdown-menu">
                                             <div class="lora-dropdown-header">
                         <span class="lora-dropdown-title">选择风格模型</span>
                        <a-button 
                          type="link" 
                          size="small" 
                          @click="refreshLoras"
                          :loading="loading"
                        >
                          <template #icon>
                            <ReloadOutlined />
                          </template>
                          刷新
                        </a-button>
                      </div>
                      
                      <div class="lora-dropdown-list">
                                                 <div 
                           v-for="lora in availableLoras" 
                           :key="lora.name"
                           class="lora-dropdown-item"
                           :class="{ 'lora-dropdown-selected': isLoraSelected(lora.name) }"
                           @click.stop="toggleLora(lora)"
                         >
                          <div class="lora-dropdown-item-icon">
                            <span class="lora-icon">🎨</span>
                          </div>
                          <div class="lora-dropdown-item-info">
                            <div class="lora-dropdown-item-name">{{ lora.name.replace('.safetensors', '') }}</div>
                            <div class="lora-dropdown-item-desc">{{ getLoraDescription(lora.name) }}</div>
                          </div>
                                                     <div class="lora-dropdown-item-status">
                             <a-checkbox 
                               :checked="isLoraSelected(lora.name)"
                               @change="(e) => handleLoraToggle(lora, e.target.checked)"
                               @click.stop
                             />
                           </div>
                        </div>
                        
                        <div v-if="availableLoras.length === 0" class="lora-dropdown-empty">
                          <a-empty description="暂无可用的LoRA模型" size="small" />
                        </div>
                      </div>
                    </div>
                  </template>
                </a-dropdown>
                
                <!-- 已选择的LoRA标签 - 放在LoRA选择器后面 -->
                <div v-if="selectedLoras.length > 0" class="selected-loras-tags">
                  <div 
                    v-for="(lora, index) in selectedLoras" 
                    :key="`selected-${lora.name}-${index}`"
                    class="selected-lora-tag"
                  >
                    <span class="lora-tag-name">{{ lora.name.replace('.safetensors', '') }}</span>
                                         <a-button 
                       type="text" 
                       size="small" 
                       danger
                       @click="removeLora(index)"
                       class="lora-tag-remove"
                     >
                       ×
                     </a-button>
                  </div>
                </div>
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
   import { ReloadOutlined, DownOutlined } from '@ant-design/icons-vue'
import ReferenceUpload from './ReferenceUpload.vue'
import MultiImageUpload from './MultiImageUpload.vue'
import ModelSelector from './ModelSelector.vue'
import SizeSelector from './SizeSelector.vue'

 // API基础URL - 自动检测环境
 const API_BASE = (() => {
   if (import.meta.env.DEV) {
     return 'http://localhost:9000'  // 开发环境指向后端9000端口
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
    default: 'flux-dev'
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
  'preview'
])

// 计算属性：根据图片数量和模型类型判断是否为融合模式
const isFusionMode = computed(() => {
  // Qwen和Gemini模型都支持多图融合
  const isMultiImageModel = localModel.value === 'qwen-image' || localModel.value === 'gemini-image'
  return isMultiImageModel && localReferenceImages.value.length >= 2
})

// 计算属性：判断是否为视频模型
const isVideoModel = computed(() => {
  return localModel.value === 'wan2.2-video'
})

// 计算属性：判断是否应该显示LoRA面板
const shouldShowLoraPanel = computed(() => {
  // 不支持LoRA的模型：Nano Banana（API模型）和Wan2.2视频模型
  const unsupportedModels = ['gemini-image', 'wan2.2-video']
  return !unsupportedModels.includes(localModel.value)
})

// 计算属性：判断是否应该显示上传按钮
const shouldShowUploadButton = computed(() => {
  const isMultiImageModel = localModel.value === 'qwen-image' || localModel.value === 'gemini-image'
  
  // 支持多图的模型：根据图片数量限制显示上传按钮
  if (isMultiImageModel) {
    // Qwen模型支持3张图片，其他模型最多2张
    const maxImages = localModel.value === 'qwen-image' ? 3 : 2
    return localReferenceImages.value.length < maxImages
  }
  
  // 其他模型：只有没有图片时才显示上传按钮
  return localReferenceImages.value.length === 0
})

// LoRA相关状态
const availableLoras = ref([])
const loading = ref(false)
const loraPanelExpanded = ref(false) // 控制LoRA面板的展开/收起
const loraConfigSource = ref('')
const loraLastUpdated = ref('')

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

 const selectedLoras = computed({
   get: () => props.loras,
   set: (value) => emit('update:loras', value)
 })

 const localModel = computed({
   get: () => props.model,
   set: (value) => emit('update:model', value)
 })

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
  
  // 如果上传了2张或更多图片，且当前不是支持多图的模型，则切换到qwen-image
  if (newCount >= 2) {
    const isMultiImageModel = localModel.value === 'qwen-image' || localModel.value === 'gemini-image'
    if (!isMultiImageModel) {
      console.log('🔄 自动切换到Qwen模型')
      localModel.value = 'qwen-image'
    }
  }
}, { immediate: true })

// 监听模型变化，处理图片数量限制
watch(() => localModel.value, (newModel) => {
  const isMultiImageModel = newModel === 'qwen-image' || newModel === 'gemini-image'
  
  // 如果切换到不支持多图的模型，且有多张图片，只保留第一张
  if (!isMultiImageModel && localReferenceImages.value.length > 1) {
    console.log('🔄 切换到不支持多图的模型，只保留第一张图片')
    localReferenceImages.value = [localReferenceImages.value[0]]
  }
}, { immediate: true })

// 获取提示词占位符
const getPromptPlaceholder = () => {
  if (isVideoModel.value) {
    return '请描述您想要的视频效果（如：镜头缓慢推进，人物微笑，背景模糊）'
  } else if (isFusionMode.value) {
    return '请描述多图融合的效果，支持中文输入（如：将三张图像拼接后，让左边的女人手里拎着中间棕色的包，坐在白色沙发上）'
  } else if (localModel.value === 'qwen-image') {
    return '请详细描述您想要生成的图像，支持中文输入（如：一只可爱的橙色小猫坐在花园里，阳光明媚，高清摄影风格）'
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

// LoRA相关方法
const fetchLoras = async () => {
  try {
    loading.value = true
    // 添加模型参数来过滤LoRA
    const response = await fetch(`${API_BASE}/api/loras?model=${localModel.value}`)
    if (response.ok) {
      const data = await response.json()
      availableLoras.value = data.loras?.loras || []
      loraConfigSource.value = data.config_source || 'unknown'
      loraLastUpdated.value = data.timestamp || ''
      console.log('📋 获取到LoRA列表:', availableLoras.value)
      console.log('🎯 当前模型:', data.model, '模型类型:', data.model_type)
      console.log('📊 LoRA配置来源:', loraConfigSource.value)
    } else {
      console.error('❌ 获取LoRA列表失败:', response.status)
      message.error('获取LoRA列表失败')
    }
  } catch (error) {
    console.error('❌ 获取LoRA列表出错:', error)
    message.error('获取LoRA列表出错')
  } finally {
    loading.value = false
  }
}

 const refreshLoras = () => {
   fetchLoras()
 }

 const isLoraSelected = (loraName) => {
   return selectedLoras.value.some(lora => lora.name === loraName)
 }

 const toggleLora = (lora) => {
   if (isLoraSelected(lora.name)) {
     removeLoraByName(lora.name)
   } else {
     addLora(lora)
   }
 }

 const handleLoraToggle = (lora, checked) => {
   if (checked) {
     addLora(lora)
   } else {
     removeLoraByName(lora.name)
   }
 }

 const addLora = (lora) => {
   if (selectedLoras.value.length >= 4) {
     message.warning('最多只能选择4个LoRA模型')
     return
   }
   
   // 检查是否已经选择了这个LoRA
   if (isLoraSelected(lora.name)) {
     console.log('⚠️ LoRA已经存在:', lora.name)
     return
   }
   
   // 检查LoRA兼容性
   if (!isLoraCompatible(lora.name)) {
     message.warning(`LoRA "${lora.name}" 与当前模型不兼容，已跳过`)
     return
   }
   
   const newLora = {
     name: lora.name,
     strength_model: 1.0,
     strength_clip: 1.0,
     trigger_word: '',
     enabled: true
   }
   
   selectedLoras.value = [...selectedLoras.value, newLora]
   console.log('✅ 添加LoRA:', newLora)
   console.log('📋 当前已选择的LoRA数量:', selectedLoras.value.length)
 }

 // 检查LoRA兼容性
 const isLoraCompatible = (loraName) => {
   const loraNameLower = loraName.toLowerCase()
   
   if (localModel.value.includes('flux')) {
     // Flux模型：排除Qwen相关的LoRA
     return !['qwen', '千问', 'qwen2'].some(keyword => loraNameLower.includes(keyword))
   } else if (localModel.value.includes('qwen')) {
     // Qwen模型：排除明确为Flux的LoRA
     return !['flux', 'kontext', 'sdxl'].some(keyword => loraNameLower.includes(keyword))
   }
   
   return true
 }

 const removeLora = (index) => {
   selectedLoras.value = selectedLoras.value.filter((_, i) => i !== index)
 }

 const removeLoraByName = (loraName) => {
   selectedLoras.value = selectedLoras.value.filter(lora => lora.name !== loraName)
 }

   // 获取LoRA描述
  const getLoraDescription = (loraName) => {
    const name = loraName.toLowerCase()
    
    // 根据LoRA名称关键词判断特点
    if (name.includes('字体') || name.includes('font')) {
      return '字体艺术风格，适合文字设计'
    } else if (name.includes('人物') || name.includes('portrait')) {
      return '人物肖像风格，适合人像生成'
    } else if (name.includes('风景') || name.includes('landscape')) {
      return '风景画风格，适合自然场景'
    } else if (name.includes('动漫') || name.includes('anime')) {
      return '动漫风格，适合二次元创作'
    } else if (name.includes('写实') || name.includes('realistic')) {
      return '写实风格，适合真实感图像'
    } else if (name.includes('艺术') || name.includes('art')) {
      return '艺术风格，适合创意表达'
    } else if (name.includes('复古') || name.includes('vintage')) {
      return '复古风格，适合怀旧主题'
    } else if (name.includes('现代') || name.includes('modern')) {
      return '现代风格，适合时尚设计'
    } else if (name.includes('科幻') || name.includes('sci-fi')) {
      return '科幻风格，适合未来主题'
    } else if (name.includes('童话') || name.includes('fairy')) {
      return '童话风格，适合梦幻场景'
    } else {
      return 'AI风格模型，增强生成效果'
    }
  }

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
  }

 // 控制LoRA面板的展开/收起
 const toggleLoraPanel = () => {
   loraPanelExpanded.value = !loraPanelExpanded.value
   
   // 当展开面板时，如果还没有加载过LoRA列表，则加载
   if (loraPanelExpanded.value && availableLoras.value.length === 0) {
     fetchLoras()
   }
 }

 const handleLoraDropdownVisibleChange = (visible) => {
   if (visible && availableLoras.value.length === 0) {
     fetchLoras()
   }
 }

 // 监听模型变化，自动刷新LoRA列表
 watch(localModel, (newModel, oldModel) => {
   if (newModel !== oldModel) {
     console.log('🔄 模型已切换:', oldModel, '->', newModel)
           // 清空已选择的LoRA，因为可能不兼容
      if (selectedLoras.value.length > 0) {
        selectedLoras.value = []
      }
     // 刷新LoRA列表
     fetchLoras()
   }
 })
 </script>

 <style scoped>
 .control-section {
   position: fixed;
   bottom: 0px;
   left: 50%;
   transform: translateX(-50%);
   z-index: 1000;
   max-width: 900px;
   width: 90%;
   border-radius: 16px;
   overflow: hidden;
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
    gap: 4px;
    background: #2a2a2a;
    border: 1px solid #444;
    border-radius: 4px;
    padding: 2px 6px;
    font-size: 11px;
    color: #fff;
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

 /* LoRA下拉菜单样式 */
 

 .lora-dropdown-trigger {
   display: flex;
   justify-content: space-between;
   align-items: center;
   padding: 6px 10px;
   background: #2a2a2a;
   border: 0px solid #444;
   border-radius: 6px;
   cursor: pointer;
   transition: all 0.2s;
   min-height: 36px;
 }

 .lora-dropdown-trigger:hover {
   background: #3a3a3a;
   border-color: #555;
 }

 .lora-trigger-content {
   display: flex;
   align-items: center;
   flex: 1;
   gap: 6px;
 }

 .lora-trigger-icon {
   font-size: 14px;
   flex-shrink: 0;
 }

 .lora-trigger-info {
   flex: 1;
   min-width: 0;
 }

 .lora-trigger-name {
   font-size: 12px;
   font-weight: 600;
   color: #fff;
   white-space: nowrap;
   overflow: hidden;
   text-overflow: ellipsis;
 }

 .lora-trigger-count {
   flex-shrink: 0;
 }

 .lora-trigger-arrow {
   color: #ccc;
   margin-left: 8px;
   transition: transform 0.2s;
 }

 .lora-dropdown-trigger:hover .lora-trigger-arrow {
   color: #fff;
 }

 /* LoRA下拉菜单样式 */
 .lora-dropdown-menu {
   background: #2a2a2a;
   border: 1px solid #444;
   border-radius: 8px;
   box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
   min-width: 320px;
   max-width: 400px;
 }

 .lora-dropdown-header {
   display: flex;
   justify-content: space-between;
   align-items: center;
   padding: 12px 16px;
   border-bottom: 1px solid #444;
 }

 .lora-dropdown-title {
   font-size: 14px;
   font-weight: 600;
   color: #fff;
 }

 .lora-dropdown-list {
   max-height: 300px;
   overflow-y: auto;
 }

 .lora-dropdown-item {
   display: flex;
   align-items: flex-start;
   padding: 12px 16px;
   cursor: pointer;
   transition: all 0.2s;
   border-bottom: 1px solid #333;
 }

 .lora-dropdown-item:hover {
   background: #3a3a3a;
 }

 .lora-dropdown-item:last-child {
   border-bottom: none;
 }

 .lora-dropdown-item.lora-dropdown-selected {
   background: #1890ff;
   color: #fff;
 }

 .lora-dropdown-item-icon {
   flex-shrink: 0;
   margin-right: 12px;
 }

 .lora-icon {
   font-size: 24px;
 }

 .lora-dropdown-item-info {
   flex: 1;
   min-width: 0;
 }

   .lora-dropdown-item-name {
    font-size: 14px;
    font-weight: 600;
    margin-bottom: 4px;
    color: #fff;
  }

  .lora-dropdown-item-desc {
    font-size: 11px;
    color: #ccc;
    line-height: 1.3;
    margin-top: 2px;
  }

  .lora-dropdown-item.lora-dropdown-selected .lora-dropdown-item-desc {
    color: rgba(255, 255, 255, 0.7);
  }

 .lora-dropdown-item-status {
   display: flex;
   align-items: center;
   margin-left: 12px;
   flex-shrink: 0;
 }

 .lora-dropdown-empty {
   padding: 20px;
   text-align: center;
 }

 /* 响应式设计 */
 @media (max-width: 768px) {
   .lora-dropdown-menu {
     min-width: 280px;
   }
   
   .lora-dropdown-item {
     flex-direction: column;
     gap: 8px;
   }
   
   .lora-dropdown-item-status {
     align-items: flex-start;
     margin-left: 0;
   }
 }
 </style>