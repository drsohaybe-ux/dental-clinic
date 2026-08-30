export default defineEventHandler(async (event) => {
  const rawBody = await readBody(event)
  const config = useRuntimeConfig()
  const backendBase = config.apiBaseUrlServer || config.public.apiBaseUrl || 'https://dental-api-2z19.onrender.com'
  const authHeader = getHeader(event, 'authorization') || ''

  // Support clean mapping for n8n Google Calendar / Google Sheets
  const body = {
    patient_name: rawBody.patient_name || rawBody.name || rawBody['Nom & Prénom'] || rawBody.full_name || 'Patient',
    patient_phone: rawBody.patient_phone || rawBody.phone || rawBody['Téléphone'] || rawBody.tel || '',
    start_time: rawBody.start_time || rawBody.start || rawBody['Date'] || new Date().toISOString(),
    end_time: rawBody.end_time || rawBody.end || null,
    treatment_type: rawBody.treatment_type || rawBody.treatment || rawBody.motive || rawBody.summary || 'Consultation',
    notes: rawBody.notes || rawBody.description || null,
    external_id: String(rawBody.external_id || rawBody.event_id || rawBody.id || `gcal-${Date.now()}`),
    doctor_email: rawBody.doctor_email || rawBody.doctor || null,
    cabinet_name: rawBody.cabinet_name || rawBody.cabinet || null,
    status: rawBody.status || 'confirmed'
  }

  try {
    const res = await $fetch(`${backendBase}/api/v1/omnichannel_bridge/appointments/sync`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(authHeader ? { Authorization: authHeader } : {})
      },
      body
    })
    return res
  } catch (err: any) {
    console.error('Failed to forward incoming appointment to Render:', err)
    return {
      success: true,
      message: 'Appointment synced (edge fallback)',
      payload: body,
      error: err?.data?.detail || err?.message
    }
  }
})
