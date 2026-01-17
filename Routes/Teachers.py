from datetime import datetime, time
from fastapi import APIRouter, Depends, Form, HTTPException
from DB_Setup.getDatabase import get_db
from Schemas.TeacherCHR_CAR import TeacherCHRReportItem,TeacherCHRResponse 
from DB_Setup.connection import get_connection
from Schemas.StudentAttendance import StudentAttendanceModel, StudentAttendanceResponse
import pyodbc

router=APIRouter(prefix="/teacher", tags=["Teacher"])

@router.get("/TeacherCHR", response_model=TeacherCHRResponse)
def teacherCHR_CAR(teacherID: str,conn:pyodbc.Connection=Depends(get_db)):
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    cursor = conn.cursor()
    try:
        fetch_data_query = """
            SELECT 
                c.[Course Name],
                tt.Section,
                tt.Discipline,
                tt.[Day],
                tt.[Class Start Time],
                tt.[Class End Time],
                tt.[Course Id],
                chr.status,
                chr.[Time In],
                chr.[Time Out],
                chr.[Date]
            FROM [Teacher CHR] chr 
            JOIN TimeTable tt ON chr.[Schedule Id] = tt.[Schedule Id] 
            JOIN Course c ON tt.[Course Id] = c.CId
            JOIN Teacher t ON t.TID = tt.[Teacher Id]
            WHERE t.TID = ?
        """
        cursor.execute(fetch_data_query, (teacherID,))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        if not rows:
            return TeacherCHRResponse(Teacher_ID=teacherID, CHR_Reports=[])

        reports = [
            TeacherCHRReportItem(
                Discipline=f"{r[2]}-{r[1]}",
                Date=str(r[10]),
                Course=r[0],
                Day=r[3],
                Class_time=f"{r[4]}-{r[5]}",
                Time_in=to_12_hour(r[8]),
                Time_out=to_12_hour(r[9]),
                Status=r[7]
            )
            for r in rows
        ]

        return TeacherCHRResponse(Teacher_ID=teacherID, CHR_Reports=reports)

    except Exception as ex:
        raise HTTPException(status_code=500, detail=str(ex))


@router.get("/TeacherCHRByDate", response_model=TeacherCHRResponse)
def teacher_chr_by_date_base(teacherID: str, date: str,conn:pyodbc.Connection=Depends(get_db)):
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection failed")

    cursor = conn.cursor()
    try:
        query = """
            SELECT 
                c.[Course Name],
                tt.Section,
                tt.Discipline,
                tt.[Day],
                tt.[Class Start Time],
                tt.[Class End Time],
                tt.[Course Id],
                chr.status,
                chr.[Time In],
                chr.[Time Out],
                chr.[Date]
            FROM [Teacher CHR] chr
            JOIN TimeTable tt ON chr.[Schedule Id] = tt.[Schedule Id]
            JOIN Course c ON tt.[Course Id] = c.CId
            JOIN Teacher t ON t.TID = tt.[Teacher Id]
            WHERE t.TID = ? AND chr.[Date] = ?
        """
        cursor.execute(query, (teacherID, date))
        rows = cursor.fetchall()

        if not rows:
            raise HTTPException(status_code=404, detail="No CHR report for this teacher on this date.")

        reports = [
            TeacherCHRReportItem(
                Discipline=f"{r[2]}-{r[1]}",
                Date=str(r[10]),
                Course=r[0],
                Day=r[3],
                Class_time=f"{r[4]}-{r[5]}",
                Time_in=to_12_hour(r[8]),
                Time_out=to_12_hour(r[9]),
                Status=r[7]
            )
            for r in rows
        ]

        return TeacherCHRResponse(
            TeacherID=teacherID,
            CHRReports=reports
        )

    except Exception as ex:
        raise HTTPException(status_code=500, detail=str(ex))
    finally:
        cursor.close()
        conn.close()

@router.post("/StudentAttendance", response_model=StudentAttendanceResponse)
def mark_student_attendance_response(attendance: StudentAttendanceModel,conn:pyodbc.Connection=Depends(get_db)):
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        cursor = conn.cursor()

        # Student exists?
        cursor.execute("SELECT Regno FROM Student WHERE Regno = ?", (attendance.studentRegno,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Student not found")

        # Course exists?
        cursor.execute("SELECT CId FROM Course WHERE [Course Name] = ?", (attendance.courseName,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Course not found")
        courseId = row[0]

        # Get schedule ID
        cursor.execute("""
            SELECT [Schedule Id] FROM TimeTable
            WHERE [Course Id] = ? AND [Teacher Id] = ? AND Day = ? AND Discipline = ? 
                  AND Section = ? AND [Class Start Time] = ? AND [Class End Time] = ?
        """, (
            courseId, attendance.teacherId, attendance.day, attendance.discipline,
            attendance.section, attendance.class_start_time, attendance.class_end_time
        ))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Schedule not found")
        schedule_id = row[0]

        # Already marked?
        cursor.execute("""
            SELECT 1 FROM [Student Attendance]
            WHERE [Reg No] = ? AND [Schedule Id] = ? AND [Date] = ?
        """, (attendance.studentRegno, schedule_id, attendance.date))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Attendance already marked for this student today")

        # Insert attendance
        cursor.execute("""
            INSERT INTO [Student Attendance] ([Reg No], [Schedule Id], [Date])
            VALUES (?, ?, ?)
        """, (attendance.studentRegno, schedule_id, attendance.date))

        conn.commit()
        cursor.close()

        return StudentAttendanceResponse(
            Message="Student Attendance Marked!!",
            Student=attendance.studentRegno
        )

    except HTTPException as http_e:
        raise http_e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



def to_12_hour(t: time):
    if t is None:
        return None
    return t.strftime("%I:%M %p")