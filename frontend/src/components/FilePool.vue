<script setup>
import { computed, inject, ref, watch } from 'vue'

import { deleteFiles, getDownloadUrl } from '../api'
import FileCard from './FileCard.vue'
import FileRow from './FileRow.vue'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['close', 'toast'])
const store = inject('store')

const selectedIds = ref([])
const viewMode = ref(localStorage.getItem('filepool_view_mode') || 'list')
const deleting = ref(false)

watch(viewMode, (value) => {
  localStorage.setItem('filepool_view_mode', value)
})

watch(
  () => props.visible,
  async (value) => {
    if (value) {
      selectedIds.value = []
      await store.refreshFiles()
    }
  }
)

const allSelected = computed(() => {
  if (!store.files.value.length) return false
  return selectedIds.value.length === store.files.value.length
})

const selectedCount = computed(() => selectedIds.value.length)

function toggleAll(checked) {
  selectedIds.value = checked ? store.files.value.map((item) => item.id) : []
}

function toggleOne(id) {
  if (selectedIds.value.includes(id)) {
    selectedIds.value = selectedIds.value.filter((item) => item !== id)
  } else {
    selectedIds.value.push(id)
  }
}

function triggerDownload(file) {
  window.open(getDownloadUrl(file.id), '_blank')
}

async function downloadSelected() {
  const selected = store.files.value.filter((item) => selectedIds.value.includes(item.id))
  for (let i = 0; i < selected.length; i += 1) {
    triggerDownload(selected[i])
    await new Promise((resolve) => window.setTimeout(resolve, 300))
  }
}

async function removeSelected() {
  if (!selectedIds.value.length || deleting.value) return
  if (!window.confirm(`确认删除选中的 ${selectedIds.value.length} 个文件吗？`)) return

  deleting.value = true
  try {
    await deleteFiles(selectedIds.value)
    emit('toast', '删除成功')
    selectedIds.value = []
    await Promise.all([store.refreshFiles(), store.refreshStats()])
  } catch (error) {
    emit('toast', error?.response?.data?.error || '删除失败')
  } finally {
    deleting.value = false
  }
}

async function removeSingle(id) {
  selectedIds.value = [id]
  await removeSelected()
}
</script>

<template>
  <div v-if="visible" class="mask" @click.self="emit('close')">
    <div class="panel">
      <header class="toolbar">
        <label class="select-all">
          <input type="checkbox" :checked="allSelected" @change="toggleAll($event.target.checked)" />
          全选
        </label>
        <div class="middle">共 {{ store.files.value.length }} 个文件</div>
        <div class="switcher">
          <button :class="{ active: viewMode === 'list' }" @click="viewMode = 'list'">列表</button>
          <button :class="{ active: viewMode === 'card' }" @click="viewMode = 'card'">块状</button>
        </div>
      </header>

      <main class="content" v-if="viewMode === 'list'">
        <FileRow
          v-for="item in store.files.value"
          :key="item.id"
          :file="item"
          :selected="selectedIds.includes(item.id)"
          @toggle="toggleOne"
          @download="triggerDownload"
          @delete="removeSingle"
        />
      </main>

      <main class="content cards" v-else>
        <FileCard
          v-for="item in store.files.value"
          :key="item.id"
          :file="item"
          :selected="selectedIds.includes(item.id)"
          @toggle="toggleOne"
        />
      </main>

      <footer class="bottom" v-if="selectedCount > 0">
        <button @click="downloadSelected">下载选中（{{ selectedCount }}）</button>
        <button class="danger" :disabled="deleting" @click="removeSelected">
          删除选中（{{ selectedCount }}）
        </button>
      </footer>
    </div>
  </div>
</template>

<style scoped>
.mask {
  position: fixed;
  inset: 0;
  z-index: 20;
  background: rgba(0, 0, 0, 0.5);
  display: grid;
  place-items: center;
}

.panel {
  width: min(1000px, 80vw);
  height: 70vh;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  animation: rise 0.2s ease;
}

.toolbar {
  height: 54px;
  border-bottom: 1px solid var(--border);
  display: grid;
  grid-template-columns: 150px 1fr 200px;
  align-items: center;
  padding: 0 14px;
}

.middle {
  text-align: center;
  color: var(--text-muted);
}

.switcher {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.switcher button,
.bottom button {
  border: 1px solid var(--border);
  background: #1e2232;
  color: var(--text);
  border-radius: 6px;
  height: 34px;
  padding: 0 12px;
  cursor: pointer;
  transition: 0.2s ease;
}

.switcher .active {
  border-color: var(--accent);
  color: #c8dcff;
}

.content {
  flex: 1;
  overflow: auto;
  padding: 8px 12px;
}

.cards {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-content: flex-start;
}

.bottom {
  height: 58px;
  border-top: 1px solid var(--border);
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 10px;
  padding: 0 14px;
}

.bottom .danger {
  border-color: rgba(224, 82, 82, 0.55);
  color: #ffaeae;
}

@keyframes rise {
  from {
    opacity: 0;
    transform: translateY(14px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 900px) {
  .panel {
    width: 94vw;
    height: 82vh;
  }

  .toolbar {
    grid-template-columns: 1fr;
    gap: 8px;
    height: auto;
    padding: 10px;
  }
}
</style>
