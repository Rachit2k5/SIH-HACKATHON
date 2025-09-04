from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
import base64

app = FastAPI()

# IMPORTANT: restrict origins in production to your frontend domain for security
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to ["https://your-frontend-domain.com"] in production
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store (replace with DB for production)
reports = []
id_counter = 1

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
        if len(contents) > 2 * 1024 * 1024:  # 2 MB size limit
            raise HTTPException(status_code=400, detail="Photo size too large, max is 2MB.")
        photo_base64 = base64.b64encode(contents).decode("utf-8")

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
        "updated_at": datetime.utcnow(),
    }
    reports.append(new_report)
    id_counter += 1

    return new_report

@app.get("/api/reports", response_model=List[Report])
def get_reports(status: Optional[str] = None, category: Optional[str] = None):
    filtered = reports
    if status:
        filtered = [r for r in filtered if r["status"].lower() == status.lower()]
    if category:
        filtered = [r for r in filtered if r["category"].lower() == category.lower()]
    return filtered

@app.get("/api/reports/{report_id}", response_model=Report)
def get_report(report_id: int):
    report = next((r for r in reports if r["id"] == report_id), None)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report

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
