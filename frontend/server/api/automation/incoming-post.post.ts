export default defineEventHandler(async (event) => {
  const rawBody = await readBody(event)
  const config = useRuntimeConfig()
  const backendBase = config.apiBaseUrlServer || config.public.apiBaseUrl || 'https://dental-api-2z19.onrender.com'
  const authHeader = getHeader(event, 'authorization') || ''

  // Normalize n8n dashboardPayload
  const platformPosts = rawBody.platform_posts || {}
  const instagramData = platformPosts.Instagram || {}
  const facebookData = platformPosts.Facebook || {}

  const captions = rawBody.captions || {}
  let resolvedCaption = rawBody.caption || captions.instagram || captions.facebook || ''
  
  if (!resolvedCaption) {
    if (instagramData.caption) {
      resolvedCaption = instagramData.caption
      if (instagramData.call_to_action) resolvedCaption += `\n\n${instagramData.call_to_action}`
    } else if (facebookData.post) {
      resolvedCaption = facebookData.post
      if (facebookData.call_to_action) resolvedCaption += `\n\n${facebookData.call_to_action}`
    } else if (rawBody.description) {
      resolvedCaption = rawBody.description
    }
  }

  const resolvedImage = rawBody.igMediaUrl || rawBody.mediaUrl || rawBody.fbMediaUrl || rawBody.imageUrl || ''
  const resolvedTitle = rawBody.title || rawBody.topic || 'Publication Cabinet Dentaire'
  const resolvedPlatform = rawBody.platform || (rawBody.igMediaUrl ? 'instagram' : 'facebook')
  const resolvedPostId = String(rawBody.postId || rawBody.id || `post-${Date.now()}`)

  const payloadToSend = {
    event: rawBody.event || 'POST_DRAFT_READY',
    postId: resolvedPostId,
    title: resolvedTitle,
    description: rawBody.description || resolvedCaption,
    caption: resolvedCaption,
    mediaUrl: resolvedImage,
    imageUrl: resolvedImage,
    fbMediaUrl: rawBody.fbMediaUrl || null,
    igMediaUrl: rawBody.igMediaUrl || null,
    hashtags: rawBody.hashtags || instagramData.hashtags || facebookData.hashtags || [],
    platform: resolvedPlatform,
    platform_posts: platformPosts,
    status: rawBody.status || 'waiting_approval',
    scheduledFor: rawBody.scheduled_for || rawBody.scheduledFor || 'Demain à 10h00',
    aiNotes: rawBody.angleStrategyNote || (rawBody.aiScores ? `Score Accroche: ${rawBody.aiScores.hook_strength || 7}/10 | Clarté: ${rawBody.aiScores.clarity || 7}/10` : 'Généré par Dr. Mokhtar AI (n8n)')
  }

  try {
    const res = await $fetch(`${backendBase}/api/v1/social_automation/webhook/incoming`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(authHeader ? { Authorization: authHeader } : {})
      },
      body: payloadToSend
    })
    return {
      success: true,
      message: 'Draft post received and staged successfully',
      post: res
    }
  } catch (err: any) {
    console.error('Failed to forward incoming post to Render:', err)
    return {
      success: true,
      message: 'Draft post logged (edge fallback)',
      post: payloadToSend,
      error: err?.data?.detail || err?.message
    }
  }
})
