<template>
  <div class="size-selector-section">
    <!-- 尺寸选择器下拉菜单 -->
    <a-dropdown 
      :trigger="['click']" 
      placement="bottomLeft"
      @openChange="handleSizeDropdownVisibleChange"
      :overlayStyle="{ pointerEvents: 'auto' }"
    >
      <div class="size-dropdown-trigger">
        <span class="size-label">尺寸:</span>
        <span class="size-value">{{ selectedSizeDisplay }}</span>
        <DownOutlined class="dropdown-icon" />
      </div>
      
      <template #overlay>
        <div class="size-dropdown-panel">
          <div class="size-panel-header">
            <span class="panel-title">选择图片尺寸</span>
            <a-button 
              type="text" 
              size="small" 
              @click="refreshSizes"
              :loading="loading"
              class="refresh-btn"
            >
              <ReloadOutlined />
            </a-button>
          </div>
          
          <div class="size-options">
            <!-- 预设尺寸选项 -->
            <div 
              v-for="size in availableSizes" 
              :key="`${size.width}x${size.height}`"
              class="size-option"
              :class="{ 'selected': isSizeSelected(size) }"
              @click="selectSize(size)"
            >
              <div class="size-info">
                <span class="size-dimensions">{{ size.width }} × {{ size.height }}</span>
                <span class="size-ratio">{{ size.ratio }}</span>
              </div>
              <div class="size-preview">
                <div 
                  class="preview-box"
                  :style="{ 
                    aspectRatio: `${size.width}/${size.height}`,
                    backgroundColor: isSizeSelected(size) ? '#667eea' : '#444'
                  }"
                ></div>
              </div>
            </div>
          </div>
          
          <!-- 自定义尺寸 -->
          <div class="custom-size-section">
            <div class="custom-size-header">
              <span>自定义尺寸</span>
            </div>
            <div class="custom-size-inputs">
              <a-input-number
                v-model:value="customWidth"
                placeholder="宽度"
                :min="256"
                :max="4096"
                :step="64"
                size="small"
                class="size-input"
              />
              <span class="size-separator">×</span>
              <a-input-number
                v-model:value="customHeight"
                placeholder="高度"
                :min="256"
                :max="4096"
                :step="64"
                size="small"
                class="size-input"
              />
              <a-button 
                type="primary" 
                size="small" 
                @click="applyCustomSize"
                :disabled="!customWidth || !customHeight"
                class="apply-btn"
              >
                应用
              </a-button>
            </div>
          </div>
          
          <!-- 配置来源信息 -->
          <div v-if="configSource" class="config-info">
            <span class="config-source">配置来源: {{ getConfigSourceText(configSource) }}</span>
            <span v-if="lastUpdated" class="config-time">{{ formatTime(lastUpdated) }}</span>
          </div>
        </div>
      </template>
    </a-dropdown>
    
    <!-- 生成数量选择器 -->
    <a-dropdown 
      :trigger="['click']" 
      placement="bottomLeft"
      @openChange="handleCountDropdownVisibleChange"
      :overlayStyle="{ pointerEvents: 'auto' }"
    >
      <div class="count-dropdown-trigger">
        <span class="count-label">数量:</span>
        <span class="count-value">{{ localCount }}张</span>
        <DownOutlined class="dropdown-icon" />
      </div>
      
      <template #overlay>
        <div class="count-dropdown-panel">
          <div class="count-options">
            <div 
              v-for="count in [1, 2, 3, 4]" 
              :key="count"
              class="count-option"
              :class="{ 'selected': localCount === count }"
              @click="selectCount(count)"
            >
              <span class="count-number">{{ count }}张</span>
              <span class="count-desc">{{ getCountDescription(count) }}</span>
            </div>
          </div>
        </div>
      </template>
    </a-dropdown>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { message } from 'ant-design-vue'
import { ReloadOutlined, DownOutlined } from '@ant-design/icons-vue'

// Props
const props = defineProps({
  size: {
    type: String,
    default: '1024x1024'
  },
  count: {
    type: Number,
    default: 1
  }
})

// Emits
const emit = defineEmits([
  'update:size',
  'update:count'
])

// API基础URL
const API_BASE = (() => {
  if (import.meta.env.DEV) {
    return 'http://localhost:8888'  // admin后端运行在8888端口
  }
  return import.meta.env.VITE_API_BASE_URL || ''
})()

// 响应式数据
const availableSizes = ref([])
const loading = ref(false)
const sizePanelExpanded = ref(false)
const configSource = ref('')
const lastUpdated = ref('')
const customWidth = ref(1024)
const customHeight = ref(1024)

// 双向绑定的计算属性
const localSize = computed({
  get: () => props.size,
  set: (value) => emit('update:size', value)
})

const localCount = computed({
  get: () => props.count,
  set: (value) => emit('update:count', value)
})

// 计算属性：当前选中尺寸的显示文本
const selectedSizeDisplay = computed(() => {
  const [width, height] = localSize.value.split('x').map(Number)
  if (width && height) {
    const ratio = getAspectRatio(width, height)
    return `${width} × ${height} (${ratio})`
  }
  return localSize.value
})

