<template>
  <div class="inpainting-canvas">
    <!-- 局部重绘工具栏 -->
    <div class="inpainting-toolbar">
      <div class="toolbar-left">
        <!-- 空区域 -->
      </div>

      <div class="toolbar-center">
        <!-- 画笔工具 -->
        <div class="tool-group">
          <button 
            class="tool-btn brush" 
            :class="{ active: currentDrawingTool === 'brush' }"
            @click="handleDrawingToolChange('brush')"
            title="画笔"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M20.71,4.63L19.37,3.29C19,2.9 18.35,2.9 17.96,3.29L9,12.25L11.75,15L20.71,6.04C21.1,5.65 21.1,5 20.71,4.63M7,14A3,3 0 0,0 4,17C4,18.31 2.84,19 2,19C2.92,20.22 4.5,21 6,21A4,4 0 0,0 10,17A3,3 0 0,0 7,14Z"/>
            </svg>
          </button>
          <button 
            class="tool-btn eraser" 
            :class="{ active: currentDrawingTool === 'eraser' }"
            @click="handleDrawingToolChange('eraser')"
            title="橡皮擦"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M16.24,3.56L21.19,8.5C21.97,9.29 21.97,10.55 21.19,11.34L12,20.53C10.44,22.09 7.91,22.09 6.34,20.53L2.81,17C2.03,16.21 2.03,14.95 2.81,14.16L13.41,3.56C14.2,2.78 15.46,2.78 16.24,3.56M4.22,15.58L7.76,19.11C8.54,19.9 9.8,19.9 10.59,19.11L14.12,15.58L9.17,10.63L4.22,15.58Z"/>
            </svg>
          </button>
        </div>

        <!-- 笔刷大小控制 -->
        <div class="brush-size-control">
          <input
            :value="currentBrushSize"
            type="range"
            min="5"
            max="100"
            step="5"
            class="brush-size-slider"
            @input="handleBrushSizeChange"
          />
          <span class="size-text">{{ currentBrushSize }}px</span>
        </div>

        <!-- 重置按钮 -->
        <div class="reset-control">
          <button 
            class="tool-btn reset" 
            @click="handleResetDrawing"
            title="重置绘制"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 5V1L7 6l5 5V7c3.31 0 6 2.69 6 6s-2.69 6-6 6-6-2.69-6-6H4c0 4.42 3.58 8 8 8s8-3.58 8-8-3.58-8-8-8z"/>
            </svg>
          </button>
        </div>
      </div>

      <div class="toolbar-right">
        <button class="toolbar-btn" @click="exitInpainting" title="退出局部重绘">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
          </svg>
        </button>
      </div>
    </div>

    <div class="canvas-wrapper" ref="canvasWrapper">
      <canvas 
        ref="canvasElement" 
        class="inpainting-canvas-element"
      ></canvas>
      
      <!-- 处理状态 -->
      <div v-if="isProcessing" class="processing-overlay">
        <div class="processing-spinner"></div>
        <p>{{ processingMessage }}</p>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import * as fabric from 'fabric'
import { executeQwenEdit } from '../services/imageService.js'

