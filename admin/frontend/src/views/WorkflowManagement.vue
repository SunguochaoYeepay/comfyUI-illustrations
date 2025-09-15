<template>
  <div>
    <div class="header-bar">
      <h1>工作流管理</h1>
      <div class="header-actions">
        <a-input-search
          v-model:value="searchQuery"
          placeholder="按名称搜索工作流"
          style="width: 250px;"
          @search="onSearch"
          allow-clear
        />
        <a-button type="primary" @click="showCreateModal" style="margin-left: 8px;">
          <plus-outlined /> 创建工作流
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
          <a-tag :color="record.status === 'enabled' ? 'green' : 'red'">
            {{ record.status === 'enabled' ? '启用' : '禁用' }}
          </a-tag>
        </template>
        <template v-else-if="column.key === 'base_model_type'">
          <a-tag v-if="record.base_model_type" color="purple">
            {{ record.base_model_type }}
          </a-tag>
          <span v-else style="color: #999;">未设置</span>
        </template>
        <template v-else-if="column.key === 'workflow_json'">
          <a-tag color="blue">
            {{ Object.keys(record.workflow_json || {}).length }} 个节点
          </a-tag>
        </template>
        <template v-else-if="column.key === 'created_at'">
          {{ formatDate(record.created_at) }}
        </template>
        <template v-else-if="column.key === 'action'">
          <a-space>
            <a @click="viewWorkflow(record)">查看</a>
            <a @click="editWorkflow(record)">编辑</a>
            <a @click="downloadWorkflow(record)">下载</a>
            <a @click="toggleWorkflowStatus(record)">
              {{ record.status === 'enabled' ? '禁用' : '启用' }}
            </a>
            <a-popconfirm
              v-if="record.status === 'disabled'"
              title="确定删除这个工作流吗？"
              @confirm="deleteWorkflow(record.id)"
            >
              <a style="color: #ff4d4f;">删除</a>
            </a-popconfirm>
            <a v-else style="color: #ccc;" disabled>删除</a>
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
      style="margin-top: 16px; text-align: right;"
    />

    <!-- 创建工作流模态框 -->
    <WorkflowCreateModal
      v-model:open="createModalOpen"
      @created="handleCreateSaved"
    />

    <!-- 编辑工作流抽屉 -->
    <WorkflowEditDrawer
      v-model:open="editModalOpen"
      :workflow-data="editingWorkflow"
      @saved="handleEditSaved"
    />


    <!-- 查看工作流模态框 -->
    <a-modal
      v-model:open="viewModalOpen"
      title="查看工作流"
      :footer="null"
      width="800px"
    >
      <div v-if="viewWorkflowData">
        <a-descriptions :column="2" bordered>
          <a-descriptions-item label="名称">{{ viewWorkflowData.name }}</a-descriptions-item>
          <a-descriptions-item label="创建时间">{{ formatDate(viewWorkflowData.created_at) }}</a-descriptions-item>
          <a-descriptions-item label="描述" :span="2">{{ viewWorkflowData.description || '无' }}</a-descriptions-item>
        </a-descriptions>
        <a-divider>工作流JSON</a-divider>
        <pre class="json-viewer">{{ JSON.stringify(viewWorkflowData.workflow_json, null, 2) }}</pre>
      </div>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { 
  getWorkflows, 
  deleteWorkflow as deleteWorkflowAPI, 
  downloadWorkflow as downloadWorkflowAPI,
  updateWorkflowStatus
} from '@/api/workflow'
import { message } from 'ant-design-vue'
import { PlusOutlined } from '@ant-design/icons-vue'
import WorkflowCreateModal from '@/components/WorkflowCreateModal.vue'
import WorkflowEditDrawer from '@/components/WorkflowEditDrawer.vue'

const router = useRouter()

const columns = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: 80 },
  { title: '名称', dataIndex: 'name', key: 'name', ellipsis: true },
  { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true },
  { title: '基础模型', dataIndex: 'base_model_type', key: 'base_model_type', width: 120 },
  { title: '状态', key: 'status', width: 80 },
  { title: '节点数', key: 'workflow_json', width: 100 },
  { title: '创建时间', key: 'created_at', width: 180 },
  { title: '操作', key: 'action', width: 250 },
]

