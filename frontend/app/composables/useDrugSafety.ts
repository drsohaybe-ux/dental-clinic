/**
 * useDrugSafety - Clinical Decision Support for Dental Medicine
 * 
 * Performs real-time checks for:
 * 1. Drug-Allergy contraindications (e.g. Penicillin allergy vs Amoxicillin)
 * 2. Drug-Drug interactions (e.g. NSAID / Ibuprofen vs Oral Anticoagulant / Sintrom)
 */

export interface SafetyCheckResult {
  hasConflict: boolean
  type?: 'allergy' | 'drug_interaction'
  severity?: 'critical' | 'high' | 'warning'
  offendingDrug?: string
  conflictingItem?: string
  title: string
  reason: string
  alternative?: string
}

function normalize(str: string): string {
  return str
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .trim()
}

// Drug class definitions
const PENICILLIN_DRUGS = [
  'amoxicilline', 'amoxicillin', 'augmentin', 'clamoxyl', 'amoclan',
  'amoxil', 'curam', 'ospamox', 'hiconcil', 'clavamox', 'ampicilline',
  'ampicillin', 'penicilline', 'penicillin', 'bristopen', 'oxacilline'
]

const NSAID_DRUGS = [
  'ibuprofene', 'ibuprofen', 'advil', 'nurofen', 'antadys',
  'ketoprofene', 'ketoprofen', 'bi-profenid', 'biprofenid', 'profenid',
  'diclofenac', 'voltarene', 'voltarène', 'cataflam', 'diclo',
  'apranax', 'naproxene', 'naproxen', 'ponstyl', 'acide mefenamique',
  'celebrex', 'celecoxib', 'piroxicam', 'feldene', 'meloxicam', 'meve'
]

const ANTICOAGULANT_DRUGS = [
  'sintrom', 'sintrome', 'acenocoumarol', 'warfarine', 'warfarin',
  'coumadine', 'eliquis', 'apixaban', 'xarelto', 'rivaroxaban',
  'pradaxa', 'dabigatran', 'plavix', 'clopidogrel', 'kardegic', 'aspegic'
]

const METRONIDAZOLE_DRUGS = [
  'metronidazole', 'flagyl', 'birodogyl', 'rodogyl', 'metron'
]

const MACROLIDE_DRUGS = [
  'clarithromycine', 'clarithromycin', 'zeclar',
  'azithromycine', 'azithromycin', 'zithromax',
  'erythromycine', 'erythromycin',
  'spiramycine', 'rovamycine'
]

const STATIN_DRUGS = [
  'atorvastatine', 'atorvastatin', 'tahor',
  'rosuvastatine', 'rosuvastatin', 'crestor',
  'simvastatine', 'simvastatin', 'zocor'
]

export function isPenicillin(drugName: string): boolean {
  const norm = normalize(drugName)
  return PENICILLIN_DRUGS.some(d => norm.includes(d))
}

export function isNsaid(drugName: string): boolean {
  const norm = normalize(drugName)
  return NSAID_DRUGS.some(d => norm.includes(d))
}

export function isAnticoagulant(drugName: string): boolean {
  const norm = normalize(drugName)
  return ANTICOAGULANT_DRUGS.some(d => norm.includes(d))
}

export function isMetronidazole(drugName: string): boolean {
  const norm = normalize(drugName)
  return METRONIDAZOLE_DRUGS.some(d => norm.includes(d))
}

export function isMacrolide(drugName: string): boolean {
  const norm = normalize(drugName)
  return MACROLIDE_DRUGS.some(d => norm.includes(d))
}

export function isStatin(drugName: string): boolean {
  const norm = normalize(drugName)
  return STATIN_DRUGS.some(d => norm.includes(d))
}

