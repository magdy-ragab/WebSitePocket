import sys
import time
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLineEdit, QTextEdit, 
                            QLabel, QComboBox, QCheckBox, QProgressBar, 
                            QMessageBox, QFileDialog, QInputDialog, QTableWidget,
                            QTableWidgetItem, QHeaderView, QSizePolicy)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QIcon, QFontDatabase, QFont, QColor
from download import WebDownloader
from translations import TRANSLATIONS

class DownloaderThread(QThread):
    progress = pyqtSignal(int, int)  # current, total
    file_progress = pyqtSignal(int, int, str)  # current, total, filename
    status = pyqtSignal(str)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, downloader, urls):
        super().__init__()
        self.downloader = downloader
        self.urls = urls
        self.is_running = True

    def stop(self):
        self.is_running = False
        self.downloader.abort = True

    def run(self):
        try:
            for url in self.urls:
                if not self.is_running:
                    break
                self.status.emit(f"Processing {url}")
                # Set progress callbacks
                def progress_callback(current, total):
                    self.progress.emit(current, total)
                
                def file_callback(current, total, filename):
                    self.file_progress.emit(current, total, filename)
                
                self.downloader.set_progress_callback(progress_callback)
                self.downloader.set_file_callback(file_callback)
                self.downloader.download_page(url)
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_lang = 'en'
        self.tr = TRANSLATIONS[self.current_lang]
        self.setWindowTitle(self.tr['title'])
        self.setMinimumSize(600, 400)
        self.downloading = False
        self.setup_font_awesome()
        self.setup_ui()
        self.load_projects()
        # Set app icon
        self.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), 'icons', 'icon.png')))

    def setup_font_awesome(self):
        # Load Font Awesome
        font_id = QFontDatabase.addApplicationFont(os.path.join(os.path.dirname(__file__), 'fonts', 'fa-solid-900.ttf'))
        if font_id < 0:
            print("Error loading Font Awesome")
        self.fa_font = QFont('Font Awesome 6 Free Solid', 10)
        
        # Define Font Awesome icons
        self.STATUS_ICONS = {
            'default': '\uf111',    # circle
            'waiting': '\uf254',    # hourglass
            'completed': '\uf00c',  # check
        }

        # Add button icons
        self.BUTTON_ICONS = {
            'download': '\uf019',  # download icon
            'abort': '\uf05e',    # ban/stop icon
        }

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Project selection
        project_layout = QHBoxLayout()
        self.project_combo = QComboBox()
        self.project_combo.addItem(self.tr['create_new_project'])
        project_layout.addWidget(QLabel(self.tr['project']))
        project_layout.addWidget(self.project_combo)
        self.new_project_btn = QPushButton(self.tr['new_project'])
        self.new_project_btn.clicked.connect(self.create_new_project)
        project_layout.addWidget(self.new_project_btn)
        
        layout.addLayout(project_layout)

        # URL input
        url_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText(self.tr['enter_url'])
        url_layout.addWidget(self.url_input)
        self.add_url_btn = QPushButton(self.tr['add_url'])
        self.add_url_btn.clicked.connect(self.add_url)
        url_layout.addWidget(self.add_url_btn)
        layout.addLayout(url_layout)

        # URLs list - replace QTextEdit with QTableWidget
        self.urls_table = QTableWidget()
        self.urls_table.setColumnCount(2)
        self.urls_table.setHorizontalHeaderLabels([self.tr['status'], self.tr['url']])
        # Always set status column to 50px regardless of language
        if self.current_lang == 'ar':
            self.urls_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
            self.urls_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
            self.urls_table.setColumnWidth(1, 50)  # Status column is second in RTL
        else:
            self.urls_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
            self.urls_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
            self.urls_table.setColumnWidth(0, 50)  # Status column is first column in LTR
        self.urls_table.setEditTriggers(QTableWidget.NoEditTriggers)  # Make table uneditable
        layout.addWidget(self.urls_table)

        # Options
        options_layout = QHBoxLayout()
        self.replace_links_cb = QCheckBox(self.tr['replace_links'])
        options_layout.addWidget(self.replace_links_cb)
        self.replace_forms_cb = QCheckBox(self.tr['replace_forms'])
        options_layout.addWidget(self.replace_forms_cb)
        layout.addLayout(options_layout)

        # Progress
        progress_group = QVBoxLayout()
        
        # Total progress
        total_progress_layout = QHBoxLayout()
        self.progress_label = QLabel(self.tr['ready'])
        total_progress_layout.addWidget(self.progress_label)
        
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        total_progress_layout.addWidget(spacer)
        
        self.time_label = QLabel(self.tr['time_remain'] + ": --:--")
        if self.current_lang == 'ar':
            self.time_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        else:
            self.time_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        total_progress_layout.addWidget(self.time_label)
        progress_group.addLayout(total_progress_layout)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setAlignment(Qt.AlignCenter)
        progress_group.addWidget(self.progress_bar)
        
        # File progress
        self.file_label = QLabel(f"{self.tr['current_file']}{self.tr['none']}")
        progress_group.addWidget(self.file_label)
        
        self.file_progress = QProgressBar()
        self.file_progress.setAlignment(Qt.AlignCenter)
        progress_group.addWidget(self.file_progress)
        
        layout.addLayout(progress_group)

        # Action buttons
        buttons_layout = QHBoxLayout()
        # buttons_layout.setContentsMargins(150, 20, 150, 0)  # Add margins (left, top, right, bottom)
        
        buttons_container = QWidget()
        buttons_container_layout = QHBoxLayout(buttons_container)
        buttons_container_layout.setContentsMargins(0, 0, 0, 0)
        buttons_container_layout.setSpacing(10)
        
        self.download_btn = QPushButton(f"{self.BUTTON_ICONS['download']} {self.tr['start_download']}")
        self.download_btn.setFont(self.fa_font)
        self.download_btn.setMinimumHeight(50)
        self.download_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                padding: 5px 10px;
                min-width: 150px;
            }
        """)
        self.download_btn.clicked.connect(self.start_download)
        buttons_container_layout.addWidget(self.download_btn, 1)  # 1 for stretch factor
        
        self.abort_btn = QPushButton(f"{self.BUTTON_ICONS['abort']} {self.tr['abort']}")
        self.abort_btn.setFont(self.fa_font)
        self.abort_btn.setMinimumHeight(50)
        self.abort_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                padding: 5px 10px;
                min-width: 150px;
            }
        """)
        self.abort_btn.clicked.connect(self.abort_download)
        self.abort_btn.setEnabled(False)
        buttons_container_layout.addWidget(self.abort_btn, 1)  # 1 for stretch factor
        
        buttons_layout.addWidget(buttons_container)
        layout.addLayout(buttons_layout)

        # Language selector and buttons
        lang_layout = QHBoxLayout()
        # lang_layout.setContentsMargins(0, 20, 0, 0)  # Add top margin

        self.lang_combo = QComboBox()
        self.lang_combo.addItems(['English', 'العربية'])
        self.lang_combo.currentTextChanged.connect(self.change_language)
        lang_layout.addWidget(self.lang_combo)
        
        # Browse and GitHub buttons
        self.browse_btn = QPushButton(self.tr['browse'])
        # self.browse_btn.setStyleSheet("max-width: 150px;")
        self.browse_btn.clicked.connect(self.browse_projects)
        lang_layout.addWidget(self.browse_btn)

        self.git_project_btn = QPushButton(self.tr['git_project'])
        # self.git_project_btn.setStyleSheet("max-width: 150px;")
        self.git_project_btn.clicked.connect(self.open_git_project)
        lang_layout.addWidget(self.git_project_btn)
        
        lang_layout.setContentsMargins(50, 30, 50, 0)  # Add margins (left, top, right, bottom)
        layout.addLayout(lang_layout)

    def retranslate_ui(self):
        """Update all UI text elements with current language"""
        self.setWindowTitle(self.tr['title'])
        self.new_project_btn.setText(self.tr['new_project'])
        self.url_input.setPlaceholderText(self.tr['enter_url'])
        self.add_url_btn.setText(self.tr['add_url'])
        self.replace_links_cb.setText(self.tr['replace_links'])
        self.replace_forms_cb.setText(self.tr['replace_forms'])
        self.download_btn.setText(f"{self.BUTTON_ICONS['download']} {self.tr['start_download']}")
        self.abort_btn.setText(f"{self.BUTTON_ICONS['abort']} {self.tr['abort']}")
        self.browse_btn.setText(self.tr['browse'])
        self.progress_label.setText(self.tr['ready'])
        self.file_label.setText(f"{self.tr['current_file']}{self.tr['none']}")
        self.time_label.setText(f"{self.tr['time_remain']}: --:--")  # Update time label
        self.urls_table.setHorizontalHeaderLabels([self.tr['status'], self.tr['url']])  # Update table headers

        # Update project combo items
        current_item = self.project_combo.currentText()
        self.project_combo.clear()
        self.project_combo.addItem(self.tr['create_new_project'])
        projects = WebDownloader.list_projects()
        for name in projects.keys():
            self.project_combo.addItem(name)
            
        # Try to restore previous selection
        index = self.project_combo.findText(current_item)
        if index >= 0:
            self.project_combo.setCurrentIndex(index)

    def change_language(self, lang_text):
        self.current_lang = 'ar' if lang_text == 'العربية' else 'en'
        self.tr = TRANSLATIONS[self.current_lang]
        
        # Set layout direction
        if self.current_lang == 'ar':
            self.setLayoutDirection(Qt.RightToLeft)
            # Set RTL alignment for all labels
            for widget in self.findChildren(QLabel):
                widget.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            # Special case for time label
            self.time_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            # Set status column width to 50px
            self.urls_table.setColumnWidth(1, 50)  # Status is second column in RTL
            
        else:
            self.setLayoutDirection(Qt.LeftToRight)
            # Reset alignment for all labels
            for widget in self.findChildren(QLabel):
                widget.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            # Special case for time label
            self.time_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            # Set status column width to 50px
            self.urls_table.setColumnWidth(0, 50)  # Status is first column in LTR

        # Update the UI with new translations
        self.retranslate_ui()

    def browse_projects(self):
        project_dir = os.path.join(os.getcwd(), 'projects')
        os.startfile(project_dir) if os.name == 'nt' else os.system(f'xdg-open "{project_dir}"')

    def load_projects(self):
        self.project_combo.clear()
        self.project_combo.addItem(self.tr['create_new_project'])
        projects = WebDownloader.list_projects()
        for name in projects.keys():
            self.project_combo.addItem(name)
        self.project_combo.currentTextChanged.connect(self.on_project_selected)

    def on_project_selected(self, project_name):
        if project_name != self.tr['create_new_project']:
            existing_project = WebDownloader.load_project(project_name)
            if existing_project:
                self.set_urls(existing_project.urls)
                self.replace_links_cb.setChecked(existing_project.replace_links)
                self.replace_forms_cb.setChecked(existing_project.replace_forms)
        else:
            self.urls_table.setRowCount(0)

    def create_new_project(self):
        project_name, ok = QInputDialog.getText(self, "New Project", "Enter project name:")
        if ok and project_name:
            project_dir = os.path.join(os.getcwd(), 'projects', project_name)
            if os.path.exists(project_dir):
                reply = QMessageBox.question(
                    self,
                    "Project Exists",
                    f"Project '{project_name}' already exists.\nDo you want to use it?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return
                
            self.project_combo.addItem(project_name)
            self.project_combo.setCurrentText(project_name)
            
            # Reset URLs table for new project
            if not os.path.exists(project_dir):
                self.urls_table.setRowCount(0)
                self.replace_links_cb.setChecked(False)
                self.replace_forms_cb.setChecked(False)

            # Load existing URLs if project exists
            existing_project = WebDownloader.load_project(project_name)
            if existing_project:
                self.set_urls(existing_project.urls)
                self.replace_links_cb.setChecked(existing_project.replace_links)
                self.replace_forms_cb.setChecked(existing_project.replace_forms)

    def add_url(self):
        url = self.url_input.text().strip()
        if url:
            row = self.urls_table.rowCount()
            self.urls_table.insertRow(row)
            status_item = QTableWidgetItem(self.STATUS_ICONS['default'])
            status_item.setFont(self.fa_font)
            status_item.setTextAlignment(Qt.AlignCenter)
            self.urls_table.setItem(row, 0, status_item)
            self.urls_table.setItem(row, 1, QTableWidgetItem(url))
            self.url_input.clear()

    def get_urls(self):
        urls = []
        for row in range(self.urls_table.rowCount()):
            urls.append(self.urls_table.item(row, 1).text())
        return urls

    def set_urls(self, urls):
        self.urls_table.setRowCount(0)
        for url in urls:
            row = self.urls_table.rowCount()
            self.urls_table.insertRow(row)
            status_item = QTableWidgetItem(self.STATUS_ICONS['default'])
            status_item.setFont(self.fa_font)
            status_item.setTextAlignment(Qt.AlignCenter)
            self.urls_table.setItem(row, 0, status_item)
            self.urls_table.setItem(row, 1, QTableWidgetItem(url))

    def start_download(self):
        if self.downloading:
            QMessageBox.warning(self, "Warning", "A download is already in progress!")
            return

        # Disable controls during download
        self.urls_table.setEnabled(False)
        self.project_combo.setEnabled(False)
        self.new_project_btn.setEnabled(False)
        self.url_input.setEnabled(False)
        self.add_url_btn.setEnabled(False)
        
        project_name = self.project_combo.currentText()
        if project_name == "Create New Project":
            QMessageBox.warning(self, "Error", "Please select or create a project first")
            return

        urls = self.get_urls()
        if not urls:
            QMessageBox.warning(self, "Error", "Please add at least one URL")
            return

        # Check if project folder exists
        project_dir = os.path.join(os.getcwd(), 'projects', project_name)
        if os.path.exists(project_dir):
            reply = QMessageBox.question(
                self, 
                "Project Exists",
                f"Project '{project_name}' already exists.\nDo you want to redownload all files?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                return
            # If yes, we'll continue with existing project

        # Initialize downloader
        downloader = WebDownloader(project_name)
        downloader.replace_links = self.replace_links_cb.isChecked()
        downloader.replace_forms = self.replace_forms_cb.isChecked()
        downloader.urls = urls

        # Save project data
        downloader.save_project_data()
        
        # Reset progress bars and labels
        self.progress_bar.setValue(0)
        self.file_progress.setValue(0)
        self.file_label.setText(f"{self.tr['current_file']}{self.tr['none']}")
        self.time_label.setText(self.tr["time_remain"] + ": --:--")

        # Update status icons to waiting
        for row in range(self.urls_table.rowCount()):
            status_item = QTableWidgetItem(self.STATUS_ICONS['waiting'])
            status_item.setFont(self.fa_font)
            status_item.setTextAlignment(Qt.AlignCenter)
            self.urls_table.setItem(row, 0, status_item)

        # Highlight current download in green
        for row in range(self.urls_table.rowCount()):
            self.urls_table.item(row, 1).setBackground(QColor('#90EE90'))  # Light green

        # Start download thread
        self.thread = DownloaderThread(downloader, urls)
        self.thread.progress.connect(self.update_progress)
        self.thread.file_progress.connect(self.update_file_progress)
        self.thread.status.connect(self.update_status)
        self.thread.finished.connect(self.download_finished)
        self.thread.error.connect(self.show_error)
        
        self.downloading = True
        self.download_btn.setEnabled(False)
        self.abort_btn.setEnabled(True)
        self.start_time = time.time()
        self.thread.start()

    def abort_download(self):
        if hasattr(self, 'thread'):
            self.thread.stop()
            self.abort_btn.setEnabled(False)
            self.progress_label.setText("Aborting...")

    def update_progress(self, current, total):
        if total > 0:  # Prevent division by zero
            self.progress_bar.setMaximum(total)
            self.progress_bar.setValue(current)
            
            # Calculate and update time estimation
            if current > 0:
                progress = current / total
                elapsed = time.time() - self.start_time
                estimated_total = elapsed / progress
                remaining = estimated_total - elapsed
                self.time_label.setText(self.tr["time_remain"] + f": <b>{int(remaining/60)}:{int(remaining%60):02d}</b>")
            
            # Update color based on progress
            progress = current / total
            if progress < 0.33:
                self.progress_bar.setStyleSheet("""
                    QProgressBar { text-align: center; }
                    QProgressBar::chunk { background-color: #ff4444; }
                """)
            elif progress < 0.66:
                self.progress_bar.setStyleSheet("""
                    QProgressBar { text-align: center; }
                    QProgressBar::chunk { background-color: #ffa500; }
                """)
            else:
                self.progress_bar.setStyleSheet("""
                    QProgressBar { text-align: center; }
                    QProgressBar::chunk { background-color: #44ff44; }
                """)

    def update_file_progress(self, current, total, filename):
        self.file_label.setText(f"{self.tr['current_file']}{filename}")
        self.file_progress.setMaximum(total)
        self.file_progress.setValue(current)
        
        # Update color based on progress
        progress = current / total if total > 0 else 0
        if progress < 0.33:
            color = "#ff4444"
        elif progress < 0.66:
            color = "#ffa500"  # Using orange instead of yellow
        else:
            color = "#44ff44"
            
        self.file_progress.setStyleSheet(f"""
            QProgressBar {{ text-align: center; }}
            QProgressBar::chunk {{ background-color: {color}; }}
        """)

    def update_status(self, message):
        self.progress_label.setText(message)

    def download_finished(self):
        self.downloading = False
        self.download_btn.setEnabled(True)
        self.abort_btn.setEnabled(False)
        
        # Re-enable controls
        self.urls_table.setEnabled(True)
        self.project_combo.setEnabled(True)
        self.new_project_btn.setEnabled(True)
        self.url_input.setEnabled(True)
        self.add_url_btn.setEnabled(True)
        
        self.progress_label.setText("Download completed!")
        self.progress_bar.setValue(0)
        self.file_progress.setValue(0)
        self.file_label.setText(f"{self.tr['current_file']}{self.tr['none']}")
        self.time_label.setText(self.tr["time_remain"] + ": <b>--:--</b>")
        # Update all status icons to finished
        for row in range(self.urls_table.rowCount()):
            status_item = QTableWidgetItem(self.STATUS_ICONS['completed'])
            status_item.setFont(self.fa_font)
            status_item.setTextAlignment(Qt.AlignCenter)
            self.urls_table.setItem(row, 0, status_item)
            self.urls_table.item(row, 1).setBackground(QColor('white'))
        QMessageBox.information(self, "Success", "Download completed successfully!")

    def show_error(self, message):
        self.downloading = False
        self.download_btn.setEnabled(True)
        self.abort_btn.setEnabled(False)
        QMessageBox.critical(self, "Error", f"Download failed: {message}")

    def open_git_project(self):
        """Open the GitHub repository in default browser"""
        repo_url = "https://github.com/magdy-ahmad/web-downloader"  # Replace with your actual repo URL
        import webbrowser
        webbrowser.open(repo_url)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
