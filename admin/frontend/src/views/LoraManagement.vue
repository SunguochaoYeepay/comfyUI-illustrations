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
        <a-select
          v-model:value="categoryFilter"
          placeholder="选择分类"
          style="width: 150px; margin-left: 8px;"
          @change="onCategoryFilter"
          allow-clear
        >
          <a-select-option 
            v-for="category in loraCategories" 
            :key="category" 
            :value="category"
          >
            {{ category }}
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
          <div v-if="record.preview_image_path">
            <a-image
              :width="64"
              :src="`/api/${record.preview_image_path}?t=${new Date().getTime()}`"
              :preview="{ src: `/api/${record.preview_image_path}?t=${new Date().getTime()}` }"
              style="border-radius: 4px;"
              @error="(e) => console.error('图片加载失败:', e.target.src, '原始路径:', record.preview_image_path)"
            />
            <div style="font-size: 10px; color: #999; margin-top: 2px;">
              {{ record.preview_image_path.split('/').pop() }}
            </div>
          </div>
          <span v-else style="color: #999;">无预览</span>
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
              v-if="!record.is_available && record.id"
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

    <!-- Edit Drawer -->
    <a-drawer
      v-model:open="editModalOpen"
      title="编辑LoRA元数据"
      placement="right"
      width="600px"
      @close="editModalOpen = false"
    >
      <a-form :model="editForm" layout="vertical">
        <a-form-item label="系统编码">
          <a-input v-model:value="editForm.code" placeholder="不可变的系统标识符" disabled />
          <div style="margin-top: 4px; font-size: 12px; color: #666;">
            系统内部使用的唯一标识符，不可修改
          </div>
        </a-form-item>
        <a-form-item label="显示名称">
          <a-input v-model:value="editForm.display_name" placeholder="用户友好的名称" />
          <div style="margin-top: 4px; font-size: 12px; color: #666;">
            在前端用户界面中显示的名称
          </div>
        </a-form-item>
        <a-form-item label="文件名">
          <div style="display: flex; gap: 8px;">
            <a-auto-complete
              v-model:value="editForm.new_name"
              :options="filenameOptions"
              placeholder="输入新文件名或选择未管理的模型"
              style="flex: 1;"
            />
            <a-button 
              @click="refreshEditFilenameOptions" 
              :loading="editFilenameLoading"
              type="default"
              title="刷新文件名选项"
            >
              <template #icon>
                <ReloadOutlined />
              </template>
              刷新
            </a-button>
          </div>
          <div style="margin-top: 4px; font-size: 12px; color: #666;">
            ComfyUI使用的文件名，通常不需要修改。点击刷新按钮更新可选文件列表
          </div>
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
        <a-form-item label="分类">
          <a-select 
            v-model:value="editForm.category" 
            placeholder="选择分类"
            :loading="loraCategoriesLoading"
            allow-clear
          >
            <a-select-option 
              v-for="category in loraCategories" 
              :key="category" 
              :value="category"
            >
              {{ category }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="描述">
          <a-textarea v-model:value="editForm.description" :rows="4" />
        </a-form-item>
        <a-form-item label="预览图片">
          <a-upload
            :file-list="fileList"
            :before-upload="beforeUpload"
            @remove="handleRemove"
            @change="handleUploadChange"
            :max-count="1"
            accept="image/*"
            list-type="picture-card"
            :show-upload-list="true"
          >
            <div v-if="fileList.length < 1">
              <upload-outlined />
              <div style="margin-top: 8px;">上传图片</div>
              <div style="font-size: 12px; color: #999;">支持 JPG、PNG、GIF 格式</div>
            </div>
          </a-upload>
        </a-form-item>
      </a-form>
      
      <template #footer>
        <div style="text-align: right;">
          <a-button style="margin-right: 8px;" @click="editModalOpen = false">
            取消
          </a-button>
          <a-button type="primary" @click="handleEdit" :loading="editModalLoading">
            保存
          </a-button>
        </div>
      </template>
    </a-drawer>

    <!-- Create Drawer -->
    <a-drawer
      v-model:open="createModalOpen"
      title="创建新LoRA记录"
      placement="right"
      width="600px"
      @close="createModalOpen = false"
    >
      <a-form :model="createForm" layout="vertical">
        <a-form-item label="系统编码" required>
          <a-input v-model:value="createForm.code" placeholder="不可变的系统标识符" />
          <div style="margin-top: 4px; font-size: 12px; color: #666;">
            系统内部使用的唯一标识符，创建后不可修改 (如: flux-logo-v1, qwen-poster-v1)
          </div>
        </a-form-item>
        <a-form-item label="模型文件" required>
          <div style="display: flex; gap: 8px;">
            <a-select
              v-model:value="createForm.filename"
              placeholder="选择模型文件"
              :loading="unassociatedLoading"
              style="flex: 1;"
            >
              <a-select-option v-for="filename in unassociatedLoras" :key="filename" :value="filename">
                {{ filename }}
              </a-select-option>
            </a-select>
            <a-button 
              @click="refreshUnassociatedLoras" 
              :loading="unassociatedLoading"
              type="default"
              title="刷新LoRA文件列表"
            >
              <template #icon>
                <ReloadOutlined />
              </template>
              刷新
            </a-button>
          </div>
          <div style="margin-top: 4px; font-size: 12px; color: #666;">
            点击刷新按钮检测新增的LoRA文件
          </div>
        </a-form-item>
        <a-form-item label="显示名称" required>
          <a-input v-model:value="createForm.display_name" placeholder="用户友好的名称" />
          <div style="margin-top: 4px; font-size: 12px; color: #666;">
            在前端用户界面中显示的名称 (如: 品牌LOGO设计, 电商海报)
          </div>
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
        <a-form-item label="分类">
          <a-select 
            v-model:value="createForm.category" 
            placeholder="选择分类"
            :loading="loraCategoriesLoading"
            allow-clear
          >
            <a-select-option 
              v-for="category in loraCategories" 
              :key="category" 
              :value="category"
            >
              {{ category }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="描述">
          <a-textarea v-model:value="createForm.description" :rows="4" />
        </a-form-item>
      </a-form>
      
      <template #footer>
        <div style="text-align: right;">
          <a-button style="margin-right: 8px;" @click="createModalOpen = false">
            取消
          </a-button>
          <a-button type="primary" @click="handleCreate" :loading="createModalLoading">
            创建
          </a-button>
        </div>
      </template>
    </a-drawer>
  </div>
</template>

<script>
import { ref, reactive, onMounted, computed } from 'vue';
    import { 
      getLoras, 
      deleteLora, 
      updateLoraMeta, 
      uploadLoraPreview, 
      getUnassociatedLoras, 
      createLoraRecord, 
      getLoraCategories 
    } from '@/api/lora';
    import { getBaseModels } from '@/api/baseModel';
import { message, Image as AImage, Space as ASpace, Upload, Popconfirm, Modal, Form, Input, Textarea, Button, Select, Tag, AutoComplete as AAutoComplete, Drawer } from 'ant-design-vue';
import { UploadOutlined, PlusOutlined, ReloadOutlined } from '@ant-design/icons-vue';

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
    ADrawer: Drawer,
  },
  setup() {
    const baseURL = import.meta.env.VITE_API_BASE_URL || '';
    const loading = ref(false);

    const columns = [
      { title: '预览', key: 'preview', width: 100 },
      { title: '系统编码', dataIndex: 'code', key: 'code', width: 120, ellipsis: true },
      { title: '显示名称', dataIndex: 'display_name', key: 'display_name', ellipsis: true },
      { title: '文件名', dataIndex: 'name', key: 'name', ellipsis: true },
      { title: '分类', dataIndex: 'category', key: 'category', width: 120 },
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
    const editFilenameLoading = ref(false);
    const editForm = reactive({ code: '', name: '', new_name: '', display_name: '', base_model: '', category: '', description: '' });
    const currentEditId = ref(null); // 当前编辑的LoRA ID
    const fileList = ref([]);
    const filenameOptions = ref([]);

    // Create Modal State
    const createModalOpen = ref(false);
    const createModalLoading = ref(false);
    const unassociatedLoras = ref([]);
    const unassociatedLoading = ref(false);
    const createForm = reactive({ code: '', filename: null, display_name: '', base_model: '', category: '', description: '' });

    const searchQuery = ref('');
    const baseModelFilter = ref('');
    const categoryFilter = ref('');
    
    // Base models for selection
    const baseModels = ref([]);
    const baseModelsLoading = ref(false);
    
    // LoRA categories for selection
    const loraCategories = ref([]);
    const loraCategoriesLoading = ref(false);

    const fetchLoras = async (page = 1, pageSize = 10, name = null, baseModel = null, category = null) => {
      loading.value = true;
      try {
        const response = await getLoras(page, pageSize, name, baseModel, category);
        console.log('LoRA API Response:', response); // 调试日志
        
        if (response && response.loras && Array.isArray(response.loras)) {
          // 直接使用新的API格式
          data.value = response.loras.map(item => ({
            ...item,
            size: item.file_size, // 映射file_size到size
            created: item.created_at, // 映射created_at到created
            modified: item.updated_at, // 映射updated_at到modified
          }));
          pagination.total = response.total || 0;
          pagination.current = page;
          pagination.pageSize = pageSize;
        } else {
          data.value = [];
          console.warn('LoRA API返回错误或非标准格式:', response);
          message.error('Failed to fetch LoRA models');
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
      fetchLoras(pagination.current, pagination.pageSize, searchValue, baseModelFilter.value, categoryFilter.value);
    };

    const onBaseModelFilter = (baseModel) => {
      pagination.current = 1; // Reset to first page on new filter
      fetchLoras(pagination.current, pagination.pageSize, searchQuery.value, baseModel, categoryFilter.value);
    };

    const onCategoryFilter = (category) => {
      pagination.current = 1; // Reset to first page on new filter
      fetchLoras(pagination.current, pagination.pageSize, searchQuery.value, baseModelFilter.value, category);
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

    // 获取LoRA分类列表
    const fetchLoraCategories = async () => {
      loraCategoriesLoading.value = true;
      try {
        const response = await getLoraCategories();
        if (response && response.code === 200 && response.data) {
          loraCategories.value = response.data;
        } else {
          console.warn('Failed to fetch LoRA categories:', response);
        }
      } catch (error) {
        console.error('Error fetching LoRA categories:', error);
        loraCategories.value = [];
      } finally {
        loraCategoriesLoading.value = false;
      }
    };

    // --- Edit Logic ---
    const showEditModal = async (record) => {
      editForm.code = record.code;
      editForm.name = record.name;
      editForm.new_name = record.name;
      editForm.display_name = record.display_name;
      editForm.base_model = record.base_model;
      editForm.category = record.category;
      editForm.description = record.description;
      currentEditId.value = record.id; // 保存当前编辑的LoRA ID
      fileList.value = [];
      editModalOpen.value = true;

      // Fetch base models if not already loaded
      if (baseModels.value.length === 0) {
        await fetchBaseModels();
      }
      
      // Fetch LoRA categories if not already loaded
      if (loraCategories.value.length === 0) {
        await fetchLoraCategories();
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

    // 刷新编辑对话框的文件名选项
    const refreshEditFilenameOptions = async () => {
      editFilenameLoading.value = true;
      try {
        const response = await getUnassociatedLoras();
        if (response.code === 200) {
          const options = response.data.map(name => ({ value: name }));
          // 确保当前文件名在选项中
          if (!options.some(opt => opt.value === editForm.name)) {
            options.unshift({ value: editForm.name });
          }
          const oldCount = filenameOptions.value.length;
          filenameOptions.value = options;
          const newCount = filenameOptions.value.length;
          
          if (newCount > oldCount) {
            message.success(`发现 ${newCount - oldCount} 个新的LoRA文件`);
          } else if (newCount === oldCount) {
            message.info('没有发现新的LoRA文件');
          } else {
            message.info(`文件名选项已更新，当前有 ${newCount} 个可选文件`);
          }
        } else {
          message.error(response.message || '刷新失败');
        }
      } catch (error) {
        console.error('Error refreshing edit filename options:', error);
        message.error('刷新文件名选项失败');
      } finally {
        editFilenameLoading.value = false;
      }
    };

    const handleEdit = async () => {
      editModalLoading.value = true;
      try {
        const metaData = {
          display_name: editForm.display_name,
          base_model: editForm.base_model,
          category: editForm.category,
          description: editForm.description,
          new_name: editForm.new_name,
        };
        await updateLoraMeta(editForm.code, metaData);

        // 上传预览图片
        if (fileList.value.length > 0 && currentEditId.value) {
          const formData = new FormData();
          formData.append('file', fileList.value[0].originFileObj || fileList.value[0]);
          await uploadLoraPreview(currentEditId.value, formData);
        }
        
        message.success('LoRA信息更新成功');
        editModalOpen.value = false;
        fetchLoras(pagination.current, pagination.pageSize, searchQuery.value, baseModelFilter.value, categoryFilter.value);
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
      
      // Fetch LoRA categories if not already loaded
      if (loraCategories.value.length === 0) {
        await fetchLoraCategories();
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

    // 刷新未关联的LoRA文件列表
    const refreshUnassociatedLoras = async () => {
      unassociatedLoading.value = true;
      try {
        const response = await getUnassociatedLoras();
        if (response.code === 200) {
          const oldCount = unassociatedLoras.value.length;
          unassociatedLoras.value = response.data;
          const newCount = unassociatedLoras.value.length;
          
          if (newCount > oldCount) {
            message.success(`发现 ${newCount - oldCount} 个新的LoRA文件`);
          } else if (newCount === oldCount) {
            message.info('没有发现新的LoRA文件');
          } else {
            message.info(`LoRA文件列表已更新，当前有 ${newCount} 个未关联文件`);
          }
        } else {
          message.error(response.message || '刷新失败');
        }
      } catch (error) {
        console.error('Error refreshing unassociated models:', error);
        message.error('刷新LoRA文件列表失败');
      } finally {
        unassociatedLoading.value = false;
      }
    };

    const handleCreate = async () => {
      if (!createForm.code || !createForm.filename || !createForm.display_name) {
        message.warning('系统编码、模型文件和显示名称都是必需的。');
        return;
      }
      createModalLoading.value = true;
      try {
        // 转换数据格式以匹配后端schema
        const loraData = {
          code: createForm.code, // 添加code字段
          name: createForm.filename, // 将filename映射为name
          display_name: createForm.display_name,
          base_model: createForm.base_model,
          description: createForm.description
        };
        const response = await createLoraRecord(loraData);
        message.success(response.message || 'LoRA record created successfully');
        createModalOpen.value = false;
        fetchLoras(1, pagination.pageSize); // Go to first page to see the new record
      } catch (error) {
        console.error('Error creating LoRA record:', error);
        const errorMessage = error.response?.data?.detail || error.message || 'Error creating LoRA record';
        message.error(errorMessage);
      } finally {
        createModalLoading.value = false;
      }
    };

    const handleUniversalEdit = (record) => {
      // 如果记录有ID或者是已管理的记录，就认为是可编辑的
      if (record.id || record.is_managed) {
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
      if (!loraId) {
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
        await updateLoraMeta(record.code, { is_available: newStatus });
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
      const isImage = file.type.startsWith('image/');
      const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'];
      
      if (!isImage || !allowedTypes.includes(file.type)) {
        message.error('只能上传 JPG、PNG、GIF、WebP 格式的图片文件！');
        return false;
      }
      
      const isLt5M = file.size / 1024 / 1024 < 5;
      if (!isLt5M) {
        message.error('图片大小不能超过 5MB！');
        return false;
      }
      
      // 添加到文件列表
      fileList.value = [file];
      return false; // Prevent auto upload
    };

    const handleUploadChange = (info) => {
      if (info.file.status === 'removed') {
        fileList.value = [];
      }
    };

    const handleRemove = () => {
      fileList.value = [];
    };

    onMounted(() => {
      fetchLoras();
      fetchBaseModels();
      fetchLoraCategories();
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
      editFilenameLoading,
      editForm,
      showEditModal,
      handleEdit,
      fileList,
      beforeUpload,
      handleUploadChange,
      handleRemove,
      filenameOptions,
      refreshEditFilenameOptions,
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
      categoryFilter,
      onCategoryFilter,
      loraCategories,
      loraCategoriesLoading,
      fetchLoraCategories,
      refreshUnassociatedLoras,
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