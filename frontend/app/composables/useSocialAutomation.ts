import { useI18n } from 'vue-i18n'

export interface SocialPost {
  id: string
  platform: 'instagram' | 'facebook' | 'tiktok'
  title: string
  caption: string
  hashtags: string[]
  image_url: string
  status: 'draft' | 'waiting_approval' | 'approved' | 'published' | 'rejected'
  scheduled_for: string
  ai_notes?: string
  feedback?: string
  is_pinned?: boolean
  metrics?: { reach: number; likes: number }
  approval_webhook_url?: string
  created_at: string
}

export const EXACT_SEED_POSTS: SocialPost[] = [
  {
    id: 'post-seed-1',
    platform: 'instagram',
    title: "5 Signes Précurseurs d'une Carie Dentaire",
    caption: "🦷 Saviez-vous qu'une carie commence souvent sans aucune douleur sous la surface de l'émail ?\n\nVoici 5 signes d'alerte à ne jamais ignorer :...\n\n👉 Prenez rendez-vous dès aujourd'hui pour votre bilan préventif.",
    hashtags: ['#SanteDentaire', '#SourireParfait', '#DentisteAlger', '#SoinsDentaires', '#HygieneBuccoDentaire'],
    image_url: 'https://images.unsplash.com/photo-1629909615184-74f495363b67?auto=format&fit=crop&w=1000&q=80',
    status: 'waiting_approval',
    scheduled_for: 'Demain à 10h00',
    ai_notes: 'Dr. Mokhtar AI : Cible : Soins préventifs et détartrage. Généré par Dr. Mokhtar AI.',
    created_at: new Date().toISOString()
  },
  {
    id: 'post-seed-2',
    platform: 'facebook',
    title: 'Avant / Après : Blanchiment Dentaire Laser au Fauteuil',
    caption: '✨ Transformation spectaculaire pour notre patient après une seule séance de blanchiment laser de 45 minutes en cabinet !\n\n...\n\n💰 Tarifs transparents en DZD et facilités de paiement. Contactez-nous sur WhatsApp pour votre devis !',
    hashtags: ['#BlanchimentDentaire', '#EsthetiqueDentaire', '#DentisteDZ', '#SourireEclatant'],
    image_url: 'https://images.unsplash.com/photo-1588776814546-1ffcf47267a5?auto=format&fit=crop&w=1000&q=80',
    status: 'waiting_approval',
    scheduled_for: 'Jeudi à 14h30',
    ai_notes: 'Dr. Mokhtar AI : Focus : Esthétique du sourire et conversion WhatsApp.',
    created_at: new Date().toISOString()
  },
  {
    id: 'post-seed-3',
    platform: 'instagram',
    title: 'Tout Savoir sur les Implants Dentaires en Zircone',
    caption: "🦷 Remplacer une dent manquante n'a jamais été aussi durable et naturel.\n\nPourquoi choisir l'implant en zircone ?...\n\n✨ Protocole chirurgical guidé et anesthésie douce au cabinet du Dr. Mokhtar.",
    hashtags: ['#ImplantDentaire', '#ChirurgieDentaire', '#Zircone', '#CabinetDentaire'],
    image_url: 'https://images.unsplash.com/photo-1629909613654-28e377c37b09?auto=format&fit=crop&w=1000&q=80',
    status: 'published',
    scheduled_for: 'Publié hier',
    metrics: { reach: 4820, likes: 312 },
    ai_notes: 'Publication validée par le Dr. Mokhtar.',
    created_at: new Date().toISOString()
  }
]

