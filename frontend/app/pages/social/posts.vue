<template>
  <div class="p-6">
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold">{{ $t('social.title') }}</h1>
      <UButton icon="i-lucide-settings" @click="isConfigModalOpen = true">
        n8n Config
      </UButton>
    </div>

    <!-- Filter Tabs -->
    <UTabs :items="tabs" class="mb-6" @change="onTabChange" />

    <!-- Grid of Posts -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <UCard v-for="post in filteredPosts" :key="post.id" class="flex flex-col h-full">
        <template #header>
          <div class="flex justify-between items-center">
            <UBadge :color="post.platform === 'instagram' ? 'fuchsia' : 'blue'">
              {{ post.platform.toUpperCase() }}
            </UBadge>
            <UBadge :color="getStatusColor(post.status)" variant="subtle">
              {{ $t('social.tabs.' + getStatusKey(post.status)) }}
            </UBadge>
          </div>
        </template>
        
        <img v-if="post.image_url" :src="post.image_url" class="w-full h-48 object-cover rounded-md mb-4" />
        
        <h3 class="font-semibold text-lg mb-2">{{ post.title }}</h3>
        <p class="text-sm text-gray-600 dark:text-gray-300 whitespace-pre-line flex-grow">
          {{ post.caption }}
        </p>

        <div class="mt-4 flex flex-wrap gap-2">
          <UBadge v-for="tag in post.hashtags" :key="tag" color="gray" variant="solid">
            {{ tag }}
          </UBadge>
        </div>

        <template #footer>
          <div class="flex gap-2 justify-end" v-if="post.status === 'waiting_approval'">
            <UButton color="gray" variant="ghost" icon="i-lucide-edit" @click="openEditModal(post)">
              {{ $t('social.card.edit_btn') }}
            </UButton>
            <UButton color="red" variant="ghost" icon="i-lucide-trash" @click="rejectPost(post.id)">
              {{ $t('social.card.delete_btn') }}
            </UButton>
            <UButton color="green" icon="i-lucide-check-circle" @click="approvePost(post.id)">
              {{ $t('social.card.approve_btn') }}
            </UButton>
          </div>
        </template>
      </UCard>
    </div>

    <!-- Edit Modal -->
    <UModal v-model="isEditModalOpen">
      <UCard>
        <template #header>
          <h3 class="font-bold">{{ $t('social.card.edit_btn') }}</h3>
        </template>
        <UFormGroup label="Caption">
          <UTextarea v-model="editForm.caption" :rows="6" />
        </UFormGroup>
        <UFormGroup label="Dr. Mokhtar AI Feedback" class="mt-4">
          <UInput v-model="editForm.feedback" placeholder="e.g. Plus court, ajouter prix DZD..." />
        </UFormGroup>
        <template #footer>
          <div class="flex justify-end gap-2">
            <UButton color="gray" @click="isEditModalOpen = false">Annuler</UButton>
            <UButton color="primary" @click="saveEdit">Enregistrer</UButton>
          </div>
        </template>
      </UCard>
    </UModal>

    <!-- Config Modal -->
    <UModal v-model="isConfigModalOpen">
      <UCard>
        <template #header>
          <h3 class="font-bold">n8n Webhook Configuration</h3>
        </template>
        <UFormGroup label="Approval Webhook URL" class="mb-4">
          <UInput v-model="configForm.approveUrl" />
        </UFormGroup>
        <UFormGroup label="Create/Refine Webhook URL">
          <UInput v-model="configForm.createUrl" />
        </UFormGroup>
        <template #footer>
          <div class="flex justify-end gap-2">
            <UButton color="gray" @click="isConfigModalOpen = false">Annuler</UButton>
            <UButton color="primary" @click="saveConfig">Enregistrer</UButton>
          </div>
        </template>
      </UCard>
    </UModal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useSocialAutomation } from '~/composables/useSocialAutomation'

// Middleware protection (global auth covers this, but explicit definition for safety)
definePageMeta({ middleware: 'auth' })

const { t } = useI18n()
const socialStore = useSocialAutomation()

onMounted(() => {
  socialStore.fetchPosts()
})

const tabs = computed(() => [
  { label: t('social.tabs.all'), key: 'all' },
  { label: t('social.tabs.waiting'), key: 'waiting_approval' },
  { label: t('social.tabs.approved'), key: 'approved' },
  { label: t('social.tabs.published'), key: 'published' }
])

const activeTab = ref('all')
const onTabChange = (index: number) => {
  activeTab.value = tabs.value[index].key
}

const filteredPosts = computed(() => {
  if (activeTab.value === 'all') return socialStore.posts
  return socialStore.posts.filter(p => p.status === activeTab.value)
})

// Editing
const isEditModalOpen = ref(false)
const editForm = ref({ id: '', caption: '', feedback: '' })
const openEditModal = (post: any) => {
  editForm.value = { id: post.id, caption: post.caption, feedback: post.feedback || '' }
  isEditModalOpen.value = true
}
const saveEdit = async () => {
  await socialStore.updatePostLocally(editForm.value.id, editForm.value.feedback, editForm.value.caption)
  isEditModalOpen.value = false
}

// Actions
const approvePost = async (id: string) => await socialStore.approvePost(id)
const rejectPost = async (id: string) => await socialStore.rejectPost(id)

// Config
const isConfigModalOpen = ref(false)
const configForm = ref({
  approveUrl: socialStore.n8nApproveUrl,
  createUrl: socialStore.n8nCreateUrl
})
const saveConfig = () => {
  socialStore.setN8nUrls(configForm.value.approveUrl, configForm.value.createUrl)
  isConfigModalOpen.value = false
}

// Helpers
const getStatusColor = (status: string) => {
  switch(status) {
    case 'waiting_approval': return 'amber'
    case 'approved': return 'green'
    case 'published': return 'blue'
    case 'rejected': return 'red'
    default: return 'gray'
  }
}
const getStatusKey = (status: string) => {
  switch(status) {
    case 'waiting_approval': return 'waiting'
    case 'approved': return 'approved'
    case 'published': return 'published'
    default: return 'all'
  }
}
</script>
