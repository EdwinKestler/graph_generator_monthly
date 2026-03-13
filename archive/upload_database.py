import os
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

def upload_to_drive(file_path, service_account_file, parent_folder_id="1YufGqLGRrqpWRyGI_Ltv3pHNyu4MVHRM"):
    """Upload a file to Google Drive."""
    # Define the Google Drive API scopes
    SCOPES = ['https://www.googleapis.com/auth/drive']
    
    # Create credentials using the service account file
    credentials = service_account.Credentials.from_service_account_file(
        service_account_file, scopes=SCOPES)

    # Build the Google Drive service
    drive_service = build('drive', 'v3', credentials=credentials)

    if not os.path.exists(file_path):
        return f"File not found: {file_path}"

    # Get the current month and year for file naming
    now = datetime.now()
    month_year = now.strftime("%B_%Y_")

    file_metadata = {
        'name': month_year + os.path.basename(file_path),
        'parents': [parent_folder_id] if parent_folder_id else []
    }

    media = MediaFileUpload(file_path)

    file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()

    return f"File ID: {file.get('id')}"  # Return the file ID after upload
