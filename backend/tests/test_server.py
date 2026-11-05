from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
import uvicorn
import uuid
from datetime import datetime

app = FastAPI(
    title="Whicoustic Test API",
    description="Test API with security report endpoint",
    version="1.0.0",
    docs_url="/docs",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for testing
reports_db = []


class SecurityReportCreate(BaseModel):
    """Request model for creating security reports"""
    type: str  # 'security', 'fraud', 'unauthorized', 'data', 'other'
    severity: str  # 'low', 'medium', 'high', 'critical'
    description: str
    email: Optional[EmailStr] = None
    anonymous: bool = False
    
    @field_validator('description')
    @classmethod
    def description_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Description cannot be empty')
        if len(v.strip()) < 10:
            raise ValueError('Description must be at least 10 characters long')
        return v.strip()


class SecurityReportResponse(BaseModel):
    """Response model for security report operations"""
    id: str
    message: str
    status: str
    created_at: datetime


@app.get("/")
async def root():
    return {"message": "Whicoustic Test API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "environment": "development", "version": "1.0.0"}


@app.post("/api/security/report", response_model=SecurityReportResponse)
async def submit_security_report(
    report_data: SecurityReportCreate,
    request: Request
):
    """Submit a new security report"""
    try:
        # Generate unique ID for the report
        report_id = str(uuid.uuid4())
        
        # Extract request information
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent", "")
        
        # Create the security report (store in memory for testing)
        security_report = {
            "id": report_id,
            "type": report_data.type,
            "severity": report_data.severity,
            "description": report_data.description,
            "contact_email": report_data.email if not report_data.anonymous else None,
            "is_anonymous": report_data.anonymous,
            "ip_address": client_ip,
            "user_agent": user_agent,
            "status": "submitted",
            "created_at": datetime.now()
        }
        
        # Store in memory
        reports_db.append(security_report)
        
        print(f"Security report submitted: {report_id}")
        print(f"Type: {report_data.type}, Severity: {report_data.severity}")
        print(f"Description: {report_data.description}")
        print(f"Anonymous: {report_data.anonymous}, Email: {report_data.email}")
        print("---")
        
        return SecurityReportResponse(
            id=report_id,
            message="Security report submitted successfully. Thank you for helping us improve security.",
            status="submitted",
            created_at=security_report["created_at"]
        )
        
    except Exception as e:
        print(f"Error submitting security report: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to submit security report. Please try again or contact support directly."
        )


@app.get("/api/security/reports")
async def list_security_reports():
    """List all submitted security reports (for testing)"""
    return {
        "reports": reports_db,
        "total": len(reports_db)
    }


if __name__ == "__main__":
    uvicorn.run(
        "test_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )