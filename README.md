# Localization AI - SaaS Platform

AI-powered localization platform that translates content from English to 8 languages and generates natural-sounding audio using text-to-speech technology.

## Features

- **Automatic Translation** - Translate from English to 8 languages
- **Text-to-Speech** - Generate natural audio in multiple languages
- **Multi-Format Support** - Process TXT, PDF, DOCX, JSON, CSV, XLSX files
- **REST API** - Full-featured API with authentication
- **Subscription Tiers** - Free, Pro & Enterprise plans
- **Usage Analytics** - Track your translations and credits

## Supported Languages

- English (For audio generation/tests only)
- Spanish (es)
- French (fr)
- German (de)
- Italian (it)
- Portuguese (pt)
- Japanese (ja)
- Traditional Chinese (zh-CN)
- Korean (ko)

## Tech Stack

- **Backend:** FastAPI (Python)
- **Database:** Supabase (PostgreSQL)
- **Auth:** Supabase Auth
- **Storage:** Supabase Storage
- **Translation:** Google Translate API
- **TTS:** Google Text-to-Speech
- **Deployment:** Railway

## Quick Start

### Prerequisites

- Python 3.11+
- pip
- ffmpeg (for audio processing)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/localization-ai-saas.git
cd localization-ai-saas
```

2. Create virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file:
```bash
cp .env.example .env
```

5. Configure environment variables in `.env`:
```env
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
SUPABASE_SERVICE_KEY=your_service_key
JWT_SECRET=your_jwt_secret
```

6. Run the server:
```bash
cd src
python3 api.py
```

7. Open API documentation:
```
http://localhost:8000/docs
```

## Project Structure
```
localization-ai-saas/
├── src/
│   ├── api.py                 # FastAPI main application
│   ├── localization_ai.py     # Core localization logic
│   ├── file_processor.py      # File parsing logic
│   ├── models.py              # Pydantic models
│   ├── config.py              # Configuration
│   └── auth.py                # Authentication (coming soon)
├── output_audio/              # Generated audio files
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variables template
├── .gitignore
└── README.md
```

## API Endpoints

### Public Endpoints
- `GET /` - API information
- `GET /health` - Health check
- `GET /languages` - List supported languages

### Translation
- `POST /translate` - Translate to one language
- `POST /translate-all` - Translate to all languages

### Localization (Translation + Audio)
- `POST /localize` - Localize to one language
- `POST /localize-all` - Localize to all languages

### File Processing
- `POST /process-file` - Extract text from file
- `POST /translate-file` - Translate file content
- `POST /localize-file` - Localize file content

### Audio
- `GET /audio/{filename}` - Download generated audio

## Authentication (Coming Soon)

- User registration and login
- JWT-based authentication
- API key management
- Credit-based usage limits

## Pricing Tiers (Pricing charts Coming soon)

- **Free:** 3 translations/month, 5K chars, 2 languages
- **Pro:** 50 translations/month, 20K chars, all languages
- **Business:** 250 translations/month, 50K chars, priority processing


## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see LICENSE file for details

## Contact

For questions or support, contact: ramireztradukisto@gmail.com

## Acknowledgments

- Google Translate API
- Google Text-to-Speech
- FastAPI Framework
- Supabase