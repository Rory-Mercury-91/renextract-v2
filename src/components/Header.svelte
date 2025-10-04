<script lang="ts">
  import { _ } from 'svelte-i18n';
  import packageJson from '../../package.json' assert { type: 'json' };
  import AboutModal from './AboutModal.svelte';

  let currentProject = $state('Aucun projet chargé');

  let showAboutModal = $state(false);

  function showHelp() {
    alert('Aide RenExtract - Fonctionnalités en cours de développement');
  }
</script>

{#if showAboutModal}
  <AboutModal bind:showAboutModal />
{/if}

<header
  class="bg-gray-800 text-white p-4 flex items-center justify-between border-b border-gray-700 gap-4"
>
  <!-- Left: App Name + Version -->
  <div class="flex items-center gap-4">
    <img
      src="/public/assets/logo.webp"
      alt="Logo RenExtract"
      class="w-12 h-12 object-contain rounded-xl"
    />

    <div>
      <h1 class="text-lg font-bold">RenExtract</h1>
      <p class="text-xs text-gray-400">v{packageJson.version}</p>
    </div>
  </div>

  <!-- Center: Project Bar -->
  <div class="flex items-center gap-2">
    <span class="text-yellow-500">📁</span>
    <span class="text-sm text-gray-300">{currentProject}</span>
    <button
      class="bg-blue-600 hover:bg-blue-700 px-3 py-1 rounded text-sm font-medium transition-colors"
    >
      {$_('app.browse')}
    </button>
  </div>

  <!-- Right: Controls -->
  <div class="flex items-center gap-4">
    <button
      class="text-gray-400 hover:text-white transition-colors px-2 py-1"
      onclick={showHelp}
      title="Aide et documentation"
    >
      ℹ️ {$_('app.help')}
    </button>

    <button
      class="text-gray-400 hover:text-white transition-colors px-2 py-1"
      onclick={() => (showAboutModal = true)}
      title="Informations sur RenExtract"
    >
      ℹ️ À propos
    </button>
  </div>
</header>
