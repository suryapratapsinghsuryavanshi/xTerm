"""
Main Application GUI Controller.
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import stat

# Local imports
from .ssh_backend import SSHBackend
from .terminal import TerminalWidget
from .utils import format_bytes

class XTermApp:
    def __init__(self, root):
        self.root = root
        self.root.title("xTerm - Modular")
        self.root.geometry("1250x850")

        self.backend = SSHBackend()
        
        self._setup_ui()
        self._start_animations()

    def _setup_ui(self):
        # 1. Top Bar
        self._create_top_bar()
        
        # 2. Split Pane
        self.paned_window = tk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 3. Left Pane (SFTP)
        self._create_sftp_pane()
        
        # 4. Right Pane (Terminal)
        frame_term = tk.Frame(self.paned_window, bg="black")
        self.paned_window.add(frame_term)
        
        self.terminal = TerminalWidget(frame_term)
        self.terminal.pack(fill=tk.BOTH, expand=True)
        self.terminal.on_input_callback = self.backend.send_command
        
        # Hook into terminal resize to update backend PTY
        original_resize = self.terminal._calculate_dimensions
        def resize_wrapper():
            dims = original_resize()
            if dims and self.backend.is_connected:
                self.backend.resize_pty(dims[0], dims[1])
        self.terminal._calculate_dimensions = resize_wrapper

    def _create_top_bar(self):
        frame = tk.LabelFrame(self.root, text="Connection", padx=5, pady=5)
        frame.pack(fill=tk.X, padx=10, pady=5)

        # Host
        tk.Label(frame, text="Host:").pack(side=tk.LEFT)
        self.entry_host = tk.Entry(frame, width=15)
        self.entry_host.pack(side=tk.LEFT, padx=5)
        self.entry_host.insert(0, "192.168.1.X")

        # User
        tk.Label(frame, text="User:").pack(side=tk.LEFT)
        self.entry_user = tk.Entry(frame, width=10)
        self.entry_user.pack(side=tk.LEFT, padx=5)
        self.entry_user.insert(0, "ubuntu")

        # Pass/Key
        tk.Label(frame, text="Password/Key:").pack(side=tk.LEFT)
        self.entry_pass = tk.Entry(frame, show="*", width=10)
        self.entry_pass.pack(side=tk.LEFT, padx=5)
        
        self.entry_key = tk.Entry(frame, width=20)
        self.entry_key.pack(side=tk.LEFT, padx=5)
        tk.Button(frame, text="...", command=self._browse_key, width=2).pack(side=tk.LEFT)

        # Connect Button
        self.btn_connect = tk.Button(
            frame, text="CONNECT", bg="#28a745", fg="black", 
            font=("Arial", 9, "bold"), command=self._connect
        )
        self.btn_connect.pack(side=tk.LEFT, padx=15)

    def _create_sftp_pane(self):
        left_frame = tk.Frame(self.paned_window)
        self.paned_window.add(left_frame, width=320)
        
        # Buttons
        btn_frame = tk.Frame(left_frame, pady=5)
        btn_frame.pack(fill=tk.X)
        
        self.btn_upload = tk.Button(btn_frame, text="⬆ Upload", state=tk.DISABLED, command=self._upload)
        self.btn_upload.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        
        self.btn_download = tk.Button(btn_frame, text="⬇ Download", state=tk.DISABLED, command=self._download)
        self.btn_download.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

        self.btn_refresh = tk.Button(btn_frame, text="↻", state=tk.DISABLED, command=self._refresh_files)
        self.btn_refresh.pack(side=tk.LEFT, padx=2)
        
        # Path Label
        self.lbl_path = tk.Label(left_frame, text="/", anchor="w", bg="#ddd", font=("Arial", 8))
        self.lbl_path.pack(fill=tk.X)

        # Treeview
        self.file_tree = ttk.Treeview(left_frame, columns=("size",), selectmode="browse")
        self.file_tree.heading("#0", text="Name")
        self.file_tree.heading("size", text="Size")
        self.file_tree.column("#0", width=180)
        self.file_tree.column("size", width=60, anchor="e")
        self.file_tree.pack(fill=tk.BOTH, expand=True)
        
        self.file_tree.bind("<Double-1>", self._on_double_click_file)

    # --- Logic ---

    def _browse_key(self):
        f = filedialog.askopenfilename()
        if f:
            self.entry_key.delete(0, tk.END)
            self.entry_key.insert(0, f)

    def _connect(self):
        host = self.entry_host.get()
        user = self.entry_user.get()
        key = self.entry_key.get()
        pwd = self.entry_pass.get()
        
        threading.Thread(target=self._connect_thread, args=(host, user, key, pwd)).start()

    def _connect_thread(self, host, user, key, pwd):
        try:
            self.backend.connect(host, user, key, pwd, self.terminal.feed)
            
            # Update UI on main thread
            self.root.after(0, self._enable_interaction)
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Connection Error", str(e)))

    def _enable_interaction(self):
        self.btn_connect.config(text="CONNECTED", state=tk.DISABLED)
        self.btn_upload.config(state=tk.NORMAL)
        self.btn_download.config(state=tk.NORMAL)
        self.btn_refresh.config(state=tk.NORMAL)
        self.terminal.focus_set()
        self._refresh_files()

    def _refresh_files(self):
        self.lbl_path.config(text=self.backend.current_remote_path)
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)

        if self.backend.current_remote_path != "/":
            self.file_tree.insert("", tk.END, text="..", values=("DIR",))

        files = self.backend.list_files()
        for f in files:
            is_dir = stat.S_ISDIR(f.st_mode)
            size = "<DIR>" if is_dir else format_bytes(f.st_size)
            icon = "📁 " if is_dir else "📄 "
            self.file_tree.insert(
                "", tk.END, text=icon + f.filename, values=(size,), 
                tags=('dir' if is_dir else 'file',)
            )

    def _on_double_click_file(self, event):
        item_id = self.file_tree.selection()[0]
        item_text = self.file_tree.item(item_id, "text")
        clean_name = item_text.replace("📁 ", "").replace("📄 ", "")

        if "📁" in item_text or clean_name == "..":
            self.backend.change_dir(clean_name)
            self._refresh_files()

    def _upload(self):
        files = filedialog.askopenfilenames()
        if files:
            threading.Thread(target=self._upload_thread, args=(files,)).start()

    def _upload_thread(self, files):
        try:
            for f in files:
                self.backend.upload(f)
            self.root.after(0, self._refresh_files)
            self.root.after(0, lambda: messagebox.showinfo("Upload", "Done"))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Upload Error", str(e)))

    def _download(self):
        try:
            sel = self.file_tree.selection()[0]
            item_text = self.file_tree.item(sel, "text")
        except IndexError:
            return

        if "📁" in item_text or ".." in item_text:
            return

        filename = item_text.replace("📄 ", "")
        save_path = filedialog.asksaveasfilename(initialfile=filename)
        if save_path:
            threading.Thread(target=self._download_thread, args=(filename, save_path)).start()

    def _download_thread(self, filename, local_path):
        try:
            self.backend.download(filename, local_path)
            self.root.after(0, lambda: messagebox.showinfo("Download", "Done"))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Download Error", str(e)))

    def _start_animations(self):
        """Loop for redrawing terminal and blinking cursor."""
        self.terminal.redraw()
        self.terminal.toggle_cursor()
        
        # Adjust timing to balance load (30ms refresh, 500ms blink)
        self.root.after(30, self._animation_loop)
        self.root.after(500, self._cursor_loop)

    def _animation_loop(self):
        if self.backend.is_connected:
            self.terminal.redraw()
        self.root.after(30, self._animation_loop)

    def _cursor_loop(self):
        if self.backend.is_connected:
            self.terminal.toggle_cursor()
        self.root.after(500, self._cursor_loop)