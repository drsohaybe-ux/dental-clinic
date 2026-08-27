<template>
  <div class="p-6 max-w-[1500px] mx-auto space-y-6">
    <!-- Top Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-gray-100 dark:border-gray-800 pb-5">
      <div>
        <h1 class="text-2xl font-bold tracking-tight text-gray-900 dark:text-white flex items-center gap-2">
          <UIcon name="i-lucide-user-plus" class="text-primary-500 w-7 h-7" />
          Prospects & Leads Telegram / WhatsApp
        </h1>
        <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Contacts entrants auto-enregistrés par l'IA n8n en attente de confirmation de consultation.
        </p>
      </div>

      <div class="flex items-center gap-3">
        <button
          type="button"
          class="inline-flex items-center gap-2 px-4 py-2 text-xs font-semibold text-white bg-primary-600 hover:bg-primary-700 rounded-lg shadow-sm transition-colors"
          @click="isCreateModalOpen = true"
        >
          <UIcon name="i-lucide-plus" class="w-4 h-4" />
          <span>Ajouter un Prospect</span>
        </button>
      </div>
    </div>

    <!-- Pipeline Stats Cards -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <div class="bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-xl p-4 shadow-2xs">
        <div class="flex items-center justify-between text-xs text-gray-500 font-semibold">
          <span>Total Prospects</span>
          <UIcon name="i-lucide-users" class="w-4 h-4 text-primary-500" />
        </div>
        <p class="text-2xl font-bold text-gray-900 dark:text-white mt-2">{{ leads.length }}</p>
      </div>

      <div class="bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-xl p-4 shadow-2xs">
        <div class="flex items-center justify-between text-xs text-gray-500 font-semibold">
          <span>Nouveaux Inscrits</span>
          <UIcon name="i-lucide-sparkles" class="w-4 h-4 text-amber-500" />
        </div>
        <p class="text-2xl font-bold text-amber-600 mt-2">{{ countByStage('new') }}</p>
      </div>

      <div class="bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-xl p-4 shadow-2xs">
        <div class="flex items-center justify-between text-xs text-gray-500 font-semibold">
          <span>Relances Envoyées</span>
          <UIcon name="i-lucide-send" class="w-4 h-4 text-blue-500" />
        </div>
        <p class="text-2xl font-bold text-blue-600 mt-2">{{ countByStage('Relance Envoyée') }}</p>
      </div>

      <div class="bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-xl p-4 shadow-2xs">
        <div class="flex items-center justify-between text-xs text-gray-500 font-semibold">
          <span>Convertis en Patients</span>
          <UIcon name="i-lucide-check-circle" class="w-4 h-4 text-emerald-500" />
        </div>
        <p class="text-2xl font-bold text-emerald-600 mt-2">{{ countByStage('converted') }}</p>
      </div>
    </div>

    <!-- Leads Table Card -->
    <div class="bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-2xl shadow-2xs overflow-hidden">
      <!-- Search & Filters -->
      <div class="p-4 border-b border-gray-100 dark:border-gray-800 flex flex-col sm:flex-row justify-between items-center gap-4 bg-gray-50/50 dark:bg-gray-800/40">
        <div class="relative w-full sm:w-80">
          <UIcon name="i-lucide-search" class="absolute left-3 top-2.5 w-4 h-4 text-gray-400" />
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Rechercher par nom ou numéro..."
            class="w-full pl-9 pr-3 py-1.5 text-xs bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:outline-hidden"
          />
        </div>

        <div class="flex gap-2">
          <select
            v-model="stageFilter"
            class="text-xs bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg px-3 py-1.5 text-gray-700 dark:text-gray-200"
          >
            <option value="all">Toutes les étapes</option>
            <option value="new">Nouveau (new)</option>
            <option value="Relance Envoyée">Relance Envoyée</option>
            <option value="RDV Fixé">RDV Fixé</option>
            <option value="converted">Converti en Patient</option>
          </select>
        </div>
      </div>

      <!-- Table Body -->
      <div class="overflow-x-auto">
        <table class="w-full text-left text-xs">
          <thead class="bg-gray-50 dark:bg-gray-800/80 text-gray-500 font-semibold border-b border-gray-100 dark:border-gray-800">
            <tr>
              <th class="p-4">Nom du Prospect</th>
              <th class="p-4">Numéro de Téléphone</th>
              <th class="p-4">Canal d'origine</th>
              <th class="p-4">Statut / Étape</th>
              <th class="p-4">Notes cliniques / IA</th>
              <th class="p-4">Date de réception</th>
              <th class="p-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100 dark:divide-gray-800">
            <tr
              v-for="lead in filteredLeads"
              :key="lead.id"
              class="hover:bg-gray-50/80 dark:hover:bg-gray-800/50 transition-colors"
            >
              <td class="p-4 font-bold text-gray-900 dark:text-white flex items-center gap-2">
                <div class="w-7 h-7 rounded-full bg-primary-100 text-primary-700 font-bold flex items-center justify-center text-[10px]">
                  {{ lead.name.slice(0, 2).toUpperCase() }}
                </div>
                <span>{{ lead.name }}</span>
              </td>
              <td class="p-4 font-mono text-gray-600 dark:text-gray-300">{{ lead.phone }}</td>
              <td class="p-4">
                <UBadge :color="lead.source === 'telegram' ? 'blue' : 'green'" variant="subtle" size="xs">
                  {{ lead.source.toUpperCase() }}
                </UBadge>
              </td>
              <td class="p-4">
                <UBadge :color="getStageColor(lead.stage)" variant="solid" size="xs">
                  {{ lead.stage }}
                </UBadge>
              </td>
              <td class="p-4 text-gray-600 dark:text-gray-300 max-w-xs truncate">{{ lead.notes || '—' }}</td>
              <td class="p-4 text-gray-400">{{ lead.createdAt }}</td>
              <td class="p-4 text-right">
                <div class="flex items-center justify-end gap-2">
                  <UButton
                    v-if="lead.stage !== 'converted'"
                    color="primary"
                    size="xs"
                    icon="i-lucide-user-check"
                    @click="convertToPatient(lead)"
                  >
                    Convertir en Patient
                  </UButton>
                  <UBadge v-else color="green" variant="subtle" size="xs">
                    Patient Confirmé
                  </UBadge>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Create Lead Modal (Nuxt UI v3 syntax) -->
    <UModal v-model:open="isCreateModalOpen">
      <template #content>
        <UCard>
          <template #header>
            <div class="flex items-center justify-between">
              <h3 class="font-bold text-base text-gray-900 dark:text-white flex items-center gap-2">
                <UIcon name="i-lucide-user-plus" class="text-primary-500 w-5 h-5" />
                Nouveau Prospect Manuel
              </h3>
              <UButton color="gray" variant="ghost" icon="i-lucide-x" size="xs" @click="isCreateModalOpen = false" />
            </div>
          </template>

          <div class="space-y-4 text-xs">
            <div>
              <label class="block font-bold text-gray-700 dark:text-gray-300 mb-1">Nom complet :</label>
              <input
                v-model="newLeadForm.name"
                type="text"
                placeholder="e.g. Karim Benali"
                class="w-full p-2.5 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-900 dark:text-white"
              />
            </div>

            <div>
              <label class="block font-bold text-gray-700 dark:text-gray-300 mb-1">Numéro de téléphone :</label>
              <input
                v-model="newLeadForm.phone"
                type="text"
                placeholder="e.g. 0555123456"
                class="w-full p-2.5 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-900 dark:text-white"
              />
            </div>

            <div>
              <label class="block font-bold text-gray-700 dark:text-gray-300 mb-1">Canal de contact :</label>
              <select
                v-model="newLeadForm.source"
                class="w-full p-2.5 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-900 dark:text-white"
              >
                <option value="telegram">Telegram</option>
                <option value="whatsapp">WhatsApp</option>
                <option value="instagram">Instagram Direct</option>
              </select>
            </div>

            <div>
              <label class="block font-bold text-gray-700 dark:text-gray-300 mb-1">Notes / Motif :</label>
              <textarea
                v-model="newLeadForm.notes"
                rows="3"
                placeholder="Motif de consultation, questions sur les tarifs en DZD..."
                class="w-full p-2.5 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-900 dark:text-white"
              ></textarea>
            </div>
          </div>

          <template #footer>
            <div class="flex justify-end gap-2">
              <UButton color="gray" variant="ghost" @click="isCreateModalOpen = false">Annuler</UButton>
              <UButton color="primary" @click="submitNewLead">Enregistrer le Prospect</UButton>
            </div>
          </template>
        </UCard>
      </template>
    </UModal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

