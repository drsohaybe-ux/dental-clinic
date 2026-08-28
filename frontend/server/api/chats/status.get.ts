export default defineEventHandler(async (event) => {
  const query = getQuery(event)
  const config = useRuntimeConfig()
  const backendBase = config.apiBaseUrlServer || config.public.apiBaseUrl || 'https://dental-api-2z19.onrender.com'

  try {
    const res = await $fetch(`${backendBase}/api/v1/omnichannel_bridge/chats/status`, {
      params: query
    })
    return res
  } catch (err: any) {
    return {
      is_human_active: false,
      patient_id: null,
      has_active_booking: false
    }
  }
})
