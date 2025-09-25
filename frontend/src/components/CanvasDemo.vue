<template>
  <div class="canvas-demo">
   
    
    <div class="demo-content">
      <CanvasEditor 
        ref="canvasEditor"
        :initial-image-data="initialImageData"
        :initial-mode="initialMode"
        @file-upload="handleFileUpload"
        @save-image="handleSaveImage"
      />
    </div>
    
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import CanvasEditor from './CanvasEditor.vue'

export default {
  name: 'CanvasDemo',
  components: {
    CanvasEditor
  },
  setup() {
    const canvasEditor = ref(null)
    const initialImageData = ref(null)
    const initialMode = ref('')
    
    // 从localStorage读取画布数据
    const loadCanvasData = () => {
      try {
        const canvasDataStr = localStorage.getItem('canvasData')
        if (canvasDataStr) {
          const canvasData = JSON.parse(canvasDataStr)
          console.log('🎨 CanvasDemo 加载画布数据:', canvasData)
          
          // 设置初始图片数据
          if (canvasData.imageData) {
            initialImageData.value = canvasData.imageData
          }
          
          // 设置初始模式
          if (canvasData.mode) {
            initialMode.value = canvasData.mode
          }
          
          // 清除localStorage中的数据，避免重复加载
          localStorage.removeItem('canvasData')
        }
      } catch (error) {
        console.error('❌ 加载画布数据失败:', error)
      }
    }
    
    const handleFileUpload = (file) => {
      console.log('CanvasDemo: File uploaded:', file.name)
      // 这里可以添加文件上传的处理逻辑
    }
    
    const handleSaveImage = () => {
      console.log('Save image requested')
      // 这里可以添加保存图像的逻辑
    }
    
    onMounted(() => {
      loadCanvasData()
    })
    
    return {
      canvasEditor,
      initialImageData,
      initialMode,
      handleFileUpload,
      handleSaveImage
    }
  }
}
</script>

<style scoped>
.canvas-demo {
  min-height: 100vh;
  background: #1a1a1a;
  color: white;
}

.demo-header {
  text-align: center;
  padding: 30px 20px;
  background: linear-gradient(135deg, #2a2a2a 0%, #1a1a1a 100%);
  border-bottom: 1px solid #333;
}

.demo-header h1 {
  margin: 0 0 10px 0;
  font-size: 2.5rem;
  font-weight: 700;
  background: linear-gradient(45deg, #007bff, #00d4ff);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.demo-header p {
  margin: 0;
  font-size: 1.1rem;
  color: #ccc;
  max-width: 600px;
  margin: 0 auto;
}

.demo-content {
  flex: 1;
  min-height: 100vh;
}


/* 响应式设计 */
@media (max-width: 768px) {
  .demo-header {
    padding: 20px 15px;
  }
  
  .demo-header h1 {
    font-size: 2rem;
  }
  
  .demo-header p {
    font-size: 1rem;
  }
  
}

@media (max-width: 480px) {
  .demo-header h1 {
    font-size: 1.8rem;
  }
  
  .demo-header p {
    font-size: 0.9rem;
  }
}
</style>
