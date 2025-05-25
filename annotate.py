import os
import sys
import signal
from tkinter import Tk, Label, Text, END, messagebox
from tkinter import N, S, E, W
from PIL import Image, ImageTk, ImageOps

class ImageLabeler:
    def __init__(self, folder):
        self.folder = folder
        self.images = [f for f in os.listdir(folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))]
        self.images.sort()
        self.index = 0
        self.previous_text = ""

        if not self.images:
            print("[DEBUG] No images found. Exiting.")
            sys.exit(0)

        self.root = Tk()
        self.root.title("Image Labeler")

        self.image_label = Label(self.root)
        self.image_label.grid(row=0, column=0, columnspan=3, sticky=N+S+E+W)

        self.text_entry = Text(self.root, height=5, width=60, undo=True)
        self.text_entry.grid(row=1, column=0, columnspan=3, sticky=N+S+E+W)

        self.button_save = Label(self.root, text="[Save]", fg="white", bg="green", cursor="hand2", padx=10, pady=5)
        self.button_save.grid(row=2, column=0, sticky="ew", pady=5, padx=5)
        self.button_save.bind("<Button-1>", lambda e: self.save_and_next())

        self.copy_btn = Label(self.root, text="[Copy previous text]", fg="white", bg="gray", cursor="hand2", padx=10, pady=5)
        self.copy_btn.grid(row=2, column=1, sticky="ew", pady=5, padx=5)
        self.copy_btn.bind("<Button-1>", lambda e: self.copy_previous())

        self.info_label = Label(self.root, text="Enter text, Ctrl+S to save & next, Ctrl+C to exit", fg="blue")
        self.info_label.grid(row=2, column=2, sticky="ew", pady=5, padx=5)

        # Configure grid weights for resizing
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=0)
        self.root.grid_columnconfigure((0,1,2), weight=1)

        # Bind Ctrl+S to save and next
        self.text_entry.bind("<Control-s>", self.ctrl_s_save)
        # Bind Ctrl+C to exit gracefully
        self.text_entry.bind("<Control-c>", self.ctrl_c_exit)

        # Also catch window close (X) event
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.load_image()

        # Catch SIGINT (Ctrl+C in terminal)
        signal.signal(signal.SIGINT, self.signal_handler)

        self.root.mainloop()

    def load_image(self):
        if self.index >= len(self.images):
            messagebox.showinfo("End", "No more images in folder.")
            print("[DEBUG] No more images in folder, exiting.")
            self.root.quit()
            return

        image_path = os.path.join(self.folder, self.images[self.index])
        print(f"[DEBUG] Loading image {self.index+1}/{len(self.images)}: {image_path}")

        img = Image.open(image_path)
        img = ImageOps.exif_transpose(img)
        img.thumbnail((800, 600))

        self.photo = ImageTk.PhotoImage(img)
        self.image_label.config(image=self.photo)

        self.text_entry.delete("1.0", END)
        txt_file = os.path.splitext(image_path)[0] + ".txt"
        if os.path.exists(txt_file):
            with open(txt_file, "r", encoding="utf-8") as f:
                text = f.read()
            self.text_entry.insert(END, text)
            self.previous_text = text
            print(f"[DEBUG] Loaded existing text from {txt_file}")
        else:
            self.previous_text = ""

        self.text_entry.focus_set()  # <-- Fokus auf das Textfeld setzen

        # reset autocomplete state (optional, da autocomplete entfernt)
        self.autocomplete_active = False
        self.matches = []
        self.match_index = 0

    def save_and_next(self):
        image_path = os.path.join(self.folder, self.images[self.index])
        txt_file = os.path.splitext(image_path)[0] + ".txt"
        text = self.text_entry.get("1.0", END).strip()
        with open(txt_file, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"[DEBUG] Saved text to {txt_file}")
        self.previous_text = text
        self.index += 1
        self.load_image()

    def copy_previous(self):
        if self.previous_text:
            self.text_entry.delete("1.0", END)
            self.text_entry.insert(END, self.previous_text)
            print("[DEBUG] Copied previous text into input field.")
        else:
            print("[DEBUG] No previous text to copy.")

    def ctrl_s_save(self, event):
        print("[DEBUG] Ctrl+S pressed: saving and loading next image.")
        self.save_and_next()
        return "break"

    def ctrl_c_exit(self, event):
        print("[DEBUG] Ctrl+C pressed: exiting gracefully.")
        self.root.quit()
        return "break"

    def on_close(self):
        print("[DEBUG] Window closed by user.")
        self.root.quit()

    def signal_handler(self, sig, frame):
        print("\n[DEBUG] SIGINT received, exiting gracefully.")
        self.root.quit()

if __name__ == "__main__":
    folder_path = sys.argv[1] if len(sys.argv) > 1 else "."
    ImageLabeler(folder_path)
