<script lang="ts">
  import Icon from '@iconify/svelte';
  /* eslint-env browser */
  import { apiService } from '$lib/api';
  import { _ } from 'svelte-i18n';
  import { appSettings } from '../stores/app';
</script>

<div class="space-y-8">
  <div>
    <h3 class="mb-4 text-xl font-semibold">{$_('settings.access_paths')}</h3>

    <div class="space-y-8">
      <!-- SDK Ren'Py -->
      <div>
        <h3 class="mb-4 flex items-center gap-2 text-lg font-semibold">
          🔧 {$_('settings.renpy_sdk')}
        </h3>
        <div class="space-y-4">
          <div>
            <label for="renpy-sdk-path" class="mb-2 block text-sm font-medium">
              {$_('settings.renpy_sdk_path')}
            </label>
            <div class="flex items-center gap-2">
              <input
                type="text"
                id="renpy-sdk-path"
                bind:value={$appSettings.paths.renpySdk}
                placeholder={$_('settings.renpy_sdk_placeholder')}
                class="w-full rounded-lg border-2 border-gray-300 p-3 text-gray-900 placeholder-gray-500 shadow-sm transition-colors duration-200 hover:border-blue-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:border-gray-700 dark:bg-gray-800"
                readonly
              />
              <div class="flex flex-col gap-1">
                <button
                  class="flex items-center gap-1 rounded bg-slate-700 px-3 py-1 text-sm transition-colors hover:bg-slate-600"
                  onclick={() =>
                    window.alert($_('settings.renpy_sdk_help'))}
                >
                  <Icon
                    icon="hugeicons:help-square"
                    class="h-5 w-5 text-red-500"
                  />
                </button>
                <button
                  class="flex items-center justify-center gap-1 rounded bg-blue-600 px-3 py-1 text-sm transition-colors hover:bg-blue-500 disabled:cursor-not-allowed disabled:bg-gray-400"
                  onclick={() =>
                    apiService.openDialog(
                      {
                        path: $appSettings.paths.renpySdk,
                        dialog_type: 'folder',
                        title: $_('settings.select_sdk_folder'),
                        initialdir: 'C:\\',
                        must_exist: true,
                      },
                      {
                        setPath: (path: string) => {
                          $appSettings.paths.renpySdk = path;
                        },
                      }
                    )}
                >
                  <Icon
                    icon="hugeicons:folder-01"
                    class="h-5 w-5 text-yellow-500"
                  />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Éditeurs de code -->
      <div>
        <h3 class="mb-4 flex items-center gap-2 text-lg font-semibold">
          {$_('settings.code_editors')}
        </h3>
        <p class="mb-4 text-sm text-gray-400">
          {$_('settings.code_editors_description')}
        </p>
        <!-- Colonne gauche -->
        <div class="space-y-6">
          <label
            for="path"
            class="mb-2 flex items-center gap-2 text-sm font-medium"
          >
            {$_('settings.executable_path')}
          </label>
          <div class="flex items-center gap-2">
            <input
              type="text"
              id="path"
              bind:value={$appSettings.paths.editor}
              placeholder={$_('settings.editor_placeholder')}
              class="w-full rounded-lg border-2 border-gray-300 p-2 text-sm text-slate-200 placeholder-gray-500 shadow-sm transition-colors duration-200 hover:border-blue-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:border-gray-700 dark:bg-gray-800"
            />
            <div class="flex flex-col gap-1">
              <button
                class="flex items-center gap-1 rounded bg-slate-700 px-3 py-1 text-sm transition-colors hover:bg-slate-600"
                onclick={() =>
                  window.alert(
                    "💡 Le SDK Ren'Py doit contenir le fichier renpy.exe. Vous pouvez télécharger la dernière version depuis le site officiel.\n\nLe dossier SDK doit contenir :\n• renpy.exe\n• renpy.py\n• Les scripts RenPy"
                  )}
              >
                <Icon
                  icon="hugeicons:help-square"
                  class="h-5 w-5 text-red-500"
                />
              </button>
              <button
                class="flex items-center justify-center gap-1 rounded bg-blue-600 px-3 py-1 text-sm transition-colors hover:bg-blue-500 disabled:cursor-not-allowed disabled:bg-gray-400"
                onclick={() =>
                  apiService.openDialog(
                    {
                      path: $appSettings.paths.editor,
                      dialog_type: 'file',
                      title: "Sélectionner l'exécutable",
                      initialdir: 'C:\\Program Files',
                      filetypes: [
                        ['Exécutables', '*.exe'],
                        ['Tous les fichiers', '*.*'],
                      ],
                      must_exist: true,
                    },
                    {
                      setPath: (path: string) => {
                        $appSettings.paths.editor = path;
                      },
                    }
                  )}
              >
                <Icon
                  icon="hugeicons:folder-01"
                  class="h-5 w-5 text-yellow-500"
                />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
