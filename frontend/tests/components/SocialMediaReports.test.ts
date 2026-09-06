import { mountSuspended } from '@nuxt/test-utils/runtime'
import { describe, expect, it } from 'vitest'
import SocialMediaReports from '~/components/social/SocialMediaReports.vue'

describe('SocialMediaReports component', () => {
  it('should mount cleanly without throwing and render the reports dashboard', async () => {
    const wrapper = await mountSuspended(SocialMediaReports)

    expect(wrapper.exists()).toBe(true)
    const text = wrapper.text()
    expect(text).toContain('Performance & Analytics Réseaux Sociaux')
    expect(text).toContain('Abonnés Totaux')
    expect(text).toContain('Portée Globale')
    expect(text).toContain('Visites du Profil')
    expect(text).toContain('Clics Site & Rendez-vous')
  })

  it('should render platform selectors and date range filters', async () => {
    const wrapper = await mountSuspended(SocialMediaReports)

    const text = wrapper.text()
    expect(text).toContain('Tous les Réseaux')
    expect(text).toContain('Instagram')
    expect(text).toContain('Facebook')
    expect(text).toContain('7 Jours')
    expect(text).toContain('30 Jours')
    expect(text).toContain('90 Jours')
  })

  it('should render the SVG trend chart and historical data table', async () => {
    const wrapper = await mountSuspended(SocialMediaReports)

    expect(wrapper.find('svg').exists()).toBe(true)
    expect(wrapper.find('table').exists()).toBe(true)
    expect(wrapper.text()).toContain('Journal Quotidien des Métriques')
  })

  it('should render action buttons for refresh, CSV export, and n8n connection', async () => {
    const wrapper = await mountSuspended(SocialMediaReports)

    const text = wrapper.text()
    expect(text).toContain('Actualiser')
    expect(text).toContain('Exporter CSV')
    expect(text).toContain('Connexion n8n')
  })

  it('should toggle n8n configuration modal when button is clicked', async () => {
    const wrapper = await mountSuspended(SocialMediaReports)
    const n8nBtn = wrapper.findAll('button').find(b => b.text().includes('Connexion n8n'))
    expect(n8nBtn).toBeDefined()
    await n8nBtn!.trigger('click')
    expect(wrapper.text()).toContain('Configuration de Synchronisation n8n')
    expect(wrapper.text()).toContain('Structure de la Table PostgreSQL')
  })
})
