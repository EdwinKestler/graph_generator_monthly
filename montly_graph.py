import sys
from PyQt6.QtWidgets import QApplication
from gui import WeatherGraphsApp


def main():
    app = QApplication(sys.argv)
    window = WeatherGraphsApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
