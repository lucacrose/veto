import React, { useState, useEffect, useRef, useCallback } from 'react';
import './App.css';

const API_BASE = 'http://localhost:8000';

function App() {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [filter, setFilter] = useState('none');
  const [parsingId, setParsingId] = useState(null);
  
  // Analysis Focus State
  const [activeTrade, setActiveTrade] = useState(null);
  const [confirming, setConfirming] = useState(false);
  const [error, setError] = useState(null);

  const scrollContainerRef = useRef(null);
  const topRef = useRef(null);
  const isInitialLoad = useRef(true);
  const isFetching = useRef(false);

  const fetchMessages = useCallback(async (beforeTimestamp, isInitial = false) => {
    if (isFetching.current || (!hasMore && !isInitial)) return;
    
    isFetching.current = true;
    setLoading(true);

    try {
      let url = `${API_BASE}/messages?limit=50`;
      if (beforeTimestamp) url += `&before=${beforeTimestamp}`;
      if (filter !== 'none') url += `&passed=${filter}`;

      const response = await fetch(url);
      const data = await response.json();

      if (!data || data.length === 0) {
        setHasMore(false);
      } else {
        const container = scrollContainerRef.current;
        const prevHeight = container.scrollHeight;
        
        setMessages((prev) => isInitial ? data : [...prev, ...data]);

        if (!isInitial) {
          requestAnimationFrame(() => {
            if (container) container.scrollTop = container.scrollHeight - prevHeight;
          });
        }
      }
    } catch (e) {
      console.error("Fetch error:", e);
    } finally {
      setLoading(false);
      isFetching.current = false;
    }
  }, [filter, hasMore]);

  useEffect(() => {
    isInitialLoad.current = true;
    setHasMore(true);
    setMessages([]);
    fetchMessages(null, true);
  }, [filter, fetchMessages]);

  useEffect(() => {
    if (isInitialLoad.current && messages.length > 0) {
      const container = scrollContainerRef.current;
      if (container) {
        container.scrollTop = container.scrollHeight;
        isInitialLoad.current = false;
      }
    }
  }, [messages]);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && !isFetching.current && hasMore && messages.length >= 20) {
          const oldestMessage = messages[messages.length - 1];
          fetchMessages(oldestMessage[1]);
        }
      },
      { threshold: 0.1, rootMargin: '200px' }
    );
    if (topRef.current) observer.observe(topRef.current);
    return () => observer.disconnect();
  }, [messages, hasMore, fetchMessages]);

  // UI Actions
  const handleAiParse = async (msg) => {
    setParsingId(msg[1]);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/autofill/${msg[1]}`);
      const data = await response.json();
      setActiveTrade({ 
        ...data, 
        timestamp: msg[1],
        imageUrl: msg[2]?.[0] ? `${API_BASE}/media/${msg[2][0]}` : null 
      });
    } catch (e) {
      alert("Error parsing trade data.");
    } finally {
      setParsingId(null);
    }
  };

  const handleConfirm = async () => {
    setConfirming(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/confirm`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ timestamp: activeTrade.timestamp })
      });

      if (response.ok) {
        setActiveTrade(null); // Close on success
      } else {
        const errData = await response.json();
        setError(errData.detail || "Server error: Confirmation failed.");
      }
    } catch (e) {
      setError("Network error: Could not connect to server.");
    } finally {
      setConfirming(false);
    }
  };

  return (
    <div className="app-container">
      <div className="filter-bar">
        <span className="filter-label">Filter:</span>
        <button className={`filter-btn ${filter === 'none' ? 'active' : ''}`} onClick={() => setFilter('none')}>All</button>
        <button className={`filter-btn ${filter === 'true' ? 'active' : ''}`} onClick={() => setFilter('true')}>Passed</button>
        <button className={`filter-btn ${filter === 'false' ? 'active' : ''}`} onClick={() => setFilter('false')}>Not Passed</button>
      </div>

      <div className="main-content">
        <div className={`messages-wrapper ${activeTrade ? 'blur' : ''}`} ref={scrollContainerRef}>
          <div ref={topRef} className="fetch-trigger">
            {loading && <div className="spinner" />}
          </div>

          {[...messages].reverse().map((msg) => (
            <div key={msg[1]} className={`message-item ${msg[3] ? 'passed' : ''}`}>
              <div className="message-header">
                <span className="author">System</span>
                <span className="timestamp">{new Date(msg[1] * 1000).toLocaleString()}</span>
                <button className="ai-btn" disabled={parsingId === msg[1]} onClick={() => handleAiParse(msg)}>
                  {parsingId === msg[1] ? '...' : 'AI Parse'}
                </button>
              </div>
              <div className="message-content">{msg[0]}</div>
              {msg[2]?.length > 0 && (
                <div className="attachments">
                  {msg[2].map(f => (
                    <div key={f} className="attachment-item">
                      <img src={`${API_BASE}/media/${f}`} className="msg-img" loading="lazy" alt="" />
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>

        {activeTrade && (
          <div className="analysis-overlay">
            <div className="analysis-image-pane">
              {activeTrade.imageUrl && <img src={activeTrade.imageUrl} alt="Source" />}
            </div>

            <div className="analysis-panel-pane">
              <div className="sidebar-header">
                <h3>Trade Analysis</h3>
                <button className="close-btn" onClick={() => setActiveTrade(null)}>×</button>
              </div>
              <div className="sidebar-meta">
                <span className="meta-label">Captured</span>
                <span className="meta-date-value">{activeTrade.date}</span>
              </div>
              <div className="sidebar-scroll">
                <div className="side-section">
                  <span className="section-label">Giving</span>
                  <div className="trade-item-row">
                    {activeTrade.trade.outgoing.items.map(item => (
                      <div key={item.id} className="trade-item-card">
                        <div className="thumb-container">
                          <img src={`${API_BASE}/thumbnail/${item.id}.png`} alt="" />
                        </div>
                        <div className="item-name-tag">{item.name}</div>
                      </div>
                    ))}
                  </div>
                  {activeTrade.trade.outgoing.robux_value > 0 && (
                    <div className="side-robux-footer">R$ {activeTrade.trade.outgoing.robux_value.toLocaleString()}</div>
                  )}
                </div>
                <div className="side-section">
                  <span className="section-label">Receiving</span>
                  <div className="trade-item-row">
                    {activeTrade.trade.incoming.items.map(item => (
                      <div key={item.id} className="trade-item-card">
                        <div className="thumb-container">
                          <img src={`${API_BASE}/thumbnail/${item.id}.png`} alt="" />
                        </div>
                        <div className="item-name-tag">{item.name}</div>
                      </div>
                    ))}
                  </div>
                  {activeTrade.trade.incoming.robux_value > 0 && (
                    <div className="side-robux-footer">R$ {activeTrade.trade.incoming.robux_value.toLocaleString()}</div>
                  )}
                </div>
              </div>
              {error && <div className="error-banner">{error}</div>}
              <div className="sidebar-actions">
                <button className="accept-btn" disabled={confirming} onClick={handleConfirm}>
                  {confirming ? "Processing..." : "Confirm Trade"}
                </button>
                <button className="deny-btn" onClick={() => setActiveTrade(null)}>Dismiss</button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
