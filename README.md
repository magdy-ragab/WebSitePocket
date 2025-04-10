# WebSitePocket

A desktop application for downloading websites and their assets for offline viewing. Built with Python and PyQt5.

![WebSitePocket Screenshot](screenshots/main.png)

## Features

- Download complete websites for offline viewing
- Save multiple websites in organized projects
- Download all linked resources (images, CSS, JavaScript, fonts)
- Option to replace links and form actions with '#'
- Progress tracking for each download
- Bilingual interface (English/Arabic)
- Modern user interface with status indicators

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

1. Run the application:

```bash
python downloader_gui.py
```

2. Create a new project or select an existing one
3. Add URLs to download
4. Configure options:
   - Replace links with '#'
   - Replace form actions with '#'
5. Click "Start Download"

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
