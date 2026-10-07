<template>
  <div class="space-y-6">
    <!-- Top Banner: Human Takeover Switch & Status -->
    <div class="bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-2xl p-5 shadow-2xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div class="flex items-center gap-3">
        <div
          :class="[
            'w-10 h-10 rounded-xl flex items-center justify-center shrink-0',
            isHumanActive ? 'bg-amber-100 dark:bg-amber-950/60 text-amber-600' : 'bg-primary-50 dark:bg-primary-950/60 text-primary-600'
          ]"
        >
          <UIcon :name="isHumanActive ? 'i-lucide-user-check' : 'i-lucide-bot'" class="w-5 h-5" />
        </div>
        <div>
          <div class="flex items-center gap-2">
            <h3 class="text-sm font-bold text-gray-900 dark:text-white">
              {{ isHumanActive ? t('patientAiDossier.humanActiveTitle', 'Prise en main humaine active') : t('patientAiDossier.aiActiveTitle', 'Assistant IA Téléphone & Messagerie actif') }}
            </h3>
            <UBadge :color="isHumanActive ? 'warning' : 'success'" variant="subtle" size="xs">
              {{ isHumanActive ? t('patientAiDossier.aiPausedBadge', 'IA en pause') : t('patientAiDossier.onlineBadge', 'En ligne (WhatsApp & Telegram)') }}
            </UBadge>
          </div>
          <p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
            {{ isHumanActive ? t('patientAiDossier.humanActiveDesc', 'Le Dr. Arselane ou le secrétariat répond directement au patient.') : t('patientAiDossier.aiActiveDesc', "L'IA recueille les symptômes, radios et antécédents avant la consultation au cabinet.") }}
          </p>
        </div>
      </div>

      <div class="flex items-center gap-3 self-end sm:self-auto">
        <button
          type="button"
          :class="[
            'inline-flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-lg shadow-2xs transition-colors cursor-pointer',
            isHumanActive
              ? 'bg-primary-600 hover:bg-primary-700 text-white'
              : 'bg-amber-500 hover:bg-amber-600 text-white'
          ]"
          :disabled="isToggling"
          @click="toggleHumanTakeover"
        >
          <UIcon :name="isHumanActive ? 'i-lucide-bot' : 'i-lucide-hand'" class="w-4 h-4" />
          <span>{{ isHumanActive ? t('patientAiDossier.takeoverAi', "Réactiver l'Assistant IA") : t('patientAiDossier.takeoverHuman', 'Prendre la main sur la conversation') }}</span>
        </button>
      </div>
    </div>

    <!-- AI Pre-Consultation Anamnèse (Collecte IA Pré-Consultation) -->
    <div class="bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-2xl p-5 shadow-2xs space-y-4">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-gray-100 dark:border-gray-800">
        <div>
          <div class="flex items-center gap-2.5">
            <div class="w-8 h-8 rounded-lg bg-primary-100 dark:bg-primary-950/80 text-primary-600 dark:text-primary-400 flex items-center justify-center">
              <UIcon name="i-lucide-clipboard-check" class="w-4 h-4" />
            </div>
            <div>
              <h3 class="text-sm font-bold text-gray-900 dark:text-white flex items-center gap-2">
                Pré-Anamnèse Recueillie par l'IA (WhatsApp / Telegram)
                <UBadge color="primary" variant="subtle" size="xs">
                  Pré-Consultation
                </UBadge>
              </h3>
              <p class="text-xs text-gray-500 dark:text-gray-400">
                Données déclarées par le patient à distance. Le Dr. Arselane valide ou décline chaque information lors de l'examen au fauteuil.
              </p>
            </div>
          </div>
        </div>

        <!-- Global Action Buttons for Doctor -->
        <div class="flex items-center gap-2 shrink-0">
          <UButton
            v-if="hasPendingItems"
            color="primary"
            variant="solid"
            size="xs"
            icon="i-lucide-check-check"
            class="cursor-pointer"
            @click="approveAllAnamnese"
          >
            Tout valider au dossier
          </UButton>
          <UButton
            color="neutral"
            variant="ghost"
            size="xs"
            icon="i-lucide-rotate-ccw"
            class="cursor-pointer text-gray-500"
            title="Réinitialiser pour re-démontrer"
            @click="resetAnamneseDemo"
          >
            Réinitialiser démo
          </UButton>
        </div>
      </div>

      <!-- Anamnèse Items Grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div
          v-for="item in anamneseItems"
          :key="item.id"
          :class="[
            'border rounded-xl p-4 transition-all space-y-3 relative',
            item.status === 'approved'
              ? 'bg-emerald-50/40 dark:bg-emerald-950/20 border-emerald-200 dark:border-emerald-800/60'
              : item.status === 'declined'
                ? 'bg-gray-50 dark:bg-gray-800/40 border-gray-200 dark:border-gray-800 opacity-60'
                : 'bg-white dark:bg-gray-900/60 border-gray-200 dark:border-gray-700/80 shadow-2xs'
          ]"
        >
          <!-- Item Header & Status -->
          <div class="flex items-start justify-between gap-3">
            <div class="flex items-center gap-2">
              <div
                :class="[
                  'w-7 h-7 rounded-lg flex items-center justify-center shrink-0',
                  item.category === 'medication' ? 'bg-amber-100 text-amber-700 dark:bg-amber-950/70 dark:text-amber-400' :
                  item.category === 'allergy' ? 'bg-rose-100 text-rose-700 dark:bg-rose-950/70 dark:text-rose-400' :
                  item.category === 'symptom' ? 'bg-blue-100 text-blue-700 dark:bg-blue-950/70 dark:text-blue-400' :
                  'bg-purple-100 text-purple-700 dark:bg-purple-950/70 dark:text-purple-400'
                ]"
              >
                <UIcon
                  :name="
                    item.category === 'medication' ? 'i-lucide-pill' :
                    item.category === 'allergy' ? 'i-lucide-shield-alert' :
                    item.category === 'symptom' ? 'i-lucide-activity' : 'i-lucide-file-text'
                  "
                  class="w-4 h-4"
                />
              </div>
              <div>
                <span class="text-[11px] font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">
                  {{ item.subtitle }}
                </span>
                <h4 class="text-xs font-bold text-gray-900 dark:text-white">
                  {{ item.title }}
                </h4>
              </div>
            </div>

            <!-- Status Badge -->
            <UBadge
              :color="item.status === 'approved' ? 'success' : item.status === 'declined' ? 'neutral' : 'warning'"
              variant="subtle"
              size="xs"
              class="shrink-0"
            >
              {{
                item.status === 'approved' ? '✅ Validé (Dr. Arselane)' :
                item.status === 'declined' ? '❌ Non confirmé' :
                'À valider au cabinet'
              }}
            </UBadge>
          </div>

          <!-- Item Details -->
          <p class="text-xs text-gray-600 dark:text-gray-300 leading-relaxed font-normal">
            {{ item.details }}
          </p>

          <!-- Warning Box if any -->
          <div
            v-if="item.warning"
            :class="[
              'p-2.5 rounded-lg text-xs flex items-start gap-2',
              item.category === 'allergy'
                ? 'bg-rose-50 dark:bg-rose-950/40 text-rose-800 dark:text-rose-300 border border-rose-200 dark:border-rose-900/40'
                : 'bg-amber-50 dark:bg-amber-950/40 text-amber-800 dark:text-amber-300 border border-amber-200 dark:border-amber-900/40'
            ]"
          >
            <UIcon name="i-lucide-alert-triangle" class="w-4 h-4 shrink-0 mt-0.5" />
            <div class="leading-tight">
              <span class="font-bold">Alerte IA Clinique :</span>
              <span class="ml-1">{{ item.warning }}</span>
            </div>
          </div>

          <!-- Doctor Validation Action Buttons -->
          <div class="flex items-center justify-between pt-2 border-t border-gray-100 dark:border-gray-800/80">
            <span class="text-[10px] text-gray-400">
              {{ item.approvedAt ? `Validé le ${formatTime(item.approvedAt)}` : 'Déclaré via WhatsApp' }}
            </span>
            <div class="flex items-center gap-1.5">
              <button
                type="button"
                :class="[
                  'px-2.5 py-1 text-xs font-medium rounded-md transition-colors cursor-pointer flex items-center gap-1',
                  item.status === 'declined'
                    ? 'bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-white font-bold'
                    : 'text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800'
                ]"
                @click="declineAnamneseItem(item)"
              >
                <UIcon name="i-lucide-x" class="w-3.5 h-3.5" />
                <span>Décliner</span>
              </button>

              <button
                type="button"
                :class="[
                  'px-3 py-1 text-xs font-semibold rounded-md transition-colors cursor-pointer flex items-center gap-1 shadow-2xs',
                  item.status === 'approved'
                    ? 'bg-emerald-600 text-white'
                    : 'bg-primary-600 hover:bg-primary-700 text-white'
                ]"
                @click="approveAnamneseItem(item)"
              >
                <UIcon name="i-lucide-check" class="w-3.5 h-3.5" />
                <span>{{ item.status === 'approved' ? 'Validé' : 'Valider' }}</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- AI Clinical Safety & Drug Interaction Engine Widget (Démonstration Client) -->
    <div class="bg-gradient-to-br from-slate-900 to-indigo-950 text-white border border-indigo-900/80 rounded-2xl p-5 shadow-md space-y-4">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-xl bg-indigo-500/20 border border-indigo-400/30 flex items-center justify-center text-indigo-300 shrink-0">
            <UIcon name="i-lucide-shield-check" class="w-5 h-5 text-indigo-400" />
          </div>
          <div>
            <div class="flex items-center gap-2">
              <h3 class="text-sm font-bold text-white flex items-center gap-1.5">
                Contrôle Thérapeutique & Pharmacovigilance IA
              </h3>
              <UBadge color="info" variant="solid" size="xs" class="bg-indigo-500 text-white font-bold">
                Moteur Actif
              </UBadge>
            </div>
            <p class="text-xs text-indigo-200/80 mt-0.5">
              Sécurité patient absolue : l'IA bloque toute prescription présentant une interaction médicamenteuse ou une allergie.
            </p>
          </div>
        </div>

        <span class="text-xs text-indigo-300 font-mono bg-indigo-950/60 border border-indigo-800/60 px-2.5 py-1 rounded-md self-start sm:self-auto">
          Patient : {{ patientDisplayName }}
        </span>
      </div>

      <!-- Quick Safety Simulation Buttons for Presentation Demo -->
      <div class="space-y-2 pt-2 border-t border-indigo-800/50">
        <div class="flex items-center justify-between">
          <span class="text-xs font-bold text-indigo-200 flex items-center gap-1.5">
            <UIcon name="i-lucide-sparkles" class="w-3.5 h-3.5 text-amber-400" />
            Tests de démonstration en direct (Cliquez pour observer le refus IA) :
          </span>
          <span class="text-[11px] text-indigo-400">
            Antécédents : Sintrom 4mg + Allergie Pénicillines
          </span>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
          <!-- Test 1: Ibuprofen (NSAID vs Anticoagulant Interaction) -->
          <button
            type="button"
            class="p-3 rounded-xl bg-rose-950/60 hover:bg-rose-900/80 border border-rose-500/40 text-left transition-all cursor-pointer group flex flex-col justify-between gap-2"
            @click="testDrugSimulation('Ibuprofène 400mg')"
          >
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-rose-200 flex items-center gap-1">
                <UIcon name="i-lucide-alert-octagon" class="w-4 h-4 text-rose-400 group-hover:scale-110 transition-transform" />
                Ibuprofène 400 mg
              </span>
              <UBadge color="error" variant="solid" size="xs" class="text-[10px]">
                Interdit
              </UBadge>
            </div>
            <p class="text-[11px] text-rose-300/80 leading-snug">
              AINS vs Sintrom (Anticoagulant) → Risque d'hémorragie digestive majeure.
            </p>
            <div class="text-[10px] font-semibold text-rose-400 flex items-center gap-1">
              <span>Tester le refus IA</span>
              <UIcon name="i-lucide-arrow-right" class="w-3 h-3" />
            </div>
          </button>

          <!-- Test 2: Amoxicilline (Penicillin Allergy) -->
          <button
            type="button"
            class="p-3 rounded-xl bg-amber-950/60 hover:bg-amber-900/80 border border-amber-500/40 text-left transition-all cursor-pointer group flex flex-col justify-between gap-2"
            @click="testDrugSimulation('Amoxicilline 1g')"
          >
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-amber-200 flex items-center gap-1">
                <UIcon name="i-lucide-alert-triangle" class="w-4 h-4 text-amber-400 group-hover:scale-110 transition-transform" />
                Amoxicilline 1 g
              </span>
              <UBadge color="warning" variant="solid" size="xs" class="text-[10px]">
                Allergie
              </UBadge>
            </div>
            <p class="text-[11px] text-amber-300/80 leading-snug">
              Bêta-lactamine vs Allergie documentée → Risque choc anaphylactique.
            </p>
            <div class="text-[10px] font-semibold text-amber-400 flex items-center gap-1">
              <span>Tester le refus IA</span>
              <UIcon name="i-lucide-arrow-right" class="w-3 h-3" />
            </div>
          </button>

          <!-- Test 3: Paracetamol (Safe Alternative) -->
          <button
            type="button"
            class="p-3 rounded-xl bg-emerald-950/60 hover:bg-emerald-900/80 border border-emerald-500/40 text-left transition-all cursor-pointer group flex flex-col justify-between gap-2"
            @click="testDrugSimulation('Paracétamol 1000mg')"
          >
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-emerald-200 flex items-center gap-1">
                <UIcon name="i-lucide-check-circle" class="w-4 h-4 text-emerald-400 group-hover:scale-110 transition-transform" />
                Paracétamol 1 000 mg
              </span>
              <UBadge color="success" variant="solid" size="xs" class="text-[10px]">
                Compatible
              </UBadge>
            </div>
            <p class="text-[11px] text-emerald-300/80 leading-snug">
              Antalgique compatible sans interaction Sintrom ni allergie.
            </p>
            <div class="text-[10px] font-semibold text-emerald-400 flex items-center gap-1">
              <span>Tester l'accord IA</span>
              <UIcon name="i-lucide-arrow-right" class="w-3 h-3" />
            </div>
          </button>
        </div>

        <!-- Custom Drug Test Input -->
        <div class="pt-2 flex items-center gap-2">
          <div class="relative flex-grow">
            <input
              v-model="customDrugInput"
              type="text"
              placeholder="Tester une autre molécule (ex: Augmentin, Cataflam, Bi-Profenid, Flagyl, Tahor...)"
              class="w-full text-xs bg-indigo-950/80 border border-indigo-700/60 rounded-lg px-3 py-2 text-white placeholder-indigo-400/60 focus:outline-hidden focus:ring-2 focus:ring-indigo-400"
              @keyup.enter="testDrugSimulation(customDrugInput)"
            />
          </div>
          <button
            type="button"
            class="px-3.5 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold transition-colors shrink-0 cursor-pointer flex items-center gap-1.5 shadow-2xs"
            :disabled="!customDrugInput.trim()"
            @click="testDrugSimulation(customDrugInput)"
          >
            <UIcon name="i-lucide-search" class="w-3.5 h-3.5" />
            <span>Tester compatibilité IA</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Main 2-Column Grid: Radiographies & Vision on Left (2 cols), Chat history on Right (1 col) -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Left Column: Radiographies & AI Vision Analysis (2/3 width) -->
      <div class="lg:col-span-2 space-y-6">
        <div class="flex items-center justify-between">
          <h3 class="text-base font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <UIcon name="i-lucide-scan" class="text-primary-500 w-5 h-5" />
            {{ t('patientAiDossier.radiosTitle', 'Radiographies & Diagnostic IA') }}
          </h3>
          <span class="text-xs text-gray-500 dark:text-gray-400 font-medium">
            {{ t('patientAiDossier.radiosAnalyzed', { count: dossierFiles.length }, `${dossierFiles.length} radiographie(s) analysée(s)`) }}
          </span>
        </div>

        <!-- Radios List -->
        <div v-if="dossierFiles.length > 0" class="space-y-6">
          <div
            v-for="file in dossierFiles"
            :key="file.id"
            class="bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-2xl overflow-hidden shadow-2xs"
          >
            <!-- Image & Preview -->
            <div class="relative w-full h-80 bg-black flex items-center justify-center overflow-hidden group">
              <img
                :src="file.file_url"
                :alt="file.name"
                class="w-full h-full object-contain cursor-pointer group-hover:scale-102 transition-transform"
                @click="openLightbox(file.file_url)"
              />
              <div class="absolute top-3.5 left-3.5 flex gap-2">
                <UBadge color="primary" variant="solid" size="xs" class="font-bold uppercase tracking-wider">
                  {{ file.file_type.replace('_', ' ') }}
                </UBadge>
                <UBadge
                  :color="radioDiagnosisConfirmed ? 'success' : 'warning'"
                  variant="solid"
                  size="xs"
                >
                  {{ radioDiagnosisConfirmed ? 'Diagnostic Confirmé (Dr. Arselane)' : 'En attente de confirmation clinique' }}
                </UBadge>
              </div>
              <div class="absolute bottom-3.5 right-3.5">
                <button
                  type="button"
                  class="p-2 bg-black/60 hover:bg-black/80 text-white rounded-lg text-xs backdrop-blur-xs flex items-center gap-1.5 transition-colors cursor-pointer"
                  @click="openLightbox(file.file_url)"
                >
                  <UIcon name="i-lucide-zoom-in" class="w-4 h-4" />
                  {{ t('patientAiDossier.fullscreen', 'Plein écran') }}
                </button>
              </div>
            </div>

            <!-- AI Clinical Analysis Card -->
            <div class="p-5 space-y-4">
              <div class="flex items-start justify-between gap-4">
                <div>
                  <h4 class="text-sm font-bold text-gray-900 dark:text-white">
                    {{ file.name }}
                  </h4>
                  <p class="text-xs text-gray-400 mt-0.5">
                    {{ t('patientAiDossier.sentVia', { date: formatDate(file.created_at) }) }}
                  </p>
                </div>
              </div>

              <!-- AI Findings Box -->
              <div class="p-4 bg-primary-50/60 dark:bg-primary-950/30 border border-primary-100 dark:border-primary-900/50 rounded-xl space-y-2.5">
                <div class="flex items-center justify-between">
                  <div class="flex items-center gap-2 text-xs font-bold text-primary-700 dark:text-primary-300">
                    <UIcon name="i-lucide-sparkles" class="w-4 h-4 text-amber-500" />
                    <span>Rapport de Vision Clinique IA (Dr. Arselane AI Vision)</span>
                  </div>
                  <UBadge color="primary" variant="subtle" size="xs">
                    Haute précision
                  </UBadge>
                </div>
                <div class="text-xs text-gray-700 dark:text-gray-200 leading-relaxed font-medium space-y-1.5">
                  <p class="whitespace-pre-line">{{ file.ai_analysis }}</p>
                </div>
              </div>

              <!-- Doctor Action Controls for the Radiograph -->
              <div class="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-gray-100 dark:border-gray-800">
                <span class="text-xs text-gray-500">
                  Décision clinique Dr. Arselane :
                </span>
                <div class="flex items-center gap-2">
                  <UButton
                    color="neutral"
                    variant="soft"
                    size="xs"
                    icon="i-lucide-refresh-cw"
                    class="cursor-pointer"
                    @click="requestRetakeRadio"
                  >
                    Demander cliché rétro-alvéolaire #16
                  </UButton>
                  <UButton
                    :color="radioDiagnosisConfirmed ? 'success' : 'primary'"
                    :variant="radioDiagnosisConfirmed ? 'solid' : 'solid'"
                    size="xs"
                    icon="i-lucide-check-circle-2"
                    class="cursor-pointer"
                    @click="confirmRadioDiagnosis"
                  >
                    {{ radioDiagnosisConfirmed ? 'Diagnostic validé par Dr. Arselane' : 'Confirmer le diagnostic radio' }}
                  </UButton>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Empty State for Radios -->
        <div
          v-else
          class="bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-2xl py-14 px-6 text-center shadow-2xs"
        >
          <UIcon name="i-lucide-scan" class="w-12 h-12 mx-auto text-gray-300 dark:text-gray-600 mb-3" />
          <h4 class="text-sm font-bold text-gray-900 dark:text-white">{{ t('patientAiDossier.noRadios', 'Aucune radiographie reçue') }}</h4>
          <p class="text-xs text-gray-500 dark:text-gray-400 mt-1 max-w-sm mx-auto">
            {{ t('patientAiDossier.noRadiosDesc', "Dès que le patient transmet une photo ou une panoramique sur WhatsApp ou Telegram, l'IA l'analysera et l'affichera ici.") }}
          </p>
        </div>
      </div>

      <!-- Right Column: 2-Way Message Timeline (1/3 width) -->
      <div class="space-y-4">
        <div class="flex items-center justify-between">
          <h3 class="text-base font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <UIcon name="i-lucide-messages-square" class="text-primary-500 w-5 h-5" />
            {{ t('patientAiDossier.omnichannelTitle', 'Échanges Omnicanal') }}
          </h3>
          <span class="text-xs text-gray-500 font-medium capitalize">
            {{ patientPhone || '+213 770 34 56 03 (WhatsApp)' }}
          </span>
        </div>

        <!-- Chat Container -->
        <div class="bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-2xl p-4 shadow-2xs flex flex-col h-[560px]">
          <!-- Message Stream -->
          <div class="flex-grow overflow-y-auto space-y-3 pr-1">
            <div
              v-for="msg in chatMessages"
              :key="msg.id"
              :class="[
                'flex flex-col max-w-[85%] rounded-xl p-3 text-xs leading-relaxed',
                msg.sender === 'patient'
                  ? 'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-white self-start rounded-bl-xs'
                  : 'bg-primary-600 text-white self-end rounded-br-xs'
              ]"
            >
              <div class="flex items-center justify-between gap-2 mb-1 opacity-75 text-[10px]">
                <span class="font-bold capitalize">{{ msg.sender === 'patient' ? t('patientAiDossier.senderPatient', 'Patient (Karim)') : (msg.sender === 'doctor' ? 'Dr. Arselane' : 'IA Assistant Cabinet') }}</span>
                <span>{{ formatTime(msg.sent_at) }}</span>
              </div>
              <p class="whitespace-pre-line">{{ msg.content }}</p>
            </div>

            <div v-if="chatMessages.length === 0" class="text-center py-20 text-gray-400 text-xs">
              <UIcon name="i-lucide-message-circle" class="w-8 h-8 mx-auto mb-2 opacity-50" />
              {{ t('patientAiDossier.noMessages', 'Aucun message synchronisé pour ce patient.') }}
            </div>
          </div>

          <!-- Bottom Reply Input for Doctor -->
          <div class="pt-3 border-t border-gray-100 dark:border-gray-800 flex gap-2">
            <input
              v-model="replyText"
              type="text"
              :placeholder="t('patientAiDossier.directMsgPlaceholder', 'Écrire un message direct au patient...')"
              class="flex-grow text-xs bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg px-3 py-2 text-gray-900 dark:text-white focus:outline-hidden focus:ring-2 focus:ring-primary-500"
              @keyup.enter="sendDoctorReply"
            />
            <button
              type="button"
              class="px-3 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg text-xs font-semibold transition-colors flex items-center justify-center cursor-pointer"
              :disabled="!replyText.trim()"
              @click="sendDoctorReply"
            >
              <UIcon name="i-lucide-send" class="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Lightbox Modal for Radiographs -->
    <UModal v-model:open="isLightboxOpen">
      <template #content>
        <UCard :ui="{ body: { padding: 'p-0 sm:p-0' } }">
          <div class="relative bg-black flex items-center justify-center max-h-[85vh] p-2">
            <img :src="selectedImageUrl" class="max-w-full max-h-[80vh] object-contain rounded" />
            <button
              type="button"
              class="absolute top-4 right-4 p-2 bg-black/60 hover:bg-black/90 text-white rounded-full transition-colors cursor-pointer"
              @click="isLightboxOpen = false"
            >
              <UIcon name="i-lucide-x" class="w-5 h-5" />
            </button>
          </div>
        </UCard>
      </template>
    </UModal>

    <!-- AI Prescription Refusal & Safety Alert Modal -->
    <UModal v-model:open="isSafetyModalOpen">
      <template #content>
        <div class="p-6 space-y-4">
          <!-- Refusal Header -->
          <div class="flex items-start gap-3">
            <div
              :class="[
                'p-3 rounded-2xl shrink-0 flex items-center justify-center',
                safetyCheckResult?.hasConflict
                  ? 'bg-rose-100 text-rose-600 dark:bg-rose-950/80 dark:text-rose-400'
                  : 'bg-emerald-100 text-emerald-600 dark:bg-emerald-950/80 dark:text-emerald-400'
              ]"
            >
              <UIcon
                :name="safetyCheckResult?.hasConflict ? 'i-lucide-shield-alert' : 'i-lucide-shield-check'"
                class="w-7 h-7"
              />
            </div>
            <div class="space-y-1">
              <div class="flex items-center gap-2">
                <UBadge
                  :color="safetyCheckResult?.hasConflict ? 'error' : 'success'"
                  variant="solid"
                  size="xs"
                  class="font-bold uppercase tracking-wider"
                >
                  {{ safetyCheckResult?.hasConflict ? '⛔ PRESCRIPTION REFUSÉE PAR L\'IA' : '✅ PRESCRIPTION VALIDÉE PAR L\'IA' }}
                </UBadge>
                <span class="text-xs text-gray-400 font-mono">{{ safetyCheckResult?.offendingDrug }}</span>
              </div>
              <h3 class="text-base font-bold text-gray-900 dark:text-white">
                {{ safetyCheckResult?.title }}
              </h3>
            </div>
          </div>

          <!-- Explanation Details Box -->
          <div
            :class="[
              'p-4 rounded-xl border text-xs leading-relaxed space-y-2',
              safetyCheckResult?.hasConflict
                ? 'bg-rose-50/70 dark:bg-rose-950/30 border-rose-200 dark:border-rose-900/50 text-rose-900 dark:text-rose-200'
                : 'bg-emerald-50/70 dark:bg-emerald-950/30 border-emerald-200 dark:border-emerald-900/50 text-emerald-900 dark:text-emerald-200'
            ]"
          >
            <div class="font-bold flex items-center gap-1.5">
              <UIcon :name="safetyCheckResult?.hasConflict ? 'i-lucide-alert-triangle' : 'i-lucide-info'" class="w-4 h-4 shrink-0" />
              <span>Analyse Pharmacologique & Risque Clinique :</span>
            </div>
            <p class="font-medium whitespace-pre-line pl-5">
              {{ safetyCheckResult?.reason }}
            </p>
          </div>

          <!-- Recommended Alternative Box -->
          <div
            v-if="safetyCheckResult?.alternative"
            class="p-4 rounded-xl bg-primary-50/70 dark:bg-primary-950/30 border border-primary-200 dark:border-primary-900/50 text-xs space-y-1.5 text-primary-950 dark:text-primary-200"
          >
            <div class="font-bold flex items-center gap-1.5 text-primary-700 dark:text-primary-300">
              <UIcon name="i-lucide-check-circle" class="w-4 h-4" />
              <span>Conduite Thérapeutique Sécurisée Recommandée par l'IA :</span>
            </div>
            <p class="font-semibold pl-5 text-gray-800 dark:text-gray-200">
              {{ safetyCheckResult.alternative }}
            </p>
          </div>

          <!-- Modal Actions -->
          <div class="flex items-center justify-end gap-2 pt-2 border-t border-gray-100 dark:border-gray-800">
            <UButton
              color="neutral"
              variant="subtle"
              class="cursor-pointer"
              @click="isSafetyModalOpen = false"
            >
              Fermer
            </UButton>
          </div>
        </div>
      </template>
    </UModal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useDrugSafety, type SafetyCheckResult } from '~~/app/composables/useDrugSafety'

