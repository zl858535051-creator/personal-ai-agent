<template>
  <article class="report-card">
    <div>
      <strong>{{ report.title }}</strong>
      <p>{{ report.filename }} · {{ report.format }}</p>
    </div>
    <a :href="downloadUrl" target="_blank">Download</a>
  </article>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { reportDownloadUrl } from '../api/reports'

const props = defineProps<{ report: { id: number; title: string; filename: string; format: string } }>()
const downloadUrl = computed(() => reportDownloadUrl(props.report.id))
</script>

