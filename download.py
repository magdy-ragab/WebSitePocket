import os
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
from tqdm import tqdm
from datetime import datetime
import platform
from common import WebSitePocketCommon

class WebDownloader:
    def __init__(self, project_name):
        self.project_name = project_name
        self.base_dir = WebSitePocketCommon.get_project_base_dir(project_name)
        self.links_file = WebSitePocketCommon.get_links_file_path(project_name)
        self.projects_file = WebSitePocketCommon.get_projects_file_path()
        self.urls = []
        self.replace_links = True  # Default to True - replace links with #
        self.replace_forms = True  # Default to True - replace forms with #
        self.total_files = 0
        self.progress_callback = None
        self.file_callback = None
        self.abort = False
        self.html_files = set()  # Track existing HTML files to avoid conflicts
        self.url_filename_mapping = {}  # Track URL to filename mapping
        self.setup_directories()

    def set_progress_callback(self, callback):
        self.progress_callback = callback

    def set_file_callback(self, callback):
        """Set callback for individual file progress"""
        self.file_callback = callback

    def setup_directories(self):
        """Create project directories"""
        WebSitePocketCommon.setup_project_directories(self.base_dir)

    def save_links(self):
        """Save URLs to JSON file"""
        WebSitePocketCommon.save_links_to_json(self.urls, self.links_file)

    def save_project_data(self):
        """Save project data to projects.json"""
        WebSitePocketCommon.save_project_data(
            self.project_name, self.urls, self.replace_links, 
            self.replace_forms, self.base_dir
        )

    def load_projects_data(self):
        """Load all projects data"""
        return WebSitePocketCommon.load_projects_data()

    @classmethod
    def list_projects(cls):
        """List all saved projects"""
        return WebSitePocketCommon.list_projects()

    @classmethod
    def load_project(cls, project_name):
        """Load existing project"""
        project_data = WebSitePocketCommon.load_project_data(project_name)
        if project_data:
            downloader = cls(project_name)
            downloader.urls = project_data['urls']
            downloader.replace_links = project_data['replace_links']
            downloader.replace_forms = project_data.get('replace_forms', True)  # Default True
            return downloader
        return None

    @classmethod
    def remove_project(cls, project_name, remove_folder=False):
        """Remove a project and optionally delete its folder"""
        return WebSitePocketCommon.remove_project(project_name, remove_folder)

    @classmethod
    def get_project_info(cls, project_name):
        """Get project information including folder size"""
        project_data = WebSitePocketCommon.load_project_data(project_name)
        if not project_data:
            return None
        
        folder_size = WebSitePocketCommon.get_project_folder_size(project_name)
        formatted_size = WebSitePocketCommon.format_file_size(folder_size)
        
        return {
            'name': project_name,
            'urls': project_data['urls'],
            'url_count': len(project_data['urls']),
            'folder_size': folder_size,
            'formatted_size': formatted_size,
            'timestamp': project_data.get('timestamp', 'Unknown'),
            'replace_links': project_data.get('replace_links', True),
            'replace_forms': project_data.get('replace_forms', True)
        }

    def download_file(self, url, local_path, position=1):
        """Download a file from URL with nested progress bar"""
        return WebSitePocketCommon.download_file_with_progress(
            url, local_path, self.file_callback, lambda: self.abort
        )

    def count_total_files(self, url):
        """Count total number of files to download"""
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            images = len(soup.find_all('img'))
            scripts = len(soup.find_all('script', src=True))
            css_files = len(soup.find_all('link', rel='stylesheet'))
            
            # Count resources in CSS files
            css_resources = 0
            for css in soup.find_all('link', rel='stylesheet'):
                href = css.get('href')
                if href:
                    absolute_url = urljoin(url, href)
                    css_response = requests.get(absolute_url)
                    urls = re.findall(r'url\([\'"]?(.*?)[\'"]?\)', css_response.text)
                    css_resources += len([u for u in urls if not u.startswith('data:')])
            
            return images + scripts + css_files + css_resources
        except:
            return 0

    def process_css(self, css_content, css_url, main_pbar):
        """Process CSS file and download its resources"""
        # Find all URLs in CSS
        url_pattern = r'url\([\'"]?(.*?)[\'"]?\)'
        urls = re.findall(url_pattern, css_content)
        
        for url in urls:
            if url.startswith('data:'):
                continue
                
            absolute_url = urljoin(css_url, url)
            file_name = os.path.basename(urlparse(absolute_url).path)
            
            if any(ext in file_name.lower() for ext in ['.ttf', '.woff', '.woff2']):
                local_path = os.path.join(self.base_dir, 'fonts', file_name)
                resource_path = f'../fonts/{file_name}'
            else:
                local_path = os.path.join(self.base_dir, 'images', file_name)
                resource_path = f'../images/{file_name}'
            
            if self.download_file(absolute_url, local_path, position=1):
                css_content = css_content.replace(url, resource_path)
                main_pbar.update(1)
                
        return css_content

    def download_page(self, url):
        """Download webpage and its assets"""
        try:
            print(f"\nProcessing webpage: {url}")
            self.total_files = self.count_total_files(url)
            completed_files = 0
            
            if self.progress_callback:
                self.progress_callback(completed_files, self.total_files)
            
            if self.replace_links:
                print("Replacing all links with href='#'...")
            
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            base_url = url

            # Main progress bar for all files
            with tqdm(total=self.total_files, desc="Total Progress", 
                     position=0, colour='red', leave=False,
                     bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]') as main_pbar:
                
                # Replace all links with # by default
                if self.replace_links:
                    WebSitePocketCommon.replace_links_with_hash(soup)
                
                # Replace all form actions with # by default
                if self.replace_forms:
                    WebSitePocketCommon.replace_forms_with_hash(soup)
                
                # Download images
                images = soup.find_all('img')
                for img in images:
                    if self.abort:
                        return
                    src = img.get('src')
                    if src:
                        absolute_url = urljoin(base_url, src)
                        file_name = os.path.basename(urlparse(absolute_url).path)
                        local_path = os.path.join(self.base_dir, 'images', file_name)
                        if self.download_file(absolute_url, local_path, position=1):
                            img['src'] = f'images/{file_name}'
                            completed_files += 1
                            if self.progress_callback:
                                self.progress_callback(completed_files, self.total_files)
                            # Update main progress bar color
                            progress = completed_files / self.total_files
                            if progress < 0.33:
                                main_pbar.colour = 'red'
                            elif progress < 0.66:
                                main_pbar.colour = 'yellow'
                            else:
                                main_pbar.colour = 'green'
                            main_pbar.update(1)

                # Download JavaScript files
                scripts = soup.find_all('script', src=True)
                for script in scripts:
                    if self.abort:
                        return
                    src = script['src']
                    absolute_url = urljoin(base_url, src)
                    file_name = os.path.basename(urlparse(absolute_url).path)
                    local_path = os.path.join(self.base_dir, 'js', file_name)
                    if self.download_file(absolute_url, local_path, position=1):
                        script['src'] = f'js/{file_name}'
                        completed_files += 1
                        if self.progress_callback:
                            self.progress_callback(completed_files, self.total_files)
                        progress = completed_files / self.total_files
                        if progress < 0.33:
                            main_pbar.colour = 'red'
                        elif progress < 0.66:
                            main_pbar.colour = 'yellow'
                        else:
                            main_pbar.colour = 'green'
                        main_pbar.update(1)

                # Download CSS files and their resources
                css_files = soup.find_all('link', rel='stylesheet')
                for css in css_files:
                    if self.abort:
                        return
                    href = css.get('href')
                    if href:
                        absolute_url = urljoin(base_url, href)
                        file_name = os.path.basename(urlparse(absolute_url).path)
                        local_path = os.path.join(self.base_dir, 'css', file_name)
                        
                        css_response = requests.get(absolute_url)
                        processed_css = self.process_css(css_response.text, absolute_url, main_pbar)
                        
                        with open(local_path, 'w', encoding='utf-8') as f:
                            f.write(processed_css)
                        
                        css['href'] = f'css/{file_name}'
                        completed_files += 1
                        if self.progress_callback:
                            self.progress_callback(completed_files, self.total_files)
                        progress = completed_files / self.total_files
                        if progress < 0.33:
                            main_pbar.colour = 'red'
                        elif progress < 0.66:
                            main_pbar.colour = 'yellow'
                        else:
                            main_pbar.colour = 'green'
                        main_pbar.update(1)

                # Save updated HTML
                print("\nSaving HTML file...")
                page_name = WebSitePocketCommon.generate_html_filename(url, self.html_files)
                self.html_files.add(page_name)
                self.url_filename_mapping[url] = page_name
                    
                with open(os.path.join(self.base_dir, page_name), 'w', encoding='utf-8') as f:
                    f.write(str(soup))
                
                print(f"Saved as: {page_name}")
                
                # Clear all progress bars after completion
                print('\n\033[K', end='')  # Move to new line and clear it

        except Exception as e:
            print(f"Error processing {url}: {e}")

    def display_download_summary(self):
        """Display a summary table of downloaded URLs and their filenames"""
        if not self.url_filename_mapping:
            return
        
        print("\n" + "="*80)
        print("DOWNLOAD SUMMARY")
        print("="*80)
        
        # Calculate column widths
        max_url_length = max(len(url) for url in self.url_filename_mapping.keys())
        max_filename_length = max(len(filename) for filename in self.url_filename_mapping.values())
        
        # Ensure minimum widths and reasonable maximums
        url_width = max(min(max_url_length, 60), 20)
        filename_width = max(min(max_filename_length, 40), 15)
        
        # Headers
        print(f"{'URL':<{url_width}} | {'SAVED AS':<{filename_width}}")
        print("-" * url_width + "-+-" + "-" * filename_width)
        
        # Data rows
        for url, filename in self.url_filename_mapping.items():
            # Truncate URL if too long
            display_url = url if len(url) <= url_width else url[:url_width-3] + "..."
            print(f"{display_url:<{url_width}} | {filename:<{filename_width}}")
        
        print("="*80)
        print(f"Total files downloaded: {len(self.url_filename_mapping)}")
        print()

