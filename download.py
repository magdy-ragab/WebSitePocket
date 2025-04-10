import os
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
from tqdm import tqdm
from datetime import datetime

class WebDownloader:
    def __init__(self, project_name):
        self.project_name = project_name
        self.base_dir = os.path.join(os.getcwd(), 'projects', project_name)
        self.links_file = os.path.join(self.base_dir, 'links.json')
        self.projects_file = os.path.join(os.getcwd(), 'projects', 'projects.json')
        self.urls = []
        self.replace_links = False
        self.replace_forms = False
        self.total_files = 0
        self.progress_callback = None
        self.file_callback = None
        self.abort = False
        self.setup_directories()

    def set_progress_callback(self, callback):
        self.progress_callback = callback

    def set_file_callback(self, callback):
        """Set callback for individual file progress"""
        self.file_callback = callback

    def setup_directories(self):
        """Create project directories"""
        directories = ['images', 'js', 'css', 'fonts']
        os.makedirs(self.base_dir, exist_ok=True)
        for dir_name in directories:
            os.makedirs(os.path.join(self.base_dir, dir_name), exist_ok=True)

    def save_links(self):
        """Save URLs to JSON file"""
        with open(self.links_file, 'w') as f:
            json.dump({'urls': self.urls}, f, indent=4)

    def save_project_data(self):
        """Save project data to projects.json"""
        projects_data = self.load_projects_data()
        projects_data[self.project_name] = {
            'urls': self.urls,
            'replace_links': self.replace_links,
            'replace_forms': self.replace_forms,
            'timestamp': datetime.now().isoformat(),
            'base_dir': self.base_dir
        }
        
        os.makedirs(os.path.dirname(self.projects_file), exist_ok=True)
        with open(self.projects_file, 'w') as f:
            json.dump(projects_data, f, indent=4)

    def load_projects_data(self):
        """Load all projects data"""
        try:
            with open(self.projects_file, 'r') as f:
                return json.load(f)
        except:
            return {}

    @classmethod
    def list_projects(cls):
        """List all saved projects"""
        projects_file = os.path.join(os.getcwd(), 'projects', 'projects.json')
        try:
            with open(projects_file, 'r') as f:
                projects = json.load(f)
            return projects
        except:
            return {}

    @classmethod
    def load_project(cls, project_name):
        """Load existing project"""
        projects = cls.list_projects()
        if project_name in projects:
            downloader = cls(project_name)
            project_data = projects[project_name]
            downloader.urls = project_data['urls']
            downloader.replace_links = project_data['replace_links']
            downloader.replace_forms = project_data.get('replace_forms', False)  # Default False for backward compatibility
            return downloader
        return None

    def download_file(self, url, local_path, position=1):
        """Download a file from URL with nested progress bar"""
        try:
            response = requests.get(url, stream=True)
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            filename = os.path.basename(local_path)
            
            if self.file_callback:
                self.file_callback(downloaded, total_size, filename)
            
            with open(local_path, 'wb') as f:
                for data in response.iter_content(chunk_size=1024):
                    if self.abort:
                        return False
                    size = f.write(data)
                    downloaded += size
                    if self.file_callback:
                        self.file_callback(downloaded, total_size, filename)
                        
            return True
        except Exception as e:
            print(f"Error downloading {url}: {e}")
            return False

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
                
                # Replace all links if option is enabled
                if self.replace_links:
                    for link in soup.find_all('a'):
                        link['href'] = '#'
                
                # Replace all form actions if option is enabled
                if self.replace_forms:
                    for form in soup.find_all('form'):
                        form['action'] = '#'
                
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
                page_name = os.path.basename(urlparse(url).path)
                if not page_name:
                    page_name = 'index.html'
                elif not page_name.endswith('.html'):
                    page_name += '.html'
                    
                with open(os.path.join(self.base_dir, page_name), 'w', encoding='utf-8') as f:
                    f.write(str(soup))
                
                # Clear all progress bars after completion
                print('\n\033[K', end='')  # Move to new line and clear it

        except Exception as e:
            print(f"Error processing {url}: {e}")

def main():
    print("\nWebsite Downloader")
    print("1. Create new project")
    print("2. Load existing project")
    choice = input("Enter your choice (1/2): ")

    if choice == '2':
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
    else:
        # Create new project
        project_name = input("Enter project name: ")
        downloader = WebDownloader(project_name)
        
        # Ask about replacing links
        replace_links = input("Replace all links with href='#'? (y/n): ").lower().strip()
        downloader.replace_links = replace_links == 'y'
        
        # Ask about replacing form actions
        replace_forms = input("Replace all form actions with action='#'? (y/n): ").lower().strip()
        downloader.replace_forms = replace_forms == 'y'
        
        # Get URLs
        while True:
            url = input("Enter URL (or press Enter to finish): ").strip()
            if not url:
                break
            downloader.urls.append(url)
        
        # Save project data
        downloader.save_project_data()
    
    # Process URLs
    for url in tqdm(downloader.urls, desc="Processing URLs"):
        print(f"\nProcessing {url}...")
        downloader.download_page(url)
        print(f"Finished processing {url}")
        print("-" * 50)

if __name__ == "__main__":
    main()