import os
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse
import logging
import argparse
import json
from time import sleep
from threading import Lock
import hashlib
from tqdm import tqdm

# Constants
URL_FILE_PATH = "/mnt/e/kiwix/urls.txt"
MAX_WORKERS = 5
PROGRESS_FILE = os.path.join("/mnt/e/kiwix", "download_progress.json")
RETRY_COUNT = 3
CHUNK_SIZE = 8192

# Lock for thread safety
progress_lock = Lock()

def setup_logging(verbose):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')

def ensure_directory_exists(directory):
    os.makedirs(directory, exist_ok=True)

def get_filename_from_url(url):
    parsed_url = urlparse(url)
    filename = os.path.basename(parsed_url.path)
    return filename if filename else f"unnamed_file_{hashlib.md5(url.encode()).hexdigest()[:8]}"

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_progress(progress):
    with progress_lock:
        with open(PROGRESS_FILE, 'w') as f:
            json.dump(progress, f, indent=4)

def download_file(url, download_dir, progress):
    try:
        filename = get_filename_from_url(url)
        filepath = os.path.join(download_dir, filename)

        headers = {}
        mode = 'wb'
        initial_pos = 0

        if url in progress and progress[url] != 'failed' and os.path.exists(filepath):
            initial_pos = os.path.getsize(filepath)
            headers['Range'] = f'bytes={initial_pos}-'
            mode = 'ab'

        for attempt in range(RETRY_COUNT):
            try:
                with requests.get(url, stream=True, timeout=30, headers=headers) as response:
                    response.raise_for_status()
                    total_size = int(response.headers.get('content-length', 0)) + initial_pos
                    
                    with open(filepath, mode) as f, tqdm(
                        desc=filename,
                        initial=initial_pos,
                        total=total_size,
                        unit='iB',
                        unit_scale=True,
                        unit_divisor=1024,
                    ) as progress_bar:
                        for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                            if chunk:
                                size = f.write(chunk)
                                progress_bar.update(size)
                        
                        progress[url] = 'completed'
                        save_progress(progress)
                        logging.info(f"Downloaded: {filename}")
                        return filename, None
            except requests.RequestException as e:
                logging.warning(f"Attempt {attempt + 1} failed for {url}. Error: {str(e)}. Retrying...")
                sleep(2 ** attempt)

        logging.error(f"Failed to download {url} after {RETRY_COUNT} attempts.")
        progress[url] = 'failed'
        save_progress(progress)
        return filename, "Download failed after retries"

    except Exception as e:
        logging.error(f"Unhandled error while downloading {url}: {str(e)}")
        progress[url] = 'failed'
        save_progress(progress)
        return url, str(e)

def read_urls(file_path):
    with open(file_path, 'r') as f:
        return [line.strip() for line in f if line.strip()]

def main(verbose, download_dir):
    setup_logging(verbose)
    ensure_directory_exists(download_dir)
    urls = read_urls(URL_FILE_PATH)
    progress = load_progress()

    remaining_urls = [url for url in urls if url not in progress or progress[url] == 'failed']

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_url = {executor.submit(download_file, url, download_dir, progress): url for url in remaining_urls}
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            filename, error = future.result()
            if error:
                logging.error(f"Error downloading {filename} from {url}: {error}")
            else:
                logging.info(f"Successfully downloaded: {filename}")

    logging.info("Download process completed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download files from a list of URLs.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Increase output verbosity")
    parser.add_argument("-d", "--download-dir", default="/mnt/e/kiwix/archives", help="Specify the download directory")
    args = parser.parse_args()

    main(args.verbose, args.download_dir)
