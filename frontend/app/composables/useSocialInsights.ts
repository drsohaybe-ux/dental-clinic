import { computed } from 'vue'

export interface InsightRecord {
  id?: number | string
  platform: 'instagram' | 'facebook'
  account_id: string
  date: string // YYYY-MM-DD
  total_followers: number
  reach: number
  profile_views: number
  website_clicks: number
  saves: number
  created_at?: string
}

export type PlatformFilter = 'all' | 'instagram' | 'facebook'
export type DateRangeFilter = '7d' | '30d' | '90d' | 'all'

/**
 * Generate 30 days of realistic demo records for Instagram and Facebook
 */
function generateRealisticDemoRecords(): InsightRecord[] {
  const records: InsightRecord[] = []
  const now = new Date()

  // Instagram baseline: 3,420 growing to ~3,580
  let igFollowers = 3420
  // Facebook baseline: 5,120 growing to ~5,240
  let fbFollowers = 5120

  for (let i = 29; i >= 0; i--) {
    const d = new Date(now)
    d.setDate(d.getDate() - i)
    const dateStr = d.toISOString().split('T')[0]!

    // Day of week factor: weekends have higher reach
    const dayOfWeek = d.getDay()
    const weekendMultiplier = (dayOfWeek === 0 || dayOfWeek === 6) ? 1.35 : 1.0

    // Instagram daily stats
    const igFollowerInc = Math.floor(4 + Math.random() * 8)
    igFollowers += igFollowerInc
    const igReach = Math.floor((1400 + Math.random() * 1600) * weekendMultiplier)
    const igViews = Math.floor(igReach * (0.045 + Math.random() * 0.025))
    const igClicks = Math.floor(igViews * (0.18 + Math.random() * 0.12))
    const igSaves = Math.floor(igClicks * (0.6 + Math.random() * 0.5))

    records.push({
      id: `demo-ig-${i}`,
      platform: 'instagram',
      account_id: 'dr_mokhtar_dental',
      date: dateStr,
      total_followers: igFollowers,
      reach: igReach,
      profile_views: igViews,
      website_clicks: igClicks,
      saves: igSaves
    })

    // Facebook daily stats
    const fbFollowerInc = Math.floor(2 + Math.random() * 6)
    fbFollowers += fbFollowerInc
    const fbReach = Math.floor((850 + Math.random() * 950) * weekendMultiplier)
    const fbViews = Math.floor(fbReach * (0.035 + Math.random() * 0.02))
    const fbClicks = Math.floor(fbViews * (0.22 + Math.random() * 0.14))
    const fbSaves = Math.floor(fbClicks * (0.3 + Math.random() * 0.3))

    records.push({
      id: `demo-fb-${i}`,
      platform: 'facebook',
      account_id: 'cabinet.dentaire.mokhtar',
      date: dateStr,
      total_followers: fbFollowers,
      reach: fbReach,
      profile_views: fbViews,
      website_clicks: fbClicks,
      saves: fbSaves
    })
  }

  return records
}

const DEMO_RECORDS: InsightRecord[] = generateRealisticDemoRecords()

