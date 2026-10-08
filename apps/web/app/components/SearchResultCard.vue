<script setup lang="ts">
import type { SearchResultItem } from '@germandict/shared-types'
import { computed } from 'vue'
import {
  articleForGender,
  formatFeatures,
  frequencyLabel,
  matchTypeLabel,
  posLabel,
  principalFormsLabel,
} from '~/utils/format'

const props = defineProps<{
  result: SearchResultItem
}>()

const inflected = computed(() => {
  const matched = props.result.matchedSurface
  return matched !== null && matched !== '' && matched !== props.result.lemma
})

const featureTokens = computed(() => formatFeatures(props.result.analysis))

const rankLabel = computed(() => frequencyLabel(props.result.frequencyRank))

const article = computed(() =>
  props.result.partOfSpeech === 'noun' ? articleForGender(props.result.gender) : null,
)

const uncertain = computed(
  () => props.result.morphCertainty !== null && props.result.morphCertainty < 0.6,
)
</script>

<template>
  <li>
    <NuxtLink
      :to="`/entries/${result.lexemeId}`"
      class="block rounded-2xl border border-stone-200 bg-white p-5 shadow-sm transition hover:border-emerald-500 hover:shadow"
    >
      <div class="flex flex-wrap items-baseline gap-x-3 gap-y-1">
        <span class="font-dictionary text-2xl font-semibold tracking-tight">
          {{ result.lemma }}
        </span>
        <span v-if="article" class="rounded bg-stone-100 px-1.5 py-0.5 text-xs text-stone-600">
          {{ article }}
        </span>
        <span class="text-xs font-medium tracking-wide text-stone-500 uppercase">
          {{ posLabel(result.partOfSpeech) }}
        </span>
        <span class="ml-auto text-xs text-stone-400">
          {{ rankLabel }}
        </span>
      </div>

      <p v-if="inflected" class="mt-1.5 text-sm text-stone-500">
        Beugte Form:
        <span class="font-dictionary font-medium text-stone-800">{{ result.matchedSurface }}</span>
        <span v-if="result.matchType !== 'lemma'" class="text-stone-400">
          · {{ matchTypeLabel(result.matchType) }}
        </span>
      </p>
      <p v-else-if="result.matchType === 'fuzzy'" class="mt-1.5 text-sm text-stone-500">
        Meinten Sie <span class="font-dictionary font-medium">{{ result.lemma }}</span
        >?
        <span class="text-stone-400">· Tippfehler-Korrektur</span>
      </p>

      <p
        v-if="result.principalForms.length > 1"
        class="font-dictionary mt-1 text-base text-stone-600"
      >
        {{ principalFormsLabel(result.principalForms) }}
      </p>

      <p v-if="result.definition" class="mt-2 leading-relaxed text-stone-700">
        {{ result.definition }}
      </p>

      <div
        v-if="featureTokens.length > 0 || uncertain"
        class="mt-3 flex flex-wrap items-center gap-1.5"
      >
        <span
          v-for="token in featureTokens"
          :key="token"
          class="rounded-full bg-emerald-50 px-2 py-0.5 text-xs text-emerald-900"
        >
          {{ token }}
        </span>
        <span v-if="uncertain" class="rounded-full bg-amber-50 px-2 py-0.5 text-xs text-amber-800">
          unsichere Analyse
        </span>
      </div>
    </NuxtLink>
  </li>
</template>
