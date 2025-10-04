<script lang="ts">
  import { locale, locales } from 'svelte-i18n';
  import { appSettings } from '../stores/app';

  const language = {
    fr: 'Français',
    en: 'Anglais',
  };
</script>

<section class="h-full w-fulln space-y-8 p-6 rounded-lg">
  <div>
    <h2 class="text-2xl font-bold text-blue-400 mb-4">
      Interface et applications
    </h2>
    <p class="text-gray-400 mb-6">
      Configuration générale de l'interface utilisateur.
    </p>
  </div>
  <div class="space-y-4">
    <h3 class="text-lg font-semibold flex items-center">Paramètres généraux</h3>
    <div class="grid grid-cols-2 gap-4">
      <div>
        <select bind:value={$locale} class="bg-primary rounded-lg px-2 py-1">
          {#each $locales as locale}
            <option value={locale}
              >{locale.toUpperCase()} - {language[
                locale as keyof typeof language
              ]}</option
            >
          {/each}
        </select>
        <span class="text-white ml-2"> Langue de l'interface </span>
      </div>
      <!-- Theme Toggle -->
      <div>
        <select class="bg-primary rounded-lg px-2 py-1">
          <option value="auto">Auto</option>
          <option value="light">Clair</option>
          <option value="dark">Sombre</option>
        </select>
        <span class="text-white ml-2"> Thème de l'interface </span>
      </div>
    </div>
  </div>

  <!-- Ouvertures automatiques -->
  <div class="space-y-4">
    <h3 class="text-lg font-semibold flex items-center">
      🚀 Ouvertures automatiques
    </h3>

    <!-- Layout 2 colonnes -->
    <div class="grid grid-cols-2 gap-4">
      <div class="space-y-3">
        <label
          class="flex items-center cursor-pointer p-2 rounded hover:bg-gray-800"
        >
          <input
            type="checkbox"
            bind:checked={$appSettings.autoOpenings.files}
            class="mr-3 w-4 h-4"
          />
          <span class="text-white"> Ouverture automatique des fichiers </span>
        </label>

        <label
          class="flex items-center cursor-pointer p-2 rounded hover:bg-gray-800"
        >
          <input
            type="checkbox"
            bind:checked={$appSettings.autoOpenings.folders}
            class="mr-3 w-4 h-4"
          />
          <span class="text-white"> Ouverture automatique des dossiers </span>
        </label>
      </div>

      <div class="space-y-3">
        <label
          class="flex items-center cursor-pointer p-2 rounded hover:bg-gray-800"
        >
          <input
            type="checkbox"
            bind:checked={$appSettings.autoOpenings.reports}
            class="mr-3 w-4 h-4"
          />
          <span class="text-white"> Ouverture automatique du rapport </span>
        </label>

        <label
          class="flex items-center cursor-pointer p-2 rounded hover:bg-gray-800"
        >
          <input
            type="checkbox"
            bind:checked={$appSettings.autoOpenings.outputField}
            class="mr-3 w-4 h-4"
          />
          <span class="text-white">
            Affichage du champ de chemin de sortie
          </span>
        </label>
      </div>
    </div>
  </div>

  <!-- Apparence et notifications -->
  <div class="space-y-4">
    <h3 class="text-lg font-semibold flex items-center">
      🔔 Apparence et notifications
    </h3>

    <div class="grid grid-cols-2 gap-8">
      <!-- Colonne gauche -->
      <div class="space-y-4">
        <div>
          <label for="notification-mode" class="block text-sm font-medium mb-2"
            >Mode de notification des résultats :</label
          >
          <select
            id="notification-mode"
            class="bg-primary rounded-lg px-2 py-1"
          >
            <option value="status">Statut seulement</option>
            <option value="dialog">Dialogue complet</option>
            <option value="none">Aucune notification</option>
          </select>
        </div>

        <label
          class="flex items-center cursor-pointer p-2 rounded hover:bg-gray-800"
        >
          <input
            type="checkbox"
            bind:checked={$appSettings.debugActive}
            class="mr-3 w-4 h-4"
          />
          <span class="text-white"> Mode debug complet </span>
        </label>
      </div>

      <!-- Colonne droite - Éditeur -->
      <div class="space-y-4">
        <div>
          <label for="text-editor" class="block text-sm font-medium mb-2"
            >Éditeur externe :</label
          >
          <select
            id="text-editor"
            bind:value={$appSettings.externalTools.textEditor}
            class="bg-primary rounded-lg px-2 py-1"
          >
            <option value="VS Code">VS Code</option>
            <option value="Notepad++">Notepad++</option>
            <option value="Atom/Pulsar">Atom/Pulsar</option>
            <option value="Sublime Text">Sublime Text</option>
          </select>
          <p class="text-xs text-gray-400 mt-1">
            Éditeur pour ouvrir les fichiers depuis l'interface temps réel et
            les rapports HTML.
          </p>
        </div>
      </div>
    </div>
  </div>
</section>
