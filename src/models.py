"""
Modelos de datos para la API de Localización
Usa Pydantic para validación automática
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum

class TargetLanguage(str, Enum):
    """Supported target languages"""
    ENGLISH = "en"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"
    ITALIAN = "it"
    PORTUGUESE = "pt"
    JAPANESE = "ja"
    CHINESE = "zh-CN"
    KOREAN = "ko"

# ============================================================================
# TRANSLATION MODELS
# ============================================================================

class TranslateRequest(BaseModel):
    """Request for text translation"""
    text: str = Field(..., min_length=1, max_length=20000, description="English text to translate")
    target_language: TargetLanguage = Field(..., description="Target language code")
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "Hello, welcome to our platform",
                "target_language": "es"
            }
        }

class TranslateResponse(BaseModel):
    """Response for translation"""
    success: bool
    source_text: str
    source_language: str
    translated_text: str
    target_language: str

# ============================================================================
# TEXT-TO-SPEECH MODELS
# ============================================================================

class TTSRequest(BaseModel):
    """Request for text-to-speech with translation"""
    text: str = Field(..., min_length=1, max_length=20000, description="English text to translate and convert to audio")
    target_language: TargetLanguage = Field(..., description="Target language for translation and audio")
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "Welcome to Habl AI, the future of voice localization",
                "target_language": "es"
            }
        }

class TTSResponse(BaseModel):
    """Response for text-to-speech"""
    success: bool
    source_text: str
    source_language: str
    translated_text: str
    target_language: str
    audio_file: str
    audio_url: str
    char_count: int

# ============================================================================
# FILE PROCESSING MODELS
# ============================================================================

class ProcessFileResponse(BaseModel):
    """Response for file processing with TTS"""
    success: bool
    filename: str
    format: str
    source_text: str
    source_language: str
    translated_text: str
    target_language: str
    audio_file: str
    audio_url: str
    char_count: int

# ============================================================================
# LANGUAGE MODELS
# ============================================================================

class LanguagesResponse(BaseModel):
    """Response with supported languages"""
    source_language: str
    source_language_name: str
    target_languages: dict
    total_languages: int

class HealthResponse(BaseModel):
    """Response for health check"""
    status: str
    version: str
    service: str

class ErrorResponse(BaseModel):
    """Response for errors"""
    success: bool = False
    error: str
    detail: Optional[str] = None

# ============================================================================
# AUTHENTICATION MODELS
# ============================================================================

class SignUpRequest(BaseModel):
    """Request for user registration"""
    email: str = Field(..., description="User email")
    password: str = Field(..., min_length=8, description="User password (min 8 characters)")
    full_name: Optional[str] = Field(None, description="User full name")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "securepassword123",
                "full_name": "John Doe"
            }
        }

class SignInRequest(BaseModel):
    """Request for user login"""
    email: str = Field(..., description="User email")
    password: str = Field(..., description="User password")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "securepassword123"
            }
        }

class AuthResponse(BaseModel):
    """Response for authentication"""
    success: bool
    user: dict
    session: dict
    message: Optional[str] = None

class UserProfileResponse(BaseModel):
    """Response for user profile"""
    id: str
    email: str
    full_name: Optional[str]
    tier: str
    credits_remaining: int
    credits_limit: int
    created_at: str

class HealthResponse(BaseModel):
    """Response for health check"""
    status: str
    version: str
    service: str
    database: Optional[str] = None    