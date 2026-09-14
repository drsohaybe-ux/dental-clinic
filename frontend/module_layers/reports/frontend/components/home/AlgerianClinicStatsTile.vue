<script setup lang="ts">
defineProps<{ ctx?: unknown }>()

const { locale } = useI18n()

const isAr = computed(() => locale.value === 'ar')

const stats = computed(() => {
  if (isAr.value) {
    return {
      title: 'مؤشرات العيادة (سكيكدة)',
      avgConsultation: '2,500 دج',
      avgConsultationLabel: 'متوسط الفحص السريري',
      acceptanceRate: '82%',
      acceptanceLabel: 'قبول المقايسات',
      activePatients: '1,280+',
      activeLabel: 'مرضى نشطون'
    }
  }
  return {
    title: 'Indicateurs Clinique (Skikda)',
    avgConsultation: '2 500 DZD',
    avgConsultationLabel: 'Tarif moyen consultation',
    acceptanceRate: '82%',
    acceptanceLabel: 'Acceptation devis',
    activePatients: '1 280+',
    activeLabel: 'Patients actifs'
  }
})
</script>

<template>
  <div class="rounded-token-lg bg-surface ring-1 ring-[var(--color-border)] px-4 py-3 shadow-[var(--shadow-sm)] flex flex-col justify-between">
    <div>
      <div class="flex items-center justify-between mb-1">
        <p class="text-caption text-subtle font-medium">
          {{ stats.title }}
        </p>
        <UIcon
          name="i-lucide-activity"
          class="w-4 h-4 text-primary-500"
        />
      </div>

      <div class="flex items-baseline gap-2 mt-1">
        <span class="text-display text-default font-bold tnum">
          {{ stats.avgConsultation }}
        </span>
        <span class="text-caption text-subtle">
          {{ stats.avgConsultationLabel }}
        </span>
      </div>
    </div>

    <div class="mt-3 pt-2 border-t border-[var(--color-border-subtle)] flex items-center justify-between text-caption text-muted">
      <span class="flex items-center gap-1">
        <span class="font-semibold text-default tnum">{{ stats.acceptanceRate }}</span>
        <span>{{ stats.acceptanceLabel }}</span>
      </span>
      <span class="flex items-center gap-1">
        <span class="font-semibold text-default tnum">{{ stats.activePatients }}</span>
        <span>{{ stats.activeLabel }}</span>
      </span>
    </div>
  </div>
</template>
