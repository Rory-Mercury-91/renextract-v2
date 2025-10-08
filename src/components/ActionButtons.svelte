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

<div class="flex justify-center gap-4">
  <button
    onclick={handleExtract}
    class="flex items-center gap-2 rounded-lg bg-orange-600 px-6 py-3 font-medium text-white transition-colors hover:bg-orange-700"
  >
    <Icon icon="hugeicons:folder-details-reference" class="h-6 w-6" />
    Extraire
  </button>

  <button
    onclick={handleReconstruct}
    class="flex items-center gap-2 rounded-lg bg-green-600 px-6 py-3 font-medium text-white transition-colors hover:bg-green-700"
  >
    <Icon icon="hugeicons:delivery-return-02" class="h-6 w-6" />
    Reconstruire
  </button>

  <button
    onclick={handleVerify}
    class="flex items-center gap-2 rounded-lg bg-orange-500 px-6 py-3 font-medium text-white transition-colors hover:bg-orange-600"
  >
    <Icon icon="hugeicons:folder-view" class="h-6 w-6" />
    Revérifier
  </button>
</div>
