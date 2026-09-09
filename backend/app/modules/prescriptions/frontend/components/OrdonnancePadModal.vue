<script setup lang="ts">
/**
 * OrdonnancePadModal — Authentic Algerian Doctor Prescription Pad.
 *
 * Implements the authentic layout from Algerian dental practice:
 * - Top Left: Doctor Name and Specialty in French
 * - Top Center: Clinic cyan tooth logo (I SmilE)
 * - Top Right: Doctor Name and Specialty in Arabic (Cairo font)
 * - Below Header: City/Date line, Patient demographics (Nom, Prénom, Âge)
 * - Center: ORDONNANCE (underlined cyan bold title)
 * - Center Watermark: Faint clinic tooth logo in background
 * - Body: Numbered list with medication name, dosage, form, posology, duration, notes
 * - Footer: Clinic address, phone numbers, email, Doctor's Signature & Stamp box
 * - Printing: Directly printable on standard A4 or A5 paper via browser print.
 */
import type { PatientExtended, ApiResponse } from '~~/app/types'
import type { Prescription, PrescriptionItem } from '../composables/usePrescriptions'

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
  modelValue: boolean
  patient: PatientExtended
  prescription?: Prescription | null
}

const props = withDefaults(defineProps<Props>(), {
  prescription: null
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'saved': [prescription: Prescription]
}>()

const api = useApi()
const { t } = useI18n()
const { user } = useAuth()
const { currentClinic } = useClinic()
const { createPrescription, updatePrescription } = usePrescriptions()

// View mode: 'preview' (Pad preview) or 'edit' (Editor form)
const activeView = ref<'preview' | 'edit'>('preview')
const paperSize = ref<'a5' | 'a4'>('a5')
const isSaving = ref(false)

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

// Doctor info (defaults to practitioner / clinic info, persisted locally)
const doctorNameFr = ref(getDefaultDoctorNameFr())
const doctorSpecialtyFr = ref('Chirurgien Dentiste')
const doctorNameAr = ref('الدكتور جراح أسنان')
const doctorSpecialtyAr = ref('جراح أسنان')
const city = ref(getDefaultCity())
const prescriptionDate = ref(new Date().toISOString().split('T')[0] ?? '')
const notes = ref('')

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
      // Ignore localStorage error
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
      // Ignore localStorage error
    }
  }
}

// Prescribed items start empty for new prescription; populated if editing
const items = ref<PrescriptionItem[]>([])

// Builder state for adding new medication
const newItem = ref<PrescriptionItem>({
  medication_name: '',
  dosage: '',
  form: '',
  frequency: '',
  duration: '',
  instructions: '',
  order: 1
})

// Search state for drug autocomplete
const drugSearchQuery = ref('')
const drugSuggestions = ref<Array<{ label: string, name: string, dosage?: string, form?: string, dci?: string, is_dental?: boolean }>>([])
const isSearchingDrugs = ref(false)

// Clinical frequency presets
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

// Computed patient age
const patientAge = computed(() => {
  if (!props.patient?.date_of_birth) return '—'
  const today = new Date()
  const birth = new Date(props.patient.date_of_birth)
  let years = today.getFullYear() - birth.getFullYear()
  const m = today.getMonth() - birth.getMonth()
  if (m < 0 || (m === 0 && today.getDate() < birth.getDate())) years--
  return years
})

// Format date for Algerian prescription (e.g. 09/09/2026)
const formattedDate = computed(() => {
  if (!prescriptionDate.value) return ''
  const parts = prescriptionDate.value.split('-')
  if (parts.length === 3) {
    return `${parts[2]}/${parts[1]}/${parts[0]}`
  }
  return prescriptionDate.value
})

// Clinic contact computed
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