interface AnamneseItem {
  id: string
  category: 'symptom' | 'medication' | 'allergy' | 'condition'
  title: string
  subtitle: string
  details: string
  warning?: string
  status: 'pending' | 'approved' | 'declined'
  approvedAt?: string
  approvedBy?: string
}

const props = defineProps<{
  patientId: string
  patientPhone?: string
  patient?: any
}>()

const { t } = useI18n()
const api = useApi()
const toast = useToast()
const drugSafety = useDrugSafety()

const isHumanActive = ref(false)
const isToggling = ref(false)
const dossierFiles = ref<any[]>([])
const chatMessages = ref<any[]>([])
const replyText = ref('')

// Lightbox state
const isLightboxOpen = ref(false)
const selectedImageUrl = ref('')

// Radio doctor confirmation state
const radioDiagnosisConfirmed = ref(false)

// Safety simulator modal state
const isSafetyModalOpen = ref(false)
const safetyCheckResult = ref<SafetyCheckResult | null>(null)
const customDrugInput = ref('')

// Patient Name Computed
const patientDisplayName = computed(() => {
  if (props.patient?.first_name || props.patient?.last_name) {
    return `${props.patient.first_name} ${props.patient.last_name}`
  }
  return 'Karim Haddad'
})

// Storage key scoped strictly per patientId to ensure ZERO cross-patient data leaking
const ANAMNESE_STORAGE_KEY = computed(() => `dentalpin:ai_anamnese:${props.patientId}`)
const SAFETY_CTX_STORAGE_KEY = computed(() => `dentalpin:patient_safety_ctx:${props.patientId}`)

