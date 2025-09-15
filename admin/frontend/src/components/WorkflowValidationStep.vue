<template>
  <div v-if="validating" style="text-align: center; padding: 40px;">
    <a-spin size="large" />
    <div style="margin-top: 16px;">正在验证工作流...</div>
  </div>
  
  <div v-else-if="validationResult">
    <a-alert 
      :type="validationResult.valid ? 'success' : 'error'"
      :message="validationResult.valid ? '工作流验证成功' : '工作流验证失败'"
      :description="validationResult.valid ? `识别出 ${validationResult.node_analysis?.total_nodes || 0} 个节点` : validationResult.errors?.join(', ') || '验证失败'"
      style="margin-bottom: 16px;"
    />
    
    <div v-if="validationResult.valid">
      <a-descriptions title="工作流分析结果" :column="2" bordered>
        <a-descriptions-item label="节点总数">{{ validationResult.node_analysis?.total_nodes || 0 }}</a-descriptions-item>
        <a-descriptions-item label="工作流类型">{{ validationResult.node_analysis?.workflow_type || '未知' }}</a-descriptions-item>
        <a-descriptions-item label="复杂度">{{ validationResult.node_analysis?.complexity || '未知' }}</a-descriptions-item>
        <a-descriptions-item label="关键节点">{{ Object.keys(validationResult.node_analysis?.key_nodes || {}).length }}</a-descriptions-item>
      </a-descriptions>
      
      <div style="margin-top: 16px;">
        <h4>识别的配置项</h4>
        <div style="margin-bottom: 8px;">
          <span style="font-weight: bold; color: #1890ff;">核心配置：</span>
          <a-tag v-for="(config, key) in validationResult.config_items?.core_config || {}" :key="key" color="blue" style="margin: 4px;">
            {{ key }}
          </a-tag>
        </div>
        <div>
          <span style="font-weight: bold; color: #52c41a;">高级配置：</span>
          <a-tag v-for="(config, key) in validationResult.config_items?.advanced_config || {}" :key="key" color="green" style="margin: 4px;">
            {{ key }}
          </a-tag>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  validating: {
    type: Boolean,
    default: false
  },
  validationResult: {
    type: Object,
    default: null
  }
})
</script>
