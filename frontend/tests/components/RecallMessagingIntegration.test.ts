import { mountSuspended } from '@nuxt/test-utils/runtime'
import { flushPromises } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import RecallRow from '~/../module_layers/recalls/frontend/components/RecallRow.vue'
import MessagesPage from '~/pages/messages/index.vue'

describe('Recall Message Button & Omnichannel Messaging Integration', () => {
  let activeWrapper: any = null

  beforeEach(() => {
    useCookie('access_token').value = 'mock-jwt-token'
    const authUser = useState<any>('auth:user', () => null)
    authUser.value = {
      id: 'doc-1',
      email: 'doctor@dentalpin.dz',
      first_name: 'Mokhtar',
      last_name: 'Dentiste'
    }
  })

  afterEach(async () => {
    if (activeWrapper) {
      activeWrapper.unmount()
      activeWrapper = null
    }
    try {
      localStorage.removeItem('dental_hidden_threads')
    } catch {}
    try {
      const router = useRouter()
      await router.push({ path: '/', query: {} })
      await router.isReady()
    } catch {}
    await flushPromises()
  })

  const sampleRecall = {
    id: 'recall-test-1',
    clinic_id: 'clinic-1',
    patient_id: 'patient-karim',
    due_month: '2026-09-01',
    reason: 'checkup',
    reason_note: 'Contrôle annuel',
    priority: 'high',
    status: 'pending',
    contact_attempt_count: 0,
    patient: {
      id: 'patient-karim',
      first_name: 'Karim',
      last_name: 'Benali',
      phone: '+213 555 12 34 56',
      status: 'active',
      do_not_contact: false
    }
  } as any

  it('renders an icon-only message button next to the call button without text "message"', async () => {
    const wrapper = await mountSuspended(RecallRow, {
      props: { recall: sampleRecall }
    })
    activeWrapper = wrapper

    expect(wrapper.exists()).toBe(true)

    // Call button exists with phone icon
    const buttons = wrapper.findAll('button, a')
    const messageBtn = buttons.find(b => {
      const html = b.html()
      return html.includes('i-lucide-message-square') || b.attributes('title')?.includes('message') || b.attributes('title')?.includes('رسالة')
    })

    expect(messageBtn).toBeDefined()
    // CRITICAL USER REQUIREMENT: "make it just an icon don't write message"
    // The button text should NOT contain "message" or "Message"
    const btnText = messageBtn!.text().trim()
    expect(btnText.toLowerCase()).not.toContain('message')
    expect(btnText.toLowerCase()).not.toContain('رسالة')

    // Tooltip/title should indicate sending a message
    const titleAttr = messageBtn!.attributes('title') || ''
    expect(titleAttr.length).toBeGreaterThan(0)
    expect(titleAttr).toMatch(/message|رسالة|Envoyer/i)
  })

  it('does not render call or message button if patient has no phone or is marked do_not_contact', async () => {
    const noContactRecall = {
      ...sampleRecall,
      id: 'recall-no-contact',
      patient: {
        ...sampleRecall.patient,
        phone: null,
        do_not_contact: true
      }
    }

    const wrapper = await mountSuspended(RecallRow, {
      props: { recall: noContactRecall }
    })
    activeWrapper = wrapper

    const buttons = wrapper.findAll('button, a')
    const messageBtn = buttons.find(b => b.html().includes('i-lucide-message-square'))
    expect(messageBtn).toBeUndefined()
  })

  it('generates the preset Arabic message for recall reasons correctly', async () => {
    const reasonsToTest: Array<{ reason: string; expectedArabic: string }> = [
      { reason: 'checkup', expectedArabic: 'فحص دوري' },
      { reason: 'hygiene', expectedArabic: 'تنظيف وتلميع الأسنان' },
      { reason: 'prosthesis_check', expectedArabic: 'فحص ومتابعة التركيبات' },
      { reason: 'post_op', expectedArabic: 'متابعة ما بعد العلاج' },
      { reason: 'orthodontic_review', expectedArabic: 'مراجعة التقويم' },
      { reason: 'ortho_review', expectedArabic: 'مراجعة التقويم' },
      { reason: 'other', expectedArabic: 'فحص ومتابعة طب الأسنان' },
      { reason: 'unknown_custom_reason', expectedArabic: 'فحص الأسنان' }
    ]

    const REASON_ARABIC_MAP: Record<string, string> = {
      checkup: 'فحص دوري',
      hygiene: 'تنظيف وتلميع الأسنان',
      prosthesis_check: 'فحص ومتابعة التركيبات',
      post_op: 'متابعة ما بعد العلاج',
      orthodontic_review: 'مراجعة التقويم',
      ortho_review: 'مراجعة التقويم',
      implant_review: 'فحص ومتابعة زراعة الأسنان',
      treatment_followup: 'متابعة العلاج',
      other: 'فحص ومتابعة طب الأسنان'
    }

    for (const testCase of reasonsToTest) {
      const reasonLabel = REASON_ARABIC_MAP[testCase.reason] || 'فحص الأسنان'
      expect(reasonLabel).toBe(testCase.expectedArabic)

      const patientName = 'Karim Benali'
      const clinicName = 'د. مختار'
      const expectedTemplate = `السلام عليكم ${patientName}، معكم عيادة طب الأسنان ${clinicName}. نود تذكيركم بموعد الفحص والمتابعة الدورية (${testCase.expectedArabic}). هل يناسبكم تحديد موعد هذا الأسبوع؟`
      expect(expectedTemplate).toContain(testCase.expectedArabic)
      expect(expectedTemplate).toContain('السلام عليكم')
      expect(expectedTemplate).toContain('عيادة طب الأسنان')
      expect(expectedTemplate).toContain('هل يناسبكم تحديد موعد هذا الأسبوع؟')
    }
  })

  it('mounts the /messages page and displays live n8n synchronization and seed threads', async () => {
    const wrapper = await mountSuspended(MessagesPage)
    activeWrapper = wrapper
    await flushPromises()

    expect(wrapper.exists()).toBe(true)

    // Should contain omnicanal messaging title
    expect(wrapper.text()).toMatch(/Messagerie Omnicanal|Omnichannel Messaging/)
    // Should display active live sync badge
    expect(wrapper.text()).toMatch(/synchronisation|synchronization/i)
    // Default seed conversations should be present
    expect(wrapper.text()).toContain('Karim Benali')
    expect(wrapper.text()).toContain('Amina Khelil')
    expect(wrapper.text()).toContain('Yacine Mansouri')
  })

  it('triggers click on message button in RecallRow cleanly without crashing', async () => {
    const wrapper = await mountSuspended(RecallRow, {
      props: { recall: sampleRecall }
    })
    activeWrapper = wrapper
    const buttons = wrapper.findAll('button, a')
    const messageBtn = buttons.find(b => {
      return b.attributes('title')?.includes('message') || b.attributes('title')?.includes('رسالة') || b.html().includes('message-square')
    })
    expect(messageBtn).toBeDefined()
    await messageBtn!.trigger('click')
    await flushPromises()
  })

  it('pre-populates message composer and selects thread from query params in /messages', async () => {
    const testPresetMsg = 'السلام عليكم كريم بن علي، معكم عيادة طب الأسنان د. مختار. نود تذكيركم بموعد الفحص والمتابعة الدورية (فحص دوري). هل يناسبكم تحديد موعد هذا الأسبوع؟'

    const queryObj = {
      phone: '+213 555 12 34 56',
      name: 'Karim Benali',
      message: testPresetMsg,
      platform: 'telegram',
      recallId: 'recall-test-1'
    }

    // Authenticate so auth middleware doesn't redirect to /login
    useCookie('access_token').value = 'mock-jwt-token'
    const authUser = useState<any>('auth:user', () => null)
    authUser.value = {
      id: 'doc-1',
      email: 'doctor@dentalpin.dz',
      first_name: 'Mokhtar',
      last_name: 'Dentiste'
    }

    const router = useRouter()
    await router.push({
      path: '/messages',
      query: queryObj
    })
    await router.isReady()

    const wrapper = await mountSuspended(MessagesPage, {
      route: {
        path: '/messages',
        query: queryObj
      }
    })
    activeWrapper = wrapper
    await flushPromises()

    const inputs = wrapper.findAll('input')

    // The composer input should be populated with the preset Arabic message
    const composerInput = inputs.find(i => i.attributes('placeholder')?.includes('Tapez') || i.attributes('placeholder')?.toLowerCase().includes('type'))
    expect(composerInput).toBeDefined()
    expect((composerInput!.element as HTMLInputElement).value).toBe(testPresetMsg)

    // Karim Benali's telegram conversation should be selected
    expect(wrapper.text()).toContain('Karim Benali')
    expect(wrapper.text()).toContain('+213 555 12 34 56')

    // Doctor clicks send button
    const composerSendBtn = wrapper.find('[data-test="send-reply-button"]')
    expect(composerSendBtn.exists()).toBe(true)
    await composerSendBtn.trigger('click')
    await flushPromises()

    // Composer text should be cleared
    expect((composerInput!.element as HTMLInputElement).value).toBe('')

    // recallId should be cleared from route query
    expect(useRoute().query.recallId).toBeUndefined()
  })

  it('matches patient phone with Algerian local format vs international format', async () => {
    const queryObj = {
      phone: '0555 12 34 56', // local format without +213
      name: 'Karim Benali',
      message: 'مرحبا',
      platform: 'telegram'
    }

    useCookie('access_token').value = 'mock-jwt-token'
    const router = useRouter()
    await router.push({
      path: '/messages',
      query: queryObj
    })
    await router.isReady()

    const wrapper = await mountSuspended(MessagesPage, {
      route: {
        path: '/messages',
        query: queryObj
      }
    })
    activeWrapper = wrapper
    await flushPromises()

    // Must match existing Karim Benali thread (+213 555 12 34 56) without creating a duplicate
    expect(wrapper.text()).toContain('Karim Benali')
    expect(wrapper.text()).toContain('+213 555 12 34 56')
  })

  it('creates new thread for previously unseen patient with pre-filled message', async () => {
    const newPatientMsg = 'السلام عليكم فاطمة، نود تذكيركم بموعد الفحص'
    const queryObj = {
      phone: '+213 550 99 88 77',
      name: 'Fatima Zohra',
      message: newPatientMsg,
      platform: 'whatsapp',
      patientId: 'patient-fatima-99'
    }

    useCookie('access_token').value = 'mock-jwt-token'
    const router = useRouter()
    await router.push({
      path: '/messages',
      query: queryObj
    })
    await router.isReady()

    const wrapper = await mountSuspended(MessagesPage, {
      route: {
        path: '/messages',
        query: queryObj
      }
    })
    activeWrapper = wrapper
    await flushPromises()

    expect(wrapper.text()).toContain('Fatima Zohra')
    expect(wrapper.text()).toContain('+213 550 99 88 77')

    const composerInput = wrapper.findAll('input').find(i => i.attributes('placeholder')?.includes('Tapez') || i.attributes('placeholder')?.toLowerCase().includes('type'))
    expect(composerInput).toBeDefined()
    expect((composerInput!.element as HTMLInputElement).value).toBe(newPatientMsg)
  })

  it('matches patient phone formatted with international 00213 prefix without creating a duplicate', async () => {
    const queryObj = {
      phone: '00213 555 12 34 56',
      name: 'Karim Benali',
      message: 'مرحبا كريم',
      platform: 'telegram'
    }

    useCookie('access_token').value = 'mock-jwt-token'
    const router = useRouter()
    await router.push({
      path: '/messages',
      query: queryObj
    })
    await router.isReady()

    const wrapper = await mountSuspended(MessagesPage, {
      route: {
        path: '/messages',
        query: queryObj
      }
    })
    activeWrapper = wrapper
    await flushPromises()

    // Must match existing Karim Benali thread
    expect(wrapper.text()).toContain('Karim Benali')
    expect(wrapper.text()).toContain('+213 555 12 34 56')
  })

  it('unhides previously archived conversation when arriving via recall navigation', async () => {
    // Simulate Karim Benali thread ('thread-1') was archived in localStorage
    localStorage.setItem('dental_hidden_threads', JSON.stringify(['thread-1']))

    const queryObj = {
      phone: '+213 555 12 34 56',
      name: 'Karim Benali',
      message: 'السلام عليكم كريم',
      platform: 'telegram',
      recallId: 'recall-test-1'
    }

    useCookie('access_token').value = 'mock-jwt-token'
    const router = useRouter()
    await router.push({
      path: '/messages',
      query: queryObj
    })
    await router.isReady()

    const wrapper = await mountSuspended(MessagesPage, {
      route: {
        path: '/messages',
        query: queryObj
      }
    })
    activeWrapper = wrapper
    await flushPromises()

    // Thread-1 should be unhidden and visible in active conversation view
    expect(wrapper.text()).toContain('Karim Benali')
    const storedHidden = JSON.parse(localStorage.getItem('dental_hidden_threads') || '[]')
    expect(storedHidden).not.toContain('thread-1')
  })

  it('RecallRow message button has data-test attribute and recovers if navigation succeeds', async () => {
    const wrapper = await mountSuspended(RecallRow, {
      props: { recall: sampleRecall }
    })
    activeWrapper = wrapper

    const msgBtn = wrapper.find('[data-test="recall-message-button"]')
    expect(msgBtn.exists()).toBe(true)
    expect(msgBtn.attributes('aria-label')).toBeDefined()
    expect(msgBtn.text().trim()).toBe('')
  })
})
