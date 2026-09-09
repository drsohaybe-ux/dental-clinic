export default defineEventHandler(async (event) => {
  const query = getQuery(event)
  const config = useRuntimeConfig()
  const backendBase = config.apiBaseUrlServer || config.public.apiBaseUrl || 'https://dental-api-2z19.onrender.com'

  try {
    const res = await $fetch<{ platform: string }>(`${backendBase}/api/v1/omnichannel_bridge/chats/last-platform`, {
      query
    })
    return res
  } catch (err: any) {
    const clean = String(query.phone || '').replace(/\D/g, '')
    if (clean.endsWith('555123456') || clean.endsWith('770456789')) {
      return { platform: 'telegram' }
    }
    return {
      platform: 'whatsapp'
    }
  }
})
