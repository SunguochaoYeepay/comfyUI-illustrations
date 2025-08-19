<template>
  <div class="control-section">
    <a-card class="control-card">
      <div class="control-layout">
        <!-- 主要输入区域 -->
        <div class="main-input-row">
          <!-- 参考图片区域 -->
          <div class="reference-section">
            <ReferenceUpload
              v-model:file-list="localReferenceImages"
              @preview="$emit('preview', $event)"
            />
          </div>

          <!-- 提示词和生成按钮区域 -->
          <div class="input-group">
            <div class="prompt-generate-row">
              <div class="prompt-input-group">
                <a-textarea
                  v-model:value="localPrompt"
                  placeholder="请详细描述您想要生成的图像，支持中文输入（如：一只可爱的橙色小猫坐在花园里，阳光明媚，高清摄影风格）"
                  :rows="2"
                  class="prompt-input"
                />
              </div>
              
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
            
            <!-- 模型和LoRA选择器 - 左右对齐 -->
            <div class="model-lora-row">
              <!-- 基础模型选择器 -->
              <ModelSelector 
                v-model:model="localModel"
                class="model-selector-section"
              />
              
              <!-- LoRA选择器 - 下拉菜单样式 -->
              <div class="lora-dropdown-section">
                <a-dropdown 
                  :trigger="['click']" 
                  placement="bottomLeft"
                  @visibleChange="handleLoraDropdownVisibleChange"
                >
                  <div class="lora-dropdown-trigger">
                    <div class="lora-trigger-content">
                      <div class="lora-trigger-icon">🎨</div>
                      <div class="lora-trigger-info">
                        <div class="lora-trigger-name">LoRA风格模型</div>
                      </div>
                      <div class="lora-trigger-count">
                        <a-tag :color="selectedLoras.length > 0 ? 'blue' : 'default'" size="small">
                          {{ selectedLoras.length }}/4
                        </a-tag>
                      </div>
                    </div>
                    <div class="lora-trigger-arrow">
                      <DownOutlined />
                    </div>
                  </div>
                  
                  <template #overlay>
                    <div class="lora-dropdown-menu">
                      <div class="lora-dropdown-header">
                        <span class="lora-dropdown-title">选择LoRA风格模型</span>
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
                          @click="toggleLora(lora)"
                        >
                          <div class="lora-dropdown-item-icon">
                            <span class="lora-icon">🎨</span>
                          </div>
                          <div class="lora-dropdown-item-info">
                            <div class="lora-dropdown-item-name">{{ lora.name.replace('.safetensors', '') }}</div>
                            <div class="lora-dropdown-item-size">{{ formatFileSize(lora.size) }}</div>
                          </div>
                          <div class="lora-dropdown-item-status">
                            <a-checkbox 
                              :checked="isLoraSelected(lora.name)"
                              @change="(e) => handleLoraToggle(lora, e.target.checked)"
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
              </div>
            </div>
            
             <!-- 已选择的LoRA配置 -->
             <div v-if="selectedLoras.length > 0" class="selected-loras-compact">
               <div 
                 v-for="(lora, index) in selectedLoras" 
                 :key="`selected-${lora.name}-${index}`"
                 class="selected-lora-compact-item"
               >
                 <div class="lora-compact-header">
                   <span class="lora-compact-title">{{ lora.name.replace('.safetensors', '') }}</span>
                   <a-button 
                     type="text" 
                     size="small" 
                     danger
                     @click="removeLora(index)"
                   >
                     <template #icon>
                       <DeleteOutlined />
                     </template>
                   </a-button>
                 </div>
                 
                 <div class="lora-compact-controls">
                   <div class="control-compact-group">
                     <label>UNET:</label>
                     <a-slider
                       v-model:value="lora.strength_model"
                       :min="0"
                       :max="2"
                       :step="0.1"
                       :tooltip-formatter="(value) => `${value}`"
                       style="width: 80px;"
                     />
                     <span class="value-display">{{ lora.strength_model }}</span>
                   </div>
                   
                   <div class="control-compact-group">
                     <label>CLIP:</label>
                     <a-slider
                       v-model:value="lora.strength_clip"
                       :min="0"
                       :max="2"
                       :step="0.1"
                       :tooltip-formatter="(value) => `${value}`"
                       style="width: 80px;"
                     />
                     <span class="value-display">{{ lora.strength_clip }}</span>
                   </div>
                   
                   <div class="control-compact-group">
                     <label>触发词:</label>
                     <a-input
                       v-model:value="lora.trigger_word"
                       placeholder="可选"
                       size="small"
                       style="width: 100px;"
                     />
                   </div>
                 </div>
               </div>
             </div>
           </div>
         </div>
       </div>
     </a-card>
   </div>
 </template>

 <script setup>
 import { computed, ref, onMounted, watch } from 'vue'
 import { message } from 'ant-design-vue'
 import { ReloadOutlined, DeleteOutlined, DownOutlined } from '@ant-design/icons-vue'
 import ReferenceUpload from './ReferenceUpload.vue'
 import ModelSelector from './ModelSelector.vue'

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
     default: 'flux1-dev'
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
   'generate',
   'preview'
 ])

 // LoRA相关状态
 const availableLoras = ref([])
 const loading = ref(false)
 const loraPanelExpanded = ref(false) // 控制LoRA面板的展开/收起

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

 // 处理生成按钮点击
 const handleGenerate = () => {
   emit('generate')
 }

 // LoRA相关方法
 const fetchLoras = async () => {
   try {
     loading.value = true
     // 添加模型参数来过滤LoRA
     const response = await fetch(`${API_BASE}/api/loras?model=${localModel.value}`)
     if (response.ok) {
       const data = await response.json()
       availableLoras.value = data.loras || []
       console.log('📋 获取到LoRA列表:', availableLoras.value)
       console.log('🎯 当前模型:', data.model, '模型类型:', data.model_type)
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
       message.info('模型已切换，已清空之前选择的LoRA（LoRA类型不兼容）')
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
   max-width: 800px;
   width: 90%;
   border-radius: 16px;
   overflow: hidden;
 }

 .control-card {
   border-radius: 16px;
   box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
   background: #1a1a1a;
   border: 1px solid #333;
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
   gap: 8px;
   margin: 0 auto;
 }

 .main-input-row {
   display: flex;
   gap: 12px;
   align-items: flex-start;
 }

 .reference-section {
   flex-shrink: 0;
 }

 .input-group {
   flex: 1;
   display: flex;
   flex-direction: column;
   gap: 12px;
 }

 /* 模型和LoRA选择器行布局 */
 .model-lora-row {
   display: flex;
   gap: 8px;
   align-items: stretch;
 }

 .model-selector-section {
   flex: 1;
 }

 .lora-dropdown-section {
   flex: 1;
 }

 .prompt-generate-row {
   display: flex;
   gap: 12px;
   align-items: flex-start;
 }

 .prompt-input-group {
   flex: 1;
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
   height: 64px;
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

 .selected-loras-compact {
   display: flex;
   flex-direction: column;
   gap: 8px;
 }

 .selected-lora-compact-item {
   background: #3a3a3a;
   border: 1px solid #555;
   border-radius: 6px;
   padding: 8px;
 }

 .lora-compact-header {
   display: flex;
   justify-content: space-between;
   align-items: center;
   margin-bottom: 6px;
 }

 .lora-compact-title {
   font-size: 12px;
   font-weight: 600;
   color: #fff;
 }

 .lora-compact-controls {
   display: flex;
   gap: 12px;
   align-items: center;
   flex-wrap: wrap;
 }

 .control-compact-group {
   display: flex;
   align-items: center;
   gap: 6px;
 }

 .control-compact-group label {
   font-size: 11px;
   color: #ccc;
   min-width: 40px;
 }

 .value-display {
   font-size: 11px;
   color: #fff;
   min-width: 20px;
   text-align: center;
 }

 /* 响应式设计 */
 @media (max-width: 768px) {
   .main-input-row {
     flex-direction: column;
   }
   
   .prompt-generate-row {
     flex-direction: column;
   }
   
   .model-lora-row {
     flex-direction: column;
   }
   
   .generate-btn {
     width: 100%;
     height: 48px;
   }
   
   .lora-quick-select {
     flex-direction: column;
   }
   
   .lora-quick-item {
     width: 100%;
   }
   
   .lora-compact-controls {
     flex-direction: column;
     align-items: stretch;
   }
 }

 /* LoRA下拉菜单样式 */
 .lora-dropdown-section {
   width: 100%;
 }

 .lora-dropdown-trigger {
   display: flex;
   justify-content: space-between;
   align-items: center;
   padding: 6px 10px;
   background: #2a2a2a;
   border: 1px solid #444;
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
   color: inherit;
 }

 .lora-dropdown-item-size {
   font-size: 12px;
   color: #ccc;
 }

 .lora-dropdown-item.lora-dropdown-selected .lora-dropdown-item-size {
   color: rgba(255, 255, 255, 0.8);
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