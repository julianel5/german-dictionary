<template>
  <div class="flex min-h-screen flex-col bg-[#faf9f7] text-stone-900">
    <header class="border-b border-stone-200 bg-white/80 backdrop-blur">
      <div class="mx-auto flex max-w-3xl items-baseline gap-3 px-4 py-3">
        <NuxtLink to="/" class="font-dictionary text-lg font-semibold tracking-tight">
          Deutsch<span class="text-emerald-700">Wörterbuch</span>
        </NuxtLink>
        <span class="text-xs text-stone-400">schnell · werbefrei · offen</span>
      </div>
    </header>

    <main class="mx-auto w-full max-w-3xl flex-1 px-4 py-8">
      <NuxtPage />
    </main>

    <footer class="border-t border-stone-200 py-6 text-center text-xs text-stone-400">
      Open-Source-Deutschwörterbuch für Lernende — keine Werbung, kein Tracking.
    </footer>
  </div>
</template>
