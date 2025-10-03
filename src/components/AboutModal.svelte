<script lang="ts">
  import packageJson from '../../package.json' assert { type: 'json' };

  let { showAboutModal = $bindable() } = $props()

</script>

<div class="fixed inset-0 bg-black/80 bg-opacity-50 flex items-center justify-center z-50">
  <div class="bg-gray-800 border border-gray-600 rounded-lg p-6 max-w-md w-full mx-4 shadow-xl²">
    <div class="text-center">
        <div class="w-16 h-16 bg-blue-600 rounded-lg flex items-center justify-center text-white font-bold text-2xl mx-auto mb-4">
          RE
        </div>
        <h2 class="text-xl font-bold mb-4 text-white">RenExtract v2.0 - WebView Interface</h2>
        <p class="text-gray-400 mb-6">Outils de traduction avancé pour scripts Ren'Py</p>
        
        <div class="text-left space-y-2 text-sm text-gray-300">
          <p><strong>Version :</strong> v{packageJson.version}</p>
          <p><strong>Développement :</strong> RoryMercury91 et Hunteraulo</p>
          <p><strong>Technologies :</strong> Svelte 5 + Python Flask + PyWebView</p>
        </div>
        
        <p class="text-xs text-gray-400 mt-6">© 2025 RenExtract Project</p>
        
        <button 
          class="mt-6 px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium"
          onclick={() => showAboutModal = false}
        >
          OK
        </button>
      </div>
  </div>
</div>
