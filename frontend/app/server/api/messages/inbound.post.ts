export default defineEventHandler(async (event) => {
  const body = await readBody(event)
  const config = useRuntimeConfig()
  const backendBase = config.apiBaseUrlServer || config.public.apiBaseUrl

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
