<script lang="ts">
  import ActionButtons from '$components/ActionButtons.svelte';
  import MainEditor from '$components/MainEditor.svelte';
  import WorkFolders from '$components/WorkFolders.svelte';
  import Icon from '@iconify/svelte';
</script>

<section class="flex flex-col">
  <div class="border-b border-gray-700 bg-gray-900">
    <div class="p-6 flex items-center justify-between">
      <div>
        <h1 class="text-3xl font-bold text-blue-300 mb-2 flex gap-3 items-center">
          <Icon icon="hugeicons:injection" class="w-8 h-8 text-blue-300" />
          Extracteur
        </h1>
        <p class="text-blue-200 text-sm">
          Extrayez les dialogues de vos jeux
        </p>
      </div>
    </div>
  </div>
  <MainEditor />
  <div class="flex flex-col">
    <ActionButtons />
    <WorkFolders />
  </div>
</section>
