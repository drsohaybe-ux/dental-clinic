<template>
  <div class="p-6 max-w-7xl mx-auto space-y-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-gray-200 dark:border-gray-800 pb-5">
      <div>
        <h1 class="text-2xl font-bold tracking-tight text-gray-900 dark:text-white flex items-center gap-2">
          <UIcon name="i-lucide-share-2" class="text-primary-500 w-7 h-7" />
          {{ $t('social.title') }}
        </h1>
        <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Supervision clinique et validation 1-clic des publications n8n pour les réseaux sociaux du Dr. Mokhtar.
        </p>
      </div>

      <div class="flex items-center gap-3">
        <UButton
          icon="i-lucide-settings"
          color="gray"
          variant="outline"
          @click="isConfigModalOpen = true"
        >
          Webhooks n8n
        </UButton>
        <UButton
          icon="i-lucide-plus-circle"
          color="primary"
          @click="isCreateModalOpen = true"
        >
          Créer une Publication
        </UButton>
      </div>
    </div>

    <!-- Filter Tabs & Stats Bar -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div class="flex gap-2">
        <UButton
          v-for="tab in tabs"
          :key="tab.key"
          :color="activeTab === tab.key ? 'primary' : 'gray'"
          :variant="activeTab === tab.key ? 'solid' : 'ghost'"
          size="sm"
          @click="activeTab = tab.key"
        >
          {{ tab.label }}
          <UBadge
            :color="activeTab === tab.key ? 'white' : 'gray'"
            variant="subtle"
            size="xs"
            class="ml-1.5"
          >
            {{ getCount(tab.key) }}
          </UBadge>
        </UButton>
      </div>

      <div class="flex items-center gap-2">
        <USelect
          v-model="platformFilter"
          :options="[
            { label: 'Toutes les plateformes', value: 'all' },
            { label: 'Instagram', value: 'instagram' },
            { label: 'Facebook', value: 'facebook' }
          ]"
          size="sm"
          class="w-48"
        />
      </div>
    </div>

    <!-- Grid of Post Cards -->
    <div v-if="filteredPosts.length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <UCard
        v-for="post in filteredPosts"
        :key="post.id"
        class="flex flex-col h-full hover:shadow-lg transition-all duration-200 border border-gray-200 dark:border-gray-800"
        :ui="{ body: { padding: 'p-0 sm:p-0' }, footer: { padding: 'p-4' }, header: { padding: 'p-4' } }"
      >
        <!-- Header -->
        <template #header>
          <div class="flex justify-between items-center">
            <div class="flex items-center gap-2">
              <UBadge
                :color="post.platform === 'instagram' ? 'fuchsia' : 'blue'"
                variant="subtle"
                class="font-semibold text-xs capitalize flex items-center gap-1"
              >
                <UIcon :name="post.platform === 'instagram' ? 'i-lucide-instagram' : 'i-lucide-facebook'" />
                {{ post.platform }}
              </UBadge>
              <span class="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-1">
                <UIcon name="i-lucide-calendar" class="w-3.5 h-3.5" />
                {{ post.scheduled_for || 'Demain à 10h00' }}
              </span>
            </div>
            
            <UBadge :color="getStatusColor(post.status)" variant="solid" size="xs">
              {{ getStatusLabel(post.status) }}
            </UBadge>
          </div>
        </template>

        <!-- Media Image -->
        <div class="relative w-full h-52 bg-gray-100 dark:bg-gray-800 overflow-hidden group">
          <img
            v-if="post.image_url"
            :src="post.image_url"
            :alt="post.title"
            class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          />
          <div v-else class="w-full h-full flex items-center justify-center text-gray-400">
            <UIcon name="i-lucide-image" class="w-12 h-12 opacity-50" />
          </div>
        </div>

        <!-- Body Content -->
        <div class="p-4 flex-grow flex flex-col justify-between space-y-3">
          <div>
            <h3 class="font-bold text-base text-gray-900 dark:text-white leading-snug">
              {{ post.title }}
            </h3>
            <p class="text-sm text-gray-600 dark:text-gray-300 mt-2 whitespace-pre-line line-clamp-4">
              {{ post.caption }}
            </p>
          </div>

          <!-- Hashtags -->
          <div v-if="post.hashtags && post.hashtags.length > 0" class="flex flex-wrap gap-1.5 pt-2">
            <span
              v-for="tag in post.hashtags"
              :key="tag"
              class="text-xs font-medium text-primary-600 dark:text-primary-400 bg-primary-50 dark:bg-primary-950/50 px-2 py-0.5 rounded"
            >
              {{ tag.startsWith('#') ? tag : '#' + tag }}
            </span>
          </div>

          <!-- AI Clinical Note -->
          <div v-if="post.ai_notes" class="bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900/50 rounded-md p-2.5 text-xs text-amber-800 dark:text-amber-300 flex items-start gap-1.5">
            <UIcon name="i-lucide-sparkles" class="w-4 h-4 flex-shrink-0 mt-0.5 text-amber-600 dark:text-amber-400" />
            <span>{{ post.ai_notes }}</span>
          </div>
        </div>

        <!-- Footer Actions -->
        <template #footer>
          <div class="flex items-center justify-between gap-2 pt-1">
            <div class="flex items-center gap-1">
              <UButton
                v-if="post.status === 'waiting_approval'"
                color="red"
                variant="ghost"
                size="sm"
                icon="i-lucide-trash"
                @click="rejectPost(post.id)"
              >
                Rejeter
              </UButton>
            </div>

            <div class="flex items-center gap-2">
              <UButton
                v-if="post.status === 'waiting_approval'"
                color="gray"
                variant="soft"
                size="sm"
                icon="i-lucide-sparkles"
                @click="openEditModal(post)"
              >
                Affiner / Modifier
              </UButton>
              <UButton
                v-if="post.status === 'waiting_approval'"
                color="primary"
                size="sm"
                icon="i-lucide-check-circle"
                @click="approvePost(post.id)"
              >
                Approuver & Publier
              </UButton>
              <UBadge
                v-else-if="post.status === 'approved' || post.status === 'published'"
                color="green"
                variant="subtle"
                class="flex items-center gap-1 py-1 px-2.5 text-xs"
              >
                <UIcon name="i-lucide-check" class="w-4 h-4" />
                Transmis aux Réseaux
              </UBadge>
              <UBadge
                v-else-if="post.status === 'rejected'"
                color="red"
                variant="subtle"
                class="flex items-center gap-1 py-1 px-2.5 text-xs"
              >
                <UIcon name="i-lucide-x" class="w-4 h-4" />
                Publication Rejetée
              </UBadge>
            </div>
          </div>
        </template>
      </UCard>
    </div>

    <!-- Empty State -->
    <div v-else class="text-center py-16 bg-white dark:bg-gray-900 rounded-xl border border-dashed border-gray-300 dark:border-gray-700 p-8">
      <UIcon name="i-lucide-sparkles" class="w-12 h-12 mx-auto text-primary-500 mb-3" />
      <h3 class="text-lg font-bold text-gray-900 dark:text-white">Aucune publication dans cette vue</h3>
      <p class="text-sm text-gray-500 dark:text-gray-400 mt-1 max-w-md mx-auto">
        Toutes les publications ont été validées ou aucun brouillon n'est actuellement en attente de vérification.
      </p>
      <div class="mt-6 flex justify-center gap-3">
        <UButton color="primary" icon="i-lucide-plus" @click="isCreateModalOpen = true">
          Créer un nouveau brouillon
        </UButton>
      </div>
    </div>

    <!-- Modal 1: Affiner / Modifier avec IA -->
    <UModal v-model="isEditModalOpen" :ui="{ width: 'sm:max-w-2xl' }">
      <UCard>
        <template #header>
          <div class="flex items-center justify-between">
            <h3 class="font-bold text-base flex items-center gap-2">
              <UIcon name="i-lucide-sparkles" class="text-primary-500" />
              Révision Clinique avec l'IA
            </h3>
            <UButton color="gray" variant="ghost" icon="i-lucide-x" size="xs" @click="isEditModalOpen = false" />
          </div>
        </template>

        <div class="space-y-4">
          <!-- Quick Prompt Chips -->
          <div>
            <label class="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-2">
              Instructions rapides en 1 clic :
            </label>
            <div class="flex flex-wrap gap-2">
              <UButton
                v-for="chip in quickChips"
                :key="chip"
                color="gray"
                variant="soft"
                size="xs"
                @click="applyQuickChip(chip)"
              >
                {{ chip }}
              </UButton>
            </div>
          </div>

          <UFormGroup label="Instructions pour l'IA ou note du médecin :" class="mt-3">
            <UInput
              v-model="editForm.feedback"
              placeholder="e.g. Mettre en avant nos devis transparents en DZD et notre bilan sans douleur..."
            />
          </UFormGroup>

          <UFormGroup label="Texte de la publication (modifiable en direct) :">
            <UTextarea v-model="editForm.caption" :rows="6" class="font-mono text-sm" />
          </UFormGroup>
        </div>

        <template #footer>
          <div class="flex justify-end gap-2">
            <UButton color="gray" variant="ghost" @click="isEditModalOpen = false">Annuler</UButton>
            <UButton color="primary" icon="i-lucide-check" @click="saveEdit">Appliquer & Mettre à jour</UButton>
          </div>
        </template>
      </UCard>
    </UModal>

    <!-- Modal 2: Créer une Publication -->
    <UModal v-model="isCreateModalOpen" :ui="{ width: 'sm:max-w-xl' }">
      <UCard>
        <template #header>
          <div class="flex items-center justify-between">
            <h3 class="font-bold text-base flex items-center gap-2">
              <UIcon name="i-lucide-plus-circle" class="text-primary-500" />
              Créer une Publication (Clinique Dr. Mokhtar)
            </h3>
            <UButton color="gray" variant="ghost" icon="i-lucide-x" size="xs" @click="isCreateModalOpen = false" />
          </div>
        </template>

        <div class="space-y-4">
          <UFormGroup label="Titre / Thématique du soin" required>
            <UInput v-model="newPostForm.title" placeholder="e.g. Facettes Dentaires & Esthétique du Sourire" />
          </UFormGroup>

          <UFormGroup label="Plateforme cible">
            <USelect
              v-model="newPostForm.platform"
              :options="[
                { label: 'Instagram', value: 'instagram' },
                { label: 'Facebook', value: 'facebook' }
              ]"
            />
          </UFormGroup>

          <UFormGroup label="Texte ou consignes cliniques" required>
            <UTextarea
              v-model="newPostForm.caption"
              :rows="4"
              placeholder="Expliquez les bienfaits du soin, les facilités de paiement en DZD et invitez à nous contacter sur WhatsApp..."
            />
          </UFormGroup>

          <UFormGroup label="URL de l'image (optionnel)">
            <UInput v-model="newPostForm.imageUrl" placeholder="https://..." />
          </UFormGroup>
        </div>

        <template #footer>
          <div class="flex justify-end gap-2">
            <UButton color="gray" variant="ghost" @click="isCreateModalOpen = false">Annuler</UButton>
            <UButton color="primary" @click="submitNewPost">Ajouter au Tableau de Bord</UButton>
          </div>
        </template>
      </UCard>
    </UModal>

    <!-- Modal 3: Configuration n8n -->
    <UModal v-model="isConfigModalOpen" :ui="{ width: 'sm:max-w-xl' }">
      <UCard>
        <template #header>
          <div class="flex items-center justify-between">
            <h3 class="font-bold text-base flex items-center gap-2">
              <UIcon name="i-lucide-webhook" class="text-primary-500" />
              Configuration des Webhooks n8n
            </h3>
            <UButton color="gray" variant="ghost" icon="i-lucide-x" size="xs" @click="isConfigModalOpen = false" />
          </div>
        </template>

        <div class="space-y-4 text-sm">
          <p class="text-gray-600 dark:text-gray-300">
            Connectez directement votre instance n8n pour synchroniser la génération et la publication automatique.
          </p>

          <UFormGroup label="Webhook d'Approbation n8n (POST)" help="Appelé quand le Dr. Mokhtar clique sur 'Approuver & Publier'">
            <UInput v-model="configForm.approveUrl" placeholder="https://n8n.your-domain.com/webhook/dental-approve" />
          </UFormGroup>

          <UFormGroup label="Webhook de Création / Révision n8n (POST)" help="Appelé pour demander une nouvelle version à l'IA">
            <UInput v-model="configForm.createUrl" placeholder="https://n8n.your-domain.com/webhook/dental-create-post" />
          </UFormGroup>
        </div>

        <template #footer>
          <div class="flex justify-end gap-2">
            <UButton color="gray" variant="ghost" @click="isConfigModalOpen = false">Annuler</UButton>
            <UButton color="primary" @click="saveConfig">Enregistrer la Configuration</UButton>
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

