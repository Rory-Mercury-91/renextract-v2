<script lang="ts">
  /* eslint-env browser */
  import { apiService } from '$lib/api';
  import Icon from '@iconify/svelte';
  import { _ } from 'svelte-i18n';
  import packageJson from '../../package.json' assert { type: 'json' };
  import { editorPath } from '../stores/app';
  import AboutModal from './AboutModal.svelte';
  import UpdateManager from './UpdateManager.svelte';

  let showAboutModal = $state(false);

  function showHelp() {
    window.alert('Aide RenExtract - Fonctionnalités en cours de développement');
  }
</script>

{#if showAboutModal}
  <AboutModal bind:showAboutModal />
{/if}

<header
  class="flex h-20 items-center justify-between gap-4 text-nowrap border-b border-gray-700 bg-gray-800 p-4 text-white"
>
  <!-- Left: App Name + Version -->
  <div class="flex min-w-40 items-center gap-4">
    <img
      src="/assets/logo.webp"
      alt="Logo RenExtract"
      class="h-12 w-12 rounded-xl object-contain"
    />

    <div>
      <h1 class="text-lg font-bold">RenExtract</h1>
      <p class="text-xs text-gray-400">v{packageJson.version}</p>
    </div>
  </div>

  <!-- Center: Project Bar -->
  <div class="flex w-full items-center justify-center gap-2">
    <Icon icon="hugeicons:folder-01" class="h-6 w-6 min-w-6 text-yellow-500" />
    <input
      class="w-full max-w-64 rounded-lg bg-slate-100 px-2 py-1 text-sm text-gray-700"
      style:direction="rtl"
      value={$editorPath}
      oninput={e => {
        $editorPath = e.currentTarget.value;
      }}
      placeholder={$editorPath || 'Aucun projet chargé'}
    />
    <button
      class="rounded bg-blue-600 px-3 py-1 text-sm font-medium transition-colors hover:bg-blue-700"
      onclick={() =>
        apiService.openDialog(
          {
            path: $editorPath,
            dialog_type: 'folder',
            title: 'Sélectionner le dossier du jeu',
            initialdir: 'C:\\',
            must_exist: true,
          },
          {
            setPath: (path: string) => {
              $editorPath = path;
            },
          }
        )}
    >
      {$_('app.browse')}
    </button>
  </div>

  <!-- Right: Controls -->
  <div class="flex items-center gap-4">
    <!-- Gestionnaire de mise à jour -->
    <UpdateManager showSettings={true} autoCheck={true} />

    <button
      class="flex items-center gap-1 px-2 py-1 text-gray-400 transition-colors hover:text-white"
      onclick={showHelp}
      title="Aide et documentation"
    >
      <Icon icon="hugeicons:help-square" class="h-6 w-6 text-blue-600" />
      {$_('app.help')}
    </button>

    <button
      class="flex items-center gap-1 px-2 py-1 text-gray-400 transition-colors hover:text-white"
      onclick={() => (showAboutModal = true)}
      title="Informations sur RenExtract"
    >
      <Icon icon="hugeicons:information-square" class="h-6 w-6 text-blue-600" />
      {$_('app.about')}
    </button>
  </div>
</header>
