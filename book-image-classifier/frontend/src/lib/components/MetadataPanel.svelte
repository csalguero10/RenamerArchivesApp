<script>
	import {
		selectedImages,
		selectedImageIds,
		selectionCount,
		imageActions,
		pageTypes // Usamos la configuración centralizada del store
	} from '../stores/imageStore.js';

	// --- Estados del componente ---
	let isLoading = false;
	let error = null;
	let successMessage = null;
	let activeTab = 'individual'; // 'individual' | 'bulk' | 'numbering'

	// --- Modelos de datos para los formularios ---
	const initialIndividualForm = {
		type: '',
		page_number: '',
		number_type: 'arabic',
		number_exception: '',
		phantom_number: false,
		validated: false
	};
	let individualForm = { ...initialIndividualForm };

	let bulkForm = {
		type: '',
		validated: null,
		clearPageNumbers: false
	};

	let numberingForm = {
		startNumber: 1,
		numberType: 'arabic',
		phantomNumber: false
	};

	// --- Lógica Reactiva ---
	// Actualiza el formulario individual cuando cambia la selección
	$: {
		if ($selectionCount === 1 && $selectedImages.length === 1) {
			const image = $selectedImages[0];
			individualForm = {
				type: image.type,
				page_number: image.page_number || '',
				number_type: image.number_type || 'arabic',
				number_exception: image.number_exception || '',
				phantom_number: image.phantom_number || false, // Corregido: 'ghost_number' a 'phantom_number' por consistencia
				validated: image.validated || false
			};
			// Si la pestaña activa no es una válida para selección individual, se cambia a 'individual'
			if (activeTab !== 'individual') {
				activeTab = 'individual';
			}
		} else {
			individualForm = { ...initialIndividualForm };
			// Si hay más de una imagen, la pestaña 'individual' se deshabilita, así que cambiamos a 'bulk'
			if ($selectionCount > 1 && activeTab === 'individual') {
				activeTab = 'bulk';
			}
		}
	}

	// --- Funciones Helper ---
	function clearMessages() {
		error = null;
		successMessage = null;
	}

	function showSuccess(message) {
		successMessage = message;
		setTimeout(() => {
			successMessage = null;
		}, 3000);
	}

	// --- Acciones de la API ---
	async function handleAsyncAction(actionFn, successMsg, errorMsgPrefix) {
		if ($selectionCount === 0) return;
		clearMessages();
		isLoading = true;
		try {
			await actionFn();
			showSuccess(successMsg);
		} catch (err) {
			error = `${errorMsgPrefix}: ${err.message}`;
		} finally {
			isLoading = false;
		}
	}

	function updateIndividualImage() {
		handleAsyncAction(
			() => imageActions.updateImage($selectedImageIds[0], individualForm),
			'Imagen actualizada correctamente.',
			'Error al actualizar'
		);
	}

	function bulkUpdateImages() {
		const updates = {};
		if (bulkForm.type) updates.type = bulkForm.type;
		if (bulkForm.validated !== null) updates.validated = bulkForm.validated;
		if (bulkForm.clearPageNumbers) {
			updates.page_number = null;
			updates.number_exception = '';
			updates.phantom_number = false;
		}

		if (Object.keys(updates).length === 0) return; // No hacer nada si no hay cambios

		handleAsyncAction(
			() => imageActions.bulkUpdateImages($selectedImageIds, updates),
			`${$selectionCount} imágenes actualizadas.`,
			'Error en actualización masiva'
		);
	}

	function applyConsecutiveNumbering() {
		handleAsyncAction(
			() => imageActions.applyConsecutiveNumbering($selectedImageIds, numberingForm),
			`Numeración aplicada a ${$selectionCount} imágenes.`,
			'Error en numeración'
		);
	}
</script>

