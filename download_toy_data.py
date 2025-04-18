from urllib.request import urlretrieve
import zipfile
import os

FOLDER_URL = 'https://owncloud.gwdg.de/index.php/s/3I1wGOdmh8W2XaZ/download'
DESTINATION = 'toy_data.zip'

def download() -> None:
    print('Downloading toy data...')
    urlretrieve(FOLDER_URL, DESTINATION)

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

