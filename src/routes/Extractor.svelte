<script lang="ts">
  import ActionButtons from '$components/ActionButtons.svelte';
  import MainEditor from '$components/MainEditor.svelte';
  import WorkFolders from '$components/WorkFolders.svelte';
</script>

<section class="flex flex-col">
  <MainEditor />
  <div class="flex flex-col">
    <ActionButtons />
    <WorkFolders />
  </div>
</section>
