<script>
	import { createEventDispatcher, onMount, onDestroy } from 'svelte';
	import { getImageUrl } from '../utils/api.js';
	import { getPageTypeConfig } from '../stores/imageStore.js';

	export let image;
	const dispatch = createEventDispatcher();

	let imageElement;
	let containerElement;
	let zoomLevel = 1;
	let panX = 0;
	let panY = 0;
	let isDragging = false;
	let lastMouseX = 0;
	let lastMouseY = 0;
	let isImageLoaded = false;
	let imageError = false;

	// Configuración de Zoom
	const MIN_ZOOM = 0.1;
	const MAX_ZOOM = 10;
	const ZOOM_STEP = 0.2;

	// Resetear vista cuando la imagen cambia
	$: if (image) {
		resetView();
	}

	onMount(() => {
		document.addEventListener('keydown', handleKeydown);
	});

	onDestroy(() => {
		document.removeEventListener('keydown', handleKeydown);
	});

	function resetView() {
		isImageLoaded = false;
		imageError = false;
		zoomLevel = 1;
		panX = 0;
		panY = 0;
	}

	// ... (el resto de las funciones como handleKeydown, zoomIn, zoomOut, etc. no necesitan cambios)
	function fitToContainer() {
		if (!containerElement || !imageElement || !isImageLoaded) return;
		const containerWidth = containerElement.clientWidth;
		const containerHeight = containerElement.clientHeight;
		const imageNaturalWidth = imageElement.naturalWidth;
		const imageNaturalHeight = imageElement.naturalHeight;

		if (!imageNaturalWidth || !imageNaturalHeight) return;
		const scaleX = (containerWidth - 40) / imageNaturalWidth; // -40 para padding
		const scaleY = (containerHeight - 40) / imageNaturalHeight;
		const newZoom = Math.min(scaleX, scaleY, 1); // Asegurarse de no hacer zoom in por defecto

		zoomLevel = newZoom;
		panX = (containerWidth - imageNaturalWidth * newZoom) / 2;
		panY = (containerHeight - imageNaturalHeight * newZoom) / 2;
	}

	function handleImageLoad() {
		isImageLoaded = true;
		fitToContainer();
	}

	$: typeConfig = image ? getPageTypeConfig(image.type) : {};
	$: imageStyle = `transform: translate(${panX}px, ${panY}px) scale(${zoomLevel}); cursor: ${isDragging ? 'grabbing' : 'grab'};`;
</script>

<div class="image-viewer-container" bind:this={containerElement}>
	<div class="toolbar">
		<div class="flex items-center space-x-2">
			{#if image}
				<span class="badge {typeConfig.color}">{typeConfig.icon} {typeConfig.label}</span>
				{#if image.page_number}<span class="page-number">Página {image.page_number}</span>{/if}
				<span class="badge {image.validated ? 'bg-green-500' : 'bg-yellow-500'} text-white">
					{image.validated ? '✓ Validada' : '⏳ Pendiente'}
				</span>
			{/if}
		</div>
		<div class="controls">
			<button on:click={zoomOut} title="Alejar (-)">-</button>
			<span>{Math.round(zoomLevel * 100)}%</span>
			<button on:click={zoomIn} title="Acercar (+)">+</button>
			<button on:click={fitToContainer} title="Ajustar (F)">⛶</button>
		</div>
	</div>

	<div
		class="image-area"
		role="region"
		aria-label="Visor de imagen interactivo con zoom y paneo"
		tabindex="0"
		on:wheel={handleWheel}
		on:mousedown={handleMouseDown}
		on:mousemove={handleMouseMove}
		on:mouseup={handleMouseUp}
		on:mouseleave={handleMouseUp}
	>
		{#if image}
			{#if imageError}
				<div class="message">Error al cargar la imagen.</div>
			{:else if !isImageLoaded}
				<div class="message">Cargando...</div>
			{/if}
			<img
				bind:this={imageElement}
				src={getImageUrl(image.id)}
				alt={image.original_filename}
				style={imageStyle}
				class:hidden={!isImageLoaded}
				on:load={handleImageLoad}
				on:error={() => (imageError = true)}
				draggable="false"
			/>
		{/if}
	</div>
</div>

<style>
	.image-viewer-container {
		display: flex;
		flex-direction: column;
		width: 100%;
		height: 100%;
		background-color: #2d3748;
		color: white;
		overflow: hidden;
	}
	.toolbar {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.5rem 1rem;
		background-color: #1a202c;
		flex-shrink: 0;
	}
	.controls {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}
	.controls button {
		background-color: #4a5568;
		border: none;
		color: white;
		border-radius: 4px;
		width: 2rem;
		height: 2rem;
		cursor: pointer;
		font-size: 1.2rem;
		line-height: 1;
	}
	.controls button:hover {
		background-color: #718096;
	}
	.badge {
		padding: 0.25rem 0.75rem;
		border-radius: 9999px;
		font-size: 0.8rem;
		font-weight: 500;
	}
	.page-number {
		font-size: 0.9rem;
		color: #a0aec0;
	}
	.image-area {
		flex-grow: 1;
		position: relative;
		overflow: hidden;
		outline: none; /* Ocultar el outline de foco por defecto, ya que no es un input */
	}
	.image-area:focus-visible {
		box-shadow: inset 0 0 0 2px #3b82f6; /* Añadir un indicador de foco visible para accesibilidad */
	}
	img {
		position: absolute;
		top: 0;
		left: 0;
		transform-origin: 0 0;
		transition: transform 0.1s linear;
		user-select: none;
	}
	img.hidden {
		visibility: hidden;
	}
	.message {
		position: absolute;
		inset: 0;
		display: flex;
		justify-content: center;
		align-items: center;
		font-size: 1.2rem;
		color: #718096;
	}
</style>