<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { appState } from '../stores/app';

  const dispatcher = createEventDispatcher();

  export let config: any;
  export let showPreview = false;

  // Ensure config.colors has the right structure on mount
  $: if (config && !config.colors?.background) {
    console.warn('Config colors structure missing, initializing...');
    config.colors = config.colors || {
      background: { primary: '#1a1a1a', secondary: '#2a2a2a', tertiary: '#3a3a3a', header: '#262626', sidebar: '#1e1e1e', modal: '#2a2a2a', input: '#3a3a3a' },
      text: { primary: '#ffffff', secondary: '#cccccc', tertiary: '#999999', placeholder: '#666666', accent: '#60a5fa' },
      border: { primary: '#4a4a4a', secondary: '#5a5a5a', focus: '#60a5fa', hover: '#6a6a6a' },
      buttons: { extract: '#3B82F6', reconstruct: '#10B981', verify: '#F59E0B', dangerous: '#ef4444', warning: '#f59e0b', success: '#10b981', neutral: '#6b7280' },
      accent: { primary: '#6366F1', secondary: '#8b5cf6', highlight: '#60a5fa', success: '#10b981', warning: '#f59e0b', danger: '#ef4444' },
      states: { hover: '#404040', active: '#505050', disabled: '#666666', selected: '#4f46e5' }
    };
  }

  // Appliquer les couleurs au chargement
  $: if (config && config.colors) {
    updateCSSVariables(config.colors);
  }

  let expandedSections: { [key: string]: boolean } = {};

  function toggleSection(section: string) {
    const isCurrentlyExpanded = expandedSections[section];
    
    if (isCurrentlyExpanded) {
      // If currently expanded, just close it
      expandedSections[section] = false;
    } else {
      // If not expanded, close all others first, then open this one
      expandedSections = {};
      expandedSections[section] = true;
    }
    
    // Reactive update for Svelte
    expandedSections = expandedSections;
  }

  function updateColor(path: string, value: string) {
    const keys = path.split('.');
    let target = config.colors;
    
    for (let i = 0; i < keys.length - 1; i++) {
      target = target[keys[i]];
    }
    
    target[keys[keys.length - 1]] = value;
    
    // Appliquer immédiatement aux CSS variables
    updateCSSVariables(config.colors);
    
    // Notifier le parent des changements
    dispatcher('themeUpdate', {
      path,
      value,
      colors: config.colors
    });
  }

  function getCurrentPath(path: string) {
    const keys = path.split('.');
    let target = config.colors;
    
    try {
      for (const key of keys) {
        if (!target || typeof target !== 'object') {
          return '#000000';
        }
        target = target[key];
      }
      
      return target || '#000000';
    } catch (error) {
      console.warn(`Failed to get path ${path}:`, error);
      return '#000000';
    }
  }

  function resetSection(section: string) {
    // Réinitialiser les couleurs selon le thème actuel
    if ($appState.currentTheme === 'dark') {
      switch(section) {
        case 'background':
          config.colors.background = {
            primary: '#1a1a1a',
            secondary: '#2a2a2a',
            tertiary: '#3a3a3a',
            header: '#262626',
            sidebar: '#1e1e1e',
            modal: '#2a2a2a',
            input: '#3a3a3a'
          };
          break;
        case 'text':
          config.colors.text = {
            primary: '#ffffff',
            secondary: '#cccccc',
            tertiary: '#999999',
            placeholder: '#666666',
            accent: '#60a5fa'
          };
          break;
        // ... autres sections
      }
    } else {
      switch(section) {
        case 'background':
          config.colors.background = {
            primary: '#ffffff',
            secondary: '#f8fafc',
            tertiary: '#f1f5f9',
            header: '#ffffff',
            sidebar: '#f8fafc',
            modal: '#ffffff',
            input: '#ffffff'
          };
          break;
        case 'text':
          config.colors.text = {
            primary: '#0f172a',
            secondary: '#475569',
            tertiary: '#64748b',
            placeholder: '#94a3b8',
            accent: '#3b82f6'
                      };
          break;
      }
    }
    
    dispatcher('themeUpdate', {
      path: section,
      value: null,
      colors: config.colors
    });
  }

  function copyTheme() {
    const themeJson = JSON.stringify(config.colors, null, 2);
    
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(themeJson);
        alert('✅ Thème copié dans le presse-papiers !');
      } else {
        // Fallback: utiliser une fenêtre temporaire
        const textarea = document.createElement('textarea');
        textarea.value = themeJson;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
        alert('✅ Thème copié !\n\nFallback utilisé car Clipboard API non disponible');
      }
    } catch (e) {
      alert('❌ Erreur lors de la copie: ' + e.message);
    }
  }

  function pasteTheme() {
    const userInput = prompt('Collez votre thème JSON ici:', '');
    
    if (userInput) {
      try {
        const newColors = JSON.parse(userInput);
        config.colors = { ...config.colors, ...newColors };
        dispatcher('themeUpdate', {
          path: 'paste',
          value: null,
          colors: config.colors
        });
        alert('✅ Thème collé avec succès !');
      } catch (e) {
        alert('❌ Erreur JSON: ' + e.message);
      }
    }
  }

  function copyCurrentColor(path: string) {
    const colorValue = getCurrentPath(path);
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(colorValue);
      } else {
        const textarea = document.createElement('textarea');
        textarea.value = colorValue;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
      }
    } catch (e) {
      alert('❌ Erreur lors de la copie: ' + e.message);
    }
  }

  // Thèmes prédéfinis
  const presetThemes = [
    {
      id: 'midnight',
      name: '🌙 Minuit',
      description: 'Sombre et élégant comme une nuit étoilée',
      naturalMode: 'dark',
      colors: {
        background: {
          primary: '#0a0a0a',
          secondary: '#1a1a2e',
          tertiary: '#16213e',
          header: '#1e1e2e',
          sidebar: '#0a0a0a',
          modal: '#1a1a2e',
          input: '#16213e'
        },
        text: {
          primary: '#e4e4e7',
          secondary: '#a1a1aa',
          tertiary: '#71717a',
          placeholder: '#52525b',
          accent: '#a78bfa'
        },
        border: {
          primary: '#374151',
          secondary: '#4b5563',
          focus: '#8b5cf6',
          hover: '#6b7280'
        },
        buttons: {
          extract: '#8b5cf6',
          reconstruct: '#06d6a0',
          verify: '#ffd23f',
          dangerous: '#f56565',
          warning: '#f6ad55',
          success: '#48bb78',
          neutral: '#718096'
        },
        accent: {
          primary: '#8b5cf6',
          secondary: '#a78bfa',
          highlight: '#06d6a0',
          success: '#48bb78',
          warning: '#f6ad55',
          danger: '#f56565'
        },
        states: {
          hover: '#2d3748',
          active: '#4a5568',
          disabled: '#718096',
          selected: '#8b5cf6'
        }
      }
    },
    {
      id: 'sunrise',
      name: '🌅 Lever de soleil',
      description: 'Chaleureux et énergique comme une aube dorée',
      naturalMode: 'light',
      colors: {
        background: {
          primary: '#fff7ed',
          secondary: '#fed7aa',
          tertiary: '#fef3c7',
          header: '#ffffff',
          sidebar: '#fed7aa',
          modal: '#fff7ed',
          input: '#ffffff'
        },
        text: {
          primary: '#1f2937',
          secondary: '#374151',
          tertiary: '#6b7280',
          placeholder: '#9ca3af',
          accent: '#f97316'
        },
        border: {
          primary: '#f3e8ff',
          secondary: '#e5e7eb',
          focus: '#f97316',
          hover: '#d1d5db'
        },
        buttons: {
          extract: '#f97316',
          reconstruct: '#059669',
          verify: '#d97706',
          dangerous: '#dc2626',
          warning: '#f59e0b',
          success: '#059669',
          neutral: '#6b7280'
        },
        accent: {
          primary: '#f97316',
          secondary: '#fb923c',
          highlight: '#059669',
          success: '#059669',
          warning: '#f59e0b',
          danger: '#dc2626'
        },
        states: {
          hover: '#fed7aa',
          active: '#fef3c7',
          disabled: '#d1d5db',
          selected: '#f97316'
        }
      }
    },
    {
      id: 'ocean',
      name: '🌊 Océan',
        description: 'Paix et sérénité comme les vagues de l\'océan',
      naturalMode: 'light',
      colors: {
        background: {
          primary: '#f0f9ff',
          secondary: '#e0f2fe',
          tertiary: '#e5e7eb',
          header: '#ffffff',
          sidebar: '#e0f2fe',
          modal: '#f0f9ff',
          input: '#ffffff'
        },
        text: {
          primary: '#0f172a',
          secondary: '#1e293b',
          tertiary: '#475569',
          placeholder: '#64748b',
          accent: '#0ea5e9'
        },
        border: {
          primary: '#94a3b8',
          secondary: '#cbd5e1',
          focus: '#0ea5e9',
          hover: '#94a3b8'
        },
        buttons: {
          extract: '#0ea5e9',
          reconstruct: '#10b981',
          verify: '#f59e0b',
          dangerous: '#ef4444',
          warning: '#f5920b',
          success: '#10b981',
          neutral: '#64748b'
        },
        accent: {
          primary: '#0ea5e9',
          secondary: '#38bdf8',
          highlight: '#10b981',
          success: '#10b981',
          warning: '#f5920b',
          danger: '#ef4444'
        },
        states: {
          hover: '#e0f2fe',
          active: '#bae6fd',
          disabled: '#94a3b8',
          selected: '#0ea5e9'
        }
      }
    },
    {
      id: 'nature',
      name: '🌿 Nature',
      description: 'Fraîcheur et tranquillité comme une forêt',
      naturalMode: 'light',
      colors: {
        background: {
          primary: '#f0fdf4',
          secondary: '#dcfce7',
          tertiary: '#f1f5f9',
          header: '#ffffff',
          sidebar: '#dcfce7',
          modal: '#f0fdf4',
          input: '#ffffff'
        },
        text: {
          primary: '#14532d',
          secondary: '#374151',
          tertiary: '#64748b',
          placeholder: '#6b7280',
          accent: '#059669'
        },
        border: {
          primary: '#d1d5db',
          secondary: '#e5e7eb',
          focus: '#059669',
          hover: '#d1d5db'
        },
        buttons: {
          extract: '#059669',
          reconstruct: '#0891b2',
          verify: '#d97706',
          dangerous: '#dc2626',
          warning: '#f59e0b',
          success: '#059669',
          neutral: '#6b7280'
        },
        accent: {
          primary: '#059669',
          secondary: '#22c55e',
          highlight: '#0891b2',
          success: '#059669',
          warning: '#f59e0b',
          danger: '#dc2626'
        },
        states: {
          hover: '#dcfce7',
          active: '#bbf7d0',
          disabled: '#d1d5db',
          selected: '#059669'
        }
      }
    },
    {
      id: 'fire',
      name: '🔥 Feu',
      description: 'Passion et énergie comme une flamme vive',
      naturalMode: 'dark',
      colors: {
        background: {
          primary: '#1f2937',
          secondary: '#374151',
          tertiary: '#4b5563',
          header: '#1f2937',
          sidebar: '#374151',
          modal: '#374151',
          input: '#4b5563'
        },
        text: {
          primary: '#fef2f2',
          secondary: '#fca5a5',
          tertiary: '#f87171',
          placeholder: '#ef4444',
          accent: '#f97316'
        },
        border: {
          primary: '#6b7280',
          secondary: '#9ca3af',
          focus: '#f97316',
          hover: '#fca5a5'
        },
        buttons: {
          extract: '#ef4444',
          reconstruct: '#f97316',
          verify: '#eab308',
          dangerous: '#ef4444',
          warning: '#f59e0b',
          success: '#22c55e',
          neutral: '#9ca3af'
        },
        accent: {
          primary: '#f97316',
          secondary: '#fb923c',
          highlight: '#ea580c',
          success: '#22c55e',
          warning: '#f59e0b',
          danger: '#ef4444'
        },
        states: {
          hover: '#4b5563',
          active: '#6b7280',
          disabled: '#9ca3af',
          selected: '#f97316'
        }
      }
    },
    {
      id: 'classic_blue',
      name: '💙 Bleu Classique',
      description: 'Professionnel et moderne comme un ciel clair',
      naturalMode: 'light',
      colors: {
        background: {
          primary: '#ffffff',
          secondary: '#f8fafc',
          tertiary: '#f1f5f9',
          header: '#ffffff',
          sidebar: '#f8fafc',
          modal: '#ffffff',
          input: '#ffffff'
        },
        text: {
          primary: '#1e293b',
          secondary: '#475569',
          tertiary: '#64748b',
          placeholder: '#94a3b8',
          accent: '#3b82f6'
        },
        border: {
          primary: '#e2e8f0',
          secondary: '#cbd5e1',
          focus: '#3b82f6',
          hover: '#94a3b8'
        },
        buttons: {
          extract: '#3b82f6',
          reconstruct: '#059669',
          verify: '#d97706',
          dangerous: '#ef4444',
          warning: '#f59e0b',
          success: '#059669',
          neutral: '#64748b'
        },
        accent: {
          primary: '#3b82f6',
          secondary: '#60a5fa',
          highlight: '#1d4ed8',
          success: '#059669',
          warning: '#f59e0b',
          danger: '#ef4444'
        },
        states: {
          hover: '#f1f5f9',
          active: '#e2e8f0',
          disabled: '#cbd5e1',
          selected: '#3b82f6'
        }
      }
    }
  ];

  function applyPresetTheme(theme: any) {
    config.colors = { ...theme.colors };
    
    // Appliquer immédiatement aux CSS variables
    updateCSSVariables(theme.colors);
    
    dispatcher('themeUpdate', {
      path: 'preset',
      value: theme.id,
      colors: config.colors
    });
    const modeInfo = theme.naturalMode === 'dark' ? '🎨 Mode naturellement sombre' : '☀️ Mode naturellement clair';
    alert(`✅ Thème "${theme.name}" appliqué avec succès !\n\n${modeInfo}\n💡 Utilisez le bouton toggle dans le header pour ajuster si nécessaire.`);
  }

  function updateCSSVariables(colors: any) {
    if (typeof document === 'undefined') return;
    
    const root = document.documentElement;
    
    // Mettre à jour les CSS variables principales
    root.style.setProperty('--bg-primary', colors.background.primary);
    root.style.setProperty('--bg-secondary', colors.background.secondary);
    root.style.setProperty('--bg-tertiary', colors.background.tertiary);
    root.style.setProperty('--text-primary', colors.text.primary);
    root.style.setProperty('--text-secondary', colors.text.secondary);
    root.style.setProperty('--border-color', colors.border.primary);
    root.style.setProperty('--accent-color', colors.accent.primary);
    root.style.setProperty('--button-bg-active', colors.buttons.extract);
    
    // Variables spécifiques
    root.style.setProperty('--header-bg', colors.background.header);
    root.style.setProperty('--sidebar-bg', colors.background.sidebar);
    
    console.log('🎨 CSS variables updated:', colors);
  }

  // Sections configurables
  const sections = [
    {
      key: 'background',
      title: '🎨 Arrière-plans',
      icon: '🖼️',
      items: [
        { key: 'primary', label: 'Arrière-plan principal', desc: 'Fond général de l\'application' },
        { key: 'secondary', label: 'Arrière-plan secondaire', desc: 'Cartes et éléments en relief' },
        { key: 'tertiary', label: 'Arrière-plan tertiaire', desc: 'Sections et zones spéciales' },
        { key: 'header', label: 'Header', desc: 'Bandeau supérieur de l\'application' },
        { key: 'sidebar', label: 'Sidebar', desc: 'Barre latérale de navigation' },
        { key: 'modal', label: 'Modales', desc: 'Fenêtres popup et dialogues' },
        { key: 'input', label: 'Champs de saisie', desc: 'Boîtes de texte et inputs' }
      ]
    },
    {
      key: 'text',
      title: '📝 Textes',
      icon: '📄',
      items: [
        { key: 'primary', label: 'Texte principal', desc: 'Texte normal et titres' },
        { key: 'secondary', label: 'Texte secondaire', desc: 'Sous-titres et texte moins important' },
        { key: 'tertiary', label: 'Texte tertiaire', desc: 'Texte discret et annotations' },
        { key: 'placeholder', label: 'Placeholder', desc: 'Texte d\'indication dans les champs' },
        { key: 'accent', label: 'Texte accent', desc: 'Liens et texte en surbrillance' }
      ]
    },
    {
      key: 'border',
      title: '🔲 Bordures',
      icon: '📐',
      items: [
        { key: 'primary', label: 'Bordure principale', desc: 'Bordures standard des éléments' },
        { key: 'secondary', label: 'Bordure secondaire', desc: 'Bordures des éléments moins importants' },
        { key: 'focus', label: 'Bordure focus', desc: 'Bordures lors de la sélection' },
        { key: 'hover', label: 'Bordure hover', desc: 'Bordures au survol' }
      ]
    },
    {
      key: 'buttons',
      title: '🔘 Boutons',
      icon: '🎯',
      items: [
        { key: 'extract', label: 'Bouton Extraire', desc: 'Bouton principal d\'extraction' },
        { key: 'reconstruct', label: 'Bouton Reconstruire', desc: 'Bouton de reconstruction' },
        { key: 'verify', label: 'Bouton Vérifier', desc: 'Bouton de vérification' },
        { key: 'dangerous', label: 'Actions dangereuses', desc: 'Boutons de suppression/reset' },
        { key: 'warning', label: 'Actions d\'avertissement', desc: 'Boutons d\'avertissement' },
        { key: 'success', label: 'Actions de succès', desc: 'Boutons de confirmation' },
        { key: 'neutral', label: 'Actions neutres', desc: 'Boutons secondaires' }
      ]
    },
    {
      key: 'accent',
      title: '✨ Accents',
      icon: '🌟',
      items: [
        { key: 'primary', label: 'Accent principal', desc: 'Couleur principale d\'accentuation' },
        { key: 'secondary', label: 'Accent secondaire', desc: 'Deuxième couleur d\'accent' },
        { key: 'highlight', label: 'Surlignage', desc: 'Éléments mis en valeur' },
        { key: 'success', label: 'Succès', desc: 'États de réussite' },
        { key: 'warning', label: 'Avertissement', desc: 'États d\'avertissement' },
        { key: 'danger', label: 'Danger', desc: 'États d\'erreur' }
      ]
    },
    {
      key: 'states',
      title: '⚡ États',
      icon: '🔄',
      items: [
        { key: 'hover', label: 'Survol', desc: 'État au survol de la souris' },
        { key: 'active', label: 'Actif', desc: 'État quand élément est sélectionné' },
        { key: 'disabled', label: 'Désactivé', desc: 'État quand élément est désactivé' },
        { key: 'selected', label: 'Sélectionné', desc: 'État d\'élément sélectionné' }
      ]
    }
  ];
