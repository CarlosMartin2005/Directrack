import sys
import os
import re
import requests
import unicodedata
from difflib import SequenceMatcher
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QListWidget, QListWidgetItem,
    QFileDialog, QMessageBox, QProgressBar, QStyledItemDelegate,
    QStyleOptionViewItem, QStyle, QTabWidget, QLabel, QTreeWidget,
    QTreeWidgetItem, QHeaderView, QComboBox, QSpinBox, QGroupBox,
    QScrollArea, QFrame
)
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QFont, QBrush
from PyQt5.QtCore import Qt, QSize, QThread, pyqtSignal, QTimer
from googleapiclient.discovery import build
import yt_dlp
from config import API_KEY
from collections import defaultdict

YOUTUBE_API = build('youtube', 'v3', developerKey=API_KEY)


# =============================================================================
# NORMALIZACIÓN DE NOMBRES DE ARTISTAS
# =============================================================================

# Diccionario de abreviaciones comunes en español
ABBREVIATIONS = {
    'ma.': 'maria',
    'ma ': 'maria ',
    'mª': 'maria',
    'jose': 'jose',
    'josé': 'jose',
    'jr.': 'junior',
    'jr': 'junior',
    'sr.': 'senior',
    'sr': 'senior',
    'dr.': 'doctor',
    'dj': 'dj',
    'mc': 'mc',
    'st.': 'saint',
    'ft.': 'feat',
    'feat.': 'feat',
    '&': 'and',
}

# Patrones de basura a eliminar de los nombres de archivo
JUNK_PATTERNS = [
    r'\(YTCONVERT\.IN\)',
    r'\(W[VW]W\.[A-Z0-9]+\.[A-Z]+\)',  # WWW o WVW (typo común)
    r'\(YTmp3xd\.com\)',
    r'\(mp3\.pm\)',
    r'\(musicpleer\.com\)',
    r'\(simp3s\.net\)',
    r'\(emp3z\.com\)',
    r'\([a-zA-Z0-9]+\.(com|net|org|in|io|me|cc)\)',
    r'\d+\s*kbps\)?',
    r'\(\d+\s*kbps\)',
    r'\[.*?(kbps|mp3|audio|download|free).*?\]',
    r'[wW][vVwW][wW]\.[a-zA-Z0-9]+\.[a-z]+',  # www o wvw sin paréntesis
    r'YTCONVERT\.IN',
    r'YTmp3xd\.com',
    r'mp3\.pm',
    r'\(official\s*(video|audio|music\s*video)?\)',
    r'\(audio\s*oficial\)',
    r'\(video\s*oficial\)',
    r'\(lyric\s*video\)',
    r'\(lyrics?\)',
    r'\(hd\)',
    r'\(hq\)',
    r'\(oficial\)',
    r'\(en\s*vivo\)',
    r'\(live\)',
    r'\.mp4',  # Extensiones de video que a veces quedan
    r'\.avi',
    r'\.mkv',
    r'\.webm',
    r'\.mov',
]

# Lista de artistas conocidos (se puede expandir)
# Esto ayuda a identificar artistas en títulos sin formato estándar
KNOWN_ARTISTS = [
    # Mexicanos / Latinos
    "Vicente Fernandez", "Vicente Fernández",
    "Jose Jose", "José José",
    "Juan Gabriel",
    "Luis Miguel",
    "Marco Antonio Solis", "Marco Antonio Solís",
    "Jose Luis Rodriguez", "José Luis Rodríguez", "El Puma",
    "Jose Maria Napoleon", "José María Napoleón", "Jose Ma. Napoleon", "Napoleon",
    "Julio Iglesias",
    "Rocio Durcal", "Rocío Dúrcal",
    "Ana Gabriel",
    "Alejandro Fernandez", "Alejandro Fernández",
    "Pedro Fernandez", "Pedro Fernández",
    "Pepe Aguilar",
    "Antonio Aguilar",
    "Jenni Rivera",
    "Lupillo Rivera",
    "Los Tigres Del Norte",
    "Los Tucanes De Tijuana",
    "Banda MS",
    "Calibre 50",
    "Christian Nodal",
    "Grupo Firme",
    "Los Angeles Azules", "Los Ángeles Azules",
    "Bronco",
    "Los Bukis",
    "Los Temerarios",
    "Los Yonics",
    "Camilo Sesto",
    "Roberto Carlos",
    "Ricardo Arjona", "Arjona",
    "Shakira",
    "Juanes",
    "Carlos Vives",
    "Marc Anthony",
    "Enrique Iglesias",
    "Ricky Martin",
    "Chayanne",
    "Ricardo Montaner",
    "Franco De Vita",
    "Emmanuel",
    "Mijares",
    "Yuri",
    "Thalia", "Thalía",
    "Gloria Trevi",
    "Paulina Rubio",
    "Alejandra Guzman", "Alejandra Guzmán",
    "Maná",
    "Café Tacvba", "Cafe Tacuba",
    "Molotov",
    "Caifanes",
    "El Tri",
    "Maldita Vecindad",
    "Los Fabulosos Cadillacs",
    "Soda Stereo",
    "Gustavo Cerati",
    "Fito Paez", "Fito Páez",
    "Charly Garcia", "Charly García",
    "Mercedes Sosa",
    "Celia Cruz",
    "Hector Lavoe", "Héctor Lavoe",
    "Ruben Blades", "Rubén Blades",
    "Willie Colon", "Willie Colón",
    "Oscar De Leon", "Oscar D'León",
    "Daddy Yankee",
    "Bad Bunny",
    "J Balvin",
    "Ozuna",
    "Maluma",
    "Nicky Jam",
    "Don Omar",
    "Wisin Y Yandel", "Wisin & Yandel",
    "Aventura",
    "Romeo Santos",
    "Prince Royce",
    "Bachata Heightz",
    # Artistas adicionales
    "Massiel",
    "Roberto Jordan", "Roberto Jordán",
    "Los Brios", "Los Bríos",
    "Jose Luis Perales", "José Luis Perales",
    "Ednita Nazario",
    "Miguel Bose", "Miguel Bosé",
    "Joan Sebastian", "Joan Sebastián",
    "Tono Nazario", "Toño Nazario",
    "Tono Rosario", "Toño Rosario",
    "Diego Verdaguer",
    "Rabito",
    "Montez De Durango",
    "El Chapo De Sinaloa",
    "Los Humildes",
    "Los Babys",
    "Los Freddy's", "Los Freddys",
    "Los Terricolas", "Los Terrícolas",
    "Los Iracundos",
    "Los Pasteles Verdes",
    "Los Galos",
    "Los Doltons",
    "Los Angeles Negros", "Los Ángeles Negros",
    "Camilo Sesto",
    "Raphael",
    "Nino Bravo",
    "Julio Jaramillo",
    "Javier Solis", "Javier Solís",
    "Pedro Infante",
    "Jorge Negrete",
    "Miguel Aceves Mejia", "Miguel Aceves Mejía",
    "Lola Beltran", "Lola Beltrán",
    "Lucha Villa",
    "Chavela Vargas",
    "Eugenia Leon", "Eugenia León",
    "Lila Downs",
    "Natalia Lafourcade",
    "Mon Laferte",
    "Julieta Venegas",
    "Ely Guerra",
    "Gloria Estefan",
    "Jon Secada",
    "Luis Fonsi",
    "Pablo Alboran", "Pablo Alborán",
    "Alejandro Sanz",
    "David Bisbal",
    "Melendi",
    "Manuel Carrasco",
    "Antonio Orozco",
    "La Oreja De Van Gogh",
    "El Canto Del Loco",
    "Amaral",
    "Jarabe De Palo",
    "Mana", "Maná",
    "Hombres G",
    "Duncan Dhu",
    "El Ultimo De La Fila", "El Último De La Fila",
    "Radio Futura",
    "Mecano",
    "Alaska",
    "Loquillo",
    "Los Secretos",
    "Los Rodriguez", "Los Rodríguez",
    "Andres Calamaro", "Andrés Calamaro",
    "Los Enanitos Verdes",
    "Los Prisioneros",
    "La Ley",
    "Los Bunkers",
    "Zoé",
    "Cafe Tacvba", "Café Tacvba",
    "Los Fabulosos Cadillacs",
    "Aterciopelados",
    "Bomba Estereo", "Bomba Estéreo",
    "Morat",
    "Reik",
    "Jesse Y Joy", "Jesse & Joy",
    "Ha Ash", "Ha*Ash",
    "Sin Bandera",
    "Camila",
    "La Quinta Estacion", "La Quinta Estación",
    "Belanova",
    "Paty Cantu", "Paty Cantú",
    "Yuridia",
    "Espinoza Paz",
    "Gerardo Ortiz",
    "Julion Alvarez", "Julión Álvarez",
    "Larry Hernandez", "Larry Hernández",
    "El Komander",
    "Regulo Caro", "Régulo Caro",
    "Alfredo Olivas",
    "Lenin Ramirez", "Lenin Ramírez",
    "Los Plebes Del Rancho",
    "Ariel Camacho",
    "Chalino Sanchez", "Chalino Sánchez",
    "Valentin Elizalde", "Valentín Elizalde",
    "Sergio Vega",
    "El Coyote",
    "El Potro De Sinaloa",
    "Pancho Barraza",
    "Joan Sebastian", "Joan Sebastián",
    "Pepe Aguilar",
    "Angela Aguilar", "Ángela Aguilar",
    "Leonardo Aguilar",
    "Aida Cuevas",
    "Paquita La Del Barrio",
    "Jenny Rivera",
    "Graciela Beltran", "Graciela Beltrán",
    "Ana Barbara", "Ana Bárbara",
    "Alicia Villarreal",
    "Selena",
    "Selena Gomez",
    "Demi Lovato",
    "Camila Cabello",
    "Becky G",
    "Natti Natasha",
    "Karol G",
    "Anitta",
    "Tini",
    "Lali",
    # Internacionales
    "Michael Jackson",
    "Madonna",
    "Queen",
    "The Beatles",
    "Elvis Presley",
    "Frank Sinatra",
    "Whitney Houston",
    "Celine Dion", "Céline Dion",
    "Mariah Carey",
    "Beyonce", "Beyoncé",
    "Adele",
    "Ed Sheeran",
    "Bruno Mars",
    "Taylor Swift",
    "Ariana Grande",
    "Lady Gaga",
    "Katy Perry",
    "Rihanna",
    "Justin Bieber",
    "The Weeknd",
    "Drake",
    "Eminem",
    "Kanye West",
    "Jay Z", "Jay-Z",
    "Coldplay",
    "U2",
    "ABBA",
    "Bee Gees",
    "AC DC", "AC/DC",
    "Guns N Roses", "Guns N' Roses",
    "Metallica",
    "Nirvana",
    "Red Hot Chili Peppers",
    "Linkin Park",
    "Green Day",
    "Bon Jovi",
    "Aerosmith",
    "Led Zeppelin",
    "Pink Floyd",
    "The Rolling Stones",
    "Eagles",
    "Fleetwood Mac",
    "Elton John",
    "Billy Joel",
    "Phil Collins",
    "Genesis",
    "Journey",
    "Foreigner",
    "Boston",
    "Chicago",
    "Earth Wind Fire", "Earth Wind & Fire",
    "Donna Summer",
    "Gloria Gaynor",
    "Barry White",
    "Lionel Richie",
    "Stevie Wonder",
    "Prince",
    "George Michael",
    "Wham",
    "Duran Duran",
    "Depeche Mode",
    "Pet Shop Boys",
    "A-ha",
    "Tears For Fears",
    "Simple Minds",
    "INXS",
    "Def Leppard",
    "Van Halen",
    "Whitesnake",
    "Scorpions",
    "Europe",
    "Poison",
    "Motley Crue", "Mötley Crüe",
    "Twisted Sister",
    "Quiet Riot",
    "Ratt",
    "Cinderella",
    "Warrant",
    "Skid Row",
    "Alice In Chains",
    "Pearl Jam",
    "Soundgarden",
    "Stone Temple Pilots",
    "Bush",
    "Creed",
    "Nickelback",
    "3 Doors Down",
    "Matchbox Twenty",
    "Counting Crows",
    "Goo Goo Dolls",
    "Third Eye Blind",
    "Semisonic",
    "Vertical Horizon",
    "Sister Hazel",
    "Hootie And The Blowfish",
]

