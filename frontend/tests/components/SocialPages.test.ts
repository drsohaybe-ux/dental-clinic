import { mountSuspended } from '@nuxt/test-utils/runtime'
import { describe, expect, it } from 'vitest'
import ReportsPage from '~/pages/social/reports.vue'
import InsightsPage from '~/pages/social/insights.vue'
import PostsPage from '~/pages/social/posts.vue'

describe('Social Media Pages Mount & Navigation', () => {
  it('should mount /social/reports page without error', async () => {
    const wrapper = await mountSuspended(ReportsPage)
    expect(wrapper.exists()).toBe(true)
    expect(wrapper.text()).toContain('Performance & Analytics Réseaux Sociaux')
    expect(wrapper.text()).toContain('Abonnés Totaux')
  })

  it('should mount /social/insights page without error', async () => {
    const wrapper = await mountSuspended(InsightsPage)
    expect(wrapper.exists()).toBe(true)
    expect(wrapper.text()).toContain('Performance & Analytics Réseaux Sociaux')
  })

  it('should mount /social/posts page and render cross-navigation tabs to reports', async () => {
    const wrapper = await mountSuspended(PostsPage)
    expect(wrapper.exists()).toBe(true)
    expect(wrapper.text()).toContain('Studio de Contenu & Validation')
    expect(wrapper.text()).toContain('Rapports & Statistiques Réseaux')

    const links = wrapper.findAll('a')
    const reportsLink = links.find(l => l.attributes('href') === '/social/reports')
    expect(reportsLink).toBeDefined()
  })
})
