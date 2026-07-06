<template>
  <section class="chat-panel">
    <div class="messages">
      <article v-for="message in messages" :key="message.id" :class="['message', message.role]">
        <p>{{ message.content }}</p>
      </article>
    </div>
    <form class="composer" @submit.prevent="$emit('send')">
      <textarea
        :value="modelValue"
        placeholder="输入问题，或让 Agent 分析知识库中的文件..."
        @input="onInput"
      />
      <button type="submit" :disabled="loading">{{ loading ? 'Thinking' : 'Send' }}</button>
    </form>
  </section>
</template>

<script setup lang="ts">
defineProps<{
  modelValue: string
  loading: boolean
  messages: Array<{ id: number; role: string; content: string }>
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
  send: []
}>()

function onInput(event: Event) {
  emit('update:modelValue', (event.target as HTMLTextAreaElement).value)
}
</script>
