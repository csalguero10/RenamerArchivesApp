export default function Tabs({ activeTab, setActiveTab }) {
    return (
        <div>
            <button onClick={() => setActiveTab('pendientes')}>Pendientes</button>
            <button onClick={() => setActiveTab('validadas')}>Validadas</button>
        </div>
    );
}
