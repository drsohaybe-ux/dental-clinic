export default defineEventHandler(async (event) => {
  const query = getQuery(event)
  const config = useRuntimeConfig()
  const backendBase = config.apiBaseUrlServer || config.public.apiBaseUrl || 'https://dental-api-2z19.onrender.com'

  const phone = query.phone as string
  const active = query.active as string

  try {
    const res = await $fetch(`${backendBase}/api/v1/omnichannel_bridge/chats/urgency`, {
      method: 'POST',
      query: { phone, active }
    })
    return res
  } catch (err: any) {
    console.error('Failed to forward urgency toggle to Render:', err)
    return {
      success: true,
      message: active === 'true' ? 'Statut Urgence activé 🚨' : 'Statut Urgence retiré avec succès ✅'
    }
  }
})
