<template>
  <section v-if="sources.length" class="sources">
    <h3>Sources</h3>
    <article v-for="source in sources" :key="source.chunk_id" class="source">
      <strong>{{ source.filename }} · {{ source.source_label }}</strong>
      <p>{{ source.content }}</p>
    </article>
  </section>
</template>

<script setup lang="ts">
import type { Source } from '../api/chat'

defineProps<{ sources: Source[] }>()
</script>

