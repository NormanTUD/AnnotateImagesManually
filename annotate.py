import os
import sys
import argparse
from tkinter import Tk, Label, Text, Button, Frame, Scrollbar, END, messagebox, BOTH, RIGHT, Y, LEFT, X, SUNKEN
from tkinter.font import Font
from PIL import Image, ImageTk, ImageOps

import signal

def signal_handler(sig, frame):
    print('You pressed Ctrl+C! Exiting gracefully...')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)


class ImageTextEditor:
    def __init__(self, root, folder, only_unannotated, max_width, max_height, exit_on_last, verbose,
                 start_index, light_mode):
        self.root = root
        self.folder = folder
        self.only_unannotated = only_unannotated
        self.max_width = max_width
        self.max_height = max_height
        self.exit_on_last = exit_on_last
        self.verbose = verbose
        self.light_mode = light_mode

        self.images = self.load_images()

        # Startindex bestimmen
        if start_index is not None and 0 <= start_index < len(self.images):
            self.index = start_index
            self.log(f"Starting at user-defined index {self.index}")
        else:
            # Automatisch erstes unannotiertes Bild, falls only_unannotated nicht gesetzt
            if not only_unannotated:
                self.index = self.find_first_unannotated()
                self.log(f"Starting at first unannotated image index {self.index}")
            else:
                self.index = 0
                self.log(f"Starting at index 0 (only_unannotated set)")

        self.previous_text = ""
        self.prev_image_text = None  # Für Button "Text aus vorherigem Bild einfügen"

        self.setup_ui()
        self.apply_theme()
        self.load_image()

        self.set_fullscreen()

    def log(self, msg):
        if self.verbose:
            print(f"[DEBUG] {msg}")

    def find_first_unannotated(self):
        for i, img in enumerate(self.images):
            txt_file = os.path.splitext(os.path.join(self.folder, img))[0] + ".txt"
            if not os.path.exists(txt_file):
                return i
        return 0

    def load_images(self):
        exts = [".jpg", ".jpeg", ".png", ".bmp", ".gif"]
        files = [f for f in os.listdir(self.folder) if os.path.splitext(f)[1].lower() in exts]

        if self.only_unannotated:
            filtered = []
            for f in files:
                txt_file = os.path.splitext(os.path.join(self.folder, f))[0] + ".txt"
                if not os.path.exists(txt_file):
                    filtered.append(f)
            self.log(f"Filtered only unannotated images, found {len(filtered)} images.")
            return sorted(filtered)

        self.log(f"Loaded {len(files)} images from folder '{self.folder}'.")
        return sorted(files)

    def setup_ui(self):
        self.root.title("Image Text Annotation Tool")

        # UI-Elemente aufbauen
        main_frame = Frame(self.root)
        main_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)

        # Linke Seite (Bild + Vorschaubild)
        left_frame = Frame(main_frame)
        left_frame.pack(side=LEFT, fill=BOTH, expand=False)

        self.image_label = Label(left_frame, bd=2, relief="groove")
        self.image_label.pack(padx=5, pady=5, fill=BOTH, expand=True)

        self.preview_label = Label(left_frame, bd=1, relief="ridge")
        self.preview_label.pack(padx=5, pady=5, fill=None)

        # Rechte Seite (Textfeld + Buttons)
        right_frame = Frame(main_frame)
        right_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=(20,0))

        text_label = Label(right_frame, text="Annotation:", font=Font(size=12, weight="bold"))
        text_label.pack(anchor="w", pady=(0,5))

        text_frame = Frame(right_frame)
        text_frame.pack(fill=BOTH, expand=True)

        self.text_entry = Text(text_frame, height=20, wrap="word", font=("Segoe UI", 11), bd=2, relief="sunken")
        self.text_entry.pack(side=LEFT, fill=BOTH, expand=True)

        scroll = Scrollbar(text_frame, command=self.text_entry.yview)
        scroll.pack(side=RIGHT, fill=Y)
        self.text_entry.config(yscrollcommand=scroll.set)

        btn_frame = Frame(right_frame)
        btn_frame.pack(fill=X, pady=10)

        self.prev_button = Button(btn_frame, text="← Previous", width=12, command=self.previous_image)
        self.prev_button.pack(side=LEFT, padx=5)

        self.next_button = Button(btn_frame, text="Next →", width=12, command=self.next_image)
        self.next_button.pack(side=LEFT, padx=5)

        self.save_button = Button(btn_frame, text="💾 Save & Next", width=15, command=self.save_and_next)
        self.save_button.pack(side=LEFT, padx=5)

        self.insert_prev_text_button = Button(btn_frame, text="Insert Prev Image Text", width=20, command=self.insert_prev_text)
        self.insert_prev_text_button.pack(side=LEFT, padx=10)
        self.insert_prev_text_button.config(state="disabled")

        self.status_label = Label(self.root, text="Shortcuts: Ctrl+S = Save & Next | ←/→ = Prev/Next | Esc = Exit", 
                                  bd=1, relief=SUNKEN, anchor="w", font=Font(size=9))
        self.status_label.pack(fill=X, side="bottom")

        self.root.bind("<Control-s>", self.ctrl_s_pressed)
        self.root.bind("<Left>", lambda e: self.previous_image())
        self.root.bind("<Right>", lambda e: self.next_image())
        self.root.bind("<Escape>", lambda e: self.exit_program())

    def apply_theme(self):
        if self.light_mode:
            bg_color = "#f0f0f0"
            fg_color = "#000000"
            entry_bg = "white"
            entry_fg = "black"
            btn_bg = "#e0e0e0"
            btn_fg = "black"
            status_bg = "#d0d0d0"
        else:
            # Dark Mode Farben
            bg_color = "#222222"
            fg_color = "#eeeeee"
            entry_bg = "#333333"
            entry_fg = "#ffffff"
            btn_bg = "#444444"
            btn_fg = "#ffffff"
            status_bg = "#111111"

        self.root.configure(bg=bg_color)

        for widget in self.root.winfo_children():
            # Frames nur bg, kein fg
            if isinstance(widget, Frame):
                widget.configure(bg=bg_color)
            # Labels bekommen bg + fg
            elif isinstance(widget, Label):
                widget.configure(bg=bg_color, fg=fg_color)

        # Bildrahmen
        self.image_label.configure(bg="#000000")
        self.preview_label.configure(bg="#000000")

        # Textfeld
        self.text_entry.configure(bg=entry_bg, fg=entry_fg, insertbackground=entry_fg)

        # Buttons
        for btn in [self.prev_button, self.next_button, self.save_button, self.insert_prev_text_button]:
            btn.configure(bg=btn_bg, fg=btn_fg, activebackground="#666666" if not self.light_mode else "#cccccc",
                          activeforeground=btn_fg, relief="raised", bd=2)

        # Status Bar
        self.status_label.configure(bg=status_bg, fg=fg_color)

    def set_fullscreen(self):
        # Plattformabhängig maximieren
        if sys.platform == "win32":
            self.root.state("zoomed")
        elif sys.platform == "darwin":  # macOS
            self.root.attributes("-zoomed", True)
        else:  # Linux & andere
            self.root.attributes("-zoomed", True)

    def load_image(self):
        if self.index >= len(self.images):
            messagebox.showinfo("End", "No more images in folder.")
            self.log(f"Reached end of image list at index {self.index}.")
            if self.exit_on_last:
                self.log("Exiting program as exit_on_last is set.")
                self.root.quit()
            return

        image_path = os.path.join(self.folder, self.images[self.index])
        self.log(f"Loading image {self.index + 1} / {len(self.images)}: {image_path}")

        try:
            img = Image.open(image_path)
            img = ImageOps.exif_transpose(img)

            img_for_display = img.copy()
            img_for_display.thumbnail((self.max_width, self.max_height))
            self.photo = ImageTk.PhotoImage(img_for_display)
            self.image_label.config(image=self.photo)
            self.image_label.image = self.photo

            preview_img = img.copy()
            preview_img.thumbnail((120, 90))
            self.preview_photo = ImageTk.PhotoImage(preview_img)
            self.preview_label.config(image=self.preview_photo)
            self.preview_label.image = self.preview_photo

            self.log("Image and preview loaded and displayed.")
        except Exception as e:
            self.log(f"Error loading image '{image_path}': {e}")
            messagebox.showerror("Error", f"Failed to load image: {e}")
            return

        self.text_entry.delete(1.0, END)

        # Annotation laden, wenn vorhanden
        txt_path = os.path.splitext(image_path)[0] + ".txt"
        if os.path.exists(txt_path):
            with open(txt_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.text_entry.insert(END, content)
            self.previous_text = content
            self.insert_prev_text_button.config(state="normal")
        else:
            self.previous_text = ""
            self.insert_prev_text_button.config(state="disabled")

        self.root.title(f"Image Text Annotation Tool — {self.images[self.index]} ({self.index + 1}/{len(self.images)})")

        self.text_entry.focus_set()

    def save_text(self):
        image_path = os.path.join(self.folder, self.images[self.index])
        txt_path = os.path.splitext(image_path)[0] + ".txt"
        text = self.text_entry.get(1.0, END).strip()

        if text != self.previous_text:
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(text)
            self.log(f"Annotation saved to {txt_path}")
            self.previous_text = text
        else:
            self.log("No changes to save.")

    def save_and_next(self):
        self.save_text()
        self.next_image()

    def previous_image(self):
        if self.index > 0:
            self.prev_image_text = self.previous_text
            self.index -= 1
            self.load_image()
        else:
            messagebox.showinfo("Info", "Already at first image.")

    def next_image(self):
        if self.index < len(self.images) - 1:
            self.prev_image_text = self.previous_text
            self.index += 1
            self.load_image()
        else:
            messagebox.showinfo("Info", "Already at last image.")
            if self.exit_on_last:
                self.log("Exiting program as exit_on_last is set.")
                self.root.quit()

    def insert_prev_text(self):
        if self.prev_image_text:
            self.text_entry.insert(END, "\n\n" + self.prev_image_text)
        else:
            messagebox.showinfo("Info", "No previous image text available.")

    def ctrl_s_pressed(self, event):
        self.save_and_next()
        return "break"

    def exit_program(self):
        if messagebox.askokcancel("Exit", "Do you really want to exit? Unsaved changes will be lost."):
            self.root.quit()

def main():
    parser = argparse.ArgumentParser(description="Image Annotation Tool with dark mode, fullscreen and start on unannotated image")
    parser.add_argument("folder", help="Folder with images to annotate")
    parser.add_argument("--only_unannotated", action="store_true", help="Only show images without .txt annotation files")
    parser.add_argument("--max_width", type=int, default=1920, help="Max image width for display")
    parser.add_argument("--max_height", type=int, default=1080, help="Max image height for display")
    parser.add_argument("--exit_on_last", action="store_true", help="Exit program after last image")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")
    parser.add_argument("--start_index", type=int, help="Start at this image index (0-based)")
    parser.add_argument("--light_mode", action="store_true", help="Use light mode theme (default: dark mode)")
    args = parser.parse_args()

    if not os.path.isdir(args.folder):
        print(f"Error: Folder '{args.folder}' does not exist or is not a directory.")
        sys.exit(1)

    root = Tk()

    def poll():
        root.after(100, poll)  # 100 ms alle 0.1 Sekunden prüfen

    poll()

    app = ImageTextEditor(root, args.folder, args.only_unannotated, args.max_width, args.max_height,
                          args.exit_on_last, args.verbose, args.start_index, args.light_mode)
    root.mainloop()

if __name__ == "__main__":
    main()
