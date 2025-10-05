<script lang="ts">
  import RouteHeader from '$components/RouteHeader.svelte';

</script>

<section class="min-h-full flex flex-col text-white">
  <RouteHeader title="Générateur" description="Générez des fichiers TL à partir de vos fichiers RPA/RPYC" icon="hugeicons:magic-wand-04" color="yellow" />
  
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
