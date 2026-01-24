import proofreader
from pathlib import Path
import time
import numpy as np
import json

def median_p95(latencies):
    arr = np.array(latencies)
    median = np.median(arr)
    p95 = np.percentile(arr, 95)
    return median, p95

directory = Path("backend/annotated")
media = Path("backend/media")

files_to_process = []

for file in directory.rglob("*"):
    if file.is_file():
        # Skip certain JSON by name
        if file.suffix == ".json" and file.name != "455b8e6e-b627-4418-8619-030056fa2bd7.png.json":
            # Only include non-empty JSONs
            if file.stat().st_size != 0:
                files_to_process.append(file)
        # Include .skipped if empty (not already written)
        elif file.suffix == ".skipped" and file.stat().st_size == 0:
            files_to_process.append(file)

print(len(files_to_process))

paths = []
times = []
#(np.float64(0.13941979999981413), np.float64(0.233303030001116))
#np.float64(0.034562549999463954), np.float64(0.067776705000324
#(np.float64(0.036774549999790906), np.float64(0.0733961049989375))*!

for file in files_to_process:
    paths.append(str(media / file.with_suffix("").name))

if False:
    for i in range(10):
        s = time.perf_counter()
        for path in paths:
            data = proofreader.get_trade_data(path)
        print(i, time.perf_counter()-s)

    for i in range(50):
        for path in paths:
            s = time.perf_counter()
            data = proofreader.get_trade_data(path)
            times.append(time.perf_counter() - s)

    print(median_p95(times))

g = 0
n = 0

for path in paths:
    data = proofreader.get_trade_data(path)

    with open(directory / f"{Path(path).name}.json", "r") as f:
        if f.read() == json.dumps(data, indent=2):
            g += 1
        else:
            n += 1

print(g, n)

#442, 58