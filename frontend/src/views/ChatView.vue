<template>
  <div class="view">
    <header class="view-header">
      <h2>Chat</h2>
      <button @click="agentMode = !agentMode">{{ agentMode ? 'Chat Mode' : 'Agent Mode' }}</button>
    </header>
    <ChatWindow v-model="draft" :messages="messages" :loading="loading" @send="submit" />
    <SourceList :sources="sources" />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import ChatWindow from '../components/ChatWindow.vue'
import SourceList from '../components/SourceList.vue'
import { runAgent, sendMessage, type Source } from '../api/chat'

const draft = ref('')
const loading = ref(false)
const sessionId = ref<number | null>(null)
const agentMode = ref(false)
const sources = ref<Source[]>([])
const messages = ref<Array<{ id: number; role: string; content: string }>>([])

async function submit() {
  const content = draft.value.trim()
  if (!content || loading.value) return
  draft.value = ''
  loading.value = true
  messages.value.push({ id: Date.now(), role: 'user', content })
  try {
    if (agentMode.value) {
      const { data } = await runAgent(content, true)
      sources.value = data.sources
      messages.value.push({ id: Date.now() + 1, role: 'assistant', content: data.result })
    } else {
      const { data } = await sendMessage(content, sessionId.value)
      sessionId.value = data.session_id
      sources.value = data.sources
      messages.value.push({ id: Date.now() + 1, role: 'assistant', content: data.message })
    }
  } finally {
    loading.value = false
  }
}
</script>

