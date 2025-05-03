import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QMessageBox, QProgressBar,
    QListWidget, QListWidgetItem
)
import yt_dlp
from PyQt5.QtGui import QIcon, QCursor
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QProgressBar
import requests
from config import API_KEY
import urllib.parse

class DescargadorMusica(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Descargador de Música")
        self.setGeometry(100, 100, 500, 400)

        layout = QVBoxLayout()

        self.label = QLabel("Nombre o URL de la canción:")
        self.label.setStyleSheet("font-size: 16px; color: #333;")
        layout.addWidget(self.label)

        self.entrada = QLineEdit()
        self.entrada.setStyleSheet("font-size: 14px; padding: 5px;")
        layout.addWidget(self.entrada)

        self.boton_buscar = QPushButton("Buscar canción")
        self.boton_buscar.setIcon(QIcon.fromTheme("search"))
        self.boton_buscar.setToolTip("Buscar canción por nombre o URL")
        self.boton_buscar.setStyleSheet("""
            QPushButton {
                background-color: #FFD700;
                font-size: 14px;
                padding: 5px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #FFC107;
            }
        """)
        self.boton_buscar.setCursor(QCursor(Qt.PointingHandCursor))
        self.boton_buscar.clicked.connect(lambda: self.buscar_cancion(self.entrada.text()))
        layout.addWidget(self.boton_buscar)

        self.boton_ruta = QPushButton("Seleccionar carpeta de destino")
        self.boton_ruta.setIcon(QIcon.fromTheme("folder"))
        self.boton_ruta.setToolTip("Selecciona la carpeta donde se guardará la canción")
        self.boton_ruta.setStyleSheet("background-color: lightblue;")
        self.boton_ruta.setFixedSize(200, 30)
        self.boton_ruta.setCursor(QCursor(Qt.PointingHandCursor))
        self.boton_ruta.setStyleSheet("QPushButton { font-size: 14px; }")
        self.boton_ruta.clicked.connect(self.seleccionar_ruta)
        layout.addWidget(self.boton_ruta)

        self.boton_descargar = QPushButton("Descargar canción")
        self.boton_descargar.setIcon(QIcon.fromTheme("download"))
        self.boton_descargar.setToolTip("Descargar la canción seleccionada")
        self.boton_descargar.setStyleSheet("""
            QPushButton {
                background-color: #32CD32;
                font-size: 14px;
                padding: 5px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #228B22;
            }
        """)
        self.boton_descargar.setCursor(QCursor(Qt.PointingHandCursor))
        self.boton_descargar.clicked.connect(self.descargar_cancion)
        layout.addWidget(self.boton_descargar)

        self.barra_progreso = QProgressBar()
        self.barra_progreso.setStyleSheet("""
            QProgressBar {
                border: 1px solid #000;
                text-align: center;
                font-size: 14px;
            }
            QProgressBar::chunk {
                background-color: #32CD32;
            }
        """)
        self.barra_progreso.setValue(0)
        layout.addWidget(self.barra_progreso)

        self.setLayout(layout)
        self.ruta_destino = ""

        self.lista_resultados = QListWidget()
        self.lista_resultados.setStyleSheet("font-size: 14px; background-color: #F0F0F0;")
        self.lista_resultados.itemClicked.connect(self.seleccionar_cancion)
        layout.addWidget(self.lista_resultados)

    def buscar_cancion(self, nombre):
        # Codificar el término de búsqueda
        nombre_codificado = urllib.parse.quote(nombre)
        URL = f"https://www.googleapis.com/youtube/v3/search?part=snippet&type=video&q={nombre_codificado}&key={API_KEY}"

        try:
            respuesta = requests.get(URL)
            datos = respuesta.json()

            if "items" in datos and datos["items"]:
                self.lista_resultados.clear()
                for item in datos["items"]:
                    video_id = item["id"]["videoId"]
                    titulo = item["snippet"]["title"]
                    self.lista_resultados.addItem(f"{titulo} | https://www.youtube.com/watch?v={video_id}")
                    # lista_item = QListWidgetItem(f"{titulo} (https://www.youtube.com/watch?v={video_id})")
                    # lista_item.setData(Qt.UserRole, f"https://www.youtube.com/watch?v={video_id}")
                    # self.lista_resultados.addItem(lista_item)
                QMessageBox.information(self, "Búsqueda exitosa", "Selecciona una canción de la lista.")
            else:
                QMessageBox.warning(self, "Error", "No se encontraron resultados.")
        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "Error", f"Error al buscar la canción: {str(e)}")

    def seleccionar_cancion(self, item):
        url = item.text().split(" | ")[1]
        self.entrada.setText(url)
    
    def seleccionar_ruta(self):
        carpeta = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta")
        if carpeta:
            self.ruta_destino = carpeta

    def descargar_cancion(self):
        url = self.entrada.text().strip()
        if not url:
            QMessageBox.warning(self, "Error", "Por favor, ingresa una URL o nombre.")
            return
        if not self.ruta_destino:
            QMessageBox.warning(self, "Error", "Selecciona una carpeta de destino.")
            return

        try:
            opciones = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(self.ruta_destino, '%(title)s.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'ffmpeg_location': r'C:\ProgramData\chocolatey\lib\ffmpeg-full\tools\ffmpeg\bin',
                'progress_hooks': [self.actualizar_progreso],
                'quiet': False
            }

            with yt_dlp.YoutubeDL(opciones) as ydl:
                ydl.download([url])
            QMessageBox.information(self, "Éxito", "Descarga completada.")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
    
    def actualizar_progreso(self, d):
        if d['status'] == 'downloading':
            if 'downloaded_bytes' in d and 'total_bytes' in d:
                downloaded = d['downloaded_bytes']
                total = d['total_bytes']
                if total > 0:
                    porcentaje = int(downloaded / total * 100)
                    self.barra_progreso.setValue(porcentaje)
                else:
                    self.barra_progreso.setValue(0)
        elif d['status'] == 'finished':
            self.barra_progreso.setValue(100)
            self.barra_progreso.setFormat("Descarga completada")
        elif d['status'] == 'error':
            self.barra_progreso.setValue(0)
            self.barra_progreso.setFormat("Error en la descarga")
            QMessageBox.critical(self, "Error", "Error en la descarga.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = DescargadorMusica()
    ventana.show()
    sys.exit(app.exec_())
