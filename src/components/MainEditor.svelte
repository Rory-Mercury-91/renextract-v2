<script lang="ts">
  /* eslint-env browser */
  import Icon from '@iconify/svelte';

  let selectedLanguage = 'Originale (none)';
  let selectedFile = '— Aucun fichier —';
  let code = 'Glissez un fichier .py ici ou utilisez les contrôles ci-dessus';
  const encoding = 'UTF-8';
  const availableFiles = 0;

  const languages = ['Originale (none)', 'Français'];

  const files: string[] = [];

  function handleLanguageChange(event: unknown) {
    const target = (event as { target: unknown })
      .target as globalThis.HTMLSelectElement;
    selectedLanguage = target.value;
  }

  function handleFileChange(event: unknown) {
    const target = (event as { target: unknown })
      .target as globalThis.HTMLSelectElement;
    selectedFile = target.value;
  }
</script>

<div class="flex min-h-[35rem] flex-1 flex-col bg-gray-900 text-white">
  <!-- Header with controls -->
  <div class="border-b border-gray-700 bg-gray-800 p-4">
    <div class="mb-4 flex items-center justify-between">
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
          class="rounded border border-gray-600 bg-gray-700 px-3 py-1 text-sm text-white focus:border-blue-500 focus:outline-none"
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
          class="rounded border border-gray-600 bg-gray-700 px-3 py-1 text-sm text-white focus:border-blue-500 focus:outline-none"
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
          class="rounded bg-gray-700 px-3 py-1 text-sm transition-colors hover:bg-gray-600"
        >
          <Icon icon="hugeicons:folder-01" class="h-5 w-5 text-yellow-500" />
        </button>
        <button
          class="rounded bg-gray-700 px-3 py-1 text-sm transition-colors hover:bg-gray-600"
        >
          <Icon icon="hugeicons:floppy-disk" class="h-5 w-5 text-blue-500" />
        </button>
      </div>

      <div class="ml-auto text-sm text-gray-400">
        {availableFiles} fichier(s) disponible(s)
      </div>
    </div>
  </div>

  <!-- Code editor area -->
  <div class="relative flex-1">
    <div class="absolute inset-0 bg-gray-900">
      <div class="flex h-full">
        <!-- Line numbers -->
        <div
          class="min-w-[60px] border-r border-gray-700 bg-gray-800 px-3 py-4 font-mono text-sm text-gray-500"
        >
          <div class="text-right">1</div>
        </div>

        <!-- Code area -->
        <div class="flex-1 p-4">
          <textarea
            bind:value={code}
            class="h-full w-full resize-none bg-transparent font-mono text-sm text-gray-300 outline-none"
            placeholder="Glissez un fichier .py ici ou utilisez les contrôles ci-dessus"
          ></textarea>
        </div>
      </div>
    </div>
  </div>

  <!-- Status bar -->
  <div
    class="flex items-center justify-between border-t border-gray-700 bg-gray-800 px-4 py-2 text-sm text-gray-400"
  >
    <span>Ligne 1, Colonne 1</span>
    <span>1 lignes, 0 caractères</span>
  </div>
</div>
