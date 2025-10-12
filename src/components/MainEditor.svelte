<script lang="ts">
  /* eslint-env browser */
  import { projectActions, projectStore, type FileInfo } from '$stores/project';

  // Variables locales pour l'affichage
  let code = $derived(
    $projectStore.fileContent.join('') ||
      'Chargez un projet ou un fichier pour commencer'
  );

  const selectedFileDisplay = $derived(
    $projectStore.currentFile
      ? $projectStore.availableFiles.find(
          (f: FileInfo) => f.path === $projectStore.currentFile
        )?.name || '— Aucun fichier —'
      : '— Aucun fichier —'
  );

  // Variables pour la numérotation des lignes (virtualisée)
  const lineCount = $derived($projectStore.fileContent.length || 1);

  // État de défilement pour la virtualisation
  let scrollTop = $state(0);
  let containerHeight = $state(0);
  const lineHeight = 24; // 1.5rem = 24px

  // Virtualisation : calculer les lignes visibles basées sur le scroll
  const visibleLineNumbers = $derived(
    lineCount <= 50
      ? Array.from({ length: lineCount }, (_, i) => i + 1)
      : (() => {
          const startLine = Math.floor(scrollTop / lineHeight) + 1;
          const visibleLines = Math.ceil(containerHeight / lineHeight) + 2; // +2 pour le buffer
          const endLine = Math.min(startLine + visibleLines, lineCount);
          return Array.from(
            { length: endLine - startLine + 1 },
            (_, i) => startLine + i
          );
        })()
  );

  // Références pour synchroniser le défilement
  let lineNumbersContainer: HTMLDivElement;
  let textareaElement: HTMLTextAreaElement;

  // Gestion du changement de langue
  const handleLanguageChange = async (event: Event) => {
    const target = event.target as HTMLSelectElement;
    const language = target.value;

    if (language && $projectStore.projectPath) {
      await projectActions.selectLanguage(language);
    }
  };

  // Gestion du changement de fichier
  const handleFileChange = async (event: Event) => {
    const target = event.target as HTMLSelectElement;
    const fileName = target.value;

    const file = $projectStore.availableFiles.find(
      (f: FileInfo) => f.name === fileName
    );
    if (file) {
      await projectActions.selectFile(file.path);
    }
  };

  // Note: Les boutons de chargement de projet sont maintenant dans le header global
  // Le système se synchronise automatiquement avec le projet du header

  // Sauvegarder le fichier (TODO: à implémenter)
  const handleSaveFile = () => {
    // eslint-disable-next-line no-console
    console.log('Save file - to be implemented');
  };

  // Synchroniser le défilement entre les numéros de lignes et le contenu
  const handleScroll = () => {
    if (lineNumbersContainer && textareaElement) {
      lineNumbersContainer.scrollTop = textareaElement.scrollTop;
      scrollTop = textareaElement.scrollTop;
    }
  };

  // Mettre à jour la hauteur du conteneur
  const updateContainerHeight = () => {
    if (lineNumbersContainer) {
      containerHeight = lineNumbersContainer.clientHeight;
    }
  };

  // Initialiser la hauteur au montage
  $effect(() => {
    if (lineNumbersContainer) {
      updateContainerHeight();
    }
  });
</script>

<div
  class="flex min-h-[35rem] flex-1 flex-col bg-gray-50 text-gray-900 dark:bg-gray-900 dark:text-white"
