<script lang="ts">
  function handleExtract() {
    console.log('Extraire clicked');
  }

  function handleReconstruct() {
    console.log('Reconstruire clicked');
  }

  function handleVerify() {
    console.log('Revérifier clicked');
  }
</script>

<div class="bg-gray-800 p-6">
  <h3 class="text-blue-400 text-lg font-semibold mb-4">Actions principales</h3>
  
  <div class="flex gap-4 mb-6">
    <button
      onclick={handleExtract}
      class="flex items-center gap-2 bg-orange-600 hover:bg-orange-700 text-white px-6 py-3 rounded-lg font-medium transition-colors"
    >
      <span>⚡</span>
      Extraire
    </button>

    <button
      onclick={handleReconstruct}
      class="flex items-center gap-2 bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-lg font-medium transition-colors"
    >
      <span>✅</span>
      Reconstruire
    </button>

    <button
      onclick={handleVerify}
      class="flex items-center gap-2 bg-orange-500 hover:bg-orange-600 text-white px-6 py-3 rounded-lg font-medium transition-colors"
    >
      <span>🔄</span>
      Revérifier
    </button>
  </div>
</div>
