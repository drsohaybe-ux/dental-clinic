<script setup lang="ts">
/**
 * ReferenceSearchInput — searchable dropdown backed by a medical_reference
 * lookup list.
 *
 * For kind === 'medications':
 * Also loads and searches the Algerian National Medication Nomenclature (~4,636
 * items), prioritizing dental drugs (antibiotics, analgesics, mouthwashes,
 * local anesthetics, corticosteroids).
 *
 * Selecting a nomenclature drug ensures a clinic ReferenceMedication row exists
 * (so patient interaction/contraindication checking works with a real reference_id),
 * and provides a 1-click action to add it directly to the clinic's permanent catalog.
 */
import type { ReferenceItem, ReferenceKind } from '../composables/useMedicalReference'

interface ExtendedItem extends ReferenceItem {
  dci?: string | null
  dosage?: string | null
  is_dental?: boolean
  is_nomenclature?: boolean
}

interface AlgerianNomenclatureItem {
  id: string
  brand_name: string
  dci: string
  dosage?: string | null
  standard_form: string
  is_dental: boolean
  requires_prescription: boolean
}

interface ApiResponse<T> {
  data: T
}

const props = withDefaults(defineProps<{
  kind: ReferenceKind
  modelValue: string
  referenceId?: string | null
  placeholder?: string
  disabled?: boolean
}>(), {
  referenceId: null,
  placeholder: undefined,
  disabled: false
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
  'update:referenceId': [value: string | null]
}>()

const api = useApi()
const toast = useToast()
const { t } = useI18n()
const { search, create } = useMedicalReference()

const items = ref<ExtendedItem[]>([])
const isLoading = ref(false)
const isCreating = ref(false)

// Quick add to clinic catalog state
const isAddingToCatalog = ref(false)
const addedToCatalog = ref(false)

onMounted(async () => {
  isLoading.value = true
  try {
    const baseItems = await search(props.kind, '')
    const mappedBase: ExtendedItem[] = baseItems.map(i => ({ ...i, is_nomenclature: false }))

    if (props.kind === 'medications') {
      try {
        const nomRes = await api.get<ApiResponse<AlgerianNomenclatureItem[]>>(
          '/api/v1/medication_catalog/nomenclature?limit=80'
        )
        const nomItems = nomRes.data || []
        const baseNames = new Set(mappedBase.map(b => b.name.trim().toLowerCase()))

        for (const n of nomItems) {
          const fullName = n.dosage ? `${n.brand_name} ${n.dosage}`.trim() : n.brand_name.trim()
          if (!baseNames.has(fullName.toLowerCase())) {
            mappedBase.push({
              id: `nom-${n.id}`,
              name: fullName,
              is_active: true,
              dci: n.dci,
              dosage: n.dosage,
              is_dental: n.is_dental,
              is_nomenclature: true
            })
          }
        }
      } catch {
        // medication_catalog might be inactive or not installed
      }
    }

    items.value = mappedBase
  } finally {
    isLoading.value = false
  }
})

const selected = computed<ExtendedItem | undefined>({
  get() {
    if (!props.referenceId) {
      if (!props.modelValue) return undefined
      return items.value.find(i => i.name.toLowerCase() === props.modelValue.toLowerCase()) ?? {
        id: '',
        name: props.modelValue,
        is_active: true
      }
    }
    return (
      items.value.find(i => i.id === props.referenceId) ?? {
        id: props.referenceId,
        name: props.modelValue,
        is_active: true
      }
    )
  },
  set(item) {
    if (!item) {
      emit('update:modelValue', '')
      emit('update:referenceId', null)
      addedToCatalog.value = false
      return
    }

    addedToCatalog.value = false

    // If selected item is from nomenclature (not yet in medical_reference_medication),
    // ensure a clinic ReferenceMedication is created so reference_id is valid!
    if (item.is_nomenclature || item.id.startsWith('nom-')) {
      isCreating.value = true
      create(props.kind, { name: item.name }).then((created) => {
        isCreating.value = false
        if (created) {
          item.id = created.id
          item.is_nomenclature = false
          emit('update:modelValue', created.name)
          emit('update:referenceId', created.id)
        } else {
          emit('update:modelValue', item.name)
          emit('update:referenceId', null)
        }
      }).catch(() => {
        isCreating.value = false
        emit('update:modelValue', item.name)
        emit('update:referenceId', null)
      })
      return
    }

    emit('update:modelValue', item.name)
    emit('update:referenceId', item.id || null)
  }
})

// Dynamic search when typing in medications
let searchDebounce: ReturnType<typeof setTimeout> | undefined
function handleSearchTerm(term: string) {
  if (props.kind !== 'medications') return
  clearTimeout(searchDebounce)
  if (!term || term.trim().length < 2) return

  searchDebounce = setTimeout(async () => {
    try {
      const res = await api.get<ApiResponse<AlgerianNomenclatureItem[]>>(
        `/api/v1/medication_catalog/nomenclature?q=${encodeURIComponent(term.trim())}&limit=30`
      )
      const existingIds = new Set(items.value.map(i => i.id))
      const existingNames = new Set(items.value.map(i => i.name.trim().toLowerCase()))

      const newBatch: ExtendedItem[] = []
      for (const n of res.data || []) {
        const fullName = n.dosage ? `${n.brand_name} ${n.dosage}`.trim() : n.brand_name.trim()
        const fakeId = `nom-${n.id}`
        if (!existingIds.has(fakeId) && !existingNames.has(fullName.toLowerCase())) {
          newBatch.push({
            id: fakeId,
            name: fullName,
            is_active: true,
            dci: n.dci,
            dosage: n.dosage,
            is_dental: n.is_dental,
            is_nomenclature: true
          })
        }
      }
      if (newBatch.length > 0) {
        items.value = [...items.value, ...newBatch]
      }
    } catch {
      // Silently fall back
    }
  }, 250)
}

async function handleCreate(name: string) {
  const trimmed = name.trim()
  if (!trimmed) return
  isCreating.value = true
  const created = await create(props.kind, { name: trimmed })
  isCreating.value = false
  if (created) {
    items.value.push(created)
    selected.value = created
  }
}

async function quickAddToClinicCatalog() {
  const medName = props.modelValue?.trim()
  if (!medName) return
  isAddingToCatalog.value = true
  try {
    await api.post('/api/v1/medication_catalog/quick-add', {
      name: medName,
      requires_prescription: true,
      is_active: true
    })
    addedToCatalog.value = true
    toast.add({
      title: t('common.success'),
      description: t('medicalReference.addedToClinicCatalog'),
      color: 'success'
    })
  } catch (e) {
    console.error('Failed to add to clinic catalog:', e)
  } finally {
    isAddingToCatalog.value = false
  }
}
</script>

<template>
  <div class="space-y-1 w-full">
    <USelectMenu
      v-model="selected"
      :items="items"
      :loading="isLoading || isCreating"
      :disabled="disabled"
      label-key="name"
      create-item="always"
      searchable
      :virtualize="true"
      :filter-fields="['name', 'dci']"
      :placeholder="placeholder"
      @create="handleCreate"
      @update:search-term="handleSearchTerm"
    >
      <template #item="{ item }">
        <div class="flex items-center justify-between w-full py-0.5">
          <div class="min-w-0">
            <div class="flex items-center gap-1.5 font-medium truncate">
              <span>{{ item.name }}</span>
              <UBadge
                v-if="item.is_dental"
                size="xs"
                color="primary"
                variant="subtle"
              >
                {{ t('medicalReference.dental') }}
              </UBadge>
            </div>
            <div
              v-if="item.dci"
              class="text-xs text-subtle truncate max-w-xs"
            >
              {{ item.dci }}
            </div>
          </div>
          <UIcon
            v-if="item.is_nomenclature"
            name="i-lucide-database"
            class="text-subtle text-xs shrink-0 ml-1"
          />
        </div>
      </template>
    </USelectMenu>

    <!-- 1-click self-learning add to clinic catalog button when a medication is selected/entered -->
    <div
      v-if="kind === 'medications' && modelValue && !disabled"
      class="flex items-center gap-1.5 pt-0.5 text-xs"
    >
      <span
        v-if="addedToCatalog"
        class="text-success flex items-center gap-1 font-medium"
      >
        <UIcon
          name="i-lucide-check"
          class="text-xs"
        />
        {{ t('medicalReference.inClinicCatalog') }}
      </span>
      <UButton
        v-else
        size="xs"
        variant="link"
        color="primary"
        icon="i-lucide-bookmark-plus"
        :loading="isAddingToCatalog"
        class="p-0 text-xs h-auto cursor-pointer"
        @click="quickAddToClinicCatalog"
      >
        {{ t('medicalReference.addToClinicCatalog') }}
      </UButton>
    </div>
  </div>
</template>
