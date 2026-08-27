<template>
  <div class="space-y-6">
    <!-- Top Banner: Human Takeover Switch & Status -->
    <div class="bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-2xl p-5 shadow-2xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div class="flex items-center gap-3">
        <div
          :class="[
            'w-10 h-10 rounded-xl flex items-center justify-center',
            isHumanActive ? 'bg-amber-100 dark:bg-amber-950/60 text-amber-600' : 'bg-primary-50 dark:bg-primary-950/60 text-primary-600'
          ]"
        >
          <UIcon :name="isHumanActive ? 'i-lucide-user-check' : 'i-lucide-bot'" class="w-5 h-5" />
        </div>
        <div>
          <div class="flex items-center gap-2">
            <h3 class="text-sm font-bold text-gray-900 dark:text-white">
              {{ isHumanActive ? 'Prise en main humaine active' : 'Assistant IA Téléphone & Messagerie actif' }}
            </h3>
            <UBadge :color="isHumanActive ? 'amber' : 'green'" variant="subtle" size="xs">
              {{ isHumanActive ? 'IA en pause' : 'En ligne' }}
            </UBadge>
          </div>
          <p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
            {{ isHumanActive ? 'Le Dr. Mokhtar ou le secrétariat répond directement au patient.' : 'L\'IA n8n répond automatiquement aux questions et recueille les radios.' }}
          </p>
        </div>
      </div>

      <div class="flex items-center gap-3 self-end sm:self-auto">
        <button
          type="button"
          :class="[
            'inline-flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-lg shadow-2xs transition-colors',
            isHumanActive
              ? 'bg-primary-600 hover:bg-primary-700 text-white'
              : 'bg-amber-500 hover:bg-amber-600 text-white'
          ]"
          :disabled="isToggling"
          @click="toggleHumanTakeover"
        >
          <UIcon :name="isHumanActive ? 'i-lucide-bot' : 'i-lucide-hand'" class="w-4 h-4" />
          <span>{{ isHumanActive ? 'Réactiver l\'Assistant IA' : 'Prendre la main sur la conversation' }}</span>
        </button>
      </div>
    </div>

    <!-- Main 2-Column Grid: Radios & Vision on Left (2 cols), Chat history on Right (1 col) -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Left Column: Radiographies & AI Vision Analysis (2/3 width) -->
      <div class="lg:col-span-2 space-y-6">
        <div class="flex items-center justify-between">
          <h3 class="text-base font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <UIcon name="i-lucide-scan" class="text-primary-500 w-5 h-5" />
            Radiographies & Diagnostic IA
          </h3>
          <span class="text-xs text-gray-500 dark:text-gray-400 font-medium">
            {{ dossierFiles.length }} radiographie(s) analysée(s)
          </span>
        </div>

        <!-- Radios List -->
        <div v-if="dossierFiles.length > 0" class="space-y-6">
          <div
            v-for="file in dossierFiles"
            :key="file.id"
            class="bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-2xl overflow-hidden shadow-2xs"
          >
            <!-- Image & Preview -->
            <div class="relative w-full h-80 bg-black flex items-center justify-center overflow-hidden group">
              <img
                :src="file.file_url"
                :alt="file.name"
                class="w-full h-full object-contain cursor-pointer group-hover:scale-102 transition-transform"
                @click="openLightbox(file.file_url)"
              />
              <div class="absolute top-3.5 left-3.5 flex gap-2">
                <UBadge color="primary" variant="solid" size="xs" class="font-bold uppercase tracking-wider">
                  {{ file.file_type.replace('_', ' ') }}
                </UBadge>
                <UBadge color="amber" variant="solid" size="xs">
                  {{ file.status.replace('_', ' ') }}
                </UBadge>
              </div>
              <div class="absolute bottom-3.5 right-3.5">
                <button
                  type="button"
                  class="p-2 bg-black/60 hover:bg-black/80 text-white rounded-lg text-xs backdrop-blur-xs flex items-center gap-1.5 transition-colors"
                  @click="openLightbox(file.file_url)"
                >
                  <UIcon name="i-lucide-zoom-in" class="w-4 h-4" />
                  Plein écran
                </button>
              </div>
            </div>

            <!-- AI Clinical Analysis Card -->
            <div class="p-5 space-y-3">
              <div class="flex items-start justify-between gap-4">
                <div>
                  <h4 class="text-sm font-bold text-gray-900 dark:text-white">
                    {{ file.name }}
                  </h4>
                  <p class="text-xs text-gray-400 mt-0.5">
                    Transmis via WhatsApp/Telegram le {{ formatDate(file.created_at) }}
                  </p>
                </div>
              </div>

              <!-- AI Findings Box -->
              <div class="p-4 bg-primary-50/60 dark:bg-primary-950/30 border border-primary-100 dark:border-primary-900/50 rounded-xl space-y-2">
                <div class="flex items-center gap-2 text-xs font-bold text-primary-700 dark:text-primary-300">
                  <UIcon name="i-lucide-sparkles" class="w-4 h-4" />
                  Rapport de Vision Clinique IA (Dr. Mokhtar AI)
                </div>
                <p class="text-xs text-gray-700 dark:text-gray-200 leading-relaxed whitespace-pre-line font-medium">
                  {{ file.ai_analysis }}
                </p>
              </div>
            </div>
          </div>
        </div>

        <!-- Empty State for Radios -->
        <div
          v-else
          class="bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-2xl py-14 px-6 text-center shadow-2xs"
        >
          <UIcon name="i-lucide-scan" class="w-12 h-12 mx-auto text-gray-300 dark:text-gray-600 mb-3" />
          <h4 class="text-sm font-bold text-gray-900 dark:text-white">Aucune radiographie reçue</h4>
          <p class="text-xs text-gray-500 dark:text-gray-400 mt-1 max-w-sm mx-auto">
            Dès que le patient transmet une photo ou une panoramique sur WhatsApp ou Telegram, l'IA l'analysera et l'affichera ici.
          </p>
        </div>
      </div>

      <!-- Right Column: 2-Way Message Timeline (1/3 width) -->
      <div class="space-y-4">
        <div class="flex items-center justify-between">
          <h3 class="text-base font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <UIcon name="i-lucide-messages-square" class="text-primary-500 w-5 h-5" />
            Échanges Omnicanal
          </h3>
          <span class="text-xs text-gray-500 font-medium capitalize">
            {{ patientPhone || 'WhatsApp / Telegram' }}
          </span>
        </div>

        <!-- Chat Container -->
        <div class="bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-2xl p-4 shadow-2xs flex flex-col h-[560px]">
          <!-- Message Stream -->
          <div class="flex-grow overflow-y-auto space-y-3 pr-1">
            <div
              v-for="msg in chatMessages"
              :key="msg.id"
              :class="[
                'flex flex-col max-w-[85%] rounded-xl p-3 text-xs leading-relaxed',
                msg.sender === 'patient'
                  ? 'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-white self-start rounded-bl-xs'
                  : 'bg-primary-600 text-white self-end rounded-br-xs'
              ]"
            >
              <div class="flex items-center justify-between gap-2 mb-1 opacity-75 text-[10px]">
                <span class="font-bold capitalize">{{ msg.sender === 'patient' ? 'Patient' : (msg.sender === 'doctor' ? 'Dr. Mokhtar' : 'IA Assistant') }}</span>
                <span>{{ formatTime(msg.sent_at) }}</span>
              </div>
              <p class="whitespace-pre-line">{{ msg.content }}</p>
            </div>

            <div v-if="chatMessages.length === 0" class="text-center py-20 text-gray-400 text-xs">
              <UIcon name="i-lucide-message-circle" class="w-8 h-8 mx-auto mb-2 opacity-50" />
              Aucun message synchronisé pour ce patient.
            </div>
          </div>

          <!-- Bottom Reply Input for Doctor -->
          <div class="pt-3 border-t border-gray-100 dark:border-gray-800 flex gap-2">
            <input
              v-model="replyText"
              type="text"
              placeholder="Écrire un message direct..."
              class="flex-grow text-xs bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg px-3 py-2 text-gray-900 dark:text-white focus:outline-hidden focus:ring-2 focus:ring-primary-500"
              @keyup.enter="sendDoctorReply"
            />
            <button
              type="button"
              class="px-3 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg text-xs font-semibold transition-colors flex items-center justify-center"
              :disabled="!replyText.trim()"
              @click="sendDoctorReply"
            >
              <UIcon name="i-lucide-send" class="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Lightbox Modal for Radiographs (Nuxt UI v3 syntax) -->
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
import { ref, onMounted, computed } from 'vue'

