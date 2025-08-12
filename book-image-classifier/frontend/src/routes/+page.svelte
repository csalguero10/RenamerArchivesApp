<script>
	import { onMount } from 'svelte';
	import {
		images,
		filteredImages,
		selectedImage,
		currentImageIndex
	} from '../lib/stores/imageStore.js';
	import { api, uploadImages, getImageUrl } from '../lib/utils/api.js';

	import ImageGallery from '../lib/components/ImageGallery.svelte';
	import ImageViewer from '../lib/components/ImageViewer.svelte';
	import MetadataPanel from '../lib/components/MetadataPanel.svelte';
	import FilterPanel from '../lib/components/FilterPanel.svelte';
	import ExportPanel from '../lib/components/ExportPanel.svelte';

	let uploadInput;
	let uploading = false;
	let uploadProgress = 0;
	let errorMessage = '';

	// App state
	let currentView = 'gallery'; // 'gallery', 'validation', 'export'
	let sidebarCollapsed = false;

	onMount(loadImages);

	async function loadImages() {
		try {
			const response = await api.get('/api/images');
			images.set(response.images || []);
			// If no image is selected, select the first one from the filtered list
			if (!$selectedImage && $filteredImages.length > 0) {
				selectedImage.set($filteredImages[0]);
			}
		} catch (error) {
			console.error('Error loading images:', error);
			errorMessage = `Failed to load images: ${error.message}`;
		}
	}

	async function handleFileUpload(event) {
		const files = event.target.files;
		if (!files || files.length === 0) return;

		uploading = true;
		uploadProgress = 0;
		errorMessage = '';

		try {
			const formData = new FormData();
			for (const file of files) {
				formData.append('files', file);
			}

			await uploadImages(formData, (progress) => {
				uploadProgress = progress;
			});

			await loadImages();
		} catch (error) {
			console.error('Error uploading images:', error);
			errorMessage = `Upload failed: ${error.message}`;
			alert(errorMessage);
		} finally {
			uploading = false;
			uploadProgress = 0;
			if (uploadInput) uploadInput.value = '';
		}
	}

	function handleDrop(event) {
		event.preventDefault();
		handleFileUpload({ target: { files: event.dataTransfer.files } });
	}

	function handleDragOver(event) {
		event.preventDefault();
	}

	async function handleImageUpdate(event) {
		const { imageId, updates } = event.detail;
		try {
			const updatedImage = await api.put(`/api/images/${imageId}`, updates);
			// Update the image in the store for immediate feedback
			images.update(items =>
				items.map(img => (img.id === imageId ? { ...img, ...updatedImage } : img))
			);
			selectedImage.update(img => (img && img.id === imageId ? { ...img, ...updatedImage } : img));
		} catch (error) {
			console.error(`Error updating image ${imageId}:`, error);
			alert(`Error updating image: ${error.message}`);
		}
	}

	async function handleImageValidation(event) {
		const { imageId } = event.detail;
		try {
			const validatedImage = await api.put(`/api/images/${imageId}`, { validated: true });
			images.update(items =>
				items.map(img => (img.id === imageId ? { ...img, ...validatedImage } : img))
			);
			selectedImage.update(img => (img && img.id === imageId ? { ...img, ...validatedImage } : img));
		} catch (error) {
			console.error(`Error validating image ${imageId}:`, error);
			alert(`Error validating image: ${error.message}`);
		}
	}

	function navigateImage(direction) {
		const currentImages = $filteredImages;
		const currentIndex = $currentImageIndex;

		if (currentImages.length === 0) return;

		let newIndex = currentIndex + direction;
		if (newIndex < 0) newIndex = currentImages.length - 1;
		if (newIndex >= currentImages.length) newIndex = 0;

		selectedImage.set(currentImages[newIndex]);
	}

	// --- Stats derived from the filtered list ---
	$: stats = {
		total: $filteredImages.length,
		validated: $filteredImages.filter((img) => img.validated).length,
		pending: $filteredImages.filter((img) => !img.validated).length
	};
</script>

<svelte:window on:keydown={(e) => {
	if (document.activeElement.tagName === 'INPUT' || document.activeElement.tagName === 'TEXTAREA') return;
	if (e.key === 'ArrowLeft') navigateImage(-1);
	if (e.key === 'ArrowRight') navigateImage(1);
}} />

