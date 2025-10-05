<script lang="ts">
  import Icon from '@iconify/svelte';
  import { _ } from 'svelte-i18n';
  import packageJson from '../../package.json' assert { type: 'json' };
  import AboutModal from './AboutModal.svelte';

  const currentProject = $state('');

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
    <Icon icon="hugeicons:folder-01" class="w-6 h-6 text-yellow-500" />
    <input class="text-sm text-gray-700 bg-slate-100 py-1 px-2 rounded-lg" value={currentProject} placeholder="Aucun projet chargé" readonly />
    <button
      class="bg-blue-600 hover:bg-blue-700 px-3 py-1 rounded text-sm font-medium transition-colors"
    >
      {$_('app.browse')}
    </button>
  </div>

  <!-- Right: Controls -->
  <div class="flex items-center gap-4">
    <button
      class="text-gray-400 hover:text-white transition-colors px-2 py-1 flex items-center gap-1"
      onclick={showHelp}
      title="Aide et documentation"
    >
      <Icon icon="hugeicons:help-square" class="w-6 h-6 text-blue-600" />
      {$_('app.help')}
    </button>

    <button
      class="text-gray-400 hover:text-white transition-colors px-2 py-1 flex items-center gap-1"
      onclick={() => (showAboutModal = true)}
      title="Informations sur RenExtract"
    >
      <Icon icon="hugeicons:information-square" class="w-6 h-6 text-blue-600" />
      {$_('app.about')}
    </button>
  </div>
</header>
