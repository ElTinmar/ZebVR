from urllib.request import urlretrieve
import zipfile
import os
import sys

FOLDER_URL = 'https://owncloud.gwdg.de/index.php/s/qkoXus2Ez28WJ86/download'
DESTINATION = 'toy_data.zip'

def download() -> None:

    def download_progress_hook(block_num, block_size, total_size):
        if total_size <= 0:
            # Total size unknown
            sys.stdout.write(f"\rDownloaded {block_num * block_size * 1/(1024**2):.2f} MB")
            sys.stdout.flush()
        else:
            downloaded = block_num * block_size
            percent = min(100, downloaded * 100 / total_size)
            bar_length = 50
            filled_length = int(bar_length * percent // 100)
            bar = '=' * filled_length + '-' * (bar_length - filled_length)
            sys.stdout.write(f'\rDownloading: |{bar}| {percent:5.1f}%')
            sys.stdout.flush()

    print('Downloading toy data...')
    urlretrieve(FOLDER_URL, DESTINATION, reporthook=download_progress_hook)
    print('\nDownload complete')

def extract() -> None:
    print(f'Extracting {DESTINATION}...')
    with zipfile.ZipFile(DESTINATION, 'r') as zip_ref:
        zip_ref.extractall()
    print("Extraction complete.")

def cleanup() -> None:
    print('Cleaning up')
    if os.path.isfile(DESTINATION):
        os.remove(DESTINATION)

if __name__ == '__main__':
    try:
        download()
        extract()
    finally:
        cleanup()

