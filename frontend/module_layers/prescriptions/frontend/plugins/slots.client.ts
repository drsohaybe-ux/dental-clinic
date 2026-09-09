import { defineAsyncComponent } from 'vue'
import { registerSlot } from '~~/app/composables/useModuleSlots'

/**
 * Slot registrations for the `prescriptions` module.
 *
 * Hosts (`patients`) expose stable slot names. The slot
 * registry is the only contract — neither side imports the other.
 */
export default defineNuxtPlugin(() => {
  // Patient Resumen — Prescriptions smart-card.
  registerSlot('patient.summary.cards', {
    id: 'prescriptions.patient.summary.cards.prescriptions',
    component: defineAsyncComponent(
      () => import('../components/PrescriptionsCard.vue')
    ),
    order: 45,
    permission: 'prescriptions.read'
  })

  // Patient Quick Actions — New Ordonnance CTA.
  registerSlot('patient.summary.actions', {
    id: 'prescriptions.patient.summary.actions.new-prescription',
    component: defineAsyncComponent(
      () => import('../components/NewPrescriptionActionButton.vue')
    ),
    order: 25,
    permission: 'prescriptions.write'
  })
})
