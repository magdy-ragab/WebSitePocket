import os
import json
import requests
import platform
from datetime import datetime
from urllib.parse import urlparse


class WebSitePocketCommon:
    """Common functions shared between download.py and downloader_gui.py"""
    
    @staticmethod
    def get_home_dir():
        """Get OS-specific home directory"""
        system = platform.system().lower()
        if system == 'windows':
            return os.path.expanduser('~\\Documents\\WebSitePocket')
        elif system == 'darwin':  # macOS
            return os.path.expanduser('~/Documents/WebSitePocket')
        else:  # Linux and others
            return os.path.expanduser('~/WebSitePocket')

    @staticmethod
    def get_projects_file_path():
        """Get the path to projects.json file"""
        return os.path.join(WebSitePocketCommon.get_home_dir(), 'projects', 'projects.json')

    @staticmethod
    def setup_project_directories(base_dir):
        """Create project directories"""
        directories = ['images', 'js', 'css', 'fonts']
        os.makedirs(base_dir, exist_ok=True)
        for dir_name in directories:
            os.makedirs(os.path.join(base_dir, dir_name), exist_ok=True)

    @staticmethod
    def save_project_data(project_name, urls, replace_links, replace_forms, base_dir):
        """Save project data to projects.json"""
        projects_data = WebSitePocketCommon.load_projects_data()
        projects_data[project_name] = {
            'urls': urls,
            'replace_links': replace_links,
            'replace_forms': replace_forms,
            'timestamp': datetime.now().isoformat(),
            'base_dir': base_dir
        }
        
        projects_file = WebSitePocketCommon.get_projects_file_path()
        os.makedirs(os.path.dirname(projects_file), exist_ok=True)
        with open(projects_file, 'w') as f:
            json.dump(projects_data, f, indent=4)

    @staticmethod
    def load_projects_data():
        """Load all projects data"""
        projects_file = WebSitePocketCommon.get_projects_file_path()
        try:
            with open(projects_file, 'r') as f:
                return json.load(f)
        except:
            return {}

    @staticmethod
    def list_projects():
        """List all saved projects"""
        return WebSitePocketCommon.load_projects_data()

    @staticmethod
    def load_project_data(project_name):
        """Load existing project data"""
        projects = WebSitePocketCommon.list_projects()
        if project_name in projects:
            return projects[project_name]
        return None

    @staticmethod
    def download_file_with_progress(url, local_path, file_callback=None, abort_flag=None):
        """Download a file from URL with progress callback"""
        try:
            response = requests.get(url, stream=True)
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            filename = os.path.basename(local_path)
            
            if file_callback:
                file_callback(downloaded, total_size, filename)
            
            with open(local_path, 'wb') as f:
                for data in response.iter_content(chunk_size=1024):
                    if abort_flag and abort_flag():
                        return False
                    size = f.write(data)
                    downloaded += size
                    if file_callback:
                        file_callback(downloaded, total_size, filename)
                        
            return True
        except Exception as e:
            print(f"Error downloading {url}: {e}")
            return False

    @staticmethod
    def replace_links_with_hash(soup):
        """Replace all links with href='#' by default"""
        for link in soup.find_all('a'):
            link['href'] = '#'

    @staticmethod
    def replace_forms_with_hash(soup):
        """Replace all form actions with action='#' by default"""
        for form in soup.find_all('form'):
            form['action'] = '#'

    @staticmethod
    def save_links_to_json(urls, links_file):
        """Save URLs to JSON file"""
        with open(links_file, 'w') as f:
            json.dump({'urls': urls}, f, indent=4)

    @staticmethod
    def get_project_base_dir(project_name):
        """Get the base directory for a project"""
        return os.path.join(WebSitePocketCommon.get_home_dir(), 'projects', project_name)

    @staticmethod
    def get_links_file_path(project_name):
        """Get the links.json file path for a project"""
        base_dir = WebSitePocketCommon.get_project_base_dir(project_name)
        return os.path.join(base_dir, 'links.json')

    @staticmethod
    def remove_project(project_name, remove_folder=False):
        """Remove a project from projects.json and optionally delete its folder"""
        projects_data = WebSitePocketCommon.load_projects_data()
        
        if project_name not in projects_data:
            return False, f"Project '{project_name}' not found."
        
        # Get project folder path before removing from data
        project_folder = WebSitePocketCommon.get_project_base_dir(project_name)
        
        # Remove from projects data
        del projects_data[project_name]
        
        # Save updated projects data
        projects_file = WebSitePocketCommon.get_projects_file_path()
        try:
            with open(projects_file, 'w') as f:
                json.dump(projects_data, f, indent=4)
        except Exception as e:
            return False, f"Error saving projects file: {e}"
        
        # Optionally remove project folder
        if remove_folder and os.path.exists(project_folder):
            try:
                import shutil
                shutil.rmtree(project_folder)
                return True, f"Project '{project_name}' and its folder removed successfully."
            except Exception as e:
                return False, f"Project removed from list but error deleting folder: {e}"
        
        return True, f"Project '{project_name}' removed successfully."

    @staticmethod
    def get_project_folder_size(project_name):
        """Get the size of a project folder in bytes"""
        project_folder = WebSitePocketCommon.get_project_base_dir(project_name)
        if not os.path.exists(project_folder):
            return 0
        
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(project_folder):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(filepath)
                except OSError:
                    pass
        return total_size

    @staticmethod
    def format_file_size(size_bytes):
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"

    @staticmethod
    def generate_html_filename(url, existing_files=None):
        """Generate a unique HTML filename for a URL"""
        if existing_files is None:
            existing_files = set()
        
        parsed_url = urlparse(url)
        
        # Get the path part
        path = parsed_url.path.strip('/')
        
        # Handle different URL patterns
        if not path or path == '':
            # Root URL like https://example.com/
            filename = 'index.html'
        elif path.endswith('/'):
            # Directory URL like https://example.com/ar/
            # Use the last directory name
            dir_name = path.rstrip('/').split('/')[-1]
            filename = f"{dir_name}.html"
        elif '.' in path.split('/')[-1]:
            # File with extension like https://example.com/page.php
            file_part = path.split('/')[-1]
            if not file_part.endswith('.html'):
                filename = file_part + '.html'
            else:
                filename = file_part
        else:
            # Path without extension like https://example.com/product/item-name
            # Use the full path, replacing slashes with underscores
            filename = path.replace('/', '_') + '.html'
        
        # Handle query parameters if present
        if parsed_url.query:
            # Add a hash of the query to make it unique
            import hashlib
            query_hash = hashlib.md5(parsed_url.query.encode()).hexdigest()[:8]
            name_part, ext = os.path.splitext(filename)
            filename = f"{name_part}_{query_hash}{ext}"
        
        # Ensure filename is valid for filesystem
        filename = "".join(c for c in filename if c.isalnum() or c in '._-')
        
        # Handle duplicates
        base_filename = filename
        counter = 1
        while filename in existing_files:
            name_part, ext = os.path.splitext(base_filename)
            filename = f"{name_part}_{counter}{ext}"
            counter += 1
        
        return filename
