<script lang="ts">
  import ActionButtons from '$components/ActionButtons.svelte';
  import MainEditor from '$components/MainEditor.svelte';
  import RouteHeader from '$components/RouteHeader.svelte';
  import WorkFolders from '$components/WorkFolders.svelte';
  import { _ } from 'svelte-i18n';
</script>

<section class="flex flex-col text-white">
  <RouteHeader
    title={$_('navigation.extract')}
    description={$_('navigation.extract_description')}
    icon="hugeicons:injection"
    color="text-blue-300"
  />

  <MainEditor />
  <div class="flex flex-col">
    <ActionButtons />
    <WorkFolders />
  </div>
</section>
