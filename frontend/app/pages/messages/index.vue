<template>
  <div class="p-6 max-w-[1500px] mx-auto space-y-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-gray-100 dark:border-gray-800 pb-5">
      <div>
        <h1 class="text-2xl font-bold tracking-tight text-gray-900 dark:text-white flex items-center gap-2">
          <UIcon name="i-lucide-messages-square" class="text-primary-500 w-7 h-7" />
          Messagerie Omnicanal (Telegram & WhatsApp)
        </h1>
        <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Supervision en direct des conversations de l'IA n8n avec les patients du cabinet du Dr. Mokhtar.
        </p>
      </div>

      <div class="flex items-center gap-3">
        <div class="flex items-center gap-2 px-3 py-1.5 bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-900/50 rounded-lg text-xs font-semibold text-emerald-700 dark:text-emerald-300">
          <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          <span>Synchronisation live n8n active</span>
        </div>
      </div>
    </div>

    <!-- Main Chat Workspace: 2-Column Split -->
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 min-h-[700px]">
      <!-- Left Column: Conversations List (4 cols) -->
      <div class="lg:col-span-4 bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-2xl p-4 shadow-2xs flex flex-col space-y-4">
        <!-- Search & Filter -->
        <div class="space-y-3">
          <div class="relative">
            <UIcon name="i-lucide-search" class="absolute left-3 top-2.5 w-4 h-4 text-gray-400" />
            <input
              v-model="searchQuery"
              type="text"
              placeholder="Rechercher par nom ou numéro..."
              class="w-full pl-9 pr-3 py-2 text-xs bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:outline-hidden"
            />
          </div>

          <!-- Filter Badges -->
          <div class="flex gap-1.5 overflow-x-auto pb-1">
            <button
              v-for="filter in ['all', 'unread', 'urgent', 'human', 'ai']"
              :key="filter"
              type="button"
              :class="[
                'px-2.5 py-1 rounded-lg text-xs font-semibold whitespace-nowrap transition-colors flex items-center gap-1',
                activeFilter === filter
                  ? (filter === 'urgent' ? 'bg-rose-600 text-white' : 'bg-primary-600 text-white')
                  : (filter === 'urgent' ? 'bg-rose-50 text-rose-700 border border-rose-200 dark:bg-rose-950/40 dark:text-rose-300' : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300 hover:bg-gray-200')
              ]"
              @click="activeFilter = filter"
            >
              <span>{{ getFilterLabel(filter) }}</span>
              <span v-if="filter === 'urgent' && countUrgent > 0" class="px-1.5 py-0.2 bg-rose-500 text-white text-[10px] rounded-full font-bold">
                {{ countUrgent }}
              </span>
            </button>
          </div>
        </div>

        <!-- Thread List -->
        <div class="flex-grow overflow-y-auto space-y-2 pr-1">
          <div
            v-for="thread in filteredThreads"
            :key="thread.id"
            :class="[
              'p-3.5 rounded-xl border cursor-pointer transition-all duration-150 relative',
              selectedThread?.id === thread.id
                ? 'bg-primary-50/60 dark:bg-primary-950/40 border-primary-300 dark:border-primary-800 shadow-2xs'
                : (thread.isUrgent ? 'bg-rose-50/40 dark:bg-rose-950/20 border-rose-200 dark:border-rose-900/50 hover:bg-rose-50' : 'bg-white dark:bg-gray-800/40 border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800')
            ]"
            @click="selectThread(thread)"
          >
            <div class="flex items-start justify-between gap-2">
              <div class="flex items-center gap-2.5">
                <div
                  :class="[
                    'w-9 h-9 rounded-full flex items-center justify-center font-bold text-xs',
                    thread.isUrgent
                      ? 'bg-rose-100 dark:bg-rose-900/60 text-rose-700 dark:text-rose-300 ring-2 ring-rose-400'
                      : 'bg-primary-100 dark:bg-primary-900/60 text-primary-700 dark:text-primary-300'
                  ]"
                >
                  {{ getInitials(thread.name) }}
                </div>
                <div>
                  <h4 class="text-xs font-bold text-gray-900 dark:text-white flex items-center gap-1.5">
                    {{ thread.name }}
                    <span v-if="thread.platform === 'telegram'" class="text-[10px] text-[#0088cc] font-medium">Telegram</span>
                    <span v-else class="text-[10px] text-[#25D366] font-medium">WhatsApp</span>
                  </h4>
                  <p class="text-[11px] text-gray-500 font-mono">{{ thread.phone }}</p>
                </div>
              </div>
              <span class="text-[10px] text-gray-400 whitespace-nowrap">{{ thread.lastTime }}</span>
            </div>

            <p class="text-xs text-gray-600 dark:text-gray-300 mt-2 line-clamp-1">
              {{ thread.lastMessage }}
            </p>

            <div class="mt-2.5 flex flex-wrap items-center justify-between gap-1">
              <div class="flex items-center gap-1.5">
                <span
                  v-if="thread.isUrgent"
                  class="inline-flex items-center gap-1 text-[10px] font-bold text-white bg-rose-600 px-2 py-0.5 rounded shadow-2xs"
                >
                  <UIcon name="i-lucide-alert-triangle" class="w-3 h-3 animate-bounce" />
                  🚨 Urgence
                </span>

                <span
                  v-if="thread.isHumanActive"
                  class="inline-flex items-center gap-1 text-[10px] font-bold text-amber-600 bg-amber-50 dark:bg-amber-950/60 px-2 py-0.5 rounded"
                >
                  <UIcon name="i-lucide-user" class="w-3 h-3" />
                  Prise en main
                </span>
                <span
                  v-else
                  class="inline-flex items-center gap-1 text-[10px] font-bold text-emerald-600 bg-emerald-50 dark:bg-emerald-950/60 px-2 py-0.5 rounded"
                >
                  <UIcon name="i-lucide-bot" class="w-3 h-3" />
                  IA Active
                </span>
              </div>

              <span v-if="thread.hasRadio" class="text-[10px] font-semibold text-primary-600 flex items-center gap-1">
                <UIcon name="i-lucide-scan" class="w-3 h-3" />
                Radio jointe
              </span>
            </div>
          </div>

          <div v-if="filteredThreads.length === 0" class="text-center py-12 text-gray-400 text-xs">
            <UIcon name="i-lucide-inbox" class="w-8 h-8 mx-auto mb-2 opacity-50" />
            Aucune conversation dans ce filtre.
          </div>
        </div>
      </div>

      <!-- Right Column: Live Chat Area (8 cols) -->
      <div v-if="selectedThread" class="lg:col-span-8 bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-2xl shadow-2xs flex flex-col justify-between overflow-hidden">
        <!-- Top Bar -->
        <div class="p-4 border-b border-gray-100 dark:border-gray-800 flex items-center justify-between gap-4 bg-gray-50/50 dark:bg-gray-800/40">
          <div class="flex items-center gap-3">
            <div
              :class="[
                'w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm',
                selectedThread.isUrgent
                  ? 'bg-rose-100 dark:bg-rose-900/60 text-rose-700 dark:text-rose-300 ring-2 ring-rose-400'
                  : 'bg-primary-100 dark:bg-primary-900/60 text-primary-700 dark:text-primary-300'
              ]"
            >
              {{ getInitials(selectedThread.name) }}
            </div>
            <div>
              <h3 class="text-sm font-bold text-gray-900 dark:text-white flex items-center gap-2">
                {{ selectedThread.name }}
                <UBadge :color="selectedThread.platform === 'telegram' ? 'blue' : 'green'" variant="subtle" size="xs">
                  {{ selectedThread.platform.toUpperCase() }}
                </UBadge>
                <UBadge v-if="selectedThread.isUrgent" color="rose" variant="solid" size="xs">
                  🚨 URGENCE
                </UBadge>
              </h3>
              <p class="text-xs text-gray-500 font-mono">{{ selectedThread.phone }}</p>
            </div>
          </div>

          <div class="flex items-center gap-2">
            <!-- 1-Click Human Takeover Toggle -->
            <button
              type="button"
              :class="[
                'inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg shadow-2xs transition-colors',
                selectedThread.isHumanActive
                  ? 'bg-primary-600 hover:bg-primary-700 text-white'
                  : 'bg-amber-500 hover:bg-amber-600 text-white'
              ]"
              @click="toggleTakeover"
            >
              <UIcon :name="selectedThread.isHumanActive ? 'i-lucide-bot' : 'i-lucide-hand'" class="w-3.5 h-3.5" />
              <span>{{ selectedThread.isHumanActive ? 'Rendre la main à l\'IA' : 'Prendre la main' }}</span>
            </button>

            <!-- Go to Patient File -->
            <UButton
              v-if="selectedThread.patientId"
              :to="`/patients/${selectedThread.patientId}`"
              icon="i-lucide-external-link"
              color="gray"
              variant="outline"
              size="xs"
            >
              Dossier Patient
            </UButton>
          </div>
        </div>

        <!-- Chat Stream -->
        <div class="flex-grow p-6 overflow-y-auto space-y-4 max-h-[500px]">
          <div
            v-for="msg in selectedThread.messages"
            :key="msg.id"
            :class="[
              'flex flex-col max-w-[80%]',
              msg.sender === 'patient' ? 'self-start items-start' : 'self-end items-end'
            ]"
          >
            <div
              :class="[
                'rounded-2xl p-4 text-xs leading-relaxed space-y-2',
                msg.sender === 'patient'
                  ? 'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-white rounded-bl-xs'
                  : 'bg-primary-600 text-white rounded-br-xs'
              ]"
            >
              <div class="flex items-center justify-between gap-3 text-[10px] opacity-75 font-semibold">
                <span>{{ msg.sender === 'patient' ? selectedThread.name : (msg.sender === 'doctor' ? '👨‍⚕️ Dr. Mokhtar' : '🤖 Dr. Mokhtar AI (n8n)') }}</span>
                <span>{{ msg.time }}</span>
              </div>

              <!-- Media Attachment (if present) -->
              <div v-if="msg.imageUrl" class="rounded-lg overflow-hidden border border-white/20 my-2 cursor-pointer" @click="openLightbox(msg.imageUrl)">
                <img :src="msg.imageUrl" class="w-full max-h-48 object-cover hover:scale-105 transition-transform" />
                <p class="text-[10px] p-1 bg-black/40 text-center">📸 Cliquez pour agrandir la radiographie</p>
              </div>

              <p class="whitespace-pre-line">{{ msg.content }}</p>
            </div>
          </div>
        </div>

        <!-- Bottom Actions & Input -->
        <div class="p-4 border-t border-gray-100 dark:border-gray-800 space-y-3 bg-gray-50/50 dark:bg-gray-800/20">
          <!-- Quick Prompt Chips -->
          <div class="flex flex-wrap gap-1.5">
            <button
              v-for="chip in quickChips"
              :key="chip"
              type="button"
              class="text-[11px] font-medium px-2.5 py-1 bg-white dark:bg-gray-800 hover:bg-primary-50 hover:text-primary-600 text-gray-700 dark:text-gray-300 rounded-lg border border-gray-200 dark:border-gray-700 transition-colors"
              @click="insertChip(chip)"
            >
              {{ chip }}
            </button>
          </div>

          <!-- Message Composer -->
          <div class="flex gap-2">
            <input
              v-model="replyText"
              type="text"
              placeholder="Tapez votre message pour le patient..."
              class="flex-grow text-xs bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl px-3.5 py-2.5 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:outline-hidden"
              @keyup.enter="sendReply"
            />
            <button
              type="button"
              class="px-4 py-2.5 bg-primary-600 hover:bg-primary-700 text-white rounded-xl text-xs font-semibold transition-colors flex items-center gap-1.5"
              :disabled="!replyText.trim()"
              @click="sendReply"
            >
              <UIcon name="i-lucide-send" class="w-4 h-4" />
              <span>Envoyer</span>
            </button>
          </div>
        </div>
      </div>

      <!-- No Thread Selected State -->
      <div v-else class="lg:col-span-8 bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-2xl p-16 text-center shadow-2xs flex flex-col items-center justify-center">
        <UIcon name="i-lucide-messages-square" class="w-16 h-16 text-gray-300 dark:text-gray-700 mb-3" />
        <h3 class="text-base font-bold text-gray-900 dark:text-white">Sélectionnez une conversation</h3>
        <p class="text-xs text-gray-500 dark:text-gray-400 mt-1 max-w-sm">
          Choisissez une conversation à gauche pour consulter les échanges et prendre la main si nécessaire.
        </p>
      </div>
    </div>

    <!-- Lightbox Modal (Nuxt UI v3 syntax) -->
    <UModal v-model:open="isLightboxOpen">
      <template #content>
        <UCard :ui="{ body: { padding: 'p-0 sm:p-0' } }">
          <div class="relative bg-black flex items-center justify-center max-h-[85vh] p-2">
            <img :src="selectedImageUrl" class="max-w-full max-h-[80vh] object-contain rounded" />
            <button
              type="button"
              class="absolute top-4 right-4 p-2 bg-black/60 hover:bg-black/90 text-white rounded-full transition-colors"
              @click="isLightboxOpen = false"
            >
              <UIcon name="i-lucide-x" class="w-5 h-5" />
            </button>
          </div>
        </UCard>
      </template>
    </UModal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'

