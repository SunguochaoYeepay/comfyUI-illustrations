<template>
  <div class="video-config-section">
    <div class="video-config-item">
      <label>时长(秒):</label>
      <a-input-number 
        v-model:value="localDuration" 
        :min="1" 
        :max="10" 
        :step="1"
        size="small"
        class="video-config-input"
      />
    </div>
    <div class="video-config-item">
      <label>帧率:</label>
      <a-select 
        v-model:value="localFps" 
        size="small"
        class="video-config-select"
      >
        <a-select-option value="8">8 FPS</a-select-option>
        <a-select-option value="16">16 FPS</a-select-option>
        <a-select-option value="24">24 FPS</a-select-option>
      </a-select>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

// Props
const props = defineProps({
  duration: {
    type: Number,
    default: 5
  },
  fps: {
    type: String,
    default: '16'
  }
})

// Emits
const emit = defineEmits(['update:duration', 'update:fps'])

// 双向绑定的计算属性
const localDuration = computed({
  get: () => props.duration,
  set: (value) => emit('update:duration', value)
})

const localFps = computed({
  get: () => props.fps,
  set: (value) => emit('update:fps', value)
})
</script>

<style scoped>
.video-config-section {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-shrink: 0;
}

.video-config-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.video-config-item label {
  color: #999;
  font-size: 12px;
  white-space: nowrap;
}

.video-config-input {
  width: 60px;
}

.video-config-select {
  width: 80px;
}
</style>
