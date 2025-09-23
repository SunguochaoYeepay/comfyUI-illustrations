<template>
  <div class="canvas-toolbar">
    <!-- 主工具栏 -->
    <div v-if="!isInpaintingMode" class="main-toolbar">
      <div class="toolbar-buttons">
        <button 
          class="action-btn inpainting" 
          @click="enterInpaintingMode"
          :class="{ active: currentMode === 'inpainting' }"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
          </svg>
          <span>局部重绘</span>
        </button>
        <button 
          class="action-btn outpainting" 
          @click="selectMode('outpainting')"
          :class="{ active: currentMode === 'outpainting' }"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
          </svg>
          <span>扩图</span>
        </button>
        <button 
          class="action-btn detail" 
          @click="selectMode('detail')"
          :class="{ active: currentMode === 'detail' }"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M12,4A8,8 0 0,1 20,12A8,8 0 0,1 12,20A8,8 0 0,1 4,12A8,8 0 0,1 12,4M12,6A6,6 0 0,0 6,12A6,6 0 0,0 12,18A6,6 0 0,0 18,12A6,6 0 0,0 12,6M12,8A4,4 0 0,1 16,12A4,4 0 0,1 12,16A4,4 0 0,1 8,12A4,4 0 0,1 12,8Z"/>
          </svg>
          <span>细节修复</span>
        </button>
        <button 
          class="action-btn hd" 
          @click="selectMode('hd')"
          :class="{ active: currentMode === 'hd' }"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <path d="M4,6H20V16H4M20,18A2,2 0 0,0 22,16V6C22,4.89 21.1,4 20,4H4C2.89,4 2,4.89 2,6V16A2,2 0 0,0 4,18H0V20H24V18H20Z"/>
          </svg>
          <span>HD超清</span>
        </button>
        <button 
          class="action-btn cutout" 
          @click="selectMode('cutout')"
          :class="{ active: currentMode === 'cutout' }"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <path d="M19,3H5C3.89,3 3,3.89 3,5V19A2,2 0 0,0 5,21H19A2,2 0 0,0 21,19V5C21,3.89 20.1,3 19,3M19,5V19H5V5H19Z"/>
          </svg>
          <span>抠图</span>
        </button>
        
        <button class="file-btn upload" @click="handleUpload">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z"/>
          </svg>
          <span>上传</span>
        </button>
        <button class="file-btn save" @click="handleSave">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <path d="M15,9H5V5H15M12,19A3,3 0 0,1 9,16A3,3 0 0,1 12,13A3,3 0 0,1 15,16A3,3 0 0,1 12,19M17,3H5C3.89,3 3,3.9 3,5V19A2,2 0 0,0 5,21H19A2,2 0 0,0 21,19V7L17,3Z"/>
          </svg>
          <span>保存</span>
        </button>
      </div>
    </div>

    <!-- 局部重绘模式工具栏 -->
    <div v-if="isInpaintingMode" class="inpainting-toolbar">
      <div class="toolbar-buttons">
        <button 
          class="tool-btn brush" 
          @click="selectDrawingTool('brush')"
          :class="{ active: currentDrawingTool === 'brush' }"
          title="画笔"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
            <path d="M20.71,4.63L19.37,3.29C19,2.9 18.35,2.9 17.96,3.29L9,12.25L11.75,15L20.71,6.04C21.1,5.65 21.1,5 20.71,4.63M7,14A3,3 0 0,0 4,17C4,18.31 2.84,19 2,19C2.92,20.22 4.5,21 6,21A4,4 0 0,0 10,17A3,3 0 0,0 7,14Z"/>
          </svg>
        </button>
        <button 
          class="tool-btn eraser" 
          @click="selectDrawingTool('eraser')"
          :class="{ active: currentDrawingTool === 'eraser' }"
          title="橡皮擦"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
            <path d="M16.24,3.56L21.19,8.5C21.97,9.29 21.97,10.55 21.19,11.34L12,20.53C10.44,22.09 7.91,22.09 6.34,20.53L2.81,17C2.03,16.21 2.03,14.95 2.81,14.16L13.41,3.56C14.2,2.78 15.46,2.78 16.24,3.56M4.22,15.58L7.76,19.11C8.54,19.9 9.8,19.9 10.59,19.11L14.12,15.58L9.17,10.63L4.22,15.58Z"/>
          </svg>
        </button>

        <div class="brush-size-control">
          <input
            v-model.number="brushSize"
            type="range"
            min="5"
            max="100"
            step="5"
            class="brush-size-slider"
            @input="updateBrushSize"
          />
          <div class="brush-size-display">
            <div class="brush-preview" :style="{ width: brushSize + 'px', height: brushSize + 'px' }"></div>
            <span class="size-text">{{ brushSize }}px</span>
          </div>
        </div>

        <button class="reset-btn" @click="clearCanvas" title="清除画布绘制内容">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
            <path d="M19,4H15.5L14.5,3H9.5L8.5,4H5V6H19M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z"/>
          </svg>
        </button>
        <button class="close-btn" @click="exitInpaintingMode" title="关闭局部重绘">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
            <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
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
  name: 'CanvasToolbar',
  props: {
    isProcessing: {
      type: Boolean,
      default: false
    }
  },
  emits: [
    'mode-change',
    'drawing-tool-change',
    'brush-size-change',
    'clear-canvas',
    'file-upload',
    'save-image'
  ],
  setup(props, { emit }) {
    const fileInput = ref(null)
    const isInpaintingMode = ref(false)
    const currentMode = ref('')
    const currentDrawingTool = ref('brush')
    const brushSize = ref(20)
    
    // 进入局部重绘模式
    const enterInpaintingMode = () => {
      isInpaintingMode.value = true
      currentMode.value = 'inpainting'
      currentDrawingTool.value = 'brush'
      emit('mode-change', 'inpainting')
    }
    
    // 退出局部重绘模式
    const exitInpaintingMode = () => {
      isInpaintingMode.value = false
      currentMode.value = ''
      emit('mode-change', '')
    }
    
    // 选择其他模式
    const selectMode = (mode) => {
      currentMode.value = mode
      emit('mode-change', mode)
    }
    
    // 选择绘制工具
    const selectDrawingTool = (tool) => {
      currentDrawingTool.value = tool
      emit('drawing-tool-change', tool)
    }
    
    // 更新画笔大小
    const updateBrushSize = () => {
      emit('brush-size-change', brushSize.value)
    }
    
    // 清除画布绘制内容
    const clearCanvas = () => {
      emit('clear-canvas')
    }
    
    // 文件上传
    const handleUpload = () => {
      fileInput.value?.click()
    }
    
    const handleFileSelect = (event) => {
      const file = event.target.files[0]
      if (file) {
        emit('file-upload', file)
      }
      // 清空input值，允许重复选择同一文件
      event.target.value = ''
    }
    
    const handleSave = () => {
      emit('save-image')
    }
    
    return {
      fileInput,
      isInpaintingMode,
      currentMode,
      currentDrawingTool,
      brushSize,
      enterInpaintingMode,
      exitInpaintingMode,
      selectMode,
      selectDrawingTool,
      updateBrushSize,
      clearCanvas,
      handleUpload,
      handleFileSelect,
      handleSave
    }
  }
}
</script>

