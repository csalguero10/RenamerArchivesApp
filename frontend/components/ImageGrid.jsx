export default function ImageGrid({ images, setImages }) {
    const validateImage = (filename) => {
        fetch('/validate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                filename,
                validated: true,
                page_number: 1 // esto luego lo puedes hacer dinámico
            })
        }).then(() => {
            setImages(prev =>
                prev.map(img =>
                    img.filename === filename ? { ...img, validated: true } : img
                )
            );
        });
    };

    return (
        <div style={{ display: 'flex', flexWrap: 'wrap' }}>
            {images.map((img, i) => (
                <div key={i} style={{ margin: 10, border: '1px solid gray', padding: 5 }}>
                    <img src={`/${img.path}`} width="150" alt={img.filename} />
                    <p>{img.type}</p>
                    <button onClick={() => validateImage(img.filename)}>Validar</button>
                </div>
            ))}
        </div>
    );
}