// 获取宽高比
const getAspectRatio = (width, height) => {
  const gcd = (a, b) => b === 0 ? a : gcd(b, a % b)
  const divisor = gcd(width, height)
  return `${width / divisor}:${height / divisor}`
}

// 判断尺寸是否被选中
const isSizeSelected = (size) => {
  return localSize.value === `${size.width}x${size.height}`
}

// 选择尺寸
const selectSize = (size) => {
  localSize.value = `${size.width}x${size.height}`
  console.log('选择尺寸:', localSize.value)
}

// 应用自定义尺寸
const applyCustomSize = () => {
  if (customWidth.value && customHeight.value) {
    localSize.value = `${customWidth.value}x${customHeight.value}`
    console.log('应用自定义尺寸:', localSize.value)
    message.success('自定义尺寸已应用')
  }
}

// 数量选择相关方法
const selectCount = (count) => {
  localCount.value = count
  console.log('选择生成数量:', count)
}

// 获取数量描述
const getCountDescription = (count) => {
  const descriptions = {
    1: '单张生成',
    2: '批量生成',
    3: '多张生成',
    4: '大量生成'
  }
  return descriptions[count] || ''
}

// 处理数量下拉菜单显示状态变化
const handleCountDropdownVisibleChange = (visible) => {
  // 可以在这里添加额外的逻辑
}

// 获取尺寸配置
const fetchSizes = async () => {
  try {
    loading.value = true
    const response = await fetch(`${API_BASE}/api/admin/image-gen-config`)
    if (response.ok) {
      const data = await response.json()
      
      // 构建尺寸选项
      const sizes = []
      
      // 添加默认尺寸
      if (data.default_size) {
        sizes.push({
          width: data.default_size.width,
          height: data.default_size.height,
          ratio: getAspectRatio(data.default_size.width, data.default_size.height),
          isDefault: true
        })
      }
      
      // 添加比例选项
      if (data.size_ratios && Array.isArray(data.size_ratios)) {
        const baseSize = data.default_size ? Math.min(data.default_size.width, data.default_size.height) : 1024
        
        data.size_ratios.forEach(ratio => {
          if (ratio && ratio.includes(':')) {
            const [widthRatio, heightRatio] = ratio.split(':').map(Number)
            if (widthRatio && heightRatio) {
              const width = Math.round(baseSize * widthRatio / Math.max(widthRatio, heightRatio))
              const height = Math.round(baseSize * heightRatio / Math.max(widthRatio, heightRatio))
              
              // 确保尺寸是64的倍数（ComfyUI要求）
              const adjustedWidth = Math.round(width / 64) * 64
              const adjustedHeight = Math.round(height / 64) * 64
              
              sizes.push({
                width: adjustedWidth,
                height: adjustedHeight,
                ratio: ratio,
                isPreset: true
              })
            }
          }
        })
      }
      
      // 去重并排序
      const uniqueSizes = sizes.filter((size, index, self) => 
        index === self.findIndex(s => s.width === size.width && s.height === size.height)
      ).sort((a, b) => {
        // 默认尺寸排在前面
        if (a.isDefault && !b.isDefault) return -1
        if (!a.isDefault && b.isDefault) return 1
        // 按面积排序
        return (b.width * b.height) - (a.width * a.height)
      })
      
      availableSizes.value = uniqueSizes
      configSource.value = 'backend'
      lastUpdated.value = new Date().toISOString()
      
      console.log('📐 获取到尺寸配置:', availableSizes.value)
      console.log('📊 配置来源:', configSource.value)
    } else {
      console.error('❌ 获取尺寸配置失败:', response.status)
      message.error('获取尺寸配置失败')
    }
  } catch (error) {
    console.error('❌ 获取尺寸配置出错:', error)
    message.error('获取尺寸配置出错')
    
    // 使用默认尺寸配置
    availableSizes.value = [
      { width: 1024, height: 1024, ratio: '1:1', isDefault: true },
      { width: 1024, height: 768, ratio: '4:3', isPreset: true },
      { width: 768, height: 1024, ratio: '3:4', isPreset: true },
      { width: 1024, height: 576, ratio: '16:9', isPreset: true },
      { width: 576, height: 1024, ratio: '9:16', isPreset: true }
    ]
    configSource.value = 'default'
  } finally {
    loading.value = false
  }
}

// 刷新尺寸配置
const refreshSizes = () => {
  fetchSizes()
}

// 处理下拉菜单显示状态变化
const handleSizeDropdownVisibleChange = (visible) => {
  sizePanelExpanded.value = visible
  if (visible && availableSizes.value.length === 0) {
    fetchSizes()
  }
}

// 获取配置来源文本
const getConfigSourceText = (source) => {
  const sourceMap = {
    'backend': '后台配置',
    'cache': '缓存配置',
    'local': '本地配置',
    'default': '默认配置',
    'error': '配置错误',
    'unknown': '未知来源'
  }
  return sourceMap[source] || source
}

