<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false,
  },
  loading: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['close', 'submit'])

const url = ref('')
const name = ref('')
const fileType = ref('auto')
const nameTouched = ref(false)

const fileTypeOptions = [
  { value: 'auto', label: '自动识别' },
  { value: 'image', label: '图片' },
  { value: 'video', label: '视频' },
  { value: 'audio', label: '音频' },
  { value: 'pdf', label: 'PDF' },
  { value: 'archive', label: '压缩包' },
  { value: 'document', label: '文档' },
  { value: 'spreadsheet', label: '表格' },
  { value: 'presentation', label: '演示文稿' },
  { value: 'code', label: '代码/文本' },
  { value: 'binary', label: '其他二进制' },
]

function resetForm() {
  url.value = ''
  name.value = ''
  fileType.value = 'auto'
  nameTouched.value = false
}

function decodeSegment(value) {
  try {
    return decodeURIComponent(value)
  } catch {
    return value
  }
}

function extractNameFromUrl(rawUrl) {
  if (!rawUrl) return ''
  try {
    const parsed = new URL(rawUrl)
    const pathname = (parsed.pathname || '').replace(/\/+$/, '')
    const segment = pathname.split('/').filter(Boolean).pop() || ''
    if (segment && segment.includes('.')) {
      return decodeSegment(segment)
    }

    // 一些下载链接会把文件名放在查询参数里。
    const queryKeys = ['filename', 'file', 'name', 'download', 'attname']
    for (let i = 0; i < queryKeys.length; i += 1) {
      const queryValue = parsed.searchParams.get(queryKeys[i])
      if (queryValue) return decodeSegment(queryValue)
    }

    return segment ? decodeSegment(segment) : ''
  } catch {
    return ''
  }
}

watch(
  () => props.visible,
  (visible) => {
    if (visible) resetForm()
  }
)

watch(url, (value) => {
  if (nameTouched.value) return
  name.value = extractNameFromUrl(value)
})

const inferredHint = computed(() => {
  const inferred = extractNameFromUrl(url.value)
  if (!inferred) return '通常会自动从外链中提取文件名和后缀'
  return `已识别: ${inferred}`
})

function handleNameInput() {
  nameTouched.value = !!name.value.trim()
}

function submit() {
  emit('submit', {
    url: url.value.trim(),
    name: name.value.trim(),
    file_type: fileType.value,
  })
}

function close() {
  if (props.loading) return
  emit('close')
}
</script>

<template>
  <div v-if="visible" class="mask" @click.self="close">
    <div class="panel">
      <h3>上传外链</h3>
      <input v-model="url" type="url" placeholder="https://example.com/file.zip" />
      <input
        v-model="name"
        type="text"
        placeholder="自定义名称（可选，不填时自动提取）"
        @input="handleNameInput"
      />
      <div class="hint">{{ inferredHint }}</div>
      <select v-model="fileType">
        <option v-for="option in fileTypeOptions" :key="option.value" :value="option.value">
          {{ option.label }}
        </option>
      </select>
      <div class="actions">
        <button @click="close">取消</button>
        <button class="primary" :disabled="loading" @click="submit">
          {{ loading ? '上传中...' : '确认上传' }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  display: grid;
  place-items: center;
  z-index: 30;
}

.panel {
  width: min(460px, 90vw);
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  animation: modalIn 0.2s ease;
}

h3 {
  margin: 0;
  font-weight: 600;
}

input {
  width: 100%;
  height: 38px;
  border: 1px solid var(--border);
  background: #11131b;
  color: var(--text);
  border-radius: 4px;
  padding: 0 10px;
  outline: none;
  transition: 0.2s ease;
}

select {
  width: 100%;
  height: 38px;
  border: 1px solid var(--border);
  background: #11131b;
  color: var(--text);
  border-radius: 4px;
  padding: 0 10px;
  outline: none;
}

.hint {
  font-size: 12px;
  color: var(--text-muted);
}

input:focus {
  border-color: var(--accent);
}

.actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

button {
  border: 1px solid var(--border);
  background: #1e2334;
  color: var(--text);
  border-radius: 6px;
  height: 34px;
  padding: 0 12px;
  cursor: pointer;
  transition: 0.2s ease;
}

.primary {
  border-color: var(--accent);
  background: var(--accent);
}

@keyframes modalIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
