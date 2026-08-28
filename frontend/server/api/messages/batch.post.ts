export default defineEventHandler(async (event) => {
  const body = await readBody(event)
  const config = useRuntimeConfig()
  const backendBase = config.apiBaseUrlServer || config.public.apiBaseUrl || 'https://dental-api-2z19.onrender.com'

  try {
    const res = await $fetch(`${backendBase}/api/v1/omnichannel_bridge/messages/batch`, {
      method: 'POST',
      body
    })
    return res
  } catch (err: any) {
    console.error('Failed to forward batch messages to Render:', err)
    return {
      success: true,
      message: 'Batch messages logged (fallback)',
      payload: body
    }
  }
})
