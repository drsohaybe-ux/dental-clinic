import { describe, it, expect } from 'vitest'
import {
  useDrugSafety,
  isPenicillin,
  isNsaid,
  isAnticoagulant,
  isMetronidazole,
  isMacrolide,
  isStatin
} from '../../app/composables/useDrugSafety'

describe('useDrugSafety - Clinical Decision Support', () => {
  const safety = useDrugSafety()

  describe('Drug Class Identifiers', () => {
    it('correctly identifies penicillins and beta-lactams', () => {
      expect(isPenicillin('Amoxicilline 1g')).toBe(true)
      expect(isPenicillin('Augmentin 1g/125mg')).toBe(true)
      expect(isPenicillin('Clamoxyl 500mg')).toBe(true)
      expect(isPenicillin('Amoclan 1g')).toBe(true)
      expect(isPenicillin('Paracétamol')).toBe(false)
    })

    it('correctly identifies NSAIDs', () => {
      expect(isNsaid('Ibuprofène 400mg')).toBe(true)
      expect(isNsaid('Bi-Profenid 150mg')).toBe(true)
      expect(isNsaid('Voltarène 50mg')).toBe(true)
      expect(isNsaid('Apranax 550mg')).toBe(true)
      expect(isNsaid('Cataflam 50mg')).toBe(true)
      expect(isNsaid('Doliprane')).toBe(false)
    })

    it('correctly identifies anticoagulants and antiplatelets', () => {
      expect(isAnticoagulant('Sintrom 4mg')).toBe(true)
      expect(isAnticoagulant('Acénocoumarol 4mg')).toBe(true)
      expect(isAnticoagulant('Plavix 75mg')).toBe(true)
      expect(isAnticoagulant('Eliquis 5mg')).toBe(true)
      expect(isAnticoagulant('Amoxicilline')).toBe(false)
    })

    it('correctly identifies metronidazole', () => {
      expect(isMetronidazole('Flagyl 500mg')).toBe(true)
      expect(isMetronidazole('Birodogyl')).toBe(true)
      expect(isMetronidazole('Rodogyl')).toBe(true)
      expect(isMetronidazole('Métronidazole 250mg')).toBe(true)
    })

    it('correctly identifies macrolides and statins', () => {
      expect(isMacrolide('Clarithromycine 500mg')).toBe(true)
      expect(isMacrolide('Rovamycine 3 M.U.I')).toBe(true)
      expect(isStatin('Tahor 20mg')).toBe(true)
      expect(isStatin('Atorvastatine 10mg')).toBe(true)
    })
  })

  describe('Allergy Refusal Checks', () => {
    it('refuses Amoxicilline when patient is allergic to Penicillin', () => {
      const result = safety.checkAllergy('Amoxicilline 1g', [
        'Pénicilline / Bêta-lactamines'
      ])
      expect(result).not.toBeNull()
      expect(result?.hasConflict).toBe(true)
      expect(result?.type).toBe('allergy')
      expect(result?.severity).toBe('critical')
      expect(result?.title).toContain('Pénicilline')
      expect(result?.alternative).toContain('Rovamycine')
    })

    it('refuses Ibuprofène when patient has NSAID allergy', () => {
      const result = safety.checkAllergy('Ibuprofène 400mg', [
        { name: 'Allergie aux AINS / Aspirine' }
      ])
      expect(result).not.toBeNull()
      expect(result?.hasConflict).toBe(true)
      expect(result?.type).toBe('allergy')
      expect(result?.alternative).toContain('Paracétamol')
    })

    it('allows Paracétamol when patient has Penicillin allergy', () => {
      const result = safety.checkAllergy('Paracétamol 1000mg', [
        'Pénicilline'
      ])
      expect(result).toBeNull()
    })
  })

  describe('Drug-Drug Interaction Refusal Checks', () => {
    it('refuses Ibuprofen when patient is under Sintrom (Anticoagulant)', () => {
      const result = safety.checkInteraction('Ibuprofène 400mg', [
        'Sintrom 4mg (Acénocoumarol)'
      ])
      expect(result).not.toBeNull()
      expect(result?.hasConflict).toBe(true)
      expect(result?.type).toBe('drug_interaction')
      expect(result?.severity).toBe('critical')
      expect(result?.title).toContain('AINS + Anticoagulant')
      expect(result?.reason).toContain('risque d\'hémorragie')
      expect(result?.alternative).toContain('Paracétamol')
    })

    it('refuses Birodogyl/Metronidazole when patient takes Sintrom', () => {
      const result = safety.checkInteraction('Birodogyl', [
        'Sintrom 4mg'
      ])
      expect(result).not.toBeNull()
      expect(result?.hasConflict).toBe(true)
      expect(result?.reason).toContain('INR')
    })

    it('refuses Clarithromycine when patient is under Tahor (Statin)', () => {
      const result = safety.checkInteraction('Clarithromycine 500mg', [
        'Tahor 20mg (Atorvastatine)'
      ])
      expect(result).not.toBeNull()
      expect(result?.hasConflict).toBe(true)
      expect(result?.reason).toContain('rhabdomyolyse')
    })

    it('allows Paracétamol when patient takes Sintrom', () => {
      const result = safety.checkInteraction('Paracétamol 1000mg', [
        'Sintrom 4mg'
      ])
      expect(result).toBeNull()
    })
  })

  describe('evaluatePrescriptionSafety Comprehensive Evaluation', () => {
    const patientContext = {
      allergies: ['Pénicilline / Bêta-lactamines'],
      medications: ['Sintrom 4mg (Acénocoumarol)', 'Amlodipine 5mg']
    }

    it('blocks Ibuprofen due to Sintrom interaction', () => {
      const evaluation = safety.evaluatePrescriptionSafety('Ibuprofène 400mg', patientContext)
      expect(evaluation?.hasConflict).toBe(true)
      expect(evaluation?.type).toBe('drug_interaction')
    })

    it('blocks Augmentin due to Penicillin allergy', () => {
      const evaluation = safety.evaluatePrescriptionSafety('Augmentin 1g', patientContext)
      expect(evaluation?.hasConflict).toBe(true)
      expect(evaluation?.type).toBe('allergy')
    })

    it('approves Paracetamol without conflict', () => {
      const evaluation = safety.evaluatePrescriptionSafety('Paracétamol 1000mg', patientContext)
      expect(evaluation).toBeNull()
    })
  })
})