def remove_accents(text):
    """Eliminar acentos y caracteres diacríticos"""
    nfkd_form = unicodedata.normalize('NFKD', text)
    return ''.join(char for char in nfkd_form if not unicodedata.combining(char))

def clean_filename(filename):
    """
    Limpiar nombre de archivo eliminando basura común como URLs, 
    calidades de audio, etc.
    """
    name = filename
    
    # Eliminar patrones de basura (case insensitive)
    for pattern in JUNK_PATTERNS:
        name = re.sub(pattern, '', name, flags=re.IGNORECASE)
    
    # Convertir guiones bajos a espacios para mejor parsing
    name = name.replace('_', ' ')
    
    # Eliminar paréntesis vacíos o con solo espacios
    name = re.sub(r'\(\s*\)', '', name)
    
    # Eliminar corchetes vacíos
    name = re.sub(r'\[\s*\]', '', name)
    
    # Eliminar espacios múltiples
    name = re.sub(r'\s+', ' ', name).strip()
    
    # Eliminar guiones o espacios al inicio y final
    name = re.sub(r'^[-_\s]+', '', name)
    name = re.sub(r'[-_\s]+$', '', name)
    
    return name

def normalize_artist_name(name):
    """
    Normalizar nombre de artista para comparación.
    - Elimina acentos
    - Convierte a minúsculas
    - Expande abreviaciones
    - Elimina caracteres especiales
    - Elimina espacios extra
    """
    if not name:
        return ""
    
    # Convertir a minúsculas
    normalized = name.lower().strip()
    
    # Convertir guiones bajos a espacios ANTES de eliminar caracteres especiales
    normalized = normalized.replace('_', ' ')
    
    # Eliminar acentos
    normalized = remove_accents(normalized)
    
    # Expandir abreviaciones comunes
    for abbrev, full in ABBREVIATIONS.items():
        normalized = normalized.replace(abbrev, full)
    
    # Eliminar caracteres especiales excepto espacios
    normalized = re.sub(r'[^a-z0-9\s]', '', normalized)
    
    # Eliminar números al inicio (como "001 - ")
    normalized = re.sub(r'^\d+\s*[-_.]?\s*', '', normalized)
    
    # Eliminar espacios múltiples
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    
    return normalized

# Crear versiones normalizadas de los artistas conocidos
KNOWN_ARTISTS_NORMALIZED = {}

def _init_known_artists():
    """Inicializar diccionario de artistas conocidos con nombres normalizados"""
    global KNOWN_ARTISTS_NORMALIZED
    KNOWN_ARTISTS_NORMALIZED = {}
    for artist in KNOWN_ARTISTS:
        normalized = normalize_artist_name(artist)
        # Guardar el nombre más completo/con acentos
        if normalized not in KNOWN_ARTISTS_NORMALIZED:
            KNOWN_ARTISTS_NORMALIZED[normalized] = artist
        else:
            # Preferir versión con acentos o más larga
            existing = KNOWN_ARTISTS_NORMALIZED[normalized]
            if (artist != remove_accents(artist) and existing == remove_accents(existing)) or \
               (len(artist) > len(existing)):
                KNOWN_ARTISTS_NORMALIZED[normalized] = artist

_init_known_artists()

