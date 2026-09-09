<script setup lang="ts">
/**
 * NewPrescriptionActionButton — Quick Action button on patient hero.
 *
 * Registered into `patient.summary.actions`. Routes directly to the dedicated
 * Prescriptions workspace in the Clinical tab with &action=new.
 */
import type { PatientExtended } from '~~/app/types'

const props = defineProps<{
  ctx: {
    patient: PatientExtended
  }
}>()

const { t } = useI18n()
const router = useRouter()

const patientId = computed(() => props.ctx?.patient?.id)

function navigateToNewPrescription() {
  if (patientId.value) {
    router.push({
      path: `/patients/${patientId.value}`,
      query: { tab: 'clinical', clinicalMode: 'prescriptions', action: 'new' }
    })
  }
}
</script>

<template>
  <div v-if="patientId">
    <UButton
      variant="soft"
      color="neutral"
      size="sm"
      icon="i-lucide-receipt"
      block
      class="w-full justify-start cursor-pointer"
      @click="navigateToNewPrescription"
    >
      {{ t('prescriptions.actionButton', 'Ordonnance') }}
    </UButton>
  </div>
</template>
