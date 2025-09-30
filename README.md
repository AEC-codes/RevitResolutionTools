# AEC.codes - Revit Resolution Tools

![Version](https://img.shields.io/badge/version-0.1.0--beta-blue)
![Python](https://img.shields.io/badge/python-3.8+-green)
![License](https://img.shields.io/badge/license-CC--BY--NC--SA--4.0-orange)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)

A comprehensive desktop application for managing, analyzing, and maintaining Autodesk Revit installations. This tool provides powerful utilities for warnings management, journal analysis, and system cleanup across multiple Revit versions.

**Author:** spaikid for AEC.codes  
**Version:** 0.1.0-beta

---

## 🎯 Features

### ✅ Warnings Management
- **HTML Import**: Load and parse Revit warning reports exported as HTML
- **JSON Storage**: Automatic conversion and storage in JSON format for easy tracking
- **Smart Grouping**: Group warnings by message type with automatic status tracking
- **Status Management**: Track warnings as Open, In Review, or Closed
- **Element ID Extraction**: Automatically extract and copy element IDs
- **Filtering**: Filter by status and search by keywords
- **Visual Organization**: Tree view with expandable/collapsible groups

### 📊 Journal Analysis
- **Auto-Discovery**: Automatically scans all installed Revit versions (2020, 2024, 2025, 2026+)
- **Smart Categorization**: Automatically categorizes journal entries:
  - Errors and Exceptions
  - Performance Issues (BIG GAP)
  - Commands and Events
  - Model Information
  - Memory Statistics
- **Multi-Model Support**: Handles journals with multiple models
- **Advanced Filtering**: Filter by category, time range, model, or search text
- **Full Content View**: Click any entry to see the complete untruncated content
- **Worker Log Integration**: Automatically loads associated worker log files
- **Export Capability**: Export filtered entries with metadata

### 🧹 Cleaning Tools
- **Automatic Version Detection**: Scans both AppData\Roaming and AppData\Local
- **7 Cleanable Areas** per Revit version:
  1. **Recent Files** - Clear recent file list from Revit.ini (UTF-16 LE support)
  2. **Recent File Cache** - Remove cached file previews
  3. **Workset Configurations** - Clean obsolete workset settings
  4. **UI Configuration Files** - Reset keyboard shortcuts and layouts
  5. **CefCache** - Clear Chrome Embedded Framework cache
  6. **CollaborationCache** - Remove collaboration cache files
  7. **Product Feedback** - Clean telemetry data
- **Size Calculation**: Real-time disk space usage for each area
- **Backup Option**: Optional backup before cleaning operations
- **Batch Operations**: Clean individual areas or entire versions

---

## 📸 Screenshots

### Warnings Tab
> Group, filter, and manage Revit warnings with status tracking and element ID extraction

### Journal Tab
> Analyze Revit journals with automatic categorization and intelligent filtering
> - Sidebar browser with all Revit versions
> - Automatic model detection
> - Performance issue highlighting

### Cleaning Tab
> Maintain your Revit installations by cleaning caches and configuration files
> - Automatic version detection
> - Real-time size calculation
> - Safe cleaning with backup option

---

## 🚀 Installation

### Prerequisites
- **Python 3.8+** (Python 3.9 or higher recommended)
- **Windows OS** (Required - uses Windows AppData structure)
- **Autodesk Revit** (any version from 2020 onwards)

### Step 1: Clone the Repository
```bash
git clone https://github.com/AEC-codes/revit-resolution-tools.git
cd revit-resolution-tools
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

**Dependencies:**
- `beautifulsoup4` - HTML parsing for warnings
- `loguru` - Advanced logging capabilities

### Step 3: Run the Application
```bash
python main.py
```

---

## 📖 Usage Guide

### Quick Start

1. **Launch the application**
   ```bash
   python main.py
   ```

2. **Navigate to your desired tab:**
   - **Warnings**: Analyze Revit warning reports
   - **Journal**: Investigate journal files for errors and performance
   - **Cleaning**: Maintain Revit installations

### Warnings Tab

**Loading Warnings:**
1. Click "Load HTML" to import a Revit warning report
2. The tool automatically parses and groups warnings
3. Use filters to focus on specific issues

**Managing Warnings:**
- **Right-click** on any warning to copy element IDs
- **Double-click** to view full details and change status
- **Group View**: See all similar warnings together
- **Status Tracking**: Mark warnings as Open, In Review, or Closed

**Exporting:**
- Click "Save JSON" to export current state
- Click "Load JSON" to restore previous session

### Journal Tab

**Auto-Loading Journals:**
1. The sidebar automatically shows all installed Revit versions
2. Expand any version to see available journal files
3. Click "► Load Selected" to analyze a journal

**Manual Loading:**
- Use "Load External File" for journals from other sources (email, network, etc.)

**Filtering:**
- **Category**: Focus on Errors, Performance issues, Commands, etc.
- **Search**: Find specific text in journal entries
- **Time Range**: View only recent entries (Last 15 min / Last 1 hour)
- **Model Filter**: Filter entries related to a specific model

**Analysis:**
- Double-click any entry to see the full, untruncated content
- View header information (Build, Branch, Release, Username)
- See all models referenced in the journal
- Track command sequences and their timestamps

### Cleaning Tab

**Scanning:**
- The tool automatically detects all Revit versions on startup
- Click 🔄 to refresh and rescan

**Cleaning Process:**
1. Select a Revit version to see all cleanable areas
2. Click on specific areas to see detailed information
3. Review size and file count before cleaning
4. Enable "Backup before cleaning" for safety (recommended)
5. Click "🗑️ Clean Selected" for individual areas
6. Click "🧹 Clean All (Version)" to clean an entire Revit version

**Safety Features:**
- Automatic backup option (enabled by default)
- Detailed warnings before deletion
- Preview of files to be removed
- Selective cleaning (choose what to remove)

---

## 🏗️ Project Structure

```
revit-resolution-tools/
├── main.py                           # Application entry point
├── requirements.txt                  # Python dependencies
├── README.md                         # This file
├── .gitignore                        # Git ignore rules
└── src/
    └── revit_warnings_manager/
        ├── __init__.py               # Package initialization
        ├── app.py                    # Main application controller
        ├── ui.py                     # UI setup and layout
        ├── handlers.py               # Event handlers
        ├── file_operations.py        # File I/O operations
        ├── parsers.py                # HTML and Journal parsers
        └── assets/
            └── icon.ico              # Application icon
```

---

## 🔧 Technical Details

### Architecture
- **Modular Design**: Separated concerns (UI, Logic, File Operations)
- **Event-Driven**: Clean separation between UI and business logic
- **Extensible**: Easy to add new parsers and cleanup operations

### File Encoding Support
- **UTF-8**: HTML exports, JSON files, worker logs
- **UTF-16 LE**: Revit.ini files (automatic detection)
- **Multi-encoding**: Journal files (utf-8, latin-1, cp1252, iso-8859-1)

### Logging
- Uses `loguru` for comprehensive logging
- Log file: `app.log` (automatically rotated at 10MB)
- Debug, Info, Warning, and Error levels
- Helpful for troubleshooting and development

---

## 🛠️ Development

### Requirements
- Python 3.8 or higher
- tkinter (usually included with Python)
- beautifulsoup4
- loguru

### Running in Development Mode
```bash
# Install dependencies
pip install -r requirements.txt

# Run with debug output
python main.py
```

### Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📋 System Requirements

### Minimum Requirements
- **OS**: Windows 10 or higher
- **Python**: 3.8+
- **RAM**: 2GB (4GB recommended)
- **Disk Space**: 50MB for application

### Supported Revit Versions
- Autodesk Revit 2020 and newer
- Automatic detection of any installed version
- No hardcoded version dependencies

---

## 🗺️ Roadmap

### Current Version (0.1.0-beta)
- ✅ Warnings management with grouping and status tracking
- ✅ Journal analysis with auto-discovery
- ✅ Cleaning tab with version scanning
- ⚠️ Cleaning operations (placeholders implemented)

### Planned Features (0.2.0)
- [ ] Implement actual cleaning operations
- [ ] Backup functionality before cleaning
- [ ] Recent files selective removal
- [ ] INI file editor for advanced users
- [ ] Statistics and reports generation

### Future Enhancements (0.3.0+)
- [ ] Cloud model support
- [ ] Multi-project warnings comparison
- [ ] Scheduled cleaning tasks
- [ ] Configuration presets
- [ ] Command-line interface (CLI)

---

## 🐛 Known Issues

- Cleaning operations are placeholders (coming in v0.2)
- Large journal files (>100MB) may take time to load
- Some UTF-16 encoded files might show encoding warnings (handled gracefully)

---

## 📄 License

This work is licensed under the **Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License**.

### License Summary

**You are free to:**
- ✅ **Share** — copy and redistribute the material in any medium or format
- ✅ **Adapt** — remix, transform, and build upon the material

**Under the following terms:**
- 📝 **Attribution** — You must give appropriate credit to AEC.codes - spaikid, provide a link to the license, and indicate if changes were made
- 💼 **NonCommercial** — You may not use the material for commercial purposes
- 🔄 **ShareAlike** — If you remix, transform, or build upon the material, you must distribute your contributions under the same license

### Full License

```
Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License

Copyright (c) 2025 AEC.codes - spaikid

This work is licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 
International License. To view a copy of this license, visit:
http://creativecommons.org/licenses/by-nc-sa/4.0/

or send a letter to Creative Commons, PO Box 1866, Mountain View, CA 94042, USA.
```

**Full legal text**: [https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode](https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode)

---

## 🙏 Acknowledgments

- Built for the AEC community
- Powered by Python and tkinter
- Uses BeautifulSoup4 for HTML parsing
- Logging by Loguru

---

## 📧 Contact & Support

**Author**: spaikid  
**Organization**: AEC.codes  
**Issues**: Please report bugs via GitHub Issues  
**Version**: 0.1.0-beta

---

## 🌟 Star this repository if you find it useful!

Made with ❤️ for the BIM community
