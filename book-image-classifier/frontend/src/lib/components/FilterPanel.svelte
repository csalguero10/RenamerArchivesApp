<script>
	import { filters, pageTypes, images as allImages, filteredImages } from '../stores/imageStore.js';

	const validationStates = [
		{ value: 'all', label: 'Todas' },
		{ value: 'validated', label: 'Validadas' },
		{ value: 'notValidated', label: 'No Validadas' }
	];
	const numberingStates = [
		{ value: 'all', label: 'Todos' },
		{ value: 'with', label: 'Con Número' },
		{ value: 'without', label: 'Sin Número' }
	];

	function clearAllFilters() {
		filters.set({
			validation: 'all',
			type: 'all',
			pageNumber: 'all'
		});
	}

	function updateValidationFilter(value) {
		filters.update(f => ({ ...f, validation: value }));
	}
	function updateTypeFilter(event) {
		filters.update(f => ({ ...f, type: event.target.value }));
	}
	function updatePageNumberFilter(value) {
		filters.update(f => ({ ...f, pageNumber: value }));
	}

	$: filteredCount = $filteredImages.length;
	$: totalCount = $allImages.length;
</script>

<div class="space-y-4">
	<div class="flex justify-between items-center">
		<h3 class="text-lg font-semibold text-gray-800">Filtros</h3>
		{#if filteredCount !== totalCount}
			<span class="text-sm font-medium text-blue-600">{filteredCount} / {totalCount}</span>
		{/if}
	</div>

	<fieldset class="filter-section">
		<legend class="label">Estado</legend>
		<div class="tabs">
			{#each validationStates as state}
				<button class:active={$filters.validation === state.value} on:click={() => updateValidationFilter(state.value)}>
					{state.label}
				</button>
			{/each}
		</div>
	</fieldset>

	<div class="filter-section">
		<label class="label" for="type-select">Tipo de Página</label>
		<select id="type-select" class="input" value={$filters.type} on:change={updateTypeFilter}>
			<option value="all">Todos los tipos</option>
			{#each Object.entries(pageTypes) as [type, config]}
				<option value={type}>{config.icon} {config.label}</option>
			{/each}
		</select>
	</div>

	<fieldset class="filter-section">
		<legend class="label">Numeración</legend>
		<div class="tabs">
			{#each numberingStates as state}
				<button class:active={$filters.pageNumber === state.value} on:click={() => updatePageNumberFilter(state.value)}>
					{state.label}
				</button>
			{/each}
		</div>
	</fieldset>

	<div class="pt-2 border-t">
		<button class="w-full text-sm text-gray-600 hover:text-red-600 transition-colors" on:click={clearAllFilters}>
			Limpiar todos los filtros
		</button>
	</div>
</div>

<style>
	.label, legend { display: block; margin-bottom: 0.5rem; font-size: 0.875rem; font-weight: 500; color: #374151; }
	fieldset { border: none; padding: 0; }
	.input { width: 100%; border-radius: 0.375rem; border: 1px solid #d1d5db; padding: 0.5rem 0.75rem; }
	.tabs { display: flex; background-color: #f3f4f6; border-radius: 0.5rem; padding: 2px; }
	.tabs button { flex: 1; padding: 0.3rem 0; font-size: 0.8rem; border: none; background: transparent; border-radius: 0.375rem; cursor: pointer; font-weight: 500; color: #4b5563; }
	.tabs button.active { background-color: white; color: #1f2937; box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06); }
</style>