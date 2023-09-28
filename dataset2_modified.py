import sys
import os
import pandas as pd
from PyQt6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget, QPushButton, QFileDialog, QLineEdit
import plotly.graph_objects as go
from bokeh.plotting import output_file, save
from bokeh.models import Range1d, LinearAxis
from bokeh.plotting import figure

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
            df = pd.read_csv(csv_file_path, header=0, delimiter=',')
            df['fecha'] = pd.to_datetime(df['fecha'], format="%d/%m/%Y")
            latest_date = df['fecha'].max()
            thirty_days_ago = latest_date - pd.Timedelta(days=30)
            last_30_days_data = df[df['fecha'] >= thirty_days_ago]
            last_30_days_data = last_30_days_data.sort_values("fecha")
            last_30_days_data[['Nombre']] = last_30_days_data[['Nombre']].replace('_', ' ', regex=True)
            estaciones = last_30_days_data["Nombre"].unique()

            for estacion in estaciones:
                grouped_data = last_30_days_data.groupby(['Nombre'])
                lluvia = grouped_data.get_group(estacion)['lluvia']
                tmin = grouped_data.get_group(estacion)['tmin']
                tseca = grouped_data.get_group(estacion)['tseca']
                tmax = grouped_data.get_group(estacion)['tmax']
                fecha = grouped_data.get_group(estacion)['fecha']

                # Creating the plot using Plotly for PNG
                fig_plotly = go.Figure()
                fig_plotly.add_trace(go.Scatter(x=fecha, y=lluvia, mode='lines', name='Precipitación'))
                fig_plotly.add_trace(go.Scatter(x=fecha, y=tmin, mode='lines+markers', name='Temp Min'))
                fig_plotly.add_trace(go.Scatter(x=fecha, y=tmax, mode='lines+markers', name='Temp Max'))
                fig_plotly.add_trace(go.Scatter(x=fecha, y=tseca, mode='lines', name='Temp Seca'))
                fig_plotly.write_image(os.path.join(directory_img, f'{estacion}.png'))
                
                # Creating the plot using Bokeh for HTML
                fig_bokeh = figure(x_axis_type='datetime', title=estacion, plot_height=400, plot_width=800, y_axis_label="Precipitación (mm)", y_range=(-5, 90))
                fig_bokeh.line(fecha, lluvia, line_color='navy', legend_label='Precipitación')
                fig_bokeh.circle(fecha, tmin, fill_color='blue', line_color='blue', size=3, legend_label='Temp Min')
                fig_bokeh.circle(fecha, tmax, fill_color='red', line_color='red', size=3, legend_label='Temp Max')
                fig_bokeh.line(fecha, tseca, line_color='green', legend_label='Temp Seca')

                output_file(os.path.join(directory_html, f'{estacion}.html'))
                save(fig_bokeh)

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