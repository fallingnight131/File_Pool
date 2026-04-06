export function formatFileSize(bytes) {
  if (!bytes || bytes < 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  let value = bytes
  let index = 0
  while (value >= 1024 && index < units.length - 1) {
    value /= 1024
    index += 1
  }
  return `${value.toFixed(index === 0 ? 0 : 2)} ${units[index]}`
}

export function formatDateTime(isoString) {
  if (!isoString) return '--'
  const date = new Date(isoString)
  if (Number.isNaN(date.getTime())) return '--'
  return date.toLocaleString('zh-CN', { hour12: false })
}

export function formatCountdown(expireAt) {
  if (!expireAt) return '永久有效'
  const total = new Date(expireAt).getTime() - Date.now()
  if (total <= 0) return '已过期'
  const dayMs = 24 * 60 * 60 * 1000
  const hourMs = 60 * 60 * 1000
  const days = Math.floor(total / dayMs)
  const hours = Math.floor((total % dayMs) / hourMs)
  return `还剩 ${days}天${hours}小时`
}

export function getFileExtension(name) {
  if (!name) return ''
  const normalized = String(name).trim().toLowerCase()
  const index = normalized.lastIndexOf('.')
  if (index <= 0 || index === normalized.length - 1) return ''
  return normalized.slice(index + 1)
}

export function resolveFileIcon(file) {
  const mime = (file?.mime_type || '').toLowerCase()
  const ext = getFileExtension(file?.name)

  if (mime.startsWith('image/') || ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'svg'].includes(ext)) {
    return '🖼️'
  }
  if (mime.startsWith('video/') || ['mp4', 'mov', 'avi', 'mkv', 'webm'].includes(ext)) {
    return '🎬'
  }
  if (mime.startsWith('audio/') || ['mp3', 'wav', 'flac', 'aac', 'ogg'].includes(ext)) {
    return '🎵'
  }
  if (mime.includes('pdf') || ext === 'pdf') {
    return '📕'
  }
  if (
    mime.includes('zip') ||
    mime.includes('rar') ||
    mime.includes('compressed') ||
    ['zip', 'rar', '7z', 'tar', 'gz', 'bz2'].includes(ext)
  ) {
    return '🗜️'
  }
  if (
    mime.includes('json') ||
    mime.includes('javascript') ||
    mime.includes('python') ||
    mime.includes('text') ||
    ['js', 'ts', 'jsx', 'tsx', 'py', 'go', 'java', 'cpp', 'c', 'json', 'txt', 'md', 'yaml', 'yml'].includes(ext)
  ) {
    return '💻'
  }
  return '📄'
}
