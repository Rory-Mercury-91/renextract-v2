<script lang="ts">
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
</section>
