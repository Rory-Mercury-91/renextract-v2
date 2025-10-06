<script lang="ts">
  /* eslint-env browser */
  import { apiService } from '$lib/api';
  import { appSettings, appSettingsActions } from '../stores/app';

  let editorPath = $state($appSettings.paths.editor);
  // État de chargement pour les dialogues
  let isDialogLoading = $state(false);

  const showBrowse = async (
    title: string,
    placeholder: string,
    inputId: string,
    currentValue: string = ''
  ) => {
    // Essayer le dialogue Windows natif d'abord
    isDialogLoading = true;
    try {
      let result;
      if (inputId === 'renpy-sdk-path') {
        result = await apiService.openFolderDialog();
      } else {
        result = await apiService.openFileDialog();
      }

      if (result.success && result.path && result.path.trim() !== '') {
        // Mettre à jour directement
        if (!$appSettings.paths) appSettingsActions.resetSettingsPaths();

        switch (inputId) {
          case 'renpy-sdk-path':
            $appSettings.paths.renpySdk = result.path;
            break;
          case 'editor-path':
            $appSettings.paths.editor = result.path;
            break;
        }

        // Mettre à jour l'input visuellement
        editorPath = result.path;

        // eslint-disable-next-line no-console
        console.log(`${inputId} path updated via Windows dialog:`, result.path);
      } else {
        // Fallback vers le modal custom si le dialogue Windows échoue
        // eslint-disable-next-line no-console
        console.log(
          'Windows dialog failed or returned empty, using fallback modal'
        );
      }
    } catch (error) {
      // eslint-disable-next-line no-console
      console.warn('Windows dialog failed, falling back to modal:', error);

      // Vérifier si c'est un timeout
      if (error instanceof Error && error.message.includes('timeout')) {
        // eslint-disable-next-line no-console
        console.warn(
          'Dialog timeout - user took too long to select a file/folder'
        );
      }
    } finally {
      isDialogLoading = false;
    }
  };
</script>

<div class="space-y-8">
  <div>
    <h3 class="text-xl font-semibold mb-4">Chemins d'accès</h3>

    <div class="space-y-8">
      <!-- SDK Ren'Py -->
      <div>
        <h3 class="text-lg font-semibold mb-4 flex items-center gap-2">
          🔧 SDK Ren'Py
        </h3>
        <div class="space-y-4">
          <div>
            <label for="renpy-sdk-path" class="block text-sm font-medium mb-2">
              Chemin vers le SDK Ren'Py (dossier contenant renpy.exe):
            </label>
            <div class="flex items-center gap-2">
              <input
                type="text"
                id="renpy-sdk-path"
                bind:value={$appSettings.paths.renpySdk}
                placeholder="Ex: C:\Ren'Py\ren'py-8.0.3"
                class="w-full p-3 rounded-lg transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:border-gray-700 border-2 border-gray-300 hover:border-blue-400 focus:border-blue-500 text-gray-900 placeholder-gray-500 shadow-sm"
              />
              <div class="flex flex-col gap-1">
                <button
                  class="px-3 py-1 bg-green-600 hover:bg-green-700 rounded text-sm transition-colors flex items-center gap-1"
                  onclick={() =>
                    window.alert(
                      "💡 Le SDK Ren'Py doit contenir le fichier renpy.exe. Vous pouvez télécharger la dernière version depuis le site officiel.\n\nLe dossier SDK doit contenir :\n• renpy.exe\n• renpy.py\n• Les scripts RenPy"
                    )}
                >
                  <span class="text-xs">?</span> Aide
                </button>
                <button
                  class="px-3 py-1 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed rounded text-sm transition-colors flex items-center gap-1"
                  disabled={isDialogLoading}
                  onclick={() =>
                    showBrowse(
                      "📁 Sélectionner le SDK Ren'Py",
                      'C:\\RenPy\\renpy-8.0.3',
                      'renpy-sdk-path',
                      $appSettings.paths?.renpySdk || ''
                    )}
                >
                  {isDialogLoading ? '⏳ Ouverture...' : '📁 Parcourir'}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Éditeurs de code -->
      <div>
        <h3 class="text-lg font-semibold mb-4 flex items-center gap-2">
          📝 Éditeurs de code - Chemins personnalisés
        </h3>
        <p class="text-sm text-gray-400 mb-4">
          Spécifiez le chemin personnalisé pour votre éditeur (optionnel):
        </p>
        <!-- Colonne gauche -->
        <div class="space-y-6">
          <label
            for="path"
            class="text-sm font-medium mb-2 flex items-center gap-2"
          >
            Chemin vers l'exécutable:
          </label>
          <div class="flex items-center gap-2">
            <input
              type="text"
              id="path"
              bind:value={$appSettings.paths.editor}
              placeholder="Ex: C:\Program Files\Notepad++\notepad++.exe"
              class="w-full p-2 rounded-lg transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:border-gray-700 border-2 border-gray-300 hover:border-blue-400 focus:border-blue-500 text-gray-900 placeholder-gray-500 shadow-sm text-sm"
            />
            <button
              class="px-2 py-1 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed rounded text-sm transition-colors"
              disabled={isDialogLoading}
              onclick={() =>
                showBrowse(
                  "📁 Sélectionner l'éditeur",
                  'C:\\Program Files\\Notepad++\\notepad++.exe',
                  'editor-path',
                  $appSettings.paths?.editor || ''
                )}
            >
              {isDialogLoading ? '⏳ Ouverture...' : '📁 Parcourir'}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
