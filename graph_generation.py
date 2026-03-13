import logging
import os
import pandas as pd
import matplotlib.pyplot as plt
from PyQt6.QtCore import QObject, pyqtSignal
from data_processing import read_and_prepare_data, prepare_data_for_graphs, process_grouped_data

class GraphGenerator(QObject):
    progress_signal = pyqtSignal(int)
    plot_data_signal = pyqtSignal(object)
    completion_signal = pyqtSignal(str)

    def generate_graphs(self, output_directory, csv_file_path):
        try:
            df = read_and_prepare_data(csv_file_path)
            grouped_data = prepare_data_for_graphs(df)
            
            directory_img = os.path.join(output_directory, "img_output")
            directory_html = os.path.join(output_directory, "html_output")
            os.makedirs(directory_img, exist_ok=True)
            os.makedirs(directory_html, exist_ok=True)

            total = len(grouped_data)
            for i, (name, group) in enumerate(grouped_data):
                plot_data = process_grouped_data(name, group, directory_img, directory_html)
                self.plot_data_signal.emit(plot_data)
                progress = int((i + 1) / total * 100)
                self.progress_signal.emit(progress)  # Update progress

            self.completion_signal.emit("Gráficos generados exitosamente!")

        except Exception as e:
            self.completion_signal.emit(f"Error: {str(e)}")

def plot_with_matplotlib(data):
    """
    Plot the data using matplotlib and save the figures.
    Three axes: precipitation (left), temperature (right), humidity (far right).
    """
    try:
        fecha = data['fecha']
        lluvia = data['lluvia']
        tmin = data['tmin']
        tseca = data['tseca']
        tmax = data['tmax']
        hum_rel = data['hum_rel']
        estacion = data['estacion']
        directory_img = data['directory_img']

        fig, ax1 = plt.subplots(figsize=(12, 5))

        ax1.set_xlabel('Fecha')
        ax1.set_ylabel('Precipitación (mm)', color='tab:blue')
        ax1.plot(fecha, lluvia, color='tab:blue', label='Precipitación')
        ax1.tick_params(axis='y', labelcolor='tab:blue')
        ax1.set_ylim(-5, 90)

        ax2 = ax1.twinx()
        ax2.set_ylabel('Temperatura (°C)', color='tab:red')
        ax2.plot(fecha, tseca, color='tab:green', label='Temperatura Seca')
        ax2.plot(fecha, tmin, color='deepskyblue', linestyle='--', label='Temp Min')
        ax2.plot(fecha, tmax, color='firebrick', linestyle='--', label='Temp Max')
        ax2.tick_params(axis='y', labelcolor='tab:red')
        ax2.set_ylim(-5, 40)

        ax3 = ax1.twinx()
        ax3.spines['right'].set_position(('outward', 60))
        ax3.set_ylabel('Humedad relativa (%)', color='darkorange')
        ax3.plot(fecha, hum_rel, color='darkorange', linestyle=':', label='Humedad relativa')
        ax3.tick_params(axis='y', labelcolor='darkorange')
        ax3.set_ylim(0, 100)

        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        lines3, labels3 = ax3.get_legend_handles_labels()
        ax2.legend(lines1 + lines2 + lines3, labels1 + labels2 + labels3, loc=0)

        plt.title(f"Datos de {estacion}")
        fig.tight_layout()

        save_path = os.path.join(directory_img, f"{estacion}.png")
        plt.savefig(save_path)
        plt.close(fig)

    except Exception as e:
        plt.close('all')
        logging.warning(f"plot_with_matplotlib failed for '{data.get('estacion', '?')}': {e}")