definePageMeta({ middleware: 'auth' })

const toast = useToast()

interface ChatThread {
  id: string
  name: string
  phone: string
  platform: 'telegram' | 'whatsapp'
  patientId?: string
  lastMessage: string
  lastTime: string
  isHumanActive: boolean
  isUrgent?: boolean
  hasRadio: boolean
  messages: Array<{
    id: string
    sender: 'patient' | 'ai_bot' | 'doctor'
    content: string
    time: string
    imageUrl?: string
  }>
}

const defaultSeedThreads: ChatThread[] = [
  {
    id: 'thread-1',
    name: 'Karim Benali',
    phone: '+213 555 12 34 56',
    platform: 'telegram',
    lastMessage: 'Voici ma panoramique faite la semaine dernière.',
    lastTime: '14:32',
    isHumanActive: false,
    isUrgent: true,
    hasRadio: true,
    messages: [
      {
        id: 'm1',
        sender: 'patient',
        content: 'Bonjour docteur, j\'ai une vive douleur et rage de dent sur la molaire droite depuis hier soir.',
        time: '14:28'
      },
      {
        id: 'm2',
        sender: 'ai_bot',
        content: 'Bonjour Karim ! Je suis l\'assistant du cabinet du Dr. Mokhtar. Pouvez-vous nous transmettre une photo ou votre dernière radio pour que le docteur analyse la situation d\'urgence ?',
        time: '14:29'
      },
      {
        id: 'm3',
        sender: 'patient',
        content: 'Voici ma panoramique faite la semaine dernière.',
        time: '14:31',
        imageUrl: 'https://images.unsplash.com/photo-1588776814546-1ffcf47267a5?auto=format&fit=crop&w=1000&q=80'
      },
      {
        id: 'm4',
        sender: 'ai_bot',
        content: 'Merci ! Notre IA a détecté une suspicion de carie sur la dent #16 et a préparé votre dossier clinique d\'urgence pour le Dr. Mokhtar. Souhaitez-vous un rendez-vous prioritaire demain à 10h00 ?',
        time: '14:32'
      }
    ]
  },
  {
    id: 'thread-2',
    name: 'Amina Khelil',
    phone: '+213 661 98 76 54',
    platform: 'whatsapp',
    lastMessage: 'Parfait pour jeudi à 14h30, merci !',
    lastTime: '11:15',
    isHumanActive: false,
    isUrgent: false,
    hasRadio: false,
    messages: [
      {
        id: 'm21',
        sender: 'patient',
        content: 'Bonjour, quels sont vos tarifs pour un blanchiment laser ?',
        time: '11:10'
      },
      {
        id: 'm22',
        sender: 'ai_bot',
        content: 'Bonjour Amina ! Le blanchiment laser au fauteuil est réalisé en 1 séance de 45 min avec des tarifs transparents en DZD. Nous avons une disponibilité ce jeudi à 14h30.',
        time: '11:12'
      },
      {
        id: 'm23',
        sender: 'patient',
        content: 'Parfait pour jeudi à 14h30, merci !',
        time: '11:15'
      }
    ]
  },
  {
    id: 'thread-3',
    name: 'Yacine Mansouri',
    phone: '+213 770 45 67 89',
    platform: 'telegram',
    lastMessage: 'Je serai là à l\'heure pour la pose de l\'implant.',
    lastTime: 'Hier',
    isHumanActive: true,
    isUrgent: false,
    hasRadio: true,
    messages: [
      {
        id: 'm31',
        sender: 'patient',
        content: 'Bonjour Dr. Mokhtar, est-ce que je dois être à jeun pour la chirurgie ?',
        time: 'Hier 16:40'
      },
      {
        id: 'm32',
        sender: 'doctor',
        content: 'Bonjour Yacine, non ce n\'est pas nécessaire, mangez léger 2h avant la consultation.',
        time: 'Hier 17:00'
      },
      {
        id: 'm33',
        sender: 'patient',
        content: 'Je serai là à l\'heure pour la pose de l\'implant.',
        time: 'Hier 17:05'
      }
    ]
  }
]

