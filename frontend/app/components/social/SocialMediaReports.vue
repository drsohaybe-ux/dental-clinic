<template>
  <div class="p-4 sm:p-6 max-w-[1400px] mx-auto space-y-6">
    <!-- Top Navigation Sub-Tabs -->
    <div class="flex items-center gap-2 border-b border-gray-200 dark:border-gray-800 pb-3">
      <NuxtLink
        to="/social/posts"
        class="inline-flex items-center gap-2 px-3.5 py-2 text-sm font-medium rounded-lg text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white transition-colors"
      >
        <UIcon
          name="i-lucide-file-text"
          class="w-4 h-4 text-gray-400"
        />
        <span>{{ t('social.tabStudio', 'Studio de Contenu & Validation') }}</span>
      </NuxtLink>

      <NuxtLink
        to="/social/reports"
        class="inline-flex items-center gap-2 px-3.5 py-2 text-sm font-semibold rounded-lg bg-white dark:bg-gray-800 text-[#0084ff] dark:text-[#38bdf8] shadow-xs border border-gray-200 dark:border-gray-700 transition-colors"
      >
        <UIcon
          name="i-lucide-bar-chart-3"
          class="w-4 h-4 text-[#0084ff] dark:text-[#38bdf8]"
        />
        <span>{{ t('social.tabReports', 'Rapports & Statistiques Réseaux') }}</span>
        <span class="text-[10px] px-2 py-0.5 rounded-full font-medium bg-emerald-50 text-emerald-600 dark:bg-emerald-950/50 dark:text-emerald-400">
          {{ t('social.syncN8n', 'Sync n8n') }}
        </span>
      </NuxtLink>
    </div>

    <!-- Page Header & Actions -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold tracking-tight text-gray-900 dark:text-white flex items-center gap-2">
          <span>{{ t('socialReports.title', 'Performance & Analytics Réseaux Sociaux') }}</span>
          <span
            v-if="isDemoMode"
            class="text-xs px-2.5 py-0.5 rounded-full font-semibold bg-amber-50 text-amber-700 border border-amber-200 dark:bg-amber-950/40 dark:text-amber-400 dark:border-amber-800"
          >
            {{ t('socialReports.modeDemo', 'Mode Aperçu / Démo') }}
          </span>
          <span
            v-else
            class="text-xs px-2.5 py-0.5 rounded-full font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-400 dark:border-emerald-800"
          >
            {{ t('socialReports.modeReal', 'Données Réelles') }}
          </span>
        </h1>
        <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
          {{ t('socialReports.subtitle', 'Mesurez la croissance de vos abonnés, votre portée quotidienne et les conversions vers les prises de rendez-vous.') }}
        </p>
      </div>

      <!-- Action Buttons -->
      <div class="flex flex-wrap items-center gap-2 sm:gap-3">
        <!-- Toggle Demo Mode -->
        <button
          type="button"
          class="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-semibold rounded-lg border transition-colors shadow-2xs"
          :class="[
            isDemoMode
              ? 'bg-amber-50 dark:bg-amber-950/30 text-amber-800 dark:text-amber-300 border-amber-200 dark:border-amber-800 hover:bg-amber-100'
              : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 border-gray-200 dark:border-gray-700 hover:bg-gray-50'
          ]"
          @click="toggleDemoMode"
        >
          <UIcon
            :name="isDemoMode ? 'i-lucide-sparkles' : 'i-lucide-database'"
            class="w-3.5 h-3.5"
          />
          <span>{{ isDemoMode ? t('socialReports.btnDemoActive', 'Mode Démo (Actif)') : t('socialReports.btnRealActive', 'Mode Réel (Actif)') }}</span>
        </button>

        <!-- n8n Config Modal Button -->
        <button
          type="button"
          class="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-semibold text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700/60 shadow-2xs transition-colors"
          @click="isN8nModalOpen = true"
        >
          <UIcon
            name="i-lucide-settings"
            class="w-3.5 h-3.5 text-gray-500"
          />
          <span>{{ t('socialReports.btnN8nConnect', 'Connexion n8n') }}</span>
        </button>

        <!-- Export CSV Button -->
        <button
          type="button"
          :disabled="!filteredRecords.length"
          class="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-semibold text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700/60 shadow-2xs transition-colors disabled:opacity-50"
          @click="exportToCsv"
        >
          <UIcon
            name="i-lucide-download"
            class="w-3.5 h-3.5 text-gray-500"
          />
          <span>{{ t('socialReports.btnExportCsv', 'Exporter CSV') }}</span>
        </button>

        <!-- Refresh / Sync Button -->
        <button
          type="button"
          :disabled="isLoading || isSyncing"
          class="inline-flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold text-white bg-[#0084ff] hover:bg-[#0073e6] rounded-lg shadow-sm transition-colors disabled:opacity-50"
          @click="handleSync"
        >
          <UIcon
            name="i-lucide-refresh-cw"
            class="w-3.5 h-3.5"
            :class="{ 'animate-spin': isLoading || isSyncing }"
          />
          <span>{{ isSyncing ? t('common.syncing', 'Synchronisation...') : t('common.refresh', 'Actualiser') }}</span>
        </button>
      </div>
    </div>

    <!-- Demo Mode Notice Banner -->
    <div
      v-if="isDemoMode"
      class="p-4 rounded-xl bg-gradient-to-r from-amber-50 to-orange-50 dark:from-amber-950/30 dark:to-orange-950/20 border border-amber-200/80 dark:border-amber-900/50 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-2xs"
    >
      <div class="flex items-center gap-3">
        <div class="p-2 bg-amber-100 dark:bg-amber-900/60 rounded-lg text-amber-700 dark:text-amber-300">
          <UIcon
            name="i-lucide-info"
            class="w-5 h-5"
          />
        </div>
        <div>
          <h2 class="text-sm font-bold text-amber-900 dark:text-amber-200">
            {{ t('socialReports.demoBannerTitle', 'Aperçu Interactif (Mode Démo)') }}
          </h2>
          <p class="text-xs text-amber-700/90 dark:text-amber-400 mt-0.5">
            {{ t('socialReports.demoBannerDesc', "Votre workflow n8n n'a pas encore transmis de données en direct. Cet écran affiche une simulation complète et réaliste pour tester l'ensemble du rapport.") }}
          </p>
        </div>
      </div>
      <div class="flex items-center gap-2 self-end sm:self-auto shrink-0">
        <button
          type="button"
          class="px-3 py-1.5 text-xs font-semibold bg-amber-600 hover:bg-amber-700 text-white rounded-lg transition-colors shadow-2xs"
          @click="seedBackendDemoData"
        >
          {{ t('socialReports.btnSaveToDb', 'Enregistrer dans la BD') }}
        </button>
        <button
          type="button"
          class="px-3 py-1.5 text-xs font-semibold bg-white dark:bg-gray-800 text-amber-900 dark:text-amber-200 border border-amber-200 dark:border-amber-800 rounded-lg hover:bg-amber-50 transition-colors shadow-2xs"
          @click="isN8nModalOpen = true"
        >
          {{ t('socialReports.btnGuideN8n', 'Guide n8n') }}
        </button>
      </div>
    </div>

    <!-- Empty State when in Live Mode but NO records exist -->
    <div
      v-if="!isDemoMode && !hasLiveRecords"
      class="p-10 text-center bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 space-y-4 shadow-xs"
    >
      <div class="w-16 h-16 bg-blue-50 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400 rounded-2xl flex items-center justify-center mx-auto shadow-inner">
        <UIcon
          name="i-lucide-activity"
          class="w-8 h-8"
        />
      </div>
      <div class="max-w-md mx-auto">
        <h3 class="text-lg font-bold text-gray-900 dark:text-white">
          {{ t('socialReports.emptyTitle', 'En attente de la première synchronisation n8n') }}
        </h3>
        <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
          {{ t('socialReports.emptyDesc', "Aucune donnée réelle n'a encore été enregistrée dans la base PostgreSQL. Vous pouvez activer le mode Démo pour visualiser immédiatement les fonctionnalités ou connecter votre workflow n8n.") }}
        </p>
      </div>
      <div class="flex flex-wrap items-center justify-center gap-3 pt-2">
        <button
          type="button"
          class="px-4 py-2 text-xs font-semibold text-white bg-[#0084ff] hover:bg-[#0073e6] rounded-lg shadow-sm transition-colors"
          @click="toggleDemoMode"
        >
          {{ t('socialReports.btnEnableDemo', 'Activer le Mode Démo (Recommandé)') }}
        </button>
        <button
          type="button"
          class="px-4 py-2 text-xs font-semibold text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 shadow-2xs transition-colors"
          @click="seedBackendDemoData"
        >
          {{ t('socialReports.btnInjectTestData', 'Injecter 30 Jours de Test') }}
        </button>
        <button
          type="button"
          class="px-4 py-2 text-xs font-semibold text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 shadow-2xs transition-colors"
          @click="isN8nModalOpen = true"
        >
          {{ t('socialReports.btnN8nInstructions', 'Instructions n8n') }}
        </button>
      </div>
    </div>

    <!-- Active Analytics Content -->
    <template v-else>
      <!-- Filters Row (Platform + Date Range) -->
      <div class="p-4 bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 shadow-2xs flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <!-- Platform Selector -->
        <div class="flex items-center gap-2">
          <span class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
            {{ t('socialReports.platformLabel', 'Plateforme :') }}
          </span>
          <div class="inline-flex p-1 bg-gray-100 dark:bg-gray-800 rounded-lg">
            <button
              type="button"
              :class="[
                'px-3 py-1 text-xs font-semibold rounded-md transition-all',
                activePlatform === 'all'
                  ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-xs'
                  : 'text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
              ]"
              @click="activePlatform = 'all'"
            >
              {{ t('socialReports.allNetworks', 'Tous les Réseaux') }}
            </button>
            <button
              type="button"
              :class="[
                'px-3 py-1 text-xs font-semibold rounded-md transition-all flex items-center gap-1.5',
                activePlatform === 'instagram'
                  ? 'bg-white dark:bg-gray-700 text-[#e1306c] dark:text-[#e1306c] shadow-xs'
                  : 'text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
              ]"
              @click="activePlatform = 'instagram'"
            >
              <UIcon
                name="i-lucide-camera"
                class="w-3.5 h-3.5"
              />
              <span>Instagram</span>
            </button>
            <button
              type="button"
              :class="[
                'px-3 py-1 text-xs font-semibold rounded-md transition-all flex items-center gap-1.5',
                activePlatform === 'facebook'
                  ? 'bg-white dark:bg-gray-700 text-[#1877f2] dark:text-[#1877f2] shadow-xs'
                  : 'text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
              ]"
              @click="activePlatform = 'facebook'"
            >
              <UIcon
                name="i-lucide-facebook"
                class="w-3.5 h-3.5"
              />
              <span>Facebook</span>
            </button>
          </div>
        </div>

        <!-- Date Range Selector -->
        <div class="flex items-center gap-2">
          <span class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
            {{ t('socialReports.periodLabel', 'Période :') }}
          </span>
          <div class="inline-flex p-1 bg-gray-100 dark:bg-gray-800 rounded-lg">
            <button
              v-for="range in dateRangeOptions"
              :key="range.key"
              type="button"
              :class="[
                'px-3 py-1 text-xs font-semibold rounded-md transition-all',
                activeDateRange === range.key
                  ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-xs'
                  : 'text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
              ]"
              @click="activeDateRange = range.key as any"
            >
              {{ range.label }}
            </button>
          </div>
        </div>
      </div>

      <!-- Top 4 KPI Summary Cards -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <!-- 1. Total Followers -->
        <div class="p-5 rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 shadow-2xs">
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              {{ t('socialReports.totalFollowers', 'Abonnés Totaux') }}
            </span>
            <span
              v-if="summaryMetrics.followerGrowth > 0"
              class="text-xs font-semibold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-600 dark:bg-emerald-950/40 dark:text-emerald-400"
            >
              +{{ summaryMetrics.followerGrowth }}
            </span>
            <span
              v-else-if="summaryMetrics.followerGrowth < 0"
              class="text-xs font-semibold px-2 py-0.5 rounded-full bg-rose-50 text-rose-600 dark:bg-rose-950/40 dark:text-rose-400"
            >
              {{ summaryMetrics.followerGrowth }}
            </span>
          </div>
          <div class="text-3xl font-extrabold text-gray-900 dark:text-white mt-3">
            {{ summaryMetrics.totalFollowers.toLocaleString() }}
          </div>
          <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">
            {{ t('socialReports.activeCommunity', 'Communauté cumulée active') }}
          </p>
        </div>

        <!-- 2. Total Reach -->
        <div class="p-5 rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 shadow-2xs">
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              {{ t('socialReports.globalReach', 'Portée Globale') }}
            </span>
            <span class="text-xs font-semibold px-2 py-0.5 rounded-full bg-blue-50 text-blue-600 dark:bg-blue-950/40 dark:text-blue-400">
              {{ t('socialReports.uniqueAccounts', 'Comptes Uniques') }}
            </span>
          </div>
          <div class="text-3xl font-extrabold text-blue-600 dark:text-blue-400 mt-3">
            {{ summaryMetrics.totalReach.toLocaleString() }}
          </div>
          <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">
            {{ t('socialReports.reachPerDay', { count: summaryMetrics.avgDailyReach.toLocaleString() }) }}
          </p>
        </div>

        <!-- 3. Profile Visits -->
        <div class="p-5 rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 shadow-2xs">
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              {{ t('socialReports.profileVisits', 'Visites du Profil') }}
            </span>
            <span class="text-xs font-semibold px-2 py-0.5 rounded-full bg-purple-50 text-purple-600 dark:bg-purple-950/40 dark:text-purple-400">
              {{ t('socialReports.intent', 'Intention') }}
            </span>
          </div>
          <div class="text-3xl font-extrabold text-purple-600 dark:text-purple-400 mt-3">
            {{ summaryMetrics.totalProfileViews.toLocaleString() }}
          </div>
          <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">
            {{ t('socialReports.bioViews', 'Consultations de la bio & coordonnées') }}
          </p>
        </div>

        <!-- 4. Website / Booking Clicks -->
        <div class="p-5 rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 shadow-2xs">
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              {{ t('socialReports.siteBookingClicks', 'Clics Site & Rendez-vous') }}
            </span>
            <span class="text-xs font-semibold px-2 py-0.5 rounded-full bg-amber-50 text-amber-600 dark:bg-amber-950/40 dark:text-amber-400">
              {{ t('socialReports.conversions', 'Conversions') }}
            </span>
          </div>
          <div class="text-3xl font-extrabold text-amber-600 dark:text-amber-400 mt-3">
            {{ summaryMetrics.totalWebsiteClicks.toLocaleString() }}
          </div>
          <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">
            {{ t('socialReports.conversionRateLabel', { rate: summaryMetrics.conversionRate }) }}
          </p>
        </div>
      </div>

      <!-- Charts & Visual Analytics Section -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Main Interactive SVG Trend Area Chart (2 Cols) -->
        <div class="lg:col-span-2 p-5 bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 shadow-2xs space-y-4">
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-gray-100 dark:border-gray-800 pb-3">
            <div>
              <h2 class="text-base font-bold text-gray-900 dark:text-white flex items-center gap-2">
                <span>{{ t('socialReports.chartGrowthTitle', 'Évolution Quotidienne de la Portée & des Visites') }}</span>
              </h2>
              <p class="text-xs text-gray-500 dark:text-gray-400">
                {{ t('socialReports.chartGrowthSubtitle', "Corrélation entre la portée des publications et l'intérêt direct des patients.") }}
              </p>
            </div>
            <!-- Chart Legend -->
            <div class="flex items-center gap-4 text-xs font-medium">
              <div class="flex items-center gap-1.5">
                <span class="w-3 h-3 rounded-full bg-[#0084ff]" />
                <span class="text-gray-600 dark:text-gray-300">{{ t('socialReports.dailyReach', 'Portée Quotidienne') }}</span>
              </div>
              <div class="flex items-center gap-1.5">
                <span class="w-3 h-3 rounded-full bg-[#a855f7]" />
                <span class="text-gray-600 dark:text-gray-300">{{ t('socialReports.profileVisitsShort', 'Visites Profil') }}</span>
              </div>
            </div>
          </div>

          <!-- Responsive SVG Chart -->
          <div class="relative w-full h-[260px] pt-4">
            <svg
              v-if="chartTrendPoints.length > 1"
              viewBox="0 0 800 240"
              class="w-full h-full overflow-visible"
              preserveAspectRatio="none"
            >
              <defs>
                <linearGradient
                  id="reachGradient"
                  x1="0"
                  y1="0"
                  x2="0"
                  y2="1"
                >
                  <stop
                    offset="0%"
                    stop-color="#0084ff"
                    stop-opacity="0.35"
                  />
                  <stop
                    offset="100%"
                    stop-color="#0084ff"
                    stop-opacity="0.0"
                  />
                </linearGradient>
                <linearGradient
                  id="viewsGradient"
                  x1="0"
                  y1="0"
                  x2="0"
                  y2="1"
                >
                  <stop
                    offset="0%"
                    stop-color="#a855f7"
                    stop-opacity="0.3"
                  />
                  <stop
                    offset="100%"
                    stop-color="#a855f7"
                    stop-opacity="0.0"
                  />
                </linearGradient>
              </defs>

              <!-- Grid Horizontal Guide Lines -->
              <line
                x1="0"
                y1="40"
                x2="800"
                y2="40"
                stroke="currentColor"
                class="text-gray-100 dark:text-gray-800"
                stroke-dasharray="3 3"
              />
              <line
                x1="0"
                y1="110"
                x2="800"
                y2="110"
                stroke="currentColor"
                class="text-gray-100 dark:text-gray-800"
                stroke-dasharray="3 3"
              />
              <line
                x1="0"
                y1="180"
                x2="800"
                y2="180"
                stroke="currentColor"
                class="text-gray-100 dark:text-gray-800"
                stroke-dasharray="3 3"
              />

              <!-- Reach Area Fill & Stroke -->
              <polygon
                :points="reachAreaPoints"
                fill="url(#reachGradient)"
              />
              <polyline
                :points="reachLinePoints"
                fill="none"
                stroke="#0084ff"
                stroke-width="2.5"
                stroke-linecap="round"
                stroke-linejoin="round"
              />

              <!-- Views Area Fill & Stroke -->
              <polygon
                :points="viewsAreaPoints"
                fill="url(#viewsGradient)"
              />
              <polyline
                :points="viewsLinePoints"
                fill="none"
                stroke="#a855f7"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
            </svg>

            <!-- Fallback if only 1 data point -->
            <div
              v-else
              class="flex items-center justify-center h-full text-xs text-gray-400"
            >
              {{ t('socialReports.collectingData', 'Collecte de données en cours...') }}
            </div>
          </div>

          <!-- Chart X-Axis Labels -->
          <div class="flex justify-between text-[11px] text-gray-400 dark:text-gray-500 pt-1 border-t border-gray-100 dark:border-gray-800">
            <span>{{ chartTrendPoints[0]?.date || '' }}</span>
            <span>{{ t('socialReports.midPeriod', 'Milieu de période') }}</span>
            <span>{{ chartTrendPoints[chartTrendPoints.length - 1]?.date || '' }}</span>
          </div>
        </div>

        <!-- Marketing-to-Clinic Funnel Card (1 Col) -->
        <div class="p-5 bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 shadow-2xs space-y-4 flex flex-col justify-between">
          <div>
            <h2 class="text-base font-bold text-gray-900 dark:text-white">
              {{ t('socialReports.funnelTitle', 'Entonnoir de Conversion Patient') }}
            </h2>
            <p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
              {{ t('socialReports.funnelSubtitle', "Du premier contact visuel jusqu'à la réservation de consultation.") }}
            </p>
          </div>

          <div class="space-y-3 my-auto">
            <!-- Stage 1: Reach -->
            <div class="p-3 rounded-lg bg-blue-50/60 dark:bg-blue-950/30 border border-blue-100 dark:border-blue-900/40">
              <div class="flex items-center justify-between text-xs font-semibold text-blue-900 dark:text-blue-300">
                <span>{{ t('socialReports.funnelStep1', '1. Portée Visuelle') }}</span>
                <span>{{ t('socialReports.funnelAccounts', { count: summaryMetrics.totalReach.toLocaleString() }) }}</span>
              </div>
              <div class="w-full bg-blue-200 dark:bg-blue-900/60 h-2 rounded-full mt-2 overflow-hidden">
                <div class="bg-blue-600 h-full rounded-full w-full" />
              </div>
            </div>

            <!-- Stage 2: Profile Views -->
            <div class="p-3 rounded-lg bg-purple-50/60 dark:bg-purple-950/30 border border-purple-100 dark:border-purple-900/40">
              <div class="flex items-center justify-between text-xs font-semibold text-purple-900 dark:text-purple-300">
                <span>{{ t('socialReports.funnelStep2', '2. Visites Profil / Intérêt') }}</span>
                <span>{{ t('socialReports.funnelVisits', { count: summaryMetrics.totalProfileViews.toLocaleString() }) }}</span>
              </div>
              <div class="w-full bg-purple-200 dark:bg-purple-900/60 h-2 rounded-full mt-2 overflow-hidden">
                <div
                  class="bg-purple-600 h-full rounded-full"
                  :style="{ width: `${Math.min(100, Math.max(15, (summaryMetrics.totalProfileViews / (summaryMetrics.totalReach || 1)) * 1000))}%` }"
                />
              </div>
            </div>

            <!-- Stage 3: Website / Bio Clicks -->
            <div class="p-3 rounded-lg bg-amber-50/60 dark:bg-amber-950/30 border border-amber-100 dark:border-amber-900/40">
              <div class="flex items-center justify-between text-xs font-semibold text-amber-900 dark:text-amber-300">
                <span>{{ t('socialReports.funnelStep3', '3. Clics Lien RDV / WhatsApp') }}</span>
                <span>{{ t('socialReports.funnelClicks', { count: summaryMetrics.totalWebsiteClicks.toLocaleString() }) }}</span>
              </div>
              <div class="w-full bg-amber-200 dark:bg-amber-900/60 h-2 rounded-full mt-2 overflow-hidden">
                <div
                  class="bg-amber-600 h-full rounded-full"
                  :style="{ width: `${Math.min(100, Math.max(20, Number(summaryMetrics.conversionRate) * 2))}%` }"
                />
              </div>
            </div>

            <!-- Stage 4: Estimated Appointments -->
            <div class="p-3 rounded-lg bg-emerald-50/60 dark:bg-emerald-950/30 border border-emerald-100 dark:border-emerald-900/40">
              <div class="flex items-center justify-between text-xs font-semibold text-emerald-900 dark:text-emerald-300">
                <span>{{ t('socialReports.funnelStep4', '4. RDV Estimés au Fauteuil') }}</span>
                <span>{{ t('socialReports.funnelPatients', { count: Math.round(summaryMetrics.totalWebsiteClicks * 0.35) }) }}</span>
              </div>
              <div class="w-full bg-emerald-200 dark:bg-emerald-900/60 h-2 rounded-full mt-2 overflow-hidden">
                <div class="bg-emerald-600 h-full rounded-full w-2/5" />
              </div>
            </div>
          </div>

          <!-- Bottom Summary Indicator -->
          <div class="pt-2 border-t border-gray-100 dark:border-gray-800 flex items-center justify-between text-xs">
            <span class="text-gray-500 dark:text-gray-400">{{ t('socialReports.globalEfficiency', 'Efficacité Globale') }}</span>
            <span class="font-bold text-emerald-600 dark:text-emerald-400">
              {{ t('socialReports.conversionRateText', { rate: summaryMetrics.conversionRate }) }}
            </span>
          </div>
        </div>
      </div>

      <!-- Platform Comparison Breakdown -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <!-- Instagram Card -->
        <div class="p-5 bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 shadow-2xs space-y-3">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <div class="p-2 bg-pink-50 dark:bg-pink-950/40 rounded-lg text-[#e1306c]">
                <UIcon
                  name="i-lucide-camera"
                  class="w-5 h-5"
                />
              </div>
              <div>
                <h3 class="text-sm font-bold text-gray-900 dark:text-white">
                  {{ t('socialReports.instagramPerformance', 'Instagram Performance') }}
                </h3>
                <p class="text-xs text-gray-400">
                  @dr_mokhtar_dental
                </p>
              </div>
            </div>
            <div class="text-right">
              <div class="text-base font-bold text-gray-900 dark:text-white">
                {{ platformBreakdown.instagram.followers.toLocaleString() }}
              </div>
              <span class="text-[11px] text-gray-400">{{ t('socialReports.followers', 'Abonnés') }}</span>
            </div>
          </div>

          <div class="grid grid-cols-2 gap-3 pt-2">
            <div class="p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
              <span class="text-[11px] text-gray-400 font-medium">{{ t('socialReports.periodReach', 'Portée Période') }}</span>
              <div class="text-lg font-bold text-blue-600 dark:text-blue-400 mt-0.5">
                {{ platformBreakdown.instagram.reach.toLocaleString() }}
              </div>
              <span class="text-[10px] text-gray-400">{{ t('socialReports.pctOfTotal', { pct: platformBreakdown.instagram.reachPct }) }}</span>
            </div>
            <div class="p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
              <span class="text-[11px] text-gray-400 font-medium">{{ t('socialReports.bookingClicks', 'Clics RDV') }}</span>
              <div class="text-lg font-bold text-amber-600 dark:text-amber-400 mt-0.5">
                {{ platformBreakdown.instagram.clicks.toLocaleString() }}
              </div>
              <span class="text-[10px] text-gray-400">{{ t('socialReports.pctOfTotal', { pct: platformBreakdown.instagram.clicksPct }) }}</span>
            </div>
          </div>
        </div>

        <!-- Facebook Card -->
        <div class="p-5 bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 shadow-2xs space-y-3">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <div class="p-2 bg-blue-50 dark:bg-blue-950/40 rounded-lg text-[#1877f2]">
                <UIcon
                  name="i-lucide-facebook"
                  class="w-5 h-5"
                />
              </div>
              <div>
                <h3 class="text-sm font-bold text-gray-900 dark:text-white">
                  {{ t('socialReports.facebookPerformance', 'Facebook Performance') }}
                </h3>
                <p class="text-xs text-gray-400">
                  Cabinet Dentaire Dr. Mokhtar
                </p>
              </div>
            </div>
            <div class="text-right">
              <div class="text-base font-bold text-gray-900 dark:text-white">
                {{ platformBreakdown.facebook.followers.toLocaleString() }}
              </div>
              <span class="text-[11px] text-gray-400">{{ t('socialReports.followers', 'Abonnés') }}</span>
            </div>
          </div>

          <div class="grid grid-cols-2 gap-3 pt-2">
            <div class="p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
              <span class="text-[11px] text-gray-400 font-medium">{{ t('socialReports.periodReach', 'Portée Période') }}</span>
              <div class="text-lg font-bold text-blue-600 dark:text-blue-400 mt-0.5">
                {{ platformBreakdown.facebook.reach.toLocaleString() }}
              </div>
              <span class="text-[10px] text-gray-400">{{ t('socialReports.pctOfTotal', { pct: platformBreakdown.facebook.reachPct }) }}</span>
            </div>
            <div class="p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
              <span class="text-[11px] text-gray-400 font-medium">{{ t('socialReports.bookingClicks', 'Clics RDV') }}</span>
              <div class="text-lg font-bold text-amber-600 dark:text-amber-400 mt-0.5">
                {{ platformBreakdown.facebook.clicks.toLocaleString() }}
              </div>
              <span class="text-[10px] text-gray-400">{{ t('socialReports.pctOfTotal', { pct: platformBreakdown.facebook.clicksPct }) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Detailed Daily Performance Log Table -->
      <div class="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 shadow-2xs overflow-hidden">
        <div class="px-5 py-4 border-b border-gray-200 dark:border-gray-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h3 class="text-base font-bold text-gray-900 dark:text-white">
              {{ t('socialReports.dailyLogTitle', 'Journal Quotidien des Métriques') }}
            </h3>
            <p class="text-xs text-gray-500 dark:text-gray-400">
              {{ t('socialReports.dailyLogSubtitle', 'Historique détaillé des instantanés quotidiens synchronisés avec n8n.') }}
            </p>
          </div>
          <div class="flex items-center gap-2">
            <span class="text-xs text-gray-500">
              {{ t('socialReports.recordCount', { count: filteredRecords.length }) }}
            </span>
          </div>
        </div>

        <div class="overflow-x-auto">
          <table class="w-full text-left text-sm text-gray-600 dark:text-gray-300">
            <thead class="bg-gray-50/60 dark:bg-gray-800/40 text-xs uppercase font-semibold text-gray-500 dark:text-gray-400 border-b border-gray-100 dark:border-gray-800">
              <tr>
                <th class="px-5 py-3">
                  {{ t('socialReports.thDate', 'Date') }}
                </th>
                <th class="px-5 py-3">
                  {{ t('socialReports.thNetwork', 'Réseau') }}
                </th>
                <th class="px-5 py-3">
                  {{ t('socialReports.thFollowers', 'Abonnés') }}
                </th>
                <th class="px-5 py-3">
                  {{ t('socialReports.thDailyReach', 'Portée Quotidienne') }}
                </th>
                <th class="px-5 py-3">
                  {{ t('socialReports.thProfileVisits', 'Visites Profil') }}
                </th>
                <th class="px-5 py-3">
                  {{ t('socialReports.thClicks', 'Clics RDV / Bio') }}
                </th>
                <th class="px-5 py-3">
                  {{ t('socialReports.thSaves', 'Enregistrements') }}
                </th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-100 dark:divide-gray-800">
              <tr
                v-for="(item, index) in paginatedRecords"
                :key="item.id || `${item.platform}-${item.date}-${index}`"
                class="hover:bg-gray-50/50 dark:hover:bg-gray-800/50 transition-colors"
              >
                <!-- Date -->
                <td class="px-5 py-3 font-semibold text-gray-900 dark:text-white whitespace-nowrap">
                  {{ item.date }}
                </td>

                <!-- Platform Badge -->
                <td class="px-5 py-3 whitespace-nowrap">
                  <span
                    v-if="item.platform === 'instagram'"
                    class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-pink-50 text-pink-700 dark:bg-pink-950/40 dark:text-pink-300"
                  >
                    <UIcon
                      name="i-lucide-camera"
                      class="w-3 h-3"
                    />
                    <span>Instagram</span>
                  </span>
                  <span
                    v-else
                    class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 dark:bg-blue-950/40 dark:text-blue-300"
                  >
                    <UIcon
                      name="i-lucide-facebook"
                      class="w-3 h-3"
                    />
                    <span>Facebook</span>
                  </span>
                </td>

                <!-- Followers -->
                <td class="px-5 py-3 font-medium">
                  {{ item.total_followers.toLocaleString() }}
                </td>

                <!-- Daily Reach -->
                <td class="px-5 py-3 font-semibold text-blue-600 dark:text-blue-400">
                  {{ item.reach.toLocaleString() }}
                </td>

                <!-- Profile Views -->
                <td class="px-5 py-3 font-medium text-purple-600 dark:text-purple-400">
                  {{ item.profile_views.toLocaleString() }}
                </td>

                <!-- Website Clicks -->
                <td class="px-5 py-3 font-bold text-amber-600 dark:text-amber-400">
                  {{ item.website_clicks.toLocaleString() }}
                </td>

                <!-- Saves -->
                <td class="px-5 py-3 font-medium text-gray-500">
                  {{ item.saves.toLocaleString() }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Table Footer / Pagination Controls -->
        <div
          v-if="totalPages > 1"
          class="px-5 py-3 bg-gray-50/50 dark:bg-gray-800/30 border-t border-gray-100 dark:border-gray-800 flex items-center justify-between text-xs text-gray-500"
        >
          <span>{{ t('socialReports.pagination', { current: currentPage, total: totalPages }) }}</span>
          <div class="flex items-center gap-1">
            <button
              type="button"
              :disabled="currentPage === 1"
              class="px-2.5 py-1 rounded-md border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 disabled:opacity-40"
              @click="currentPage = Math.max(1, currentPage - 1)"
            >
              {{ t('common.previous', 'Précédent') }}
            </button>
            <button
              type="button"
              :disabled="currentPage === totalPages"
              class="px-2.5 py-1 rounded-md border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 disabled:opacity-40"
              @click="currentPage = Math.min(totalPages, currentPage + 1)"
            >
              {{ t('common.next', 'Suivant') }}
            </button>
          </div>
        </div>
      </div>
    </template>

    <!-- n8n Configuration & Webhook Modal -->
    <div
      v-if="isN8nModalOpen"
      class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs"
    >
      <div class="bg-white dark:bg-gray-900 rounded-2xl max-w-2xl w-full border border-gray-200 dark:border-gray-800 shadow-xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        <!-- Modal Header -->
        <div class="p-5 border-b border-gray-100 dark:border-gray-800 flex items-center justify-between">
          <div class="flex items-center gap-2.5">
            <div class="p-2 bg-[#ff6d5a]/10 text-[#ff6d5a] rounded-xl font-black">
              n8n
            </div>
            <div>
              <h3 class="text-base font-bold text-gray-900 dark:text-white">
                {{ t('socialReports.modalN8nTitle', 'Configuration de Synchronisation n8n') }}
              </h3>
              <p class="text-xs text-gray-500 dark:text-gray-400">
                {{ t('socialReports.modalN8nSubtitle', 'Connectez votre workflow scheduled quotidien pour alimenter ce rapport automatiquement.') }}
              </p>
            </div>
          </div>
          <button
            type="button"
            class="p-1.5 text-gray-400 hover:text-gray-600 dark:hover:text-white rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800"
            @click="isN8nModalOpen = false"
          >
            <UIcon
              name="i-lucide-x"
              class="w-5 h-5"
            />
          </button>
        </div>

        <!-- Modal Body -->
        <div class="p-5 space-y-4 max-h-[75vh] overflow-y-auto text-sm">
          <!-- Architecture Choice Card -->
          <div class="p-4 rounded-xl bg-blue-50/60 dark:bg-blue-950/30 border border-blue-100 dark:border-blue-900/40 space-y-2">
            <h4 class="font-bold text-xs uppercase text-blue-900 dark:text-blue-300">
              {{ t('socialReports.modalMethodsTitle', 'Deux Méthodes de Synchronisation Prises en Charge :') }}
            </h4>
            <ul class="text-xs text-blue-800/90 dark:text-blue-300/90 space-y-1 list-disc list-inside">
              <li>{{ t('socialReports.modalOption1') }}</li>
              <li>{{ t('socialReports.modalOption2') }}</li>
            </ul>
          </div>

          <!-- Webhook URL Box -->
          <div>
            <label class="block text-xs font-bold text-gray-700 dark:text-gray-300 mb-1">
              {{ t('socialReports.modalWebhookLabel', "URL du Webhook d'Ingestion :") }}
            </label>
            <div class="flex items-center gap-2">
              <input
                type="text"
                readonly
                :value="webhookUrl"
                class="flex-1 text-xs font-mono bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg px-3 py-2 text-gray-800 dark:text-gray-200 focus:outline-hidden"
              >
              <button
                type="button"
                class="px-3 py-2 text-xs font-semibold bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-200 rounded-lg transition-colors shrink-0"
                @click="copyToClipboard(webhookUrl, t('socialReports.toastWebhookCopied', 'URL du webhook copiée !'))"
              >
                {{ t('socialReports.btnCopy', 'Copier') }}
              </button>
            </div>
          </div>

          <!-- PostgreSQL Table Definition Snippet -->
          <div>
            <div class="flex items-center justify-between mb-1">
              <label class="text-xs font-bold text-gray-700 dark:text-gray-300">
                {{ t('socialReports.modalSqlLabel', 'Structure de la Table PostgreSQL (social_media_insights) :') }}
              </label>
              <button
                type="button"
                class="text-[11px] font-semibold text-[#0084ff] hover:underline"
                @click="copyToClipboard(sqlSchemaCode, t('socialReports.toastSqlCopied', 'Code SQL copié !'))"
              >
                {{ t('socialReports.btnCopySql', 'Copier SQL') }}
              </button>
            </div>
            <pre class="p-3 bg-gray-950 text-emerald-400 font-mono text-[11px] rounded-lg overflow-x-auto"><code>{{ sqlSchemaCode }}</code></pre>
          </div>

          <!-- Payload Example -->
          <div>
            <div class="flex items-center justify-between mb-1">
              <label class="text-xs font-bold text-gray-700 dark:text-gray-300">
                {{ t('socialReports.modalJsonLabel', 'Format du Payload JSON n8n :') }}
              </label>
              <button
                type="button"
                class="text-[11px] font-semibold text-[#0084ff] hover:underline"
                @click="copyToClipboard(samplePayload, t('socialReports.toastJsonCopied', 'Payload JSON copié !'))"
              >
                {{ t('socialReports.btnCopyJson', 'Copier JSON') }}
              </button>
            </div>
            <pre class="p-3 bg-gray-950 text-gray-300 font-mono text-[11px] rounded-lg overflow-x-auto"><code>{{ samplePayload }}</code></pre>
          </div>
        </div>

        <!-- Modal Footer -->
        <div class="p-4 bg-gray-50 dark:bg-gray-800/40 border-t border-gray-100 dark:border-gray-800 flex items-center justify-between">
          <button
            type="button"
            class="px-3.5 py-1.5 text-xs font-semibold text-amber-700 dark:text-amber-300 bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 rounded-lg hover:bg-amber-100 transition-colors"
            @click="seedBackendDemoData"
          >
            {{ t('socialReports.btnTestInject', 'Tester en injectant des données') }}
          </button>
          <button
            type="button"
            class="px-4 py-1.5 text-xs font-semibold text-white bg-[#0084ff] hover:bg-[#0073e6] rounded-lg transition-colors shadow-2xs"
            @click="isN8nModalOpen = false"
          >
            {{ t('common.close', 'Fermer') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useSocialInsights } from '~/composables/useSocialInsights'

const {
  isDemoMode,
  isLoading,
  isSyncing,
  activePlatform,
  activeDateRange,
  hasLiveRecords,
  filteredRecords,
  summaryMetrics,
  chartTrendPoints,
  platformBreakdown,
  fetchInsights,
  syncFromN8n,
  seedBackendDemoData,
  toggleDemoMode,
  exportToCsv
} = useSocialInsights()

const { t } = useI18n()
const toast = useToast()
const isN8nModalOpen = ref(false)
const currentPage = ref(1)
const itemsPerPage = 10

const dateRangeOptions = computed(() => [
  { key: '7d', label: t('socialReports.period7d', '7 Jours') },
  { key: '30d', label: t('socialReports.period30d', '30 Jours') },
  { key: '90d', label: t('socialReports.period90d', '90 Jours') },
  { key: 'all', label: t('socialReports.periodAll', 'Tout') }
])

// Pagination for historical logs table
const totalPages = computed(() => {
  return Math.ceil(filteredRecords.value.length / itemsPerPage) || 1
})

const paginatedRecords = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage
  return filteredRecords.value.slice(start, start + itemsPerPage)
})

// SVG Polyline points for Reach
const reachLinePoints = computed(() => {
  const pts = chartTrendPoints.value
  if (pts.length < 2) return ''
  const maxReach = Math.max(...pts.map(p => p.reach), 1)
  const width = 800
  const height = 240
  const step = width / (pts.length - 1)

  return pts
    .map((p, i) => {
      const x = (i * step).toFixed(1)
      const y = (height - (p.reach / maxReach) * (height - 30) - 15).toFixed(1)
      return `${x},${y}`
    })
    .join(' ')
})

const reachAreaPoints = computed(() => {
  const line = reachLinePoints.value
  if (!line) return ''
  return `0,240 ${line} 800,240`
})

// SVG Polyline points for Profile Views
const viewsLinePoints = computed(() => {
  const pts = chartTrendPoints.value
  if (pts.length < 2) return ''
  const maxViews = Math.max(...pts.map(p => p.views), 1)
  const width = 800
  const height = 240
  const step = width / (pts.length - 1)

  return pts
    .map((p, i) => {
      const x = (i * step).toFixed(1)
      const y = (height - (p.views / maxViews) * (height - 30) - 15).toFixed(1)
      return `${x},${y}`
    })
    .join(' ')
})

const viewsAreaPoints = computed(() => {
  const line = viewsLinePoints.value
  if (!line) return ''
  return `0,240 ${line} 800,240`
})

// Webhook URL
const webhookUrl = computed(() => {
  if (import.meta.client) {
    return `${window.location.origin}/api/automation/insights`
  }
  return 'https://votre-dashboard.com/api/automation/insights'
})

// SQL Schema Snippet
const sqlSchemaCode = `CREATE TABLE IF NOT EXISTS social_media_insights (
    id SERIAL PRIMARY KEY,
    platform VARCHAR(50) NOT NULL, -- 'instagram' ou 'facebook'
    account_id VARCHAR(100) NOT NULL,
    date DATE NOT NULL,
    total_followers INTEGER NOT NULL DEFAULT 0,
    reach INTEGER NOT NULL DEFAULT 0,
    profile_views INTEGER NOT NULL DEFAULT 0,
    website_clicks INTEGER NOT NULL DEFAULT 0,
    saves INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(platform, account_id, date)
);`

// JSON Payload Snippet
const samplePayload = `{
  "platform": "instagram",
  "account_id": "dr_mokhtar_dental",
  "date": "2026-09-06",
  "total_followers": 3580,
  "reach": 2450,
  "profile_views": 142,
  "website_clicks": 38,
  "saves": 28
}`

function copyToClipboard(text: string, title: string) {
  if (!import.meta.client) return
  if (navigator?.clipboard?.writeText) {
    navigator.clipboard.writeText(text).then(() => {
      toast.add({
        title,
        color: 'success'
      })
    }).catch(() => {
      fallbackCopyText(text, title)
    })
  } else {
    fallbackCopyText(text, title)
  }
}

function fallbackCopyText(text: string, title: string) {
  try {
    const el = document.createElement('textarea')
    el.value = text
    el.style.position = 'fixed'
    el.style.opacity = '0'
    document.body.appendChild(el)
    el.select()
    document.execCommand('copy')
    document.body.removeChild(el)
    toast.add({
      title,
      color: 'success'
    })
  } catch {
    toast.add({
      title: t('socialReports.toastCopyError', 'Impossible de copier'),
      description: t('socialReports.toastCopyErrorDesc', 'Veuillez copier le texte manuellement.'),
      color: 'neutral'
    })
  }
}

async function handleSync() {
  await syncFromN8n()
}

onMounted(() => {
  // Silent initial fetch on page load — will not pop up errors if table is empty
  fetchInsights(false)
})
</script>