def find_known_artist_in_text(text):
    """
    Buscar un artista conocido dentro de un texto.
    Retorna el nombre del artista si lo encuentra, None si no.
    """
    if not text:
        return None
        
    normalized_text = normalize_artist_name(text)
    
    # Si el texto normalizado está vacío o es muy corto, no buscar
    if len(normalized_text) < 3:
        return None
    
    # Buscar coincidencias exactas o parciales con artistas conocidos
    best_match = None
    best_match_len = 0
    
    for norm_artist, original_artist in KNOWN_ARTISTS_NORMALIZED.items():
        # Verificar que el artista esté como palabra completa, no como subcadena
        # Por ejemplo, "ana" no debe coincidir con "mana"
        pattern = r'\b' + re.escape(norm_artist) + r'\b'
        if re.search(pattern, normalized_text):
            # Preferir coincidencias más largas (más específicas)
            if len(norm_artist) > best_match_len:
                best_match = original_artist
                best_match_len = len(norm_artist)
    
    return best_match

def is_likely_song_title(text):
    """
    Determinar si un texto parece ser un título de canción más que un nombre de artista.
    """
    normalized = normalize_artist_name(text)
    words = normalized.split()
    
    if not words:
        return False
    
    # Palabras que típicamente inician títulos de canciones
    song_starters = [
        'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas',
        'mi', 'tu', 'su', 'mis', 'tus', 'sus', 'nuestro', 'nuestra',
        'que', 'como', 'cuando', 'donde', 'por', 'para', 'con', 'sin',
        'sobre', 'entre', 'hasta', 'desde', 'hacia', 'contra',
        'si', 'no', 'ya', 'aun', 'solo', 'nunca', 'siempre', 'jamas',
        'the', 'a', 'an', 'my', 'your', 'our', 'i', 'you', 'we', 'he', 'she',
        'amor', 'corazon', 'vida', 'noche', 'dia', 'tiempo', 'mundo',
        'sueno', 'sueño', 'beso', 'fuego', 'cielo', 'mar', 'sol', 'luna',
        'te', 'me', 'se', 'le', 'nos', 'quiero', 'amo', 'necesito',
        'eres', 'soy', 'estoy', 'voy', 'ven', 'dame', 'dime', 'dejame',
        'esta', 'ese', 'esa', 'esto', 'eso', 'aqui', 'ahi', 'alla',
        'hoy', 'ayer', 'manana', 'tarde', 'pronto', 'despues',
        'todo', 'toda', 'todos', 'todas', 'nada', 'algo', 'alguien',
        'brindaremos', 'cantemos', 'bailemos', 'vivamos',
        'silueta', 'cristal', 'perfecta', 'perfecto',
    ]
    
    # Si la primera palabra es un indicador de canción
    if words[0] in song_starters:
        return True
    
    # Si contiene verbos conjugados típicos de canciones
    verb_patterns = [
        r'\b(quiero|amo|necesito|extraño|siento|pienso)\b',
        r'\b(eres|soy|estoy|estas|tengo|tienes)\b',
        r'\b(vamos|voy|vas|viene|vengo)\b',
        r'\b(dame|dime|dejame|llevame|besame)\b',
        r'\b(contigo|conmigo|sin ti|por ti)\b',
    ]
    
    for pattern in verb_patterns:
        if re.search(pattern, normalized):
            return True
    
    return False

def extract_artist_from_filename(filename):
    """
    Extraer el nombre del artista de un nombre de archivo.
    Maneja múltiples formatos:
    - "Artista - Canción.mp3"
    - "Canción - Artista.mp3"
    - "Artista-Canción.mp3" (guión sin espacios)
    - "Canción (Artista).mp3" (artista entre paréntesis)
    - "001 - Artista - Canción.mp3"
    - "CANCIÓN ARTISTA.mp3" (sin separador)
    """
    # Quitar extensión
    name = os.path.splitext(filename)[0]
    
    # Limpiar basura (URLs, calidades, etc.)
    name = clean_filename(name)
    
    # Quitar números al inicio
    name = re.sub(r'^\d+\s*[-_.]?\s*', '', name).strip()
    
    # Si después de limpiar está vacío, retornar None
    if not name or len(name) < 3:
        return None
    
    # Caso 0: Buscar artista entre paréntesis (formato "Canción (Artista)" o "Canción...(Artista)")
    parenthesis_match = re.search(r'\(([^)]+)\)', name)
    if parenthesis_match:
        potential_artist = parenthesis_match.group(1).strip()
        artist = find_known_artist_in_text(potential_artist)
        if artist:
            return artist
    
    # Caso 1: Tiene separador " - " (con espacios)
    if " - " in name:
        parts = name.split(" - ")
        
        # Filtrar partes vacías
        parts = [p.strip() for p in parts if p.strip()]
        
        if len(parts) >= 2:
            part1 = parts[0].strip()
            part2 = parts[-1].strip()  # Usar la última parte en caso de múltiples separadores
            
            # Si hay más de 2 partes, la del medio podría ser el artista
            if len(parts) > 2:
                # Buscar artista conocido en todas las partes
                for part in parts:
                    artist = find_known_artist_in_text(part)
                    if artist:
                        return artist
            
            # Verificar si alguna parte es un artista conocido
            artist_in_part1 = find_known_artist_in_text(part1)
            artist_in_part2 = find_known_artist_in_text(part2)
            
            if artist_in_part1 and not artist_in_part2:
                return artist_in_part1
            elif artist_in_part2 and not artist_in_part1:
                return artist_in_part2
            elif artist_in_part1 and artist_in_part2:
                # Ambos tienen artista conocido
                # Preferir el que esté en la posición estándar (primera parte)
                # a menos que la primera parte parezca título de canción
                if is_likely_song_title(part1):
                    return artist_in_part2
                return artist_in_part1
            else:
                # Ninguno es artista conocido, usar heurísticas
                if is_likely_song_title(part1) and not is_likely_song_title(part2):
                    # Part1 parece ser la canción, part2 es el artista
                    return part2
                elif is_likely_song_title(part2) and not is_likely_song_title(part1):
                    # Part2 parece ser la canción, part1 es el artista
                    return part1
                else:
                    # Asumir formato estándar: Artista - Canción
                    # Pero verificar que no sea un patrón de basura
                    if len(part1) > 2 and not re.match(r'^[\d\s\-_.]+$', part1):
                        return part1
                    elif len(part2) > 2 and not re.match(r'^[\d\s\-_.]+$', part2):
                        return part2
    
    # Caso 2: Tiene separador "-" sin espacios (formato "Artista-Canción")
    elif "-" in name and " - " not in name:
        parts = name.split("-")
        parts = [p.strip() for p in parts if p.strip()]
        
        if len(parts) >= 2:
            part1 = parts[0].strip()
            part2 = parts[-1].strip()
            
            # Buscar artista conocido en las partes
            artist_in_part1 = find_known_artist_in_text(part1)
            artist_in_part2 = find_known_artist_in_text(part2)
            
            if artist_in_part1 and not artist_in_part2:
                return artist_in_part1
            elif artist_in_part2 and not artist_in_part1:
                return artist_in_part2
            elif artist_in_part1 and artist_in_part2:
                # Preferir el que está en posición estándar a menos que parezca título
                if is_likely_song_title(part1):
                    return artist_in_part2
                return artist_in_part1
            else:
                # Ninguno conocido, usar heurísticas
                if is_likely_song_title(part1) and not is_likely_song_title(part2):
                    return part2
                elif is_likely_song_title(part2) and not is_likely_song_title(part1):
                    return part1
                else:
                    # Asumir formato estándar: Artista-Canción
                    if len(part1) > 2:
                        return part1
    
    # Caso 3: Tiene separador "_" o "__"
    elif "__" in name or "_" in name:
        separator = "__" if "__" in name else "_"
        parts = name.split(separator)
        parts = [p.strip() for p in parts if p.strip()]
        
        if len(parts) >= 2:
            # Buscar artista conocido en las partes
            for part in parts:
                artist = find_known_artist_in_text(part)
                if artist:
                    return artist
            # Si no se encuentra, usar la primera parte
            clean_part = parts[0].strip().replace("_", " ")
            if len(clean_part) > 2:
                return clean_part
    
    # Caso 4: Sin separador claro - buscar artista conocido en todo el texto
    else:
        artist = find_known_artist_in_text(name)
        if artist:
            return artist
        
        # Último recurso: buscar patrones comunes
        # Muchos archivos tienen el formato "CANCIÓN   ARTISTA" con espacios múltiples
        parts = re.split(r'\s{2,}', name)  # Dividir por 2+ espacios
        if len(parts) >= 2:
            # El artista suele estar al final
            for part in reversed(parts):
                artist = find_known_artist_in_text(part)
                if artist:
                    return artist
    
    return None

