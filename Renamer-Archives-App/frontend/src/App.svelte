<script>
  import { onMount } from 'svelte';

  let images = [];
  let validated = [];

  // Carga las imágenes desde el backend al montar el componente
  onMount(async () => {
    try {
      const res = await fetch('/api/images');
      images = await res.json();
    } catch (error) {
      console.error('Error cargando imágenes:', error);
    }
  });

  // Marca imagen como validada y la mueve a la lista validated
  function validateImage(img) {
    img.validated = true;
    validated = [...validated, img];
    images = images.filter(i => i !== img);
  }

  // Exporta JSON con imágenes validadas y nuevos nombres
  function exportJSON() {
    const result = validated.map((img, idx) => ({
      original: img.filename,
      new_name: `${String(idx + 1).padStart(3, '0')}.jpg`,
      type: img.type
    }));

    const blob = new Blob([JSON.stringify(result, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'renamed_pages.json';
    a.click();
  }
</script>

<h1>📄 Renombrador de páginas</h1>

<h2>Páginas clasificadas</h2>
{#if images.length === 0}
  <p>No hay imágenes para mostrar</p>
{/if}
{#each images as img}
  <div style="border: 1px solid #ccc; padding: 10px; margin-bottom: 5px;">
    <strong>{img.filename}</strong> — tipo: <em>{img.type}</em>
    <button on:click={() => validateImage(img)} style="margin-left: 10px;">Validar</button>
  </div>
{/each}

<h2>Páginas validadas</h2>
{#if validated.length === 0}
  <p>No hay imágenes validadas aún</p>
{/if}
{#each validated as val}
  <div style="background-color: #d3ffd3; padding: 5px; margin-bottom: 4px;">
    ✅ {val.filename} — tipo: {val.type}
  </div>
{/each}

{#if validated.length > 0}
  <button on:click={exportJSON} style="margin-top: 20px; padding: 10px 15px; font-weight: bold;">
    Exportar JSON
  </button>
{/if}

<style>
  :global(body) {
    font-family: Arial, sans-serif;
    background: #f9f9f9;
    padding: 2rem;
  }
  button {
    cursor: pointer;
  }
</style>
