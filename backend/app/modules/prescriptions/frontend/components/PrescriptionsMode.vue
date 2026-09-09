<script setup lang="ts">
/**
 * PrescriptionsMode — Full-width Clinical Workspace for Medical Prescriptions (Ordonnances).
 *
 * Dedicated clinical sub-tab between Treatment Plans and Appointments.
 * Full page width, natural dimensions, zero overlapping elements.
 *
 * Workspace features:
 * - Master/list of past ordonnances for this patient (dates, doctor, medications count, "+ Nouvelle Ordonnance").
 * - Detail / Composer: Full-sized Algerian drug auto-complete (brand name, DCI, auto-fill dosage, form,
 *   clinical frequency dropdown presets, duration, notes).
 * - Live authentic Algerian prescription pad preview (A4/A5 toggle, print button, bilingual French/Arabic
 *   clinic headers, tooth watermark, doctor stamp/signature box).
 */
import type { PatientExtended, ApiResponse } from '~~/app/types'
import type { Prescription, PrescriptionItem } from '../composables/usePrescriptions'
import { usePrescriptions } from '../composables/usePrescriptions'

interface NomenclatureItem {
  id: string
  brand_name: string
  dci: string
  dosage?: string | null
  dose?: string | null
  unit?: string | null
  standard_form: string
  is_dental: boolean
  requires_prescription: boolean
}

interface Props {
  patientId: string
  patient?: PatientExtended
  initialRxId?: string | null
  initialAction?: string | null
  readonly?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  patient: undefined,
  initialRxId: null,
  initialAction: null,
  readonly: false
})

const emit = defineEmits<{
  'prescription-saved': [prescription: Prescription]
  'prescription-deleted': [id: string]
}>()

const api = useApi()
const { t, locale } = useI18n()
const { user } = useAuth()
const { currentClinic } = useClinic()
const router = useRouter()
const route = useRoute()
const toast = useToast()
const {
  getPatientPrescriptions,
  createPrescription,
  updatePrescription,
  deletePrescription
} = usePrescriptions()

// ============================================================================
// State
// ============================================================================

const patientData = ref<PatientExtended | null>(props.patient ?? null)
const prescriptions = ref<Prescription[]>([])
const selectedRxId = ref<string | null>(null)
const isLoadingList = ref(false)
const isSaving = ref(false)
const isDeleting = ref(false)

// Active view in detail pane: 'editor' (Composer form) or 'preview' (Algerian Pad Preview)
const activeView = ref<'editor' | 'preview'>('preview')
const paperSize = ref<'a5' | 'a4'>('a5')
const searchFilter = ref('')
const isDoctorHeaderOpen = ref(false)

// Delete confirm dialog
const showDeleteConfirm = ref(false)
const rxToDelete = ref<Prescription | null>(null)

// Storage key for persisting doctor header
const STORAGE_KEY = 'dentalpin:ordonnance_header'

function getDefaultDoctorNameFr(): string {
  if (user.value?.first_name || user.value?.last_name) {
    return `Dr. ${user.value.first_name || ''} ${user.value.last_name || ''}`.trim()
  }
  return 'Dr. Chirurgien Dentiste'
}

function getDefaultCity(): string {
  if (currentClinic.value?.address && typeof currentClinic.value.address === 'object') {
    const c = currentClinic.value.address.city
    if (c) return c
  }
  return 'Alger'
}

// Doctor & Clinic Header fields
const doctorNameFr = ref(getDefaultDoctorNameFr())
const doctorSpecialtyFr = ref('Chirurgien Dentiste')
const doctorNameAr = ref('الدكتور جراح أسنان')
const doctorSpecialtyAr = ref('جراح أسنان')
const city = ref(getDefaultCity())
const prescriptionDate = ref(new Date().toISOString().split('T')[0] ?? '')
const notes = ref('')

// Prescribed medications list
const items = ref<PrescriptionItem[]>([])

// Medication builder
const newItem = ref<PrescriptionItem>({
  medication_name: '',
  dosage: '',
  form: '',
  frequency: '',
  duration: '',
  instructions: '',
  order: 1
})

// Drug search autocomplete
const drugSearchQuery = ref('')
const drugSuggestions = ref<Array<{ label: string, name: string, dosage?: string, form?: string, dci?: string, is_dental?: boolean }>>([])
const isSearchingDrugs = ref(false)

// Presets
const frequencyPresets = [
  '1 comp 2x/jour (Matin / Soir)',
  '1 comp 3x/jour (Toutes les 8h)',
  '1 comp 1x/jour (Le matin)',
  '1 comp 1x/jour (Le soir)',
  '1 sachet en cas de douleur',
  '1 comp si douleur (max 3/j)',
  'Bain de bouche 3x/jour après les repas',
  'Application locale 2x/jour',
  '1 gélule 3x/jour avant les repas',
  '2 comp en prise unique'
]

const durationPresets = [
  '3 jours',
  '5 jours',
  '6 jours',
  '7 jours',
  '8 jours',
  '10 jours',
  '15 jours',
  '1 mois',
  'En cas de douleur'
]

const instructionPresets = [
  'Au milieu des repas',
  'Après les repas',
  'À jeun le matin',
  'Après brossage des dents',
  'Ne pas avaler (recracher après 1 minute)',
  'Avec un grand verre d\'eau'
]

const frequencyDropdownItems = computed(() => [
  frequencyPresets.map(preset => ({
    label: preset,
    onSelect: () => { newItem.value.frequency = preset }
  }))
])

const durationDropdownItems = computed(() => [
  durationPresets.map(d => ({
    label: d,
    onSelect: () => { newItem.value.duration = d }
  }))
])

const instructionDropdownItems = computed(() => [
  instructionPresets.map(ins => ({
    label: ins,
    onSelect: () => { newItem.value.instructions = ins }
  }))
])

// ============================================================================
// Computed properties
// ============================================================================

const filteredPrescriptions = computed(() => {
  if (!searchFilter.value.trim()) return prescriptions.value
  const q = searchFilter.value.toLowerCase().trim()
  return prescriptions.value.filter((rx) => {
    const doctorMatch = rx.doctor_name_fr?.toLowerCase().includes(q) || rx.doctor_name_ar?.includes(q)
    const dateMatch = rx.prescription_date?.includes(q)
    const drugMatch = rx.items?.some(it => it.medication_name.toLowerCase().includes(q))
    return doctorMatch || dateMatch || drugMatch
  })
})

const isEditingExisting = computed(() => !!selectedRxId.value)