definePageMeta({ middleware: 'auth' })

const toast = useToast()

interface Lead {
  id: string
  name: string
  phone: string
  source: 'telegram' | 'whatsapp' | 'instagram'
  stage: string
  notes?: string
  createdAt: string
}

const leads = ref<Lead[]>([
  {
    id: 'lead-1',
    name: 'Karim Benali',
    phone: '0555123456',
    source: 'telegram',
    stage: 'new',
    notes: 'Intéressé par blanchiment dentaire & bilan carie',
    createdAt: 'Aujourd\'hui 14:28'
  },
  {
    id: 'lead-2',
    name: 'Amina Khelil',
    phone: '0661987654',
    source: 'whatsapp',
    stage: 'Relance Envoyée',
    notes: 'Demande de devis blanchiment laser en DZD',
    createdAt: 'Aujourd\'hui 11:10'
  },
  {
    id: 'lead-3',
    name: 'Yacine Mansouri',
    phone: '0770456789',
    source: 'telegram',
    stage: 'converted',
    notes: 'RDV fixé pour pose d\'implant en Zircone',
    createdAt: 'Hier'
  }
])

const searchQuery = ref('')
const stageFilter = ref('all')
const isCreateModalOpen = ref(false)

const newLeadForm = ref({
  name: '',
  phone: '',
  source: 'telegram' as 'telegram' | 'whatsapp' | 'instagram',
  notes: ''
})

