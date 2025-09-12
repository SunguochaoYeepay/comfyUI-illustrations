<template>
  <div>
    <div class="header-bar">
      <h1>LoRA Model Management</h1>
      <div class="header-actions">
        <a-input-search
          v-model:value="searchQuery"
          placeholder="Search by name"
          style="width: 250px;"
          @search="onSearch"
          allow-clear
        />
        <a-button type="primary" @click="showCreateModal" style="margin-left: 8px;">
          <plus-outlined /> Create New LoRA
        </a-button>
      </div>
    </div>
    <a-table
      :columns="columns"
      :data-source="data"
      row-key="name"
      :pagination="false"
      :loading="loading"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'preview'">
          <a-image
            v-if="record.preview_url"
            :width="64"
            :src="`${baseURL}${record.preview_url}?t=${new Date().getTime()}`"
            :preview="{ src: `${baseURL}${record.preview_url}?t=${new Date().getTime()}` }"
          />
          <span v-else>N/A</span>
        </template>
        <template v-else-if="column.key === 'is_managed'">
          <a-tag :color="record.is_managed ? 'green' : 'orange'">
            {{ record.is_managed ? 'Managed' : 'Unmanaged' }}
          </a-tag>
        </template>
        <template v-else-if="column.key === 'action'">
          <a-space>
            <a-button type="primary" @click="handleUniversalEdit(record)">Edit</a-button>
            <a-popconfirm
              title="Delete metadata only (.json/.png)? The model file will NOT be deleted."
              @confirm="handleDelete(record.name, record.is_managed)"
            >
              <a-button type="danger">Delete Meta</a-button>
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

    <!-- Edit Modal -->
    <a-modal
      v-model:open="editModalOpen"
      title="Edit LoRA Meta"
      @ok="handleEdit"
      :confirm-loading="editModalLoading"
    >
      <a-form :model="editForm" layout="vertical">
        <a-form-item label="Display Name">
          <a-input v-model:value="editForm.display_name" />
        </a-form-item>
        <a-form-item label="Filename">
          <a-auto-complete
            v-model:value="editForm.new_name"
            :options="filenameOptions"
            placeholder="Enter new filename or select an unmanaged model"
          />
        </a-form-item>
        <a-form-item label="Base Model">
          <a-input v-model:value="editForm.base_model" />
        </a-form-item>
        <a-form-item label="Description">
          <a-textarea v-model:value="editForm.description" :rows="4" />
        </a-form-item>
        <a-form-item label="Upload Preview">
          <a-upload
            :file-list="fileList"
            :before-upload="beforeUpload"
            @remove="handleRemove"
            :max-count="1"
          >
            <a-button>
              <upload-outlined /> Select File
            </a-button>
          </a-upload>
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- Create Modal -->
    <a-modal
      v-model:open="createModalOpen"
      title="Create New LoRA Record"
      @ok="handleCreate"
      :confirm-loading="createModalLoading"
    >
      <a-form :model="createForm" layout="vertical">
        <a-form-item label="Model File" required>
          <a-select
            v-model:value="createForm.filename"
            placeholder="Select an unassociated model file"
            :loading="unassociatedLoading"
          >
            <a-select-option v-for="filename in unassociatedLoras" :key="filename" :value="filename">
              {{ filename }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="Display Name" required>
          <a-input v-model:value="createForm.display_name" />
        </a-form-item>
        <a-form-item label="Base Model">
          <a-input v-model:value="createForm.base_model" />
        </a-form-item>
        <a-form-item label="Description">
          <a-textarea v-model:value="createForm.description" :rows="4" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue';
import { getLoras, deleteLora, updateLoraMeta, uploadLoraPreview, getUnassociatedLoras, createLoraRecord } from '@/api/lora';
import { message, Image as AImage, Space as ASpace, Upload, Popconfirm, Modal, Form, Input, Textarea, Button, Select, Tag, AutoComplete as AAutoComplete } from 'ant-design-vue';
import { UploadOutlined, PlusOutlined } from '@ant-design/icons-vue';

export default {
  name: 'LoraManagement',
  components: {
    AImage,
    ASpace,
    AUpload: Upload,
    UploadOutlined,
    PlusOutlined,
    APopconfirm: Popconfirm,
    AModal: Modal,
    AForm: Form,
    AFormItem: Form.Item,
    AInput: Input,
    ATextarea: Textarea,
    AButton: Button,
    ASelect: Select,
    ASelectOption: Select.Option,
    ATag: Tag,
  },
  setup() {
    const baseURL = import.meta.env.VITE_API_BASE_URL || '';
    const loading = ref(false);

    const columns = [
      { title: 'Preview', key: 'preview', width: 100 },
      { title: 'Display Name', dataIndex: 'display_name', key: 'display_name', ellipsis: true },
      { title: 'Filename', dataIndex: 'name', key: 'name', ellipsis: true },
      { title: 'Status', key: 'is_managed', width: 120 },
      { title: 'Size (MB)', dataIndex: 'size', key: 'size', customRender: ({ text }) => `${(text / 1024 / 1024).toFixed(2)} MB` },
      { title: 'Base Model', dataIndex: 'base_model', key: 'base_model' },
      { 
        title: 'Created',
        dataIndex: 'created',
        key: 'created',
        width: 180 
      },
      { 
        title: 'Modified',
        dataIndex: 'modified',
        key: 'modified',
        width: 180 
      },
      { title: 'Action', key: 'action', width: 220 },
    ];

    const data = ref([]);
    const pagination = reactive({ current: 1, pageSize: 10, total: 0 });

    // Edit Modal State
    const editModalOpen = ref(false);
    const editModalLoading = ref(false);
    const editForm = reactive({ name: '', new_name: '', display_name: '', base_model: '', description: '' });
    const fileList = ref([]);
    const filenameOptions = ref([]);

    // Create Modal State
    const createModalOpen = ref(false);
    const createModalLoading = ref(false);
    const unassociatedLoras = ref([]);
    const unassociatedLoading = ref(false);
    const createForm = reactive({ filename: null, display_name: '', base_model: '', description: '' });

    const searchQuery = ref('');

    const fetchLoras = async (page = 1, pageSize = 10, name = null) => {
      loading.value = true;
      try {
        const response = await getLoras(page, pageSize, name);
        if (response.code === 200) {
          data.value = response.data.items;
          pagination.total = response.data.total;
          pagination.current = response.data.page;
          pagination.pageSize = response.data.pageSize;
        } else {
          message.error(response.message || 'Failed to fetch LoRA models');
        }
      } catch (error) {
        console.error('Error fetching LoRA models:', error);
        message.error('Error fetching LoRA models');
      } finally {
        loading.value = false;
      }
    };

    const onSearch = (searchValue) => {
      pagination.current = 1; // Reset to first page on new search
      fetchLoras(pagination.current, pagination.pageSize, searchValue);
    };

    // --- Edit Logic ---
    const showEditModal = async (record) => {
      editForm.name = record.name;
      editForm.new_name = record.name;
      editForm.display_name = record.display_name;
      editForm.base_model = record.base_model;
      editForm.description = record.description;
      fileList.value = [];
      editModalOpen.value = true;

      // Fetch unassociated models for the autocomplete
      try {
        const response = await getUnassociatedLoras();
        if (response.code === 200) {
          const options = response.data.map(name => ({ value: name }));
          if (!options.some(opt => opt.value === record.name)) {
            options.unshift({ value: record.name });
          }
          filenameOptions.value = options;
        } else {
          message.error(response.message || 'Failed to fetch unassociated models for editing');
          filenameOptions.value = [{ value: record.name }];
        }
      } catch (error) {
        console.error('Error fetching unassociated models for editing:', error);
        message.error('Error fetching unassociated models for editing');
        filenameOptions.value = [{ value: record.name }]; // Fallback to just the current name
      }
    };

    const handleEdit = async () => {
      editModalLoading.value = true;
      try {
        const metaData = {
          display_name: editForm.display_name,
          base_model: editForm.base_model,
          description: editForm.description,
          new_name: editForm.new_name,
        };
        await updateLoraMeta(editForm.name, metaData);

        if (fileList.value.length > 0) {
          const formData = new FormData();
          formData.append('file', fileList.value[0].originFileObj);
          const nameForPreview = editForm.new_name || editForm.name;
          await uploadLoraPreview(nameForPreview, formData);
        }
        
        message.success('LoRA meta updated successfully');
        editModalOpen.value = false;
        fetchLoras(pagination.current, pagination.pageSize);
      } catch (error) {
        console.error('Error updating LoRA meta:', error);
        message.error(error.response?.data?.detail || 'Error updating LoRA meta');
      } finally {
        editModalLoading.value = false;
      }
    };

    // --- Create Logic ---
    const showCreateModal = async () => {
      createForm.filename = null; // Reset filename for fresh creation
      createModalOpen.value = true;
      unassociatedLoading.value = true;
      try {
        const response = await getUnassociatedLoras();
        if (response.code === 200) {
          unassociatedLoras.value = response.data;
          // Reset form
          createForm.filename = null;
          createForm.display_name = '';
          createForm.base_model = '';
          createForm.description = '';
        } else {
          message.error(response.message || 'Failed to fetch unassociated models');
        }
      } catch (error) {
        console.error('Error fetching unassociated models:', error);
        message.error('Error fetching unassociated models');
      } finally {
        unassociatedLoading.value = false;
      }
    };

    const handleCreate = async () => {
      if (!createForm.filename || !createForm.display_name) {
        message.warning('Model File and Display Name are required.');
        return;
      }
      createModalLoading.value = true;
      try {
        await createLoraRecord(createForm);
        message.success('LoRA record created successfully');
        createModalOpen.value = false;
        fetchLoras(1, pagination.pageSize); // Go to first page to see the new record
      } catch (error) {
        console.error('Error creating LoRA record:', error);
        message.error(error.response?.data?.detail || 'Error creating LoRA record');
      } finally {
        createModalLoading.value = false;
      }
    };

    const handleUniversalEdit = (record) => {
      if (record.is_managed) {
        showEditModal(record);
      } else {
        // For unmanaged, we pre-fill the create/manage modal
        createForm.filename = record.name;
        createForm.display_name = '';
        createForm.base_model = '';
        createForm.description = '';
        unassociatedLoras.value = []; // No need to fetch, we have the filename
        createModalOpen.value = true;
      }
    };

    // --- Delete Logic ---
    const handleDelete = async (name, is_managed) => {
      if (!is_managed) {
        message.info('This LoRA has no metadata to delete.');
        return;
      }
      try {
        await deleteLora(name);
        message.success('LoRA metadata deleted successfully');
        fetchLoras(pagination.current, pagination.pageSize);
      } catch (error) {
        console.error('Error deleting LoRA meta:', error);
        message.error(error.response?.data?.detail || 'Error deleting LoRA meta');
      }
    };

    // --- Common ---
    const handleTableChange = (page, pageSize) => {
      fetchLoras(page, pageSize, searchQuery.value);
    };

    const beforeUpload = (file) => {
      const isPng = file.type === 'image/png';
      if (!isPng) message.error('You can only upload PNG file!');
      const isLt2M = file.size / 1024 / 1024 < 2;
      if (!isLt2M) message.error('Image must smaller than 2MB!');
      if (isPng && isLt2M) fileList.value = [file];
      return false; // Prevent auto upload
    };

    const handleRemove = () => {
      fileList.value = [];
    };

    onMounted(() => {
      fetchLoras();
    });

    return {
      baseURL,
      loading,
      columns,
      data,
      pagination,
      searchQuery,
      onSearch,
      handleDelete,
      handleTableChange,
      editModalOpen,
      editModalLoading,
      editForm,
      showEditModal,
      handleEdit,
      fileList,
      beforeUpload,
      handleRemove,
      filenameOptions,
      createModalOpen,
      createModalLoading,
      createForm,
      unassociatedLoras,
      unassociatedLoading,
      showCreateModal,
      handleCreate,
      handleUniversalEdit, // Add this line
    };
  },
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