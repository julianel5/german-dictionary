<script setup lang="ts">
import type { SearchResponse } from '@germandict/shared-types'
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from '#app'
import { useDictApi } from '~/composables/useDictApi'
import { matchTypeLabel } from '~/utils/format'

const EXAMPLES = ['gehen', 'ging', 'gegangen', 'Häusern']

const route = useRoute()
const router = useRouter()
const { search } = useDictApi()

const query = ref('')
const response = ref<SearchResponse | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

let requestSequence = 0

async function runSearch(rawQuery: string) {
  const trimmed = rawQuery.trim()
  if (!trimmed) {
    response.value = null
    error.value = null
    loading.value = false
    return
  }
  const requestId = ++requestSequence
  loading.value = true
  error.value = null
  try {
    const data = await search(trimmed)
    if (requestId === requestSequence) {
      response.value = data
    }
  } catch {
    if (requestId === requestSequence) {
      response.value = null
      error.value = 'Die Suche ist gerade nicht erreichbar. Bitte versuchen Sie es erneut.'
    }
  } finally {
    if (requestId === requestSequence) {
      loading.value = false
    }
  }
}

watch(
  () => route.query.q,
  (value) => {
    query.value = typeof value === 'string' ? value : ''
    void runSearch(query.value)
  },
  { immediate: true },
)

function submit() {
  const trimmed = query.value.trim()
  router.push({ path: '/', query: trimmed ? { q: trimmed } : {} })
}

function useExample(example: string) {
  router.push({ path: '/', query: { q: example } })
}

const resultCountLabel = computed(() => {
  const count = response.value?.results.length ?? 0
  if (count === 1) return '1 Treffer'
  return `${count} Treffer`
})

const queryTypeNote = computed(() => {
  const type = response.value?.queryType
  if (!type || type === 'lemma') return null
  return matchTypeLabel(type)
})
</script>

<template>
  <div>
    <section class="text-center">
      <h1 class="font-dictionary text-4xl font-semibold tracking-tight">
        Deutsch<span class="text-emerald-700">Wörterbuch</span>
      </h1>
      <p class="mt-2 text-stone-500">
        Jede Form findet ihren Eintrag — Präteritum, Partizip und Kasus eingeschlossen.
      </p>
    </section>

    <div class="mt-6">
      <SearchBox v-model="query" :loading="loading" @submit="submit" />
    </div>

    <div v-if="!query.trim() && !response" class="mt-8 text-center">
      <p class="text-sm text-stone-500">Zum Ausprobieren:</p>
      <div class="mt-3 flex flex-wrap justify-center gap-2">
        <button
          v-for="example in EXAMPLES"
          :key="example"
          class="font-dictionary rounded-full border border-stone-300 bg-white px-3 py-1 text-sm text-stone-700 transition hover:border-emerald-600 hover:text-emerald-800"
          @click="useExample(example)"
        >
          {{ example }}
        </button>
      </div>
    </div>

    <div v-if="error" class="mt-8 rounded-xl border border-red-200 bg-red-50 p-4 text-red-800">
      {{ error }}
    </div>

    <div v-else-if="loading" class="mt-8 space-y-3" aria-busy="true">
      <div v-for="n in 3" :key="n" class="h-24 animate-pulse rounded-2xl bg-stone-200/70" />
    </div>

    <template v-else-if="response">
      <div class="mt-8 flex items-baseline justify-between">
        <p class="text-sm text-stone-500">
          <span class="font-medium text-stone-800">{{ resultCountLabel }}</span>
          für „{{ response.query }}“
          <span v-if="queryTypeNote" class="text-stone-400"> · {{ queryTypeNote }}</span>
        </p>
        <p v-if="response.morphologyEngine" class="text-xs text-stone-400">
          Morphologie: {{ response.morphologyEngine }}
        </p>
      </div>

      <ul v-if="response.results.length > 0" class="mt-4 space-y-3">
        <SearchResultCard
          v-for="result in response.results"
          :key="result.lexemeId"
          :result="result"
        />
      </ul>

      <div v-else class="mt-6 rounded-2xl border border-dashed border-stone-300 p-6 text-center">
        <p class="font-dictionary text-lg">Keine Treffer für „{{ response.query }}“.</p>
        <p class="mt-1 text-sm text-stone-500">
          Prüfen Sie die Schreibweise oder probieren Sie eine der Grundformen.
        </p>
      </div>
    </template>
  </div>
</template>
