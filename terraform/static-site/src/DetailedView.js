import React, {useState} from 'react';
import './App.css';

function DetailedView({item, onClose}) {
    const [showTranscript, setShowTranscript] = useState(false);

    const sentiments = {
        NEGATIVE: '😠', NEUTRAL: '😐', MIXED: '🤔', POSITIVE: '😊',
    };

    const sentimentToEmoji = sentiment => sentiments[sentiment] || null;

    const timelineEvents = [{sentiment: item.Sentiment0, label: 'Start', position: '10%'}, {
        sentiment: item.Sentiment1,
        label: 'Midpoint',
        position: '50%'
    }, {sentiment: item.Sentiment2, label: 'Resolution', position: '90%'},].filter(event => event.sentiment);

    const convertDateToISO = dateString => dateString
        .replace(/-/g, (match, offset) => (offset > 9) ? ':' : match)
        .replace(' ', 'T');

    return (<div className="detailed-view">
            <button onClick={onClose}>Close</button>
            <h2>{item.UniqueId}</h2>
            <p>Date and Time: {new Date(convertDateToISO(item.Date)).toLocaleString()}</p>
            <div className="timeline-container">
                <div className="timeline-line"></div>
                {timelineEvents.map((event, index) => (
                    <div key={index} className="timeline-event" style={{left: event.position}}>
                        <div className="timeline-sentiment">{event.sentiment}</div>
                        <div className="timeline-icon">{sentimentToEmoji(event.sentiment)}</div>
                        <div className="timeline-label">{event.label}</div>
                    </div>))}
            </div>
            <p>{item.Summary}</p>
            <button onClick={() => setShowTranscript(true)}>Full Transcript</button>
            {showTranscript && (<div className="transcript-window">
                    <h3>Full Transcript</h3>
                    {item.TranscriptionFull.split('\n').map((line, index) => {
                        const speakerClass = line.startsWith('Customer:') ? 'customer-line' : 'agent-line';
                        return (<p key={index} className={speakerClass}>{line}</p>);
                    })}
                    <button onClick={() => setShowTranscript(false)}>Close Transcript</button>
                </div>)}
        </div>);
}

export default DetailedView;
