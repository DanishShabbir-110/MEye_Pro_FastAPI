from datetime import datetime
import os
from turtle import pd
from typing import List
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile,status
from DB_Setup.getDatabase import get_db
from Schemas.DVR import  DVRModelInput
from Schemas.SWAP import SwapModelInput
from Schemas.Teachers import Teacher
from Schemas.camera import CameraModelInput
from Schemas.prescheduleClass import PrescheduleModel,PrescheduleInput
from Schemas.rescheduleClass import RescheduleModel,RescheduleInput
from Schemas.TeacherCHR_CAR import TeacherCHR,TeacherCHRInput, TeacherCHRReport
from Schemas.user import User
from Routes.Face_encodings import save_face_encodings_from_paths

router = APIRouter(prefix="/admin", tags=["Admin"])
base_folder="Assetes/Teachers"

@router.post("/AddTeacher")
async def addTeacher(
    teacher_id: str = Form(...),
    name: str = Form(...),
    Password: str = Form(...),
    teachers_pics: list[UploadFile] = File(...),
    conn = Depends(get_db)
):
    cursor = conn.cursor()

    try:
        # pehle check kar rahe hain ke teacher already exist na karta ho
        cursor.execute("SELECT UID FROM [User] WHERE UID=?", (teacher_id,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Teacher ID already exists!")

        # face recognition ke liye exactly 4 images required hain
        if len(teachers_pics) != 4:
            raise HTTPException(status_code=400, detail="Exactly 4 images required")

        # har teacher ke liye uski separate folder create ho gi
        teacher_folder = os.path.join(base_folder, teacher_id)
        os.makedirs(teacher_folder, exist_ok=True)

        teachers_pics_urls = []
        images_path = []

        for index, pic in enumerate(teachers_pics, start=1):
            file_name = f"{teacher_id}_pic{index}.jpg"
            full_path = os.path.join(teacher_folder, file_name)

            with open(full_path, "wb") as f:
                f.write(await pic.read())

            images_path.append(full_path)

            # db mein sirf relative path store ho raha hai (server move safe)
            relative_path = os.path.join(
                "Assetes", "Teachers", teacher_id, file_name
            ).replace("\\", "/")

            teachers_pics_urls.append(relative_path)

        # images save hone ke baad face encodings generate ho rahi hain
        await save_face_encodings_from_paths(
            teacher_id, "Teacher", images_path
        )

        # pehli image ko profile picture ke tor pe use kar rahe hain
        profile_url = teachers_pics_urls[0]

        user_obj = User(
            UID=teacher_id,
            Full_Name=name,
            Password=Password,
            Role="Teacher",
            Profile_Image_Url=profile_url,
            Profile_Created_Time=datetime.now().time(),
            Profile_Created_Date=datetime.now().date()
        )

        cursor.execute(
            "INSERT INTO [User] (UID,[Full Name],Password,Role,[Profile Image Url],Profile_Created_Time,Profile_Created_Date) "
            "VALUES (?,?,?,?,?,?,?)",
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

        # teacher ka record alag table mein maintain ho raha hai
        cursor.execute("INSERT INTO Teacher (TID) VALUES (?)", (teacher_id,))

        # teacher ki saari images ka reference pics table mein ja raha hai
        for index, pic_url in enumerate(teachers_pics_urls, start=1):
            cursor.execute(
                "INSERT INTO [Teacher Pic] ([Pic id],[Pic Url],[Teacher id]) VALUES (?,?,?)",
                (f"{teacher_id}_pic{index}.jpg", pic_url, teacher_id)
            )

        conn.commit()
        cursor.close()

        return {"Teacher Registered Successfully": user_obj}

    except Exception as ex:
        raise HTTPException(status_code=500, detail=str(ex))


@router.post("/AddDatacellStaff")
async def addDatacellStaff(
    datacell_id: str,
    name: str,
    Password: str,
    profileImg: UploadFile,
    conn=Depends(get_db)
):
    if conn is None:
        return {"Error": "Database connection not built!"}

    cursor = conn.cursor()
    try:
        # UID check
        cursor.execute("SELECT UID FROM [User] WHERE UID=?", (datacell_id,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail=f"User {datacell_id} exists")

        # Save profile image
        os.makedirs(base_folder, exist_ok=True)
        img_name = f"{datacell_id}_datacell.jpg"
        img_path = os.path.join(base_folder, img_name)
        with open(img_path, "wb") as f:
            f.write(await profileImg.read())
        profile_image_url = img_path.replace("\\", "/")

        # Insert into User table
        cursor.execute(
            """
            INSERT INTO [User] (UID, [Full Name], Password, Role, [Profile Image Url], Profile_Created_Time, Profile_Created_Date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datacell_id, name, Password,
                "Datacell", profile_image_url,
                datetime.now().time(), datetime.now().date()
            )
        )

        # Insert into DataCell
        cursor.execute("INSERT INTO DataCell([DC ID]) VALUES(?)", (datacell_id,))
        conn.commit()

        return {"Datacell Staff Added Successfully": {"UID": datacell_id, "Full_Name": name, "Role": "Datacell", "Profile_Image_Url": profile_image_url}}

    except Exception as ex:
        raise HTTPException(status_code=500, detail=str(ex))
    finally:
        cursor.close()
    
@router.post("/AddAdminStaff")
async def addAdminStaff(
    admin_id: str,
    name: str,
    Password: str,
    profileImg: UploadFile,
    conn=Depends(get_db)
):
    if conn is None:
        return {"Error": "Database connection not built!"}

    cursor = conn.cursor()
    try:
        # UID check
        cursor.execute("SELECT UID FROM [User] WHERE UID=?", (admin_id,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail=f"User {admin_id} exists")

        # Save profile image
        os.makedirs(base_folder, exist_ok=True)
        img_name = f"{admin_id}_admin.jpg"
        img_path = os.path.join(base_folder, img_name)
        with open(img_path, "wb") as f:
            f.write(await profileImg.read())
        profile_image_url = img_path.replace("\\", "/")

        # Insert into User table
        cursor.execute(
            """
            INSERT INTO [User] (UID, [Full Name], Password, Role, [Profile Image Url], Profile_Created_Time, Profile_Created_Date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                admin_id, name, Password,
                "Admin", profile_image_url,
                datetime.now().time(), datetime.now().date()
            )
        )

        # Insert into Admin table
        cursor.execute("INSERT INTO Admin(AID) VALUES(?)", (admin_id,))
        conn.commit()

        return {"Admin Staff Added Successfully": {"UID": admin_id, "Full_Name": name, "Role": "Admin", "Profile_Image_Url": profile_image_url}}

    except Exception as ex:
        raise HTTPException(status_code=500, detail=str(ex))
    finally:
        cursor.close()

@router.post("/prescheduleClass")
async def prescheduleClass(
    data: PrescheduleInput,
    conn=Depends(get_db)
):
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection not established")
    
    cursor = conn.cursor()
    try:
        # Teacher ID
        cursor.execute("SELECT UID FROM [User] WHERE [Full Name]=?", (data.teacherName,))
        teacher_row = cursor.fetchone()
        if not teacher_row:
            raise HTTPException(status_code=404, detail="Teacher not found")
        teacherId = str(teacher_row[0]).strip()

        # Course ID
        cursor.execute("SELECT CId FROM Course WHERE [Course Name]=?", (data.courseName,))
        course_row = cursor.fetchone()
        if not course_row:
            raise HTTPException(status_code=404, detail="Course not found")
        courseId = str(course_row[0]).strip()

        # Old venue
        cursor.execute(
            """
            SELECT [Venue Id] FROM TimeTable 
            WHERE Discipline=? AND Section=? AND [Day]=? AND [Class Start Time]=? AND [Class End Time]=? 
            AND [Teacher Id]=? AND [Course Id]=?
            """,
            (data.discipline, data.section, data.old_Day, data.old_class_start_time, data.old_class_end_time, teacherId, courseId)
        )
        old_venue_row = cursor.fetchone()
        old_venue_id = str(old_venue_row[0]).strip() if old_venue_row else None

        # All venues
        cursor.execute("SELECT [Venue Id] FROM Venue")
        all_venues = [str(v[0]).strip() for v in cursor.fetchall()]

        # Busy venues
        cursor.execute(
            """
            SELECT [Venue Id] FROM TimeTable 
            WHERE [Day] = ? AND [Class Start Time] < ? AND [Class End Time] > ?
            """,
            (data.old_Day, data.old_class_start_time, data.old_class_end_time)
        )
        busy_venues = [str(v[0]).strip() for v in cursor.fetchall()]

        # Free venue allocation
        free_venues = [v for v in all_venues if v not in busy_venues and v != old_venue_id]
        if not free_venues:
            raise HTTPException(status_code=400, detail="No free venues available for new schedule")
        new_venue_id = free_venues[0]

        # Old schedule ID
        cursor.execute(
            "SELECT [Schedule Id] FROM TimeTable WHERE [Teacher Id]=? AND [Day]=? AND [Class Start Time]=? AND [Class End Time]=?",
            (teacherId, data.old_Day, data.old_class_start_time, data.old_class_end_time)
        )
        old_schedule_row = cursor.fetchone()
        old_schedule_id = int(old_schedule_row[0]) if old_schedule_row else None

        # Check if section free
        cursor.execute(
            """
            SELECT 1 FROM TimeTable 
            WHERE Discipline = ? AND Section = ? AND [Day] = ? 
            AND [Class Start Time] < ? AND [Class End Time] > ?
            """,
            (data.discipline, data.section, data.new_Day, data.new_class_end_time, data.new_class_start_time)
        )
        if cursor.fetchone():
            raise HTTPException(
                status_code=400,
                detail=f"Class {data.discipline}-{data.section} already has a class at this time"
            )

        # Create Preschedule model
        obj = PrescheduleModel(
            old_schedule_id=old_schedule_id,
            new_venue_id=new_venue_id,
            start_time=data.new_class_start_time,
            end_time=data.new_class_end_time,
            preschedule=1,
            Day=data.new_Day
        )

        # Insert into Schedule Changes table
        cursor.execute(
            """
            INSERT INTO [Schedule Changes] 
            ([Old Schedule Id],[New Venue Id],[Start Time],[End Time],[Preschedule],[Reschedule],[Swap],[Day]) 
            VALUES (?, ?, ?, ?, 1, 0, 0, ?)
            """,
            (obj.old_schedule_id, obj.new_venue_id, obj.start_time, obj.end_time, obj.Day)
        )
        conn.commit()
        return {"Class Prescheduled Successfully": obj}

    except Exception as ex:
        raise HTTPException(status_code=500, detail=str(ex))
    finally:
        cursor.close()

@router.post("/RescheduleClass")
async def rescheduleClass(
    data: RescheduleInput,
    conn=Depends(get_db)
):
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection not established")
    
    cursor = conn.cursor()
    try:
        # Teacher ID
        cursor.execute("SELECT UID FROM [User] WHERE [Full Name]=?", (data.teacherName,))
        teacher_row = cursor.fetchone()
        if not teacher_row:
            raise HTTPException(status_code=404, detail="Teacher not found")
        teacherId = str(teacher_row[0]).strip()

        # Course ID
        cursor.execute("SELECT CId FROM Course WHERE [Course Name]=?", (data.courseName,))
        course_row = cursor.fetchone()
        if not course_row:
            raise HTTPException(status_code=404, detail="Course not found")
        courseId = str(course_row[0]).strip()

        # Old venue
        cursor.execute(
            """
            SELECT [Venue Id] FROM TimeTable 
            WHERE Discipline=? AND Section=? AND [Day]=? AND [Class Start Time]=? AND [Class End Time]=? 
            AND [Teacher Id]=? AND [Course Id]=?
            """,
            (data.discipline, data.section, data.old_Day, data.old_class_start_time, data.old_class_end_time, teacherId, courseId)
        )
        old_venue_row = cursor.fetchone()
        old_venue_id = str(old_venue_row[0]).strip() if old_venue_row else ""

        # All venues
        cursor.execute("SELECT [Venue Id] FROM Venue")
        all_venues = [str(v[0]).strip() for v in cursor.fetchall()]

        # Busy venues
        cursor.execute(
            """
            SELECT [Venue Id] FROM TimeTable 
            WHERE [Day] = ? AND [Class Start Time] < ? AND [Class End Time] > ?
            """,
            (data.new_Day, data.new_class_end_time, data.new_class_start_time)
        )
        busy_venues = [str(v[0]).strip() for v in cursor.fetchall()]

        # Free venue allocation
        free_venues = [v for v in all_venues if v not in busy_venues and v != old_venue_id]
        if not free_venues:
            raise HTTPException(status_code=400, detail="No free venues available for new schedule")
        new_venue_id = free_venues[0]

        # Old schedule ID
        cursor.execute(
            "SELECT [Schedule Id] FROM TimeTable WHERE [Teacher Id]=? AND [Day]=? AND [Class Start Time]=? AND [Class End Time]=?",
            (teacherId, data.old_Day, data.old_class_start_time, data.old_class_end_time)
        )
        old_schedule_row = cursor.fetchone()
        old_schedule_id = int(old_schedule_row[0]) if old_schedule_row else 0

        # Check if section free
        cursor.execute(
            """
            SELECT 1 FROM TimeTable 
            WHERE Discipline=? AND Section=? AND [Day]=? 
            AND [Class Start Time] < ? AND [Class End Time] > ?
            """,
            (data.discipline, data.section, data.new_Day, data.new_class_end_time, data.new_class_start_time)
        )
        if cursor.fetchone():
            raise HTTPException(
                status_code=400,
                detail=f"Class {data.discipline}-{data.section} already has another class at this time"
            )

        # Create Reschedule model
        obj = RescheduleModel(
            teacherId=teacherId,
            courseId=courseId,
            venueId=old_venue_id,
            old_schedule_id=old_schedule_id,
            new_venue_id=new_venue_id,
            start_time=data.new_class_start_time,
            end_time=data.new_class_end_time,
            reschedule=1,
            Day=data.new_Day
        )

        # Insert into Schedule Changes table
        cursor.execute(
            """
            INSERT INTO [Schedule Changes] 
            ([Old Schedule Id],[New Venue Id],[Start Time],[End Time],[Preschedule],[Reschedule],[Swap],[Day]) 
            VALUES (?, ?, ?, ?, 0, 1, 0, ?)
            """,
            (obj.old_schedule_id, obj.new_venue_id, obj.start_time, obj.end_time, obj.Day)
        )
        conn.commit()
        return {"Class Rescheduled Successfully": obj}

    except Exception as ex:
        raise HTTPException(status_code=500, detail=str(ex))
    finally:
        cursor.close()

@router.post("/swapClass")
async def swapClass(swap: SwapModelInput, conn=Depends(get_db)):
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    cursor = conn.cursor()
    try:
        # Teacher A
        cursor.execute("SELECT UID FROM [User] WHERE [Full Name] = ?", (swap.teacherAName,))
        row = cursor.fetchone()
        if not row: raise HTTPException(status_code=404, detail="Teacher A not found")
        teacherA_id = str(row[0]).strip()

        # Teacher B
        cursor.execute("SELECT UID FROM [User] WHERE [Full Name] = ?", (swap.teacherBName,))
        row = cursor.fetchone()
        if not row: raise HTTPException(status_code=404, detail="Teacher B not found")
        teacherB_id = str(row[0]).strip()

        # Course A
        cursor.execute("SELECT CId FROM Course WHERE [Course Name] = ?", (swap.courseAName,))
        row = cursor.fetchone()
        if not row: raise HTTPException(status_code=404, detail="Course A not found")
        courseA_id = str(row[0]).strip()

        # Course B
        cursor.execute("SELECT CId FROM Course WHERE [Course Name] = ?", (swap.courseBName,))
        row = cursor.fetchone()
        if not row: raise HTTPException(status_code=404, detail="Course B not found")
        courseB_id = str(row[0]).strip()

        # Teacher B class details
        cursor.execute("""
            SELECT [Schedule Id], [Class Start Time], [Class End Time], [Venue Id]
            FROM TimeTable
            WHERE [Teacher Id] = ? AND [Day] = ? AND [Section] = ? AND [Discipline] = ?
        """, (teacherB_id, swap.day, swap.section, swap.discipline))
        recB = cursor.fetchone()
        if not recB:
            debug_info = cursor.execute("SELECT [Day], [Class Start Time], [Venue Id] FROM TimeTable WHERE [Teacher Id] = ?", (teacherB_id,)).fetchall()
            raise HTTPException(status_code=400, detail=f"Class not found for {swap.teacherBName}. DB: {debug_info}")
        scheduleB_id, startTimeB, endTimeB, venueB = recB

        # Teacher A class details
        cursor.execute("""
            SELECT [Schedule Id], [Class Start Time], [Class End Time], [Venue Id]
            FROM TimeTable
            WHERE [Teacher Id] = ? AND [Day] = ? AND [Section] = ? AND [Discipline] = ?
        """, (teacherA_id, swap.day, swap.section, swap.discipline))
        recA = cursor.fetchone()
        if not recA:
            raise HTTPException(status_code=400, detail=f"Teacher A ({swap.teacherAName}) has no class on {swap.day} with section {swap.section} to swap.")
        scheduleA_id, startTimeA, endTimeA, venueA = recA

        # Insert Swap for Teacher A
        insert_query = """
            INSERT INTO [Schedule Changes] 
            ([Old Schedule Id],[New Venue Id],[Start Time],[End Time],[Preschedule],[Reschedule],[Swap],[Day]) 
            VALUES (?, ?, ?, ?, 0, 0, 1, ?)
        """
        cursor.execute(insert_query, (scheduleA_id, venueB, startTimeB, endTimeB, swap.day))
        swapA_id = int(cursor.execute("SELECT CAST(SCOPE_IDENTITY() AS INT)").fetchone()[0])

        # Insert Swap for Teacher B
        cursor.execute(insert_query, (scheduleB_id, venueA, startTimeA, endTimeA, swap.day))
        swapB_id = int(cursor.execute("SELECT CAST(SCOPE_IDENTITY() AS INT)").fetchone()[0])

        conn.commit()
        return {
            "message": "Swap Request Successfully",
            "data": {
                "TeacherA_Status": f"{swap.teacherAName} was in {venueA}, now moves to {venueB}",
                "TeacherB_Status": f"{swap.teacherBName} was in {venueB}, now moves to {venueA}",
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        cursor.close()


## Generate the CHR 
@router.post("/generateCHR")
async def generateCHR(input: TeacherCHRInput, conn=Depends(get_db)):
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    cursor = conn.cursor()
    try:
        # Teacher ID
        cursor.execute("SELECT UID FROM [User] WHERE [Full Name] = ?", (input.teacherName,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Teacher not found")
        teacher_id = str(row[0]).strip()

        # Course ID
        cursor.execute("SELECT CId FROM Course WHERE [Course Name] = ?", (input.courseName,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Course not found")
        course_id = str(row[0]).strip()

        # Schedule ID
        cursor.execute("""
            SELECT [Schedule Id] FROM TimeTable
            WHERE [Teacher Id] = ? AND [Course Id] = ? AND [Venue Id] = ? AND Discipline = ?
            AND Section = ? AND [Day] = ? AND [Class Start Time] = ? AND [Class End Time] = ?
        """, (teacher_id, course_id, input.venue, input.discipline, input.section, input.day, input.class_start_time, input.class_end_time))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="No schedule found for this class")
        schedule_id = int(row[0])

        # Insert into Teacher CHR
        insert_query = """
            INSERT INTO [Teacher CHR] 
            ([Schedule Id],[Date],[Time In],[Time Out],[Stand Time],[Sit Time],[Status],Claim)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        obj = TeacherCHR(
            scheduleId=schedule_id,
            date=input.date,
            time_in=input.time_in,
            time_out=input.time_out,
            stand_time=input.stand_time,
            sit_time=input.sit_time,
            status=input.status,
            claim=0
        )
        cursor.execute(insert_query, (obj.scheduleId, obj.date, obj.time_in, obj.time_out, obj.stand_time, obj.sit_time, obj.status, obj.claim))
        conn.commit()
        return {"Generate Successfully": obj}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()


@router.post("/AddDVR")
async def add_dvr(dvr: DVRModelInput, conn=Depends(get_db)):
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection failed")

    cursor = conn.cursor()
    try:
        # Check if MAC exists
        cursor.execute("SELECT MAC FROM DVR WHERE MAC = ?", (dvr.MAC,))
        if cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"DVR with MAC '{dvr.MAC}' already exists."
            )

        # Insert into DVR table
        cursor.execute(
            "INSERT INTO DVR (MAC, [IP], Name, channel, Password) VALUES (?, ?, ?, ?, ?)",
            (dvr.MAC, dvr.IP, dvr.Name, dvr.channel, dvr.Password)
        )

        # Insert into DVR Management table
        current_date = datetime.now().date().strftime('%Y-%m-%d')
        current_time = datetime.now().time().strftime('%H:%M:%S')

        cursor.execute(
            "INSERT INTO [DVR Management] ([Admin Id],[DVR Id],[Date],[Time]) VALUES (?, ?, ?, ?)",
            (dvr.admin_id, dvr.MAC, current_date, current_time)
        )

        conn.commit()
        return {"message": f"DVR '{dvr.Name}' added successfully with MAC: {dvr.MAC}"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database insertion failed for DVR. Unexpected Error: {e}"
        )
    finally:
        cursor.close() 

@router.post("/addCamera")
async def add_camera(cam: CameraModelInput, conn=Depends(get_db)):
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection failed")

    cursor = conn.cursor()
    try:
        # Check duplicate MAC
        cursor.execute("SELECT MAC FROM Camera WHERE MAC = ?", (cam.mac,))
        if cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Camera with MAC '{cam.mac}' already exists."
            )

        # Check DVR existence and channel capacity
        cursor.execute("SELECT channel FROM DVR WHERE MAC = ?", (cam.dvr_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"DVR ID '{cam.dvr_id}' not found."
            )
        total_channels = row[0]
        if cam.channel_no < 1 or cam.channel_no > total_channels:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Channel number {cam.channel_no} is out of range (1 to {total_channels})."
            )

        # Check if channel is in use
        cursor.execute(
            "SELECT MAC FROM Camera WHERE [DVR Id] = ? AND [Channel No] = ?",
            (cam.dvr_id, cam.channel_no)
        )
        if cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Channel No. {cam.channel_no} is already in use for DVR '{cam.dvr_id}'."
            )

        # Insert Camera
        cursor.execute(
            """INSERT INTO Camera (MAC, Placement, [Channel No], Resolution, Status, [DVR Id], [Venue Id], [IP])
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (cam.mac, cam.placement, cam.channel_no, cam.resolution, cam.status, cam.dvr_id, cam.venue_id, cam.IP)
        )

        conn.commit()
        return {"message": f"Camera '{cam.mac}' added successfully to DVR '{cam.dvr_id}' on Channel {cam.channel_no}."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        
@router.get("/SitAllTimeLecture", response_model=List[TeacherCHRReport])
def getTeacherCHR_by_SitTime(conn=Depends(get_db)):
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                u.[Full Name],
                c.[Course Name],
                tt.Section,
                tt.Discipline,
                chr.[Date],
                chr.[Stand Time],
                chr.[Sit Time]
            FROM [Teacher CHR] chr
            JOIN TimeTable tt ON chr.[Schedule Id] = tt.[Schedule Id]
            JOIN [User] u ON u.UID = tt.[Teacher Id]
            JOIN Course c ON c.CId = tt.[Course Id]
            WHERE 
                ISNULL(chr.[Stand Time], '00:00') = '00:00'
                AND ISNULL(chr.[Sit Time], '00:00') > '00:00'
        """)
        rows = cursor.fetchall()
        result = [
            TeacherCHRReport(
                TeacherName=row[0],
                CourseName=row[1],
                Section=row[2],
                Discipline=row[3],
                Date=str(row[4]),
                StandTime=str(row[5]),
                SitTime=str(row[6])
            )
            for row in rows
        ]
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()

@router.get("/StandAllTimeLecture", response_model=List[TeacherCHRReport])
def getTeacherCHR_by_StandTime(conn=Depends(get_db)):
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                u.[Full Name],
                c.[Course Name],
                tt.Section,
                tt.Discipline,
                chr.[Date],
                chr.[Stand Time],
                chr.[Sit Time]
            FROM [Teacher CHR] chr
            JOIN TimeTable tt ON chr.[Schedule Id] = tt.[Schedule Id]
            JOIN [User] u ON u.UID = tt.[Teacher Id]
            JOIN Course c ON c.CId = tt.[Course Id]
            WHERE 
                ISNULL(chr.[Sit Time], '00:00') = '00:00'
                AND ISNULL(chr.[Stand Time], '00:00') > '00:00'
        """)
        rows = cursor.fetchall()
        result = [
            TeacherCHRReport(
                TeacherName=row[0],
                CourseName=row[1],
                Section=row[2],
                Discipline=row[3],
                Date=str(row[4]),
                StandTime=str(row[5]),
                SitTime=str(row[6])
            )
            for row in rows
        ]
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()