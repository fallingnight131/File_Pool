<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { formatCountdown } from '../utils/format'

const props = defineProps({
  expireAt: {
    type: String,
    default: null,
  },
})

const nowTick = ref(Date.now())
let timer = null

onMounted(() => {
  timer = window.setInterval(() => {
    nowTick.value = Date.now()
  }, 60000)
})

onUnmounted(() => {
  if (timer) window.clearInterval(timer)
})

const dayMs = 24 * 60 * 60 * 1000
const ttlMs = 7 * dayMs

const state = computed(() => {
  if (!props.expireAt) return 'permanent'
  const left = new Date(props.expireAt).getTime() - nowTick.value
  if (left <= 0) return 'expired'
  if (left <= dayMs) return 'danger'
  if (left <= 3 * dayMs) return 'warning'
  return 'safe'
})

const progress = computed(() => {
  if (!props.expireAt) return 100
  const left = new Date(props.expireAt).getTime() - nowTick.value
  if (left <= 0) return 0
  return Math.max(0, Math.min(100, (left / ttlMs) * 100))
})

const label = computed(() => formatCountdown(props.expireAt))
</script>

<template>
  <div class="life-wrap" :class="`state-${state}`">
    <template v-if="state === 'expired'">
      <span class="label">已过期</span>
    </template>
    <template v-else>
      <div class="bar">
        <div class="inner" :style="{ width: `${progress}%` }"></div>
      </div>
      <span class="label">{{ label }}</span>
    </template>
  </div>
</template>

<style scoped>
.life-wrap {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.bar {
  width: 100%;
  height: 6px;
  border-radius: 999px;
  background: #222534;
  overflow: hidden;
}

.inner {
  height: 100%;
  border-radius: inherit;
  transition: width 0.2s ease;
}

.label {
  font-size: 12px;
  color: var(--text-muted);
}

.state-safe .inner,
.state-permanent .inner {
  background: var(--success);
}

.state-permanent .label {
  color: var(--success);
}

.state-warning .inner {
  background: var(--warning);
}

.state-danger .inner,
.state-danger .label {
  background: var(--danger);
  color: var(--danger);
  animation: pulse 1.2s infinite;
}

.state-expired .label {
  color: #8e94a3;
}

@keyframes pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.45;
  }
}
</style>
