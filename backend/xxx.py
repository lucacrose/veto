import json
import plotly.graph_objects as go
from pathlib import Path
from collections import Counter
from tqdm import tqdm  # Progress bar library
import proofreader 

# --- Setup Paths ---
BUFFERS_DIR = Path("backend/buffers")
MEDIA_DIR = Path("backend/media")

def generate_live_memory_graph():
    # 1. Load Messages
    messages = []
    if BUFFERS_DIR.exists():
        buffer_files = sorted(BUFFERS_DIR.glob("*.json"), key=lambda p: int(p.stem) if p.stem.isdigit() else 0)
        for file_path in buffer_files:
            with open(file_path, "r") as f:
                messages += json.load(f)

    if not messages:
        print("No messages found in buffers.")
        return

    # 2. Data Structures
    running_item_counts = Counter()
    milestone_labels = ["Seen 1x", "Seen 2-5x", "Seen 6-20x", "Seen 21-100x", "Seen 101+x"]
    milestone_colors = ["#2c3e50", "#34495e", "#5d6d7e", "#85929e", "#aeb6bf"]
    history = {label: [] for label in milestone_labels}

    def get_bin(count):
        if count == 1: return "Seen 1x"
        if 2 <= count <= 5: return "Seen 2-5x"
        if 6 <= count <= 20: return "Seen 6-20x"
        if 21 <= count <= 100: return "Seen 21-100x"
        return "Seen 101+x"

    valid_trades_processed = 0

    # 3. Process with Progress Bar
    # tqdm wraps the list and prints a live bar to the console
    print("\n🚀 Starting On-the-Fly CV Analysis...\n")
    for msg in tqdm(messages, desc="Analyzing Trades", unit="trade"):
        if not msg[2]: continue 
        
        filename = msg[2][0]
        img_path = MEDIA_DIR / filename
        
        if not img_path.exists(): continue

        try:
            # Memory-only CV call
            trade_data = proofreader.get_trade_data(str(img_path))
            
            current_trade_uniques = set()
            for side in ['incoming', 'outgoing']:
                items = trade_data.get(side, {}).get('items', [])
                for item in items:
                    iid = item.get('id')
                    if iid: current_trade_uniques.add(iid)
            
            for iid in current_trade_uniques:
                running_item_counts[iid] += 1
            
            snapshot = Counter()
            for iid, count in running_item_counts.items():
                snapshot[get_bin(count)] += 1
            
            for label in milestone_labels:
                history[label].append(snapshot[label])
                
            valid_trades_processed += 1
            
        except Exception:
            continue

    if valid_trades_processed == 0:
        print("\n❌ No valid trade data extracted.")
        return

    # 4. Construct Graph
    fig = go.Figure()
    x_axis = list(range(1, valid_trades_processed + 1))

    for label, color in zip(milestone_labels, milestone_colors):
        fig.add_trace(go.Scatter(
            x=x_axis, y=history[label],
            mode='lines',
            line=dict(width=0.5, color="rgba(255,255,255,0.1)"),
            stackgroup='one', 
            name=label,
            fillcolor=color,
            hovertemplate='<b>%{y}</b> items<extra></extra>'
        ))

    fig.update_layout(
        title=dict(text="LIVE BUFFER DISCOVERY DYNAMICS", font=dict(color="#85929e"), x=0.02),
        xaxis=dict(title="TRADES FROM BUFFER", gridcolor="#1a1a1a", zeroline=False),
        yaxis=dict(title="UNIQUE ITEMS", gridcolor="#1a1a1a", zeroline=False),
        hovermode="x unified",
        template="plotly_dark",
        paper_bgcolor="#000000",
        plot_bgcolor="#000000",
        margin=dict(l=0, r=0, t=60, b=0),
        legend=dict(yanchor="top", y=0.98, xanchor="left", x=0.01, bgcolor="rgba(0,0,0,0.3)")
    )

    print("\n✅ Analysis Complete. Launching Interactive Graph...")
    fig.show(config={'displaylogo': False})

if __name__ == "__main__":
    generate_live_memory_graph()