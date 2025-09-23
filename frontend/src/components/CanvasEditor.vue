<template>
  <div class="canvas-editor">
    <!-- 工具栏 -->
    <CanvasToolbar 
      :is-processing="isProcessing"
      @mode-change="handleModeChange"
      @drawing-tool-change="handleDrawingToolChange"
      @brush-size-change="handleBrushSizeChange"
      @clear-canvas="handleClearCanvas"
      @file-upload="handleFileUpload"
      @save-image="handleSaveImage"
      @save-state="handleSaveState"
      @clear-state="handleClearState"
    />
    
    <!-- 主内容区域 -->
    <div class="main-content" :class="{ 'full-width': isInpaintingMode || historyRecords.length === 0 }">
      <!-- 画布容器 -->
      <div class="canvas-container">
        <div class="canvas-wrapper">
          <canvas 
            ref="canvasElement" 
            class="main-canvas"
            @drop="handleDrop"
            @dragover="handleDragOver"
            @dragenter="handleDragEnter"
            @dragleave="handleDragLeave"
          ></canvas>
          
          <!-- 加载状态 -->
          <div v-if="isLoading" class="loading-overlay">
            <div class="loading-spinner"></div>
            <p>加载图像中...</p>
          </div>
          
          <!-- 处理状态 -->
          <div v-if="isProcessing" class="processing-overlay">
            <div class="processing-spinner"></div>
            <p>{{ processingMessage }}</p>
          </div>
          
          <!-- 调试信息 -->
          <div v-if="!currentImage" class="debug-info">
            <p>拖拽图像文件到此处，或点击工具栏的"上传"按钮</p>
            <p>支持格式：PNG, JPG, JPEG, GIF, WebP</p>
            <button @click="testImageLoad" class="test-btn">测试图像加载</button>
          </div>
        </div>
      </div>
      
      <!-- 参数面板 -->
      <CanvasParameterPanel
        v-model:prompt="parameters.prompt"
        @execute="handleExecuteInpainting"
      />
    </div>
    
    <!-- 历史面板 - 局部重绘模式下隐藏，且需要有历史记录 -->
    <CanvasHistoryPanel
      v-if="!isInpaintingMode && historyRecords.length > 0"
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
import * as fabric from 'fabric'
import { executeQwenEdit } from '../services/imageService.js'
import CanvasToolbar from './CanvasToolbar.vue'
import CanvasParameterPanel from './CanvasParameterPanel.vue'
import CanvasHistoryPanel from './CanvasHistoryPanel.vue'
import MaskGenerator from '../utils/maskGenerator.js'

