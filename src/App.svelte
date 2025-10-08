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
  import Translator from '$routes/Translator.svelte';
  import { onMount } from 'svelte';
  import { _, waitLocale } from 'svelte-i18n';
  import { Route, Router } from 'svelte5-router';
  import { appSettings } from './stores/app';

  let isLoading = $state(true);
  let error: string | null = $state(null);

  const url = $state(window.location.pathname);

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
    <div class="flex flex-1 flex-col items-center justify-center gap-5">
      <div
        class="h-10 w-10 animate-spin rounded-full border-4 border-gray-600 border-t-blue-500"
      ></div>
      <p class="text-gray-400">
        {$_('app.loading') || 'Loading application...'}
      </p>
    </div>
  {:else if error}
    <div class="flex flex-1 items-center justify-center">
      <div
        class="max-w-md rounded-lg border border-red-700 bg-red-900 p-10 text-center text-red-300"
      >
        <h2 class="mb-2 text-xl font-semibold">
          {$_('app.connection_error') || 'Connection error'}
        </h2>
        <p class="mb-4">{error}</p>
        <button
          class="cursor-pointer rounded border-0 bg-red-600 px-5 py-2.5 text-white transition-colors hover:bg-red-700"
          onclick={() => window.location.reload()}
        >
          {$_('app.retry') || 'Retry'}
        </button>
      </div>
    </div>
  {:else}
    <div
      class="relative grid h-screen max-h-screen min-h-screen grid-rows-[5rem_1fr]"
    >
      <Header />

      <div class="relative flex h-[calc(100vh-5rem)]">
        <Sidebar />

        <div class="h-full max-h-full w-full overflow-y-auto">
          <Route path="/" component={Generator} />
          <Route path="/extract" component={Extractor} />
          {#if $appSettings.translatorFeature}
            <Route path="/translator" component={Translator} />
          {/if}
          <Route path="/tools" component={Tools} />
          <Route path="/backups" component={Backups} />
          <Route path="/settings" component={Settings} />
          <Route path="*" component={NotFound} />
        </div>
      </div>
    </div>
  {/if}
</Router>
