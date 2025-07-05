# WebSitePocket

A powerful command-line and desktop application for downloading websites and their assets for offline viewing. Built with Python and PyQt5.

![WebSitePocket Screenshot](screenshots/main.png)

## Features

- **Two Interfaces**: Command-line interface (CLI) and graphical user interface (GUI)
- **Complete Website Downloads**: Download websites with all assets for offline viewing
- **Project Management**: Save multiple websites in organized projects
- **Resource Downloading**: Download all linked resources (images, CSS, JavaScript, fonts)
- **Smart Link Handling**: Option to replace links and form actions with '#' by default
- **Progress Tracking**: Real-time progress tracking for each download
- **Unique Filenames**: Intelligent filename generation prevents file overwrites
- **Download Summary**: View a summary table of all downloaded URLs and their filenames
- **Project Removal**: Remove projects with optional folder deletion
- **Bilingual Interface**: English/Arabic support in GUI
- **Modern UI**: Clean and intuitive user interface with status indicators

## Installation

1. Clone the repository: ```bash git clone https://github.com/magdy-ragab/WebSitePocket.git
cd WebSitePocket```

2. Create a virtual environment (recommended):

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Command Line Interface (CLI)

1. Run the CLI application:

```bash
python download.py
```

2. Choose from the menu:
   - **1. Create new project** - Create a new download project
   - **2. Load existing project** - Continue working on an existing project
   - **3. Launch GUI** - Open the graphical interface
   - **4. Remove project** - Delete a project (with optional folder removal)

3. For new projects:
   - Enter project name
   - Choose link/form replacement options
   - Add URLs to download
   - View download progress and summary table

### Graphical User Interface (GUI)

1. Run the GUI application:

```bash
python downloader_gui.py
```

2. Or launch it from the CLI menu (option 3)

3. Using the GUI:
   - Create a new project or select an existing one
   - Add URLs to the table
   - Configure options:
     - Replace links with '#'
     - Replace form actions with '#'
   - Click "Start Download"
   - View progress and the "Saved as" column for filenames
   - Use "Remove Project" to delete projects

## Dependencies

- Python 3.6+
- PyQt5
- BeautifulSoup4
- Requests
- tqdm

## Contributing

1. Fork the repository
2. Create a new branch (`git checkout -b feature/improvement`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/improvement`)
5. Create a Pull Request

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Credits

Created by [Magdy Ragab](https://github.com/magdy-ragab)

## Support

If you find this project helpful, please give it a star ⭐ on GitHub.

For issues and feature requests, please use the [GitHub Issues](https://github.com/magdy-ragab/WebSitePocket/issues) page.
