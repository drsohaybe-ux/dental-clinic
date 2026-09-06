import { mountSuspended } from '@nuxt/test-utils/runtime'
import { describe, expect, it } from 'vitest'
import { defineComponent, h } from 'vue'

async function runInSetup<T>(fn: () => T): Promise<T> {
  let captured!: T
  await mountSuspended(defineComponent({
    setup() {
      captured = fn()
      return () => h('div')
    }
  }))
  return captured
}

describe('useSocialInsights composable', () => {
  it('should export useSocialInsights function', async () => {
    const module = await import('~/composables/useSocialInsights')
    expect(module.useSocialInsights).toBeDefined()
    expect(typeof module.useSocialInsights).toBe('function')
  })

  it('should default to demo mode when no live records exist to prevent blank page', async () => {
    const { useSocialInsights } = await import('~/composables/useSocialInsights')
    const state = await runInSetup(() => useSocialInsights())

    expect(state.isDemoMode.value).toBe(true)
    expect(state.filteredRecords.value.length).toBeGreaterThan(0)
    expect(state.summaryMetrics.value.totalFollowers).toBeGreaterThan(0)
    expect(state.summaryMetrics.value.totalReach).toBeGreaterThan(0)
    expect(state.summaryMetrics.value.totalProfileViews).toBeGreaterThan(0)
    expect(state.summaryMetrics.value.totalWebsiteClicks).toBeGreaterThan(0)
  })

  it('should filter records properly by platform', async () => {
    const { useSocialInsights } = await import('~/composables/useSocialInsights')
    const state = await runInSetup(() => useSocialInsights())

    state.activePlatform.value = 'instagram'
    const igRecords = state.filteredRecords.value
    expect(igRecords.length).toBeGreaterThan(0)
    expect(igRecords.every(r => r.platform === 'instagram')).toBe(true)

    state.activePlatform.value = 'facebook'
    const fbRecords = state.filteredRecords.value
    expect(fbRecords.length).toBeGreaterThan(0)
    expect(fbRecords.every(r => r.platform === 'facebook')).toBe(true)

    state.activePlatform.value = 'all'
    const allRecords = state.filteredRecords.value
    expect(allRecords.some(r => r.platform === 'instagram')).toBe(true)
    expect(allRecords.some(r => r.platform === 'facebook')).toBe(true)
  })

  it('should filter records by date range', async () => {
    const { useSocialInsights } = await import('~/composables/useSocialInsights')
    const state = await runInSetup(() => useSocialInsights())

    state.activePlatform.value = 'all'
    state.activeDateRange.value = '7d'
    const recs7d = state.filteredRecords.value

    state.activeDateRange.value = '30d'
    const recs30d = state.filteredRecords.value

    expect(recs7d.length).toBeLessThanOrEqual(recs30d.length)
  })

  it('should calculate valid conversion rates and platform breakdown', async () => {
    const { useSocialInsights } = await import('~/composables/useSocialInsights')
    const state = await runInSetup(() => useSocialInsights())

    expect(Number(state.summaryMetrics.value.conversionRate)).toBeGreaterThan(0)
    expect(state.platformBreakdown.value.instagram.followers).toBeGreaterThan(0)
    expect(state.platformBreakdown.value.facebook.followers).toBeGreaterThan(0)
    expect(state.chartTrendPoints.value.length).toBeGreaterThan(0)
  })

  it('should toggle demo mode gracefully', async () => {
    const { useSocialInsights } = await import('~/composables/useSocialInsights')
    const state = await runInSetup(() => useSocialInsights())

    const initial = state.isDemoMode.value
    state.toggleDemoMode()
    expect(state.isDemoMode.value).toBe(!initial)
    state.toggleDemoMode()
    expect(state.isDemoMode.value).toBe(initial)
  })

  it('should handle fetchInsights gracefully without throwing or crashing when API is unavailable', async () => {
    const { useSocialInsights } = await import('~/composables/useSocialInsights')
    const state = await runInSetup(() => useSocialInsights())

    await expect(state.fetchInsights(false)).resolves.not.toThrow()
    expect(state.isLoading.value).toBe(false)
  }, 15000)

  it('should fallback to local demo mode on seedBackendDemoData when backend is unavailable', async () => {
    const { useSocialInsights } = await import('~/composables/useSocialInsights')
    const state = await runInSetup(() => useSocialInsights())

    await expect(state.seedBackendDemoData()).resolves.not.toThrow()
    expect(state.isDemoMode.value).toBe(true)
    expect(state.filteredRecords.value.length).toBeGreaterThan(0)
    expect(state.isLoading.value).toBe(false)
  }, 15000)

  it('should execute exportToCsv and exportToJson safely without throwing', async () => {
    const { useSocialInsights } = await import('~/composables/useSocialInsights')
    const state = await runInSetup(() => useSocialInsights())

    expect(() => state.exportToCsv()).not.toThrow()
    expect(() => state.exportToJson()).not.toThrow()
  })

  it('should compute negative follower growth when community size decreases', async () => {
    const { useSocialInsights } = await import('~/composables/useSocialInsights')
    const state = await runInSetup(() => useSocialInsights())

    // Inject 2 live records where followers declined
    state.isDemoMode.value = false
    state.liveRecords.value = [
      {
        id: 'test-rec-2',
        platform: 'instagram',
        account_id: 'test',
        date: '2026-09-06',
        total_followers: 950,
        reach: 500,
        profile_views: 40,
        website_clicks: 10,
        saves: 5
      },
      {
        id: 'test-rec-1',
        platform: 'instagram',
        account_id: 'test',
        date: '2026-09-01',
        total_followers: 1000,
        reach: 450,
        profile_views: 35,
        website_clicks: 8,
        saves: 4
      }
    ]
    state.activePlatform.value = 'instagram'

    expect(state.summaryMetrics.value.followerGrowth).toBe(-50)
  })
})
