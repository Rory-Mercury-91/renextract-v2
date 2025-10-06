<script lang="ts">
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

<section class="min-h-full flex flex-col justify-between text-white">
  <RouteHeader
    title={$_('navigation.settings')}
    description={$_('navigation.settings_description')}
    icon="hugeicons:settings-01"
    color="text-gray-300"
  >
    <div class="flex space-x-1 w-full justify-between">
      {#each tabs as tab}
        <button
          class="tab-button text-sm font-medium w-full h-10 flex justify-center items-center hover:bg-gray-700"
          class:bg-blue-600!={activeTab === tab.id}
          onclick={() => (activeTab = tab.id)}
        >
          {tab.label}
        </button>
      {/each}
    </div>
  </RouteHeader>

  <!-- Tab Content -->
  <div class="flex-1 p-6 h-full">
    {#each tabs as tab}
      {#if activeTab === tab.id}
        {@const Component = tab.component}
        <Component />
      {/if}
    {/each}
  </div>

  <!-- Action buttons -->
  <div
    class="p-6 border-t border-gray-700 bg-gray-800 flex justify-center items-center space-x-4"
  >
    <!-- Bouton de ménage -->
    <button
      class="px-4 py-2 bg-orange-600 hover:bg-orange-700 rounded-lg transition-colors flex items-center"
      onclick={() =>
        alert('🧹 Nettoyage des fichiers temporaires, backups et reports...')}
    >
      🧹 Nettoyer les fichiers temporaires
    </button>

    <!-- Bouton réinitialiser application -->
    <button
      class="px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg transition-colors flex items-center"
      onclick={() => {
        if (
          confirm(
            "Êtes-vous sûr de vouloir réinitialiser TOUTE l'application ? Ceci remettra tous les paramètres, projets et configurations à leurs valeurs par défaut."
          )
        ) {
          alert("🔄 Réinitialisation complète de l'application...");
          appSettingsActions.resetSettings();
        }
      }}
    >
      🔄 Réinitialiser l'application
    </button>

    <!-- Bouton réinitialiser paramètres seulement -->
    <button
      class="px-4 py-2 bg-yellow-600 hover:bg-yellow-700 rounded-lg transition-colors"
      onclick={() => {
        if (confirm('Réinitialiser seulement les paramètres de cette page ?')) {
          appSettingsActions.resetSettings();
        }
      }}
      disabled={saving}
    >
      ⚙️ Réinitialiser les paramètres
    </button>
  </div>
</section>
