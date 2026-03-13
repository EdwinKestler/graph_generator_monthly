import sys
import logging
import matplotlib
matplotlib.use('Agg')   # force non-interactive backend before any pyplot import
from PyQt6.QtWidgets import QApplication
from gui import WeatherGraphsApp

__version__ = "1.0.0"

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
