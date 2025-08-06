<template>
  <div class="generating-state">
    <div class="task-card">
      <!-- 任务信息头部 -->
      <div class="task-header">
        <div class="task-info">
          <p class="task-prompt">{{ prompt || '正在生成' + imageCount +'图片...' }}</p>
        </div>
      </div>
      
      <!-- 图片占位符网格 -->
      <div class="images-grid" :data-count="imageCount">
        <div
          v-for="index in imageCount"
          :key="index"
          class="image-item"
        >
          <div class="image-container loading-placeholder">
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
                <div class="core-icon">✨</div>
              </div>
            </div>
            
            <!-- 进度指示器 -->
            <div class="progress-indicator">
              <div class="progress-circle">
                <svg class="progress-svg" viewBox="0 0 36 36">
                  <defs>
                    <linearGradient id="progressGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                      <stop offset="0%" style="stop-color:#667eea;stop-opacity:1" />
                      <stop offset="50%" style="stop-color:#764ba2;stop-opacity:1" />
                      <stop offset="100%" style="stop-color:#f093fb;stop-opacity:1" />
                    </linearGradient>
                  </defs>
                  <path class="progress-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"/>
                  <path class="progress-bar" :stroke-dasharray="progress + ', 100'" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"/>
                </svg>
                <div class="progress-text">{{ Math.round(progress) }}%</div>
              </div>
            </div>
            
            <!-- 状态文字 -->
            <div class="loading-text">
              <div class="text-line">AI创作中</div>
              <div class="dots">
                <span class="dot"></span>
                <span class="dot"></span>
                <span class="dot"></span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
// Props
defineProps({
  prompt: {
    type: String,
    default: ''
  },
  imageCount: {
    type: Number,
    default: 4
  },
  progress: {
    type: Number,
    default: 0
  }
})
</script>

<style scoped>
.generating-state {
  margin-top: 20px;
}

.task-card {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 16px;
  padding: 10px;
  backdrop-filter: blur(10px);
}

.task-header {
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.task-info {
  flex: 1;
}

.task-prompt {
  font-size: 1rem;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.9);
  margin: 0 0 4px 0;
  line-height: 1.4;
}

.task-meta {
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.6);
  margin: 0;
}

.images-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
}

.images-grid[data-count="1"] {
  grid-template-columns: 1fr;
  max-width: 400px;
  margin: 0 auto;
}

.images-grid[data-count="2"] {
  grid-template-columns: repeat(2, 1fr);
}

.images-grid[data-count="3"] {
  grid-template-columns: repeat(3, 1fr);
}

.images-grid[data-count="4"] {
  grid-template-columns: repeat(4, 1fr);
}

@media (max-width: 1200px) {
  .images-grid[data-count="4"] {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .images-grid[data-count="4"] {
    grid-template-columns: 1fr;
  }
}

.image-item {
  position: relative;
  aspect-ratio: 1;
  border-radius: 12px;
  overflow: hidden;
}

.image-container {
  position: relative;
  width: 100%;
  height: 100%;
  border-radius: 12px;
  overflow: hidden;
}

.loading-placeholder {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  position: relative;
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
  width: 4px;
  height: 4px;
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
  border: 2px solid transparent;
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

/* 进度指示器 */
.progress-indicator {
  position: absolute;
  bottom: 15px;
  right: 15px;
  width: 50px;
  height: 50px;
}

.progress-circle {
  position: relative;
  width: 100%;
  height: 100%;
}

.progress-svg {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}

.progress-bg {
  fill: none;
  stroke: rgba(255, 255, 255, 0.1);
  stroke-width: 2;
}

.progress-bar {
  fill: none;
  stroke: url(#progressGradient);
  stroke-width: 2;
  stroke-linecap: round;
  transition: stroke-dasharray 0.3s ease;
}

.progress-text {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 10px;
  font-weight: bold;
  color: rgba(255, 255, 255, 0.9);
}

/* 状态文字 */
.loading-text {
  position: absolute;
  bottom: 15px;
  left: 15px;
  color: rgba(255, 255, 255, 0.8);
  font-size: 12px;
}

.text-line {
  margin-bottom: 4px;
  font-weight: 500;
}

.dots {
  display: flex;
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
</style>