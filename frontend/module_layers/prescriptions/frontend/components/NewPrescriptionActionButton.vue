<script setup lang="ts">
/**
 * NewPrescriptionActionButton — Quick Action button on patient hero.
 *
 * Registered into ``patient.summary.actions``. Opens the authentic Algerian
 * Ordonnance prescription pad modal for immediate drafting and printing.
 */
import type { PatientExtended } from '~~/app/types'

const props = defineProps<{
  ctx: {
    patient: PatientExtended
  }
}>()

const { t } = useI18n()
const isOpen = ref(false)

const patient = computed(() => props.ctx?.patient)

function onPrescriptionSaved() {
  if (patient.value?.id) {
    refreshNuxtData(`prescriptions:summary-card:${patient.value.id}`)
  }
}
</script>

<template>
  <div v-if="patient?.id">
    <UButton
      variant="soft"
      color="neutral"
      size="sm"
      icon="i-lucide-receipt"
      block
      class="w-full justify-start"
      @click="isOpen = true"
    >
      {{ t('prescriptions.actionButton', 'Ordonnance') }}
    </UButton>

    <OrdonnancePadModal
      v-if="isOpen && patient"
      v-model="isOpen"
      :patient="patient"
      @saved="onPrescriptionSaved"
    />
  </div>
</template>