const filteredLeads = computed(() => {
  return leads.value.filter(l => {
    const matchSearch = l.name.toLowerCase().includes(searchQuery.value.toLowerCase()) || l.phone.includes(searchQuery.value)
    if (!matchSearch) return false
    if (stageFilter.value !== 'all' && l.stage !== stageFilter.value) return false
    return true
  })
})

function countByStage(stage: string) {
  return leads.value.filter(l => l.stage === stage).length
}

function getStageColor(stage: string) {
  switch (stage) {
    case 'new': return 'amber'
    case 'Relance Envoyée': return 'blue'
    case 'RDV Fixé': return 'fuchsia'
    case 'converted': return 'green'
    default: return 'gray'
  }
}

function submitNewLead() {
  if (!newLeadForm.value.name.trim() || !newLeadForm.value.phone.trim()) return
  const newL: Lead = {
    id: `lead-${Date.now()}`,
    name: newLeadForm.value.name,
    phone: newLeadForm.value.phone,
    source: newLeadForm.value.source,
    stage: 'new',
    notes: newLeadForm.value.notes,
    createdAt: 'À l\'instant'
  }
  leads.value.unshift(newL)
  isCreateModalOpen.value = false
  newLeadForm.value = { name: '', phone: '', source: 'telegram', notes: '' }
  toast.add({ title: 'Prospect ajouté avec succès ⚡', color: 'green' })
}

function convertToPatient(lead: Lead) {
  lead.stage = 'converted'
  toast.add({
    title: 'Prospect Converti en Patient ! 🎉',
    description: `${lead.name} a été validé et ajouté au registre officiel des patients.`,
    color: 'green'
  })
}
</script>
