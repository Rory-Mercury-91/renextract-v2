<script lang="ts">
  import { apiService } from '../lib/api';

  const currentTheme = $state<'light' | 'dark' | 'auto'>('dark');

  // Configuration model - simplified debug mode
  let config = {
    language: 'fr',
    theme: 'dark',
    debugActive: false, // Single debug mode (false=Level 3, true=Level 4)
    autoOpenings: {
      files: true,
      folders: true,
      reports: false,
      outputField: false,
    },
    externalTools: {
      textEditor: 'VS Code',
      translator: '',
    },
    paths: {
      renpySdk: '',
      vscode: '',
      sublime: '',
      notepad: '',
      atom: '',
    },
    folders: {
      temporary: '01_Temporary/',
      reports: '02_Reports/',
      backups: '03_Backups/',
      configs: '04_Configs/',
    },
    extraction: {
      placeholderFormat: 'PLACEHOLDER_{n}',
      encoding: 'UTF-8',
    },
  };

  // Tab management
  let activeTab = $state('interface_applications');
  let tabs = [
    {
      id: 'interface_applications',
      label: 'Interface et applications',
    },
    {
      id: 'extraction_protection',
      label: 'Extraction et protection',
    },
    {
      id: 'theme_customizer',
      label: 'Personnalisation des thèmes',
    },
    {
      id: 'access_paths',
      label: 'Chemins d\'accès',
    }
  ];

  let saving = $state(false);

  // Modal states
  let helpModal = { isOpen: false, title: '', content: '' };
  let browseModal = {
    isOpen: false,
    title: '',
    inputValue: '',
    inputPlaceholder: '',
    inputId: '',
  };

  async function saveSettings() {
    saving = true;
    try {
      // Ensure config.paths exists before saving
      const configToSave = {
        ...config,
        paths: {
          ...config.paths,
          renpySdk: config.paths?.renpySdk || '',
          vscode: config.paths?.vscode || '',
          sublime: config.paths?.sublime || '',
          notepad: config.paths?.notepad || '',
          atom: config.paths?.atom || '',
        },
      };

      const result = await apiService.updateSettings(configToSave);
      if (result.success) {
        alert('✅ Paramètres sauvegardés avec succès !');
      } else {
        alert('❌ Erreur lors de la sauvegarde');
      }
    } catch (error) {
      console.error('Erreur de sauvegarde:', error);
      alert('❌ Erreur lors de la sauvegarde');
    } finally {
      saving = false;
    }
  }

  function browseForFile(inputId: string) {
    // Pour les fichiers .exe des éditeurs
    console.log('browseForFile called with:', inputId);
    const input = document.getElementById(inputId) as HTMLInputElement;
    if (input) {
      const editorName = inputId.replace('-path', '');
      console.log('Editor name:', editorName);
      const defaultPaths: { [key: string]: string } = {
        vscode:
          'C:\\Users\\VotreNom\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe',
        sublime: 'C:\\Program Files\\Sublime Text\\subl.exe',
        notepad: 'C:\\Program Files\\Notepad++\\notepad++.exe',
        atom: 'C:\\Users\\VotreNom\\AppData\\Local\\atom\\atom.exe',
      };

      const editorPath = prompt(
        `Entrez le chemin vers ${editorName.toUpperCase()}:`,
        input.value || defaultPaths[editorName] || '',
      );
      if (editorPath) {
        if (!config.paths) config.paths = {};

        config.paths[editorName as keyof typeof config.paths] = editorPath;
        input.value = editorPath;
        console.log(`${editorName} path updated:`, editorPath);
      }
    } else {
      console.log('Input element not found:', inputId);
    }
  }

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
      `💡 Chemins par défaut pour ${editorName.toUpperCase()}:\n\n${defaultPaths[editorName]}\n\nCes chemins peuvent varier selon votre installation.`,
    );
  };

  function resetEditorPaths() {
    if (confirm('Réinitialiser tous les chemins des éditeurs ?')) {
      if (!config.paths) config.paths = {};
      config.paths.renpySdk = '';
      config.paths.vscode = '';
      config.paths.sublime = '';
      config.paths.notepad = '';
      config.paths.atom = '';
      saveSettings();
      alert('✅ Chemins des éditeurs réinitialisés !');
    }
  }

  // New modal functions
  function showHelp(title: string, content: string) {
    helpModal = { isOpen: true, title, content };
  }

  async function showBrowse(
    title: string,
    placeholder: string,
    inputId: string,
    currentValue: string = '',
  ) {
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
        if (!config.paths) config.paths = {};

        switch (inputId) {
          case 'renpy-sdk-path':
            config.paths.renpySdk = result.path;
            break;
          case 'vscode-path':
            config.paths.vscode = result.path;
            break;
          case 'sublime-path':
            config.paths.sublime = result.path;
            break;
          case 'notepad-path':
            config.paths.notepad = result.path;
            break;
          case 'atom-path':
            config.paths.atom = result.path;
            break;
        }

        // Mettre à jour l'input visuellement
        const input = document.getElementById(inputId) as HTMLInputElement;
        if (input) {
          input.value = result.path;
        }

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

  function updateGlobalTheme(colors: any) {
    // Appeler la fonction de l'application principale pour mettre à jour les styles CSS
    if (typeof window !== 'undefined') {
      window.dispatchEvent(
        new CustomEvent('themeUpdate', {
          detail: { colors, themeType: config.theme },
        }),
      );
    }
  }

  function resetSettings() {
    config.debugActive = false;
    config.language = 'fr';
    config.theme = 'dark';
    config.autoOpenings = {
      files: true,
      folders: true,
      reports: false,
      outputField: false,
    };
    config.externalTools.textEditor = 'Sublime Text';
    saveSettings();
  }
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

  
  <div class="space-y-8">
    <div>
      <h3 class="text-xl font-semibold mb-4">Extraction & Protection</h3>
      <p class="text-gray-400">
        Configuration des paramètres d'extraction et de protection des
        données.
      </p>

      <div class="space-y-6">
        <!-- Configuration des placeholders -->
        <div>
          <h3 class="text-lg font-semibold mb-4">
            🔧 Configuration des placeholders
          </h3>
          <div class="space-y-4">
            <div>
              <label
                for="placeholder-format"
                class="block text-sm font-medium mb-2"
                >Format des placeholders :</label
              >
              <input
                id="placeholder-format"
                type="text"
                bind:value={config.extraction.placeholderFormat}
                placeholder="Ex: PLACEHOLDER_N"
                class="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white focus:border-blue-500 focus:outline-none"
              />
              <p class="text-sm text-gray-400 mt-1">
                Format utilisé pour marquer les éléments à traduire
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
      

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
            resetSettings();
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
            resetSettings();
          }
        }}
        disabled={saving}
      >
        ⚙️ Réinitialiser les paramètres
      </button>
    </div>
  </div>
</div>
