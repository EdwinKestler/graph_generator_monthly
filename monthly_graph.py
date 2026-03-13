import sys
import logging
from PyQt6.QtWidgets import QApplication
from gui import WeatherGraphsApp

logging.basicConfig(
    filename='graph_generator.log',
    level=logging.WARNING,
    format='%(asctime)s %(levelname)s %(module)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)


def main():
    app = QApplication(sys.argv)
    window = WeatherGraphsApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