definePageMeta({ middleware: 'auth' })

const { t } = useI18n()
const socialStore = useSocialAutomation()

onMounted(() => {
  socialStore.fetchPosts()
})

// Navigation tabs
const tabs = [
  { label: 'Toutes', key: 'all' },
  { label: 'En attente', key: 'waiting_approval' },
  { label: 'Validées', key: 'approved' },
  { label: 'Publiées', key: 'published' }
]

const activeTab = ref('all')
const platformFilter = ref('all')

const filteredPosts = computed(() => {
  let list = socialStore.posts
  if (activeTab.value !== 'all') {
    list = list.filter(p => p.status === activeTab.value)
  }
  if (platformFilter.value !== 'all') {
    list = list.filter(p => p.platform === platformFilter.value)
  }
  return list
})

function getCount(key: string) {
  if (key === 'all') return socialStore.posts.length
  return socialStore.posts.filter(p => p.status === key).length
}

// Quick Revision Chips
const quickChips = [
  '⚡ Plus court & percutant',
  '💰 Insister sur les tarifs en DZD',
  '👨‍⚕️ Ajouter le conseil du Dr. Mokhtar',
  '📲 Ajouter le bouton WhatsApp',
  '🦷 Mettre en avant le soin sans douleur'
]

function applyQuickChip(chip: string) {
  editForm.value.feedback = chip
  if (chip.includes('court')) {
    editForm.value.caption = `🦷 ${editForm.value.caption.slice(0, 120)}...\n\n✨ Prenez rendez-vous en message privé WhatsApp !`
  } else if (chip.includes('DZD') || chip.includes('tarifs')) {
    editForm.value.caption = `${editForm.value.caption}\n\n💰 Tarifs transparents en DZD et facilités de paiement. Contactez-nous pour votre devis !`
  } else if (chip.includes('Dr.')) {
    editForm.value.caption = `👨‍⚕️ Conseil du Dr. Mokhtar :\n\n${editForm.value.caption}\n\nProtocole clinique certifié et anesthésie douce.`
  }
}

