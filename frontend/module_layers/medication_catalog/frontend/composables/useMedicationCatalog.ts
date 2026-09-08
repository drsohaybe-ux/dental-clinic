export type MedicationForm
  = | 'tablet'
    | 'capsule'
    | 'syrup'
    | 'suspension'
    | 'injection'
    | 'topical'
    | 'drops'
    | 'spray'
    | 'mouthwash'
    | 'gel'
    | 'cream'
    | 'paste'
    | 'varnish'
    | 'other'

export interface MedicationCatalogItem {
  id: string
  clinic_id: string
  name: string
  dose?: string | null
  unit?: string | null
  form: MedicationForm
  requires_prescription: boolean
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface MedicationCreatePayload {
  name: string
  dose?: string | null
  unit?: string | null
  form: MedicationForm
  requires_prescription?: boolean
  is_active?: boolean
}

export type MedicationUpdatePayload = Partial<MedicationCreatePayload>

export interface AlgerianMedication {
  id: string
  code?: string | null
  registration_number?: string | null
  brand_name: string
  dci: string
  form?: string | null
  standard_form: MedicationForm
  dosage?: string | null
  dose?: string | null
  unit?: string | null
  packaging?: string | null
  laboratory?: string | null
  country?: string | null
  price?: string | null
  reimbursement?: string | null
  is_dental: boolean
  requires_prescription: boolean
  is_active: boolean
}

export interface QuickAddMedicationPayload {
  name: string
  dose?: string | null
  unit?: string | null
  form?: MedicationForm
  requires_prescription?: boolean
  is_active?: boolean
}

interface ApiOk<T> { data: T, message?: string | null }
interface ApiPaged<T> { data: T[], total: number, page: number, page_size: number }

export interface MedicationListFilters {
  q?: string
  form?: MedicationForm
  is_active?: boolean
  page?: number
  page_size?: number
}

export function useMedicationCatalog() {
  const api = useApi()

  async function list(filters: MedicationListFilters = {}): Promise<ApiPaged<MedicationCatalogItem>> {
    const qs = new URLSearchParams()
    for (const [k, v] of Object.entries(filters)) {
      if (v === undefined || v === null || v === '') continue
      qs.append(k, String(v))
    }
    const url = `/api/v1/medication_catalog/${qs.toString() ? `?${qs.toString()}` : ''}`
    return await api.get<ApiPaged<MedicationCatalogItem>>(url)
  }

  async function create(payload: MedicationCreatePayload): Promise<ApiOk<MedicationCatalogItem>> {
    return await api.post<ApiOk<MedicationCatalogItem>>('/api/v1/medication_catalog/', payload)
  }

  async function update(id: string, payload: MedicationUpdatePayload): Promise<ApiOk<MedicationCatalogItem>> {
    return await api.patch<ApiOk<MedicationCatalogItem>>(`/api/v1/medication_catalog/${id}`, payload)
  }

  async function remove(id: string): Promise<void> {
    await api.del(`/api/v1/medication_catalog/${id}`)
  }

  async function seed(): Promise<ApiOk<{ created: number, skipped: number }>> {
    return await api.post('/api/v1/medication_catalog/seed', {})
  }

  async function searchNomenclature(
    query?: string,
    isDental?: boolean,
    limit = 30
  ): Promise<AlgerianMedication[]> {
    try {
      const qs = new URLSearchParams()
      if (query) qs.set('q', query)
      if (isDental !== undefined) qs.set('is_dental', String(isDental))
      if (limit) qs.set('limit', String(limit))
      const suffix = qs.toString() ? `?${qs.toString()}` : ''
      const res = await api.get<ApiOk<AlgerianMedication[]>>(
        `/api/v1/medication_catalog/nomenclature${suffix}`
      )
      return res.data || []
    } catch (e) {
      console.error('Failed to search Algerian nomenclature:', e)
      return []
    }
  }

  async function quickAdd(payload: QuickAddMedicationPayload): Promise<ApiOk<MedicationCatalogItem>> {
    return await api.post<ApiOk<MedicationCatalogItem>>('/api/v1/medication_catalog/quick-add', payload)
  }

  async function seedNomenclature(force = false): Promise<ApiOk<{ seeded: number, total: number }>> {
    return await api.post(`/api/v1/medication_catalog/nomenclature/seed${force ? '?force=true' : ''}`, {})
  }

  return {
    list,
    create,
    update,
    remove,
    seed,
    searchNomenclature,
    quickAdd,
    seedNomenclature
  }
}
