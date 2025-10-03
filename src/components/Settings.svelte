<script lang="ts">
  import { apiService } from '../lib/api';
  import CustomModal from './CustomModal.svelte';
  import ThemeCustomizer from './ThemeCustomizer.svelte';

  // Configuration model - simplified debug mode
  let config = {
    language: 'fr',
    theme: 'dark',
    debugActive: false, // Single debug mode (false=Level 3, true=Level 4)
    autoOpenings: {
      files: true,
      folders: true,
      reports: false,
      outputField: false
    },
    externalTools: {
      textEditor: 'VS Code',
      translator: ''
    },
    paths: {
      renpySdk: '',
      vscode: '',
      sublime: '',
      notepad: '',
      atom: ''
    },
    folders: {
      temporary: '01_Temporary/',
      reports: '02_Reports/',
      backups: '03_Backups/',
      configs: '04_Configs/'
    },
    extraction: {
      placeholderFormat: 'PLACEHOLDER_{n}',
      encoding: 'UTF-8'
    },
    colors: {
      // Couleurs de base
      background: {
        primary: '#1a1a1a',
        secondary: '#2a2a2a',
        tertiary: '#3a3a3a',
        header: '#262626',
        sidebar: '#1e1e1e',
        modal: '#2a2a2a',
        input: '#3a3a3a'
      },
      text: {
        primary: '#ffffff',
        secondary: '#cccccc',
        tertiary: '#999999',
        placeholder: '#666666',
        accent: '#60a5fa'
      },
      border: {
        primary: '#4a4a4a',
        secondary: '#5a5a5a',
        focus: '#60a5fa',
        hover: '#6a6a6a'
      },
      // Couleurs des boutons
      buttons: {
        extract: '#3B82F6',
        reconstruct: '#10B981',
        verify: '#F59E0B',
        dangerous: '#ef4444',
        warning: '#f59e0b',
        success: '#10b981',
        neutral: '#6b7280'
      },
      // Couleurs d'accent
      accent: {
        primary: '#6366F1',
        secondary: '#8b5cf6',
        highlight: '#60a5fa',
        success: '#10b981',
        warning: '#f59e0b',
        danger: '#ef4444'
      },
      // États spéciaux
      states: {
        hover: '#404040',
        active: '#505050',
        disabled: '#666666',
        selected: '#4f46e5'
      }
    }
  };

  // Tab management
  let activeTab = 'interface_applications';
  let tabs = ['interface_applications', 'extraction_protection', 'theme_customizer', 'access_paths'];

  let saving = false;

  // Modal states
  let helpModal = { isOpen: false, title: '', content: '' };
  let browseModal = { 
    isOpen: false, 
    title: '', 
    inputValue: '', 
    inputPlaceholder: '',
    inputId: '' 
  };

  function switchTab(tabId: string) {
    activeTab = tabId;
  }

  async function loadSettings() {
    try {
      const result = await apiService.getSettings();
      if (result.success) {
        // Merge with default config to ensure all properties exist
        // Ensure all required fields exist with defaults
        const apiData = result.data || {};
        
        // Ensure the new colors structure exists
        const defaultColors = {
          background: {
            primary: '#1a1a1a',
            secondary: '#2a2a2a',
            tertiary: '#3a3a3a',
            header: '#262626',
            sidebar: '#1e1e1e',
            modal: '#2a2a2a',
            input: '#3a3a3a'
          },
          text: {
            primary: '#ffffff',
            secondary: '#cccccc',
            tertiary: '#999999',
            placeholder: '#666666',
            accent: '#60a5fa'
          },
          border: {
            primary: '#4a4a4a',
            secondary: '#5a5a5a',
            focus: '#60a5fa',
            hover: '#6a6a6a'
          },
          buttons: {
            extract: '#3B82F6',
            reconstruct: '#10B981',
            verify: '#F59E0B',
            dangerous: '#ef4444',
            warning: '#f59e0b',
            success: '#10b981',
            neutral: '#6b7280'
          },
          accent: {
            primary: '#6366F1',
            secondary: '#8b5cf6',
            highlight: '#60a5fa',
            success: '#10b981',
            warning: '#f59e0b',
            danger: '#ef4444'
          },
          states: {
            hover: '#404040',
            active: '#505050',
            disabled: '#666666',
            selected: '#4f46e5'
          }
        };
        
        config = {
          ...config,
          ...apiData,
          // Ensure paths exists even if not in API response
          paths: {
            renpySdk: '',
            vscode: '',
            sublime: '',
            notepad: '',
            atom: '',
            ...apiData.paths
          },
          // Ensure colors exists with full structure
          colors: {
            ...defaultColors,
            ...apiData.colors,
            // Deep merge the color categories
            background: { ...defaultColors.background, ...apiData.colors?.background },
            text: { ...defaultColors.text, ...apiData.colors?.text },
            border: { ...defaultColors.border, ...apiData.colors?.border },
            buttons: { ...defaultColors.buttons, ...apiData.colors?.buttons },
            accent: { ...defaultColors.accent, ...apiData.colors?.accent },
            states: { ...defaultColors.states, ...apiData.colors?.states }
          }
        };
        console.log('Settings loaded:', config);
      }
    } catch (error) {
      console.error('Erreur de chargement des paramètres:', error);
    }
  }

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
          atom: config.paths?.atom || ''
        }
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

  // Fonctions pour les boutons Parcourir
  function browseForFolder(inputId: string) {
    // Pour les dossiers (SDK Ren'Py)
    console.log('browseForFolder called with:', inputId);
    const input = document.getElementById(inputId) as HTMLInputElement;
    if (input) {
      // Simulation d'un sélecteur de carte
      const folderPath = prompt('Entrez le chemin vers le dossier SDK Ren\'Py (doit contenir renpy.exe):', 
        input.value || 'C:\\RenPy\\renpy-8.0.3');
      if (folderPath) {
        if (!config.paths) config.paths = {};
        config.paths.renpySdk = folderPath;
        input.value = folderPath;
        console.log('SDK Ren\'Py path updated:', folderPath);
      }
    } else {
      console.log('Input element not found:', inputId);
    }
  }

  function browseForFile(inputId: string) {
    // Pour les fichiers .exe des éditeurs
    console.log('browseForFile called with:', inputId);
    const input = document.getElementById(inputId) as HTMLInputElement;
    if (input) {
      const editorName = inputId.replace('-path', '');
      console.log('Editor name:', editorName);
      const defaultPaths: {[key: string]: string} = {
        'vscode': 'C:\\Users\\VotreNom\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe',
        'sublime': 'C:\\Program Files\\Sublime Text\\subl.exe',
        'notepad': 'C:\\Program Files\\Notepad++\\notepad++.exe',
        'atom': 'C:\\Users\\VotreNom\\AppData\\Local\\atom\\atom.exe'
      };
      
      const editorPath = prompt(`Entrez le chemin vers ${editorName.toUpperCase()}:`, 
        input.value || defaultPaths[editorName] || '');
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

  function openPathDefault(editorName: string) {
    // Ouvrir les options par défaut et détecter automatiquement
    const defaultPaths: {[key: string]: string} = {
      'vscode': 'C:\\Users\\VotreNom\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe',
      'sublime': 'C:\\Program Files\\Sublime Text\\subl.exe',
      'notepad': 'C:\\Program Files\\Notepad++\\notepad++.exe',
      'atom': 'C:\\Users\\VotreNom\\AppData\\Local\\atom\\atom.exe'
    };
    
    alert(`💡 Chemins par défaut pour ${editorName.toUpperCase()}:\n\n${defaultPaths[editorName]}\n\nCes chemins peuvent varier selon votre installation.`);
  }

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

  async function showBrowse(title: string, placeholder: string, inputId: string, currentValue: string = '') {
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
        
        switch(inputId) {
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
          inputId 
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
        inputId 
      };
    }
  }

  function handleBrowseConfirm(event: CustomEvent) {
    const { value } = event.detail;
    if (value && browseModal.inputId) {
      // Update the corresponding config field
      if (!config.paths) config.paths = {};
      
      switch(browseModal.inputId) {
        case 'renpy-sdk-path':
          config.paths.renpySdk = value;
          break;
        case 'vscode-path':
          config.paths.vscode = value;
          break;
        case 'sublime-path':
          config.paths.sublime = value;
          break;
        case 'notepad-path':
          config.paths.notepad = value;
          break;
        case 'atom-path':
          config.paths.atom = value;
          break;
      }
      
      // Update the actual input element
      const input = document.getElementById(browseModal.inputId) as HTMLInputElement;
      if (input) {
        input.value = value;
      }
    }
  }

  function handleThemeUpdate(event: CustomEvent) {
    const { colors } = event.detail;
    
    // Mettre à jour le thème global en temps réel
    updateGlobalTheme(colors);
    
    // Optionnel: sauvegarder automatiquement les changements de couleur
    console.log('Theme updated:', colors);
  }

  function updateGlobalTheme(colors: any) {
    // Appeler la fonction de l'application principale pour mettre à jour les styles CSS
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('themeUpdate', {
        detail: { colors, themeType: config.theme }
      }));
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
      outputField: false
    };
    config.externalTools.textEditor = 'Sublime Text';
    saveSettings();
  }