// Edit Modal
const isEditModalOpen = ref(false)
const editForm = ref({ id: '', caption: '', feedback: '' })

function openEditModal(post: any) {
  editForm.value = { id: post.id, caption: post.caption, feedback: post.feedback || '' }
  isEditModalOpen.value = true
}

async function saveEdit() {
  await socialStore.updatePostLocally(editForm.value.id, editForm.value.feedback, editForm.value.caption)
  isEditModalOpen.value = false
}

// Actions
const approvePost = async (id: string) => await socialStore.approvePost(id)
const rejectPost = async (id: string) => await socialStore.rejectPost(id)

// Create New Post Modal
const isCreateModalOpen = ref(false)
const newPostForm = ref({
  title: '',
  caption: '',
  platform: 'instagram',
  imageUrl: ''
})

function submitNewPost() {
  if (!newPostForm.value.title.trim() || !newPostForm.value.caption.trim()) return
  socialStore.createNewDraft({
    title: newPostForm.value.title,
    caption: newPostForm.value.caption,
    platform: newPostForm.value.platform,
    imageUrl: newPostForm.value.imageUrl || undefined
  })
  newPostForm.value = { title: '', caption: '', platform: 'instagram', imageUrl: '' }
  isCreateModalOpen.value = false
}

// Config Modal
const isConfigModalOpen = ref(false)
const configForm = ref({
  approveUrl: socialStore.n8nApproveUrl,
  createUrl: socialStore.n8nCreateUrl
})

function saveConfig() {
  socialStore.setN8nUrls(configForm.value.approveUrl, configForm.value.createUrl)
  isConfigModalOpen.value = false
}

// Status helpers
function getStatusColor(status: string) {
  switch (status) {
    case 'waiting_approval': return 'amber'
    case 'approved': return 'green'
    case 'published': return 'blue'
    case 'rejected': return 'red'
    default: return 'gray'
  }
}

function getStatusLabel(status: string) {
  switch (status) {
    case 'waiting_approval': return 'En attente'
    case 'approved': return 'Validé'
    case 'published': return 'Publié'
    case 'rejected': return 'Rejeté'
    default: return status
  }
}
</script>
