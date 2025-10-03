<script lang="ts">
  import packageJson from '../../package.json' assert { type: 'json' };
  import { i18n } from '../lib/i18n';
  import { appActions, appState } from '../stores/app';

  let currentProject = 'Aucun projet chargé';

  // Initialize theme on mount
  $: {
    if (typeof document !== 'undefined') {
      document.documentElement.classList.toggle('dark-mode', $appState.currentTheme === 'dark');
    }
  }

  function updateLanguage(event: Event) {
    const target = event.target as HTMLSelectElement;
    const lang = target.value as 'fr' | 'en' | 'de';
    appActions.setLanguage(lang);
  }

  // Fonction pour déterminer si un thème est naturellement clair ou sombre
  function isThemeNaturallyDark(backgroundColor: string): boolean {
    // Convertir hex en RGB pour calculer la luminosité
    const hex = backgroundColor.replace('#', '');
    const r = parseInt(hex.substr(0, 2), 16);
    const g = parseInt(hex.substr(2, 2), 16);
    const b = parseInt(hex.substr(4, 2), 16);
    
    // Calcul de luminance (0-1)
    const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
    return luminance < 0.4; // Si < 0.4, considéré comme sombre
  }

  function toggleTheme() {
    const currentTheme = $appState.currentTheme;
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    appActions.setTheme(newTheme as 'light' | 'dark');
    
    // DOM update
    document.documentElement.classList.toggle('dark-mode', newTheme === 'dark');
    document.documentElement.style.colorScheme = newTheme === 'dark' ? 'dark' : 'light';
  }

  function quitApplication() {
    if (confirm('Êtes-vous sûr de vouloir quitter RenExtract ?')) {
      window.close ? window.close() : location.reload();
    }
  }

  function showHelp() {
    alert('Aide RenExtract - Fonctionnalités en cours de développement');
  }

  function showAbout() {
    // Créer une modale personnalisée adaptée au thème
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
    
    const dialogBox = document.createElement('div');
    dialogBox.className = `bg-gray-800 border border-gray-600 rounded-lg p-6 max-w-md w-full mx-4 shadow-xl ${
      $appState.currentTheme === 'dark' ? 'bg-gray-800 text-white' : 'bg-white text-gray-900'
    }`;
    
    dialogBox.innerHTML = `
      <div class="text-center">
        <div class="w-16 h-16 bg-blue-600 rounded-lg flex items-center justify-center text-white font-bold text-2xl mx-auto mb-4">
          RE
        </div>
        <h2 class="text-xl font-bold mb-4 ${$appState.currentTheme === 'dark' ? 'text-white' : 'text-gray-900'}">RenExtract v2.0 - WebView Interface</h2>
        <p class="text-gray-400 mb-6">Outils de traduction avancé pour scripts Ren'Py</p>
        
        <div class="text-left space-y-2 text-sm ${$appState.currentTheme === 'dark' ? 'text-gray-300' : 'text-gray-600'}">
          <p><strong>Version :</strong> ${packageJson.version}</p>
          <p><strong>Développement :</strong> [Votre nom]</p>
          <p><strong>Technologies :</strong> Svelte 5 + Python Flask + PyWebView</p>
        </div>
        
        <p class="text-xs text-gray-400 mt-6">© 2025 RenExtract Project</p>
        
        <button 
          class="mt-6 px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium"
          onclick="this.closest('.fixed').remove()"
        >
          OK
        </button>
      </div>
    `;
    
    modal.appendChild(dialogBox);
    modal.addEventListener('click', (e) => {
      if (e.target === modal) modal.remove();
    });
    
    document.body.appendChild(modal);
  }

  $: currentTheme = $appState.currentTheme;
  $: currentLang = $appState.currentLanguage;
</script>

<header class="bg-gray-800 text-white p-4 flex items-center justify-between border-b border-gray-700 gap-4">
  <!-- Left: App Name + Version -->
  <div class="flex items-center gap-2">
    <div>
      <h1 class="text-lg font-bold">RenExtract</h1>
      <p class="text-xs text-gray-400">v{packageJson.version} WebView</p>
    </div>
  </div>

  <!-- Center: Project Bar -->
  <div class="flex items-center gap-2">
    <span class="text-yellow-500">📁</span>
    <span class="text-sm text-gray-300">{currentProject}</span>
    <button class="bg-blue-600 hover:bg-blue-700 px-3 py-1 rounded text-sm font-medium transition-colors">
      {i18n.t('app.browse')}
    </button>
  </div>

  <!-- Right: Controls -->
  <div class="flex items-center gap-4">
    <button 
      class="text-gray-400 hover:text-white transition-colors px-2 py-1"
      onclick={showHelp}
      title="Aide et documentation"
    >
      ℹ️ {i18n.t('app.help')}
    </button>

    <button 
      class="text-gray-400 hover:text-white transition-colors px-2 py-1"
      onclick={showAbout}
      title="Informations sur RenExtract"
    >
      ℹ️ À propos
    </button>

    <!-- Theme Toggle -->
    <button 
      class="text-gray-400 hover:text-white transition-colors px-2 py-1 flex items-center gap-1"
      onclick={toggleTheme}
    >
      {#if currentTheme === 'dark'}
        ☀️ Thème clair
      {:else}
        🌙 Thème sombre
      {/if}
    </button>

    <!-- Language Selector with Tooltip -->
    <div class="relative group">
      <select 
        class="unified-select"
        value={currentLang}
        onchange={updateLanguage}
        title="Changer la langue de l'interface"
      >
        <option value="fr">🇫🇷 {i18n.t('languages.fr')}</option>
        <option value="en">🇺🇸 {i18n.t('languages.en')}</option>
        <option value="de">🇩🇪 {i18n.t('languages.de')}</option>
      </select>
      
              <!-- Tooltip overlay -->
              <div class="absolute top-full left-1/2 transform -translate-x-1/2 mt-2 px-3 py-1 bg-gray-900 text-white text-xs rounded shadow-lg opacity-0 group-hover:opacity-100 transition-opacity duration-200 whitespace-nowrap">
                Changer la langue de l'interface
                <div class="absolute bottom-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-b-gray-900"></div>
              </div>
    </div>

    <!-- Quit Button -->
    <button 
      class="bg-red-600 hover:bg-red-700 px-3 py-1 rounded text-sm font-medium transition-colors"
      onclick={quitApplication}
    >
      ❌ Quitter
    </button>
  </div>
</header>