def main():
    print("""
__        __         _       ____                   _             _   
\ \      / /   ___  | |__   |  _ \    ___     ___  | | __   ___  | |_ 
 \ \ /\ / /   / _ \ | '_ \  | |_) |  / _ \   / __| | |/ /  / _ \ | __|
  \ V  V /   |  __/ | |_) | |  __/  | (_) | | (__  |   <  |  __/ | |_ 
   \_/\_/     \___| |_.__/  |_|      \___/   \___| |_|\_\  \___|  \__|
                                                                      
    """)
    print("WebSitePocket - Website Download Tool")
    print("1. Create new project")
    print("2. Load existing project") 
    print("3. Launch GUI")
    print("4. Remove project")
    choice = input("Enter your choice (1/2/3/4): ")

    if choice == '3':
        # Launch GUI
        gui_file = 'downloader_gui.py'
        if not os.path.exists(gui_file):
            print(f"Error: {gui_file} not found in current directory.")
            return
            
        try:
            import subprocess
            import sys
            print("Launching GUI...")
            subprocess.run([sys.executable, gui_file])
            return
        except Exception as e:
            print(f"Error launching GUI: {e}")
            print("Make sure PyQt5 is installed and downloader_gui.py is available.")
            return
    elif choice == '4':
        # Remove project
        projects = WebDownloader.list_projects()
        if not projects:
            print("No existing projects found.")
            return
        
        # Store projects in a list to maintain order
        project_list = list(projects.items())
        print("\nExisting projects:")
        for i, (name, data) in enumerate(project_list, 1):
            project_info = WebDownloader.get_project_info(name)
            size_info = f" - {project_info['formatted_size']}" if project_info else ""
            print(f"{i}. {name} ({len(data['urls'])} URLs{size_info})")
        
        project_input = input("\nEnter project number or name to remove: ")
        
        # Try to load by number first
        try:
            idx = int(project_input) - 1
            if 0 <= idx < len(project_list):
                project_name = project_list[idx][0]
            else:
                project_name = project_input
        except ValueError:
            project_name = project_input
        
        # Check if project exists
        if project_name not in projects:
            print(f"Project '{project_name}' not found.")
            return
        
        # Show project info
        project_info = WebDownloader.get_project_info(project_name)
        if project_info:
            print(f"\nProject: {project_info['name']}")
            print(f"URLs: {project_info['url_count']}")
            print(f"Folder size: {project_info['formatted_size']}")
            print(f"Created: {project_info['timestamp']}")
        
        # Confirm removal
        confirm = input(f"\nAre you sure you want to remove project '{project_name}'? (y/N): ").lower().strip()
        if confirm != 'y':
            print("Operation cancelled.")
            return
        
        # Ask about folder removal
        remove_folder = input("Also delete project folder and all downloaded files? (y/N): ").lower().strip()
        remove_folder = remove_folder == 'y'
        
        # Remove project
        success, message = WebDownloader.remove_project(project_name, remove_folder)
        print(message)
        return
    elif choice == '2':
        # Show existing projects
        projects = WebDownloader.list_projects()
        if not projects:
            print("No existing projects found.")
            return
        
        # Store projects in a list to maintain order
        project_list = list(projects.items())
        print("\nExisting projects:")
        for i, (name, data) in enumerate(project_list, 1):
            print(f"{i}. {name} ({len(data['urls'])} URLs)")
        
        project_input = input("\nEnter project number or name to load: ")
        
        # Try to load by number first
        try:
            idx = int(project_input) - 1
            if 0 <= idx < len(project_list):
                project_name = project_list[idx][0]
            else:
                project_name = project_input
        except ValueError:
            project_name = project_input
        
        downloader = WebDownloader.load_project(project_name)
        if not downloader:
            print(f"Project '{project_name}' not found.")
            return
    elif choice == '1':
        # Create new project
        project_name = input("Enter project name: ")
        downloader = WebDownloader(project_name)
        
        # Ask about replacing links (default Yes)
        replace_links = input("Replace all links with href='#'? (Y/n): ").lower().strip()
        downloader.replace_links = replace_links != 'n'
        
        # Ask about replacing form actions (default Yes)  
        replace_forms = input("Replace all form actions with action='#'? (Y/n): ").lower().strip()
        downloader.replace_forms = replace_forms != 'n'
        
        # Get URLs
        while True:
            url = input("Enter URL (or press Enter to finish): ").strip()
            if not url:
                break
            downloader.urls.append(url)
        
        # Save project data
        downloader.save_project_data()
    else:
        print("Invalid choice. Please select 1, 2, 3, or 4.")
        return
    
    # Process URLs
    for url in tqdm(downloader.urls, desc="Processing URLs"):
        print(f"\nProcessing {url}...")
        downloader.download_page(url)
        print(f"Finished processing {url}")
        print("-" * 50)

    # Display summary table
    downloader.display_download_summary()

if __name__ == "__main__":
    main()