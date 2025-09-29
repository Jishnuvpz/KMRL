"""
Simplified Demo Main for KMRL Document Intelligence Platform
"""
from fastapi import FastAPI, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import json
import os
from datetime import datetime

app = FastAPI(
    title="KMRL Document Intelligence API - Demo",
    description="Simplified demo version of the Document Management System",
    version="2.0.0-demo",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS setup
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock data models
class User(BaseModel):
    username: str
    role: str
    department: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: User

class Document(BaseModel):
    id: int
    sender: str
    subject: str
    body: str
    date: str
    departments: List[str]
    language: str
    critical: bool
    priority: str
    docType: str
    source: str
    summary: dict
    roleSpecificSummaries: Optional[dict] = None
    sharedWith: Optional[List[str]] = None
    attachmentFilename: Optional[str] = None
    dueDate: Optional[str] = None

# Mock database
mock_users = {
    "admin@kmrl.co.in": {"password": "password123", "role": "Admin", "department": "All"},
    "director.ops@kmrl.co.in": {"password": "password123", "role": "Director", "department": "Operations"},
    "manager.fin@kmrl.co.in": {"password": "password123", "role": "Manager", "department": "Finance"},
    "staff.safety@kmrl.co.in": {"password": "password123", "role": "Staff", "department": "Safety"},
}

mock_documents = [
    {
        "id": 1,
        "sender": "railcorp@example.com",
        "subject": "Urgent: Track Maintenance Schedule Q3",
        "body": "Please review the attached track maintenance schedule for Q3. All departments must confirm their resource availability by EOD Friday.",
        "date": "2024-07-20",
        "departments": ["Operations"],
        "language": "English",
        "critical": True,
        "priority": "High",
        "docType": "Schedule",
        "source": "Email",
        "summary": {"en": "Q3 track maintenance requires departmental resource confirmation by Friday.", "ml": "ക്യു 3-ലെ ട്രാക്ക് അറ്റകുറ്റപ്പണി വെള്ളിയാഴ്ചയ്ക്കകം സ്ഥിരീകരിക്കണം."},
        "roleSpecificSummaries": {
            "Staff": "Confirm your team's availability for Q3 track maintenance by Friday.",
            "Manager": "Review Q3 maintenance schedule and confirm departmental resources by Friday.",
            "Director": "Critical Q3 track maintenance requires cross-departmental resource confirmation."
        },
        "attachmentFilename": "Q3_Maintenance_Schedule.pdf",
        "dueDate": "2024-07-26"
    },
    {
        "id": 2,
        "sender": "hr@kmrl.co.in",
        "subject": "New Employee Onboarding Policy",
        "body": "The updated employee onboarding policy is now effective. All managers are requested to familiarize themselves with the new procedures.",
        "date": "2024-07-19",
        "departments": ["HR"],
        "language": "English",
        "critical": False,
        "priority": "Medium",
        "docType": "Policy",
        "source": "SharePoint",
        "summary": {"en": "New employee onboarding policy is effective, managers need training.", "ml": "പുതിയ ജീവനക്കാർക്കുള്ള നയം നിലവിൽ വന്നു, മാനേജർമാർ പരിശീലനം ആവശ്യം."},
        "roleSpecificSummaries": {
            "Staff": "Be aware of new onboarding policy for team members.",
            "Manager": "Familiarize with new onboarding procedures and attend training.",
            "Director": "New onboarding policy implemented to standardize new hire integration."
        },
        "attachmentFilename": "Onboarding_Policy_v2.docx",
        "dueDate": "2024-07-31"
    }
]

# Routes
@app.get("/")
async def root():
    return {
        "success": True,
        "data": {
            "system": "KMRL Document Intelligence API - Demo",
            "version": "2.0.0-demo",
            "status": "operational",
            "message": "Demo version running successfully!"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "success": True,
        "data": {
            "status": "healthy",
            "version": "2.0.0-demo",
            "timestamp": datetime.now().isoformat()
        }
    }

@app.post("/api/auth/login")
async def login(username: str = Form(), password: str = Form()):
    if username not in mock_users:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    user_data = mock_users[username]
    if user_data["password"] != password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    return {
        "success": True,
        "data": {
            "access_token": f"demo-token-{username}",
            "token_type": "bearer",
            "user": {
                "username": username,
                "role": user_data["role"],
                "department": user_data["department"]
            }
        }
    }

@app.get("/api/documents/")
async def get_documents():
    return {
        "success": True,
        "data": mock_documents
    }

@app.get("/api/documents/{doc_id}")
async def get_document(doc_id: int):
    doc = next((d for d in mock_documents if d["id"] == doc_id), None)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {
        "success": True,
        "data": doc
    }

@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    return {
        "success": True,
        "data": {
            "total_documents": len(mock_documents),
            "critical_documents": len([d for d in mock_documents if d["critical"]]),
            "processing_documents": 0,
            "departments": ["Operations", "HR", "Finance", "Legal", "IT", "Safety"]
        }
    }

@app.post("/api/summarization/summarize")
async def summarize_text(request: dict):
    text = request.get("text", "")
    language = request.get("language", "english")
    
    # Mock summarization
    if language == "english":
        summary = f"Summary: {text[:100]}..." if len(text) > 100 else f"Summary: {text}"
    else:
        summary = f"സംഗ്രഹം: {text[:50]}..." if len(text) > 50 else f"സംഗ്രഹം: {text}"
    
    return {
        "success": True,
        "data": {
            "summary": summary,
            "language": language,
            "confidence": 0.95
        }
    }

@app.get("/api/documents/search")
async def search_documents(q: str):
    filtered = [d for d in mock_documents if q.lower() in d["subject"].lower() or q.lower() in d["body"].lower()]
    return {
        "success": True,
        "data": filtered
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("demo_main:app", host="0.0.0.0", port=8000, reload=True)