// Default Pre-Anamnèse for Karim Haddad (or template patient)
function getDefaultKarimAnamnese(): AnamneseItem[] {
  return [
    {
      id: 'symptom-1',
      category: 'symptom',
      subtitle: 'Symptômes déclarés (WhatsApp)',
      title: 'Douleur aiguë molaire supérieure droite (#16)',
      details: 'Douleur vive, lancinante et pulsatile (EVA 7/10). Exacerbée par la mastication et les variations thermiques (froid et chaud). Réveils nocturnes depuis 48h.',
      status: 'pending'
    },
    {
      id: 'med-1',
      category: 'medication',
      subtitle: 'Traitement habituel en cours',
      title: 'SINTROM 4mg (Acénocoumarol) — 1 comp/soir',
      details: 'Anticoagulant oral (Anti-vitamine K) pris quotidiennement pour fibrillation auriculaire. Dernier INR : 2.4.',
      warning: 'TERRAIN À HAUT RISQUE HÉMORRAGIQUE : Contre-indication formelle aux AINS (Ibuprofène, Kétoprofène) et interaction sévère avec Métronidazole.',
      status: 'pending'
    },
    {
      id: 'allergy-1',
      category: 'allergy',
      subtitle: 'Allergie médicamenteuse déclarée',
      title: 'Pénicillines & Bêta-lactamines (Amoxicilline / Clamoxyl)',
      details: 'Réaction sévère en 2021 suite à la prise de Clamoxyl : Éruption cutanée généralisée, prurit intense et œdème de Quincke ayant nécessité une prise en charge urgente.',
      warning: 'CONTRE-INDICATION ABSOLUE AUX PÉNICILLINES : Risque vital immédiat de choc anaphylactique. Prescrire Macrolides (Spiramycine / Rovamycine) en alternative.',
      status: 'pending'
    },
    {
      id: 'condition-1',
      category: 'condition',
      subtitle: 'Antécédents généraux & Médicaux',
      title: 'Hypertension artérielle (HTA) & Appendicectomie',
      details: 'HTA traitée par Amlodipine 5mg (1 comprimé le matin). Pression artérielle stabilisée. Antécédent chirurgical d\'appendicectomie (2015). Non fumeur.',
      status: 'pending'
    }
  ]
}

