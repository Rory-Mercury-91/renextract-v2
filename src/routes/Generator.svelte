<script lang="ts">
  import { appState } from '../stores/app';

  let currentSection = 'settings';
  
  $: currentSection = $appState.currentSection;
</script>

<div class="flex-1 flex flex-col bg-gray-900">
  <div class="p-6">
    <h2 class="text-2xl font-bold mb-4">⚡ Générateur</h2>
    <div class="bg-gray-800 rounded-xl p-6 border border-gray-700">
      <p class="text-gray-300">Module generator en cours de développement...</p>
      <div class="mt-6">
        <h3 class="text-lg font-semibold mb-3">Architecture prévue :</h3>
        <ul class="space-y-2 text-gray-400">
          <li>🔍 Extraction Rpa/Rpyc</li>
          <li>🌐 Génération TL</li>
          <li>📤 Extraction +</li>
          <li>🔀 Combinaison / Division</li>
          <li>📦 Compilation Rpa</li>
        </ul>
      </div>
    </div>
  </div>
</div>
