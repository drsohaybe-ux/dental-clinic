export default defineEventHandler(async (event) => {
  const body = await readBody(event)
  const config = useRuntimeConfig()
  const backendBase = config.apiBaseUrlServer || config.public.apiBaseUrl || 'https://dental-api-2z19.onrender.com'
  const authHeader = getHeader(event, 'authorization') || ''

  try {
    const res = await $fetch(`${backendBase}/api/v1/social_automation/insights`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(authHeader ? { Authorization: authHeader } : {})
      },
      body
    })

    return {
      success: true,
      message: 'Insights synced successfully',
      data: res
    }
  } catch (err: any) {
    console.warn('Insights webhook edge reception fallback:', err?.message)
    return {
      success: true,
      message: 'Insights payload received (edge mode)',
      received: body,
      error: err?.data?.detail || err?.message
    }
  }
})
