<template>
  <div class="p-6 max-w-[1400px] mx-auto space-y-6">
    <!-- Top Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold tracking-tight text-gray-900 dark:text-white">
          Studio de Contenu & Validation IA
        </h1>
        <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Générez, approuvez et diffusez vos publications sociales connectées en direct à vos workflows n8n.
        </p>
      </div>

      <div class="flex items-center gap-3">
        <!-- Configuration n8n Button -->
        <button
          type="button"
          class="inline-flex items-center gap-2 px-3.5 py-2 text-xs font-semibold text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700/60 shadow-2xs transition-colors"
          @click="isConfigModalOpen = true"
        >
          <UIcon name="i-lucide-settings" class="w-4 h-4 text-gray-500" />
          <span>Configuration n8n</span>
        </button>

        <!-- Créer une Publication Button -->
        <button
          type="button"
          class="inline-flex items-center gap-2 px-4 py-2 text-xs font-semibold text-white bg-[#0084ff] hover:bg-[#0073e6] rounded-lg shadow-sm transition-colors"
          @click="isCreateModalOpen = true"
        >
          <UIcon name="i-lucide-zap" class="w-4 h-4 text-white" />
          <span>Créer une Publication (IA / Manuel)</span>
        </button>
      </div>
    </div>

    <!-- Filter Bar Card -->
    <div class="bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-xl px-4 py-3 shadow-2xs flex flex-col sm:flex-row justify-between items-center gap-4">
      <!-- Tabs (Toutes, En attente, Validées, Publiées) -->
      <div class="flex items-center gap-1.5 w-full sm:w-auto overflow-x-auto">
        <button
          type="button"
          :class="[
            'px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all',
            activeTab === 'all'
              ? 'bg-[#0084ff] text-white shadow-xs'
              : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'
          ]"
          @click="activeTab = 'all'"
        >
          Toutes ({{ counts.all }})
        </button>

        <button
          type="button"
          :class="[
            'px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all',
            activeTab === 'waiting_approval'
              ? 'bg-[#f59e0b] text-white shadow-xs'
              : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'
          ]"
          @click="activeTab = 'waiting_approval'"
        >
          En attente ({{ counts.waiting }})
        </button>

        <button
          type="button"
          :class="[
            'px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all',
            activeTab === 'approved'
              ? 'bg-[#0084ff] text-white shadow-xs'
              : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'
          ]"
          @click="activeTab = 'approved'"
        >
          Validées ({{ counts.approved }})
        </button>

        <button
          type="button"
          :class="[
            'px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all',
            activeTab === 'published'
              ? 'bg-[#16a34a] text-white shadow-xs'
              : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'
          ]"
          @click="activeTab = 'published'"
        >
          Publiées ({{ counts.published }})
        </button>
      </div>

      <!-- Platform Dropdown -->
      <div class="flex items-center gap-2 self-end sm:self-auto">
        <span class="text-xs text-gray-500 dark:text-gray-400 font-medium">Plateforme :</span>
        <select
          v-model="platformFilter"
          class="text-xs font-medium bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-200 rounded-lg px-2.5 py-1.5 focus:outline-hidden focus:ring-2 focus:ring-[#0084ff]"
        >
          <option value="all">Toutes</option>
          <option value="instagram">Instagram</option>
          <option value="facebook">Facebook</option>
        </select>
      </div>
    </div>

    <!-- Cards Grid -->
    <div v-if="filteredPosts.length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <div
        v-for="post in filteredPosts"
        :key="post.id"
        class="bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-2xl shadow-2xs overflow-hidden flex flex-col justify-between hover:shadow-md transition-shadow"
      >
        <!-- Card Top & Image -->
        <div>
          <div class="relative w-full h-56 bg-gray-100 dark:bg-gray-800 overflow-hidden">
            <img
              :src="post.image_url"
              :alt="post.title"
              class="w-full h-full object-cover"
            />
            
            <!-- Platform Badge (Top Left) -->
            <div class="absolute top-3.5 left-3.5">
              <span
                v-if="post.platform === 'instagram'"
                class="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-bold text-white bg-[#0084ff] rounded-md shadow-xs"
              >
                <UIcon name="i-lucide-instagram" class="w-3.5 h-3.5" />
                Instagram
              </span>
              <span
                v-else
                class="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-bold text-white bg-[#1877f2] rounded-md shadow-xs"
              >
                <UIcon name="i-lucide-facebook" class="w-3.5 h-3.5" />
                Facebook
              </span>
            </div>

            <!-- Status Badge (Top Right) -->
            <div class="absolute top-3.5 right-3.5">
              <span
                v-if="post.status === 'waiting_approval'"
                class="inline-flex items-center px-2.5 py-1 text-xs font-bold text-white bg-[#f59e0b] rounded-md shadow-xs"
              >
                En attente de validation
              </span>
              <span
                v-else-if="post.status === 'published' || post.status === 'approved'"
                class="inline-flex items-center px-2.5 py-1 text-xs font-bold text-white bg-[#16a34a] rounded-md shadow-xs"
              >
                Publié
              </span>
            </div>
          </div>

          <!-- Card Content -->
          <div class="p-5 space-y-3">
            <!-- Date -->
            <div class="flex items-center gap-1.5 text-xs text-gray-500 dark:text-gray-400 font-medium">
              <UIcon name="i-lucide-calendar" class="w-3.5 h-3.5 text-red-500" />
              <span>{{ post.scheduled_for }}</span>
            </div>

            <!-- Title -->
            <h3 class="text-base font-bold text-gray-900 dark:text-white leading-snug">
              {{ post.title }}
            </h3>

            <!-- Caption -->
            <p class="text-xs text-gray-600 dark:text-gray-300 whitespace-pre-line leading-relaxed line-clamp-5">
              {{ post.caption }}
            </p>

            <!-- Hashtags -->
            <div v-if="post.hashtags && post.hashtags.length > 0" class="flex flex-wrap gap-1.5 pt-1">
              <span
                v-for="tag in post.hashtags"
                :key="tag"
                class="text-xs font-semibold text-[#0084ff] hover:underline cursor-pointer"
              >
                {{ tag.startsWith('#') ? tag : '#' + tag }}
              </span>
            </div>

            <!-- Dr. Mokhtar AI Note Box -->
            <div
              v-if="post.ai_notes"
              class="bg-gray-50 dark:bg-gray-800/70 border border-gray-100 dark:border-gray-700/60 rounded-xl p-3 text-xs text-gray-600 dark:text-gray-300 flex items-start gap-2 mt-3"
            >
              <UIcon name="i-lucide-sparkles" class="w-4 h-4 text-[#0084ff] flex-shrink-0 mt-0.5" />
              <span>{{ post.ai_notes }}</span>
            </div>
          </div>
        </div>

        <!-- Card Footer -->
        <div class="px-5 pb-5 pt-2">
          <!-- Pending Actions -->
          <div v-if="post.status === 'waiting_approval'" class="flex items-center justify-between gap-2 border-t border-gray-100 dark:border-gray-800 pt-4">
            <div class="flex items-center gap-2">
              <button
                type="button"
                class="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-semibold text-white bg-[#0084ff] hover:bg-[#0073e6] rounded-lg shadow-2xs transition-colors"
                @click="approvePost(post.id)"
              >
                <UIcon name="i-lucide-check" class="w-4 h-4" />
                Approuver & Publier
              </button>

              <button
                type="button"
                class="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-semibold text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/60 rounded-lg transition-colors"
                @click="openEditModal(post)"
              >
                <UIcon name="i-lucide-sparkles" class="w-3.5 h-3.5 text-gray-500" />
                Modifier
              </button>
            </div>

            <button
              type="button"
              class="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-950/30 rounded-lg transition-colors"
              title="Supprimer la publication"
              @click="rejectPost(post.id)"
            >
              <UIcon name="i-lucide-trash-2" class="w-4 h-4" />
            </button>
          </div>

          <!-- Published Metrics -->
          <div v-else class="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400 border-t border-gray-100 dark:border-gray-800 pt-3 font-medium">
            <span>Portée : {{ post.metrics?.reach || 4820 }} vues</span>
            <span class="flex items-center gap-1 text-gray-700 dark:text-gray-200 font-semibold">
              <span class="text-red-500">❤️</span> {{ post.metrics?.likes || 312 }} likes
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty State (Exact clone of Screenshot 2) -->
    <div
      v-else
      class="bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-2xl py-20 px-6 text-center shadow-2xs"
    >
      <div class="w-16 h-16 mx-auto bg-gray-100 dark:bg-gray-800 rounded-2xl flex items-center justify-center text-gray-400 dark:text-gray-500 mb-4">
        <UIcon name="i-lucide-newspaper" class="w-8 h-8 opacity-70" />
      </div>
      <h3 class="text-base font-bold text-gray-900 dark:text-white">
        Aucune publication dans cette catégorie
      </h3>
      <p class="text-xs text-gray-500 dark:text-gray-400 mt-1 max-w-sm mx-auto">
        Créez ou générez une nouvelle publication avec Dr. Mokhtar AI.
      </p>
      <button
        type="button"
        class="mt-5 inline-flex items-center gap-1.5 px-4 py-2 text-xs font-semibold text-[#0084ff] bg-[#e0f2fe] hover:bg-[#bae6fd] dark:bg-sky-950 dark:text-sky-400 rounded-lg transition-colors shadow-2xs"
        @click="isCreateModalOpen = true"
      >
        <UIcon name="i-lucide-sparkles" class="w-3.5 h-3.5" />
        <span>Créer une publication</span>
      </button>
    </div>

    <!-- MODAL 1: Modifier / Révision Clinique avec l'IA -->
    <UModal v-model:open="isEditModalOpen">
      <template #content>
        <UCard>
          <template #header>
            <div class="flex items-center justify-between">
              <h3 class="font-bold text-base text-gray-900 dark:text-white flex items-center gap-2">
                <UIcon name="i-lucide-sparkles" class="text-[#0084ff] w-5 h-5" />
                Modifier & Révision Clinique
              </h3>
              <UButton color="gray" variant="ghost" icon="i-lucide-x" size="xs" @click="isEditModalOpen = false" />
            </div>
          </template>

          <div class="space-y-4">
            <!-- Quick 1-Click Prompt Chips -->
            <div>
              <label class="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-2">
                Recommandations rapides en 1 clic :
              </label>
              <div class="flex flex-wrap gap-2">
                <button
                  v-for="chip in quickChips"
                  :key="chip"
                  type="button"
                  class="text-xs font-medium px-3 py-1.5 bg-gray-100 dark:bg-gray-800 hover:bg-[#e0f2fe] hover:text-[#0084ff] text-gray-700 dark:text-gray-300 rounded-lg border border-gray-200 dark:border-gray-700 transition-colors"
                  @click="applyQuickChip(chip)"
                >
                  {{ chip }}
                </button>
              </div>
            </div>

            <!-- Instruction input -->
            <div>
              <label class="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1.5">
                Instructions pour Dr. Mokhtar AI :
              </label>
              <input
                v-model="editForm.feedback"
                type="text"
                placeholder="e.g. Mettre en avant nos devis transparents en DZD et notre bilan sans douleur..."
                class="w-full text-xs bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-2.5 text-gray-900 dark:text-white focus:ring-2 focus:ring-[#0084ff] focus:outline-hidden"
              />
            </div>

            <!-- Textarea -->
            <div>
              <label class="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1.5">
                Texte de la publication (modifiable en direct) :
              </label>
              <textarea
                v-model="editForm.caption"
                rows="6"
                class="w-full text-xs font-sans bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-3 text-gray-900 dark:text-white focus:ring-2 focus:ring-[#0084ff] focus:outline-hidden"
              ></textarea>
            </div>
          </div>

          <template #footer>
            <div class="flex justify-end gap-3">
              <UButton
                color="gray"
                variant="ghost"
                @click="isEditModalOpen = false"
              >
                Annuler
              </UButton>
              <button
                type="button"
                class="px-4 py-2 text-xs font-semibold text-white bg-[#0084ff] hover:bg-[#0073e6] rounded-lg shadow-xs"
                @click="saveEdit"
              >
                Appliquer les Modifications
              </button>
            </div>
          </template>
        </UCard>
      </template>
    </UModal>

    <!-- MODAL 2: Créer une Publication (Auto ou Custom) -->
    <UModal v-model:open="isCreateModalOpen">
      <template #content>
        <UCard>
          <template #header>
            <div class="flex items-center justify-between">
              <h3 class="font-bold text-base text-gray-900 dark:text-white flex items-center gap-2">
                <UIcon name="i-lucide-zap" class="text-[#0084ff] w-5 h-5" />
                Créer une Publication (IA / Manuel)
              </h3>
              <UButton color="gray" variant="ghost" icon="i-lucide-x" size="xs" @click="isCreateModalOpen = false" />
            </div>
          </template>

          <div class="space-y-4">
            <!-- Mode Toggle -->
            <div class="flex rounded-lg bg-gray-100 dark:bg-gray-800 p-1">
              <button
                type="button"
                :class="[
                  'flex-1 py-1.5 text-xs font-bold rounded-md transition-all',
                  createMode === 'auto' ? 'bg-white dark:bg-gray-900 text-[#0084ff] shadow-xs' : 'text-gray-500'
                ]"
                @click="createMode = 'auto'"
              >
                ⚡ Mode 100% Automatique (IA)
              </button>
              <button
                type="button"
                :class="[
                  'flex-1 py-1.5 text-xs font-bold rounded-md transition-all',
                  createMode === 'custom' ? 'bg-white dark:bg-gray-900 text-[#0084ff] shadow-xs' : 'text-gray-500'
                ]"
                @click="createMode = 'custom'"
              >
                ✍️ Mode Personnalisé
              </button>
            </div>

            <!-- Auto Mode Fields -->
            <div v-if="createMode === 'auto'" class="space-y-4">
              <div>
                <label class="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1.5">
                  Pilier / Thématique Clinique :
                </label>
                <select
                  v-model="newPostForm.pillar"
                  class="w-full text-xs bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-2.5 text-gray-900 dark:text-white focus:ring-2 focus:ring-[#0084ff]"
                >
                  <option value="Esthétique Dentaire & Blanchiment">✨ Esthétique Dentaire & Blanchiment</option>
                  <option value="Orthodontie Invisible & Aligners">🦷 Orthodontie Invisible & Aligners</option>
                  <option value="Implants & Chirurgie Guidée">🔩 Implants & Chirurgie Guidée</option>
                  <option value="Soins Préventifs & Pédodontie">🛡️ Soins Préventifs & Pédodontie</option>
                  <option value="Vie du Cabinet (Nouveaux horaires, Local, Équipe)">🏥 Vie du Cabinet (Nouveaux horaires, Local, Équipe)</option>
                </select>
              </div>

              <div>
                <label class="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1.5">
                  Plateforme Cible :
                </label>
                <select
                  v-model="newPostForm.platform"
                  class="w-full text-xs bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-2.5 text-gray-900 dark:text-white focus:ring-2 focus:ring-[#0084ff]"
                >
                  <option value="instagram">Instagram</option>
                  <option value="facebook">Facebook</option>
                </select>
              </div>
            </div>

            <!-- Custom Mode Fields -->
            <div v-else class="space-y-4">
              <div>
                <label class="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1.5">Titre du soin :</label>
                <input
                  v-model="newPostForm.title"
                  type="text"
                  placeholder="e.g. Facettes Dentaires en Céramique"
                  class="w-full text-xs bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-2.5 text-gray-900 dark:text-white"
                />
              </div>

              <div>
                <label class="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1.5">Texte / Légende :</label>
                <textarea
                  v-model="newPostForm.caption"
                  rows="4"
                  placeholder="Texte détaillé avec tarifs DZD et appel à l'action WhatsApp..."
                  class="w-full text-xs bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-2.5 text-gray-900 dark:text-white"
                ></textarea>
              </div>

              <div>
                <label class="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1.5">URL de l'image (optionnel) :</label>
                <input
                  v-model="newPostForm.imageUrl"
                  type="text"
                  placeholder="https://images.unsplash.com/..."
                  class="w-full text-xs bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-2.5 text-gray-900 dark:text-white"
                />
              </div>
            </div>
          </div>

          <template #footer>
            <div class="flex justify-end gap-3">
              <UButton
                color="gray"
                variant="ghost"
                @click="isCreateModalOpen = false"
              >
                Annuler
              </UButton>
              <button
                type="button"
                class="px-4 py-2 text-xs font-semibold text-white bg-[#0084ff] hover:bg-[#0073e6] rounded-lg shadow-xs"
                @click="submitNewPost"
              >
                Générer / Enregistrer
              </button>
            </div>
          </template>
        </UCard>
      </template>
    </UModal>

    <!-- MODAL 3: Configuration n8n -->
    <UModal v-model:open="isConfigModalOpen">
      <template #content>
        <UCard>
          <template #header>
            <div class="flex items-center justify-between">
              <h3 class="font-bold text-base text-gray-900 dark:text-white flex items-center gap-2">
                <UIcon name="i-lucide-settings" class="text-[#0084ff] w-5 h-5" />
                Configuration des Webhooks n8n
              </h3>
              <UButton color="gray" variant="ghost" icon="i-lucide-x" size="xs" @click="isConfigModalOpen = false" />
            </div>
          </template>

          <div class="space-y-4">
            <p class="text-xs text-gray-600 dark:text-gray-400">
              Vos webhooks n8n permettent d'envoyer les publications directement sur Instagram, Facebook et TikTok une fois approuvées par le Dr. Mokhtar.
            </p>

            <div>
              <label class="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1.5">
                Webhook d'Approbation n8n (POST) :
              </label>
              <input
                v-model="configForm.approveUrl"
                type="text"
                placeholder="https://n8n.your-instance.com/webhook/dental-approve"
                class="w-full text-xs bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-2.5 text-gray-900 dark:text-white font-mono"
              />
            </div>

            <div>
              <label class="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1.5">
                Webhook de Création / Révision n8n (POST) :
              </label>
              <input
                v-model="configForm.createUrl"
                type="text"
                placeholder="https://n8n.your-instance.com/webhook/dental-create"
                class="w-full text-xs bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-2.5 text-gray-900 dark:text-white font-mono"
              />
            </div>

            <div class="p-3 bg-blue-50 dark:bg-blue-950/40 border border-blue-100 dark:border-blue-900/50 rounded-xl text-xs text-blue-800 dark:text-blue-300">
              <p class="font-bold flex items-center gap-1.5 mb-1">
                <UIcon name="i-lucide-shield-check" class="w-4 h-4 text-[#0084ff]" />
                Inbound Secret Token
              </p>
              <p>Configuré dans vos variables Render : <code class="font-bold">DENTALPIN_N8N_SECRET=your_random_password_here</code></p>
            </div>
          </div>

          <template #footer>
            <div class="flex justify-end gap-3">
              <UButton
                color="gray"
                variant="ghost"
                @click="isConfigModalOpen = false"
              >
                Fermer
              </UButton>
              <button
                type="button"
                class="px-4 py-2 text-xs font-semibold text-white bg-[#0084ff] hover:bg-[#0073e6] rounded-lg shadow-xs"
                @click="saveConfig"
              >
                Enregistrer la Configuration
              </button>
            </div>
          </template>
        </UCard>
      </template>
    </UModal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useSocialAutomation, type SocialPost } from '~/composables/useSocialAutomation'