const threads = ref<ChatThread[]>([...defaultSeedThreads])
const selectedThread = ref<ChatThread | null>(threads.value[0])
const searchQuery = ref('')
const activeFilter = ref('all')
const replyText = ref('')

let syncTimer: any = null

async function syncLiveThreads() {
  try {
    const liveThreads = await $fetch<any[]>('/api/messages/threads')
    if (Array.isArray(liveThreads) && liveThreads.length > 0) {
      liveThreads.forEach(live => {
        const existingIdx = threads.value.findIndex(t => t.phone.replace(/\D/g, '') === live.phone.replace(/\D/g, ''))
        const mapped: ChatThread = {
          id: live.id || `thread-${live.phone}`,
          name: live.name || live.phone,
          phone: live.phone,
          platform: live.platform || 'telegram',
          patientId: live.patient_id || undefined,
          lastMessage: live.last_message || '',
          lastTime: live.last_time ? new Date(live.last_time).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }) : 'À l\'instant',
          isHumanActive: live.is_human_active || false,
          isUrgent: live.is_urgent || false,
          hasRadio: live.has_radio || false,
          messages: Array.isArray(live.messages) ? live.messages : []
        }

        if (existingIdx >= 0) {
          threads.value[existingIdx] = mapped
          if (selectedThread.value?.id === mapped.id) {
            selectedThread.value = mapped
          }
        } else {
          threads.value.unshift(mapped)
        }
      })
    }
  } catch {}
}