const patientAge = computed(() => {
  if (!patientData.value?.date_of_birth) return '—'
  const today = new Date()
  const birth = new Date(patientData.value.date_of_birth)
  let years = today.getFullYear() - birth.getFullYear()
  const m = today.getMonth() - birth.getMonth()
  if (m < 0 || (m === 0 && today.getDate() < birth.getDate())) years--
  return years >= 0 ? years : '—'
})

const formattedDate = computed(() => {
  if (!prescriptionDate.value) return ''
  const parts = prescriptionDate.value.split('-')
  if (parts.length === 3) {
    return `${parts[2]}/${parts[1]}/${parts[0]}`
  }
  return prescriptionDate.value
})

const clinicAddress = computed(() => {
  if (!currentClinic.value?.address) {
    return 'Cité 351 Logts. Bt.25 N° 01 commune de boumerdès, W. BOUMERDES'
  }
  const a = currentClinic.value.address
  const parts = [a.street, a.city, a.province].filter(Boolean)
  return parts.length > 0 ? parts.join(', ') : 'Boumerdès Centre, Algérie'
})

const clinicPhone = computed(() => currentClinic.value?.phone || '024 79 50 12 / 0550 44 73 55')
const clinicEmail = computed(() => currentClinic.value?.email || 'contact@ismile-clinic.dz')

// ============================================================================
// Storage & Population
// ============================================================================

function loadSavedDoctorHeader() {
  if (import.meta.client) {
    try {
      const raw = localStorage.getItem(STORAGE_KEY)
      if (raw) {
        const parsed = JSON.parse(raw)
        if (parsed.doctorNameFr) doctorNameFr.value = parsed.doctorNameFr
        if (parsed.doctorSpecialtyFr) doctorSpecialtyFr.value = parsed.doctorSpecialtyFr
        if (parsed.doctorNameAr) doctorNameAr.value = parsed.doctorNameAr
        if (parsed.doctorSpecialtyAr) doctorSpecialtyAr.value = parsed.doctorSpecialtyAr
        if (parsed.city) city.value = parsed.city
        return
      }
    } catch {
      // Ignore
    }
  }
  doctorNameFr.value = getDefaultDoctorNameFr()
  doctorSpecialtyFr.value = 'Chirurgien Dentiste'
  doctorNameAr.value = 'الدكتور جراح أسنان'
  doctorSpecialtyAr.value = 'جراح أسنان'
  city.value = getDefaultCity()
}

function saveDoctorHeaderToStorage() {
  if (import.meta.client) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({
        doctorNameFr: doctorNameFr.value,
        doctorSpecialtyFr: doctorSpecialtyFr.value,
        doctorNameAr: doctorNameAr.value,
        doctorSpecialtyAr: doctorSpecialtyAr.value,
        city: city.value
      }))
    } catch {
      // Ignore
    }
  }
}

function populateFormFromRx(rx: Prescription) {
  doctorNameFr.value = rx.doctor_name_fr || getDefaultDoctorNameFr()
  doctorSpecialtyFr.value = rx.doctor_specialty_fr || 'Chirurgien Dentiste'
  doctorNameAr.value = rx.doctor_name_ar || 'الدكتور جراح أسنان'
  doctorSpecialtyAr.value = rx.doctor_specialty_ar || 'جراح أسنان'
  city.value = rx.city || getDefaultCity()
  prescriptionDate.value = rx.prescription_date || new Date().toISOString().split('T')[0]
  notes.value = rx.notes || ''
  items.value = rx.items && rx.items.length > 0 ? rx.items.map((it, idx) => ({ ...it, order: idx + 1 })) : []
}

function resetFormToNew() {
  loadSavedDoctorHeader()
  prescriptionDate.value = new Date().toISOString().split('T')[0] ?? ''
  notes.value = ''
  items.value = []
  newItem.value = {
    medication_name: '',
    dosage: '',
    form: '',
    frequency: '',
    duration: '',
    instructions: '',
    order: 1
  }
  selectedRxId.value = null
  activeView.value = 'editor'
}

// ============================================================================
// Actions & Handlers
// ============================================================================

async function fetchPatientData() {
  if (patientData.value?.id) return
  try {
    const res = await api.get<ApiResponse<PatientExtended>>(`/api/v1/patients/${props.patientId}/extended`)
    if (res.data) {
      patientData.value = res.data
    }
  } catch (err) {
    console.error('Failed to load patient details for prescriptions:', err)
  }
}

async function loadPrescriptionsList() {
  isLoadingList.value = true
  try {
    const list = await getPatientPrescriptions(props.patientId)
    prescriptions.value = list

    // Check if initial rxId is requested
    if (props.initialRxId) {
      const match = list.find(rx => rx.id === props.initialRxId)
      if (match) {
        selectPrescription(match, 'preview')
        return
      }
    }

    // Check if initial action is new
    if (props.initialAction === 'new' || list.length === 0) {
      resetFormToNew()
      return
    }

    // Otherwise select latest prescription in preview mode
    if (list.length > 0 && !selectedRxId.value) {
      selectPrescription(list[0], 'preview')
    }
  } finally {
    isLoadingList.value = false
  }
}

function selectPrescription(rx: Prescription, viewMode: 'editor' | 'preview' = 'preview') {
  selectedRxId.value = rx.id
  populateFormFromRx(rx)
  activeView.value = viewMode

  // Update URL query without refresh
  router.replace({
    query: {
      ...route.query,
      clinicalMode: 'prescriptions',
      rxId: rx.id,
      action: undefined
    }
  })
}

function handleNewPrescription() {
  resetFormToNew()
  router.replace({
    query: {
      ...route.query,
      clinicalMode: 'prescriptions',
      action: 'new',
      rxId: undefined
    }
  })
}

// Drug autocomplete debounced search
let searchTimer: ReturnType<typeof setTimeout> | undefined
watch(drugSearchQuery, (term) => {
  clearTimeout(searchTimer)
  if (!term || term.trim().length < 2) {
    drugSuggestions.value = []
    return
  }

  searchTimer = setTimeout(async () => {
    isSearchingDrugs.value = true
    try {
      const res = await api.get<ApiResponse<NomenclatureItem[]>>(
        `/api/v1/medication_catalog/nomenclature?q=${encodeURIComponent(term.trim())}&limit=20`
      )
      const list = res.data || []
      drugSuggestions.value = list.map(n => ({
        label: n.dosage ? `${n.brand_name} ${n.dosage} (${n.standard_form})` : `${n.brand_name} (${n.standard_form})`,
        name: n.brand_name,
        dosage: n.dosage || (n.dose && n.unit ? `${n.dose}${n.unit}` : n.dose) || '',
        form: n.standard_form === 'tablet' ? 'Comprimé' : n.standard_form === 'capsule' ? 'Gélule' : n.standard_form === 'syrup' ? 'Sirop' : n.standard_form === 'mouthwash' ? 'Bain de bouche' : n.standard_form,
        dci: n.dci,
        is_dental: n.is_dental
      }))
    } catch {
      drugSuggestions.value = []
    } finally {
      isSearchingDrugs.value = false
    }
  }, 200)
})

