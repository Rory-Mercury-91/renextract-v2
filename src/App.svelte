<script lang="ts">
  import Header from '$components/Header.svelte';
  import Sidebar from '$components/Sidebar.svelte';
  import { apiService } from '$lib/api';
  import Backups from '$routes/Backups.svelte';
  import Extractor from '$routes/Extractor.svelte';
  import Generator from '$routes/Generator.svelte';
  import NotFound from '$routes/NotFound.svelte';
  import Settings from '$routes/Settings.svelte';
  import Tools from '$routes/Tools.svelte';
  import { onMount } from 'svelte';
  import { _, waitLocale } from 'svelte-i18n';
  import { Route, Router } from 'svelte5-router';

  let isLoading = $state(true);
  let error: string | null = $state(null);

  let url = $state(window.location.pathname);

  onMount(async () => {
    try {
      // Check API connection
      await apiService.healthCheck();
      await waitLocale();
      isLoading = false;
    } catch (err) {
      error = 'Unable to connect to Python backend';
      isLoading = true;
    }
  });
</script>

<Router {url}>
  {#if isLoading}
    <div class="flex-1 flex flex-col items-center justify-center gap-5">
      <div
        class="w-10 h-10 border-4 border-gray-600 border-t-blue-500 rounded-full animate-spin"
      ></div>
      <p class="text-gray-400">
        {$_('app.loading') || 'Loading application...'}
      </p>
    </div>
  {:else if error}
    <div class="flex-1 flex items-center justify-center">
      <div
        class="text-center p-10 bg-red-900 border border-red-700 rounded-lg text-red-300 max-w-md"
      >
        <h2 class="text-xl font-semibold mb-2">
          {$_('app.connection_error') || 'Connection error'}
        </h2>
        <p class="mb-4">{error}</p>
        <button
          class="px-5 py-2.5 bg-red-600 text-white border-0 rounded cursor-pointer hover:bg-red-700 transition-colors"
          onclick={() => window.location.reload()}
        >
          {$_('app.retry') || 'Retry'}
        </button>
      </div>
    </div>
  {:else}
    <div class="h-screen max-h-screen flex flex-col relative">
      <Header />

      <div class="flex h-full relative">
        <Sidebar />

        <Route path="/" component={Generator} />
        <Route path="/extract" component={Extractor} />
        <Route path="/tools" component={Tools} />
        <Route path="/backups" component={Backups} />
        <Route path="/settings" component={Settings} />
        <Route path="*" component={NotFound} />
      </div>
    </div>
  {/if}
</Router>
