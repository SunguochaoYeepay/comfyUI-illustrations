import { ref, computed, watch } from 'vue'
import { message } from 'ant-design-vue'

export function useLora(apiBase, currentModel) {
  // LoRA相关状态
  const availableLoras = ref([])
  const loading = ref(false)
  const loraConfigSource = ref('')
  const loraLastUpdated = ref('')
  const loraCategories = ref([])
  const selectedLoraCategory = ref('')
  const selectedLoras = ref([])

  // 计算属性：过滤后的LoRA列表
  const filteredLoras = computed(() => {
    if (!selectedLoraCategory.value) {
      return availableLoras.value
    }
    return availableLoras.value.filter(lora => lora.category === selectedLoraCategory.value)
  })

  // 获取LoRA列表
  const fetchLoras = async () => {
    try {
      loading.value = true
      const response = await fetch(`${apiBase}/api/loras?model=${currentModel.value}`)
      if (response.ok) {
        const data = await response.json()
        availableLoras.value = data.loras?.loras || []
        loraConfigSource.value = data.config_source || 'unknown'
        loraLastUpdated.value = data.timestamp || ''
        console.log('📋 获取到LoRA列表:', availableLoras.value)
        console.log('🎯 当前模型:', data.model, '模型类型:', data.model_type)
        console.log('📊 LoRA配置来源:', loraConfigSource.value)
      } else {
        console.error('❌ 获取LoRA列表失败:', response.status)
        message.error('获取LoRA列表失败')
      }
    } catch (error) {
      console.error('❌ 获取LoRA列表出错:', error)
      message.error('获取LoRA列表出错')
    } finally {
      loading.value = false
    }
  }

  // 获取LoRA分类列表
  const fetchLoraCategories = async () => {
    try {
      const response = await fetch(`${apiBase}/api/lora-categories`)
      if (response.ok) {
        const data = await response.json()
        loraCategories.value = data.data || []
        console.log('📋 获取到LoRA分类列表:', loraCategories.value)
      } else {
        console.error('❌ 获取LoRA分类列表失败:', response.status)
      }
    } catch (error) {
      console.error('❌ 获取LoRA分类列表出错:', error)
    }
  }

  // 分类过滤方法
  const onLoraCategoryFilter = (category) => {
    selectedLoraCategory.value = category
    console.log('🔍 LoRA分类过滤:', category)
  }

  // 获取分类下的LoRA数量
  const getCategoryCount = (category) => {
    return availableLoras.value.filter(lora => lora.category === category).length
  }

  // 检查LoRA是否被选中
  const isLoraSelected = (loraName) => {
    return selectedLoras.value.some(lora => lora.name === loraName)
  }

  // 检查LoRA兼容性
  const isLoraCompatible = (loraName) => {
    const loraNameLower = loraName.toLowerCase()
    
    if (currentModel.value.includes('flux')) {
      // Flux模型：排除Qwen相关的LoRA
      return !['qwen', '千问', 'qwen2'].some(keyword => loraNameLower.includes(keyword))
    } else if (currentModel.value.includes('qwen')) {
      // Qwen模型：排除明确为Flux的LoRA
      return !['flux', 'kontext', 'sdxl'].some(keyword => loraNameLower.includes(keyword))
    }
    
    return true
  }

  // 添加LoRA
  const addLora = (lora) => {
    if (selectedLoras.value.length >= 4) {
      message.warning('最多只能选择4个LoRA模型')
      return
    }
    
    // 检查是否已经选择了这个LoRA
    if (isLoraSelected(lora.name)) {
      console.log('⚠️ LoRA已经存在:', lora.name)
      return
    }
    
    // 检查LoRA兼容性
    if (!isLoraCompatible(lora.name)) {
      message.warning(`LoRA "${lora.name}" 与当前模型不兼容，已跳过`)
      return
    }
    
    const newLora = {
      name: lora.name,
      strength_model: 1.0,
      strength_clip: 1.0,
      trigger_word: '',
      enabled: true
    }
    
    selectedLoras.value = [...selectedLoras.value, newLora]
    console.log('✅ 添加LoRA:', newLora)
    console.log('📋 当前已选择的LoRA数量:', selectedLoras.value.length)
  }

  // 移除LoRA
  const removeLoraByName = (loraName) => {
    selectedLoras.value = selectedLoras.value.filter(lora => lora.name !== loraName)
  }

  // 切换LoRA选择状态
  const toggleLora = (lora) => {
    if (isLoraSelected(lora.name)) {
      removeLoraByName(lora.name)
    } else {
      addLora(lora)
    }
  }

  // 处理LoRA选择状态变化
  const handleLoraToggle = (lora, checked) => {
    if (checked) {
      addLora(lora)
    } else {
      removeLoraByName(lora.name)
    }
  }

  // 刷新LoRA数据
  const refreshLoras = () => {
    fetchLoras()
    fetchLoraCategories()
  }

  // 监听模型变化，自动刷新LoRA列表
  watch(currentModel, (newModel, oldModel) => {
    if (newModel !== oldModel) {
      console.log('🔄 模型已切换:', oldModel, '->', newModel)
      // 清空已选择的LoRA，因为可能不兼容
      if (selectedLoras.value.length > 0) {
        selectedLoras.value = []
      }
      // 刷新LoRA列表
      fetchLoras()
    }
  })

  return {
    // 状态
    availableLoras,
    loading,
    loraConfigSource,
    loraLastUpdated,
    loraCategories,
    selectedLoraCategory,
    selectedLoras,
    
    // 计算属性
    filteredLoras,
    
    // 方法
    fetchLoras,
    fetchLoraCategories,
    onLoraCategoryFilter,
    getCategoryCount,
    isLoraSelected,
    isLoraCompatible,
    addLora,
    removeLoraByName,
    toggleLora,
    handleLoraToggle,
    refreshLoras
  }
}
