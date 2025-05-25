import os
import sys
import argparse
from tkinter import Tk, Label, Text, Button, END, messagebox, Frame
from PIL import Image, ImageTk, ImageOps

class ImageTextEditor:
    def __init__(self, root, folder, only_unannotated, max_width, max_height, exit_on_last, verbose):
        self.root = root
        self.folder = folder
        self.only_unannotated = only_unannotated
        self.max_width = max_width
        self.max_height = max_height
        self.exit_on_last = exit_on_last
        self.verbose = verbose

        self.images = self.load_images()
        self.index = 0
        self.previous_text = ""

        self.root.title("Image Text Editor")

        self.image_label = Label(root)
        self.image_label.pack()

        self.text_entry = Text(root, height=10)
        self.text_entry.pack()

        btn_frame = Frame(root)
        btn_frame.pack()

        self.prev_button = Button(btn_frame, text="Previous", command=self.previous_image)
        self.prev_button.pack(side="left", padx=5, pady=5)

        self.next_button = Button(btn_frame, text="Next", command=self.next_image)
        self.next_button.pack(side="left", padx=5, pady=5)

        self.save_button = Button(btn_frame, text="Save", command=self.save_and_next)
        self.save_button.pack(side="left", padx=5, pady=5)

        # Status bar unten mit Tastenkombis
        self.status_label = Label(root, text="Shortcuts: Ctrl+S = Save & Next | Left/Right = Prev/Next | Esc = Exit", bd=1, relief="sunken", anchor="w")
        self.status_label.pack(fill="x", side="bottom")

        # Tastaturbindung für Ctrl+S
        self.root.bind("<Control-s>", self.ctrl_s_pressed)
        self.root.bind("<Left>", lambda e: self.previous_image())
        self.root.bind("<Right>", lambda e: self.next_image())
        self.root.bind("<Escape>", lambda e: self.exit_program())

        self.load_image()

    def log(self, msg):
        if self.verbose:
            print(f"[DEBUG] {msg}")

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
            img.thumbnail((self.max_width, self.max_height))
            self.photo = ImageTk.PhotoImage(img)
            self.image_label.config(image=self.photo)
            self.log("Image loaded and displayed.")
        except Exception as e:
            self.log(f"Error loading image '{image_path}': {e}")
            messagebox.showerror("Error", f"Failed to load image: {e}")
            return

        self.text_entry.delete("1.0", END)
        txt_file = os.path.splitext(image_path)[0] + ".txt"
        if os.path.exists(txt_file):
            with open(txt_file, "r", encoding="utf-8") as f:
                text = f.read()
            self.text_entry.insert(END, text)
            self.previous_text = text
            self.log(f"Loaded existing annotation from {txt_file}.")
        else:
            self.previous_text = ""
            self.log("No existing annotation found, text field cleared.")

        self.text_entry.focus_set()
        self.log("Focus set to text entry.")

    def save_text(self):
        if self.index >= len(self.images):
            self.log("Save called but no images left.")
            return

        image_path = os.path.join(self.folder, self.images[self.index])
        txt_file = os.path.splitext(image_path)[0] + ".txt"
        current_text = self.text_entry.get("1.0", END).strip()

        if current_text == self.previous_text:
            self.log("Text unchanged, skipping save.")
            return

        try:
            with open(txt_file, "w", encoding="utf-8") as f:
                f.write(current_text)
            self.previous_text = current_text
            self.log(f"Saved annotation to {txt_file}.")
        except Exception as e:
            self.log(f"Error saving annotation '{txt_file}': {e}")
            messagebox.showerror("Error", f"Failed to save annotation: {e}")

    def save_and_next(self):
        self.log("Save & Next triggered.")
        self.save_text()
        if self.index < len(self.images) - 1:
            self.index += 1
            self.log(f"Moving to next image (index {self.index}).")
            self.load_image()
        else:
            messagebox.showinfo("End", "No more images.")
            self.log("Reached last image on Save & Next.")

    def next_image(self):
        self.log("Next image requested.")
        self.save_text()
        if self.index < len(self.images) - 1:
            self.index += 1
            self.log(f"Loading next image (index {self.index}).")
            self.load_image()
        else:
            messagebox.showinfo("End", "This is the last image.")
            self.log("Already at last image.")

    def previous_image(self):
        self.log("Previous image requested.")
        self.save_text()
        if self.index > 0:
            self.index -= 1
            self.log(f"Loading previous image (index {self.index}).")
            self.load_image()
        else:
            messagebox.showinfo("Start", "This is the first image.")
            self.log("Already at first image.")

    def ctrl_s_pressed(self, event):
        self.log("Ctrl+S pressed.")
        self.save_and_next()
        return "break"  # verhindert Defaultverhalten

    def exit_program(self):
        self.log("Exit requested (Escape key).")
        self.root.quit()

def main():
    parser = argparse.ArgumentParser(description="Simple Image Text Annotation Tool")
    parser.add_argument("folder", default=os.getcwd(),
                        help="Folder containing images (default: current directory)")
    parser.add_argument("--only_unannotated", "-u", action="store_true",
                        help="Only show images without existing .txt annotation files")
    parser.add_argument("--max_width", type=int, default=800,
                        help="Max width of images (default: 800)")
    parser.add_argument("--max_height", type=int, default=600,
                        help="Max height of images (default: 600)")
    parser.add_argument("--exit_on_last", action="store_true",
                        help="Exit the program when the last image is reached")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Show debug messages")

    args = parser.parse_args()

    root = Tk()
    app = ImageTextEditor(root,
                          folder=args.folder,
                          only_unannotated=args.only_unannotated,
                          max_width=args.max_width,
                          max_height=args.max_height,
                          exit_on_last=args.exit_on_last,
                          verbose=args.verbose)
    root.mainloop()

if __name__ == "__main__":
    main()