onMounted(() => {
  syncLiveThreads()
  syncTimer = setInterval(syncLiveThreads, 3000) // 3-second live sync loop
})

onUnmounted(() => {
  if (syncTimer) clearInterval(syncTimer)
})

// Lightbox
const isLightboxOpen = ref(false)
const selectedImageUrl = ref('')

function openLightbox(url: string) {
  selectedImageUrl.value = url
  isLightboxOpen.value = true
}

const quickChips = [
  '⚡ Créneau d\'urgence disponible aujourd\'hui',
  '📅 Proposer un RDV demain à 10h00',
  '🩻 Demander une radio panoramique',
  '💰 Envoyer devis transparent en DZD',
  '📲 Confirmer la réservation'
]

function insertChip(chip: string) {
  replyText.value = chip.slice(2).trim()
}

const countUrgent = computed(() => {
  return threads.value.filter(t => t.isUrgent).length
})

const filteredThreads = computed(() => {
  return threads.value.filter(t => {
    const matchSearch = t.name.toLowerCase().includes(searchQuery.value.toLowerCase()) || t.phone.includes(searchQuery.value)
    if (!matchSearch) return false
    if (activeFilter.value === 'unread') return t.id === 'thread-1'
    if (activeFilter.value === 'urgent') return t.isUrgent === true
    if (activeFilter.value === 'human') return t.isHumanActive
    if (activeFilter.value === 'ai') return !t.isHumanActive
    return true
  }).sort((a, b) => {
    if (a.isUrgent && !b.isUrgent) return -1
    if (!a.isUrgent && b.isUrgent) return 1
    return 0
  })
})

