<template>
  <div class="outpainting-canvas-container">
    <!-- 调试信息 -->
    <div v-if="false" style="position: absolute; top: 0; left: 0; background: rgba(255,0,0,0.8); color: white; padding: 4px; font-size: 12px; z-index: 1000;">
      OutpaintingCanvas 已渲染 - 模式: {{ currentMode || '未知' }}
    </div>
    <!-- 比例设置工具栏 -->
    <div class="aspect-ratio-toolbar">
      <div class="toolbar-left">
        <!-- 缩放功能已移除，等待整体缩放实现 -->
      </div>
      
      <div class="aspect-ratio-controls">
        <button 
          class="aspect-btn" 
          :class="{ active: currentAspectRatio === 'original' }"
          @click="setAspectRatio('original')"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <path d="M3 3h18v18H3V3zm2 2v14h14V5H5z"/>
          </svg>
          原始比例
        </button>
        
        <button 
          class="aspect-btn" 
          :class="{ active: currentAspectRatio === '1:1' }"
          @click="setAspectRatio('1:1')"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <path d="M3 3h18v18H3V3zm2 2v14h14V5H5z"/>
          </svg>
          1:1
        </button>
        
        <button 
          class="aspect-btn" 
          :class="{ active: currentAspectRatio === '3:4' }"
          @click="setAspectRatio('3:4')"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <path d="M3 3h18v18H3V3zm2 2v14h14V5H5z"/>
          </svg>
          3:4
        </button>
        
        <button 
          class="aspect-btn" 
          :class="{ active: currentAspectRatio === '4:3' }"
          @click="setAspectRatio('4:3')"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <path d="M3 3h18v18H3V3zm2 2v14h14V5H5z"/>
          </svg>
          4:3
        </button>
        
        <button 
          class="aspect-btn" 
          :class="{ active: currentAspectRatio === '9:16' }"
          @click="setAspectRatio('9:16')"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <path d="M3 3h18v18H3V3zm2 2v14h14V5H5z"/>
          </svg>
          9:16
        </button>
        
        <button 
          class="aspect-btn" 
          :class="{ active: currentAspectRatio === '16:9' }"
          @click="setAspectRatio('16:9')"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <path d="M3 3h18v18H3V3zm2 2v14h14V5H5z"/>
          </svg>
          16:9
        </button>
      </div>
      
      <div class="toolbar-right">
        <button class="toolbar-btn" @click="resetOutpainting" title="重置扩图区域">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 5V1L7 6l5 5V7c3.31 0 6 2.69 6 6s-2.69 6-6 6-6-2.69-6-6H4c0 4.42 3.58 8 8 8s8-3.58 8-8-3.58-8-8-8z"/>
          </svg>
          重置
        </button>
        <button class="toolbar-btn" @click="exitOutpainting">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
          </svg>
        </button>
      </div>
    </div>

    <!-- 主画布区域 -->
    <div class="canvas-wrapper" ref="canvasWrapper">
      <!-- 图片容器 - 用于扩图区域定位 -->
      <div 
        class="image-container" 
        ref="imageContainer"
        :style="imageContainerStyle"
      >
        <canvas 
          ref="canvasRef" 
          class="outpainting-canvas"
          @mousedown="handleMouseDown"
          @mousemove="handleMouseMove"
          @mouseup="handleMouseUp"
        ></canvas>
        
        <!-- 扩图区域指示器 -->
        <div 
          v-if="showExpansionArea"
          class="expansion-area"
          :style="expansionAreaStyle"
          @mousedown="handleMouseDown"
        >
          <div class="expansion-info">
            <span>{{ realExpansionWidth }} × {{ realExpansionHeight }}</span>
          </div>
          <!-- 调整大小手柄 -->
          <div class="resize-handle resize-handle-n"></div>
          <div class="resize-handle resize-handle-s"></div>
          <div class="resize-handle resize-handle-e"></div>
          <div class="resize-handle resize-handle-w"></div>
          <div class="resize-handle resize-handle-nw"></div>
          <div class="resize-handle resize-handle-ne"></div>
          <div class="resize-handle resize-handle-sw"></div>
          <div class="resize-handle resize-handle-se"></div>
        </div>
      </div>
      
      <!-- 上传按钮 - 当没有图像时显示 -->
      <div v-if="!currentImage" class="upload-overlay">
        <div class="upload-content">
          <div class="upload-icon">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="currentColor">
              <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z"/>
            </svg>
          </div>
          <h3>上传图片开始扩图</h3>
          <p>拖拽图片到此处或点击上传</p>
          <button class="upload-btn" @click="handleUploadClick">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z"/>
            </svg>
            选择图片
          </button>
        </div>
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

    <!-- 处理状态覆盖层 -->
    <div v-if="isProcessing" class="processing-overlay">
      <div class="processing-content">
        <div class="spinner"></div>
        <p>{{ processingMessage }}</p>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, computed, watch, nextTick } from 'vue'