<div class="flex h-screen flex-col bg-gray-100 font-sans">
	<header class="flex-shrink-0 border-b border-gray-200 bg-white px-6 py-3 shadow-sm">
		<div class="flex items-center justify-between">
			<div class="flex items-center space-x-4">
				<h1 class="text-xl font-bold text-gray-800">📚 Book Image Classifier</h1>
				<div class="text-sm text-gray-500">
					{$images.length} Total | {stats.total} Filtered ({stats.validated} validadas)
				</div>
			</div>
			<div class="flex items-center space-x-3">
				<div class="flex rounded-lg bg-gray-100 p-1">
					<button class:active={currentView === 'gallery'} on:click={() => (currentView = 'gallery')}>Galería</button>
					<button class:active={currentView === 'export'} on:click={() => (currentView = 'export')}>Exportar</button>
				</div>
				<button class="btn-primary" on:click={() => uploadInput.click()} disabled={uploading}>
					{#if uploading}
						<span>Subiendo... {uploadProgress}%</span>
					{:else}
						<span>📁 Cargar Imágenes</span>
					{/if}
				</button>
			</div>
		</div>
	</header>

	<input type="file" multiple accept="image/*" bind:this={uploadInput} on:change={handleFileUpload} class="hidden" />

	<div class="flex flex-1 overflow-hidden">
		<aside class:collapsed={sidebarCollapsed} class="sidebar">
			<button class="collapse-btn" on:click={() => (sidebarCollapsed = !sidebarCollapsed)}>
				{sidebarCollapsed ? '→' : '←'}
			</button>
			{#if !sidebarCollapsed}
				<div class="flex flex-1 flex-col overflow-hidden">
					<div class="p-4"><FilterPanel /></div>
					<div class="flex-1 overflow-y-auto border-t border-gray-200">
						<ImageGallery
							images={$filteredImages}
							bind:selectedImage={$selectedImage}
						/>
					</div>
				</div>
			{/if}
		</aside>

		<main class="flex flex-1" on:drop={handleDrop} on:dragover={handleDragOver}>
			<div class="flex-1 bg-gray-800">
				{#if $filteredImages.length === 0}
					<div class="flex h-full items-center justify-center text-center text-gray-400">
						<div>
							<div class="mb-4 text-6xl">📚</div>
							<h3 class="text-xl font-semibold">No hay imágenes que mostrar</h3>
							<p>Sube algunas imágenes para empezar o ajusta tus filtros.</p>
						</div>
					</div>
				{:else if $selectedImage}
					<ImageViewer
						image={$selectedImage}
						on:navigate={(e) => navigateImage(e.detail)}
					/>
				{:else}
					<div class="flex h-full items-center justify-center text-center text-gray-400">
						<div>
							<div class="mb-4 text-4xl">👆</div>
							<p>Selecciona una imagen de la galería</p>
						</div>
					</div>
				{/if}
			</div>

			{#if currentView === 'export'}
				<div class="w-96 flex-shrink-0 border-l border-gray-200 bg-white overflow-y-auto">
					<ExportPanel />
				</div>
			{:else if $selectedImage}
				<div class="w-80 flex-shrink-0 border-l border-gray-200 bg-white">
					<MetadataPanel
						image={$selectedImage}
						on:update={handleImageUpdate}
						on:validate={handleImageValidation}
					/>
				</div>
			{/if}
		</main>
	</div>
</div>

<style>
	.sidebar {
		width: 320px;
		flex-shrink: 0;
		display: flex;
		flex-direction: column;
		background: white;
		border-right: 1px solid #e5e7eb;
		transition: width 0.3s ease;
	}
	.sidebar.collapsed {
		width: 48px;
	}
	.collapse-btn {
		padding: 0.75rem;
		border-bottom: 1px solid #e5e7eb;
		color: #4b5563;
	}
	.collapse-btn:hover {
		background: #f9fafb;
	}
	button.active {
		background: white;
		color: #1e40af;
		box-shadow: 0 1px 2px rgba(0,0,0,0.05);
	}
	:global(.btn-primary) {
		padding: 0.5rem 1rem;
		background-color: #2563eb;
		color: white;
		border-radius: 0.5rem;
		font-weight: 500;
		transition: background-color 0.2s;
	}
	:global(.btn-primary:hover) {
		background-color: #1d4ed8;
	}
	:global(.btn-primary:disabled) {
		background-color: #93c5fd;
		cursor: not-allowed;
	}
	:global(button) {
		padding: 0.5rem 0.75rem;
		border-radius: 0.375rem;
		font-size: 0.875rem;
		font-weight: 500;
		color: #374151;
		transition: background-color 0.2s;
	}
</style>