// Populate from existing prescription if provided, or reset cleanly to user defaults
watch(
  () => props.prescription,
  (rx) => {
    if (rx) {
      doctorNameFr.value = rx.doctor_name_fr || getDefaultDoctorNameFr()
      doctorSpecialtyFr.value = rx.doctor_specialty_fr || 'Chirurgien Dentiste'
      doctorNameAr.value = rx.doctor_name_ar || 'الدكتور جراح أسنان'
      doctorSpecialtyAr.value = rx.doctor_specialty_ar || 'جراح أسنان'
      city.value = rx.city || getDefaultCity()
      prescriptionDate.value = rx.prescription_date || new Date().toISOString().split('T')[0] ?? ''
      notes.value = rx.notes || ''
      items.value = rx.items && rx.items.length > 0 ? rx.items.map((it, idx) => ({ ...it, order: idx + 1 })) : []
    } else {
      loadSavedDoctorHeader()
      prescriptionDate.value = new Date().toISOString().split('T')[0] ?? ''
      notes.value = ''
      items.value = []
    }
  },
  { immediate: true }
)

// Autocomplete debounced search for drugs
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

  // Auto-extract dosage if present in name (e.g. "AMOCLAN 1G/200MG", "DOLIPRANE 1000MG COMPRIMES")
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

  // Reset new item form
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
  if (items.value.length === 0) return
  isSaving.value = true
  saveDoctorHeaderToStorage()
  try {
    const payload = {
      patient_id: props.patient.id,
      doctor_name_fr: doctorNameFr.value,
      doctor_specialty_fr: doctorSpecialtyFr.value,
      doctor_name_ar: doctorNameAr.value,
      doctor_specialty_ar: doctorSpecialtyAr.value,
      city: city.value,
      prescription_date: prescriptionDate.value,
      notes: notes.value || null,
      items: items.value.map((it, idx) => ({ ...it, order: idx + 1 }))
    }

    let result: Prescription | null
    if (props.prescription?.id) {
      result = await updatePrescription(props.prescription.id, payload)
    } else {
      result = await createPrescription(payload)
    }

    if (result) {
      emit('saved', result)
      emit('update:modelValue', false)
    }
  } finally {
    isSaving.value = false
  }
}

function close() {
  emit('update:modelValue', false)
}
</script>

