<template>
  <div>
    <a-card title="图片管理">
      <a-table :columns="columns" :data-source="tableData" :loading="loading" row-key="image_id">
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'url'">
            <a-image :width="100" :src="record.url" />
          </template>
          <template v-if="column.key === 'action'">
            <a-popconfirm
              title="确定要删除这张图片吗?"
              ok-text="是的"
              cancel-text="取消"
              @confirm="handleDelete(record.image_id)"
            >
              <a-button type="primary" danger>删除</a-button>
            </a-popconfirm>
          </template>
        </template>
      </a-table>
    </a-card>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { getImages, deleteImage } from '@/api/images';
import { message } from 'ant-design-vue';

const loading = ref(false);
const data = ref([]);

// 计算属性确保数据始终是数组
const tableData = computed(() => {
  return Array.isArray(data.value) ? data.value : [];
});

// 确保数据始终是数组的防护函数
const ensureArray = (value) => {
  if (Array.isArray(value)) {
    return value;
  }
  if (value && Array.isArray(value.data)) {
    return value.data;
  }
  if (value && value.data && Array.isArray(value.data.items)) {
    return value.data.items;
  }
  return [];
};

const columns = [
  {
    title: '图片ID',
    dataIndex: 'image_id',
    key: 'image_id',
  },
  {
    title: '图片',
    key: 'url',
  },
  {
    title: 'Prompt',
    dataIndex: 'prompt',
    key: 'prompt',
  },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status',
  },
  {
    title: '创建时间',
    dataIndex: 'create_time',
    key: 'create_time',
  },
  {
    title: '操作',
    key: 'action',
  },
];

const fetchImages = async () => {
  loading.value = true;
  try {
    const res = await getImages();
    console.log('API Response:', res); // 调试日志
    
    // 使用防护函数确保数据是数组
    data.value = ensureArray(res);
    
    if (data.value.length === 0 && res) {
      console.warn('API返回的数据不是数组格式:', res);
    }
  } catch (error) {
    console.error('获取图片列表失败:', error);
    data.value = []; // 确保data是数组
    // 错误消息已经在request拦截器中处理了
  } finally {
    loading.value = false;
  }
};

const handleDelete = async (id) => {
  try {
    await deleteImage(id);
    message.success('删除成功');
    fetchImages(); // Refresh the list
  } catch (error) {
    message.error('删除失败');
    console.error(error);
  }
};

onMounted(() => {
  fetchImages();
});
</script>

<style scoped>
</style>