from PIL import Image, ImageTk
from pathlib import Path
import tkinter as tk

# ---- Find skipped files ----
directory = Path("backend/annotated")
MEDIA_DIR = Path("backend/media")

skipped_files = []

for file in directory.rglob("*.json"):
    if file.stat().st_size == 0:
        skipped_files.append(file)

skipped_files.sort()

# ---- GUI reviewer ----
index = 0
img_tk = None

def load_image():
    global img_tk

    if index >= len(skipped_files):
        label.config(text="All done 🎉")
        panel.config(image="")
        return

    skipped = skipped_files[index]

    # Strip .skipped
    image_path = (MEDIA_DIR / skipped.name).with_suffix("")

    if not image_path.exists():
        label.config(text=f"Missing image:\n{image_path}")
        panel.config(image="")
        return

    img = Image.open(image_path)
    img.thumbnail((900, 900))
    img_tk = ImageTk.PhotoImage(img)

    panel.config(image=img_tk)
    label.config(text=f"{index + 1}/{len(skipped_files)}\n{image_path.name}")

def write_and_next():
    global index
    skipped = skipped_files[index]

    # WRITE TO SOURCE .skipped FILE
    skipped.write_text("ood\n")  # <-- customize if needed

    index += 1
    load_image()

def skip_and_next():
    global index
    index += 1
    load_image()

# ---- UI ----
root = tk.Tk()
root.title("Skipped Image Reviewer")

label = tk.Label(root, text="", wraplength=900)
label.pack(pady=5)

panel = tk.Label(root)
panel.pack()

btn_frame = tk.Frame(root)
btn_frame.pack(pady=10)

write_btn = tk.Button(btn_frame, text="Write", width=20, command=write_and_next)
write_btn.pack(side=tk.LEFT, padx=5)

skip_btn = tk.Button(btn_frame, text="Skip", width=20, command=skip_and_next)
skip_btn.pack(side=tk.LEFT, padx=5)

# Optional keyboard shortcuts
root.bind("<Right>", lambda e: skip_and_next())
root.bind("<Left>", lambda e: write_and_next())
root.bind("<Return>", lambda e: write_and_next())

load_image()
root.mainloop()
