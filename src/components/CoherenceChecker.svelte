<!-- src/components/CoherenceChecker.svelte -->
<script lang="ts">
  import {
    checkProgress,
    coherenceActions,
    coherenceOptions,
    isChecking,
    lastCoherenceError,
    lastCoherenceResult,
  } from '$stores/coherence';
  import { projectStore } from '$stores/project';
  import Icon from '@iconify/svelte';
  import { onMount } from 'svelte';

  // État réactif
  const currentProject = $derived(
    $projectStore.projectSummary
      ? {
          path: $projectStore.projectPath,
          languages: $projectStore.availableLanguages,
        }
      : null
  );
  const currentLanguage = $derived($projectStore.language);
  const checking = $derived($isChecking);
  const coherenceProgressText = $derived($checkProgress);
  const lastCoherenceRes = $derived($lastCoherenceResult);
  const lastCoherenceErr = $derived($lastCoherenceError);
  const options = $derived($coherenceOptions);

  // État local
  let selectedLanguage = $state('');
  let analysisMode = $state<'single_file' | 'all_files'>('single_file');
  let excludedFiles = $state('');
  let excludedLines = $state('');

  // Charger les options au montage
  onMount(() => {
    coherenceActions.loadOptions();
  });

  // Synchroniser avec le projet actuel
  $effect(() => {
    if (currentLanguage && !selectedLanguage) {
      selectedLanguage = currentLanguage;
    }
  });

  // Options de vérification
  const checkOptions = [
    {
      key: 'check_variables',
      label: 'Variables [] incohérentes',
      description:
        'Vérifie que les variables [xxx] sont présentes et identiques',
    },
    {
      key: 'check_tags',
      label: 'Balises {} incohérentes',
      description: 'Vérifie que les balises {xxx} sont équilibrées',
    },
    {
      key: 'check_untranslated',
      label: 'Lignes non traduites',
      description: 'Détecte les lignes identiques (non traduites)',
    },
    {
      key: 'check_ellipsis',
      label: '… Ellipsis (-- → ...)',
      description: 'Détecte les ellipses incorrectes',
    },
    {
      key: 'check_escape_sequences',
      label: "\\ Séquences d'échappement",
      description: 'Vérifie la cohérence des \\n, \\t, \\r, \\\\',
    },
    {
      key: 'check_percentages',
      label: '% Variables de formatage',
      description: 'Vérifie la cohérence des %s, %d, etc.',
    },
    {
      key: 'check_quotations',
      label: '" Guillemets et échappements',
      description: 'Vérifie les guillemets et échappements',
    },
    {
      key: 'check_parentheses',
      label: '() Parenthèses et crochets',
      description: "Vérifie l'équilibre des (), [], {}",
    },
    {
      key: 'check_syntax',
      label: "Syntaxe Ren'Py et structure",
      description: 'Vérifie la syntaxe et structure générale',
    },
    {
      key: 'check_deepl_ellipsis',
      label: '[...] Ellipses DeepL',
      description: 'Détecte les [...] qui devraient être ...',
    },
    {
      key: 'check_isolated_percent',
      label: '% Pourcentages isolés',
      description: 'Détecte les % isolés qui devraient être %%',
    },
    {
      key: 'check_french_quotes',
      label: '«» Guillemets français',
      description: 'Détecte les « » qui devraient être \\"',
    },
    {
      key: 'check_line_structure',
      label: 'Structure des lignes',
      description: 'Vérifie que chaque bloc a bien old + new',
    },
  ];

  // Gestion des options
  function toggleOption(key: keyof typeof options) {
    coherenceActions.updateOption(key, !(options as any)[key]);
  }

  function selectAllOptions(enabled: boolean) {
    coherenceActions.toggleAllOptions(enabled);
  }

  function updateExclusions() {
    const exclusions = excludedFiles
      .split(',')
      .map(s => s.trim())
      .filter(s => s.length > 0);
    coherenceActions.updateOption('custom_exclusions', exclusions);
  }

  // Validation et lancement
  function canStartAnalysis(): boolean {
    return (
      !checking &&
      !!selectedLanguage &&
      !!currentProject &&
      !!currentProject.path
    );
  }

  async function startAnalysis() {
    if (!canStartAnalysis()) return;

    try {
      let targetPath: string;
      let selectionInfo: any;

      if (analysisMode === 'all_files') {
        // Analyser tous les fichiers de la langue
        targetPath = `${currentProject!.path}/game/tl/${selectedLanguage}`;
        selectionInfo = {
          project_path: currentProject!.path,
          language: selectedLanguage,
          file_paths: [],
          is_all_files: true,
          selected_option: `Tous les fichiers ${selectedLanguage}`,
        };
      } else {
        // Analyser le fichier actuel
        if (!$projectStore.currentFile) {
          console.error("❌ Aucun fichier actuel pour l'analyse");
          return;
        }
        targetPath = $projectStore.currentFile;
        selectionInfo = {
          project_path: currentProject!.path,
          language: selectedLanguage,
          file_paths: [$projectStore.currentFile],
          is_all_files: false,
          selected_option: $projectStore.currentFile.split('/').pop(),
        };
      }

      console.debug(`🔍 Début analyse cohérence: ${targetPath}`);
      await coherenceActions.analyzeCoherence(targetPath, selectionInfo);
    } catch (error) {
      console.error('❌ Erreur lancement analyse:', error);
    }
  }

  // Actions sur les résultats
  async function openDetailedReport() {
    await coherenceActions.openDetailedReport();
  }

  async function openReportsFolder() {
    await coherenceActions.openReportsFolder();
  }
