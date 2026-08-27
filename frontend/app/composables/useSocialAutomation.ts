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
  approval_webhook_url?: string
  created_at: string
}

const DEFAULT_POSTS: SocialPost[] = [
  {
    id: 'post-seed-1',
    platform: 'instagram',
    title: 'Blanchiment Dentaire au Fauteuil ✨',
    caption: '🦷 Retrouvez l\'éclat naturel de votre sourire en 1 seule séance au cabinet du Dr. Mokhtar !\n\n✨ Protocole laser sans douleur avec des résultats visibles immédiatement.\n💰 Tarifs transparents en DZD. Prenez rendez-vous dès aujourd\'hui par message privé WhatsApp !',
    hashtags: ['#DentisteAlger', '#DrMokhtar', '#BlanchimentDentaire', '#SourireEclatant', '#SanteDentaire'],
    image_url: 'https://images.unsplash.com/photo-1606811841689-23dfddce3e95?auto=format&fit=crop&w=1000&q=80',
    status: 'waiting_approval',
    scheduled_for: 'Demain à 10h00',
    ai_notes: 'Généré automatiquement par Dr. Mokhtar AI (n8n) — Focus esthétique et tarifs DZD.',
    created_at: new Date().toISOString()
  },
  {
    id: 'post-seed-2',
    platform: 'facebook',
    title: 'Alignement Invisible & Orthodontie Moderne 🦷',
    caption: 'Transformez votre sourire en toute discrétion grâce à nos gouttières transparentes.\n\n👨‍⚕️ Le Dr. Mokhtar vous accompagne pour un plan de traitement sur-mesure adapté à votre rythme de vie.\n\n📍 Cabinet situé à Alger. Facilités de paiement disponibles.',
    hashtags: ['#OrthodontieInvisible', '#AlignersDZ', '#CabinetDentaireAlger', '#DrMokhtar'],
    image_url: 'https://images.unsplash.com/photo-1588776814546-1ffcf47267a5?auto=format&fit=crop&w=1000&q=80',
    status: 'waiting_approval',
    scheduled_for: 'Vendredi à 14h30',
    ai_notes: 'Généré par n8n — Pilier: Traitements Modernes & Orthodontie.',
    created_at: new Date().toISOString()
  },
  {
    id: 'post-seed-3',
    platform: 'instagram',
    title: 'Implants Dentaires : Retrouvez Votre Confort',
    caption: 'Une solution pérenne, naturelle et indolore pour remplacer vos dents manquantes.\n\n🦷 Chirurgie guidée par ordinateur et matériaux certifiés haute biocompatibilité.\n\n📲 Réservez votre consultation bilan sur WhatsApp.',
    hashtags: ['#ImplantDentaire', '#ChirurgieDentaire', '#DentisteAlgerie', '#DrMokhtar'],
    image_url: 'https://images.unsplash.com/photo-1629909613654-28e377c37b09?auto=format&fit=crop&w=1000&q=80',
    status: 'approved',
    scheduled_for: 'Publié récemment',
    ai_notes: 'Publication validée par le Dr. Mokhtar.',
    created_at: new Date().toISOString()
  }
]

export function useSocialAutomation() {
  const posts = useState<SocialPost[]>('social_posts', () => [...DEFAULT_POSTS])
  
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

  async function fetchPosts() {
    try {
      const data = await api.get<SocialPost[]>('/api/v1/social_automation/posts')
      if (Array.isArray(data) && data.length > 0) {
        posts.value = data
      }
    } catch {
      // Backend is ready or using seed fallback gracefully
    }
  }

  async function approvePost(postId: string) {
    const post = posts.value.find(p => p.id === postId)
    if (!post) return

    post.status = 'approved'

    // Try backend persistence
    try {
      await api.patch(`/api/v1/social_automation/posts/${postId}`, {
        status: 'approved'
      })
    } catch {}

    // Trigger n8n actual publishing webhook
    const targetWebhook = post.approval_webhook_url || n8nApproveUrl.value
    if (targetWebhook) {
      try {
        await $fetch(targetWebhook, {
          method: 'POST',
          body: {
            event: 'post_approved',
            decision: t('social.decision.approve_publish'),
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
      title: t('social.toast.approved_title'),
      description: t('social.toast.approved_desc', { title: post.title }),
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

    // Trigger n8n revision webhook if set
    if (n8nCreateUrl.value) {
      try {
        $fetch(n8nCreateUrl.value, {
          method: 'POST',
          body: {
            topic: post.title,
            instructions: `Modification demandée : ${feedback}. Texte précédent : ${newCaption}`
          }
        }).catch(() => {})
      } catch {}
    }

    toast.add({
      title: t('social.toast.updated_title'),
      color: 'blue'
    })
  }

  async function rejectPost(postId: string) {
    const post = posts.value.find(p => p.id === postId)
    if (!post) return

    post.status = 'rejected'
    try {
      await api.patch(`/api/v1/social_automation/posts/${postId}`, {
        status: 'rejected'
      })
    } catch {}

    toast.add({ title: t('social.toast.rejected'), color: 'gray' })
  }

  function createNewDraft(payload: { title: string; caption: string; imageUrl?: string; platform?: string }) {
    const newPost: SocialPost = {
      id: `post-${Date.now()}`,
      platform: (payload.platform as any) || 'instagram',
      title: payload.title,
      caption: payload.caption,
      hashtags: ['#DentisteAlger', '#DrMokhtar', '#SanteDentaire'],
      image_url: payload.imageUrl || 'https://images.unsplash.com/photo-1606811841689-23dfddce3e95?auto=format&fit=crop&w=1000&q=80',
      status: 'waiting_approval',
      scheduled_for: 'Demain à 10h00',
      ai_notes: 'Créé via le studio de validation',
      created_at: new Date().toISOString()
    }
    posts.value.unshift(newPost)
    toast.add({ title: 'Nouvelle publication ajoutée !', color: 'green' })
  }

  function setN8nUrls(approveUrl: string, createUrl: string) {
    n8nApproveUrl.value = approveUrl.trim()
    n8nCreateUrl.value = createUrl.trim()
    if (import.meta.client) {
      localStorage.setItem('n8n_approve_url', approveUrl.trim())
      localStorage.setItem('n8n_create_url', createUrl.trim())
    }
    toast.add({
      title: t('social.toast.config_saved'),
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
    createNewDraft,
    setN8nUrls
  }
}
