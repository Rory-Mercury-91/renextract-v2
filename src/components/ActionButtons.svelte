<script lang="ts">
  /* eslint-env browser */
  import { extractionActions, extractionProgress, isExtracting, lastExtractionError, lastExtractionResult } from '$stores/extraction';
  import { projectStore } from '$stores/project';
  import Icon from '@iconify/svelte';

  // État réactif depuis le store projet
  $: currentFile = $projectStore.currentFile;
  $: fileContent = $projectStore.fileContent;
  $: isLoading = $projectStore.isLoading;
  
  // État réactif depuis le store extraction
  $: extracting = $isExtracting;
  $: progress = $extractionProgress;
  $: lastResult = $lastExtractionResult;
  $: lastError = $lastExtractionError;
  
  // Les boutons sont actifs seulement si un fichier est chargé et qu'on n'est pas en train d'extraire
  $: canExtract = !!currentFile && fileContent.length > 0 && !isLoading && !extracting;
  $: canReconstruct = !!currentFile && fileContent.length > 0 && !isLoading && !extracting && !!lastResult;
  $: canVerify = !!currentFile && fileContent.length > 0 && !isLoading && !extracting;

  async function handleExtract() {
    if (!canExtract || !currentFile) return;
    
    try {
      console.info('🚀 Lancement de l\'extraction', { 
        file: currentFile, 
        lines: fileContent.length,
        fileContent: fileContent.slice(0, 3) // Afficher les 3 premières lignes pour debug
      });

      // Lancer l'extraction
      const success = await extractionActions.extractTexts(fileContent, currentFile);
      
      if (success) {
        console.log('✅ Extraction terminée avec succès');
      } else {
        console.error('❌ Échec de l\'extraction');
      }
    } catch (error) {
      console.error('❌ Erreur exceptionnelle lors de l\'extraction:', error);
    }
  }

  function handleReconstruct() {
    if (!canReconstruct) return;
    console.info('Reconstruire clicked', { file: currentFile, lines: fileContent.length });
    // TODO: Implémenter la logique de reconstruction
    alert('🚧 Fonctionnalité de reconstruction en cours de développement');
  }

  function handleVerify() {
    if (!canVerify) return;
    console.info('Revérifier clicked', { file: currentFile, lines: fileContent.length });
    // TODO: Implémenter la logique de vérification
    alert('🚧 Fonctionnalité de vérification en cours de développement');
  }

  function openOutputFolder() {
    if (lastResult?.output_folder) {
      extractionActions.openOutputFolder();
    }
  }
</script>

<div class="flex flex-col gap-4">
  <!-- Indicateur de progression d'extraction -->
  {#if extracting}
    <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
      <div class="flex items-center gap-3">
        <div class="animate-spin">
          <Icon icon="hugeicons:loading-01" class="w-6 h-6 text-blue-600" />
        </div>
        <div class="flex-1">
          <p class="text-blue-800 font-medium">Extraction en cours...</p>
          <p class="text-blue-600 text-sm">{progress}</p>
        </div>
      </div>
    </div>
  {/if}

  <!-- Résultat de la dernière extraction -->
  {#if lastResult && !extracting}
    <div class="bg-green-50 border border-green-200 rounded-lg p-4">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3">
          <Icon icon="hugeicons:checkmark-circle-02" class="w-6 h-6 text-green-600" />
          <div>
            <p class="text-green-800 font-medium">Extraction terminée</p>
            <p class="text-green-600 text-sm">
              {lastResult.extracted_count} dialogues 
              {#if lastResult.asterix_count > 0}• {lastResult.asterix_count} astérisques{/if}
              {#if lastResult.duplicate_count > 0}• {lastResult.duplicate_count} doublons{/if}
            </p>
          </div>
        </div>
        <button
          onclick={openOutputFolder}
          class="text-green-600 hover:text-green-800 transition-colors"
          title="Ouvrir le dossier de sortie"
        >
          <Icon icon="hugeicons:folder-open" class="w-5 h-5" />
        </button>
      </div>
    </div>
  {/if}

  <!-- Erreur de la dernière extraction -->
  {#if lastError && !extracting}
    <div class="bg-red-50 border border-red-200 rounded-lg p-4">
      <div class="flex items-center gap-3">
        <Icon icon="hugeicons:close-circle" class="w-6 h-6 text-red-600" />
        <div>
          <p class="text-red-800 font-medium">Erreur d'extraction</p>
          <p class="text-red-600 text-sm">{lastError}</p>
        </div>
      </div>
    </div>
  {/if}

  <!-- Boutons d'action -->
  <div class="flex gap-4 justify-center">
    <button
      onclick={handleExtract}
      disabled={!canExtract}
      class="flex items-center gap-2 bg-orange-600 hover:bg-orange-700 text-white px-6 py-3 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-orange-600"
      title={canExtract ? 'Extraire les textes du fichier' : 'Chargez d\'abord un fichier'}
    >
      <Icon icon="hugeicons:folder-details-reference" class="w-6 h-6" />
      Extraire
      {#if currentFile && canExtract}
        <span class="text-xs opacity-75">({fileContent.length} lignes)</span>
      {/if}
    </button>

    <button
      onclick={handleReconstruct}
      disabled={!canReconstruct}
      class="flex items-center gap-2 bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-green-600"
      title={canReconstruct ? 'Reconstruire le fichier' : 'Chargez d\'abord un fichier'}
    >
      <Icon icon="hugeicons:delivery-return-02" class="w-6 h-6" />
      Reconstruire
    </button>

    <button
      onclick={handleVerify}
      disabled={!canVerify}
      class="flex items-center gap-2 bg-orange-500 hover:bg-orange-600 text-white px-6 py-3 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-orange-500"
      title={canVerify ? 'Vérifier la cohérence' : 'Chargez d\'abord un fichier'}
    >
      <Icon icon="hugeicons:folder-view" class="w-6 h-6" />
      Revérifier
    </button>
  </div>
</div>
