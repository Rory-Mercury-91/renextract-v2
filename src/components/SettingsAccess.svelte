<script lang="ts">
  import { apiService } from '$lib/api';
  import { appSettings, appSettingsActions } from '../stores/app';

  let editorPath = $state($appSettings.paths.editor)
  
  let helpModal = { isOpen: false, title: '', content: '' };
  let browseModal = {
    isOpen: false,
    title: '',
    inputValue: '',
    inputPlaceholder: '',
    inputId: '',
  };

  const openPathDefault = (editorName: string) => {
    // Ouvrir les options par défaut et détecter automatiquement
    const defaultPaths: { [key: string]: string } = {
      vscode:
        'C:\\Users\\VotreNom\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe',
      sublime: 'C:\\Program Files\\Sublime Text\\subl.exe',
      notepad: 'C:\\Program Files\\Notepad++\\notepad++.exe',
      atom: 'C:\\Users\\VotreNom\\AppData\\Local\\atom\\atom.exe',
    };

    alert(
      `💡 Chemins par défaut pour ${editorName.toUpperCase()}:\n\n${defaultPaths[editorName]}\n\nCes chemins peuvent varier selon votre installation.`
    );
  };

  // New modal functions
  const showHelp = (title: string, content: string) => {
    helpModal = { isOpen: true, title, content };
  }

  const showBrowse = async (
    title: string,
    placeholder: string,
    inputId: string,
    currentValue: string = ''
  ) => {
    // Essayer le dialogue Windows natif d'abord
    try {
      let result;
      if (inputId === 'renpy-sdk-path') {
        result = await apiService.openFolderDialog();
      } else {
        result = await apiService.openFileDialog();
      }

      if (result.success && result.path) {
        // Mettre à jour directement
        if (!$appSettings.paths) appSettingsActions.resetSettingsPaths()

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

        console.log(`${inputId} path updated via Windows dialog:`, result.path);
      } else {
        // Fallback vers le modal custom si le dialogue Windows échoue
        browseModal = {
          isOpen: true,
          title,
          inputPlaceholder: placeholder,
          inputValue: currentValue,
          inputId,
        };
      }
    } catch (error) {
      console.warn('Windows dialog failed, falling back to modal:', error);
      // Fallback vers le modal custom
      browseModal = {
        isOpen: true,
        title,
        inputPlaceholder: placeholder,
        inputValue: currentValue,
        inputId,
      };
    }
  }
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
                class="w-full p-3 rounded-lg transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:border-gray-700 dark:text-white bg-white border-2 border-gray-300 hover:border-blue-400 focus:border-blue-500 text-gray-900 placeholder-gray-500 shadow-sm"
              />
              <div class="flex flex-col gap-1">
                <button
                  class="px-3 py-1 bg-green-600 hover:bg-green-700 text-white rounded text-sm transition-colors flex items-center gap-1"
                  onclick={() =>
                    showHelp(
                      "💡 SDK Ren'Py",
                      "Le SDK Ren'Py doit contenir le fichier renpy.exe. Vous pouvez télécharger la dernière version depuis le site officiel.\n\nLe dossier SDK doit contenir :\n• renpy.exe\n• renpy.py\n• Les scripts RenPy"
                    )}
                >
                  <span class="text-xs">?</span> Aide
                </button>
                <button
                  class="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm transition-colors flex items-center gap-1"
                  onclick={() =>
                    showBrowse(
                      "📁 Sélectionner le SDK Ren'Py",
                      'C:\\RenPy\\renpy-8.0.3',
                      'renpy-sdk-path',
                      $appSettings.paths?.renpySdk || ''
                    )}
                >
                  📁 Parcourir
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
              class="w-full p-2 rounded-lg transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:border-gray-700 dark:text-white bg-white border-2 border-gray-300 hover:border-blue-400 focus:border-blue-500 text-gray-900 placeholder-gray-500 shadow-sm text-sm"
            />
            <button
              class="px-2 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm transition-colors"
              onclick={() => showBrowse(
                "📁 Sélectionner l'éditeur",
                'C:\Program Files\Notepad++\notepad++.exe',
                'editor-path',
                $appSettings.paths?.editor || ''
              )}
            >
              📁 Parcourir
            </button>
            <button
              class="px-2 py-1 bg-gray-600 hover:bg-gray-700 text-white rounded text-sm transition-colors"
              onclick={() => openPathDefault('editor')}
            >
              📝
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
