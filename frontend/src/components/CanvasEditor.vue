<template>
  <div class="canvas-editor">
    <!-- 顶部工具栏 - 扩图模式下隐藏 -->
    <CanvasTopToolbar
      v-if="currentMode !== 'outpainting'"
      :can-undo="currentHistoryIndex > 0"
      :can-redo="currentHistoryIndex < historyRecords.length - 1"
      :current-canvas-size="currentCanvasSize"
      :current-zoom-level="currentZoomLevel"
      :show-history="showHistory"
      @canvas-size-change="handleCanvasSizeChange"
      @zoom-in="handleZoomIn"
      @zoom-out="handleZoomOut"
      @zoom-fit="handleZoomFit"
      @zoom-100="handleZoom100"
      @toggle-history="handleToggleHistory"
      @undo="handleUndo"
      @redo="handleRedo"
      @upload="handleFileUpload"
      @save="handleSaveImage"
      @clear="handleClearCanvas"
      @download="handleDownloadImage"
    />
    
    <!-- 功能工具栏 - 只在主画布被选中且非局部重绘模式时显示功能选择按钮 -->
    <CanvasToolbar 
      v-if="currentMode === '' && isMainCanvasSelected"
      :is-processing="isProcessing"
      :current-mode="currentMode"
      @mode-change="handleModeChange"
      @drawing-tool-change="handleDrawingToolChange"
      @brush-size-change="handleBrushSizeChange"
      @clear-canvas="handleClearCanvas"
    />
    
    <!-- 局部重绘工具栏 - 在局部重绘模式下显示工具按钮 -->
    <CanvasToolbar 
      v-if="currentMode === 'inpainting'"
      :is-processing="isProcessing"
      :current-mode="currentMode"
      :show-function-buttons="false"
      @mode-change="handleModeChange"
      @drawing-tool-change="handleDrawingToolChange"
      @brush-size-change="handleBrushSizeChange"
      @clear-canvas="handleClearCanvas"
    />
    
    <!-- 主内容区域 -->
    <div class="main-content" :class="{ 'full-width': isInpaintingMode || currentMode === 'outpainting' || !showHistory }" @click="handleMainContentClick">
      <!-- 主画板 -->
      <MainCanvas
        v-if="currentMode === ''"
        ref="mainCanvasRef"
        :image-file="currentImageFile"
        :image-data="currentImageData"
        :is-selected="isMainCanvasSelected"
        :zoom-level="currentZoomLevel"
        @image-loaded="handleImageLoaded"
        @image-cleared="handleImageCleared"
        @canvas-selected="handleMainCanvasSelected"
        @canvas-deselected="handleMainCanvasDeselected"
        @zoom-changed="handleZoomChanged"
      />
      
      <!-- 局部重绘画板 -->
      <InpaintingCanvas
        v-show="currentMode === 'inpainting'"
        ref="inpaintingCanvasRef"
        :original-image="currentImageData"
        :original-image-file="currentImageFile"
        :prompt="parameters.prompt"
        :brush-size="brushSize"
        :current-tool="currentDrawingTool"
        :zoom-level="currentZoomLevel"
        @inpainting-complete="handleInpaintingComplete"
        @processing-start="handleProcessingStart"
        @processing-end="handleProcessingEnd"
        @zoom-changed="handleZoomChanged"
      />
      
      <!-- 扩图画板 -->
      <OutpaintingCanvas
        v-show="currentMode === 'outpainting'"
        ref="outpaintingCanvasRef"
        :original-image="currentImageData"
        :original-image-file="currentImageFile"
        :prompt="parameters.prompt"
        :zoom-level="currentZoomLevel"
        @outpainting-complete="handleOutpaintingComplete"
        @processing-start="handleProcessingStart"
        @processing-end="handleProcessingEnd"
        @zoom-changed="handleZoomChanged"
        @file-upload="handleFileUpload"
        @exit-outpainting="handleExitOutpainting"
      />
      
      <!-- 调试信息 -->
      <div v-if="currentMode !== '' && currentMode !== 'inpainting' && currentMode !== 'outpainting'" class="debug-mode">
        <p>未知模式: {{ currentMode }}</p>
      </div>
      
      <!-- 参数面板 -->
      <CanvasParameterPanel
        v-if="currentMode === 'inpainting'"
        v-model:prompt="parameters.prompt"
        @execute="handleExecuteInpainting"
      />
      
      <!-- 扩图参数面板 -->
      <OutpaintingParameterPanel
        v-if="currentMode === 'outpainting'"
        v-model:prompt="parameters.prompt"
        @execute="handleExecuteOutpainting"
      />
      
      <!-- 隐藏的执行按钮，用于触发局部重绘 -->
      <button 
        v-show="false"
        ref="executeButtonRef"
        @click="triggerInpaintingExecution"
      ></button>
    </div>
    
    <!-- 历史面板 - 通过顶部工具栏的历史按钮控制显示 -->
    <CanvasHistoryPanel
      v-if="!isInpaintingMode && currentMode !== 'outpainting' && showHistory"
      v-model="historyRecords"
      v-model:current-index="currentHistoryIndex"
      @switch-history="handleSwitchHistory"
      @undo="handleUndo"
      @redo="handleRedo"
    />
  </div>
