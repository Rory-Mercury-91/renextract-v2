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

<div class="flex-1 flex flex-col bg-gray-900 text-white min-h-[35rem]">
  <!-- Header with controls -->
  <div class="bg-gray-800 p-4 border-b border-gray-700">
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-lg font-semibold text-blue-400">
        Éditeur principal
        {#if isLoading}
          <span class="text-xs text-yellow-400 ml-2">Chargement...</span>
        {/if}
      </h2>
      <div class="flex items-center gap-4 text-sm">
        {#if currentFile}
          <span class="text-green-400">✓ Fichier chargé ({fileContent.length} lignes)</span>
        {:else if projectPath}
          <span class="text-yellow-400">Projet chargé - Sélectionnez un fichier</span>
        {:else}
          <span class="text-gray-400">Aucun fichier chargé</span>
        {/if}
        <span>{encoding}</span>
      </div>
    </div>

    <div class="flex items-center gap-4">
      <!-- Mode indicator -->
      <div class="flex items-center gap-2 px-3 py-1 bg-gray-700 rounded">
        <span class="text-xs text-gray-400">
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
            class="bg-gray-700 border border-gray-600 rounded px-3 py-1 text-white text-sm focus:outline-none focus:border-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
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
            class="bg-gray-700 border border-gray-600 rounded px-3 py-1 text-white text-sm focus:outline-none focus:border-blue-500 disabled:opacity-50 disabled:cursor-not-allowed min-w-[200px]"
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
          class="bg-gray-700 hover:bg-gray-600 px-3 py-1 rounded text-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          title="Sauvegarder le fichier"
        >
          <Icon icon="hugeicons:floppy-disk" class="w-5 h-5 text-green-500" />
        </button>
      </div>

      <!-- Files count -->
      {#if mode === 'project'}
        <div class="ml-auto text-sm text-gray-400">
          {availableFiles.length} fichier(s) disponible(s)
        </div>
      {/if}
    </div>
  </div>

  <!-- Code editor area -->
  <div class="flex-1 relative">
    <div class="absolute inset-0 bg-gray-900">
      <div class="h-full flex">
        <!-- Line numbers -->
        <div
          class="bg-gray-800 px-3 py-4 text-gray-500 text-sm font-mono border-r border-gray-700 min-w-[60px]"
        >
          <div class="text-right">1</div>
        </div>

        <!-- Code area -->
        <div class="flex-1 p-4">
          <textarea
            bind:value={code}
            class="w-full h-full bg-transparent text-gray-300 font-mono text-sm resize-none outline-none"
            placeholder="Glissez un fichier .py ici ou utilisez les contrôles ci-dessus"
          ></textarea>
        </div>
      </div>
    </div>
  </div>

  <!-- Status bar -->
  <div
    class="bg-gray-800 px-4 py-2 border-t border-gray-700 text-sm text-gray-400 flex items-center justify-between"
  >
    <span>Ligne 1, Colonne 1</span>
    <span>1 lignes, 0 caractères</span>
  </div>
</div>
