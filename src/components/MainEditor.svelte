<script lang="ts">
  import Icon from '@iconify/svelte';

  let selectedLanguage = 'Originale (none)';
  let selectedFile = '— Aucun fichier —';
  let code = 'Glissez un fichier .py ici ou utilisez les contrôles ci-dessus';
  const encoding = 'UTF-8';
  const availableFiles = 0;

  const languages = [
    'Originale (none)',
    'Français',
  ];

  const files: string[] = [];

  function handleLanguageChange(event: Event) {
    const target = event.target as HTMLSelectElement;
    selectedLanguage = target.value;
  }

  function handleFileChange(event: Event) {
    const target = event.target as HTMLSelectElement;
    selectedFile = target.value;
  }
</script>

<div class="flex-1 flex flex-col bg-gray-900 text-white min-h-[35rem]">
  <!-- Header with controls -->
  <div class="bg-gray-800 p-4 border-b border-gray-700">
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-lg font-semibold text-blue-400">Éditeur principal</h2>
      <div class="flex items-center gap-4 text-sm">
        <span>Aucun fichier chargé</span>
        <span>{encoding}</span>
      </div>
    </div>

    <div class="flex items-center gap-4">
      <div class="flex items-center gap-2">
        <label for="language-select" class="text-sm">Langue:</label>
        <select
          id="language-select"
          bind:value={selectedLanguage}
          on:change={handleLanguageChange}
          class="bg-gray-700 border border-gray-600 rounded px-3 py-1 text-white text-sm focus:outline-none focus:border-blue-500"
        >
          {#each languages as language}
            <option value={language}>{language}</option>
          {/each}
        </select>
      </div>

      <div class="flex items-center gap-2">
        <label for="file-select" class="text-sm">Fichier:</label>
        <select
          id="file-select"
          bind:value={selectedFile}
          on:change={handleFileChange}
          class="bg-gray-700 border border-gray-600 rounded px-3 py-1 text-white text-sm focus:outline-none focus:border-blue-500"
        >
          {#each files as file}
            <option value={file}>{file}</option>
          {:else}
            <option value="— Aucun fichier —">— Aucun fichier —</option>
          {/each}
        </select>
      </div>

      <div class="flex items-center gap-2">
        <button
          class="bg-gray-700 hover:bg-gray-600 px-3 py-1 rounded text-sm transition-colors"
        >
          <Icon icon="hugeicons:folder-01" class="w-5 h-5 text-yellow-500" />
        </button>
        <button
          class="bg-gray-700 hover:bg-gray-600 px-3 py-1 rounded text-sm transition-colors"
        >
          <Icon icon="hugeicons:floppy-disk" class="w-5 h-5 text-blue-500" />
        </button>
      </div>

      <div class="ml-auto text-sm text-gray-400">
        {availableFiles} fichier(s) disponible(s)
      </div>
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
