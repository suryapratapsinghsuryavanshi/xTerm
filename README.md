# xTerm - Modular SSH & SFTP Client

xTerm is a lightweight, cross-platform terminal emulator and SFTP client built with Python and Tkinter. It provides a clean, dual-pane interface for managing remote servers: a fully functional terminal on the right and a graphical file manager on the left.

---

## Features

- **SSH Terminal**: VT100/xterm emulation using pyte with support for standard shell colors and interactive commands (top, nano, vi).
- **SFTP File Manager**: Graphical interface to browse remote directories.
- **File Transfer**: Upload and download files with a single click.
- **Authentication**: Support for both password and SSH Key (PEM/OpenSSH) authentication.
- **Cross-Platform**: Runs on Windows, Linux, and macOS.
- **Modular Architecture**: Clean separation between UI (Tkinter), Networking (Paramiko), and Emulation (Pyte).

---

## Getting Started

### Prerequisites
- Python 3.10 or higher  
- pip (Python package manager)

### Running from Source

#### Clone the repository
```bash
git clone https://github.com/yourusername/xTerm.git
cd xTerm
````

#### Create a Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

#### Install Dependencies

```bash
pip install -r requirements.txt
```

#### Run the Application

```bash
python main.py
```

---

## Usage

### Connect

Enter the Host IP, Username, and either a Password or select a Private Key file.
Click **CONNECT**.

### Terminal

Once connected, the right pane acts as a standard shell.
Click inside the black area to focus and type commands.

### File Management

* **Navigate**: Double-click folders (📁) to enter them. Double-click `..` to go up a directory.
* **Upload**: Click the **⬆ Upload** button to select files from your computer and send them to the current remote folder.
* **Download**: Select a file (📄) in the list and click **⬇ Download** to save it to your computer.
* **Refresh**: Click the **↻** button to update the file list if changes occurred outside the app.

---

## Building Executables

### Automated Builds (GitHub Actions)

This project is configured to automatically build standalone executables for Windows, Linux, and macOS whenever a version tag is pushed.

1. Commit your changes.
2. Tag the release:

   ```bash
   git tag v1.0.0
   ```
3. Push the tag:

   ```bash
   git push origin v1.0.0
   ```
4. Go to the **Actions** tab on GitHub to watch the build.
5. Once finished, the executables will be available under **Releases**.

---

### Manual Build (Local)

To build a binary on your local machine, install PyInstaller:

```bash
pip install pyinstaller
```

Run the build command:

```bash
pyinstaller --clean --onefile --windowed --name xTerm \
    --hidden-import=paramiko --hidden-import=pyte --hidden-import=tkinter \
    main.py
```

The executable will be located in the `dist/` folder.

---

## Project Structure

```
main.py                 # Entry point of the application
src/app.py              # Main GUI Controller
src/ssh_backend.py      # Paramiko SSH/SFTP logic
src/terminal.py         # Custom Tkinter widget for Pyte screen buffer
src/utils.py            # Helper functions (byte formatting, etc.)
```

---

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the project.
2. Create your feature branch:

   ```bash
   git checkout -b feature/AmazingFeature
   ```
3. **Code Style**: Follow PEP 8. Variables -> snake_case, Classes -> CamelCase.
4. Commit your changes:

   ```bash
   git commit -m "Add some AmazingFeature"
   ```
5. Push to the branch:

   ```bash
   git push origin feature/AmazingFeature
   ```
6. Open a Pull Request.

---

## TODOs / Future Ideas

* Implement drag-and-drop for file transfers.
* Add support for saving connection profiles.
* Add context menu (right-click) for file operations (Delete, Rename).
* Add syntax highlighting themes for the terminal.

---

## License

Distributed under the MIT License. See `LICENSE` for more information.