function selectDrugSuggestion(sug: { name: string, dosage?: string, form?: string }) {
  newItem.value.medication_name = sug.name
  if (sug.dosage) newItem.value.dosage = sug.dosage
  if (sug.form) newItem.value.form = sug.form
  drugSearchQuery.value = ''
  drugSuggestions.value = []
}

function addItemToPrescription() {
  if (!newItem.value.medication_name.trim()) return

  // Auto-extract dosage if present in name
  let name = newItem.value.medication_name.trim()
  let dosage = newItem.value.dosage?.trim() || ''

  if (!dosage) {
    const match = name.match(/\b(\d+(?:\.\d+)?\s*(?:mg|g|mcg|ml|iu|ui|%)(?:\/\d*(?:\.\d+)?\s*(?:mg|g|mcg|ml)?)?)\b/i)
    if (match) {
      dosage = match[1].trim()
      name = name.replace(match[1], '').replace(/\s{2,}/g, ' ').trim()
    }
  }

  items.value.push({
    medication_name: name,
    dosage: dosage || null,
    form: newItem.value.form?.trim() || null,
    frequency: newItem.value.frequency?.trim() || null,
    duration: newItem.value.duration?.trim() || null,
    instructions: newItem.value.instructions?.trim() || null,
    order: items.value.length + 1
  })

  // Reset builder
  newItem.value = {
    medication_name: '',
    dosage: '',
    form: '',
    frequency: '',
    duration: '',
    instructions: '',
    order: items.value.length + 1
  }
}

function removeItem(idx: number) {
  items.value.splice(idx, 1)
  items.value.forEach((it, i) => {
    it.order = i + 1
  })
}

function moveItem(idx: number, direction: 'up' | 'down') {
  if (direction === 'up' && idx > 0) {
    const temp = items.value[idx]
    items.value[idx] = items.value[idx - 1]
    items.value[idx - 1] = temp
  } else if (direction === 'down' && idx < items.value.length - 1) {
    const temp = items.value[idx]
    items.value[idx] = items.value[idx + 1]
    items.value[idx + 1] = temp
  }
  items.value.forEach((it, i) => {
    it.order = i + 1
  })
}

function printOrdonnance() {
  saveDoctorHeaderToStorage()
  const previousView = activeView.value
  activeView.value = 'preview'

  nextTick(() => {
    if (typeof document !== 'undefined') {
      document.body.classList.add('printing-ordonnance')
      const cleanup = () => {
        document.body.classList.remove('printing-ordonnance')
        window.removeEventListener('afterprint', cleanup)
      }
      window.addEventListener('afterprint', cleanup, { once: true })
      window.print()
      setTimeout(() => {
        document.body.classList.remove('printing-ordonnance')
        activeView.value = previousView
      }, 800)
    }
  })
}

async function handleSave() {
  if (items.value.length === 0) {
    toast.add({
      title: t('prescriptions.noItemsError', 'Médicaments requis'),
      description: t('prescriptions.pleaseAddItems', 'Veuillez ajouter au moins un médicament à l\'ordonnance'),
      color: 'warning'
    })
    activeView.value = 'editor'
    return
  }

  isSaving.value = true
  saveDoctorHeaderToStorage()
  try {
    const payload = {
      patient_id: props.patientId,
      doctor_name_fr: doctorNameFr.value,
      doctor_specialty_fr: doctorSpecialtyFr.value,
      doctor_name_ar: doctorNameAr.value,
      doctor_specialty_ar: doctorSpecialtyAr.value,
      city: city.value,
      prescription_date: prescriptionDate.value,
      notes: notes.value || null,
      items: items.value.map((it, idx) => ({ ...it, order: idx + 1 }))
    }

    let result: Prescription | null = null
    if (selectedRxId.value) {
      result = await updatePrescription(selectedRxId.value, payload)
    } else {
      result = await createPrescription(payload)
    }

    if (result) {
      emit('prescription-saved', result)
      // Refresh summary card cache
      refreshNuxtData(`prescriptions:summary-card:${props.patientId}`)
      await loadPrescriptionsList()
      selectedRxId.value = result.id
      populateFormFromRx(result)
      activeView.value = 'preview'
    }
  } finally {
    isSaving.value = false
  }
}

function requestDelete(rx: Prescription) {
  rxToDelete.value = rx
  showDeleteConfirm.value = true
}

async function confirmDelete() {
  if (!rxToDelete.value) return
  isDeleting.value = true
  try {
    const success = await deletePrescription(rxToDelete.value.id)
    if (success) {
      emit('prescription-deleted', rxToDelete.value.id)
      refreshNuxtData(`prescriptions:summary-card:${props.patientId}`)
      showDeleteConfirm.value = false
      if (selectedRxId.value === rxToDelete.value.id) {
        selectedRxId.value = null
      }
      rxToDelete.value = null
      await loadPrescriptionsList()
    }
  } finally {
    isDeleting.value = false
  }
}

function formatDate(isoOrDate: string): string {
  if (!isoOrDate) return ''
  try {
    const d = new Date(isoOrDate)
    return new Intl.DateTimeFormat(locale.value, {
      day: '2-digit',
      month: 'short',
      year: 'numeric'
    }).format(d)
  } catch {
    return isoOrDate
  }
}

function formatMedicationSummary(rx: Prescription): string {
  if (!rx.items || rx.items.length === 0) return t('prescriptions.noItems', 'Sans médicaments')
  const names = rx.items.slice(0, 3).map(i => i.medication_name)
  if (rx.items.length > 3) {
    return `${names.join(', ')} (+${rx.items.length - 3})`
  }
  return names.join(', ')
}

// ============================================================================
// Lifecycle
// ============================================================================

onMounted(async () => {
  await Promise.all([
    fetchPatientData(),
    loadPrescriptionsList()
  ])
})

watch(() => props.patientId, async () => {
  patientData.value = props.patient ?? null
  selectedRxId.value = null
  await Promise.all([
    fetchPatientData(),
    loadPrescriptionsList()
  ])
})

watch(() => props.patient, (p) => {
  if (p) patientData.value = p
})
</script>

