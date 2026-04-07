<script setup>
import { inject, ref } from 'vue'

import { uploadFiles, pollCosProgress } from '../api'

const emit = defineEmits(['open-pool', 'open-link', 'toast'])
const store = inject('store')

const fileInputRef = ref(null)
const dragOver = ref(false)
const uploading = ref(false)
const progress = ref(0)
const progressLabel = ref('')
const uploadController = ref(null)

function openNativePicker() {
  fileInputRef.value?.click()
}

async function waitForCos(taskId) {
  while (true) {
    const res = await pollCosProgress(taskId)
    const { status, uploaded, total } = res.data

    if (status === 'done') {
      progress.value = 100
      progressLabel.value = '上传完成'
      break
    }
    if (status === 'failed') {
      throw new Error('云存储上传失败')
    }

    const cosPercent = total > 0 ? uploaded / total : 0
    progress.value = 60 + Math.round(cosPercent * 40)
    progressLabel.value = '上传到云存储...'

    await new Promise((resolve) => setTimeout(resolve, 500))
  }
}

async function uploadWithFiles(fileList) {
  if (!fileList.length) return
  uploadController.value = new AbortController()
  uploading.value = true
  progress.value = 0
  progressLabel.value = '上传到服务器...'
  try {
    const response = await uploadFiles(
      fileList,
      (evt) => {
        if (!evt.total) return
        progress.value = Math.round((evt.loaded / evt.total) * 60)
      },
      uploadController.value.signal
    )

    const taskId = response.data.task_id
    if (taskId) {
      progressLabel.value = '上传到云存储...'
      await waitForCos(taskId)
    } else {
      progress.value = 100
    }

    emit('toast', '上传成功')
    await Promise.all([store.refreshFiles(), store.refreshStats()])
  } catch (error) {
    if (error?.code === 'ERR_CANCELED') {
      emit('toast', '已取消上传')
      return
    }
    const status = error?.response?.status
    if (status === 413) {
      emit('toast', '文件池已满，请先删除一些文件')
    } else {
      emit('toast', error?.response?.data?.error || error?.message || '网络错误，请稍后重试')
    }
  } finally {
    uploadController.value = null
    uploading.value = false
    progress.value = 0
    progressLabel.value = ''
  }
}

function cancelUpload() {
  if (!uploadController.value) return
  uploadController.value.abort()
}

function handleInputChange(event) {
  const files = Array.from(event.target.files || [])
  uploadWithFiles(files)
  event.target.value = ''
}

function handleDrop(event) {
  event.preventDefault()
  dragOver.value = false
  const files = Array.from(event.dataTransfer?.files || [])
  uploadWithFiles(files)
}
</script>

<template>
  <div
    class="drop"
    :class="{ over: dragOver }"
    @dragover.prevent="dragOver = true"
    @dragleave.prevent="dragOver = false"
    @drop="handleDrop"
  >
    <input ref="fileInputRef" type="file" multiple hidden @change="handleInputChange" />

    <div class="title">拖入文件或点击上传</div>
    <p class="hint">可直接拖拽批量上传</p>

    <div class="actions" @click.stop>
      <button class="primary" :disabled="uploading" @click="openNativePicker">上传文件</button>
      <button :disabled="uploading" @click="emit('open-link')">上传外链</button>
      <button :disabled="uploading" @click="emit('open-pool')">查看文件池</button>
      <button v-if="uploading" class="danger" @click="cancelUpload">取消上传</button>
    </div>

    <div v-if="uploading" class="progress" role="progressbar" :aria-valuenow="progress" aria-valuemin="0" aria-valuemax="100">
      <div class="progress-label">{{ progressLabel }} {{ progress }}%</div>
      <div class="progress-track">
        <div class="progress-fill" :style="{ width: `${progress}%` }"></div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.drop {
  width: min(900px, 92vw);
  min-height: 430px;
  border: 2px dashed #3a3f55;
  border-radius: 10px;
  background: radial-gradient(circle at 20% 20%, #1a2137 0%, #121723 45%, #0f1117 100%);
  display: grid;
  place-content: center;
  gap: 14px;
  text-align: center;
  transition: 0.2s ease;
  cursor: pointer;
  padding: 24px;
}

.drop.over {
  border-color: var(--accent);
  box-shadow: 0 0 0 4px rgba(79, 142, 247, 0.15);
}

.title {
  font-size: 28px;
  font-weight: 600;
  letter-spacing: 0.4px;
}

.hint {
  margin: 0;
  color: var(--text-muted);
}

.actions {
  display: flex;
  justify-content: center;
  gap: 12px;
}

button {
  height: 38px;
  padding: 0 16px;
  border: 1px solid var(--border);
  background: #1c2232;
  color: var(--text);
  border-radius: 6px;
  cursor: pointer;
  transition: 0.2s ease;
}

button:hover {
  transform: translateY(-1px);
}

button.primary {
  border-color: var(--accent);
  background: var(--accent);
}

button.danger {
  border-color: rgba(224, 82, 82, 0.6);
  color: #ffadad;
}

.progress {
  width: min(420px, 80vw);
}

.progress-label {
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 6px;
}

.progress-track {
  width: 100%;
  height: 8px;
  border-radius: 999px;
  background: #22283a;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #4f8ef7 0%, #4ade80 100%);
  transition: width 0.2s ease;
}

@media (max-width: 720px) {
  .drop {
    min-height: 58vh;
  }

  .title {
    font-size: 22px;
  }

  .actions {
    flex-direction: column;
  }
}
</style>
