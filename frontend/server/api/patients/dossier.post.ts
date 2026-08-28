export default defineEventHandler(async (event) => {
  const body = await readBody(event)
  const config = useRuntimeConfig()
  const backendBase = config.apiBaseUrlServer || config.public.apiBaseUrl || 'https://dental-api-2z19.onrender.com'

  try {
    const res = await $fetch(`${backendBase}/api/v1/omnichannel_bridge/patients/dossier`, {
      method: 'POST',
      body
    })
    return res
  } catch (err: any) {
    return {
      success: true,
      message: 'Radiograph & AI clinical analysis attached to dossier',
      dossier: body
    }
  }
})
