<script setup>
import { computed, provide, ref } from 'vue'

import { fetchFiles, fetchStats, uploadLink } from './api'
import DropZone from './components/DropZone.vue'
import FilePool from './components/FilePool.vue'
import LinkUpload from './components/LinkUpload.vue'
import { formatFileSize } from './utils/format'

const files = ref([])
const stats = ref({ used_bytes: 0, total_bytes: 10 * 1024 * 1024 * 1024, file_count: 0 })

const poolVisible = ref(false)
const linkModalVisible = ref(false)
const linkLoading = ref(false)
const toastText = ref('')

let toastTimer = null

function showToast(text) {
  toastText.value = text
  if (toastTimer) window.clearTimeout(toastTimer)
  toastTimer = window.setTimeout(() => {
    toastText.value = ''
  }, 2500)
}

async function refreshFiles() {
  const { data } = await fetchFiles()
  files.value = data.files || []
}

async function refreshStats() {
  const { data } = await fetchStats()
  stats.value = data
}

async function initData() {
  try {
    await Promise.all([refreshFiles(), refreshStats()])
  } catch (error) {
    showToast(error?.response?.data?.error || '初始化失败，请刷新页面')
  }
}

provide('store', {
  files,
  stats,
  refreshFiles,
  refreshStats,
})

initData()

const usagePercent = computed(() => {
  if (!stats.value.total_bytes) return 0
  return Math.min(100, (stats.value.used_bytes / stats.value.total_bytes) * 100)
})

const usageText = computed(() => {
  return `${formatFileSize(stats.value.used_bytes)} / ${formatFileSize(stats.value.total_bytes)}`
})

async function handleLinkSubmit(payload) {
  if (!payload.url) {
    showToast('请输入外链 URL')
    return
  }

  linkLoading.value = true
  try {
    await uploadLink(payload)
    linkModalVisible.value = false
    await Promise.all([refreshFiles(), refreshStats()])
    showToast('外链上传成功')
  } catch (error) {
    showToast(error?.response?.data?.error || '无法访问该链接，请检查 URL')
  } finally {
    linkLoading.value = false
  }
}
</script>

<template>
  <div class="app">
    <header class="top">
      <div class="progress">
        <div class="inner" :style="{ width: `${usagePercent}%` }"></div>
      </div>
      <div class="status">已用 {{ usageText }}</div>
    </header>

    <DropZone
      @open-pool="poolVisible = true"
      @open-link="linkModalVisible = true"
      @toast="showToast"
    />

    <FilePool :visible="poolVisible" @close="poolVisible = false" @toast="showToast" />

    <LinkUpload
      :visible="linkModalVisible"
      :loading="linkLoading"
      @close="linkModalVisible = false"
      @submit="handleLinkSubmit"
    />

    <transition name="fade">
      <div v-if="toastText" class="toast">{{ toastText }}</div>
    </transition>
  </div>
</template>

<style>
:root {
  --bg: #0f1117;
  --surface: #1a1d27;
  --border: #2a2d3a;
  --accent: #4f8ef7;
  --danger: #e05252;
  --text: #e8eaf0;
  --text-muted: #6b7280;
  --success: #4ade80;
  --warning: #fb923c;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  background: radial-gradient(circle at 20% 0%, #1f2a44 0%, #0f1117 50%);
  color: var(--text);
  font-family: 'Outfit', sans-serif;
}

.app {
  min-height: 100vh;
  padding: 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.top {
  width: min(900px, 92vw);
  display: flex;
  align-items: center;
  gap: 16px;
}

.progress {
  flex: 1;
  height: 10px;
  border-radius: 999px;
  background: #1d2130;
  overflow: hidden;
}

.inner {
  height: 100%;
  background: linear-gradient(90deg, #4f8ef7 0%, #4ade80 100%);
  transition: width 0.2s ease;
}

.status {
  min-width: 220px;
  text-align: right;
  font-family: 'JetBrains Mono', monospace;
  color: #afc2e6;
}

.toast {
  position: fixed;
  bottom: 26px;
  left: 50%;
  transform: translateX(-50%);
  padding: 10px 16px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: rgba(22, 26, 38, 0.95);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

@media (max-width: 720px) {
  .app {
    padding: 14px;
  }

  .top {
    flex-direction: column;
    align-items: stretch;
  }

  .status {
    text-align: left;
  }
}
</style>
