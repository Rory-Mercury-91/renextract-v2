<script module lang="ts">
  export type ActiveTool = 'coherence' | null;
</script>

<script lang="ts">
  import CoherenceChecker from '$components/CoherenceChecker.svelte';
  import RouteHeader from '$components/RouteHeader.svelte';
  import { _ } from 'svelte-i18n';

  let active = $state<ActiveTool>(null);
</script>

<section class="flex min-h-full flex-col dark:text-white">
  <RouteHeader
    title={$_('navigation.tools')}
    description={$_('navigation.tools_description')}
    icon="hugeicons:tools"
    color="text-green-300"
  />

  <!-- Contenu principal -->
  <div class="flex-1 p-6">
    <div class="mx-auto max-w-7xl">
      <CoherenceChecker bind:active />
    </div>
  </div>
</section>
