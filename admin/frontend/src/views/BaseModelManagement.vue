<template>
  <div>
    <div class="header-bar">
      <h1>Base Model Management</h1>
      <div class="header-actions">
        <a-input-search
          v-model:value="searchQuery"
          placeholder="Search by name"
          style="width: 250px;"
          @search="onSearch"
          allow-clear
        />
        <a-button type="primary" @click="showCreateModel" style="margin-left: 8px;">
          <plus-outlined /> Create New Model
        </a-button>
      </div>
    </div>
    <a-table
      :columns="columns"
      :data-source="data"
      row-key="id"
      :pagination="false"
      :loading="loading"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'action'">
          <a-space>
            <a-button type="primary" @click="showEditModel(record)">Edit</a-button>
            <a-popconfirm
              title="Are you sure you want to delete this model?"
              @confirm="deleteModel(record.id)"
            >
              <a-button type="danger">Delete</a-button>
            </a-popconfirm>
          </a-space>
        </template>
      </template>
    </a-table>
    <a-pagination
      v-model:current="pagination.current"
      :total="pagination.total"
      :page-size="pagination.pageSize"
      @change="handleTableChange"
      show-less-items
    />

    <a-modal v-model:open="modelVisible" :title="modelTitle" @ok="handleModelOk" :confirm-loading="modalLoading">
      <a-form :model="formState" layout="vertical">
        <a-form-item label="Name" required>
          <a-input v-model:value="formState.name" />
        </a-form-item>
        <a-form-item label="Description">
          <a-textarea v-model:value="formState.description" :rows="4" />
        </a-form-item>
        <a-form-item label="Model File Path">
          <a-input v-model:value="formState.model_file_path" />
        </a-form-item>
        <a-form-item label="Preview Image Path">
          <a-input v-model:value="formState.preview_image_path" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { getBaseModels, createBaseModel, updateBaseModel, deleteBaseModel } from '@/api/baseModel';
import { message, Space as ASpace, Popconfirm, Modal, Form, Input, Textarea, Button, Table as ATable, Pagination as APagination, InputSearch as AInputSearch } from 'ant-design-vue';
import { PlusOutlined } from '@ant-design/icons-vue';

const columns = [
  { title: 'Name', dataIndex: 'name', key: 'name', ellipsis: true },
  { title: 'Description', dataIndex: 'description', key: 'description', ellipsis: true },
  { title: 'Model Path', dataIndex: 'model_file_path', key: 'model_file_path', ellipsis: true },
  { title: 'Created At', dataIndex: 'created_at', key: 'created_at', width: 180 },
  { title: 'Updated At', dataIndex: 'updated_at', key: 'updated_at', width: 180 },
  { title: 'Action', key: 'action', width: 200 },
];

const data = ref([]);
const loading = ref(false);
const pagination = reactive({ current: 1, pageSize: 10, total: 0 });
const searchQuery = ref('');

const modelVisible = ref(false);
const modalLoading = ref(false);
const modelTitle = ref('');
const isEdit = ref(false);
const currentModelId = ref(null);

const formState = reactive({
  name: '',
  description: '',
  model_file_path: '',
  preview_image_path: '',
});

const fetchBaseModels = async (page = 1, pageSize = 10, name = null) => {
  loading.value = true;
  try {
    const response = await getBaseModels({ page, size: pageSize, name });
    if (response.code === 200) {
      data.value = response.data.items;
      pagination.total = response.data.total;
      pagination.current = response.data.page;
      pagination.pageSize = response.data.size;
    } else {
      message.error(response.message || 'Failed to fetch base models');
    }
  } catch (error) {
    console.error('Error fetching base models:', error);
    message.error('An error occurred while fetching base models');
  } finally {
    loading.value = false;
  }
};

const onSearch = (searchValue) => {
  pagination.current = 1; // Reset to first page on new search
  fetchBaseModels(pagination.current, pagination.pageSize, searchValue);
};

const handleTableChange = (page, pageSize) => {
  fetchBaseModels(page, pageSize, searchQuery.value);
};

onMounted(() => {
  fetchBaseModels();
});

const showCreateModel = () => {
  isEdit.value = false;
  modelTitle.value = 'Create Base Model';
  Object.assign(formState, { name: '', description: '', model_file_path: '', preview_image_path: '' });
  modelVisible.value = true;
};

const showEditModel = (record) => {
  isEdit.value = true;
  modelTitle.value = 'Edit Base Model';
  currentModelId.value = record.id;
  Object.assign(formState, record);
  modelVisible.value = true;
};

const handleModelOk = async () => {
  modalLoading.value = true;
  try {
    if (isEdit.value) {
      await updateBaseModel(currentModelId.value, formState);
      message.success('Update successful');
    } else {
      await createBaseModel(formState);
      message.success('Creation successful');
    }
    modelVisible.value = false;
    fetchBaseModels(pagination.current, pagination.pageSize, searchQuery.value);
  } catch (error) {
    message.error(isEdit.value ? 'Update failed' : 'Creation failed');
  } finally {
    modalLoading.value = false;
  }
};

const deleteModel = async (id) => {
  try {
    await deleteBaseModel(id);
    message.success('Deletion successful');
    fetchBaseModels(pagination.current, pagination.pageSize, searchQuery.value);
  } catch (error) {
    message.error('Deletion failed');
  }
};
</script>

<style scoped>
.header-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.header-actions {
  display: flex;
  align-items: center;
}
.ant-pagination {
  margin-top: 16px;
  text-align: right;
}
</style>