export default {
  name: 'CanvasEditor',
  components: {
    CanvasToolbar,
    CanvasParameterPanel,
    CanvasHistoryPanel
  },
  setup() {
    // 响应式数据
    const canvasElement = ref(null)
    const canvas = ref(null)
    // 模式配置
    const currentMode = ref('')
    const isInpaintingMode = ref(false)
    const currentDrawingTool = ref('brush')
    const brushSize = ref(20)
    const isLoading = ref(false)
    const isProcessing = ref(false)
    const processingMessage = ref('')
    const currentImage = ref(null)
    const currentImageFile = ref(null) // 存储原始图像文件
    const maskGenerator = new MaskGenerator()
    
    // 参数配置
    const parameters = reactive({
      prompt: ''
    })
    
    // 历史管理
    const historyRecords = ref([])
    const currentHistoryIndex = ref(-1)
    const originalImageUrl = ref(null) // 保存原始图像URL
    
    // 持久化存储键名
    const STORAGE_KEYS = {
      CANVAS_STATE: 'canvas_editor_state',
      HISTORY_RECORDS: 'canvas_history_records',
      CURRENT_INDEX: 'canvas_current_index',
      ORIGINAL_IMAGE: 'canvas_original_image',
      PARAMETERS: 'canvas_parameters'
    }
    
    // 工具配置
    const tools = {
      select: { cursor: 'default', name: '选择' },
      rectangle: { cursor: 'crosshair', name: '矩形框选' },
      polygon: { cursor: 'crosshair', name: '多边形' },
      brush: { cursor: 'crosshair', name: '画笔' },
      eraser: { cursor: 'crosshair', name: '擦除' }
    }
    
    // 初始化画布
    const initCanvas = () => {
      if (!canvasElement.value) return
      
      // 在创建Canvas之前，先设置canvas元素的样式来避免wheel事件问题
      canvasElement.value.style.touchAction = 'pan-x pan-y'
      
      canvas.value = new fabric.Canvas(canvasElement.value, {
        width: 800,
        height: 600,
        backgroundColor: '#f0f0f0',
        selection: true,
        preserveObjectStacking: true,
        enablePointerEvents: true
      })
      
      // 设置画布事件
      setupCanvasEvents()
      
      // 修复wheel事件警告 - 更彻底的修复方法
      setTimeout(() => {
        if (canvas.value) {
          // 直接禁用Fabric.js的wheel事件处理
          canvas.value.enablePointerEvents = false
          
          // 移除所有wheel事件监听器
          const upperCanvas = canvas.value.upperCanvasEl
          const lowerCanvas = canvas.value.lowerCanvasEl
          
          if (upperCanvas) {
            upperCanvas.removeEventListener('wheel', canvas.value._onMouseWheel, { passive: false })
            upperCanvas.removeEventListener('wheel', canvas.value._onMouseWheel)
          }
          
          if (lowerCanvas) {
            lowerCanvas.removeEventListener('wheel', canvas.value._onMouseWheel, { passive: false })
            lowerCanvas.removeEventListener('wheel', canvas.value._onMouseWheel)
          }
          
          // 重新启用指针事件，但不包括wheel
          canvas.value.enablePointerEvents = true
          
          // 设置touch-action来避免滚动阻塞
          if (canvas.value.upperCanvasEl) {
            canvas.value.upperCanvasEl.style.touchAction = 'pan-x pan-y'
          }
          if (canvas.value.lowerCanvasEl) {
            canvas.value.lowerCanvasEl.style.touchAction = 'pan-x pan-y'
          }
        }
      }, 0)
    }
    
    // 设置画布事件
    const setupCanvasEvents = () => {
      if (!canvas.value) return
      
      // 选择事件
      canvas.value.on('selection:created', handleSelectionCreated)
      canvas.value.on('selection:updated', handleSelectionUpdated)
      canvas.value.on('selection:cleared', handleSelectionCleared)
      
      // 鼠标事件
      canvas.value.on('mouse:down', handleMouseDown)
      canvas.value.on('mouse:move', handleMouseMove)
      canvas.value.on('mouse:up', handleMouseUp)
      
      // 对象事件
      canvas.value.on('object:added', handleObjectAdded)
      canvas.value.on('object:removed', handleObjectRemoved)
    }
    
    // 处理模式变化
    const handleModeChange = (mode) => {
      currentMode.value = mode
      isInpaintingMode.value = mode === 'inpainting'
      updateCanvasCursor() // 更新画布设置
      console.log('模式切换到:', mode)
    }
    
    // 处理绘制工具变化
    const handleDrawingToolChange = (tool) => {
      currentDrawingTool.value = tool
      console.log('绘制工具切换到:', tool)
    }
    
    // 处理画笔大小变化
    const handleBrushSizeChange = (size) => {
      brushSize.value = size
      updateCanvasCursor() // 更新光标大小
      console.log('画笔大小设置为:', size)
    }
    
    // 清除画布绘制内容
    const handleClearCanvas = () => {
      if (canvas.value) {
        // 获取所有对象
        const objects = canvas.value.getObjects()
        
        // 移除所有绘制对象（保留原始图像）
        objects.forEach(obj => {
          // 只移除绘制路径，保留原始图像
          if (obj.type === 'path' || obj.type === 'rect' || obj.type === 'circle') {
            canvas.value.remove(obj)
          }
        })
        
        // 重新渲染画布
        canvas.value.renderAll()
        console.log('画布绘制内容已清除')
        
        // 清除后保存状态
        saveCanvasState()
      }
    }
    
    // 更新画布光标
    const updateCanvasCursor = () => {
      if (canvas.value) {
        if (isInpaintingMode.value) {
          // 创建自定义光标，显示工具大小
          const cursorSize = Math.max(brushSize.value, 10) // 最小10px
          const cursorCanvas = document.createElement('canvas')
          cursorCanvas.width = cursorSize + 4
          cursorCanvas.height = cursorSize + 4
          const ctx = cursorCanvas.getContext('2d')
          
          // 绘制圆形光标
          ctx.strokeStyle = currentDrawingTool.value === 'brush' ? '#007bff' : '#ff4444'
          ctx.lineWidth = 2
          ctx.beginPath()
          ctx.arc(cursorSize/2 + 2, cursorSize/2 + 2, cursorSize/2, 0, 2 * Math.PI)
          ctx.stroke()
          
          // 设置自定义光标
          const cursorUrl = cursorCanvas.toDataURL()
          canvas.value.defaultCursor = `url(${cursorUrl}) ${cursorSize/2 + 2} ${cursorSize/2 + 2}, crosshair`
          canvas.value.selection = false // 禁用选择功能
        } else {
          canvas.value.defaultCursor = 'default'
          canvas.value.selection = true // 启用选择功能
        }
      }
    }
    
    // 验证图像文件
    const validateImageFile = (file) => {
      // 检查文件类型
      const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp', 'image/bmp']
      if (!validTypes.includes(file.type)) {
        throw new Error('不支持的文件格式，请使用 JPG、PNG、GIF、WebP 或 BMP 格式')
      }
      
      // 检查文件大小 (限制为50MB)
      const maxSize = 50 * 1024 * 1024 // 50MB
      if (file.size > maxSize) {
        throw new Error('文件过大，请使用小于50MB的图像文件')
      }
      
      // 检查文件大小 (最小1KB)
      const minSize = 1024 // 1KB
      if (file.size < minSize) {
        throw new Error('文件过小，可能不是有效的图像文件')
      }
      
      return true
    }
    
    // 处理图像上传
    const loadImage = (file) => {
      if (!file || !canvas.value) {
        console.log('No file or canvas:', { file, canvas: canvas.value })
        return
      }
      
      try {
        // 验证文件
        validateImageFile(file)
        
        console.log('Loading image:', file.name, file.type, file.size)
        currentImageFile.value = file // 保存原始文件
        isLoading.value = true
        processingMessage.value = '正在加载图像...'
      } catch (error) {
        console.error('File validation failed:', error)
        alert(error.message)
        return
      }
      
      const reader = new FileReader()
      reader.onload = (e) => {
        console.log('FileReader loaded, creating fabric image...')
        const imageUrl = e.target.result
        
        // 使用Promise包装fabric.Image.fromURL
        console.log('Starting fabric.Image.fromURL with URL length:', imageUrl.length)
        
        new Promise((resolve, reject) => {
          const timeout = setTimeout(() => {
            console.log('Fabric image loading timeout, trying fallback...')
            reject(new Error('Fabric image loading timeout'))
          }, 30000) // 增加到30秒超时
          
          fabric.Image.fromURL(imageUrl, (img) => {
            clearTimeout(timeout)
            console.log('Fabric callback executed, img:', img)
            if (img && img.width > 0 && img.height > 0) {
              resolve(img)
            } else {
              reject(new Error('Failed to create fabric image - invalid dimensions'))
            }
          }, {
            crossOrigin: 'anonymous'
          })
        }).then((img) => {
          console.log('Fabric image created:', img)
          
          // 清除现有内容
          canvas.value.clear()
          
          // 保持画布尺寸不变，只缩放图像
          const canvasWidth = 600
          const canvasHeight = 600
          
          // 计算缩放比例以适应画布
          const scaleX = canvasWidth / img.width
          const scaleY = canvasHeight / img.height
          const scale = Math.min(scaleX, scaleY)
          
          // 设置图像
          img.set({
            left: 0,
            top: 0,
            selectable: false,
            evented: false,
            scaleX: scale,
            scaleY: scale
          })
          
          // 添加图像到画布
          canvas.value.add(img)
          
          currentImage.value = img
          isLoading.value = false
          processingMessage.value = ''
          
          // 居中显示
          canvas.value.centerObject(img)
          canvas.value.renderAll()
          
          console.log('Image loaded successfully, dimensions:', img.width, 'x', img.height)
        }).catch((error) => {
          console.error('Error loading image with Fabric.js:', error)
          // 尝试使用HTML5 Image作为备选方案
          console.log('Trying fallback method...')
          try {
            loadImageFallback(imageUrl)
          } catch (fallbackError) {
            console.error('Fallback method also failed:', fallbackError)
            isLoading.value = false
            alert('图像加载失败，请尝试使用其他格式的图像文件')
          }
        })
      }
      reader.onerror = (error) => {
        console.error('FileReader error:', error)
        isLoading.value = false
      }
      reader.readAsDataURL(file)
    }
    
    // 备选图像加载方案
    const loadImageFallback = (imageUrl) => {
      console.log('Using fallback image loading method')
      console.log('Image URL length:', imageUrl.length)
      processingMessage.value = '使用备选方法加载图像...'
      
      const img = new Image()
      img.crossOrigin = 'anonymous'
      
      img.onload = () => {
        try {
          console.log('Fallback image loaded:', img.width, 'x', img.height)
          
          if (img.width === 0 || img.height === 0) {
            throw new Error('Invalid image dimensions')
          }
          
          console.log('Canvas before clear:', canvas.value)
          
          // 清除现有内容
          canvas.value.clear()
          
          // 创建fabric图像对象
          const fabricImg = new fabric.Image(img, {
            left: 0,
            top: 0,
            selectable: false,
            evented: false
          })
          
          console.log('Fabric image created from fallback:', fabricImg)
          
          // 保持画布尺寸不变，只缩放图像
          const canvasWidth = 600
          const canvasHeight = 600
          
          // 计算缩放比例以适应画布
          const scaleX = canvasWidth / img.width
          const scaleY = canvasHeight / img.height
          const scale = Math.min(scaleX, scaleY)
          
          // 设置图像缩放
          fabricImg.set({
            scaleX: scale,
            scaleY: scale
          })
          
          // 添加图像到画布
          canvas.value.add(fabricImg)
          
          currentImage.value = fabricImg
          isLoading.value = false
          processingMessage.value = ''
          
          // 居中显示
          canvas.value.centerObject(fabricImg)
          canvas.value.renderAll()
          
          console.log('Image added to canvas successfully')
          console.log('Fallback image loaded successfully')
        } catch (error) {
          console.error('Error in fallback image loading:', error)
          isLoading.value = false
          alert('图像处理失败: ' + error.message)
        }
      }
      img.onerror = (error) => {
        console.error('Fallback image loading failed:', error)
        console.error('Image src:', imageUrl.substring(0, 100) + '...')
        isLoading.value = false
        alert('图像加载失败，请检查文件格式')
      }
      
      console.log('Setting image src...')
      img.src = imageUrl
      
      // 设置超时，如果fallback也失败，使用最简单的方案
      setTimeout(() => {
        if (isLoading.value) {
          console.log('Fallback timeout, trying simplest method...')
          loadImageSimplest(imageUrl)
        }
      }, 20000) // 20秒后尝试最简单的方法
    }
    
    // 最简单的图像加载方案
    const loadImageSimplest = (imageUrl) => {
      console.log('Using simplest image loading method')
      
      try {
        // 直接使用loadImageFromUrl方法
        loadImageFromUrl(imageUrl, true) // 标记为原始图像
        isLoading.value = false
      } catch (error) {
        console.error('Simplest method failed:', error)
        isLoading.value = false
        alert('所有图像加载方法都失败了，请尝试使用其他图像文件')
      }
    }
    
    // 处理拖拽上传
    const handleDrop = (e) => {
      e.preventDefault()
      e.stopPropagation()
      
      const files = e.dataTransfer.files
      if (files.length > 0) {
        loadImage(files[0])
      }
    }
    
    const handleDragOver = (e) => {
      e.preventDefault()
    }
    
    const handleDragEnter = (e) => {
      e.preventDefault()
      e.currentTarget.classList.add('drag-over')
    }
    
    const handleDragLeave = (e) => {
      e.preventDefault()
      e.currentTarget.classList.remove('drag-over')
    }
    
    // 鼠标事件处理
    const handleMouseDown = (e) => {
      if (isInpaintingMode.value && (currentDrawingTool.value === 'brush' || currentDrawingTool.value === 'eraser')) {
        startBrushDrawing(e)
      }
    }
    
    const handleMouseMove = (e) => {
      if (isInpaintingMode.value && (currentDrawingTool.value === 'brush' || currentDrawingTool.value === 'eraser') && isDrawing.value) {
        continueBrushDrawing(e)
      }
    }
    
    const handleMouseUp = (e) => {
      if (isInpaintingMode.value && (currentDrawingTool.value === 'brush' || currentDrawingTool.value === 'eraser')) {
        finishBrushDrawing(e)
      }
    }
    
    // 矩形选择
    const isDrawing = ref(false)
    const startPoint = ref(null)
    const currentRect = ref(null)
    
    const startRectangleSelection = (e) => {
      isDrawing.value = true
      startPoint.value = canvas.value.getPointer(e.e)
    }
    
    const finishRectangleSelection = (e) => {
      if (!isDrawing.value) return
      
      isDrawing.value = false
      const endPoint = canvas.value.getPointer(e.e)
      
      // 创建选择矩形
      const rect = new fabric.Rect({
        left: Math.min(startPoint.value.x, endPoint.x),
        top: Math.min(startPoint.value.y, endPoint.y),
        width: Math.abs(endPoint.x - startPoint.value.x),
        height: Math.abs(endPoint.y - startPoint.value.y),
        fill: 'rgba(0, 123, 255, 0.3)',
        stroke: '#007bff',
        strokeWidth: 2,
        selectable: true,
        evented: true
      })
      
      canvas.value.add(rect)
      canvas.value.setActiveObject(rect)
      canvas.value.renderAll()
    }
    
    // 画笔绘制
    const brushPath = ref([])
    
    const startBrushDrawing = (e) => {
      isDrawing.value = true
      brushPath.value = [canvas.value.getPointer(e.e)]
    }
    
    const continueBrushDrawing = (e) => {
      if (!isDrawing.value) return
      brushPath.value.push(canvas.value.getPointer(e.e))
      
      // 实时显示绘制路径
      if (currentDrawingTool.value === 'brush') {
        // 清除之前的临时路径
        const existingTemp = canvas.value.getObjects().find(obj => obj.tempPath)
        if (existingTemp) {
          canvas.value.remove(existingTemp)
        }
        
        // 创建临时路径显示
        if (brushPath.value.length > 1) {
          const tempPath = new fabric.Path(
            createBrushPathFromPoints(brushPath.value, brushSize.value),
            {
              fill: 'rgba(0, 100, 200, 0.3)',
              stroke: 'transparent', // 移除边框
              strokeWidth: 0, // 无边框
              selectable: false,
              evented: false,
              tempPath: true
            }
          )
          
          canvas.value.add(tempPath)
          canvas.value.renderAll()
        }
      } else if (currentDrawingTool.value === 'eraser') {
        // 橡皮擦功能：删除与橡皮擦路径相交的绘制对象
        const pointer = canvas.value.getPointer(e.e)
        const objects = canvas.value.getObjects()
        
        // 检查每个绘制对象是否与橡皮擦路径相交
        objects.forEach(obj => {
          if (obj.tempPath || obj === currentImage.value) return // 跳过临时路径和原始图像
          
          // 检查对象是否在橡皮擦范围内
          if (isObjectInEraserRange(obj, pointer, brushSize.value)) {
            canvas.value.remove(obj)
          }
        })
        
        canvas.value.renderAll()
      }
    }
    
    const finishBrushDrawing = (e) => {
      if (!isDrawing.value) return
      
      isDrawing.value = false
      
      // 清除临时路径
      const existingTemp = canvas.value.getObjects().find(obj => obj.tempPath)
      if (existingTemp) {
        canvas.value.remove(existingTemp)
      }
      
      // 只有画笔工具才创建路径，橡皮擦不需要
      if (currentDrawingTool.value === 'brush' && brushPath.value.length >= 2) {
        // 创建多个小圆形对象，而不是一个大路径
        // 这样橡皮擦就可以只删除相交的小对象
        const radius = brushSize.value / 2
        
        // 创建棋盘格图案（只创建一次，所有圆形共享）
        const patternCanvas = document.createElement('canvas')
        patternCanvas.width = 20
        patternCanvas.height = 20
        const patternCtx = patternCanvas.getContext('2d')
        
        // 绘制棋盘格
        patternCtx.fillStyle = 'rgba(0, 100, 200, 1.0)'
        patternCtx.fillRect(0, 0, 10, 10)
        patternCtx.fillRect(10, 10, 10, 10)
        patternCtx.fillStyle = 'rgba(0, 100, 200, 0.6)'
        patternCtx.fillRect(10, 0, 10, 10)
        patternCtx.fillRect(0, 10, 10, 10)
        
        // 应用图案
        const pattern = new fabric.Pattern({
          source: patternCanvas,
          repeat: 'repeat'
        })
        
        // 创建连贯的绘制效果，使用更密集的点
        const step = Math.max(radius * 0.3, 2) // 根据画笔大小调整步长
        
        for (let i = 0; i < brushPath.value.length - 1; i++) {
          const currentPoint = brushPath.value[i]
          const nextPoint = brushPath.value[i + 1]
          
          // 计算两点之间的距离
          const distance = Math.sqrt(
            Math.pow(nextPoint.x - currentPoint.x, 2) + Math.pow(nextPoint.y - currentPoint.y, 2)
          )
          
          // 计算需要插入的点数
          const numPoints = Math.ceil(distance / step)
          
          // 在两点之间插入多个点，确保连贯
          for (let j = 0; j <= numPoints; j++) {
            const t = j / numPoints
            const x = currentPoint.x + (nextPoint.x - currentPoint.x) * t
            const y = currentPoint.y + (nextPoint.y - currentPoint.y) * t
            
            const circle = new fabric.Circle({
              left: x - radius,
              top: y - radius,
              radius: radius,
              fill: pattern,
              stroke: 'transparent',
              strokeWidth: 0,
              selectable: false,
              evented: false,
              moveable: false,
              lockMovementX: true,
              lockMovementY: true,
              isDrawnMask: true // 标识这是绘制的遮罩区域
            })
            
            canvas.value.add(circle)
          }
        }
        
        // 添加最后一个点
        if (brushPath.value.length > 0) {
          const lastPoint = brushPath.value[brushPath.value.length - 1]
          const circle = new fabric.Circle({
            left: lastPoint.x - radius,
            top: lastPoint.y - radius,
            radius: radius,
            fill: pattern,
            stroke: 'transparent',
            strokeWidth: 0,
            selectable: false,
            evented: false,
            moveable: false,
            lockMovementX: true,
            lockMovementY: true,
            isDrawnMask: true // 标识这是绘制的遮罩区域
          })
          
          canvas.value.add(circle)
        }
        
        canvas.value.renderAll()
        
        // 绘制完成后自动保存
        saveCanvasState()
      }
      
      brushPath.value = []
    }
    
    // 从点创建路径
    const createPathFromPoints = (points) => {
      if (points.length < 2) return ''
      
      let path = `M ${points[0].x} ${points[0].y}`
      for (let i = 1; i < points.length; i++) {
        path += ` L ${points[i].x} ${points[i].y}`
      }
      return path
    }
    
    // 检查对象是否在橡皮擦范围内
    const isObjectInEraserRange = (obj, pointer, eraserSize) => {
      const objBounds = obj.getBoundingRect()
      const eraserRadius = eraserSize / 2
      
      // 检查橡皮擦中心是否在对象范围内，或者对象是否与橡皮擦圆形区域相交
      const centerX = pointer.x
      const centerY = pointer.y
      
      // 检查橡皮擦中心是否在对象边界内
      if (centerX >= objBounds.left && centerX <= objBounds.left + objBounds.width &&
          centerY >= objBounds.top && centerY <= objBounds.top + objBounds.height) {
        return true
      }
      
      // 检查橡皮擦圆形是否与对象矩形相交
      const closestX = Math.max(objBounds.left, Math.min(centerX, objBounds.left + objBounds.width))
      const closestY = Math.max(objBounds.top, Math.min(centerY, objBounds.top + objBounds.height))
      
      const distanceX = centerX - closestX
      const distanceY = centerY - closestY
      const distanceSquared = distanceX * distanceX + distanceY * distanceY
      
      return distanceSquared <= (eraserRadius * eraserRadius)
    }
    
    
    // 从点创建画笔路径（有宽度）
    const createBrushPathFromPoints = (points, brushSize) => {
      if (points.length < 2) return ''
      
      const radius = brushSize / 2
      let path = ''
      
      // 为每个点创建圆形
      for (let i = 0; i < points.length; i++) {
        const point = points[i]
        const x = point.x
        const y = point.y
        
        // 创建圆形路径
        path += `M ${x - radius} ${y} A ${radius} ${radius} 0 1 1 ${x + radius} ${y} A ${radius} ${radius} 0 1 1 ${x - radius} ${y} Z `
      }
      
      // 连接相邻的圆形
      for (let i = 0; i < points.length - 1; i++) {
        const current = points[i]
        const next = points[i + 1]
        
        // 计算连接矩形的路径
        const dx = next.x - current.x
        const dy = next.y - current.y
        const distance = Math.sqrt(dx * dx + dy * dy)
        
        if (distance > 0) {
          const angle = Math.atan2(dy, dx)
          const perpAngle = angle + Math.PI / 2
          
          const x1 = current.x + Math.cos(perpAngle) * radius
          const y1 = current.y + Math.sin(perpAngle) * radius
          const x2 = current.x - Math.cos(perpAngle) * radius
          const y2 = current.y - Math.sin(perpAngle) * radius
          const x3 = next.x - Math.cos(perpAngle) * radius
          const y3 = next.y - Math.sin(perpAngle) * radius
          const x4 = next.x + Math.cos(perpAngle) * radius
          const y4 = next.y + Math.sin(perpAngle) * radius
          
          path += `M ${x1} ${y1} L ${x2} ${y2} L ${x3} ${y3} L ${x4} ${y4} Z `
        }
      }
      
      return path
    }
    
    // 选择事件处理
    const handleSelectionCreated = (e) => {
      console.log('Selection created:', e.selected)
    }
    
    const handleSelectionUpdated = (e) => {
      console.log('Selection updated:', e.selected)
    }
    
    const handleSelectionCleared = (e) => {
      console.log('Selection cleared')
    }
    
    // 对象事件处理
    const handleObjectAdded = (e) => {
      console.log('Object added:', e.target)
    }
    
    const handleObjectRemoved = (e) => {
      console.log('Object removed:', e.target)
    }
    
    // 清除选择
    const handleClearSelection = () => {
      if (canvas.value) {
        canvas.value.discardActiveObject()
        canvas.value.renderAll()
      }
    }
    
    // 历史管理方法
    const addToHistory = (record) => {
      // 如果当前不在最新记录，删除后面的记录
      if (currentHistoryIndex.value < historyRecords.value.length - 1) {
        historyRecords.value = historyRecords.value.slice(0, currentHistoryIndex.value + 1)
      }
      
      // 添加新记录
      historyRecords.value.push(record)
      currentHistoryIndex.value = historyRecords.value.length - 1
      
      console.log('📝 添加到历史记录:', record)
    }
    
    const handleSwitchHistory = (record) => {
      console.log('🔄 切换到历史记录:', record)
      // 加载历史记录中的图像
      loadImageFromUrl(record.resultImageUrl)
    }
    
    const handleUndo = () => {
      console.log('↶ 撤销操作')
    }
    
    const handleRedo = () => {
      console.log('↷ 重做操作')
    }
    
    // 执行局部重绘
    const handleExecuteInpainting = async () => {
      if (!currentImage.value) {
        alert('请先上传图像')
        return
      }
      
      // 检查是否有绘制的区域
      const objects = canvas.value.getObjects()
      console.log('所有画布对象:', objects.length)
      
      const drawnObjects = objects.filter(obj => 
        obj !== currentImage.value && 
        !obj.tempPath && 
        obj.isDrawnMask === true
      )
      
      console.log('绘制的对象数量:', drawnObjects.length)
      
      if (drawnObjects.length === 0) {
        alert('请先绘制要重绘的区域')
        return
      }
      
      isProcessing.value = true
      processingMessage.value = '正在执行局部重绘...'
      
      try {
        // 调用API（generateMaskImage在executeInpaintingAPI内部调用）
        const result = await executeInpaintingAPI(currentImage.value, null, parameters)
        
        // 更新图像
        if (result.success) {
          console.log('🎨 局部重绘成功，准备更新图像:', result.imageUrl)
          
          // 保存当前状态到历史记录
          const historyRecord = {
            id: Date.now().toString(),
            timestamp: Date.now(),
            prompt: parameters.prompt,
            originalImageUrl: originalImageUrl.value,
            maskDataUrl: result.maskDataUrl,
            resultImageUrl: result.imageUrl,
            parameters: { ...parameters }
          }
          
          // 添加到历史记录
          addToHistory(historyRecord)
          
          // 加载新图像
          console.log('🔄 开始加载重绘结果图像...')
          loadImageFromUrl(result.imageUrl)
        } else {
          alert('局部重绘失败: ' + result.message)
        }
      } catch (error) {
        console.error('Inpainting error:', error)
        alert('局部重绘失败: ' + error.message)
      } finally {
        isProcessing.value = false
      }
    }
    
    // 执行扩图
    const handleExecuteOutpainting = async () => {
      if (!currentImage.value) {
        alert('请先上传图像')
        return
      }
      
      isProcessing.value = true
      processingMessage.value = '正在执行扩图...'
      
      try {
        const result = await executeOutpaintingAPI(currentImage.value, parameters)
        
        if (result.success) {
          loadImageFromUrl(result.imageUrl)
        } else {
          alert('扩图失败: ' + result.message)
        }
      } catch (error) {
        console.error('Outpainting error:', error)
        alert('扩图失败: ' + error.message)
      } finally {
        isProcessing.value = false
      }
    }
    
    // 从URL加载图像
    const loadImageFromUrl = (url, isOriginal = false) => {
      console.log('📥 开始加载图像:', url, 'isOriginal:', isOriginal)
      
      fabric.Image.fromURL(url, (img) => {
        console.log('✅ 图像加载成功:', img.width, 'x', img.height)
        if (isOriginal) {
          // 原始图像加载：清除所有内容
          canvas.value.clear()
          
          img.set({
            left: 0,
            top: 0,
            selectable: false,
            evented: false
          })
          
          canvas.value.setWidth(img.width)
          canvas.value.setHeight(img.height)
          canvas.value.add(img)
          canvas.value.sendToBack(img)
          
          currentImage.value = img
          canvas.value.centerObject(img)
          canvas.value.renderAll()
          
          // 保存原始图像URL
          originalImageUrl.value = url
        } else {
          // 重绘结果加载：只替换背景图像，保留其他绘制内容
          if (currentImage.value) {
            // 获取当前图像的位置和缩放信息
            const currentLeft = currentImage.value.left
            const currentTop = currentImage.value.top
            const currentScaleX = currentImage.value.scaleX
            const currentScaleY = currentImage.value.scaleY
            
            // 设置新图像的位置和缩放
            img.set({
              left: currentLeft,
              top: currentTop,
              scaleX: currentScaleX,
              scaleY: currentScaleY,
              selectable: false,
              evented: false
            })
            
            // 移除旧图像，添加新图像
            canvas.value.remove(currentImage.value)
            canvas.value.add(img)
            canvas.value.sendToBack(img)
            
            // 更新当前图像引用
            currentImage.value = img
            canvas.value.renderAll()
            
            console.log('✅ 重绘结果已回填到画板')
          } else {
            // 如果没有当前图像，按原始图像方式加载
            canvas.value.clear()
            
            img.set({
              left: 0,
              top: 0,
              selectable: false,
              evented: false
            })
            
            canvas.value.setWidth(img.width)
            canvas.value.setHeight(img.height)
            canvas.value.add(img)
            canvas.value.sendToBack(img)
            
            currentImage.value = img
            canvas.value.centerObject(img)
            canvas.value.renderAll()
          }
        }
      })
    }
    
    // 生成遮罩图像
    const generateMaskImage = () => {
      if (!canvas.value || !currentImage.value) {
        throw new Error('画布或图像未加载')
      }
      
      // 创建临时画布用于生成遮罩
      const tempCanvas = document.createElement('canvas')
      const tempCtx = tempCanvas.getContext('2d')
      
      // 获取原始图像尺寸
      // 从Fabric.js图像对象获取原始尺寸
      const originalWidth = currentImage.value._originalElement ? currentImage.value._originalElement.width : 1024
      const originalHeight = currentImage.value._originalElement ? currentImage.value._originalElement.height : 1024
      
      // 设置画布尺寸为原始图像尺寸
      tempCanvas.width = originalWidth
      tempCanvas.height = originalHeight
      
      // 获取所有绘制的对象
      const objects = canvas.value.getObjects()
      const drawnObjects = objects.filter(obj => 
        obj !== currentImage.value && 
        !obj.tempPath && 
        obj.isDrawnMask === true // 检查是否是绘制的遮罩区域
      )
      
      if (drawnObjects.length === 0) {
        throw new Error('请先绘制要重绘的区域')
      }
      
      // 计算坐标缩放比例
      // 从Fabric.js显示尺寸到原始图像尺寸的缩放比例
      const scaleX = originalWidth / (currentImage.value.width * currentImage.value.scaleX)
      const scaleY = originalHeight / (currentImage.value.height * currentImage.value.scaleY)
      
      // 获取图像在画布中的实际位置（考虑居中偏移）
      const imageBounds = currentImage.value.getBoundingRect()
      const imageLeft = imageBounds.left
      const imageTop = imageBounds.top
      
      // 调试信息：图像位置和尺寸 - 简化输出
      console.log('图像信息:', {
        imageWidth: currentImage.value.width,
        imageHeight: currentImage.value.height,
        originalWidth: originalWidth,
        originalHeight: originalHeight,
        scaleX: scaleX,
        scaleY: scaleY,
        isCentered: currentImage.value.left === (canvas.value.width - currentImage.value.width) / 2
      })
      
      console.log('遮罩生成逻辑:')
      console.log('1. 创建白色背景 (alpha=255, 保持不变的区域)')
      console.log('2. 在绘制区域创建透明洞 (alpha=0, 要重绘的区域)')
      console.log('3. 绘制对象数量:', drawnObjects.length)
      
      // 绘制遮罩 - 使用alpha通道表示遮罩区域
      // 1. 先创建完全不透明的白色背景（表示保持不变的区域）
      tempCtx.fillStyle = 'rgba(255, 255, 255, 1.0)' // 白色，完全不透明
      tempCtx.fillRect(0, 0, originalWidth, originalHeight)
      
      // 2. 在绘制的区域创建透明"洞"（表示要重绘的区域）
      // 使用destination-out模式来移除像素，创建透明区域
      tempCtx.globalCompositeOperation = 'destination-out'
      tempCtx.fillStyle = 'rgba(0, 0, 0, 1.0)' // 任何颜色都可以，destination-out会移除像素
      drawnObjects.forEach(obj => {
        if (obj.type === 'circle') {
          // 将Fabric.js画布坐标转换为原始图像坐标
          // 1. 减去图像在画布中的偏移
          const relativeLeft = obj.left - imageLeft
          const relativeTop = obj.top - imageTop
          
          // 2. 转换为原始图像坐标
          const originalLeft = relativeLeft * scaleX
          const originalTop = relativeTop * scaleY
          const originalRadius = obj.radius * Math.min(scaleX, scaleY)
          
          // 调试信息 - 简化输出
          if (drawnObjects.indexOf(obj) < 3) { // 只显示前3个对象的详细信息
            console.log('遮罩坐标转换:', {
              fabricLeft: obj.left,
              fabricTop: obj.top,
              originalLeft: originalLeft,
              originalTop: originalTop,
              scaleX: scaleX,
              scaleY: scaleY
            })
          }
          
          tempCtx.beginPath()
          tempCtx.arc(
            originalLeft + originalRadius, 
            originalTop + originalRadius, 
            originalRadius, 
            0, 
            2 * Math.PI
          )
          tempCtx.fill()
        }
      })
      
      // 恢复默认的合成模式
      tempCtx.globalCompositeOperation = 'source-over'
      
      return tempCanvas.toDataURL('image/png')
    }
    
    // 将DataURL转换为File对象
    const dataUrlToFile = (dataUrl, filename) => {
      const arr = dataUrl.split(',')
      const mime = arr[0].match(/:(.*?);/)[1]
      const bstr = atob(arr[1])
      let n = bstr.length
      const u8arr = new Uint8Array(n)
      while (n--) {
        u8arr[n] = bstr.charCodeAt(n)
      }
      return new File([u8arr], filename, { type: mime })
    }
    
    // API调用函数
    const executeInpaintingAPI = async (image, mask, params) => {
      try {
        console.log('🎨 开始执行局部重绘API调用')
        
        // 生成遮罩图像
        const maskDataUrl = generateMaskImage()
        const maskFile = dataUrlToFile(maskDataUrl, 'mask.png')
        
        // 准备参数
        const parameters = {
          negative_prompt: '',
          steps: 8,
          cfg: 2.5,
          denoise: 1.0,
          target_size: 1024,
          lora_strength: 1.0,
          seed: -1
        }
        
        // 调用Qwen-Edit API
        const API_BASE = 'http://localhost:9000' // 后端API地址
        
        return new Promise((resolve, reject) => {
          executeQwenEdit(
            currentImageFile.value, // 原始图像文件
            maskFile, // 遮罩文件
            params.prompt, // 提示词
            parameters, // 参数
            API_BASE, // API地址
            {
              onTaskCreated: (taskId) => {
                console.log(`✅ 任务已创建: ${taskId}`)
              },
              onProgress: (progress) => {
                console.log(`📊 进度: ${progress}%`)
              },
              onSuccess: async (statusData, taskId) => {
                console.log('✅ 局部重绘完成:', statusData)
                
                // 获取图像URL
                let imageUrl = null
                if (statusData.result) {
                  // 优先使用direct_urls，然后是image_urls
                  if (statusData.result.direct_urls && statusData.result.direct_urls.length > 0) {
                    imageUrl = statusData.result.direct_urls[0]
                  } else if (statusData.result.image_urls && statusData.result.image_urls.length > 0) {
                    imageUrl = statusData.result.image_urls[0]
                  } else if (statusData.result.image_url) {
                    imageUrl = statusData.result.image_url
                  }
                }
                
                // 如果是相对路径，添加API基础URL
                if (imageUrl && imageUrl.startsWith('/')) {
                  imageUrl = API_BASE + imageUrl
                }
                
                console.log('🖼️ 图像URL:', imageUrl)
                
                resolve({
                  success: true,
                  imageUrl: imageUrl,
                  maskDataUrl: maskDataUrl // 返回遮罩数据URL
                })
              },
              onError: (error) => {
                console.error('❌ 局部重绘失败:', error)
                reject(new Error(error))
              }
            }
          )
        })
      } catch (error) {
        console.error('❌ 执行局部重绘时出错:', error)
        throw error
      }
    }
    
    const executeOutpaintingAPI = async (image, params) => {
      // TODO: 实现实际的扩图API调用
      return new Promise((resolve) => {
        setTimeout(() => {
          resolve({
            success: true,
            imageUrl: image.toDataURL()
          })
        }, 2000)
      })
    }
    
    // 生命周期
    onMounted(async () => {
      nextTick(async () => {
        initCanvas()
        
        // 启动自动保存
        startAutoSave()
        
        // 加载保存的状态
        await loadCanvasState()
      })
    })
    
    onUnmounted(() => {
      // 停止自动保存
      stopAutoSave()
      
      // 保存当前状态
      saveCanvasState()
      
      if (canvas.value) {
        canvas.value.dispose()
      }
    })
    
    // 处理文件上传事件
    const handleFileUpload = (file) => {
      console.log('File uploaded:', file)
      loadImage(file)
    }
    
    // 处理保存图像事件
    const handleSaveImage = () => {
      if (!canvas.value || !currentImage.value) {
        alert('没有可保存的图像')
        return
      }
      
      try {
        // 导出画布为图像
        const dataURL = canvas.value.toDataURL({
          format: 'png',
          quality: 1.0,
          multiplier: 1
        })
        
        // 创建下载链接
        const link = document.createElement('a')
        link.download = `canvas-image-${Date.now()}.png`
        link.href = dataURL
        
        // 触发下载
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        
        console.log('图像已保存')
      } catch (error) {
        console.error('保存图像失败:', error)
        alert('保存图像失败: ' + error.message)
      }
    }
    
    // 测试图像加载
    const testImageLoad = () => {
      console.log('Testing image load...')
      // 创建一个简单的测试图像
      const canvas = document.createElement('canvas')
      canvas.width = 400
      canvas.height = 300
      const ctx = canvas.getContext('2d')
      
      // 绘制一个简单的测试图像
      ctx.fillStyle = '#007bff'
      ctx.fillRect(0, 0, 400, 300)
      ctx.fillStyle = 'white'
      ctx.font = '24px Arial'
      ctx.textAlign = 'center'
      ctx.fillText('测试图像', 200, 150)
      
      // 转换为blob并加载
      canvas.toBlob((blob) => {
        const file = new File([blob], 'test.png', { type: 'image/png' })
        loadImage(file)
      })
    }
    
    // ==================== 持久化功能 ====================
    
    // 保存画布状态到localStorage
    const saveCanvasState = () => {
      try {
        if (!canvas.value) return
        
        // 保存画布JSON状态
        const canvasState = canvas.value.toJSON(['isDrawnMask'])
        localStorage.setItem(STORAGE_KEYS.CANVAS_STATE, JSON.stringify(canvasState))
        
        // 保存历史记录
        localStorage.setItem(STORAGE_KEYS.HISTORY_RECORDS, JSON.stringify(historyRecords.value))
        
        // 保存当前历史索引
        localStorage.setItem(STORAGE_KEYS.CURRENT_INDEX, currentHistoryIndex.value.toString())
        
        // 保存原始图像URL
        if (originalImageUrl.value) {
          localStorage.setItem(STORAGE_KEYS.ORIGINAL_IMAGE, originalImageUrl.value)
        }
        
        // 保存参数
        localStorage.setItem(STORAGE_KEYS.PARAMETERS, JSON.stringify(parameters))
        
        console.log('✅ 画布状态已保存到localStorage')
      } catch (error) {
        console.error('❌ 保存画布状态失败:', error)
      }
    }
    
    // 从localStorage加载画布状态
    const loadCanvasState = async () => {
      try {
        // 加载画布状态
        const canvasStateStr = localStorage.getItem(STORAGE_KEYS.CANVAS_STATE)
        if (canvasStateStr && canvas.value) {
          const canvasState = JSON.parse(canvasStateStr)
          await canvas.value.loadFromJSON(canvasState, () => {
            canvas.value.renderAll()
            console.log('✅ 画布状态已从localStorage恢复')
          })
        }
        
        // 加载历史记录
        const historyStr = localStorage.getItem(STORAGE_KEYS.HISTORY_RECORDS)
        if (historyStr) {
          historyRecords.value = JSON.parse(historyStr)
        }
        
        // 加载当前历史索引
        const indexStr = localStorage.getItem(STORAGE_KEYS.CURRENT_INDEX)
        if (indexStr) {
          currentHistoryIndex.value = parseInt(indexStr)
        }
        
        // 加载原始图像URL
        const originalImageStr = localStorage.getItem(STORAGE_KEYS.ORIGINAL_IMAGE)
        if (originalImageStr) {
          originalImageUrl.value = originalImageStr
        }
        
        // 加载参数
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
    
    // 清除所有保存的状态
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
      // 每30秒自动保存一次
      autoSaveTimer = setInterval(() => {
        if (canvas.value && currentImage.value) {
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
      // 清除localStorage
      clearSavedState()
      
      // 清除当前状态
      historyRecords.value = []
      currentHistoryIndex.value = -1
      originalImageUrl.value = null
      parameters.prompt = ''
      
      // 清除画布
      if (canvas.value) {
        canvas.value.clear()
        canvas.value.renderAll()
      }
      
      alert('所有状态已清除！')
    }
    
    return {
      // 响应式数据
      canvasElement,
      currentMode,
      isInpaintingMode,
      currentDrawingTool,
      brushSize,
      isLoading,
      isProcessing,
      processingMessage,
      parameters,
      currentImage,
      currentImageFile,
      
      // 方法
      handleModeChange,
      handleDrawingToolChange,
      handleBrushSizeChange,
      handleClearCanvas,
      handleExecuteInpainting,
      handleExecuteOutpainting,
      handleClearSelection,
      handleDrop,
      handleDragOver,
      handleDragEnter,
      handleDragLeave,
      handleFileUpload,
      handleSaveImage,
      testImageLoad,
      // 历史管理
      historyRecords,
      currentHistoryIndex,
      handleSwitchHistory,
      handleUndo,
      handleRedo,
      
      // 持久化功能
      saveCanvasState,
      loadCanvasState,
      clearSavedState,
      startAutoSave,
      stopAutoSave,
      handleSaveState,
      handleClearState
    }
  }
}
</script>

<style scoped>
.canvas-editor {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #1a1a1a;
  color: white;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  margin-right: 320px; /* 为固定的历史面板留出空间 */
  transition: margin-right 0.3s ease;
}

.main-content.full-width {
  margin-right: 0; /* 局部重绘模式下使用全宽 */
}

.canvas-container {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 10px;
  overflow: auto;
  min-height: 0; /* 允许flex子项缩小 */
}

.canvas-wrapper {
  position: relative;
  border: 2px solid #333;
  border-radius: 8px;
  background: #2a2a2a;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
  max-width: 100%;
  max-height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
}

.main-canvas {
  display: block;
  border-radius: 6px;
}

.loading-overlay,
.processing-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  border-radius: 6px;
  z-index: 10;
}

.loading-spinner,
.processing-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #333;
  border-top: 4px solid #007bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 10px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.drag-over {
  border-color: #007bff !important;
  background: rgba(0, 123, 255, 0.1) !important;
}

.debug-info {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  color: #888;
  pointer-events: none;
  z-index: 5;
}

.debug-info p {
  margin: 5px 0;
  font-size: 14px;
}

.test-btn {
  margin-top: 10px;
  padding: 8px 16px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.2s ease;
}

.test-btn:hover {
  background: #0056b3;
}
</style>
