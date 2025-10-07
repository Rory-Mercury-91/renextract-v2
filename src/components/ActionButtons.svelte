<script lang="ts">
  /* eslint-env browser */
  import Icon from '@iconify/svelte';

  function handleExtract() {
    // eslint-disable-next-line no-console
    console.info('Extraire clicked');
  }

  function handleReconstruct() {
    // eslint-disable-next-line no-console
    console.info('Reconstruire clicked');
  }

  function handleVerify() {
    // eslint-disable-next-line no-console
    console.info('Revérifier clicked');
  }
</script>

<div class="flex gap-4 justify-center">
  <button
    onclick={handleExtract}
    class="flex items-center gap-2 bg-orange-600 hover:bg-orange-700 text-white px-6 py-3 rounded-lg font-medium transition-colors"
  >
    <Icon icon="hugeicons:folder-details-reference" class="w-6 h-6" />
    Extraire
  </button>

  <button
    onclick={handleReconstruct}
    class="flex items-center gap-2 bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-lg font-medium transition-colors"
  >
    <Icon icon="hugeicons:delivery-return-02" class="w-6 h-6" />
    Reconstruire
  </button>

  <button
    onclick={handleVerify}
    class="flex items-center gap-2 bg-orange-500 hover:bg-orange-600 text-white px-6 py-3 rounded-lg font-medium transition-colors"
  >
    <Icon icon="hugeicons:folder-view" class="w-6 h-6" />
    Revérifier
  </button>
</div>
