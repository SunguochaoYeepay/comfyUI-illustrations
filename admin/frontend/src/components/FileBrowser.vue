<template>
  <a-modal
    :open="visible"
    title="File Browser"
    @cancel="handleCancel"
    @ok="handleOk"
    width="800px"
  >
    <div class="file-browser">
      <div class="breadcrumb-bar">
        <a-breadcrumb>
          <a-breadcrumb-item v-for="(part, index) in currentPathParts" :key="index">
            <a @click="navigateToPath(index)">{{ part }}</a>
          </a-breadcrumb-item>
        </a-breadcrumb>
      </div>
      <a-list
        :loading="loading"
        :data-source="items"
        item-layout="horizontal"
        class="file-list"
      >
        <template #renderItem="{ item }">
          <a-list-item
            @click="handleItemClick(item)"
            :class="{ 'selected': selectedFile === item.path }"
          >
            <a-list-item-meta>
              <template #title>
                <a>{{ item.name }}</a>
              </template>
              <template #avatar>
                <folder-outlined v-if="item.is_dir" />
                <file-outlined v-else />
              </template>
            </a-list-item-meta>
          </a-list-item>
        </template>
      </a-list>
    </div>
  </a-modal>
</template>

<script setup>
import { ref, watch, computed } from 'vue';
import { browseFiles } from '@/api/fileSystem';
import { message, Modal as AModal, List as AList, ListItem as AListItem, ListItemMeta as AListItemMeta, Breadcrumb as ABreadcrumb, BreadcrumbItem as ABreadcrumbItem } from 'ant-design-vue';
import { FolderOutlined, FileOutlined } from '@ant-design/icons-vue';

const props = defineProps({
  visible: {
    type: Boolean,
    required: true,
  },
  basePath: {
    type: String,
    default: 'models',
  },
});

const emit = defineEmits(['update:visible', 'select']);

const loading = ref(false);
const items = ref([]);
const currentPath = ref(props.basePath);
const selectedFile = ref(null);

const currentPathParts = computed(() => currentPath.value.split('/').filter(p => p));

const fetchFiles = async (path) => {
  loading.value = true;
  try {
    const response = await browseFiles({ path });
    if (response.code === 200) {
      items.value = response.data;
    } else {
      message.error(response.message || 'Failed to browse files.');
    }
  } catch (error) {
    console.error('Error browsing files:', error);
    message.error('An error occurred while browsing files.');
  } finally {
    loading.value = false;
  }
};

watch(() => props.visible, (newVal) => {
  if (newVal) {
    currentPath.value = props.basePath;
    selectedFile.value = null;
    fetchFiles(props.basePath);
  }
});

const handleItemClick = (item) => {
  if (item.is_dir) {
    currentPath.value = item.path;
    fetchFiles(item.path);
  } else {
    selectedFile.value = item.path;
  }
};

const navigateToPath = (index) => {
  const newPath = currentPathParts.value.slice(0, index + 1).join('/');
  currentPath.value = newPath;
  fetchFiles(newPath);
};

const handleCancel = () => {
  emit('update:visible', false);
};

const handleOk = () => {
  if (selectedFile.value) {
    emit('select', selectedFile.value);
    emit('update:visible', false);
  } else {
    message.warning('Please select a file.');
  }
};
</script>

<style scoped>
.file-browser {
  height: 500px;
  display: flex;
  flex-direction: column;
}
.breadcrumb-bar {
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f0f0f0;
}
.file-list {
  flex-grow: 1;
  overflow-y: auto;
}
.ant-list-item {
  cursor: pointer;
}
.ant-list-item:hover {
  background-color: #f5f5f5;
}
.selected {
  background-color: #e6f7ff;
}
</style>