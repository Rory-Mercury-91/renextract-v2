<script lang="ts">
  import { locales } from 'svelte-i18n';
  import { appSettings } from '../stores/app';

  const language = {
    fr: 'Français',
    en: 'Anglais',
  };
</script>

<section class="h-full w-full space-y-8 rounded-lg p-6">
  <div>
    <h2 class="mb-4 text-2xl font-bold text-blue-600 dark:text-blue-400">
      Interface et applications
    </h2>
    <p class="mb-6 text-gray-600 dark:text-gray-400">
      Configuration générale de l'interface utilisateur.
    </p>
  </div>
  <div class="space-y-4">
    <h3 class="flex items-center text-lg font-semibold">Paramètres généraux</h3>
    <div class="grid grid-cols-2 gap-4">
      <div>
        <label for="language-select" class="mb-2 block text-sm font-medium"
          >Langue de l'interface</label
        >
        <select
          id="language-select"
          bind:value={$appSettings.language}
          class="rounded-lg bg-gray-100 px-2 py-1 text-gray-900 dark:bg-gray-700 dark:text-white"
        >
          {#each $locales as locale}
            <option value={locale}
              >{locale.toUpperCase()} - {language[
                locale as keyof typeof language
              ]}</option
            >
          {/each}
        </select>
      </div>
      <!-- Theme Toggle -->
      <div>
        <label for="theme-select" class="mb-2 block text-sm font-medium">
          Thème de l'interface
        </label>
        <select
          id="theme-select"
          bind:value={$appSettings.theme}
          class="rounded-lg bg-gray-100 px-2 py-1 text-gray-900 dark:bg-gray-700 dark:text-white"
        >
          <option value="auto">Auto</option>
          <option value="light">Clair</option>
          <option value="dark">Sombre</option>
        </select>
      </div>

      <label
        class="flex cursor-pointer items-center rounded p-2 hover:bg-gray-200 dark:hover:bg-gray-800"
      >
        <input
          type="checkbox"
          bind:checked={$appSettings.translatorFeature}
          class="mr-3 h-4 w-4"
        />
        <span class=""> Fonctionnalité de traduction par GPU</span>
      </label>
    </div>
  </div>

  <!-- Ouvertures automatiques -->
  <div class="space-y-4">
    <h3 class="flex items-center text-lg font-semibold">
      🚀 Ouvertures automatiques
    </h3>

    <!-- Layout 2 colonnes -->
    <div class="grid grid-cols-2 gap-4">
      <div class="space-y-3">
        <label
          class="flex cursor-pointer items-center rounded p-2 hover:bg-gray-200 dark:hover:bg-gray-800"
        >
          <input
            type="checkbox"
            bind:checked={$appSettings.autoOpenings.files}
            class="mr-3 h-4 w-4"
          />
          <span class=""> Ouverture automatique des fichiers </span>
        </label>

        <label
          class="flex cursor-pointer items-center rounded p-2 hover:bg-gray-200 dark:hover:bg-gray-800"
        >
          <input
            type="checkbox"
            bind:checked={$appSettings.autoOpenings.folders}
            class="mr-3 h-4 w-4"
          />
          <span class=""> Ouverture automatique des dossiers </span>
        </label>
      </div>

      <div class="space-y-3">
        <label
          class="flex cursor-pointer items-center rounded p-2 hover:bg-gray-200 dark:hover:bg-gray-800"
        >
          <input
            type="checkbox"
            bind:checked={$appSettings.autoOpenings.reports}
            class="mr-3 h-4 w-4"
          />
          <span class=""> Ouverture automatique du rapport </span>
        </label>

        <label
          class="flex cursor-pointer items-center rounded p-2 hover:bg-gray-200 dark:hover:bg-gray-800"
        >
          <input
            type="checkbox"
            bind:checked={$appSettings.autoOpenings.outputField}
            class="mr-3 h-4 w-4"
          />
          <span class=""> Affichage du champ de chemin de sortie </span>
        </label>
      </div>
    </div>
  </div>

  <!-- Apparence et notifications -->
  <div class="space-y-4">
    <h3 class="flex items-center text-lg font-semibold">
      🔔 Apparence et notifications
    </h3>

    <div class="grid grid-cols-2 gap-8">
      <!-- Colonne gauche -->
      <div class="space-y-4">
        <div>
          <label for="notification-mode" class="mb-2 block text-sm font-medium"
            >Mode de notification des résultats :</label
          >
          <select
            id="notification-mode"
            class="rounded-lg bg-gray-100 px-2 py-1 text-gray-900 dark:bg-gray-700 dark:text-white"
          >
            <option value="status">Statut seulement</option>
            <option value="dialog">Dialogue complet</option>
            <option value="none">Aucune notification</option>
          </select>
        </div>

        <label
          class="flex cursor-pointer items-center rounded p-2 hover:bg-gray-200 dark:hover:bg-gray-800"
        >
          <input
            type="checkbox"
            bind:checked={$appSettings.debugActive}
            class="mr-3 h-4 w-4"
          />
          <span class=""> Mode debug complet </span>
        </label>
      </div>

      <!-- Colonne droite - Éditeur -->
      <div class="space-y-4">
        <div>
          <label for="text-editor" class="mb-2 block text-sm font-medium"
            >Éditeur externe :</label
          >
          <select
            id="text-editor"
            bind:value={$appSettings.externalTools.textEditor}
            class="rounded-lg bg-gray-100 px-2 py-1 text-gray-900 dark:bg-gray-700 dark:text-white"
          >
            <option value="VS Code">VS Code</option>
            <option value="Notepad++">Notepad++</option>
            <option value="Atom/Pulsar">Atom/Pulsar</option>
            <option value="Sublime Text">Sublime Text</option>
          </select>
          <p class="mt-1 text-xs text-gray-600 dark:text-gray-400">
            Éditeur pour ouvrir les fichiers depuis l'interface temps réel et
            les rapports HTML.
          </p>
        </div>
      </div>
    </div>
  </div>
</section>
