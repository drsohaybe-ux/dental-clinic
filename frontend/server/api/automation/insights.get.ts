export default defineEventHandler(async (event) => {
  const query = getQuery(event)
  const config = useRuntimeConfig()
  const backendBase = config.apiBaseUrlServer || config.public.apiBaseUrl || 'https://dental-api-2z19.onrender.com'
  const authHeader = getHeader(event, 'authorization') || ''

  try {
    const params = new URLSearchParams()
    if (query.platform) params.append('platform', String(query.platform))
    if (query.days) params.append('days', String(query.days))

    const queryString = params.toString() ? `?${params.toString()}` : ''
    const res = await $fetch(`${backendBase}/api/v1/social_automation/insights${queryString}`, {
      headers: {
        ...(authHeader ? { Authorization: authHeader } : {})
      }
    })

    return {
      success: true,
      data: Array.isArray(res) ? res : []
    }
  } catch (err: any) {
    // Graceful fallback when backend or table is unavailable yet
    return {
      success: true,
      data: [],
      note: 'Awaiting backend/n8n synchronization'
    }
  }
})
