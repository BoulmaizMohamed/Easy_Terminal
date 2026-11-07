# Command Center

A modern, keyboard-first desktop terminal front-end for **PowerShell** and **Command Prompt** (`cmd.exe`) on Windows. Built with Python 3.11+, [Textual](https://github.com/Textualize/textual), and SQLite.

Command Center turns Windows shells into an interactive, IDE-like console with persistent sessions, intelligent auto-completion, an offline command catalog, and destructive command safety confirmation.

---

## Features

- **Persistent Shell Sessions**: Long-running background sessions for both PowerShell and `cmd.exe`. Directory changes (`cd`) and environment variables persist across commands without shell prompt pollution.
- **Zero-Latency Shell Toggle (`F2`)**: Switch seamlessly between PowerShell and Command Prompt with synchronized working directories.
- **Intelligent Auto-Suggestions**: Predictive dropdown ranking past commands and library recipes by prefix match, execution frequency, recency decay, and favorites.
- **Curated Command Library (`Ctrl+L`)**: 50+ pre-seeded Windows system commands across 8 categories (Network, Files, System, Processes, Disk, Users, Search, Services). Full CRUD, favorites, 6 sort modes, and instant search.
- **Fuzzy Command Palette & Help (`Ctrl+P`)**: Search all library commands and examples with detailed syntax guides, tags, and one-key execution or insertion.
- **Destructive Command Guard**: Detects dangerous system operations (`del /s`, `rd /s`, `format`, `Remove-Item -Recurse -Force`, `diskpart`, `shutdown`, `reg delete`) and prompts for explicit confirmation before execution.
- **tldr-pages Synchronizer**: One-click download and offline sync of community man-pages from [tldr-pages](https://github.com/tldr-pages/tldr) with automatic Windows category tagging.
- **JSON Backup & Migration**: Export custom commands and import external libraries with schema validation and duplicate detection.
- **Rich Theming (`Ctrl+T` / `F10`)**: 7 built-in themes including Catppuccin Mocha, Nord, Tokyo Night, Dracula, and Textual Dark/Light.
- **Privacy & Offline First**: Zero telemetry. Completely offline capable (network is only touched when explicitly triggering a tldr sync).

---

## Architecture

```
┌────────────────────────────────────────────────────────┐
│                   Command Center UI                    │
│             (Textual Async TUI / Widgets)              │
└──────────────┬──────────────────────────┬──────────────┘
               │                          │
┌──────────────▼─────────────┐   ┌────────▼──────────────┐
│        ShellManager        │   │     SQLite Engine     │
│  (Persistent Background    │   │  (WAL Mode / Local)   │
│   PowerShell & cmd.exe)    │   │                       │
│  - Sentinel Token Protocol │   │  - command_center.db  │
│  - Non-blocking I/O Stream │   │  - history table      │
│  - Directory Synchronization│  │  - library table      │
└────────────────────────────┘   └───────────────────────┘
```

1. **Persistent Execution**: Rather than launching a new process per command, Command Center maintains long-running processes (`powershell.exe -NoLogo -NoProfile -NoExit -Command -` and `cmd.exe /Q /K`).
2. **Sentinel Token Protocol**: Commands are suffixed with a unique, unguessable sentinel line printing execution exit codes and current working directory without polluting stdout.
3. **Background Worker Threads**: Command I/O runs asynchronously off the UI thread via Textual workers, preventing interface stuttering or lockups.
4. **Local Data Isolation**: User history and library databases are persisted safely in the standard Windows roaming user data folder (`%APPDATA%\command_center`).

---

## Installation

### Prerequisites
- **Windows 10 / 11** or Windows Server
- **Python 3.11+** installed and available on `PATH`

### Setup

1. Clone or download the repository:
   ```powershell
   git clone https://github.com/your-username/command-center.git
   cd command-center
   ```

2. Create and activate a virtual environment:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\activate
   ```

3. Install required dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

---

## Usage

Launch Command Center directly:
```powershell
python -m command_center
```

Or execute within the project directory:
```powershell
python -m command_center.app
```

---

## Keyboard Shortcuts

Command Center is designed to be fully navigable without a mouse:

### Global Shortcuts

| Shortcut | Description |
| :--- | :--- |
| **`F2`** | Toggle Shell between **PowerShell** and **Command Prompt** (syncs CWD) |
| **`Ctrl + P`** | Open **Command Palette & Help** fuzzy search |
| **`Ctrl + L`** | Open **Command Library** management screen |
| **`Ctrl + H`** | Open **Execution History** browser |
| **`F10`** | Open **Settings & Preferences** modal |
| **`Ctrl + T`** | Cycle through interface color themes |
| **`Ctrl + C`** | Interrupt running command / dismiss open dropdown |
| **`Ctrl + R`** | Restart the active shell session |
| **`Ctrl + Y`** | Copy the last command's terminal output to system clipboard |
| **`Ctrl + Q`** | Quit application |
| **`Up / Down`** | Cycle through command input history (when dropdown is hidden) |

### Auto-Suggest Dropdown

| Shortcut | Description |
| :--- | :--- |
| **`Tab`** | Accept highlighted suggestion and fill command input |
| **`Up / Down`** | Move suggestion highlight |
| **`Enter`** | Run highlighted suggestion directly |
| **`Escape`** | Close suggestion dropdown |

### Command Library (`Ctrl+L`)

| Shortcut | Description |
| :--- | :--- |
| **`Enter`** | Run command (or insert, depending on settings) |
| **`Space`** | Toggle favorite status |
| **`A`** | Add new command to library |
| **`E`** | Edit selected command |
| **`D`** | Delete selected command (seed commands are protected) |
| **`S`** | Synchronize offline community library from tldr-pages |
| **`Ctrl + E`** | Export custom commands to JSON |
| **`Ctrl + I`** | Import commands from JSON |
| **`Escape`** | Close library screen |

### Palette & Help (`Ctrl+P`)

| Shortcut | Description |
| :--- | :--- |
| **`Enter`** | Run selected command immediately |
| **`Tab`** | Insert selected command into input without running |
| **`Up / Down`** | Navigate search results and preview documentation |
| **`Escape`** | Close palette |

---

## Packaging as Standalone Windows Executable

You can package Command Center into a self-contained `.exe` using [PyInstaller](https://pyinstaller.org):

1. Install PyInstaller:
   ```powershell
   pip install pyinstaller
   ```

2. Build standalone directory distribution:
   ```powershell
   pyinstaller --noconfirm --onedir --name "CommandCenter" `
     --add-data "command_center/styles.tcss;command_center" `
     --add-data "command_center/data/seed_library.json;command_center/data" `
     command_center/__main__.py
   ```

3. (Optional) Build a single `.exe` file:
   ```powershell
   pyinstaller --noconfirm --onefile --name "CommandCenter" `
     --add-data "command_center/styles.tcss;command_center" `
     --add-data "command_center/data/seed_library.json;command_center/data" `
     command_center/__main__.py
   ```

The compiled binaries will be output to the `dist/CommandCenter/` directory.

---

## Running the Test Suite

Run the full pytest test suite (40+ unit and integration tests):
```powershell
pytest -v
```

Run specific test modules:
```powershell
pytest tests/test_shell.py -v
pytest tests/test_history.py -v
pytest tests/test_library.py -v
pytest tests/test_suggest.py -v
pytest tests/test_palette.py -v
pytest tests/test_importers.py -v
pytest tests/test_safety_and_settings.py -v
```

---

## Data Storage Locations

Command Center stores local state under the user's standard application data directory:
- **Database**: `%APPDATA%\command_center\command_center.db`
- **Settings**: `%APPDATA%\command_center\settings.json`

---

## License & Attribution

- Built under the MIT License.
- Includes community manual pages provided by [tldr-pages](https://github.com/tldr-pages/tldr) under the MIT License.
- Detailed license terms for all dependencies and components are documented in [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md).