</script>

<div class="h-full bg-gray-900 text-white flex flex-col">
  <!-- Title -->
  <div class="p-6 border-b border-gray-700">
    <h1 class="text-3xl font-bold text-blue-400">Paramètres</h1>
    
    <!-- Navigation tabs -->
    <div class="mt-6 flex space-x-1">
      {#each tabs as tab}
        <button
          class="tab-button text-sm font-medium {activeTab === tab ? 'active' : ''}"
          onclick={() => switchTab(tab)}
        >
          {#if tab === 'interface_applications'}
            Interface et applications
          {:else if tab === 'extraction_protection'}
            Extraction et protection
          {:else if tab === 'theme_customizer'}
            Personnalisation des thèmes
          {:else if tab === 'access_paths'}
            Chemins d'accès
          {:else}
            {tab.replace('_', ' ')}
          {/if}
        </button>
      {/each}
    </div>
  </div>

  <!-- Tab Content -->
  <div class="flex-1 overflow-y-auto">
    <div class="p-6 h-full">
      {#if activeTab === 'interface_applications'}
        <div class="settings-section space-y-8 p-6 rounded-lg">
          <div>
            <h2 class="text-2xl font-bold text-blue-400 mb-4">Interface et applications</h2>
            <p class="text-gray-400 mb-6">Configuration générale de l'interface utilisateur.</p>
          </div>

          <!-- Ouvertures automatiques -->
          <div class="space-y-4">
            <h3 class="text-lg font-semibold flex items-center">
              🚀 Ouvertures automatiques
            </h3>
            
            <!-- Layout 2 colonnes -->
            <div class="grid grid-cols-2 gap-4">
              <div class="space-y-3">
                <label class="flex items-center cursor-pointer p-2 rounded hover:bg-gray-800">
                  <input
                    type="checkbox"
                    bind:checked={config.autoOpenings.files}
                    class="mr-3 w-4 h-4"
                  />
                  <span class="text-white">
                    Ouverture automatique des fichiers
                  </span>
                </label>

                <label class="flex items-center cursor-pointer p-2 rounded hover:bg-gray-800">
                  <input
                    type="checkbox"
                    bind:checked={config.autoOpenings.folders}
                    class="mr-3 w-4 h-4"
                  />
                  <span class="text-white">
                    Ouverture automatique des dossiers
                  </span>
                </label>
              </div>

              <div class="space-y-3">
                <label class="flex items-center cursor-pointer p-2 rounded hover:bg-gray-800">
                  <input
                    type="checkbox"
                    bind:checked={config.autoOpenings.reports}
                    class="mr-3 w-4 h-4"
                  />
                  <span class="text-white">
                    Ouverture automatique du rapport
                  </span>
                </label>

                <label class="flex items-center cursor-pointer p-2 rounded hover:bg-gray-800">
                  <input
                    type="checkbox"
                    bind:checked={config.autoOpenings.outputField}
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
                  <label for="notification-mode" class="block text-sm font-medium mb-2">Mode de notification des résultats :</label>
                  <select
                    id="notification-mode"
                    class="unified-select"
                  >
                    <option value="status">Statut seulement</option>
                    <option value="dialog">Dialogue complet</option>
                    <option value="none">Aucune notification</option>
                  </select>
                </div>

                <label class="flex items-center cursor-pointer p-2 rounded hover:bg-gray-800">
                  <input
                    type="checkbox"
                    bind:checked={config.debugActive}
                    class="mr-3 w-4 h-4"
                  />
                  <span class="text-white">
                    Mode debug complet
                  </span>
                </label>
              </div>

              <!-- Colonne droite - Éditeur -->
              <div class="space-y-4">
                <div>
                  <label for="text-editor" class="block text-sm font-medium mb-2">Éditeur externe :</label>
                  <select
                    id="text-editor"
                    bind:value={config.externalTools.textEditor}
                    class="unified-select"
                  >
                  <option value="VS Code">VS Code</option>
                  <option value="Notepad++">Notepad++</option>
                  <option value="Atom/Pulsar">Atom/Pulsar</option>
                  <option value="Sublime Text">Sublime Text</option>
                  </select>
                  <p class="text-xs text-gray-400 mt-1">
                    Éditeur pour ouvrir les fichiers depuis l'interface temps réel et les rapports HTML.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

      <!-- Tabs placeholder -->
      {:else if activeTab === 'extraction_protection'}
        <div class="space-y-8">
          <div>
            <h3 class="text-xl font-semibold mb-4">Extraction & Protection</h3>
            <p class="text-gray-400">Configuration des paramètres d'extraction et de protection des données.</p>
            
            <div class="space-y-6">
              <!-- Configuration des placeholders -->
              <div>
                <h3 class="text-lg font-semibold mb-4">🔧 Configuration des placeholders</h3>
                <div class="space-y-4">
                  <div>
                    <label for="placeholder-format" class="block text-sm font-medium mb-2">Format des placeholders :</label>
                    <input
                      id="placeholder-format"
                      type="text"
                      bind:value={config.extraction.placeholderFormat}
                      placeholder="Ex: PLACEHOLDER_N"
                      class="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white focus:border-blue-500 focus:outline-none"
                    />
                    <p class="text-sm text-gray-400 mt-1">Format utilisé pour marquer les éléments à traduire</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

      {:else if activeTab === 'theme_customizer'}
        <div class="space-y-8">
          <div>
            <h3 class="text-xl font-semibold mb-4">🎨 Personnalisation complète des thèmes</h3>
            <p class="text-gray-400 mb-6">Modifiez TOUTES les couleurs de l'interface selon vos préférences personnelles.</p>
            
            <ThemeCustomizer 
              bind:config={config}
              showPreview={true}
              on:themeUpdate={handleThemeUpdate}
            />
          </div>
        </div>

      {:else if activeTab === 'button_colors_invalid'}
        <div class="space-y-8">
          <div>
            <h3 class="text-xl font-semibold mb-4">Couleurs des boutons</h3>
            <p class="text-gray-400">Personnalisez les couleurs de l'interface selon vos préférences.</p>
            
            <div class="space-y-6">
              <!-- Boutons principaux -->
              <div>
                <h3 class="text-lg font-semibold mb-4">🎨 Boutons principaux</h3>
                <div class="grid grid-cols-2 gap-6">
                  <div>
                    <label for="extract-color" class="block text-sm font-medium mb-2">Bouton Extraire :</label>
                    <div class="flex items-center gap-3">
                      <input
                        id="extract-color"
                        type="color"
                        bind:value={config.colors.buttons.extract}
                        class="w-12 h-8 border border-gray-600 rounded cursor-pointer"
                      />
                      <span class="text-sm text-gray-400">{config.colors.buttons.extract}</span>
                    </div>
                  </div>

                  <div>
                    <label for="reconstruct-color" class="block text-sm font-medium mb-2">Bouton Reconstruire :</label>
                    <div class="flex items-center gap-3">
                      <input
                        id="reconstruct-color"
                        type="color"
                        bind:value={config.colors.buttons.reconstruct}
                        class="w-12 h-8 border border-gray-600 rounded cursor-pointer"
                      />
                      <span class="text-sm text-gray-400">{config.colors.buttons.reconstruct}</span>
                    </div>
                  </div>

                  <div>
                    <label for="verify-color" class="block text-sm font-medium mb-2">Bouton Vérifier :</label>
                    <div class="flex items-center gap-3">
                      <input
                        id="verify-color"
                        type="color"
                        bind:value={config.colors.buttons.verify}
                        class="w-12 h-8 border border-gray-600 rounded cursor-pointer"
                      />
                      <span class="text-sm text-gray-400">{config.colors.buttons.verify}</span>
                    </div>
                  </div>

                  <div>
                    <label for="accent-color" class="block text-sm font-medium mb-2">Couleurs d'accent :</label>
                    <div class="flex items-center gap-3">
                      <input
                        id="accent-color"
                        type="color"
                        bind:value={config.colors.accent.primary}
                        class="w-12 h-8 border border-gray-600 rounded cursor-pointer"
                      />
                      <span class="text-sm text-gray-400">{config.colors.accent.primary}</span>
                    </div>
                  </div>
                </div>

                <!-- Prévisualisation -->
                <div>
                  <h3 class="text-lg font-semibold mb-4">👁️ Prévisualisation</h3>
                  <div class="flex gap-4 p-4 bg-gray-800 rounded-lg">
                    <button 
                      style="background-color: {config.colors.buttons.extract};"
                      class="px-4 py-2 text-white rounded hover:opacity-80 transition-opacity"
                    >
                      ⚡ Extraire
                    </button>
                    <button 
                      style="background-color: {config.colors.buttons.reconstruct};"
                      class="px-4 py-2 text-white rounded hover:opacity-80 transition-opacity"
                    >
                      🔨 Reconstruire
                    </button>
                    <button 
                      style="background-color: {config.colors.buttons.verify};"
                      class="px-4 py-2 text-white rounded hover:opacity-80 transition-opacity"
                    >
                      ✅ Vérifier
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

      {:else if activeTab === 'access_paths'}
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
                        bind:value={config.paths.renpySdk}
                        placeholder="Ex: C:\Ren'Py\ren'py-8.0.3"
                        class="w-full p-3 rounded-lg transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:border-gray-700 dark:text-white bg-white border-2 border-gray-300 hover:border-blue-400 focus:border-blue-500 text-gray-900 placeholder-gray-500 shadow-sm"
                      />
                      <div class="flex flex-col gap-1">
                        <button 
                          class="px-3 py-1 bg-green-600 hover:bg-green-700 text-white rounded text-sm transition-colors flex items-center gap-1"
                          onclick={() => showHelp('💡 SDK Ren\'Py', 'Le SDK Ren\'Py doit contenir le fichier renpy.exe. Vous pouvez télécharger la dernière version depuis le site officiel.\n\nLe dossier SDK doit contenir :\n• renpy.exe\n• renpy.py\n• Les scripts RenPy')}
                        >
                          <span class="text-xs">?</span> Aide
                        </button>
                        <button 
                          class="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm transition-colors flex items-center gap-1"
                          onclick={() => showBrowse('📁 Sélectionner le SDK Ren\'Py', 'C:\\RenPy\\renpy-8.0.3', 'renpy-sdk-path', config.paths?.renpySdk || '')}
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
                <p class="text-sm text-gray-400 mb-4">Spécifiez des chemins personnalisés pour vos éditeurs (optionnel):</p>
                
                <!-- Contrôles globaux -->
                <div class="flex gap-2 mb-6">
                <button 
                  class="px-3 py-1 bg-green-600 hover:bg-green-700 text-white rounded text-sm transition-colors flex items-center gap-1"
                  onclick={() => showHelp('📝 Chemins des éditeurs', 'Les chemins personnalisés permettent d\'utiliser des versions spécifiques de vos éditeurs de code.\n\nSi vous laissez ces champs vides, l\'application utilisera les chemins par défaut situés dans le PATH système.\n\nRecommandé pour : installations dans des dossiers non-standard, versions portables.')}
                >
                    <span class="text-xs">?</span> Aide
                  </button>
                  <button 
                    class="px-3 py-1 bg-yellow-600 hover:bg-yellow-700 text-white rounded text-sm transition-colors flex items-center gap-1"
                    onclick={() => resetEditorPaths()}
                  >
                    ↺ Reset
                  </button>
                </div>

                <!-- Grille des éditeurs -->
                <div class="grid grid-cols-2 gap-6">
                  <!-- Colonne gauche -->
                  <div class="space-y-6">
                    <!-- VSCode -->
                    <div>
                      <label for="vscode-path" class="block text-sm font-medium mb-2 flex items-center gap-2">
                        <span class="text-blue-500">🔵</span>
                        VSCode - Chemin vers l-exécutable:
                      </label>
                      <div class="flex items-center gap-2">
                        <input
                          type="text"
                          id="vscode-path"
                          bind:value={config.paths.vscode}
                          placeholder="Ex: C:\Users\VotreNom\AppData\Local\Programs\Microsoft VS Code\Code.exe"
                          class="w-full p-2 rounded-lg transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:border-gray-700 dark:text-white bg-white border-2 border-gray-300 hover:border-blue-400 focus:border-blue-500 text-gray-900 placeholder-gray-500 shadow-sm text-sm"
                        />
                        <button 
                          class="px-2 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm transition-colors"
                          onclick={() => browseForFile('vscode-path')}
                        >
                          📁 Parcourir
                        </button>
                        <button 
                          class="px-2 py-1 bg-gray-600 hover:bg-gray-700 text-white rounded text-sm transition-colors"
                          onclick={() => openPathDefault('vscode')}
                        >
                          📝
                        </button>
                      </div>
                    </div>

                    <!-- Sublime Text -->
                    <div>
                      <label for="sublime-path" class="block text-sm font-medium mb-2 flex items-center gap-2">
                        <span class="text-orange-500">⚡</span>
                        Sublime Text - Chemin vers l-exécutable:
                      </label>
                      <div class="flex items-center gap-2">
                        <input
                          type="text"
                          id="sublime-path"
                          bind:value={config.paths.sublime}
                          placeholder="Ex: C:\Program Files\Sublime Text\subl.exe"
                          class="w-full p-2 rounded-lg transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:border-gray-700 dark:text-white bg-white border-2 border-gray-300 hover:border-blue-400 focus:border-blue-500 text-gray-900 placeholder-gray-500 shadow-sm text-sm"
                        />
                        <button 
                          class="px-2 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm transition-colors"
                          onclick={() => browseForFile('sublime-path')}
                        >
                          📁 Parcourir
                        </button>
                        <button 
                          class="px-2 py-1 bg-gray-600 hover:bg-gray-700 text-white rounded text-sm transition-colors"
                          onclick={() => openPathDefault('sublime')}
                        >
                          📝
                        </button>
                      </div>
                    </div>
                  </div>

                  <!-- Colonne droite -->
                  <div class="space-y-6">
                    <!-- Notepad++ -->
                    <div>
                      <label for="notepad-path" class="block text-sm font-medium mb-2 flex items-center gap-2">
                        <span class="text-green-500">📝</span>
                        Notepad++ - Chemin vers l-exécutable:
                      </label>
                      <div class="flex items-center gap-2">
                        <input
                          type="text"
                          id="notepad-path"
                          bind:value={config.paths.notepad}
                          placeholder="Ex: C:\Program Files\Notepad++\notepad++.exe"
                          class="w-full p-2 rounded-lg transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:border-gray-700 dark:text-white bg-white border-2 border-gray-300 hover:border-blue-400 focus:border-blue-500 text-gray-900 placeholder-gray-500 shadow-sm text-sm"
                        />
                        <button 
                          class="px-2 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm transition-colors"
                          onclick={() => browseForFile('notepad-path')}
                        >
                          📁 Parcourir
                        </button>
                        <button 
                          class="px-2 py-1 bg-gray-600 hover:bg-gray-700 text-white rounded text-sm transition-colors"
                          onclick={() => openPathDefault('notepad')}
                        >
                          📝
                        </button>
                      </div>
                    </div>

                    <!-- Atom/Pulsar -->
                    <div>
                      <label for="atom-path" class="block text-sm font-medium mb-2 flex items-center gap-2">
                        <span class="text-purple-500">⚛️</span>
                        Atom/Pulsar - Chemin vers l-exécutable:
                      </label>
                      <div class="flex items-center gap-2">
                        <input
                          type="text"
                          id="atom-path"
                          bind:value={config.paths.atom}
                          placeholder="Ex: C:\Users\VotreNom\AppData\Local\atom\atom.exe"
                          class="w-full p-2 rounded-lg transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:border-gray-700 dark:text-white bg-white border-2 border-gray-300 hover:border-blue-400 focus:border-blue-500 text-gray-900 placeholder-gray-500 shadow-sm text-sm"
                        />
                        <button 
                          class="px-2 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm transition-colors"
                          onclick={() => browseForFile('atom-path')}
                        >
                          📁 Parcourir
                        </button>
                        <button 
                          class="px-2 py-1 bg-gray-600 hover:bg-gray-700 text-white rounded text-sm transition-colors"
                          onclick={() => openPathDefault('atom')}
                        >
                          📝
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      {/if}
    </div>
  </div>

  <!-- Action buttons -->
  <div class="p-6 border-t border-gray-700 bg-gray-800 flex justify-center">
    <div class="flex items-center space-x-4">
      <!-- Bouton de ménage -->
      <button
        class="px-4 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded-lg transition-colors flex items-center"
        onclick={() => alert('🧹 Nettoyage des fichiers temporaires, backups et reports...')}
      >
        🧹 Nettoyer les fichiers temporaires
      </button>

      <!-- Bouton réinitialiser application -->
      <button
        class="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors flex items-center"
        onclick={() => {
          if (confirm('Êtes-vous sûr de vouloir réinitialiser TOUTE l\'application ? Ceci remettra tous les paramètres, projets et configurations à leurs valeurs par défaut.')) {
            alert('🔄 Réinitialisation complète de l\'application...');
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
          if (confirm('Réinitialiser seulement les paramètres de cette page ?')) {
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

<!-- Custom Modals -->
<CustomModal
  bind:isOpen={helpModal.isOpen}
  title={helpModal.title}
  content={helpModal.content}
  confirmText="OK"
  cancelText={null}
/>

<CustomModal
  bind:isOpen={browseModal.isOpen}
  bind:inputValue={browseModal.inputValue}
  title={browseModal.title}
  placeholder={browseModal.inputPlaceholder}
  showInput={true}
  confirmText="Valider"
  cancelText="Annuler"
  on:confirm={handleBrowseConfirm}
/>
