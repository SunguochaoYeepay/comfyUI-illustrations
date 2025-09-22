<template>
  <a-dropdown 
    :trigger="['click']" 
    :placement="getPlacement()"
    @openChange="handleDropdownVisibleChange"
    :overlayStyle="{ pointerEvents: 'auto', zIndex: 10001 }"
    :getPopupContainer="getPopupContainer"
  >
    <div class="lora-dropdown-trigger">
      <div class="lora-trigger-content">
        <div class="lora-trigger-icon">🎨</div>
        <div class="lora-trigger-info">
          <div class="lora-trigger-name">
            风格模型{{ selectedLoras.length > 0 ? ` (${selectedLoras.length})` : '' }}
          </div>
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
            @click="$emit('refresh')"
            :loading="loading"
          >
            <template #icon>
              <ReloadOutlined />
            </template>
            刷新
          </a-button>
        </div>
        
        <!-- 分类tabs和LoRA列表 -->
        <div class="lora-content-wrapper" v-if="loraCategories.length > 0">
          <div class="lora-category-tabs">
            <div 
              class="lora-category-tab"
              :class="{ 'lora-category-tab-active': !selectedLoraCategory }"
              @click.stop="$emit('category-filter', '')"
            >
              <span class="tab-label">全部</span>
              <span class="tab-count">({{ availableLoras.length }})</span>
            </div>
            <div 
              v-for="category in loraCategories" 
              :key="category"
              class="lora-category-tab"
              :class="{ 'lora-category-tab-active': selectedLoraCategory === category }"
              @click.stop="$emit('category-filter', category)"
            >
              <span class="tab-label">{{ category }}</span>
              <span class="tab-count">({{ getCategoryCount(category) }})</span>
            </div>
          </div>
          
          <div class="lora-dropdown-list">
            <div 
             v-for="lora in filteredLoras" 
             :key="lora.name"
             class="lora-dropdown-item"
             :class="{ 'lora-dropdown-selected': isLoraSelected(lora.name) }"
             @click.stop="$emit('toggle-lora', lora)"
           >
            <div class="lora-dropdown-item-icon">
              <div v-if="lora.preview_image_path" class="lora-preview-image">
                <img 
                  :src="`${apiBase}/api/${lora.preview_image_path}?t=${new Date().getTime()}`"
                  :alt="lora.display_name || lora.name"
                  @error="handleImageError"
                />
              </div>
              <span v-else class="lora-icon">🎨</span>
            </div>
            <div class="lora-dropdown-item-info">
              <div class="lora-dropdown-item-name">{{ lora.display_name || lora.name.replace('.safetensors', '') }}</div>
              <div class="lora-dropdown-item-desc">{{ getLoraDescription(lora) }}</div>
            </div>
            <div class="lora-dropdown-item-status">
               <a-checkbox 
                 :checked="isLoraSelected(lora.name)"
                 @change="(e) => $emit('lora-toggle', lora, e.target.checked)"
                 @click.stop
               />
             </div>
          </div>
          
          <div v-if="availableLoras.length === 0" class="lora-dropdown-empty">
            <a-empty description="暂无可用的LoRA模型" size="small" />
          </div>
          </div>
        </div>
        
        <!-- 没有分类数据时的fallback -->
        <div v-else class="lora-dropdown-list">
          <div 
            v-for="lora in availableLoras" 
            :key="lora.name"
            class="lora-dropdown-item"
            :class="{ 'lora-dropdown-selected': isLoraSelected(lora.name) }"
            @click.stop="$emit('toggle-lora', lora)"
          >
            <div class="lora-dropdown-item-icon">
              <div v-if="lora.preview_image_path" class="lora-preview-image">
                <img 
                  :src="`${apiBase}/api/${lora.preview_image_path}?t=${new Date().getTime()}`"
                  :alt="lora.display_name || lora.name"
                  @error="handleImageError"
                />
              </div>
              <span v-else class="lora-icon">🎨</span>
            </div>
            <div class="lora-dropdown-item-info">
              <div class="lora-dropdown-item-name">{{ lora.display_name || lora.name.replace('.safetensors', '') }}</div>
              <div class="lora-dropdown-item-desc">{{ getLoraDescription(lora) }}</div>
            </div>
            <div class="lora-dropdown-item-status">
              <a-checkbox 
                :checked="isLoraSelected(lora.name)"
                @change="(e) => $emit('lora-toggle', lora, e.target.checked)"
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
</template>

<script setup>
import { computed } from 'vue'
import { ReloadOutlined, DownOutlined } from '@ant-design/icons-vue'

// Props
const props = defineProps({
  availableLoras: {
    type: Array,
    default: () => []
  },
  selectedLoras: {
    type: Array,
    default: () => []
  },
  loraCategories: {
    type: Array,
    default: () => []
  },
  selectedLoraCategory: {
    type: String,
    default: ''
  },
  loading: {
    type: Boolean,
    default: false
  },
  apiBase: {
    type: String,
    required: true
  }
})

