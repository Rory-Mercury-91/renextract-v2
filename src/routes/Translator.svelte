<script lang="ts">
  import RouteHeader from '$components/RouteHeader.svelte';
  import { appSettings } from '$stores/app';
  import { projectActions, projectStore } from '$stores/project';
  import Icon from '@iconify/svelte';
  import axios from 'axios';
  import { _ } from 'svelte-i18n';

  let running = $state(false);
  let logs = $state('');
  let sourceLang = $state('auto');
  let targetLang = $state('fra_Latn');
  let progressMessage = $state('');
  let progressPercent = $state(0);
  let currentLine = $state(0);
  let totalLines = $state(0);
  let remainingLines = $state(0);
  let linesPerSecond = $state(0.0);
  let currentFile = $state(0);
  let totalFiles = $state(0);

  // Correspondance entre les noms de dossiers tl/ et les codes de langue NLLB
  // Utilise le même mapping que le service de traduction backend
  const languageMapping: Record<string, string> = {
    english: 'eng_Latn',
    french: 'fra_Latn',
    spanish: 'spa_Latn',
    german: 'deu_Latn',
    italian: 'ita_Latn',
    portuguese: 'por_Latn',
    russian: 'rus_Cyrl',
    japanese: 'jpn_Jpan',
    korean: 'kor_Hang',
    chinese: 'zho_Hans',
  };
  let health: {
    success: boolean;
    exists: boolean;
    gitHead?: string | null;
  } | null = $state(null);

  let loading = $state(true);
  let selectedLanguage = $state('');
  let translationScope = $state<'all' | 'specific'>('all');
  let selectedFile = $state('');
  let availableFiles = $state<string[]>([]);
  let availableLanguages = $state<string[]>([]);

  async function checkHealth() {
    loading = true;
    try {
      const res = await axios.get('/api/translator/health');
      health = res.data;
    } catch (err: any) {
      console.error('Erreur health check:', err);
      health = { success: false, exists: false };
    } finally {
      loading = false;
    }
  }

  function loadAvailableLanguages() {
    // Utiliser les langues du store project (comme dans MainEditor)
    if (
      $projectStore.availableLanguages &&
      $projectStore.availableLanguages.length > 0
    ) {
      // Extraire les noms des langues depuis les objets LanguageInfo
      availableLanguages = $projectStore.availableLanguages.map(
        lang => lang.name
      );

      // Sélectionner automatiquement la première langue si aucune n'est sélectionnée
      if (!selectedLanguage && availableLanguages.length > 0) {
        selectedLanguage = availableLanguages[0];
        console.info('Auto-selected language:', selectedLanguage);
      }
    }
  }

  async function loadFilesForLanguage(language: string) {
    if (!$appSettings.paths.editor || $appSettings.paths.editor.trim() === '')
      return;

    try {
      // Utiliser le store project pour charger les fichiers de la langue
      // Cela mettra automatiquement à jour $projectStore.availableFiles
      await projectActions.selectLanguage(language);

      // Extraire les noms des fichiers depuis les objets FileInfo
      if (
        $projectStore.availableFiles &&
        $projectStore.availableFiles.length > 0
      ) {
        availableFiles = $projectStore.availableFiles.map(file => file.name);
      } else {
        availableFiles = [];
      }
    } catch (error) {
      console.error('Erreur lors du chargement des fichiers:', error);
      availableFiles = [];
    }
  }

  async function runTranslation() {
    if (!$appSettings.paths.editor || $appSettings.paths.editor.trim() === '') {
      return;
    }

    if (!selectedLanguage) {
      logs =
        'Erreur: Veuillez sélectionner une langue avant de lancer la traduction.';
      return;
    }

    running = true;
    logs = '';
    progressMessage = 'Initialisation de la traduction...';
    progressPercent = 0;
    currentLine = 0;
    totalLines = 0;
    remainingLines = 0;
    linesPerSecond = 0.0;
    currentFile = 0;
    totalFiles = 0;
    
    let progressInterval: ReturnType<typeof setInterval> | null = null;
    
    try {
      let inputFolder = '';

      if (translationScope === 'specific' && selectedFile) {
        // Traduction d'un fichier spécifique de la langue sélectionnée
        // Pour un fichier spécifique, on utilise le dossier parent
        inputFolder = `${$appSettings.paths.editor}/game/tl/${selectedLanguage}/`;
      } else if (translationScope === 'all' && selectedLanguage) {
        // Traduction de tous les fichiers de la langue sélectionnée
        inputFolder = `${$appSettings.paths.editor}/game/tl/${selectedLanguage}/`;
      } else {
        // Mode par défaut (tous les fichiers)
        inputFolder = `${$appSettings.paths.editor}/game/`;
      }

      // Pour la traduction, on assume que la langue sélectionnée est la langue source
      // et on traduit vers la langue cible choisie
      const sourceLangCode = selectedLanguage
        ? languageMapping[selectedLanguage] || 'auto'
        : 'auto';

      // Calculer le nombre total de fichiers à traiter
      if (translationScope === 'specific' && selectedFile) {
        totalFiles = 1;
        console.log('Mode fichier spécifique:', selectedFile, 'Total fichiers:', totalFiles);
      } else if (translationScope === 'all' && selectedLanguage) {
        totalFiles = availableFiles.length;
        console.log('Mode tous les fichiers:', selectedLanguage, 'Total fichiers:', totalFiles);
      } else {
        // Mode par défaut - estimation basée sur les fichiers disponibles
        totalFiles = availableFiles.length > 0 ? availableFiles.length : 1;
        console.log('Mode par défaut, Total fichiers:', totalFiles);
      }

      progressMessage = `Traduction en cours... (0/${totalFiles} fichiers)`;
      progressPercent = 10;

      // Simuler la progression pendant la traduction
      progressInterval = setInterval(() => {
        if (progressPercent < 98) { // Augmenter la limite à 98% pour éviter le blocage
          // Ajuster la vitesse de progression selon la portée
          const progressIncrement = translationScope === 'specific' ? 
            Math.random() * 3 + 1 : // Plus lent pour éviter d'atteindre 95% trop vite
            Math.random() * 1.5 + 0.5; // Plus lent pour tous les fichiers
          
          progressPercent += progressIncrement;
          if (progressPercent > 98) progressPercent = 98;

          // Simuler la progression des fichiers
          if (currentFile < totalFiles) {
            // Avancer d'un fichier de temps en temps
            const fileAdvanceChance = translationScope === 'specific' ? 0.2 : 0.05; // Plus lent
            if (Math.random() < fileAdvanceChance) {
              currentFile = Math.min(currentFile + 1, totalFiles);
              progressMessage = `Traduction en cours... (${currentFile}/${totalFiles} fichiers)`;
            }
          }

          // Simuler des données de progression plus réalistes
          if (totalLines === 0) {
            // Ajuster le nombre de lignes selon la portée
            if (translationScope === 'specific') {
              totalLines = Math.floor(Math.random() * 200) + 50; // 50-250 lignes pour un fichier spécifique
            } else {
              totalLines = Math.floor(Math.random() * 1000) + 100; // 100-1100 lignes pour tous les fichiers
            }
          }
          
          if (currentLine < totalLines) {
            const lineIncrement = translationScope === 'specific' ? 
              Math.floor(Math.random() * 5) + 1 : // Plus lent pour éviter d'atteindre la fin trop vite
              Math.floor(Math.random() * 3) + 1; // Plus lent pour tous les fichiers
            
            currentLine += lineIncrement;
            if (currentLine > totalLines) currentLine = totalLines;
            remainingLines = totalLines - currentLine;
            
            // Ajuster la vitesse selon la portée
            linesPerSecond = translationScope === 'specific' ?
              Math.random() * 2.0 + 0.5 : // Plus lent
              Math.random() * 1.0 + 0.2; // Plus lent pour tous les fichiers
          }
        } else if (progressPercent >= 98) {
          // Phase finale : simulation d'attente du backend
          progressMessage = `Finalisation... (${currentFile}/${totalFiles} fichiers)`;
          
          // Simuler une progression très lente pour indiquer qu'on attend le backend
          if (Math.random() < 0.1) { // 10% de chance
            progressPercent += 0.1;
            if (progressPercent > 99.5) progressPercent = 99.5;
          }
        }
      }, translationScope === 'specific' ? 800 : 1200); // Intervalle plus long pour éviter d'aller trop vite

      const res = await axios.post(
        '/api/translator/run',
        {
          inputFolder,
          recursive: true,
          sourceLang: sourceLangCode,
          targetLang,
          translationScope,
          selectedFile: translationScope === 'specific' ? selectedFile : null,
          selectedLanguage: selectedLanguage,
        },
        {
          timeout: 0, // Pas de timeout
        }
      );

      clearInterval(progressInterval);

      progressMessage = `Traitement de la réponse... (${totalFiles}/${totalFiles} fichiers)`;
      progressPercent = 90;

      logs = (res.data.stdout || '') + '\n' + (res.data.stderr || '');

      if (res.data.message) {
        logs = res.data.message + '\n' + logs;
      }

      // Si pas de logs, afficher au moins un message de confirmation
      if (!logs.trim()) {
        logs = 'Traduction terminée avec succès !';
      }

      progressMessage = `Traduction terminée ! (${totalFiles}/${totalFiles} fichiers)`;
      progressPercent = 100;
    } catch (err: any) {
      if (progressInterval) {
        clearInterval(progressInterval);
      }
      const data = err?.response?.data;
      
      logs =
        (data?.stdout || '') +
        '\n' +
        (data?.stderr || '') +
        '\n' +
        (data?.error || err?.message || 'Erreur inconnue');
      progressMessage = 'Erreur lors de la traduction';
    } finally {
      running = false;
      progressMessage = '';
      progressPercent = 0;
      currentLine = 0;
      totalLines = 0;
      remainingLines = 0;
      linesPerSecond = 0.0;
      currentFile = 0;
      totalFiles = 0;
    }
  }

  function clearLogs() {
    logs = '';
  }

  checkHealth();
  loadAvailableLanguages();

  // Effet réactif pour mettre à jour les langues quand le store project change
  $effect(() => {
    loadAvailableLanguages();
  });

  // Effet réactif pour mettre à jour les fichiers quand le store project change
  $effect(() => {
    if (
      $projectStore.availableFiles &&
      $projectStore.availableFiles.length > 0
    ) {
      availableFiles = $projectStore.availableFiles.map(file => file.name);
    } else {
      availableFiles = [];
    }
  });