<style scoped>
.canvas-toolbar {
  display: flex;
  justify-content: center;
  padding: 10px 15px;
  background: #2a2a2a;
  border-bottom: 1px solid #333;
  flex-shrink: 0;
}

.main-toolbar,
.inpainting-toolbar {
  display: flex;
  justify-content: center;
  width: 100%;
}

.toolbar-buttons {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
}

.action-btn,
.file-btn,
.tool-btn,
.close-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 8px 12px;
  border: 1px solid #444;
  border-radius: 6px;
  background: #333;
  color: #ccc;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 11px;
  font-weight: 500;
  min-width: 60px;
}

/* 局部重绘工具栏按钮 - 只显示图标 */
.inpainting-toolbar .tool-btn,
.inpainting-toolbar .reset-btn,
.inpainting-toolbar .close-btn {
  flex-direction: row;
  padding: 10px;
  min-width: 40px;
  width: 40px;
  height: 40px;
}

.action-btn:hover,
.file-btn:hover,
.tool-btn:hover,
.close-btn:hover {
  background: #444;
  border-color: #555;
  color: white;
}

.action-btn.active {
  background: #007bff;
  border-color: #007bff;
  color: white;
}

.action-btn.inpainting {
  background: #28a745;
  border-color: #28a745;
  color: white;
}

