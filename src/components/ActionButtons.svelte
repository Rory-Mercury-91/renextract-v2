<script lang="ts">
  /* eslint-env browser */
  import { extractionActions, extractionProgress, isExtracting, lastExtractionError, lastExtractionResult } from '$stores/extraction';
  import { projectStore } from '$stores/project';
  import { isReconstructing, lastReconstructionError, lastReconstructionResult, reconstructionActions, reconstructionProgress } from '$stores/reconstruction';
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
  
  // Les boutons sont actifs seulement si un fichier est chargé et qu'on n'est pas en train d'extraire/reconstruire
  $: canExtract = !!currentFile && fileContent.length > 0 && !isLoading && !extracting && !reconstructing;
  $: canReconstruct = !!currentFile && fileContent.length > 0 && !isLoading && !extracting && !reconstructing && !!lastExtractionRes;
  $: canVerify = !!currentFile && fileContent.length > 0 && !isLoading && !extracting && !reconstructing;

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

  async function handleReconstruct() {
    if (!canReconstruct || !currentFile) return;
    
    try {
      console.info('🔨 Lancement de la reconstruction', { 
        file: currentFile, 
        lines: fileContent.length 
      });

      // Lancer la reconstruction (utilise le mode de sauvegarde des paramètres)
      const success = await reconstructionActions.reconstructFile(fileContent, currentFile);
      
      if (success) {
        console.log('✅ Reconstruction terminée avec succès');
      } else {
        console.error('❌ Échec de la reconstruction');
      }
    } catch (error) {
      console.error('❌ Erreur exceptionnelle lors de la reconstruction:', error);
    }
  }

  function handleVerify() {
    if (!canVerify) return;
    console.info('Revérifier clicked', { file: currentFile, lines: fileContent.length });
    // TODO: Implémenter la logique de vérification
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
    <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
      <div class="flex items-center gap-3">
        <div class="animate-spin">
          <Icon icon="hugeicons:loading-01" class="w-6 h-6 text-blue-600" />
        </div>
        <div class="flex-1">
          <p class="text-blue-800 font-medium">Extraction en cours...</p>
          <p class="text-blue-600 text-sm">{extractionProgressText}</p>
        </div>
      </div>
    </div>
  {/if}

  <!-- Indicateur de progression de reconstruction -->
  {#if reconstructing}
    <div class="bg-purple-50 border border-purple-200 rounded-lg p-4">
      <div class="flex items-center gap-3">
        <div class="animate-spin">
          <Icon icon="hugeicons:loading-01" class="w-6 h-6 text-purple-600" />
        </div>
        <div class="flex-1">
          <p class="text-purple-800 font-medium">Reconstruction en cours...</p>
          <p class="text-purple-600 text-sm">{reconstructionProgressText}</p>
        </div>
      </div>
    </div>
  {/if}

  <!-- Résultat de la dernière extraction -->
  {#if lastExtractionRes && !extracting}
    <div class="bg-green-50 border border-green-200 rounded-lg p-4">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3">
          <Icon icon="hugeicons:checkmark-circle-02" class="w-6 h-6 text-green-600" />
          <div>
            <p class="text-green-800 font-medium">Extraction terminée</p>
            <p class="text-green-600 text-sm">
              {lastExtractionRes.extracted_count} dialogues 
              {#if lastExtractionRes.asterix_count > 0}• {lastExtractionRes.asterix_count} astérisques{/if}
              {#if lastExtractionRes.duplicate_count > 0}• {lastExtractionRes.duplicate_count} doublons{/if}
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

  <!-- Résultat de la dernière reconstruction -->
  {#if lastReconstructionRes && !reconstructing}
    <div class="bg-emerald-50 border border-emerald-200 rounded-lg p-4">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3">
          <Icon icon="hugeicons:checkmark-circle-02" class="w-6 h-6 text-emerald-600" />
          <div>
            <p class="text-emerald-800 font-medium">Reconstruction terminée</p>
            <p class="text-emerald-600 text-sm">
              Fichier: {lastReconstructionRes.save_path.split('/').pop()}
              {#if lastReconstructionRes.reconstruction_time}
                • {(lastReconstructionRes.reconstruction_time).toFixed(2)}s
              {/if}
            </p>
          </div>
        </div>
        <button
          onclick={openReconstructedFile}
          class="text-emerald-600 hover:text-emerald-800 transition-colors"
          title="Ouvrir le fichier reconstruit"
        >
          <Icon icon="hugeicons:file-view" class="w-5 h-5" />
        </button>
      </div>
    </div>
  {/if}

  <!-- Erreur de la dernière extraction -->
  {#if lastExtractionErr && !extracting}
    <div class="bg-red-50 border border-red-200 rounded-lg p-4">
      <div class="flex items-center gap-3">
        <Icon icon="hugeicons:close-circle" class="w-6 h-6 text-red-600" />
        <div>
          <p class="text-red-800 font-medium">Erreur d'extraction</p>
          <p class="text-red-600 text-sm">{lastExtractionErr}</p>
        </div>
      </div>
    </div>
  {/if}

  <!-- Erreur de la dernière reconstruction -->
  {#if lastReconstructionErr && !reconstructing}
    <div class="bg-red-50 border border-red-200 rounded-lg p-4">
      <div class="flex items-center gap-3">
        <Icon icon="hugeicons:close-circle" class="w-6 h-6 text-red-600" />
        <div>
          <p class="text-red-800 font-medium">Erreur de reconstruction</p>
          <p class="text-red-600 text-sm">{lastReconstructionErr}</p>
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