// 格式化时间
const formatTime = (timeString) => {
  try {
    const date = new Date(timeString)
    return date.toLocaleTimeString('zh-CN', { 
      hour: '2-digit', 
      minute: '2-digit' 
    })
  } catch (error) {
    return ''
  }
}

// 监听当前尺寸变化，更新自定义尺寸输入框
watch(() => props.size, (newSize) => {
  if (newSize && newSize.includes('x')) {
    const [width, height] = newSize.split('x').map(Number)
    if (width && height) {
      customWidth.value = width
      customHeight.value = height
    }
  }
}, { immediate: true })

// 组件挂载时获取尺寸配置
onMounted(() => {
  fetchSizes()
})
</script>

<style scoped>
.size-selector-section {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.size-dropdown-trigger {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #2a2a2a;
  border: 1px solid #444;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  min-width: 140px;
}

.size-dropdown-trigger:hover {
  border-color: #667eea;
  background: #333;
}

.size-label {
  color: #999;
  font-size: 12px;
  white-space: nowrap;
}

.size-value {
  color: #fff;
  font-size: 12px;
  font-weight: 500;
  flex: 1;
  text-align: center;
}

.dropdown-icon {
  color: #999;
  font-size: 10px;
  transition: transform 0.2s ease;
}

.size-dropdown-trigger:hover .dropdown-icon {
  transform: rotate(180deg);
}

.size-dropdown-panel {
  background: #2a2a2a;
  border: 1px solid #444;
  border-radius: 8px;
  padding: 12px;
  min-width: 280px;
  max-height: 400px;
  overflow-y: auto;
}

.size-panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #444;
}

.panel-title {
  color: #fff;
  font-size: 14px;
  font-weight: 500;
}

.refresh-btn {
  color: #999;
  padding: 4px;
  min-width: auto;
}

.refresh-btn:hover {
  color: #667eea;
  background: #333;
}

.size-options {
  margin-bottom: 16px;
}

.size-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  margin-bottom: 4px;
  background: #333;
  border: 1px solid #444;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.size-option:hover {
  background: #3a3a3a;
  border-color: #555;
}

.size-option.selected {
  background: #667eea;
  border-color: #667eea;
}

.size-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.size-dimensions {
  color: #fff;
  font-size: 13px;
  font-weight: 500;
}

.size-ratio {
  color: #999;
  font-size: 11px;
}

.size-preview {
  margin-left: 12px;
}

.preview-box {
  width: 24px;
  height: 18px;
  border-radius: 2px;
  border: 1px solid #666;
}

.custom-size-section {
  margin-bottom: 12px;
  padding-top: 12px;
  border-top: 1px solid #444;
}

.custom-size-header {
  margin-bottom: 8px;
}

.custom-size-header span {
  color: #fff;
  font-size: 13px;
  font-weight: 500;
}

.custom-size-inputs {
  display: flex;
  align-items: center;
  gap: 8px;
}

.size-input {
  flex: 1;
  min-width: 0;
}

.size-separator {
  color: #999;
  font-size: 14px;
  font-weight: 500;
}

.apply-btn {
  min-width: 60px;
}

.config-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 8px;
  border-top: 1px solid #444;
  font-size: 11px;
}

.config-source {
  color: #999;
}

.config-time {
  color: #666;
}

.count-dropdown-trigger {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #2a2a2a;
  border: 1px solid #444;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  min-width: 100px;
}

.count-dropdown-trigger:hover {
  border-color: #667eea;
  background: #333;
}

.count-label {
  color: #999;
  font-size: 12px;
  white-space: nowrap;
}

.count-value {
  color: #fff;
  font-size: 12px;
  font-weight: 500;
  flex: 1;
  text-align: center;
}

.count-dropdown-panel {
  background: #2a2a2a;
  border: 1px solid #444;
  border-radius: 8px;
  padding: 8px;
  min-width: 160px;
}

.count-options {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.count-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #333;
  border: 1px solid #444;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.count-option:hover {
  background: #3a3a3a;
  border-color: #555;
}

.count-option.selected {
  background: #667eea;
  border-color: #667eea;
}

.count-number {
  color: #fff;
  font-size: 13px;
  font-weight: 500;
}

.count-desc {
  color: #999;
  font-size: 11px;
}

/* 全局样式覆盖 */
:deep(.ant-select-selector) {
  background: #2a2a2a !important;
  border-color: #444 !important;
  color: #fff !important;
}

:deep(.ant-select-selection-item) {
  color: #fff !important;
}

:deep(.ant-input-number) {
  background: #2a2a2a !important;
  border-color: #444 !important;
}

:deep(.ant-input-number-input) {
  background: transparent !important;
  color: #fff !important;
}

:deep(.ant-input-number-input::placeholder) {
  color: #999 !important;
}

:deep(.ant-button) {
  border-color: #444 !important;
}

:deep(.ant-button-primary) {
  background: #667eea !important;
  border-color: #667eea !important;
}

:deep(.ant-button-primary:hover) {
  background: #5a6fd8 !important;
  border-color: #5a6fd8 !important;
}
</style>