definePageMeta({ middleware: 'auth' })

const socialStore = useSocialAutomation()

onMounted(() => {
  socialStore.fetchPosts()
})

// Tab & Platform state
const activeTab = ref<'all' | 'waiting_approval' | 'approved' | 'published'>('all')
const platformFilter = ref<'all' | 'instagram' | 'facebook'>('all')

// Tab Counts
const counts = computed(() => {
  return {
    all: socialStore.posts.value.length,
    waiting: socialStore.posts.value.filter(p => p.status === 'waiting_approval').length,
    approved: socialStore.posts.value.filter(p => p.status === 'approved').length,
    published: socialStore.posts.value.filter(p => p.status === 'published').length
  }
})

// Filtered posts logic
const filteredPosts = computed(() => {
  let list = socialStore.posts.value
  if (activeTab.value !== 'all') {
    list = list.filter(p => p.status === activeTab.value)
  }
  if (platformFilter.value !== 'all') {
    list = list.filter(p => p.platform === platformFilter.value)
  }
  return list
})

// Actions
const approvePost = async (id: string) => await socialStore.approvePost(id)
const rejectPost = async (id: string) => await socialStore.rejectPost(id)

// Edit Modal State & Chips
const isEditModalOpen = ref(false)
const editForm = ref({ id: '', caption: '', feedback: '' })

