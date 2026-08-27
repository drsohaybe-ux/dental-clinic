export default defineEventHandler(async (event) => {
  const query = getQuery(event)
  const config = useRuntimeConfig()
  const backendBase = config.apiBaseUrlServer || config.public.apiBaseUrl

  try {
    const res = await $fetch(`${backendBase}/api/v1/omnichannel_bridge/chats/status`, {
      params: query
    })
    return res
  } catch (err: any) {
    // Fallback response matching contract
    return {
      is_human_active: false,
      patient_id: null,
      has_active_booking: false
    }
  }
})
