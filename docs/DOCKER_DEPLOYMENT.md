# YeePay Docker 生产环境部署指南

## 🚀 快速部署

### 一键部署
```bash
deploy.bat
```

### 手动部署
```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

## 🌐 服务访问

- **统一入口**: http://localhost:80
- **HTTPS**: https://localhost:443 (需要SSL证书)
- **健康检查**: http://localhost/health

## 🏗️ 架构说明

```
用户 → Nginx (端口 80/443) → 前端/后端 (内部网络)
```

### Nginx 的优势
- **安全性**: 隐藏后端服务，统一SSL终止
- **性能**: 静态文件缓存，Gzip压缩
- **可维护性**: 统一日志，集中配置
- **生产就绪**: 符合最佳实践

## 📊 容器管理

### 查看状态
```bash
docker-compose -f docker-compose.prod.yml ps
```

### 查看日志
```bash
docker-compose -f docker-compose.prod.yml logs -f
```

### 停止服务
```bash
docker-compose -f docker-compose.prod.yml down
```

## 🔧 配置说明

### 资源限制
- **后端**: 内存 2GB，CPU 1.0 核
- **前端**: 内存 256MB，CPU 0.5 核
- **Nginx**: 内存 128MB，CPU 0.25 核

### 环境变量
- `ENVIRONMENT=production`
- `DEBUG=false`
- `LOG_LEVEL=INFO`
- `MAX_CONCURRENT_TASKS=3`

## 🔍 故障排除

### 常见问题

1. **端口冲突**:
   ```bash
   netstat -ano | findstr :80
   netstat -ano | findstr :443
   ```

2. **容器启动失败**:
   ```bash
   docker-compose -f docker-compose.prod.yml logs backend
   docker-compose -f docker-compose.prod.yml logs nginx
   ```

3. **健康检查失败**:
   ```bash
   curl http://localhost/health
   ```

## 📝 注意事项

1. **ComfyUI 服务**: 确保在 `http://localhost:8188` 运行
2. **Ollama 服务**: 确保在 `http://localhost:11434` 运行
3. **防火墙**: 确保端口 80 和 443 未被阻止
4. **SSL 证书**: 如需 HTTPS，请准备证书文件

## 🔄 更新部署

1. **停止服务**:
   ```bash
   docker-compose -f docker-compose.prod.yml down
   ```

2. **重新部署**:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d --build
   ```
