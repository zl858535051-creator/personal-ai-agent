import { api } from './client'

export function listReports() {
  return api.get('/reports')
}

export function createReport(title: string, content: string, format: string) {
  return api.post('/reports', { title, content, format })
}

export function reportDownloadUrl(id: number) {
  return `/api/v1/reports/${id}/download`
}