export function useDrugSafety() {
  /**
   * Check if a proposed drug causes an allergy conflict with patient declared allergies
   */
  function checkAllergy(
    drugName: string,
    allergies: Array<{ name?: string, reaction?: string } | string>
  ): SafetyCheckResult | null {
    if (!drugName || !allergies || allergies.length === 0) return null

    const drugNorm = normalize(drugName)
    const allergyNames = allergies.map(a => typeof a === 'string' ? normalize(a) : normalize(a?.name || ''))

    // 1. Penicillin allergy check
    if (isPenicillin(drugNorm)) {
      const match = allergyNames.find(a =>
        a.includes('penicilline') ||
        a.includes('amoxicilline') ||
        a.includes('beta-lactamine') ||
        a.includes('clamoxyl') ||
        a.includes('augmentin')
      )
      if (match) {
        return {
          hasConflict: true,
          type: 'allergy',
          severity: 'critical',
          offendingDrug: drugName,
          conflictingItem: 'Allergie aux Pénicillines / Bêta-lactamines',
          title: 'Contre-indication Absolue : Allergie Pénicilline',
          reason: `Le dossier du patient indique une allergie documentée aux Pénicillines (${match}). L'administration de ${drugName} expose le patient à un risque vital de choc anaphylactique ou œdème de Quincke. Prescription refusée pour sécurité vitale.`,
          alternative: 'Remplacer par un macrolide : Rovamycine (Spiramycine 3M UI) ou Azithromycine 500mg.'
        }
      }
    }

    // 2. NSAID / Aspirin allergy check
    if (isNsaid(drugNorm)) {
      const match = allergyNames.find(a =>
        a.includes('ains') ||
        a.includes('aspirine') ||
        a.includes('anti-inflammatoire') ||
        a.includes('ibuprofene') ||
        a.includes('ketoprofene') ||
        a.includes('voltarene')
      )
      if (match) {
        return {
          hasConflict: true,
          type: 'allergy',
          severity: 'critical',
          offendingDrug: drugName,
          conflictingItem: 'Allergie aux AINS / Aspirine',
          title: 'Contre-indication Absolue : Allergie AINS',
          reason: `Le patient présente une hypersensibilité connue aux anti-inflammatoires (${match}). Risque de bronchospasme aigu (syndrome de Widal) et d'angio-œdème. Prescription refusée.`,
          alternative: 'Privilégier le Paracétamol (Doliprane 1000mg, max 3g/jour).'
        }
      }
    }

    // 3. Direct literal match
    for (const aName of allergyNames) {
      if (aName && (drugNorm.includes(aName) || aName.includes(drugNorm))) {
        return {
          hasConflict: true,
          type: 'allergy',
          severity: 'critical',
          offendingDrug: drugName,
          conflictingItem: aName,
          title: 'Contre-indication Directe : Allergie Médicamenteuse',
          reason: `Le patient est formellement allergique à "${aName}". La prescription de "${drugName}" est refusée.`,
          alternative: 'Choisir une molécule d\'une classe pharmacologique différente.'
        }
      }
    }

    return null
  }

  /**
   * Check if a proposed drug interacts dangerously with existing active medications
   */
  function checkInteraction(
    drugName: string,
    existingMedications: Array<{ name?: string, dosage?: string } | string>
  ): SafetyCheckResult | null {
    if (!drugName || !existingMedications || existingMedications.length === 0) return null

    const drugNorm = normalize(drugName)
    const medNames = existingMedications.map(m => typeof m === 'string' ? normalize(m) : normalize(m?.name || ''))

    // Interaction 1: NSAID + Oral Anticoagulant (e.g. Ibuprofen + Sintrom / Plavix)
    if (isNsaid(drugNorm)) {
      const anticoMatch = medNames.find(m => isAnticoagulant(m))
      if (anticoMatch) {
        return {
          hasConflict: true,
          type: 'drug_interaction',
          severity: 'critical',
          offendingDrug: drugName,
          conflictingItem: anticoMatch.toUpperCase(),
          title: 'Interaction Majeure : AINS + Anticoagulant',
          reason: `Association formellement déconseillée : La prise conjointe d'un AINS (${drugName}) et d'un anticoagulant/antiagrégant (${anticoMatch}) majore drastiquement le risque d'hémorragie digestive et muqueuse sévère et déstabilise l'INR. Prescription refusée pour sécurité vitale.`,
          alternative: 'Prescrire du Paracétamol (Doliprane 1g, max 3g/j) en antalgique de première intention sans AINS.'
        }
      }
    }

    // Reverse interaction 1: Patient prescribed Anticoagulant while taking NSAID
    if (isAnticoagulant(drugNorm)) {
      const nsaidMatch = medNames.find(m => isNsaid(m))
      if (nsaidMatch) {
        return {
          hasConflict: true,
          type: 'drug_interaction',
          severity: 'critical',
          offendingDrug: drugName,
          conflictingItem: nsaidMatch.toUpperCase(),
          title: 'Interaction Majeure : Anticoagulant + AINS en cours',
          reason: `Le patient prend déjà un AINS (${nsaidMatch}). L'ajout d'un anticoagulant (${drugName}) crée un risque hémorragique majeur.`,
          alternative: 'Arrêter l\'AINS avant toute thérapie anticoagulante.'
        }
      }
    }

    // Interaction 2: Metronidazole (Flagyl / Birodogyl / Rodogyl) + Sintrom (Acenocoumarol)
    if (isMetronidazole(drugNorm)) {
      const anticoMatch = medNames.find(m => isAnticoagulant(m))
      if (anticoMatch) {
        return {
          hasConflict: true,
          type: 'drug_interaction',
          severity: 'high',
          offendingDrug: drugName,
          conflictingItem: anticoMatch.toUpperCase(),
          title: 'Interaction Sévère : Métronidazole + Anticoagulant',
          reason: `Le Métronidazole (${drugName}) inhibe fortement le métabolisme du ${anticoMatch}, provoquant une augmentation brutale de l'INR et un risque de saignement aigu per et post-opératoire.`,
          alternative: 'Si antibiothérapie nécessaire, préférer l\'Amoxicilline (si non allergique) ou adapter l\'anticoagulation avec avis cardiologique.'
        }
      }
    }

    // Interaction 3: Macrolides (Clarithromycine / Zeclar) + Statines (Tahor / Atorvastatine)
    if (isMacrolide(drugNorm)) {
      const statinMatch = medNames.find(m => isStatin(m))
      if (statinMatch) {
        return {
          hasConflict: true,
          type: 'drug_interaction',
          severity: 'high',
          offendingDrug: drugName,
          conflictingItem: statinMatch.toUpperCase(),
          title: 'Interaction : Macrolide + Statine',
          reason: `L'association de ${drugName} avec une statine (${statinMatch}) augmente fortement les taux sériques de statine avec risque de rhabdomyolyse et de myopathies sévères.`,
          alternative: 'Suspendre temporairement la statine pendant les 5 jours de traitement, ou choisir la Spiramycine (Rovamycine).'
        }
      }
    }

    return null
  }

  /**
   * Combined safety check: checks both allergies and current drug interactions
   */
  function evaluatePrescriptionSafety(
    drugName: string,
    options: {
      allergies?: Array<{ name?: string, reaction?: string } | string>
      medications?: Array<{ name?: string, dosage?: string } | string>
    }
  ): SafetyCheckResult | null {
    // 1. Allergy check first (highest priority)
    const allergyConflict = checkAllergy(drugName, options.allergies || [])
    if (allergyConflict) return allergyConflict

    // 2. Drug-drug interaction check
    const interactionConflict = checkInteraction(drugName, options.medications || [])
    if (interactionConflict) return interactionConflict

    return null
  }

  return {
    checkAllergy,
    checkInteraction,
    evaluatePrescriptionSafety,
    isPenicillin,
    isNsaid,
    isAnticoagulant,
    isMetronidazole,
    isMacrolide,
    isStatin
  }
}
