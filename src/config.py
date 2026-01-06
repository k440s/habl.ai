"""
Configuración centralizada de la API
"""

import os
from pathlib import Path

class Config:
    """Configuración de la aplicación"""
    
    # Información de la API
    API_TITLE = "Habl.AI API"
    API_VERSION = "1.0.0"
    API_DESCRIPTION = """
    AI Localization API
    
    Habl.AI - Voice Your Content in Any Language
    **Main features:**
    - Text-to-Speech with natural voices
    - Drag & Drop your text and download your translated .mp3 file
    - Multi-format support for source files (PDF, DOCX, TXT, JSON, CSV, XLSX)
    
    **Supported languages:**
    - 🇺🇸 English (US)
    - 🇪🇸 Spanish
    - 🇫🇷 Français
    - 🇩🇪 Deutsch
    - 🇮🇹 Italiano
    - 🇵🇹 Português
    - 🇯🇵 日本語
    - 🇨🇳 中文
    - 🇰🇷 한국어

    **Pricing Tiers:**
    - 🆓 Free: 3 credits/month
    - ⭐ Pro: 50 credits/month
    - 💼 Business: 250 credits/month
    - 🏢 Enterprise: Custom limits
    """
    
    # Paths
    BASE_DIR = Path(__file__).resolve().parent.parent
    OUTPUT_AUDIO_DIR = BASE_DIR / "output_audio"
    
    # Idiomas
    SOURCE_LANGUAGE = "en"
    SOURCE_LANGUAGE_NAME = "English (US)"
    
    TARGET_LANGUAGES = {
    'en': 'English (US)',
    'es': 'Spanish',
    'fr': 'French',
    'de': 'German',
    'it': 'Italian',
    'pt': 'Portuguese',
    'ja': 'Japanese',
    'zh-CN': 'Chinese',
    'ko': 'Korean'
        
    }
    
    # Límites
    MAX_TEXT_LENGTH = 20000
    MIN_TEXT_LENGTH = 1
    
    # CORS - Allow frontend origins
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "").split(",") if os.getenv("CORS_ORIGINS") else [
    "http://localhost:3000",
    "http://localhost:8080",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8080",
]
    
    # Server
    HOST = "0.0.0.0"
    PORT = 8000
    
    @classmethod
    def ensure_directories(cls):
        """Crea directorios necesarios si no existen"""
        cls.OUTPUT_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
        print(f"✓ Directorio de audio: {cls.OUTPUT_AUDIO_DIR}")
    
    @classmethod
    def get_audio_url(cls, filename: str, host: str = "localhost", port: int = 8000) -> str:
        """Genera URL para descargar el audio"""
        return f"http://{host}:{port}/audio/{filename}"


# Inicializar directorios al importar
Config.ensure_directories()