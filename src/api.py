"""
API REST para el sistema de Localización con IA
Servidor FastAPI con endpoints para traducción y TTS
"""

from fastapi import FastAPI, HTTPException, status, UploadFile, File, Depends, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from typing import Optional
import uvicorn
import os
import logging

# Imports internos CORRECTOS
from src.file_processor import FileProcessor
from src.hablai_core import LocalizationAI
from src.auth import AuthService, get_current_active_user, supabase
from src.models import (
    TranslateRequest, TranslateResponse,
    TTSRequest, TTSResponse,
    ProcessFileResponse,
    LanguagesResponse, HealthResponse,
    SignUpRequest, SignInRequest,
    AuthResponse, UserProfileResponse
)
from src.config import Config

# Rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded


# ============================================================================
# FASTAPI INIT (UNA SOLA VEZ)
# ============================================================================

app = FastAPI(
    title=Config.API_TITLE,
    version=Config.API_VERSION,
    description=Config.API_DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# ============================================================================
# MIDDLEWARES
# ============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# ============================================================================
# LOGGING
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)

logger = logging.getLogger(__name__)


# ============================================================================
# STATIC FILES
# ============================================================================

app.mount(
    "/audio",
    StaticFiles(directory=str(Config.OUTPUT_AUDIO_DIR)),
    name="audio"
)


# ============================================================================
# AI CORE INIT
# ============================================================================

ai = LocalizationAI()


# ============================================================================
# ROOT
# ============================================================================

@app.get("/", tags=["Root"])
async def root():

    return {
        "service": Config.API_TITLE,
        "version": Config.API_VERSION,
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }


# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():

    try:

        supabase.table("user_profiles").select("id").limit(1).execute()
        db_status = "connected"

    except Exception:

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

    return await AuthService.sign_up(
        email=request.email,
        password=request.password,
        full_name=request.full_name
    )


@app.post("/auth/signin", response_model=AuthResponse, tags=["Authentication"])
async def sign_in(request: SignInRequest):

    return await AuthService.sign_in(
        email=request.email,
        password=request.password
    )


@app.get("/auth/me", response_model=UserProfileResponse, tags=["Authentication"])
async def get_profile(
    current_user: dict = Depends(get_current_active_user)
):

    profile = await AuthService.get_user_profile(current_user["id"])

    if not profile:

        raise HTTPException(
            status_code=404,
            detail="User profile not found"
        )

    return UserProfileResponse(**profile)


# ============================================================================
# LANGUAGES
# ============================================================================

@app.get("/languages", response_model=LanguagesResponse, tags=["Languages"])
async def get_languages():

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
async def translate(
    request: Request,
    data: TranslateRequest,
    current_user: dict = Depends(get_current_active_user)
):

    try:

        has_credits = await AuthService.check_and_deduct_credits(
            current_user["id"],
            credits_needed=1
        )

        if not has_credits:

            raise HTTPException(
                status_code=402,
                detail="Insufficient credits"
            )

        translated = ai.translate_text(
            data.text,
            data.target_language.value
        )

        return TranslateResponse(
            success=True,
            source_text=data.text,
            source_language=Config.SOURCE_LANGUAGE,
            translated_text=translated,
            target_language=data.target_language.value
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
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

    content = await file.read()

    file_result = await FileProcessor.process_file(
        content,
        file.filename
    )

    if not file_result["success"]:

        raise HTTPException(
            status_code=400,
            detail=file_result["error"]
        )

    translated = ai.translate_text(
        file_result["text"],
        target_language
    )

    audio_file = ai.text_to_speech(
        translated,
        target_language
    )

    return ProcessFileResponse(
        success=True,
        filename=file.filename,
        format=file_result["format"],
        source_text=file_result["text"],
        translated_text=translated,
        audio_file=os.path.basename(audio_file),
        audio_url=f"/audio/{os.path.basename(audio_file)}",
        char_count=len(file_result["text"]),
        source_language=Config.SOURCE_LANGUAGE,
        target_language=target_language
    )


# ============================================================================
# EXCEPTION HANDLERS
# ============================================================================

@app.exception_handler(HTTPException)
async def http_handler(request, exc):

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail
        }
    )


@app.exception_handler(Exception)
async def general_handler(request, exc):

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": str(exc)
        }
    )


# ============================================================================
# STARTUP EVENT
# ============================================================================

@app.on_event("startup")
async def startup():

    logger.info(f"{Config.API_TITLE} started")


# ============================================================================
# MAIN ENTRYPOINT
# ============================================================================

if __name__ == "__main__":

    port = int(os.getenv("PORT", Config.PORT))

    uvicorn.run(
        "src.api:app",
        host="0.0.0.0",
        port=port,
        reload=False
    )