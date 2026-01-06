"""
API REST para el sistema de Localización con IA
Servidor FastAPI con endpoints para traducción y TTS
"""
from fastapi import FastAPI, HTTPException, status, UploadFile, File, Depends, Request
from file_processor import FileProcessor

from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import Optional
import uvicorn
from pathlib import Path
import os
import logging
from datetime import datetime

from hablai_core import LocalizationAI
from file_processor import FileProcessor
from auth import AuthService, get_current_active_user 

from models import (
    TranslateRequest, TranslateResponse,
    TTSRequest, TTSResponse,
    ProcessFileResponse,
    LanguagesResponse, HealthResponse, ErrorResponse,
    SignUpRequest, SignInRequest, AuthResponse, UserProfileResponse
)
from config import Config
from auth import AuthService, get_current_active_user, supabase

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Inicializar FastAPI
app = FastAPI(
    title=Config.API_TITLE,
    version=Config.API_VERSION,
    description=Config.API_DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app = FastAPI(
    title=Config.API_TITLE,
    version=Config.API_VERSION,
    description=Config.API_DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Montar carpeta de archivos estáticos (audios)
app.mount("/audio", StaticFiles(directory=str(Config.OUTPUT_AUDIO_DIR)), name="audio")

# Inicializar sistema de localización
ai = LocalizationAI()

# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/", tags=["Root"])
async def root():
    """Endpoint raíz - Información básica de la API"""
    return {
        "service": Config.API_TITLE,
        "version": Config.API_VERSION,
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }
# ============================================================================
# HEALTH
# ============================================================================    

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check - Verificar que el servicio está funcionando"""
    try:
        # Check database connection
        supabase.table("user_profiles").select("id").limit(1).execute()
        db_status = "connected"
    except:
        db_status = "disconnected"
    
    return HealthResponse(
        status="healthy" if db_status == "connected" else "degraded",
        version=Config.API_VERSION,
        service=Config.API_TITLE,
        database=db_status
    )

# ============================================================================
# AUTH
# ============================================================================

@app.post("/auth/signup", response_model=AuthResponse, tags=["Authentication"])
async def sign_up(request: SignUpRequest):
    """
    Register a new user
    
    - **email**: User email
    - **password**: Password (minimum 8 characters)
    - **full_name**: Optional full name
    
    Returns user data and session tokens
    """
    return await AuthService.sign_up(
        email=request.email,
        password=request.password,
        full_name=request.full_name
    )

@app.post("/auth/signin", response_model=AuthResponse, tags=["Authentication"])
async def sign_in(request: SignInRequest):
    """
    Login user
    
    - **email**: User email
    - **password**: User password
    
    Returns session tokens for authenticated requests
    """
    return await AuthService.sign_in(
        email=request.email,
        password=request.password
    )

@app.get("/auth/me", response_model=UserProfileResponse, tags=["Authentication"])
async def get_my_profile(current_user: dict = Depends(get_current_active_user)):
    """
    Get current user profile
    
    Requires authentication (Bearer token in Authorization header)
    """
    profile = await AuthService.get_user_profile(current_user["id"])
    
    if not profile:
        raise HTTPException(
            status_code=404,
            detail="User profile not found"
        )
    
    return UserProfileResponse(
        id=profile["id"],
        email=profile["email"],
        full_name=profile.get("full_name"),
        tier=profile["tier"],
        credits_remaining=profile["credits_remaining"],
        credits_limit=profile["credits_limit"],
        created_at=profile["created_at"]
    )
# ============================================================================
# LANGUAGES
# ============================================================================    

@app.get("/languages", response_model=LanguagesResponse, tags=["Languages"])
async def get_languages():
    """Obtener lista de idiomas soportados"""
    return LanguagesResponse(
        source_language=Config.SOURCE_LANGUAGE,
        source_language_name=Config.SOURCE_LANGUAGE_NAME,
        target_languages=Config.TARGET_LANGUAGES,
        total_languages=len(Config.TARGET_LANGUAGES)
    )
# ============================================================================
# TRANSLATE
# ============================================================================    

@app.post("/translate", response_model=TranslateResponse, tags=["Translation"])
@limiter.limit("30/minute")
async def translate_text(
    request: Request,
    data: TranslateRequest,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Translate text from English-US to a specific language
    
    **Authentication required** - Include Bearer token in Authorization header
    **Cost:** 1 credit
    
    - **text**: English text to translate
    - **target_language**: Target language code (es, fr, de, etc.)
    """
    try:
        # Check and deduct credits
        has_credits = await AuthService.check_and_deduct_credits(
            current_user["id"], 
            credits_needed=1
        )
        
        if not has_credits:
            raise HTTPException(
                status_code=402,
                detail=f"Insufficient credits. You have {current_user['credits_remaining']} credits remaining. Upgrade your plan to continue."
            )
        
        # Translate
        translated = ai.translate_text(data.text, data.target_language.value)
        
        if "Error" in str(translated):
            await AuthService.log_usage(
                user_id=current_user["id"],
                action_type="translate",
                char_count=len(data.text),
                target_languages=[data.target_language.value],
                success=False,
                error_message=translated
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=translated
            )
        
        # Log successful usage
        await AuthService.log_usage(
            user_id=current_user["id"],
            action_type="translate",
            char_count=len(data.text),
            target_languages=[data.target_language.value],
            success=True
        )
        
        return TranslateResponse(
            success=True,
            source_text=data.text,
            source_language=Config.SOURCE_LANGUAGE,
            translated_text=translated,
            target_language=data.target_language.value
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Translation error: {str(e)}"
        )
# ============================================================================
# TEXT TO SPEECH
# ============================================================================    
@app.post("/tts", response_model=TTSResponse, tags=["Text-to-Speech"])
@limiter.limit("20/minute")
async def text_to_speech(
    request: Request,
    data: TTSRequest,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Translate text and generate audio (TTS)
    
    **Authentication required**
    **Cost:** 1 credit
    
    - **text**: English text to translate and convert to audio
    - **target_language**: Target language code
    
    Returns translated text and downloadable MP3 audio
    """
    try:
        # Check and deduct credits
        has_credits = await AuthService.check_and_deduct_credits(
            current_user["id"], 
            credits_needed=1
        )
        
        if not has_credits:
            raise HTTPException(
                status_code=402,
                detail=f"Insufficient credits. You have {current_user['credits_remaining']} credits remaining."
            )
        
        # Translate text
        translated = ai.translate_text(data.text, data.target_language.value)
        
        if "Error" in str(translated):
            await AuthService.log_usage(
                user_id=current_user["id"],
                action_type="tts",
                char_count=len(data.text),
                target_languages=[data.target_language.value],
                success=False,
                error_message=translated
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=translated
            )
        
        # Generate audio
        audio_file = ai.text_to_speech(translated, data.target_language.value)
        
        if "Error" in str(audio_file):
            await AuthService.log_usage(
                user_id=current_user["id"],
                action_type="tts",
                char_count=len(data.text),
                target_languages=[data.target_language.value],
                success=False,
                error_message=audio_file
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=audio_file
            )
        
        # Get audio filename and URL
        audio_filename = os.path.basename(audio_file)
        audio_url = f"/audio/{audio_filename}"
        
        # Save to database
        try:
            translation = supabase.table("translations").insert({
                "user_id": current_user["id"],
                "source_text": data.text,
                "translated_text": translated,
                "source_language": Config.SOURCE_LANGUAGE,
                "target_language": data.target_language.value,
                "char_count": len(data.text)
            }).execute()
            
            supabase.table("localizations").insert({
                "user_id": current_user["id"],
                "translation_id": translation.data[0]['id'],
                "audio_file_path": audio_file,
                "audio_url": audio_url
            }).execute()
        except Exception as db_error:
            print(f"Database error: {str(db_error)}")
        
        # Log usage
        await AuthService.log_usage(
            user_id=current_user["id"],
            action_type="tts",
            char_count=len(data.text),
            target_languages=[data.target_language.value],
            success=True
        )
        
        return TTSResponse(
            success=True,
            source_text=data.text,
            source_language=Config.SOURCE_LANGUAGE,
            translated_text=translated,
            target_language=data.target_language.value,
            audio_file=audio_filename,
            audio_url=audio_url,
            char_count=len(data.text)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"TTS error: {str(e)}"
        )
# ============================================================================
# FILE PROCESSING
# ============================================================================

@app.post("/process-file", response_model=ProcessFileResponse, tags=["File Processing"])
@limiter.limit("10/minute")
async def process_file(
    request: Request,
    file: UploadFile = File(...),
    target_language: str = "es",
    current_user: dict = Depends(get_current_active_user)
):
    """
    Process file: Extract text → Translate → Generate audio
    
    **Authentication required**
    **Cost:** 1 credit
    
    **Supported formats:** TXT, PDF, DOCX, JSON, CSV, XLSX
    
    - **file**: File to process
    - **target_language**: Target language code (default: es)
    
    Returns translated text and downloadable MP3 audio
    """
    try:
        # Validate target language
        if target_language not in Config.TARGET_LANGUAGES:
            raise HTTPException(
                status_code=400,
                detail=f"Language '{target_language}' not supported. Supported: {list(Config.TARGET_LANGUAGES.keys())}"
            )
        
        # Check and deduct credits
        has_credits = await AuthService.check_and_deduct_credits(
            current_user["id"], 
            credits_needed=1
        )
        
        if not has_credits:
            raise HTTPException(
                status_code=402,
                detail=f"Insufficient credits. You have {current_user['credits_remaining']} credits remaining."
            )
        
        # Read file content
        content = await file.read()
        
        # Process file to extract text
        file_result = await FileProcessor.process_file(content, file.filename)
        
        if not file_result['success']:
            await AuthService.log_usage(
                user_id=current_user["id"],
                action_type="process_file",
                char_count=0,
                target_languages=[target_language],
                success=False,
                error_message=file_result.get('error', 'Unknown error')
            )
            raise HTTPException(
                status_code=400,
                detail=file_result.get('error', 'Error processing file')
            )
        
        text = file_result['text']
        
        # Validate text length
        if len(text) > Config.MAX_TEXT_LENGTH:
            raise HTTPException(
                status_code=400,
                detail=f"Text too long. Maximum: {Config.MAX_TEXT_LENGTH} characters. Found: {len(text)}"
            )
        
        if len(text) < 1:
            raise HTTPException(
                status_code=400,
                detail="No text found in file"
            )
        
        # Translate
        translated = ai.translate_text(text, target_language)
        
        if "Error" in str(translated):
            await AuthService.log_usage(
                user_id=current_user["id"],
                action_type="process_file",
                char_count=len(text),
                target_languages=[target_language],
                success=False,
                error_message=translated
            )
            raise HTTPException(
                status_code=500,
                detail=f"Translation error: {translated}"
            )
        
        # Generate audio
        audio_file = ai.text_to_speech(translated, target_language)
        
        if "Error" in str(audio_file):
            await AuthService.log_usage(
                user_id=current_user["id"],
                action_type="process_file",
                char_count=len(text),
                target_languages=[target_language],
                success=False,
                error_message=audio_file
            )
            raise HTTPException(
                status_code=500,
                detail=f"TTS error: {audio_file}"
            )
        
        # Get audio filename and URL
        audio_filename = os.path.basename(audio_file)
        audio_url = f"/audio/{audio_filename}"
        
        # Save to database
        try:
            translation = supabase.table("translations").insert({
                "user_id": current_user["id"],
                "source_text": text,
                "translated_text": translated,
                "source_language": Config.SOURCE_LANGUAGE,
                "target_language": target_language,
                "char_count": len(text),
                "file_name": file.filename,
                "file_format": file_result['format']
            }).execute()
            
            supabase.table("localizations").insert({
                "user_id": current_user["id"],
                "translation_id": translation.data[0]['id'],
                "audio_file_path": audio_file,
                "audio_url": audio_url
            }).execute()
        except Exception as db_error:
            print(f"Database error: {str(db_error)}")
        
        # Log usage
        await AuthService.log_usage(
            user_id=current_user["id"],
            action_type="process_file",
            char_count=len(text),
            target_languages=[target_language],
            success=True
        )
        
        return ProcessFileResponse(
            success=True,
            filename=file.filename,
            format=file_result['format'],
            source_text=text[:500] + "..." if len(text) > 500 else text,
            source_language=Config.SOURCE_LANGUAGE,
            translated_text=translated[:500] + "..." if len(translated) > 500 else translated,
            target_language=target_language,
            audio_file=audio_filename,
            audio_url=audio_url,
            char_count=len(text)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing file: {str(e)}"
        )
    
# ============================================================================
# EXCEPTION HANDLERS
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Manejador personalizado de excepciones HTTP"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Manejador de excepciones generales"""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "Internal server error",
            "detail": str(exc)
        }
    )

# ============================================================================
# STARTUP EVENT
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Evento ejecutado al iniciar el servidor"""
    logger.info("="*60)
    logger.info(f"🚀 {Config.API_TITLE} v{Config.API_VERSION}")
    logger.info("="*60)
    logger.info(f"📝 Documentation: http://{Config.HOST}:{Config.PORT}/docs")
    logger.info(f"🔍 ReDoc: http://{Config.HOST}:{Config.PORT}/redoc")
    logger.info(f"💚 Health: http://{Config.HOST}:{Config.PORT}/health")
    logger.info(f"🌐 Supported languages: {len(Config.TARGET_LANGUAGES)}")
    logger.info(f"🔐 CORS Origins: {Config.CORS_ORIGINS}")
    logger.info("="*60)

# ============================================================================
# MAIN - Ejecutar servidor
# ============================================================================

if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", Config.PORT))
    
    uvicorn.run(
        "api:app",
        host=Config.HOST,
        port=port,
        reload=False,  # Cambiado a False para producción
        log_level="info"
    )