const data = ref([])
const loading = ref(false)
const searchQuery = ref('')
const pagination = reactive({ current: 1, pageSize: 10, total: 0 })

// 计算属性确保数据始终是数组
const tableData = computed(() => {
  return Array.isArray(data.value) ? data.value : []
})

// 模态框状态
const createModalOpen = ref(false)
const editModalOpen = ref(false)
const editingWorkflow = ref(null)


// 查看模态框状态
const viewModalOpen = ref(false)
const viewWorkflowData = ref(null)

// 获取工作流列表
const fetchWorkflows = async (page = 1, pageSize = 10, search = '') => {
  loading.value = true
  try {
    console.log('正在获取工作流列表...', { page, pageSize, search })
    const response = await getWorkflows({
      page,
      pageSize,
      search
    })
    
    console.log('API响应:', response)
    console.log('响应类型:', typeof response, '是否为数组:', Array.isArray(response))
    
    if (response && Array.isArray(response)) {
      data.value = response
      pagination.total = response.length
      pagination.current = page
      pagination.pageSize = pageSize
      console.log('设置数据成功，工作流数量:', response.length)
    } else {
      data.value = []
      console.error('响应格式错误:', response)
      message.error('获取工作流列表失败')
    }
  } catch (error) {
    console.error('Error fetching workflows:', error)
    data.value = []
    message.error('获取工作流列表失败')
  } finally {
    loading.value = false
  }
}

// 搜索功能
const onSearch = (searchValue) => {
  pagination.current = 1
  fetchWorkflows(1, pagination.pageSize, searchValue)
}

// 分页处理
const handleTableChange = (page, pageSize) => {
  fetchWorkflows(page, pageSize, searchQuery.value)
}

// 创建工作流
const showCreateModal = () => {
  createModalOpen.value = true
}


// 编辑工作流
const editWorkflow = (record) => {
  editingWorkflow.value = record
  editModalOpen.value = true
}

// 处理编辑保存
const handleEditSaved = () => {
  fetchWorkflows(pagination.current, pagination.pageSize, searchQuery.value)
}

// 处理创建保存
const handleCreateSaved = () => {
  fetchWorkflows(pagination.current, pagination.pageSize, searchQuery.value)
}



// 删除工作流
const toggleWorkflowStatus = async (record) => {
  try {
    const newStatus = record.status === 'enabled' ? 'disabled' : 'enabled'
    await updateWorkflowStatus(record.id, newStatus)
    message.success(`工作流已${newStatus === 'enabled' ? '启用' : '禁用'}`)
    fetchWorkflows(pagination.current, pagination.pageSize, searchQuery.value)
  } catch (error) {
    console.error('Error updating workflow status:', error)
    message.error('更新工作流状态失败')
  }
}

const deleteWorkflow = async (id) => {
  try {
    await deleteWorkflowAPI(id)
    message.success('工作流删除成功')
    fetchWorkflows(pagination.current, pagination.pageSize, searchQuery.value)
  } catch (error) {
    console.error('Error deleting workflow:', error)
    message.error('删除工作流失败')
  }
}

// 查看工作流
const viewWorkflow = (record) => {
  viewWorkflowData.value = record
  viewModalOpen.value = true
}

// 下载工作流
const downloadWorkflow = async (record) => {
  try {
    const response = await downloadWorkflowAPI(record.id)
    const blob = new Blob([JSON.stringify(response.content, null, 2)], { type: 'application/json' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = response.filename || `${record.name}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
    message.success('工作流下载成功')
  } catch (error) {
    console.error('Error downloading workflow:', error)
    message.error('下载工作流失败')
  }
}


// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  return new Date(dateString).toLocaleString('zh-CN')
}

onMounted(() => {
  fetchWorkflows()
})
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

.json-viewer {
  background: #f5f5f5;
  padding: 16px;
  border-radius: 4px;
  max-height: 400px;
  overflow-y: auto;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.4;
}
</style>
