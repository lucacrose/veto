import React, { useState, useEffect, useCallback, useRef } from 'react';
import './App.css';

const API_URL = 'http://localhost:8000';

function App() {
  const [currentTrade, setCurrentTrade] = useState(null);
  const [buffer, setBuffer] = useState([]);
  const [stats, setStats] = useState({ accepted: 0, rejected: 0, remaining: 0 });
  
  // The Mutex Lock: Prevents the "Infinite Request Loop"
  const isFetching = useRef(false);

  const syncStats = async () => {
    try {
      const res = await fetch(`${API_URL}/stats`);
      const data = await res.json();
      setStats(data);
    } catch (e) {
      console.error("Failed to fetch stats");
    }
  };

  const refillBuffer = useCallback(async () => {
    // Only fetch if we aren't already fetching and buffer isn't full
    if (isFetching.current || buffer.length >= 3) return;
    isFetching.current = true;

    try {
      // Exclude logic: Tell backend what we already have to avoid duplicates
      const exclude = buffer.map(t => t.filename);
      if (currentTrade) exclude.push(currentTrade.filename);
      
      const query = exclude.map(f => `exclude=${encodeURIComponent(f)}`).join('&');
      const res = await fetch(`${API_URL}/next?${query}`);
      
      if (res.ok) {
        const data = await res.json();
        if (data) setBuffer(prev => [...prev, data]);
      }
    } catch (e) {
      console.error("Buffer refill failed", e);
    } finally {
      isFetching.current = false;
    }
  }, [buffer, currentTrade]);

  // Initial load and monitoring
  useEffect(() => {
    syncStats();
    refillBuffer();
  }, [refillBuffer]);

  // Consumer: Pull from buffer when screen is empty
  useEffect(() => {
    if (!currentTrade && buffer.length > 0) {
      setCurrentTrade(buffer[0]);
      setBuffer(prev => prev.slice(1));
    }
  }, [currentTrade, buffer]);

  const handleAction = async (action) => {
    if (!currentTrade) return;
    const target = currentTrade;
    
    // Optimistic UI: Clear immediately so next item pops in
    setCurrentTrade(null);

    try {
      await fetch(`${API_URL}/action`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          filename: target.filename,
          message_index: target.message_index,
          action: action,
          metadata: target.metadata
        })
      });
      syncStats();
    } catch (e) {
      console.error("Action submission failed", e);
    }
  };

  // Keyboard Listeners
  useEffect(() => {
    const onKey = (e) => {
      if (e.key.toLowerCase() === 'a') handleAction('accept');
      if (e.key.toLowerCase() === 'd') handleAction('reject');
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [currentTrade]);

  if (!currentTrade && buffer.length === 0) {
    return <div className="full-center"><h1>Scanning Trade Queue...</h1></div>;
  }

  return (
    <div className="app-shell">
      <header className="status-bar">
        <div className="stat-pill">Processed: <b>{stats.accepted + stats.rejected}</b></div>
        <div className="stat-pill">Remaining: <b>{stats.remaining}</b></div>
        <div className="spacer" />
        <div className="controls-hint">
          <span className="key">A</span> Accept 
          <span className="key">D</span> Skip
        </div>
      </header>

      <main className="content-split">
        <section className="image-viewer">
          {currentTrade && (
            <img 
              src={`${API_URL}/media/${currentTrade.filename}`} 
              alt="Trade Proof" 
            />
          )}
        </section>

        <section className="data-inspector">
          {currentTrade ? (
            <TradeRender data={currentTrade.metadata} />
          ) : (
            <div className="loader">Preparing Metadata...</div>
          )}
        </section>
      </main>
    </div>
  );
}

const TradeRender = ({ data }) => {
  const Side = ({ title, info }) => {
    // Ensure exactly 4 slots are rendered
    const items = info.items || [];
    const slots = [...items, ...Array(Math.max(0, 4 - items.length)).fill(null)];

    return (
      <div className="trade-section">
        <div className="section-header">
          <h3>{title}</h3>
        </div>
        
        <div className="item-grid-1x4">
          {slots.map((item, i) => (
            <div key={i} className={`item-slot ${!item ? 'empty' : ''}`}>
              {item && (
                <>
                  <img 
                    src={`${API_URL}/thumbnails/${item.id}.png`} 
                    alt="" 
                    onError={(e) => { e.target.src = 'https://tr.rbxcdn.com/42px-placeholder.png'; }} 
                  />
                  <div className="item-label">
                    <span className="name">{item.name}</span>
                    <span className="id">{item.id}</span>
                  </div>
                </>
              )}
            </div>
          ))}
        </div>

        <div className={`robux-footer ${info.robux_value > 0 ? 'active' : 'inactive'}`}>
          <div className="robux-content">
            <span className="robux-icon">R$</span>
            <span className="robux-amount">
              {info.robux_value > 0 ? info.robux_value.toLocaleString() : '0'}
            </span>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="trade-stack">
      <Side title="Items You Gave" info={data.outgoing} />
      <div className="middle-divider"><span>RECEIVING</span></div>
      <Side title="Items You Received" info={data.incoming} />
    </div>
  );
};

export default App;