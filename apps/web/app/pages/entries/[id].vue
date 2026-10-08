<script setup lang="ts">
import type { EntryDetail, GrammaticalFeatures } from '@germandict/shared-types'
import { computed, ref, watch } from 'vue'
import { useRoute } from '#app'
import { useDictApi } from '~/composables/useDictApi'
import {
  articleForGender,
  formatFeatures,
  formTypeLabel,
  frequencyLabel,
  posLabel,
  principalFormsLabel,
  registerLabel,
  relationTypeLabel,
  sliceHighlighted,
} from '~/utils/format'

const route = useRoute()
const { getEntry } = useDictApi()

const entry = ref<EntryDetail | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

let requestSequence = 0

async function loadEntry(id: string) {
  const requestId = ++requestSequence
  loading.value = true
  error.value = null
  entry.value = null
  try {
    const data = await getEntry(id)
    if (requestId === requestSequence) entry.value = data
  } catch {
    if (requestId === requestSequence) {
      error.value = 'Dieser Eintrag wurde nicht gefunden.'
    }
  } finally {
    if (requestId === requestSequence) loading.value = false
  }
}

watch(
  () => route.params.id,
  (id) => {
    if (typeof id === 'string' && id.length > 0) {
      void loadEntry(id)
    } else {
      error.value = 'Dieser Eintrag wurde nicht gefunden.'
    }
  },
  { immediate: true },
)

const article = computed(() => {
  if (!entry.value || entry.value.lexeme.partOfSpeech !== 'noun') return null
  return articleForGender(entry.value.lexeme.gender)
})

useHead(() => ({
  title: entry.value ? `${entry.value.lexeme.lemma} – Deutsch Wörterbuch` : 'Deutsch Wörterbuch',
}))

function featuresOf(features: GrammaticalFeatures | null): string[] {
  return formatFeatures(features)
}
</script>

