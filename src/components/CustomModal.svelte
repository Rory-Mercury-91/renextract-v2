<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { appState } from '../stores/app';

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

  // Theme classes based on current theme
  $: modalClasses = $appState.currentTheme === 'dark' 
    ? 'bg-gray-800 text-white border-gray-700' 
    : 'bg-white text-gray-900 border-gray-200';
    
  $: overlayClasses = $appState.currentTheme === 'dark'
    ? 'bg-black bg-opacity-50'
    : 'bg-black bg-opacity-30';
    
  $: titleClasses = $appState.currentTheme === 'dark'
    ? 'text-white border-b-gray-700'
    : 'text-gray-900 border-b-gray-200';
    
  $: buttonPrimaryClasses = $appState.currentTheme === 'dark'
    ? 'bg-blue-600 hover:bg-blue-700 text-white'
    : 'bg-blue-600 hover:bg-blue-700 text-white';
    
  $: buttonSecondaryClasses = $appState.currentTheme === 'dark'
    ? 'bg-gray-600 hover:bg-gray-700 text-white'
    : 'bg-gray-200 hover:bg-gray-300 text-gray-900';
    
  $: inputClasses = $appState.currentTheme === 'dark'
    ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400'
    : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500';
</script>

{#if isOpen}
  <div 
    class="fixed inset-0 z-50 {overlayClasses} flex items-center justify-center p-4"
    on:click={closeModal}
    on:keydown={handleKeydown}
    tabindex="-1"
    role="dialog"
    aria-modal="true"
  >
    <div 
      class="max-w-md w-full {modalClasses} rounded-xl shadow-xl border"
      on:click|stopPropagation
      on:keydown={handleKeydown}
      tabindex="-1"
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
    >
      <!-- Header -->
      <div class="flex items-center justify-between p-6 border-b" class:border-b-gray-700={$appState.currentTheme === 'dark'}>
        <h3 id="modal-title" class="text-lg font-semibold {titleClasses}">
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
            class="w-full p-3 border rounded-lg {inputClasses} focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        {/if}
      </div>

      <!-- Footer -->
      <div class="flex justify-end gap-3 p-6 border-t" class:border-t-gray-700={$appState.currentTheme === 'dark'}>
        {#if cancelText}
          <button 
            class="px-4 py-2 rounded-lg font-medium transition-colors {buttonSecondaryClasses}"
            on:click={closeModal}
          >
            {cancelText}
          </button>
        {/if}
        <button 
          class="px-4 py-2 rounded-lg font-medium transition-colors {buttonPrimaryClasses}"
          on:click={handleConfirm}
        >
          {confirmText}
        </button>
      </div>
    </div>
  </div>
{/if}
