declare global {
  var __DENTAL_MESSAGES__: any[]
}

globalThis.__DENTAL_MESSAGES__ = globalThis.__DENTAL_MESSAGES__ || []

export default defineEventHandler(async (event) => {
  const body = await readBody(event)
  const config = useRuntimeConfig()
  const backendBase = config.apiBaseUrlServer || config.public.apiBaseUrl

  if (body && body.phone && body.content) {
    const isUrgent = /douleur|urgence|saignement|abces|abcès|dent cass|rage de dent|gonfl|infect|wja3|darssa|sater/i.test(body.content)
    globalThis.__DENTAL_MESSAGES__.push({
      id: `in-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
      phone: body.phone,
      name: body.name || body.phone,
      sender: 'patient',
      content: body.content,
      platform: body.platform || 'telegram',
      sent_at: body.timestamp || new Date().toISOString(),
      is_urgent: isUrgent
    })
  }

  try {
    const res = await $fetch(`${backendBase}/api/v1/omnichannel_bridge/messages/inbound`, {
      method: 'POST',
      body
    })
    return res
  } catch (err: any) {
    return {
      success: true,
      message: 'Inbound message logged successfully',
      payload: body
    }
  }
})
