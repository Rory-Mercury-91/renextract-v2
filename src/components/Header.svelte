<script lang="ts">
  import { _, locale, locales } from 'svelte-i18n';
  import packageJson from '../../package.json' assert { type: 'json' };

  let currentProject = 'Aucun projet chargé';

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
    dialogBox.className = `bg-gray-800 border border-gray-600 rounded-lg p-6 max-w-md w-full mx-4 shadow-xl`;
    
    dialogBox.innerHTML = `
      <div class="text-center">
        <div class="w-16 h-16 bg-blue-600 rounded-lg flex items-center justify-center text-white font-bold text-2xl mx-auto mb-4">
          RE
        </div>
        <h2 class="text-xl font-bold mb-4 text-white">RenExtract v2.0 - WebView Interface</h2>
        <p class="text-gray-400 mb-6">Outils de traduction avancé pour scripts Ren'Py</p>
        
        <div class="text-left space-y-2 text-sm text-gray-300">
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
      {$_('app.browse')}
    </button>
  </div>

  <!-- Right: Controls -->
  <div class="flex items-center gap-4">
    <button 
      class="text-gray-400 hover:text-white transition-colors px-2 py-1"
      onclick={showHelp}
      title="Aide et documentation"
    >
      ℹ️ {$_('app.help')}
    </button>

    <button 
      class="text-gray-400 hover:text-white transition-colors px-2 py-1"
      onclick={showAbout}
      title="Informations sur RenExtract"
    >
      ℹ️ À propos
    </button>

    <!-- Theme Toggle --> TODO: refactoring this
    <!-- <button 
      class="text-gray-400 hover:text-white transition-colors px-2 py-1 flex items-center gap-1"
      onclick={toggleTheme}
    >
      {#if currentTheme === 'dark'}
        ☀️ Thème clair
      {:else}
        🌙 Thème sombre
      {/if}
    </button> -->

    <!-- Language Selector with Tooltip -->
    <div class="relative group">
      <select bind:value={$locale}>
        {#each $locales as locale}
          <option value={locale}>{locale}</option>
        {/each}
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
