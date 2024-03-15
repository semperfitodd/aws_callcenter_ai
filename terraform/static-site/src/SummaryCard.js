import React from 'react';
import './App.css';

function SummaryCard({item, onClick}) {
    const convertDateToISO = dateString => dateString
        .replace(/-/g, (match, offset) => (offset > 9) ? ':' : match)
        .replace(' ', 'T');

    const sentiment = item.Sentiment2.toLowerCase();
    return (
        <div className={`summary-card ${sentiment}`} onClick={onClick}>
            <h2>{item.UniqueId}</h2>
            <p>{new Date(convertDateToISO(item.Date)).toLocaleString()}</p>
        </div>
    );
}

export default SummaryCard;
