<script setup lang="ts">
/**
 * PrescriptionsCard — smart-card for the patient Resumen grid.
 *
 * Registered into `patient.summary.cards` by the prescriptions module.
 * Displays recent official prescriptions (ordonnances), medication summary,
 * and quick trigger to navigate directly to the dedicated Prescriptions workspace
 * in the Clinical tab.
 */
import type { PatientExtended, ApiResponse } from '~~/app/types'
import type { Prescription } from '../composables/usePrescriptions'

interface Ctx {
  patient: PatientExtended
}

const props = defineProps<{ ctx: Ctx }>()

const { t, locale } = useI18n()
const api = useApi()
const router = useRouter()

const patientId = computed(() => props.ctx.patient?.id)

const { data, status } = await useAsyncData(
  () => `prescriptions:summary-card:${patientId.value}`,
  async () => {
    if (!patientId.value) return []
    try {
      const res = await api.get<ApiResponse<Prescription[]>>(
        `/api/v1/prescriptions/patient/${patientId.value}`
      )
      return res.data || []
    } catch {
      return []
    }
  },
  { watch: [patientId], server: false }
)

const prescriptions = computed<Prescription[]>(() => data.value ?? [])
const total = computed(() => prescriptions.value.length)
const recentPrescriptions = computed(() => prescriptions.value.slice(0, 3))

function openCreate() {
  if (patientId.value) {
    router.push({
      path: `/patients/${patientId.value}`,
      query: { tab: 'clinical', clinicalMode: 'prescriptions', action: 'new' }
    })
  }
}

function openView(rx: Prescription) {
  if (patientId.value) {
    router.push({
      path: `/patients/${patientId.value}`,
      query: { tab: 'clinical', clinicalMode: 'prescriptions', rxId: rx.id }
    })
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
  const names = rx.items.slice(0, 2).map(i => i.medication_name)
  if (rx.items.length > 2) {
    return `${names.join(', ')} (+${rx.items.length - 2})`
  }
  return names.join(', ')
}

const severity = computed<'neutral' | 'info'>(() => {
  return total.value > 0 ? 'info' : 'neutral'
})
</script>

<template>
  <SummaryCard
    :title="t('prescriptions.cardTitle', 'Ordonnances')"
    icon="i-lucide-receipt"
    :severity="severity"
    :loading="status === 'pending'"
    :empty="total === 0"
  >
    <template #empty>
      <div class="py-2 text-center text-caption text-muted">
        <p>{{ t('prescriptions.empty', 'Aucune ordonnance émise') }}</p>
        <UButton
          size="xs"
          variant="soft"
          color="primary"
          icon="i-lucide-plus"
          class="mt-2 cursor-pointer"
          @click.stop="openCreate"
        >
          {{ t('prescriptions.newPrescription', 'Créer une ordonnance') }}
        </UButton>
      </div>
    </template>

    <div class="space-y-2">
      <div class="flex items-baseline justify-between">
        <div class="flex items-baseline gap-1">
          <span class="text-h2 text-default tnum">{{ total }}</span>
          <span class="text-caption text-muted">
            {{ total > 1 ? t('prescriptions.pluralCount', 'ordonnances') : t('prescriptions.singularCount', 'ordonnance') }}
          </span>
        </div>
        <UButton
          size="xs"
          variant="ghost"
          color="primary"
          icon="i-lucide-plus"
          class="cursor-pointer"
          @click.stop="openCreate"
        >
          {{ t('prescriptions.new', 'Nouvelle') }}
        </UButton>
      </div>

      <ul class="space-y-1.5 divide-y divide-default/50">
        <li
          v-for="rx in recentPrescriptions"
          :key="rx.id"
          class="pt-1.5 first:pt-0 flex items-center justify-between gap-2 group cursor-pointer hover:bg-elevated/50 p-1 rounded-token-sm transition-colors"
          @click="openView(rx)"
        >
          <div class="min-w-0 flex-1">
            <p class="text-xs font-medium text-default truncate">
              {{ formatMedicationSummary(rx) }}
            </p>
            <p class="text-[11px] text-subtle flex items-center gap-1.5 mt-0.5">
              <span>{{ formatDate(rx.prescription_date || rx.created_at) }}</span>
              <span
                v-if="rx.doctor_name_fr"
                class="text-muted truncate"
              >· {{ rx.doctor_name_fr }}</span>
            </p>
          </div>
          <UButton
            size="xs"
            variant="ghost"
            color="neutral"
            icon="i-lucide-printer"
            class="opacity-70 group-hover:opacity-100 shrink-0 cursor-pointer"
            :title="t('prescriptions.print', 'Imprimer')"
            @click.stop="openView(rx)"
          />
        </li>
      </ul>
    </div>

    <template #footer>
      <div class="flex items-center justify-between w-full text-caption">
        <span
          class="text-primary hover:underline cursor-pointer flex items-center gap-1 font-medium"
          @click="openCreate"
        >
          <UIcon
            name="i-lucide-file-plus"
            class="w-3.5 h-3.5"
          />
          {{ t('prescriptions.createOrdonnance', 'Rédiger une ordonnance') }}
        </span>
      </div>
    </template>
  </SummaryCard>
</template>
