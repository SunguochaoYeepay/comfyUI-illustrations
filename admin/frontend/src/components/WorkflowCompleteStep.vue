<template>
  <a-result
    status="success"
    title="工作流配置完成"
    sub-title="点击确定保存工作流到系统"
  >
    <template #extra>
      <a-descriptions :column="1" bordered>
        <a-descriptions-item label="工作流名称">{{ createForm.name }}</a-descriptions-item>
        <a-descriptions-item label="描述">{{ createForm.description || '无' }}</a-descriptions-item>
        <a-descriptions-item label="节点数量">{{ validationResult?.node_analysis?.total_nodes || 0 }}</a-descriptions-item>
        <a-descriptions-item label="配置项数量">
          {{ Object.keys(validationResult?.config_items?.core_config || {}).length + Object.keys(validationResult?.config_items?.advanced_config || {}).length }}
        </a-descriptions-item>
      </a-descriptions>
    </template>
  </a-result>
</template>

<script setup>
defineProps({
  createForm: {
    type: Object,
    required: true
  },
  validationResult: {
    type: Object,
    required: true
  }
})
</script>
