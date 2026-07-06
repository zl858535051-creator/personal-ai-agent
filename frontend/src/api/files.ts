import { api } from './client'

export function uploadFile(file: File) {
  const form = new FormData()
  form.append('file', file)
  return api.post('/files/upload', form)
}

export function listFiles() {
  return api.get('/files')
}

export function deleteFile(id: number) {
  return api.delete(`/files/${id}`)
}