</script>

<div class="space-y-6">
  <!-- En-tête avec actions globales -->
  <div class="bg-gray-800 rounded-lg p-6 border border-gray-700">
    <div class="flex items-center justify-between mb-4">
      <div>
        <h3 class="text-xl font-semibold text-white mb-2">🧙‍♂️ Personnalisation des Thèmes</h3>
        <p class="text-gray-400">Personnalisez chaque aspect visuel de votre interface RenExtract.</p>
      </div>
      <div class="flex gap-2">
        <button 
          class="px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm transition-colors"
          onclick={() => copyTheme()}
        >
          📋 Copier thème
        </button>
        <button 
          class="px-3 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded text-sm transition-colors"
          onclick={() => pasteTheme()}
        >
          📌 Coller thème
        </button>
      </div>
  </div>

  <!-- Thèmes prédéfinis -->
  <div class="bg-gray-800 rounded-lg p-6 border border-gray-700">
    <div class="mb-6">
      <h3 class="text-xl font-semibold text-white mb-2">🎨 Thèmes Prédéfinis</h3>
      <p class="text-gray-400">Choisissez un thème parmi nos créations pour un changement rapide et élégant.</p>
    </div>
    
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {#each presetThemes as theme}
        <div 
          class="bg-gray-700 rounded-lg p-4 border border-gray-600 hover:border-blue-400 transition-colors cursor-pointer group" 
          onclick={() => applyPresetTheme(theme)}
          onkeydown={(e) => e.key === 'Enter' || e.key === ' ' ? applyPresetTheme(theme) : null}
          role="button"
          tabindex="0"
          aria-label="Appliquer le thème {theme.name}"
        >
          <div class="flex items-start gap-3">
            <div class="text-3xl">{theme.name.split(' ')[0]}</div>
            <div class="flex-1">
                <h4 class="text-lg font-semibold text-white group-hover:text-blue-300 transition-colors">{theme.name}</h4>
                <p class="text-sm text-gray-400 mb-2">{theme.description}</p>
                <p class="text-xs text-blue-400 mb-3">
                  {theme.naturalMode === 'dark' ? '🌙 Mode naturellement sombre' : '☀️ Mode naturellement clair'}
                </p>
              
              <!-- Aperçu miniature des couleurs -->
              <div class="flex gap-1 mb-3">
                <div class="w-6 h-6 rounded-full border border-gray-600" style="background-color: {theme.colors.background.primary}"></div>
                <div class="w-6 h-6 rounded-full border border-gray-600" style="background-color: {theme.colors.buttons.extract}"></div>
                <div class="w-6 h-6 rounded-full border border-gray-600" style="background-color: {theme.colors.buttons.reconstruct}"></div>
                <div class="w-6 h-6 rounded-full border border-gray-600" style="background-color: {theme.colors.accent.primary}"></div>
              </div>
              
              <button class="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm transition-colors">
                ✨ Appliquer ce thème
              </button>
            </div>
          </div>
        </div>
      {/each}
    </div>
    
    <div class="mt-4 p-3 bg-gray-700 rounded-lg border border-gray-600">
      <p class="text-sm text-gray-400 text-center">
        💡 <strong>Astuce:</strong> Vous pouvez personnaliser ces thèmes après les avoir appliqués via les options détaillées ci-dessous.
      </p>
    </div>
  </div>

  {#if showPreview}
      <div class="mt-4 p-4 bg-gray-700 rounded border">
        <h4 class="text-white font-medium mb-3">👁️ Aperçu en temps réel</h4>
        <p class="text-sm text-gray-400 mb-4">Cet aperçu utilise les couleurs directement appliquées à l'application.</p>
        <div class="grid grid-cols-3 gap-4">
          <div class="text-center">
            <div 
              class="h-16 rounded border mb-2"
              style="background-color: var(--bg-primary); border-color: var(--border-color); color: var(--text-primary);"
            >
              <div class="flex items-center justify-center h-full text-sm font-medium">
                Interface
              </div>
            </div>
            <p class="text-xs text-gray-400">Arrière-plan principal</p>
            <p class="text-xs text-gray-500">{getCurrentPath('background.primary')}</p>
          </div>
          <div class="text-center">
            <div 
              class="h-16 rounded border mb-2 flex items-center justify-center"
              style="background-color: var(--button-bg-active, #3b82f6); color: white; border-color: var(--border-color);"
            >
              <span class="text-sm font-medium">Extrait</span>
            </div>
            <p class="text-xs text-gray-400">Bouton Extract</p>
            <p class="text-xs text-gray-500">{getCurrentPath('buttons.extract')}</p>
          </div>
          <div class="text-center">
            <div 
              class="h-16 rounded border mb-2 flex items-center justify-center"
              style="background-color: var(--bg-primary); border-color: var(--border-color); color: var(--text-primary);"
            >
              <span class="text-sm">Header/Sidebar</span>
            </div>
            <p class="text-xs text-gray-400">Eléments navigation</p>
            <p class="text-xs text-gray-500">Header: {getCurrentPath('background.header')}</p>
          </div>
        </div>
      </div>
    {/if}
  </div>

  <!-- Sections configurables avec grille responsive -->
  <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
    {#each sections as section}
      <div class="bg-gray-800 rounded-lg border border-gray-700 overflow-hidden hover:shadow-xl transition-all duration-300 {expandedSections[section.key] ? 'xl:col-span-3 md:col-span-2' : ''} {expandedSections[section.key] ? 'active-section' : ''}">
        <div class="p-4 flex items-center justify-between hover:bg-gray-700 transition-colors">
          <button 
            class="flex items-center gap-3 text-left flex-1"
            onclick={() => toggleSection(section.key)}
          >
            <span class="text-xl">{section.icon}</span>
            <div>
              <h3 class="text-lg font-semibold text-white">{section.title}</h3>
              <p class="text-sm text-gray-400">Configurer les {section.title.toLowerCase()}</p>
            </div>
          </button>
          <div class="flex items-center gap-2">
            <button 
              class="px-3 py-1 bg-gray-600 hover:bg-gray-500 text-white rounded text-xs transition-colors"
              onclick={() => resetSection(section.key)}
            >
              🔄 Reset
            </button>
            <span class="text-gray-400 transform transition-transform duration-200">
              {expandedSections[section.key] ? '▼' : '▶'}
            </span>
          </div>
        </div>

        {#if expandedSections[section.key]}
          <div class="p-4 bg-gray-750 border-t border-gray-700 animate-fadeIn">
            <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
              {#each section.items as item}
                <div class="space-y-2">
                  <label for="{section.key}-{item.key}-color" class="block">
                    <span class="text-sm font-medium text-white">{item.label}</span>
                    <p class="text-xs text-gray-500">{item.desc}</p>
                  </label>
                  <div class="flex items-center gap-2">
                    <input
                      id="{section.key}-{item.key}-color"
                      type="color"
                      value={getCurrentPath(`${section.key}.${item.key}`)}
                      onchange={(e) => updateColor(`${section.key}.${item.key}`, e.target.value)}
                      class="w-10 h-8 rounded border border-gray-600 cursor-pointer hover:scale-110 transition-transform"
                    />
                    <input
                      id="{section.key}-{item.key}-text"
                      type="text"
                      value={getCurrentPath(`${section.key}.${item.key}`)}
                      onchange={(e) => updateColor(`${section.key}.${item.key}`, e.target.value)}
                      placeholder="#ffffff"
                      class="flex-1 px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white text-sm hover:border-blue-400 transition-colors"
                    />
                    <button
                      class="px-2 py-2 bg-gray-600 hover:bg-gray-500 text-white rounded text-xs transition-colors"
                      onclick={() => copyCurrentColor(`${section.key}.${item.key}`)}
                      title="Copier la couleur"
                    >
                      📋
                    </button>
                  </div>
                </div>
              {/each}
            </div>
          </div>
        {/if}
      </div>
    {/each}
  </div>
</div>

<style>
  .animate-fadeIn {
    animation: fadeIn 0.3s ease-in-out;
  }

  @keyframes fadeIn {
    from {
      opacity: 0;
      transform: translateY(-10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  /* Transition fluide pour le changement de colonne */
  .transition-col-span {
    transition: all 0.3s ease-in-out;
  }

  /* Animation pour la réduction des autres sections */
  .section-close-animation {
    animation: fadeOutScale 0.2s ease-out forwards;
  }

  @keyframes fadeOutScale {
    to {
      opacity: 0.8;
      transform: scale(0.98);
    }
  }

  /* Effet de focus sur la section active */
  .active-section {
    box-shadow: 0 0 20px rgba(96, 165, 250, 0.3);
    border-color: rgba(96, 165, 250, 0.5);
  }

  /* Transition douce pour le redimensionnement */
  .transition-all {
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }
</style>
