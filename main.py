import tkinter as tk
from src.app import XTermApp

if __name__ == "__main__":
    root = tk.Tk()
    app = XTermApp(root)
    root.mainloop()