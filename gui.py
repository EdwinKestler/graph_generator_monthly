import sys
import subprocess
import os
import pandas as pd
from datetime import date
from PyQt6.QtWidgets import (
    QApplication, QLabel, QVBoxLayout, QWidget, QPushButton, QFileDialog,
    QLineEdit, QProgressBar, QDialog, QMessageBox, QHBoxLayout
)
import webbrowser
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QPixmap, QMovie
from data_processing import detect_date_format
from download_database import download_file_from_google_drive
from graph_generation import GraphGenerator, plot_with_matplotlib
from map_viewer import build_station_summary, generate_map


def resource_path(relative_path):
    """Resolve asset paths for both dev and PyInstaller bundle contexts."""
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


class LoadingDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setModal(True)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)

        self.loading_movie = QMovie(resource_path("assets/spinning-loading.gif"))
        self.loading_label = QLabel(self)
        self.loading_label.setMovie(self.loading_movie)
        self.loading_movie.start()

        self._layout = QVBoxLayout()
        self._layout.addWidget(self.loading_label)
        self.setLayout(self._layout)


def open_map_in_browser(map_path: str) -> None:
    """Open a mapa_*.html file in the system default browser."""
    webbrowser.open(f"file:///{map_path.replace(os.sep, '/')}")


class DownloadWorker(QThread):
    finished_signal = pyqtSignal(str, str)   # (final_path, display_message)  on success
    error_signal    = pyqtSignal(str)         # error message on failure

    FILE_ID = '19gcM1e5rb-HvJ-MVhNSZgsinNhN0S79Y'

    def run(self):
        data_dir  = 'data'
        os.makedirs(data_dir, exist_ok=True)
        temp_path = os.path.join(data_dir, '_download_temp.csv')

        try:
            success = download_file_from_google_drive(self.FILE_ID, temp_path)
            if not success:
                self.error_signal.emit(
                    'No se pudo descargar la base de datos. '
                    'Verifique su conexión e intente de nuevo.'
                )
                return

            df_dates   = pd.read_csv(temp_path, usecols=['fecha'], low_memory=False)
            sample     = str(df_dates['fecha'].dropna().iloc[0]).strip()
            date_fmt   = detect_date_format(sample)
            fechas     = pd.to_datetime(df_dates['fecha'], format=date_fmt)
            data_start = fechas.min().strftime('%Y%m')
            data_end   = fechas.max().strftime('%Y%m')

            download_date = date.today().strftime('%Y%m%d')
            final_name    = f'insivumeh_{download_date}_{data_start}_a_{data_end}.csv'
            final_path    = os.path.join(data_dir, final_name)

            os.replace(temp_path, final_path)

            msg = (
                f'Base de datos descargada exitosamente.\n\n'
                f'Archivo: {final_name}\n'
                f'Período de datos: {data_start[:4]}-{data_start[4:]} '
                f'a {data_end[:4]}-{data_end[4:]}'
            )
            self.finished_signal.emit(final_path, msg)

        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            self.error_signal.emit(f'Ocurrió un error durante la descarga: {str(e)}')


class MapWorker(QThread):
    finished_signal = pyqtSignal(str, str)   # (map_path, status_message)
    error_signal    = pyqtSignal(str)

    def __init__(self, csv_file_path, output_directory):
        super().__init__()
        self.csv_file_path    = csv_file_path
        self.output_directory = output_directory

    def run(self):
        try:
            summary  = build_station_summary(self.csv_file_path)
            map_path = generate_map(summary, self.output_directory)
            msg      = f'Mapa generado: {len(summary)} estaciones — {map_path}'
            self.finished_signal.emit(map_path, msg)
        except Exception as e:
            self.error_signal.emit(str(e))


class GraphWorker(QThread):
    progress_signal = pyqtSignal(int)
    plot_data_signal = pyqtSignal(object)
    finished_signal = pyqtSignal(str)

    def __init__(self, output_directory, csv_file_path):
        super().__init__()
        self.output_directory = output_directory
        self.csv_file_path = csv_file_path

    def run(self):
        generator = GraphGenerator()
        generator.progress_signal.connect(self.progress_signal)
        generator.plot_data_signal.connect(self.plot_data_signal)
        generator.completion_signal.connect(self.finished_signal)
        generator.generate_graphs(self.output_directory, self.csv_file_path)


