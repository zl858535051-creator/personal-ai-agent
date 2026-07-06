<template>
  <div class="view">
    <header class="view-header">
      <h2>Files</h2>
      <button @click="refresh">Refresh</button>
    </header>
    <FileUploader @selected="handleFile" />
    <p v-if="status" class="status">{{ status }}</p>
    <section class="list">
      <article v-for="file in files" :key="file.id" class="row">
        <div>
          <strong>{{ file.filename }}</strong>
          <p>{{ file.file_type }} · {{ file.status }}</p>
        </div>
        <button @click="remove(file.id)">Delete</button>
      </article>
    </section>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import FileUploader from '../components/FileUploader.vue'
import { deleteFile, listFiles, uploadFile } from '../api/files'

const files = ref<any[]>([])
const status = ref('')

async function refresh() {
  const { data } = await listFiles()
  files.value = data
}

async function handleFile(file: File) {
  status.value = 'Uploading and indexing...'
  await uploadFile(file)
  status.value = 'Indexed'
  await refresh()
}

async function remove(id: number) {
  await deleteFile(id)
  await refresh()
}

onMounted(refresh)
</script>

