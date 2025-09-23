<template>
  <div class="inpainting-canvas">
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
      default: 20
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
  emits: ['inpainting-complete', 'processing-start', 'processing-end', 'zoom-changed'],
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
    
    // 获取固定的画布尺寸
    const getCanvasSize = () => {
      return { width: 600, height: 600 }
    }
    
    // 计算图片适应画布的缩放比例
    const calculateImageScale = (imgWidth, imgHeight, canvasWidth, canvasHeight) => {
      // 高度适配画布，宽度自适应
      // 使用高度比例，让图片高度填满画布
      return canvasHeight / imgHeight
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
        if (props.currentTool === 'brush') {
          startBrushDrawing(e)
        } else if (props.currentTool === 'eraser') {
          startErasing(e)
        }
      })
      
      // 鼠标移动
      canvas.value.on('mouse:move', (e) => {
        if (isDrawing.value) {
          if (props.currentTool === 'brush') {
            continueBrushDrawing(e)
          } else if (props.currentTool === 'eraser') {
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
      if (props.currentTool === 'brush' && brushPath.value.length >= 2) {
        createBrushObjects()
      }
      
      brushPath.value = []
    }
    
    // 创建画笔对象
    const createBrushObjects = () => {
      const radius = props.brushSize / 2
      
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
        strokeWidth: props.brushSize,
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
      const radius = props.brushSize / 2
      
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
      
      // 创建临时画布
      const tempCanvas = document.createElement('canvas')
      tempCanvas.width = originalWidth
      tempCanvas.height = originalHeight
      const tempCtx = tempCanvas.getContext('2d')
      
      // 填充白色背景
      tempCtx.fillStyle = 'rgba(255, 255, 255, 1.0)'
      tempCtx.fillRect(0, 0, originalWidth, originalHeight)
      
      // 计算缩放比例
      const scaleX = originalWidth / (currentImage.value.width * currentImage.value.scaleX)
      const scaleY = originalHeight / (currentImage.value.height * currentImage.value.scaleY)
      
      // 绘制遮罩区域（透明）
      tempCtx.globalCompositeOperation = 'destination-out'
      tempCtx.fillStyle = 'rgba(255, 255, 255, 1.0)'
      
      drawnObjects.forEach(obj => {
        if (obj.type === 'circle') {
          const imageBounds = currentImage.value.getBoundingRect()
          const imageLeft = imageBounds.left
          const imageTop = imageBounds.top
          
          const relativeLeft = obj.left - imageLeft
          const relativeTop = obj.top - imageTop
          
          const originalLeft = relativeLeft * scaleX
          const originalTop = relativeTop * scaleY
          const originalRadius = obj.radius * scaleY // 使用高度缩放比例，与图像缩放逻辑保持一致
          
          tempCtx.beginPath()
          tempCtx.arc(originalLeft, originalTop, originalRadius, 0, 2 * Math.PI)
          tempCtx.fill()
        }
      })
      
      return tempCanvas.toDataURL('image/png')
    }
    
    // 执行局部重绘
    const executeInpainting = async () => {
      if (!currentImage.value) {
        throw new Error('没有图像')
      }
      
      const drawnObjects = canvas.value.getObjects().filter(obj => 
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
        
        // 调用API
        const API_BASE = 'http://localhost:9000'
        
        const result = await new Promise((resolve, reject) => {
          executeQwenEdit(
            props.originalImageFile,
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
                
                let imageUrl = null
                if (statusData.result) {
                  if (statusData.result.direct_urls && statusData.result.direct_urls.length > 0) {
                    imageUrl = statusData.result.direct_urls[0]
                  } else if (statusData.result.image_urls && statusData.result.image_urls.length > 0) {
                    imageUrl = statusData.result.image_urls[0]
                  }
                }
                
                if (imageUrl && imageUrl.startsWith('/')) {
                  imageUrl = API_BASE + imageUrl
                }
                
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
          
          // 通知父组件
          emit('inpainting-complete', {
            resultImageUrl: result.imageUrl,
            maskDataUrl: result.maskDataUrl,
            prompt: props.prompt
          })
        } else {
          throw new Error('局部重绘失败')
        }
        
      } catch (error) {
        console.error('局部重绘错误:', error)
        throw error
      } finally {
        isProcessing.value = false
        processingMessage.value = ''
        emit('processing-end')
      }
    }
    
    // 加载结果图像
    const loadResultImage = async (imageUrl) => {
      return new Promise((resolve, reject) => {
        fabric.Image.fromURL(imageUrl, (img) => {
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
            resolve()
          } else {
            reject(new Error('没有当前图像'))
          }
        })
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
      } else {
        console.error('❌ InpaintingCanvas: 无法识别的图像数据格式', imageData)
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
    
    // 暴露方法给父组件
    return {
      canvasElement,
      canvasWrapper,
      currentImage,
      isProcessing,
      processingMessage,
      currentZoom,
      executeInpainting,
      clearDrawing,
      applyZoom,
      zoomIn,
      zoomOut,
      zoomFit,
      zoom100
    }
  }
}
</script>

<style scoped>
.inpainting-canvas {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 0;
  overflow: hidden;
  min-height: 0;
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
