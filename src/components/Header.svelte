<script lang="ts">
  import packageJson from '../../package.json' assert { type: 'json' };

  let currentProject = 'Aucun projet chargé';
</script>

<header class="bg-gray-800 text-white p-4 flex items-center justify-between border-b border-gray-700 gap-4">
  <div class="flex items-center gap-2">
    <div class="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center font-bold text-sm">
      <img src="/public/assets/logo.webp" alt="logo"  >
    </div>
    <div>
      <h1 class="text-lg font-bold">RenExtract</h1>
      <p class="text-xs text-gray-400">v{packageJson.version} WebView</p>
    </div>
  </div>

  <div>
    <span class="text-yellow-500">📁</span>
    <input type="text" class="bg-gray-700 border border-gray-600 rounded px-2 py-1 text-sm w-80" value={currentProject}>
    <button class="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded text-sm font-medium transition-colors">
      Parcourir
    </button>
  </div>
  
  <div class="flex items-center gap-2">
    <button class="text-gray-400 hover:text-white transition-colors">Aide</button>
    <button class="text-gray-400 hover:text-white transition-colors">Thème</button>
    <select class="bg-gray-700 border border-gray-600 rounded px-2 py-1 text-sm">
      <option>FR Français</option>
      <option>EN English</option>
    </select>
  </div>
</header>
