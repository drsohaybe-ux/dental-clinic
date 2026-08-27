import { defineStore } from 'pinia'

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

export const useSocialAutomation = defineStore('socialAutomation', () => {
  const posts = ref<SocialPost[]>([])
  const n8nApproveUrl = useLocalStorage('n8n_approve_url', '')
  const n8nCreateUrl = useLocalStorage('n8n_create_url', '')

  const toast = useToast()
  const { t } = useI18n()
  const api = useApi() // Assuming Nuxt app has a useApi composable, otherwise use $fetch

  async function fetchPosts() {
    try {
      const data = await api.get('/api/social-automation/posts')
      posts.value = data
    } catch (err) {
      console.error('Failed to fetch posts', err)
      toast.add({ title: t('error'), color: 'red' })
    }
  }

  async function approvePost(postId: string) {
    const post = posts.value.find(p => p.id === postId)
    if (!post) return

    try {
      // 1. Mark as approved in our Database via our API
      const updatedPost = await api.patch(`/api/social-automation/posts/${postId}`, {
        status: 'approved'
      })
      post.status = 'approved'

      // 2. Trigger n8n actual publishing webhook
      const targetWebhook = post.approval_webhook_url || n8nApproveUrl.value
      if (targetWebhook) {
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
      }

      toast.add({
        title: t('social.toast.approved_title'),
        description: t('social.toast.approved_desc', { title: post.title }),
        color: 'green'
      })
    } catch (err) {
      toast.add({ title: t('error'), description: t('social.toast.webhook_failed'), color: 'red' })
    }
  }

  async function updatePostLocally(postId: string, feedback: string, newCaption: string) {
    const post = posts.value.find(p => p.id === postId)
    if (!post) return

    try {
      await api.patch(`/api/social-automation/posts/${postId}`, {
        status: 'waiting_approval',
        caption: newCaption,
        feedback: feedback
      })
      
      post.caption = newCaption
      post.feedback = feedback
      post.status = 'waiting_approval'

      toast.add({
        title: t('social.toast.updated_title'),
        color: 'blue'
      })
    } catch (err) {
      toast.add({ title: t('error'), color: 'red' })
    }
  }

  async function rejectPost(postId: string) {
    const post = posts.value.find(p => p.id === postId)
    if (!post) return

    try {
      await api.patch(`/api/social-automation/posts/${postId}`, {
        status: 'rejected'
      })
      post.status = 'rejected'
      toast.add({ title: t('social.toast.rejected'), color: 'gray' })
    } catch (err) {
      toast.add({ title: t('error'), color: 'red' })
    }
  }

  function setN8nUrls(approveUrl: string, createUrl: string) {
    n8nApproveUrl.value = approveUrl.trim()
    n8nCreateUrl.value = createUrl.trim()
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
    setN8nUrls
  }
})
