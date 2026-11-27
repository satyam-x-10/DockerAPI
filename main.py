import logging
import time
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger("student-api")

app = FastAPI(
    title="Student Management API",
    description="A stateless FastAPI service for managing student records with structured logging and health checks.",
    version="1.0.0",
)


class StudentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    course: str = Field(..., min_length=1, max_length=120)
    semester: int = Field(default=1, ge=1, le=12)


class StudentUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    course: Optional[str] = Field(default=None, min_length=1, max_length=120)
    semester: Optional[int] = Field(default=None, ge=1, le=12)


students: list[dict] = [
    {"id": 1, "name": "Aarav", "course": "Backend Development", "semester": 4},
    {"id": 2, "name": "Diya", "course": "Backend Development", "semester": 4},
]
next_id = 3


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    try:
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "method=%s path=%s status=%s duration_ms=%.2f",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response
    except Exception:
        duration_ms = (time.perf_counter() - start) * 1000
        logger.exception(
            "method=%s path=%s status=500 duration_ms=%.2f",
            request.method,
            request.url.path,
            duration_ms,
        )
        raise


@app.get("/")
def root():
    return {
        "application": "Student Management API",
        "framework": "FastAPI",
        "status": "running",
        "routes": ["/health", "/students", "/docs"],
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/students")
def list_students():
    return students


@app.get("/students/{student_id}")
def get_student(student_id: int):
    for student in students:
        if student["id"] == student_id:
            return student
    raise HTTPException(status_code=404, detail="Student not found")


@app.post("/students", status_code=201)
def create_student(payload: StudentCreate):
    global next_id
    student = {
        "id": next_id,
        "name": payload.name,
        "course": payload.course,
        "semester": payload.semester,
    }
    next_id += 1
    students.append(student)
    return student


@app.put("/students/{student_id}")
def update_student(student_id: int, payload: StudentUpdate):
    for student in students:
        if student["id"] == student_id:
            if payload.name is not None:
                student["name"] = payload.name
            if payload.course is not None:
                student["course"] = payload.course
            if payload.semester is not None:
                student["semester"] = payload.semester
            return student
    raise HTTPException(status_code=404, detail="Student not found")


@app.delete("/students/{student_id}")
def delete_student(student_id: int):
    for index, student in enumerate(students):
        if student["id"] == student_id:
            removed = students.pop(index)
            return {"deleted": True, "student": removed}
    raise HTTPException(status_code=404, detail="Student not found")
