from datetime import datetime
import io
import os
from turtle import pd
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from DB_Setup.getDatabase import get_db
from DB_Setup.connection import get_connection
from Schemas.user import User
from Schemas.Student import Student
from Schemas.enrollment import SingleEnrollmentInput
from Routes.Face_encodings import save_face_encodings_from_paths
import pyodbc
import pandas as pd
from Schemas.Allocation import AllocationInput
import uuid 

route = APIRouter(prefix="/datacell", tags=["DataCell"])
BASE_FOLDER = "Assetes/Students"


@route.post("/AddStudent")
async def addStudent(
    Regno: str = Form(...),
    name: str = Form(...),
    Password: str = Form(...),
    discipline: str = Form(...),
    session: str = Form(...),
    student_pics: list[UploadFile] = File(...),
    conn:pyodbc.Connection=Depends(get_db)
):
    # Face recognition ke liye exactly 4 images required hain
    if conn is None:
        return {"Error": "connection not built"}
    
    cursor = conn.cursor()

        # Duplicate student entry se bachne ke liye check
    cursor.execute("SELECT UID FROM [User] WHERE UID = ?", (Regno,))
    if cursor.fetchone():
        raise HTTPException(status_code=400, detail="Student already exists!")
    if len(student_pics) != 4:
        raise HTTPException(status_code=400, detail="Exactly 4 images required")

    # Discipline ke naam se folder create / use ho ga
    discipline_folder = os.path.join(BASE_FOLDER, discipline)
    os.makedirs(discipline_folder, exist_ok=True)

    student_pics_url = []
    images_path = []

    for index, pic in enumerate(student_pics, start=1):
        file_name = f"{Regno}_pic{index}.jpg"
        file_path = os.path.join(discipline_folder, file_name)

        images_path.append(file_path)

        with open(file_path, "wb") as image:
            image.write(await pic.read())

        student_pics_url.append(file_path.replace("\\", "/"))

    # Images se face encodings generate kar rahe hain
    await save_face_encodings_from_paths(Regno, "Student", images_path)

    profile_url = student_pics_url[0]  # First image profile pic ke liye

    try:
        user_obj = User(
            UID=Regno,
            Full_Name=name,
            Password=Password,
            Role="Student",
            Profile_Image_Url=profile_url,
            Profile_Created_Time=datetime.now().time(),
            Profile_Created_Date=datetime.now().date()
        )

        cursor.execute(
            """
            INSERT INTO [User]
            (UID, [Full Name], Password, Role,
             [Profile Image Url], Profile_Created_Time, Profile_Created_Date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_obj.UID,
                user_obj.Full_Name,
                user_obj.Password,
                user_obj.Role,
                user_obj.Profile_Image_Url,
                user_obj.Profile_Created_Time,
                user_obj.Profile_Created_Date
            )
        )
        conn.commit()

        student_obj = Student(Regno=Regno, Discipline=discipline, Session=session)
        cursor.execute(
            "INSERT INTO Student (Regno, Discipline,Session) VALUES (?, ?, ?)",
            (student_obj.Regno, student_obj.Discipline, student_obj.Session)
        )
        conn.commit()

        # Student ki images ka record database mein save
        for index, pic_url in enumerate(student_pics_url, start=1):
            cursor.execute(
                "INSERT INTO [Student Pic] ([Pic id], [Pic Url], [regno]) VALUES (?, ?, ?)",
                (f"{Regno}_pic{index}.jpg", pic_url, Regno)
            )
            conn.commit()

        cursor.close()

        return {"Student Registered!": user_obj}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@route.post("/singleEnrollmentofStudent")
async def singleEnrollmentofStudent(
    Regno: str = Form(...),
    courseName: str = Form(...),
    section: str = Form(...),
    semester: int = Form(...),
    session: str = Form(...),
    conn:pyodbc.Connection=Depends(get_db)
):
    if conn is None:
        return {"Error": "connection not built"}
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT UID FROM [User] WHERE UID = ?", (Regno,))
        if not cursor.fetchone():
            raise HTTPException(status_code=400, detail=f"No Student with this RegNo: {Regno}")
        
        cursor.execute("select CId from Course where [Course Name]=?",(courseName,))
        row=cursor.fetchone()
        if row is None:
            raise HTTPException(status_code=400, detail=f"No course offered with this Name!")
        courseId=row[0]
        insert_query="insert into Enrollment ([Student Id],[Course Id],section,Semester,Session) values(?,?,?,?,?)"
        cursor.execute(insert_query,(Regno,courseId,section,semester,session))
        conn.commit()
        cursor.close()
        return {"Enrolled Course Success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@route.post("/UploadEnrollmentExcel")
async def upload_enrollment_excel(
    file: UploadFile = File(...),
    conn: pyodbc.Connection = Depends(get_db)
):
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Please upload an Excel file.")

    try:
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))

        required_columns = ['StudentId', 'CourseId', 'Session', 'Semester', 'Section']
        if not all(col in df.columns for col in required_columns):
            raise HTTPException(status_code=400, detail=f"Excel must have columns: {required_columns}")

        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM Enrollment")
        current_count = cursor.fetchone()[0]

        success_count = 0
        errors = []

        for index, row in df.iterrows():
            try:
                student_id = str(row['StudentId'])
                course_id = str(row['CourseId'])
                session = str(row['Session'])
                semester = int(row['Semester'])
                section = str(row['Section'])

                cursor.execute("""
                    SELECT 1 FROM Enrollment 
                    WHERE [Student Id] = ? AND [Course Id] = ? AND [Session] = ? AND [Semester] = ? AND [Section] = ?
                """, (student_id, course_id, session, semester, section))

                if cursor.fetchone():
                    errors.append(f"Row {index+2}: Record already exists in database.")
                    continue

                cursor.execute("SELECT 1 FROM Student WHERE Regno = ?", (student_id,))
                if not cursor.fetchone():
                    errors.append(f"Row {index+2}: Student {student_id} not found.")
                    continue

                cursor.execute("SELECT 1 FROM Course WHERE CId = ?", (course_id,))
                if not cursor.fetchone():
                    errors.append(f"Row {index+2}: Course {course_id} not found.")
                    continue

                current_count += 1
                enrollment_id = f"Enroll-{current_count}"

                insert_query = """
                    INSERT INTO Enrollment 
                    ([Student Id], [Course Id], section,Semester,Session) 
                    VALUES (?, ?, ?, ?, ?)
                """
                cursor.execute(insert_query, (
                    student_id, course_id, section, semester,session 
                ))
                success_count += 1

            except Exception as e:
                errors.append(f"Row {index+2}: {str(e)}")

        conn.commit()
        cursor.close()

        return {
            "message": f"Successfully enrolled {success_count} students.",
            "total_rows": len(df),
            "errors": errors
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@route.post("/singleAllocation")
async def single_allocation(
    allocation: AllocationInput, 
    conn: pyodbc.Connection = Depends(get_db)
):
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = conn.cursor()

        
        cursor.execute("SELECT CId FROM Course WHERE [Course Name] = ?", (allocation.courseName,))
        course_row = cursor.fetchone()
        if not course_row:
            raise HTTPException(status_code=404, detail="Course not found")
        course_id = course_row[0]

        
        cursor.execute("SELECT UID FROM [User] WHERE [Full Name] = ? AND Role = 'Teacher'", (allocation.teacherName,))
        teacher_row = cursor.fetchone()
        if not teacher_row:
            raise HTTPException(status_code=404, detail="Teacher not found")
        teacher_id = teacher_row[0]
        
        check_query = """
            SELECT 1 FROM Allocation 
            WHERE [Cid] = ? AND [Tid] = ? AND [Section] = ? 
            AND Semester = ? AND [Session] = ?
        """
        cursor.execute(check_query, (course_id, teacher_id, allocation.section, allocation.semester, allocation.session))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="This allocation already exists!")

       
        insert_query = """
            INSERT INTO Allocation 
            ([Cid], [Tid], Discipline, [Session], Section, Semester)
            VALUES ( ?, ?, ?, ?, ?, ?)
        """
        cursor.execute(insert_query, (
             course_id, teacher_id, allocation.discipline, 
            allocation.session, allocation.section, allocation.semester
        ))
        
        conn.commit()
        cursor.close()
        return {"Allocation Success":allocation}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@route.post("/UploadAllocationExcel")
async def upload_allocation_excel(
    file: UploadFile = File(...),
    conn: pyodbc.Connection = Depends(get_db)
):
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Please upload an Excel file.")

    try:    
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))

       
        required_columns = ['CourseId', 'TeacherId', 'Discipline', 'Session', 'Section', 'Semester']
        if not all(col in df.columns for col in required_columns):
            raise HTTPException(status_code=400, detail=f"Required columns: {required_columns}")

        cursor = conn.cursor()
        

        success_count = 0
        errors = []

        for index, row in df.iterrows():
            try:
                c_id = str(row['CourseId'])
                t_id = str(row['TeacherId'])
                disc = str(row['Discipline'])
                sess = str(row['Session'])
                sect = str(row['Section'])
                sem = int(row['Semester'])

                # Duplicate Check
                cursor.execute("""
                    SELECT 1 FROM Allocation 
                    WHERE [Cid] = ? AND [Tid] = ? AND Section = ? AND Semester = ? AND [Session] = ?
                """, (c_id, t_id, sect, sem, sess))

                if cursor.fetchone():
                    errors.append(f"Row {index+2}: Allocation already exists.")
                    continue
                
                cursor.execute("""
                    INSERT INTO Allocation 
                    (Cid, Tid, Discipline, [Session], Section, Semester)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (c_id, t_id, disc, sess, sect, sem))
                
                success_count += 1

            except Exception as e:
                errors.append(f"Row {index+2}: {str(e)}")

        conn.commit()
        cursor.close()

        return {
            "message": f"Successfully allocated {success_count} records.",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
