# QuickButtons

QuickButtons is a modern, floating, always-on-top button panel for running scripts, opening websites, playing music, and sending POST requests. It features a modern UI, persistent settings, multilingual support (English/Dutch), and a grid of fully configurable buttons.

## Features
- Persistent settings (geometry, theme, language, translucency, button size, volume)
- Modern, themeable UI with ttk widgets
- Button types: Run Script, Open Website, Play Music, POST Request
- Add/Edit/Delete buttons with context-aware dialogs
- Drag-and-drop (dropdown) button ordering
- Keyboard shortcut support
- Full translation and theming via JSON
- Error handling and user feedback

## Command Line Options

You can specify a custom configuration file or get help from the command line:

```sh
python quickbuttons.py --config myconfig.json   # Use a custom config file
python quickbuttons.py -c myconfig.json         # Short form
python quickbuttons.py --help                   # Show help and options
```

If not specified, the app uses `config.json` by default.

## Compiling to a Windows Executable

You can compile QuickButtons into a standalone Windows executable using [PyInstaller](https://pyinstaller.org/). This will bundle all dependencies and data files (including translations and themes) into a single `.exe` file.

### Prerequisites
- Python 3.8+ (with Tkinter support; included by default in most Python installers)
- pip
- PyInstaller (`pip install pyinstaller`)

> **Note:** Tkinter is required for the GUI. It is included with most standard Python installations. If you encounter errors about missing `tkinter`, please ensure your Python was installed with Tk support.

### Steps
1. **Clone or copy this repository to your Windows machine.**
2. **Install PyInstaller:**
   ```sh
   pip install pyinstaller
   ```
3. **Build the executable:**
   - Using a one-liner (no icon):
     ```sh
     pyinstaller --onefile --windowed --add-data "translations.json;." --add-data "themes.json;." quickbuttons.py
     ```
   - Or use the provided batch/sh script (see below).
   - If you want a custom icon, add `--icon quickbuttons.ico` (if you have one).
4. **Find your executable in the `dist` folder.**

### Including Data Files
- The `--add-data` option ensures `translations.json` and `themes.json` are bundled with the executable.
- On Windows, separate source and destination with a semicolon (`;`).
- On Linux/Mac, use a colon (`:`).

### Using the Provided Scripts
- On Windows, run `build_win.bat`.
- On Linux/Mac, run `build_win.sh` (requires Wine and Python for Windows).

---

## Compiling with Cython and PyInstaller

For extra performance and code protection, you can compile QuickButtons with [Cython](https://cython.org/) before packaging with PyInstaller.

### Prerequisites
- Cython (`pip install cython`)
- A C compiler (e.g., MSVC on Windows, gcc/clang on Linux/Mac)
- PyInstaller

### Steps
1. **Install Cython:**
   ```sh
   pip install cython
   ```
2. **Compile quickbuttons.py to C and build the extension:**
   ```sh
   cythonize -3 --embed -i quickbuttons.py
   ```
   This will produce a compiled executable (e.g., `quickbuttons` or `quickbuttons.exe`).

   Or, to generate a C file and then build:
   ```sh
   cython --embed -3 quickbuttons.py
   gcc -Os -I /path/to/python/include -o quickbuttons quickbuttons.c -lpython3.12
   ```
   (Adjust the Python include/library paths and version as needed.)

3. **Package with PyInstaller (optional, for data files):**
   ```sh
   pyinstaller --onefile --windowed --add-data "translations.json;." --add-data "themes.json;." quickbuttons.py
   ```
   Or use the batch/sh scripts as before.

---

## License
MIT 