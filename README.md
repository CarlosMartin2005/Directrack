# Directrack

Aplicación de escritorio (PyQt5) para buscar canciones y artistas en YouTube, descargarlas como MP3 y organizar tu biblioteca musical.

## Requisitos

- Python 3
- [ffmpeg](https://ffmpeg.org/) (en Windows: `choco install ffmpeg-full`)
- Una API key de la **YouTube Data API v3** (gratuita, ver abajo cómo crearla)

## Instalación

```bash
git clone https://github.com/CarlosMartin2005/Directrack.git
cd Directrack
pip install -r requirements.txt
```

## Crear la API key de YouTube

Necesitas una cuenta de Google. El uso de la API es gratuito dentro de la cuota diaria (10.000 unidades).

### 1. Crear un proyecto en Google Cloud

1. Entra en [Google Cloud Console](https://console.cloud.google.com/) con tu cuenta de Google.
2. Si es la primera vez, acepta los términos de servicio.
3. En la barra superior, haz clic en el **selector de proyectos** y luego en **Proyecto nuevo**.
4. Ponle un nombre (por ejemplo `Directrack`) y pulsa **Crear**.
5. Cuando termine, asegúrate de que el proyecto nuevo está seleccionado en la barra superior.

### 2. Habilitar la YouTube Data API v3

1. En el menú lateral ve a **APIs y servicios → Biblioteca**.
2. Busca **YouTube Data API v3** y ábrela.
3. Pulsa **Habilitar**.

### 3. Crear la clave

1. Ve a **APIs y servicios → Credenciales**.
2. Pulsa **+ Crear credenciales → Clave de API**.
3. Se mostrará la clave generada (empieza por `AIza...`). Cópiala.

### 4. Restringir la clave (recomendado)

Así, si alguien obtiene tu clave, no podrá usarla para otras APIs de Google.

1. En **Credenciales**, haz clic en el nombre de la clave que acabas de crear.
2. **Nombre**: ponle uno reconocible, por ejemplo `Directrack-desktop`.
3. **Restricciones de aplicación**: deja **Ninguna**. Las opciones de sitios web, Android o iOS no sirven para una aplicación de escritorio. Usa **Direcciones IP** solo si tu IP pública es fija.
4. **Restricciones de API**: selecciona **Restringir clave** y marca únicamente **YouTube Data API v3**.
5. Pulsa **Guardar**. Los cambios pueden tardar unos minutos en aplicarse.

## Configurar la API key

Elige una de estas dos opciones:

**Opción A: archivo `config.py`**

1. Copia el archivo de ejemplo:
   ```bash
   # Windows
   copy config.example.py config.py
   # Linux / macOS
   cp config.example.py config.py
   ```
2. Abre `config.py` y sustituye el texto de ejemplo por tu clave:
   ```python
   API_KEY = "tu_clave"
   ```

**Opción B: variable de entorno `YOUTUBE_API_KEY`**

```powershell
# Windows (PowerShell), permanente para tu usuario; abre una terminal nueva después
setx YOUTUBE_API_KEY "tu_clave"
```

```bash
# Linux / macOS, solo para la terminal actual
export YOUTUBE_API_KEY="tu_clave"
```

Si están configuradas las dos, se usa la variable de entorno.

## Ejecutar

```bash
python app.py
```