class WeatherGraphsApp(QWidget):
    def __init__(self):
        super().__init__()
        self._last_run_folder = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Generador de Graficas Mensual")
        main_layout = QVBoxLayout()

        logo_layout = QHBoxLayout()
        self.setup_logo(logo_layout, resource_path("assets/logo_insivumeh.png"))
        self.setup_logo(logo_layout, resource_path("assets/waterco-logo.png"))
        self.setup_logo(logo_layout, resource_path("assets/IUCN_logo.png"))
        main_layout.addLayout(logo_layout)

        self.download_button = QPushButton("1. Bajar base de datos Mensual .CSV de INSIVUMEH")
        self.download_button.clicked.connect(self.download_database)
        main_layout.addWidget(self.download_button)

        self.directory_label = QLabel("Directorio de salida:")
        main_layout.addWidget(self.directory_label)

        self.directory_edit = QLineEdit()
        main_layout.addWidget(self.directory_edit)

        self.directory_browse_button = QPushButton("2. Seleccionar Directorio de Salida")
        self.directory_browse_button.clicked.connect(self.browse_directory)
        main_layout.addWidget(self.directory_browse_button)

        self.csv_label = QLabel("Base de datos .CSV:")
        main_layout.addWidget(self.csv_label)

        self.csv_edit = QLineEdit()
        main_layout.addWidget(self.csv_edit)

        self.csv_browse_button = QPushButton("3. Selecionar base de datos .csv a graficar")
        self.csv_browse_button.clicked.connect(self.browse_csv)
        main_layout.addWidget(self.csv_browse_button)

        self.generate_button = QPushButton("4. Generar Graficos mensuales")
        self.generate_button.clicked.connect(self.generate_graphs_wrapper)
        main_layout.addWidget(self.generate_button)

        self.map_button = QPushButton("4b. Generar Mapa de Estaciones")
        self.map_button.clicked.connect(self.generate_map_wrapper)
        main_layout.addWidget(self.map_button)

        self.explore_button = QPushButton("5. Explorar graficas generadas")
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
        self.status_label.setText("Descargando base de datos... por favor espere.")
        self.show_loading()
        self.download_button.setEnabled(False)

        self.download_worker = DownloadWorker()
        self.download_worker.finished_signal.connect(self._on_download_complete)
        self.download_worker.error_signal.connect(self._on_download_error)
        self.download_worker.start()

    def _on_download_complete(self, final_path: str, msg: str):
        self.hide_loading()
        self.download_button.setEnabled(True)
        self.csv_edit.setText(final_path)
        self.status_label.setText("Descarga completada.")
        QMessageBox.information(self, 'Descarga completada', msg)

    def _on_download_error(self, error_msg: str):
        self.hide_loading()
        self.download_button.setEnabled(True)
        self.status_label.setText("Error en la descarga.")
        QMessageBox.critical(self, 'Error de descarga', error_msg)

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

    # Function to open the output directory
    def open_output_directory(self):
        target = self._last_run_folder or self.directory_edit.text()
        if target:
            if sys.platform == "win32":
                os.startfile(target)
            elif sys.platform == "darwin":
                subprocess.check_call(["open", target])
            else:
                subprocess.check_call(["xdg-open", target])

    # Function to generate graphs
    def generate_graphs_wrapper(self):
        output_directory = self.directory_edit.text()
        csv_file_path = self.csv_edit.text()

        if not (output_directory and csv_file_path):
            self.status_label.setText("Porfavor provea todos los requisitos para genrar las graficas!")
            return

        self.status_label.setText("Procesando datos... porfavor espere.")
        self.show_loading()

        self.graph_worker = GraphWorker(output_directory, csv_file_path)
        self.graph_worker.progress_signal.connect(self.update_progress)
        self.graph_worker.plot_data_signal.connect(plot_with_matplotlib)
        self.graph_worker.finished_signal.connect(self.on_graphs_complete)
        self.graph_worker.start()

    def generate_map_wrapper(self):
        csv_file_path    = self.csv_edit.text()
        output_directory = self.directory_edit.text()

        if not csv_file_path or not output_directory:
            self.status_label.setText(
                "Por favor seleccione el CSV y el directorio de salida antes de generar el mapa."
            )
            return

        self.status_label.setText("Generando mapa de estaciones...")
        self.show_loading()

        self.map_worker = MapWorker(csv_file_path, output_directory)
        self.map_worker.finished_signal.connect(self._on_map_complete)
        self.map_worker.error_signal.connect(self._on_map_error)
        self.map_worker.start()

    def _on_map_complete(self, map_path: str, msg: str):
        self.hide_loading()
        self.status_label.setText(msg)
        open_map_in_browser(map_path)

    def _on_map_error(self, error_msg: str):
        self.hide_loading()
        QMessageBox.critical(self, "Error al generar mapa", error_msg)
        self.status_label.setText("Error al generar el mapa.")

    def update_progress(self, value):
        self.progress.setValue(value)

    def on_graphs_complete(self, message):
        self.hide_loading()
        self.status_label.setText(message)
        if not message.startswith("Error"):
            # Parse the graficas_* subfolder path from the completion message if present
            import re
            m = re.search(r'(graficas_\S+)', message)
            if m:
                base = self.directory_edit.text()
                candidate = os.path.join(base, m.group(1))
                if os.path.isdir(candidate):
                    self._last_run_folder = candidate
            self.explore_button.setEnabled(True)


def main():
    app = QApplication(sys.argv)
    window = WeatherGraphsApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
