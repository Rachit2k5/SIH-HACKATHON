from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
import base64

app = FastAPI(title="Civic Issue Reporting Backend")

# CORS: allow your frontend origin here in production for security
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with your frontend URL in prod
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage (replace with real DB in production)
reports = []
tasks = {}
id_counter = 1

# Departments based on keywords - simplistic routing logic demo
department_map = {
    "pothole": "Public Works",
    "street light": "Electrical",
    "water supply": "Water Department",
    "garbage": "Sanitation",
    "traffic signal": "Traffic Control",
    "default": "General Services"
}

class Report(BaseModel):
    id: int
    title: str
    category: str
    priority: str
    location: str
    description: str
    photo: Optional[str] = None
    status: str = Field(default="Submitted")
    assigned_department: Optional[str] = None
    created_at: datetime
    updated_at: datetime

# Helper: assign department based on category and keywords
def assign_department(report):
    cat = report.category.lower()
    for key in department_map:
        if key in cat:
            return department_map[key]
    # Fallback by location keywords example (can be improved)
    loc = report.location.lower()
    if "downtown" in loc:
        return "City Center Services"
    return department_map["default"]

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
        if len(contents) > 5 * 1024 * 1024:  # 5MB max size, adjust as needed
            raise HTTPException(status_code=400, detail="Photo too large (max 5 MB)")
        photo_base64 = base64.b64encode(contents).decode("utf-8")

    report_obj = Report(
        id=id_counter,
        title=title,
        category=category,
        priority=priority,
        location=location,
        description=description,
        photo=photo_base64,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    report_obj.assigned_department = assign_department(report_obj)
    reports.append(report_obj)
    tasks[report_obj.id] = {
        "assigned_to": report_obj.assigned_department,
        "status": report_obj.status,
        "last_updated": report_obj.updated_at
    }
    id_counter += 1
    return report_obj

@app.get("/api/reports", response_model=List[Report])
def get_reports(
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    location_contains: Optional[str] = Query(None),
):
    filtered = reports
    if status:
        filtered = [r for r in filtered if r.status.lower() == status.lower()]
    if category:
        filtered = [r for r in filtered if r.category.lower() == category.lower()]
    if priority:
        filtered = [r for r in filtered if r.priority.lower() == priority.lower()]
    if location_contains:
        filtered = [r for r in filtered if location_contains.lower() in r.location.lower()]
    return filtered

@app.get("/api/reports/{report_id}", response_model=Report)
def get_report(report_id: int):
    report = next((r for r in reports if r.id == report_id), None)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report

class StatusUpdate(BaseModel):
    status: str

@app.patch("/api/reports/{report_id}/status", response_model=Report)
def update_report_status(report_id: int, update: StatusUpdate):
    valid_statuses = {"Submitted", "In Progress", "Resolved", "Rejected"}
    if update.status not in valid_statuses:
        raise HTTPException(status_code=400, detail="Invalid status")

    report = next((r for r in reports if r.id == report_id), None)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    report.status = update.status
    report.updated_at = datetime.utcnow()
    tasks[report_id]["status"] = update.status
    tasks[report_id]["last_updated"] = report.updated_at
    return report

@app.get("/api/tasks/{report_id}")
def get_task(report_id: int):
    task = tasks.get(report_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.get("/api/departments")
def get_departments():
    return list(set(department_map.values()))

# Optional: health check endpoint
@app.get("/health")
def health():
    return {"status": "ok"}
