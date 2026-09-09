<script setup lang="ts">
/**
 * ClinicalModeToggle — full-width pill-bar over clinical tab modes.
 * Chronological order: diagnosis → plans → appointments → history.
 * Optional badges surface contextual counts (e.g. "Planes 2") so the
 * user sees workload before clicking in.
 */
import type { ClinicalMode } from '~~/app/types'

interface ModeBadges {
  diagnosis?: string | number
  plans?: string | number
  prescriptions?: string | number
  appointments?: string | number
  history?: string | number
}

const props = defineProps<{
  modelValue: ClinicalMode
  badges?: ModeBadges
}>()

const emit = defineEmits<{
  'update:modelValue': [mode: ClinicalMode]
}>()

const { t } = useI18n()

const options = computed(() => [
  {
    value: 'diagnosis',
    label: t('clinical.modes.diagnosis', 'Diagnostic'),
    icon: 'i-lucide-stethoscope',
    badge: props.badges?.diagnosis
  },
  {
    value: 'plans',
    label: t('clinical.modes.plans', 'Plans de traitement'),
    icon: 'i-lucide-clipboard-list',
    badge: props.badges?.plans
  },
  {
    value: 'prescriptions',
    label: t('clinical.modes.prescriptions', 'Prescriptions'),
    icon: 'i-lucide-receipt',
    badge: props.badges?.prescriptions
  },
  {
    value: 'appointments',
    label: t('clinical.modes.appointments', 'Rendez-vous'),
    icon: 'i-lucide-calendar',
    badge: props.badges?.appointments
  },
  {
    value: 'history',
    label: t('clinical.modes.history', 'Historique'),
    icon: 'i-lucide-history',
    badge: props.badges?.history
  }
])
</script>

<template>
  <SegmentedControl
    :model-value="modelValue"
    :options="options"
    full-width
    @update:model-value="(v) => emit('update:modelValue', v as ClinicalMode)"
  />
</template>
