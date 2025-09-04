from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
import base64

app = FastAPI()

# Allow CORS for all origins (adjust to your frontend domain)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for demo
reports = []
id_counter = 1

# Pydantic model for response schema
class Report(BaseModel):
    id: int
    title: str
    category: str
    priority: str
    location: str
    description: str
    photo: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime

# Endpoint to submit new report
@app.post("/api/report", response_model=Report)
async def create_report(
    title: str = Form(...),
    category: str = Form(...),
    priority: str = Form(...),
    location: str = Form(...),
    description: str = Form(...),
    photo: Optional[UploadFile] = File(None),
):
    global id_counter
    
    photo_base64 = None
    if photo:
        contents = await photo.read()
        photo_base64 = base64.b64encode(contents).decode('utf-8')
    
    new_report = {
        "id": id_counter,
        "title": title,
        "category": category,
        "priority": priority,
        "location": location,
        "description": description,
        "photo": photo_base64,
        "status": "Submitted",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    reports.append(new_report)
    id_counter += 1
    
    return new_report

# Endpoint to get all reports, filterable by status and category
@app.get("/api/reports", response_model=List[Report])
def get_reports(status: Optional[str] = None, category: Optional[str] = None):
    filtered = reports
    if status:
        filtered = [r for r in filtered if r["status"] == status]
    if category:
        filtered = [r for r in filtered if r["category"] == category]
    return filtered

# Endpoint to get a single report by id
@app.get("/api/reports/{report_id}", response_model=Report)
def get_report(report_id: int):
    report = next((r for r in reports if r["id"] == report_id), None)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report

# Endpoint to update report status (for admin use)
@app.patch("/api/reports/{report_id}", response_model=Report)
def update_report_status(report_id: int, status: str = Form(...)):
    valid_statuses = ["Submitted", "In Progress", "Resolved", "Rejected"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail="Invalid status value")
    
    report = next((r for r in reports if r["id"] == report_id), None)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    report["status"] = status
    report["updated_at"] = datetime.utcnow()
    return report
