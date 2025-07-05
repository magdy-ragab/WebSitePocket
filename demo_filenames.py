#!/usr/bin/env python3

from common import WebSitePocketCommon

# Your original problematic URLs
urls = [
    'https://unionaire.com/',
    'https://unionaire.com/ar/',
    'https://unionaire.com/product-category/screens/',
    'https://unionaire.com/product/tv-43-inches-smart-from-unionaire-q-led-q43ux820/'
]

print("URL to Filename Mapping (Your URLs):")
print("="*80)
print(f"{'URL':<60} | {'SAVED AS':<30}")
print("-" * 60 + "-+-" + "-" * 30)

existing_files = set()
for url in urls:
    filename = WebSitePocketCommon.generate_html_filename(url, existing_files)
    existing_files.add(filename)
    display_url = url if len(url) <= 60 else url[:57] + "..."
    print(f"{display_url:<60} | {filename:<30}")

print("="*80)
print(f"Total files: {len(urls)}")
print("\nNo more overwrites! Each URL gets its unique filename.")