>
  <!-- Header with controls -->
  <div
    class="border-b border-gray-200 bg-gray-100 p-4 dark:border-gray-700 dark:bg-gray-800"
  >
    <div class="mb-4 flex items-center justify-between">
      <h2 class="text-lg font-semibold text-blue-600 dark:text-blue-400">
        Éditeur principal
        {#if $projectStore.isLoading}
          <span class="ml-2 text-xs text-yellow-600 dark:text-yellow-400"
            >Chargement...</span
          >
        {/if}
      </h2>
      <div class="flex items-center gap-4 text-sm">
        {#if $projectStore.currentFile}
          <span class="text-green-600 dark:text-green-400"
            >✓ Fichier chargé ({$projectStore.fileContent.length} lignes)</span
          >
        {:else if $projectStore.projectPath}
          <span class="text-yellow-600 dark:text-yellow-400"
            >Projet chargé - Sélectionnez un fichier</span
          >
        {:else}
          <span class="text-gray-500 dark:text-gray-400"
            >Aucun fichier chargé</span
          >
        {/if}
      </div>
    </div>

    <div class="flex items-center gap-4">
      <!-- Language selector -->
      <div class="flex items-center gap-2">
        <label for="language-select" class="text-sm">Langue:</label>
        <select
          id="language-select"
          value={$projectStore.language || ''}
          onchange={handleLanguageChange}
          disabled={!$projectStore.projectPath ||
            $projectStore.availableLanguages.length === 0 ||
            $projectStore.isLoading}
          class="rounded border border-gray-300 bg-white px-3 py-1 text-sm text-gray-900 focus:border-blue-500 focus:outline-none disabled:cursor-not-allowed disabled:opacity-50 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
        >
          <option value="">— Sélectionner une langue —</option>
          {#each $projectStore.availableLanguages as lang}
            <option value={lang.name}
              >{lang.name} ({lang.file_count} fichiers)</option
            >
          {/each}
        </select>
      </div>

      <!-- File selector -->
      <div class="flex items-center gap-2">
        <label for="file-select" class="text-sm">Fichier:</label>
        <select
          id="file-select"
          value={selectedFileDisplay}
          onchange={handleFileChange}
          disabled={!$projectStore.language ||
            $projectStore.availableFiles.length === 0 ||
            $projectStore.isLoading}
          class="min-w-[200px] rounded border border-gray-300 bg-white px-3 py-1 text-sm text-gray-900 focus:border-blue-500 focus:outline-none disabled:cursor-not-allowed disabled:opacity-50 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
        >
          <option value="— Aucun fichier —">— Aucun fichier —</option>
          {#each $projectStore.availableFiles as file}
            <option value={file.name}>{file.name}</option>
          {/each}
        </select>
      </div>

      <!-- Files count -->
      <div class="ml-auto text-sm text-gray-500 dark:text-gray-400">
        {$projectStore.availableFiles.length} fichier(s) disponible(s)
      </div>
    </div>
  </div>

  <!-- Code editor area -->
  <div class="relative flex-1">
    <div class="absolute inset-0 bg-white dark:bg-gray-900">
      <div class="flex h-full">
        <!-- Line numbers -->
        <div
          bind:this={lineNumbersContainer}
          onresize={updateContainerHeight}
          class="pointer-events-none min-w-[60px] select-none overflow-y-auto border-r border-gray-300 bg-gray-100 px-3 py-4 font-mono text-sm text-gray-500 [-ms-overflow-style:none] [scrollbar-width:none] dark:border-gray-700 dark:bg-gray-800 [&::-webkit-scrollbar]:hidden"
        >
          {#each visibleLineNumbers as lineNumber}
            <div class="text-right leading-6">{lineNumber}</div>
          {/each}
        </div>

        <!-- Code area -->
        <div class="flex-1 p-4">
          <textarea
            bind:this={textareaElement}
            bind:value={code}
            onscroll={handleScroll}
            class="h-full w-full resize-none bg-transparent font-mono text-sm leading-6 text-gray-700 outline-none [-ms-overflow-style:none] [scrollbar-width:none] dark:text-gray-300 [&::-webkit-scrollbar]:hidden"
            placeholder="Glissez un fichier .py ici ou utilisez les contrôles ci-dessus"
            readonly
          ></textarea>
        </div>
      </div>
    </div>
  </div>

  <!-- Status bar -->
  <div
    class="flex items-center justify-between border-t border-gray-300 bg-gray-100 px-4 py-2 text-sm text-gray-600 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-400"
  >
    <span>{lineCount} lignes, {code.length} caractères</span>
  </div>
</div>
