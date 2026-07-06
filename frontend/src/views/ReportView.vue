<template>
  <div class="view">
    <header class="view-header">
      <h2>Reports</h2>
      <button @click="refresh">Refresh</button>
    </header>
    <form class="report-form" @submit.prevent="create">
      <input v-model="title" placeholder="Report title" />
      <select v-model="format">
        <option value="markdown">Markdown</option>
        <option value="pdf">PDF</option>
      </select>
      <textarea v-model="content" placeholder="Report content" />
      <button type="submit">Create</button>
    </form>
    <ReportPreview v-for="report in reports" :key="report.id" :report="report" />
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import ReportPreview from '../components/ReportPreview.vue'
import { createReport, listReports } from '../api/reports'

const reports = ref<any[]>([])
const title = ref('New Report')
const content = ref('')
const format = ref('markdown')

async function refresh() {
  const { data } = await listReports()
  reports.value = data
}

async function create() {
  await createReport(title.value, content.value, format.value)
  content.value = ''
  await refresh()
}

onMounted(refresh)
</script>

