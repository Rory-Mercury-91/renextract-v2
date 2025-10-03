<script lang="ts">
  import { createEventDispatcher } from 'svelte';

  const dispatch = createEventDispatcher();

  export let isOpen = false;
  export let title = '';
  export let content = '';
  export let showInput = false;
  export let inputPlaceholder = '';
  export let inputValue = '';
  export let confirmText = 'Confirmer';
  export let cancelText = 'Annuler';

  function handleConfirm() {
    dispatch('confirm', { value: showInput ? inputValue : null });
    closeModal();
  }

  function closeModal() {
    isOpen = false;
    dispatch('close');
  }

  function handleKeydown(event: KeyboardEvent) {
    if (event.key === 'Escape') {
      closeModal();
    }
  }
</script>

{#if isOpen}
  <div 
    class="fixed inset-0 z-50 flex items-center justify-center p-4"
    on:click={closeModal}
    on:keydown={handleKeydown}
    tabindex="-1"
    role="dialog"
    aria-modal="true"
  >
    <div 
      class="max-w-md w-full rounded-xl shadow-xl border"
      on:click|stopPropagation
      on:keydown={handleKeydown}
      tabindex="-1"
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
    >
      <!-- Header -->
      <div class="flex items-center justify-between p-6 border-b dark:border-b-gray-700">
        <h3 id="modal-title" class="text-lg font-semibold">
          {title}
        </h3>
        <button 
          class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
          on:click={closeModal}
          aria-label="Fermer"
        >
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
          </svg>
        </button>
      </div>

      <!-- Content -->
      <div class="p-6">
        <p class="mb-4 text-gray-600 dark:text-gray-300">{content}</p>
        
        {#if showInput}
          <input 
            type="text" 
            bind:value={inputValue}
            placeholder={inputPlaceholder}
            class="w-full p-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        {/if}
      </div>

      <!-- Footer -->
      <div class="flex justify-end gap-3 p-6 border-t dark:border-t-gray-700">
        {#if cancelText}
          <button 
            class="px-4 py-2 rounded-lg font-medium transition-colors"
            on:click={closeModal}
          >
            {cancelText}
          </button>
        {/if}
        <button 
          class="px-4 py-2 rounded-lg font-medium transition-colors"
          on:click={handleConfirm}
        >
          {confirmText}
        </button>
      </div>
    </div>
  </div>
{/if}