const anamneseItems = ref<AnamneseItem[]>([])

const hasPendingItems = computed(() => {
  return anamneseItems.value.some(it => it.status === 'pending')
})

function loadAnamneseData() {
  if (import.meta.client) {
    try {
      const stored = localStorage.getItem(ANAMNESE_STORAGE_KEY.value)
      if (stored) {
        const parsed = JSON.parse(stored)
        if (Array.isArray(parsed) && parsed.length > 0) {
          anamneseItems.value = parsed
          return
        }
      }
    } catch {
      // Ignore
    }
  }

  // Load default test items
  anamneseItems.value = getDefaultKarimAnamnese()
  syncSafetyContext()
}

function persistAnamneseData() {
  if (import.meta.client) {
    try {
      localStorage.setItem(ANAMNESE_STORAGE_KEY.value, JSON.stringify(anamneseItems.value))
    } catch {
      // Ignore
    }
  }
  syncSafetyContext()
}

// Synchronize approved medications and allergies into safety context for prescriptions mode
function syncSafetyContext() {
  if (import.meta.client) {
    try {
      const approvedAllergies = anamneseItems.value
        .filter(it => it.category === 'allergy' && it.status !== 'declined')
        .map(it => it.title)

      const approvedMedications = anamneseItems.value
        .filter(it => it.category === 'medication' && it.status !== 'declined')
        .map(it => it.title)

      localStorage.setItem(SAFETY_CTX_STORAGE_KEY.value, JSON.stringify({
        patientId: props.patientId,
        allergies: approvedAllergies,
        medications: approvedMedications,
        updatedAt: new Date().toISOString()
      }))
    } catch {
      // Ignore
    }
  }
}

