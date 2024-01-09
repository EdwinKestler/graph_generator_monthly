import os
import io
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Define the Google Drive API scopes and service account file path
SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = r"C:\keyfile\clean-trees-410621-753ef42ab44d.json"  # Use a raw string for Windows path

# Create credentials using the service account file
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)

# Build the Google Drive service
drive_service = build('drive', 'v3', credentials=credentials)

def upload_file(file_path, parent_folder_id="1YufGqLGRrqpWRyGI_Ltv3pHNyu4MVHRM"):  # Corrected parent folder ID
    """Upload a file to Google Drive."""
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    # Get the current month and year
    now = datetime.now()
    month_year = now.strftime("%B_%Y_")

    file_metadata = {
        'name': month_year + os.path.basename(file_path),
        'parents': [parent_folder_id] if parent_folder_id else []
    }

    media = MediaFileUpload(file_path)

    file = drive_service.files().create(body=file_metadata,
                                        media_body=media,
                                        fields='id').execute()

    print(f"File ID: {file.get('id')}")

if __name__ == '__main__':
    # Example usage:
    file_path = r"D:\graph_generator_monthly-1\datos-csv\download-database.csv"  # Corrected Windows file path
    upload_file(file_path)