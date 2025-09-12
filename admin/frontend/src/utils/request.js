import axios from 'axios';
import { message } from 'ant-design-vue';

// 创建 axios 实例
const service = axios.create({
  baseURL: import.meta.env.VITE_APP_BASE_API, // api 的 base_url
  timeout: 5000, // 请求超时时间
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
    const res = response.data;
    // 如果自定义代码不是 20000，则判断为错误。
    if (res.code !== 20000 && response.status !== 200) {
      message.error(res.message || 'Error');
      return Promise.reject(new Error(res.message || 'Error'));
    } else {
      return res;
    }
  },
  (error) => {
    console.log('err' + error); // for debug
    message.error(error.message);
    return Promise.reject(error);
  }
);

export default service;