export function useSocialAutomation() {
  const posts = useState<SocialPost[]>('social_posts', () => [...EXACT_SEED_POSTS])
  const pinnedPostIds = useState<Set<string>>('pinned_social_post_ids', () => new Set())
  
  const n8nApproveUrl = useState<string>('n8n_approve_url', () => {
    if (import.meta.client) return localStorage.getItem('n8n_approve_url') || ''
    return ''
  })
  const n8nCreateUrl = useState<string>('n8n_create_url', () => {
    if (import.meta.client) return localStorage.getItem('n8n_create_url') || ''
    return ''
  })

  const toast = useToast()
  const { t } = useI18n()
  const api = useApi()

  function loadPinnedState() {
    if (import.meta.client) {
      try {
        const saved = localStorage.getItem('pinned_social_posts')
        if (saved) {
          const ids = JSON.parse(saved)
          pinnedPostIds.value = new Set(ids)
        }
      } catch {}
    }
  }

  function savePinnedState() {
    if (import.meta.client) {
      try {
        localStorage.setItem('pinned_social_posts', JSON.stringify(Array.from(pinnedPostIds.value)))
      } catch {}
    }
  }

  async function fetchPosts() {
    loadPinnedState()
    try {
      const data = await api.get<SocialPost[]>('/api/v1/social_automation/posts')
      if (Array.isArray(data) && data.length > 0) {
        const existingIds = new Set(data.map(p => p.id))
        const remainingSeeds = EXACT_SEED_POSTS.filter(s => !existingIds.has(s.id))
        const all = [...data, ...remainingSeeds].map(p => ({
          ...p,
          is_pinned: pinnedPostIds.value.has(p.id)
        }))
        posts.value = all.sort((a, b) => {
          if (a.is_pinned && !b.is_pinned) return -1
          if (!a.is_pinned && b.is_pinned) return 1
          return 0
        })
      }
    } catch {
      // Fallback: apply pinned state to existing posts
      posts.value = posts.value.map(p => ({
        ...p,
        is_pinned: pinnedPostIds.value.has(p.id)
      })).sort((a, b) => {
        if (a.is_pinned && !b.is_pinned) return -1
        if (!a.is_pinned && b.is_pinned) return 1
        return 0
      })
    }
  }

  function togglePinPost(postId: string) {
    const post = posts.value.find(p => p.id === postId)
    if (!post) return

    post.is_pinned = !post.is_pinned
    if (post.is_pinned) {
      pinnedPostIds.value.add(postId)
      toast.add({
        title: 'Publication Épinglée 📌',
        description: `"${post.title}" reste en tête de liste et restera toujours réutilisable/re-publiable.`,
        color: 'amber'
      })
    } else {
      pinnedPostIds.value.delete(postId)
      toast.add({
        title: 'Publication Désépinglée',
        description: `"${post.title}" suit désormais le cycle de publication standard.`,
        color: 'gray'
      })
    }
    savePinnedState()

    // Re-sort so pinned items rise to top
    posts.value = [...posts.value].sort((a, b) => {
      if (a.is_pinned && !b.is_pinned) return -1
      if (!a.is_pinned && b.is_pinned) return 1
      return 0
    })
  }

  async function approvePost(postId: string) {
    const post = posts.value.find(p => p.id === postId)
    if (!post) return

    // If NOT pinned, mark as published. If pinned, preserve it as reusable template!
    if (!post.is_pinned) {
      post.status = 'published'
      try {
        await api.patch(`/api/v1/social_automation/posts/${postId}`, {
          status: 'published'
        })
      } catch {}
    }

    const targetWebhook = post.approval_webhook_url || n8nApproveUrl.value
    if (targetWebhook) {
      try {
        await $fetch(targetWebhook, {
          method: 'POST',
          body: {
            event: 'post_approved',
            decision: 'Approuver & Publier sur les Réseaux',
            approved: true,
            mediaUrl: post.image_url,
            caption: post.caption,
            title: post.title,
            post
          }
        })
      } catch {}
    }

    toast.add({
      title: post.is_pinned ? 'Transmis à n8n (Modèle Épinglé conservé) 📌🚀' : 'Publication Transmise à n8n ! 🚀',
      description: post.is_pinned
        ? `Le post "${post.title}" a été envoyé aux réseaux et reste actif dans votre studio pour réutilisation future.`
        : `Le post "${post.title}" a été approuvé et envoyé aux réseaux sociaux.`,
      color: 'green'
    })
  }

  async function updatePostLocally(postId: string, feedback: string, newCaption: string) {
    const post = posts.value.find(p => p.id === postId)
    if (!post) return

    post.caption = newCaption
    post.feedback = feedback
    post.status = 'waiting_approval'

    try {
      await api.patch(`/api/v1/social_automation/posts/${postId}`, {
        status: 'waiting_approval',
        caption: newCaption,
        feedback: feedback
      })
    } catch {}

    if (n8nCreateUrl.value) {
      try {
        $fetch(n8nCreateUrl.value, {
          method: 'POST',
          body: {
            topic: post.title,
            instructions: `Modification demandée par Dr. Mokhtar: ${feedback}. Texte: ${newCaption}`
          }
        }).catch(() => {})
      } catch {}
    }

    toast.add({
      title: 'Publication Modifiée avec Succès ✨',
      description: 'Le texte a été mis à jour et réaligné sur vos instructions.',
      color: 'blue'
    })
  }

  async function deletePost(postId: string) {
    const index = posts.value.findIndex(p => p.id === postId)
    if (index !== -1) {
      const post = posts.value[index]
      posts.value.splice(index, 1)
      pinnedPostIds.value.delete(postId)
      savePinnedState()

      try {
        await api.delete(`/api/v1/social_automation/posts/${postId}`)
      } catch {
        try {
          await api.patch(`/api/v1/social_automation/posts/${postId}`, {
            status: 'rejected'
          })
        } catch {}
      }

      toast.add({
        title: 'Publication Supprimée 🗑️',
        description: `Le post "${post.title}" a été retiré du tableau de bord.`,
        color: 'gray'
      })
    }
  }

  const rejectPost = deletePost

  function createNewDraft(payload: {
    title?: string
    topic?: string
    caption?: string
    instructions?: string
    imageUrl?: string
    platform?: 'instagram' | 'facebook' | 'both'
    platforms?: string[]
    pillar?: string
    hashtags?: string[] | string
    cta?: string
  }) {
    const selectedPlatform = payload.platform || 'both'
    const targetPlatforms = payload.platforms || (
      selectedPlatform === 'both' ? ['facebook', 'instagram'] : [selectedPlatform]
    )

    const resolvedTitle = payload.title?.trim() || (payload.pillar ? `${payload.pillar} au Cabinet Dr. Mokhtar` : 'Publication IA Cabinet Dentaire')
    const resolvedCaption = payload.caption?.trim() || (payload.instructions?.trim() ? `Instructions Dr. Mokhtar : ${payload.instructions}` : '🦷 Publication générée par l\'IA n8n selon les protocoles cliniques du cabinet.')

    const newPost: SocialPost = {
      id: `post-${Date.now()}`,
      platform: (selectedPlatform === 'both' ? 'instagram' : selectedPlatform) as any,
      title: resolvedTitle,
      caption: resolvedCaption,
      hashtags: ['#DentisteAlger', '#DrMokhtar', '#SanteDentaire', '#CabinetDentaire'],
      image_url: payload.imageUrl || 'https://images.unsplash.com/photo-1629909613654-28e377c37b09?auto=format&fit=crop&w=1000&q=80',
      status: 'waiting_approval',
      scheduled_for: 'Demain à 10h00',
      ai_notes: `Généré automatiquement par Dr. Mokhtar AI — Pilier: ${payload.pillar || 'Soins Généraux'}. Réseaux cibles: ${targetPlatforms.join(', ')}.`,
      created_at: new Date().toISOString()
    }

    posts.value.unshift(newPost)

    if (n8nCreateUrl.value) {
      try {
        $fetch(n8nCreateUrl.value, {
          method: 'POST',
          body: {
            platforms: targetPlatforms,
            pillar: payload.pillar || undefined,
            title: payload.title?.trim() || undefined,
            topic: payload.title?.trim() || payload.topic?.trim() || undefined,
            content: payload.caption?.trim() || undefined,
            custom_content: payload.caption?.trim() || undefined,
            instructions: payload.instructions?.trim() || payload.caption?.trim() || undefined,
            image_url: payload.imageUrl?.trim() || undefined,
            imageSource: payload.imageUrl?.trim() ? 'custom' : 'pollinations',
            hashtags: payload.hashtags || undefined,
            cta: payload.cta?.trim() || undefined,
            content_mode: (payload.title?.trim() || payload.caption?.trim()) ? 'doctor_copilot' : 'ai_autonomous'
          }
        }).catch((err) => {
          console.warn('n8n Create Draft notice:', err)
        })
      } catch {}
    }

    toast.add({
      title: 'Publication Transmise à l\'IA n8n ! ⚡',
      description: `Génération lancée pour ${targetPlatforms.join(' & ')}.`,
      color: 'green'
    })
  }

  function setN8nUrls(approveUrl: string, createUrl: string) {
    n8nApproveUrl.value = approveUrl.trim()
    n8nCreateUrl.value = createUrl.trim()
    if (import.meta.client) {
      localStorage.setItem('n8n_approve_url', approveUrl.trim())
      localStorage.setItem('n8n_create_url', createUrl.trim())
    }
    toast.add({
      title: 'Configuration n8n Enregistrée ! ⚡',
      description: 'Vos webhooks n8n sont connectés en direct au tableau de bord.',
      color: 'green'
    })
  }

  return {
    posts,
    n8nApproveUrl,
    n8nCreateUrl,
    fetchPosts,
    approvePost,
    updatePostLocally,
    rejectPost,
    deletePost,
    togglePinPost,
    createNewDraft,
    setN8nUrls
  }
}
