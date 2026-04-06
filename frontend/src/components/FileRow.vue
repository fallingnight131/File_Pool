<script setup>
import LifeBar from './LifeBar.vue'
import { formatDateTime, formatFileSize, resolveFileIcon } from '../utils/format'

const props = defineProps({
  file: {
    type: Object,
    required: true,
  },
  selected: {
    type: Boolean,
    default: false,
  },
})

defineEmits(['toggle', 'download', 'delete'])
</script>

<template>
  <div class="row" :class="{ link: file.is_link, dead: file.is_link && file.status === 'dead' }">
    <input type="checkbox" :checked="selected" @change="$emit('toggle', file.id)" />
    <div class="name" :title="file.name">
      <span class="icon">{{ resolveFileIcon(file) }}</span>
      <span>{{ file.name }}</span>
    </div>
    <div class="size">{{ formatFileSize(file.size) }}</div>
    <div class="time">{{ formatDateTime(file.created_at) }}</div>
    <div class="life"><LifeBar :expire-at="file.expire_at" /></div>
    <div class="actions">
      <button class="mini" @click="$emit('download', file)">下载</button>
      <button class="mini danger" @click="$emit('delete', file.id)">删除</button>
    </div>
  </div>
</template>

<style scoped>
.row {
  display: grid;
  grid-template-columns: 28px minmax(160px, 1fr) 100px 160px 180px 140px;
  gap: 10px;
  align-items: center;
  border-bottom: 1px solid #24293a;
  padding: 10px 4px;
  font-size: 13px;
}

.name {
  display: flex;
  align-items: center;
  gap: 6px;
  font-family: 'JetBrains Mono', monospace;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.icon {
  font-size: 15px;
  flex-shrink: 0;
}

.size,
.time {
  color: var(--text-muted);
}

.actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.mini {
  border: 1px solid #3f4a6a;
  background: #202438;
  color: var(--text);
  border-radius: 6px;
  padding: 4px 8px;
  cursor: pointer;
  transition: 0.2s ease;
}

.mini:hover {
  transform: translateY(-1px);
}

.danger {
  border-color: rgba(224, 82, 82, 0.5);
  color: #ff9f9f;
}

.link {
  background: rgba(79, 142, 247, 0.08);
}

.dead {
  opacity: 0.6;
}
</style>
