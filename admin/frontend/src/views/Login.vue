<template>
  <div class="login-container">
    <a-card title="Login" :style="{ width: '300px' }">
      <a-form>
        <a-form-item>
          <a-input v-model:value="username" placeholder="Username">
            <template #prefix><user-outlined /></template>
          </a-input>
        </a-form-item>
        <a-form-item>
          <a-input-password v-model:value="password" placeholder="Password">
            <template #prefix><lock-outlined /></template>
          </a-input-password>
        </a-form-item>
        <a-form-item>
          <a-button type="primary" block @click="handleLogin">Login</a-button>
        </a-form-item>
      </a-form>
    </a-card>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { UserOutlined, LockOutlined } from '@ant-design/icons-vue';
import { useRouter } from 'vue-router';

const router = useRouter();
const username = ref('');
const password = ref('');

const handleLogin = () => {
  // Mock login
  if (username.value === 'admin' && password.value === 'admin') {
    router.push('/');
  }
};
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background: #001529;
}
</style>