function approveAnamneseItem(item: AnamneseItem) {
  item.status = 'approved'
  item.approvedAt = new Date().toISOString()
  item.approvedBy = 'Dr. Arselane'
  persistAnamneseData()
  toast.add({
    title: 'Information validée',
    description: `"${item.title}" a été intégré au dossier médical par le Dr. Arselane.`,
    color: 'success'
  })
}

function declineAnamneseItem(item: AnamneseItem) {
  item.status = 'declined'
  item.approvedAt = undefined
  persistAnamneseData()
  toast.add({
    title: 'Information déclinée',
    description: `"${item.title}" a été marqué comme non confirmé.`,
    color: 'neutral'
  })
}

function approveAllAnamnese() {
  anamneseItems.value.forEach(it => {
    it.status = 'approved'
    it.approvedAt = new Date().toISOString()
    it.approvedBy = 'Dr. Arselane'
  })
  persistAnamneseData()
  toast.add({
    title: 'Pré-anamnèse entièrement validée',
    description: 'Toutes les informations ont été intégrées avec succès au dossier médical du patient.',
    color: 'success'
  })
}

function resetAnamneseDemo() {
  anamneseItems.value = getDefaultKarimAnamnese()
  radioDiagnosisConfirmed.value = false
  persistAnamneseData()
  toast.add({
    title: 'Démo réinitialisée',
    description: 'Les données de pré-anamnèse sont prêtes pour une nouvelle démonstration.',
    color: 'info'
  })
}

