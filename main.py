import tkinter as tk
from tkinter import messagebox
from view import View

class TorrentClient(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("TorrentClient")
        self.geometry("700x500")

        self['bg'] = '#E0E0E0'
        self.text_font = ("Segoe UI", 10)

        self.put_main_frames()
        self.protocol("WM_DELETE_WINDOW", self.on_window_close)

    def put_main_frames(self):
        self.LEFTframe = View.LEFTframe(self)
        self.LEFTframe.pack(side=tk.LEFT, fill=tk.Y)

        self.UPframe = View.UPframe(self)
        self.UPframe.pack(side=tk.LEFT, expand=1, fill=tk.BOTH)

    def on_window_close(self):
        choice = messagebox.askyesno("Quit", "Do you want to quit?")
        if choice:
            self.destroy()


if __name__ == '__main__':
    app = TorrentClient()
    app.mainloop()