def similarity_ratio(name1, name2):
    """Calcular ratio de similitud entre dos nombres"""
    return SequenceMatcher(None, name1, name2).ratio()

def are_similar_artists(name1, name2, threshold=0.90):
    """
    Determinar si dos nombres de artistas son el mismo.
    Usa normalización y comparación de similitud.
    NOTA: threshold aumentado a 0.90 para evitar falsos positivos
    como Juan Gabriel vs Ana Gabriel
    """
    norm1 = normalize_artist_name(name1)
    norm2 = normalize_artist_name(name2)
    
    # Si alguno está vacío, no son similares
    if not norm1 or not norm2:
        return False
    
    # Si son exactamente iguales después de normalizar
    if norm1 == norm2:
        return True
    
    # Verificar palabras en común
    words1 = set(norm1.split())
    words2 = set(norm2.split())
    
    # Si tienen menos de la mitad de palabras en común, no son el mismo
    common_words = words1 & words2
    total_words = max(len(words1), len(words2))
    
    if total_words > 1 and len(common_words) < total_words * 0.5:
        return False
    
    # Caso especial: nombres con "Gabriel" - Juan Gabriel vs Ana Gabriel son diferentes
    if 'gabriel' in words1 and 'gabriel' in words2:
        # Verificar que el otro nombre sea el mismo
        other_words1 = words1 - {'gabriel'}
        other_words2 = words2 - {'gabriel'}
        if other_words1 != other_words2:
            return False
    
    # Si uno está contenido en el otro Y es significativo (más de 3 caracteres)
    if len(norm1) > 3 and len(norm2) > 3:
        if norm1 == norm2:
            return True
        # Solo considerar contenido si es una porción significativa
        if norm1 in norm2 and len(norm1) >= len(norm2) * 0.8:
            return True
        if norm2 in norm1 and len(norm2) >= len(norm1) * 0.8:
            return True
    
    # Comparar similitud con threshold alto
    ratio = similarity_ratio(norm1, norm2)
    return ratio >= threshold

def find_canonical_artist_name(artist_name, existing_artists):
    """
    Buscar si el artista ya existe con otro nombre similar.
    Retorna el nombre canónico si existe, o el nombre original si no.
    """
    normalized_new = normalize_artist_name(artist_name)
    
    for existing in existing_artists:
        if are_similar_artists(artist_name, existing):
            # Preferir el nombre más largo/completo
            if len(existing) > len(artist_name):
                return existing
            return artist_name
    
    return artist_name

def get_best_artist_name(name1, name2):
    """
    Dado dos nombres de artista que son el mismo, elegir el mejor.
    Preferir: con acentos > más largo > título case > el que está en KNOWN_ARTISTS
    """
    # Verificar si alguno está en la lista de conocidos
    norm1 = normalize_artist_name(name1)
    norm2 = normalize_artist_name(name2)
    
    if norm1 in KNOWN_ARTISTS_NORMALIZED:
        return KNOWN_ARTISTS_NORMALIZED[norm1]
    if norm2 in KNOWN_ARTISTS_NORMALIZED:
        return KNOWN_ARTISTS_NORMALIZED[norm2]
    
    # Preferir el que tiene acentos
    has_accents_1 = name1 != remove_accents(name1)
    has_accents_2 = name2 != remove_accents(name2)
    
    if has_accents_1 and not has_accents_2:
        return name1
    if has_accents_2 and not has_accents_1:
        return name2
    
    # Preferir el más largo
    if len(name1) > len(name2):
        return name1
    if len(name2) > len(name1):
        return name2
    
    # Preferir título case sobre MAYÚSCULAS
    if name1.istitle() and not name2.istitle():
        return name1
    if name2.istitle() and not name1.istitle():
        return name2
    
    # Preferir el que no está todo en mayúsculas
    if name1.isupper() and not name2.isupper():
        return name2
    if name2.isupper() and not name1.isupper():
        return name1
    
    return name1

def group_similar_artists(artists_dict):
    """
    Agrupar artistas con nombres similares.
    Retorna un nuevo diccionario con artistas agrupados.
    """
    # Lista de artistas únicos (normalizados -> nombre original preferido)
    canonical_names = {}
    grouped = defaultdict(list)
    
    for artist, songs in artists_dict.items():
        normalized = normalize_artist_name(artist)
        
        # Saltar artistas vacíos o inválidos
        if not normalized or len(normalized) < 2:
            grouped["Sin Artista"].extend(songs)
            continue
        
        # Buscar si ya existe un artista similar
        found_match = False
        for canon_norm, canon_original in list(canonical_names.items()):
            if are_similar_artists(artist, canon_original):
                # Elegir el mejor nombre
                best_name = get_best_artist_name(artist, canon_original)
                
                if best_name != canon_original:
                    # Actualizar nombre canónico
                    old_songs = grouped[canon_original]
                    del grouped[canon_original]
                    grouped[best_name] = old_songs + songs
                    canonical_names[normalize_artist_name(best_name)] = best_name
                else:
                    grouped[canon_original].extend(songs)
                found_match = True
                break
        
        if not found_match:
            canonical_names[normalized] = artist
            grouped[artist] = songs
    
    return grouped

# =============================================================================
# HILOS PARA OPERACIONES EN SEGUNDO PLANO
# =============================================================================

class SearchThread(QThread):
    """Hilo para buscar videos sin bloquear la UI"""
    results_ready = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, query, search_type="song", max_results=20):
        super().__init__()
        self.query = query
        self.search_type = search_type
        self.max_results = max_results
    
    def run(self):
        try:
            # Modificar la búsqueda según el tipo
            if self.search_type == "song":
                search_query = f"{self.query} audio"
            elif self.search_type == "artist":
                search_query = f"{self.query} official music"
            else:
                search_query = self.query
            
            request = YOUTUBE_API.search().list(
                part="snippet",
                q=search_query,
                type="video",
                maxResults=self.max_results,
                videoCategoryId="10"  # Categoría de música
            )
            response = request.execute()
            
            results = []
            for video in response.get('items', []):
                video_id = video['id']['videoId']
                snippet = video['snippet']
                results.append({
                    'title': snippet['title'],
                    'channel': snippet['channelTitle'],
                    'video_id': video_id,
                    'url': f"https://www.youtube.com/watch?v={video_id}",
                    'thumbnail_url': f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg"
                })
            
            self.results_ready.emit(results)
        except Exception as e:
            self.error_occurred.emit(str(e))