export function useSocialInsights() {
  const toast = useToast()

  const liveRecords = useState<InsightRecord[]>('social_insights:live_records', () => [])
  const isDemoMode = useState<boolean>('social_insights:is_demo_mode', () => true)
  const isLoading = useState<boolean>('social_insights:is_loading', () => false)
  const isSyncing = useState<boolean>('social_insights:is_syncing', () => false)
  const activePlatform = useState<PlatformFilter>('social_insights:active_platform', () => 'all')
  const activeDateRange = useState<DateRangeFilter>('social_insights:active_date_range', () => '30d')
  const lastSyncAt = useState<string | null>('social_insights:last_sync_at', () => null)
  const fetchError = useState<string | null>('social_insights:fetch_error', () => null)

  const hasLiveRecords = computed(() => liveRecords.value.length > 0)

  // Active pool of records: demo or live
  const activeRecordsPool = computed<InsightRecord[]>(() => {
    if (isDemoMode.value || liveRecords.value.length === 0) {
      return DEMO_RECORDS
    }
    return liveRecords.value
  })

  // Date filtering logic
  const filteredRecords = computed<InsightRecord[]>(() => {
    const pool = activeRecordsPool.value
    const now = new Date()

    let cutoffDate: Date | null = null
    if (activeDateRange.value === '7d') {
      cutoffDate = new Date(now)
      cutoffDate.setDate(cutoffDate.getDate() - 7)
    } else if (activeDateRange.value === '30d') {
      cutoffDate = new Date(now)
      cutoffDate.setDate(cutoffDate.getDate() - 30)
    } else if (activeDateRange.value === '90d') {
      cutoffDate = new Date(now)
      cutoffDate.setDate(cutoffDate.getDate() - 90)
    }

    return pool
      .filter((r) => {
        // Platform filter
        if (activePlatform.value !== 'all' && r.platform !== activePlatform.value) {
          return false
        }
        // Date filter
        if (cutoffDate) {
          const recDate = new Date(r.date)
          if (recDate < cutoffDate) return false
        }
        return true
      })
      .sort((a, b) => b.date.localeCompare(a.date))
  })

  // Latest snapshot per platform
  const latestInstagram = computed<InsightRecord | null>(() => {
    const list = activeRecordsPool.value
      .filter(r => r.platform === 'instagram')
      .sort((a, b) => b.date.localeCompare(a.date))
    return list[0] || null
  })

  const latestFacebook = computed<InsightRecord | null>(() => {
    const list = activeRecordsPool.value
      .filter(r => r.platform === 'facebook')
      .sort((a, b) => b.date.localeCompare(a.date))
    return list[0] || null
  })

  // Summary KPI Metrics
  const summaryMetrics = computed(() => {
    const list = filteredRecords.value

    const igSnap = latestInstagram.value
    const fbSnap = latestFacebook.value

    let totalFollowers = 0
    if (activePlatform.value === 'all') {
      totalFollowers = (igSnap?.total_followers || 0) + (fbSnap?.total_followers || 0)
    } else if (activePlatform.value === 'instagram') {
      totalFollowers = igSnap?.total_followers || 0
    } else {
      totalFollowers = fbSnap?.total_followers || 0
    }

    // Follower growth calculation
    let followerGrowth = 0
    if (list.length >= 2) {
      const byPlatform = {
        instagram: list.filter(r => r.platform === 'instagram'),
        facebook: list.filter(r => r.platform === 'facebook')
      }

      if (activePlatform.value === 'all' || activePlatform.value === 'instagram') {
        const ig = byPlatform.instagram
        if (ig.length >= 2) {
          followerGrowth += (ig[0]?.total_followers || 0) - (ig[ig.length - 1]?.total_followers || 0)
        }
      }
      if (activePlatform.value === 'all' || activePlatform.value === 'facebook') {
        const fb = byPlatform.facebook
        if (fb.length >= 2) {
          followerGrowth += (fb[0]?.total_followers || 0) - (fb[fb.length - 1]?.total_followers || 0)
        }
      }
    }

    const totalReach = list.reduce((sum, r) => sum + (r.reach || 0), 0)
    const totalProfileViews = list.reduce((sum, r) => sum + (r.profile_views || 0), 0)
    const totalWebsiteClicks = list.reduce((sum, r) => sum + (r.website_clicks || 0), 0)
    const totalSaves = list.reduce((sum, r) => sum + (r.saves || 0), 0)

    const conversionRate = totalProfileViews > 0
      ? ((totalWebsiteClicks / totalProfileViews) * 100).toFixed(1)
      : '0.0'

    const distinctDays = new Set(list.map(r => r.date)).size || 1
    const avgDailyReach = Math.round(totalReach / distinctDays)

    return {
      totalFollowers,
      followerGrowth,
      totalReach,
      avgDailyReach,
      totalProfileViews,
      totalWebsiteClicks,
      totalSaves,
      conversionRate
    }
  })

  // Chart trend points
  const chartTrendPoints = computed(() => {
    // Group records by date (chronological order)
    const map = new Map<string, { date: string, reach: number, views: number, clicks: number }>()

    const sortedAsc = [...filteredRecords.value].sort((a, b) => a.date.localeCompare(b.date))
    for (const r of sortedAsc) {
      const existing = map.get(r.date) || { date: r.date, reach: 0, views: 0, clicks: 0 }
      existing.reach += r.reach
      existing.views += r.profile_views
      existing.clicks += r.website_clicks
      map.set(r.date, existing)
    }

    return Array.from(map.values())
  })

  // Platform share breakdown
  const platformBreakdown = computed(() => {
    const list = filteredRecords.value
    const igRecords = list.filter(r => r.platform === 'instagram')
    const fbRecords = list.filter(r => r.platform === 'facebook')

    const igReach = igRecords.reduce((sum, r) => sum + r.reach, 0)
    const fbReach = fbRecords.reduce((sum, r) => sum + r.reach, 0)
    const totalReach = igReach + fbReach || 1

    const igClicks = igRecords.reduce((sum, r) => sum + r.website_clicks, 0)
    const fbClicks = fbRecords.reduce((sum, r) => sum + r.website_clicks, 0)
    const totalClicks = igClicks + fbClicks || 1

    return {
      instagram: {
        followers: latestInstagram.value?.total_followers || 0,
        reach: igReach,
        reachPct: Math.round((igReach / totalReach) * 100),
        clicks: igClicks,
        clicksPct: Math.round((igClicks / totalClicks) * 100)
      },
      facebook: {
        followers: latestFacebook.value?.total_followers || 0,
        reach: fbReach,
        reachPct: Math.round((fbReach / totalReach) * 100),
        clicks: fbClicks,
        clicksPct: Math.round((fbClicks / totalClicks) * 100)
      }
    }
  })

  /**
   * Fetch insights from backend or edge API.
   * Completely resilient: NEVER spams error toasts on page load or when n8n hasn't sent data yet.
   */
  async function fetchInsights(showNotification = false): Promise<void> {
    isLoading.value = true
    fetchError.value = null

    try {
      let res: unknown = null
      const config = useRuntimeConfig()
      const auth = useAuth()
      const authHeader = auth.accessToken.value ? { Authorization: `Bearer ${auth.accessToken.value}` } : {}

      // 1. Try Nitro edge route first (safely proxies to backend or returns clean fallback)
      try {
        res = await $fetch('/api/automation/insights?days=90', {
          headers: authHeader,
          timeout: 3000
        })
      } catch {
        // 2. Fallback directly to FastAPI backend with direct $fetch (avoiding useApi global toast interceptor)
        const apiBaseUrl = import.meta.server ? config.apiBaseUrlServer : config.public.apiBaseUrl
        if (apiBaseUrl) {
          try {
            res = await $fetch(`${apiBaseUrl}/api/v1/social_automation/insights?days=90`, {
              headers: authHeader,
              timeout: 3000
            })
          } catch {
            res = null
          }
        }
      }

      const resObj = (res && typeof res === 'object') ? (res as Record<string, unknown>) : null
      const incomingList = Array.isArray(res)
        ? (res as Array<Record<string, unknown>>)
        : (resObj?.data && Array.isArray(resObj.data) ? (resObj.data as Array<Record<string, unknown>>) : [])

      if (incomingList.length > 0) {
        liveRecords.value = incomingList.map(item => ({
          id: item.id as string | number | undefined,
          platform: item.platform as 'instagram' | 'facebook',
          account_id: (item.account_id as string) || 'default',
          date: typeof item.date === 'string' ? item.date.slice(0, 10) : String(item.date),
          total_followers: Number(item.total_followers) || 0,
          reach: Number(item.reach) || 0,
          profile_views: Number(item.profile_views) || 0,
          website_clicks: Number(item.website_clicks) || 0,
          saves: Number(item.saves) || 0,
          created_at: item.created_at as string | undefined
        }))
        isDemoMode.value = false
        lastSyncAt.value = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })

        if (showNotification) {
          toast.add({
            title: 'Statistiques Synchronisées ! 🚀',
            description: `${incomingList.length} instantanés quotidiens chargés depuis la base de données.`,
            color: 'success'
          })
        }
      } else {
        // No live records yet — keep demo mode active so the UI is never blank
        liveRecords.value = []
        isDemoMode.value = true
        lastSyncAt.value = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })

        if (showNotification) {
          toast.add({
            title: 'En Attente de Données n8n ⏳',
            description: 'Aucune donnée n8n enregistrée pour le moment. Affichage du Mode Démo / Aperçu.',
            color: 'info'
          })
        }
      }
    } catch (err) {
      fetchError.value = err instanceof Error ? err.message : 'Connexion indisponible'
      // Fail gracefully: ensure demo mode is available
      if (liveRecords.value.length === 0) {
        isDemoMode.value = true
      }
      if (showNotification) {
        toast.add({
          title: 'Mode Démo Actif',
          description: 'Aperçu des performances avec métriques simulées.',
          color: 'neutral'
        })
      }
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Sync trigger simulation (calls fetch)
   */
  async function syncFromN8n(): Promise<void> {
    isSyncing.value = true
    try {
      await fetchInsights(true)
    } finally {
      isSyncing.value = false
    }
  }

  /**
   * Seed backend database with realistic demo data
   */
  async function seedBackendDemoData(): Promise<void> {
    isLoading.value = true
    try {
      let seeded = false
      const config = useRuntimeConfig()
      const auth = useAuth()
      const apiBaseUrl = import.meta.server ? config.apiBaseUrlServer : config.public.apiBaseUrl
      const authHeader = auth.accessToken.value ? { Authorization: `Bearer ${auth.accessToken.value}` } : {}

      // Try seeding backend directly
      if (apiBaseUrl) {
        try {
          const res = await $fetch<Record<string, unknown>>(`${apiBaseUrl}/api/v1/social_automation/insights/seed`, {
            method: 'POST',
            headers: authHeader,
            timeout: 3000
          })
          if (res && res.success !== false && (Number(res.count) > 0 || Number(res.processed_count) > 0)) {
            seeded = true
          }
        } catch {
          seeded = false
        }
      }

      if (seeded) {
        await fetchInsights(false)
        isDemoMode.value = false
        toast.add({
          title: 'Données de Test Injectées ! 📊',
          description: '30 jours d\'historique Instagram et Facebook ont été enregistrés dans la base.',
          color: 'success'
        })
      } else {
        // Backend unavailable or table unmigrated: activate demo mode locally
        isDemoMode.value = true
        toast.add({
          title: 'Mode Démo Local Actif 💡',
          description: 'Base de données non initialisée. 30 jours de données simulées sont affichés en mode aperçu.',
          color: 'info'
        })
      }
    } catch {
      isDemoMode.value = true
      toast.add({
        title: 'Mode Démo Actif',
        description: 'Visualisation des statistiques simulées.',
        color: 'neutral'
      })
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Toggle between Demo Mode and Live Mode
   */
  function toggleDemoMode(): void {
    isDemoMode.value = !isDemoMode.value
    toast.add({
      title: isDemoMode.value ? 'Mode Démo Activé ✨' : 'Mode Données Réelles Activé 📡',
      description: isDemoMode.value
        ? 'Vous visualisez un aperçu complet avec des données simulées.'
        : 'Affichage des données transmises par votre workflow n8n.',
      color: isDemoMode.value ? 'neutral' : 'primary'
    })
  }

  /**
   * Export filtered records as CSV
   */
  function exportToCsv(): void {
    if (typeof window === 'undefined' || !window.URL?.createObjectURL) {
      return
    }

    const records = filteredRecords.value
    if (!records.length) return

    const headers = ['Date', 'Plateforme', 'Abonnes', 'Portee', 'Visites_Profil', 'Clics_Site_Web', 'Enregistrements']
    const rows = records.map(r => [
      r.date,
      r.platform,
      r.total_followers,
      r.reach,
      r.profile_views,
      r.website_clicks,
      r.saves
    ])

    const csvContent = '\uFEFF' + [headers.join(','), ...rows.map(row => row.join(','))].join('\n')
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `rapport_social_media_${activePlatform.value}_${new Date().toISOString().split('T')[0]}.csv`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)

    toast.add({
      title: 'Exportation CSV Terminée 📥',
      description: 'Le fichier du rapport a été téléchargé avec succès.',
      color: 'success'
    })
  }

  /**
   * Export filtered records as JSON
   */
  function exportToJson(): void {
    if (typeof window === 'undefined' || !window.URL?.createObjectURL) {
      return
    }

    const records = filteredRecords.value
    if (!records.length) return

    const jsonStr = JSON.stringify(records, null, 2)
    const blob = new Blob([jsonStr], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `rapport_social_media_${activePlatform.value}_${new Date().toISOString().split('T')[0]}.json`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)

    toast.add({
      title: 'Exportation JSON Terminée 📥',
      description: 'Données exportées au format JSON.',
      color: 'success'
    })
  }

  return {
    liveRecords,
    isDemoMode,
    isLoading,
    isSyncing,
    activePlatform,
    activeDateRange,
    lastSyncAt,
    fetchError,
    hasLiveRecords,
    filteredRecords,
    latestInstagram,
    latestFacebook,
    summaryMetrics,
    chartTrendPoints,
    platformBreakdown,
    fetchInsights,
    syncFromN8n,
    seedBackendDemoData,
    toggleDemoMode,
    exportToCsv,
    exportToJson
  }
}
