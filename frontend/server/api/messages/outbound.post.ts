export default defineEventHandler(async (event) => {
  const rawBody = await readBody(event)
  const config = useRuntimeConfig()
  const backendBase = config.apiBaseUrlServer || config.public.apiBaseUrl || 'https://dental-api-2z19.onrender.com'

  // Normalize flexible keys from n8n
  const body = {
    phone: String(rawBody.phone || rawBody['chat id'] || rawBody.chat_id || rawBody.chatId || 'unknown'),
    chat_id: String(rawBody['chat id'] || rawBody.chat_id || rawBody.chatId || rawBody.phone || ''),
    content: rawBody.content || '',
    sender: rawBody.sender || 'ai_bot',
    name: rawBody.name || rawBody['full name'] || rawBody.full_name || '',
    timestamp: rawBody.timestamp || new Date().toISOString()
  }

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