<template>
  <div>
    <NuxtLink to="/" class="text-sm text-emerald-800 hover:underline">
      ← Zurück zur Suche
    </NuxtLink>

    <div v-if="loading" class="mt-6 space-y-4" aria-busy="true">
      <div class="h-10 w-64 animate-pulse rounded bg-stone-200/70" />
      <div class="h-28 animate-pulse rounded-2xl bg-stone-200/70" />
      <div class="h-28 animate-pulse rounded-2xl bg-stone-200/70" />
    </div>

    <div v-else-if="error" class="mt-6 rounded-xl border border-red-200 bg-red-50 p-4 text-red-800">
      {{ error }}
    </div>

    <template v-else-if="entry">
      <header class="mt-5 flex flex-wrap items-baseline gap-x-3 gap-y-1">
        <h1 class="font-dictionary text-5xl font-semibold tracking-tight">
          {{ entry.lexeme.lemma }}
        </h1>
        <span v-if="article" class="rounded bg-stone-200 px-2 py-0.5 text-sm text-stone-700">
          {{ article }}
        </span>
        <span class="text-sm font-medium tracking-wide text-stone-500 uppercase">
          {{ posLabel(entry.lexeme.partOfSpeech) }}
        </span>
        <span v-if="entry.lexeme.register" class="text-xs text-stone-400">
          {{ registerLabel(entry.lexeme.register) }}
        </span>
        <span v-if="entry.lexeme.domain" class="text-xs text-stone-400">
          {{ entry.lexeme.domain }}
        </span>
      </header>

      <p v-if="entry.principalForms.length > 1" class="font-dictionary mt-2 text-xl text-stone-600">
        {{ principalFormsLabel(entry.principalForms) }}
      </p>

      <section v-if="entry.senses.length > 0" class="mt-10">
        <h2
          class="mb-3 border-b border-stone-200 pb-1 text-xs font-semibold tracking-widest text-stone-500 uppercase"
        >
          Bedeutungen
        </h2>
        <ol class="space-y-4">
          <li v-for="sense in entry.senses" :key="sense.id" class="flex gap-3">
            <span
              class="mt-0.5 h-6 w-6 shrink-0 rounded-full bg-emerald-700 text-center text-sm leading-6 text-white"
            >
              {{ sense.senseIndex }}
            </span>
            <div>
              <p class="text-lg leading-relaxed text-stone-800">{{ sense.definition }}</p>
              <p class="mt-1 flex gap-2 text-xs text-stone-400">
                <span v-if="sense.register">{{ registerLabel(sense.register) }}</span>
                <span v-if="sense.domain">{{ sense.domain }}</span>
              </p>
            </div>
          </li>
        </ol>
      </section>

      <section v-if="entry.forms.length > 0" class="mt-10">
        <h2
          class="mb-3 border-b border-stone-200 pb-1 text-xs font-semibold tracking-widest text-stone-500 uppercase"
        >
          Wortformen
        </h2>
        <div class="overflow-x-auto">
          <table class="w-full text-left text-sm">
            <thead>
              <tr class="text-xs tracking-wide text-stone-400 uppercase">
                <th class="py-2 pr-4 font-medium">Form</th>
                <th class="py-2 pr-4 font-medium">Typ</th>
                <th class="py-2 font-medium">Merkmale</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="form in entry.forms" :key="form.id" class="border-t border-stone-100">
                <td class="font-dictionary py-2 pr-4 text-base">{{ form.surface }}</td>
                <td class="py-2 pr-4 text-stone-500">{{ formTypeLabel(form.formType) }}</td>
                <td class="py-2">
                  <span class="flex flex-wrap gap-1.5">
                    <span
                      v-for="token in featuresOf(form.features)"
                      :key="token"
                      class="rounded-full bg-stone-100 px-2 py-0.5 text-xs text-stone-600"
                    >
                      {{ token }}
                    </span>
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section v-if="entry.examples.length > 0" class="mt-10">
        <h2
          class="mb-3 border-b border-stone-200 pb-1 text-xs font-semibold tracking-widest text-stone-500 uppercase"
        >
          Beispiele
        </h2>
        <ul class="space-y-5">
          <li v-for="example in entry.examples" :key="example.id">
            <blockquote class="font-dictionary text-lg leading-relaxed text-stone-800">
              <template
                v-for="(segment, index) in sliceHighlighted(example.text, example.highlights)"
                :key="index"
              >
                <mark v-if="segment.mark" class="rounded bg-amber-100 px-0.5 text-stone-900">{{
                  segment.text
                }}</mark>
                <template v-else>{{ segment.text }}</template>
              </template>
            </blockquote>
            <p v-if="example.translation" class="mt-1 text-sm text-stone-500">
              {{ example.translation }}
            </p>
            <p v-if="example.source" class="mt-0.5 text-xs text-stone-400">
              {{ example.source }}
            </p>
          </li>
        </ul>
      </section>

      <section v-if="entry.frequency.length > 0" class="mt-10">
        <h2
          class="mb-3 border-b border-stone-200 pb-1 text-xs font-semibold tracking-widest text-stone-500 uppercase"
        >
          Häufigkeit
        </h2>
        <div class="flex flex-wrap gap-2">
          <span
            v-for="frequency in entry.frequency"
            :key="`${frequency.corpus}-${frequency.wordFormId ?? 'lexeme'}`"
            class="rounded-full border border-stone-200 bg-white px-3 py-1 text-xs text-stone-600"
          >
            {{ frequency.corpus }}
            <span class="font-medium">{{ frequencyLabel(frequency.rank) }}</span>
            <span class="text-stone-400">
              · {{ frequency.count.toLocaleString('de-DE') }} Vorkommen</span
            >
          </span>
        </div>
      </section>

      <section v-if="entry.relations.length > 0" class="mt-10">
        <h2
          class="mb-3 border-b border-stone-200 pb-1 text-xs font-semibold tracking-widest text-stone-500 uppercase"
        >
          Siehe auch
        </h2>
        <div class="flex flex-wrap gap-2">
          <NuxtLink
            v-for="(relation, index) in entry.relations"
            :key="`${relation.relationType}-${relation.lexemeId}-${index}`"
            :to="`/?q=${encodeURIComponent(relation.lemma)}`"
            class="rounded-full border border-stone-300 bg-white px-3 py-1 text-sm text-stone-700 transition hover:border-emerald-600 hover:text-emerald-800"
          >
            {{ relationTypeLabel(relation.relationType) }}:
            <span class="font-dictionary">{{ relation.lemma }}</span>
          </NuxtLink>
        </div>
      </section>
    </template>
  </div>
</template>