export default {
  name: 'OutpaintingCanvas',
  props: {
    originalImage: {
      type: [String, Object],
      default: ''
    },
    originalImageFile: {
      type: File,
      default: null
    },
    prompt: {
      type: String,
      default: ''
    },
    zoomLevel: {
      type: Number,
      default: 1
    }
  },
  emits: [
    'outpainting-complete',
    'processing-start', 
    'processing-end',
    'zoom-changed',
    'file-upload',
    'exit-outpainting'
  ],
  setup(props, { emit }) {
    // 画布引用
    const canvasRef = ref(null)
    const canvasWrapper = ref(null)
    const imageContainer = ref(null)
    const fileInput = ref(null)
    
    // 画布状态
    const canvas = ref(null)
    const currentImage = ref(null)
    
    // 扩图区域状态
    const showExpansionArea = ref(false)
    const expansionX = ref(0)
    const expansionY = ref(0)
    const expansionWidth = ref(512)
    const expansionHeight = ref(512)
    const currentAspectRatio = ref('original')
    const originalImageSize = ref({ width: 0, height: 0 })
    
    // 图像缩放比例
    const imageScaleX = ref(1)
    const imageScaleY = ref(1)
    
    // 拖拽状态
    const isDragging = ref(false)
    const dragStart = ref({ x: 0, y: 0 })
    
    // 调整大小状态
    const isResizing = ref(false)
    const resizeHandle = ref('')
    const resizeStart = ref({ x: 0, y: 0, width: 0, height: 0 })
    
    // 处理状态
    const isProcessing = ref(false)
    const processingMessage = ref('')
    
    // 历史记录
    const history = ref([])
    const historyIndex = ref(-1)
    
    // 加载状态
    const isImageLoaded = ref(false)
    
    // 计算属性
    const canUndo = computed(() => historyIndex.value > 0)
    const canRedo = computed(() => historyIndex.value < history.value.length - 1)
    
    // 计算真实的像素尺寸（无缩放）
    const realExpansionWidth = computed(() => {
      return expansionWidth.value
    })
    
    const realExpansionHeight = computed(() => {
      return expansionHeight.value
    })
    
    // 图片容器样式 - 与图片尺寸相同
    const imageContainerStyle = computed(() => {
      if (!originalImageSize.value.width || !originalImageSize.value.height) {
        return {}
      }
      return {
        width: `${originalImageSize.value.width}px`,
        height: `${originalImageSize.value.height}px`,
        position: 'relative'
      }
    })
    
    const expansionAreaStyle = computed(() => {
      return {
        left: `${expansionX.value}px`,
        top: `${expansionY.value}px`,
        width: `${expansionWidth.value}px`,
        height: `${expansionHeight.value}px`
      }
    })
    
    // 初始化画布
    const initCanvas = () => {
      if (!canvasRef.value || !canvasWrapper.value) return
      
      canvas.value = canvasRef.value
      
      // 不设置任何默认尺寸，等待图片加载后根据图片尺寸设置
      console.log('🎨 画布初始化完成，等待图片加载')
    }
    
    // 根据图片尺寸设置画布大小（无缩放）
    const resizeCanvasForImage = (img) => {
      if (!canvas.value || !canvasWrapper.value) {
        console.log('⚠️ resizeCanvasForImage: canvas或canvasWrapper未准备好')
        return
      }
      
      console.log('🔄 resizeCanvasForImage 开始执行（无缩放）:', {
        imgSize: { width: img.width, height: img.height },
        currentCanvas: { width: canvas.value.width, height: canvas.value.height }
      })
      
      // 直接使用图片原始尺寸，不进行缩放
      const canvasWidth = img.width
      const canvasHeight = img.height
      
      // 设置缩放比例为1（无缩放）
      imageScaleX.value = 1
      imageScaleY.value = 1
      
      // 更新画布尺寸
      canvas.value.width = canvasWidth
      canvas.value.height = canvasHeight
      canvas.value.style.width = `${canvasWidth}px`
      canvas.value.style.height = `${canvasHeight}px`
      
      // 重新绘制背景
      const ctx = canvas.value.getContext('2d')
      ctx.fillStyle = '#1a1a1a'
      ctx.fillRect(0, 0, canvasWidth, canvasHeight)
      
      console.log('🎨 画布尺寸设置（无缩放）:', {
        image: { width: img.width, height: img.height },
        canvas: { width: canvasWidth, height: canvasHeight }
      })
    }
    
    // 加载原始图像
    const loadOriginalImage = async () => {
      console.log('🖼️ loadOriginalImage 被调用:', {
        originalImage: props.originalImage,
        originalImageFile: props.originalImageFile,
        isImageLoaded: isImageLoaded.value
      })
      
      // 检查是否需要重新加载图片
      // 如果图片已经加载过，但props没有变化，则跳过重复加载
      if (isImageLoaded.value && currentImage.value) {
        // 检查当前图片是否与props中的图片一致
        const currentImageUrl = currentImage.value.imageUrl || currentImage.value.src
        let propsImageUrl = ''
        
        if (props.originalImageFile && props.originalImageFile instanceof File) {
          propsImageUrl = URL.createObjectURL(props.originalImageFile)
        } else if (props.originalImage) {
          if (typeof props.originalImage === 'string') {
            propsImageUrl = props.originalImage
          } else if (props.originalImage.imageUrl) {
            propsImageUrl = props.originalImage.imageUrl
          } else if (props.originalImage.url) {
            propsImageUrl = props.originalImage.url
          }
        }
        
        // 如果图片URL相同，跳过重复加载
        if (currentImageUrl && propsImageUrl && currentImageUrl === propsImageUrl) {
          console.log('⏭️ 图片未变化，跳过重复加载')
          return Promise.resolve(currentImage.value.img)
        } else {
          console.log('🔄 检测到图片变化，需要重新加载:', {
            currentImageUrl: currentImageUrl?.substring(0, 50) + '...',
            propsImageUrl: propsImageUrl?.substring(0, 50) + '...'
          })
        }
      }
      
      // 检查是否有有效的图片数据
      const hasImageData = props.originalImage || props.originalImageFile
      if (!hasImageData) {
        console.log('⚠️ 没有图片数据，跳过加载')
        return Promise.reject(new Error('没有图片数据'))
      }
      
      console.log('🔍 检查图片数据类型:', {
        originalImage: typeof props.originalImage,
        originalImageFile: typeof props.originalImageFile,
        originalImageValue: props.originalImage,
        originalImageFileValue: props.originalImageFile
      })
      
      try {
        let imageUrl = ''
        
        // 处理不同类型的originalImage
        if (props.originalImageFile) {
          if (props.originalImageFile instanceof File) {
            imageUrl = URL.createObjectURL(props.originalImageFile)
          } else if (typeof props.originalImageFile === 'string') {
            // 如果是字符串，可能是文件名，尝试构造URL
            imageUrl = `/uploads/${props.originalImageFile}`
          }
        } else if (props.originalImage) {
          if (typeof props.originalImage === 'string') {
            imageUrl = props.originalImage
          } else if (props.originalImage.imageUrl) {
            imageUrl = props.originalImage.imageUrl
          } else if (props.originalImage.url) {
            imageUrl = props.originalImage.url
          } else if (props.originalImage === true) {
            // 如果originalImage是true，说明有图片数据但需要从其他地方获取URL
            console.log('⚠️ originalImage是true，需要其他方式获取图片URL')
            return
          }
        }
        
        console.log('🔗 最终图片URL:', imageUrl)
        
        if (!imageUrl) {
          return Promise.reject(new Error('没有有效的图片URL'))
        }
        
        const img = new Image()
        
        // 返回Promise，等待图片加载完成
        return new Promise((resolve, reject) => {
          img.onload = () => {
            console.log('📸 图片加载完成，开始重新计算画布尺寸:', {
              imageSize: { width: img.width, height: img.height },
              currentCanvas: { width: canvas.value?.width, height: canvas.value?.height }
            })
            
            // 根据图片尺寸重新计算画布大小
            resizeCanvasForImage(img)
            drawImageToCanvas(img)
            
            // 只有在扩图区域未初始化时才设置扩图区域
            if (expansionWidth.value === 512 && expansionHeight.value === 512) {
              console.log('🔄 loadOriginalImage: 扩图区域未初始化，设置扩图区域为图片尺寸')
              setupExpansionArea(img)
            } else {
              console.log('✅ loadOriginalImage: 扩图区域已调整，保持用户拖拽结果:', {
                width: expansionWidth.value,
                height: expansionHeight.value
              })
              // 确保扩图区域显示
              showExpansionArea.value = true
            }
            
            saveToHistory()
            
            // 标记图片已加载
            isImageLoaded.value = true
            
            resolve(img)
          }
          img.onerror = (error) => {
            console.error('图像加载失败:', error)
            reject(error)
          }
          img.src = imageUrl
        })
      } catch (error) {
        console.error('加载图像失败:', error)
      }
    }
    
    // 绘制图像到画布（无缩放）
    const drawImageToCanvas = (img) => {
      if (!canvas.value) return
      
      const ctx = canvas.value.getContext('2d')
      const canvasWidth = canvas.value.width
      const canvasHeight = canvas.value.height
      
      // 清除画布
      ctx.fillStyle = '#1a1a1a'
      ctx.fillRect(0, 0, canvasWidth, canvasHeight)
      
      // 直接绘制图像到画布左上角，不进行缩放
      ctx.drawImage(img, 0, 0, img.width, img.height)
      
      // 保存图像信息（使用原始尺寸）
      currentImage.value = {
        img,
        x: 0,
        y: 0,
        width: img.width,
        height: img.height,
        originalWidth: img.width,
        originalHeight: img.height,
        scale: 1
      }
      
      console.log('🎨 图片绘制完成（无缩放）:', {
        original: { width: img.width, height: img.height },
        canvas: { width: canvasWidth, height: canvasHeight },
        drawArea: { x: 0, y: 0, width: img.width, height: img.height }
      })
    }
    
    // 设置扩图区域
    const setupExpansionArea = (img) => {
      if (!currentImage.value || !canvas.value) return
      
      // 保存原始图像尺寸
      originalImageSize.value = { width: img.width, height: img.height }
      
      // 初始扩图区域与图片位置和尺寸相同（无缩放）
      expansionX.value = 0
      expansionY.value = 0
      expansionWidth.value = img.width
      expansionHeight.value = img.height
      
      console.log('🔍 扩图区域初始设置:', {
        imageSize: { width: img.width, height: img.height },
        expansionSize: { width: expansionWidth.value, height: expansionHeight.value }
      })
      
      showExpansionArea.value = true
      
      // 延迟设置扩图区域，确保画布已经完全渲染
      nextTick(() => {
        setTimeout(() => {
          console.log('🎯 setupExpansionArea: 扩图区域设置完成')
        }, 50)
      })
    }
    
    // 设置比例（无缩放）
    const setAspectRatio = (ratio) => {
      currentAspectRatio.value = ratio
       
      if (!canvas.value || !canvasWrapper.value) {
        console.log('⚠️ setAspectRatio: canvas或canvasWrapper未准备好')
        return
      }
       
      console.log('🔧 setAspectRatio 开始执行:', ratio)
       
      let newWidth, newHeight
       
      if (ratio === 'original') {
         // 恢复原始比例
         newWidth = originalImageSize.value.width
         newHeight = originalImageSize.value.height
       } else {
         // 设置固定比例
         const [widthRatio, heightRatio] = ratio.split(':').map(Number)
         const targetAspect = widthRatio / heightRatio
         
         // 以原图尺寸为基础计算新的扩图区域
         const originalAspect = originalImageSize.value.width / originalImageSize.value.height
         
         if (targetAspect > originalAspect) {
           // 更宽的比例，以宽度为准
           newWidth = originalImageSize.value.width
           newHeight = newWidth / targetAspect
         } else {
           // 更高的比例，以高度为准
           newHeight = originalImageSize.value.height
           newWidth = newHeight * targetAspect
         }
       }
       
       // 确保扩图区域不小于原图尺寸（避免裁切）
       const minWidth = originalImageSize.value.width
       const minHeight = originalImageSize.value.height
       
       if (newWidth < minWidth) {
         newWidth = minWidth
         newHeight = newWidth * (ratio === 'original' ? originalImageSize.value.height / originalImageSize.value.width : newHeight / newWidth)
       }
       if (newHeight < minHeight) {
         newHeight = minHeight
         newWidth = newHeight * (ratio === 'original' ? originalImageSize.value.width / originalImageSize.value.height : newWidth / newHeight)
       }
       
       // 扩图区域居中定位
       const offsetX = (newWidth - originalImageSize.value.width) / 2
       const offsetY = (newHeight - originalImageSize.value.height) / 2
       
       expansionX.value = -offsetX
       expansionY.value = -offsetY
       expansionWidth.value = newWidth
       expansionHeight.value = newHeight
       
       console.log('比例设置完成:', {
         ratio,
         original: { width: originalImageSize.value.width, height: originalImageSize.value.height },
         newSize: { width: newWidth, height: newHeight },
         expansion: { 
           x: expansionX.value, 
           y: expansionY.value, 
           width: expansionWidth.value, 
           height: expansionHeight.value 
         }
       })
     }
    
    // 重置扩图区域位置（不改变大小）
    const resetOutpainting = () => {
      console.log('🔄 重置扩图区域位置')
      
      if (currentImage.value && canvas.value) {
        const img = currentImage.value.img
        if (img) {
          console.log('✅ 重新定位扩图区域，保持当前大小')
          
          // 只重新定位，不改变大小
          const canvasWidth = canvas.value.width
          const canvasHeight = canvas.value.height
          const centerX = canvasWidth / 2
          const centerY = canvasHeight / 2
          
          // 保持当前的扩图区域大小，只重新居中定位
          expansionX.value = centerX - expansionWidth.value / 2
          expansionY.value = centerY - expansionHeight.value / 2
          
          console.log('🎯 扩图区域重新居中:', {
            size: { width: expansionWidth.value, height: expansionHeight.value },
            position: { x: expansionX.value, y: expansionY.value },
            center: { x: centerX, y: centerY }
          })
        } else {
          console.log('⚠️ 没有找到图片数据，重新加载图片')
          loadOriginalImage()
        }
      } else {
        console.log('⚠️ 画布未初始化，重新初始化')
        initCanvas()
        loadOriginalImage()
      }
    }
    
    // 退出扩图模式
    const exitOutpainting = () => {
      emit('exit-outpainting')
    }
    
    // 文件上传处理
    const handleUploadClick = () => {
      fileInput.value?.click()
    }
    
    const handleFileSelect = (event) => {
      const file = event.target.files[0]
      if (file) {
        console.log('📁 OutpaintingCanvas: 用户选择了文件:', file.name)
        emit('file-upload', file)
      }
      event.target.value = ''
    }
    
    // 简化的鼠标事件处理
    const handleMouseDown = (e) => {
      if (!canvas.value || !canvasWrapper.value) return
      
      // 检查是否点击在调整大小手柄上
      const target = e.target
      if (target.classList.contains('resize-handle')) {
        // 获取手柄类型
        let handleType = ''
        if (target.classList.contains('resize-handle-n')) handleType = 'n'
        else if (target.classList.contains('resize-handle-s')) handleType = 's'
        else if (target.classList.contains('resize-handle-e')) handleType = 'e'
        else if (target.classList.contains('resize-handle-w')) handleType = 'w'
        else if (target.classList.contains('resize-handle-nw')) handleType = 'nw'
        else if (target.classList.contains('resize-handle-ne')) handleType = 'ne'
        else if (target.classList.contains('resize-handle-sw')) handleType = 'sw'
        else if (target.classList.contains('resize-handle-se')) handleType = 'se'
        
        console.log('✅ 开始调整大小:', handleType)
        isResizing.value = true
        resizeHandle.value = handleType
        
        const wrapperRect = canvasWrapper.value.getBoundingClientRect()
        resizeStart.value = { 
          x: e.clientX - wrapperRect.left, 
          y: e.clientY - wrapperRect.top, 
          width: expansionWidth.value, 
          height: expansionHeight.value,
          startX: expansionX.value,
          startY: expansionY.value
        }
        e.preventDefault()
        e.stopPropagation()
        return
      }
    }
    
    const handleMouseMove = (e) => {
      if (!isResizing.value) return
      
      if (!canvas.value || !canvasWrapper.value) return
      
      const wrapperRect = canvasWrapper.value.getBoundingClientRect()
      const wrapperX = e.clientX - wrapperRect.left
      const wrapperY = e.clientY - wrapperRect.top
      
      // 计算鼠标移动距离
      const deltaX = wrapperX - resizeStart.value.x
      const deltaY = wrapperY - resizeStart.value.y
      
      let newWidth = resizeStart.value.width
      let newHeight = resizeStart.value.height
      let newX = resizeStart.value.startX
      let newY = resizeStart.value.startY
      
      // 根据手柄类型调整尺寸和位置
      const handle = resizeHandle.value
      
      if (handle.includes('e')) { // 东边 (右)
        newWidth = resizeStart.value.width + deltaX
      }
      if (handle.includes('w')) { // 西边 (左)
        newWidth = resizeStart.value.width - deltaX
        newX = resizeStart.value.startX + deltaX
      }
      if (handle.includes('s')) { // 南边 (下)
        newHeight = resizeStart.value.height + deltaY
      }
      if (handle.includes('n')) { // 北边 (上)
        newHeight = resizeStart.value.height - deltaY
        newY = resizeStart.value.startY + deltaY
      }
      
       // 确保不小于原图尺寸
       const minWidth = originalImageSize.value.width
       const minHeight = originalImageSize.value.height
      
      if (newWidth < minWidth) {
        if (handle.includes('w')) {
          newX = resizeStart.value.startX + (resizeStart.value.width - minWidth)
        }
        newWidth = minWidth
      }
      if (newHeight < minHeight) {
        if (handle.includes('n')) {
          newY = resizeStart.value.startY + (resizeStart.value.height - minHeight)
        }
        newHeight = minHeight
      }
      
      // 更新位置和尺寸
      expansionX.value = newX
      expansionY.value = newY
      expansionWidth.value = newWidth
      expansionHeight.value = newHeight
      
      // 直接更新DOM样式
      const expansionArea = document.querySelector('.expansion-area')
      if (expansionArea) {
        expansionArea.style.left = `${newX}px`
        expansionArea.style.top = `${newY}px`
        expansionArea.style.width = `${newWidth}px`
        expansionArea.style.height = `${newHeight}px`
        console.log('✅ 更新位置和尺寸:', { x: newX, y: newY, width: newWidth, height: newHeight })
      }
    }
    
    const handleMouseUp = () => {
      if (isResizing.value) {
        isResizing.value = false
        resizeHandle.value = ''
        console.log('✅ 调整大小完成')
      }
    }
    
    
    // 缩放功能已移除，等待整体缩放实现
    
    // 历史记录
    const saveToHistory = () => {
      const state = {
        expansionX: expansionX.value,
        expansionY: expansionY.value,
        expansionWidth: expansionWidth.value,
        expansionHeight: expansionHeight.value
      }
      
      history.value = history.value.slice(0, historyIndex.value + 1)
      history.value.push(state)
      historyIndex.value = history.value.length - 1
    }
    
    const undo = () => {
      if (canUndo.value) {
        historyIndex.value--
        const state = history.value[historyIndex.value]
        expansionX.value = state.expansionX
        expansionY.value = state.expansionY
        expansionWidth.value = state.expansionWidth
        expansionHeight.value = state.expansionHeight
      }
    }
    
    const redo = () => {
      if (canRedo.value) {
        historyIndex.value++
        const state = history.value[historyIndex.value]
        expansionX.value = state.expansionX
        expansionY.value = state.expansionY
        expansionWidth.value = state.expansionWidth
        expansionHeight.value = state.expansionHeight
      }
    }
    
    // 保存画布
    const saveCanvas = () => {
      if (!canvas.value) return
      
      const link = document.createElement('a')
      link.download = 'outpainting-canvas.png'
      link.href = canvas.value.toDataURL()
      link.click()
    }
    
    // 执行扩图
    const executeOutpainting = async () => {
      console.log('🎨 OutpaintingCanvas: 开始执行扩图')
      console.log('🔍 执行前状态检查:', {
        currentImage: currentImage.value,
        isProcessing: isProcessing.value,
        canvas: !!canvas.value,
        canvasSize: canvas.value ? { width: canvas.value.width, height: canvas.value.height } : null
      })
      
      if (!currentImage.value) {
        console.error('❌ OutpaintingCanvas: 没有图像，无法执行扩图')
        throw new Error('没有图像')
      }
      
      // 使用用户输入的提示词，如果为空则传递空字符串
      const prompt = props.prompt.trim()
      
      console.log('📊 OutpaintingCanvas: 扩图参数:', {
        image: currentImage.value,
        expansion: {
          x: expansionX.value,
          y: expansionY.value,
          width: expansionWidth.value,
          height: expansionHeight.value
        },
        originalPrompt: props.prompt,
        finalPrompt: prompt
      })
      
       // 计算传递给后端的参数（无缩放）
       const originalWidth = currentImage.value.originalWidth || currentImage.value.width
       const originalHeight = currentImage.value.originalHeight || currentImage.value.height
       
       // 直接使用前端扩图区域的坐标和尺寸，不进行缩放转换
       const expansion_x = expansionX.value
       const expansion_y = expansionY.value
       const originalExpansionWidth = expansionWidth.value
       const originalExpansionHeight = expansionHeight.value
       
       console.log('🔍 扩图参数计算（无缩放）:', {
         original: { width: originalWidth, height: originalHeight },
         expansion: { 
           x: expansion_x, 
           y: expansion_y, 
           width: originalExpansionWidth, 
           height: originalExpansionHeight 
         }
       })
      
      isProcessing.value = true
      processingMessage.value = '正在执行扩图...'
      console.log('⏳ 设置loading状态:', { isProcessing: isProcessing.value, processingMessage: processingMessage.value })
      emit('processing-start')
      
       try {
         // 计算四个方向的扩图参数
         const left = Math.max(0, -expansion_x)
         const top = Math.max(0, -expansion_y)
         const right = Math.max(0, expansion_x + originalExpansionWidth - originalWidth)
         const bottom = Math.max(0, expansion_y + originalExpansionHeight - originalHeight)
         
         console.log('🔍 扩图参数计算:', {
           left, top, right, bottom,
           expansion_x, expansion_y,
           originalExpansionWidth, originalExpansionHeight,
           originalWidth, originalHeight
         })
         
         // 生成扩图参数（使用原始尺寸）
         const parameters = {
           original_width: originalWidth,
           original_height: originalHeight,
           expansion_width: originalExpansionWidth,
           expansion_height: originalExpansionHeight,
           expansion_x: expansion_x,
           expansion_y: expansion_y,
           left: left,
           top: top,
           right: right,
           bottom: bottom,
           negative_prompt: '',
           steps: 8,
           cfg: 2.5,
           denoise: 1.0,
           target_size: 1024,
           lora_strength: 1.0,
           seed: -1
         }
        
        // 准备图像文件
        let sourceImageFile
        if (props.originalImageFile) {
          sourceImageFile = props.originalImageFile
        } else {
          // 从画布生成图像文件
          const dataUrl = canvas.value.toDataURL('image/png')
          sourceImageFile = dataUrlToFile(dataUrl, 'source.png')
        }
        
        // 调用扩图API
        const formData = new FormData()
        formData.append('image', sourceImageFile)
        formData.append('prompt', prompt)
        formData.append('parameters', JSON.stringify(parameters))
        
        const response = await fetch('/api/outpainting', {
          method: 'POST',
          body: formData
        })
        
        if (!response.ok) {
          const errorText = await response.text()
          console.error('❌ 扩图API请求失败:', {
            status: response.status,
            statusText: response.statusText,
            errorText: errorText
          })
          throw new Error(`扩图请求失败: ${response.status} - ${errorText}`)
        }
        
        const result = await response.json()
        console.log('📥 扩图API响应:', result)
        
        if (result.success || result.status === 'pending') {
          // 异步任务已提交，需要轮询检查状态
          console.log('✅ 扩图任务已提交，开始轮询状态...')
          processingMessage.value = '正在处理扩图任务...'
          
          // 轮询任务状态
          await pollTaskStatus(result.task_id, prompt, parameters)
        } else {
          throw new Error(result.message || '扩图失败')
        }
        
      } catch (error) {
        console.error('❌ OutpaintingCanvas: 扩图执行失败:', error)
        processingMessage.value = `扩图失败: ${error.message}`
        
        // 延迟隐藏loading状态，让用户看到错误信息
        setTimeout(() => {
          isProcessing.value = false
          processingMessage.value = ''
          emit('processing-end')
        }, 2000)
        
        throw error
      }
    }
    
    // 轮询任务状态
    const pollTaskStatus = async (taskId, prompt, parameters) => {
      const maxAttempts = 60 // 最多轮询60次
      const pollInterval = 3000 // 每3秒轮询一次
      let attempts = 0
      
      console.log('🔄 开始轮询任务状态:', taskId)
      
      while (attempts < maxAttempts) {
        try {
          await new Promise(resolve => setTimeout(resolve, pollInterval))
          attempts++
          
          console.log(`🔍 第${attempts}次检查任务状态: ${taskId}`)
          
          const response = await fetch(`/api/task/${taskId}`)
          if (!response.ok) {
            throw new Error(`获取任务状态失败: ${response.status}`)
          }
          
          const statusResult = await response.json()
          console.log('📊 任务状态响应:', statusResult)
          
          if (statusResult.status === 'completed') {
            console.log('✅ 扩图任务完成!')
            processingMessage.value = '扩图完成，正在加载结果...'
            
            // 从result中获取图像URL
            let imageUrl = null
            if (statusResult.result && statusResult.result.direct_urls && statusResult.result.direct_urls.length > 0) {
              imageUrl = statusResult.result.direct_urls[0]
            } else if (statusResult.result && statusResult.result.image_urls && statusResult.result.image_urls.length > 0) {
              imageUrl = statusResult.result.image_urls[0]
            }
            
            if (imageUrl) {
              // 加载结果图像
              await loadResultImage(imageUrl)
              
              // 通知父组件
              emit('outpainting-complete', {
                resultImageUrl: imageUrl,
                prompt: prompt,
                parameters: parameters
              })
            } else {
              throw new Error('任务完成但没有找到结果图像')
            }
            
            isProcessing.value = false
            processingMessage.value = ''
            emit('processing-end')
            return
            
          } else if (statusResult.status === 'failed') {
            throw new Error(statusResult.error || '扩图任务失败')
          } else if (statusResult.status === 'processing') {
            processingMessage.value = `正在处理扩图... `
          } else {
            processingMessage.value = `等待扩图任务... `
          }
          
        } catch (error) {
          console.error('❌ 轮询任务状态失败:', error)
          throw error
        }
      }
      
      // 超时
      throw new Error('扩图任务超时，请重试')
    }
    
    // 加载结果图像
    const loadResultImage = async (imageUrl) => {
      const img = new Image()
      img.onload = () => {
        console.log('🔄 扩图结果加载完成，重新设置画布和扩图区域:', {
          imageSize: { width: img.width, height: img.height },
          currentCanvas: { width: canvas.value?.width, height: canvas.value?.height }
        })
        
        // 根据扩图结果重新设置画布尺寸
        resizeCanvasForImage(img)
        drawImageToCanvas(img)
        
        // 重新设置扩图区域，支持继续扩图
        setupExpansionArea(img)
        
        // 保存到历史记录
        saveToHistory()
        
        console.log('✅ 扩图结果处理完成，可以继续扩图')
      }
      img.src = imageUrl
    }
    
    // 工具函数
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
    
    // 监听props变化
    watch(() => props.originalImage, (newValue, oldValue) => {
      console.log('🔄 originalImage props变化:', { 
        newValue, 
        oldValue, 
        hasChanged: newValue !== oldValue,
        newValueType: typeof newValue,
        oldValueType: typeof oldValue
      })
      if (newValue !== oldValue) {
        console.log('✅ originalImage发生变化，重新加载图片')
        loadOriginalImage()
      }
    }, { immediate: false })
    
    watch(() => props.originalImageFile, (newValue, oldValue) => {
      console.log('🔄 originalImageFile props变化:', { 
        newValue, 
        oldValue, 
        hasChanged: newValue !== oldValue,
        newValueType: typeof newValue,
        oldValueType: typeof oldValue
      })
      if (newValue !== oldValue) {
        console.log('✅ originalImageFile发生变化，重新加载图片')
        loadOriginalImage()
      }
    }, { immediate: false })
    
    // 监听组件可见性变化（解决v-show模式下不重新初始化的问题）
    const isVisible = ref(false)
    const checkVisibility = () => {
      const canvasElement = canvasWrapper.value
      if (canvasElement) {
        const rect = canvasElement.getBoundingClientRect()
        const visible = rect.width > 0 && rect.height > 0
        if (visible !== isVisible.value) {
          console.log('🔄 OutpaintingCanvas可见性变化:', { 
            wasVisible: isVisible.value, 
            nowVisible: visible,
            rect: { width: rect.width, height: rect.height }
          })
          isVisible.value = visible
          
          if (visible) {
            console.log('✅ OutpaintingCanvas变为可见，重新初始化')
            // 组件变为可见时，重新初始化
            nextTick(() => {
              setTimeout(() => {
                initCanvas()
                loadOriginalImage()
              }, 100)
            })
          }
        }
      }
    }
    
    // 定期检查可见性
    let visibilityCheckInterval = null
    
    
    // 生命周期
    onMounted(() => {
      nextTick(() => {
        // 延迟初始化，确保容器完全渲染
        setTimeout(() => {
          initCanvas()
          loadOriginalImage()
        }, 100)
        
        // 延迟检查图片加载状态
        setTimeout(() => {
          if (!isImageLoaded.value && (props.originalImage || props.originalImageFile)) {
            console.log('🔄 延迟加载图片')
            loadOriginalImage()
          }
        }, 500)
        
        // 启动可见性检查
        visibilityCheckInterval = setInterval(checkVisibility, 500)
        
        // 监听窗口大小变化
        window.addEventListener('resize', initCanvas)
        
        // 监听全局鼠标事件，确保在画布外部释放鼠标时也能正确结束拖拽
        window.addEventListener('mouseup', handleMouseUp)
        window.addEventListener('mousemove', handleMouseMove)
        
        // 监听扩图执行事件
        window.addEventListener('execute-outpainting', triggerOutpaintingExecution)
      })
    })
    
    onUnmounted(() => {
      // 清理可见性检查
      if (visibilityCheckInterval) {
        clearInterval(visibilityCheckInterval)
      }
      
      window.removeEventListener('resize', initCanvas)
      window.removeEventListener('mouseup', handleMouseUp)
      window.removeEventListener('mousemove', handleMouseMove)
      window.removeEventListener('execute-outpainting', triggerOutpaintingExecution)
    })
    
    // 暴露方法给父组件
    const triggerOutpaintingExecution = async () => {
      console.log('🚀 OutpaintingCanvas: 收到扩图执行事件')
      console.log('🎯 当前状态检查:', {
        currentImage: currentImage.value,
        isProcessing: isProcessing.value,
        canvas: canvas.value,
        props: {
          originalImage: props.originalImage,
          originalImageFile: props.originalImageFile
        }
      })
      
      // 强制重新加载图片（解决换图片后缓存问题）
      console.log('🔄 强制重新加载图片，确保使用最新图片数据')
      
      // 清除当前缓存的图片数据，强制重新加载
      currentImage.value = null
      isImageLoaded.value = false
      
      await loadOriginalImage()
      
      executeOutpainting()
    }
    
    return {
      canvasRef,
      canvasWrapper,
      imageContainer,
      fileInput,
      currentImage,
      showExpansionArea,
      expansionX,
      expansionY,
      expansionWidth,
      expansionHeight,
      realExpansionWidth,
      realExpansionHeight,
      isProcessing,
      processingMessage,
      canUndo,
      canRedo,
      imageContainerStyle,
      expansionAreaStyle,
      currentAspectRatio,
      currentMode: ref('outpainting'), // 添加调试用的模式
      handleMouseDown,
      handleMouseMove,
      handleMouseUp,
      undo,
      redo,
      saveCanvas,
      executeOutpainting,
      pollTaskStatus,
      triggerOutpaintingExecution,
      setAspectRatio,
      resetOutpainting,
      exitOutpainting,
      handleUploadClick,
      handleFileSelect
    }
  }
}

