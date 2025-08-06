import React, { useEffect, useState } from 'react';
import ImageGrid from './components/ImageGrid';
import Tabs from './components/Tabs';

function App() {
    const [images, setImages] = useState([]);
    const [activeTab, setActiveTab] = useState('pendientes');

    useEffect(() => {
        fetch('/images')
            .then(res => res.json())
            .then(data => setImages(data));
    }, []);

    const filtered = images.filter(img => {
        if (activeTab === 'validadas') return img.validated;
        return !img.validated;
    });

    return (
        <div>
            <h1>Renominador de Páginas</h1>
            <Tabs activeTab={activeTab} setActiveTab={setActiveTab} />
            <ImageGrid images={filtered} setImages={setImages} />
        </div>
    );
}

export default App;
