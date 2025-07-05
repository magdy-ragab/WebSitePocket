#!/usr/bin/env python3
"""
Demo script showing WebSitePocket functionality
"""

import os
import sys
from common import WebSitePocketCommon
from download import WebDownloader

def demo_filename_generation():
    """Demo the filename generation functionality"""
    print("=== FILENAME GENERATION DEMO ===")
    
    test_urls = [
        "https://example.com/",
        "https://example.com/about",
        "https://example.com/contact/",
        "https://example.com/page.php",
        "https://example.com/search?q=test",
        "https://example.com/search?q=different", 
        "https://example.com/products/item-1",
        "https://example.com/ar/",
        "https://example.com/en/home",
    ]
    
    existing_files = set()
    url_mapping = {}
    
    for url in test_urls:
        filename = WebSitePocketCommon.generate_html_filename(url, existing_files)
        existing_files.add(filename)
        url_mapping[url] = filename
        print(f"{url:<40} -> {filename}")
    
    print(f"\nGenerated {len(url_mapping)} unique filenames")
    return url_mapping

def demo_project_functions():
    """Demo project management functions"""
    print("\n=== PROJECT MANAGEMENT DEMO ===")
    
    # List existing projects
    projects = WebSitePocketCommon.list_projects()
    print(f"Current projects: {len(projects)}")
    for name, data in projects.items():
        print(f"  - {name}: {len(data.get('urls', []))} URLs")
    
    return projects

def demo_common_functions():
    """Demo common functions"""
    print("\n=== COMMON FUNCTIONS DEMO ===")
    
    print(f"Home directory: {WebSitePocketCommon.get_home_dir()}")
    print(f"Projects file: {WebSitePocketCommon.get_projects_file_path()}")
    
    # Test file size formatting
    test_sizes = [0, 512, 1024, 1536, 1048576, 2097152, 1073741824]
    print("\nFile size formatting:")
    for size in test_sizes:
        formatted = WebSitePocketCommon.format_file_size(size)
        print(f"  {size:>10} bytes -> {formatted}")

def main():
    print("WebSitePocket - Functionality Demo")
    print("=" * 50)
    
    # Demo filename generation
    demo_filename_generation()
    
    # Demo project functions  
    demo_project_functions()
    
    # Demo common functions
    demo_common_functions()
    
    print("\n" + "=" * 50)
    print("Demo completed successfully!")
    print("\nTo test the full application:")
    print("  CLI: python download.py")
    print("  GUI: python downloader_gui.py")

if __name__ == "__main__":
    main()
