#!/usr/bin/env python3

from common import WebSitePocketCommon

urls = [
    'https://unionaire.com/',
    'https://unionaire.com/ar/',
    'https://unionaire.com/product-category/screens/',
    'https://unionaire.com/product/tv-43-inches-smart-from-unionaire-q-led-q43ux820/'
]

print("Testing filename generation:")
existing_files = set()
for url in urls:
    try:
        filename = WebSitePocketCommon.generate_html_filename(url, existing_files)
        existing_files.add(filename)
        print(f'{url} -> {filename}')
    except Exception as e:
        print(f'Error with {url}: {e}')
        import traceback
        traceback.print_exc()