export default {
  name: 'InpaintingCanvas',
  props: {
    originalImage: {
      type: Object,
      default: null
    },
    originalImageFile: {
      type: File,
      default: null
    },
    prompt: {
      type: String,
      default: ''
    },
    brushSize: {
      type: Number,
      default: 50
    },
    currentTool: {
      type: String,
      default: 'brush'
    },
    zoomLevel: {
      type: Number,
      default: 1
    }
  },
  emits: ['inpainting-complete', 'processing-start', 'processing-end', 'zoom-changed', 'exit-inpainting'],
  setup(props, { emit }) {
    const canvasElement = ref(null)
    const canvasWrapper = ref(null)
    const canvas = ref(null)
    const currentImage = ref(null)
    const isProcessing = ref(false)
    const processingMessage = ref('')
    const currentZoom = ref(1)
    
    // 绘制相关状态
    const isDrawing = ref(false)
    const brushPath = ref([])
    
    // 工具栏相关状态
    const currentDrawingTool = ref(props.currentTool || 'brush')
    const currentBrushSize = ref(props.brushSize || 50)
    
    // 获取固定的画布尺寸
    const getCanvasSize = () => {
      return { width: 600, height: 600 }
    }
    
    // 计算图片适应画布的缩放比例
    const calculateImageScale = (imgWidth, imgHeight, canvasWidth, canvasHeight) => {
      // 计算适应画布的缩放比例，确保图片完整显示
      const scaleX = canvasWidth / imgWidth
      const scaleY = canvasHeight / imgHeight
      // 使用较小的缩放比例，确保图片完全适应画布
      return Math.min(scaleX, scaleY)
    }
    
    // 初始化画布
    const initCanvas = () => {
      if (!canvasElement.value) return
      
      // 使用固定的画布尺寸
      const { width, height } = getCanvasSize()
      canvas.value = new fabric.Canvas(canvasElement.value, {
        width: width,
        height: height,
        backgroundColor: '#2a2a2a'
      })
      
      // 禁用默认选择
      canvas.value.selection = false
      
      // 设置事件监听
      setupCanvasEvents()
      
      console.log('局部重绘画布初始化完成')
      
      // 检查是否有待加载的图像
      if (props.originalImage) {
        console.log('🔄 画布初始化完成，检查是否有待加载的图像')
        nextTick(() => {
          loadOriginalImage(props.originalImage)
        })
      }
    }
    
    // 设置画布事件
    const setupCanvasEvents = () => {
      if (!canvas.value) return
      
      // 鼠标按下
      canvas.value.on('mouse:down', (e) => {
        if (currentDrawingTool.value === 'brush') {
          startBrushDrawing(e)
        } else if (currentDrawingTool.value === 'eraser') {
          startErasing(e)
        }
      })
      
      // 鼠标移动
      canvas.value.on('mouse:move', (e) => {
        if (isDrawing.value) {
          if (currentDrawingTool.value === 'brush') {
            continueBrushDrawing(e)
          } else if (currentDrawingTool.value === 'eraser') {
            continueErasing(e)
          }
        }
      })
      
      // 鼠标释放
      canvas.value.on('mouse:up', () => {
        if (isDrawing.value) {
          finishBrushDrawing()
        }
      })
    }
    
    // 开始画笔绘制
    const startBrushDrawing = (e) => {
      isDrawing.value = true
      brushPath.value = []
      
      const pointer = canvas.value.getPointer(e.e)
      brushPath.value.push({ x: pointer.x, y: pointer.y })
    }
    
    // 继续画笔绘制
    const continueBrushDrawing = (e) => {
      if (!isDrawing.value) return
      
      const pointer = canvas.value.getPointer(e.e)
      brushPath.value.push({ x: pointer.x, y: pointer.y })
      
      // 创建临时路径预览
      updateTempPath()
    }
    
    // 完成画笔绘制
    const finishBrushDrawing = () => {
      if (!isDrawing.value) return
      
      isDrawing.value = false
      
      // 清除临时路径
      const existingTemp = canvas.value.getObjects().find(obj => obj.tempPath)
      if (existingTemp) {
        canvas.value.remove(existingTemp)
      }
      
      // 创建绘制对象
      if (currentDrawingTool.value === 'brush' && brushPath.value.length >= 2) {
        createBrushObjects()
      }
      
      brushPath.value = []
    }
    
    // 创建画笔对象
    const createBrushObjects = () => {
      const radius = currentBrushSize.value / 2
      
      // 创建棋盘格图案
      const patternCanvas = document.createElement('canvas')
      patternCanvas.width = 20
      patternCanvas.height = 20
      const patternCtx = patternCanvas.getContext('2d')
      
      patternCtx.fillStyle = 'rgba(0, 100, 200, 1.0)'
      patternCtx.fillRect(0, 0, 10, 10)
      patternCtx.fillRect(10, 10, 10, 10)
      patternCtx.fillStyle = 'rgba(0, 100, 200, 0.6)'
      patternCtx.fillRect(10, 0, 10, 10)
      patternCtx.fillRect(0, 10, 10, 10)
      
      const pattern = new fabric.Pattern({
        source: patternCanvas,
        repeat: 'repeat'
      })
      
      // 创建圆形对象
      for (let i = 0; i < brushPath.value.length - 1; i++) {
        const current = brushPath.value[i]
        const next = brushPath.value[i + 1]
        
        // 插值创建更平滑的路径
        const steps = Math.max(1, Math.floor(Math.sqrt(
          Math.pow(next.x - current.x, 2) + Math.pow(next.y - current.y, 2)
        ) / 2))
        
        for (let j = 0; j < steps; j++) {
          const t = j / steps
          const x = current.x + (next.x - current.x) * t
          const y = current.y + (next.y - current.y) * t
          
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
            isDrawnMask: true
          })
          
          canvas.value.add(circle)
        }
      }
      
      canvas.value.renderAll()
    }
    
    // 更新临时路径
    const updateTempPath = () => {
      // 清除现有临时路径
      const existingTemp = canvas.value.getObjects().find(obj => obj.tempPath)
      if (existingTemp) {
        canvas.value.remove(existingTemp)
      }
      
      if (brushPath.value.length < 2) return
      
      // 创建新的临时路径
      const pathData = createPathFromPoints(brushPath.value)
      const tempPath = new fabric.Path(pathData, {
        stroke: 'rgba(0, 100, 200, 0.8)',
        strokeWidth: currentBrushSize.value,
        fill: '',
        selectable: false,
        evented: false,
        tempPath: true
      })
      
      canvas.value.add(tempPath)
      canvas.value.renderAll()
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
    
    // 开始擦除
    const startErasing = (e) => {
      isDrawing.value = true
      performErasing(e)
    }
    
    // 继续擦除
    const continueErasing = (e) => {
      if (!isDrawing.value) return
      performErasing(e)
    }
    
    // 执行擦除
    const performErasing = (e) => {
      const pointer = canvas.value.getPointer(e.e)
      const radius = currentBrushSize.value / 2
      
      // 获取所有绘制对象
      const objects = canvas.value.getObjects()
      const drawnObjects = objects.filter(obj => 
        obj !== currentImage.value && 
        obj.isDrawnMask === true
      )
      
      // 检查哪些对象与擦除区域相交
      drawnObjects.forEach(obj => {
        if (obj.type === 'circle') {
          const distance = Math.sqrt(
            Math.pow(obj.left + obj.radius - pointer.x, 2) + 
            Math.pow(obj.top + obj.radius - pointer.y, 2)
          )
          
          if (distance <= radius + obj.radius) {
            canvas.value.remove(obj)
          }
        }
      })
      
      canvas.value.renderAll()
    }
    
    // 生成遮罩图像
    const generateMaskImage = () => {
      if (!canvas.value || !currentImage.value) {
        throw new Error('画布或图像未加载')
      }
      
      const objects = canvas.value.getObjects()
      const drawnObjects = objects.filter(obj => 
        obj !== currentImage.value && 
        obj.isDrawnMask === true
      )
      
      if (drawnObjects.length === 0) {
        throw new Error('没有绘制的遮罩区域')
      }
      
      // 获取原始图像尺寸
      const originalWidth = currentImage.value._originalElement.width
      const originalHeight = currentImage.value._originalElement.height
      
      // 创建临时画布 - 确保尺寸与原始图像完全一致
      const tempCanvas = document.createElement('canvas')
      tempCanvas.width = originalWidth
      tempCanvas.height = originalHeight
      const tempCtx = tempCanvas.getContext('2d')
      
      // 确保画布尺寸正确
      console.log(`🖼️ 临时画布尺寸: ${tempCanvas.width}x${tempCanvas.height}`)
      console.log(`🖼️ 原始图像尺寸: ${originalWidth}x${originalHeight}`)
      
      // 1. 先绘制原图作为背景
      tempCtx.drawImage(currentImage.value._originalElement, 0, 0, originalWidth, originalHeight)
      
      // 2. 计算缩放比例 - 修正坐标计算
      // 获取图像在画布上的实际显示尺寸
      const displayWidth = currentImage.value.width * currentImage.value.scaleX
      const displayHeight = currentImage.value.height * currentImage.value.scaleY
      
      // 计算从显示尺寸到原始尺寸的缩放比例
      const scaleX = originalWidth / displayWidth
      const scaleY = originalHeight / displayHeight
      
      console.log('📐 缩放计算详情:')
      console.log(`   原始尺寸: ${originalWidth}x${originalHeight}`)
      console.log(`   显示尺寸: ${displayWidth}x${displayHeight}`)
      console.log(`   缩放比例: X=${scaleX.toFixed(3)}, Y=${scaleY.toFixed(3)}`)
      
      // 获取图像在画布上的实际位置
      const imageBounds = currentImage.value.getBoundingRect()
      
      console.log(`🖼️ 图像边界信息:`)
      console.log(`   getBoundingRect(): left=${imageBounds.left.toFixed(1)}, top=${imageBounds.top.toFixed(1)}`)
      console.log(`   getBoundingRect(): width=${imageBounds.width.toFixed(1)}, height=${imageBounds.height.toFixed(1)}`)
      console.log(`   图像实际尺寸: ${currentImage.value.width}x${currentImage.value.height}`)
      console.log(`   图像缩放: ${currentImage.value.scaleX}x${currentImage.value.scaleY}`)
      console.log(`   图像中心: (${currentImage.value.left.toFixed(1)}, ${currentImage.value.top.toFixed(1)})`)
      
      // 尝试使用Fabric.js的坐标转换功能
      // 将画布坐标转换为图像坐标
      try {
        const canvasTransform = canvas.value.getViewportTransform()
        console.log(`   画布变换矩阵: [${canvasTransform.map(v => v.toFixed(2)).join(', ')}]`)
      } catch (error) {
        console.log(`   画布变换矩阵: 无法获取 (${error.message})`)
      }
      
      // 计算图像在画布上的实际左上角坐标
      const imageCanvasLeft = imageBounds.left
      const imageCanvasTop = imageBounds.top
      
      console.log('📏 遮罩生成调试信息:')
      console.log(`   原始图像尺寸: ${originalWidth}x${originalHeight}`)
      console.log(`   绘制对象数量: ${drawnObjects.length}`)
      console.log(`   画布图像尺寸: ${currentImage.value.width}x${currentImage.value.height}`)
      console.log(`   画布图像缩放: ${currentImage.value.scaleX}x${currentImage.value.scaleY}`)
      console.log(`   画布图像角度: ${currentImage.value.angle}°`)
      console.log(`   画布图像翻转: 水平=${currentImage.value.flipX}, 垂直=${currentImage.value.flipY}`)
      console.log(`   显示尺寸: ${displayWidth}x${displayHeight}`)
      console.log(`   图像中心: (${currentImage.value.left.toFixed(1)}, ${currentImage.value.top.toFixed(1)})`)
      console.log(`   缩放比例: X=${scaleX.toFixed(3)}, Y=${scaleY.toFixed(3)}`)
      
      // 3. 在要重绘的区域绘制纯黑色（Alpha=0，完全透明）
      drawnObjects.forEach((obj, index) => {
        if (obj.type === 'circle') {
          // 遮罩对象在画布上的中心点
          const objCanvasCenterX = obj.left
          const objCanvasCenterY = obj.top
          
          // 计算遮罩对象相对于图像左上角的坐标
          
          // 计算遮罩对象相对于图像左上角的坐标
          const relativeLeft = objCanvasCenterX - imageCanvasLeft
          const relativeTop = objCanvasCenterY - imageCanvasTop
          
          // 计算从显示尺寸到原始尺寸的缩放比例
          // 使用图像边界的实际尺寸
          const displayToOriginalScaleX = originalWidth / imageBounds.width
          const displayToOriginalScaleY = originalHeight / imageBounds.height
          
          // 转换到原始图像坐标
          const originalLeft = relativeLeft * displayToOriginalScaleX
          const originalTop = relativeTop * displayToOriginalScaleY
          const originalRadius = obj.radius * Math.min(displayToOriginalScaleX, displayToOriginalScaleY)
          
          // 添加偏移修正 - 如果遮罩偏左偏上，尝试调整
          // 根据你的反馈，遮罩偏左偏上，我们添加一些偏移来修正
          const offsetX = 20 // X轴向右偏移，修正偏左问题
          const offsetY = 20 // Y轴向下偏移，修正偏上问题
          
          const finalOriginalLeft = originalLeft + offsetX
          const finalOriginalTop = originalTop + offsetY
          
          console.log(`🎯 遮罩对象 ${index + 1}:`)
          console.log(`   画布中心: (${objCanvasCenterX.toFixed(1)}, ${objCanvasCenterY.toFixed(1)}), 半径: ${obj.radius.toFixed(1)}`)
          console.log(`   图像左上角: (${imageCanvasLeft.toFixed(1)}, ${imageCanvasTop.toFixed(1)})`)
          console.log(`   相对图像左上角: (${relativeLeft.toFixed(1)}, ${relativeTop.toFixed(1)})`)
          console.log(`   显示到原始缩放: X=${displayToOriginalScaleX.toFixed(3)}, Y=${displayToOriginalScaleY.toFixed(3)}`)
          console.log(`   原始图像坐标: (${originalLeft.toFixed(1)}, ${originalTop.toFixed(1)}), 半径: ${originalRadius.toFixed(1)}`)
          console.log(`   修正后坐标: (${finalOriginalLeft.toFixed(1)}, ${finalOriginalTop.toFixed(1)})`)
          
          // 检查坐标是否在画布范围内
          if (finalOriginalLeft >= 0 && finalOriginalLeft <= originalWidth && 
              finalOriginalTop >= 0 && finalOriginalTop <= originalHeight) {
            // 使用globalCompositeOperation来创建透明区域
            tempCtx.globalCompositeOperation = 'destination-out'
            tempCtx.beginPath()
            tempCtx.arc(finalOriginalLeft, finalOriginalTop, originalRadius, 0, 2 * Math.PI)
            tempCtx.fill()
            tempCtx.globalCompositeOperation = 'source-over' // 重置合成模式
            console.log(`✅ 成功绘制透明遮罩对象 ${index + 1}`)
          } else {
            console.log(`❌ 遮罩对象 ${index + 1} 坐标超出画布范围，跳过绘制`)
          }
        }
      })
      
      // 验证生成的遮罩图像
      const dataUrl = tempCanvas.toDataURL('image/png')
      console.log(`✅ 遮罩生成完成，尺寸: ${tempCanvas.width}x${tempCanvas.height}`)
      console.log(`📊 遮罩DataURL长度: ${dataUrl.length} 字符`)
      console.log(`🎯 遮罩DataURL前缀: ${dataUrl.substring(0, 50)}...`)
      
      return dataUrl
    }
    
    // 执行局部重绘
    const executeInpainting = async () => {
      if (!currentImage.value) {
        throw new Error('没有图像')
      }
      
      // 检查是否有绘制的遮罩区域
      const objects = canvas.value.getObjects()
      const drawnObjects = objects.filter(obj => 
        obj !== currentImage.value && 
        obj.isDrawnMask === true
      )
      
      if (drawnObjects.length === 0) {
        throw new Error('请先绘制要重绘的区域')
      }
      
      isProcessing.value = true
      processingMessage.value = '正在执行局部重绘...'
      emit('processing-start')
      
      try {
        // 生成遮罩
        console.log('🎨 开始生成遮罩图像...')
        const maskDataUrl = generateMaskImage()
        console.log('✅ 遮罩图像生成成功，DataURL长度:', maskDataUrl.length)
        
        const maskFile = dataUrlToFile(maskDataUrl, 'mask.png')
        console.log('✅ 遮罩文件转换成功，文件大小:', maskFile.size, 'bytes')
        
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
        
        // 决定使用哪个图像作为重绘源
        // 如果当前画布上的图像是重绘结果（不是原始图像），则使用当前画布图像
        // 否则使用原始图像文件
        let sourceImageFile
        console.log('🔍 检查当前图像状态:')
        console.log('   currentImage.value:', currentImage.value ? '存在' : '不存在')
        console.log('   isInpaintingResult:', currentImage.value ? currentImage.value.isInpaintingResult : 'N/A')
        
        if (currentImage.value && currentImage.value.isInpaintingResult) {
          // 当前画布上是重绘结果，需要找到第一次重绘的结果文件
          console.log('🔄 需要找到第一次重绘的结果文件作为重绘源')
          
          // 从当前图像获取第一次重绘的结果文件路径
          const firstResultPath = currentImage.value.firstResultPath
          if (firstResultPath) {
            console.log('✅ 找到第一次重绘结果文件:', firstResultPath)
            // 从URL获取第一次重绘的结果文件
            sourceImageFile = await getFileFromUrl(firstResultPath)
          } else {
            console.log('⚠️ 没有找到第一次重绘结果文件路径，使用原始文件')
            sourceImageFile = props.originalImageFile
          }
        } else {
          // 当前画布上是原始图像，使用原始文件
          console.log('🔄 使用原始图像文件作为重绘源')
          sourceImageFile = props.originalImageFile
        }
        
        // 调用API - 使用相对路径，通过Vite代理
        const API_BASE = ''
        
        const result = await new Promise((resolve, reject) => {
          executeQwenEdit(
            sourceImageFile,
            maskFile,
            props.prompt,
            parameters,
            API_BASE,
            {
              onTaskCreated: (taskId) => {
                console.log(`✅ 任务已创建: ${taskId}`)
              },
              onProgress: (progress) => {
                console.log(`📊 进度: ${progress}%`)
              },
              onSuccess: async (statusData, taskId) => {
                console.log('✅ 局部重绘完成:', statusData)
                console.log('📋 statusData.result:', statusData.result)
                
                let imageUrl = null
                if (statusData.result) {
                console.log('📋 direct_urls:', statusData.result.direct_urls)
                console.log('📋 image_urls:', statusData.result.image_urls)
                console.log('📋 filenames:', statusData.result.filenames)
                
                // 优先使用第一个文件（主要结果），跳过可能的遮罩文件
                if (statusData.result.direct_urls && statusData.result.direct_urls.length > 0) {
                  // 查找主要结果文件（通常是第一个，文件名包含主要结果）
                  const mainResultIndex = statusData.result.filenames.findIndex(filename => 
                    filename.includes('00011') || filename.includes('main') || filename.includes('result')
                  )
                  const selectedIndex = mainResultIndex >= 0 ? mainResultIndex : 0
                  imageUrl = statusData.result.direct_urls[selectedIndex]
                  console.log('✅ 使用 direct_urls[', selectedIndex, ']:', imageUrl)
                  console.log('📋 对应的文件名:', statusData.result.filenames[selectedIndex])
                } else if (statusData.result.image_urls && statusData.result.image_urls.length > 0) {
                  imageUrl = statusData.result.image_urls[0]
                  console.log('✅ 使用 image_urls[0]:', imageUrl)
                } else {
                  console.log('❌ 没有找到图像URL')
                }
                } else {
                  console.log('❌ statusData.result 为空')
                }
                
                if (imageUrl && imageUrl.startsWith('/')) {
                  imageUrl = API_BASE + imageUrl
                  console.log('🔗 完整图像URL:', imageUrl)
                }
                
                console.log('📤 最终图像URL:', imageUrl)
                
                resolve({
                  success: true,
                  imageUrl: imageUrl,
                  maskDataUrl: maskDataUrl
                })
              },
              onError: (error) => {
                console.error('❌ 局部重绘失败:', error)
                reject(new Error(error))
              }
            }
          )
        })
        
        if (result.success) {
          // 加载新图像
          await loadResultImage(result.imageUrl)
          
          // 重绘成功后清除画布上的遮罩对象
          const objects = canvas.value.getObjects()
          const drawnObjects = objects.filter(obj => 
            obj !== currentImage.value && 
            obj.isDrawnMask === true
          )
          drawnObjects.forEach(obj => {
            canvas.value.remove(obj)
          })
          canvas.value.renderAll()
          console.log('🧹 重绘成功，已清除遮罩对象，数量:', drawnObjects.length)
          
          // 通知父组件
          emit('inpainting-complete', {
            resultImageUrl: result.imageUrl,
            maskDataUrl: result.maskDataUrl,
            prompt: props.prompt
          })
          
          // 只有成功加载图像后才重置处理状态
          isProcessing.value = false
          processingMessage.value = ''
          emit('processing-end')
        } else {
          throw new Error('局部重绘失败')
        }
        
      } catch (error) {
        console.error('局部重绘错误:', error)
        // 发生错误时也要重置处理状态
        isProcessing.value = false
        processingMessage.value = ''
        emit('processing-end')
        throw error
      }
    }
    
    // 加载结果图像
    const loadResultImage = async (imageUrl) => {
      console.log('🔄 开始加载结果图像:', imageUrl)
      return new Promise((resolve, reject) => {
        // 设置超时
        const timeout = setTimeout(() => {
          console.error('❌ 图像加载超时 (10秒)')
          reject(new Error('图像加载超时'))
        }, 10000)
        
        // 直接使用原生Image对象加载图像
        const img = new Image()
        img.crossOrigin = 'anonymous' // 设置跨域
        
        img.onload = () => {
          console.log('✅ 图像加载成功，开始创建Fabric.js对象')
          clearTimeout(timeout)
          
          try {
            // 手动创建Fabric.js图像对象
            const fabricImg = new fabric.Image(img, {
              left: 0,
              top: 0,
              selectable: false,
              evented: false
            })
            
            console.log('✅ Fabric.js图像对象创建成功:', fabricImg)
            
            if (currentImage.value) {
              // 获取当前图像的位置和缩放信息
              const currentLeft = currentImage.value.left
              const currentTop = currentImage.value.top
              const currentScaleX = currentImage.value.scaleX
              const currentScaleY = currentImage.value.scaleY
              
              console.log('📋 当前图像信息:', { currentLeft, currentTop, currentScaleX, currentScaleY })
              
              // 设置新图像的位置和缩放
              fabricImg.set({
                left: currentLeft,
                top: currentTop,
                scaleX: currentScaleX,
                scaleY: currentScaleY,
                selectable: false,
                evented: false,
                isInpaintingResult: true,  // 标记为重绘结果
                firstResultPath: imageUrl  // 保存第一次重绘的结果文件路径
              })
              
              // 移除旧图像，添加新图像
              canvas.value.remove(currentImage.value)
              canvas.value.add(fabricImg)
              // 图像顺序不重要，直接跳过sendToBack调用
              
              // 更新当前图像引用
              currentImage.value = fabricImg
              canvas.value.renderAll()
              
              console.log('✅ 重绘结果已回填到画板')
              resolve()
            } else {
              console.error('❌ 没有当前图像')
              reject(new Error('没有当前图像'))
            }
          } catch (error) {
            console.error('❌ 创建Fabric.js图像对象失败:', error)
            reject(error)
          }
        }
        
        img.onerror = (error) => {
          console.error('❌ 图像加载失败:', error)
          clearTimeout(timeout)
          reject(new Error('图像加载失败'))
        }
        
        console.log('🔄 开始加载图像:', imageUrl)
        img.src = imageUrl
      })
    }
    
    // 数据URL转文件
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
    
    // 从URL获取文件
    const getFileFromUrl = async (url) => {
      try {
        const response = await fetch(url)
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }
        const blob = await response.blob()
        const file = new File([blob], 'result_image.png', { type: blob.type })
        console.log('✅ 从URL获取文件成功:', file.name, file.size, '字节')
        return file
      } catch (error) {
        console.error('❌ 从URL获取文件失败:', error)
        throw error
      }
    }
    
    // 获取当前画布上的图像作为重绘源
    const getCurrentCanvasImage = async () => {
      if (!currentImage.value) {
        throw new Error('画布上没有图像')
      }
      
      return new Promise((resolve, reject) => {
        try {
          // 将当前图像转换为DataURL，使用高质量参数
          const dataURL = currentImage.value.toDataURL({
            format: 'png',
            quality: 1.0,
            multiplier: 2.0  // 提高分辨率
          })
          
          // 检查DataURL是否有效
          if (!dataURL || dataURL === 'data:,') {
            throw new Error('无法生成有效的图像数据')
          }
          
          // 转换为File对象
          const imageFile = dataUrlToFile(dataURL, 'current_canvas_image.png')
          
          // 检查文件大小
          if (imageFile.size === 0) {
            throw new Error('生成的图像文件为空')
          }
          
          console.log('✅ 获取当前画布图像成功')
          console.log('   文件大小:', imageFile.size, '字节')
          console.log('   文件类型:', imageFile.type)
          console.log('   文件名:', imageFile.name)
          
          resolve(imageFile)
        } catch (error) {
          console.error('❌ 获取当前画布图像失败:', error)
          reject(error)
        }
      })
    }
    
    
    
    // 清除绘制内容
    const clearDrawing = () => {
      if (!canvas.value) return
      
      const objects = canvas.value.getObjects()
      objects.forEach(obj => {
        if (obj !== currentImage.value && obj.isDrawnMask === true) {
          canvas.value.remove(obj)
        }
      })
      
      canvas.value.renderAll()
    }
    
    // 加载原始图像
    const loadOriginalImage = (imageData) => {
      if (!canvas.value || !imageData) {
        console.log('❌ InpaintingCanvas: 缺少画布或图像数据', { canvas: !!canvas.value, imageData })
        return
      }
      
      console.log('🔄 InpaintingCanvas: 开始加载图像', imageData)
      
      // 清除画布
      canvas.value.clear()
      
      // 创建图像对象
      let img
      
      if (imageData.image && imageData.image._originalElement) {
        // 从MainCanvas传递的Fabric.js图像对象
        console.log('📋 使用Fabric.js图像对象的_originalElement')
        img = new fabric.Image(imageData.image._originalElement, {
          left: 0,
          top: 0,
          selectable: false,
          evented: false
        })
      } else if (imageData.imageUrl) {
        // 从MainCanvas传递的图像URL
        console.log('📋 使用图像URL创建新图像')
        const imageElement = new Image()
        imageElement.src = imageData.imageUrl
        img = new fabric.Image(imageElement, {
          left: 0,
          top: 0,
          selectable: false,
          evented: false
        })
      } else if (imageData.url) {
        // 从生图详情页面传递的图像URL（新格式）
        console.log('📋 使用生图详情页面的图像URL创建新图像')
        const imageElement = new Image()
        imageElement.crossOrigin = 'anonymous'
        imageElement.onload = () => {
          console.log('📸 图片元素加载完成，尺寸:', imageElement.width, 'x', imageElement.height)
          const fabricImg = new fabric.Image(imageElement, {
            left: 0,
            top: 0,
            selectable: false,
            evented: false
          })
          addImageToCanvas(fabricImg)
        }
        imageElement.onerror = (error) => {
          console.error('❌ 图片加载失败:', error)
        }
        imageElement.src = imageData.url
        return // 异步加载，直接返回
      } else if (imageData.directUrl) {
        // 使用directUrl作为备选
        console.log('📋 使用directUrl创建新图像')
        const imageElement = new Image()
        imageElement.crossOrigin = 'anonymous'
        imageElement.onload = () => {
          console.log('📸 图片元素加载完成，尺寸:', imageElement.width, 'x', imageElement.height)
          const fabricImg = new fabric.Image(imageElement, {
            left: 0,
            top: 0,
            selectable: false,
            evented: false
          })
          addImageToCanvas(fabricImg)
        }
        imageElement.onerror = (error) => {
          console.error('❌ 图片加载失败:', error)
        }
        imageElement.src = imageData.directUrl
        return // 异步加载，直接返回
      } else {
        console.error('❌ InpaintingCanvas: 无法识别的图像数据格式', imageData)
        return
      }
      
      // 对于同步加载的图片（Fabric.js对象或imageUrl），直接处理
      addImageToCanvas(img)
    }
    
    // 添加图片到画布的通用方法
    const addImageToCanvas = (img) => {
      if (!canvas.value || !img) {
        console.log('❌ InpaintingCanvas: 缺少画布或图像对象')
        return
      }
      
      // 获取画布尺寸
      const { width: canvasWidth, height: canvasHeight } = getCanvasSize()
      
      // 计算图片适应画布的缩放比例
      const scale = calculateImageScale(img.width, img.height, canvasWidth, canvasHeight)
      
      // 设置图片的缩放比例
      img.scale(scale)
      
      // 添加图像
      canvas.value.add(img)
      canvas.value.sendObjectToBack(img)
      
      // 居中显示
      canvas.value.centerObject(img)
      canvas.value.renderAll()
      
      currentImage.value = img
      console.log('✅ InpaintingCanvas: 图像加载完成，尺寸:', img.width, 'x', img.height)
      
      // 图像加载完成后，设置为100%缩放，让图片按原始缩放比例显示
      setTimeout(() => {
        currentZoom.value = 1
        applyZoom(1)
        console.log('✅ InpaintingCanvas: 已设置为100%缩放显示')
      }, 100)
    }
    
    // 生命周期
    onMounted(() => {
      nextTick(() => {
        initCanvas()
      })
      
      // 监听执行事件
      window.addEventListener('execute-inpainting', handleExecuteRequest)
    })
    
    onUnmounted(() => {
      if (canvas.value) {
        canvas.value.dispose()
      }
      
      // 清理事件监听器
      window.removeEventListener('execute-inpainting', handleExecuteRequest)
    })
    
    // 处理执行请求
    const handleExecuteRequest = async () => {
      console.log('InpaintingCanvas: 收到执行请求')
      try {
        await executeInpainting()
      } catch (error) {
        console.error('InpaintingCanvas: 执行失败:', error)
      }
    }
    
    // 监听props变化
    watch(() => props.originalImage, (newImage) => {
      console.log('🔄 InpaintingCanvas: 检测到originalImage变化', newImage)
      if (newImage && canvas.value) {
        console.log('✅ 画布已初始化，立即加载图像')
        loadOriginalImage(newImage)
      } else if (newImage && !canvas.value) {
        console.log('⏳ 画布未初始化，等待初始化完成')
        // 画布未初始化，等待初始化完成
        nextTick(() => {
          if (canvas.value) {
            console.log('✅ 画布初始化完成，现在加载图像')
            loadOriginalImage(newImage)
          }
        })
      }
    }, { immediate: true })
    
    // 应用缩放到所有canvas元素
    const applyZoom = (zoom) => {
      if (!canvasWrapper.value) return
      
      // 延迟执行，确保Fabric.js已经初始化完成
      nextTick(() => {
        // 获取所有相关的canvas元素
        const lowerCanvas = canvasWrapper.value.querySelector('.lower-canvas')
        const upperCanvas = canvasWrapper.value.querySelector('.upper-canvas')
        
        console.log('🔍 查找canvas元素:', { lowerCanvas, upperCanvas, zoom })
        
        // 应用缩放
        const transform = `scale(${zoom})`
        if (lowerCanvas) {
          lowerCanvas.style.transform = transform
          lowerCanvas.style.transformOrigin = 'center center'
          console.log('✅ 应用缩放到lower-canvas:', transform)
        }
        if (upperCanvas) {
          upperCanvas.style.transform = transform
          upperCanvas.style.transformOrigin = 'center center'
          console.log('✅ 应用缩放到upper-canvas:', transform)
        }
      })
    }
    
    // 缩放相关方法
    const zoomIn = () => {
      console.log('🔍 InpaintingCanvas zoomIn 被调用')
      const newZoom = Math.min(currentZoom.value * 1.2, 5) // 最大5倍
      currentZoom.value = newZoom
      applyZoom(newZoom)
      emit('zoom-changed', newZoom)
    }
    
    const zoomOut = () => {
      console.log('🔍 InpaintingCanvas zoomOut 被调用')
      const newZoom = Math.max(currentZoom.value / 1.2, 0.1) // 最小0.1倍
      currentZoom.value = newZoom
      applyZoom(newZoom)
      emit('zoom-changed', newZoom)
    }
    
    const zoomFit = () => {
      console.log('🔍 InpaintingCanvas zoomFit 被调用')
      if (!canvasWrapper.value || !currentImage.value) return
      
      const containerWidth = canvasWrapper.value.parentElement.clientWidth
      const containerHeight = canvasWrapper.value.parentElement.clientHeight
      const imageWidth = currentImage.value.width
      const imageHeight = currentImage.value.height
      
      const scaleX = containerWidth / imageWidth
      const scaleY = containerHeight / imageHeight
      const scale = Math.min(scaleX, scaleY) * 0.9 // 留一些边距
      
      currentZoom.value = scale
      applyZoom(scale)
      emit('zoom-changed', scale)
    }
    
    const zoom100 = () => {
      console.log('🔍 InpaintingCanvas zoom100 被调用')
      currentZoom.value = 1
      applyZoom(1)
      emit('zoom-changed', 1)
    }
    
    // 监听zoomLevel变化
    watch(() => props.zoomLevel, (newZoom) => {
      if (canvasWrapper.value) {
        currentZoom.value = newZoom
        applyZoom(newZoom)
      }
    })
    
    // 监听外部传入的画笔大小变化
    watch(() => props.brushSize, (newSize) => {
      if (newSize !== undefined) {
        currentBrushSize.value = newSize
      }
    })
    
    // 监听外部传入的当前工具变化
    watch(() => props.currentTool, (newTool) => {
      if (newTool !== undefined) {
        currentDrawingTool.value = newTool
      }
    })
    
    // 工具栏相关方法
    const handleDrawingToolChange = (tool) => {
      currentDrawingTool.value = tool
    }
    
    const handleBrushSizeChange = (event) => {
      currentBrushSize.value = parseInt(event.target.value)
    }
    
    const handleResetDrawing = () => {
      // 清除所有绘制对象，但保留原始图像
      if (canvas.value) {
        const objects = canvas.value.getObjects()
        const drawnObjects = objects.filter(obj => 
          obj !== currentImage.value && 
          (obj.tempPath || obj.isDrawnMask === true)
        )
        
        drawnObjects.forEach(obj => {
          canvas.value.remove(obj)
        })
        
        canvas.value.renderAll()
        console.log('✅ 已重置所有绘制结果，清除对象数量:', drawnObjects.length)
      }
    }
    
    const exitInpainting = () => {
      emit('exit-inpainting')
    }
    
    // 暴露方法给父组件
    return {
      canvasElement,
      canvasWrapper,
      currentImage,
      isProcessing,
      processingMessage,
      currentZoom,
      currentDrawingTool,
      currentBrushSize,
      executeInpainting,
      clearDrawing,
      applyZoom,
      zoomIn,
      zoomOut,
      zoomFit,
      zoom100,
      handleDrawingToolChange,
      handleBrushSizeChange,
      handleResetDrawing,
      exitInpainting
    }
  }
}
</script>

