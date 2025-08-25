<script>
	import { createEventDispatcher } from 'svelte';
	// CORREGIDO: Se importa 'filteredImages' que es el store correcto para el panel.
	import { filteredImages, images } from '../stores/imageStore.js';
	// CORREGIDO: Se importa el objeto 'api' que contiene los métodos de fetch.
	import { api } from '../utils/api.js';

	const dispatch = createEventDispatcher();

	// Estados del export (sin tipos de TypeScript)
	let isExporting = false;
	let exportProgress = 0;
	let exportStatus = 'idle'; // 'idle' | 'preparing' | 'exporting' | 'success' | 'error'
	let exportMessage = '';
	let downloadUrl = null;
	let showPreview = false;
	let previewItems = [];


	// Configuración de exportación
	let exportConfig = {
		includeValidatedOnly: false,
		includeImages: true,
		includeMetadata: true,
		renameFiles: true,
		exportFormat: 'zip' // 'zip' | 'json-only'
	};

	// Estadísticas de exportación
	$: imagesForStats = exportConfig.includeValidatedOnly
		? $filteredImages.filter(img => img.validated)
		: $filteredImages;

	$: exportStats = {
		total: imagesForStats.length,
		validated: imagesForStats.filter(img => img.validated).length,
		notValidated: imagesForStats.filter(img => !img.validated).length,
		withNumbers: imagesForStats.filter(img => img.page_number && img.page_number !== 'False').length
	};

	// Generar nuevo nombre de archivo
	function generateNewFilename(image) {
		if (!exportConfig.renameFiles) {
			return image.original_filename;
		}

		const extension = image.original_filename.split('.').pop();
		const baseName = image.original_filename.replace(`.${extension}`, '');
		let newName = `${baseName} ${image.type}`;

		if (image.page_number && image.page_number !== 'False' && image.page_number !== false) {
			if (image.phantom_number) { // CORREGIDO: Se usa 'ghost_number'
				newName += ` [${image.page_number}]`;
			} else {
				newName += ` p ${image.page_number}`;
			}
		}

		return `${newName}.${extension}`;
	}

	// Función principal de exportación
	async function startExport() {
		isExporting = true;
		exportStatus = 'preparing';
		exportMessage = 'Preparando exportación...';
		exportProgress = 0;
		downloadUrl = null;

		const imagesToExport = exportConfig.includeValidatedOnly
			? $filteredImages.filter(img => img.validated)
			: $filteredImages;

		if (imagesToExport.length === 0) {
			exportMessage = 'No hay imágenes para exportar.';
			exportStatus = 'error';
			isExporting = false;
			return;
		}

		try {
			// Generar metadata
			const metadata = imagesToExport.map(img => ({
				id: img.id, // <-- AÑADIR ESTA LÍNEA ES CRUCIAL
				original_filename: img.original_filename,
				new_filename: generateNewFilename(img),
				type: img.type,
				validated: img.validated,
				page_number: img.page_number || null,
				phantom_number: img.phantom_number || false
			}));

			exportStatus = 'exporting';
			exportMessage = 'Generando archivos...';
			
			// Llamada al backend para generar el export
			const exportData = {
				images: imagesToExport.map(img => img.id),
				metadata: metadata,
				config: exportConfig
			};

			const response = await api.post('/api/export', exportData);
			
			exportProgress = 90;
			exportMessage = 'Preparando descarga...';

			if (response.success && response.download_url) {
				downloadUrl = response.download_url;
				exportStatus = 'success';
				exportMessage = `Exportación completada. ${imagesToExport.length} archivos procesados.`;
				exportProgress = 100;
			} else {
				throw new Error(response.error || 'Error en la respuesta del servidor.');
			}
		} catch (error) {
			console.error('Error en exportación:', error);
			exportStatus = 'error';
			exportMessage = error.message;
			exportProgress = 0;
		} finally {
			isExporting = false;
		}
	}

	// Descargar archivo exportado
	function downloadExport() {
		if (downloadUrl) {
			const fullUrl = `http://localhost:5000${downloadUrl}`;
			const link = document.createElement('a');
			link.href = fullUrl;
			link.download = `book-export-${new Date().toISOString().split('T')[0]}.zip`;
			document.body.appendChild(link);
			link.click();
			document.body.removeChild(link);
		}
	}
	
	function resetExport() {
		exportStatus = 'idle';
		exportMessage = '';
		exportProgress = 0;
		downloadUrl = null;
	}
</script>

<div class="export-panel p-4 space-y-4">
  <div class="export-header border-b pb-2 mb-4">
    <h3 class="text-xl font-semibold">Exportar proyecto</h3>
  </div>
  
  <div class="export-stats bg-gray-100 p-3 rounded-lg space-y-2">
    <div class="stat-item flex justify-between"><span class="text-gray-600">Imágenes a exportar:</span> <span class="font-bold">{exportStats.total}</span></div>
    <div class="stat-item flex justify-between"><span class="text-gray-600">Validadas:</span> <span class="font-bold text-green-600">{exportStats.validated}</span></div>
    <div class="stat-item flex justify-between"><span class="text-gray-600">Pendientes:</span> <span class="font-bold text-yellow-600">{exportStats.notValidated}</span></div>
  </div>
  
  <div class="export-config space-y-3">
    <h4 class="font-medium">Configuración</h4>
    <label class="flex items-center space-x-2 cursor-pointer">
      <input type="checkbox" bind:checked={exportConfig.includeValidatedOnly} class="rounded" />
      <span>Solo imágenes validadas</span>
    </label>
    <label class="flex items-center space-x-2 cursor-pointer">
      <input type="checkbox" bind:checked={exportConfig.renameFiles} class="rounded" />
      <span>Renombrar archivos</span>
    </label>
  </div>
  
  {#if exportStatus !== 'idle'}
    <div class="export-status p-3 rounded-lg" class:bg-blue-100={isExporting} class:bg-green-100={exportStatus === 'success'} class:bg-red-100={exportStatus === 'error'}>
      <div class="status-message font-medium mb-2">{exportMessage}</div>
      {#if isExporting}
        <div class="progress-bar bg-gray-200 rounded-full h-2.5">
          <div class="bg-blue-600 h-2.5 rounded-full" style="width: {exportProgress}%"></div>
        </div>
      {/if}
      {#if exportStatus === 'success' && downloadUrl}
        <button class="btn btn-primary w-full mt-2" on:click={downloadExport}>
          Descargar Archivo ZIP
        </button>
      {/if}
      {#if exportStatus === 'error' || exportStatus === 'success'}
        <button class="btn btn-secondary w-full mt-2" on:click={resetExport}>
          Reiniciar
        </button>
      {/if}
    </div>
  {/if}
  
  <div class="export-actions pt-4 border-t">
    <button class="btn btn-primary w-full" on:click={startExport} disabled={isExporting || exportStats.total === 0 || exportStatus === 'success'}>
      {#if isExporting}
        <span>Exportando...</span>
      {:else}
        <span>Exportar {exportStats.total} {exportStats.total === 1 ? 'archivo' : 'archivos'}</span>
      {/if}
    </button>
  </div>
</div>

<style>
  .btn {
    padding: 0.5rem 1rem;
    border-radius: 0.375rem;
    font-weight: 500;
    transition: background-color 0.2s;
  }
  .btn-primary {
    background-color: #3b82f6;
    color: white;
  }
  .btn-primary:hover {
    background-color: #2563eb;
  }
  .btn-primary:disabled {
    background-color: #9ca3af;
    cursor: not-allowed;
  }
  .btn-secondary {
    background-color: #e5e7eb;
    color: #374151;
  }
</style>