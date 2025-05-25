import os
import sys
import argparse
from tkinter import Tk, Label, Text, Button, END, messagebox
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

        self.prev_button = Button(root, text="Previous", command=self.previous_image)
        self.prev_button.pack(side="left")

        self.next_button = Button(root, text="Next", command=self.next_image)
        self.next_button.pack(side="right")

        self.save_button = Button(root, text="Save", command=self.save_text)
        self.save_button.pack()

        self.load_image()

    def log(self, msg):
        if self.verbose:
            print(msg)

    def load_images(self):
        exts = [".jpg", ".jpeg", ".png", ".bmp", ".gif"]
        files = [f for f in os.listdir(self.folder) if os.path.splitext(f)[1].lower() in exts]

        if self.only_unannotated:
            filtered = []
            for f in files:
                txt_file = os.path.splitext(os.path.join(self.folder, f))[0] + ".txt"
                if not os.path.exists(txt_file):
                    filtered.append(f)
            self.log(f"[DEBUG] Only unannotated images selected, {len(filtered)} found.")
            return sorted(filtered)

        self.log(f"[DEBUG] Loaded {len(files)} images from folder {self.folder}")
        return sorted(files)

    def load_image(self):
        if self.index >= len(self.images):
            messagebox.showinfo("End", "No more images in folder.")
            self.log("[DEBUG] No more images in folder.")
            if self.exit_on_last:
                self.root.quit()
            return

        image_path = os.path.join(self.folder, self.images[self.index])
        self.log(f"[DEBUG] Loading image {self.index+1}/{len(self.images)}: {image_path}")

        img = Image.open(image_path)
        img = ImageOps.exif_transpose(img)
        img.thumbnail((self.max_width, self.max_height))

        self.photo = ImageTk.PhotoImage(img)
        self.image_label.config(image=self.photo)

        self.text_entry.delete("1.0", END)
        txt_file = os.path.splitext(image_path)[0] + ".txt"
        if os.path.exists(txt_file):
            with open(txt_file, "r", encoding="utf-8") as f:
                text = f.read()
            self.text_entry.insert(END, text)
            self.previous_text = text
            self.log(f"[DEBUG] Loaded existing text from {txt_file}")
        else:
            self.previous_text = ""

        self.text_entry.focus_set()

    def save_text(self):
        if self.index >= len(self.images):
            return

        image_path = os.path.join(self.folder, self.images[self.index])
        txt_file = os.path.splitext(image_path)[0] + ".txt"
        current_text = self.text_entry.get("1.0", END).strip()

        if current_text == self.previous_text:
            self.log("[DEBUG] Text unchanged, not saving.")
            return

        with open(txt_file, "w", encoding="utf-8") as f:
            f.write(current_text)
        self.previous_text = current_text
        self.log(f"[DEBUG] Saved text to {txt_file}")

    def next_image(self):
        self.save_text()
        if self.index < len(self.images) - 1:
            self.index += 1
            self.load_image()
        else:
            messagebox.showinfo("End", "No more images.")
            self.log("[DEBUG] Reached last image.")

    def previous_image(self):
        self.save_text()
        if self.index > 0:
            self.index -= 1
            self.load_image()
        else:
            messagebox.showinfo("Start", "This is the first image.")
            self.log("[DEBUG] At first image.")

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
