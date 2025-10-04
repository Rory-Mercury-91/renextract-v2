<script lang="ts">
  import SettingsAccess from '$components/SettingsAccess.svelte';
  import SettingsApp from '$components/SettingsApp.svelte';
  import SettingsExtract from '$components/SettingsExtract.svelte';
  import type { Component } from 'svelte';
  import { appSettingsActions } from '../stores/app';
  // Tab management
  interface Tab {
    id: string;
    label: string;
    component: Component<any, Record<string, any>>;
  }
  
  let activeTab = $state('interface_applications');
  
  let tabs: Tab[] = [
    {
      id: 'interface_applications',
      label: 'Interface et applications',
      component: SettingsApp
    },
    {
      id: 'extraction_protection',
      label: 'Extraction et protection',
      component: SettingsExtract
    },
    {
      id: 'access_paths',
      label: 'Chemins d\'accès',
      component: SettingsAccess
    }
  ];

  let saving = $state(false);
</script>

<div class="h-full w-full bg-gray-900 text-white flex flex-col">
  <!-- Title -->
  <div class="pt-6 border-b border-gray-700">
    <h1 class="mx-6 text-3xl font-bold text-blue-400">Paramètres</h1>

    <!-- Navigation tabs -->
    <div class="mt-6 flex space-x-1 w-full justify-between">
      {#each tabs as tab}
        <button
          class="tab-button text-sm font-medium w-full h-10 flex justify-center items-center bg-gray-800 hover:bg-gray-700"
          class:bg-blue-600!={activeTab === tab.id}
          onclick={() => activeTab = tab.id}
        >
          {tab.label}
        </button>
      {/each}
    </div>
  </div>

  <!-- Tab Content -->
  <section class="flex-1 overflow-y-auto">
    <div class="p-6 h-full">
      {#each tabs as tab}
        {#if activeTab === tab.id}
          {@const Component = tab.component}
          <Component />
        {/if}
      {/each}
    </div>
  </section>

  <!-- Action buttons -->
  <div class="p-6 border-t border-gray-700 bg-gray-800 flex justify-center">
    <div class="flex items-center space-x-4">
      <!-- Bouton de ménage -->
      <button
        class="px-4 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded-lg transition-colors flex items-center"
        onclick={() =>
          alert('🧹 Nettoyage des fichiers temporaires, backups et reports...')}
      >
        🧹 Nettoyer les fichiers temporaires
      </button>

      <!-- Bouton réinitialiser application -->
      <button
        class="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors flex items-center"
        onclick={() => {
          if (
            confirm(
              "Êtes-vous sûr de vouloir réinitialiser TOUTE l'application ? Ceci remettra tous les paramètres, projets et configurations à leurs valeurs par défaut.",
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
        class="px-4 py-2 bg-yellow-600 hover:bg-yellow-700 text-white rounded-lg transition-colors"
        onclick={() => {
          if (
            confirm('Réinitialiser seulement les paramètres de cette page ?')
          ) {
            appSettingsActions.resetSettings();
          }
        }}
        disabled={saving}
      >
        ⚙️ Réinitialiser les paramètres
      </button>
    </div>
  </div>
</div>
