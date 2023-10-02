import sys
import os
import pandas as pd
from PyQt6.QtWidgets import (QApplication, QLabel, QVBoxLayout, QWidget, QPushButton, QFileDialog, QLineEdit, QProgressBar)
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtCore import Qt
from bokeh.plotting import output_file, save
from bokeh.models import Range1d, LinearAxis, HoverTool
from bokeh.plotting import figure
import matplotlib.pyplot as plt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtWidgets import QHBoxLayout
import subprocess
import requests

#get_confirm_token, save_response_content, download_file_from_google_drive
def get_confirm_token(response):
    for key, value in response.cookies.items():
        if key.startswith('download_warning'):
            return value

    return None

#save_response_content
def save_response_content(response, destination):
    CHUNK_SIZE = 32768

    with open(destination, "wb") as f:
        for chunk in response.iter_content(CHUNK_SIZE):
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)
                
#download_file_from_google_drive
def download_file_from_google_drive(file_id, destination):
    URL = "https://drive.google.com/uc?export=download"
    
    session = requests.Session()
    response = session.get(URL, params = { 'id' : file_id }, stream = True)
    token = get_confirm_token(response)
    
    if token:
        params = { 'id' : file_id, 'confirm' : token }
        response = session.get(URL, params = params, stream = True)
    
    save_response_content(response, destination)
    
def resource_path(relative_path):
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

class Worker(QThread):
    progress_signal = pyqtSignal(str)
    plot_data_signal = pyqtSignal(object)


    def __init__(self, grouped_data, directory_img, directory_html):
        super().__init__()
        self.grouped_data = grouped_data
        self.directory_img = directory_img
        self.directory_html = directory_html

    def run(self):
        for name, group in self.grouped_data:
            plot_data = generate_graphs_worker((name, group, self.directory_img, self.directory_html))
            self.plot_data_signal.emit(plot_data)
            self.progress_signal.emit(name)

def generate_graphs_worker(args):
    estacion,group, directory_img, directory_html = args

        
    # Load the CSV data
    # Extract data specific to the station passed into this function
    df = group

    # Convert 'fecha' column to datetime format and sort
    df['fecha'] = pd.to_datetime(df['fecha'], format="%d/%m/%Y")
    latest_date = df['fecha'].max()
    thirty_days_ago = latest_date - pd.Timedelta(days=30)
    last_30_days_data = df[df['fecha'] >= thirty_days_ago]
    last_30_days_data = last_30_days_data.sort_values("fecha")

    # Replacing underscores with spaces in 'Nombre'
    last_30_days_data[['Nombre']] = last_30_days_data[['Nombre']].replace('_', ' ', regex=True)

    # Extracting necessary data
    lluvia = last_30_days_data['lluvia']
    tmin = last_30_days_data['tmin']
    tseca = last_30_days_data['tseca']
    tmax = last_30_days_data['tmax']
    hum_rel = last_30_days_data['hum_rel']
    fecha = last_30_days_data['fecha']
    
    fig = figure(x_axis_type='datetime', title=estacion, height=400, width=800, toolbar_location='below', y_axis_label="Precipitación (mm)", y_range=(-5, 90), background_fill_color='white', background_fill_alpha=0.6, tools="save,pan,box_zoom,reset,wheel_zoom")
    fig.yaxis.axis_label_text_font_size = "8pt"
    fig.title.text_font_size = '8pt'
    fig.left[0].formatter.use_scientific = False

    # agregar el segundo eje para la temperatura
    fig.extra_y_ranges = {"temp_range": Range1d(start=-5, end=40)}
    fig.add_layout(LinearAxis(y_range_name="temp_range", axis_label="Temperatura (°C)"), 'right')

    # agregar las líneas y los círculos
    fig.line(fecha, lluvia, line_color='navy', line_width=1, legend_label='Precipitación',
    name='lluvia')

    fig.line(fecha, tseca, line_color='seagreen', line_width=1, line_dash='dashed', legend_label='Temperatura media', name='tseca',y_range_name='temp_range')
    fig.circle(fecha, tmin, fill_color='deepskyblue', line_color='blue', size=3, legend_label='Temperatura min', name='tmin',y_range_name='temp_range')
    fig.circle(fecha, tmax, fill_color='firebrick', line_color='red', size=3, legend_label='Temperatura max', name='tmax',y_range_name='temp_range')
    #fig.line(fecha, hum_rel, line_color='orange', line_width=1, line_dash='dashed', legend_label='Temperatura media', name='hum_rel')
    
    fig.legend.location = 'top_left'
    fig.title.text_font_size = '10pt'
    fig.yaxis.axis_label_text_font_size = "10pt"

    # agregar etiquetas a las líneas y los círculos
    tooltips = [
        ("Valor", "@y"),
        ("Fecha", "@x{%F}")
        ]
    formatters = {
        '@x': 'datetime'
        }
    
    hover = HoverTool(tooltips=tooltips, formatters=formatters, mode='vline')
    fig.add_tools(hover)

    # generar el archivo html y mostrar la gráfica
    output_file(os.path.join(directory_html, f'{estacion}.html'))            
    fig.legend.background_fill_alpha = 0.5
    fig.legend.label_text_font_size = "8pt"
    fig.legend.spacing = 1
    save(fig)
    
    data = {
        'fecha': fecha,
        'lluvia': lluvia,
        'tmin': tmin,
        'tseca': tseca,
        'tmax': tmax,
        'estacion': estacion,
        'directory_img': directory_img
    }

    # Return the prepared data for Matplotlib
    return data

