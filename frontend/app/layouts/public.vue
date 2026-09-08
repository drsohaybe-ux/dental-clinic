<script setup lang="ts">
/**
 * Patient-facing layout — no app sidebar, no sticky chrome.
 * Used by ``/p/budget/<token>`` (ADR 0006). Mobile-first.
 */
</script>

<template>
  <div class="min-h-screen bg-[var(--ui-bg)] flex flex-col">
    <header class="border-b border-[var(--ui-border)] bg-[var(--ui-bg-elevated)]">
      <div class="max-w-3xl mx-auto px-4 py-3 flex items-center gap-2.5">
        <img
          src="/logo.png"
          alt="I SmilE"
          width="28"
          height="28"
          class="shrink-0 h-7 w-7 object-contain"
        >
        <span class="font-pacifico text-xl text-primary-600 dark:text-primary-400">I SmilE</span>
      </div>
    </header>
    <main class="flex-1">
      <slot />
    </main>
    <footer class="border-t border-[var(--ui-border)] py-4 text-center text-xs text-[var(--ui-text-muted)]">
      <span>I SmilE · {{ new Date().getFullYear() }}</span>
    </footer>
  </div>
</template>