class ThumbnailLoader(QThread):
    """Hilo para cargar miniaturas sin bloquear la UI"""
    thumbnail_loaded = pyqtSignal(int, QPixmap)
    
    def __init__(self, index, url):
        super().__init__()
        self.index = index
        self.url = url
    
    def run(self):
        try:
            response = requests.get(self.url, timeout=5)
            if response.status_code == 200:
                pixmap = QPixmap()
                pixmap.loadFromData(response.content)
                pixmap = pixmap.scaled(120, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.thumbnail_loaded.emit(self.index, pixmap)
        except:
            pass


class DownloadThread(QThread):
    """Hilo para descargar videos sin bloquear la UI"""
    progress_updated = pyqtSignal(dict)
    download_finished = pyqtSignal(str)
    download_error = pyqtSignal(str)
    
    def __init__(self, video_url, save_path, artist_name="", song_number=0):
        super().__init__()
        self.video_url = video_url
        self.save_path = save_path
        self.artist_name = artist_name
        self.song_number = song_number
    
    def run(self):
        try:
            # Crear carpeta del artista si se especificó
            if self.artist_name:
                artist_folder = os.path.join(self.save_path, self.sanitize_filename(self.artist_name))
                os.makedirs(artist_folder, exist_ok=True)
                output_path = artist_folder
            else:
                output_path = self.save_path
            
            # Template con número si se especificó
            if self.song_number > 0:
                output_template = os.path.join(output_path, f'{self.song_number:03d} - %(title)s.%(ext)s')
            else:
                output_template = os.path.join(output_path, '%(title)s.%(ext)s')
            
            options = {
                'format': 'bestaudio/best',
                'outtmpl': output_template,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'ffmpeg_location': r'C:\ProgramData\chocolatey\lib\ffmpeg-full\tools\ffmpeg\bin',
                'progress_hooks': [self.progress_hook],
                'quiet': True
            }
            
            with yt_dlp.YoutubeDL(options) as ydl:
                ydl.download([self.video_url])
            
            self.download_finished.emit("Descarga completada exitosamente")
        except Exception as e:
            self.download_error.emit(str(e))
    
    def progress_hook(self, d):
        self.progress_updated.emit(d)
    
    def sanitize_filename(self, name):
        return re.sub(r'[<>:"/\\|?*]', '', name)


# =============================================================================
# INDICADOR DE CARGA CIRCULAR
# =============================================================================

class CircularProgress(QWidget):
    """Widget de progreso circular animado"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(80, 80)
        self.angle = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.rotate)
        self.hide()
    
    def start(self):
        self.show()
        self.timer.start(30)
    
    def stop(self):
        self.timer.stop()
        self.hide()
    
    def rotate(self):
        self.angle = (self.angle + 10) % 360
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Fondo semi-transparente
        painter.setBrush(QColor(30, 30, 30, 200))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 10, 10)
        
        # Arco de progreso
        pen_width = 6
        painter.setPen(QColor("#3a8ee6"))
        painter.setBrush(Qt.NoBrush)
        
        from PyQt5.QtGui import QPen
        pen = QPen(QColor("#3a8ee6"), pen_width, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(pen)
        
        rect = self.rect().adjusted(15, 15, -15, -15)
        painter.drawArc(rect, self.angle * 16, 270 * 16)


# =============================================================================
# APLICACIÓN PRINCIPAL
# =============================================================================

class YouTubeDownloader(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎵 Descargador de Música - Directrack")
        self.setGeometry(100, 100, 1000, 700)
        self.save_path = os.getcwd()
        self.thumbnail_loaders = []
        self.search_results = []
        self.next_song_number = 1
        
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #1a1a2e;
                color: #ffffff;
                font-family: 'Segoe UI';
            }
            QLineEdit {
                background-color: #16213e;
                border: 2px solid #0f3460;
                padding: 10px;
                border-radius: 8px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #e94560;
            }
            QListWidget {
                background-color: #16213e;
                border: 2px solid #0f3460;
                border-radius: 8px;
                padding: 5px;
            }
            QListWidget::item {
                background-color: #1a1a2e;
                border-radius: 5px;
                margin: 3px;
                padding: 5px;
            }
            QListWidget::item:selected {
                background-color: #e94560;
            }
            QListWidget::item:hover {
                background-color: #0f3460;
            }
            QPushButton {
                background-color: #e94560;
                color: white;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ff6b6b;
            }
            QPushButton:pressed {
                background-color: #c73e54;
            }
            QPushButton:disabled {
                background-color: #444;
                color: #888;
            }
            QTabWidget::pane {
                border: 2px solid #0f3460;
                border-radius: 8px;
                background-color: #16213e;
            }
            QTabBar::tab {
                background-color: #0f3460;
                color: white;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }
            QTabBar::tab:selected {
                background-color: #e94560;
            }
            QTabBar::tab:hover {
                background-color: #1a1a2e;
            }
            QProgressBar {
                border: 2px solid #0f3460;
                border-radius: 8px;
                text-align: center;
                font-size: 12px;
                color: white;
                background-color: #16213e;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #e94560, stop:1 #ff6b6b);
                border-radius: 6px;
            }
            QTreeWidget {
                background-color: #16213e;
                border: 2px solid #0f3460;
                border-radius: 8px;
            }
            QTreeWidget::item {
                padding: 5px;
            }
            QTreeWidget::item:selected {
                background-color: #e94560;
            }
            QComboBox {
                background-color: #16213e;
                border: 2px solid #0f3460;
                border-radius: 5px;
                padding: 5px;
                color: white;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #16213e;
                selection-background-color: #e94560;
            }
            QSpinBox {
                background-color: #16213e;
                border: 2px solid #0f3460;
                border-radius: 5px;
                padding: 5px;
                color: white;
            }
            QGroupBox {
                border: 2px solid #0f3460;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #e94560;
            }
            QLabel {
                color: #ffffff;
            }
        """)

        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Título
        title_label = QLabel("🎵 Descargador de Música")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #e94560; padding: 10px;")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        # Tabs para diferentes funciones
        self.tabs = QTabWidget()
        
        # Tab 1: Buscar Canciones
        self.tab_songs = QWidget()
        self.setup_songs_tab()
        self.tabs.addTab(self.tab_songs, "🎵 Buscar Canciones")
        
        # Tab 2: Buscar Artistas
        self.tab_artists = QWidget()
        self.setup_artists_tab()
        self.tabs.addTab(self.tab_artists, "🎤 Buscar Artistas")
        
        # Tab 3: Organizar Biblioteca
        self.tab_library = QWidget()
        self.setup_library_tab()
        self.tabs.addTab(self.tab_library, "📁 Mi Biblioteca")
        
        main_layout.addWidget(self.tabs)

        # Barra de progreso de descarga
        progress_layout = QHBoxLayout()
        self.progress_label = QLabel("Listo para descargar")
        self.progress_label.setStyleSheet("color: #aaa;")
        progress_layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(25)
        progress_layout.addWidget(self.progress_bar)
        
        main_layout.addLayout(progress_layout)

        # Botones inferiores
        button_layout = QHBoxLayout()
        
        self.select_path_button = QPushButton("📂 Seleccionar Carpeta")
        self.select_path_button.clicked.connect(self.select_download_path)
        button_layout.addWidget(self.select_path_button)
        
        self.path_label = QLabel(f"Carpeta: {self.save_path}")
        self.path_label.setStyleSheet("color: #888; font-size: 11px;")
        button_layout.addWidget(self.path_label, 1)
        
        self.download_button = QPushButton("⬇️ Descargar Seleccionada")
        self.download_button.clicked.connect(self.download_selected)
        button_layout.addWidget(self.download_button)
        
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
        
        # Indicador de carga circular
        self.loading_indicator = CircularProgress(self)
        self.loading_indicator.move(self.width() // 2 - 40, self.height() // 2 - 40)

    def setup_songs_tab(self):
        """Configurar pestaña de búsqueda de canciones"""
        layout = QVBoxLayout()
        
        # Búsqueda
        search_layout = QHBoxLayout()
        self.song_search_input = QLineEdit()
        self.song_search_input.setPlaceholderText("🔍 Buscar canción... (ej: Bohemian Rhapsody)")
        self.song_search_input.returnPressed.connect(lambda: self.search_video("song"))
        search_layout.addWidget(self.song_search_input)
        
        self.song_search_button = QPushButton("🔍 Buscar")
        self.song_search_button.clicked.connect(lambda: self.search_video("song"))
        search_layout.addWidget(self.song_search_button)
        
        layout.addLayout(search_layout)
        
        # Opciones de descarga
        options_layout = QHBoxLayout()
        
        options_layout.addWidget(QLabel("Artista:"))
        self.artist_input = QLineEdit()
        self.artist_input.setPlaceholderText("Nombre del artista (opcional)")
        self.artist_input.setMaximumWidth(200)
        options_layout.addWidget(self.artist_input)
        
        options_layout.addWidget(QLabel("Número:"))
        self.song_number_spin = QSpinBox()
        self.song_number_spin.setRange(0, 9999)
        self.song_number_spin.setValue(0)
        self.song_number_spin.setToolTip("0 = sin numeración")
        self.song_number_spin.setMaximumWidth(80)
        options_layout.addWidget(self.song_number_spin)
        
        options_layout.addStretch()
        layout.addLayout(options_layout)
        
        # Lista de resultados
        self.song_results_list = QListWidget()
        self.song_results_list.setIconSize(QSize(120, 90))
        self.song_results_list.setSpacing(8)
        self.song_results_list.itemDoubleClicked.connect(self.download_selected)
        layout.addWidget(self.song_results_list)
        
        self.tab_songs.setLayout(layout)

    def setup_artists_tab(self):
        """Configurar pestaña de búsqueda de artistas"""
        layout = QVBoxLayout()
        
        # Búsqueda
        search_layout = QHBoxLayout()
        self.artist_search_input = QLineEdit()
        self.artist_search_input.setPlaceholderText("🔍 Buscar artista... (ej: Queen, The Beatles)")
        self.artist_search_input.returnPressed.connect(lambda: self.search_video("artist"))
        search_layout.addWidget(self.artist_search_input)
        
        self.artist_search_button = QPushButton("🔍 Buscar")
        self.artist_search_button.clicked.connect(lambda: self.search_video("artist"))
        search_layout.addWidget(self.artist_search_button)
        
        layout.addLayout(search_layout)
        
        # Info
        info_label = QLabel("💡 Al buscar un artista, se mostrarán sus videos musicales oficiales")
        info_label.setStyleSheet("color: #888; font-style: italic;")
        layout.addWidget(info_label)
        
        # Lista de resultados
        self.artist_results_list = QListWidget()
        self.artist_results_list.setIconSize(QSize(120, 90))
        self.artist_results_list.setSpacing(8)
        self.artist_results_list.itemDoubleClicked.connect(self.download_selected)
        layout.addWidget(self.artist_results_list)
        
        self.tab_artists.setLayout(layout)

    def setup_library_tab(self):
        """Configurar pestaña de biblioteca/organización"""
        layout = QVBoxLayout()
        
        # Controles
        controls_layout = QHBoxLayout()
        
        self.scan_button = QPushButton("🔄 Escanear Carpeta")
        self.scan_button.clicked.connect(self.scan_library)
        controls_layout.addWidget(self.scan_button)
        
        self.organize_button = QPushButton("📁 Organizar por Artista")
        self.organize_button.clicked.connect(self.organize_by_artist)
        controls_layout.addWidget(self.organize_button)
        
        self.flatten_button = QPushButton("📤 Desorganizar (Aplanar)")
        self.flatten_button.clicked.connect(self.flatten_folders)
        self.flatten_button.setToolTip("Mover todas las canciones de subcarpetas a la carpeta principal")
        controls_layout.addWidget(self.flatten_button)
        
        self.renumber_button = QPushButton("🔢 Renumerar Canciones")
        self.renumber_button.clicked.connect(self.renumber_songs)
        controls_layout.addWidget(self.renumber_button)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # Estadísticas
        self.stats_label = QLabel("📊 Selecciona una carpeta para escanear tu biblioteca")
        self.stats_label.setStyleSheet("color: #aaa; padding: 10px;")
        layout.addWidget(self.stats_label)
        
        # Árbol de biblioteca
        self.library_tree = QTreeWidget()
        self.library_tree.setHeaderLabels(["Artista / Canción", "Tipo", "Tamaño"])
        self.library_tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.library_tree.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.library_tree.header().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        layout.addWidget(self.library_tree)
        
        self.tab_library.setLayout(layout)

    def search_video(self, search_type="song"):
        """Buscar videos según el tipo"""
        if search_type == "song":
            query = self.song_search_input.text().strip()
            results_list = self.song_results_list
        else:
            query = self.artist_search_input.text().strip()
            results_list = self.artist_results_list
        
        if not query:
            QMessageBox.warning(self, "Advertencia", "Por favor, ingresa un término de búsqueda.")
            return
        
        # Mostrar indicador de carga
        self.loading_indicator.move(self.width() // 2 - 40, self.height() // 2 - 40)
        self.loading_indicator.start()
        
        # Deshabilitar botones durante la búsqueda
        self.song_search_button.setEnabled(False)
        self.artist_search_button.setEnabled(False)
        
        # Limpiar resultados anteriores
        results_list.clear()
        self.search_results = []
        
        # Cancelar loaders anteriores
        for loader in self.thumbnail_loaders:
            loader.quit()
        self.thumbnail_loaders = []
        
        # Iniciar búsqueda en segundo plano
        self.search_thread = SearchThread(query, search_type)
        self.search_thread.results_ready.connect(
            lambda results: self.on_search_results(results, results_list)
        )
        self.search_thread.error_occurred.connect(self.on_search_error)
        self.search_thread.start()

    def on_search_results(self, results, results_list):
        """Manejar resultados de búsqueda"""
        self.loading_indicator.stop()
        self.song_search_button.setEnabled(True)
        self.artist_search_button.setEnabled(True)
        
        self.search_results = results
        
        for i, video in enumerate(results):
            # Crear item con placeholder
            item = QListWidgetItem(f"🎵 {video['title']}\n   📺 {video['channel']}")
            item.setData(Qt.UserRole, video)
            item.setSizeHint(QSize(0, 100))
            results_list.addItem(item)
            
            # Cargar miniatura en segundo plano
            loader = ThumbnailLoader(i, video['thumbnail_url'])
            loader.thumbnail_loaded.connect(
                lambda idx, pixmap, lst=results_list: self.on_thumbnail_loaded(idx, pixmap, lst)
            )
            self.thumbnail_loaders.append(loader)
            loader.start()
        
        if not results:
            QMessageBox.information(self, "Sin resultados", "No se encontraron videos para tu búsqueda.")

    def on_thumbnail_loaded(self, index, pixmap, results_list):
        """Actualizar miniatura cuando se carga"""
        if index < results_list.count():
            item = results_list.item(index)
            item.setIcon(QIcon(pixmap))

    def on_search_error(self, error):
        """Manejar error de búsqueda"""
        self.loading_indicator.stop()
        self.song_search_button.setEnabled(True)
        self.artist_search_button.setEnabled(True)
        QMessageBox.critical(self, "Error", f"No se pudo buscar: {error}")

    def select_download_path(self):
        path = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta de descarga", self.save_path)
        if path:
            self.save_path = path
            self.path_label.setText(f"Carpeta: {path}")

    def download_selected(self):
        """Descargar video seleccionado"""
        # Determinar qué lista está activa
        current_tab = self.tabs.currentIndex()
        if current_tab == 0:
            item = self.song_results_list.currentItem()
        elif current_tab == 1:
            item = self.artist_results_list.currentItem()
        else:
            QMessageBox.warning(self, "Advertencia", "Selecciona un video de las pestañas de búsqueda.")
            return
        
        if not item:
            QMessageBox.warning(self, "Advertencia", "Selecciona un video para descargar.")
            return
        
        video_data = item.data(Qt.UserRole)
        if not video_data:
            return
        
        video_url = video_data['url']
        
        if not self.save_path:
            QMessageBox.warning(self, "Advertencia", "Selecciona una carpeta de descarga.")
            return
        
        # Obtener opciones
        artist_name = self.artist_input.text().strip() if current_tab == 0 else ""
        song_number = self.song_number_spin.value() if current_tab == 0 else 0
        
        # Deshabilitar botón de descarga
        self.download_button.setEnabled(False)
        self.progress_label.setText(f"Descargando: {video_data['title'][:50]}...")
        self.progress_bar.setValue(0)
        
        # Iniciar descarga en segundo plano
        self.download_thread = DownloadThread(video_url, self.save_path, artist_name, song_number)
        self.download_thread.progress_updated.connect(self.update_progress)
        self.download_thread.download_finished.connect(self.on_download_finished)
        self.download_thread.download_error.connect(self.on_download_error)
        self.download_thread.start()

    def update_progress(self, d):
        if d['status'] == 'downloading':
            if 'downloaded_bytes' in d and 'total_bytes' in d:
                downloaded = d['downloaded_bytes']
                total = d['total_bytes']
                if total > 0:
                    percentage = int(downloaded / total * 100)
                    self.progress_bar.setValue(percentage)
                    self.progress_label.setText(f"Descargando... {percentage}%")
        elif d['status'] == 'finished':
            self.progress_bar.setValue(100)
            self.progress_label.setText("Procesando audio...")

    def on_download_finished(self, message):
        self.download_button.setEnabled(True)
        self.progress_label.setText("✅ " + message)
        self.progress_bar.setValue(100)
        
        # Incrementar número de canción para la próxima
        if self.song_number_spin.value() > 0:
            self.song_number_spin.setValue(self.song_number_spin.value() + 1)
        
        QMessageBox.information(self, "Éxito", message)

    def on_download_error(self, error):
        self.download_button.setEnabled(True)
        self.progress_label.setText("❌ Error en la descarga")
        self.progress_bar.setValue(0)
        QMessageBox.critical(self, "Error", f"No se pudo descargar: {error}")

    def scan_library(self):
        """Escanear carpeta de música y mostrar estadísticas"""
        path = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta de música", self.save_path)
        if not path:
            return
        
        self.library_tree.clear()
        artists_raw = defaultdict(list)
        total_songs = 0
        total_size = 0
        
        # Escanear archivos
        for root, dirs, files in os.walk(path):
            for file in files:
                if file.lower().endswith(('.mp3', '.m4a', '.wav', '.flac', '.ogg')):
                    file_path = os.path.join(root, file)
                    file_size = os.path.getsize(file_path)
                    
                    # Intentar extraer artista del nombre o carpeta
                    parent_folder = os.path.basename(root)
                    if parent_folder != os.path.basename(path):
                        # Si está en una subcarpeta, usar el nombre de la carpeta como artista
                        artist = parent_folder
                    else:
                        # Usar el algoritmo inteligente de extracción
                        artist = extract_artist_from_filename(file)
                        
                        if not artist:
                            artist = "Sin Artista"
                    
                    if not artist or not artist.strip():
                        artist = "Sin Artista"
                    
                    artists_raw[artist].append({
                        'name': file,
                        'path': file_path,
                        'size': file_size
                    })
                    total_songs += 1
                    total_size += file_size
        
        # Agrupar artistas similares
        artists = group_similar_artists(artists_raw)
        
        # Mostrar estadísticas
        size_mb = total_size / (1024 * 1024)
        original_count = len(artists_raw)
        grouped_count = len(artists)
        
        # Contar canciones sin artista
        sin_artista_count = len(artists.get("Sin Artista", []))
        
        stats_text = f"📊 Total: {total_songs} canciones | {grouped_count} artistas"
        if original_count != grouped_count:
            stats_text += f" (agrupados de {original_count})"
        stats_text += f" | {size_mb:.1f} MB"
        if sin_artista_count > 0:
            stats_text += f" | ⚠️ {sin_artista_count} sin artista identificado"
        
        self.stats_label.setText(stats_text)
        
        # Llenar árbol
        for artist, songs in sorted(artists.items()):
            artist_item = QTreeWidgetItem([f"🎤 {artist}", "Artista", f"{len(songs)} canciones"])
            artist_item.setExpanded(False)
            
            for song in sorted(songs, key=lambda x: x['name']):
                size_str = f"{song['size'] / 1024:.0f} KB"
                song_item = QTreeWidgetItem([f"  🎵 {song['name']}", "Canción", size_str])
                song_item.setData(0, Qt.UserRole, song['path'])
                artist_item.addChild(song_item)
            
            self.library_tree.addTopLevelItem(artist_item)

    def organize_by_artist(self):
        """Organizar canciones renombrándolas con el artista al inicio para agruparlas alfabéticamente"""
        path = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta a organizar", self.save_path)
        if not path:
            return
        
        # Primero, recopilar todos los artistas y sus archivos
        artists_files = defaultdict(list)
        unidentified_files = []
        
        for file in os.listdir(path):
            if file.lower().endswith(('.mp3', '.m4a', '.wav', '.flac', '.ogg')):
                # Usar el algoritmo inteligente de extracción
                artist = extract_artist_from_filename(file)
                
                if artist:
                    artists_files[artist].append(file)
                else:
                    unidentified_files.append(file)
        
        if not artists_files and not unidentified_files:
            QMessageBox.warning(self, "Sin archivos", 
                              "No se encontraron archivos de música en la carpeta.")
            return
        
        # Agrupar artistas similares
        grouped_artists = group_similar_artists(
            {artist: [{'name': f, 'path': os.path.join(path, f)} for f in files] 
             for artist, files in artists_files.items()}
        )
        
        renamed_count = 0
        skipped_count = 0
        
        # Renombrar archivos agregando el artista al inicio
        for canonical_artist, songs in grouped_artists.items():
            safe_artist = self.sanitize_filename(canonical_artist)
            
            for song in songs:
                src = song['path']
                original_name = song['name']
                
                if not os.path.exists(src):
                    continue
                
                # Verificar si ya tiene el nombre del artista al inicio
                name_without_ext = os.path.splitext(original_name)[0]
                ext = os.path.splitext(original_name)[1]
                
                # Limpiar el nombre (quitar numeración existente y el artista si ya está)
                clean_name = re.sub(r'^\d+\s*[-_.]?\s*', '', name_without_ext)  # Quitar números al inicio
                
                # Verificar si el artista ya está al inicio del nombre
                artist_normalized = normalize_artist_name(safe_artist)
                name_normalized = normalize_artist_name(clean_name)
                
                # Si ya empieza con el artista, no renombrar
                if name_normalized.startswith(artist_normalized):
                    skipped_count += 1
                    continue
                
                # Quitar el artista del nombre si está en otra posición (ej: "Canción - Artista")
                # para evitar duplicación
                if " - " in clean_name:
                    parts = clean_name.split(" - ")
                    # Buscar y remover la parte que coincide con el artista
                    new_parts = []
                    for part in parts:
                        if normalize_artist_name(part) != artist_normalized:
                            new_parts.append(part)
                    if new_parts:
                        clean_name = " - ".join(new_parts)
                
                # Crear nuevo nombre: "Artista - Canción.ext"
                new_name = f"{safe_artist} - {clean_name}{ext}"
                dst = os.path.join(path, new_name)
                
                # Si ya existe un archivo con ese nombre, agregar sufijo
                if os.path.exists(dst) and src != dst:
                    counter = 1
                    while os.path.exists(dst):
                        new_name = f"{safe_artist} - {clean_name} ({counter}){ext}"
                        dst = os.path.join(path, new_name)
                        counter += 1
                
                # Renombrar
                if src != dst:
                    try:
                        os.rename(src, dst)
                        renamed_count += 1
                    except Exception as e:
                        print(f"Error renombrando {src}: {e}")
                        skipped_count += 1
                else:
                    skipped_count += 1
        
        # Renombrar archivos sin artista identificado con prefijo especial
        for file in unidentified_files:
            src = os.path.join(path, file)
            if os.path.exists(src):
                # Verificar si ya tiene el prefijo
                if not file.startswith("_Sin Artista - "):
                    new_name = f"_Sin Artista - {file}"
                    dst = os.path.join(path, new_name)
                    if not os.path.exists(dst):
                        try:
                            os.rename(src, dst)
                            renamed_count += 1
                        except:
                            pass
        
        # Contar artistas que fueron fusionados
        original_count = len(artists_files)
        final_count = len(grouped_artists)
        merged_artists = original_count - final_count
        
        message = f"✅ Se renombraron {renamed_count} canciones con el formato 'Artista - Canción'."
        if skipped_count > 0:
            message += f"\n\n⏭️ {skipped_count} archivos ya tenían el formato correcto o fueron omitidos."
        if merged_artists > 0:
            message += f"\n\n🔗 Se unificaron {merged_artists} variantes de nombres de artistas."
        if unidentified_files:
            message += f"\n\n⚠️ {len(unidentified_files)} archivos sin artista identificado (prefijo '_Sin Artista')."
        
        QMessageBox.information(self, "Organización completada", message)


    def flatten_folders(self):
        """Mover todas las canciones de subcarpetas a la carpeta principal y eliminar carpetas vacías"""
        path = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta a aplanar", self.save_path)
        if not path:
            return
        
        # Confirmar acción
        reply = QMessageBox.question(
            self, 
            "Confirmar Desorganización",
            f"¿Estás seguro de que deseas mover TODAS las canciones de las subcarpetas a:\n\n{path}\n\nLas carpetas vacías serán eliminadas.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        moved_count = 0
        skipped_count = 0
        deleted_folders = 0
        
        # Recopilar todas las subcarpetas (de más profunda a menos profunda para eliminar correctamente)
        all_folders = []
        for root, dirs, files in os.walk(path):
            if root != path:  # No incluir la carpeta principal
                all_folders.append(root)
        
        # Ordenar de más profunda a menos profunda
        all_folders.sort(key=lambda x: x.count(os.sep), reverse=True)
        
        # Mover archivos de música a la carpeta principal
        for folder in all_folders:
            for file in os.listdir(folder):
                if file.lower().endswith(('.mp3', '.m4a', '.wav', '.flac', '.ogg')):
                    src = os.path.join(folder, file)
                    dst = os.path.join(path, file)
                    
                    # Si ya existe un archivo con el mismo nombre, agregar sufijo
                    if os.path.exists(dst):
                        base, ext = os.path.splitext(file)
                        counter = 1
                        while os.path.exists(dst):
                            dst = os.path.join(path, f"{base} ({counter}){ext}")
                            counter += 1
                    
                    try:
                        os.rename(src, dst)
                        moved_count += 1
                    except Exception as e:
                        print(f"Error moviendo {src}: {e}")
                        skipped_count += 1
        
        # Eliminar carpetas vacías (de más profunda a menos profunda)
        for folder in all_folders:
            try:
                # Verificar si la carpeta está vacía o solo tiene archivos ocultos/sistema
                remaining = os.listdir(folder)
                # Filtrar archivos del sistema como Thumbs.db, .DS_Store
                remaining = [f for f in remaining if not f.startswith('.') and f.lower() != 'thumbs.db' and f.lower() != 'desktop.ini']
                
                if not remaining:
                    # Eliminar archivos del sistema primero
                    for f in os.listdir(folder):
                        try:
                            os.remove(os.path.join(folder, f))
                        except:
                            pass
                    os.rmdir(folder)
                    deleted_folders += 1
            except Exception as e:
                print(f"No se pudo eliminar {folder}: {e}")
        
        # Mostrar resultado
        message = f"✅ Se movieron {moved_count} canciones a la carpeta principal."
        if skipped_count > 0:
            message += f"\n⚠️ {skipped_count} archivos no se pudieron mover."
        if deleted_folders > 0:
            message += f"\n🗑️ Se eliminaron {deleted_folders} carpetas vacías."
        
        QMessageBox.information(self, "Desorganización completada", message)

    def renumber_songs(self):
        """Renumerar canciones en una carpeta, agrupando por artista"""
        path = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta a renumerar", self.save_path)
        if not path:
            return
        
        # Obtener archivos de música
        music_files = []
        for file in os.listdir(path):
            if file.lower().endswith(('.mp3', '.m4a', '.wav', '.flac', '.ogg')):
                music_files.append(file)
        
        if not music_files:
            QMessageBox.warning(self, "Sin archivos", "No se encontraron archivos de música en la carpeta.")
            return
        
        # Agrupar por artista
        artists_files = defaultdict(list)
        
        for file in music_files:
            # Quitar numeración existente para detectar artista
            clean_name = re.sub(r'^\d+\s*[-_.]?\s*', '', file)
            
            # Extraer artista del nombre del archivo
            artist = extract_artist_from_filename(clean_name)
            
            if not artist:
                # Si no se detecta artista, intentar extraer del formato "Artista - Canción"
                if " - " in clean_name:
                    potential_artist = clean_name.split(" - ")[0].strip()
                    if potential_artist and len(potential_artist) > 2:
                        artist = potential_artist
                    else:
                        artist = "_Sin Artista"
                else:
                    artist = "_Sin Artista"
            
            artists_files[artist].append(file)
        
        # Agrupar artistas similares
        grouped_artists = group_similar_artists(
            {artist: [{'name': f, 'path': os.path.join(path, f)} for f in files] 
             for artist, files in artists_files.items()}
        )
        
        renamed_count = 0
        
        # Ordenar artistas alfabéticamente y renumerar cada grupo
        for canonical_artist in sorted(grouped_artists.keys()):
            songs = grouped_artists[canonical_artist]
            
            # Ordenar canciones de este artista alfabéticamente
            songs_sorted = sorted(songs, key=lambda x: x['name'].lower())
            
            # Renumerar canciones de este artista
            for i, song in enumerate(songs_sorted, start=1):
                src = song['path']
                original_name = song['name']
                
                if not os.path.exists(src):
                    continue
                
                # Quitar numeración existente
                clean_name = re.sub(r'^\d+\s*[-_.]?\s*', '', original_name)
                
                # Nuevo nombre con numeración
                new_name = f"{i:03d} - {clean_name}"
                dst = os.path.join(path, new_name)
                
                # Si ya existe un archivo con ese nombre (y no es el mismo), agregar sufijo
                if os.path.exists(dst) and src != dst:
                    base, ext = os.path.splitext(new_name)
                    counter = 1
                    while os.path.exists(dst):
                        new_name = f"{base} ({counter}){ext}"
                        dst = os.path.join(path, new_name)
                        counter += 1
                
                if src != dst:
                    try:
                        os.rename(src, dst)
                        renamed_count += 1
                    except Exception as e:
                        print(f"Error renombrando {src}: {e}")
        
        # Mensaje de resultado
        artist_count = len(grouped_artists)
        message = f"✅ Se renumeraron {renamed_count} canciones."
        message += f"\n\n📊 {artist_count} artistas detectados."
        message += f"\n\n💡 Cada artista tiene su propia numeración empezando en 001."
        
        QMessageBox.information(self, "Renumeración completada", message)

    def sanitize_filename(self, name):
        return re.sub(r'[<>:"/\\|?*]', '', name)

    def resizeEvent(self, event):
        """Reposicionar indicador de carga al redimensionar"""
        super().resizeEvent(event)
        self.loading_indicator.move(self.width() // 2 - 40, self.height() // 2 - 40)


class CustomItemDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        # Cambiar el color de fondo del elemento
        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, QColor("#e94560"))
        elif option.state & QStyle.State_MouseOver:
            painter.fillRect(option.rect, QColor("#0f3460"))
        else:
            painter.fillRect(option.rect, QColor("#1a1a2e"))

        super().paint(painter, option, index)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = YouTubeDownloader()
    window.showMaximized()
    sys.exit(app.exec_())