function selectThread(thread: ChatThread) {
  selectedThread.value = thread
}

function getInitials(name: string) {
  return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
}

function getFilterLabel(filter: string) {
  switch(filter) {
    case 'all': return 'Toutes'
    case 'unread': return 'Non lus'
    case 'urgent': return '🚨 Urgences'
    case 'human': return 'Prise en main'
    case 'ai': return 'IA Active'
    default: return filter
  }
}

function toggleTakeover() {
  if (!selectedThread.value) return
  selectedThread.value.isHumanActive = !selectedThread.value.isHumanActive
  const active = selectedThread.value.isHumanActive
  toast.add({
    title: active ? 'Prise en main activée (IA en pause)' : 'Assistant IA réactivé',
    description: active ? 'Vous répondez désormais en direct au patient.' : 'L\'IA n8n reprend les réponses automatiques.',
    color: active ? 'amber' : 'green'
  })

  try {
    $fetch(`/api/chats/takeover?phone=${encodeURIComponent(selectedThread.value.phone)}&active=${active}`, {
      method: 'POST'
    }).catch(() => {})
  } catch {}
}

function sendReply() {
  if (!selectedThread.value || !replyText.value.trim()) return
  const text = replyText.value.trim()
  selectedThread.value.messages.push({
    id: `m-${Date.now()}`,
    sender: 'doctor',
    content: text,
    time: new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
  })
  selectedThread.value.lastMessage = text
  selectedThread.value.lastTime = 'À l\'instant'

  try {
    $fetch('/api/messages/outbound', {
      method: 'POST',
      body: {
        phone: selectedThread.value.phone,
        content: text,
        sender: 'doctor',
        timestamp: new Date().toISOString()
      }
    }).catch(() => {})
  } catch {}

  replyText.value = ''
  toast.add({ title: 'Message envoyé au patient 🚀', color: 'green' })
}
</script>
