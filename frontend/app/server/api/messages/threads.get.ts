declare global {
  var __DENTAL_MESSAGES__: any[]
}

globalThis.__DENTAL_MESSAGES__ = globalThis.__DENTAL_MESSAGES__ || []

export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()
  const backendBase = config.apiBaseUrlServer || config.public.apiBaseUrl

  let dbThreads: any[] = []
  try {
    const res = await $fetch<any[]>(`${backendBase}/api/v1/omnichannel_bridge/conversations`)
    if (Array.isArray(res)) {
      dbThreads = res
    }
  } catch {}

  // Merge in-memory edge messages
  const memoryMsgs = globalThis.__DENTAL_MESSAGES__ || []
  const threadsMap = new Map<string, any>()

  // 1. Put DB threads into map
  for (const t of dbThreads) {
    threadsMap.set(t.phone, { ...t })
  }

  // 2. Overlay in-memory messages
  for (const m of memoryMsgs) {
    const phone = m.phone
    if (!threadsMap.has(phone)) {
      threadsMap.set(phone, {
        id: `thread-${phone}`,
        phone,
        platform: m.platform || 'telegram',
        name: m.name || phone,
        last_message: m.content,
        last_time: m.sent_at,
        is_human_active: false,
        is_urgent: m.is_urgent || false,
        has_radio: false,
        messages: []
      })
    }
    const t = threadsMap.get(phone)
    t.last_message = m.content
    t.last_time = m.sent_at
    if (m.is_urgent) t.is_urgent = true
    if (!t.messages.some((existing: any) => existing.id === m.id)) {
      t.messages.push({
        id: m.id,
        sender: m.sender,
        content: m.content,
        time: new Date(m.sent_at).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
      })
    }
  }

  return Array.from(threadsMap.values())
})
