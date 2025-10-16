<script lang="ts">
  import { _, locales } from 'svelte-i18n';
  import { appSettings } from '../stores/app';

  const language = {
    fr: 'Français',
    en: 'Anglais',
  };
</script>

<section class="h-full w-full space-y-8 rounded-lg p-6">
  <div>
    <h2 class="mb-4 text-2xl font-bold text-blue-600 dark:text-blue-400">
      {$_('settings_app.title')}
    </h2>
    <p class="mb-6 text-gray-600 dark:text-gray-400">
      {$_('settings_app.description')}
    </p>
  </div>
  <div class="space-y-4">
    <h3 class="flex items-center text-lg font-semibold">{$_('settings_app.general_settings')}</h3>
    <div class="grid grid-cols-2 gap-4">
      <div>
        <label for="language-select" class="mb-2 block text-sm font-medium"
          >{$_('settings_app.interface_language')}</label
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
          {$_('settings_app.interface_theme')}
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
        <span class=""> {$_('settings_app.translator_feature')}</span>
      </label>

      <label
        class="flex cursor-pointer items-center rounded p-2 hover:bg-gray-200 dark:hover:bg-gray-800"
      >
        <input
          type="checkbox"
          bind:checked={$appSettings.debugActive}
          class="mr-3 h-4 w-4"
        />
        <span class=""> {$_('settings_app.debug_mode')} </span>
      </label>
    </div>
  </div>

  <!-- Ouvertures automatiques -->
  <div class="space-y-4">
    <h3 class="flex items-center text-lg font-semibold">
      🚀 {$_('settings_app.auto_openings')}
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
          <span class=""> {$_('settings_app.auto_files')} </span>
        </label>

        <label
          class="flex cursor-pointer items-center rounded p-2 hover:bg-gray-200 dark:hover:bg-gray-800"
        >
          <input
            type="checkbox"
            bind:checked={$appSettings.autoOpenings.folders}
            class="mr-3 h-4 w-4"
          />
          <span class=""> {$_('settings_app.auto_folders')} </span>
        </label>
      </div>

      <div class="space-y-3">
        <label
          class="flex cursor-pointer items-center rounded p-2 hover:bg-gray-200 dark:hover:bg-gray-800"
        >
          <input
            type="checkbox"
            bind:checked={$appSettings.autoOpenings.outputField}
            class="mr-3 h-4 w-4"
          />
          <span class=""> {$_('settings_app.auto_output_field')} </span>
        </label>

        <label
          class="flex cursor-pointer items-center rounded p-2 hover:bg-gray-200 dark:hover:bg-gray-800"
        >
          <input
            type="checkbox"
            bind:checked={$appSettings.autoOpenings.lastProject}
            class="mr-3 h-4 w-4"
          />
          <span class=""> {$_('settings_app.auto_last_project')} </span>
        </label>
      </div>
    </div>
  </div>
</section>
