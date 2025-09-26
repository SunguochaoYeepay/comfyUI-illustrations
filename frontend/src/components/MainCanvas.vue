<template>
  <div class="main-canvas">
    <div class="canvas-wrapper" ref="canvasWrapper">
      <canvas 
        ref="canvasElement" 
        class="main-canvas-element"
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
      
   
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import * as fabric from 'fabric'

export default {
  name: 'MainCanvas',
  props: {
    imageFile: {
      type: File,
      default: null
    },
    imageData: {
      type: Object,
      default: null
    },
    isSelected: {
      type: Boolean,
      default: false
    },
    zoomLevel: {
      type: Number,
      default: 1
    },
    canvasSize: {
      type: String,
      default: 'fit'
    }
  },
  emits: ['image-loaded', 'image-cleared', 'canvas-selected', 'canvas-deselected', 'zoom-changed'],
  setup(props, { emit }) {
    const canvasElement = ref(null)
    const canvasWrapper = ref(null)
    const canvas = ref(null)
    const currentImage = ref(null)
    const isLoading = ref(false)
    const currentZoom = ref(1)
    
    // 计算图片适应画布的缩放比例
    const calculateImageScale = (imgWidth, imgHeight, canvasWidth, canvasHeight) => {
      // 计算适应画布的缩放比例，确保图片完整显示
      const scaleX = canvasWidth / imgWidth
      const scaleY = canvasHeight / imgHeight
      
      
      // 使用较小的缩放比例，确保图片完全适应画布
      return Math.min(scaleX, scaleY)
    }
    
    // 获取画布尺寸
    const getCanvasSize = () => {
      const baseSize = 800
      
      
      switch (props.canvasSize) {
        case '1:1':
          return { width: baseSize, height: baseSize }
        case '4:3':
          return { width: baseSize, height: Math.round(baseSize * 3 / 4) }
        case '3:2':
          return { width: baseSize, height: Math.round(baseSize * 2 / 3) }
        case '16:9':
          return { width: baseSize, height: Math.round(baseSize * 9 / 16) }
        case 'fit':
        default:
          // 适应内容：优先使用图片尺寸
          if (props.imageData && props.imageData.width && props.imageData.height) {
            return { width: props.imageData.width, height: props.imageData.height }
          }
          
          // 如果没有 imageData，尝试从当前图片获取尺寸
          if (currentImage.value && currentImage.value._originalElement) {
            const img = currentImage.value._originalElement
            if (img.width && img.height) {
              return { width: img.width, height: img.height }
            }
          }
          
          return { width: 800, height: 600 }
      }
    }
    
    // 初始化画布
    const initCanvas = () => {
      if (!canvasElement.value) return
      
      // 获取画布尺寸
      const { width, height } = getCanvasSize()
      
      canvas.value = new fabric.Canvas(canvasElement.value, {
        width: width,
        height: height,
        backgroundColor: '#2a2a2a'
      })
      
      // 添加选择事件处理
      canvas.value.on('selection:created', handleImageSelected)
      canvas.value.on('selection:cleared', handleImageDeselected)
      
      // 添加点击事件处理
      canvas.value.on('mouse:down', handleCanvasClick)
      
      
      // 检查是否有待加载的图像
      if (props.imageFile) {
        nextTick(() => {
          loadImage(props.imageFile)
        })
      } else if (props.imageData && props.imageData.imageUrl) {
        nextTick(() => {
          loadImageFromData(props.imageData)
        })
      }
    }
    
    // 加载图像
    const loadImage = (file) => {
      if (!file || !canvas.value) return
      
      isLoading.value = true
      
      const reader = new FileReader()
      reader.onload = (e) => {
        const imageUrl = e.target.result
        
        // 直接使用备用方法，因为fabric.Image.fromURL有问题
        loadImageFallback(imageUrl, file)
      }
      
      reader.onerror = (error) => {
        console.error('FileReader错误:', error)
        isLoading.value = false
      }
      
      reader.readAsDataURL(file)
    }
    
    // 备用图像加载方法
    const loadImageFallback = (imageUrl, file) => {
      
      // 设置备用方法的超时
      const fallbackTimeout = setTimeout(() => {
        console.error('❌ 备用方法也超时了')
        isLoading.value = false
      }, 5000)
      
      const img = new Image()
      img.onload = () => {
        clearTimeout(fallbackTimeout)
        
        // 清除画布
        canvas.value.clear()
        
        // 创建Fabric.js图像对象
        const fabricImg = new fabric.Image(img, {
          left: 0,
          top: 0,
          selectable: true,
          evented: true
        })
        
        // 在 'fit' 模式下，直接使用图片尺寸作为画布尺寸
        if (props.canvasSize === 'fit') {
          const { width: newWidth, height: newHeight } = { width: img.width, height: img.height }
          canvas.value.setDimensions({ width: newWidth, height: newHeight })
          // 不进行缩放，使用原始尺寸
        } else {
          // 其他模式使用原来的逻辑
          const { width: canvasWidth, height: canvasHeight } = getCanvasSize()
          const scale = calculateImageScale(img.width, img.height, canvasWidth, canvasHeight)
          // 设置图片的缩放比例
          fabricImg.scale(scale)
        }
        
        // 添加图像到画布
        canvas.value.add(fabricImg)
        canvas.value.sendObjectToBack(fabricImg)
        
        // 居中显示
        canvas.value.centerObject(fabricImg)
        canvas.value.renderAll()
        
        currentImage.value = fabricImg
        isLoading.value = false
        
        // 通知父组件图像已加载
        emit('image-loaded', {
          image: fabricImg,
          file: file,
          imageUrl: imageUrl,
          width: img.width,
          height: img.height
        })
        
        // 如果当前是 'fit' 模式，需要重新计算画布尺寸
        if (props.canvasSize === 'fit') {
          nextTick(() => {
            const { width, height } = getCanvasSize()
            canvas.value.setDimensions({ width, height })
            // 重新居中图片
            canvas.value.centerObject(fabricImg)
            canvas.value.renderAll()
          })
        }
        
      }
      
      img.onerror = (error) => {
        clearTimeout(fallbackTimeout)
        console.error('❌ 备用方法图像加载失败:', error)
        isLoading.value = false
      }
      
      img.src = imageUrl
    }
    
    // 从图像数据加载图像
    const loadImageFromData = (imageData) => {
      if (!canvas.value || !imageData) return
      
      
      const img = new Image()
      img.onload = () => {
        
        // 清除画布
        canvas.value.clear()
        
        // 创建Fabric.js图像对象
        const fabricImg = new fabric.Image(img, {
          left: 0,
          top: 0,
          selectable: true,
          evented: true
        })
        
        // 在 'fit' 模式下，直接使用图片尺寸作为画布尺寸
        if (props.canvasSize === 'fit') {
          const { width: newWidth, height: newHeight } = { width: img.width, height: img.height }
          canvas.value.setDimensions({ width: newWidth, height: newHeight })
          // 不进行缩放，使用原始尺寸
        } else {
          // 其他模式使用原来的逻辑
          const { width: canvasWidth, height: canvasHeight } = getCanvasSize()
          const scale = calculateImageScale(img.width, img.height, canvasWidth, canvasHeight)
          // 设置图片的缩放比例
          fabricImg.scale(scale)
        }
        
        // 添加图像到画布
        canvas.value.add(fabricImg)
        canvas.value.sendObjectToBack(fabricImg)
        
        // 居中显示
        canvas.value.centerObject(fabricImg)
        canvas.value.renderAll()
        
        currentImage.value = fabricImg
        isLoading.value = false
        
        // 通知父组件图像已加载
        emit('image-loaded', {
          image: fabricImg,
          file: imageData.file,
          imageUrl: imageData.imageUrl,
          width: img.width,
          height: img.height
        })
        
        // 如果当前是 'fit' 模式，需要重新计算画布尺寸
        if (props.canvasSize === 'fit') {
          nextTick(() => {
            const { width, height } = getCanvasSize()
            canvas.value.setDimensions({ width, height })
            // 重新居中图片
            canvas.value.centerObject(fabricImg)
            canvas.value.renderAll()
          })
        }
        
      }
      
      img.onerror = (error) => {
        isLoading.value = false
      }
      
      img.src = imageData.imageUrl
    }
    
    // 清除图像
    const clearImage = () => {
      if (canvas.value) {
        canvas.value.clear()
        currentImage.value = null
        emit('image-cleared')
      }
    }
    
    // 处理图像被选中
    const handleImageSelected = (e) => {
      emit('canvas-selected')
    }
    
    // 处理图像取消选择
    const handleImageDeselected = (e) => {
      emit('canvas-deselected')
    }
    
    // 处理画布点击
    const handleCanvasClick = (e) => {
      // 如果点击的是空白区域（没有对象被选中）
      if (!e.target) {
        // 清除所有选择
        canvas.value.discardActiveObject()
        canvas.value.renderAll()
        emit('canvas-deselected')
      }
    }
    
    // 缩放相关方法
    const zoomIn = () => {
      if (!canvasWrapper.value) return
      const newZoom = Math.min(currentZoom.value * 1.2, 5) // 最大5倍
      currentZoom.value = newZoom
      canvasWrapper.value.style.transform = `scale(${newZoom})`
      emit('zoom-changed', newZoom)
    }
    
    const zoomOut = () => {
      if (!canvasWrapper.value) return
      const newZoom = Math.max(currentZoom.value / 1.2, 0.1) // 最小0.1倍
      currentZoom.value = newZoom
      canvasWrapper.value.style.transform = `scale(${newZoom})`
      emit('zoom-changed', newZoom)
    }
    
    const zoomFit = () => {
      if (!canvasWrapper.value || !currentImage.value) return
      
      // 如果是 'fit' 模式，重新计算画布尺寸
      if (props.canvasSize === 'fit') {
        const { width, height } = getCanvasSize()
        canvas.value.setDimensions({ width, height })
        canvas.value.centerObject(currentImage.value)
        canvas.value.renderAll()
        return
      }
      
      // 其他模式使用原来的缩放逻辑
      const containerWidth = canvasWrapper.value.parentElement.clientWidth
      const containerHeight = canvasWrapper.value.parentElement.clientHeight
      const imageWidth = currentImage.value.width
      const imageHeight = currentImage.value.height
      
      const scaleX = containerWidth / imageWidth
      const scaleY = containerHeight / imageHeight
      const scale = Math.min(scaleX, scaleY) * 0.9 // 留一些边距
      
      currentZoom.value = scale
      canvasWrapper.value.style.transform = `scale(${scale})`
      emit('zoom-changed', scale)
    }
    
    const zoom100 = () => {
      if (!canvasWrapper.value) return
      currentZoom.value = 1
      canvasWrapper.value.style.transform = 'scale(1)'
      emit('zoom-changed', 1)
    }
    
    // 暴露缩放方法给父组件
    const setZoom = (zoom) => {
      if (!canvasWrapper.value) return
      currentZoom.value = zoom
      canvasWrapper.value.style.transform = `scale(${zoom})`
    }
    
    
    // 拖拽处理
    const handleDrop = (e) => {
      e.preventDefault()
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
    }
    
    const handleDragLeave = (e) => {
      e.preventDefault()
    }
    
    // 监听props变化
    watch(() => props.imageFile, (newFile, oldFile) => {
      if (newFile && canvas.value) {
        // 检查是否是相同的文件，避免重复加载
        if (!oldFile || oldFile.name !== newFile.name || oldFile.size !== newFile.size) {
          loadImage(newFile)
        }
      } else if (newFile && !canvas.value) {
        // 画布未初始化，等待初始化完成
        nextTick(() => {
          if (canvas.value) {
            loadImage(newFile)
          }
        })
      } else {
        // 如果没有文件但有图像数据，尝试从图像数据恢复
        if (props.imageData && props.imageData.imageUrl && canvas.value) {
          loadImageFromData(props.imageData)
        }
      }
    }, { immediate: true })
    
    // 监听imageData变化
    watch(() => props.imageData, (newImageData, oldImageData) => {
      // 防止重复加载相同的图片
      if (newImageData && newImageData.imageUrl && canvas.value) {
        // 检查是否是相同的图片URL，避免重复加载
        if (!oldImageData || oldImageData.imageUrl !== newImageData.imageUrl) {
          loadImageFromData(newImageData)
        }
      } else if (newImageData && newImageData.imageUrl && !canvas.value) {
        // 画布未初始化，等待初始化完成
        nextTick(() => {
          if (canvas.value) {
            loadImageFromData(newImageData)
          }
        })
      } else if (!newImageData && canvas.value) {
        clearImage()
      }
    }, { immediate: true })
    
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
    
    // 监听画布尺寸变化
    watch(() => props.canvasSize, () => {
      nextTick(() => {
        initCanvas()
        // 如果有图片数据，重新加载
        if (props.imageData) {
          loadImageFromData(props.imageData)
        }
      })
    })
    
    return {
      canvasElement,
      canvasWrapper,
      currentImage,
      isLoading,
      currentZoom,
      calculateImageScale,
      getCanvasSize,
      handleDrop,
      handleDragOver,
      handleDragEnter,
      handleDragLeave,
      clearImage,
      handleImageSelected,
      handleImageDeselected,
      handleCanvasClick,
      zoomIn,
      zoomOut,
      zoomFit,
      zoom100,
      setZoom
    }
  }
}
</script>

<style scoped>
.main-canvas {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 10px;
  overflow: auto;
  min-height: 0;
}

.canvas-wrapper {
  position: relative;
  border: 1px solid #333;
  background: #2a2a2a;
  max-width: 100%;
  max-height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  transform-origin: center center;
  transition: transform 0.2s ease;
}

.main-canvas-element {
  display: block;
}

.loading-overlay {
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

.loading-spinner {
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

.debug-info {
  text-align: center;
  color: #888;
  padding: 40px;
}

.debug-info p {
  margin: 8px 0;
  font-size: 14px;
}
</style>
