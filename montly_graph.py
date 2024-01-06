import sys
import os
from gui import WeatherGraphsApp
from PyQt6.QtWidgets import QApplication
                
#varify_and_create_folders
def verify_and_create_folders():
    # Define the main folder and subfolders
    main_folder = 'main_folder'
    subfolders = ['datos-csv', 'output-folder', 'images']

    # Create the main folder if it doesn't exist
    if not os.path.exists(main_folder):
        os.makedirs(main_folder)

    # Create the subfolders if they don't exist
    for subfolder in subfolders:
        subfolder_path = os.path.join(main_folder, subfolder)
        if not os.path.exists(subfolder_path):
            os.makedirs(subfolder_path)
                            
    
def resource_path(relative_path):
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)
    
def main():
    verify_and_create_folders()
    app = QApplication(sys.argv)
    window = WeatherGraphsApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()