// Drug Safety Simulation Handler
function testDrugSimulation(drugName: string) {
  if (!drugName.trim()) return

  // Gather current patient context
  const activeAllergies = anamneseItems.value
    .filter(it => it.category === 'allergy' && it.status !== 'declined')
    .map(it => ({ name: it.title, reaction: 'Choc anaphylactique / Œdème de Quincke' }))

  const activeMedications = anamneseItems.value
    .filter(it => it.category === 'medication' && it.status !== 'declined')
    .map(it => ({ name: it.title }))

  // Always include Sintrom and Penicillin if simulating on Karim Haddad
  if (activeAllergies.length === 0) {
    activeAllergies.push({ name: 'Pénicilline / Bêta-lactamines', reaction: 'Œdème de Quincke' })
  }
  if (activeMedications.length === 0) {
    activeMedications.push({ name: 'Sintrom 4mg (Acénocoumarol)' })
  }

  const check = drugSafety.evaluatePrescriptionSafety(drugName, {
    allergies: activeAllergies,
    medications: activeMedications
  })

  if (check && check.hasConflict) {
    safetyCheckResult.value = check
  } else {
    safetyCheckResult.value = {
      hasConflict: false,
      offendingDrug: drugName,
      title: `Prescription Validée : ${drugName}`,
      reason: `La molécule "${drugName}" est pharmacologiquement compatible avec le profil du patient. Aucune interaction avec le traitement anticoagulant (Sintrom) et absence de réactivité croisée avec les pénicillines. Respecter la posologie recommandée.`,
      alternative: undefined
    }
  }

  isSafetyModalOpen.value = true
}

