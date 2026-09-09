import { mountSuspended } from '@nuxt/test-utils/runtime'
import { describe, expect, it } from 'vitest'
import ReportsPage from '~/pages/social/reports.vue'
import InsightsPage from '~/pages/social/insights.vue'
import PostsPage from '~/pages/social/posts.vue'

describe('Social Media Pages Mount & Navigation', () => {
  it('should mount /social/reports page without error', async () => {
    const wrapper = await mountSuspended(ReportsPage)
    expect(wrapper.exists()).toBe(true)
    expect(wrapper.text()).toMatch(/Performance & Analytics Réseaux Sociaux|Social Media Performance & Analytics/)
    expect(wrapper.text()).toMatch(/Abonnés Totaux|Total Followers/)
  })

  it('should mount /social/insights page without error', async () => {
    const wrapper = await mountSuspended(InsightsPage)
    expect(wrapper.exists()).toBe(true)
    expect(wrapper.text()).toMatch(/Performance & Analytics Réseaux Sociaux|Social Media Performance & Analytics/)
  })

  it('should mount /social/posts page and render cross-navigation tabs to reports', async () => {
    const wrapper = await mountSuspended(PostsPage)
    expect(wrapper.exists()).toBe(true)
    expect(wrapper.text()).toMatch(/Studio de Contenu & Validation|Content Studio & Validation/)
    expect(wrapper.text()).toMatch(/Rapports & Statistiques Réseaux|Social Reports & Analytics/)

    const links = wrapper.findAll('a')
    const reportsLink = links.find(l => l.attributes('href') === '/social/reports')
    expect(reportsLink).toBeDefined()
  })
})
