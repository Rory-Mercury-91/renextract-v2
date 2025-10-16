<script lang="ts">
  /* eslint-env browser */
  import {
    checkProgress,
    coherenceActions,
    isChecking,
    lastCoherenceError,
    lastCoherenceResult,
  } from '$stores/coherence';
  import {
    extractionActions,
    extractionProgress,
    isExtracting,
    lastExtractionError,
    lastExtractionResult,
  } from '$stores/extraction';
  import { projectStore } from '$stores/project';
  import {
    isReconstructing,
    lastReconstructionError,
    lastReconstructionResult,
    reconstructionActions,
    reconstructionProgress,
  } from '$stores/reconstruction';
  import Icon from '@iconify/svelte';

  // État réactif depuis le store projet
  $: currentFile = $projectStore.currentFile;
  $: fileContent = $projectStore.fileContent;
  $: isLoading = $projectStore.isLoading;

  // État réactif depuis le store extraction
  $: extracting = $isExtracting;
  $: extractionProgressText = $extractionProgress;
  $: lastExtractionRes = $lastExtractionResult;
  $: lastExtractionErr = $lastExtractionError;

  // État réactif depuis le store reconstruction
  $: reconstructing = $isReconstructing;
  $: reconstructionProgressText = $reconstructionProgress;
  $: lastReconstructionRes = $lastReconstructionResult;
  $: lastReconstructionErr = $lastReconstructionError;

  // État réactif depuis le store cohérence
  $: checking = $isChecking;
  $: coherenceProgressText = $checkProgress;
  $: lastCoherenceRes = $lastCoherenceResult;
  $: lastCoherenceErr = $lastCoherenceError;

  // Les boutons sont actifs seulement si un fichier est chargé et qu'on n'est pas en train d'extraire/reconstruire/vérifier
  $: canExtract =
    !!currentFile &&
    fileContent.length > 0 &&
    !isLoading &&
    !extracting &&
    !reconstructing &&
    !checking;
  $: canReconstruct =
    !!currentFile &&
    fileContent.length > 0 &&
    !isLoading &&
    !extracting &&
    !reconstructing &&
    !checking &&
    !!lastExtractionRes;
  $: canVerify =
    !!currentFile &&
    fileContent.length > 0 &&
    !isLoading &&
    !extracting &&
    !reconstructing &&
    !checking;

  async function handleExtract() {
    if (!canExtract || !currentFile) return;

    try {
      console.info("🚀 Lancement de l'extraction", {
        file: currentFile,
        lines: fileContent.length,
        fileContent: fileContent.slice(0, 3), // Afficher les 3 premières lignes pour debug
      });

      // Lancer l'extraction
      const success = await extractionActions.extractTexts(
        fileContent,
        currentFile
      );

      if (success) {
        console.info('✅ Extraction terminée avec succès');
      } else {
        console.error("❌ Échec de l'extraction");
      }
    } catch (error) {
      console.error("❌ Erreur exceptionnelle lors de l'extraction:", error);
    }
  }

  async function handleReconstruct() {
    if (!canReconstruct || !currentFile) return;

    try {
      console.info('🔨 Lancement de la reconstruction', {
        file: currentFile,
        lines: fileContent.length,
      });

      // Lancer la reconstruction (utilise le mode de sauvegarde des paramètres)
      const success = await reconstructionActions.reconstructFile(
        fileContent,
        currentFile
      );

      if (success) {
        console.info('✅ Reconstruction terminée avec succès');
      } else {
        console.error('❌ Échec de la reconstruction');
      }
    } catch (error) {
      console.error(
        '❌ Erreur exceptionnelle lors de la reconstruction:',
        error
      );
    }
  }

  async function handleVerify() {
    if (!canVerify || !currentFile) return;

    try {
      console.info('🔍 Lancement de la vérification rapide', {
        file: currentFile,
        lines: fileContent.length,
      });

      // Utiliser le fichier reconstruit si disponible, sinon le fichier original
      const fileToCheck = lastReconstructionRes?.save_path || currentFile;

      // Lancer la vérification rapide
      const success = await coherenceActions.quickCheckFile(fileToCheck);

      if (success) {
        console.info('✅ Vérification rapide terminée avec succès');
      } else {
        console.error('❌ Échec de la vérification rapide');
      }
    } catch (error) {
      console.error('❌ Erreur exceptionnelle lors de la vérification:', error);
    }
  }

  function openOutputFolder() {
    if (lastExtractionRes?.output_folder) {
      extractionActions.openOutputFolder();
    }
  }

  function openReconstructedFile() {
    if (lastReconstructionRes?.save_path) {
      reconstructionActions.openReconstructedFile();
    }
  }
</script>

