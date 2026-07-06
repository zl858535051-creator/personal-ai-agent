import { api } from './client'

export interface Source {
  document_id: number
  chunk_id: number
  filename: string
  source_label: string
  content: string
  score: number
}

export interface ChatResponse {
  session_id: number
  message: string
  sources: Source[]
}

export function sendMessage(message: string, sessionId: number | null) {
  return api.post<ChatResponse>('/chat', {
    message,
    session_id: sessionId,
    use_knowledge_base: true
  })
}

export function runAgent(task: string, generateReport = false) {
  return api.post('/agent/run', { task, generate_report: generateReport })
}

export function listSessions() {
  return api.get('/chat/sessions')
}

