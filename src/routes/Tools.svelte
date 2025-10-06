<script lang="ts">
  import RouteHeader from '$components/RouteHeader.svelte';
  import { _ } from 'svelte-i18n';
</script>

<section class="min-h-full flex flex-col text-white">
  <RouteHeader
    title={$_('navigation.tools')}
    description={$_('navigation.tools_description')}
    icon="hugeicons:tools"
    color="green"
  />
</section>
