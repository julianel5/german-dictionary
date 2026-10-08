<script setup lang="ts">
interface Props {
  modelValue: string
  loading?: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
  submit: []
}>()

function onInput(event: Event) {
  const target = event.target as HTMLInputElement
  emit('update:modelValue', target.value)
}
</script>

<template>
  <form role="search" class="relative" @submit.prevent="emit('submit')">
    <label for="dict-search" class="sr-only">Wörterbuchsuche</label>
    <input
      id="dict-search"
      type="search"
      enterkeyhint="search"
      autofocus
      autocomplete="off"
      spellcheck="false"
      :value="props.modelValue"
      placeholder="Wort oder Form eingeben … z. B. gehen, ging, Häusern"
      class="w-full rounded-2xl border border-stone-300 bg-white py-4 pr-28 pl-5 text-lg shadow-sm outline-none transition focus:border-emerald-600 focus:ring-2 focus:ring-emerald-600/20"
      @input="onInput"
    />
    <button
      type="submit"
      :disabled="props.loading"
      class="absolute top-1/2 right-2 -translate-y-1/2 rounded-xl bg-emerald-700 px-4 py-2 text-sm font-medium text-white transition hover:bg-emerald-800 disabled:opacity-50"
    >
      {{ props.loading ? 'Suche …' : 'Suchen' }}
    </button>
  </form>
</template>
