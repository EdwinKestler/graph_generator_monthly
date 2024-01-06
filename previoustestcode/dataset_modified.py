import sys
import os
import pandas as pd
from PyQt6.QtWidgets import (QApplication, QLabel, QVBoxLayout, QWidget, QPushButton, QFileDialog, QLineEdit, QProgressBar)
from bokeh.plotting import output_file, save
from bokeh.models import Range1d, LinearAxis
from bokeh.plotting import figure
from bokeh.models.tools import HoverTool
import matplotlib.pyplot as plt


class WeatherGraphsApp(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Weather Graphs Generator")
        layout = QVBoxLayout()

        # Directory Input
        self.directory_label = QLabel("Output Directory:")
        layout.addWidget(self.directory_label)
        self.directory_edit = QLineEdit()
        layout.addWidget(self.directory_edit)
        self.directory_browse_button = QPushButton("Browse Directory")
        self.directory_browse_button.clicked.connect(self.browse_directory)
        layout.addWidget(self.directory_browse_button)

        # CSV File Input
        self.csv_label = QLabel("Database CSV:")
        layout.addWidget(self.csv_label)
        self.csv_edit = QLineEdit()
        layout.addWidget(self.csv_edit)
        self.csv_browse_button = QPushButton("Browse CSV")
        self.csv_browse_button.clicked.connect(self.browse_csv)
        layout.addWidget(self.csv_browse_button)

        # Generate Graphs Button
        self.generate_button = QPushButton("Generate Graphs")
        self.generate_button.clicked.connect(self.generate_graphs)
        layout.addWidget(self.generate_button)

        # Progress Bar
        self.progress = QProgressBar(self)
        layout.addWidget(self.progress)

        # Status Updates
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        self.setLayout(layout)

    def browse_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if directory:
            self.directory_edit.setText(directory)

    def browse_csv(self):
        file_filter = "CSV Files (*.csv);;All Files (*)"
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Database CSV", "", file_filter)
        if file_name:
            self.csv_edit.setText(file_name)

    def generate_graphs(self):
        idx = 0
        output_directory = self.directory_edit.text()
        csv_file_path = self.csv_edit.text()

        if not (output_directory and csv_file_path):
            self.status_label.setText("Please provide all inputs before generating graphs!")
            return

        self.status_label.setText("Processing... Please wait.")
        directory_img = os.path.join(output_directory, "img_output")
        directory_html = os.path.join(output_directory, "html_output")
        os.makedirs(directory_img, exist_ok=True)
        os.makedirs(directory_html, exist_ok=True)

        try:
           # Load the CSV data
            print("Loading data...")
            df = pd.read_csv(csv_file_path, header=0, delimiter=',')
            print("Data loaded!")
            # Convertir la columna FECHA a formato datetime y ordenar el dataframe
            df['fecha'] = pd.to_datetime(df['fecha'], format="%d/%m/%Y")

            # Obtener la fecha más reciente en el dataframe
            latest_date = df['fecha'].max()

            # Calcular la fecha de hace 30 días a partir de la fecha más reciente
            thirty_days_ago = latest_date - pd.Timedelta(days=30)

            # Filtrar los datos para que solo incluyan los de los últimos 30 días
            last_30_days_data = df[df['fecha'] >= thirty_days_ago]
            last_30_days_data = last_30_days_data.sort_values("fecha")

            last_30_days_data[['Nombre']] = last_30_days_data[['Nombre']].replace('_', ' ', regex=True)
            # Obtener la lista de estaciones disponibles en el dataframe
            estaciones = last_30_days_data["Nombre"].unique()
            self.progress.setMaximum(len(estaciones))


            # Crear un gráfico y un archivo HTML para cada estación
            for estacion in estaciones:
                # Filtrar los datos para la estación actual
                data = df[df['estacion'] == estacion]
                # filtrar los datos por la estación (k)
                gk = last_30_days_data.groupby(['Nombre'])
                lluvia = gk.get_group(estacion)['lluvia']
                tmin=gk.get_group(estacion)['tmin']
                tseca=gk.get_group(estacion)['tseca']
                tmax=gk.get_group(estacion)['tmax']
                hum_rel=gk.get_group(estacion)['hum_rel']
                fecha=gk.get_group(estacion)['fecha']

                fig = figure(x_axis_type='datetime', title=estacion, height=400, width=800, toolbar_location='below',
                                y_axis_label="Precipitación (mm)", y_range=(-5, 90), background_fill_color='white', 
                                background_fill_alpha=0.6, tools="save,pan,box_zoom,reset,wheel_zoom")


                fig.yaxis.axis_label_text_font_size = "8pt"
                fig.title.text_font_size = '8pt'
                fig.left[0].formatter.use_scientific = False

                # agregar el segundo eje para la temperatura
                fig.extra_y_ranges = {"temp_range": Range1d(start=-5, end=40)}
                fig.add_layout(LinearAxis(y_range_name="temp_range", axis_label="Temperatura (°C)"), 'right')


                # agregar las líneas y los círculos
                fig.line(fecha, lluvia, line_color='navy', line_width=1, legend_label='Precipitación',
                            name='lluvia')

                fig.line(fecha, tseca, line_color='seagreen', line_width=1, line_dash='dashed', legend_label='Temperatura media', 
                            name='tseca',y_range_name='temp_range')
                fig.circle(fecha, tmin, fill_color='deepskyblue', line_color='blue', size=3,
                            legend_label='Temperatura min', name='tmin',y_range_name='temp_range')
                fig.circle(fecha, tmax, fill_color='firebrick', line_color='red', size=3,
                            legend_label='Temperatura max', name='tmax',y_range_name='temp_range')

                #fig.line(fecha, hum_rel, line_color='orange', line_width=1, line_dash='dashed', legend_label='Temperatura media', 
                #          name='hum_rel')

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
                
                #now we use matplotlib to generate the PNG
                # Start plotting with matplotlib
                fig, ax1 = plt.subplots(figsize=(10,5))

                ax1.set_xlabel('Fecha')
                ax1.set_ylabel('Precipitación (mm)', color='tab:blue')
                ax1.plot(fecha, lluvia, color='tab:blue', label='Precipitación')
                ax1.tick_params(axis='y', labelcolor='tab:blue')
                
                ax2 = ax1.twinx()  # instantiate a second axis sharing the same x-axis
                ax2.set_ylabel('Temperatura (°C)', color='tab:red')
                ax2.plot(fecha, tseca, color='tab:green', label='Temperatura media', linestyle='--')
                ax2.plot(fecha, tmin, color='tab:cyan', label='Temperatura min', marker='o')
                ax2.plot(fecha, tmax, color='tab:red', label='Temperatura max', marker='o')
                ax2.tick_params(axis='y', labelcolor='tab:red')
                
                fig.tight_layout()  
                fig.suptitle(estacion)

                # Save figure as PNG
                png_path = os.path.join(directory_img, f"{estacion}.png")
                plt.savefig(png_path)
                plt.close(fig)  # Close the figure to free up memory
                
                idx += 1
                # Update progress bar
                self.progress.setValue(idx)

            self.status_label.setText("Graphs generated successfully!")

        except Exception as e:
            self.status_label.setText(f"Error occurred: {str(e)}")

def main():
    app = QApplication(sys.argv)
    window = WeatherGraphsApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()