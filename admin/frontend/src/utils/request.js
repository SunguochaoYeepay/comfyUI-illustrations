import axios from 'axios';
import { message } from 'ant-design-vue';

// 创建 axios 实例
const service = axios.create({
  baseURL: import.meta.env.VITE_APP_BASE_API || '/api', // api 的 base_url
  timeout: 10000, // 请求超时时间
});

// 请求拦截器
service.interceptors.request.use(
  (config) => {
    // 在发送请求之前做些什么，例如添加 token
    // if (store.getters.token) {
    //   config.headers['X-Token'] = getToken();
    // }
    return config;
  },
  (error) => {
    // 对请求错误做些什么
    console.log(error); // for debug
    return Promise.reject(error);
  }
);

// 响应拦截器
service.interceptors.response.use(
  (response) => {
    const data = response.data;
    
    // 如果响应有code字段，说明是自定义格式，直接返回
    if (data && typeof data === 'object' && 'code' in data) {
      return data;
    }
    
    // 否则直接返回数据
    return data;
  },
  (error) => {
    console.log('API Error:', error); // for debug
    if (error.response) {
      // 服务器返回了错误状态码
      const errorMessage = error.response.data?.detail || error.response.data?.message || '请求失败';
      message.error(errorMessage);
    } else if (error.request) {
      // 请求已发出但没有收到响应
      message.error('网络错误，请检查网络连接');
    } else {
      // 其他错误
      message.error(error.message || '请求失败');
    }
    return Promise.reject(error);
  }
);

export default service;