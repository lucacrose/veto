import json
import plotly.graph_objects as go
import numpy as np
from pathlib import Path
from collections import Counter
import webbrowser
import os

# --- Configuration ---
directory = Path("backend/annotated")
output_html = "trade_analytics_chronological.html"

# --- 1. Setup ---
# Sorting by modification time (st_mtime) to ensure chronological order
json_files = [f for f in directory.rglob("*.json") if f.stat().st_size > 0]
json_files.sort(key=lambda x: os.path.getmtime(x))

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

# --- 2. Process Trades ---
valid_trade_count = 0
for file in json_files:
    try:
        with open(file, 'r') as f:
            data = json.load(f)
        
        current_trade_uniques = set()
        for side in ['incoming', 'outgoing']:
            items_list = data.get(side, {}).get('items', [])
            for item in items_list:
                iid = item.get('id')
                if iid is not None:
                    current_trade_uniques.add(iid)
        
        for iid in current_trade_uniques:
            running_item_counts[iid] += 1
            
        current_snapshot = Counter()
        for iid, count_at_this_time in running_item_counts.items():
            current_snapshot[get_bin(count_at_this_time)] += 1
            
        for label in milestone_labels:
            history[label].append(current_snapshot[label])
            
        valid_trade_count += 1
    except:
        continue

# --- 3. Plotting ---
if valid_trade_count > 0:
    fig = go.Figure()
    x_axis = list(range(1, valid_trade_count + 1))

    for label, color in zip(milestone_labels, milestone_colors):
        fig.add_trace(go.Scatter(
            x=x_axis, 
            y=history[label],
            mode='lines',
            line=dict(width=0.5, color="rgba(255,255,255,0.1)"),
            stackgroup='one', 
            name=label,
            fillcolor=color,
            hovertemplate='<b>%{y}</b> items<extra></extra>'
        ))

    fig.update_layout(
        title=dict(text="CHRONOLOGICAL ITEM DISCOVERY (BY FILE MODIFIED DATE)", font=dict(color="#85929e"), x=0.02),
        xaxis=dict(title="TRADES (Oldest to Newest)", gridcolor="#1a1a1a", zeroline=False),
        yaxis=dict(title="UNIQUE ITEMS DISCOVERED", gridcolor="#1a1a1a", zeroline=False),
        hovermode="x unified",
        template="plotly_dark",
        paper_bgcolor="#000000",
        plot_bgcolor="#000000",
        margin=dict(l=0, r=0, t=60, b=0),
        legend=dict(yanchor="top", y=0.98, xanchor="left", x=0.01, bgcolor="rgba(0,0,0,0.3)")
    )

    # --- HTML Export with CSS Fixes ---
    html_content = fig.to_html(full_html=True, include_plotlyjs='cdn', config={'displaylogo': False})
    css_fix = "<style>body { background-color: #000000 !important; margin: 0; padding: 0; overflow: hidden; }</style>"
    html_content = html_content.replace('</head>', f'{css_fix}</head>')

    with open(output_html, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    webbrowser.open(f"file://{Path(output_html).absolute()}")
    print(f"✅ Chronological Graph generated based on file history.")