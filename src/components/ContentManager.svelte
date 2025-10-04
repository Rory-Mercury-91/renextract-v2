<script lang="ts">
  import Backup from '../routes/Backups.svelte';
  import { appState } from '../stores/app';
  import ActionButtons from './ActionButtons.svelte';
  import MainEditor from './MainEditor.svelte';
  import Settings from './Settings.svelte';
  import WorkFolders from './WorkFolders.svelte';

  let currentSection = 'settings';
  
  $: currentSection = $appState.currentSection;
</script>

<div class="flex-1 flex flex-col bg-gray-900">
  {#if currentSection === 'settings'}
    <Settings />
  {:else if currentSection === 'renextract'}
    <div class="flex flex-col h-full">
      <MainEditor />
      <div class="flex flex-col">
        <ActionButtons />
        <WorkFolders />
      </div>
    </div>
  {:else if currentSection === 'generator'}
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
  {:else if currentSection === 'tools'}
    <div class="p-6">
      <h2 class="text-2xl font-bold mb-4">🔧 Outils spécialisés</h2>
      <div class="bg-gray-800 rounded-xl p-6 border border-gray-700">
        <p class="text-gray-300">Module tools en cours de développement...</p>
        <div class="mt-6">
          <h3 class="text-lg font-semibold mb-3">Architecture prévue :</h3>
          <ul class="space-y-2 text-gray-400">
            <li>🧹 Nettoyage intelligent</li>
            <li>🔍 Contrôle de cohérence</li>
            <li>⚡ Éditeur en temps réel</li>
          </ul>
        </div>
      </div>
    </div>
  {:else if currentSection === 'backup'}
    <Backup />
  {:else}
    <!-- Fallback -->
    <div class="p-6">
      <h2 class="text-2xl font-bold mb-4">📋 Section non trouvée</h2>
      <div class="bg-gray-800 rounded-xl p-6 border border-gray-700">
        <p class="text-gray-300">Cette section n'est pas encore implémentée : {currentSection}</p>
      </div>
    </div>
  {/if}
</div>