</template>

<script>
import { ref, reactive, onMounted, onUnmounted, nextTick } from 'vue'
import CanvasTopToolbar from './CanvasTopToolbar.vue'
import CanvasToolbar from './CanvasToolbar.vue'
import CanvasParameterPanel from './CanvasParameterPanel.vue'
import OutpaintingParameterPanel from './OutpaintingParameterPanel.vue'
import CanvasHistoryPanel from './CanvasHistoryPanel.vue'
import MainCanvas from './MainCanvas.vue'
import InpaintingCanvas from './InpaintingCanvas.vue'
import OutpaintingCanvas from './OutpaintingCanvas.vue'

export default {
  name: 'CanvasEditor',
  components: {
    CanvasTopToolbar,
    CanvasToolbar,
    CanvasParameterPanel,
    OutpaintingParameterPanel,
    CanvasHistoryPanel,
    MainCanvas,
    InpaintingCanvas,
    OutpaintingCanvas
  },
  setup() {
    // 响应式数据
    const currentMode = ref('')
    const isInpaintingMode = ref(false)
    const currentDrawingTool = ref('brush')
    const brushSize = ref(20)
    const isProcessing = ref(false)
    const processingMessage = ref('')
    const currentImageFile = ref(null)
    const currentImageData = ref(null)
    const currentCanvasSize = ref('fit')
    const isMainCanvasSelected = ref(false)
    const currentZoomLevel = ref(1)
    const mainCanvasRef = ref(null)
    const inpaintingCanvasRef = ref(null)
    const outpaintingCanvasRef = ref(null)
    const showHistory = ref(false)
    
    // 参数配置
    const parameters = reactive({
      prompt: ''
    })
    
    // 历史管理
    const historyRecords = ref([])
    const currentHistoryIndex = ref(-1)
    const originalImageUrl = ref(null)
    
    // 持久化存储键名
    const STORAGE_KEYS = {
      CANVAS_STATE: 'canvas_editor_state',
      HISTORY_RECORDS: 'canvas_history_records',
      CURRENT_INDEX: 'canvas_current_index',
      ORIGINAL_IMAGE: 'canvas_original_image',
      PARAMETERS: 'canvas_parameters'
    }
    
    // 处理模式变化
    const handleModeChange = (mode) => {
      console.log('🔄 收到模式切换请求:', mode, '当前模式:', currentMode.value)
      console.log('📋 当前图像状态:', {
        currentImageFile: currentImageFile.value?.name,
        currentImageData: !!currentImageData.value,
        originalImageUrl: !!originalImageUrl.value
      })
      
      currentMode.value = mode
      isInpaintingMode.value = mode === 'inpainting'
      
      // 进入局部重绘模式时，InpaintingCanvas会自动适应画布显示全图
      // 进入扩图模式时，OutpaintingCanvas会自动适应画布显示全图
      
      console.log('✅ 模式已切换到:', mode, '局部重绘模式:', isInpaintingMode.value)
    }
    
    // 退出扩图模式
    const exitOutpaintingMode = () => {
      console.log('退出扩图模式')
      currentMode.value = ''
      isInpaintingMode.value = false
    }
    
    // 处理绘制工具变化
    const handleDrawingToolChange = (tool) => {
      currentDrawingTool.value = tool
      console.log('绘制工具切换到:', tool)
    }
    
    // 处理画笔大小变化
    const handleBrushSizeChange = (size) => {
      brushSize.value = size
      console.log('画笔大小设置为:', size)
    }
    
    // 处理清除画布
    const handleClearCanvas = () => {
      console.log('清除画布')
    }
    
    // 处理文件上传事件
    const handleFileUpload = (file) => {
      console.log('File uploaded:', file)
      currentImageFile.value = file
    }
    
    // 处理图像加载完成
    const handleImageLoaded = (imageData) => {
      console.log('Image loaded:', imageData)
      currentImageData.value = imageData
      originalImageUrl.value = imageData.imageUrl
    }
    
    // 处理图像清除
    const handleImageCleared = () => {
      console.log('Image cleared')
      currentImageData.value = null
      currentImageFile.value = null
      originalImageUrl.value = null
    }
    
    // 处理局部重绘完成
    const handleInpaintingComplete = (result) => {
      console.log('Inpainting complete:', result)
      
      // 添加到历史记录
      const historyRecord = {
        id: Date.now().toString(),
        timestamp: Date.now(),
        prompt: parameters.prompt,
        originalImageUrl: originalImageUrl.value,
        maskDataUrl: result.maskDataUrl,
        resultImageUrl: result.resultImageUrl,
        parameters: { ...parameters }
      }
      
      addToHistory(historyRecord)
    }
    
    // 处理扩图完成
    const handleOutpaintingComplete = (result) => {
      console.log('Outpainting complete:', result)
      
      // 检查是否是退出扩图模式
      if (result.action === 'exit') {
        console.log('退出扩图模式')
        exitOutpaintingMode()
        return
      }
      
      // 添加到历史记录
      const historyRecord = {
        id: Date.now().toString(),
        timestamp: Date.now(),
        prompt: parameters.prompt,
        originalImageUrl: originalImageUrl.value,
        resultImageUrl: result.resultImageUrl,
        parameters: result.parameters,
        type: 'outpainting'
      }
      
      addToHistory(historyRecord)
    }
    
    // 处理退出扩图模式
    const handleExitOutpainting = () => {
      console.log('收到退出扩图模式请求')
      exitOutpaintingMode()
    }
    
    // 处理处理开始
    const handleProcessingStart = () => {
      isProcessing.value = true
      // 根据当前模式设置不同的处理消息
      if (currentMode.value === 'inpainting') {
        processingMessage.value = '正在执行局部重绘...'
      } else if (currentMode.value === 'outpainting') {
        processingMessage.value = '正在执行扩图...'
      } else {
        processingMessage.value = '正在处理...'
      }
    }
    
    // 处理处理结束
    const handleProcessingEnd = () => {
      isProcessing.value = false
      processingMessage.value = ''
    }
    
    // 处理保存图像事件
    const handleSaveImage = () => {
      console.log('保存图像')
    }
    
    // 处理执行局部重绘
    const handleExecuteInpainting = async () => {
      console.log('执行局部重绘')
      console.log('当前模式:', currentMode.value)
      
      if (currentMode.value !== 'inpainting') {
        console.error('当前不在局部重绘模式')
        return
      }
      
      // 使用事件通信触发执行
      console.log('通过事件触发局部重绘执行')
      window.dispatchEvent(new CustomEvent('execute-inpainting'))
    }
    
    // 处理执行扩图
    const handleExecuteOutpainting = async () => {
      console.log('执行扩图')
      console.log('当前模式:', currentMode.value)
      
      if (currentMode.value !== 'outpainting') {
        console.error('当前不在扩图模式')
        return
      }
      
      // 使用事件通信触发执行
      console.log('通过事件触发扩图执行')
      window.dispatchEvent(new CustomEvent('execute-outpainting'))
    }
    
    // 触发局部重绘执行（备用方法）
    const triggerInpaintingExecution = () => {
      console.log('通过按钮触发局部重绘执行')
      window.dispatchEvent(new CustomEvent('execute-inpainting'))
    }
    
    // 触发扩图执行（备用方法）
    const triggerOutpaintingExecution = () => {
      console.log('通过按钮触发扩图执行')
      window.dispatchEvent(new CustomEvent('execute-outpainting'))
    }
    
    // 历史管理方法
    const addToHistory = (record) => {
      historyRecords.value = historyRecords.value.slice(0, currentHistoryIndex.value + 1)
      historyRecords.value.push(record)
      currentHistoryIndex.value = historyRecords.value.length - 1
      console.log('历史记录已添加:', record)
    }
    
    const handleSwitchHistory = (record) => {
      console.log('🔄 切换到历史记录:', record)
    }
    
    const handleUndo = () => {
      console.log('↶ 撤销操作')
      if (currentHistoryIndex.value > 0) {
        currentHistoryIndex.value--
      }
    }
    
    const handleRedo = () => {
      console.log('↷ 重做操作')
      if (currentHistoryIndex.value < historyRecords.value.length - 1) {
        currentHistoryIndex.value++
      }
    }
    
    // 持久化功能
    const saveCanvasState = () => {
      try {
        localStorage.setItem(STORAGE_KEYS.HISTORY_RECORDS, JSON.stringify(historyRecords.value))
        localStorage.setItem(STORAGE_KEYS.CURRENT_INDEX, currentHistoryIndex.value.toString())
        if (originalImageUrl.value) {
          localStorage.setItem(STORAGE_KEYS.ORIGINAL_IMAGE, originalImageUrl.value)
        }
        localStorage.setItem(STORAGE_KEYS.PARAMETERS, JSON.stringify(parameters))
        console.log('✅ 画布状态已保存到localStorage')
      } catch (error) {
        console.error('❌ 保存画布状态失败:', error)
      }
    }
    
    const loadCanvasState = async () => {
      try {
        const historyStr = localStorage.getItem(STORAGE_KEYS.HISTORY_RECORDS)
        if (historyStr) {
          historyRecords.value = JSON.parse(historyStr)
        }
        
        const indexStr = localStorage.getItem(STORAGE_KEYS.CURRENT_INDEX)
        if (indexStr) {
          currentHistoryIndex.value = parseInt(indexStr)
        }
        
        const originalImageStr = localStorage.getItem(STORAGE_KEYS.ORIGINAL_IMAGE)
        if (originalImageStr) {
          originalImageUrl.value = originalImageStr
        }
        
        const paramsStr = localStorage.getItem(STORAGE_KEYS.PARAMETERS)
        if (paramsStr) {
          const savedParams = JSON.parse(paramsStr)
          Object.assign(parameters, savedParams)
        }
        
        console.log('✅ 所有状态已从localStorage恢复')
      } catch (error) {
        console.error('❌ 加载画布状态失败:', error)
      }
    }
    
    const clearSavedState = () => {
      try {
        Object.values(STORAGE_KEYS).forEach(key => {
          localStorage.removeItem(key)
        })
        console.log('✅ 已清除所有保存的状态')
      } catch (error) {
        console.error('❌ 清除保存状态失败:', error)
      }
    }
    
    // 自动保存功能
    let autoSaveTimer = null
    const startAutoSave = () => {
      autoSaveTimer = setInterval(() => {
        if (historyRecords.value.length > 0) {
          saveCanvasState()
        }
      }, 30000)
    }
    
    const stopAutoSave = () => {
      if (autoSaveTimer) {
        clearInterval(autoSaveTimer)
        autoSaveTimer = null
      }
    }
    
    // 处理手动保存状态
    const handleSaveState = () => {
      saveCanvasState()
      alert('状态已保存！')
    }
    
    // 处理清除状态
    const handleClearState = () => {
      clearSavedState()
      historyRecords.value = []
      currentHistoryIndex.value = -1
      originalImageUrl.value = null
      parameters.prompt = ''
      currentImageData.value = null
      currentImageFile.value = null
      alert('所有状态已清除！')
    }
    
    // 处理画布尺寸变化
    const handleCanvasSizeChange = (size) => {
      currentCanvasSize.value = size
      console.log('画布尺寸设置为:', size)
      // TODO: 实现画布尺寸调整逻辑
    }
    
    // 处理缩放操作
    const handleZoomIn = () => {
      console.log('🔍 CanvasEditor: 放大画布')
      if (mainCanvasRef.value) {
        mainCanvasRef.value.zoomIn()
      }
      if (inpaintingCanvasRef.value) {
        inpaintingCanvasRef.value.zoomIn()
      }
      if (outpaintingCanvasRef.value) {
        outpaintingCanvasRef.value.zoomIn()
      }
    }
    
    const handleZoomOut = () => {
      console.log('🔍 CanvasEditor: 缩小画布')
      if (mainCanvasRef.value) {
        mainCanvasRef.value.zoomOut()
      }
      if (inpaintingCanvasRef.value) {
        inpaintingCanvasRef.value.zoomOut()
      }
      if (outpaintingCanvasRef.value) {
        outpaintingCanvasRef.value.zoomOut()
      }
    }
    
    const handleZoomFit = () => {
      console.log('🔍 CanvasEditor: 适应画布')
      if (mainCanvasRef.value) {
        mainCanvasRef.value.zoomFit()
      }
      if (inpaintingCanvasRef.value) {
        inpaintingCanvasRef.value.zoomFit()
      }
      if (outpaintingCanvasRef.value) {
        outpaintingCanvasRef.value.resetZoom()
      }
    }
    
    const handleZoom100 = () => {
      console.log('🔍 CanvasEditor: 100%缩放')
      if (mainCanvasRef.value) {
        mainCanvasRef.value.zoom100()
      }
      if (inpaintingCanvasRef.value) {
        inpaintingCanvasRef.value.zoom100()
      }
      if (outpaintingCanvasRef.value) {
        outpaintingCanvasRef.value.resetZoom()
      }
    }
    
    // 处理缩放变化
    const handleZoomChanged = (zoomLevel) => {
      currentZoomLevel.value = zoomLevel
      console.log('缩放级别变化:', zoomLevel)
    }
    
    // 处理下载图像
    const handleDownloadImage = () => {
      if (currentImageData.value && currentImageData.value.imageUrl) {
        const link = document.createElement('a')
        link.href = currentImageData.value.imageUrl
        link.download = `canvas-image-${Date.now()}.png`
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        console.log('图像已下载')
      } else {
        alert('没有可下载的图像')
      }
    }
    
    // 处理主画布选择
    const handleMainCanvasSelected = () => {
      isMainCanvasSelected.value = true
      console.log('主画布已选中')
    }
    
    // 处理主画布取消选择
    const handleMainCanvasDeselected = () => {
      isMainCanvasSelected.value = false
      console.log('主画布已取消选择')
    }
    
    // 处理历史窗口切换
    const handleToggleHistory = () => {
      showHistory.value = !showHistory.value
    }
    
    // 处理主内容区域点击
    const handleMainContentClick = (e) => {
      // 如果点击的是主内容区域的空白部分，取消选择
      if (e.target.classList.contains('main-content')) {
        isMainCanvasSelected.value = false
        console.log('点击主内容区域空白部分，取消图像选择')
      }
    }
    
    // 生命周期
    onMounted(async () => {
      console.log('📋 CanvasEditor 组件挂载，初始状态:')
      console.log('  - currentMode:', currentMode.value)
      console.log('  - isInpaintingMode:', isInpaintingMode.value)
      
      startAutoSave()
      await loadCanvasState()
      
      console.log('📋 状态加载完成后:')
      console.log('  - currentMode:', currentMode.value)
      console.log('  - isInpaintingMode:', isInpaintingMode.value)
    })
    
    onUnmounted(() => {
      stopAutoSave()
      saveCanvasState()
    })
    
    return {
      // 响应式数据
      currentMode,
      isInpaintingMode,
      currentDrawingTool,
      brushSize,
      isProcessing,
      processingMessage,
      parameters,
      currentImageFile,
      currentImageData,
      currentCanvasSize,
      isMainCanvasSelected,
      currentZoomLevel,
      mainCanvasRef,
      
      // 历史管理
      historyRecords,
      currentHistoryIndex,
      
      // 方法
      handleModeChange,
      handleDrawingToolChange,
      handleBrushSizeChange,
      handleClearCanvas,
      handleFileUpload,
      handleImageLoaded,
      handleImageCleared,
      handleInpaintingComplete,
      handleOutpaintingComplete,
      handleExitOutpainting,
      handleProcessingStart,
      handleProcessingEnd,
      handleSaveImage,
      handleExecuteInpainting,
      handleExecuteOutpainting,
      exitOutpaintingMode,
      handleSwitchHistory,
      handleUndo,
      handleRedo,
      handleSaveState,
      handleClearState,
      handleCanvasSizeChange,
      handleZoomIn,
      handleZoomOut,
      handleZoomFit,
      handleZoom100,
      handleZoomChanged,
      handleDownloadImage,
      handleMainCanvasSelected,
      handleMainCanvasDeselected,
      handleMainContentClick,
      showHistory,
      handleToggleHistory
    }
  }
}
</script>

<style scoped>
.canvas-editor {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #0f0f0f;
  color: white;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  margin-right: 320px;
  transition: margin-right 0.3s ease;
}

.main-content.full-width {
  margin-right: 0;
}

.debug-mode {
  padding: 20px;
  background: #ff4444;
  color: white;
  text-align: center;
  font-weight: bold;
}
</style>
