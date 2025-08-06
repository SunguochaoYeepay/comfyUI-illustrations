<script setup>
import ImageGenerator from './components/ImageGenerator.vue'
</script>

<template>
  <div id="app">
    <ImageGenerator />
  </div>
</template>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body {
  margin: 0 !important;
  padding: 0 !important;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  overflow-x: hidden;
  position: relative;
  top: 0;
  left: 0;
}

#app {
  min-height: 100vh;
  margin: 0 !important;
  padding: 0 !important;
  position: relative;
  top: 0;
  left: 0;
}

/* 强制重置可能的全局样式 */
body > div:first-child {
  margin: 0 !important;
  padding: 0 !important;
  transform: none !important;
}
</style>
