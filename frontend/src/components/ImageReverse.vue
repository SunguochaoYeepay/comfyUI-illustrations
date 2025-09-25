<template>
  <div class="image-reverse-panel">
    <div class="reverse-header">
      <h4>图片内容反推</h4>
      <a-button 
        type="primary" 
        size="small" 
        :loading="isReversing"
        :disabled="!imageUrl"
        @click="handleReverse"
      >
        <template #icon>
          <SearchOutlined />
        </template>
        {{ isReversing ? '反推中...' : '开始反推' }}
      </a-button>
    </div>
    
    <div class="reverse-content">
      <!-- 反推结果 -->
      <div v-if="reverseResult" class="reverse-result">
        <div class="result-header">
          <span class="result-label">反推结果：</span>
          <div class="result-actions">
            <a-button 
              type="text" 
              size="small" 
              @click="usePrompt"
              title="使用提示词"
              class="use-prompt-btn"
            >
              使用提示词
            </a-button>
            <a-button 
              type="text" 
              size="small" 
              @click="copyResult"
              title="复制结果"
            >
              <CopyOutlined />
            </a-button>
          </div>
        </div>
        <div class="result-text">
          {{ reverseResult }}
        </div>
      </div>
      
      <!-- 错误信息 -->
      <div v-if="reverseError" class="reverse-error">
        <div class="error-icon">⚠️</div>
        <div class="error-text">{{ reverseError }}</div>
      </div>
      
      <!-- 空状态 -->
      <div v-if="!reverseResult && !reverseError && !isReversing" class="reverse-empty">
        <div class="empty-icon">🔍</div>
        <div class="empty-text">点击"开始反推"分析图片内容</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { message } from 'ant-design-vue'
import { SearchOutlined, CopyOutlined } from '@ant-design/icons-vue'

const props = defineProps({
  imageUrl: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['use-prompt'])

const isReversing = ref(false)
const reverseResult = ref('')
const reverseError = ref('')

// 处理图片反推
const handleReverse = async () => {
  if (!props.imageUrl) {
    message.warning('请先选择图片')
    return
  }
  
  isReversing.value = true
  reverseError.value = ''
  reverseResult.value = ''
  
  try {
    console.log('开始图片反推，图片URL:', props.imageUrl)
    
    // 处理图片URL格式
    let imageUrl = props.imageUrl
    
    // 如果是相对路径，转换为完整的URL
    if (imageUrl && !imageUrl.startsWith('http://') && !imageUrl.startsWith('https://') && !imageUrl.startsWith('blob:')) {
      // 相对路径，需要转换为完整的URL
      if (imageUrl.startsWith('/')) {
        // 已经是绝对路径，直接添加协议和域名
        imageUrl = `${window.location.protocol}//${window.location.host}${imageUrl}`
      } else {
        // 相对路径，需要添加基础路径
        imageUrl = `${window.location.protocol}//${window.location.host}/${imageUrl}`
      }
      console.log('转换后的完整URL:', imageUrl)
    }
    
    // 调用图片反推API
    const response = await fetch('/api/image/reverse', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        image_url: imageUrl
      })
    })
    
    if (!response.ok) {
      throw new Error(`反推请求失败: ${response.status}`)
    }
    
    const result = await response.json()
    console.log('图片反推结果:', result)
    
    if (result.success && result.prompt) {
      reverseResult.value = result.prompt
      message.success('图片反推完成')
    } else {
      throw new Error(result.message || '反推失败')
    }
    
  } catch (error) {
    console.error('图片反推失败:', error)
    reverseError.value = error.message || '反推过程中发生错误'
    message.error('图片反推失败')
  } finally {
    isReversing.value = false
  }
}

// 复制反推结果
const copyResult = async () => {
  if (!reverseResult.value) return
  
  try {
    await navigator.clipboard.writeText(reverseResult.value)
    message.success('已复制到剪贴板')
  } catch (error) {
    console.error('复制失败:', error)
    message.error('复制失败')
  }
}

// 使用提示词
const usePrompt = () => {
  if (!reverseResult.value) return
  
  // 通过事件向父组件传递提示词
  emit('use-prompt', reverseResult.value)
  message.success('提示词已应用到生图界面')
}

// 监听图片URL变化，清空之前的结果
watch(() => props.imageUrl, () => {
  reverseResult.value = ''
  reverseError.value = ''
})
</script>

<style scoped>
.image-reverse-panel {
  background: #1a1a1a;
  border-radius: 8px;
  padding: 16px;
  min-height: 200px; /* 改为最小高度而不是固定高度 */
  display: flex;
  flex-direction: column;
}

.reverse-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #333;
}

.reverse-header h4 {
  margin: 0;
  color: #fff;
  font-size: 16px;
  font-weight: 600;
}

.reverse-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0; /* 允许flex子项收缩 */
}

.reverse-result {
  background: #2a2a2a;
  border-radius: 6px;
  padding: 12px;
  border: 1px solid #444;
  max-height: none; /* 移除高度限制 */
  overflow: visible; /* 允许内容溢出显示 */
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.result-label {
  color: #fff;
  font-weight: 500;
  font-size: 14px;
}

.result-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.use-prompt-btn {
  color: #1890ff !important;
  font-size: 12px;
  padding: 4px 8px;
  height: auto;
  line-height: 1.2;
}

.use-prompt-btn:hover {
  color: #40a9ff !important;
  background: rgba(24, 144, 255, 0.1);
}

.result-text {
  color: #e0e0e0;
  line-height: 1.6;
  font-size: 14px;
  white-space: pre-wrap;
  word-break: break-word;
}

.reverse-error {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  background: #2d1b1b;
  border: 1px solid #5c2c2c;
  border-radius: 6px;
  color: #ff6b6b;
}

.error-icon {
  font-size: 16px;
}

.error-text {
  flex: 1;
  font-size: 14px;
}

.reverse-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
  color: #666;
  text-align: center;
}

.empty-icon {
  font-size: 32px;
  margin-bottom: 8px;
  opacity: 0.6;
}

.empty-text {
  font-size: 14px;
  opacity: 0.8;
}

/* 按钮样式调整 */
:deep(.ant-btn-primary) {
  background: #667eea;
  border-color: #667eea;
}

:deep(.ant-btn-primary:hover) {
  background: #5a6fd8;
  border-color: #5a6fd8;
}

:deep(.ant-btn-text) {
  color: #999;
}

:deep(.ant-btn-text:hover) {
  color: #fff;
  background: rgba(255, 255, 255, 0.1);
}
</style>