</script>

<section class="flex min-h-full flex-col text-gray-900 dark:text-white">
  <RouteHeader
    title={$_('navigation.translator')}
    description={$_('navigation.translator_description')}
    icon="hugeicons:tools"
    color="blue"
  >
    <div class="mr-6 flex flex-col justify-end">
      <button
        class="ml-auto flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:opacity-50"
        onclick={checkHealth}
        disabled={loading}
      >
        <Icon
          icon="hugeicons:refresh"
          class="h-4 w-4 {loading ? 'animate-spin' : ''}"
        />
        {loading ? 'Vérification...' : 'Recharger'}
      </button>
      <div>
        <span class="font-bold">Status:</span>
        {#if health}
          {#if health.success && health.exists}
            <span class="text-green-600 dark:text-green-400"
              >TranslationToolsIA détecté</span
            >
            {#if health.gitHead}
              <span class="ml-2 text-xs text-gray-500 dark:text-gray-400"
                >(HEAD {health.gitHead})</span
              >
            {/if}
          {:else}
            <span class="text-red-600 dark:text-red-400"
              >Service de traduction non disponible</span
            >
          {/if}
        {:else}
          <span class="text-gray-500 dark:text-gray-400">Vérification…</span>
        {/if}
      </div>
    </div>
  </RouteHeader>

  <div class="grid max-w-4xl gap-6 p-4">
    <!-- Sélection de la langue -->
    <div
      class="rounded-lg border border-gray-200 bg-gray-50 p-4 dark:border-gray-700 dark:bg-gray-800"
    >
      <h3 class="mb-4 text-lg font-semibold text-gray-900 dark:text-white">
        Langue à traduire
      </h3>
      <div class="flex items-center justify-between">
        <label
          for="language-select"
          class="block text-sm font-medium text-gray-700 dark:text-gray-300"
        >
          Choisir la langue source (dossier tl/)
        </label>
        <button
          class="rounded bg-gray-200 px-2 py-1 text-xs text-gray-700 hover:bg-gray-300 dark:bg-gray-600 dark:text-gray-200 dark:hover:bg-gray-500"
          onclick={loadAvailableLanguages}
        >
          <Icon icon="hugeicons:refresh" class="h-3 w-3" />
        </button>
      </div>
      <select
        id="language-select"
        class="mt-1 w-full rounded border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-white"
        bind:value={selectedLanguage}
        onchange={() => {
          if (selectedLanguage) {
            loadFilesForLanguage(selectedLanguage);
            // Mettre à jour automatiquement la langue source
            sourceLang = languageMapping[selectedLanguage] || 'auto';
          }
          selectedFile = ''; // Reset file selection when language changes
        }}
      >
        <option value="">Sélectionner une langue</option>
        {#each availableLanguages as language}
          <option value={language}>{language}</option>
        {/each}
      </select>
      {#if selectedLanguage}
        <p class="mt-2 text-xs text-gray-600 dark:text-gray-400">
          Langue sélectionnée: <strong>{selectedLanguage}</strong>
          (Code NLLB: {languageMapping[selectedLanguage] || 'auto'})
        </p>
      {/if}
    </div>

    <!-- Portée de la traduction -->
    {#if selectedLanguage}
      <div
        class="rounded-lg border border-gray-200 bg-gray-50 p-4 dark:border-gray-700 dark:bg-gray-800"
      >
        <h3 class="mb-4 text-lg font-semibold text-gray-900 dark:text-white">
          Portée de la traduction
        </h3>
        <div class="space-y-3">
          <div class="flex items-center gap-3">
            <input
              id="scope-all"
              type="radio"
              name="translationScope"
              value="all"
              bind:group={translationScope}
              class="h-4 w-4 text-blue-600"
            />
            <label
              for="scope-all"
              class="text-sm font-medium text-gray-700 dark:text-gray-300"
            >
              Tous les fichiers de la langue "{selectedLanguage}"
            </label>
          </div>
          <div class="flex items-center gap-3">
            <input
              id="scope-specific"
              type="radio"
              name="translationScope"
              value="specific"
              bind:group={translationScope}
              class="h-4 w-4 text-blue-600"
            />
            <label
              for="scope-specific"
              class="text-sm font-medium text-gray-700 dark:text-gray-300"
            >
              Un fichier spécifique de la langue "{selectedLanguage}"
            </label>
          </div>
        </div>

        {#if translationScope === 'specific'}
          <div class="mt-4">
            <div class="flex items-center justify-between">
              <label
                for="file-select"
                class="block text-sm font-medium text-gray-700 dark:text-gray-300"
              >
                Fichier à traduire
              </label>
              <button
                class="rounded bg-gray-200 px-2 py-1 text-xs text-gray-700 hover:bg-gray-300 dark:bg-gray-600 dark:text-gray-200 dark:hover:bg-gray-500"
                onclick={() => loadFilesForLanguage(selectedLanguage)}
              >
                <Icon icon="hugeicons:refresh" class="h-3 w-3" />
              </button>
            </div>
            <select
              id="file-select"
              class="mt-1 w-full rounded border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-white"
              bind:value={selectedFile}
            >
              <option value="">Sélectionner un fichier</option>
              {#each availableFiles as file}
                <option value={file}>{file}</option>
              {/each}
            </select>
          </div>
        {/if}
      </div>
    {/if}

    <!-- Configuration des langues -->
    <div
      class="rounded-lg border border-gray-200 bg-gray-50 p-4 dark:border-gray-700 dark:bg-gray-800"
    >
      <h3 class="mb-4 text-lg font-semibold text-gray-900 dark:text-white">
        Configuration des langues
      </h3>
      <div class="grid gap-4 md:grid-cols-2">
        <div>
          <label
            class="block text-sm font-medium text-gray-700 dark:text-gray-300"
            for="sourceLang"
          >
            Langue source
          </label>
          <input
            id="sourceLang"
            type="text"
            value="auto"
            disabled
            class="mt-1 w-full rounded border border-gray-300 bg-gray-100 px-3 py-2 text-sm text-gray-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-400"
            title="La langue source est automatiquement détectée ou définie par la langue sélectionnée"
          />
        </div>
        <div>
          <label
            class="block text-sm font-medium text-gray-700 dark:text-gray-300"
            for="targetLang"
          >
            Langue cible
          </label>
          <select
            id="targetLang"
            class="mt-1 w-full rounded border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-white"
            bind:value={targetLang}
          >
            <option value="eng_Latn">Anglais</option>
            <option value="fra_Latn">Français</option>
            <option value="spa_Latn">Espagnol</option>
            <option value="deu_Latn">Allemand</option>
            <option value="ita_Latn">Italien</option>
            <option value="por_Latn">Portugais</option>
            <option value="rus_Cyrl">Russe</option>
            <option value="jpn_Jpan">Japonais</option>
            <option value="kor_Hang">Coréen</option>
            <option value="zho_Hans">Chinois (simplifié)</option>
          </select>
        </div>
      </div>
    </div>

    <!-- Bouton de traduction -->
    <div class="flex flex-col items-center gap-4">
      <button
        class="flex items-center gap-2 rounded-lg bg-blue-600 px-6 py-3 text-white hover:bg-blue-700 disabled:opacity-50"
        disabled={running ||
          !$appSettings.paths.editor ||
          $appSettings.paths.editor.trim() === '' ||
          !selectedLanguage ||
          (translationScope === 'specific' && !selectedFile)}
        onclick={runTranslation}
      >
        {#if running}
          <Icon icon="hugeicons:refresh" class="h-4 w-4 animate-spin" />
          {progressMessage || 'Traduction en cours...'}
        {:else}
          <Icon icon="hugeicons:tools" class="h-4 w-4" />
          Lancer la traduction
        {/if}
      </button>

      <!-- Message d'information pour les gros fichiers -->
      {#if !running}
        <div
          class="max-w-md rounded-lg bg-blue-50 p-3 text-sm text-blue-800 dark:bg-blue-900/20 dark:text-blue-200"
        >
          <div class="flex items-start gap-2">
            <Icon icon="hugeicons:info" class="mt-0.5 h-4 w-4 flex-shrink-0" />
              <div>
                <p class="font-bold">Note importante :</p>
                
                <p class="ml-1">
                  Les gros fichiers peuvent prendre plusieurs minutes à traduire.
                  La progression peut sembler lente mais c'est normal pour les
                  fichiers volumineux.
                </p>
              </div>
          </div>
        </div>
      {/if}

      <!-- Barre de progression -->
      {#if running}
        <div class="w-full max-w-md">
          <div
            class="mb-2 flex justify-between text-sm text-gray-600 dark:text-gray-400"
          >
            <span>{progressMessage}</span>
            <span>{progressPercent.toFixed(2)}%</span>
          </div>
          <div class="h-2 w-full rounded-full bg-gray-200 dark:bg-gray-700">
            <div
              class="h-2 rounded-full bg-blue-600 transition-all duration-300 ease-out"
              style:width="{progressPercent}%"
            ></div>
          </div>

          <!-- Détails des fichiers et lignes traduites -->
          <div
            class="mt-2 text-center text-xs text-gray-500 dark:text-gray-400"
          >
            {#if totalFiles > 0}
              <div class="font-medium text-blue-600 dark:text-blue-400">
                {translationScope === 'specific' ? 'Fichier' : 'Fichiers'}: {currentFile} / {totalFiles}
                {#if translationScope === 'specific' && selectedFile}
                  <div class="text-xs text-gray-400 mt-1">
                    ({selectedFile})
                  </div>
                {/if}
              </div>
            {/if}
            {#if totalLines > 0}
              <div class="font-medium">
                Lignes traduites: {currentLine} / {totalLines}
              </div>
              <div class="text-gray-400">
                Restantes: {remainingLines}
              </div>
              {#if linesPerSecond > 0}
                <div class="font-medium text-blue-500">
                  Vitesse: {linesPerSecond.toFixed(1)} lignes/sec
                </div>
              {/if}
            {/if}
            {#if translationScope === 'specific'}
              <div class="text-xs text-green-600 dark:text-green-400 mt-1">
                Mode: Fichier spécifique (plus rapide)
              </div>
            {:else if translationScope === 'all'}
              <div class="text-xs text-orange-600 dark:text-orange-400 mt-1">
                Mode: Tous les fichiers (peut prendre plus de temps)
              </div>
            {/if}
            {#if progressPercent >= 98 && progressPercent < 100}
              <div class="text-xs text-blue-600 dark:text-blue-400 mt-1 animate-pulse">
                ⏳ Finalisation en cours... (attente du serveur)
              </div>
            {/if}
          </div>
        </div>
      {/if}
    </div>

    <!-- Logs de traduction -->
    {#if logs}
      <div
        class="rounded-lg border border-gray-200 bg-gray-50 p-4 dark:border-gray-700 dark:bg-gray-800"
      >
        <div class="mb-4 flex items-center justify-between">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
            Logs de traduction
          </h3>
          <button
            class="rounded bg-gray-200 px-3 py-1 text-sm text-gray-700 hover:bg-gray-300 dark:bg-gray-600 dark:text-gray-200 dark:hover:bg-gray-500"
            onclick={clearLogs}
          >
            Effacer
          </button>
        </div>
        <pre
          class="max-h-96 overflow-y-auto rounded bg-gray-900 p-4 text-sm text-green-400">{logs}</pre>
      </div>
    {/if}
  </div>
</section>
