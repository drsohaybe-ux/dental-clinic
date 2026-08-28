export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()
  const backendBase = config.apiBaseUrlServer || config.public.apiBaseUrl || 'https://dental-api-2z19.onrender.com'

  try {
    const res = await $fetch<any[]>(`${backendBase}/api/v1/omnichannel_bridge/conversations`)
    if (Array.isArray(res)) {
      return res
    }
  } catch (err: any) {
    console.error('Error fetching conversations from Render:', err)
  }

  return []
})
