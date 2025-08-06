<script>
  import { onMount } from 'svelte';

  let images = [];
  let validated = [];
  let selectedIndex = 0;
  let filterType = 'all';
  let showValidated = false;

  // Carga inicial de imágenes y metadata del backend
  async function loadImages() {
    const res = await fetch('http://localhost:5000/images');
    images = await res.json();
    validated = images.filter(i => i.validated);
  }

  onMount(() => {
    loadImages();
  });

  // Clasificación automática básica según nombre
  function classifyImage(name) {
    const lower = name.toLowerCase();
    if (lower.includes('ref')) return 'referencia';
    if (lower.includes('ins')) return 'inserto';
    if (name === '00001.jpg') return 'portada';
    if (name === '00002.jpg') return 'guardia';
    // Simula detección texto/ilustración si quieres agregar
    if (lower.includes('ilustracion')) return 'ilustracion';
    if (lower.includes('blanca')) return 'blanca';
    return 'texto';
  }

  // Cambiar tipo manualmente
  function changeType(img, newType) {
    img.type = newType;
  }

  // Validar imagen: la mueve a validadas y la marca
  function validateImage(img) {
    img.validated = true;
    if (!validated.includes(img)) validated.push(img);
  }

  // Cambiar página numérica o romano
  function toRoman(num) {
    if (!num) return '';
    const romans = [
      ['M',1000], ['CM',900], ['D',500], ['CD',400],
      ['C',100], ['XC',90], ['L',50], ['XL',40],
      ['X',10], ['IX',9], ['V',5], ['IV',4], ['I',1]
    ];
    let result = '';
    let n = num;
    for (const [r,v] of romans) {
      while (n >= v) {
        result += r;
        n -= v;
      }
    }
    return result;
  }

  // Asignar número de página (y romano si quiere)
  function setPageNum(img, val) {
    const n = parseInt(val);
    if (!isNaN(n)) img.pageNum = n;
  }
  function setRoman(img, val) {
    img.pageNumRoman = val;
  }

  // Marcar si número entre corchetes (no aparece en libro)
  function toggleBracket(img) {
    img.bracketed = !img.bracketed;
  }

  // Asignar excepción (ej. bis)
  function setException(img, val) {
    img.exception = val;
  }

  // Guardar cambios al backend
  async function saveMetadata() {
    const res = await fetch('http://localhost:5000/images', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify(images)
    });
    if (res.ok) alert('Metadata guardada');
    else alert('Error al guardar');
  }

  // Renombrar archivos físicamente
  async function renameFiles() {
    // Generamos lista para backend con new_name basado en página validada
    const renameList = validated.map((img, idx) => {
      const baseNum = img.pageNumRoman ? toRoman(img.pageNum) : img.pageNum;
      let pageStr = baseNum || (idx + 1);
      if (img.bracketed) pageStr = `[${pageStr}]`;
      if (img.exception) pageStr += img.exception;
      return {
        original: img.name,
        new_name: `${pageStr}.jpg`
      };
    });

    const res = await fetch('http://localhost:5000/rename', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify(renameList)
    });
    if (res.ok) alert('Archivos renombrados');
    else {
      const data = await res.json();
      alert('Error renombrando:\n' + (data.errors || []).join('\n'));
    }
  }

  // Filtrar imágenes según validadas/no validadas y tipo
  $: filteredImages = (showValidated ? validated : images.filter(i => !i.validated))
    .filter(i => filterType === 'all' ? true : i.type === filterType);

  // Navegación imágenes estilo visor PDF
  function selectIndex(i) {
    selectedIndex = i;
  }
</script>

<h1>Renombrador de Páginas</h1>

<label>
  Mostrar:
  <select bind:value={filterType}>
    <option value="all">Todas</option>
    <option value="portada">Portada</option>
    <option value="guardia">Guardia</option>
    <option value="referencia">Referencia</option>
    <option value="inserto">Inserto</option>
    <option value="blanca">Página Blanca</option>
    <option value="ilustracion">Ilustración</option>
    <option value="texto">Texto</option>
  </select>
</label>

<label>
  <input type="checkbox" bind:checked={showValidated} /> Mostrar solo validadas
</label>

<div style="display:flex; gap: 2rem; margin-top: 1rem;">
  <!-- Visualizador grande -->
  {#if filteredImages.length > 0}
    <div style="flex: 3; border: 1px solid #ccc; padding: 1rem;">
      <img src={`http://localhost:5000/uploads/${filteredImages[selectedIndex].name}`} alt={filteredImages[selectedIndex].name} style="max-width:100%; max-height:400px;" />
      <p><strong>{filteredImages[selectedIndex].name}</strong></p>

      <p>Tipo:
        <select bind:value={filteredImages[selectedIndex].type}>
          <option value="portada">Portada</option>
          <option value="guardia">Guardia</option>
          <option value="referencia">Referencia</option>
          <option value="inserto">Inserto</option>
          <option value="blanca">Página Blanca</option>
          <option value="ilustracion">Ilustración</option>
          <option value="texto">Texto</option>
          <option value="contraportada">Contraportada</option>
          <option value="frontispicio">Frontispicio</option>
          <option value="vite">Vite</option>
        </select>
      </p>

      <p>
        Número de página:
        <input type="number" min="1" bind:value={filteredImages[selectedIndex].pageNum} on:input={(e) => setPageNum(filteredImages[selectedIndex], e.target.value)} />
        <label><input type="checkbox" bind:checked={filteredImages[selectedIndex].pageNumRoman} /> Romano</label>
        <label>Excepción: <input type="text" maxlength="10" size="5" bind:value={filteredImages[selectedIndex].exception} on:input={(e) => setException(filteredImages[selectedIndex], e.target.value)} /></label>
        <button on:click={() => toggleBracket(filteredImages[selectedIndex])}>
          {filteredImages[selectedIndex].bracketed ? 'Quitar []' : 'Poner []'}
        </button>
      </p>

      <p>
        <button on:click={() => validateImage(filteredImages[selectedIndex])}>Validar esta página</button>
      </p>
    </div>

    <!-- Visualizador lateral para seleccionar -->
    <div style="flex: 1; max-height: 500px; overflow-y: auto; border: 1px solid #ccc; padding: 0.5rem;">
      {#each filteredImages as img, i}
        <button
          type="button"
          style="margin-bottom: 0.5rem; cursor: pointer; padding: 3px; border: 1px solid {i === selectedIndex ? 'blue' : '#ccc'}; background: none; width: 100%; text-align: left;"
          aria-pressed={i === selectedIndex}
          on:click={() => selectIndex(i)}
        >
          <img src={`http://localhost:5000/uploads/${img.name}`} alt={img.name} style="max-width: 100%; max-height: 60px;" />
          <div>{img.name}</div>
        </button>
      {/each}
    </div>
  {:else}
    <p>No hay imágenes para mostrar.</p>
  {/if}
</div>

<div style="margin-top: 2rem;">
  <button on:click={saveMetadata}>Guardar metadata</button>
  <button on:click={renameFiles}>Renombrar archivos físicamente</button>
</div>
