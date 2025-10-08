<script lang="ts">
  import RouteHeader from '$components/RouteHeader.svelte';
  import { _ } from 'svelte-i18n';
</script>

<section class="flex min-h-full flex-col text-white">
  <RouteHeader
    title={$_('navigation.generator')}
    description={$_('navigation.generator_description')}
    icon="hugeicons:magic-wand-04"
    color="text-yellow-300"
  />

  <div class="p-6">
    <h2 class="mb-4 text-2xl font-bold">⚡ Générateur</h2>
    <div class="rounded-xl border border-gray-700 bg-gray-800 p-6">
      <p class="text-gray-300">Module generator en cours de développement...</p>
      <div class="mt-6">
        <h3 class="mb-3 text-lg font-semibold">Architecture prévue :</h3>
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
