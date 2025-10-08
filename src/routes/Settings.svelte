<script lang="ts">
  /* eslint-env browser */
  import RouteHeader from '$components/RouteHeader.svelte';
  import SettingsAccess from '$components/SettingsAccess.svelte';
  import SettingsApp from '$components/SettingsApp.svelte';
  import SettingsExtract from '$components/SettingsExtract.svelte';
  import type { Component } from 'svelte';
  import { _ } from 'svelte-i18n';
  import { appSettingsActions } from '../stores/app';
  // Tab management
  interface Tab {
    id: string;
    label: string;
    component: Component<any, Record<string, any>>;
  }

  let activeTab = $state('interface_applications');

  const tabs: Tab[] = [
    {
      id: 'interface_applications',
      label: 'Interface et applications',
      component: SettingsApp,
    },
    {
      id: 'extraction_protection',
      label: 'Extraction et protection',
      component: SettingsExtract,
    },
    {
      id: 'access_paths',
      label: "Chemins d'accès",
      component: SettingsAccess,
    },
  ];

  const saving = $state(false);
</script>

<section class="flex min-h-full flex-col justify-between text-white">
  <RouteHeader
    title={$_('navigation.settings')}
    description={$_('navigation.settings_description')}
    icon="hugeicons:settings-01"
    color="text-gray-300"
  >
    <div class="flex w-full justify-between space-x-1">
      {#each tabs as tab}
        <button
          class="tab-button flex h-10 w-full items-center justify-center text-sm font-medium hover:bg-gray-700"
          class:bg-blue-600!={activeTab === tab.id}
          onclick={() => (activeTab = tab.id)}
        >
          {tab.label}
        </button>
      {/each}
    </div>
  </RouteHeader>

  <!-- Tab Content -->
  <div class="h-full flex-1 p-6">
    {#each tabs as tab}
      {#if activeTab === tab.id}
        {@const Component = tab.component}
        <Component />
      {/if}
    {/each}
  </div>

  <!-- Action buttons -->
  <div
    class="flex items-center justify-center space-x-4 border-t border-gray-700 bg-gray-800 p-6"
  >
    <!-- Bouton de ménage -->
    <button
      class="flex items-center rounded-lg bg-orange-600 px-4 py-2 transition-colors hover:bg-orange-700"
      onclick={() =>
        window.alert(
          '🧹 Nettoyage des fichiers temporaires, backups et reports...'
        )}
    >
      🧹 Nettoyer les fichiers temporaires
    </button>

    <!-- Bouton réinitialiser application -->
    <button
      class="flex items-center rounded-lg bg-red-600 px-4 py-2 transition-colors hover:bg-red-700"
      onclick={() => {
        if (
          window.confirm(
            "Êtes-vous sûr de vouloir réinitialiser TOUTE l'application ? Ceci remettra tous les paramètres, projets et configurations à leurs valeurs par défaut."
          )
        ) {
          window.alert("🔄 Réinitialisation complète de l'application...");
          appSettingsActions.resetSettings();
        }
      }}
    >
      🔄 Réinitialiser l'application
    </button>

    <!-- Bouton réinitialiser paramètres seulement -->
    <button
      class="rounded-lg bg-yellow-600 px-4 py-2 transition-colors hover:bg-yellow-700"
      onclick={() => {
        if (
          window.confirm(
            'Réinitialiser seulement les paramètres de cette page ?'
          )
        ) {
          appSettingsActions.resetSettings();
        }
      }}
      disabled={saving}
    >
      ⚙️ Réinitialiser les paramètres
    </button>
  </div>
</section>
