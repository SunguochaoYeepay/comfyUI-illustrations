<template>
  <div>
    <a-card title="图片管理">
      <a-table :columns="columns" :data-source="data" :loading="loading" row-key="image_id">
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
import { ref, onMounted } from 'vue';
import { getImages, deleteImage } from '@/api/images';
import { message } from 'ant-design-vue';

const loading = ref(false);
const data = ref([]);

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
    if (res && Array.isArray(res)) {
      data.value = res;
    } else {
      // If the response is not an array (e.g., an error object), set data to an empty array
      data.value = [];
      message.error('获取图片列表失败：无效的响应格式');
      console.error('Invalid response format:', res);
    }
  } catch (error) {
    message.error('获取图片列表失败');
    console.error(error);
    data.value = []; // Also clear data on catch
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