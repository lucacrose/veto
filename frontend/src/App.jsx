import { useState, useEffect, useCallback } from 'react'
import './App.css'

function App() {
  const [currentData, setCurrentData] = useState(null);
  const [nextData, setNextData] = useState(null);
  const [loading, setLoading] = useState(true);

  const getSingleItem = async () => {
    try {
      const res = await fetch('http://localhost:8000/next');
      if (!res.ok) return null;
      return await res.json();
    } catch (err) { return null; }
  };

  // Logic to handle the decision and advance
  const handleDecision = useCallback(async (choice) => {
    if (!currentData) return;

    console.log(`Decision for ${currentData.message[0]}: ${choice}`);

    // Optional: Send the decision to your backend
    /*
    fetch('http://localhost:8000/decide', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id: currentData.message[1], decision: choice })
    });
    */

    // Advance to preloaded data
    if (nextData) {
      setCurrentData(nextData);
      setNextData(null);
      // Refill the buffer
      const backup = await getSingleItem();
      setNextData(backup);
    } else {
      setCurrentData(null);
    }
  }, [currentData, nextData]);

  // Keybind Listener
  useEffect(() => {
    const handleKeyDown = (event) => {
      if (event.key.toLowerCase() === 'a') {
        handleDecision('accept');
      } else if (event.key.toLowerCase() === 'd') {
        handleDecision('decline');
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleDecision]);

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

  if (loading) return <div className="loading">Loading...</div>;
  if (!currentData) return <div className="loading">Queue Empty.</div>;

  return (
    <div className="container">
      <div className="media-section">
        <img 
          src={`http://localhost:8000/media/${currentData.message[2]}`} 
          alt="Trade" 
          className="main-image"
        />
      </div>

      <div className="data-section">
        <div className="trade-content">
          <TradeSide title="Outgoing" sideData={currentData.data.outgoing} />
          <hr style={{ border: '0.5px solid #333', margin: '20px 0' }} />
          <TradeSide title="Incoming" sideData={currentData.data.incoming} />
        </div>

        {/* Button group at the bottom of the sidebar */}
        <div className="button-group" style={{ marginTop: 'auto', paddingTop: '20px' }}>
          <button className="btn accept" onClick={() => handleDecision('accept')}>
            Accept (A)
          </button>
          <button className="btn decline" onClick={() => handleDecision('decline')}>
            Decline (D)
          </button>
        </div>
      </div>

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