<div class="flex flex-col gap-4">
  <!-- Indicateur de progression d'extraction -->
  {#if extracting}
    <div
      class="rounded-lg border border-blue-200 bg-blue-50 p-4 dark:border-blue-900 dark:bg-blue-950"
    >
      <div class="flex items-center gap-3">
        <div class="animate-spin">
          <Icon icon="hugeicons:loading-01" class="h-6 w-6 text-blue-600" />
        </div>
        <div class="flex-1">
          <p class="font-medium text-blue-900 dark:text-blue-200">
            Extraction en cours...
          </p>
          <p class="text-sm text-blue-700 dark:text-blue-300">
            {extractionProgressText}
          </p>
        </div>
      </div>
    </div>
  {/if}

  <!-- Indicateur de progression de reconstruction -->
  {#if reconstructing}
    <div
      class="rounded-lg border border-purple-200 bg-purple-50 p-4 dark:border-purple-900 dark:bg-purple-950"
    >
      <div class="flex items-center gap-3">
        <div class="animate-spin">
          <Icon icon="hugeicons:loading-01" class="h-6 w-6 text-purple-600" />
        </div>
        <div class="flex-1">
          <p class="font-medium text-purple-900 dark:text-purple-200">
            Reconstruction en cours...
          </p>
          <p class="text-sm text-purple-700 dark:text-purple-300">
            {reconstructionProgressText}
          </p>
        </div>
      </div>
    </div>
  {/if}

  <!-- Indicateur de progression de vérification -->
  {#if checking}
    <div class="rounded-lg border border-orange-200 bg-orange-50 p-4">
      <div class="flex items-center gap-3">
        <div class="animate-spin">
          <Icon icon="hugeicons:loading-01" class="h-6 w-6 text-orange-600" />
        </div>
        <div class="flex-1">
          <p class="font-medium text-orange-800">Vérification en cours...</p>
          <p class="text-sm text-orange-600">{coherenceProgressText}</p>
        </div>
      </div>
    </div>
  {/if}

  <!-- Résultat de la dernière extraction -->
  {#if lastExtractionRes && !extracting}
    <div
      class="rounded-lg border border-green-200 bg-green-50 p-4 dark:border-green-900 dark:bg-green-950"
    >
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3">
          <Icon
            icon="hugeicons:checkmark-circle-02"
            class="h-6 w-6 text-green-600"
          />
          <div>
            <p class="font-medium text-green-900 dark:text-green-200">
              Extraction terminée
            </p>
            <p class="text-sm text-green-700 dark:text-green-300">
              {lastExtractionRes.extracted_count} dialogues
              {#if lastExtractionRes.asterix_count > 0}• {lastExtractionRes.asterix_count}
                astérisques{/if}
              {#if lastExtractionRes.duplicate_count > 0}• {lastExtractionRes.duplicate_count}
                doublons{/if}
            </p>
          </div>
        </div>
        <button
          onclick={openOutputFolder}
          class="text-green-600 transition-colors hover:text-green-800 dark:text-green-400 dark:hover:text-green-200"
          title="Ouvrir le dossier de sortie"
        >
          <Icon icon="hugeicons:folder-open" class="h-5 w-5" />
        </button>
      </div>
    </div>
  {/if}

  <!-- Résultat de la dernière reconstruction -->
  {#if lastReconstructionRes && !reconstructing}
    <div
      class="rounded-lg border border-emerald-200 bg-emerald-50 p-4 dark:border-emerald-900 dark:bg-emerald-950"
    >
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3">
          <Icon
            icon="hugeicons:checkmark-circle-02"
            class="h-6 w-6 text-emerald-600"
          />
          <div>
            <p class="font-medium text-emerald-900 dark:text-emerald-200">
              Reconstruction terminée
            </p>
            <p class="text-sm text-emerald-700 dark:text-emerald-300">
              Fichier: {lastReconstructionRes.save_path.split('/').pop()}
              {#if lastReconstructionRes.reconstruction_time}
                • {lastReconstructionRes.reconstruction_time.toFixed(2)}s
              {/if}
            </p>
          </div>
        </div>
        <button
          onclick={openReconstructedFile}
          class="text-emerald-600 transition-colors hover:text-emerald-800 dark:text-emerald-400 dark:hover:text-emerald-200"
          title="Ouvrir le fichier reconstruit"
        >
          <Icon icon="hugeicons:file-view" class="h-5 w-5" />
        </button>
      </div>
    </div>
  {/if}

  <!-- Erreur de la dernière extraction -->
  {#if lastExtractionErr && !extracting}
    <div
      class="rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-900 dark:bg-red-950"
    >
      <div class="flex items-center gap-3">
        <Icon icon="hugeicons:close-circle" class="h-6 w-6 text-red-600" />
        <div>
          <p class="font-medium text-red-900 dark:text-red-200">
            Erreur d'extraction
          </p>
          <p class="text-sm text-red-700 dark:text-red-300">
            {lastExtractionErr}
          </p>
        </div>
      </div>
    </div>
  {/if}

  <!-- Erreur de la dernière reconstruction -->
  {#if lastReconstructionErr && !reconstructing}
    <div
      class="rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-900 dark:bg-red-950"
    >
      <div class="flex items-center gap-3">
        <Icon icon="hugeicons:close-circle" class="h-6 w-6 text-red-600" />
        <div>
          <p class="font-medium text-red-900 dark:text-red-200">
            Erreur de reconstruction
          </p>
          <p class="text-sm text-red-700 dark:text-red-300">
            {lastReconstructionErr}
          </p>
        </div>
      </div>
    </div>
  {/if}

  <!-- Résultat de la dernière vérification -->
  {#if lastCoherenceRes && !checking}
    <div class="rounded-lg border border-teal-200 bg-teal-50 p-4 mx-2">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3">
          {#if lastCoherenceRes.stats.total_issues === 0}
            <Icon
              icon="hugeicons:checkmark-circle-02"
              class="h-6 w-6 text-teal-600"
            />
            <div>
              <p class="font-medium text-teal-800">Vérification terminée</p>
              <p class="text-sm text-teal-600">
                ✅ Aucun problème détecté
                {#if lastCoherenceRes.stats.files_analyzed > 0}
                  • {lastCoherenceRes.stats.files_analyzed} fichier(s) analysé(s)
                {/if}
              </p>
            </div>
          {:else}
            <Icon
              icon="hugeicons:warning-triangle"
              class="h-6 w-6 text-orange-600"
            />
            <div>
              <p class="font-medium text-orange-800">Problèmes détectés</p>
              <p class="text-sm text-orange-600">
                ⚠️ {lastCoherenceRes.stats.total_issues} erreur(s) sur {Object.values(
                  lastCoherenceRes.stats.issues_by_type
                ).filter(count => count > 0).length} type(s)
                {#if lastCoherenceRes.stats.files_analyzed > 0}
                  • {lastCoherenceRes.stats.files_analyzed} fichier(s) analysé(s)
                {/if}
              </p>
            </div>
          {/if}
        </div>
        <!-- Le nouveau système Svelte affiche les résultats directement dans l'interface -->
      </div>
    </div>
  {/if}

  <!-- Erreur de la dernière vérification -->
  {#if lastCoherenceErr && !checking}
    <div class="rounded-lg border border-red-200 bg-red-50 p-4">
      <div class="flex items-center gap-3">
        <Icon icon="hugeicons:close-circle" class="h-6 w-6 text-red-600" />
        <div>
          <p class="font-medium text-red-800">Erreur de vérification</p>
          <p class="text-sm text-red-600">{lastCoherenceErr}</p>
        </div>
      </div>
    </div>
  {/if}

  <!-- Boutons d'action -->
  <div class="flex justify-center gap-4">
    <button
      onclick={handleExtract}
      disabled={!canExtract}
      class="flex items-center gap-2 rounded-lg bg-orange-600 px-6 py-3 font-medium text-white transition-colors hover:bg-orange-700 disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:bg-orange-600"
      title={canExtract
        ? 'Extraire les textes du fichier'
        : "Chargez d'abord un fichier"}
    >
      <Icon icon="hugeicons:folder-details-reference" class="h-6 w-6" />
      Extraire
      {#if currentFile && canExtract}
        <span class="text-xs opacity-75">({fileContent.length} lignes)</span>
      {/if}
    </button>

    <button
      onclick={handleReconstruct}
      disabled={!canReconstruct}
      class="flex items-center gap-2 rounded-lg bg-green-600 px-6 py-3 font-medium text-white transition-colors hover:bg-green-700 disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:bg-green-600"
      title={canReconstruct
        ? 'Reconstruire le fichier'
        : "Chargez d'abord un fichier"}
    >
      <Icon icon="hugeicons:delivery-return-02" class="h-6 w-6" />
      Reconstruire
    </button>

    <button
      onclick={handleVerify}
      disabled={!canVerify}
      class="flex items-center gap-2 rounded-lg bg-orange-500 px-6 py-3 font-medium text-white transition-colors hover:bg-orange-600 disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:bg-orange-500"
      title={canVerify ? 'Vérifier la cohérence' : "Chargez d'abord un fichier"}
    >
      <Icon icon="hugeicons:folder-view" class="h-6 w-6" />
      Revérifier
    </button>
  </div>
</div>
