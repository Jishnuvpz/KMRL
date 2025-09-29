# KMRL Document Intelligence Platform

A comprehensive document management system with AI-powered OCR, summarization, and real-time collaboration features.

## 🏗️ Architecture

- **Frontend**: React + TypeScript + Vite
- **Backend**: FastAPI + Python
- **Database**: SQLite (development) / PostgreSQL (production)
- **AI Services**: Google Gemini, Tesseract OCR
- **Storage**: AWS S3 (optional)
- **Authentication**: JWT-based

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ and npm
- Python 3.8+
- Git

### 1. Setup (One-time)
```bash
# Run the setup script
setup.bat
```

### 2. Configure Environment Variables

**Backend (.env)**:
```env
DATABASE_URL=sqlite:///./faiss_app.db
SECRET_KEY=your-super-secret-key
GEMINI_API_KEY=your-gemini-api-key
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
AWS_REGION=us-east-1
AWS_S3_BUCKET=your-bucket-name
```

**Frontend (.env)**:
```env
VITE_API_BASE_URL=http://localhost:8000
VITE_GEMINI_API_KEY=your-gemini-api-key
```

### 3. Start Development Servers
```bash
# Start both frontend and backend
start-dev.bat
```

## 📋 Manual Setup (Alternative)

### Backend Setup
```bash
cd Backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

### Frontend Setup
```bash
cd Frontend
npm install
npm run dev
```

## 🌐 Access Points

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/api/docs
- **Health Check**: http://localhost:8000/health

## 🔐 Demo Accounts

| Username | Password | Role | Department |
|----------|----------|------|------------|
| admin@kmrl.co.in | password123 | Admin | All |
| director.ops@kmrl.co.in | password123 | Director | Operations |
| manager.fin@kmrl.co.in | password123 | Manager | Finance |
| staff.safety@kmrl.co.in | password123 | Staff | Safety |

## 🎯 Key Features

### Document Processing
- **Multi-language OCR**: Tesseract + Google Vision API
- **AI Summarization**: English (BART) + Malayalam (IndicBART)
- **Format Support**: PDF, Images, Word, Text files
- **Real-time Processing**: Instant analysis and summaries

### User Management
- **Role-based Access**: Staff, Manager, Director, Board Member, Admin
- **Department Filtering**: Operations, HR, Finance, Legal, IT, Safety
- **JWT Authentication**: Secure token-based auth
- **Session Management**: Auto-logout and session validation

### Document Intelligence
- **Semantic Search**: Find documents by content and context
- **Priority Classification**: High, Medium, Low priority detection
- **Due Date Tracking**: Automatic deadline monitoring
- **Language Detection**: Auto-route to appropriate AI models

### Collaboration
- **Document Sharing**: Share with specific users
- **Real-time Updates**: WebSocket-based collaboration
- **Comment System**: Threaded discussions
- **Activity Tracking**: Full audit logs

## 🛠️ Development

### Frontend Development
```bash
cd Frontend
npm run dev          # Start dev server
npm run build        # Build for production
npm run preview      # Preview production build
```

### Backend Development
```bash
cd Backend
python -m uvicorn app.main:app --reload --port 8000
```

### API Testing
- Visit http://localhost:8000/api/docs for Swagger UI
- Use tools like Postman or curl for API testing
- Health check: `curl http://localhost:8000/health`

## 📁 Project Structure

```
KMRL-Platform/
├── Frontend/                 # React + TypeScript
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── hooks/           # Custom hooks
│   │   ├── services/        # API services
│   │   ├── contexts/        # React contexts
│   │   └── main.tsx         # Entry point
│   ├── public/
│   └── package.json
├── Backend/                 # FastAPI + Python
│   ├── app/
│   │   ├── core/           # Core functionality
│   │   ├── routes/         # API endpoints
│   │   ├── models/         # Database models
│   │   ├── services/       # Business logic
│   │   └── main.py         # FastAPI app
│   └── requirements.txt
├── setup.bat               # Setup script
├── start-dev.bat           # Development starter
└── README.md
```

## 🔧 Configuration Options

### Environment Variables

**VITE_API_BASE_URL**: Backend API URL
**GEMINI_API_KEY**: Google Gemini API key for AI features
**DATABASE_URL**: Database connection string
**AWS_***: AWS credentials for S3 storage
**SECRET_KEY**: JWT signing key

## 🧪 Testing

### Frontend Testing
```bash
cd Frontend
npm run test        # Run unit tests
npm run e2e         # Run e2e tests
```

### Backend Testing
```bash
cd Backend
pytest              # Run all tests
pytest -v           # Verbose output
```

## 🚀 Production Deployment

### Build Frontend
```bash
cd Frontend
npm run build
# Serve from Backend/static/ or deploy to CDN
```

### Deploy Backend
```bash
cd Backend
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Commit: `git commit -am 'Add feature'`
5. Push: `git push origin feature-name`
6. Create a Pull Request

## 📝 License

MIT License - see LICENSE file for details

## 📞 Support

For support, email: zodiacmrv@gmail.com

---

**KMRL Document Intelligence Platform** - Empowering decisions with intelligent document processing.
