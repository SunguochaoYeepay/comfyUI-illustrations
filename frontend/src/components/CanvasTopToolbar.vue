<template>
  <div class="canvas-top-toolbar">
    <!-- 左侧按钮组 - 居中对齐 -->
    <div v-if="showLeftControls" class="toolbar-left">
      <!-- 画布缩放操作 -->
      <div class="canvas-zoom-group">
        <button 
          class="zoom-btn" 
          @click="handleZoomOut"
          title="缩小"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <path d="M19,13H5V11H19V13Z"/>
          </svg>
        </button>
        <button 
          class="zoom-btn" 
          @click="handleZoomFit"
          title="适应画布"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <path d="M9,9H15V15H9V9M7,7V17H17V7H7Z"/>
          </svg>
        </button>
        <button 
          class="zoom-btn" 
          @click="handleZoom100"
          :title="`当前: ${Math.round(currentZoomLevel * 100)}%`"
        >
          <span class="zoom-text">{{ Math.round(currentZoomLevel * 100) }}%</span>
        </button>
        <button 
          class="zoom-btn" 
          @click="handleZoomIn"
          title="放大"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <path d="M19,13H13V19H11V13H5V11H11V5H13V11H19V13Z"/>
          </svg>
        </button>
      </div>

      <!-- 功能按钮组 - 原底部工具栏的功能按钮，只在主模式下显示 -->
      <div v-if="currentMode === ''" class="function-group">
        <button 
          class="function-btn inpainting" 
          @click="handleModeChange('inpainting')"
          :class="{ active: currentMode === 'inpainting' }"
          title="局部重绘"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
          </svg>
          <span>局部重绘</span>
        </button>
        <button 
          class="function-btn outpainting" 
          @click="handleModeChange('outpainting')"
          :class="{ active: currentMode === 'outpainting' }"
          title="扩图"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
          </svg>
          <span>扩图</span>
        </button>
        <button 
          class="function-btn detail" 
          @click="handleModeChange('detail')"
          :class="{ active: currentMode === 'detail' }"
          title="细节修复"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M12,4A8,8 0 0,1 20,12A8,8 0 0,1 12,20A8,8 0 0,1 4,12A8,8 0 0,1 12,4M12,6A6,6 0 0,0 6,12A6,6 0 0,0 12,18A6,6 0 0,0 18,12A6,6 0 0,0 12,6M12,8A4,4 0 0,1 16,12A4,4 0 0,1 12,16A4,4 0 0,1 8,12A4,4 0 0,1 12,8Z"/>
          </svg>
          <span>细节修复</span>
        </button>
        <button 
          class="function-btn hd" 
          @click="handleModeChange('hd')"
          :class="{ active: currentMode === 'hd' }"
          title="HD超清"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <path d="M4,6H20V16H4M20,18A2,2 0 0,0 22,16V6C22,4.89 21.1,4 20,4H4C2.89,4 2,4.89 2,6V16A2,2 0 0,0 4,18H0V20H24V18H20Z"/>
          </svg>
          <span>HD超清</span>
        </button>
        <button 
          class="function-btn cutout" 
          @click="handleModeChange('cutout')"
          :class="{ active: currentMode === 'cutout' }"
          title="抠图"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <path d="M19,3H5C3.89,3 3,3.89 3,5V19A2,2 0 0,0 5,21H19A2,2 0 0,0 21,19V5C21,3.89 20.1,3 19,3M19,5V19H5V5H19Z"/>
          </svg>
          <span>抠图</span>
        </button>
      </div>
    </div>

    <!-- 右侧按钮组 - 右对齐 -->
    <div class="toolbar-right">
      <!-- 文件操作组 -->
      <div class="file-group">
        <button class="file-btn upload" @click="handleUpload" title="上传">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z"/>
          </svg>
        </button>
        <button 
          class="history-btn" 
          @click="handleToggleHistory"
          @mousedown="console.log('🔄 历史按钮 mousedown 事件')"
          :class="{ active: showHistory }"
          title="历史记录"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <path d="M13.5,8H12V13L16.28,15.54L17,14.33L13.5,12.25V8M13,3A9,9 0 0,0 4,12H1L4.96,16.03L9,12H6A7,7 0 0,1 13,5A7,7 0 0,1 20,12A7,7 0 0,1 13,19C11.07,19 9.32,18.21 8.06,16.94L6.64,18.36C8.27,20 10.5,21 13,21A9,9 0 0,0 22,12A9,9 0 0,0 13,3"/>
          </svg>
        </button>
      </div>
    </div>

    <!-- 隐藏的文件输入 -->
    <input 
      ref="fileInput"
      type="file"
      accept="image/*"
      style="display: none"
      @change="handleFileSelect"
    />
  </div>
</template>

<script>
import { ref } from 'vue'

