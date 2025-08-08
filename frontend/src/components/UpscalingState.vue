<template>
  <div class="upscaling-state">
    <div class="task-card">
      <!-- 任务信息头部 -->
      <div class="task-header">
        <div class="task-info">
          <p class="task-prompt">{{ `正在${scaleFactor}倍放大图片...` }}</p>
          <p class="task-meta">使用UltimateSDUpscale算法</p>
        </div>
      </div>
      
      <!-- 图片占位符 -->
      <div class="image-container">
        <div class="loading-placeholder">
          <!-- 背景脉冲动画 -->
          <div class="pulse-bg"></div>
          
          <!-- 粒子效果 -->
          <div class="particles">
            <div class="particle" v-for="i in 8" :key="i"></div>
          </div>
          
          <!-- 中心旋转加载器 -->
          <div class="center-loader">
            <div class="loader-ring ring-1"></div>
            <div class="loader-ring ring-2"></div>
            <div class="loader-ring ring-3"></div>
            <div class="loader-core">
              <div class="core-icon">🔍</div>
            </div>
          </div>
          
          <!-- 状态文字 -->
          <div class="loading-text">
            <div class="text-line">AI放大中</div>
            <div class="dots">
              <span class="dot"></span>
              <span class="dot"></span>
              <span class="dot"></span>
            </div>
          </div>
          
          <!-- 进度信息 -->
          <div class="progress-info">
            <div class="progress-text">预计时间: {{ estimatedTime }}</div>
            <div class="progress-bar">
              <div class="progress-fill" :style="{ width: progress + '%' }"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

// Props
const props = defineProps({
  scaleFactor: {
    type: Number,
    default: 2
  },
  progress: {
    type: Number,
    default: 0
  }
})

// 计算预计时间
const estimatedTime = computed(() => {
  const baseTime = props.scaleFactor * 30 // 基础时间：2倍=60秒，3倍=90秒，4倍=120秒
  const remaining = Math.max(0, baseTime - (props.progress / 100) * baseTime)
  return `${Math.ceil(remaining)}秒`
})
</script>

<style scoped>
.upscaling-state {
  margin-top: 20px;
}

.task-card {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 16px;
  padding: 20px;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.task-header {
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.task-info {
  flex: 1;
}

.task-prompt {
  font-size: 1.1rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  margin: 0 0 4px 0;
  line-height: 1.4;
}

.task-meta {
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.6);
  margin: 0;
}

.image-container {
  position: relative;
  width: 100%;
  max-width: 200px;
  margin: 0;
  aspect-ratio: 1;
  border-radius: 12px;
  overflow: hidden;
}

.loading-placeholder {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  position: relative;
  width: 100%;
  height: 100%;
  overflow: hidden;
}

/* 背景脉冲动画 */
.pulse-bg {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(45deg, transparent 30%, rgba(255, 255, 255, 0.1) 50%, transparent 70%);
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { transform: translateX(-100%); }
  50% { transform: translateX(100%); }
}

/* 粒子效果 */
.particles {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
}

.particle {
  position: absolute;
  width: 3px;
  height: 3px;
  background: rgba(255, 255, 255, 0.6);
  border-radius: 50%;
  animation: float 3s ease-in-out infinite;
}

.particle:nth-child(1) { top: 20%; left: 10%; animation-delay: 0s; }
.particle:nth-child(2) { top: 60%; left: 20%; animation-delay: 0.5s; }
.particle:nth-child(3) { top: 40%; left: 70%; animation-delay: 1s; }
.particle:nth-child(4) { top: 80%; left: 60%; animation-delay: 1.5s; }
.particle:nth-child(5) { top: 30%; left: 80%; animation-delay: 2s; }
.particle:nth-child(6) { top: 70%; left: 40%; animation-delay: 2.5s; }
.particle:nth-child(7) { top: 10%; left: 50%; animation-delay: 3s; }
.particle:nth-child(8) { top: 90%; left: 30%; animation-delay: 3.5s; }

@keyframes float {
  0%, 100% { transform: translateY(0px) scale(1); opacity: 0.7; }
  50% { transform: translateY(-20px) scale(1.2); opacity: 1; }
}

/* 中心旋转加载器 */
.center-loader {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 60px;
  height: 60px;
}

.loader-ring {
  position: absolute;
  border-radius: 50%;
  border: 2px solid transparent;
}

.ring-1 {
  width: 60px;
  height: 60px;
  border-top-color: #667eea;
  animation: spin 2s linear infinite;
}

.ring-2 {
  width: 45px;
  height: 45px;
  top: 7.5px;
  left: 7.5px;
  border-right-color: #764ba2;
  animation: spin 1.5s linear infinite reverse;
}

.ring-3 {
  width: 30px;
  height: 30px;
  top: 15px;
  left: 15px;
  border-bottom-color: #f093fb;
  animation: spin 1s linear infinite;
}

.loader-core {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 15px;
  height: 15px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.core-icon {
  font-size: 12px;
  animation: glow 2s ease-in-out infinite alternate;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes glow {
  from { text-shadow: 0 0 5px #fff, 0 0 10px #fff, 0 0 15px #667eea; }
  to { text-shadow: 0 0 10px #fff, 0 0 20px #fff, 0 0 30px #f093fb; }
}

/* 状态文字 */
.loading-text {
  position: absolute;
  bottom: 45px;
  left: 10px;
  color: rgba(255, 255, 255, 0.8);
  font-size: 10px;
}

.text-line {
  margin-bottom: 3px;
  font-weight: 500;
}

.dots {
  display: flex;
  gap: 2px;
}

.dot {
  width: 3px;
  height: 3px;
  background: rgba(255, 255, 255, 0.6);
  border-radius: 50%;
  animation: blink 1.4s ease-in-out infinite;
}

.dot:nth-child(1) { animation-delay: 0s; }
.dot:nth-child(2) { animation-delay: 0.2s; }
.dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes blink {
  0%, 80%, 100% { opacity: 0.3; }
  40% { opacity: 1; }
}

/* 进度信息 */
.progress-info {
  position: absolute;
  bottom: 10px;
  left: 10px;
  right: 10px;
  color: rgba(255, 255, 255, 0.8);
}

.progress-text {
  font-size: 9px;
  margin-bottom: 6px;
  text-align: center;
}

.progress-bar {
  width: 100%;
  height: 3px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 2px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #667eea, #764ba2, #f093fb);
  border-radius: 2px;
  transition: width 0.3s ease;
  animation: shimmer 2s ease-in-out infinite;
}

@keyframes shimmer {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}
</style>
