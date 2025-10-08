<script lang="ts">
  /* eslint-env browser */
  import { projectActions, projectStore, type FileInfo } from '$stores/project';
  import Icon from '@iconify/svelte';

  // État réactif depuis le store
  $: projectPath = $projectStore.projectPath;
  $: availableLanguages = $projectStore.availableLanguages;
  $: availableFiles = $projectStore.availableFiles;
  $: selectedLanguage = $projectStore.language;
  $: currentFile = $projectStore.currentFile;
  $: fileContent = $projectStore.fileContent;
  $: isLoading = $projectStore.isLoading;
  $: mode = $projectStore.mode;

  // Variables locales pour l'affichage
  $: code = fileContent.join('') || 'Chargez un projet ou un fichier pour commencer';
  const encoding = 'UTF-8';
  $: selectedFileDisplay = currentFile 
    ? availableFiles.find((f: FileInfo) => f.path === currentFile)?.name || '— Aucun fichier —'
    : '— Aucun fichier —';

  // Gestion du changement de langue
  async function handleLanguageChange(event: Event) {
    const target = event.target as HTMLSelectElement;
    const language = target.value;
    
    if (language && projectPath) {
      await projectActions.selectLanguage(language);
    }
  }

  // Gestion du changement de fichier
  async function handleFileChange(event: Event) {
    const target = event.target as HTMLSelectElement;
    const fileName = target.value;
    
    const file = availableFiles.find((f: FileInfo) => f.name === fileName);
    if (file) {
      await projectActions.selectFile(file.path);
    }
  }

  // Note: Les boutons de chargement de projet sont maintenant dans le header global
  // Le système se synchronise automatiquement avec le projet du header

  // Sauvegarder le fichier (TODO: à implémenter)
  function handleSaveFile() {
    // eslint-disable-next-line no-console
    console.log('Save file - to be implemented');
  }
</script>

<div class="flex min-h-[35rem] flex-1 flex-col bg-gray-50 text-gray-900 dark:bg-gray-900 dark:text-white">
  <!-- Header with controls -->
  <div class="border-b border-gray-200 bg-gray-100 p-4 dark:border-gray-700 dark:bg-gray-800">
    <div class="mb-4 flex items-center justify-between">
      <h2 class="text-lg font-semibold text-blue-600 dark:text-blue-400">
        Éditeur principal
        {#if isLoading}
          <span class="ml-2 text-xs text-yellow-600 dark:text-yellow-400">Chargement...</span>
        {/if}
      </h2>
      <div class="flex items-center gap-4 text-sm">
        {#if currentFile}
          <span class="text-green-600 dark:text-green-400">✓ Fichier chargé ({fileContent.length} lignes)</span>
        {:else if projectPath}
          <span class="text-yellow-600 dark:text-yellow-400">Projet chargé - Sélectionnez un fichier</span>
        {:else}
          <span class="text-gray-500 dark:text-gray-400">Aucun fichier chargé</span>
        {/if}
        <span>{encoding}</span>
      </div>
    </div>

    <div class="flex items-center gap-4">
      <!-- Mode indicator -->
      <div class="flex items-center gap-2 rounded bg-gray-200 px-3 py-1 dark:bg-gray-700">
        <span class="text-xs text-gray-600 dark:text-gray-400">
          {mode === 'project' ? '🎮 Projet du header' : '📄 Fichier unique'}
        </span>
      </div>

      <!-- Language selector -->
      {#if mode === 'project'}
        <div class="flex items-center gap-2">
          <label for="language-select" class="text-sm">Langue:</label>
          <select
            id="language-select"
            value={selectedLanguage || ''}
            on:change={handleLanguageChange}
            disabled={!projectPath || availableLanguages.length === 0 || isLoading}
            class="rounded border border-gray-300 bg-white px-3 py-1 text-sm text-gray-900 focus:border-blue-500 focus:outline-none disabled:cursor-not-allowed disabled:opacity-50 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
          >
            <option value="">— Sélectionner une langue —</option>
            {#each availableLanguages as lang}
              <option value={lang.name}>{lang.name} ({lang.file_count} fichiers)</option>
            {/each}
          </select>
        </div>

        <!-- File selector -->
        <div class="flex items-center gap-2">
          <label for="file-select" class="text-sm">Fichier:</label>
          <select
            id="file-select"
            value={selectedFileDisplay}
            on:change={handleFileChange}
            disabled={!selectedLanguage || availableFiles.length === 0 || isLoading}
            class="min-w-[200px] rounded border border-gray-300 bg-white px-3 py-1 text-sm text-gray-900 focus:border-blue-500 focus:outline-none disabled:cursor-not-allowed disabled:opacity-50 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
          >
            <option value="— Aucun fichier —">— Aucun fichier —</option>
            {#each availableFiles as file}
              <option value={file.name}>{file.name}</option>
            {/each}
          </select>
        </div>
      {/if}

      <!-- Action buttons -->
      <div class="flex items-center gap-2">
        <button
          on:click={handleSaveFile}
          disabled={!currentFile || isLoading}
          class="rounded bg-gray-200 px-3 py-1 text-sm transition-colors hover:bg-gray-300 disabled:cursor-not-allowed disabled:opacity-50 dark:bg-gray-700 dark:hover:bg-gray-600"
          title="Sauvegarder le fichier"
        >
          <Icon icon="hugeicons:floppy-disk" class="h-5 w-5 text-green-600 dark:text-green-500" />
        </button>
      </div>

      <!-- Files count -->
      {#if mode === 'project'}
        <div class="ml-auto text-sm text-gray-500 dark:text-gray-400">
          {availableFiles.length} fichier(s) disponible(s)
        </div>
      {/if}
    </div>
  </div>

  <!-- Code editor area -->
  <div class="relative flex-1">
    <div class="absolute inset-0 bg-white dark:bg-gray-900">
      <div class="flex h-full">
        <!-- Line numbers -->
        <div
          class="min-w-[60px] border-r border-gray-300 bg-gray-100 px-3 py-4 font-mono text-sm text-gray-500 dark:border-gray-700 dark:bg-gray-800"
        >
          <div class="text-right">1</div>
        </div>

        <!-- Code area -->
        <div class="flex-1 p-4">
          <textarea
            bind:value={code}
            class="h-full w-full resize-none bg-transparent font-mono text-sm text-gray-700 outline-none dark:text-gray-300"
            placeholder="Glissez un fichier .py ici ou utilisez les contrôles ci-dessus"
          ></textarea>
        </div>
      </div>
    </div>
  </div>

  <!-- Status bar -->
  <div
    class="flex items-center justify-between border-t border-gray-300 bg-gray-100 px-4 py-2 text-sm text-gray-600 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-400"
  >
    <span>Ligne 1, Colonne 1</span>
    <span>1 lignes, 0 caractères</span>
  </div>
</div>
