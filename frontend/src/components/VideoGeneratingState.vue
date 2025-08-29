<template>
  <div class="video-generating-state">
    <!-- 动画容器 -->
    <div class="animation-container">
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
            <div class="core-icon">🎬</div>
          </div>
        </div>
        
        <!-- 状态文字 -->
        <div class="loading-text">
          <div class="text-line">AI视频生成中</div>
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
</template>

<script setup>
import { computed } from 'vue'

// Props
const props = defineProps({
  progress: {
    type: Number,
    default: 0
  }
})

// 计算预计时间
const estimatedTime = computed(() => {
  const baseTime = 120 // 基础时间：2分钟
  const remaining = Math.max(0, baseTime - (props.progress / 100) * baseTime)
  return `${Math.ceil(remaining)}秒`
})
</script>

<style scoped>
.video-generating-state {
  width: 100%;
  height: 200px; /* 与UpscalingState保持一致 */
  display: flex;
  align-items: center;
  justify-content: flex-start; /* 左对齐 */
}

.animation-container {
  position: relative;
  width: 100%;
  max-width: 200px; /* 与UpscalingState保持一致 */
  margin: 0;
  aspect-ratio: 1; /* 保持正方形比例 */
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
  width: 80px;
  height: 80px;
}

.loader-ring {
  position: absolute;
  border-radius: 50%;
  border: 3px solid transparent;
}

.ring-1 {
  width: 80px;
  height: 80px;
  border-top-color: #667eea;
  animation: spin 2s linear infinite;
}

.ring-2 {
  width: 60px;
  height: 60px;
  top: 10px;
  left: 10px;
  border-right-color: #764ba2;
  animation: spin 1.5s linear infinite reverse;
}

.ring-3 {
  width: 40px;
  height: 40px;
  top: 20px;
  left: 20px;
  border-bottom-color: #f093fb;
  animation: spin 1s linear infinite;
}

.loader-core {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.core-icon {
  font-size: 16px;
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
  bottom: 50px;
  left: 50%;
  transform: translateX(-50%);
  text-align: center;
  z-index: 10;
  color: rgba(255, 255, 255, 0.8);
  font-size: 12px;
}

.text-line {
  margin-bottom: 6px;
  font-weight: 600;
}

.dots {
  display: flex;
  justify-content: center;
  gap: 3px;
}

.dot {
  width: 4px;
  height: 4px;
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
  bottom: 15px;
  left: 50%;
  transform: translateX(-50%);
  width: 80%;
  z-index: 10;
  color: rgba(255, 255, 255, 0.8);
}

.progress-text {
  font-size: 12px;
  margin-bottom: 8px;
  text-align: center;
}

.progress-bar {
  width: 100%;
  height: 6px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #667eea, #764ba2, #f093fb);
  border-radius: 3px;
  transition: width 0.3s ease;
  animation: shimmer 2s ease-in-out infinite;
}

@keyframes shimmer {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}
</style>