const quickChips = [
  '⚡ Plus court & percutant',
  '💰 Insister sur les tarifs en DZD',
  '👨‍⚕️ Ajouter le conseil du Dr. Mokhtar',
  '📲 Ajouter le bouton WhatsApp',
  '🦷 Mettre en avant le soin sans douleur',
  '🌟 Style Avant / Après'
]

function openEditModal(post: SocialPost) {
  editForm.value = {
    id: post.id,
    caption: post.caption,
    feedback: post.feedback || ''
  }
  isEditModalOpen.value = true
}

function applyQuickChip(chip: string) {
  editForm.value.feedback = chip
  if (chip.includes('court')) {
    editForm.value.caption = `🦷 ${editForm.value.caption.slice(0, 110)}...\n\n✨ Prenez rendez-vous en message privé WhatsApp !`
  } else if (chip.includes('DZD') || chip.includes('tarifs')) {
    editForm.value.caption = `${editForm.value.caption}\n\n💰 Tarifs transparents en DZD et facilités de paiement. Contactez-nous pour votre devis !`
  } else if (chip.includes('Dr.')) {
    editForm.value.caption = `👨‍⚕️ Conseil du Dr. Mokhtar :\n\n${editForm.value.caption}\n\nProtocole clinique certifié, anesthésie douce et stérilisation de pointe.`
  } else if (chip.includes('WhatsApp')) {
    editForm.value.caption = `${editForm.value.caption}\n\n📲 Consultation bilan rapide : Contactez-nous directement sur WhatsApp au cabinet.`
  }
}

