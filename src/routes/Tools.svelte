<script lang="ts">
  import CoherenceChecker from '$components/CoherenceChecker.svelte';
  import RouteHeader from '$components/RouteHeader.svelte';
  import { _ } from 'svelte-i18n';
</script>

<section class="flex min-h-full flex-col text-gray-900 dark:text-white">
  <RouteHeader
    title={$_('navigation.tools')}
    description={$_('navigation.tools_description')}
    icon="hugeicons:tools"
    color="text-green-300"
  />
  
  <!-- Contenu principal -->
  <div class="flex-1 bg-gray-900 p-6">
    <div class="max-w-7xl mx-auto">
      <CoherenceChecker />
    </div>
  </div>
</section>
