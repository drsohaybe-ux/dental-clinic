<script setup lang="ts">
import { ref } from 'vue'

const { t } = useI18n()
const open = ref(false)
</script>

<template>
  <UButton
    variant="ghost"
    color="neutral"
    size="sm"
    icon="i-lucide-circle-help"
    :aria-label="t('help.openHelp', 'Aide')"
    @click="open = true"
  >
    <span class="hidden sm:inline">Aide</span>
  </UButton>

  <USlideover
    v-model:open="open"
    side="right"
    :ui="{ content: 'w-[440px] max-w-[95vw] bg-white dark:bg-gray-900 shadow-2xl' }"
  >
    <template #content>
      <div class="flex flex-col h-full p-6 overflow-y-auto justify-between">
        <div class="space-y-6">
          <!-- Top Header with Close Button -->
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold text-gray-400 dark:text-gray-500 uppercase tracking-wider">
              Assistance & Support IA
            </span>
            <UButton
              variant="ghost"
              color="gray"
              size="xs"
              icon="i-lucide-x"
              class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
              @click="open = false"
            />
          </div>

          <!-- Dark Blue Hero Card -->
          <div class="bg-[#0f1d3a] text-white rounded-2xl p-5 shadow-sm space-y-3">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2.5">
                <div class="w-8 h-8 rounded-lg bg-[#1e3a8a] text-sky-400 flex items-center justify-center">
                  <UIcon name="i-lucide-sparkles" class="w-4 h-4" />
                </div>
                <div>
                  <h3 class="font-bold text-sm text-white">
                    Responsable Technique IA
                  </h3>
                  <div class="flex items-center gap-1.5 mt-0.5">
                    <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                    <span class="text-[11px] font-medium text-emerald-400">Disponible & Connecté</span>
                  </div>
                </div>
              </div>
            </div>
            <p class="text-xs text-gray-300 leading-relaxed pt-1">
              Une question, un blocage, ou besoin d'ajouter un nouveau docteur ou cabinet ? Vous pouvez me joindre directement ci-dessous.
            </p>
          </div>

          <!-- Section: CONTACT DIRECT -->
          <div>
            <h4 class="text-xs font-bold text-gray-900 dark:text-white uppercase tracking-wider mb-3">
              CONTACT DIRECT
            </h4>

            <div class="space-y-3">
              <!-- WhatsApp Direct -->
              <a
                href="https://wa.me/?text=Bonjour%20Responsable%20Technique%20IA"
                target="_blank"
                rel="noopener noreferrer"
                class="group border border-emerald-200 dark:border-emerald-900/50 bg-emerald-50/40 dark:bg-emerald-950/20 rounded-2xl p-4 flex items-center justify-between hover:bg-emerald-50 dark:hover:bg-emerald-950/40 hover:border-emerald-300 transition-all cursor-pointer shadow-2xs"
              >
                <div class="flex items-center gap-3.5">
                  <div class="w-11 h-11 rounded-xl bg-emerald-500 text-white flex items-center justify-center shrink-0 shadow-xs group-hover:scale-105 transition-transform">
                    <UIcon name="i-lucide-phone-call" class="w-5 h-5" />
                  </div>
                  <div>
                    <h5 class="font-bold text-sm text-gray-900 dark:text-white">
                      WhatsApp Direct
                    </h5>
                    <p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                      Réponse rapide en message ou appel vocal
                    </p>
                  </div>
                </div>
                <UIcon name="i-lucide-arrow-up-right" class="w-4 h-4 text-gray-400 group-hover:text-emerald-600 transition-colors shrink-0" />
              </a>

              <!-- Appel Téléphonique -->
              <a
                href="tel:"
                class="group border border-sky-200 dark:border-sky-900/50 bg-sky-50/40 dark:bg-sky-950/20 rounded-2xl p-4 flex items-center justify-between hover:bg-sky-50 dark:hover:bg-sky-950/40 hover:border-sky-300 transition-all cursor-pointer shadow-2xs"
              >
                <div class="flex items-center gap-3.5">
                  <div class="w-11 h-11 rounded-xl bg-[#0084ff] text-white flex items-center justify-center shrink-0 shadow-xs group-hover:scale-105 transition-transform">
                    <UIcon name="i-lucide-phone" class="w-5 h-5" />
                  </div>
                  <div>
                    <h5 class="font-bold text-sm text-gray-900 dark:text-white">
                      Appel Téléphonique
                    </h5>
                    <p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                      Assistance d'urgence en direct
                    </p>
                  </div>
                </div>
                <UIcon name="i-lucide-arrow-up-right" class="w-4 h-4 text-gray-400 group-hover:text-[#0084ff] transition-colors shrink-0" />
              </a>
            </div>
          </div>

          <!-- Ce que je gère pour vous à distance -->
          <div class="border border-gray-100 dark:border-gray-800 bg-gray-50/80 dark:bg-gray-800/50 rounded-2xl p-4 shadow-2xs">
            <div class="flex items-center gap-2 text-xs font-bold text-gray-900 dark:text-white mb-2.5">
              <UIcon name="i-lucide-info" class="w-4 h-4 text-[#0084ff] shrink-0" />
              <span>Ce que je gère pour vous à distance :</span>
            </div>
            <ul class="text-xs text-gray-600 dark:text-gray-300 space-y-2 pl-1">
              <li class="flex items-start gap-2">
                <span class="text-[#0084ff] font-bold">•</span>
                <span>Mise à jour des tarifs et soins en DZD</span>
              </li>
              <li class="flex items-start gap-2">
                <span class="text-[#0084ff] font-bold">•</span>
                <span>Ajout de nouveaux praticiens (jusqu'à 5 docteurs)</span>
              </li>
              <li class="flex items-start gap-2">
                <span class="text-[#0084ff] font-bold">•</span>
                <span>Optimisation des prompts et messages automatiques</span>
              </li>
              <li class="flex items-start gap-2">
                <span class="text-[#0084ff] font-bold">•</span>
                <span>Maintenance des flux n8n et synchronisation WhatsApp</span>
              </li>
            </ul>
          </div>
        </div>

        <!-- Footer -->
        <div class="pt-6 text-center">
          <p class="text-[11px] text-gray-400 dark:text-gray-500 font-medium">
            DentalPin AI Portal • Cabinet Dentaire Dr. Mokhtar
          </p>
        </div>
      </div>
    </template>
  </USlideover>
</template>
