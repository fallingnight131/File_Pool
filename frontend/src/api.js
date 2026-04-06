import axios from 'axios'

const client = axios.create({
  baseURL: '/api',
  timeout: 20000,
})

export function uploadFiles(fileList, onUploadProgress, signal) {
  const formData = new FormData()
  fileList.forEach((file) => formData.append('files[]', file))
  return client.post('/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress,
    signal,
  })
}

export function uploadLink(payload) {
  return client.post('/link', payload)
}

export function fetchFiles() {
  return client.get('/files')
}

export function deleteFiles(ids) {
  return client.delete('/files', { data: { ids } })
}

export function fetchStats() {
  return client.get('/stats')
}

export function getDownloadUrl(id) {
  return `/api/download/${id}`
}
