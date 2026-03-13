import re
import requests
import logging
import os

CHUNK_SIZE = 32768


def _extract_token(response):
    """
    Extract the Google Drive virus-scan confirmation token.

    Checks two locations in order:
      1. Cookie named 'download_warning'  (pre-2023 behaviour, still present on
         some responses)
      2. 'confirm=<value>' query parameter embedded in the HTML warning page
         body (post-2023 behaviour for files that trigger the interstitial)

    Returns the token string, or None if no interstitial was detected (small
    files are served directly without a confirmation step).
    """
    # Path 1 — cookie (legacy)
    for key, value in response.cookies.items():
        if key.startswith('download_warning'):
            return value

    # Path 2 — HTML body regex (current GDrive behaviour)
    content_type = response.headers.get('Content-Type', '')
    if 'text/html' in content_type:
        match = re.search(r'confirm=([0-9A-Za-z_]+)', response.text)
        if match:
            return match.group(1)

    return None


def save_response_content(response, destination):
    """
    Stream response body to disk in 32 KB chunks.

    Raises ValueError if the first bytes look like an HTML page rather than
    the expected CSV — catches the case where Google returns a warning page
    instead of the file.
    """
    try:
        first_chunk = True
        with open(destination, "wb") as f:
            for chunk in response.iter_content(CHUNK_SIZE):
                if not chunk:
                    continue
                if first_chunk:
                    first_chunk = False
                    if chunk.lstrip()[:1] == b'<':
                        raise ValueError(
                            "Google Drive returned an HTML page instead of the "
                            "CSV file. The confirmation token may be missing or "
                            "the file ID may be incorrect."
                        )
                f.write(chunk)
    except IOError as e:
        logging.error(f"Error writing to {destination}: {e}")
        raise


def download_file_from_google_drive(file_id, destination):
    """
    Download a publicly shared file from Google Drive.

    Handles the virus-scan confirmation interstitial Google shows for large
    files by extracting the confirm token from either the response cookies
    (legacy) or the HTML warning page body (current behaviour).

    Args:
        file_id (str):      Google Drive file ID.
        destination (str):  Local path where the file will be saved.

    Returns:
        True on success, False on any network or HTTP error.

    Raises:
        ValueError: if Google returns an HTML warning page instead of the file
                    (indicates a missing/expired token or wrong file ID).
        IOError:    if the local file cannot be written.
    """
    URL = "https://drive.google.com/uc?export=download"

    try:
        session = requests.Session()
        response = session.get(URL, params={'id': file_id}, stream=True)

        if response.status_code != 200:
            logging.error(f"Error downloading file: HTTP {response.status_code}")
            return False

        token = _extract_token(response)

        if token:
            response = session.get(URL, params={'id': file_id, 'confirm': token}, stream=True)
            if response.status_code != 200:
                logging.error(f"Error downloading after confirmation: HTTP {response.status_code}")
                return False

        save_response_content(response, destination)
        return True

    except requests.RequestException as e:
        logging.error(f"Network error occurred: {e}")
        return False
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        return False