class WeatherGraphsApp(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Generador de Graficas Mensual")
        main_layout= layout = QVBoxLayout()
        
        # Horizontal layout for logos
        logo_layout = QHBoxLayout()
        # Logos at the top
        self.logo1 = QLabel(self)
        pixmap1 = QPixmap("images\\logo_insivumeh.png")  # replace with your logo's path
        self.logo1.setPixmap(pixmap1)
        resized_pixmap1 = pixmap1.scaled(128, 128, Qt.AspectRatioMode.KeepAspectRatio)
        self.logo1.setPixmap(resized_pixmap1)
        logo_layout.addWidget(self.logo1)
        
        self.logo2 = QLabel(self)
        pixmap2 = QPixmap("images\\waterco-logo.png")  # replace with your logo's path
        self.logo2.setPixmap(pixmap2)
        resized_pixmap2 = pixmap2.scaled(128, 128, Qt.AspectRatioMode.KeepAspectRatio)
        self.logo2.setPixmap(resized_pixmap2)
        logo_layout.addWidget(self.logo2)
        
        self.logo3 = QLabel(self)
        pixmap3 = QPixmap("images\\IUCN_logo.png")  # replace with your logo's path
        self.logo3.setPixmap(pixmap3)
        resized_pixmap3 = pixmap3.scaled(128, 128, Qt.AspectRatioMode.KeepAspectRatio)
        self.logo3.setPixmap(resized_pixmap3)
        logo_layout.addWidget(self.logo3)
        
        # Add logos_layout to main layout
        main_layout.addLayout(logo_layout)
        
        # Main layout    
        self.setLayout(layout)
        self.setWindowTitle("Generador de Graficas climaticas")
        
        # Download Button
        self.download_button = QPushButton("1. Bajar base de datos a: datos-CSV\\download-database.csv")
        self.download_button.clicked.connect(self.download_database)
        layout.addWidget(self.download_button)

        # Directory Input
        self.directory_label = QLabel("Directorio de salida:")
        layout.addWidget(self.directory_label)
        self.directory_edit = QLineEdit()
        layout.addWidget(self.directory_edit)
        self.directory_browse_button = QPushButton("2. Seleccionar Directorio")
        self.directory_browse_button.clicked.connect(self.browse_directory)
        layout.addWidget(self.directory_browse_button)

        # CSV File Input
        self.csv_label = QLabel("Base de datos .CSV:")
        layout.addWidget(self.csv_label)
        self.csv_edit = QLineEdit()
        layout.addWidget(self.csv_edit)
        self.csv_browse_button = QPushButton("3. Selecionar Archivo .CSV")
        self.csv_browse_button.clicked.connect(self.browse_csv)
        layout.addWidget(self.csv_browse_button)

        # Generate Graphs Button
        self.generate_button = QPushButton("4. Generar Graficos")
        self.generate_button.clicked.connect(self.generate_graphs)
        layout.addWidget(self.generate_button)
        
        #Explore button after generating graphs
        self.explore_button = QPushButton("5. Explorar archivos generados")
        self.explore_button.setEnabled(False)  # Initially disable the button
        self.explore_button.clicked.connect(self.open_output_directory)
        layout.addWidget(self.explore_button)

        # Progress Bar
        self.progress = QProgressBar(self)
        layout.addWidget(self.progress)

        # Status Updates
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)
        
        # About Button
        self.about_button = QPushButton("Acerca de")
        self.about_button.clicked.connect(self.show_about)
        layout.addWidget(self.about_button)
        
        
        
        # Set the main layout to the widget
        self.setLayout(main_layout)
        
    # Function to download the database
    def download_database(self):
        try:
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
    def generate_graphs(self):
        output_directory = self.directory_edit.text()
        csv_file_path = self.csv_edit.text()

        if not (output_directory and csv_file_path):
            self.status_label.setText("Porfavor provea todos los requisitos para genrar las graficas!")
            return

        self.status_label.setText("Procesando datos... porfavor espere.")
        directory_img = os.path.join(output_directory, "img_output")
        directory_html = os.path.join(output_directory, "html_output")
        os.makedirs(directory_img, exist_ok=True)
        os.makedirs(directory_html, exist_ok=True)

        try:
            df = pd.read_csv(csv_file_path, header=0, delimiter=',')
            df['fecha'] = pd.to_datetime(df['fecha'], format="%d/%m/%Y")

            grouped_data = df.groupby('Nombre')

            # Set progress bar
            self.progress.setMaximum(len(grouped_data))
            self.progress.setValue(0)

            self.worker = Worker(grouped_data, directory_img, directory_html)
            self.worker.plot_data_signal.connect(self.plot_with_matplotlib)
            self.worker.progress_signal.connect(self.update_progress)
            self.worker.finished.connect(lambda: self.status_label.setText("Graficos generados exitosamente!"))
            self.worker.finished.connect(self.graphs_generated)
               
            self.worker.start()

        except Exception as e:
            self.status_label.setText(f"Error: {str(e)}")
            
    def graphs_generated(self):
                self.status_label.setText("Graficos generados exitosamente!")
                self.explore_button.setEnabled(True)

    def plot_with_matplotlib(self, data):
        # 1. Extract the data
        fecha = data['fecha']
        lluvia = data['lluvia']
        tmin = data['tmin']
        tseca = data['tseca']
        tmax = data['tmax']
        estacion = data['estacion']
        directory_img = data['directory_img']

        # 2. Start plotting with matplotlib
        fig, ax1 = plt.subplots(figsize=(10,5))
        
        ax1.set_xlabel('Fecha')
        ax1.set_ylabel('Precipitación (mm)', color='tab:blue')
        ax1.plot(fecha, lluvia, color='tab:blue', label='Precipitación')
        ax1.tick_params(axis='y', labelcolor='tab:blue')
        ax1.set_ylim(-5, 90)  # Set y-axis limit for Precipitation

        
        ax2 = ax1.twinx()  # Create a second y-axis sharing the same x-axis
        ax2.set_ylabel('Temperatura (°C)', color='tab:red')
        ax2.plot(fecha, tseca, color='tab:green', label='Temperatura Seca')
        ax2.plot(fecha, tmin, color='deepskyblue', linestyle='--', label='Temp Min')
        ax2.plot(fecha, tmax, color='firebrick', linestyle='--', label='Temp Max')
        ax2.tick_params(axis='y', labelcolor='tab:red')
        
        # Handle legends and title
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax2.legend(lines1 + lines2, labels1 + labels2, loc=0)
        ax2.set_ylim(-5, 40)  # Set y-axis limit for Temperature
        
        plt.title(f"Data for {estacion}")
        fig.tight_layout()  # Ensure the layout fits well
        
        # Save the figure to a PNG file
        save_path = os.path.join(directory_img, f"{estacion}.png")
        plt.savefig(save_path)
        
        # Optionally show the plot (might not be needed in a GUI app, but useful for testing)
        #plt.show()
        plt.close(fig)
        
    def update_progress(self, estacion):
            self.progress.setValue(self.progress.value() + 1)
            self.status_label.setText(f"Procesando estacion {estacion}...")

    
def main():
    app = QApplication(sys.argv)
    window = WeatherGraphsApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()