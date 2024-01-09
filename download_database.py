import requests
import logging
import os

def get_confirm_token(response):
    """Retrieve confirmation token from the response cookies."""
    for key, value in response.cookies.items():
        if key.startswith('download_warning'):
            return value
    return None


def save_response_content(response, destination):
    """Save the content of the response to a file."""
    CHUNK_SIZE = 32768  # Constant variable names should be uppercase

    try:
        with open(destination, "wb") as f:
            for chunk in response.iter_content(CHUNK_SIZE):
                if chunk:  # filter out keep-alive new chunks
                    f.write(chunk)
    except IOError as e:
        logging.error(f"Error writing to {destination}: {e}")
        raise
    

def download_file_from_google_drive(file_id, destination):
    """Download a file from Google Drive."""
    URL = "https://drive.google.com/uc?export=download"

    try:
        session = requests.Session()
        response = session.get(URL, params={'id': file_id}, stream=True)

        # Check for valid response
        if response.status_code != 200:
            logging.error(f"Error downloading file: HTTP {response.status_code}")
            return False

        token = get_confirm_token(response)

        if token:
            params = {'id': file_id, 'confirm': token}
            response = session.get(URL, params=params, stream=True)

            if response.status_code != 200:
                logging.error(f"Error downloading file after confirming token: HTTP {response.status_code}")
                return False

        save_response_content(response, destination)
        return True

    except requests.RequestException as e:
        logging.error(f"Network error occurred: {e}")
        return False
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        return False

