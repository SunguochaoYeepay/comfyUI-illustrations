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
    />
    
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
</template>

<script>
import { ref, reactive, onMounted, onUnmounted, nextTick } from 'vue'
import * as fabric from 'fabric'
import CanvasToolbar from './CanvasToolbar.vue'
import CanvasParameterPanel from './CanvasParameterPanel.vue'
import MaskGenerator from '../utils/maskGenerator.js'

export default {
  name: 'CanvasEditor',
  components: {
    CanvasToolbar,
    CanvasParameterPanel
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
    const maskGenerator = new MaskGenerator()
    
    // 参数配置
    const parameters = reactive({
      prompt: ''
    })
    
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
      
      // 修复wheel事件警告 - 使用更简单的方法
      setTimeout(() => {
        if (canvas.value && canvas.value.upperCanvasEl) {
          canvas.value.upperCanvasEl.style.touchAction = 'pan-x pan-y'
        }
      }, 100)
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
    
    // 处理图像上传
    const loadImage = (file) => {
      if (!file || !canvas.value) {
        console.log('No file or canvas:', { file, canvas: canvas.value })
        return
      }
      
      console.log('Loading image:', file.name, file.type, file.size)
      isLoading.value = true
      
      const reader = new FileReader()
      reader.onload = (e) => {
        console.log('FileReader loaded, creating fabric image...')
        const imageUrl = e.target.result
        
        // 使用Promise包装fabric.Image.fromURL
        console.log('Starting fabric.Image.fromURL with URL length:', imageUrl.length)
        
        new Promise((resolve, reject) => {
          const timeout = setTimeout(() => {
            reject(new Error('Fabric image loading timeout'))
          }, 10000) // 10秒超时
          
          fabric.Image.fromURL(imageUrl, (img) => {
            clearTimeout(timeout)
            console.log('Fabric callback executed, img:', img)
            if (img) {
              resolve(img)
            } else {
              reject(new Error('Failed to create fabric image'))
            }
          }, {
            crossOrigin: 'anonymous'
          })
        }).then((img) => {
          console.log('Fabric image created:', img)
          
          // 清除现有内容
          canvas.value.clear()
          
          // 设置图像
          img.set({
            left: 0,
            top: 0,
            selectable: false,
            evented: false
          })
          
          // 计算适合的显示尺寸
          const maxWidth = 800
          const maxHeight = 600
          let displayWidth = img.width
          let displayHeight = img.height
          
          // 如果图像太大，按比例缩放
          if (img.width > maxWidth || img.height > maxHeight) {
            const scale = Math.min(maxWidth / img.width, maxHeight / img.height)
            displayWidth = img.width * scale
            displayHeight = img.height * scale
          }
          
          // 调整画布大小
          canvas.value.setWidth(displayWidth)
          canvas.value.setHeight(displayHeight)
          
          // 缩放图像以适应画布
          img.scaleToWidth(displayWidth)
          img.scaleToHeight(displayHeight)
          
          // 添加图像到画布
          canvas.value.add(img)
          
          currentImage.value = img
          isLoading.value = false
          
          // 居中显示
          canvas.value.centerObject(img)
          canvas.value.renderAll()
          
          console.log('Image loaded successfully, dimensions:', img.width, 'x', img.height)
        }).catch((error) => {
          console.error('Error loading image with Fabric.js:', error)
          // 尝试使用HTML5 Image作为备选方案
          console.log('Trying fallback method...')
          loadImageFallback(imageUrl)
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
      
      const img = new Image()
      img.onload = () => {
        try {
          console.log('Fallback image loaded:', img.width, 'x', img.height)
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
          
          // 计算适合的显示尺寸
          const maxWidth = 800
          const maxHeight = 600
          let displayWidth = img.width
          let displayHeight = img.height
          
          // 如果图像太大，按比例缩放
          if (img.width > maxWidth || img.height > maxHeight) {
            const scale = Math.min(maxWidth / img.width, maxHeight / img.height)
            displayWidth = img.width * scale
            displayHeight = img.height * scale
          }
          
          // 调整画布大小
          canvas.value.setWidth(displayWidth)
          canvas.value.setHeight(displayHeight)
          
          // 缩放图像以适应画布
          fabricImg.scaleToWidth(displayWidth)
          fabricImg.scaleToHeight(displayHeight)
          
          // 添加图像到画布
          canvas.value.add(fabricImg)
          
          currentImage.value = fabricImg
          isLoading.value = false
          
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
              lockMovementY: true
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
            lockMovementY: true
          })
          
          canvas.value.add(circle)
        }
        
        canvas.value.renderAll()
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
    
    // 执行局部重绘
    const handleExecuteInpainting = async () => {
      if (!currentImage.value) {
        alert('请先上传图像')
        return
      }
      
      const selection = canvas.value.getActiveObject()
      if (!selection) {
        alert('请先选择要重绘的区域')
        return
      }
      
      isProcessing.value = true
      processingMessage.value = '正在生成遮罩...'
      
      try {
        // 生成遮罩
        const mask = await maskGenerator.generateMaskFromSelection(
          selection,
          currentImage.value.width,
          currentImage.value.height
        )
        
        processingMessage.value = '正在执行局部重绘...'
        
        // 调用API
        const result = await executeInpaintingAPI(currentImage.value, mask, parameters)
        
        // 更新图像
        if (result.success) {
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
    const loadImageFromUrl = (url) => {
      fabric.Image.fromURL(url, (img) => {
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
      })
    }
    
    // API调用函数（占位符）
    const executeInpaintingAPI = async (image, mask, params) => {
      // TODO: 实现实际的千问编辑API调用
      console.log('调用千问编辑API:', {
        prompt: params.prompt
      })
      
      return new Promise((resolve) => {
        setTimeout(() => {
          resolve({
            success: true,
            imageUrl: image.toDataURL()
          })
        }, 2000)
      })
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
    onMounted(() => {
      nextTick(() => {
        initCanvas()
      })
    })
    
    onUnmounted(() => {
      if (canvas.value) {
        canvas.value.dispose()
      }
    })
    
    // 处理文件上传事件
    const handleFileUpload = (file) => {
      console.log('File uploaded:', file)
      loadImage(file)
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
      testImageLoad
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