<div class="p-4 space-y-4">
	<div>
		<h3 class="text-lg font-semibold text-gray-800">Panel de Metadatos</h3>
		{#if $selectionCount === 0}
			<p class="text-sm text-gray-500 mt-1">Selecciona una o más imágenes para editar.</p>
		{:else}
			<p class="text-sm text-blue-600 font-medium mt-1">
				{$selectionCount} imagen{$selectionCount !== 1 ? 'es' : ''} seleccionada{$selectionCount !== 1 ? 's' : ''}.
			</p>
		{/if}
	</div>

	{#if error}
		<div class="p-3 bg-red-50 text-sm text-red-700 border border-red-200 rounded-md">{error}</div>
	{/if}
	{#if successMessage}
		<div class="p-3 bg-green-50 text-sm text-green-700 border border-green-200 rounded-md">
			{successMessage}
		</div>
	{/if}

	{#if $selectionCount > 0}
		<div class="border-t pt-4">
			<div class="border-b border-gray-200">
				<nav class="-mb-px flex space-x-6" aria-label="Tabs">
					<button
						class="tab"
						class:active={activeTab === 'individual'}
						disabled={$selectionCount !== 1}
						on:click={() => (activeTab = 'individual')}>Edición Individual</button
					>
					<button class="tab" class:active={activeTab === 'bulk'} on:click={() => (activeTab = 'bulk')}
						>Edición Masiva</button
					>
					<button
						class="tab"
						class:active={activeTab === 'numbering'}
						on:click={() => (activeTab = 'numbering')}>Numeración</button
					>
				</nav>
			</div>

			<div class="mt-4">
				{#if activeTab === 'individual'}
					<form on:submit|preventDefault={updateIndividualImage} class="space-y-4">
						<div>
							<label for="type-select" class="label">Tipo de Página</label>
							<select id="type-select" class="input" bind:value={individualForm.type}>
								{#each Object.entries(pageTypes) as [type, config] (type)}
									<option value={type}>{config.icon} {config.label}</option>
								{/each}
							</select>
						</div>
						<div>
							<label for="page-number-input" class="label">Número de Página</label>
							<input
								id="page-number-input"
								type="text"
								class="input"
								placeholder="Ej: 15, XV, 15bis"
								bind:value={individualForm.page_number}
							/>
						</div>
						<label class="checkbox-label">
							<input type="checkbox" class="checkbox" bind:checked={individualForm.phantom_number} />
							<span>Número fantasma (no impreso)</span>
						</label>
						<label class="checkbox-label">
							<input type="checkbox" class="checkbox" bind:checked={individualForm.validated} />
							<span>Marcado como validado</span>
						</label>
						<button type="submit" class="button-primary w-full" disabled={isLoading}>
							{isLoading ? 'Actualizando...' : 'Actualizar Imagen'}
						</button>
					</form>
				{/if}

				{#if activeTab === 'bulk'}
					<form on:submit|preventDefault={bulkUpdateImages} class="space-y-4">
						<div>
							<label for="bulk-type-select" class="label">Cambiar tipo a:</label>
							<select id="bulk-type-select" class="input" bind:value={bulkForm.type}>
								<option value="">-- No cambiar --</option>
								{#each Object.entries(pageTypes) as [type, config] (type)}
									<option value={type}>{config.icon} {config.label}</option>
								{/each}
							</select>
						</div>
						<div>
							<label for="bulk-validated" class="label">Estado de validación:</label>
							<select id="bulk-validated" class="input" bind:value={bulkForm.validated}>
								<option value={null}>-- No cambiar --</option>
								<option value={true}>Validado</option>
								<option value={false}>No validado</option>
							</select>
						</div>
						<label class="checkbox-label">
							<input type="checkbox" class="checkbox" bind:checked={bulkForm.clearPageNumbers} />
							<span>Limpiar números de página</span>
						</label>
						<button type="submit" class="button-primary w-full" disabled={isLoading}>
							{isLoading ? 'Actualizando...' : `Actualizar ${$selectionCount} Imágenes`}
						</button>
					</form>
				{/if}

				{#if activeTab === 'numbering'}
					<form on:submit|preventDefault={applyConsecutiveNumbering} class="space-y-4">
						<div>
							<label for="start-number" class="label">Número inicial</label>
							<input
								id="start-number"
								type="number"
								min="1"
								class="input"
								bind:value={numberingForm.startNumber}
							/>
						</div>
						<label class="checkbox-label">
							<input type="checkbox" class="checkbox" bind:checked={numberingForm.phantomNumber} />
							<span>Aplicar como número fantasma</span>
						</label>
						<button type="submit" class="button-primary w-full" disabled={isLoading}>
							{isLoading ? 'Aplicando...' : `Aplicar Numeración`}
						</button>
					</form>
				{/if}
			</div>
		</div>
	{/if}
</div>

<style>
	.label {
		display: block;
		margin-bottom: 0.25rem;
		font-size: 0.875rem;
		font-weight: 500;
		color: #374151;
	}
	.input {
		width: 100%;
		border-radius: 0.375rem; /* [cite: 8] */
		border: 1px solid #d1d5db; /* [cite: 8] */
		padding: 0.5rem 0.75rem; /* [cite: 8] */
	}
	.input:focus {
		border-color: #3b82f6; /* [cite: 9] */
		box-shadow: 0 0 0 2px #bfdbfe; /* [cite: 9] */
		outline: none; /* [cite: 9] */
	}
	.checkbox-label {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.875rem;
		color: #374151;
	}
	.checkbox {
		border-radius: 0.25rem;
		border-color: #d1d5db;
		color: #3b82f6;
	}
	.button-primary {
		background-color: #2563eb;
		color: white;
		font-weight: 600;
		padding: 0.5rem 1rem;
		border-radius: 0.375rem;
		transition: background-color 0.2s;
	}
	.button-primary:hover {
		background-color: #1d4ed8;
	}
	.button-primary:disabled {
		background-color: #9ca3af;
		cursor: not-allowed;
	}
	.tab {
		border-bottom: 2px solid transparent;
		padding: 0.5rem 0.25rem;
		font-size: 0.875rem;
		font-weight: 500;
		color: #6b7280;
	}
	.tab:hover {
		border-color: #d1d5db;
		color: #4b5563;
	}
	.tab.active {
		border-color: #3b82f6;
		color: #3b82f6;
	}
	.tab:disabled {
		color: #d1d5db;
		cursor: not-allowed;
	}
	.tab:disabled:hover {
		border-color: transparent;
	}
</style>