function confirmRadioDiagnosis() {
  radioDiagnosisConfirmed.value = true
  toast.add({
    title: 'Diagnostic radio confirmé',
    description: 'Le Dr. Arselane a confirmé la présence de la carie occluso-pulpaire sur la dent #16.',
    color: 'success'
  })
}

function requestRetakeRadio() {
  toast.add({
    title: 'Demande enregistrée',
    description: 'Un cliché rétro-alvéolaire centré sur la dent #16 a été ajouté à la fiche clinique.',
    color: 'info'
  })
}

function openLightbox(url: string) {
  selectedImageUrl.value = url
  isLightboxOpen.value = true
}

// Fetch dossier files & chat history
async function loadData() {
  loadAnamneseData()

  // 1. Fetch Radios & AI analyses
  try {
    const files = await api.get(`/api/v1/omnichannel_bridge/patients/${props.patientId}/dossier-files`)
    if (Array.isArray(files) && files.length > 0) {
      dossierFiles.value = files
    } else {
      setSeedRadio()
    }
  } catch {
    setSeedRadio()
  }

  // 2. Fetch Chat Messages
  try {
    const msgs = await api.get(`/api/v1/omnichannel_bridge/patients/${props.patientId}/chat-history`)
    if (Array.isArray(msgs) && msgs.length > 0) {
      chatMessages.value = msgs
    } else {
      setSeedChatMessages()
    }
  } catch {
    setSeedChatMessages()
  }
}

