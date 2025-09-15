<template>
  <div>
    <div class="header-bar">
      <h1>LoRA管理</h1>
      <div class="header-actions">
        <a-input-search
          v-model:value="searchQuery"
          placeholder="按名称搜索"
          style="width: 200px;"
          @search="onSearch"
          allow-clear
        />
        <a-select
          v-model:value="baseModelFilter"
          placeholder="选择基础模型"
          style="width: 200px; margin-left: 8px;"
          @change="onBaseModelFilter"
          allow-clear
        >
          <a-select-option 
            v-for="model in baseModels" 
            :key="model.name" 
            :value="model.name"
          >
            {{ model.display_name }}
          </a-select-option>
        </a-select>
        <a-button type="primary" @click="showCreateModal" style="margin-left: 8px;">
          <plus-outlined /> 创建新LoRA
        </a-button>
      </div>
    </div>
    <a-table
      :columns="columns"
      :data-source="tableData"
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
        <template v-else-if="column.key === 'is_available'">
          <a-tag :color="record.is_available ? 'green' : 'red'">
            {{ record.is_available ? '启用' : '禁用' }}
          </a-tag>
        </template>
        <template v-else-if="column.key === 'action'">
          <a-space>
            <a @click="handleUniversalEdit(record)">编辑</a>
            <a @click="toggleAvailability(record)">
              {{ record.is_available ? '禁用' : '启用' }}
            </a>
            <a-popconfirm
              v-if="!record.is_available"
              title="仅删除元数据(.json/.png)？模型文件不会被删除。"
              @confirm="handleDelete(record.id, record.is_managed)"
            >
              <a style="color: #ff4d4f;">删除</a>
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
      title="编辑LoRA元数据"
      @ok="handleEdit"
      :confirm-loading="editModalLoading"
    >
      <a-form :model="editForm" layout="vertical">
        <a-form-item label="显示名称">
          <a-input v-model:value="editForm.display_name" />
        </a-form-item>
        <a-form-item label="文件名">
          <a-auto-complete
            v-model:value="editForm.new_name"
            :options="filenameOptions"
            placeholder="输入新文件名或选择未管理的模型"
          />
        </a-form-item>
        <a-form-item label="基础模型">
          <a-select 
            v-model:value="editForm.base_model" 
            placeholder="选择基础模型"
            :loading="baseModelsLoading"
            show-search
            :filter-option="(input, option) => option.children.toLowerCase().indexOf(input.toLowerCase()) >= 0"
          >
            <a-select-option 
              v-for="model in baseModels" 
              :key="model.name" 
              :value="model.name"
            >
              {{ model.display_name }} ({{ model.name }})
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="描述">
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
      title="创建新LoRA记录"
      @ok="handleCreate"
      :confirm-loading="createModalLoading"
    >
      <a-form :model="createForm" layout="vertical">
        <a-form-item label="模型文件" required>
          <a-select
            v-model:value="createForm.filename"
            placeholder="选择模型文件"
            :loading="unassociatedLoading"
          >
            <a-select-option v-for="filename in unassociatedLoras" :key="filename" :value="filename">
              {{ filename }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="显示名称" required>
          <a-input v-model:value="createForm.display_name" />
        </a-form-item>
        <a-form-item label="基础模型">
          <a-select 
            v-model:value="createForm.base_model" 
            placeholder="选择基础模型"
            :loading="baseModelsLoading"
            show-search
            :filter-option="(input, option) => option.children.toLowerCase().indexOf(input.toLowerCase()) >= 0"
          >
            <a-select-option 
              v-for="model in baseModels" 
              :key="model.name" 
              :value="model.name"
            >
              {{ model.display_name }} ({{ model.name }})
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="描述">
          <a-textarea v-model:value="createForm.description" :rows="4" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script>
import { ref, reactive, onMounted, computed } from 'vue';
    import { getLoras, deleteLora, updateLoraMeta, uploadLoraPreview, getUnassociatedLoras, createLoraRecord } from '@/api/lora';
    import { getBaseModels } from '@/api/baseModel';
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
      { title: '预览', key: 'preview', width: 100 },
      { title: '显示名称', dataIndex: 'display_name', key: 'display_name', ellipsis: true },
      { title: '文件名', dataIndex: 'name', key: 'name', ellipsis: true },
      { title: '状态', key: 'is_available', width: 120 },
      { title: '大小 (MB)', dataIndex: 'size', key: 'size', customRender: ({ text }) => `${(text / 1024 / 1024).toFixed(2)} MB` },
      { title: '基础模型', dataIndex: 'base_model', key: 'base_model' },
      { 
        title: '创建时间',
        dataIndex: 'created',
        key: 'created',
        width: 180 
      },
      { 
        title: '修改时间',
        dataIndex: 'modified',
        key: 'modified',
        width: 180 
      },
      { title: '操作', key: 'action', width: 220 },
    ];

    const data = ref([]);
    const pagination = reactive({ current: 1, pageSize: 10, total: 0 });

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
    const baseModelFilter = ref('');
    
    // Base models for selection
    const baseModels = ref([]);
    const baseModelsLoading = ref(false);

    const fetchLoras = async (page = 1, pageSize = 10, name = null, baseModel = null) => {
      loading.value = true;
      try {
        const response = await getLoras(page, pageSize, name, baseModel);
        console.log('LoRA API Response:', response); // 调试日志
        
        if (response && response.code === 200) {
          // 使用防护函数确保数据是数组，并映射字段
          const rawData = ensureArray(response.data?.items || response.data || response);
          data.value = rawData.map(item => ({
            ...item,
            size: item.file_size, // 映射file_size到size
            created: item.created_at, // 映射created_at到created
            modified: item.updated_at, // 映射updated_at到modified
          }));
          pagination.total = response.data?.total || 0;
          pagination.current = response.data?.page || 1;
          pagination.pageSize = response.data?.pageSize || 10;
        } else {
          data.value = [];
          console.warn('LoRA API返回错误或非标准格式:', response);
          message.error(response?.message || 'Failed to fetch LoRA models');
        }
      } catch (error) {
        console.error('Error fetching LoRA models:', error);
        data.value = []; // 确保data是数组
        message.error('Error fetching LoRA models');
      } finally {
        loading.value = false;
      }
    };

    const onSearch = (searchValue) => {
      pagination.current = 1; // Reset to first page on new search
      fetchLoras(pagination.current, pagination.pageSize, searchValue, baseModelFilter.value);
    };

    const onBaseModelFilter = (baseModel) => {
      pagination.current = 1; // Reset to first page on new filter
      fetchLoras(pagination.current, pagination.pageSize, searchQuery.value, baseModel);
    };

    // Fetch base models for selection
    const fetchBaseModels = async () => {
      baseModelsLoading.value = true;
      try {
        const response = await getBaseModels();
        if (response && response.code === 200) {
          baseModels.value = response.data.items || [];
        } else {
          baseModels.value = [];
          console.warn('Failed to fetch base models:', response);
        }
      } catch (error) {
        console.error('Error fetching base models:', error);
        baseModels.value = [];
      } finally {
        baseModelsLoading.value = false;
      }
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

      // Fetch base models if not already loaded
      if (baseModels.value.length === 0) {
        await fetchBaseModels();
      }

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
      
      // Fetch base models if not already loaded
      if (baseModels.value.length === 0) {
        await fetchBaseModels();
      }
      
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
      // 如果记录在数据库中，就认为是已管理的，可以编辑
      if (record.id) {
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
    const handleDelete = async (loraId, is_managed) => {
      if (!is_managed) {
        message.info('This LoRA has no metadata to delete.');
        return;
      }
      try {
        await deleteLora(loraId);
        message.success('LoRA metadata deleted successfully');
        fetchLoras(pagination.current, pagination.pageSize);
      } catch (error) {
        console.error('Error deleting LoRA meta:', error);
        message.error(error.response?.data?.detail || 'Error deleting LoRA meta');
      }
    };

    const toggleAvailability = async (record) => {
      try {
        const newStatus = !record.is_available;
        await updateLoraMeta(record.id, { is_available: newStatus });
        message.success(`LoRA ${newStatus ? '启用' : '禁用'}成功`);
        fetchLoras(pagination.current, pagination.pageSize, searchQuery.value, baseModelFilter.value);
      } catch (error) {
        console.error('Error toggling LoRA availability:', error);
        message.error(error.response?.data?.detail || '切换状态失败');
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
      fetchBaseModels();
    });

    return {
      baseURL,
      loading,
      columns,
      data,
      tableData,
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
      handleUniversalEdit,
      toggleAvailability,
      baseModels,
      baseModelsLoading,
      fetchBaseModels,
      baseModelFilter,
      onBaseModelFilter,
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