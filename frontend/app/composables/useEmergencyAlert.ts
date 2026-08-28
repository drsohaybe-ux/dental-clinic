import { ref, computed } from 'vue'

export interface EmergencyCase {
  id: string
  phone: string
  name: string
  lastMessage: string
  lastTime?: string
  platform?: string
}

const activeEmergency = ref<EmergencyCase | null>(null)
const isDismissed = ref(false)
let syncInterval: any = null

export function useEmergencyAlert() {
  const api = useApi()
  const router = useRouter()

  async function checkEmergencies() {
    try {
      const threads = await api.get<any[]>('/api/v1/omnichannel_bridge/conversations')
      if (Array.isArray(threads)) {
        const urgent = threads.find(t => t.is_urgent)
        if (urgent) {
          if (activeEmergency.value?.phone !== urgent.phone) {
            // New emergency detected -> reset dismiss state
            isDismissed.value = false
          }
          activeEmergency.value = {
            id: urgent.id || `thread-${urgent.phone}`,
            phone: urgent.phone,
            name: urgent.name || urgent.phone,
            lastMessage: urgent.last_message || 'Signale une douleur aiguë ou urgence dentaire',
            lastTime: urgent.last_time,
            platform: urgent.platform || 'telegram'
          }
        } else {
          activeEmergency.value = null
        }
      }
    } catch {}
  }

  function startGlobalSync() {
    if (typeof window === 'undefined') return
    if (!syncInterval) {
      checkEmergencies()
      syncInterval = setInterval(checkEmergencies, 4000)
    }
  }

  function dismissEmergency() {
    isDismissed.value = true
  }

  function openEmergencyChat() {
    router.push('/messages')
  }

  function clearEmergency() {
    activeEmergency.value = null
    isDismissed.value = true
  }

  return {
    activeEmergency,
    isDismissed,
    hasActiveAlert: computed(() => Boolean(activeEmergency.value && !isDismissed.value)),
    checkEmergencies,
    startGlobalSync,
    dismissEmergency,
    openEmergencyChat,
    clearEmergency
  }
}
