<script lang="ts">
  import { onMount } from 'svelte';
  import { waitLocale } from 'svelte-i18n';
  import ContentManager from './components/ContentManager.svelte';
  import Header from './components/Header.svelte';
  import Sidebar from './components/Sidebar.svelte';
  import { apiService } from './lib/api';

  let isLoading = true;
  let error: string | null = null;

  onMount(async () => {
    try {
      // Check API connection
      await apiService.healthCheck();
      await waitLocale()
      isLoading = false;
    } catch (err) {
      error = 'Unable to connect to Python backend';
      isLoading = false;
    }
  });
</script>

<div class="h-screen flex flex-col font-sans">
  <Header />
  
  {#if isLoading}
    <div class="flex-1 flex flex-col items-center justify-center gap-5">
      <div
        class="w-10 h-10 border-4 border-gray-600 border-t-blue-500 rounded-full animate-spin"
      ></div>
      <p class="text-gray-400">Loading application...</p>
    </div>
  {:else if error}
    <div class="flex-1 flex items-center justify-center">
      <div
        class="text-center p-10 bg-red-900 border border-red-700 rounded-lg text-red-300 max-w-md"
      >
        <h2 class="text-xl font-semibold mb-2">Connection Error</h2>
        <p class="mb-4">{error}</p>
        <button
          class="px-5 py-2.5 bg-red-600 text-white border-0 rounded cursor-pointer hover:bg-red-700 transition-colors"
          onclick={() => window.location.reload()}
        >
          Retry
        </button>
      </div>
    </div>
  {:else}
    <div class="flex-1 flex overflow-hidden">
      <Sidebar />
      <ContentManager />
    </div>
  {/if}
</div>
