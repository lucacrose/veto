import { useState, useEffect, useCallback } from 'react'
import './App.css'

function App() {
  const [currentData, setCurrentData] = useState(null);
  const [nextData, setNextData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isProcessing, setIsProcessing] = useState(false); // The "Lock"

  const getSingleItem = async () => {
    try {
      const res = await fetch('http://localhost:8000/next');
      if (!res.ok) return null;
      return await res.json();
    } catch (err) { return null; }
  };

  const handleDecision = useCallback(async (choice) => {
    if (isProcessing || !currentData) return;

    setIsProcessing(true); // Lock inputs
    
    // Get the filename from the current data
    const fileName = currentData.message[2];

    try {
      // 1. Send the POST request to your API
      const response = await fetch(`http://localhost:8000/tag/${fileName}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(currentData.data),
      });

      if (!response.ok) {
        throw new Error('Failed to save decision to the server');
      }

      console.log(`Decision "${choice}" saved for ${fileName}`);

      // 2. Move to next item and refill buffer
      if (nextData) {
        setCurrentData(nextData);
        setNextData(null);
        const backup = await getSingleItem();
        setNextData(backup);
      } else {
        const fresh = await getSingleItem();
        setCurrentData(fresh);
        const backup = await getSingleItem();
        setNextData(backup);
      }
    } catch (err) {
      console.error("API Error:", err);
      alert("Error saving decision. Please check backend connection.");
    } finally {
      setIsProcessing(false); // Unlock
    }
  }, [currentData, nextData, isProcessing]);

  // Keybinds with Lock Check
  useEffect(() => {
    const handleKeyDown = (event) => {
      if (isProcessing) return; // Ignore keys if processing
      
      const key = event.key.toLowerCase();
      if (key === 'a') handleDecision('accept');
      if (key === 'd') handleDecision('decline');
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleDecision, isProcessing]);

  // Initial Load
  useEffect(() => {
    const init = async () => {
      const first = await getSingleItem();
      const second = await getSingleItem();
      setCurrentData(first);
      setNextData(second);
      setLoading(false);
    };
    init();
  }, []);

  if (loading) return <div className="loading">Connecting...</div>;
  if (!currentData) return <div className="loading">All trades processed!</div>;

  return (
    <div className={`container ${isProcessing ? 'processing' : ''}`}>
      <div className="media-section">
        <img 
          src={`http://localhost:8000/media/${currentData.message[2]}`} 
          alt="Trade" 
          className="main-image"
        />
      </div>

      <div className="data-section">
        <div className="trade-panel">
          <TradeSide title="Outgoing" sideData={currentData.data.outgoing} />
          <hr className="divider" />
          <TradeSide title="Incoming" sideData={currentData.data.incoming} />
        </div>

        <div className="button-group">
          <button 
            className="btn accept" 
            onClick={() => handleDecision('accept')}
            disabled={isProcessing}
          >
            {isProcessing ? "..." : "Accept (A)"}
          </button>
          <button 
            className="btn decline" 
            onClick={() => handleDecision('decline')}
            disabled={isProcessing}
          >
            {isProcessing ? "..." : "Decline (D)"}
          </button>
        </div>
      </div>

      {/* Background Preload Tag */}
      {nextData && (
        <img src={`http://localhost:8000/media/${nextData.message[2]}`} style={{ display: 'none' }} />
      )}
    </div>
  )
}

function TradeSide({ title, sideData }) {
  const items = (sideData?.items || []).filter(item => item.name);
  const robux = sideData?.robux_value || 0;

  return (
    <div className="side-container">
      <h4 className="side-title">{title}</h4>
      <div className="item-grid">
        {items.map((item, idx) => (
          <div key={idx} className="item-box">
            <div className="item-image-container">
              {/* Replace item.image_url with the actual key from your JSON */}
              <img 
                src={"http://localhost:8000/thumbnail/" + item.id + ".png"} 
                alt={item.name} 
                className="item-photo"
              />
            </div>
            <div className="item-details">
              <span className="item-name">{item.name}</span>
            </div>
          </div>
        ))}
      </div>
      {robux > 0 && (
        <div className="robux-line">
           <span className="rbx-icon">R$</span> {robux.toLocaleString()}
        </div>
      )}
    </div>
  );
}

export default App;