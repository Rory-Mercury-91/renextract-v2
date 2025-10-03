<script lang="ts">
  import Icon from '@iconify/svelte';

  function handleExtract() {
    console.info('Extraire clicked');
  }

  function handleReconstruct() {
    console.info('Reconstruire clicked');
  }

  function handleVerify() {
    console.info('Revérifier clicked');
  }
</script>

<div class="bg-gray-800 p-6">
  <h3 class="text-blue-400 text-lg font-semibold mb-4">Actions principales</h3>
  
  <div class="flex gap-4 mb-6 justify-center">
    <button
      onclick={handleExtract}
      class="flex items-center gap-2 bg-orange-600 hover:bg-orange-700 text-white px-6 py-3 rounded-lg font-medium transition-colors"
    >
      <Icon icon="hugeicons:zap" class="w-6 h-6" />
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
      <Icon icon="hugeicons:check-list" class="w-6 h-6" />
      Revérifier
    </button>
  </div>
</div>