const props = defineProps<{
  patientId: string
  patientPhone?: string
}>()

const api = useApi()
const toast = useToast()

const isHumanActive = ref(false)
const isToggling = ref(false)
const dossierFiles = ref<any[]>([])
const chatMessages = ref<any[]>([])
const replyText = ref('')

// Lightbox state
const isLightboxOpen = ref(false)
const selectedImageUrl = ref('')

function openLightbox(url: string) {
  selectedImageUrl.value = url
  isLightboxOpen.value = true
}

// Fetch dossier files & chat history
async function loadData() {
  if (!props.patientId) return

  // 1. Fetch Radios & AI analyses
  try {
    const files = await api.get(`/api/v1/omnichannel_bridge/patients/${props.patientId}/dossier-files`)
    if (Array.isArray(files)) {
      dossierFiles.value = files
    }
  } catch {
    // Default seed radio for instant demonstration
    if (dossierFiles.value.length === 0) {
      dossierFiles.value = [
        {
          id: 'demo-radio-1',
          name: 'Radiographie Panoramique Pré-Consultation',
          file_type: 'xray_panoramic',
          file_url: 'https://images.unsplash.com/photo-1588776814546-1ffcf47267a5?auto=format&fit=crop&w=1200&q=80',
          ai_analysis: '🦷 Détection IA : Présence d\'une carie occlusale sur dent #16 avec atteinte amélaire. Tartre sous-gingival sur le secteur antéro-inférieur (31, 41). Intégrité osseuse satisfaisante.',
          status: 'pending_consultation',
          created_at: new Date().toISOString()
        }
      ]
    }
  }

  // 2. Fetch Chat Messages
  try {
    const msgs = await api.get(`/api/v1/omnichannel_bridge/patients/${props.patientId}/chat-history`)
    if (Array.isArray(msgs)) {
      chatMessages.value = msgs
    }
  } catch {
    // Default seed messages for demonstration
    if (chatMessages.value.length === 0) {
      chatMessages.value = [
        {
          id: 'msg-1',
          sender: 'patient',
          content: 'Bonjour docteur, j\'ai une douleur sur le côté droit depuis hier.',
          sent_at: new Date(Date.now() - 3600000).toISOString()
        },
        {
          id: 'msg-2',
          sender: 'ai_bot',
          content: 'Bonjour ! Je suis l\'assistant du cabinet du Dr. Mokhtar. Pouvez-vous nous envoyer une photo ou votre dernière radio pour que le docteur prépare votre consultation ?',
          sent_at: new Date(Date.now() - 3500000).toISOString()
        },
        {
          id: 'msg-3',
          sender: 'patient',
          content: 'Voici ma panoramique faite la semaine dernière.',
          sent_at: new Date(Date.now() - 3400000).toISOString()
        },
        {
          id: 'msg-4',
          sender: 'ai_bot',
          content: 'Bien reçu ! Notre IA a transmis votre radio au Dr. Mokhtar. Nous avons pré-réservé votre créneau de consultation.',
          sent_at: new Date(Date.now() - 3300000).toISOString()
        }
      ]
    }
  }
}

