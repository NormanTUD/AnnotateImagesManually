import os
import sys
from tkinter import Tk, Label, Text, END, Listbox, Scrollbar, Frame, BOTH, VERTICAL
from tkinter import messagebox
from tkinter import NSEW, LEFT, RIGHT, Y
from PIL import Image, ImageTk

class ImageLabeler:
    def __init__(self, folder):
        self.folder = folder
        self.images = [f for f in os.listdir(folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))]
        self.images.sort()
        self.index = 0
        self.previous_text = ""
        self.suggestions = set()
        
        print(f"[DEBUG] Found {len(self.images)} images in '{folder}'")
        self.load_all_suggestions()
        
        if not self.images:
            print("[DEBUG] No images found. Exiting.")
            sys.exit(0)
        
        self.root = Tk()
        self.root.title("Image Labeler")
        
        # Image display
        self.image_label = Label(self.root)
        self.image_label.pack()
        
        # Frame für Text + Vorschläge
        self.text_frame = Frame(self.root)
        self.text_frame.pack(fill=BOTH, expand=True)
        
        # Textfeld
        self.text_entry = Text(self.text_frame, height=5, width=60)
        self.text_entry.pack(side=LEFT, fill=BOTH, expand=True)
        self.text_entry.bind("<KeyRelease>", self.on_keyrelease)
        self.text_entry.bind("<Down>", self.move_down)
        self.text_entry.bind("<Up>", self.move_up)
        self.text_entry.bind("<Return>", self.on_enter)
        self.text_entry.bind("<Escape>", self.hide_suggestions)
        
        # Scrollbar für Listbox
        self.scrollbar = Scrollbar(self.text_frame, orient=VERTICAL)
        
        # Listbox für Vorschläge
        self.listbox = Listbox(self.text_frame, height=5, yscrollcommand=self.scrollbar.set)
        self.listbox.pack_forget()
        self.listbox.bind("<<ListboxSelect>>", self.on_listbox_select)
        self.listbox.bind("<Return>", self.on_listbox_enter)
        self.listbox.bind("<Escape>", self.hide_suggestions)
        self.scrollbar.config(command=self.listbox.yview)
        
        # Buttons
        self.save_btn = Label(self.root, text="Drücke Enter oder Klick 'Speichern' um zu speichern und zum nächsten Bild", fg="blue")
        self.save_btn.pack(pady=2)
        
        self.button_save = Label(self.root, text="[Speichern]", fg="white", bg="green", cursor="hand2")
        self.button_save.pack(pady=5)
        self.button_save.bind("<Button-1>", lambda e: self.save_and_next())
        
        self.copy_btn = Label(self.root, text="[Vorherigen Text übernehmen]", fg="white", bg="gray", cursor="hand2")
        self.copy_btn.pack(pady=5)
        self.copy_btn.bind("<Button-1>", lambda e: self.copy_previous())
        
        self.load_image()
        
        self.root.mainloop()
    
    def load_all_suggestions(self):
        print("[DEBUG] Lade alle bisherigen Texte für Vorschläge...")
        for f in os.listdir(self.folder):
            if f.lower().endswith(".txt"):
                path = os.path.join(self.folder, f)
                try:
                    with open(path, "r", encoding="utf-8") as file:
                        text = file.read()
                    words = set(word.lower() for word in text.split())
                    self.suggestions.update(words)
                except Exception as e:
                    print(f"[DEBUG] Fehler beim Laden von {f}: {e}")
        print(f"[DEBUG] Insgesamt {len(self.suggestions)} Vorschlagswörter geladen.")
    
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
        img.thumbnail((800, 600))
        
        self.photo = ImageTk.PhotoImage(img)
        self.image_label.config(image=self.photo)
        
        # Textfeld leeren und ggf. bestehenden Text laden
        self.text_entry.delete("1.0", END)
        txt_file = os.path.splitext(image_path)[0] + ".txt"
        if os.path.exists(txt_file):
            with open(txt_file, "r", encoding="utf-8") as f:
                text = f.read()
            print(f"[DEBUG] Lade existierenden Text aus {txt_file}")
            self.text_entry.insert(END, text)
            self.previous_text = text
        else:
            print("[DEBUG] Kein existierender Text gefunden.")
            self.previous_text = ""
        
        self.hide_suggestions()
    
    def save_and_next(self):
        image_path = os.path.join(self.folder, self.images[self.index])
        txt_file = os.path.splitext(image_path)[0] + ".txt"
        text = self.text_entry.get("1.0", END).strip()
        with open(txt_file, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"[DEBUG] Text gespeichert in {txt_file}")
        self.previous_text = text
        self.index += 1
        self.load_image()
    
    def copy_previous(self):
        if self.previous_text:
            print("[DEBUG] Übernehme Text vom vorherigen Bild.")
            self.text_entry.delete("1.0", END)
            self.text_entry.insert(END, self.previous_text)
        else:
            print("[DEBUG] Kein vorheriger Text vorhanden.")
    
    # --- Vorschlagsfunktion ---
    def on_keyrelease(self, event):
        if event.keysym in ("Up", "Down", "Return", "Escape"):
            return  # für diese Tasten keine Vorschläge öffnen
        
        cursor_index = self.text_entry.index("insert")
        line, col = map(int, cursor_index.split("."))
        current_line = self.text_entry.get(f"{line}.0", f"{line}.end")
        prefix = ""
        # Finde das Wort, das gerade getippt wird, am Cursor vorwärts (links)
        i = col - 1
        while i >= 0 and current_line[i].isalpha():
            i -= 1
        prefix = current_line[i+1:col].lower()
        
        if not prefix:
            self.hide_suggestions()
            return
        
        print(f"[DEBUG] Suche Vorschläge für Prefix '{prefix}'")
        matches = sorted(w for w in self.suggestions if w.startswith(prefix))
        if not matches:
            self.hide_suggestions()
            return
        
        self.show_suggestions(matches)
    
    def show_suggestions(self, suggestions):
        # Listbox füllen und anzeigen
        self.listbox.delete(0, END)
        for w in suggestions:
            self.listbox.insert(END, w)
        if not self.listbox.winfo_ismapped():
            self.listbox.pack(side=RIGHT, fill=Y)
            self.scrollbar.pack(side=RIGHT, fill=Y)
        self.listbox.selection_set(0)
    
    def hide_suggestions(self, event=None):
        self.listbox.pack_forget()
        self.scrollbar.pack_forget()
    
    def move_down(self, event):
        if self.listbox.winfo_ismapped():
            current = self.listbox.curselection()
            if not current:
                idx = 0
            else:
                idx = current[0]
                if idx < self.listbox.size() - 1:
                    idx += 1
            self.listbox.selection_clear(0, END)
            self.listbox.selection_set(idx)
            self.listbox.activate(idx)
            return "break"
    
    def move_up(self, event):
        if self.listbox.winfo_ismapped():
            current = self.listbox.curselection()
            if not current:
                idx = 0
            else:
                idx = current[0]
                if idx > 0:
                    idx -= 1
            self.listbox.selection_clear(0, END)
            self.listbox.selection_set(idx)
            self.listbox.activate(idx)
            return "break"
    
    def on_enter(self, event):
        if self.listbox.winfo_ismapped():
            self.insert_suggestion()
            return "break"  # Enter nicht als neue Zeile einfügen
        else:
            # Enter speichert und geht weiter
            self.save_and_next()
            return "break"
    
    def on_listbox_enter(self, event):
        self.insert_suggestion()
        return "break"
    
    def on_listbox_select(self, event):
        # Kein automatisches einfügen beim Mausklick - warte auf Enter
        pass
    
    def insert_suggestion(self):
        sel = self.listbox.curselection()
        if not sel:
            return
        word = self.listbox.get(sel[0])
        
        # Wort unter Cursor ersetzen
        cursor_index = self.text_entry.index("insert")
        line, col = map(int, cursor_index.split("."))
        current_line = self.text_entry.get(f"{line}.0", f"{line}.end")
        
        i = col - 1
        while i >= 0 and current_line[i].isalpha():
            i -= 1
        start = i+1
        
        # Ersetze Wort
        self.text_entry.delete(f"{line}.{start}", cursor_index)
        self.text_entry.insert(f"{line}.{start}", word)
        
        # Cursor ans Ende des Wortes setzen
        self.text_entry.mark_set("insert", f"{line}.{start + len(word)}")
        self.hide_suggestions()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 image_labeler.py /path/to/image_folder")
        sys.exit(1)
    folder = sys.argv[1]
    if not os.path.isdir(folder):
        print(f"Error: '{folder}' is not a valid directory.")
        sys.exit(1)
    
    ImageLabeler(folder)