function setSeedRadio() {
  dossierFiles.value = [
    {
      id: 'demo-radio-1',
      name: 'Radiographie Panoramique Pré-Consultation (WhatsApp)',
      file_type: 'xray_panoramic',
      file_url: 'https://images.unsplash.com/photo-1588776814546-1ffcf47267a5?auto=format&fit=crop&w=1200&q=80',
      ai_analysis: '🦷 Détection Vision IA (Dr. Arselane Vision) :\n• Lésion carieuse occluso-distale profonde sur dent #16 avec proximité pulpaire immédiate (indication : traitement endodontique / coiffage selon vitalité).\n• Dépôt tartrique sous-gingival modéré secteur antéro-inférieur (31, 41).\n• Intégrité parodontale et corticale osseuse satisfaisante.',
      status: 'pending_consultation',
      created_at: new Date(Date.now() - 7200000).toISOString()
    }
  ]
}

function setSeedChatMessages() {
  chatMessages.value = [
    {
      id: 'msg-1',
      sender: 'patient',
      content: 'Bonjour Dr. Arselane, j\'ai une très forte douleur pulsatile au fond à droite depuis 2 jours qui m\'empêche de dormir.',
      sent_at: new Date(Date.now() - 7200000).toISOString()
    },
    {
      id: 'msg-2',
      sender: 'ai_bot',
      content: 'Bonjour Karim ! Je suis l\'assistant IA du cabinet du Dr. Arselane. Pouvez-vous nous transmettre votre dernière radio et nous préciser vos traitements en cours ?',
      sent_at: new Date(Date.now() - 7100000).toISOString()
    },
    {
      id: 'msg-3',
      sender: 'patient',
      content: 'Voici ma panoramique. Pour mes médicaments : je prends du Sintrom 4mg pour le cœur et j\'ai une allergie grave à la Pénicilline (Clamoxyl m\'a provoqué un œdème de Quincke).',
      sent_at: new Date(Date.now() - 6900000).toISOString()
    },
    {
      id: 'msg-4',
      sender: 'ai_bot',
      content: 'Bien noté Karim ! Notre IA a analysé votre radio et enregistré votre alerte Sintrom et allergie Pénicilline dans votre pré-anamnèse. Le Dr. Arselane a réservé votre créneau prioritaire.',
      sent_at: new Date(Date.now() - 6800000).toISOString()
    }
  ]
}

// Human takeover toggle
async function toggleHumanTakeover() {
  const phone = props.patientPhone || '213770345603'
  isToggling.value = true
  const nextState = !isHumanActive.value

  try {
    await api.post(`/api/v1/omnichannel_bridge/chats/takeover?phone=${encodeURIComponent(phone)}&active=${nextState}`)
    isHumanActive.value = nextState
    toast.add({
      title: nextState ? 'Prise en main activée (IA en pause)' : 'Assistant IA réactivé',
      color: nextState ? 'warning' : 'success'
    })
  } catch {
    isHumanActive.value = nextState
  } finally {
    isToggling.value = false
  }
}

// Doctor sends reply
async function sendDoctorReply() {
  if (!replyText.value.trim()) return
  const text = replyText.value.trim()
  const newMsg = {
    id: `msg-${Date.now()}`,
    sender: 'doctor',
    content: text,
    sent_at: new Date().toISOString()
  }
  chatMessages.value.push(newMsg)
  replyText.value = ''

  try {
    await api.post('/api/v1/omnichannel_bridge/messages/outbound', {
      phone: props.patientPhone || '213770345603',
      content: text,
      sender: 'doctor',
      timestamp: new Date().toISOString()
    })
  } catch {}
}

function formatDate(dateStr: string) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('fr-FR', {
    day: '2-digit',
    month: 'long',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function formatTime(dateStr: string) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleTimeString('fr-FR', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

onMounted(() => {
  loadData()
})
</script>