</script>

<div class="flex flex-col gap-6">
  <!-- Header avec aide -->
  <div
    class="rounded-lg bg-gradient-to-r from-teal-600 to-blue-600 p-6 text-white"
  >
    <div class="flex items-center justify-between">
      <div>
        <h2 class="flex items-center gap-3 text-2xl font-bold">
          <Icon icon="hugeicons:test-tube" class="h-8 w-8" />
          Vérification de Cohérence
        </h2>
        <p class="mt-2 text-teal-100">
          Analysez la qualité et la cohérence de vos traductions Ren'Py
        </p>
      </div>
      <button
        class="rounded-lg bg-white/20 px-4 py-2 transition-colors hover:bg-white/30"
        title="À quoi ça sert ?"
      >
        <Icon icon="hugeicons:question-mark-circle" class="h-6 w-6" />
      </button>
    </div>
  </div>

  <!-- Sélection Projet/Langue -->
  <div class="rounded-lg border border-gray-700 bg-gray-800 p-6">
    <h3 class="mb-4 flex items-center gap-2 text-lg font-semibold text-white">
      <Icon icon="hugeicons:folder-open" class="h-5 w-5" />
      Sélection de l'analyse
    </h3>

    <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
      <!-- Langue -->
      <div>
        <label
          for="language-select"
          class="mb-2 block text-sm font-medium text-gray-300"
        >
          Langue à analyser
        </label>
        <select
          id="language-select"
          bind:value={selectedLanguage}
          class="w-full rounded-lg border border-gray-600 bg-gray-700 px-3 py-2 text-white focus:border-transparent focus:ring-2 focus:ring-teal-500"
          disabled={checking}
        >
          <option value="">Sélectionner une langue...</option>
          {#if currentProject && currentProject.languages}
            {#each currentProject.languages as lang}
              <option value={lang.name}>{lang.name}</option>
            {/each}
          {/if}
        </select>
      </div>

      <!-- Mode d'analyse -->
      <div>
        <label
          for="mode-single"
          class="mb-2 block text-sm font-medium text-gray-300"
        >
          Mode d'analyse
        </label>
        <div class="space-y-2">
          <label for="mode-single" class="flex items-center">
            <input
              id="mode-single"
              type="radio"
              bind:group={analysisMode}
              value="single_file"
              class="mr-2 text-teal-600 focus:ring-teal-500"
              disabled={checking}
            />
            <span class="text-sm text-white">Fichier actuel uniquement</span>
          </label>
          <label for="mode-all" class="flex items-center">
            <input
              id="mode-all"
              type="radio"
              bind:group={analysisMode}
              value="all_files"
              class="mr-2 text-teal-600 focus:ring-teal-500"
              disabled={checking}
            />
            <span class="text-sm text-white"
              >Tous les fichiers de la langue</span
            >
          </label>
        </div>
      </div>
    </div>
  </div>

  <!-- Options de vérification -->
  <div class="rounded-lg border border-gray-700 bg-gray-800 p-6">
    <div class="mb-4 flex items-center justify-between">
      <h3 class="flex items-center gap-2 text-lg font-semibold text-white">
        <Icon icon="hugeicons:settings-02" class="h-5 w-5" />
        Options de vérification
      </h3>
      <div class="flex gap-2">
        <button
          onclick={() => selectAllOptions(true)}
          class="rounded bg-blue-600 px-3 py-1 text-sm text-white transition-colors hover:bg-blue-700"
          disabled={checking}
        >
          Tout sélectionner
        </button>
        <button
          onclick={() => selectAllOptions(false)}
          class="rounded bg-gray-600 px-3 py-1 text-sm text-white transition-colors hover:bg-gray-700"
          disabled={checking}
        >
          Tout désélectionner
        </button>
      </div>
    </div>

    <div class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
      {#each checkOptions as option}
        <label
          class="flex cursor-pointer items-start gap-3 rounded-lg border border-gray-600 bg-gray-700/50 p-3 transition-colors hover:bg-gray-700"
        >
          <input
            type="checkbox"
            checked={(options as any)[option.key]}
            onchange={() => toggleOption(option.key as keyof typeof options)}
            class="mt-1 h-5 w-5 rounded border-gray-600 bg-gray-800 text-teal-600 focus:ring-2 focus:ring-teal-500"
            disabled={checking}
          />
          <div class="flex-1">
            <div class="text-sm font-medium text-white">{option.label}</div>
            <div class="mt-1 text-xs text-gray-400">{option.description}</div>
          </div>
        </label>
      {/each}
    </div>
  </div>

  <!-- Exclusions -->
  <div class="rounded-lg border border-gray-700 bg-gray-800 p-6">
    <h3 class="mb-4 flex items-center gap-2 text-lg font-semibold text-white">
      <Icon icon="hugeicons:filter-remove" class="h-5 w-5" />
      Exclusions
    </h3>

    <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
      <div>
        <label
          for="excluded-files"
          class="mb-2 block text-sm font-medium text-gray-300"
        >
          Fichiers à exclure (séparés par des virgules)
        </label>
        <input
          id="excluded-files"
          type="text"
          bind:value={excludedFiles}
          oninput={updateExclusions}
          placeholder="Ex: OK, Menu, Continue"
          class="w-full rounded-lg border border-gray-600 bg-gray-700 px-3 py-2 text-white focus:border-transparent focus:ring-2 focus:ring-teal-500"
          disabled={checking}
        />
      </div>

      <div>
        <label
          for="excluded-lines"
          class="mb-2 block text-sm font-medium text-gray-300"
        >
          Lignes à exclure (séparées par des virgules)
        </label>
        <input
          id="excluded-lines"
          type="text"
          bind:value={excludedLines}
          placeholder="Ex: Yes, No, Back"
          class="w-full rounded-lg border border-gray-600 bg-gray-700 px-3 py-2 text-white focus:border-transparent focus:ring-2 focus:ring-teal-500"
          disabled={checking}
        />
      </div>
    </div>
  </div>

  <!-- Indicateur de progression -->
  {#if checking}
    <div class="rounded-lg border border-orange-700 bg-orange-900/30 p-4">
      <div class="flex items-center gap-3">
        <div class="animate-spin">
          <Icon icon="hugeicons:loading-01" class="h-6 w-6 text-orange-400" />
        </div>
        <div class="flex-1">
          <p class="font-medium text-orange-200">Analyse en cours...</p>
          <p class="text-sm text-orange-400">{coherenceProgressText}</p>
        </div>
      </div>
    </div>
  {/if}

  <!-- Résultats -->
  {#if lastCoherenceRes && !checking}
    <div class="rounded-lg border border-gray-700 bg-gray-800 p-6">
      <div class="mb-4 flex items-center justify-between">
        <h3 class="flex items-center gap-2 text-lg font-semibold text-white">
          <Icon icon="hugeicons:chart-bar" class="h-5 w-5" />
          Résultats de l'analyse
        </h3>
        <div class="flex gap-2">
          {#if lastCoherenceRes.stats.total_issues > 0}
            <button
              onclick={openDetailedReport}
              class="flex items-center gap-2 rounded-lg bg-teal-600 px-4 py-2 text-white transition-colors hover:bg-teal-700"
            >
              <Icon icon="hugeicons:file-document" class="h-4 w-4" />
              Rapport détaillé
            </button>
          {/if}
          <button
            onclick={openReportsFolder}
            class="flex items-center gap-2 rounded-lg bg-gray-600 px-4 py-2 text-white transition-colors hover:bg-gray-700"
          >
            <Icon icon="hugeicons:folder-open" class="h-4 w-4" />
            Ouvrir dossier
          </button>
        </div>
      </div>

      <!-- Statistiques -->
      <div class="mb-6 grid grid-cols-2 gap-4 md:grid-cols-4">
        <div class="rounded-lg bg-gray-700 p-4 text-center">
          <div
            class="text-2xl font-bold {lastCoherenceRes.stats.total_issues === 0
              ? 'text-green-400'
              : 'text-red-400'}"
          >
            {lastCoherenceRes.stats.total_issues}
          </div>
          <div class="text-sm text-gray-300">Problèmes</div>
        </div>
        <div class="rounded-lg bg-gray-700 p-4 text-center">
          <div class="text-2xl font-bold text-blue-400">
            {lastCoherenceRes.stats.files_analyzed}
          </div>
          <div class="text-sm text-gray-300">Fichiers</div>
        </div>
        <div class="rounded-lg bg-gray-700 p-4 text-center">
          <div class="text-2xl font-bold text-orange-400">
            {Object.values(lastCoherenceRes.stats.issues_by_type).filter(
              count => count > 0
            ).length}
          </div>
          <div class="text-sm text-gray-300">Types</div>
        </div>
        <div class="rounded-lg bg-gray-700 p-4 text-center">
          <div class="text-2xl font-bold text-purple-400">
            {lastCoherenceRes.analysis_time.toFixed(1)}s
          </div>
          <div class="text-sm text-gray-300">Durée</div>
        </div>
      </div>

      <!-- Message de résultat -->
      {#if lastCoherenceRes.stats.total_issues === 0}
        <div
          class="rounded-lg border border-green-700 bg-green-900/30 p-6 text-center"
        >
          <Icon
            icon="hugeicons:checkmark-circle-02"
            class="mx-auto mb-3 h-12 w-12 text-green-400"
          />
          <h4 class="mb-2 text-lg font-semibold text-green-200">
            ✅ Aucun problème détecté !
          </h4>
          <p class="text-green-400">
            Votre traduction est cohérente et de qualité.
          </p>
        </div>
      {:else}
        <div
          class="rounded-lg border border-orange-700 bg-orange-900/30 p-6 text-center"
        >
          <Icon
            icon="hugeicons:warning-triangle"
            class="mx-auto mb-3 h-12 w-12 text-orange-400"
          />
          <h4 class="mb-2 text-lg font-semibold text-orange-200">
            ⚠️ Problèmes détectés
          </h4>
          <p class="text-orange-400">
            {lastCoherenceRes.stats.total_issues} problème(s) trouvé(s) sur {Object.values(
              lastCoherenceRes.stats.issues_by_type
            ).filter(count => count > 0).length} type(s) différent(s).
          </p>
        </div>
      {/if}
    </div>
  {/if}

  <!-- Erreur -->
  {#if lastCoherenceErr && !checking}
    <div class="rounded-lg border border-red-700 bg-red-900/30 p-4">
      <div class="flex items-center gap-3">
        <Icon icon="hugeicons:close-circle" class="h-6 w-6 text-red-400" />
        <div>
          <p class="font-medium text-red-200">Erreur d'analyse</p>
          <p class="text-sm text-red-400">{lastCoherenceErr}</p>
        </div>
      </div>
    </div>
  {/if}

  <!-- Bouton de lancement -->
  <div class="flex justify-center">
    <button
      onclick={startAnalysis}
      disabled={!canStartAnalysis()}
      class="flex items-center gap-2 rounded-lg bg-teal-600 px-8 py-3 text-lg font-medium text-white transition-colors hover:bg-teal-700 disabled:cursor-not-allowed disabled:bg-gray-600"
    >
      <Icon icon="hugeicons:play" class="h-5 w-5" />
      {checking ? 'Analyse en cours...' : "Démarrer l'analyse"}
    </button>
  </div>
</div>
