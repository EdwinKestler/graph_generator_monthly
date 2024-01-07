import sys
import subprocess
import os
from PyQt6.QtWidgets import (QApplication, QLabel, QVBoxLayout, QWidget, QPushButton, QFileDialog, QLineEdit, QProgressBar, QDialog, QMessageBox, QHBoxLayout)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QPixmap, QMovie
from download_database import download_file_from_google_drive
from graph_generation import GraphGenerator, plot_with_matplotlib

class LoadingDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setModal(True)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)

        self.loading_movie = QMovie("images\\spinning-loading.gif")
        self.loading_label = QLabel(self)
        self.loading_label.setMovie(self.loading_movie)
        self.loading_movie.start()

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.loading_label)
        self.setLayout(self.layout)

class Worker(QThread):
    progress_signal = pyqtSignal(int)
    plot_data_signal = pyqtSignal(object)
    finished_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()

class WeatherGraphsApp(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Generador de Graficas Mensual")
        main_layout = QVBoxLayout()

        logo_layout = QHBoxLayout()
        self.setup_logo(logo_layout, "images\\logo_insivumeh.png")
        self.setup_logo(logo_layout, "images\\waterco-logo.png")
        self.setup_logo(logo_layout, "images\\IUCN_logo.png")
        main_layout.addLayout(logo_layout)

        self.download_button = QPushButton("1. Bajar base de datos a: datos-CSV\\download-database.csv")
        self.download_button.clicked.connect(self.download_database)
        main_layout.addWidget(self.download_button)

        self.directory_label = QLabel("Directorio de salida:")
        main_layout.addWidget(self.directory_label)

        self.directory_edit = QLineEdit()
        main_layout.addWidget(self.directory_edit)

        self.directory_browse_button = QPushButton("2. Seleccionar Directorio")
        self.directory_browse_button.clicked.connect(self.browse_directory)
        main_layout.addWidget(self.directory_browse_button)

        self.csv_label = QLabel("Base de datos .CSV:")
        main_layout.addWidget(self.csv_label)

        self.csv_edit = QLineEdit()
        main_layout.addWidget(self.csv_edit)

        self.csv_browse_button = QPushButton("3. Selecionar Archivo .CSV")
        self.csv_browse_button.clicked.connect(self.browse_csv)
        main_layout.addWidget(self.csv_browse_button)

        self.generate_button = QPushButton("4. Generar Graficos")
        self.generate_button.clicked.connect(self.generate_graphs_wrapper)
        main_layout.addWidget(self.generate_button)

        self.explore_button = QPushButton("5. Explorar archivos generados")
        self.explore_button.setEnabled(False)
        self.explore_button.clicked.connect(self.open_output_directory)
        main_layout.addWidget(self.explore_button)

        self.progress = QProgressBar(self)
        main_layout.addWidget(self.progress)

        self.status_label = QLabel("")
        main_layout.addWidget(self.status_label)

        self.about_button = QPushButton("Acerca de")
        self.about_button.clicked.connect(self.show_about)
        main_layout.addWidget(self.about_button)

        self.setLayout(main_layout)
        self.loading_dialog = None

    def setup_logo(self, layout, image_path):
        logo = QLabel(self)
        pixmap = QPixmap(image_path)
        resized_pixmap = pixmap.scaled(128, 128, Qt.AspectRatioMode.KeepAspectRatio)
        logo.setPixmap(resized_pixmap)
        layout.addWidget(logo)

    def show_loading(self):
        self.loading_dialog = LoadingDialog(self)
        self.loading_dialog.show()

    def hide_loading(self):
        if self.loading_dialog:
            self.loading_dialog.accept()
        
    # Function to download the database
    def download_database(self):
        try:
            self.show_loading()  # Show loading spinner
            file_id = '19gcM1e5rb-HvJ-MVhNSZgsinNhN0S79Y'
            destination = 'datos-csv\\download-database.csv'
            
            # Check if the directory exists and create if not
            os.makedirs(os.path.dirname(destination), exist_ok=True)
            
            download_file_from_google_drive(file_id, destination)
            
            # Update the CSV file path input after download
            self.csv_edit.setText(destination)
            
            # Notify the user that the database has been downloaded
            QMessageBox.information(self, 'Descarga completada', 'Base de datos descargada Exitosamente!')
            
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Ocurrió un error durante la descarga: {str(e)}')
        finally:
            self.hide_loading()  # Hide loading spinner whether download succeeds or fails
        
    # Function to show "About" dialog
    def show_about(self):
        about_message = """
        Generador de Gráficos Climáticos

        Esta aplicación ha sido desarrollada bajo la Licencia de Código Abierto MIT.

        Se concede permiso, de forma gratuita, a cualquier persona que obtenga una copia de este software y de los archivos de documentación asociados (el "Software"), para utilizar el Software sin restricciones, incluyendo sin limitación los derechos a usar, copiar, modificar, fusionar, publicar, distribuir, sublicenciar y/o vender copias del Software, y permitir que las personas a las que se les proporcione el Software hagan lo mismo, sujeto a las siguientes condiciones:

        La notificación de derechos de autor anterior y esta notificación de permiso deberán ser incluidas en todas las copias o partes sustanciales del Software.

        EL SOFTWARE SE PROPORCIONA "TAL CUAL", SIN GARANTÍA DE NINGÚN TIPO, EXPRESA O IMPLÍCITA, INCLUYENDO, PERO NO LIMITADO A, LAS GARANTÍAS DE COMERCIABILIDAD, IDONEIDAD PARA UN PROPÓSITO PARTICULAR Y NO INFRACCIÓN. EN NINGÚN CASO LOS AUTORES O TITULARES DE LOS DERECHOS DE AUTOR SERÁN RESPONSABLES DE CUALQUIER RECLAMACIÓN, DAÑOS U OTRA RESPONSABILIDAD, YA SEA EN UNA ACCIÓN DE CONTRATO, AGRAVIO O DE OTRO TIPO, DERIVADA DE, FUERA DE O EN CONEXIÓN CON EL SOFTWARE O SU USO U OTRO TIPO DE ACCIONES EN EL SOFTWARE.
        """
        QMessageBox.about(self, "Acerca del Generador de Gráficos Climáticos", about_message)
        
    # Function to open the output directory            
    def browse_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Seleccionar Directorio de Salida")
        if directory:
            self.directory_edit.setText(directory)

    # Function to browse the CSV file
    def browse_csv(self):
        file_filter = "CSV Files (*.csv);;All Files (*)"
        file_name, _ = QFileDialog.getOpenFileName(self, "seleccionar base de datos csv", "", file_filter)
        if file_name:
            self.csv_edit.setText(file_name)
            
    #funciton to open the output directory
    def open_output_directory(self):
        output_directory = self.directory_edit.text()
        if output_directory:
            # Depending on your OS, the approach to open a folder might differ
            if sys.platform == "win32":
                os.startfile(output_directory)
            elif sys.platform == "darwin":  # macOS
                subprocess.check_call(["open", output_directory])
            else:  # linux variants
                subprocess.check_call(["xdg-open", output_directory])    
            
    #Fucntion to generate graphs
    def generate_graphs_wrapper(self):
        output_directory = self.directory_edit.text()
        csv_file_path = self.csv_edit.text()

        if not (output_directory and csv_file_path):
            self.status_label.setText("Porfavor provea todos los requisitos para genrar las graficas!")
            return

        self.status_label.setText("Procesando datos... porfavor espere.")
        self.show_loading()

        self.graph_generator = GraphGenerator()
        self.graph_generator.progress_signal.connect(self.update_progress)
        self.graph_generator.plot_data_signal.connect(plot_with_matplotlib)
        self.graph_generator.completion_signal.connect(lambda message: self.status_label.setText(message))

        self.graph_generator.generate_graphs(output_directory, csv_file_path)

    def update_progress(self, value):
        self.progress.setValue(value)

    def graphs_generated(self):
        self.status_label.setText("Graficos generados exitosamente!")
        self.explore_button.setEnabled(True)

def main():
    app = QApplication(sys.argv)
    window = WeatherGraphsApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()