export default {
  name: 'CanvasTopToolbar',
  props: {
    canUndo: {
      type: Boolean,
      default: false
    },
    canRedo: {
      type: Boolean,
      default: false
    },
    currentCanvasSize: {
      type: String,
      default: 'fit'
    },
    currentZoomLevel: {
      type: Number,
      default: 1
    },
    showHistory: {
      type: Boolean,
      default: false
    },
    showLeftControls: {
      type: Boolean,
      default: true
    },
    currentMode: {
      type: String,
      default: ''
    }
  },
  emits: [
    'canvas-size-change',
    'zoom-in',
    'zoom-out',
    'zoom-fit',
    'zoom-100',
    'toggle-history',
    'undo',
    'redo',
    'upload',
    'clear',
    'download',
    'mode-change',
  ],
  setup(props, { emit }) {
    const fileInput = ref(null)
    const canvasSize = ref(props.currentCanvasSize)

    // 设置画布尺寸
    const setCanvasSize = (size) => {
      canvasSize.value = size
      emit('canvas-size-change', size)
    }

    // 缩放操作
    const handleZoomIn = () => {
      emit('zoom-in')
    }

    const handleZoomOut = () => {
      emit('zoom-out')
    }

    const handleZoomFit = () => {
      emit('zoom-fit')
    }

    const handleZoom100 = () => {
      emit('zoom-100')
    }

    // 历史操作
    const handleToggleHistory = () => {
      console.log('🔄 CanvasTopToolbar: 历史按钮被点击')
      emit('toggle-history')
    }

    const handleUndo = () => {
      if (props.canUndo) {
        emit('undo')
      }
    }

    const handleRedo = () => {
      if (props.canRedo) {
        emit('redo')
      }
    }

    // 文件操作
    const handleUpload = () => {
      fileInput.value?.click()
    }

    const handleFileSelect = (event) => {
      const file = event.target.files[0]
      if (file) {
        emit('upload', file)
      }
      event.target.value = ''
    }

    const handleClear = () => {
      emit('clear')
    }

    const handleDownload = () => {
      emit('download')
    }

    // 处理模式切换
    const handleModeChange = (mode) => {
      emit('mode-change', mode)
    }

    return {
      fileInput,
      canvasSize,
      setCanvasSize,
      handleZoomIn,
      handleZoomOut,
      handleZoomFit,
      handleZoom100,
      handleToggleHistory,
      handleUndo,
      handleRedo,
      handleUpload,
      handleFileSelect,
      handleClear,
      handleDownload,
      handleModeChange,
    }
  }
}
</script>

<style scoped>
.canvas-top-toolbar {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 4px;
  background: #2a2a2a;
  flex-shrink: 0;
  gap: 24px;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.canvas-zoom-group,
.function-group,
.file-group {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px;
  background: #333;
  border-radius: 6px;
  border: 1px solid #444;
}

.zoom-btn,
.function-btn,
.history-btn,
.file-btn,
.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 4px;
  background: transparent;
  color: #ccc;
  cursor: pointer;
  transition: all 0.2s ease;
}

/* 功能按钮特殊样式 - 带文字 */
.function-btn {
  flex-direction: column;
  gap: 2px;
  padding: 4px 6px;
  min-width: 60px;
  height: auto;
  font-size: 10px;
  font-weight: 500;
}

.function-btn svg {
  width: 14px;
  height: 14px;
}

.function-btn span {
  font-size: 9px;
  line-height: 1;
  white-space: nowrap;
}

.zoom-btn:hover,
.function-btn:hover,
.history-btn:hover,
.file-btn:hover,
.action-btn:hover {
  background: #444;
  color: white;
}

.function-btn.active,
.history-btn.active {
  background: #007bff;
  color: white;
}

/* 功能按钮颜色样式 */
.function-btn.inpainting {
  background: #28a745;
  color: white;
}

.function-btn.inpainting:hover {
  background: #218838;
}

.function-btn.outpainting {
  background: #17a2b8;
  color: white;
}

.function-btn.outpainting:hover {
  background: #138496;
}

.function-btn.detail {
  background: #6f42c1;
  color: white;
}

.function-btn.detail:hover {
  background: #5a32a3;
}

.function-btn.hd {
  background: #fd7e14;
  color: white;
}

.function-btn.hd:hover {
  background: #e8650e;
}

.function-btn.cutout {
  background: #20c997;
  color: white;
}

.function-btn.cutout:hover {
  background: #1aa179;
}

.history-btn:disabled,
.file-btn:disabled,
.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.history-btn:disabled:hover,
.file-btn:disabled:hover,
.action-btn:disabled:hover {
  background: transparent;
  color: #ccc;
}

.action-btn.clear {
  background: #dc3545;
  color: white;
}

.action-btn.clear:hover {
  background: #c82333;
}

.action-btn.download {
  background: #28a745;
  color: white;
}

.action-btn.download:hover {
  background: #218838;
}

.zoom-text {
  font-size: 10px;
  font-weight: 500;
}

.file-btn.upload {
  background: #17a2b8;
  color: white;
}

.file-btn.upload:hover {
  background: #138496;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .canvas-top-toolbar {
    padding: 4px 12px;
    gap: 8px;
  }
  
  .toolbar-left {
    gap: 8px;
  }
  
  .function-group,
  .file-group {
    gap: 2px;
    padding: 2px;
  }
  
  .function-btn {
    min-width: 50px;
    font-size: 9px;
  }
  
  .function-btn svg {
    width: 12px;
    height: 12px;
  }
  
  .function-btn span {
    font-size: 8px;
  }
  
  .history-btn,
  .file-btn,
  .action-btn {
    width: 28px;
    height: 28px;
  }
}

</style>
