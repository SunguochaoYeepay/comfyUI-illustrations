<template>
  <div>
    <div class="header-bar">
      <h1>模型管理</h1>
      <div class="header-actions">
        <a-input-search
          v-model:value="searchQuery"
          placeholder="搜索模型名称"
          style="width: 250px;"
          @search="onSearch"
          allow-clear
        />
        <a-button type="primary" @click="showCreateModel" style="margin-left: 8px;">
          <plus-outlined /> 创建基础模型
        </a-button>
      </div>
    </div>
    <a-table
      :columns="columns"
      :data-source="tableData"
      row-key="id"
      :pagination="false"
      :loading="loading"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'status'">
          <a-tag :color="record.is_available ? 'green' : 'red'">
            {{ record.is_available ? '可用' : '不可用' }}
          </a-tag>
        </template>
        <template v-if="column.key === 'action'">
          <a-space>
            <a @click="showEditModel(record)">编辑</a>
            <a @click="toggleAvailability(record)">
              {{ record.is_available ? '禁用' : '启用' }}
            </a>
            <a-popconfirm 
              v-if="!record.is_available"
              title="确定删除吗?" 
              @confirm="deleteModel(record.id)"
            >
              <a style="color: #ff4d4f;">删除</a>
            </a-popconfirm>
          </a-space>
        </template>
      </template>
    </a-table>

    <a-drawer
      v-model:open="modelVisible"
      :title="modelTitle"
      placement="right"
      width="600px"
      @close="handleDrawerClose"
    >
      <a-form :model="formState" layout="vertical" class="model-form">
        <a-form-item label="模型名称" required>
          <a-input v-model:value="formState.name" placeholder="唯一标识符" />
        </a-form-item>
        
        <a-form-item label="显示名称" required>
          <a-input v-model:value="formState.display_name" placeholder="用户看到的名称" />
        </a-form-item>
        
        <a-form-item label="模型类型" required>
          <a-select v-model:value="formState.model_type" placeholder="选择模型类型">
            <a-select-option value="flux">Flux</a-select-option>
            <a-select-option value="qwen">Qwen</a-select-option>
            <a-select-option value="wan">Wan</a-select-option>
            <!-- flux1选项已移除，只保留FLUX.1 Kontext -->
            <a-select-option value="gemini">Gemini</a-select-option>
          </a-select>
        </a-form-item>
        
        <a-form-item label="描述">
          <a-textarea v-model:value="formState.description" :rows="3" placeholder="模型描述信息" />
        </a-form-item>
        
        <a-divider>工作流关联</a-divider>
        
        <a-form-item label="关联工作流" required>
          <a-select 
            v-model:value="formState.workflow_id" 
            placeholder="选择关联的工作流"
            :loading="workflowsLoading"
            show-search
            :filter-option="(input, option) => option.children.toLowerCase().indexOf(input.toLowerCase()) >= 0"
          >
            <a-select-option 
              v-for="workflow in workflows" 
              :key="workflow.id" 
              :value="workflow.id"
            >
              {{ workflow.name }} - {{ workflow.description || '无描述' }}
            </a-select-option>
          </a-select>
          <div style="margin-top: 4px; font-size: 12px; color: #666;">
            基础模型必须关联至少一个工作流
          </div>
        </a-form-item>
        
        <!-- 工作流模板路径已移除，完全数据库化 -->
        
        <a-divider>模型文件配置</a-divider>
        
        <a-form-item label="UNet文件">
          <a-input 
            v-model:value="formState.unet_file" 
            placeholder="从关联工作流中自动加载" 
            readonly 
          />
          <div style="margin-top: 4px; font-size: 12px; color: #666;">
            从关联工作流的UNet/模型加载器节点中自动提取
          </div>
        </a-form-item>
        
        <a-form-item label="CLIP文件">
          <a-input 
            v-model:value="formState.clip_file" 
            placeholder="从关联工作流中自动加载" 
            readonly 
          />
          <div style="margin-top: 4px; font-size: 12px; color: #666;">
            从关联工作流的CLIP加载器节点中自动提取
          </div>
        </a-form-item>
        
        <a-form-item label="VAE文件">
          <a-input 
            v-model:value="formState.vae_file" 
            placeholder="从关联工作流中自动加载" 
            readonly 
          />
          <div style="margin-top: 4px; font-size: 12px; color: #666;">
            从关联工作流的VAE加载器节点中自动提取
          </div>
        </a-form-item>
        
        <a-form-item label="预览图">
          <a-input-group compact>
            <a-input v-model:value="formState.preview_image_path" placeholder="选择预览图" style="width: calc(100% - 80px)" />
            <a-button type="primary" @click="selectFile('preview_image_path')" style="width: 80px">选择</a-button>
          </a-input-group>
        </a-form-item>
        
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="可用状态">
              <a-switch v-model:checked="formState.is_available" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="默认模型">
              <a-switch v-model:checked="formState.is_default" />
            </a-form-item>
          </a-col>
        </a-row>
      </a-form>
      
      <template #footer>
        <div style="text-align: right">
          <a-button style="margin-right: 8px" @click="handleDrawerClose">取消</a-button>
          <a-button type="primary" @click="handleModelOk">确定</a-button>
        </div>
      </template>
    </a-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, watch } from 'vue';
