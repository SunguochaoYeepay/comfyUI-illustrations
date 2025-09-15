<template>
  <a-config-provider :theme="{
    token: {
      colorPrimary: '#00b96b',
    },
    algorithm: theme.darkAlgorithm,
  }">
    <a-layout style="min-height: 100vh">
      <a-layout-sider v-model:collapsed="collapsed" collapsible>
        <div class="logo" />
        <a-menu v-model:selectedKeys="selectedKeys" theme="dark" mode="inline" @click="handleMenuClick">
          <a-menu-item key="/dashboard">
            <pie-chart-outlined />
            <span>Dashboard</span>
          </a-menu-item>

          <a-menu-item key="/lora-management">
            <cloud-upload-outlined />
            <span>LoRA模型管理</span>
          </a-menu-item>
          <a-menu-item key="/base-model-management">
            <database-outlined />
            <span>基础模型管理</span>
          </a-menu-item>
        </a-menu>
      </a-layout-sider>
      <a-layout>
        <a-layout-header style="background: #141414; padding: 0" />
        <a-layout-content style="margin: 0 16px">
          <a-breadcrumb style="margin: 16px 0">
            <a-breadcrumb-item>User</a-breadcrumb-item>
            <a-breadcrumb-item>Bill</a-breadcrumb-item>
          </a-breadcrumb>
          <div :style="{ padding: '24px', background: '#141414', minHeight: '360px' }">
            <router-view v-slot="{ Component }">
              <component :is="Component" v-if="Component" />
            </router-view>
          </div>
        </a-layout-content>
        <a-layout-footer style="text-align: center">
          YeePay Admin ©2024 Created by Trae
        </a-layout-footer>
      </a-layout>
    </a-layout>
  </a-config-provider>
</template>
<script setup>
import { ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import {
  PieChartOutlined,
  PictureOutlined,
  CloudUploadOutlined,
  DatabaseOutlined,
} from '@ant-design/icons-vue';
import { theme, ConfigProvider, Layout, Breadcrumb, Menu } from 'ant-design-vue';

const collapsed = ref(false);
const selectedKeys = ref(['/dashboard']);

const router = useRouter();
const route = useRoute();

const menuKeys = ['/', '/image-management', '/lora-management', '/base-model-management'];

watch(
  () => route.path,
  (newPath) => {
    const matchingKey = menuKeys.find(key => newPath.startsWith(key));
    if (matchingKey) {
      selectedKeys.value = [matchingKey];
    }
  },
  { immediate: true }
);

const handleMenuClick = ({ key }) => {
  router.push(key);
};
</script>
<style scoped>
.logo {
  height: 32px;
  margin: 16px;
  background: rgba(255, 255, 255, 0.3);
}
</style>