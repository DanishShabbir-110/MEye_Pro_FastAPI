from datetime import datetime
import os
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from DB_Setup.getDatabase import get_db
from Schemas.user import User
from Schemas.StudentAttendance import ClaimAttendanceResponse

router=APIRouter(prefix="/student", tags=["Student"])

@router.put("/ClaimAttendance", response_model=ClaimAttendanceResponse)
def claim_attendance_modern(regno: str, date: str, courseName: str, conn=Depends(get_db)):
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        with conn.cursor() as cursor:
            # 1. Get course ID
            cursor.execute("SELECT CId FROM Course WHERE [Course Name]=?", (courseName,))
            course_row = cursor.fetchone()
            if not course_row:
                raise HTTPException(status_code=404, detail="Course not found")
            course_id = course_row[0]

            # 2. Get schedule
            cursor.execute("""
                SELECT sa.[Schedule Id]
                FROM [Student Attendance] sa
                JOIN TimeTable tt ON sa.[Schedule Id] = tt.[Schedule Id]
                WHERE sa.[Date]=? AND sa.[Reg No]=? AND tt.[Course Id]=?
            """, (date, regno, course_id))
            schedule_row = cursor.fetchone()
            if not schedule_row:
                raise HTTPException(status_code=404, detail="No schedule found to claim attendance!")
            schedule_id = schedule_row[0]

            # 3. Claim attendance
            cursor.execute("""
                UPDATE [Student Attendance]
                SET claim = 1
                WHERE [Date]=? AND [Reg No]=? AND [Schedule Id]=?
            """, (date, regno, schedule_id))
            conn.commit()

        return ClaimAttendanceResponse(
            regno=regno,
            date=date,
            course=courseName,
            message="Attendance has been claimed!"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))