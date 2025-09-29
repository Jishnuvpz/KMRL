# 📄 Document Management System API v2.0

> **A comprehensive, AI-powered document processing solution with multi-language OCR and intelligent summarization**

[![FastAPI](https://img.shields.io/badge/FastAPI-2.0-009688.svg)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## 🚀 Overview

The Document Management System API is a powerful, production-ready solution for processing documents with advanced OCR capabilities and AI-powered summarization. Built with FastAPI, it provides real-time document analysis, multi-language support, and seamless cloud integration.

### ✨ Key Features

- **🔍 Multi-Language OCR**: Tesseract (85%+) + Google Vision API (95%+)
- **🤖 AI Summarization**: English (BART/Pegasus) + Malayalam (IndicBART)
- **📧 Email Integration**: Automatic processing of attachments from zodiacmrv@gmail.com
- **☁️ Cloud Storage**: AWS S3 with compression and encryption
- **⚡ Real-time Processing**: Instant document analysis and summaries
- **🔐 Secure Authentication**: JWT-based user management
- **📊 Comprehensive Monitoring**: Health checks and performance metrics

### 🌍 Language Support

| Language | OCR Support | Summarization | Model Used |
|----------|-------------|---------------|------------|
| English | ✅ Tesseract + Google Vision | ✅ 3-4 line summaries | BART/Pegasus |
| Malayalam | ✅ Tesseract + Google Vision | ✅ Native script | IndicBART |
| Auto-detection | ✅ Automatic routing | ✅ Language-specific processing | Combined models |

## 📁 Project Structure

```
Backend/
├── app/
│   ├── core/                  # Core system modules
│   │   ├── exceptions.py      # Custom exception handling
│   │   ├── logging.py         # Professional logging system
│   │   ├── middleware.py      # Security & performance middleware
│   │   └── health.py          # Comprehensive health checks
│   ├── routes/                # API route handlers
│   │   ├── auth.py           # Authentication endpoints
│   │   ├── documents.py      # Document management
│   │   ├── ocr_routes.py     # OCR processing endpoints
│   │   ├── summarization_routes.py  # AI summarization
│   │   ├── email.py          # Email processing
│   │   ├── cloud.py          # Cloud storage operations
│   │   └── raw_data.py       # Raw data management
│   ├── services/             # Business logic services
│   │   ├── tesseract_service.py     # Tesseract OCR
│   │   ├── google_vision_service.py # Google Vision API
│   │   ├── combined_ocr_service.py  # Unified OCR
│   │   ├── english_summarization_service.py    # English AI
│   │   ├── malayalam_summarization_service.py  # Malayalam AI
│   │   ├── combined_summarization_service.py   # Auto-routing
│   │   ├── s3_service.py            # AWS S3 integration
│   │   ├── email_service.py         # Email processing
│   │   └── raw_data_service.py      # Data storage
│   ├── models/               # Data models and schemas
│   ├── utils/                # Utility functions
│   ├── config.py            # Configuration management
│   ├── db.py                # Database setup
│   └── main.py              # FastAPI application
├── tests/                   # Test suites
├── docs/                    # Documentation
├── credentials/             # Service account files
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables
└── README.md               # This file
```

## 🛠️ Installation & Setup

### Prerequisites

- Python 3.8+
- Tesseract OCR
- Git
- Virtual environment tool (venv/conda)

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Backend
```

### 2. Create Virtual Environment

```bash
# Using venv
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate

# Using conda
conda create -n docms python=3.9
conda activate docms
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install System Dependencies

#### Tesseract OCR

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-eng tesseract-ocr-mal
```

**Windows:**
1. Download from [GitHub Releases](https://github.com/UB-Mannheim/tesseract/wiki)
2. Install and add to PATH
3. Install language packs for English and Malayalam

**macOS:**
```bash
brew install tesseract
brew install tesseract-lang  # For additional languages
```

### 5. Configure Environment Variables

Create a `.env` file in the Backend directory:

```env
# Required - Application Settings
SECRET_KEY=your-super-secret-key-minimum-32-characters
ENVIRONMENT=development
DEBUG=true

# Database
DATABASE_URL=sqlite:///./app.db

# CORS Settings
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000

# OCR Settings
TESSERACT_PATH=tesseract
OCR_LANGUAGES=eng,mal

# AWS S3 Storage (Optional but recommended)
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_REGION=us-east-1
AWS_S3_BUCKET_NAME=your-s3-bucket-name
USE_S3_STORAGE=true

# Google Vision API (Optional)
GOOGLE_CLOUD_PROJECT_ID=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json
GOOGLE_VISION_API_ENABLED=true

# Email Settings
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAIL_DATA_SOURCE=zodiacmrv@gmail.com

# AI Models
HUGGINGFACE_API_KEY=your-huggingface-token
ENGLISH_SUMMARIZATION_MODEL=facebook/bart-large-cnn
MALAYALAM_SUMMARIZATION_MODEL=ai4bharat/IndicBART

# Performance
MAX_REQUESTS_PER_MINUTE=100
REQUEST_TIMEOUT=30
LOG_LEVEL=INFO
```

### 6. Initialize Database

```bash
# The database tables will be created automatically on first run
python -c "from app.db import engine, Base; Base.metadata.create_all(bind=engine)"
```

## 🚀 Running the Application

### Development Mode

```bash
# Start the FastAPI development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode

```bash
# Set environment to production
export ENVIRONMENT=production
export DEBUG=false

# Run with Gunicorn (recommended for production)
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## 📖 API Documentation

Once the server is running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

### Core Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | System overview and API information |
| `/health` | GET | Comprehensive health check |
| `/health/quick` | GET | Quick health check for load balancers |
| `/api/ocr/extract` | POST | Extract text from images/documents |
| `/api/summarization/auto` | POST | Auto-detect language and summarize |
| `/api/summarization/english` | POST | English text summarization |
| `/api/summarization/malayalam` | POST | Malayalam text summarization |
| `/api/documents/` | POST | Upload and process documents |
| `/api/email/process` | POST | Process email attachments |

## 🧪 Testing

### Run Test Suite

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run all tests
pytest tests/ -v

# Run specific test categories
pytest tests/test_ocr.py -v
pytest tests/test_summarization.py -v
pytest tests/test_api.py -v

# Run with coverage
pip install pytest-cov
pytest --cov=app tests/
```

## 📊 Monitoring & Health Checks

### Health Check Endpoints

- **`/health`**: Comprehensive system health with detailed service status
- **`/health/quick`**: Fast health check for load balancers
- **`/api/ocr/health`**: OCR services health status
- **`/api/summarization/demo`**: AI model health verification

### Logging

The application uses structured logging with rotation:

```python
# Log files are created in the application directory
app.log           # Main application log
app.log.1         # Rotated logs (up to 5 files)
```

## 🔒 Security Features

### Built-in Security

- **JWT Authentication**: Secure token-based authentication
- **CORS Protection**: Configurable cross-origin resource sharing
- **Rate Limiting**: Configurable request rate limiting
- **Security Headers**: Comprehensive security header middleware
- **Input Validation**: Pydantic-based request validation
- **Error Handling**: Secure error responses without sensitive data

## 🚀 Deployment

### Production Environment Setup

1. **Set Production Environment Variables**:
   ```bash
   export ENVIRONMENT=production
   export DEBUG=false
   export SECRET_KEY="your-production-secret-key"
   ```

2. **Use Production Database**:
   ```bash
   export DATABASE_URL="postgresql://user:pass@host:port/dbname"
   ```

3. **Configure Cloud Services**:
   - Set up AWS S3 bucket with proper IAM permissions
   - Configure Google Cloud Vision API if needed
   - Set up Supabase/MongoDB for data storage

4. **Run with Production Server**:
   ```bash
   gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
   ```

## 🤝 Integration

### Frontend Integration (React/Frontend)

```javascript
// Example API integration
const api = {
  baseURL: 'http://localhost:8000/api',
  
  async summarizeText(text, language = 'auto') {
    const response = await fetch(`${this.baseURL}/summarization/${language}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text })
    });
    return response.json();
  },
  
  async extractText(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${this.baseURL}/ocr/extract`, {
      method: 'POST',
      body: formData
    });
    return response.json();
  }
};
```

## 🐛 Troubleshooting

### Common Issues

**1. Tesseract not found**
```bash
# Install Tesseract and verify installation
tesseract --version
which tesseract  # On Unix systems
```

**2. Google Vision API errors**
```bash
# Verify credentials file exists and is valid
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"
```

**3. AWS S3 connection issues**
```bash
# Test AWS credentials
aws s3 ls s3://your-bucket-name
```

**4. Model download failures**
```bash
# Pre-download models
python -c "from transformers import pipeline; pipeline('summarization', model='facebook/bart-large-cnn')"
```

### Debug Mode

Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
export DEBUG=true
```

### Health Check Debugging

```bash
# Test health endpoint
curl http://localhost:8000/health

# Quick health check
curl http://localhost:8000/health/quick

# Service-specific health
curl http://localhost:8000/api/ocr/health
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📞 Support

- **Email**: zodiacmrv@gmail.com
- **Documentation**: [API Docs](http://localhost:8000/api/docs)
- **Issues**: Create GitHub issue for bugs or feature requests

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Tesseract OCR GitHub](https://github.com/tesseract-ocr/tesseract)
- [Google Cloud Vision API](https://cloud.google.com/vision/docs)
- [Hugging Face Transformers](https://huggingface.co/docs/transformers)
- [AWS S3 Documentation](https://docs.aws.amazon.com/s3/)

---

**Built with using FastAPI, AI, and modern cloud technologies**