.action-btn.inpainting:hover {
  background: #218838;
  border-color: #1e7e34;
}

.action-btn.outpainting {
  background: #17a2b8;
  border-color: #17a2b8;
  color: white;
}

.action-btn.outpainting:hover {
  background: #138496;
  border-color: #117a8b;
}

.action-btn.detail {
  background: #6f42c1;
  border-color: #6f42c1;
  color: white;
}

.action-btn.detail:hover {
  background: #5a32a3;
  border-color: #4c2d85;
}

.action-btn.hd {
  background: #fd7e14;
  border-color: #fd7e14;
  color: white;
}

.action-btn.hd:hover {
  background: #e8650e;
  border-color: #d55a0c;
}

.action-btn.cutout {
  background: #20c997;
  border-color: #20c997;
  color: white;
}

.action-btn.cutout:hover {
  background: #1aa179;
  border-color: #179b73;
}

.tool-btn.active {
  background: #007bff;
  border-color: #007bff;
  color: white;
}

.reset-btn {
  background: #6c757d;
  border-color: #6c757d;
  color: white;
}

.reset-btn:hover {
  background: #5a6268;
  border-color: #545b62;
}

.close-btn {
  background: #dc3545;
  border-color: #dc3545;
  color: white;
}

.close-btn:hover {
  background: #c82333;
  border-color: #bd2130;
}

.brush-size-control {
  display: flex;
  flex-direction: row;
  gap: 8px;
  align-items: center;
  padding: 8px 12px;
  border: 1px solid #444;
  border-radius: 6px;
  background: #333;
  min-width: 100px;
  height: 40px;
}

.brush-size-slider {
  width: 50px;
  height: 6px;
  border-radius: 3px;
  background: #444;
  outline: none;
  -webkit-appearance: none;
  appearance: none;
}

.brush-size-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #007bff;
  cursor: pointer;
  border: 2px solid white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.brush-size-slider::-moz-range-thumb {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #007bff;
  cursor: pointer;
  border: 2px solid white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.brush-size-display {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 6px;
}

.brush-preview {
  border-radius: 50%;
  background: #007bff;
  border: 2px solid white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
  min-width: 12px;
  min-height: 12px;
  max-width: 20px;
  max-height: 20px;
}

.size-text {
  font-size: 10px;
  color: #888;
  font-weight: 500;
}

.action-btn svg,
.file-btn svg,
.tool-btn svg,
.close-btn svg {
  flex-shrink: 0;
}

.action-btn span,
.file-btn span,
.tool-btn span,
.close-btn span {
  white-space: nowrap;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .canvas-toolbar {
    padding: 10px;
    gap: 10px;
  }
  
  .main-toolbar,
  .inpainting-toolbar {
    gap: 10px;
  }
  
  .action-buttons,
  .file-buttons,
  .drawing-tools {
    gap: 6px;
  }
  
  .action-btn,
  .file-btn,
  .tool-btn,
  .close-btn {
    padding: 6px 8px;
    min-width: 50px;
    font-size: 10px;
  }
  
  .action-btn svg,
  .file-btn svg,
  .tool-btn svg,
  .close-btn svg {
    width: 14px;
    height: 14px;
  }
  
  .brush-size-slider {
    width: 100px;
  }
}
</style>