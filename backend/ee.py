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

print(f"Files to process: {len(files_to_process)}")

paths = [str(media / file.with_suffix("").name) for file in files_to_process]

# Track correct vs incorrect
correct_count = 0
failures = []

def json_diff(pred, truth, path=""):
    diffs = []
    if isinstance(pred, dict) and isinstance(truth, dict):
        for key in set(pred.keys()).union(truth.keys()):
            new_path = f"{path}.{key}" if path else key
            if key not in pred:
                diffs.append(f"Missing in predicted: {new_path} = {truth[key]}")
            elif key not in truth:
                diffs.append(f"Extra in predicted: {new_path} = {pred[key]}")
            else:
                diffs.extend(json_diff(pred[key], truth[key], new_path))
    elif isinstance(pred, list) and isinstance(truth, list):
        for i, (p_item, t_item) in enumerate(zip(pred, truth)):
            new_path = f"{path}[{i}]"
            diffs.extend(json_diff(p_item, t_item, new_path))
        # Handle extra items
        if len(pred) > len(truth):
            for i in range(len(truth), len(pred)):
                diffs.append(f"Extra in predicted: {path}[{i}] = {pred[i]}")
        elif len(truth) > len(pred):
            for i in range(len(pred), len(truth)):
                diffs.append(f"Missing in predicted: {path}[{i}] = {truth[i]}")
    else:
        if pred != truth:
            diffs.append(f"{path}: predicted={pred} | truth={truth}")
    return diffs

for file, path in zip(files_to_process, paths):
    model_output = proofreader.get_trade_data(path)
    with open(file, "r") as f:
        ground_truth = json.load(f)

    if model_output != ground_truth:
        failures.append({
            "file": str(file),
            "diff": json_diff(model_output, ground_truth)
        })

# Summary
total = len(files_to_process)
incorrect_count = total - correct_count
accuracy = correct_count / total * 100

print(f"Correct: {correct_count}")
print(f"Incorrect: {incorrect_count}")
print(f"Accuracy: {accuracy:.2f}%")
print("\n=== Failures ===")
for fail in failures:
    print(f"File: {fail['file']}")
    for line in fail['diff']:
        print("  ", line)
    print("-" * 50)
