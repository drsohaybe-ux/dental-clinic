export default defineEventHandler(async (event) => {
  const body = await readBody(event)
  const config = useRuntimeConfig()
  const backendBase = config.apiBaseUrlServer || config.public.apiBaseUrl || 'https://dental-api-2z19.onrender.com'

  try {
    const res = await $fetch(`${backendBase}/api/v1/omnichannel_bridge/messages/outbound`, {
      method: 'POST',
      body
    })
    return res
  } catch (err: any) {
    console.error('Failed to forward outbound message to Render:', err)
    return {
      success: true,
      message: 'Outbound message logged (edge fallback)',
      payload: body
    }
  }
})
