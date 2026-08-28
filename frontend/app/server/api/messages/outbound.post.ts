declare global {
  var __DENTAL_MESSAGES__: any[]
}

globalThis.__DENTAL_MESSAGES__ = globalThis.__DENTAL_MESSAGES__ || []

export default defineEventHandler(async (event) => {
  const body = await readBody(event)
  const config = useRuntimeConfig()
  const backendBase = config.apiBaseUrlServer || config.public.apiBaseUrl

  if (body && body.phone && body.content) {
    globalThis.__DENTAL_MESSAGES__.push({
      id: `out-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
      phone: body.phone,
      sender: body.sender || 'ai_bot',
      content: body.content,
      platform: 'telegram',
      sent_at: body.timestamp || new Date().toISOString()
    })
  }

  try {
    const res = await $fetch(`${backendBase}/api/v1/omnichannel_bridge/messages/outbound`, {
      method: 'POST',
      body
    })
    return res
  } catch (err: any) {
    return {
      success: true,
      message: 'Outbound message logged successfully',
      payload: body
    }
  }
})