<template>
  <UModal
    :model-value="modelValue"
    :ui="{ content: 'max-w-4xl p-0 overflow-hidden print:shadow-none print:border-none' }"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <!-- Dynamic print page styling according to selected paperSize -->
    <component :is="'style'">
      @media print {
        @page {
          size: {{ paperSize === 'a5' ? 'A5 portrait' : 'A4 portrait' }};
          margin: {{ paperSize === 'a5' ? '6mm' : '10mm' }};
        }
      }
    </component>

    <div class="ordonnance-modal flex flex-col max-h-[92vh]">
      <!-- Header bar with controls (hidden when printing) -->
      <div class="no-print flex items-center justify-between px-5 py-3 border-b border-default bg-surface/90 backdrop-blur z-20">
        <div class="flex items-center gap-3">
          <div class="p-1.5 rounded-lg bg-cyan-500/10 text-cyan-600 dark:text-cyan-400">
            <UIcon name="i-lucide-receipt" class="text-xl" />
          </div>
          <div>
            <h2 class="text-base font-semibold text-default">
              {{ t('prescriptions.modalTitle', 'Ordonnance Médicale') }}
            </h2>
            <p class="text-xs text-subtle">
              {{ patient.first_name }} {{ patient.last_name }} ({{ patientAge }} ans)
            </p>
          </div>
        </div>

        <div class="flex items-center gap-2">
          <!-- Switch Editor / Preview -->
          <div class="bg-surface-muted rounded-lg p-0.5 flex items-center text-xs">
            <button
              type="button"
              class="px-2.5 py-1 rounded font-medium transition cursor-pointer"
              :class="activeView === 'preview' ? 'bg-surface shadow-xs text-cyan-600 font-semibold' : 'text-subtle hover:text-default'"
              @click="activeView = 'preview'"
            >
              {{ t('prescriptions.viewPad', 'Aperçu Ordonnance') }}
            </button>
            <button
              type="button"
              class="px-2.5 py-1 rounded font-medium transition cursor-pointer"
              :class="activeView === 'edit' ? 'bg-surface shadow-xs text-cyan-600 font-semibold' : 'text-subtle hover:text-default'"
              @click="activeView = 'edit'"
            >
              {{ t('prescriptions.viewEdit', 'Éditeur & Médicaments') }}
            </button>
          </div>

          <!-- Format A5 / A4 toggle -->
          <USelect
            v-if="activeView === 'preview'"
            v-model="paperSize"
            :items="[
              { label: 'Format A5 (Carnet)', value: 'a5' },
              { label: 'Format A4 (Standard)', value: 'a4' }
            ]"
            value-key="value"
            label-key="label"
            size="xs"
            class="w-36"
          />

          <!-- Print button -->
          <UButton
            icon="i-lucide-printer"
            color="primary"
            size="sm"
            class="font-medium cursor-pointer"
            @click="printOrdonnance"
          >
            {{ t('common.print', 'Imprimer') }}
          </UButton>

          <!-- Save button -->
          <UButton
            icon="i-lucide-save"
            variant="soft"
            color="neutral"
            size="sm"
            :loading="isSaving"
            class="cursor-pointer"
            @click="handleSave"
          >
            {{ t('common.save', 'Enregistrer') }}
          </UButton>

          <!-- Close button -->
          <UButton
            icon="i-lucide-x"
            variant="ghost"
            color="neutral"
            size="sm"
            class="cursor-pointer ml-1"
            @click="close"
          />
        </div>
      </div>

      <!-- Modal Body -->
      <div class="overflow-y-auto flex-1 p-4 sm:p-6 bg-surface-muted/20">
        <!-- ============================================================= -->
        <!-- VIEW 1: AUTHENTIC ALGERIAN ORDONNANCE PAD (PREVIEW & PRINT) -->
        <!-- ============================================================= -->
        <div v-show="activeView === 'preview'" class="flex justify-center w-full">
          <div
            id="ordonnance-printable-area"
            class="ordonnance-sheet bg-white text-neutral-900 mx-auto relative rounded-md shadow-lg border border-neutral-200/80 transition-all font-sans print:shadow-none print:border-none print:rounded-none print:w-full"
            :class="paperSize === 'a5' ? 'w-full max-w-[560px] min-h-[760px]' : 'w-full max-w-[760px] min-h-[980px]'"
          >
            <!-- Faint Tooth Watermark in background -->
            <div class="absolute inset-0 flex items-center justify-center pointer-events-none overflow-hidden select-none">
              <img
                src="/logo.png?v=3"
                alt="I SmilE Watermark"
                class="w-72 h-72 object-contain opacity-[0.06] grayscale contrast-125"
              />
            </div>

            <!-- Content layer -->
            <div class="relative z-10 flex flex-col justify-between h-full p-6 sm:p-9">
              <!-- Top Section -->
              <div>
                <!-- Header: French doctor (Left), Cyan Logo (Center), Arabic doctor (Right) -->
                <div class="flex items-start justify-between border-b border-cyan-100 pb-3">
                  <!-- Left: Doctor & Specialty in French -->
                  <div class="text-left space-y-0.5 max-w-[35%]">
                    <div class="text-base sm:text-lg font-bold text-cyan-700 uppercase tracking-tight">
                      {{ doctorNameFr }}
                    </div>
                    <div class="text-xs sm:text-sm font-medium text-cyan-600">
                      {{ doctorSpecialtyFr }}
                    </div>
                  </div>

                  <!-- Center: Clinic logo & tooth branding -->
                  <div class="flex flex-col items-center px-2">
                    <img
                      src="/logo.png?v=3"
                      alt="I SmilE Logo"
                      class="h-11 w-11 sm:h-12 sm:w-12 object-contain"
                    />
                    <span class="font-pacifico text-cyan-600 text-sm mt-0.5 tracking-tight">
                      I SmilE
                    </span>
                    <span class="text-[10px] text-cyan-700/80 font-medium -mt-1">
                      Cabinet Dentaire
                    </span>
                  </div>

                  <!-- Right: Doctor & Specialty in Arabic -->
                  <div class="text-right space-y-0.5 max-w-[35%] font-['Cairo']" dir="rtl">
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
                  <div class="flex items-baseline justify-between border-b border-dotted border-neutral-300 pb-2 pt-1 font-medium">
                    <div>
                      <span class="text-neutral-500">Nom: </span>
                      <span class="font-bold text-neutral-900 uppercase tracking-wider pl-1">
                        {{ patient.last_name }}
                      </span>
                    </div>
                    <div>
                      <span class="text-neutral-500">Prénom: </span>
                      <span class="font-bold text-neutral-900 capitalize pl-1">
                        {{ patient.first_name }}
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
                      <span v-if="item.dosage" class="font-bold text-cyan-700 text-xs sm:text-sm">
                        {{ item.dosage }}
                      </span>
                      <span v-if="item.form" class="text-neutral-600 italic text-xs">
                        ({{ item.form }})
                      </span>
                    </div>

                    <!-- Posology & Duration -->
                    <div class="pl-5 text-xs sm:text-sm text-neutral-800 space-y-0.5">
                      <div v-if="item.frequency">
                        <span class="text-neutral-500">• Posologie: </span>
                        <span class="font-medium text-neutral-900">{{ item.frequency }}</span>
                        <span v-if="item.duration" class="font-semibold text-neutral-900"> — pendant {{ item.duration }}</span>
                      </div>
                      <div v-if="item.instructions" class="text-neutral-600 italic text-xs">
                        <span>• Note: {{ item.instructions }}</span>
                      </div>
                    </div>
                  </div>

                  <!-- Empty state if no drugs yet (hidden on print so blank pad can be printed) -->
                  <div
                    v-if="items.length === 0"
                    class="no-print h-44 flex items-center justify-center text-subtle text-xs italic"
                  >
                    {{ t('prescriptions.noDrugsYet', 'Aucun médicament prescrit. Cliquez sur "Éditeur" pour en ajouter.') }}
                  </div>
                </div>
              </div>

              <!-- Bottom Footer -->
              <div class="ordonnance-footer mt-8 pt-3 border-t border-cyan-100">
                <div class="flex items-end justify-between text-[11px] sm:text-xs text-cyan-900">
                  <!-- Contact info -->
                  <div class="space-y-1 max-w-[65%]">
                    <div class="flex items-center gap-1.5 text-cyan-800">
                      <UIcon name="i-lucide-map-pin" class="text-cyan-600 shrink-0 text-xs" />
                      <span class="truncate">{{ clinicAddress }}</span>
                    </div>
                    <div class="flex items-center gap-3 text-cyan-800 flex-wrap">
                      <span v-if="clinicPhone" class="flex items-center gap-1">
                        <UIcon name="i-lucide-phone" class="text-cyan-600 text-xs" />
                        {{ clinicPhone }}
                      </span>
                      <span v-if="clinicEmail" class="flex items-center gap-1">
                        <UIcon name="i-lucide-mail" class="text-cyan-600 text-xs" />
                        {{ clinicEmail }}
                      </span>
                    </div>
                  </div>

                  <!-- Doctor Stamp & Signature Box -->
                  <div class="text-center">
                    <div class="text-[10px] uppercase font-semibold text-cyan-700 tracking-wider mb-1">
                      Signature & Cachet
                    </div>
                    <div class="w-32 h-16 sm:w-36 sm:h-20 border border-dashed border-cyan-300 rounded bg-cyan-50/20 flex items-center justify-center text-[10px] text-cyan-400 select-none">
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- ============================================================= -->
        <!-- VIEW 2: FULL PRESCRIPTION BUILDER & EDITOR -->
        <!-- ============================================================= -->
        <div v-show="activeView === 'edit'" class="space-y-6 max-w-3xl mx-auto">
          <!-- Doctor & Clinic Settings -->
          <div class="p-4 rounded-xl border border-default bg-surface space-y-4">
            <h3 class="text-sm font-semibold text-default flex items-center gap-2">
              <UIcon name="i-lucide-user-check" class="text-primary" />
              {{ t('prescriptions.doctorHeader', 'En-tête du Médecin & Cabinet') }}
            </h3>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div class="space-y-1">
                <label class="text-xs font-medium text-subtle">
                  Nom du médecin (Français)
                </label>
                <UInput v-model="doctorNameFr" placeholder="Dr. LOKMANE R." />
              </div>

              <div class="space-y-1">
                <label class="text-xs font-medium text-subtle">
                  Spécialité (Français)
                </label>
                <UInput v-model="doctorSpecialtyFr" placeholder="Chirurgien Dentiste" />
              </div>

              <div class="space-y-1">
                <label class="text-xs font-medium text-subtle">
                  اسم الطبيب (بالعربية)
                </label>
                <UInput v-model="doctorNameAr" dir="rtl" placeholder="الدكتور لقمان ر." />
              </div>

              <div class="space-y-1">
                <label class="text-xs font-medium text-subtle">
                  التخصص (بالعربية)
                </label>
                <UInput v-model="doctorSpecialtyAr" dir="rtl" placeholder="جراح أسنان" />
              </div>

              <div class="space-y-1">
                <label class="text-xs font-medium text-subtle">
                  Ville / Commune
                </label>
                <UInput v-model="city" placeholder="Boumerdès" />
              </div>

              <div class="space-y-1">
                <label class="text-xs font-medium text-subtle">
                  Date de prescription
                </label>
                <UInput v-model="prescriptionDate" type="date" />
              </div>
            </div>
          </div>

          <!-- Add Medication Card with Autocomplete & Presets -->
          <div class="p-4 rounded-xl border border-default bg-surface space-y-4">
            <h3 class="text-sm font-semibold text-default flex items-center gap-2">
              <UIcon name="i-lucide-pill" class="text-primary" />
              {{ t('prescriptions.addMedication', 'Ajouter un médicament') }}
            </h3>

            <!-- Search Algerian nomenclature -->
            <div class="space-y-2 relative">
              <label class="text-xs font-medium text-subtle block">
                Rechercher dans la nomenclature algérienne & catalogue clinique
              </label>
              <div class="relative">
                <UInput
                  v-model="drugSearchQuery"
                  icon="i-lucide-search"
                  :loading="isSearchingDrugs"
                  placeholder="Tapez le nom d'un médicament (ex: Amoclan, Augmentin, Doliprane, Eludril...)"
                  class="w-full"
                />

                <!-- Suggestions dropdown -->
                <div
                  v-if="drugSuggestions.length > 0"
                  class="absolute left-0 right-0 top-full mt-1 bg-surface border border-default rounded-lg shadow-xl max-h-56 overflow-y-auto z-30 divide-y divide-default"
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
                        <span v-if="sug.dosage" class="text-cyan-600 font-semibold">{{ sug.dosage }}</span>
                        <UBadge v-if="sug.is_dental" size="xs" color="primary" variant="subtle">
                          Dentaire
                        </UBadge>
                      </div>
                      <div v-if="sug.dci" class="text-[11px] text-subtle truncate">
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

            <!-- Manual or refined input fields -->
            <div class="grid grid-cols-1 sm:grid-cols-12 gap-3 items-end pt-1">
              <div class="sm:col-span-4 space-y-1">
                <label class="text-xs font-medium text-subtle">
                  Médicament
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
                  <UDropdownMenu
                    :items="[
                      frequencyPresets.map(preset => ({
                        label: preset,
                        onSelect: () => { newItem.frequency = preset }
                      }))
                    ]"
                  >
                    <UButton
                      size="xs"
                      variant="ghost"
                      color="primary"
                      trailing-icon="i-lucide-chevron-down"
                      class="text-xs py-0 h-5"
                    >
                      Presets
                    </UButton>
                  </UDropdownMenu>
                </div>
                <UInput
                  v-model="newItem.frequency"
                  placeholder="ex: 1 comp 2x/jour (Matin/Soir)"
                />
              </div>

              <!-- Duration with presets -->
              <div class="sm:col-span-3 space-y-1">
                <div class="flex items-center justify-between">
                  <label class="text-xs font-medium text-subtle">
                    Durée
                  </label>
                  <UDropdownMenu
                    :items="[
                      durationPresets.map(d => ({
                        label: d,
                        onSelect: () => { newItem.duration = d }
                      }))
                    ]"
                  >
                    <UButton
                      size="xs"
                      variant="ghost"
                      color="primary"
                      trailing-icon="i-lucide-chevron-down"
                      class="text-xs py-0 h-5"
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

              <!-- Instructions / Notes -->
              <div class="sm:col-span-3 space-y-1">
                <div class="flex items-center justify-between">
                  <label class="text-xs font-medium text-subtle">
                    Instructions
                  </label>
                  <UDropdownMenu
                    :items="[
                      instructionPresets.map(ins => ({
                        label: ins,
                        onSelect: () => { newItem.instructions = ins }
                      }))
                    ]"
                  >
                    <UButton
                      size="xs"
                      variant="ghost"
                      color="primary"
                      trailing-icon="i-lucide-chevron-down"
                      class="text-xs py-0 h-5"
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

          <!-- Prescribed List -->
          <div class="p-4 rounded-xl border border-default bg-surface space-y-3">
            <div class="flex items-center justify-between">
              <h3 class="text-sm font-semibold text-default">
                Médicaments sur l'ordonnance ({{ items.length }})
              </h3>
              <UButton
                size="xs"
                variant="soft"
                color="primary"
                icon="i-lucide-eye"
                @click="activeView = 'preview'"
              >
                Voir le résultat
              </UButton>
            </div>

            <div v-if="items.length === 0" class="text-subtle text-xs py-4 text-center">
              Aucun médicament ajouté pour le moment.
            </div>

            <div v-else class="space-y-2">
              <div
                v-for="(it, idx) in items"
                :key="idx"
                class="p-3 bg-surface-muted/40 rounded-lg border border-default flex items-start justify-between gap-3"
              >
                <div class="flex items-start gap-2.5">
                  <span class="w-6 h-6 rounded-full bg-cyan-600/10 text-cyan-700 font-bold text-xs flex items-center justify-center shrink-0 mt-0.5">
                    {{ idx + 1 }}
                  </span>
                  <div>
                    <div class="font-bold text-sm text-default flex items-center gap-1.5">
                      <span>{{ it.medication_name }}</span>
                      <span v-if="it.dosage" class="text-cyan-600">{{ it.dosage }}</span>
                      <span v-if="it.form" class="text-subtle text-xs font-normal">({{ it.form }})</span>
                    </div>
                    <div class="text-xs text-neutral-600 dark:text-neutral-300 mt-0.5">
                      <span class="font-medium">• Posologie:</span> {{ it.frequency || '1 prise / jour' }}
                      <span v-if="it.duration" class="font-medium"> — pendant {{ it.duration }}</span>
                    </div>
                    <div v-if="it.instructions" class="text-[11px] text-subtle italic">
                      {{ it.instructions }}
                    </div>
                  </div>
                </div>

                <UButton
                  variant="ghost"
                  color="error"
                  icon="i-lucide-trash-2"
                  size="xs"
                  class="cursor-pointer"
                  @click="removeItem(idx)"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </UModal>
</template>

<style scoped>
/* Print stylesheet for Algerian Doctor Prescription Pad */
@media print {
  /* Scoped strictly to when the ordonnance print trigger is active to prevent polluting global app printing */
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
