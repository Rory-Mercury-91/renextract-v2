<script lang="ts">
  import Icon from '@iconify/svelte';

</script>

<section class="min-h-full flex flex-col text-white">
  <div class="border-b border-gray-700 bg-gray-900">
    <div class="p-6 flex items-center justify-between">
      <div>
        <h1 class="text-3xl font-bold text-yellow-300 mb-2 flex gap-3 items-center">
          <Icon icon="hugeicons:magic-wand-04" class="w-8 h-8 text-yellow-300" />
          Générateur
        </h1>
        <p class="text-yellow-200 text-sm">
          Générez des fichiers TL à partir de vos fichiers RPA/RPYC
        </p>
      </div>
    </div>
  </div>
  
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
</section>
