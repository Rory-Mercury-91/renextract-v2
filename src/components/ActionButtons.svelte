<script lang="ts">
  /* eslint-env browser */
  import { projectStore } from '$stores/project';
  import Icon from '@iconify/svelte';

  // État réactif depuis le store
  $: currentFile = $projectStore.currentFile;
  $: fileContent = $projectStore.fileContent;
  $: isLoading = $projectStore.isLoading;
  
  // Les boutons sont actifs seulement si un fichier est chargé
  $: canExtract = !!currentFile && fileContent.length > 0 && !isLoading;
  $: canReconstruct = !!currentFile && fileContent.length > 0 && !isLoading;
  $: canVerify = !!currentFile && fileContent.length > 0 && !isLoading;

  function handleExtract() {
    if (!canExtract) return;
    // eslint-disable-next-line no-console
    console.info('Extraire clicked', { file: currentFile, lines: fileContent.length });
    // TODO: Implémenter la logique d'extraction
  }

  function handleReconstruct() {
    if (!canReconstruct) return;
    // eslint-disable-next-line no-console
    console.info('Reconstruire clicked', { file: currentFile, lines: fileContent.length });
    // TODO: Implémenter la logique de reconstruction
  }

  function handleVerify() {
    if (!canVerify) return;
    // eslint-disable-next-line no-console
    console.info('Revérifier clicked', { file: currentFile, lines: fileContent.length });
    // TODO: Implémenter la logique de vérification
  }
</script>

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