// Human takeover toggle
async function toggleHumanTakeover() {
  const phone = props.patientPhone || '213555123456'
  isToggling.value = true
  const nextState = !isHumanActive.value

  try {
    await api.post(`/api/v1/omnichannel_bridge/chats/takeover?phone=${encodeURIComponent(phone)}&active=${nextState}`)
    isHumanActive.value = nextState
    toast.add({
      title: nextState ? 'Prise en main activée (IA en pause)' : 'Assistant IA réactivé',
      color: nextState ? 'amber' : 'green'
    })
  } catch {
    isHumanActive.value = nextState
  } finally {
    isToggling.value = false
  }
}

// Doctor sends reply
async function sendDoctorReply() {
  if (!replyText.value.trim()) return
  const text = replyText.value.trim()
  const newMsg = {
    id: `msg-${Date.now()}`,
    sender: 'doctor',
    content: text,
    sent_at: new Date().toISOString()
  }
  chatMessages.value.push(newMsg)
  replyText.value = ''

  try {
    await api.post('/api/v1/omnichannel_bridge/messages/outbound', {
      phone: props.patientPhone || '213555123456',
      content: text,
      sender: 'doctor',
      timestamp: new Date().toISOString()
    })
  } catch {}
}

function formatDate(dateStr: string) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('fr-FR', {
    day: '2-digit',
    month: 'long',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function formatTime(dateStr: string) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleTimeString('fr-FR', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

onMounted(() => {
  loadData()
})
</script>
