<template>
  <label class="upload-box">
    <input type="file" accept=".pdf,.docx,.txt,.md,.markdown" @change="onChange" />
    <span>Drop or choose a PDF, Word, TXT, or Markdown file</span>
  </label>
</template>

<script setup lang="ts">
const emit = defineEmits<{ selected: [file: File] }>()

function onChange(event: Event) {
  const input = event.target as HTMLInputElement
  if (input.files?.[0]) emit('selected', input.files[0])
}
</script>

