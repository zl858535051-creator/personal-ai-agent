<template>
  <div class="view">
    <header class="view-header">
      <h2>History</h2>
      <button @click="refresh">Refresh</button>
    </header>
    <article v-for="session in sessions" :key="session.id" class="history-item">
      <strong>{{ session.title }}</strong>
      <p>{{ new Date(session.updated_at).toLocaleString() }}</p>
      <div class="mini-message" v-for="message in session.messages" :key="message.id">
        {{ message.role }}: {{ message.content }}
      </div>
    </article>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { listSessions } from '../api/chat'

const sessions = ref<any[]>([])

async function refresh() {
  const { data } = await listSessions()
  sessions.value = data
}

onMounted(refresh)
</script>

