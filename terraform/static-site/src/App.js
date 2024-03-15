import React, {useEffect, useState} from 'react';
import './App.css';
import SummaryCard from './SummaryCard';
import DetailedView from './DetailedView';

function App() {
    const [data, setData] = useState([]);
    const [activeItem, setActiveItem] = useState(null);

    useEffect(() => {
        fetch('https://callcenter.brewsentry.com/data')
            .then(response => response.json())
            .then(data => setData(data.Items))
            .catch(error => console.error('Error fetching data:', error));
    }, []);

    return (
        <div className="App">
            <header className="App-header">
                <h1>Call Center Analytics</h1>
                <div className="summary-container">
                    {data.map((item, index) => (
                        <SummaryCard
                            key={index}
                            item={item}
                            onClick={() => setActiveItem(item)}
                        />
                    ))}
                </div>
                {activeItem && <DetailedView item={activeItem} onClose={() => setActiveItem(null)}/>}
            </header>
        </div>
    );
}

export default App;