<style scoped>
.inpainting-canvas {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 0;
  overflow: hidden;
  min-height: 0;
}

/* 局部重绘工具栏样式 */
.inpainting-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  background: #2a2a2a;
  border-bottom: 1px solid #333;
  color: white;
  min-height: 48px;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.toolbar-center {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.tool-group {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px;
  background: #333;
  border-radius: 6px;
  border: 1px solid #444;
}

.tool-btn {
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

.tool-btn:hover {
  background: #444;
  color: #fff;
}

.tool-btn.active {
  background: #1890ff;
  color: #fff;
}

.brush-size-control {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 8px;
  background: #333;
  border-radius: 6px;
  border: 1px solid #444;
}

.brush-size-slider {
  width: 80px;
  height: 4px;
  background: #555;
  border-radius: 2px;
  outline: none;
  cursor: pointer;
}

.brush-size-slider::-webkit-slider-thumb {
  appearance: none;
  width: 16px;
  height: 16px;
  background: #1890ff;
  border-radius: 50%;
  cursor: pointer;
}

.brush-size-slider::-moz-range-thumb {
  width: 16px;
  height: 16px;
  background: #1890ff;
  border-radius: 50%;
  cursor: pointer;
  border: none;
}

.size-text {
  color: #ccc;
  font-size: 12px;
  min-width: 35px;
}

.reset-control {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px;
  background: #333;
  border-radius: 6px;
  border: 1px solid #444;
}

.tool-btn.reset {
  color: #ff6b6b;
}

.tool-btn.reset:hover {
  background: #ff6b6b;
  color: #fff;
}

.toolbar-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: #333;
  border: 1px solid #444;
  border-radius: 4px;
  color: white;
  cursor: pointer;
  transition: all 0.2s;
}

.toolbar-btn:hover:not(:disabled) {
  background: #444;
  border-color: #555;
}

.toolbar-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.canvas-wrapper {
  position: relative;
  border: 2px solid #333;
  background: #2a2a2a;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
  max-width: 100%;
  max-height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
}

.inpainting-canvas-element {
  display: block;
  border-radius: 6px;
  transform-origin: center center;
  transition: transform 0.2s ease;
}

.processing-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  color: white;
  border-radius: 6px;
}

.processing-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #333;
  border-top: 4px solid #007bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>
