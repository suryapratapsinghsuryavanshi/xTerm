"""
Handles SSH and SFTP connections using Paramiko.
"""
import os
import threading
import stat
import time
import posixpath
import paramiko

class SSHBackend:
    """
    Wrapper for Paramiko SSH and SFTP clients.
    """
    def __init__(self):
        self.ssh_client = None
        self.sftp_client = None
        self.shell = None
        self.is_connected = False
        self.current_remote_path = "/"

    def connect(self, host, user, key_path, password, on_output_callback):
        """
        Establishes SSH and SFTP connections.
        
        Args:
            host (str): Hostname or IP.
            user (str): Username.
            key_path (str): Path to private key file.
            password (str): Password.
            on_output_callback (func): Function to handle shell output.
        """
        self.ssh_client = paramiko.SSHClient()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        if key_path and os.path.exists(key_path):
            self.ssh_client.connect(
                host, username=user, key_filename=key_path, password=password or None
            )
        else:
            self.ssh_client.connect(host, username=user, password=password)

        # Initialize Shell
        self.shell = self.ssh_client.invoke_shell(term='xterm-256color')
        self.shell.setblocking(0)
        self.shell.send("export LANG=en_US.UTF-8\n")
        self.shell.send("clear\n")

        # Initialize SFTP
        self.sftp_client = self.ssh_client.open_sftp()
        self.current_remote_path = self.sftp_client.normalize('.')
        self.is_connected = True

        # Start listening loop
        threading.Thread(
            target=self._listen_to_shell, 
            args=(on_output_callback,), 
            daemon=True
        ).start()

    def _listen_to_shell(self, callback):
        """Background thread to listen for shell output."""
        while self.is_connected:
            try:
                if self.shell.recv_ready():
                    data = self.shell.recv(4096).decode('utf-8', errors='ignore')
                    callback(data)
                else:
                    time.sleep(0.01)
            except (OSError, AttributeError):
                break

    def list_files(self):
        """
        Lists files in the current remote directory.
        Returns: List of file objects with attributes.
        """
        if not self.sftp_client:
            return []
        
        try:
            files = self.sftp_client.listdir_attr(self.current_remote_path)
            # Sort: Directories first, then alphabetical
            files.sort(key=lambda x: (not stat.S_ISDIR(x.st_mode), x.filename))
            return files
        except IOError:
            return []

    def change_dir(self, directory):
        """Changes the current remote directory."""
        if directory == "..":
            self.current_remote_path = posixpath.dirname(self.current_remote_path)
        else:
            self.current_remote_path = posixpath.join(self.current_remote_path, directory)

    def upload(self, local_path):
        """Uploads a file to the current remote path."""
        filename = os.path.basename(local_path)
        remote_path = posixpath.join(self.current_remote_path, filename)
        self.sftp_client.put(local_path, remote_path)

    def download(self, filename, local_path):
        """Downloads a file from the current remote path."""
        remote_path = posixpath.join(self.current_remote_path, filename)
        self.sftp_client.get(remote_path, local_path)

    def send_command(self, cmd):
        """Sends a keystroke or command to the shell."""
        if self.shell:
            self.shell.send(cmd)

    def resize_pty(self, cols, rows):
        """Resizes the pseudoterminal."""
        if self.shell:
            try:
                self.shell.resize_pty(width=cols, height=rows)
            except paramiko.SSHException:
                pass