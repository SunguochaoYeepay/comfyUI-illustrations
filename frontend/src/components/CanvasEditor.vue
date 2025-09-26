<template>
  <div class="canvas-editor">
    <!-- 顶部工具栏 - 扩图和局部重绘模式下完全隐藏 -->
    <CanvasTopToolbar
      v-if="currentMode !== 'outpainting' && currentMode !== 'inpainting'"
      :can-undo="currentHistoryIndex > 0"
      :can-redo="currentHistoryIndex < historyRecords.length - 1"
      :current-canvas-size="currentCanvasSize"
      :current-zoom-level="currentZoomLevel"
      :show-history="showHistory"
      :show-left-controls="true"
      :current-mode="currentMode"
      @canvas-size-change="handleCanvasSizeChange"
      @zoom-in="handleZoomIn"
      @zoom-out="handleZoomOut"
      @zoom-fit="handleZoomFit"
      @zoom-100="handleZoom100"
      @toggle-history="handleToggleHistory"
      @undo="handleUndo"
      @redo="handleRedo"
      @upload="handleFileUpload"
      @clear="handleClearCanvas"
      @download="handleDownloadImage"
      @mode-change="handleModeChange"
    />
    
    
    <!-- 局部重绘工具栏已集成到顶部工具栏中 -->
    
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
        :canvas-size="currentCanvasSize"
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
        @exit-inpainting="handleExitInpainting"
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
    
    
    
    <!-- 漂浮的参数面板 -->
    <CanvasParameterPanel
      v-if="currentMode === 'inpainting'"
      v-model:prompt="parameters.prompt"
      @execute="handleExecuteInpainting"
      class="floating-parameter-panel"
    />
    
    <!-- 漂浮的扩图参数面板 -->
    <OutpaintingParameterPanel
      v-if="currentMode === 'outpainting'"
      v-model:prompt="parameters.prompt"
      @execute="handleExecuteOutpainting"
      class="floating-parameter-panel"
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
  props: {
    initialImageData: {
      type: Object,
      default: null
    },
    initialMode: {
      type: String,
      default: ''
    }
  },
  setup(props) {
    // 响应式数据
    const currentMode = ref('')
    const isInpaintingMode = ref(false)
    const currentDrawingTool = ref('brush')
    const brushSize = ref(50)
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
    
    // 处理退出局部重绘模式
    const handleExitInpainting = () => {
      console.log('收到退出局部重绘模式请求')
      currentMode.value = ''
      isInpaintingMode.value = false
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
        // 限制历史记录数量，避免存储空间超限
        const maxHistoryRecords = 10
        let recordsToSave = historyRecords.value
        
        if (recordsToSave.length > maxHistoryRecords) {
          // 保留最新的记录，删除最旧的
          recordsToSave = recordsToSave.slice(-maxHistoryRecords)
          console.log(`📝 历史记录过多，已清理为最新 ${maxHistoryRecords} 条`)
        }
        
        // 压缩历史记录数据，移除不必要的字段
        const compressedRecords = recordsToSave.map(record => ({
          id: record.id,
          timestamp: record.timestamp,
          mode: record.mode,
          prompt: record.prompt,
          // 移除大的图片数据，只保留必要信息
          imageInfo: record.imageData ? {
            filename: record.imageData.filename,
            task_id: record.imageData.task_id
          } : null
        }))
        
        localStorage.setItem(STORAGE_KEYS.HISTORY_RECORDS, JSON.stringify(compressedRecords))
        localStorage.setItem(STORAGE_KEYS.CURRENT_INDEX, currentHistoryIndex.value.toString())
        if (originalImageUrl.value) {
          localStorage.setItem(STORAGE_KEYS.ORIGINAL_IMAGE, originalImageUrl.value)
        }
        localStorage.setItem(STORAGE_KEYS.PARAMETERS, JSON.stringify(parameters))
        console.log('✅ 画布状态已保存到localStorage')
      } catch (error) {
        console.error('❌ 保存画布状态失败:', error)
        // 如果存储失败，尝试清理所有画布相关数据
        if (error.name === 'QuotaExceededError') {
          console.log('🧹 存储空间不足，清理画布历史数据')
          try {
            localStorage.removeItem(STORAGE_KEYS.HISTORY_RECORDS)
            localStorage.removeItem(STORAGE_KEYS.CURRENT_INDEX)
            localStorage.removeItem(STORAGE_KEYS.ORIGINAL_IMAGE)
            localStorage.removeItem(STORAGE_KEYS.PARAMETERS)
            console.log('✅ 已清理画布历史数据')
          } catch (cleanError) {
            console.error('❌ 清理数据也失败:', cleanError)
          }
        }
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
      }, 60000) // 改为60秒保存一次，减少存储压力
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
        // OutpaintingCanvas 没有缩放功能，跳过
        console.log('🔍 OutpaintingCanvas 跳过缩放操作')
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
        // OutpaintingCanvas 没有缩放功能，跳过
        console.log('🔍 OutpaintingCanvas 跳过缩放操作')
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
      console.log('🔄 历史窗口切换:', {
        showHistory: showHistory.value,
        isInpaintingMode: isInpaintingMode.value,
        currentMode: currentMode.value,
        shouldShow: !isInpaintingMode.value && currentMode.value !== 'outpainting' && showHistory.value
      })
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
      console.log('  - initialImageData:', props.initialImageData)
      console.log('  - initialMode:', props.initialMode)
      
      startAutoSave()
      await loadCanvasState()
      
      // 如果有初始数据，设置图片和模式
      if (props.initialImageData) {
        console.log('🎨 设置初始图片数据:', props.initialImageData)
        currentImageData.value = props.initialImageData
        // 如果有图片URL，创建图片对象
        if (props.initialImageData.url) {
          const img = new Image()
          img.crossOrigin = 'anonymous'
          img.onload = () => {
            console.log('✅ 初始图片加载完成')
            // 图片加载完成后，如果指定了模式，切换到对应模式
            if (props.initialMode) {
              console.log('🎨 切换到初始模式:', props.initialMode)
              currentMode.value = props.initialMode
              if (props.initialMode === 'inpainting') {
                isInpaintingMode.value = true
              }
            }
          }
          img.src = props.initialImageData.url
        }
      } else if (props.initialMode) {
        // 即使没有图片数据，也要设置模式
        console.log('🎨 设置初始模式:', props.initialMode)
        currentMode.value = props.initialMode
        if (props.initialMode === 'inpainting') {
          isInpaintingMode.value = true
        }
      }
      
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
      handleExitInpainting,
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
  /* 历史抽屉是漂浮的，不需要右边距 */
  margin-right: 0;
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

/* 漂浮的参数面板样式 */
.floating-parameter-panel {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 1000;
  background: rgba(42, 42, 42, 0.95);
  border: 1px solid #555;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(10px);
  max-width: 90vw;
  min-width: 400px;
}
</style>
