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

      <!-- 画布尺寸选择 -->
      <div class="canvas-size-group">
        <button 
          class="size-btn" 
          :class="{ active: canvasSize === 'fit' }"
          @click="setCanvasSize('fit')"
          title="适应内容"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <path d="M4,4H20A2,2 0 0,1 22,6V18A2,2 0 0,1 20,20H4A2,2 0 0,1 2,18V6A2,2 0 0,1 4,4M4,6V18H20V6H4Z"/>
          </svg>
        </button>
        <button 
          class="size-btn" 
          :class="{ active: canvasSize === '1:1' }"
          @click="setCanvasSize('1:1')"
          title="1:1"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <path d="M3,3V21H21V3H3M5,5H19V19H5V5Z"/>
          </svg>
        </button>
        <button 
          class="size-btn" 
          :class="{ active: canvasSize === '4:3' }"
          @click="setCanvasSize('4:3')"
          title="4:3"
        >
          <svg width="16" height="12" viewBox="0 0 24 18" fill="currentColor">
            <path d="M3,3V15H21V3H3M5,5H19V13H5V5Z"/>
          </svg>
        </button>
        <button 
          class="size-btn" 
          :class="{ active: canvasSize === '3:2' }"
          @click="setCanvasSize('3:2')"
          title="3:2"
        >
          <svg width="16" height="11" viewBox="0 0 24 16" fill="currentColor">
            <path d="M3,3V13H21V3H3M5,5H19V11H5V5Z"/>
          </svg>
        </button>
        <button 
          class="size-btn" 
          :class="{ active: canvasSize === '16:9' }"
          @click="setCanvasSize('16:9')"
          title="16:9"
        >
          <svg width="16" height="9" viewBox="0 0 24 14" fill="currentColor">
            <path d="M3,3V11H21V3H3M5,5H19V9H5V5Z"/>
          </svg>
        </button>
      </div>

 

      <!-- 文件操作 -->
      <div class="file-group">
        <button class="file-btn upload" @click="handleUpload" title="上传">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z"/>
          </svg>
        </button>
        <button class="file-btn save" @click="handleSave" title="保存">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <path d="M15,9H5V5H15M12,19A3,3 0 0,1 9,16A3,3 0 0,1 12,13A3,3 0 0,1 15,16A3,3 0 0,1 12,19M17,3H5C3.89,3 3,3.9 3,5V19A2,2 0 0,0 5,21H19A2,2 0 0,0 21,19V7L17,3Z"/>
          </svg>
        </button>
      </div>
    </div>

      <!-- 右侧按钮组 - 右对齐 -->
      <div class="toolbar-right">
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
    'save',
    'clear',
    'download',
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

    const handleSave = () => {
      emit('save')
    }

    const handleClear = () => {
      emit('clear')
    }

    const handleDownload = () => {
      emit('download')
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
      handleSave,
      handleClear,
      handleDownload,
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
.canvas-size-group,
.history-group,
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
.size-btn,
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

.zoom-btn:hover,
.size-btn:hover,
.history-btn:hover,
.file-btn:hover,
.action-btn:hover {
  background: #444;
  color: white;
}

.size-btn.active,
.history-btn.active {
  background: #007bff;
  color: white;
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

.file-btn.save {
  background: #6f42c1;
  color: white;
}

.file-btn.save:hover {
  background: #5a32a3;
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
  
  .canvas-size-group,
  .history-group,
  .file-group {
    gap: 2px;
    padding: 2px;
  }
  
  .size-btn,
  .history-btn,
  .file-btn,
  .action-btn {
    width: 28px;
    height: 28px;
  }
}

</style>
