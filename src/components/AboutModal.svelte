<script lang="ts">
  import packageJson from '../../package.json' assert { type: 'json' };

  let { showAboutModal = $bindable() } = $props();
</script>

<div
  class="fixed inset-0 z-50 flex items-center justify-center bg-black/80 bg-opacity-50"
>
  <div
    class="shadow-xl² mx-4 w-full max-w-md rounded-lg border border-gray-600 bg-gray-800 p-6"
  >
    <div class="text-center">
      <div
        class="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-lg bg-blue-600 text-2xl font-bold text-white"
      >
        RE
      </div>
      <h2 class="mb-4 text-xl font-bold text-white">
        RenExtract v2.0 - WebView Interface
      </h2>
      <p class="mb-6 text-gray-400">
        Outils de traduction avancé pour scripts Ren'Py
      </p>

      <div class="space-y-2 text-left text-sm text-gray-300">
        <p><strong>Version :</strong> v{packageJson.version}</p>
        <p><strong>Développement :</strong> RoryMercury91 et Hunteraulo</p>
        <p>
          <strong>Technologies :</strong> Svelte 5 + Python Flask + PyWebView
        </p>
      </div>

      <p class="mt-6 text-xs text-gray-400">© 2025 RenExtract Project</p>

      <button
        class="mt-6 rounded-lg bg-blue-600 px-6 py-2 font-medium text-white transition-colors hover:bg-blue-700"
        onclick={() => (showAboutModal = false)}
      >
        OK
      </button>
    </div>
  </div>
</div>
