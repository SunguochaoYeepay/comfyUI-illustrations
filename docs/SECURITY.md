# 安全配置指南

## API密钥管理

### Gemini API密钥配置

1. **环境变量设置**
   ```bash
   # 在 .env 文件中设置
   GEMINI_API_KEY=your_actual_api_key_here
   ```

2. **工作流文件**
   - 所有工作流文件中的API密钥已替换为环境变量占位符 `${GEMINI_API_KEY}`
   - 不再在代码中硬编码API密钥

3. **安全措施**
   - `.gitignore` 已更新，忽略包含敏感信息的文件
   - 环境变量文件 `.env*` 被忽略
   - 包含 `*api_key*`, `*secret*`, `*password*`, `*credentials*` 的文件被忽略

## 部署注意事项

### 开发环境
1. 复制 `back/env.example` 为 `back/.env`
2. 在 `.env` 文件中填入真实的API密钥
3. 确保 `.env` 文件不被提交到Git

### 生产环境
1. 通过环境变量或Docker secrets设置API密钥
2. 不要在代码或配置文件中硬编码敏感信息
3. 定期轮换API密钥

## 安全检查清单

- [ ] 所有API密钥使用环境变量
- [ ] 工作流文件不包含硬编码密钥
- [ ] `.gitignore` 正确配置
- [ ] 生产环境使用安全的密钥管理
- [ ] 定期审查和轮换密钥

## 紧急响应

如果发现API密钥泄露：
1. 立即在Google Cloud Console中撤销密钥
2. 生成新的API密钥
3. 更新所有环境中的密钥配置
4. 检查Git历史，必要时清理敏感信息
