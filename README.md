# Kiwix Downloader

Kiwix Downloader is a Python-based tool for downloading large `.zim` archive files from a list of URLs, with support for resuming incomplete downloads and handling concurrent downloads efficiently.

## Features
- Resumable downloads
- Thread-safe download progress
- Customizable download directory
- Concurrent downloads with retries

## Requirements
- Python 3.9+
- Docker (optional, for running in a container)

## Installation

1. Clone the repository:

   ```bash
   git clone git@github.com:jaelliot/kiwix-downloader.git
   cd kiwix-downloader
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Python Script

To run the downloader directly:

```bash
python kiwix-downloader.py --download-dir /path/to/download
```

- Use the `--verbose` flag for detailed logging.
- Specify the download directory with `--download-dir`.

### Docker

To build and run the Docker container:

1. Build the Docker image:

   ```bash
   docker build -t kiwix-downloader .
   ```

2. Run the container with a custom download directory:

   ```bash
   docker run -v /path/to/host/dir:/mnt/output-dir kiwix-downloader python kiwix-downloader.py --download-dir /mnt/output-dir
   ```

## License
This project is licensed under the MIT License.