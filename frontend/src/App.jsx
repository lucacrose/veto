import React, { useState, useEffect, useRef, useCallback } from 'react';
import './App.css';

const API_BASE = 'http://localhost:8000';

function App() {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [filter, setFilter] = useState('none'); 
  
  const scrollContainerRef = useRef(null);
  const topRef = useRef(null);
  const isInitialLoad = useRef(true); // Track if this is the very first render

  const fetchMessages = useCallback(async (beforeTimestamp, isInitial = false) => {
    if (loading || (!hasMore && !isInitial)) return;
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
        const previousScrollHeight = container.scrollHeight;

        setMessages((prev) => isInitial ? data : [...prev, ...data]);

        if (!isInitial) {
          // Maintain scroll position when loading OLDER messages at the top
          requestAnimationFrame(() => {
            if (container) {
              container.scrollTop = container.scrollHeight - previousScrollHeight;
            }
          });
        }
      }
    } catch (error) {
      console.error("Fetch error:", error);
    } finally {
      setLoading(false);
    }
  }, [loading, hasMore, filter]);

  // Reset and fetch when filter changes
  useEffect(() => {
    isInitialLoad.current = true; // Reset initial load flag
    setMessages([]);
    setHasMore(true);
    fetchMessages(null, true);
  }, [filter]);

  // FORCE SCROLL TO BOTTOM ON INITIAL LOAD
  useEffect(() => {
    if (isInitialLoad.current && messages.length > 0) {
      const container = scrollContainerRef.current;
      if (container) {
        container.scrollTop = container.scrollHeight;
        isInitialLoad.current = false; // Turn off flag so it doesn't snap bottom again
      }
    }
  }, [messages]);

  // Observer for Infinite Scroll
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && !loading && hasMore && messages.length > 0) {
          const oldestMessage = messages[messages.length - 1];
          fetchMessages(oldestMessage[1]);
        }
      },
      { threshold: 0.1, rootMargin: '150px' }
    );

    if (topRef.current) observer.observe(topRef.current);
    return () => observer.disconnect();
  }, [messages, loading, hasMore, fetchMessages]);

  return (
    <div className="app-container">
      <div className="filter-bar">
        <span className="filter-label">Show:</span>
        <button className={`filter-btn ${filter === 'none' ? 'active' : ''}`} onClick={() => setFilter('none')}> All </button>
        <button className={`filter-btn ${filter === 'true' ? 'active' : ''}`} onClick={() => setFilter('true')}> Passed </button>
        <button className={`filter-btn ${filter === 'false' ? 'active' : ''}`} onClick={() => setFilter('false')}> Not Passed </button>
      </div>

      <div className="messages-wrapper" ref={scrollContainerRef}>
        {!hasMore ? (
          <div className="history-end">
            <div className="hashtag-icon">#</div>
            <h1>Beginning of History</h1>
            <p>No more messages to load.</p>
            <hr className="divider" />
          </div>
        ) : (
          <div ref={topRef} className="fetch-trigger">
            {loading && <div className="spinner"></div>}
          </div>
        )}

        {[...messages].reverse().map((msg, index) => {
          const isPassed = msg[3] === true;
          return (
            <div key={`${msg[1]}-${index}`} className={`message-item ${isPassed ? 'passed' : ''}`}>
              <div className="message-header">
                <span className="author">System</span>
                <span className="timestamp">
                  {new Date(msg[1] * 1000).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                </span>
                {isPassed && <span className="passed-badge">PASSED</span>}
              </div>
              <div className="message-content">{msg[0]}</div>
              {msg[2]?.length > 0 && (
                <div className="attachments">
                  {msg[2].map((file) => (
                    <img key={file} src={`${API_BASE}/media/${file}`} className="msg-img" loading="lazy" />
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default App;