import os
import sys
from tkinter import Tk, Label, Text, END, INSERT, messagebox
from tkinter import N, S, E, W
from PIL import Image, ImageTk, ImageOps

class ImageLabeler:
    def __init__(self, folder):
        self.folder = folder
        self.images = [f for f in os.listdir(folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))]
        self.images.sort()
        self.index = 0
        self.previous_text = ""

        self.suggestions = self.load_suggestions_from_current_folder()

        if not self.images:
            print("[DEBUG] No images found. Exiting.")
            sys.exit(0)

        self.root = Tk()
        self.root.title("Image Labeler")

        self.image_label = Label(self.root)
        self.image_label.grid(row=0, column=0, columnspan=3, sticky=N+S+E+W)

        self.text_entry = Text(self.root, height=5, width=60, undo=True)
        self.text_entry.grid(row=1, column=0, columnspan=3, sticky=N+S+E+W)
        self.text_entry.bind("<Key>", self.on_keypress)
        self.text_entry.bind("<KeyRelease>", self.on_keyrelease)
        self.text_entry.bind("<Tab>", self.on_tab)
        self.text_entry.bind("<Up>", self.on_up)
        self.text_entry.bind("<Down>", self.on_down)
        self.text_entry.bind("<Return>", self.on_return)
        self.text_entry.bind("<Control-s>", self.ctrl_s_save)

        self.button_save = Label(self.root, text="[Save]", fg="white", bg="green", cursor="hand2", padx=10, pady=5)
        self.button_save.grid(row=2, column=0, sticky="ew", pady=5, padx=5)
        self.button_save.bind("<Button-1>", lambda e: self.save_and_next())

        self.copy_btn = Label(self.root, text="[Copy previous text]", fg="white", bg="gray", cursor="hand2", padx=10, pady=5)
        self.copy_btn.grid(row=2, column=1, sticky="ew", pady=5, padx=5)
        self.copy_btn.bind("<Button-1>", lambda e: self.copy_previous())

        self.info_label = Label(self.root, text="Enter text, use Tab/Up/Down to autocomplete, Ctrl+S to save & next", fg="blue")
        self.info_label.grid(row=2, column=2, sticky="ew", pady=5, padx=5)

        # Autocomplete state
        self.matches = []
        self.match_index = 0
        self.autocomplete_active = False

        # Configure grid weights for resizing
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=0)
        self.root.grid_columnconfigure((0,1,2), weight=1)

        self.load_image()
        self.root.mainloop()

    def get_word_bounds(self):
        # aktuelle Cursorposition (Index als string z.B. "1.7")
        cursor_pos = self.text_entry.index("insert")

        # Anfang der Zeile, um Rückwärts zu suchen
        line_start = cursor_pos.split('.')[0] + ".0"

        # Text von Zeilenanfang bis Cursor
        text_before_cursor = self.text_entry.get(line_start, cursor_pos)

        # Finde Anfang des aktuellen Wortes (letztes Leerzeichen o. Zeilenanfang)
        import re
        matches = list(re.finditer(r'\b\w+$', text_before_cursor))
        if matches:
            word_start_offset = matches[-1].start()
        else:
            word_start_offset = len(text_before_cursor)  # kein Wort gefunden, nur Cursor

        # Berechne word_start als Text-Index
        word_start = f"{line_start.split('.')[0]}.{word_start_offset}"
        return word_start, cursor_pos

    def load_suggestions_from_current_folder(self):
        suggestions = set()
        for f in os.listdir(self.folder):
            if f.lower().endswith(".txt"):
                path = os.path.join(self.folder, f)
                try:
                    with open(path, "r", encoding="utf-8") as file:
                        text = file.read()
                    words = set(word.lower() for word in text.split())
                    suggestions.update(words)
                except Exception as e:
                    print(f"[DEBUG] Error loading {f}: {e}")
        print(f"[DEBUG] Loaded {len(suggestions)} suggestions from current folder")
        return suggestions

    def load_image(self):
        if self.index >= len(self.images):
            messagebox.showinfo("End", "No more images in folder.")
            print("[DEBUG] No more images in folder, exiting.")
            self.root.quit()
            return

        image_path = os.path.join(self.folder, self.images[self.index])
        print(f"[DEBUG] Loading image {self.index+1}/{len(self.images)}: {image_path}")

        img = Image.open(image_path)
        # Korrekte Rotation aus EXIF
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

    # --- Autocomplete ---
    def on_keyrelease(self, event):
        if event.keysym in ("Up", "Down", "Return", "Tab", "Control_L", "Control_R", "Shift_L", "Shift_R", "Alt_L", "Alt_R"):
            return

        cursor_index = self.text_entry.index("insert")
        line, col = map(int, cursor_index.split("."))
        line_text = self.text_entry.get(f"{line}.0", f"{line}.end")

        # Suche Wortanfang links vom Cursor (nur alphabetische Zeichen)
        i = col - 1
        while i >= 0 and line_text[i].isalpha():
            i -= 1
        start = i + 1
        prefix = line_text[start:col].lower()

        if not prefix:
            self.autocomplete_active = False
            self.matches = []
            self.text_entry.tag_remove("autocomplete", "1.0", END)
            return

        self.matches = sorted(w for w in self.suggestions if w.startswith(prefix))
        if not self.matches:
            self.autocomplete_active = False
            self.text_entry.tag_remove("autocomplete", "1.0", END)
            return

        self.match_index = 0
        self.autocomplete_active = True
        self._autocomplete_replace(start, col)

    def _autocomplete_replace(self, start_index, end_index):
        # Nimm den Vorschlag aus deinem state (z.B. self.current_suggestion)
        suggestion = self.current_suggestion if hasattr(self, "current_suggestion") else ""
        if not suggestion:
            return

        # Ersetze den Text zwischen start_index und end_index mit dem Vorschlag
        self.text_entry.delete(start_index, end_index)
        self.text_entry.insert(start_index, suggestion)

        # Entferne Highlight
        self.text_entry.tag_remove("autocomplete", "1.0", "end")
        self.autocomplete_active = False

        # Setze Cursor ans Ende des eingefügten Vorschlags
        new_pos = self.text_entry.index(f"{start_index}+{len(suggestion)}c")
        self.text_entry.mark_set("insert", new_pos)

    def on_tab(self, event):
        if not self.autocomplete_active or not self.matches:
            return
        self.match_index = (self.match_index + 1) % len(self.matches)
        cursor_index = self.text_entry.index("insert")
        line, col = map(int, cursor_index.split("."))
        line_text = self.text_entry.get(f"{line}.0", f"{line}.end")
        i = col - 1
        while i >= 0 and line_text[i].isalpha():
            i -= 1
        start = i + 1
        self._autocomplete_replace(start, col)
        return "break"

    def on_up(self, event):
        if not self.autocomplete_active or not self.matches:
            return
        self.match_index = (self.match_index - 1) % len(self.matches)
        cursor_index = self.text_entry.index("insert")
        line, col = map(int, cursor_index.split("."))
        line_text = self.text_entry.get(f"{line}.0", f"{line}.end")
        i = col - 1
        while i >= 0 and line_text[i].isalpha():
            i -= 1
        start = i + 1
        self._autocomplete_replace(start, col)
        return "break"

    def on_keypress(self, event):
        if self.autocomplete_active:
            if event.keysym in ("Tab", "Right"):
                word_start, cursor_pos = self.get_word_bounds()
                self._autocomplete_replace(word_start, cursor_pos)
                return "break"
            elif len(event.char) == 1 and event.char.isprintable():
                self.text_entry.tag_remove("autocomplete", "1.0", "end")
                self.autocomplete_active = False
        if event.keysym == "s" and (event.state & 0x4):  # Ctrl+S
            self._save_and_next()
            return "break"

    def on_down(self, event):
        return self.on_tab(event)

    def on_return(self, event):
        if self.autocomplete_active:
            self.text_entry.tag_remove("autocomplete", "1.0", END)
            # Cursor ans Ende des Wortes setzen (nach dem Vorschlag)
            cursor_index = self.text_entry.index("insert")
            line, col = map(int, cursor_index.split("."))
            line_text = self.text_entry.get(f"{line}.0", f"{line}.end")
            i = col - 1
            while i < len(line_text) and line_text[i].isalpha():
                i += 1
            new_pos = f"{line}.{i}"
            self.text_entry.mark_set("insert", new_pos)
            self.autocomplete_active = False
            return "break"  # Verhindert Zeilenumbruch
        else:
            # Wenn kein Autocomplete aktiv, dann Save + next beim Enter
            self.save_and_next()
            return "break"

if __name__ == "__main__":
    folder_path = sys.argv[1] if len(sys.argv) > 1 else "."
    ImageLabeler(folder_path)
