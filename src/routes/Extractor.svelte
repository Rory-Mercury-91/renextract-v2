<script lang="ts">
  import ActionButtons from '$components/ActionButtons.svelte';
  import MainEditor from '$components/MainEditor.svelte';
  import RouteHeader from '$components/RouteHeader.svelte';
  import WorkFolders from '$components/WorkFolders.svelte';
</script>

<section class="flex flex-col">
  <RouteHeader title="Extracteur" description="Extrayez les dialogues de vos jeux" icon="hugeicons:injection" color="blue" />
  
  <MainEditor />
  <div class="flex flex-col">
    <ActionButtons />
    <WorkFolders />
  </div>
</section>
