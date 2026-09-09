import type { ApiResponse } from '~~/app/types'

export interface PrescriptionItem {
  id?: string
  medication_name: string
  dosage?: string | null
  form?: string | null
  frequency?: string | null
  duration?: string | null
  instructions?: string | null
  order?: number
}

export interface Prescription {
  id: string
  clinic_id: string
  patient_id: string
  doctor_name_fr: string
  doctor_specialty_fr: string
  doctor_name_ar: string
  doctor_specialty_ar: string
  city: string
  prescription_date: string
  notes?: string | null
  is_active: boolean
  created_at: string
  updated_at: string
  items: PrescriptionItem[]
}

export interface PrescriptionCreatePayload {
  patient_id: string
  doctor_name_fr?: string
  doctor_specialty_fr?: string
  doctor_name_ar?: string
  doctor_specialty_ar?: string
  city?: string
  prescription_date?: string
  notes?: string | null
  items: PrescriptionItem[]
}

export function usePrescriptions() {
  const api = useApi()
  const toast = useToast()
  const { t } = useI18n()

  const isLoading = ref(false)

  async function getPatientPrescriptions(patientId: string): Promise<Prescription[]> {
    isLoading.value = true
    try {
      const res = await api.get<ApiResponse<Prescription[]>>(`/api/v1/prescriptions/patient/${patientId}`)
      return res.data || []
    } catch (e) {
      console.error('Failed to fetch patient prescriptions:', e)
      return []
    } finally {
      isLoading.value = false
    }
  }

  async function getPrescription(id: string): Promise<Prescription | null> {
    isLoading.value = true
    try {
      const res = await api.get<ApiResponse<Prescription>>(`/api/v1/prescriptions/${id}`)
      return res.data || null
    } catch (e) {
      console.error('Failed to fetch prescription:', e)
      return null
    } finally {
      isLoading.value = false
    }
  }

  async function createPrescription(payload: PrescriptionCreatePayload): Promise<Prescription | null> {
    isLoading.value = true
    try {
      const res = await api.post<ApiResponse<Prescription>>('/api/v1/prescriptions', payload)
      toast.add({
        title: t('common.success', 'Succès'),
        description: t('prescriptions.createdSuccess', 'Ordonnance enregistrée avec succès'),
        color: 'success'
      })
      return res.data
    } catch (e) {
      console.error('Failed to create prescription:', e)
      toast.add({
        title: t('common.error', 'Erreur'),
        description: t('prescriptions.createError', "Échec de l'enregistrement de l'ordonnance"),
        color: 'error'
      })
      return null
    } finally {
      isLoading.value = false
    }
  }

  async function updatePrescription(id: string, payload: Partial<PrescriptionCreatePayload>): Promise<Prescription | null> {
    isLoading.value = true
    try {
      const res = await api.put<ApiResponse<Prescription>>(`/api/v1/prescriptions/${id}`, payload)
      toast.add({
        title: t('common.success', 'Succès'),
        description: t('prescriptions.updatedSuccess', 'Ordonnance mise à jour avec succès'),
        color: 'success'
      })
      return res.data
    } catch (e) {
      console.error('Failed to update prescription:', e)
      toast.add({
        title: t('common.error', 'Erreur'),
        description: t('prescriptions.updateError', 'Échec de la mise à jour'),
        color: 'error'
      })
      return null
    } finally {
      isLoading.value = false
    }
  }

  async function deletePrescription(id: string): Promise<boolean> {
    isLoading.value = true
    try {
      await api.del(`/api/v1/prescriptions/${id}`)
      toast.add({
        title: t('common.success', 'Succès'),
        description: t('prescriptions.deletedSuccess', 'Ordonnance supprimée'),
        color: 'success'
      })
      return true
    } catch (e) {
      console.error('Failed to delete prescription:', e)
      toast.add({
        title: t('common.error', 'Erreur'),
        description: t('prescriptions.deleteError', 'Échec de la suppression'),
        color: 'error'
      })
      return false
    } finally {
      isLoading.value = false
    }
  }

  return {
    isLoading,
    getPatientPrescriptions,
    getPrescription,
    createPrescription,
    updatePrescription,
    deletePrescription
  }
}