import { getBaseModels, createBaseModel, updateBaseModel, deleteBaseModel } from '@/api/baseModel';
import { getWorkflows } from '@/api/workflow';
import { message } from 'ant-design-vue';
import { PlusOutlined } from '@ant-design/icons-vue';

const columns = [
  { title: '模型名称', dataIndex: 'name', key: 'name', width: 120 },
  { title: '显示名称', dataIndex: 'display_name', key: 'display_name', width: 150 },
  { title: '类型', dataIndex: 'model_type', key: 'model_type', width: 100 },
  { title: '状态', key: 'status', width: 80 },
  { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true },
  { title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 150 },
  { title: '操作', key: 'action', width: 120 },
];

const data = ref([]);
const loading = ref(false);
const searchQuery = ref('');
const workflows = ref([]);
const workflowsLoading = ref(false);

// 计算属性确保数据始终是数组
const tableData = computed(() => {
  return Array.isArray(data.value) ? data.value : [];
});

// 计算属性：根据选择的工作流自动生成模板路径
const selectedWorkflow = computed(() => {
  if (!formState.workflow_id || !workflows.value.length) return null;
  return workflows.value.find(w => w.id === formState.workflow_id);
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
const modelVisible = ref(false);
const modelTitle = ref('');
const isEdit = ref(false);
const currentModelId = ref(null);

const formState = reactive({
  name: '',
  display_name: '',
  model_type: '',
  description: '',
  unet_file: '',
  clip_file: '',
  vae_file: '',
  // template_path 已移除，完全数据库化
  workflow_id: null, // 新增：关联的工作流ID
  preview_image_path: '',
  is_available: false,
  is_default: false,
});

const fetchBaseModels = async () => {
  loading.value = true;
  try {
    const response = await getBaseModels();
    console.log('Base Models API Response:', response); // 调试日志
    
    // 使用防护函数确保数据是数组
    data.value = ensureArray(response);
    
    if (data.value.length === 0 && response) {
      console.warn('Base Models API返回的数据不是数组格式:', response);
    }
  } catch (error) {
    console.error('获取基础模型列表失败:', error);
    data.value = []; // 确保data是数组
  }
  loading.value = false;
};

// 获取工作流列表
const fetchWorkflows = async () => {
  workflowsLoading.value = true;
  try {
    const response = await getWorkflows({ page: 1, pageSize: 1000 }); // 获取所有工作流
    workflows.value = response.data || response || [];
  } catch (error) {
    console.error('获取工作流列表失败:', error);
    workflows.value = [];
  }
  workflowsLoading.value = false;
};

// 搜索功能
const onSearch = (searchValue) => {
  if (!searchValue) {
    fetchBaseModels();
    return;
  }
  
  // 简单的客户端搜索
  const filteredData = data.value.filter(item => 
    item.name?.toLowerCase().includes(searchValue.toLowerCase()) ||
    item.description?.toLowerCase().includes(searchValue.toLowerCase())
  );
  data.value = filteredData;
};

// 从工作流JSON中提取模型文件配置
const extractModelFilesFromWorkflow = (workflowJson) => {
  const modelFiles = {
    unet_file: '',
    clip_file: '',
    vae_file: ''
  };
  
  if (!workflowJson) {
    return modelFiles;
  }
  
  // 检查工作流JSON的结构
  let nodes = null;
  if (workflowJson.nodes) {
    nodes = workflowJson.nodes;
  } else if (typeof workflowJson === 'object' && !workflowJson.nodes) {
    // 可能是直接的节点字典格式
    nodes = workflowJson;
  } else {
    return modelFiles;
  }
  
  // 查找UNet/模型加载器节点
  for (const [nodeId, node] of Object.entries(nodes)) {
    const classType = node.class_type;
    const inputs = node.inputs || {};
    
    // 识别不同类型的模型加载器
    if (classType === 'CheckpointLoaderSimple' || classType === 'UNETLoader') {
      if (inputs.ckpt_name) {
        // 将文件名转换为完整路径
        modelFiles.unet_file = convertToFullPath(inputs.ckpt_name, 'unet');
      }
      if (inputs.unet_name) {
        // 将文件名转换为完整路径
        modelFiles.unet_file = convertToFullPath(inputs.unet_name, 'unet');
      }
    }
    
    // 识别CLIP加载器
    if (classType === 'CLIPLoader' || classType === 'CLIPTextEncode' || classType === 'DualCLIPLoader') {
      if (inputs.clip_name) {
        modelFiles.clip_file = convertToFullPath(inputs.clip_name, 'clip');
      }
      if (inputs.clip_name1) {
        modelFiles.clip_file = convertToFullPath(inputs.clip_name1, 'clip');
      }
      if (inputs.clip_name2) {
        modelFiles.clip_file = convertToFullPath(inputs.clip_name2, 'clip');
      }
    }
    
    // 识别VAE加载器
    if (classType === 'VAELoader') {
      if (inputs.vae_name) {
        modelFiles.vae_file = convertToFullPath(inputs.vae_name, 'vae');
      }
    }
  }
  
  return modelFiles;
};

// 将文件名转换为完整的系统路径
const convertToFullPath = (filename, type) => {
  if (!filename) return '';
  
  // 如果已经是完整路径，直接返回
  if (filename.includes('/') || filename.includes('\\')) {
    return filename;
  }
  
  // 根据文件类型添加目录前缀
  const pathMapping = {
    'unet': 'unet/',
    'clip': 'clip/',
    'vae': 'vae/',
    'checkpoint': 'checkpoints/'
  };
  
  const prefix = pathMapping[type] || '';
  return prefix + filename;
};

// 监听工作流选择变化，自动更新模型文件（不再需要模板路径）
watch(() => formState.workflow_id, (newWorkflowId) => {
  if (newWorkflowId && selectedWorkflow.value) {
    // 从工作流JSON中提取模型文件配置
    const modelFiles = extractModelFilesFromWorkflow(selectedWorkflow.value.workflow_json);
    
    formState.unet_file = modelFiles.unet_file;
    formState.clip_file = modelFiles.clip_file;
    formState.vae_file = modelFiles.vae_file;
  } else {
    formState.unet_file = '';
    formState.clip_file = '';
    formState.vae_file = '';
  }
});

onMounted(() => {
  fetchBaseModels();
  fetchWorkflows();
});

const showCreateModel = () => {
  isEdit.value = false;
  modelTitle.value = '创建基础模型';
  Object.assign(formState, {
    name: '',
    display_name: '',
    model_type: '',
    description: '',
    unet_file: '',
    clip_file: '',
    vae_file: '',
    // template_path 已移除，完全数据库化
    workflow_id: null,
    preview_image_path: '',
    is_available: false,
    is_default: false,
  });
  modelVisible.value = true;
};

const showEditModel = (record) => {
  isEdit.value = true;
  modelTitle.value = '编辑基础模型';
  currentModelId.value = record.id;
  Object.assign(formState, record);
  modelVisible.value = true;
};

// 抽屉关闭处理
const handleDrawerClose = () => {
  modelVisible.value = false;
  // 重置表单
  Object.assign(formState, {
    name: '',
    display_name: '',
    model_type: '',
    description: '',
    unet_file: '',
    clip_file: '',
    vae_file: '',
    // template_path 已移除，完全数据库化
    workflow_id: null,
    preview_image_path: '',
    is_available: false,
    is_default: false,
  });
};

// 文件选择功能（仅用于预览图）
const selectFile = (fieldName) => {
  // 只允许选择预览图文件
  if (fieldName !== 'preview_image_path') {
    return;
  }
  
  // 创建文件选择对话框
  const input = document.createElement('input');
  input.type = 'file';
  input.accept = 'image/*';
  
  input.onchange = (event) => {
    const file = event.target.files[0];
    if (file) {
      // 这里可以根据需要处理文件路径
      // 在实际应用中，可能需要上传文件到服务器
      formState[fieldName] = file.name;
    }
  };
  
  input.click();
};

const handleModelOk = async () => {
  // 表单验证
  if (!formState.name || !formState.display_name || !formState.model_type) {
    message.error('请填写必填字段：模型名称、显示名称、模型类型');
    return;
  }
  
  if (!formState.workflow_id) {
    message.error('基础模型必须关联至少一个工作流');
    return;
  }
  
  try {
    if (isEdit.value) {
      await updateBaseModel(currentModelId.value, formState);
      message.success('更新成功');
    } else {
      await createBaseModel(formState);
      message.success('创建成功');
    }
    handleDrawerClose(); // 使用统一的关闭处理
    fetchBaseModels();
  } catch (error) {
    message.error(isEdit.value ? '更新失败' : '创建失败');
  }
};

const deleteModel = async (id) => {
  try {
    await deleteBaseModel(id);
    message.success('删除成功');
    fetchBaseModels();
  } catch (error) {
    message.error('删除失败');
  }
};

const toggleAvailability = async (record) => {
  try {
    const newStatus = !record.is_available;
    await updateBaseModel(record.id, { is_available: newStatus });
    message.success(`基础模型${newStatus ? '启用' : '禁用'}成功`);
    fetchBaseModels();
  } catch (error) {
    console.error('Error toggling base model availability:', error);
    message.error('切换状态失败');
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

.model-form {
  padding: 0 8px;
}

.model-form .ant-form-item {
  margin-bottom: 16px;
}

.model-form .ant-input-group {
  display: flex;
}

.model-form .ant-input-group .ant-input {
  border-top-right-radius: 0;
  border-bottom-right-radius: 0;
}

.model-form .ant-input-group .ant-btn {
  border-top-left-radius: 0;
  border-bottom-left-radius: 0;
  border-left: 0;
}
</style>
