import { mountSuspended } from '@nuxt/test-utils/runtime'
import { describe, expect, it } from 'vitest'
import SocialMediaReports from '~/components/social/SocialMediaReports.vue'

describe('SocialMediaReports component', () => {
  it('should mount cleanly without throwing and render the reports dashboard', async () => {
    const wrapper = await mountSuspended(SocialMediaReports)

    expect(wrapper.exists()).toBe(true)
    const text = wrapper.text()
    expect(text).toMatch(/Performance & Analytics Réseaux Sociaux|Social Media Performance & Analytics/)
    expect(text).toMatch(/Abonnés Totaux|Total Followers/)
    expect(text).toMatch(/Portée Globale|Global Reach/)
    expect(text).toMatch(/Visites du Profil|Profile Visits/)
    expect(text).toMatch(/Clics Site & Rendez-vous|Website & Booking Clicks/)
  })

  it('should render platform selectors and date range filters', async () => {
    const wrapper = await mountSuspended(SocialMediaReports)

    const text = wrapper.text()
    expect(text).toMatch(/Tous les Réseaux|All Networks/)
    expect(text).toContain('Instagram')
    expect(text).toContain('Facebook')
    expect(text).toMatch(/7 Jours|7 Days/)
    expect(text).toMatch(/30 Jours|30 Days/)
    expect(text).toMatch(/90 Jours|90 Days/)
  })

  it('should render the SVG trend chart and historical data table', async () => {
    const wrapper = await mountSuspended(SocialMediaReports)

    expect(wrapper.find('svg').exists()).toBe(true)
    expect(wrapper.find('table').exists()).toBe(true)
    expect(wrapper.text()).toMatch(/Journal Quotidien des Métriques|Daily Metrics Log/)
  })

  it('should render action buttons for refresh, CSV export, and n8n connection', async () => {
    const wrapper = await mountSuspended(SocialMediaReports)

    const text = wrapper.text()
    expect(text).toMatch(/Actualiser|Refresh/)
    expect(text).toMatch(/Exporter CSV|Export CSV/)
    expect(text).toMatch(/Connexion n8n|n8n Connection/)
  })

  it('should toggle n8n configuration modal when button is clicked', async () => {
    const wrapper = await mountSuspended(SocialMediaReports)
    const n8nBtn = wrapper.findAll('button').find(b => b.text().includes('Connexion n8n') || b.text().includes('n8n Connection'))
    expect(n8nBtn).toBeDefined()
    await n8nBtn!.trigger('click')
    expect(wrapper.text()).toMatch(/Configuration de Synchronisation n8n|n8n Sync|n8n Connection/)
    expect(wrapper.text()).toMatch(/Structure de la Table PostgreSQL|PostgreSQL Table Structure/)
  })
})