async function saveEdit() {
  await socialStore.updatePostLocally(editForm.value.id, editForm.value.feedback, editForm.value.caption)
  isEditModalOpen.value = false
}

// Create Modal State
const isCreateModalOpen = ref(false)
const createMode = ref<'auto' | 'custom'>('auto')
const newPostForm = ref({
  title: '',
  caption: '',
  platform: 'instagram' as 'instagram' | 'facebook',
  pillar: 'Esthétique Dentaire & Blanchiment',
  imageUrl: ''
})

function submitNewPost() {
  if (createMode.value === 'auto') {
    socialStore.createNewDraft({
      title: `${newPostForm.value.pillar} au Cabinet Dr. Mokhtar`,
      caption: `🦷 Nouveau traitement personnalisé au cabinet :\n\nPrenez soin de votre sourire grâce à nos protocoles modernes et indolores.\n\n💰 Tarifs transparents en DZD. Contactez-nous sur WhatsApp !`,
      platform: newPostForm.value.platform,
      pillar: newPostForm.value.pillar
    })
  } else {
    if (!newPostForm.value.title.trim() || !newPostForm.value.caption.trim()) return
    socialStore.createNewDraft({
      title: newPostForm.value.title,
      caption: newPostForm.value.caption,
      platform: newPostForm.value.platform,
      imageUrl: newPostForm.value.imageUrl || undefined
    })
  }
  isCreateModalOpen.value = false
  newPostForm.value = {
    title: '',
    caption: '',
    platform: 'instagram',
    pillar: 'Esthétique Dentaire & Blanchiment',
    imageUrl: ''
  }
}

// Config Modal State
const isConfigModalOpen = ref(false)
const configForm = ref({
  approveUrl: socialStore.n8nApproveUrl.value,
  createUrl: socialStore.n8nCreateUrl.value
})

function saveConfig() {
  socialStore.setN8nUrls(configForm.value.approveUrl, configForm.value.createUrl)
  isConfigModalOpen.value = false
}
</script>