<template>
  <div class="prescriptions-workspace w-full space-y-6">
    <!-- Dynamic print page styling according to selected paperSize -->
    <component :is="'style'">
      @media print {
      @page {
      size: {{ paperSize === 'a5' ? 'A5 portrait' : 'A4 portrait' }};
      margin: {{ paperSize === 'a5' ? '6mm' : '10mm' }};
      }
      }
    </component>

    <!-- Main Workspace Grid: Master column (left) + Detail/Composer column (right) -->
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
      <!-- ============================================================= -->
      <!-- MASTER: Past Ordonnances List -->
      <!-- ============================================================= -->
      <div class="lg:col-span-4 xl:col-span-4 space-y-4">
        <div class="bg-surface border border-default rounded-xl p-4 shadow-xs space-y-4">
          <!-- Master Header -->
          <div class="flex items-center justify-between gap-2">
            <div class="flex items-center gap-2">
              <div class="p-1.5 rounded-lg bg-cyan-500/10 text-cyan-600 dark:text-cyan-400">
                <UIcon
                  name="i-lucide-receipt"
                  class="text-lg"
                />
              </div>
              <div>
                <h3 class="font-semibold text-sm text-default">
                  {{ t('prescriptions.cardTitle', 'Ordonnances') }}
                </h3>
                <p class="text-[11px] text-subtle">
                  {{ prescriptions.length }} {{ prescriptions.length > 1 ? t('prescriptions.pluralCount', 'ordonnances') : t('prescriptions.singularCount', 'ordonnance') }}
                </p>
              </div>
            </div>

            <!-- New prescription button -->
            <UButton
              v-if="!readonly"
              size="xs"
              color="primary"
              icon="i-lucide-plus"
              class="cursor-pointer font-medium"
              @click="handleNewPrescription"
            >
              {{ t('prescriptions.new', 'Nouvelle') }}
            </UButton>
          </div>

          <!-- Search Filter -->
          <div v-if="prescriptions.length > 0">
            <UInput
              v-model="searchFilter"
              icon="i-lucide-search"
              size="xs"
              :placeholder="t('common.search', 'Filtrer les ordonnances...')"
              class="w-full"
            />
          </div>

          <!-- Prescriptions Scrollable List -->
          <div class="space-y-2 max-h-[calc(100vh-280px)] overflow-y-auto pr-1">
            <div
              v-if="isLoadingList"
              class="py-8 text-center text-subtle text-xs flex items-center justify-center gap-2"
            >
              <UIcon
                name="i-lucide-loader-2"
                class="animate-spin text-base"
              />
              <span>{{ t('common.loading', 'Chargement des ordonnances...') }}</span>
            </div>

            <div
              v-else-if="filteredPrescriptions.length === 0"
              class="py-8 px-4 text-center text-caption text-muted border border-dashed border-default rounded-lg"
            >
              <UIcon
                name="i-lucide-file-text"
                class="text-3xl text-subtle mx-auto mb-2 opacity-50"
              />
              <p class="font-medium text-xs text-default">
                {{ t('prescriptions.empty', 'Aucune ordonnance émise') }}
              </p>
              <p class="text-[11px] text-subtle mt-0.5">
                {{ t('prescriptions.emptySubtitle', 'Rédigez la première ordonnance pour ce patient.') }}
              </p>
              <UButton
                v-if="!readonly"
                size="xs"
                variant="soft"
                color="primary"
                icon="i-lucide-plus"
                class="mt-3 cursor-pointer"
                @click="handleNewPrescription"
              >
                {{ t('prescriptions.newPrescription', 'Créer une ordonnance') }}
              </UButton>
            </div>

            <div
              v-for="rx in filteredPrescriptions"
              :key="rx.id"
              class="p-3 rounded-lg border transition-all cursor-pointer group"
              :class="selectedRxId === rx.id
                ? 'border-cyan-500 bg-cyan-50/50 dark:bg-cyan-950/20 shadow-xs'
                : 'border-default bg-surface hover:bg-surface-muted/50'"
              @click="selectPrescription(rx, 'preview')"
            >
              <div class="flex items-start justify-between gap-2">
                <div class="min-w-0 flex-1">
                  <div class="flex items-center gap-2">
                    <span class="font-semibold text-xs text-default">
                      {{ formatDate(rx.prescription_date || rx.created_at) }}
                    </span>
                    <UBadge
                      size="xs"
                      :color="selectedRxId === rx.id ? 'primary' : 'neutral'"
                      variant="subtle"
                    >
                      {{ rx.items?.length || 0 }} {{ (rx.items?.length || 0) > 1 ? 'médicaments' : 'médicament' }}
                    </UBadge>
                  </div>

                  <p class="text-xs font-medium text-neutral-800 dark:text-neutral-200 mt-1 truncate">
                    {{ formatMedicationSummary(rx) }}
                  </p>

                  <p
                    v-if="rx.doctor_name_fr"
                    class="text-[11px] text-subtle mt-0.5 truncate"
                  >
                    {{ rx.doctor_name_fr }}
                  </p>
                </div>

                <div class="flex items-center gap-1 opacity-80 group-hover:opacity-100 shrink-0">
                  <UButton
                    size="xs"
                    variant="ghost"
                    color="neutral"
                    icon="i-lucide-printer"
                    class="cursor-pointer"
                    :title="t('prescriptions.print', 'Imprimer')"
                    @click.stop="selectPrescription(rx, 'preview'); nextTick(() => printOrdonnance())"
                  />
                  <UButton
                    v-if="!readonly"
                    size="xs"
                    variant="ghost"
                    color="error"
                    icon="i-lucide-trash-2"
                    class="cursor-pointer"
                    :title="t('common.delete', 'Supprimer')"
                    @click.stop="requestDelete(rx)"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ============================================================= -->
      <!-- DETAIL / COMPOSER: Full-Sized Editor & Pad Preview -->
      <!-- ============================================================= -->
      <div class="lg:col-span-8 xl:col-span-8 space-y-4">
        <!-- Top Workspace Action Bar -->
        <div class="bg-surface border border-default rounded-xl p-4 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <!-- Title and patient info -->
          <div class="flex items-center gap-3">
            <div>
              <div class="flex items-center gap-2">
                <h2 class="text-base font-bold text-default">
                  {{ isEditingExisting ? `Ordonnance du ${formatDate(prescriptionDate)}` : t('prescriptions.newPrescription', 'Nouvelle Ordonnance') }}
                </h2>
                <UBadge
                  size="xs"
                  :color="isEditingExisting ? 'success' : 'primary'"
                  variant="subtle"
                >
                  {{ isEditingExisting ? 'Enregistrée' : 'Brouillon' }}
                </UBadge>
              </div>
              <p class="text-xs text-subtle mt-0.5">
                {{ patientData?.first_name }} {{ patientData?.last_name }} ({{ patientAge }} ans)
              </p>
            </div>
          </div>

          <!-- Controls: View Switch, Format, Print, Save -->
          <div class="flex items-center gap-2 flex-wrap">
            <!-- View switcher -->
            <div class="bg-surface-muted rounded-lg p-0.5 flex items-center text-xs">
              <button
                type="button"
                class="px-3 py-1.5 rounded-md font-medium transition cursor-pointer flex items-center gap-1.5"
                :class="activeView === 'editor' ? 'bg-surface shadow-xs text-cyan-600 dark:text-cyan-400 font-semibold' : 'text-subtle hover:text-default'"
                @click="activeView = 'editor'"
              >
                <UIcon
                  name="i-lucide-pencil"
                  class="text-xs"
                />
                <span>{{ t('prescriptions.viewEdit', 'Éditeur & Médicaments') }}</span>
              </button>
              <button
                type="button"
                class="px-3 py-1.5 rounded-md font-medium transition cursor-pointer flex items-center gap-1.5"
                :class="activeView === 'preview' ? 'bg-surface shadow-xs text-cyan-600 dark:text-cyan-400 font-semibold' : 'text-subtle hover:text-default'"
                @click="activeView = 'preview'"
              >
                <UIcon
                  name="i-lucide-file-text"
                  class="text-xs"
                />
                <span>{{ t('prescriptions.viewPad', 'Aperçu Ordonnance') }}</span>
              </button>
            </div>

            <!-- Format A5 / A4 select -->
            <USelect
              v-model="paperSize"
              :items="[
                { label: 'Format A5 (Carnet)', value: 'a5' },
                { label: 'Format A4 (Standard)', value: 'a4' }
              ]"
              value-key="value"
              label-key="label"
              size="sm"
              class="w-36"
            />

            <!-- Print Button -->
            <UButton
              icon="i-lucide-printer"
              color="primary"
              size="sm"
              class="font-medium cursor-pointer"
              @click="printOrdonnance"
            >
              {{ t('common.print', 'Imprimer') }}
            </UButton>

            <!-- Save Button -->
            <UButton
              v-if="!readonly"
              icon="i-lucide-save"
              variant="solid"
              color="primary"
              size="sm"
              :loading="isSaving"
              class="font-medium cursor-pointer"
              @click="handleSave"
            >
              {{ t('common.save', 'Enregistrer') }}
            </UButton>
          </div>
        </div>

        <!-- ============================================================= -->
        <!-- VIEW 1: AUTHENTIC ALGERIAN ORDONNANCE PAD (PREVIEW & PRINT) -->
        <!-- ============================================================= -->
        <div
          v-show="activeView === 'preview'"
          class="flex justify-center w-full"
        >
          <div
            id="ordonnance-printable-area"
            class="ordonnance-sheet bg-white text-neutral-900 mx-auto relative rounded-lg shadow-md border border-neutral-200/90 transition-all font-sans print:shadow-none print:border-none print:rounded-none print:w-full"
            :class="paperSize === 'a5' ? 'w-full max-w-[580px] min-h-[780px]' : 'w-full max-w-[780px] min-h-[1020px]'"
          >
            <!-- Faint Tooth Watermark in background -->
            <div class="absolute inset-0 flex items-center justify-center pointer-events-none overflow-hidden select-none">
              <img
                src="/logo.png?v=3"
                alt="I SmilE Watermark"
                class="w-72 h-72 object-contain opacity-[0.06] grayscale contrast-125"
              >
            </div>

            <!-- Content layer -->
            <div class="relative z-10 flex flex-col justify-between h-full p-6 sm:p-9">
              <!-- Top Section -->
              <div>
                <!-- Header: French doctor (Left), Cyan Logo (Center), Arabic doctor (Right) -->
                <div class="flex items-start justify-between border-b border-cyan-100 pb-3 gap-2">
                  <!-- Left: Doctor & Specialty in French -->
                  <div class="text-left space-y-0.5 flex-1 min-w-[140px]">
                    <div class="text-base sm:text-lg font-bold text-cyan-700 uppercase tracking-tight">
                      {{ doctorNameFr }}
                    </div>
                    <div class="text-xs sm:text-sm font-medium text-cyan-600">
                      {{ doctorSpecialtyFr }}
                    </div>
                  </div>

                  <!-- Center: Clinic logo & tooth branding -->
                  <div class="flex flex-col items-center px-3 shrink-0">
                    <img
                      src="/logo.png?v=3"
                      alt="I SmilE Logo"
                      class="h-11 w-11 sm:h-12 sm:w-12 object-contain"
                    >
                    <span class="font-pacifico text-cyan-600 text-sm mt-0.5 tracking-tight">
                      I SmilE
                    </span>
                    <span class="text-[10px] text-cyan-700/80 font-medium -mt-1">
                      Cabinet Dentaire
                    </span>
                  </div>

                  <!-- Right: Doctor & Specialty in Arabic -->
                  <div
                    class="text-right space-y-0.5 flex-1 min-w-[140px] font-['Cairo']"
                    dir="rtl"
                  >
                    <div class="text-base sm:text-lg font-bold text-cyan-700">
                      {{ doctorNameAr }}
                    </div>
                    <div class="text-xs sm:text-sm font-medium text-cyan-600 border-b border-cyan-500/50 pb-0.5 inline-block">
                      {{ doctorSpecialtyAr }}
                    </div>
                  </div>
                </div>

                <!-- Date & Patient line with authentic dotted fills -->
                <div class="mt-4 space-y-2 text-xs sm:text-sm">
                  <!-- Date on the right -->
                  <div class="text-right text-neutral-700 font-medium">
                    <span>{{ city }}, le: </span>
                    <span class="border-b border-dotted border-neutral-400 px-3 font-semibold text-neutral-900 tracking-wide">
                      {{ formattedDate }}
                    </span>
                  </div>

                  <!-- Patient demographics row -->
                  <div class="flex items-baseline justify-between border-b border-dotted border-neutral-300 pb-2 pt-1 font-medium flex-wrap gap-2">
                    <div>
                      <span class="text-neutral-500">Nom: </span>
                      <span class="font-bold text-neutral-900 uppercase tracking-wider pl-1">
                        {{ patientData?.last_name || '—' }}
                      </span>
                    </div>
                    <div>
                      <span class="text-neutral-500">Prénom: </span>
                      <span class="font-bold text-neutral-900 capitalize pl-1">
                        {{ patientData?.first_name || '—' }}
                      </span>
                    </div>
                    <div>
                      <span class="text-neutral-500">Âge: </span>
                      <span class="font-bold text-neutral-900 pl-1">
                        {{ patientAge }}
                      </span>
                      <span class="text-neutral-500"> ans</span>
                    </div>
                  </div>
                </div>

                <!-- Center Title: ORDONNANCE (bold, cyan, underlined, uppercase) -->
                <div class="my-5 text-center">
                  <span class="inline-block text-lg sm:text-xl font-extrabold tracking-widest text-cyan-700 uppercase border-b-2 border-cyan-600 pb-0.5">
                    ORDONNANCE
                  </span>
                </div>

                <!-- Prescribed Medications Body -->
                <div class="space-y-4 px-1 sm:px-3 py-1 min-h-[260px]">
                  <div
                    v-for="(item, idx) in items"
                    :key="idx"
                    class="ordonnance-med-item space-y-0.5"
                  >
                    <!-- Drug name, dosage and form -->
                    <div class="flex items-baseline gap-2">
                      <span class="font-bold text-cyan-800 text-sm sm:text-base">{{ idx + 1 }}-</span>
                      <span class="font-bold text-neutral-900 text-sm sm:text-base uppercase tracking-tight">
                        {{ item.medication_name }}
                      </span>
                      <span
                        v-if="item.dosage"
                        class="font-bold text-cyan-700 text-xs sm:text-sm"
                      >
                        {{ item.dosage }}
                      </span>
                      <span
                        v-if="item.form"
                        class="text-neutral-600 italic text-xs"
                      >
                        ({{ item.form }})
                      </span>
                    </div>

                    <!-- Posology & Duration -->
                    <div class="pl-5 text-xs sm:text-sm text-neutral-800 space-y-0.5">
                      <div v-if="item.frequency">
                        <span class="text-neutral-500">• Posologie: </span>
                        <span class="font-medium text-neutral-900">{{ item.frequency }}</span>
                        <span
                          v-if="item.duration"
                          class="font-semibold text-neutral-900"
                        > — pendant {{ item.duration }}</span>
                      </div>
                      <div
                        v-if="item.instructions"
                        class="text-neutral-600 italic text-xs"
                      >
                        <span>• Note: {{ item.instructions }}</span>
                      </div>
                    </div>
                  </div>

                  <!-- Empty state if no drugs yet -->
                  <div
                    v-if="items.length === 0"
                    class="no-print h-44 flex flex-col items-center justify-center text-subtle text-xs gap-2"
                  >
                    <p class="italic">
                      {{ t('prescriptions.noDrugsYet', 'Aucun médicament sur cette ordonnance.') }}
                    </p>
                    <UButton
                      size="xs"
                      variant="soft"
                      color="primary"
                      icon="i-lucide-pencil"
                      class="cursor-pointer"
                      @click="activeView = 'editor'"
                    >
                      {{ t('prescriptions.editOrdonnance', 'Rédiger dans l\'éditeur') }}
                    </UButton>
                  </div>
                </div>
              </div>

              <!-- Bottom Footer -->
              <div class="ordonnance-footer mt-8 pt-3 border-t border-cyan-100">
                <div class="flex items-end justify-between text-[11px] sm:text-xs text-cyan-900 gap-3">
                  <!-- Contact info -->
                  <div class="space-y-1 max-w-[65%]">
                    <div class="flex items-center gap-1.5 text-cyan-800">
                      <UIcon
                        name="i-lucide-map-pin"
                        class="text-cyan-600 shrink-0 text-xs"
                      />
                      <span class="truncate">{{ clinicAddress }}</span>
                    </div>
                    <div class="flex items-center gap-3 text-cyan-800 flex-wrap">
                      <span
                        v-if="clinicPhone"
                        class="flex items-center gap-1"
                      >
                        <UIcon
                          name="i-lucide-phone"
                          class="text-cyan-600 text-xs"
                        />
                        {{ clinicPhone }}
                      </span>
                      <span
                        v-if="clinicEmail"
                        class="flex items-center gap-1"
                      >
                        <UIcon
                          name="i-lucide-mail"
                          class="text-cyan-600 text-xs"
                        />
                        {{ clinicEmail }}
                      </span>
                    </div>
                  </div>

                  <!-- Doctor Stamp & Signature Box -->
                  <div class="text-center shrink-0">
                    <div class="text-[10px] uppercase font-semibold text-cyan-700 tracking-wider mb-1">
                      Signature & Cachet
                    </div>
                    <div class="w-32 h-16 sm:w-36 sm:h-20 border border-dashed border-cyan-300 rounded bg-cyan-50/20 flex items-center justify-center text-[10px] text-cyan-400 select-none" />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- ============================================================= -->
        <!-- VIEW 2: FULL PRESCRIPTION BUILDER & COMPOSER -->
        <!-- ============================================================= -->
        <div
          v-show="activeView === 'editor'"
          class="space-y-4"
        >
          <!-- Doctor & Clinic Settings (Collapsible Header) -->
          <div class="p-4 rounded-xl border border-default bg-surface space-y-3">
            <div
              class="flex items-center justify-between cursor-pointer select-none"
              @click="isDoctorHeaderOpen = !isDoctorHeaderOpen"
            >
              <h3 class="text-sm font-semibold text-default flex items-center gap-2">
                <UIcon
                  name="i-lucide-user-check"
                  class="text-primary"
                />
                {{ t('prescriptions.doctorHeader', 'En-tête du Médecin & Cabinet') }}
              </h3>
              <div class="flex items-center gap-2">
                <span class="text-xs text-subtle">
                  {{ doctorNameFr }} · {{ city }}
                </span>
                <UIcon
                  :name="isDoctorHeaderOpen ? 'i-lucide-chevron-up' : 'i-lucide-chevron-down'"
                  class="text-subtle text-xs"
                />
              </div>
            </div>

            <div
              v-show="isDoctorHeaderOpen"
              class="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2 border-t border-default/50"
            >
              <div class="space-y-1">
                <label class="text-xs font-medium text-subtle">
                  Nom du médecin (Français)
                </label>
                <UInput
                  v-model="doctorNameFr"
                  placeholder="Dr. LOKMANE R."
                />
              </div>

              <div class="space-y-1">
                <label class="text-xs font-medium text-subtle">
                  Spécialité (Français)
                </label>
                <UInput
                  v-model="doctorSpecialtyFr"
                  placeholder="Chirurgien Dentiste"
                />
              </div>

              <div class="space-y-1">
                <label class="text-xs font-medium text-subtle">
                  اسم الطبيب (بالعربية)
                </label>
                <UInput
                  v-model="doctorNameAr"
                  dir="rtl"
                  placeholder="الدكتور لقمان ر."
                />
              </div>

              <div class="space-y-1">
                <label class="text-xs font-medium text-subtle">
                  التخصص (بالعربية)
                </label>
                <UInput
                  v-model="doctorSpecialtyAr"
                  dir="rtl"
                  placeholder="جراح أسنان"
                />
              </div>

              <div class="space-y-1">
                <label class="text-xs font-medium text-subtle">
                  Ville / Commune
                </label>
                <UInput
                  v-model="city"
                  placeholder="Boumerdès"
                />
              </div>

              <div class="space-y-1">
                <label class="text-xs font-medium text-subtle">
                  Date de prescription
                </label>
                <UInput
                  v-model="prescriptionDate"
                  type="date"
                />
              </div>
            </div>
          </div>

          <!-- Add Medication Card with Algerian Drug Autocomplete & Presets -->
          <div class="p-4 rounded-xl border border-default bg-surface space-y-4">
            <h3 class="text-sm font-semibold text-default flex items-center gap-2">
              <UIcon
                name="i-lucide-pill"
                class="text-primary"
              />
              {{ t('prescriptions.addMedication', 'Ajouter un médicament') }}
            </h3>

            <!-- Search Algerian nomenclature -->
            <div class="space-y-1.5 relative">
              <label class="text-xs font-medium text-subtle block">
                Rechercher dans la nomenclature algérienne (DPMF) & catalogue clinique
              </label>
              <div class="relative">
                <UInput
                  v-model="drugSearchQuery"
                  icon="i-lucide-search"
                  :loading="isSearchingDrugs"
                  placeholder="Tapez le nom d'un médicament (ex: Amoclan, Augmentin, Doliprane, Eludril, Flagyl...)"
                  class="w-full"
                />

                <!-- Autocomplete suggestions dropdown -->
                <div
                  v-if="drugSuggestions.length > 0"
                  class="absolute left-0 right-0 top-full mt-1 bg-surface border border-default rounded-lg shadow-xl max-h-60 overflow-y-auto z-40 divide-y divide-default"
                >
                  <button
                    v-for="(sug, sIdx) in drugSuggestions"
                    :key="sIdx"
                    type="button"
                    class="w-full px-3 py-2 text-left hover:bg-surface-muted transition flex items-center justify-between gap-2 cursor-pointer"
                    @click="selectDrugSuggestion(sug)"
                  >
                    <div>
                      <div class="font-medium text-xs sm:text-sm text-default flex items-center gap-1.5">
                        <span>{{ sug.name }}</span>
                        <span
                          v-if="sug.dosage"
                          class="text-cyan-600 font-semibold"
                        >{{ sug.dosage }}</span>
                        <UBadge
                          v-if="sug.is_dental"
                          size="xs"
                          color="primary"
                          variant="subtle"
                        >
                          Dentaire
                        </UBadge>
                      </div>
                      <div
                        v-if="sug.dci"
                        class="text-[11px] text-subtle truncate"
                      >
                        {{ sug.dci }}
                      </div>
                    </div>
                    <span class="text-xs text-subtle shrink-0 font-medium">
                      {{ sug.form }}
                    </span>
                  </button>
                </div>
              </div>
            </div>

            <!-- Medication input fields -->
            <div class="grid grid-cols-1 sm:grid-cols-12 gap-3 items-end pt-1">
              <div class="sm:col-span-4 space-y-1">
                <label class="text-xs font-medium text-subtle">
                  Nom du médicament *
                </label>
                <UInput
                  v-model="newItem.medication_name"
                  placeholder="ex: AMOCLAN"
                />
              </div>

              <div class="sm:col-span-4 space-y-1">
                <label class="text-xs font-medium text-subtle">
                  Dosage
                </label>
                <UInput
                  v-model="newItem.dosage"
                  placeholder="ex: 1G/200MG, 500mg"
                />
              </div>

              <div class="sm:col-span-4 space-y-1">
                <label class="text-xs font-medium text-subtle">
                  Forme galénique
                </label>
                <UInput
                  v-model="newItem.form"
                  placeholder="ex: Comprimé, Gélule"
                />
              </div>

              <!-- Posology with presets -->
              <div class="sm:col-span-6 space-y-1">
                <div class="flex items-center justify-between">
                  <label class="text-xs font-medium text-subtle">
                    Posologie / Fréquence
                  </label>
                  <UDropdownMenu :items="frequencyDropdownItems">
                    <UButton
                      size="xs"
                      variant="ghost"
                      color="primary"
                      trailing-icon="i-lucide-chevron-down"
                      class="text-xs py-0 h-5 cursor-pointer"
                    >
                      Presets
                    </UButton>
                  </UDropdownMenu>
                </div>
                <UInput
                  v-model="newItem.frequency"
                  placeholder="ex: 1 comp 2x/jour (Matin / Soir)"
                />
              </div>

              <!-- Duration with presets -->
              <div class="sm:col-span-3 space-y-1">
                <div class="flex items-center justify-between">
                  <label class="text-xs font-medium text-subtle">
                    Durée
                  </label>
                  <UDropdownMenu :items="durationDropdownItems">
                    <UButton
                      size="xs"
                      variant="ghost"
                      color="primary"
                      trailing-icon="i-lucide-chevron-down"
                      class="text-xs py-0 h-5 cursor-pointer"
                    >
                      Presets
                    </UButton>
                  </UDropdownMenu>
                </div>
                <UInput
                  v-model="newItem.duration"
                  placeholder="ex: 7 jours"
                />
              </div>

              <!-- Instructions / Notes with presets -->
              <div class="sm:col-span-3 space-y-1">
                <div class="flex items-center justify-between">
                  <label class="text-xs font-medium text-subtle">
                    Instructions
                  </label>
                  <UDropdownMenu :items="instructionDropdownItems">
                    <UButton
                      size="xs"
                      variant="ghost"
                      color="primary"
                      trailing-icon="i-lucide-chevron-down"
                      class="text-xs py-0 h-5 cursor-pointer"
                    >
                      Presets
                    </UButton>
                  </UDropdownMenu>
                </div>
                <UInput
                  v-model="newItem.instructions"
                  placeholder="ex: Au milieu des repas"
                />
              </div>
            </div>

            <div class="flex justify-end pt-1">
              <UButton
                icon="i-lucide-plus"
                color="primary"
                :disabled="!newItem.medication_name.trim()"
                class="font-medium cursor-pointer"
                @click="addItemToPrescription"
              >
                {{ t('prescriptions.addToPad', 'Ajouter à l\'ordonnance') }}
              </UButton>
            </div>
          </div>

          <!-- Prescribed Medications List -->
          <div class="p-4 rounded-xl border border-default bg-surface space-y-3">
            <div class="flex items-center justify-between">
              <h3 class="text-sm font-semibold text-default flex items-center gap-2">
                <UIcon
                  name="i-lucide-list-ordered"
                  class="text-primary"
                />
                <span>Médicaments sur l'ordonnance ({{ items.length }})</span>
              </h3>
              <UButton
                size="xs"
                variant="soft"
                color="primary"
                icon="i-lucide-eye"
                class="cursor-pointer"
                @click="activeView = 'preview'"
              >
                {{ t('prescriptions.seePadResult', 'Voir l\'aperçu du carnet') }}
              </UButton>
            </div>

            <div
              v-if="items.length === 0"
              class="text-subtle text-xs py-6 text-center border border-dashed border-default rounded-lg"
            >
              Aucun médicament ajouté pour le moment. Utilisez le formulaire ci-dessus pour composer l'ordonnance.
            </div>

            <div
              v-else
              class="space-y-2"
            >
              <div
                v-for="(it, idx) in items"
                :key="idx"
                class="p-3 bg-surface-muted/40 rounded-lg border border-default flex items-center justify-between gap-3"
              >
                <div class="flex items-start gap-3 min-w-0">
                  <span class="w-6 h-6 rounded-full bg-cyan-600/10 text-cyan-700 dark:text-cyan-400 font-bold text-xs flex items-center justify-center shrink-0 mt-0.5">
                    {{ idx + 1 }}
                  </span>
                  <div class="min-w-0">
                    <div class="font-bold text-sm text-default flex items-center gap-1.5 flex-wrap">
                      <span class="uppercase">{{ it.medication_name }}</span>
                      <span
                        v-if="it.dosage"
                        class="text-cyan-600 dark:text-cyan-400 font-semibold"
                      >{{ it.dosage }}</span>
                      <span
                        v-if="it.form"
                        class="text-subtle text-xs font-normal"
                      >({{ it.form }})</span>
                    </div>
                    <div class="text-xs text-neutral-600 dark:text-neutral-300 mt-0.5">
                      <span class="font-medium">• Posologie:</span> {{ it.frequency || '1 prise / jour' }}
                      <span
                        v-if="it.duration"
                        class="font-medium"
                      > — pendant {{ it.duration }}</span>
                    </div>
                    <div
                      v-if="it.instructions"
                      class="text-[11px] text-subtle italic mt-0.5"
                    >
                      • {{ it.instructions }}
                    </div>
                  </div>
                </div>

                <div class="flex items-center gap-1 shrink-0">
                  <UButton
                    variant="ghost"
                    color="neutral"
                    icon="i-lucide-arrow-up"
                    size="xs"
                    :disabled="idx === 0"
                    class="cursor-pointer"
                    title="Monter"
                    @click="moveItem(idx, 'up')"
                  />
                  <UButton
                    variant="ghost"
                    color="neutral"
                    icon="i-lucide-arrow-down"
                    size="xs"
                    :disabled="idx === items.length - 1"
                    class="cursor-pointer"
                    title="Descendre"
                    @click="moveItem(idx, 'down')"
                  />
                  <UButton
                    variant="ghost"
                    color="error"
                    icon="i-lucide-trash-2"
                    size="xs"
                    class="cursor-pointer ml-1"
                    title="Supprimer"
                    @click="removeItem(idx)"
                  />
                </div>
              </div>
            </div>

            <!-- Notes field -->
            <div class="pt-3 border-t border-default/50 space-y-1">
              <label class="text-xs font-medium text-subtle">
                Instructions cliniques complémentaires ou notes
              </label>
              <UTextarea
                v-model="notes"
                :rows="2"
                placeholder="ex: Contrôle clinique dans 7 jours si persistance de la douleur..."
                class="w-full"
              />
            </div>
          </div>

          <!-- Bottom Action Buttons in Editor -->
          <div class="flex items-center justify-end gap-3 pt-2">
            <UButton
              variant="outline"
              color="neutral"
              icon="i-lucide-eye"
              class="cursor-pointer"
              @click="activeView = 'preview'"
            >
              {{ t('prescriptions.seePadResult', 'Voir l\'aperçu du carnet') }}
            </UButton>
            <UButton
              v-if="!readonly"
              color="primary"
              icon="i-lucide-save"
              :loading="isSaving"
              class="cursor-pointer font-medium"
              @click="handleSave"
            >
              {{ t('common.save', 'Enregistrer l\'ordonnance') }}
            </UButton>
          </div>
        </div>
      </div>
    </div>

    <!-- Delete Confirmation Modal -->
    <UModal v-model="showDeleteConfirm">
      <div class="p-6 space-y-4">
        <div class="flex items-center gap-3">
          <div class="p-2 rounded-full bg-error-500/10 text-error-600">
            <UIcon
              name="i-lucide-alert-triangle"
              class="text-xl"
            />
          </div>
          <div>
            <h3 class="font-semibold text-default">
              {{ t('prescriptions.confirmDeleteTitle', 'Supprimer l\'ordonnance ?') }}
            </h3>
            <p class="text-xs text-subtle mt-0.5">
              Cette action est irréversible. L'ordonnance sera retirée du dossier du patient.
            </p>
          </div>
        </div>

        <div class="flex justify-end gap-2 pt-2">
          <UButton
            variant="ghost"
            color="neutral"
            class="cursor-pointer"
            @click="showDeleteConfirm = false"
          >
            {{ t('common.cancel', 'Annuler') }}
          </UButton>
          <UButton
            color="error"
            :loading="isDeleting"
            class="cursor-pointer"
            @click="confirmDelete"
          >
            {{ t('common.delete', 'Supprimer définitivement') }}
          </UButton>
        </div>
      </div>
    </UModal>
  </div>
</template>

<style scoped>
/* Print stylesheet for Algerian Doctor Prescription Pad */
@media print {
  :global(body.printing-ordonnance *) {
    visibility: hidden;
  }
  :global(body.printing-ordonnance #ordonnance-printable-area),
  :global(body.printing-ordonnance #ordonnance-printable-area *) {
    visibility: visible;
  }
  :global(body.printing-ordonnance #ordonnance-printable-area) {
    position: absolute !important;
    left: 0 !important;
    top: 0 !important;
    width: 100% !important;
    max-width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
    box-shadow: none !important;
    border: none !important;
    background: white !important;
    color: #171717 !important;
    z-index: 999999 !important;
    display: block !important;
    print-color-adjust: exact !important;
    -webkit-print-color-adjust: exact !important;
  }

  :global(.ordonnance-med-item) {
    page-break-inside: avoid !important;
    break-inside: avoid !important;
  }

  :global(.ordonnance-footer) {
    page-break-inside: avoid !important;
    break-inside: avoid !important;
  }
}
</style>
