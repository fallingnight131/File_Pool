<script setup>
import LifeBar from './LifeBar.vue'
import { formatFileSize, resolveFileIcon } from '../utils/format'

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

defineEmits(['toggle'])
</script>

<template>
  <div class="card" :class="{ link: file.is_link }">
    <label class="pick">
      <input type="checkbox" :checked="selected" @change="$emit('toggle', file.id)" />
    </label>
    <div class="link-tag" v-if="file.is_link">🔗</div>
    <div class="icon">{{ resolveFileIcon(file) }}</div>
    <div class="name" :title="file.name">{{ file.name }}</div>
    <div class="size">{{ formatFileSize(file.size) }}</div>
    <LifeBar :expire-at="file.expire_at" />
  </div>
</template>

<style scoped>
.card {
  position: relative;
  width: 160px;
  min-height: 180px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: linear-gradient(180deg, #1a1d27 0%, #121420 100%);
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  transition: 0.2s ease;
}

.card:hover {
  transform: translateY(-2px);
  border-color: #3b4258;
}

.pick {
  position: absolute;
  left: 10px;
  top: 10px;
  opacity: 0;
  transition: 0.2s ease;
}

.card:hover .pick {
  opacity: 1;
}

.link-tag {
  position: absolute;
  top: 10px;
  right: 10px;
  font-size: 14px;
}

.icon {
  margin-top: 12px;
  font-size: 30px;
  text-align: center;
}

.name {
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  color: var(--text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.size {
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  color: var(--text-muted);
}

.link {
  box-shadow: inset 0 0 0 1px rgba(79, 142, 247, 0.25);
}
</style>
