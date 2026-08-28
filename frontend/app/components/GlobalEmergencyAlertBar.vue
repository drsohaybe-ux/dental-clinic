<template>
  <ClientOnly>
    <div
      v-if="hasActiveAlert && activeEmergency"
      class="mb-4 bg-gradient-to-r from-rose-600 via-rose-500 to-red-600 rounded-2xl p-4 text-white shadow-lg flex flex-col sm:flex-row sm:items-center justify-between gap-3 border border-rose-300/40 animate-pulse"
      role="alert"
    >
      <div class="flex items-center gap-3.5 min-w-0">
        <div class="w-10 h-10 rounded-xl bg-white/20 flex items-center justify-center text-xl shrink-0 shadow-inner">
          🚨
        </div>
        <div class="min-w-0">
          <div class="flex items-center gap-2">
            <h3 class="font-bold text-xs sm:text-sm tracking-wide flex items-center gap-1.5">
              ALERTE URGENCE DENTAIRE (DR. MOKHTAR)
            </h3>
            <span class="text-[10px] bg-white text-rose-700 font-extrabold px-2 py-0.5 rounded-full uppercase tracking-wider">
              Priorité Maximale
            </span>
          </div>
          <p class="text-xs text-rose-100 mt-0.5 truncate">
            <strong>{{ activeEmergency.name }}</strong> ({{ activeEmergency.phone }}) : {{ activeEmergency.lastMessage }}
          </p>
        </div>
      </div>

      <div class="flex items-center gap-2 shrink-0">
        <button
          type="button"
          class="px-3.5 py-1.5 bg-white hover:bg-rose-50 text-rose-700 font-bold text-xs rounded-xl shadow-xs transition-colors flex items-center gap-1.5"
          @click="openEmergencyChat"
        >
          <UIcon name="i-lucide-message-circle" class="w-4 h-4" />
          <span>Ouvrir la Messagerie</span>
        </button>
        <button
          type="button"
          class="p-1.5 hover:bg-white/20 text-white rounded-lg transition-colors"
          title="Masquer l'alerte"
          @click="dismissEmergency"
        >
          <UIcon name="i-lucide-x" class="w-4 h-4" />
        </button>
      </div>
    </div>
  </ClientOnly>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'

const { activeEmergency, hasActiveAlert, startGlobalSync, dismissEmergency, openEmergencyChat } = useEmergencyAlert()

onMounted(() => {
  startGlobalSync()
})
</script>
