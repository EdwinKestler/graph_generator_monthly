import sys
from PyQt6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout
from PyQt6.QtGui import QMovie

class TestApp(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Spinner Test")
        self.layout = QVBoxLayout()
        self.loading_movie = QMovie("images\\spinning-loading.gif")
        self.loading_label = QLabel(self)
        self.loading_label.setMovie(self.loading_movie)
        self.loading_movie.start()
        self.layout.addWidget(self.loading_label)
        self.setLayout(self.layout)

def main():
    app = QApplication(sys.argv)
    window = TestApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()