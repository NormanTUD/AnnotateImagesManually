import os
import sys
from tkinter import Tk, Label, Entry, Button, Text, END, messagebox
from PIL import Image, ImageTk

class ImageLabeler:
    def __init__(self, folder):
        self.folder = folder
        self.images = [f for f in os.listdir(folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))]
        self.images.sort()
        self.index = 0
        self.previous_text = ""
        
        print(f"[DEBUG] Found {len(self.images)} images in '{folder}'")
        
        if not self.images:
            print("[DEBUG] No images found. Exiting.")
            sys.exit(0)
        
        self.root = Tk()
        self.root.title("Image Labeler")
        
        # Image display
        self.image_label = Label(self.root)
        self.image_label.pack()
        
        # Input field
        self.text_entry = Text(self.root, height=5, width=60)
        self.text_entry.pack()
        
        # Buttons
        self.save_btn = Button(self.root, text="Speichern", command=self.save_text)
        self.save_btn.pack(side="left", padx=10, pady=10)
        
        self.copy_btn = Button(self.root, text="Vorherigen Text übernehmen", command=self.copy_previous)
        self.copy_btn.pack(side="left", padx=10, pady=10)
        
        self.next_btn = Button(self.root, text="Nächstes Bild", command=self.next_image)
        self.next_btn.pack(side="left", padx=10, pady=10)
        
        self.load_image()
        
        self.root.mainloop()
        
    def load_image(self):
        if self.index >= len(self.images):
            print("[DEBUG] Keine Bilder mehr übrig.")
            messagebox.showinfo("Ende", "Keine Bilder mehr im Ordner.")
            self.root.quit()
            return
        
        image_path = os.path.join(self.folder, self.images[self.index])
        print(f"[DEBUG] Lade Bild {self.index+1}/{len(self.images)}: {image_path}")
        
        # Bild laden und skalieren
        img = Image.open(image_path)
        img.thumbnail((800, 600))  # max Größe
        
        self.photo = ImageTk.PhotoImage(img)
        self.image_label.config(image=self.photo)
        
        # Textfeld leeren
        self.text_entry.delete("1.0", END)
        
        # Wenn schon Textdatei existiert, laden
        txt_file = os.path.splitext(image_path)[0] + ".txt"
        if os.path.exists(txt_file):
            with open(txt_file, "r", encoding="utf-8") as f:
                text = f.read()
            print(f"[DEBUG] Lade existierenden Text aus {txt_file}")
            self.text_entry.insert(END, text)
        else:
            print("[DEBUG] Kein existierender Text gefunden.")
        
    def save_text(self):
        image_path = os.path.join(self.folder, self.images[self.index])
        txt_file = os.path.splitext(image_path)[0] + ".txt"
        text = self.text_entry.get("1.0", END).strip()
        with open(txt_file, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"[DEBUG] Text gespeichert in {txt_file}")
        self.previous_text = text
        
    def copy_previous(self):
        if self.previous_text:
            print("[DEBUG] Übernehme Text vom vorherigen Bild.")
            self.text_entry.delete("1.0", END)
            self.text_entry.insert(END, self.previous_text)
        else:
            print("[DEBUG] Kein vorheriger Text vorhanden.")
            
    def next_image(self):
        self.save_text()
        self.index += 1
        self.load_image()
        

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 image_labeler.py /path/to/image_folder")
        sys.exit(1)
    folder = sys.argv[1]
    if not os.path.isdir(folder):
        print(f"Error: '{folder}' is not a valid directory.")
        sys.exit(1)
    
    ImageLabeler(folder)