// Emits
const emit = defineEmits([
  'refresh',
  'category-filter',
  'toggle-lora',
  'lora-toggle',
  'dropdown-visible-change'
])

// 计算属性：过滤后的LoRA列表
const filteredLoras = computed(() => {
  if (!props.selectedLoraCategory) {
    return props.availableLoras
  }
  return props.availableLoras.filter(lora => lora.category === props.selectedLoraCategory)
})

// 获取分类下的LoRA数量
const getCategoryCount = (category) => {
  return props.availableLoras.filter(lora => lora.category === category).length
}

// 检查LoRA是否被选中
const isLoraSelected = (loraName) => {
  return props.selectedLoras.some(lora => lora.name === loraName)
}

// 获取LoRA描述
const getLoraDescription = (lora) => {
  // 如果传入的是LoRA对象，优先使用其description字段
  if (typeof lora === 'object' && lora.description) {
    return lora.description
  }
  
  // 如果传入的是字符串（向后兼容），使用原来的逻辑
  const loraName = typeof lora === 'string' ? lora : lora.name
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

// 图片加载错误处理
const handleImageError = (event) => {
  console.error('图片加载失败:', event.target.src)
}

// 处理下拉菜单显示状态变化
const handleDropdownVisibleChange = (visible) => {
  emit('dropdown-visible-change', visible)
}

// 安全的获取弹出容器方法 - 使用body避免被父容器截断
const getPopupContainer = () => {
  // 直接使用body作为容器，避免被control-section的overflow限制
  return document?.body || document?.documentElement || document
}

// 动态计算placement
const getPlacement = () => {
  const controlPanel = document.querySelector('.control-section')
  if (controlPanel) {
    const rect = controlPanel.getBoundingClientRect()
    const viewportHeight = window.innerHeight
    const spaceBelow = viewportHeight - rect.bottom
    const spaceAbove = rect.top
    
    // 如果下方空间不足，向上展开
    if (spaceBelow < 400 && spaceAbove > spaceBelow) {
      return 'topLeft'
    }
  }
  return 'bottomLeft'
}
</script>

<style scoped>
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

.lora-trigger-arrow {
  color: #ccc;
  margin-left: 8px;
  transition: transform 0.2s;
}

.lora-dropdown-trigger:hover .lora-trigger-arrow {
  color: #fff;
}

.lora-dropdown-menu {
  background: #2a2a2a;
  border: 1px solid #444;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
  min-width: 320px;
  max-width: 450px;
  position: relative;
  z-index: 2000;
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

/* LoRA内容包装器 */
.lora-content-wrapper {
  display: flex;
  min-height: 200px;
  max-height: 60vh;
}

/* 分类tabs */
.lora-category-tabs {
  width: 120px;
  background: #1a1a1a;
  border-right: 1px solid #333;
  overflow-y: auto;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
}

/* 分类tabs滚动条样式 */
.lora-category-tabs::-webkit-scrollbar {
  width: 4px;
}

.lora-category-tabs::-webkit-scrollbar-track {
  background: #0a0a0a;
  border-radius: 2px;
}

.lora-category-tabs::-webkit-scrollbar-thumb {
  background: #444;
  border-radius: 2px;
}

.lora-category-tabs::-webkit-scrollbar-thumb:hover {
  background: #666;
}

.lora-category-tab {
  padding: 12px 16px;
  cursor: pointer;
  border-bottom: 1px solid #2a2a2a;
  transition: all 0.2s ease;
  display: flex;
  flex-direction: column;
  gap: 2px;
  color: #fff;
}

.lora-category-tab:hover {
  background: #2a2a2a;
}

.lora-category-tab-active {
  background: #1890ff;
  color: #fff;
}

.lora-category-tab-active:hover {
  background: #40a9ff;
}

.tab-label {
  font-size: 13px;
  font-weight: 500;
  line-height: 1.2;
  color: #fff;
}

.tab-count {
  font-size: 11px;
  opacity: 0.7;
  line-height: 1;
  color: #fff;
}

.lora-dropdown-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

/* 自定义滚动条样式 */
.lora-dropdown-list::-webkit-scrollbar {
  width: 6px;
}

.lora-dropdown-list::-webkit-scrollbar-track {
  background: #1a1a1a;
  border-radius: 3px;
}

.lora-dropdown-list::-webkit-scrollbar-thumb {
  background: #555;
  border-radius: 3px;
}

.lora-dropdown-list::-webkit-scrollbar-thumb:hover {
  background: #777;
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
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
}

.lora-icon {
  font-size: 24px;
}

.lora-preview-image {
  width: 100%;
  height: 100%;
  border-radius: 8px;
  overflow: hidden;
}

.lora-preview-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
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
