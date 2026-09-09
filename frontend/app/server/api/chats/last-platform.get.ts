export default defineEventHandler(async (event) => {
  const query = getQuery(event)
  const config = useRuntimeConfig()
  const backendBase = config.apiBaseUrlServer || config.public.apiBaseUrl || 'https://dental-api-2z19.onrender.com'

  try {
    const res = await $fetch<{ platform: string }>(`${backendBase}/api/v1/omnichannel_bridge/chats/last-platform`, {
      params: query
    })
    return res
  } catch (err: any) {
    return {
      platform: 'whatsapp'
    }
  }
})