</script>

<style scoped>
.outpainting-canvas-container {
  position: relative;
  width: 100%;
  height: 100%;
  background: #1a1a1a;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.aspect-ratio-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  background: #2a2a2a;
  border-bottom: 1px solid #333;
  color: white;
  min-height: 48px;
}

.toolbar-left,
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.aspect-ratio-controls {
  display: flex;
  align-items: center;
  gap: 4px;
}

.aspect-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background: #374151;
  border: 1px solid #4b5563;
  border-radius: 4px;
  color: #d1d5db;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.aspect-btn:hover {
  background: #4b5563;
  border-color: #6b7280;
}

.aspect-btn.active {
  background: #3b82f6;
  border-color: #2563eb;
  color: white;
}

.zoom-info {
  font-size: 12px;
  color: #ccc;
  min-width: 40px;
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
  width: 100%;
  height: calc(100% - 48px);
  overflow: auto;
  background: #1a1a1a;
  box-sizing: border-box;
  min-height: 400px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.image-container {
  position: relative;
  display: inline-block;
}

.outpainting-canvas {
  display: block;
  cursor: crosshair;
  border: 1px solid #555;
  background: #1a1a1a;
  box-shadow: 0 0 20px rgba(0, 0, 0, 0.5);
  border-radius: 0px;
}

.expansion-area {
  position: absolute;
  border: 2px dashed #64748b;
  background: rgba(100, 116, 139, 0.1);
  cursor: default;
  transform-origin: top left;
}

.resize-handle {
  position: absolute;
  background: #3b82f6;
  border: 1px solid #2563eb;
  z-index: 10;
}

/* 边线手柄 */
.resize-handle-n {
  top: -8px;
  left: 50%;
  transform: translateX(-50%);
  width: 16px;
  height: 8px;
  cursor: n-resize;
  border-radius: 4px;
}

.resize-handle-s {
  bottom: -8px;
  left: 50%;
  transform: translateX(-50%);
  width: 16px;
  height: 8px;
  cursor: s-resize;
  border-radius: 4px;
}

.resize-handle-e {
  right: -8px;
  top: 50%;
  transform: translateY(-50%);
  width: 8px;
  height: 16px;
  cursor: e-resize;
  border-radius: 4px;
}

.resize-handle-w {
  left: -8px;
  top: 50%;
  transform: translateY(-50%);
  width: 8px;
  height: 16px;
  cursor: w-resize;
  border-radius: 4px;
}

/* 角落手柄 */
.resize-handle-nw {
  top: -8px;
  left: -8px;
  width: 16px;
  height: 16px;
  cursor: nw-resize;
  border-radius: 50%;
}

.resize-handle-ne {
  top: -8px;
  right: -8px;
  width: 16px;
  height: 16px;
  cursor: ne-resize;
  border-radius: 50%;
}

.resize-handle-sw {
  bottom: -8px;
  left: -8px;
  width: 16px;
  height: 16px;
  cursor: sw-resize;
  border-radius: 50%;
}

.resize-handle-se {
  bottom: -8px;
  right: -8px;
  width: 16px;
  height: 16px;
  cursor: se-resize;
  border-radius: 50%;
}

.resize-handle:hover {
  background: #2563eb;
  transform: scale(1.2);
}


.expansion-info {
  position: absolute;
  top: -25px;
  left: 0;
  background: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 11px;
  white-space: nowrap;
}

.processing-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.processing-content {
  text-align: center;
  color: white;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #333;
  border-top: 4px solid #00ff88;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 16px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.upload-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(26, 26, 26, 0.9);
  z-index: 100;
}

.upload-content {
  text-align: center;
  color: white;
  padding: 40px;
  border: 2px dashed #555;
  border-radius: 12px;
  background: rgba(42, 42, 42, 0.8);
  backdrop-filter: blur(10px);
  max-width: 400px;
}

.upload-icon {
  margin-bottom: 20px;
  color: #888;
}

.upload-content h3 {
  margin: 0 0 8px 0;
  font-size: 20px;
  font-weight: 600;
  color: #fff;
}

.upload-content p {
  margin: 0 0 24px 0;
  color: #aaa;
  font-size: 14px;
}

.upload-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  background: #007bff;
  border: none;
  border-radius: 6px;
  color: white;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.upload-btn:hover {
  background: #0056b3;
  transform: translateY(-1px);
}

.upload-btn:active {
  transform: translateY(0);
}
</style>
