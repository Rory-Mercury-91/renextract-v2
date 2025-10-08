<script lang="ts">
  import { appSettings } from '../stores/app';
</script>

<div class="space-y-8">
  <div>
    <h3 class="mb-4 text-xl font-semibold">Extraction & Protection</h3>
    <p class="text-gray-600 dark:text-gray-400">
      Configuration des paramètres d'extraction et de protection des données.
    </p>

    <div class="space-y-6">
      <!-- Configuration des placeholders -->
      <div>
        <h3 class="mb-4 text-lg font-semibold">
          🔧 Configuration des placeholders
        </h3>
        <div class="space-y-4">
          <div>
            <label
              for="placeholder-format"
              class="mb-2 block text-sm font-medium"
              >Format des placeholders :</label
            >
            <input
              id="placeholder-format"
              type="text"
              bind:value={$appSettings.extraction.placeholderFormat}
              placeholder="Ex: PLACEHOLDER_N"
              class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 focus:border-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-800 dark:text-white"
            />
            <p class="mt-1 text-sm text-gray-600 dark:text-gray-400">
              Format utilisé pour marquer les éléments à traduire
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
